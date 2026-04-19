"""Artifact persistence helpers for translation_v2 runs."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {"api_key", "authorization", "token", "secret", "password"}


def _sanitize_slug(slug: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in slug)


class TranslationRunArtifacts:
    """Persists prompts, responses, errors, and runner logs per run."""

    def __init__(self, run_id: str, base_dir: str | Path = "_cache/translation-runs"):
        self.run_id = run_id
        self.base_dir = Path(base_dir)
        self.run_dir = self.base_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def stage_dir(self, post_slug: str, stage: str) -> Path:
        slug = _sanitize_slug(post_slug)
        stage_path = self.run_dir / "posts" / slug / stage
        stage_path.mkdir(parents=True, exist_ok=True)
        return stage_path

    def write_prompt(
        self,
        post_slug: str,
        stage: str,
        prompt_text: str,
        *,
        prompt_version: str | None = None,
        prompt_fingerprint: str | None = None,
    ) -> Path:
        path = self.stage_dir(post_slug, stage) / "prompt.txt"
        path.write_text(prompt_text, encoding="utf-8")
        if prompt_version is not None or prompt_fingerprint is not None:
            metadata: dict[str, str] = {}
            if prompt_version is not None:
                metadata["prompt_version"] = prompt_version
            if prompt_fingerprint is not None:
                metadata["prompt_fingerprint"] = prompt_fingerprint
            metadata_path = self.stage_dir(post_slug, stage) / "prompt-metadata.json"
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8"
            )
        return path

    def write_structured_response(
        self, post_slug: str, stage: str, response: dict[str, Any]
    ) -> Path:
        sanitized = _redact_sensitive_fields(response)
        path = self.stage_dir(post_slug, stage) / "structured-response.json"
        path.write_text(json.dumps(sanitized, ensure_ascii=True, indent=2), encoding="utf-8")
        return path

    def write_error(self, post_slug: str, stage: str, error_message: str) -> Path:
        path = self.stage_dir(post_slug, stage) / "error.txt"
        path.write_text(error_message, encoding="utf-8")
        return path

    def write_runner_stdout(self, post_slug: str, stage: str, stdout_text: str) -> Path:
        path = self.stage_dir(post_slug, stage) / "runner-stdout.log"
        path.write_text(stdout_text, encoding="utf-8")
        return path

    def write_runner_stderr(self, post_slug: str, stage: str, stderr_text: str) -> Path:
        path = self.stage_dir(post_slug, stage) / "runner-stderr.log"
        path.write_text(stderr_text, encoding="utf-8")
        return path

    def write_runner_attempt(
        self, post_slug: str, stage: str, attempt: int, artifact: dict[str, Any]
    ) -> Path:
        path = self.stage_dir(post_slug, stage) / f"runner-attempt-{attempt}.json"
        path.write_text(
            json.dumps(_redact_sensitive_fields(artifact), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        return path

    def write_trigger_event(self, post_slug: str, event_payload: Any) -> Path:
        stage_path = self.stage_dir(post_slug, "trigger")
        path = stage_path / "event.json"
        serializable: Any = event_payload
        if is_dataclass(event_payload) and not isinstance(event_payload, type):
            serializable = asdict(event_payload)
        path.write_text(
            json.dumps(_redact_sensitive_fields(serializable), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        return path


def _redact_sensitive_fields(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            if key.lower() in SENSITIVE_KEYS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact_sensitive_fields(nested)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive_fields(item) for item in value]
    return value
