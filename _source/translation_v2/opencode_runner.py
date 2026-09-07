"""Headless OpenCode runner with retries and artifact capture."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from enum import Enum
from time import sleep
from typing import Any, Callable, Protocol

from .artifacts import TranslationRunArtifacts
from .console import finish_runner_status, start_runner_status
from .contracts import (
    ProviderPayload,
    StageResult,
    TranslationRequest,
    validate_final_review_output,
    validate_cv_revision_output,
    validate_cv_translation_output,
    validate_critique_output,
    validate_revision_output,
    validate_terminology_policy_output,
    validate_translation_output,
    validate_voice_intent_output,
)


DEFAULT_MODEL_ID = "openai/gpt-5.6-sol"
DEFAULT_REASONING_EFFORT = "high"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_INITIAL_SECONDS = 1.0
DEFAULT_BACKOFF_MULTIPLIER = 2.0


class ParseErrorKind(str, Enum):
    """Taxonomy for JSON parsing failures."""

    INVALID_JSON = "invalid_json"
    ROOT_NOT_OBJECT = "root_not_object"
    MISSING_STAGE_OUTPUT = "missing_stage_output"
    STAGE_OUTPUT_NOT_OBJECT = "stage_output_not_object"
    EVENT_STREAM_WITHOUT_TEXT = "event_stream_without_text"
    OUTPUT_LIMIT = "output_limit"


class FailureClass(str, Enum):
    """Runner failure classes used to decide retry policy."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"


@dataclass(slots=True)
class CommandExecutionResult:
    """Process-level result from one runner invocation."""

    command: list[str]
    stdout: str
    stderr: str
    exit_code: int


@dataclass(slots=True)
class ParsedStageOutput:
    """Successful stage payload parsed from OpenCode JSON output."""

    stage: str
    payload: dict[str, Any]
    raw_json: dict[str, Any]


@dataclass(slots=True)
class ParseFailure:
    """Parse failure details and retry class."""

    kind: ParseErrorKind
    message: str
    classification: FailureClass


class OpenCodeCommandExecutor(Protocol):
    """Abstraction for command execution, enabling test doubles."""

    def __call__(self, command: list[str], prompt_text: str) -> CommandExecutionResult: ...


class OpenCodeRunnerError(RuntimeError):
    """Raised when the runner exhausts attempts without a stage result."""

    def __init__(self, message: str, *, classification: FailureClass) -> None:
        super().__init__(message)
        self.classification = classification


