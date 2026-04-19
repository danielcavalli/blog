"""Structured run logging for translation_v2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any


REQUIRED_EVENT_FIELDS = (
    "run_id",
    "post_slug",
    "stage",
    "attempt",
    "model",
    "duration_ms",
    "outcome",
)


@dataclass(slots=True)
class BuildSummaryCounters:
    """Concise counters for build-level translation outcomes."""

    cache_hit: int = 0
    cache_miss: int = 0
    retries: int = 0
    failures: int = 0

    def increment_cache_hit(self) -> None:
        self.cache_hit += 1

    def increment_cache_miss(self) -> None:
        self.cache_miss += 1

    def increment_retries(self, count: int = 1) -> None:
        self.retries += count

    def increment_failures(self, count: int = 1) -> None:
        self.failures += count

    def as_dict(self) -> dict[str, int]:
        return {
            "cache_hit": self.cache_hit,
            "cache_miss": self.cache_miss,
            "retries": self.retries,
            "failures": self.failures,
        }

    def to_summary_line(self) -> str:
        return (
            "translation_summary "
            f"cache_hit={self.cache_hit} "
            f"cache_miss={self.cache_miss} "
            f"retries={self.retries} "
            f"failures={self.failures}"
        )


class TranslationRunEventLogger:
    """Writes JSONL stage events for translation runs."""

    def __init__(self, run_id: str, base_dir: str | Path = "_cache/translation-runs"):
        self.run_id = run_id
        self.base_dir = Path(base_dir)
        self.run_dir = self.base_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.run_dir / "stage-events.jsonl"

    def emit_stage_event(
        self,
        *,
        post_slug: str,
        stage: str,
        attempt: int,
        model: str,
        duration_ms: int,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "ts": int(time() * 1000),
            "run_id": self.run_id,
            "post_slug": post_slug,
            "stage": stage,
            "attempt": attempt,
            "model": model,
            "duration_ms": duration_ms,
            "outcome": outcome,
        }
        if metadata:
            event["metadata"] = metadata
        self._append_jsonl(event)
        return event

    def _append_jsonl(self, payload: dict[str, Any]) -> None:
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def event_has_required_schema(event: dict[str, Any]) -> bool:
    """Check if an event dictionary has all required schema fields."""

    return all(field in event for field in REQUIRED_EVENT_FIELDS)
