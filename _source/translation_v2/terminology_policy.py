"""Terminology and borrowing policy helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .contracts import TerminologyPolicyPacket, TranslationRequest, VoiceIntentPacket


def build_terminology_policy_context(
    request: TranslationRequest,
    *,
    source_analysis: VoiceIntentPacket,
    glossary_entries: list[Any],
    do_not_translate_entities: list[str],
    style_constraints: list[str],
) -> dict[str, str]:
    """Build prompt context for terminology and borrowing analysis."""

    return {
        "source_locale": request.source_locale,
        "target_locale": request.target_locale,
        "locale_direction": str(request.metadata.get("locale_direction", "")),
        "source_analysis_json": json.dumps(
            _voice_packet_dict(source_analysis),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        "glossary_entries": _render_glossary(glossary_entries),
        "do_not_translate_entities": _render_bullets(do_not_translate_entities),
        "style_constraints": _render_bullets(style_constraints),
        "source_markdown": request.source_text,
    }


def build_translation_policy_context(
    request: TranslationRequest,
    *,
    source_analysis: VoiceIntentPacket,
    terminology_policy: TerminologyPolicyPacket,
    glossary_entries: list[Any],
    do_not_translate_entities: list[str],
    style_constraints: list[str],
    writing_style_brief: str,
) -> dict[str, str]:
    """Build common translation/critique/revise/final-review prompt context."""

    merged_do_not_translate = list(dict.fromkeys(do_not_translate_entities + terminology_policy.do_not_translate))
    return {
        "source_locale": request.source_locale,
        "target_locale": request.target_locale,
        "locale_direction": str(request.metadata.get("locale_direction", "")),
        "style_constraints": _render_bullets(style_constraints),
        "writing_style_brief": writing_style_brief,
        "glossary_entries": _render_glossary(glossary_entries),
        "do_not_translate_entities": _render_bullets(merged_do_not_translate),
        "source_analysis_json": json.dumps(
            _voice_packet_dict(source_analysis),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        "terminology_policy_json": json.dumps(
            _terminology_packet_dict(terminology_policy),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        "source_markdown": request.source_text,
    }


def _render_bullets(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return "- none"
    return "\n".join(f"- {item}" for item in cleaned)


def _render_glossary(entries: list[Any]) -> str:
    rendered: list[str] = []
    for entry in entries:
        if isinstance(entry, Mapping):
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


def _voice_packet_dict(packet: VoiceIntentPacket) -> dict[str, Any]:
    return {
        "author_voice_summary": packet.author_voice_summary,
        "tone": packet.tone,
        "register": packet.register,
        "sentence_rhythm": packet.sentence_rhythm,
        "connective_tissue": packet.connective_tissue,
        "rhetorical_moves": packet.rhetorical_moves,
        "humor_signals": packet.humor_signals,
        "stance_markers": packet.stance_markers,
        "must_preserve": packet.must_preserve,
    }


def _terminology_packet_dict(packet: TerminologyPolicyPacket) -> dict[str, Any]:
    return {
        "keep_english": packet.keep_english,
        "localize": packet.localize,
        "context_sensitive": packet.context_sensitive,
        "do_not_translate": packet.do_not_translate,
        "consistency_rules": packet.consistency_rules,
        "rationale_notes": packet.rationale_notes,
    }