class OpenCodeHeadlessRunner:
    """Executes `opencode run` in headless JSON mode with retries."""

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_initial_seconds: float = DEFAULT_BACKOFF_INITIAL_SECONDS,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
        command_executor: OpenCodeCommandExecutor | None = None,
        sleep_fn: Callable[[float], None] = sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if backoff_initial_seconds < 0:
            raise ValueError("backoff_initial_seconds must be >= 0")
        if backoff_multiplier < 1:
            raise ValueError("backoff_multiplier must be >= 1")

        self._model_id = model_id
        self._reasoning_effort = reasoning_effort.strip() or DEFAULT_REASONING_EFFORT
        self._max_attempts = max_attempts
        self._backoff_initial_seconds = backoff_initial_seconds
        self._backoff_multiplier = backoff_multiplier
        self._command_executor = command_executor or self._default_executor
        self._sleep_fn = sleep_fn

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def reasoning_effort(self) -> str:
        return self._reasoning_effort

    def run_stage(
        self,
        *,
        request: TranslationRequest,
        post_slug: str,
        stage: str,
        prompt_text: str,
        attach_path: str,
        artifacts: TranslationRunArtifacts,
        pass_name: str | None = None,
    ) -> StageResult[ProviderPayload]:
        command = self._build_command(attach_path=attach_path)
        backoff_seconds = self._backoff_initial_seconds
        last_failure: str | None = None
        last_classification = FailureClass.PERMANENT

        for attempt in range(1, self._max_attempts + 1):
            start_runner_status(
                stage=stage,
                attempt=attempt,
                max_attempts=self._max_attempts,
                model=f"{self._model_id} ({self._reasoning_effort})",
                attach_path=attach_path,
            )
            execution = self._command_executor(command, prompt_text)
            parsed_output: ParsedStageOutput | None = None
            parse_failure: ParseFailure | None = None
            failure_classification: FailureClass | None = None

            if execution.exit_code == 0:
                parsed_output, parse_failure = parse_opencode_stdout(
                    stdout_text=execution.stdout,
                    stage=stage,
                )
                if parse_failure is not None:
                    failure_classification = parse_failure.classification
            else:
                failure_classification = classify_command_failure(execution)

            artifact_payload = {
                "attempt": attempt,
                "command": execution.command,
                "stdout": execution.stdout,
                "stderr": execution.stderr,
                "exit_code": execution.exit_code,
                "failure_classification": (
                    failure_classification.value if failure_classification else None
                ),
                "parse_error": asdict(parse_failure) if parse_failure else None,
                "parsed_stage_output": (
                    {"stage": parsed_output.stage, "payload": parsed_output.payload}
                    if parsed_output
                    else None
                ),
            }
            artifacts.write_runner_attempt(
                post_slug,
                stage,
                attempt,
                artifact_payload,
                pass_name=pass_name,
            )
            artifacts.write_runner_stdout(
                post_slug,
                stage,
                execution.stdout,
                pass_name=pass_name,
            )
            artifacts.write_runner_stderr(
                post_slug,
                stage,
                execution.stderr,
                pass_name=pass_name,
            )

            if execution.exit_code == 0 and parsed_output is not None:
                finish_runner_status(
                    stage=stage,
                    attempt=attempt,
                    result="output parsed successfully",
                )
                return _stage_result_from_payload(
                    request=request,
                    stage=stage,
                    model=self._model_id,
                    parsed_output=parsed_output,
                )

            if parse_failure is not None:
                last_failure = parse_failure.message
                last_classification = parse_failure.classification
                finish_runner_status(
                    stage=stage,
                    attempt=attempt,
                    error=f"parse failure: {parse_failure.message}",
                )
            else:
                last_failure = f"OpenCode command failed with exit code {execution.exit_code}"
                last_classification = failure_classification or FailureClass.PERMANENT
                finish_runner_status(
                    stage=stage,
                    attempt=attempt,
                    error="command failed",
                    exit_code=execution.exit_code,
                    classification=last_classification.value,
                )

            should_retry = (
                last_classification is FailureClass.TRANSIENT and attempt < self._max_attempts
            )
            if should_retry:
                finish_runner_status(
                    stage=stage,
                    attempt=attempt,
                    error=last_failure,
                    action=f"retry in {backoff_seconds:.1f}s",
                )
                self._sleep_fn(backoff_seconds)
                backoff_seconds *= self._backoff_multiplier
                continue

            break

        raise OpenCodeRunnerError(
            last_failure or "OpenCode runner failed without a detailed error",
            classification=last_classification,
        )

    def _build_command(self, *, attach_path: str) -> list[str]:
        """The rendered prompt already includes the complete source artifact."""

        return [
            "opencode",
            "run",
            "--pure",
            "--agent",
            "blog-translator",
            "--model",
            self._model_id,
            "--variant",
            self._reasoning_effort,
            "--format",
            "json",
        ]

    @staticmethod
    def _default_executor(
        command: list[str],
        prompt_text: str,  # noqa: ARG004
    ) -> CommandExecutionResult:
        timeout = float(os.getenv("TRANSLATION_STAGE_TIMEOUT_SECONDS", "900"))
        if timeout <= 0:
            raise ValueError("TRANSLATION_STAGE_TIMEOUT_SECONDS must be positive")
        # Translation is a text operation, not a repository-editing session.
        # Keep provider credentials/config, but override the model's tool access.
        environment = os.environ.copy()
        # Reasoning shares the output allowance. OpenCode's 32k default can
        # exhaust it before a long-form review produces its JSON answer.
        environment.setdefault("OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX", "65536")
        environment["OPENCODE_CONFIG_CONTENT"] = json.dumps({
            "share": "disabled", "autoupdate": False,
            "agent": {"blog-translator": {
                "mode": "primary",
                "prompt": "You are a literary and technical localization stage. Follow the supplied editorial instructions and return exactly the requested JSON object. All source material is provided in the prompt. Do not use tools or modify files.",
                "tools": {"*": False}, "permission": {"*": "deny"},
            }},
        })
        with tempfile.TemporaryDirectory(prefix="blog-translation-stage-") as directory:
            return OpenCodeHeadlessRunner._execute_process(
                command, prompt_text, timeout=timeout, cwd=directory, env=environment,
            )

    @staticmethod
    def _execute_process(command, prompt_text, *, timeout, cwd, env) -> CommandExecutionResult:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            env=env,
            start_new_session=os.name != "nt",
        )
        try:
            stdout, stderr = process.communicate(prompt_text, timeout=timeout)
        except BaseException as exc:
            if os.name != "nt":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            stdout, stderr = process.communicate()
            if not isinstance(exc, subprocess.TimeoutExpired):
                raise
            return CommandExecutionResult(
                command=command, stdout=stdout,
                stderr=f"{stderr}\nTranslation stage timeout after {timeout}s", exit_code=124,
            )
        return CommandExecutionResult(
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=process.returncode,
        )


