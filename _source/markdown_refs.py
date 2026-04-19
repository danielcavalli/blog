"""Markdown rendering helpers for post-local anchors and internal references.

Supports:
- Numeric in-document citations like ``[text][7]`` that point to a
  numbered references section written as ``[7] ...``.
- Stable heading anchors, including explicit ``{#custom-id}`` overrides.
- Block-level ids/permalinks for deep links into specific passages.
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


_REFERENCE_LINE_RE = re.compile(r"^\[(\d+)\]\s+")
_NUMERIC_CITATION_RE = re.compile(r"\[([^\]\n]+?)\]\[(\d+)\]")
_BARE_NUMERIC_CITATION_RE = re.compile(r"(?<!\[)\[(\d+)\](?![\]\(:])")
_FENCE_RE = re.compile(r"^\s*```")
_ATX_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
_EXPLICIT_ANCHOR_SUFFIX_RE = re.compile(r"\s+\{#([A-Za-z][\w:.-]*)\}\s*$")
_TRAILING_CLOSING_HASHES_RE = re.compile(r"[ \t]+#+[ \t]*$")
_INLINE_LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^)]+\)")
_INLINE_REFERENCE_RE = re.compile(r"\[([^\]]+)\]\[[^\]]+\]")
_INLINE_HTML_RE = re.compile(r"<[^>]+>")
_INLINE_MARKER_RE = re.compile(r"[*_~`]")
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS = {"p", "li", "blockquote", "pre", "table"}
_SCROLL_TARGET_TAGS = _HEADING_TAGS | _BLOCK_TAGS
_UNWRAPPABLE_BLOCK_TAGS = {"pre", "table", "blockquote", "ul", "ol"}
_WRAPPED_BLOCK_HTML_RE = re.compile(
    r"<p(?P<attrs>[^>]*)>\s*(?P<block><(?P<tag>pre|table|blockquote|ul|ol)\b.*?</(?P=tag)>)\s*</p>",
    re.DOTALL,
)


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


@dataclass(frozen=True)
class HeadingAnchorSpec:
    """Stable heading-anchor metadata extracted from markdown source."""

    level: int
    text: str
    anchor_id: str


def _append_class(element: ET.Element, class_name: str) -> None:
    classes = element.get("class", "").split()
    if class_name not in classes:
        classes.append(class_name)
    if classes:
        element.set("class", " ".join(classes))


def _normalize_heading_text(raw_text: str) -> tuple[str, str | None]:
    text = _TRAILING_CLOSING_HASHES_RE.sub("", raw_text).strip()
    explicit_match = _EXPLICIT_ANCHOR_SUFFIX_RE.search(text)
    explicit_anchor = None
    if explicit_match:
        explicit_anchor = explicit_match.group(1).strip()
        text = text[: explicit_match.start()].rstrip()
    return text, explicit_anchor


def _plain_text_for_slug(text: str) -> str:
    normalized = _INLINE_LINK_RE.sub(r"\1", text)
    normalized = _INLINE_REFERENCE_RE.sub(r"\1", normalized)
    normalized = _INLINE_HTML_RE.sub("", normalized)
    normalized = _INLINE_MARKER_RE.sub("", normalized)
    return " ".join(normalized.split())


def _slugify_anchor(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", _plain_text_for_slug(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_text = ascii_text.replace("'", "")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or "section"


def _dedupe_id(candidate: str, used: set[str]) -> str:
    base = candidate.strip() or "section"
    deduped = base
    index = 2
    while deduped in used:
        deduped = f"{base}-{index}"
        index += 1
    used.add(deduped)
    return deduped


def _normalize_wrapped_block_html(html: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs").strip()
        block_html = match.group("block")
        if not attrs:
            return block_html
        return re.sub(
            r"^<([a-z0-9]+)([^>]*)>",
            lambda block_match: f"<{block_match.group(1)}{block_match.group(2)} {attrs}>",
            block_html,
            count=1,
        )

    return _WRAPPED_BLOCK_HTML_RE.sub(_replace, html)


def extract_heading_anchor_specs(markdown_text: str) -> list[HeadingAnchorSpec]:
    """Return deterministic heading anchors from markdown source text."""
    in_fence = False
    specs: list[HeadingAnchorSpec] = []
    used_ids: set[str] = set()

    for line in markdown_text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        match = _ATX_HEADING_RE.match(line)
        if not match:
            continue

        level = len(match.group(1))
        heading_text, explicit_anchor = _normalize_heading_text(match.group(2))
        candidate_id = explicit_anchor or _slugify_anchor(heading_text)
        specs.append(
            HeadingAnchorSpec(
                level=level,
                text=heading_text,
                anchor_id=_dedupe_id(candidate_id, used_ids),
            )
        )

    return specs


class _PostAnchorTreeprocessor(Treeprocessor):
    """Assign stable ids/permalinks to headings and linkable blocks."""

    def __init__(self, md: markdown.Markdown, heading_specs: list[HeadingAnchorSpec]) -> None:
        super().__init__(md)
        self._heading_specs = heading_specs

    def run(self, root: ET.Element) -> ET.Element:
        self._unwrap_block_wrappers(root)

        used_ids: set[str] = set()
        heading_index = 0
        block_index = 1

        for element in root.iter():
            tag = str(element.tag)

            if tag in _HEADING_TAGS:
                if heading_index < len(self._heading_specs):
                    candidate = self._heading_specs[heading_index].anchor_id
                else:
                    candidate = _slugify_anchor("".join(element.itertext()))
                heading_index += 1
                anchor_id = _dedupe_id(candidate, used_ids)
                element.set("id", anchor_id)
                _append_class(element, "section-heading")
                self._append_permalink(
                    element,
                    anchor_id=anchor_id,
                    class_name="heading-anchor",
                    label="#",
                    aria_label="Link to this section",
                )
                continue

            existing_id = element.get("id")
            if existing_id:
                used_ids.add(existing_id)

            if tag in _BLOCK_TAGS and not existing_id:
                block_id = _dedupe_id(f"block-{block_index:03d}", used_ids)
                block_index += 1
                element.set("id", block_id)
                element.set("data-block-id", block_id)
                _append_class(element, "linkable-block")

        return root

    def _unwrap_block_wrappers(self, parent: ET.Element) -> None:
        for child in list(parent):
            self._unwrap_block_wrappers(child)

            if str(child.tag) != "p":
                continue

            if (child.text or "").strip():
                continue

            nested_children = list(child)
            if len(nested_children) != 1:
                continue

            nested = nested_children[0]
            if str(nested.tag) not in _UNWRAPPABLE_BLOCK_TAGS:
                continue

            if (nested.tail or "").strip():
                continue

            insert_at = list(parent).index(child)
            parent.remove(child)
            nested.tail = child.tail
            parent.insert(insert_at, nested)

    @staticmethod
    def _append_permalink(
        element: ET.Element,
        *,
        anchor_id: str,
        class_name: str,
        label: str,
        aria_label: str,
        prepend: bool = False,
    ) -> None:
        link = ET.Element(
            "a",
            attrib={
                "href": f"#{anchor_id}",
                "class": f"permalink-anchor {class_name}",
                "aria-label": aria_label,
                "data-share-label": "Copy section link",
                "data-copied-label": "Link copied",
            },
        )
        glyph = ET.SubElement(link, "span", attrib={"class": "permalink-glyph", "aria-hidden": "true"})
        glyph.text = label
        sr_only = ET.SubElement(link, "span", attrib={"class": "sr-only"})
        sr_only.text = aria_label

        if prepend:
            existing_text = element.text or ""
            element.text = None
            link.tail = existing_text
            element.insert(0, link)
        else:
            element.append(link)


class _PostAnchorExtension(Extension):
    """Markdown extension that injects stable ids/permalinks into rendered posts."""

    def __init__(self, *, heading_specs: list[HeadingAnchorSpec]) -> None:
        self._heading_specs = heading_specs
        super().__init__()

    def extendMarkdown(self, md: markdown.Markdown) -> None:  # noqa: N802
        md.treeprocessors.register(
            _PostAnchorTreeprocessor(md, self._heading_specs),
            "post-anchor-treeprocessor",
            priority=15,
        )


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


def render_markdown_with_internal_refs(
    markdown_text: str,
    *,
    source_markdown: str | None = None,
) -> str:
    """Render Markdown with support for post-local anchors and numeric references."""
    processed = preprocess_numeric_internal_references(markdown_text)
    anchor_source = source_markdown if source_markdown is not None else markdown_text
    heading_specs = extract_heading_anchor_specs(anchor_source)
    renderer = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "nl2br",
            "attr_list",
            _PostAnchorExtension(heading_specs=heading_specs),
        ]
    )
    return _normalize_wrapped_block_html(renderer.convert(processed))
