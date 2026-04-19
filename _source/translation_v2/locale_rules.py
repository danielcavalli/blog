"""Locale-pair defaults for translation prompt context."""

from __future__ import annotations

from typing import Any


LocaleRules = dict[str, list[Any]]


_EN_US_TO_PT_BR: LocaleRules = {
    "style_constraints": [
        "Prefer natural PT-BR wording over literal English word order.",
        "Rewrite idioms, metaphors, and discourse patterns idiomatically in PT-BR; preserve meaning, not English imagery.",
        "If a sentence sounds like translated English, rewrite it fully in natural Brazilian Portuguese instead of mirroring the source structure.",
        "Do not calque expressions literally; choose the phrasing a native Brazilian technical writer would actually use.",
        "Keep a practical engineering blog tone with concise sentences.",
        "Use second-person neutral register consistently across the text.",
        "Translate UI and operational verbs consistently in imperative instructions.",
        "Keep technical precision; avoid adding claims not present in the source.",
        "Preserve markdown structure exactly, including headings and lists.",
    ],
    "glossary": [
        {"source": "throughput", "target": "vazao"},
        {"source": "latency", "target": "latencia"},
        {"source": "fine-tuning", "target": "ajuste fino"},
        {"source": "prompt engineering", "target": "engenharia de prompts"},
        {"source": "feature flag", "target": "feature flag"},
        {"source": "rollout", "target": "rollout"},
        {"source": "rollback", "target": "rollback"},
        {"source": "observability", "target": "observabilidade"},
        {"source": "dataset", "target": "conjunto de dados"},
        {"source": "cache invalidation", "target": "invalidacao de cache"},
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
}


_PT_BR_TO_EN_US: LocaleRules = {
    "style_constraints": [
        "Prefer idiomatic US English over literal Portuguese structure.",
        "Rewrite idioms and figurative language naturally in US English; preserve meaning instead of preserving Portuguese imagery.",
        "If a sentence sounds like translated Portuguese, rewrite it fully in idiomatic US English instead of following the source syntax.",
        "Keep a practical engineering blog tone with direct phrasing.",
        "Use active voice and concise clauses when possible.",
        "Normalize punctuation and capitalization to US English conventions.",
        "Keep technical precision; do not simplify away implementation details.",
        "Preserve markdown structure exactly, including headings and lists.",
    ],
    "glossary": [
        {"source": "vazao", "target": "throughput"},
        {"source": "latencia", "target": "latency"},
        {"source": "ajuste fino", "target": "fine-tuning"},
        {"source": "engenharia de prompts", "target": "prompt engineering"},
        {"source": "sinalizador de recurso", "target": "feature flag"},
        {"source": "implantacao", "target": "deployment"},
        {"source": "reversao", "target": "rollback"},
        {"source": "observabilidade", "target": "observability"},
        {"source": "conjunto de dados", "target": "dataset"},
        {"source": "invalidacao de cache", "target": "cache invalidation"},
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
        }

    return {
        "style_constraints": list(rules["style_constraints"]),
        "glossary": [
            dict(entry) if isinstance(entry, dict) else entry for entry in rules["glossary"]
        ],
        "do_not_translate_entities": list(rules["do_not_translate_entities"]),
    }