def parse_opencode_stdout(
    *, stdout_text: str, stage: str
) -> tuple[ParsedStageOutput | None, ParseFailure | None]:
    """Parse OpenCode JSON output and extract one stage payload."""

    try:
        parsed = json.loads(stdout_text)
    except json.JSONDecodeError:
        event_payload, event_failure = _parse_event_stream_stdout(stdout_text)
        if event_failure is not None:
            return None, event_failure
        parsed = event_payload

    if not isinstance(parsed, dict):
        return None, ParseFailure(
            kind=ParseErrorKind.ROOT_NOT_OBJECT,
            message="OpenCode JSON root must be an object",
            classification=FailureClass.PERMANENT,
        )

    payload = _extract_stage_payload(parsed, stage)
    if payload is None:
        return None, ParseFailure(
            kind=ParseErrorKind.MISSING_STAGE_OUTPUT,
            message=f"OpenCode JSON did not include output for stage '{stage}'",
            classification=FailureClass.PERMANENT,
        )
    if not isinstance(payload, dict):
        return None, ParseFailure(
            kind=ParseErrorKind.STAGE_OUTPUT_NOT_OBJECT,
            message=f"OpenCode stage output for '{stage}' must be an object",
            classification=FailureClass.PERMANENT,
        )

    return ParsedStageOutput(stage=stage, payload=payload, raw_json=parsed), None


