"""Tests for numeric in-document markdown references."""

import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from markdown_refs import (  # noqa: E402
    extract_heading_anchor_specs,
    preprocess_numeric_internal_references,
    render_markdown_with_internal_refs,
)


def test_preprocess_rewrites_numeric_reference_citation_and_anchor():
    md = "It is [updated frequently][7].\n\n[7] Reference item"

    processed = preprocess_numeric_internal_references(md)

    assert "updated frequently[[7]](#ref-7)" in processed
    assert '<span id="ref-7"></span>[7] Reference item' in processed


def test_render_outputs_clickable_numeric_citation_and_reference_target():
    md = "It is [updated frequently][7].\n\n[7] Reference item"

    html = render_markdown_with_internal_refs(md)

    assert '<a href="#ref-7">[7]</a>' in html
    assert 'id="ref-7"' in html
    assert "[updated frequently][7]" not in html


def test_external_links_are_unchanged():
    md = "Read [on X](https://x.com/example).\n\n[7] Reference item"

    html = render_markdown_with_internal_refs(md)

    assert '<a href="https://x.com/example">on X</a>' in html


def test_unknown_numeric_reference_is_not_rewritten():
    md = "Text [unknown citation][99].\n\n[7] Reference item"

    processed = preprocess_numeric_internal_references(md)
    html = render_markdown_with_internal_refs(md)

    assert "[unknown citation][99]" in processed
    assert "[unknown citation][99]" in html


def test_non_numeric_reference_label_is_not_rewritten():
    md = "Text [named citation][abc].\n\n[7] Reference item"

    processed = preprocess_numeric_internal_references(md)
    html = render_markdown_with_internal_refs(md)

    assert "[named citation][abc]" in processed
    assert "[named citation][abc]" in html


def test_bare_numeric_citation_is_rewritten_to_internal_anchor_link():
    md = "Context continuity is rebuilt [7].\n\n[7] Reference item"

    processed = preprocess_numeric_internal_references(md)
    html = render_markdown_with_internal_refs(md)

    assert "[[7]](#ref-7)" in processed
    assert '<a href="#ref-7">[7]</a>' in html


def test_unknown_bare_numeric_citation_is_not_rewritten():
    md = "Context continuity is rebuilt [7]."

    processed = preprocess_numeric_internal_references(md)
    html = render_markdown_with_internal_refs(md)

    assert "[7]" in processed
    assert '<a href="#ref-7">[7]</a>' not in html


def test_extract_heading_anchor_specs_supports_explicit_ids_and_dedupes() -> None:
    md = "## Topic {#custom-topic}\n\n## Topic\n\n## Topic"

    specs = extract_heading_anchor_specs(md)

    assert [spec.anchor_id for spec in specs] == [
        "custom-topic",
        "topic",
        "topic-2",
    ]


def test_render_adds_heading_ids_and_heading_permalinks() -> None:
    md = "## Topic heading\n\nParagraph text."

    html = render_markdown_with_internal_refs(md)

    assert 'id="topic-heading"' in html
    assert 'class="section-heading"' in html
    assert 'href="#topic-heading"' in html
    assert 'class="permalink-anchor heading-anchor"' in html
    assert 'class="permalink-glyph"' in html
    assert 'data-share-label="Copy section link"' in html
    assert 'data-copied-label="Link copied"' in html


def test_render_adds_block_ids_and_block_permalinks() -> None:
    md = "Paragraph text.\n\n- Bullet item"

    html = render_markdown_with_internal_refs(md)

    assert 'id="block-001"' in html
    assert 'data-block-id="block-001"' in html
    assert 'id="block-002"' in html


def test_render_uses_source_markdown_heading_ids_for_translated_markdown() -> None:
    source_md = "## O elo de design\n\nTexto."
    translated_md = "## The design link\n\nText."

    html = render_markdown_with_internal_refs(
        translated_md,
        source_markdown=source_md,
    )

    assert 'id="o-elo-de-design"' in html
    assert 'href="#o-elo-de-design"' in html
    assert 'id="the-design-link"' not in html


def test_render_does_not_inject_block_permalink_into_paragraph_wrapping_code_block() -> None:
    md = "Intro:\n```text\ncontent\n```"

    html = render_markdown_with_internal_refs(md)

    assert 'class="linkable-block" data-block-id="block-001" id="block-001"' in html
    assert '<p class="linkable-block" data-block-id="block-002" id="block-002"><pre>' not in html
    assert '<pre class="linkable-block" data-block-id="block-002" id="block-002">' in html
    assert 'class="permalink-anchor block-anchor"' not in html
