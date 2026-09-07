"""Protect program code and Mermaid flowchart syntax while localizing labels."""

import re
from collections import Counter

from presentation_translation import extract_fenced_code_blocks, strip_fenced_code_blocks


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
