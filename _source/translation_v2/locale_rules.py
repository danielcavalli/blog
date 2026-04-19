"""Locale-pair defaults for translation prompt context."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


LocaleRules = dict[str, Any]
_REFERENCES_ROOT = Path(__file__).with_name("references")


def _load_reference(filename: str) -> str:
    path = _REFERENCES_ROOT / filename
    return path.read_text(encoding="utf-8").strip()


_EN_US_TO_PT_BR: LocaleRules = {
    "style_constraints": [
        "Localize for Brazilian Portuguese readership; do not mirror English sentence order just because the meaning is recoverable.",
        "Preserve the author's voice, argumentative pressure, caveats, humor, and connective logic instead of flattening them into generic explanatory prose.",
        "Rewrite idioms, metaphors, and discourse moves idiomatically in PT-BR; preserve effect and meaning, not English imagery.",
        "If a sentence sounds imported from English, rewrite it fully in natural Brazilian Portuguese instead of patching individual words.",
        "Keep a serious technical-editorial tone: clear, precise, credible, and readable, without sounding bureaucratic or translated.",
        "Apply borrowing decisions artifact-wide. Do not oscillate between English and Portuguese renderings for the same concept without an explicit contextual reason.",
        "Normalize punctuation, clause order, and connective phrasing to PT-BR editorial usage.",
        "Keep technical precision and implementation detail; do not add claims not present in the source.",
        "Preserve markdown structure exactly, including headings, lists, tables, blockquotes, and protected spans.",
    ],
    "glossary": [
        {"source": "throughput", "target": "vazão"},
        {"source": "latency", "target": "latência"},
        {"source": "fine-tuning", "target": "ajuste fino"},
        {"source": "prompt engineering", "target": "engenharia de prompts"},
        {"source": "feature flag", "target": "feature flag"},
        {"source": "rollout", "target": "rollout"},
        {"source": "rollback", "target": "rollback"},
        {"source": "observability", "target": "observabilidade"},
        {"source": "dataset", "target": "conjunto de dados"},
        {"source": "cache invalidation", "target": "invalidação de cache"},
        {"source": "benchmark", "target": "benchmark"},
        {"source": "runbook", "target": "runbook"},
    ],
    "do_not_translate_entities": [
        "OpenCode",
        "CUDA",
        "Kubernetes",
        "Docker",
        "PostgreSQL",
        "Redis",
        "OpenAPI",
        "RFC 9110",
        "GitHub Actions",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "README.md",
        "/etc/nginx/nginx.conf",
    ],
    "localization_brief": _load_reference("pt_br_localization_brief.md"),
    "borrowing_conventions": [
        "Treat English borrowings as a policy problem, not a token-by-token whim.",
        "Keep established technical borrowings in English when that is what Brazilian technical readers expect.",
        "Localize terms that are naturally written in Portuguese in serious Brazilian technical prose.",
        "Keep product names, branded platforms, and unmistakable identifiers exactly as named in the source.",
        "When a term is context-sensitive, decide once per artifact and apply the decision consistently.",
    ],
    "punctuation_conventions": [
        "Prefer PT-BR clause rhythm and punctuation over copied English pauses.",
        "Use the travessão correctly when you need an inciso; do not substitute a hyphen for it.",
        "Do not place a comma before the opening travessão in parenthetical structures.",
        "Avoid overusing travessões when commas, parênteses, or sentence recasting would read more naturally.",
        "Use commas according to Portuguese syntax and explanatory structure, not English pacing habits.",
    ],
    "discourse_conventions": [
        "Rebuild connective tissue in PT-BR instead of preserving English clause sequencing mechanically.",
        "Let concessive, contrastive, and causal movement sound like authored Brazilian prose.",
        "Prefer paragraph and sentence movement that a Brazilian technical writer would naturally publish.",
        "Preserve the author's layered argument structure, not only the facts carried by each sentence.",
    ],
    "register_conventions": [
        "Use contemporary Brazilian technical-editorial prose, not bureaucratic officialese.",
        "Keep the register serious and credible without sounding stiff or inflated.",
        "Preserve the author's restraint, confidence, and dry humor where present.",
        "Do not neutralize strong opinions into generic informational language.",
    ],
    "review_checks": [
        "Flag literal calques, especially when the wording sounds understandable but socially wrong in PT-BR.",
        "Flag inconsistent English borrowings across title, headings, body, tags, and summary fields.",
        "Flag imported English punctuation or clause movement that makes the prose feel translated.",
        "Flag flattened rhetoric, lost connective texture, or disappearance of understated humor or soft disagreement.",
        "Flag PT-BR that is grammatical but not publishable as native Brazilian technical writing.",
    ],
}


_PT_BR_TO_EN_US: LocaleRules = {
    "style_constraints": [
        "Prefer idiomatic US English over literal Portuguese structure.",
        "Rewrite idioms, metaphors, and discourse patterns naturally in US English; preserve function rather than Portuguese imagery.",
        "If a sentence sounds carried over from Portuguese, rewrite it fully in idiomatic US English instead of following the source syntax.",
        "Keep a practical engineering blog tone with direct phrasing and intact nuance.",
        "Normalize punctuation and capitalization to US English conventions.",
        "Keep technical precision; do not simplify away implementation details.",
        "Preserve markdown structure exactly, including headings and lists.",
    ],
    "glossary": [
        {"source": "vazão", "target": "throughput"},
        {"source": "latência", "target": "latency"},
        {"source": "ajuste fino", "target": "fine-tuning"},
        {"source": "engenharia de prompts", "target": "prompt engineering"},
        {"source": "sinalizador de recurso", "target": "feature flag"},
        {"source": "implantação", "target": "deployment"},
        {"source": "reversão", "target": "rollback"},
        {"source": "observabilidade", "target": "observability"},
        {"source": "conjunto de dados", "target": "dataset"},
        {"source": "invalidação de cache", "target": "cache invalidation"},
        {"source": "teste de carga", "target": "load test"},
        {"source": "guia operacional", "target": "runbook"},
    ],
    "do_not_translate_entities": [
        "OpenCode",
        "CUDA",
        "Kubernetes",
        "Docker",
        "PostgreSQL",
        "Redis",
        "OpenAPI",
        "RFC 9110",
        "GitHub Actions",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "README.md",
        "/etc/nginx/nginx.conf",
    ],
    "localization_brief": _load_reference("en_us_localization_brief.md"),
    "borrowing_conventions": [
        "Keep established English technical terms in their expected US form.",
        "Translate PT-BR-specific labels into the idiomatic term an English technical reader would expect.",
        "Do not preserve Portuguese lexical choices when a standard US English term is clearly preferred.",
    ],
    "punctuation_conventions": [
        "Normalize clause rhythm and punctuation to US English editorial usage.",
        "Prefer commas, em dashes, and sentence breaks in their natural US English roles rather than copied Portuguese punctuation.",
    ],
    "discourse_conventions": [
        "Rebuild connective movement so the prose reads as written in English, not translated from Portuguese.",
        "Preserve layered argument structure, but let sentence flow follow idiomatic US English sequencing.",
    ],
    "register_conventions": [
        "Keep the voice technical, direct, and publishable for an English-speaking technical audience.",
        "Preserve confidence, understatement, and rhetorical layering without sounding bureaucratic or machine-translated.",
    ],
    "review_checks": [
        "Flag Portuguese-influenced syntax that remains grammatically understandable but reads translated.",
        "Flag terminology inconsistency, register drift, or over-literal borrowings.",
    ],
}


_RULES_BY_DIRECTION: dict[tuple[str, str], LocaleRules] = {
    ("en-us", "pt-br"): _EN_US_TO_PT_BR,
    ("pt-br", "en-us"): _PT_BR_TO_EN_US,
}


def get_default_locale_rules(*, source_locale: str, target_locale: str) -> LocaleRules:
    """Return locale-pair defaults for known directions, otherwise empty defaults."""

    key = (source_locale.strip().lower(), target_locale.strip().lower())
    rules = _RULES_BY_DIRECTION.get(key)
    if rules is None:
        return {
            "style_constraints": [],
            "glossary": [],
            "do_not_translate_entities": [],
            "localization_brief": "",
            "borrowing_conventions": [],
            "punctuation_conventions": [],
            "discourse_conventions": [],
            "register_conventions": [],
            "review_checks": [],
        }

    copied: LocaleRules = {}
    for key_name, value in rules.items():
        if isinstance(value, str):
            copied[key_name] = value
        else:
            copied[key_name] = deepcopy(value)
    return copied
