"""Integration test for OpenCode headless runner retries and artifacts.

Run only this suite:
    uv run --extra dev pytest tests/test_opencode_runner.py -q
"""

from __future__ import annotations

import json
import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.artifacts import TranslationRunArtifacts  # noqa: E402
from translation_v2.contracts import TranslationRequest  # noqa: E402
from translation_v2.opencode_runner import (  # noqa: E402
    CommandExecutionResult,
    OpenCodeHeadlessRunner,
)


def test_runner_retries_transient_failure_and_captures_attempt_artifacts(tmp_path):
    responses = [
        {
            "stdout": "",
            "stderr": "rate limit exceeded",
            "exit_code": 75,
        },
        {
            "stdout": json.dumps(
                {
                    "stage_outputs": {
                        "translate": {
                            "title": "Titulo final",
                            "excerpt": "Resumo final",
                            "tags": ["ia", "agentes"],
                            "content": "Conteudo traduzido",
                        }
                    }
                }
            ),
            "stderr": "",
            "exit_code": 0,
        },
    ]
    call_commands: list[list[str]] = []

    def _executor(command: list[str], prompt_text: str) -> CommandExecutionResult:
        index = len(call_commands)
        call_commands.append(command)
        response = responses[index]
        return CommandExecutionResult(
            command=command,
            stdout=response["stdout"],
            stderr=response["stderr"],
            exit_code=response["exit_code"],
        )

    backoff_sleeps: list[float] = []
    runner = OpenCodeHeadlessRunner(
        command_executor=_executor,
        sleep_fn=backoff_sleeps.append,
    )
    artifacts = TranslationRunArtifacts(run_id="runner-test-run", base_dir=tmp_path)
    request = TranslationRequest(
        run_id="runner-test-run",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="Hello world",
        prompt_version="opencode-v2",
    )

    result = runner.run_stage(
        request=request,
        post_slug="runner-post",
        stage="translate",
        prompt_text="Translate this content",
        attach_path="/tmp/source.md",
        artifacts=artifacts,
    )

    assert result.model == "openai/gpt-5.4"
    assert result.stage == "translate"
    assert result.payload.title == "Titulo final"
    assert len(call_commands) == 2
    assert backoff_sleeps == [1.0]

    first_command = call_commands[0]
    assert first_command == [
        "opencode",
        "run",
        "--model",
        "openai/gpt-5.4",
        "--file",
        "/tmp/source.md",
        "--format",
        "json",
    ]

    stage_dir = artifacts.stage_dir("runner-post", "translate")
    attempt1 = json.loads((stage_dir / "runner-attempt-1.json").read_text("utf-8"))
    attempt2 = json.loads((stage_dir / "runner-attempt-2.json").read_text("utf-8"))

    assert attempt1["command"] == first_command
    assert attempt1["exit_code"] == 75
    assert attempt1["failure_classification"] == "transient"
    assert attempt1["parsed_stage_output"] is None

    assert attempt2["exit_code"] == 0
    assert attempt2["failure_classification"] is None
    assert attempt2["parsed_stage_output"]["stage"] == "translate"
    assert attempt2["parsed_stage_output"]["payload"]["title"] == "Titulo final"


def test_runner_passes_prompt_via_stdin_not_argv(tmp_path):
    captured_prompt_texts: list[str] = []
    captured_commands: list[list[str]] = []

    def _executor(command: list[str], prompt_text: str) -> CommandExecutionResult:
        captured_commands.append(command)
        captured_prompt_texts.append(prompt_text)
        return CommandExecutionResult(
            command=command,
            stdout=json.dumps(
                {
                    "stage_outputs": {
                        "translate": {
                            "title": "Titulo final",
                            "excerpt": "Resumo final",
                            "tags": ["ia"],
                            "content": "Conteudo traduzido",
                        }
                    }
                }
            ),
            stderr="",
            exit_code=0,
        )

    runner = OpenCodeHeadlessRunner(command_executor=_executor)
    artifacts = TranslationRunArtifacts(run_id="runner-stdin", base_dir=tmp_path)
    request = TranslationRequest(
        run_id="runner-stdin",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="Hello world",
        prompt_version="v1",
    )
    prompt_text = "Translate this content with a long body " + ("x" * 10_000)

    result = runner.run_stage(
        request=request,
        post_slug="runner-post",
        stage="translate",
        prompt_text=prompt_text,
        attach_path="/tmp/source.md",
        artifacts=artifacts,
    )

    assert result.payload.title == "Titulo final"
    assert captured_prompt_texts == [prompt_text]
    assert captured_commands == [
        [
            "opencode",
            "run",
            "--model",
        "openai/gpt-5.4",
            "--file",
            "/tmp/source.md",
            "--format",
            "json",
        ]
    ]


