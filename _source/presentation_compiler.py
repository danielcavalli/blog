"""Markdown-first presentation compiler."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

import markdown


ALLOWED_LAYOUTS = frozenset(
    {
        "lead",
        "divider",
        "bio",
        "content",
        "dark_content",
        "emphasis",
        "split",
        "card_grid",
        "table",
        "code",
        "image",
        "paragraph",
        "quote",
        "list",
    }
)
ALLOWED_DENSITIES = frozenset({"normal", "dense", "very_dense"})


_OPEN_MARKER_RE = re.compile(r"^\s*<!--\s*presentation:slide\s+(?P<attrs>.*?)\s*-->\s*$")
_CLOSE_MARKER_RE = re.compile(r"^\s*<!--\s*/presentation:slide\s*-->\s*$")
_ATTR_RE = re.compile(r'\s*([A-Za-z_:][\w:.-]*)="([^"]*)"')
_FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(?P<fence>`{3,}|~{3,}).*$")
_STRUCTURAL_COMMENT_RE = re.compile(
    r"<!--\s*(?P<closing>/)?presentation:(?P<kind>block|card|column)"
    r"(?:\s+type=\"(?P<type>[A-Za-z_][\w.-]*)\")?\s*-->"
)


class PresentationCompileError(ValueError):
    """Raised when presentation slide markers cannot be compiled safely."""


@dataclass(frozen=True)
class PresentationSlide:
    """Compiled slide content and rendered HTML."""

    id: str
    layout: str
    density: str
    markdown: str
    html: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class PresentationDocument:
    """Compiled presentation document model."""

    slides: tuple[PresentationSlide, ...]

    @property
    def slide_count(self) -> int:
        return len(self.slides)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(slide.id for slide in self.slides)


def compile_presentation_markdown(
    body: str,
    *,
    expected_slide_count: int | None = None,
    allowed_layouts: set[str] | frozenset[str] = ALLOWED_LAYOUTS,
    allowed_densities: set[str] | frozenset[str] = ALLOWED_DENSITIES,
) -> PresentationDocument:
    """Compile HTML-comment-marked Markdown slides into a document model.

    Only full-line presentation markers outside fenced code blocks are treated
    as directives. Markdown outside slide markers is ignored by the compiler.
    """

    slides: list[PresentationSlide] = []
    seen_ids: set[str] = set()
    current_attrs: dict[str, str] | None = None
    current_lines: list[str] = []
    current_start_line = 0
    fence_state: tuple[str, int] | None = None

    for line_number, raw_line in enumerate(body.splitlines(keepends=True), start=1):
        line = raw_line.rstrip("\r\n")

        if fence_state is None:
            open_match = _OPEN_MARKER_RE.match(line)
            if open_match:
                if current_attrs is not None:
                    raise PresentationCompileError(
                        f"Nested presentation slide marker at line {line_number}"
                    )
                current_attrs = _parse_slide_attrs(open_match.group("attrs"), line_number)
                _validate_slide_attrs(
                    current_attrs,
                    line_number=line_number,
                    allowed_layouts=allowed_layouts,
                    allowed_densities=allowed_densities,
                )
                if current_attrs["id"] in seen_ids:
                    raise PresentationCompileError(
                        f"Duplicate presentation slide id {current_attrs['id']!r} at line {line_number}"
                    )
                current_lines = []
                current_start_line = line_number
                continue

            if _CLOSE_MARKER_RE.match(line):
                if current_attrs is None:
                    raise PresentationCompileError(
                        f"Closing presentation slide marker without opener at line {line_number}"
                    )
                slide_markdown = "".join(current_lines)
                slide = PresentationSlide(
                    id=current_attrs["id"],
                    layout=current_attrs["layout"],
                    density=current_attrs["density"],
                    markdown=slide_markdown,
                    html=render_slide_markdown(slide_markdown),
                    start_line=current_start_line,
                    end_line=line_number,
                )
                slides.append(slide)
                seen_ids.add(slide.id)
                current_attrs = None
                current_lines = []
                current_start_line = 0
                continue

        if current_attrs is not None:
            current_lines.append(raw_line)

        fence_state = _next_fence_state(line, fence_state)

    if current_attrs is not None:
        raise PresentationCompileError(
            f"Presentation slide {current_attrs['id']!r} opened at line "
            f"{current_start_line} is missing a closing marker"
        )

    if not slides:
        raise PresentationCompileError("No presentation slide markers found")

    if expected_slide_count is not None and len(slides) != expected_slide_count:
        raise PresentationCompileError(
            f"Expected {expected_slide_count} presentation slides, found {len(slides)}"
        )

    return PresentationDocument(slides=tuple(slides))


def render_slide_markdown(markdown_text: str) -> str:
    """Render slide Markdown without post anchor permalink controls."""

    renderer = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "nl2br",
            "attr_list",
        ]
    )
    return _wrap_markdown_tables(_promote_structural_comments(renderer.convert(markdown_text)))


def _promote_structural_comments(html: str) -> str:
    """Turn presentation block comments into semantic slide-local wrappers."""

    def replace(match: re.Match[str]) -> str:
        closing = bool(match.group("closing"))
        kind = match.group("kind")
        block_type = match.group("type") or ""

        if kind == "block":
            if closing:
                return "</div>"
            if block_type == "split":
                return '<div class="presentation-split presentation-block">'
            if block_type == "card_grid":
                return '<div class="presentation-card-grid presentation-block">'
            return (
                '<div class="presentation-block" '
                f'data-presentation-block="{_escape_attr(block_type)}">'
            )

        if kind == "card":
            return "</article>" if closing else '<article class="presentation-card">'

        if kind == "column":
            return "</section>" if closing else '<section class="presentation-column">'

        return ""

    return _STRUCTURAL_COMMENT_RE.sub(replace, html)


def _wrap_markdown_tables(html: str) -> str:
    """Give Markdown tables the same responsive presentation wrapper as structured tables."""

    return re.sub(
        r"(?s)(?<!<div class=\"presentation-table-wrap\" data-overflow=\"scroll\">)(<table>.*?</table>)",
        r'<div class="presentation-table-wrap" data-overflow="scroll">\1</div>',
        html,
    )


def _escape_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def presentation_document_to_dict(document: PresentationDocument) -> dict[str, Any]:
    """Serialize a compiled presentation document to plain Python objects."""

    return {
        "slide_count": document.slide_count,
        "slides": [asdict(slide) for slide in document.slides],
    }


def presentation_document_from_dict(data: dict[str, Any]) -> PresentationDocument:
    """Deserialize a presentation document produced by presentation_document_to_dict."""

    raw_slides = data.get("slides")
    if not isinstance(raw_slides, list):
        raise PresentationCompileError("Serialized presentation document must contain slides")

    slides: list[PresentationSlide] = []
    seen_ids: set[str] = set()
    for index, raw_slide in enumerate(raw_slides):
        if not isinstance(raw_slide, dict):
            raise PresentationCompileError(f"Serialized slide {index + 1} must be an object")
        try:
            slide = PresentationSlide(
                id=str(raw_slide["id"]),
                layout=str(raw_slide["layout"]),
                density=str(raw_slide["density"]),
                markdown=str(raw_slide["markdown"]),
                html=str(raw_slide.get("html") or render_slide_markdown(str(raw_slide["markdown"]))),
                start_line=int(raw_slide.get("start_line", 0)),
                end_line=int(raw_slide.get("end_line", 0)),
            )
        except KeyError as exc:
            raise PresentationCompileError(
                f"Serialized slide {index + 1} is missing {exc.args[0]!r}"
            ) from exc
        if slide.id in seen_ids:
            raise PresentationCompileError(f"Duplicate serialized slide id {slide.id!r}")
        if slide.layout not in ALLOWED_LAYOUTS:
            raise PresentationCompileError(f"Unknown serialized slide layout {slide.layout!r}")
        if slide.density not in ALLOWED_DENSITIES:
            raise PresentationCompileError(f"Unknown serialized slide density {slide.density!r}")
        seen_ids.add(slide.id)
        slides.append(slide)

    expected_count = data.get("slide_count")
    if expected_count is not None and int(expected_count) != len(slides):
        raise PresentationCompileError(
            f"Serialized slide_count {expected_count} does not match {len(slides)} slides"
        )

    return PresentationDocument(slides=tuple(slides))


def _parse_slide_attrs(raw_attrs: str, line_number: int) -> dict[str, str]:
    attrs: dict[str, str] = {}
    position = 0
    while position < len(raw_attrs):
        match = _ATTR_RE.match(raw_attrs, position)
        if match is None:
            raise PresentationCompileError(
                f"Malformed presentation slide attributes at line {line_number}: {raw_attrs!r}"
            )
        attrs[match.group(1)] = match.group(2)
        position = match.end()

    if raw_attrs[position:].strip():
        raise PresentationCompileError(
            f"Malformed presentation slide attributes at line {line_number}: {raw_attrs!r}"
        )
    return attrs


def _validate_slide_attrs(
    attrs: dict[str, str],
    *,
    line_number: int,
    allowed_layouts: set[str] | frozenset[str],
    allowed_densities: set[str] | frozenset[str],
) -> None:
    required = {"id", "layout", "density"}
    missing = sorted(required.difference(attrs))
    if missing:
        raise PresentationCompileError(
            f"Presentation slide marker at line {line_number} is missing: {', '.join(missing)}"
        )

    unexpected = sorted(set(attrs).difference(required))
    if unexpected:
        raise PresentationCompileError(
            f"Presentation slide marker at line {line_number} has unknown attributes: "
            f"{', '.join(unexpected)}"
        )

    if not attrs["id"]:
        raise PresentationCompileError(f"Presentation slide marker at line {line_number} has empty id")
    if attrs["layout"] not in allowed_layouts:
        raise PresentationCompileError(
            f"Unknown presentation slide layout {attrs['layout']!r} at line {line_number}"
        )
    if attrs["density"] not in allowed_densities:
        raise PresentationCompileError(
            f"Unknown presentation slide density {attrs['density']!r} at line {line_number}"
        )


def _next_fence_state(
    line: str,
    fence_state: tuple[str, int] | None,
) -> tuple[str, int] | None:
    if fence_state is None:
        match = _FENCE_OPEN_RE.match(line)
        if match is None:
            return None
        fence = match.group("fence")
        return (fence[0], len(fence))

    fence_char, fence_length = fence_state
    close_re = re.compile(rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*$")
    if close_re.match(line):
        return None
    return fence_state
