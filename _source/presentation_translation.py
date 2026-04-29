"""Translation invariant checks for Markdown-first presentations."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re

from presentation_compiler import (
    PresentationCompileError,
    PresentationDocument,
    compile_presentation_markdown,
)


@dataclass(frozen=True)
class PresentationInvariantIssue:
    """A structural mismatch between source and translated presentation Markdown."""

    code: str
    message: str
    slide_id: str | None = None


class PresentationTranslationInvariantError(ValueError):
    """Raised when strict presentation translation validation fails."""

    def __init__(self, issues: list[PresentationInvariantIssue]) -> None:
        self.issues = issues
        super().__init__("\n".join(issue.message for issue in issues))


@dataclass(frozen=True)
class LinkDestination:
    kind: str
    destination: str


def compare_presentation_translation_invariants(
    source_markdown: str,
    translated_markdown: str,
    *,
    expected_slide_count: int | None = None,
    preserve_code_fences: bool = True,
) -> list[PresentationInvariantIssue]:
    """Return invariant issues between source and translated presentation Markdown."""

    issues: list[PresentationInvariantIssue] = []
    source_doc = _compile_for_invariants(
        source_markdown,
        label="source",
        issues=issues,
        expected_slide_count=expected_slide_count,
    )
    translated_doc = _compile_for_invariants(
        translated_markdown,
        label="translated",
        issues=issues,
        expected_slide_count=expected_slide_count,
    )
    if source_doc is None or translated_doc is None:
        return issues

    if source_doc.slide_count != translated_doc.slide_count:
        issues.append(
            PresentationInvariantIssue(
                code="slide_count",
                message=(
                    f"Slide count changed: source has {source_doc.slide_count}, "
                    f"translated has {translated_doc.slide_count}"
                ),
            )
        )

    source_ids = list(source_doc.ids)
    translated_ids = list(translated_doc.ids)
    if source_ids != translated_ids:
        issues.append(
            PresentationInvariantIssue(
                code="slide_ids",
                message=f"Slide ids/order changed: source {source_ids!r}, translated {translated_ids!r}",
            )
        )

    for index, (source_slide, translated_slide) in enumerate(
        zip(source_doc.slides, translated_doc.slides),
        start=1,
    ):
        slide_id = source_slide.id
        if source_slide.layout != translated_slide.layout:
            issues.append(
                PresentationInvariantIssue(
                    code="layout",
                    message=(
                        f"Slide {index} layout changed for {slide_id!r}: "
                        f"{source_slide.layout!r} -> {translated_slide.layout!r}"
                    ),
                    slide_id=slide_id,
                )
            )
        if source_slide.density != translated_slide.density:
            issues.append(
                PresentationInvariantIssue(
                    code="density",
                    message=(
                        f"Slide {index} density changed for {slide_id!r}: "
                        f"{source_slide.density!r} -> {translated_slide.density!r}"
                    ),
                    slide_id=slide_id,
                )
            )

        if preserve_code_fences:
            source_fences = extract_fenced_code_fence_signatures(source_slide.markdown)
            translated_fences = extract_fenced_code_fence_signatures(translated_slide.markdown)
            if source_fences != translated_fences:
                issues.append(
                    PresentationInvariantIssue(
                        code="code_fences",
                        message=f"Code fence structure changed in slide {slide_id!r}",
                        slide_id=slide_id,
                    )
                )

        source_destinations = extract_markdown_destinations(source_slide.markdown)
        translated_destinations = extract_markdown_destinations(translated_slide.markdown)
        if source_destinations != translated_destinations:
            issues.append(
                PresentationInvariantIssue(
                    code="destinations",
                    message=f"Image/link destinations changed in slide {slide_id!r}",
                    slide_id=slide_id,
                )
            )

    return issues


def assert_presentation_translation_invariants(
    source_markdown: str,
    translated_markdown: str,
    *,
    expected_slide_count: int | None = None,
    preserve_code_fences: bool = True,
) -> None:
    """Raise if translated presentation Markdown violates structural invariants."""

    issues = compare_presentation_translation_invariants(
        source_markdown,
        translated_markdown,
        expected_slide_count=expected_slide_count,
        preserve_code_fences=preserve_code_fences,
    )
    if issues:
        raise PresentationTranslationInvariantError(issues)


def extract_fenced_code_blocks(markdown_text: str) -> list[str]:
    """Return fenced code blocks, including their fence delimiter lines."""

    blocks: list[str] = []
    current: list[str] | None = None
    fence_state: tuple[str, int] | None = None

    for raw_line in markdown_text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        if fence_state is None:
            match = _FENCE_OPEN_RE.match(line)
            if match is None:
                continue
            fence = match.group("fence")
            fence_state = (fence[0], len(fence))
            current = [raw_line]
            continue

        current = current or []
        current.append(raw_line)
        fence_char, fence_length = fence_state
        close_re = re.compile(rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*$")
        if close_re.match(line):
            blocks.append("".join(current))
            current = None
            fence_state = None

    if current is not None:
        blocks.append("".join(current))

    return blocks


def extract_fenced_code_fence_signatures(markdown_text: str) -> list[tuple[str, str]]:
    """Return opening/closing fence lines without treating content as invariant."""

    signatures: list[tuple[str, str]] = []
    opening_line = ""
    fence_state: tuple[str, int] | None = None

    for raw_line in markdown_text.splitlines(keepends=False):
        line = raw_line.rstrip("\r\n")
        if fence_state is None:
            match = _FENCE_OPEN_RE.match(line)
            if match is None:
                continue
            fence = match.group("fence")
            fence_state = (fence[0], len(fence))
            opening_line = line
            continue

        fence_char, fence_length = fence_state
        close_re = re.compile(rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*$")
        if close_re.match(line):
            signatures.append((opening_line, line))
            opening_line = ""
            fence_state = None

    if fence_state is not None:
        signatures.append((opening_line, ""))

    return signatures


def extract_markdown_destinations(markdown_text: str) -> list[LinkDestination]:
    """Extract Markdown and inline-HTML image/link destinations outside code fences."""

    text = strip_fenced_code_blocks(markdown_text)
    destinations = _extract_inline_markdown_destinations(text)
    destinations.extend(_extract_reference_destinations(text))
    destinations.extend(_extract_html_destinations(text))
    return destinations


def strip_fenced_code_blocks(markdown_text: str) -> str:
    """Remove fenced code blocks while preserving surrounding text order."""

    output: list[str] = []
    fence_state: tuple[str, int] | None = None

    for raw_line in markdown_text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        if fence_state is None:
            match = _FENCE_OPEN_RE.match(line)
            if match is not None:
                fence = match.group("fence")
                fence_state = (fence[0], len(fence))
                output.append("\n")
                continue
            output.append(raw_line)
            continue

        fence_char, fence_length = fence_state
        close_re = re.compile(rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*$")
        if close_re.match(line):
            fence_state = None
        output.append("\n")

    return "".join(output)


def _compile_for_invariants(
    markdown_text: str,
    *,
    label: str,
    issues: list[PresentationInvariantIssue],
    expected_slide_count: int | None,
) -> PresentationDocument | None:
    try:
        return compile_presentation_markdown(
            markdown_text,
            expected_slide_count=expected_slide_count,
        )
    except PresentationCompileError as exc:
        issues.append(
            PresentationInvariantIssue(
                code=f"{label}_markers",
                message=f"{label.capitalize()} presentation markers are invalid: {exc}",
            )
        )
        return None


_FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(?P<fence>`{3,}|~{3,}).*$")
_REFERENCE_DESTINATION_RE = re.compile(
    r"^[ \t]{0,3}\[[^\]]+\]:[ \t]*(?P<destination><[^>\n]+>|\S+)",
    re.MULTILINE,
)


def _extract_inline_markdown_destinations(text: str) -> list[LinkDestination]:
    destinations: list[LinkDestination] = []
    position = 0
    while position < len(text):
        marker_position = text.find("[", position)
        if marker_position == -1:
            break

        is_image = marker_position > 0 and text[marker_position - 1] == "!"
        if _is_escaped(text, marker_position):
            position = marker_position + 1
            continue

        label_end = _find_closing_bracket(text, marker_position)
        if label_end == -1 or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            position = marker_position + 1
            continue

        destination_end = _find_closing_paren(text, label_end + 1)
        if destination_end == -1:
            position = marker_position + 1
            continue

        raw_destination = text[label_end + 2 : destination_end]
        destination = _normalize_markdown_destination(raw_destination)
        if destination:
            destinations.append(LinkDestination("image" if is_image else "link", destination))
        position = destination_end + 1

    return destinations


def _extract_reference_destinations(text: str) -> list[LinkDestination]:
    destinations: list[LinkDestination] = []
    for match in _REFERENCE_DESTINATION_RE.finditer(text):
        destination = _normalize_markdown_destination(match.group("destination"))
        if destination:
            destinations.append(LinkDestination("link", destination))
    return destinations


class _DestinationHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.destinations: list[LinkDestination] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value for name, value in attrs}
        if tag.lower() == "a" and attrs_dict.get("href"):
            self.destinations.append(LinkDestination("link", attrs_dict["href"] or ""))
        if tag.lower() == "img" and attrs_dict.get("src"):
            self.destinations.append(LinkDestination("image", attrs_dict["src"] or ""))


def _extract_html_destinations(text: str) -> list[LinkDestination]:
    parser = _DestinationHTMLParser()
    parser.feed(text)
    return parser.destinations


def _find_closing_bracket(text: str, opening_position: int) -> int:
    position = opening_position + 1
    while position < len(text):
        if text[position] == "]" and not _is_escaped(text, position):
            return position
        position += 1
    return -1


def _find_closing_paren(text: str, opening_position: int) -> int:
    depth = 0
    position = opening_position
    while position < len(text):
        char = text[position]
        if char == "\\":
            position += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return position
        position += 1
    return -1


def _normalize_markdown_destination(raw_destination: str) -> str:
    stripped = raw_destination.strip()
    if not stripped:
        return ""
    if stripped.startswith("<"):
        closing = stripped.find(">")
        return stripped[1:closing] if closing != -1 else stripped[1:]
    return stripped.split(maxsplit=1)[0]


def _is_escaped(text: str, position: int) -> bool:
    backslash_count = 0
    cursor = position - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslash_count += 1
        cursor -= 1
    return backslash_count % 2 == 1
