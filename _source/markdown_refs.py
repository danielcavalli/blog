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
from html import escape
from html.parser import HTMLParser

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.inlinepatterns import InlineProcessor
from markdown.util import AtomicString


_REFERENCE_LINE_RE = re.compile(r"^\[(\d+)\]\s+")
_INLINE_LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^)]+\)")
_INLINE_REFERENCE_RE = re.compile(r"\[([^\]]+)\]\[[^\]]+\]")
_INLINE_HTML_RE = re.compile(r"<[^>]+>")
_INLINE_MARKER_RE = re.compile(r"[*_~`]")
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS = {"p", "li", "blockquote", "pre", "table"}
_SCROLL_TARGET_TAGS = _HEADING_TAGS | _BLOCK_TAGS
_UNWRAPPABLE_BLOCK_TAGS = {"pre", "table", "blockquote", "ul", "ol", "figure"}
_WRAPPED_BLOCK_HTML_RE = re.compile(
    r"<p(?P<attrs>[^>]*)>\s*(?P<block><(?P<tag>pre|table|blockquote|ul|ol|figure)\b.*?</(?P=tag)>)\s*</p>",
    re.DOTALL,
)


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


class _TagAttributes(HTMLParser):
    """Read an opening HTML tag without treating HTML attributes as XML."""

    def __init__(self, opening_tag: str) -> None:
        super().__init__(convert_charrefs=True)
        self.attributes: dict[str, str | None] = {}
        self.feed(opening_tag)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.attributes = dict(attrs)


def _normalize_wrapped_block_html(html: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs").strip()
        block_html = match.group("block")
        if not attrs:
            return block_html

        def merge_attributes(block_match: re.Match[str]) -> str:
            wrapper = _TagAttributes(f"<p {attrs}>").attributes
            original = _TagAttributes(block_match.group(0)).attributes
            merged = {**wrapper, **original}
            classes = [*(original.get("class") or "").split(), *(wrapper.get("class") or "").split()]
            if classes:
                merged["class"] = " ".join(dict.fromkeys(classes))
            if "data-block-id" in wrapper and original.get("id"):
                merged["data-block-id"] = original["id"]
            rendered = "".join(
                f' {key}="{escape(value, quote=True)}"' if value is not None else f" {key}"
                for key, value in merged.items()
            )
            return f"<{block_match.group(1)}{rendered}>"

        return re.sub(
            r"^<([a-z0-9]+)([^>]*)>",
            merge_attributes,
            block_html,
            count=1,
        )

    return _WRAPPED_BLOCK_HTML_RE.sub(_replace, html)


def extract_heading_anchor_specs(markdown_text: str) -> list[HeadingAnchorSpec]:
    """Use Markdown's parser for source anchors, including Setext headings and code."""
    renderer = _markdown_renderer([])
    renderer.convert(markdown_text)
    processor = renderer.treeprocessors["post-anchor-treeprocessor"]
    assert isinstance(processor, _PostAnchorTreeprocessor)
    return processor.headings


class _PostAnchorTreeprocessor(Treeprocessor):
    """Assign stable ids/permalinks to headings and linkable blocks."""

    def __init__(self, md: markdown.Markdown, heading_specs: list[HeadingAnchorSpec]) -> None:
        super().__init__(md)
        self._heading_specs = heading_specs
        self.headings: list[HeadingAnchorSpec] = []

    def run(self, root: ET.Element) -> ET.Element:
        self._unwrap_block_wrappers(root)

        used_ids = {e.attrib["id"] for e in root.iter() if e.get("id") and e.tag not in _HEADING_TAGS}
        self.headings.clear()
        heading_index = 0
        block_index = 1

        for element in root.iter():
            tag = str(element.tag)

            if tag in _HEADING_TAGS:
                if heading_index < len(self._heading_specs):
                    candidate = self._heading_specs[heading_index].anchor_id
                else:
                    candidate = element.get("id") or _slugify_anchor("".join(element.itertext()))
                heading_index += 1
                anchor_id = _dedupe_id(candidate, used_ids)
                self.headings.append(HeadingAnchorSpec(int(tag[1]), "".join(element.itertext()), anchor_id))
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
            priority=5,
        )


class _NumericReferenceDefinitions(Treeprocessor):
    def __init__(self, md, references: set[str]):
        super().__init__(md)
        self.references = references

    def run(self, root):
        for paragraph in root.iter("p"):
            match = _REFERENCE_LINE_RE.match(paragraph.text or "")
            if not match:
                continue
            number = match[1]
            self.references.add(number)
            marker = ET.Element("span", {"id": f"ref-{number}"})
            marker.text = AtomicString(f"[{number}]")
            marker.tail = (paragraph.text or "")[len(number) + 2:]
            paragraph.text = None
            paragraph.insert(0, marker)


class _NumericCitation(InlineProcessor):
    # Markdown handles escapes, code, HTML and link destinations first.
    ANCESTOR_EXCLUDES = ("a", "code", "pre")

    def __init__(self, pattern, references, *, labeled=False):
        super().__init__(pattern)
        self.references = references
        self.labeled = labeled

    def handleMatch(self, match, data):  # noqa: N802
        number = match[2] if self.labeled else match[1]
        if number not in self.references:
            return None, None, None
        anchor = ET.Element("a", {"href": f"#ref-{number}"})
        anchor.text = AtomicString(f"[{number}]")
        result = anchor
        if self.labeled:
            result = ET.Element("span")
            result.text = match[1]
            result.append(anchor)
        return result, match.start(0), match.end(0)


class _NumericReferenceExtension(Extension):
    def extendMarkdown(self, md):  # noqa: N802
        references: set[str] = set()
        md.treeprocessors.register(_NumericReferenceDefinitions(md, references), "numeric-definitions", 25)
        md.inlinePatterns.register(
            _NumericCitation(r"\[([^\]\n]+?)\]\[(\d+)\]", references, labeled=True),
            "numeric-citation", 145,
        )
        md.inlinePatterns.register(
            _NumericCitation(r"(?<!\[)\[(\d+)\](?![\]\(:])", references), "bare-numeric-citation", 144,
        )


def _markdown_renderer(heading_specs: list[HeadingAnchorSpec]) -> markdown.Markdown:
    return markdown.Markdown(extensions=[
        "fenced_code", "tables", "nl2br", "attr_list", "footnotes",
        _NumericReferenceExtension(), _PostAnchorExtension(heading_specs=heading_specs),
    ])


def render_markdown_with_internal_refs(
    markdown_text: str,
    *,
    source_markdown: str | None = None,
) -> str:
    """Render Markdown with support for post-local anchors and numeric references."""
    heading_specs = extract_heading_anchor_specs(source_markdown) if source_markdown is not None else []
    return _normalize_wrapped_block_html(_markdown_renderer(heading_specs).convert(markdown_text))
