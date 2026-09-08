"""Protect program code and Mermaid flowchart syntax while localizing labels."""

import re
from collections import Counter
from html.parser import HTMLParser

import markdown

from presentation_translation import extract_fenced_code_blocks, strip_fenced_code_blocks


class _ProseText(HTMLParser):
    """Read visible prose, excluding syntax, attributes, and executable content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"pre", "code", "script", "style"}:
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in {"pre", "code", "script", "style"}:
            self.ignored = max(0, self.ignored - 1)
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "figcaption"}:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def parenthetical_structure(text: str) -> list[str]:
    """Balanced prose parentheses, including nesting, in reading order.

    Markdown rendering excludes link destinations, image paths, and code. This
    checks delimiters, not the translated meaning inside them; editorial review
    still has to verify that each aside encloses the same thought.
    """
    prose = _ProseText()
    prose.feed(markdown.markdown(text, extensions=["fenced_code", "footnotes", "tables"]))
    structures = []
    for block in "".join(prose.parts).split("\n\n"):
        # Bare URLs are protected destinations, not authorial asides.
        # Keep an enclosing aside's closing parenthesis when a bare URL is its
        # final token; balanced parentheses within a URL belong to the URL.
        block = re.sub(
            r"https?://\S+",
            lambda match: ")" * max(0, match[0].count(")") - match[0].count("(")),
            block,
        )
        depth = 0
        current = ""
        for char in block:
            if char == "(":
                depth += 1
                current += char
            elif char == ")" and depth:
                depth -= 1
                current += char
                if depth == 0:
                    structures.append(current)
                    current = ""
    return structures


def validate_parenthetical_asides(source: str, translated: str) -> None:
    if parenthetical_structure(source) != parenthetical_structure(translated):
        raise RuntimeError(
            "Translation changed parenthetical asides: preserve parentheses around "
            "the same thoughts, including nested asides; localize their contents "
            "without replacing the delimiters with commas or dashes"
        )


def footnote_identity(markdown: str) -> Counter[str]:
    """Definitions and every reference must survive localization with the same label."""
    return Counter(re.findall(r"(?<!\\)\[\^([^\]\s]+)\]", strip_fenced_code_blocks(markdown)))


def protected_fences(markdown: str) -> list[str]:
    return [_signature(block) for block in extract_fenced_code_blocks(markdown)]


def _label(text: str) -> str:
    # Preserve embedded markup (including links and line breaks) in diagram labels.
    return "TEXT" + "".join(re.findall(r"<[^>]*>", text))


def _signature(block: str) -> str:
    lines = block.splitlines(keepends=True)
    if not re.fullmatch(r"\s*(?:`{3,}|~{3,})mermaid\s*", lines[0]):
        return block
    if not any(
        re.match(r"\s*(?:flowchart|graph)\s+(?:TB|TD|BT|RL|LR)\s*$", line) for line in lines[1:]
    ):
        return block  # Unknown diagram grammars keep the ordinary exact-code rule.
    normalized = []
    for line in lines:
        if line.lstrip().startswith("%%") or re.match(
            r"\s*(?:click|style|classDef|class|linkStyle)\b", line
        ):
            normalized.append(line)  # Directives and comments stay byte-for-byte.
            continue
        if re.match(r"\s*acc(?:Title|Descr):", line):
            line = re.sub(r"(?<=:)[^\r\n]*", " TEXT", line, count=1)
        else:
            # Quoted rectangular node/subgraph labels; identifiers and shapes remain.
            line = re.sub(
                r'\["((?:\\.|[^"\\])*)"\]', lambda match: '["' + _label(match[1]) + '"]', line
            )
            line = re.sub(r'\[([^\[\]"\r\n]*)\]', lambda match: "[" + _label(match[1]) + "]", line)
            if re.search(r"(?:--|==|\.->)", line):
                line = re.sub(r"\|([^|\r\n]*)\|", lambda match: "|" + _label(match[1]) + "|", line)
        normalized.append(line)
    return "".join(normalized)
