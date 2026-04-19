"""Tests for post-page annotation UI wiring."""

import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from renderer import generate_post_html  # noqa: E402


def test_generate_post_html_includes_annotations_runtime_and_ui_labels() -> None:
    post = {
        "title": "Deep links",
        "excerpt": "Section and passage links.",
        "slug": "deep-links",
        "date": "2026-04-19",
        "published_date": "2026-04-19",
        "reading_time": 4,
        "tags": ["systems"],
        "content": '<h2 class="section-heading" id="topic">Topic<a href="#topic" class="permalink-anchor heading-anchor" aria-label="Link to this section" data-share-label="Copy section link" data-copied-label="Link copied"><span class="permalink-glyph" aria-hidden="true">↗</span><span class="sr-only">Link to this section</span></a></h2><p class="linkable-block" id="block-001" data-block-id="block-001">Paragraph.</p>',
    }

    html = generate_post_html(post, post_number=1, lang="en")

    assert "/static/js/annotations.js" in html
    assert 'data-copy-section-link="Copy section link"' in html
    assert 'data-copy-passage-link="Copy passage link"' in html
    assert 'data-link-copied="Link copied"' in html


def test_generate_post_html_localizes_annotation_labels_for_portuguese() -> None:
    post = {
        "title": "Links profundos",
        "excerpt": "Seções e trechos.",
        "slug": "links-profundos",
        "date": "2026-04-19",
        "published_date": "2026-04-19",
        "reading_time": 4,
        "tags": ["sistemas"],
        "content": '<p class="linkable-block" id="block-001" data-block-id="block-001">Trecho.</p>',
    }

    html = generate_post_html(post, post_number=1, lang="pt")

    assert 'data-copy-section-link="Copiar link da seção"' in html
    assert 'data-copy-passage-link="Copiar link do trecho"' in html
    assert 'data-link-copied="Link copiado"' in html
