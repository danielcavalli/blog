"""Helpers for loading the committed writing style brief."""

from __future__ import annotations

import hashlib
from pathlib import Path

from paths import PROJECT_ROOT


STYLE_BRIEF_PATH = PROJECT_ROOT / ".agents/skills/writing-style/references/WRITING_STYLE.md"
AUTHORING_REFERENCES = (
    ("Blog composition", PROJECT_ROOT / ".agents/skills/editorial-line/references/blog-composition.md"),
    ("Prose", PROJECT_ROOT / ".agents/skills/prose-style/references/prose-contract.md"),
    ("Author voice", STYLE_BRIEF_PATH),
)


def load_writing_style_brief(path: str | Path | None = None) -> str:
    """Read authoring context once; missing guidance must not weaken localization."""
    references = (("Author voice", Path(path)),) if path is not None else AUTHORING_REFERENCES
    sections = []
    for label, reference in references:
        content = reference.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"Empty authoring reference: {reference}")
        sections.append(f"## {label}\n\n{content}")
    return "\n\n".join(sections)


def compute_writing_style_fingerprint(style_brief: str) -> str:
    """Compute a deterministic fingerprint for a style brief payload."""

    return hashlib.sha256(style_brief.encode("utf-8")).hexdigest()