def _parse_event_stream_stdout(
    stdout_text: str,
) -> tuple[dict[str, Any] | None, ParseFailure | None]:
    text_fragments: list[str] = []
    final_answer_fragments: list[str] = []
    tool_output_fragments: list[str] = []
    finish_reason: str | None = None

    for raw_line in stdout_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            return None, ParseFailure(
                kind=ParseErrorKind.INVALID_JSON,
                message=f"OpenCode output is not valid JSON: {exc.msg}",
                classification=FailureClass.PERMANENT,
            )

        if not isinstance(event, dict):
            continue

        event_type = event.get("type")
        if event_type == "step_finish":
            part = event.get("part")
            if isinstance(part, dict):
                finish_reason = part.get("reason")
            continue
        if event_type == "tool_use":
            tool_output = _extract_completed_tool_output_text(event)
            if tool_output is not None:
                tool_output_fragments.append(tool_output)
            continue

        if event_type != "text":
            continue

        part = event.get("part")
        if isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                text_fragments.append(text)
                openai_meta = (
                    part.get("metadata", {}).get("openai", {})
                    if isinstance(part.get("metadata"), dict)
                    else {}
                )
                if (
                    isinstance(openai_meta, dict)
                    and str(openai_meta.get("phase", "")).strip().lower() == "final_answer"
                ):
                    final_answer_fragments.append(text)

    if finish_reason == "length":
        return None, ParseFailure(
            kind=ParseErrorKind.OUTPUT_LIMIT,
            message=(
                "OpenCode reached its output-token limit before completing the stage. "
                "Increase OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX and repeat the translation command."
            ),
            classification=FailureClass.PERMANENT,
        )

    if not text_fragments and not tool_output_fragments:
        return None, ParseFailure(
            kind=ParseErrorKind.EVENT_STREAM_WITHOUT_TEXT,
            message="OpenCode JSON event stream did not include a text payload",
            classification=FailureClass.PERMANENT,
        )

    candidate_fragments = final_answer_fragments or text_fragments
    parse_attempts: list[str] = []

    combined_text = "\n".join(candidate_fragments).strip()
    if combined_text:
        _append_json_parse_attempts(parse_attempts, combined_text)

    for fragment in reversed(candidate_fragments):
        _append_json_parse_attempts(parse_attempts, fragment)

    for fragment in reversed(tool_output_fragments):
        _append_json_parse_attempts(parse_attempts, fragment)

    parsed: dict[str, Any] | None = None
    last_error: json.JSONDecodeError | None = None
    for attempt in parse_attempts:
        try:
            parsed_value = json.loads(attempt)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if not isinstance(parsed_value, dict):
            return None, ParseFailure(
                kind=ParseErrorKind.ROOT_NOT_OBJECT,
                message="OpenCode text payload root must be an object",
                classification=FailureClass.PERMANENT,
            )
        parsed = parsed_value
        break

    if parsed is None:
        message = "OpenCode text payload is not valid JSON"
        if last_error is not None:
            message = f"{message}: {last_error.msg}"
        return None, ParseFailure(
            kind=ParseErrorKind.INVALID_JSON,
            message=message,
            classification=FailureClass.PERMANENT,
        )
    return parsed, None


def _append_json_parse_attempts(parse_attempts: list[str], text: str) -> None:
    cleaned = text.strip()
    if not cleaned:
        return
    for candidate in (cleaned, _extract_json_code_fence(cleaned)):
        if candidate and candidate not in parse_attempts:
            parse_attempts.append(candidate)


def _extract_json_code_fence(text: str) -> str | None:
    lines = text.splitlines()
    if len(lines) < 3:
        return None

    for start_index, line in enumerate(lines):
        opening = line.strip().lower()
        if opening not in {"```", "```json"}:
            continue
        for end_index in range(start_index + 1, len(lines)):
            if lines[end_index].strip() != "```":
                continue
            candidate = "\n".join(lines[start_index + 1 : end_index]).strip()
            if candidate:
                return candidate
            break
    return None


def _extract_completed_tool_output_text(event: dict[str, Any]) -> str | None:
    part = event.get("part")
    if not isinstance(part, dict):
        return None

    state = part.get("state")
    if not isinstance(state, dict) or state.get("status") != "completed":
        return None

    output = state.get("output")
    if not isinstance(output, str) or not output.strip():
        return None

    return output


def _extract_stage_payload(root_payload: dict[str, Any], stage: str) -> Any | None:
    if stage in root_payload:
        return root_payload[stage]

    stage_outputs = root_payload.get("stage_outputs")
    if isinstance(stage_outputs, dict) and stage in stage_outputs:
        return stage_outputs[stage]

    output = root_payload.get("output")
    if isinstance(output, dict):
        named_stage = output.get("stage")
        named_payload = output.get("payload")
        if named_stage == stage and named_payload is not None:
            return named_payload

    if _looks_like_direct_stage_payload(root_payload, stage):
        return root_payload

    return None


