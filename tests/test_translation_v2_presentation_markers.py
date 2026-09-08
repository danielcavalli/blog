"""Presentation marker preservation tests for translation_v2 integration."""

from __future__ import annotations

import os
import sys
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


import build  # noqa: E402
from content_loader import parse_markdown_post  # noqa: E402


SOURCE = """<!-- presentation:slide id="intro" layout="lead" density="normal" -->
# Title

[Docs](https://example.com/docs)
![Image](/img/x.png)
<!-- /presentation:slide -->
"""


def test_parse_markdown_post_preserves_content_type(tmp_path):
    post_path = tmp_path / "deck.md"
    post_path.write_text(
        "---\ntitle: Deck\ndate: 2026-04-29\ncontent_type: presentation\n---\n"
        + SOURCE,
        encoding="utf-8",
    )

    post = parse_markdown_post(post_path)

    assert post["content_type"] == "presentation"


def test_prompt_pack_mentions_exact_presentation_marker_preservation():
    translate_prompt = Path(
        "_source/translation_v2/prompts/v2/presentation_translate.md"
    ).read_text(encoding="utf-8")
    revise_prompt = Path("_source/translation_v2/prompts/v2/presentation_revise.md").read_text(
        encoding="utf-8"
    )

    for prompt in (translate_prompt, revise_prompt):
        assert "<!-- presentation:slide ... -->" in prompt
        assert "<!-- /presentation:slide -->" in prompt
        assert "ids, layout, density" in prompt
        assert "link" in prompt
        assert "image" in prompt


def test_presentation_validator_accepts_exact_markers_and_destinations():
    translated = SOURCE.replace("# Title", "# Titulo")

    is_valid, issues = build.validate_presentation_translation(SOURCE, translated)

    assert is_valid is True
    assert issues == []


def test_presentation_validator_rejects_marker_drift():
    translated = SOURCE.replace('id="intro"', 'id="intro-pt"')

    is_valid, issues = build.validate_presentation_translation(SOURCE, translated)

    assert is_valid is False
    assert any("Slide ids/order changed" in issue for issue in issues)
