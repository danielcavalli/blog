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
    localization_brief: str,
    borrowing_conventions: list[str],
    punctuation_conventions: list[str],
    discourse_conventions: list[str],
    register_conventions: list[str],
    review_checks: list[str],
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
        "localization_brief": _render_text_block(localization_brief),
        "borrowing_conventions": _render_bullets(borrowing_conventions),
        "punctuation_conventions": _render_bullets(punctuation_conventions),
        "discourse_conventions": _render_bullets(discourse_conventions),
        "register_conventions": _render_bullets(register_conventions),
        "review_checks": _render_bullets(review_checks),
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
    localization_brief: str,
    borrowing_conventions: list[str],
    punctuation_conventions: list[str],
    discourse_conventions: list[str],
    register_conventions: list[str],
    review_checks: list[str],
    writing_style_brief: str,
) -> dict[str, str]:
    """Build common translation/critique/revise/final-review prompt context."""

    merged_do_not_translate = list(dict.fromkeys(do_not_translate_entities + terminology_policy.do_not_translate))
    return {
        "source_locale": request.source_locale,
        "target_locale": request.target_locale,
        "locale_direction": str(request.metadata.get("locale_direction", "")),
        "style_constraints": _render_bullets(style_constraints),
        "localization_brief": _render_text_block(localization_brief),
        "borrowing_conventions": _render_bullets(borrowing_conventions),
        "punctuation_conventions": _render_bullets(punctuation_conventions),
        "discourse_conventions": _render_bullets(discourse_conventions),
        "register_conventions": _render_bullets(register_conventions),
        "review_checks": _render_bullets(review_checks),
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
        "resolved_terminology_decisions_json": json.dumps(
            [
                {
                    "source_term": decision.source_term,
                    "preferred_rendering": decision.preferred_rendering,
                    "decision_type": decision.decision_type,
                    "scope": decision.scope,
                    "rationale": decision.rationale,
                    "applies_to": decision.applies_to,
                }
                for decision in terminology_policy.resolved_decisions
            ],
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        "education_degree_localization_policy_json": json.dumps(
            (
                {
                    "decision": terminology_policy.education_degree_localization_policy.decision,
                    "apply_consistently": terminology_policy.education_degree_localization_policy.apply_consistently,
                    "rule": terminology_policy.education_degree_localization_policy.rule,
                    "exceptions": [
                        {
                            "source_degree": exception.source_degree,
                            "approved_rendering": exception.approved_rendering,
                            "reason": exception.reason,
                        }
                        for exception in terminology_policy.education_degree_localization_policy.exceptions
                    ],
                }
                if terminology_policy.education_degree_localization_policy is not None
                else {}
            ),
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


def _render_text_block(value: str) -> str:
    cleaned = value.strip()
    return cleaned or "- none"


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
        "resolved_decisions": [
            {
                "source_term": decision.source_term,
                "preferred_rendering": decision.preferred_rendering,
                "decision_type": decision.decision_type,
                "scope": decision.scope,
                "rationale": decision.rationale,
                "applies_to": decision.applies_to,
            }
            for decision in packet.resolved_decisions
        ],
        "education_degree_localization_policy": (
            {
                "decision": packet.education_degree_localization_policy.decision,
                "apply_consistently": packet.education_degree_localization_policy.apply_consistently,
                "rule": packet.education_degree_localization_policy.rule,
                "exceptions": [
                    {
                        "source_degree": exception.source_degree,
                        "approved_rendering": exception.approved_rendering,
                        "reason": exception.reason,
                    }
                    for exception in packet.education_degree_localization_policy.exceptions
                ],
            }
            if packet.education_degree_localization_policy is not None
            else None
        ),
    }