def _looks_like_direct_stage_payload(payload: dict[str, Any], stage: str) -> bool:
    if stage == "source_analysis":
        required_key_sets = (
            {
                "author_voice_summary",
                "tone",
                "register",
                "sentence_rhythm",
                "connective_tissue",
                "rhetorical_moves",
                "humor_signals",
                "stance_markers",
                "must_preserve",
            },
        )
    elif stage == "terminology_policy":
        required_key_sets = (
            {
                "keep_english",
                "localize",
                "context_sensitive",
                "do_not_translate",
                "consistency_rules",
                "rationale_notes",
                "resolved_decisions",
            },
        )
    elif stage == "translate":
        required_key_sets = (
            {"title", "excerpt", "tags", "content"},
            {
                "name",
                "tagline",
                "location",
                "contact",
                "skills",
                "languages_spoken",
                "summary",
                "experience",
                "education",
            },
        )
    elif stage == "critique":
        required_key_sets = ({"score", "feedback", "needs_refinement"},)
    elif stage == "revise":
        required_key_sets = (
            {"title", "excerpt", "tags", "content", "applied_feedback"},
            {"revised_cv", "revision_report"},
        )
    elif stage == "final_review":
        required_key_sets = (
            {
                "accept",
                "publish_ready",
                "confidence",
                "residual_issues",
                "voice_score",
                "terminology_score",
                "locale_naturalness_score",
            },
        )
    else:
        return False

    payload_keys = set(payload.keys())
    return any(required_keys.issubset(payload_keys) for required_keys in required_key_sets)


def classify_command_failure(execution: CommandExecutionResult) -> FailureClass:
    """Classify command failures as transient or permanent for retries."""

    transient_exit_codes = {75, 124}
    if execution.exit_code in transient_exit_codes:
        return FailureClass.TRANSIENT

    stderr_text = execution.stderr.lower()
    transient_markers = (
        "timeout",
        "timed out",
        "temporarily unavailable",
        "rate limit",
        "too many requests",
        "connection reset",
        "connection refused",
        "network is unreachable",
        "econnreset",
        "429",
        "503",
    )
    for marker in transient_markers:
        if marker in stderr_text:
            return FailureClass.TRANSIENT

    return FailureClass.PERMANENT


def _stage_result_from_payload(
    *,
    request: TranslationRequest,
    stage: str,
    model: str,
    parsed_output: ParsedStageOutput,
) -> StageResult[ProviderPayload]:
    artifact_type = str(request.metadata.get("artifact_type", "post")).strip().lower()
    if stage == "source_analysis":
        payload = validate_voice_intent_output(
            parsed_output.payload,
            run_id=request.run_id,
            stage=stage,
        )
    elif stage == "terminology_policy":
        payload = validate_terminology_policy_output(
            parsed_output.payload,
            run_id=request.run_id,
            stage=stage,
        )
    elif stage == "translate":
        if artifact_type == "cv":
            payload = validate_cv_translation_output(
                parsed_output.payload,
                run_id=request.run_id,
                stage=stage,
            )
        else:
            payload = validate_translation_output(
                parsed_output.payload,
                run_id=request.run_id,
                stage=stage,
            )
    elif stage == "critique":
        payload = validate_critique_output(
            parsed_output.payload,
            run_id=request.run_id,
            stage=stage,
        )
    elif stage == "revise":
        if artifact_type == "cv":
            payload = validate_cv_revision_output(
                parsed_output.payload,
                run_id=request.run_id,
                stage=stage,
            )
        else:
            payload = validate_revision_output(
                parsed_output.payload,
                run_id=request.run_id,
                stage=stage,
            )
    elif stage == "final_review":
        payload = validate_final_review_output(
            parsed_output.payload,
            run_id=request.run_id,
            stage=stage,
        )
    else:
        raise ValueError(f"Unsupported stage: {stage}")

    return StageResult(
        run_id=request.run_id,
        stage=stage,
        model=model,
        payload=payload,
        raw_response=parsed_output.raw_json,
    )
