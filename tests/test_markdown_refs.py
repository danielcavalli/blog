"""Tests for numeric in-document markdown references."""

import os
import sys

import html5lib
import pytest

_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from markdown_refs import (  # noqa: E402
    extract_heading_anchor_specs,
    render_markdown_with_internal_refs,
)


@pytest.mark.parametrize("code", [
    "`[7]`", "``[label][7]``", "`multi\n[7]`",
    "~~~text\n[7]\n~~~", "````text\n```\n[7]\n````",
    "    [7]", "    [label][7]",
])
def test_numeric_references_never_rewrite_authored_code(code):
    import markdown

    text = f"{code}\n\nActual citation [7].\n\n[7] Evidence."
    expected = html5lib.parseFragment(markdown.markdown(text, extensions=["fenced_code"]), namespaceHTMLElements=False)
    actual = html5lib.parseFragment(render_markdown_with_internal_refs(text), namespaceHTMLElements=False)
    assert [e.text for e in actual.iter("code")] == [e.text for e in expected.iter("code")]
    assert len([a for a in actual.iter("a") if a.get("href") == "#ref-7"]) == 1


def test_numeric_references_preserve_escapes_and_link_destinations():
    text = r"Literal \[7]. [Link](https://example.com/[7]) and [real][7]." + "\n\n[7] Evidence."
    actual = html5lib.parseFragment(render_markdown_with_internal_refs(text), namespaceHTMLElements=False)
    assert [a.get("href") for a in actual.iter("a")] == ["https://example.com/[7]", "#ref-7"]


def test_setext_and_atx_headings_share_source_anchors_across_locales():
    source = "First\n=====\n\n~~~markdown\n# Code heading\n~~~\n\n## Second {#stable}"
    translated = "Primeiro\n========\n\n~~~markdown\n# Code heading\n~~~\n\n## Segundo {#stable}"
    assert [s.anchor_id for s in extract_heading_anchor_specs(source)] == ["first", "stable"]
    actual = html5lib.parseFragment(render_markdown_with_internal_refs(translated, source_markdown=source), namespaceHTMLElements=False)
    assert [e.get("id") for e in actual.iter() if e.tag in {"h1", "h2"}] == ["first", "stable"]


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

    html = render_markdown_with_internal_refs(md)

    assert "[unknown citation][99]" in html


def test_non_numeric_reference_label_is_not_rewritten():
    md = "Text [named citation][abc].\n\n[7] Reference item"

    html = render_markdown_with_internal_refs(md)

    assert "[named citation][abc]" in html


def test_bare_numeric_citation_is_rewritten_to_internal_anchor_link():
    md = "Context continuity is rebuilt [7].\n\n[7] Reference item"

    html = render_markdown_with_internal_refs(md)

    assert '<a href="#ref-7">[7]</a>' in html


def test_unknown_bare_numeric_citation_is_not_rewritten():
    md = "Context continuity is rebuilt [7]."

    html = render_markdown_with_internal_refs(md)

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


def test_native_theme_figure_keeps_attributes_and_valid_block_structure() -> None:
    md = '''Intro.

<figure class="post-figure theme-media" id="hub-view">
  <picture data-theme-variant="light">
    <source media="(max-width: 560px)" srcset="/day-mobile.svg" width="400" height="900">
    <img src="/day.svg" alt="Day view" width="960" height="660">
  </picture>
  <picture data-theme-variant="dark"><img src="/night.svg" alt="Night view"></picture>
  <figcaption>A &amp; B.</figcaption>
</figure>

After the figure.
'''
    rendered = render_markdown_with_internal_refs(md)
    parser = html5lib.HTMLParser(namespaceHTMLElements=False)
    fragment = parser.parseFragment(rendered)
    assert not parser.errors
    figure = fragment.find("figure")
    assert figure is not None
    assert figure.get("id") == "hub-view"
    assert figure.get("data-block-id") == "hub-view"
    assert set(figure.get("class", "").split()) == {
        "post-figure", "theme-media", "linkable-block"
    }
    assert [p.get("data-theme-variant") for p in figure.findall("picture")] == ["light", "dark"]
    source = figure.find("picture/source")
    assert source is not None
    assert source.get("srcset") == "/day-mobile.svg"
    assert source.get("width") == "400"
    assert figure.findtext("figcaption") == "A & B."
    assert len(fragment.findall("p")) == 2
