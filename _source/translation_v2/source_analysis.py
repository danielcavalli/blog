"""Context builders for the source-analysis stage."""

from __future__ import annotations

import json

from .contracts import TranslationRequest
from .voice_profile import AuthorVoiceProfile


def build_source_analysis_context(
    request: TranslationRequest,
    *,
    voice_profile: AuthorVoiceProfile,
    writing_style_brief: str,
    style_constraints: list[str],
    glossary_entries: list[str] | list[object],
    do_not_translate_entities: list[str],
) -> dict[str, str]:
    """Build prompt context for source-analysis."""

    metadata = request.metadata
    frontmatter = {
        "title": metadata.get("title", ""),
        "excerpt": metadata.get("excerpt", ""),
        "tags": metadata.get("tags", []),
    }
    return {
        "source_locale": request.source_locale,
        "target_locale": request.target_locale,
        "locale_direction": str(metadata.get("locale_direction", "")),
        "frontmatter_json": json.dumps(frontmatter, ensure_ascii=False, sort_keys=True, indent=2),
        "writing_style_brief": writing_style_brief,
        "author_voice_profile": voice_profile.brief,
        "style_constraints": _render_bullets(style_constraints),
        "glossary_entries": _render_glossary(glossary_entries),
        "do_not_translate_entities": _render_bullets(do_not_translate_entities),
        "source_markdown": request.source_text,
    }


def _render_bullets(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return "- none"
    return "\n".join(f"- {item}" for item in cleaned)


def _render_glossary(entries: list[str] | list[object]) -> str:
    rendered: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            source = str(entry.get("source", "")).strip()
            target = str(entry.get("target", "")).strip()
            if source and target:
                rendered.append(f"- {source} => {target}")
                continue
        cleaned = str(entry).strip()
        if cleaned:
            rendered.append(f"- {cleaned}")
    if not rendered:
        return "- none"
    return "\n".join(rendered)
