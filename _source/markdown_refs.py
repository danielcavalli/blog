"""Markdown rendering helpers for numeric internal references.

Supports in-document citations like ``[text][7]`` that point to a
numbered references section where entries are written as ``[7] ...``.
"""

from __future__ import annotations

import re

import markdown


_REFERENCE_LINE_RE = re.compile(r"^\[(\d+)\]\s+")
_NUMERIC_CITATION_RE = re.compile(r"\[([^\]\n]+?)\]\[(\d+)\]")
_BARE_NUMERIC_CITATION_RE = re.compile(r"(?<!\[)\[(\d+)\](?![\]\(:])")
_FENCE_RE = re.compile(r"^\s*```")


def _collect_reference_numbers(lines: list[str]) -> set[str]:
    """Collect numeric reference ids from ``[N] ...`` lines."""
    in_fence = False
    refs: set[str] = set()

    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        match = _REFERENCE_LINE_RE.match(line)
        if match:
            refs.add(match.group(1))

    return refs


def preprocess_numeric_internal_references(markdown_text: str) -> str:
    """Rewrite numeric internal citations and add reference anchors.

    Transformations:
    - ``[label][7]`` -> ``label[[7]](#ref-7)`` (only when ``[7] ...`` exists)
    - ``[7] ...`` -> ``<span id="ref-7"></span>[7] ...``
    """
    lines = markdown_text.splitlines()
    reference_numbers = _collect_reference_numbers(lines)

    in_fence = False
    processed_lines: list[str] = []

    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            processed_lines.append(line)
            continue

        if in_fence:
            processed_lines.append(line)
            continue

        ref_match = _REFERENCE_LINE_RE.match(line)
        if ref_match:
            ref_number = ref_match.group(1)
            line = f'<span id="ref-{ref_number}"></span>{line}'
            processed_lines.append(line)
            continue

        def _replace_citation(match: re.Match[str]) -> str:
            label = match.group(1)
            ref_number = match.group(2)
            if ref_number in reference_numbers:
                return f"{label}[[{ref_number}]](#ref-{ref_number})"
            return match.group(0)

        line = _NUMERIC_CITATION_RE.sub(_replace_citation, line)

        def _replace_bare_citation(match: re.Match[str]) -> str:
            ref_number = match.group(1)
            if ref_number in reference_numbers:
                return f"[[{ref_number}]](#ref-{ref_number})"
            return match.group(0)

        processed_lines.append(_BARE_NUMERIC_CITATION_RE.sub(_replace_bare_citation, line))

    return "\n".join(processed_lines)


def render_markdown_with_internal_refs(markdown_text: str) -> str:
    """Render Markdown with support for numeric in-document references."""
    processed = preprocess_numeric_internal_references(markdown_text)
    return markdown.markdown(processed, extensions=["fenced_code", "tables", "nl2br"])
