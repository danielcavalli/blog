"""Provider-neutral translation validation and sanitization helpers."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


TECH_GLOSSARY: set[str] = {
    "machine learning",
    "deep learning",
    "data science",
    "mlops",
    "training",
    "inference",
    "model",
    "dataset",
    "benchmark",
    "feature",
    "batch",
    "streaming",
    "transformer",
    "fine-tuning",
    "cuda",
    "gpu",
    "cpu",
    "kernel",
    "runtime",
    "hardware",
    "software",
    "thread",
    "overhead",
    "docker",
    "kubernetes",
    "cloud",
    "deploy",
    "pipeline",
    "backend",
    "frontend",
    "full-stack",
    "serverless",
    "microservice",
    "container",
    "orchestration",
    "stack",
    "cluster",
    "cache",
    "hash",
    "token",
    "endpoint",
    "ci/cd",
    "devops",
    "sre",
    "latency",
    "throughput",
    "api",
    "rest",
    "graphql",
    "framework",
    "dashboard",
    "payload",
    "metadata",
    "debug",
    "log",
    "commit",
    "merge",
    "branch",
    "pull request",
    "code review",
    "sprint",
    "agile",
    "scrum",
    "open source",
    "build",
    "tooling",
    "workflow",
    "nubank",
    "picpay",
    "aws",
    "sagemaker",
    "kubeflow",
    "dagster",
    "gemini",
    "pytorch",
    "tensorflow",
    "python",
    "javascript",
    "github",
    "gitlab",
}

_RE_FENCED_CODE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_RE_INLINE_CODE = re.compile(r"`[^`]+`")
_RE_MD_TAGS = re.compile(r"<[^>]+>|!\[.*?\]\(.*?\)|\[.*?\]\(.*?\)")
_INVARIANT_HEADING_PATTERNS = (
    re.compile(r"^(?:#+\s*)?(?:\*\*)?\s*(?:fontes|sources)\s*:?(?:\*\*)?$", re.IGNORECASE),
    re.compile(r"^(?:#+\s*)?(?:\*\*)?\s*tl;dr\s*(?:\*\*)?$", re.IGNORECASE),
    re.compile(
        r"^(?:#+\s*)?(?:\*\*)?\s*view\s+transitions\s+api\s*:?(?:\*\*)?$",
        re.IGNORECASE,
    ),
)
_REFERENCE_ENTRY_PREFIX = re.compile(r"^\s*(?:\[\d+\]|\d+\.|;\s*)")

_RE_SCRIPT_TAG = re.compile(r"<\s*script[\s>].*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
_RE_SCRIPT_OPEN = re.compile(r"<\s*script[\s>]", re.IGNORECASE)
_RE_EVENT_HANDLER = re.compile(r"""\bon[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|\S+)""", re.IGNORECASE)
_RE_JAVASCRIPT_URI = re.compile(
    r"""(?:href|src|action)\s*=\s*"""
    r"""(?:"\s*javascript:[^"]*"|'\s*javascript:[^']*'|\s*javascript:\S*)""",
    re.IGNORECASE,
)


def sanitize_translation_html(html: str) -> str:
    """Strip dangerous HTML patterns from translated HTML fragments."""

    html = _RE_SCRIPT_TAG.sub("", html)
    html = _RE_SCRIPT_OPEN.sub("&lt;script", html)
    html = _RE_EVENT_HANDLER.sub("", html)
    html = _RE_JAVASCRIPT_URI.sub("", html)
    return html


def sanitize_translation_text(text: str) -> str:
    """Strip HTML tags from plain-text translation fields."""

    return re.sub(r"<[^>]*>", "", text)


def normalize_locale(locale: str) -> str:
    """Normalize locale identifiers to lowercase hyphenated form."""

    return str(locale or "").strip().lower().replace("_", "-")


