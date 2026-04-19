"""Helpers for loading the committed writing style brief."""

from __future__ import annotations

import hashlib
from pathlib import Path

from paths import PROJECT_ROOT


STYLE_BRIEF_PATH = PROJECT_ROOT / "WRITING_STYLE.md"
DEFAULT_STYLE_BRIEF = (
    "Opinionated, layered, structurally aware, dry. Preserve connective tissue, "
    "argument flow, and understated humor without signaling jokes explicitly."
)


def load_writing_style_brief(path: str | Path = STYLE_BRIEF_PATH) -> str:
    """Load the committed writing style brief used by translation prompts."""

    style_path = Path(path)
    try:
        content = style_path.read_text(encoding="utf-8").strip()
    except OSError:
        return DEFAULT_STYLE_BRIEF
    return content or DEFAULT_STYLE_BRIEF


def compute_writing_style_fingerprint(style_brief: str) -> str:
    """Compute a deterministic fingerprint for a style brief payload."""

    return hashlib.sha256(style_brief.encode("utf-8")).hexdigest()
