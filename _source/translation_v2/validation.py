"""Deterministic validation gates for translation_v2."""

from __future__ import annotations

from typing import Any

from translation_common import validate_translation


def run_integrity_gate(
    *,
    source_text: str,
    translated_text: str,
    source_locale: str,
    target_locale: str,
) -> tuple[bool, list[str]]:
    """Run deterministic structural/integrity checks on translated text."""

    return validate_translation(
        source_text,
        translated_text,
        source_locale=source_locale,
        target_locale=target_locale,
    )


def build_quality_gate_metadata(*, residual_issues: list[str] | None = None) -> dict[str, Any]:
    """Return structured metadata for quality-gate decisions."""

    return {
        "residual_issues": list(residual_issues or []),
        "accepted": len(residual_issues or []) == 0,
    }