def validate_translation(
    original_en: str,
    translated_pt: str,
    *,
    source_locale: str = "en-us",
    target_locale: str = "pt-br",
) -> Tuple[bool, List[str]]:
    """Validate a translation for supported EN<->PT directions."""

    issues: List[str] = []

    source = normalize_locale(source_locale)
    target = normalize_locale(target_locale)
    run_untranslated_checks = (source.startswith("en") and target.startswith("pt")) or (
        source.startswith("pt") and target.startswith("en")
    )

    if not translated_pt or not translated_pt.strip():
        return False, ["ERROR: translation is empty"]

    source_clean = _strip_code_and_tags(original_en)
    target_clean = _strip_code_and_tags(translated_pt)

    if run_untranslated_checks:
        source_paragraphs = [p.strip() for p in source_clean.split("\n\n") if p.strip()]
        target_paragraphs = [p.strip() for p in target_clean.split("\n\n") if p.strip()]

        for idx, (source_para, target_para) in enumerate(zip(source_paragraphs, target_paragraphs)):
            if source_para.strip() == target_para.strip() and _is_allowed_invariant_heading(
                source_para
            ):
                continue
            if _is_reference_entry(source_para) or _is_reference_entry(target_para):
                continue
            source_filtered = _remove_glossary_terms(source_para.lower())
            target_filtered = _remove_glossary_terms(target_para.lower())
            source_words = _word_set(source_filtered)
            target_words = _word_set(target_filtered)
            if not source_words:
                continue
            overlap = len(source_words & target_words) / len(source_words)
            if overlap > 0.70:
                snippet = source_para[:80].replace("\n", " ")
                issues.append(
                    f"ERROR: paragraph {idx + 1} appears untranslated "
                    f"({overlap:.0%} word overlap after removing glossary terms): "
                    f'"{snippet}…"'
                )

    if run_untranslated_checks:
        source_sentences = _split_sentences(source_clean)
        target_sentences = _split_sentences(target_clean)

        consecutive = 0
        for source_sentence, target_sentence in zip(source_sentences, target_sentences):
            if _is_reference_entry(source_sentence) or _is_reference_entry(target_sentence):
                consecutive = 0
                continue
            if source_sentence.strip() == target_sentence.strip():
                if _is_allowed_invariant_heading(source_sentence):
                    consecutive = 0
                    continue
                consecutive += 1
                if consecutive > 3:
                    snippet = source_sentence.strip()[:80]
                    issues.append(
                        f"ERROR: {consecutive} consecutive identical sentences "
                        f"detected — section appears untranslated near: "
                        f'"{snippet}…"'
                    )
                    break
            else:
                consecutive = 0

    fence_count = len(re.findall(r"^```", translated_pt, re.MULTILINE))
    if fence_count % 2 != 0:
        issues.append(
            f"ERROR: unclosed fenced code block "
            f"({fence_count} ``` delimiter(s) found — expected even number)"
        )

    open_tags = re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b[^/>]*>", translated_pt)
    close_tags = re.findall(r"</([a-zA-Z][a-zA-Z0-9]*)\s*>", translated_pt)
    void_tags = {
        "br",
        "hr",
        "img",
        "input",
        "meta",
        "link",
        "area",
        "base",
        "col",
        "embed",
        "source",
        "track",
        "wbr",
    }
    open_counts: Dict[str, int] = {}
    close_counts: Dict[str, int] = {}
    for tag in open_tags:
        lowered = tag.lower()
        if lowered not in void_tags:
            open_counts[lowered] = open_counts.get(lowered, 0) + 1
    for tag in close_tags:
        lowered = tag.lower()
        close_counts[lowered] = close_counts.get(lowered, 0) + 1
    for tag, count in open_counts.items():
        closed = close_counts.get(tag, 0)
        if count > closed:
            issues.append(f"ERROR: {count - closed} unclosed <{tag}> tag(s) in translation")

    source_len = len(original_en.strip())
    target_len = len(translated_pt.strip())
    if source_len > 0 and target_len < source_len * 0.50:
        issues.append(
            f"WARNING: translation is suspiciously short "
            f"({target_len} chars vs {source_len} original — "
            f"{target_len / source_len:.0%} of source length)"
        )

    has_errors = any(issue.startswith("ERROR:") for issue in issues)
    return (not has_errors, issues)


def _strip_code_and_tags(text: str) -> str:
    text = _RE_FENCED_CODE.sub("", text)
    text = _RE_INLINE_CODE.sub("", text)
    text = _RE_MD_TAGS.sub("", text)
    return text


def _remove_glossary_terms(text: str) -> str:
    for term in sorted(TECH_GLOSSARY, key=len, reverse=True):
        text = text.replace(term, " ")
    return text


def _normalize_heading_candidate(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"^#+\s*", "", normalized)
    normalized = re.sub(r"^\*\*\s*|\s*\*\*$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _is_allowed_invariant_heading(text: str) -> bool:
    candidate = _normalize_heading_candidate(text)
    if not candidate:
        return False
    return any(pattern.match(candidate) for pattern in _INVARIANT_HEADING_PATTERNS)


def _is_reference_entry(text: str) -> bool:
    candidate = text.strip()
    if not candidate:
        return False
    return bool(_REFERENCE_ENTRY_PREFIX.match(candidate))


def _word_set(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-záàâãéêíóôõúüç]+", text.lower()) if len(word) > 1}


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in parts if sentence.strip()]