def test_runner_parses_json_event_stream_text_payload(tmp_path):
    event_stream = "\n".join(
        [
            json.dumps(
                {
                    "type": "step_start",
                    "part": {"type": "step-start"},
                }
            ),
            json.dumps(
                {
                    "type": "text",
                    "part": {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "stage_outputs": {
                                    "translate": {
                                        "title": "Titulo final",
                                        "excerpt": "Resumo final",
                                        "tags": ["ia"],
                                        "content": "Conteudo traduzido",
                                    }
                                }
                            }
                        ),
                    },
                }
            ),
            json.dumps(
                {
                    "type": "step_finish",
                    "part": {"type": "step-finish", "reason": "stop"},
                }
            ),
        ]
    )

    def _executor(command: list[str], prompt_text: str) -> CommandExecutionResult:  # noqa: ARG001
        return CommandExecutionResult(
            command=command,
            stdout=event_stream,
            stderr="",
            exit_code=0,
        )

    runner = OpenCodeHeadlessRunner(command_executor=_executor)
    artifacts = TranslationRunArtifacts(run_id="runner-event-stream", base_dir=tmp_path)
    request = TranslationRequest(
        run_id="runner-event-stream",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="Hello world",
        prompt_version="v1",
    )

    result = runner.run_stage(
        request=request,
        post_slug="runner-post",
        stage="translate",
        prompt_text="Translate this content",
        attach_path="/tmp/source.md",
        artifacts=artifacts,
    )

    assert result.payload.title == "Titulo final"
    assert result.payload.content == "Conteudo traduzido"


def test_runner_ignores_commentary_text_and_uses_final_answer_json(tmp_path):
    event_stream = "\n".join(
        [
            json.dumps({"type": "step_start", "part": {"type": "step-start"}}),
            json.dumps(
                {
                    "type": "text",
                    "part": {
                        "type": "text",
                        "text": "Vou ler o post original antes de traduzir.",
                        "metadata": {"openai": {"phase": "commentary"}},
                    },
                }
            ),
            json.dumps(
                {
                    "type": "tool_use",
                    "part": {"type": "tool"},
                }
            ),
            json.dumps(
                {
                    "type": "text",
                    "part": {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "title": "Titulo final",
                                "excerpt": "Resumo final",
                                "tags": ["ia"],
                                "content": "Conteudo traduzido",
                            }
                        ),
                        "metadata": {"openai": {"phase": "final_answer"}},
                    },
                }
            ),
            json.dumps({"type": "step_finish", "part": {"type": "step-finish"}}),
        ]
    )

    def _executor(command: list[str], prompt_text: str) -> CommandExecutionResult:  # noqa: ARG001
        return CommandExecutionResult(
            command=command,
            stdout=event_stream,
            stderr="",
            exit_code=0,
        )

    runner = OpenCodeHeadlessRunner(command_executor=_executor)
    artifacts = TranslationRunArtifacts(run_id="runner-commentary-stream", base_dir=tmp_path)
    request = TranslationRequest(
        run_id="runner-commentary-stream",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="Hello world",
        prompt_version="v1",
    )

    result = runner.run_stage(
        request=request,
        post_slug="runner-post",
        stage="translate",
        prompt_text="Translate this content",
        attach_path="/tmp/source.md",
        artifacts=artifacts,
    )

    assert result.payload.title == "Titulo final"
    assert result.payload.content == "Conteudo traduzido"


def test_runner_accepts_direct_stage_payload_without_wrapper(tmp_path):
    event_stream = "\n".join(
        [
            json.dumps({"type": "step_start", "part": {"type": "step-start"}}),
            json.dumps(
                {
                    "type": "text",
                    "part": {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "title": "Titulo final",
                                "excerpt": "Resumo final",
                                "tags": ["ia"],
                                "content": "Conteudo traduzido",
                            }
                        ),
                    },
                }
            ),
            json.dumps({"type": "step_finish", "part": {"type": "step-finish"}}),
        ]
    )

    def _executor(command: list[str], prompt_text: str) -> CommandExecutionResult:  # noqa: ARG001
        return CommandExecutionResult(
            command=command,
            stdout=event_stream,
            stderr="",
            exit_code=0,
        )

    runner = OpenCodeHeadlessRunner(command_executor=_executor)
    artifacts = TranslationRunArtifacts(run_id="runner-direct-payload", base_dir=tmp_path)
    request = TranslationRequest(
        run_id="runner-direct-payload",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="Hello world",
        prompt_version="v1",
    )

    result = runner.run_stage(
        request=request,
        post_slug="runner-post",
        stage="translate",
        prompt_text="Translate this content",
        attach_path="/tmp/source.md",
        artifacts=artifacts,
    )

    assert result.payload.title == "Titulo final"


def test_runner_accepts_direct_cv_stage_payload_without_wrapper(tmp_path):
    event_stream = "\n".join(
        [
            json.dumps({"type": "step_start", "part": {"type": "step-start"}}),
            json.dumps(
                {
                    "type": "text",
                    "part": {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "name": "Daniel Cavalli",
                                "tagline": "Engenheiro de ML",
                                "location": "Rio de Janeiro, Brazil",
                                "contact": {
                                    "email": "daniel@cavalli.dev",
                                    "linkedin": "cavallidaniel",
                                    "github": "danielcavalli",
                                    "phone": "+55(21)985979780",
                                },
                                "skills": ["Kubeflow"],
                                "languages_spoken": ["Portuguese", "English"],
                                "summary": "Resumo",
                                "experience": [
                                    {
                                        "title": "Senior Machine Learning Engineer",
                                        "company": "Nubank",
                                        "location": "Brazil",
                                        "period": "2026 - Present",
                                        "description": "Descricao",
                                        "achievements": ["Entrega importante"],
                                    }
                                ],
                                "education": [
                                    {
                                        "degree": "Bacharelado em Economia",
                                        "school": "Federal University of Rio de Janeiro",
                                        "period": "2017 - 2023",
                                    }
                                ],
                            }
                        ),
                    },
                }
            ),
            json.dumps({"type": "step_finish", "part": {"type": "step-finish"}}),
        ]
    )

    def _executor(command: list[str], prompt_text: str) -> CommandExecutionResult:  # noqa: ARG001
        return CommandExecutionResult(
            command=command,
            stdout=event_stream,
            stderr="",
            exit_code=0,
        )

    runner = OpenCodeHeadlessRunner(command_executor=_executor)
    artifacts = TranslationRunArtifacts(run_id="runner-direct-cv-payload", base_dir=tmp_path)
    request = TranslationRequest(
        run_id="runner-direct-cv-payload",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="{}",
        prompt_version="v1",
        metadata={"artifact_type": "cv"},
    )

    result = runner.run_stage(
        request=request,
        post_slug="cv",
        stage="translate",
        prompt_text="Translate this CV",
        attach_path="/tmp/cv.yaml",
        artifacts=artifacts,
    )

    assert result.payload.name == "Daniel Cavalli"
    assert result.payload.contact["phone"] == "+55(21)985979780"
    assert result.payload.experience[0].company == "Nubank"
