"""Tests for blog-native presentation rendering."""

import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from renderer import generate_index_html, generate_post_html, generate_presentation_html  # noqa: E402


def sample_presentation():
    return {
        "title": "How I Use AI Agents",
        "excerpt": "What I built, what broke, and what survived.",
        "slug": "how-i-use-ai-agents",
        "date": "2026-04-30",
        "published_date": "2026-04-30",
        "reading_time": 18,
        "tags": ["AI Agents", "Workflow"],
        "content_type": "presentation",
        "year": 2026,
        "month": "April",
        "lang": "en-us",
        "slides": [
            {
                "id": "title",
                "layout": "lead",
                "title": "How I Use AI Agents",
                "subtitle": "What survived the work",
                "kicker": "dan.rio",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "A focused deck for blog-native rendering.",
                    }
                ],
            },
            {
                "id": "systems",
                "layout": "card_grid",
                "density": "dense",
                "blocks": [
                    {
                        "type": "card_grid",
                        "cards": [
                            {"title": "Builder", "body": "Turns intent into artifacts."},
                            {"title": "Reviewer", "body": "Finds weak assumptions."},
                        ],
                    },
                    {
                        "type": "table",
                        "headers": ["Mode", "Use"],
                        "rows": [["Plan", "Decide scope"], ["Run", "Produce output"]],
                    },
                ],
            },
            {
                "id": "code",
                "layout": "code",
                "density": "very_dense",
                "blocks": [
                    {
                        "type": "code",
                        "language": "html",
                        "code": "<script>alert('no')</script>",
                    },
                    {
                        "type": "quote",
                        "text": "The point is not automation theater.",
                        "cite": "Speaker note",
                    },
                ],
            },
        ],
    }


def test_generate_post_html_dispatches_to_presentation_renderer_and_includes_assets() -> None:
    html = generate_post_html(sample_presentation(), post_number=3, lang="en")

    assert 'class="container presentation-page"' in html
    assert "/static/css/presentation.css" in html
    assert "/static/js/presentation.js" in html
    assert 'data-presentation-page data-slide-count="3"' in html


def test_generate_presentation_html_emits_controls_progress_and_accessible_labels() -> None:
    html = generate_presentation_html(sample_presentation(), post_number=3, lang="en")

    assert 'aria-label="Presentation slides"' in html
    assert 'aria-label="Presentation controls"' in html
    assert 'data-presentation-action="previous" aria-label="Previous slide"' in html
    assert 'data-presentation-action="next" aria-label="Next slide"' in html
    assert 'data-presentation-action="fullscreen"' in html
    assert 'aria-label="Fullscreen"' in html
    assert 'data-label-exit="Exit fullscreen"' in html
    assert 'data-presentation-progress-text aria-live="polite">Slide 1 of 3<' in html
    assert 'role="progressbar"' in html
    assert 'aria-valuemin="1"' in html
    assert 'aria-valuemax="3"' in html
    assert 'aria-valuenow="1"' in html
    assert 'data-presentation-jump-form' in html
    assert 'data-presentation-slide-input' in html
    assert 'max="3"' in html
    assert 'Go to slide' in html


def test_generate_presentation_html_emits_stable_slide_ids_and_layout_metadata() -> None:
    html = generate_presentation_html(sample_presentation(), post_number=3, lang="en")

    assert html.count('class="presentation-slide ') == 3
    assert 'id="title"' in html
    assert 'data-slide-id="title"' in html
    assert 'data-slide-number="1"' in html
    assert 'aria-label="Slide 1 of 3"' in html
    assert 'id="systems"' in html
    assert 'data-layout="card_grid"' in html
    assert 'data-density="dense"' in html
    assert 'id="code"' in html
    assert 'data-density="very_dense"' in html
    code_slide = html[html.index('id="code"') : html.index('data-presentation-progress-text')]
    assert 'data-overflow="scroll"' not in code_slide


def test_generate_presentation_html_renders_blocks_and_escapes_text() -> None:
    html = generate_presentation_html(sample_presentation(), post_number=3, lang="en")

    assert '<article class="presentation-card">' in html
    assert '<h3 class="presentation-card-title">Builder</h3>' in html
    assert '<th>Mode</th>' in html
    assert '<td>Decide scope</td>' in html
    assert 'data-language="html"' in html
    assert "&lt;script&gt;alert(&#x27;no&#x27;)&lt;/script&gt;" in html
    assert "<script>alert('no')</script>" not in html
    assert "<blockquote><p>The point is not automation theater.</p><cite>Speaker note</cite></blockquote>" in html


def test_generate_presentation_html_includes_presentation_jsonld_hints() -> None:
    html = generate_presentation_html(sample_presentation(), post_number=3, lang="en")

    assert '"@type": "BlogPosting"' in html
    assert '"genre": "Presentation"' in html
    assert '"learningResourceType": "Presentation"' in html


def test_generate_index_html_marks_presentation_cards_without_breaking_post_contract() -> None:
    html = generate_index_html([sample_presentation()], lang="en")

    assert 'class="post-card" data-content-type="presentation"' in html
    assert 'data-content-type-marker="presentation">Presentation</span>' in html
    assert "/static/js/presentation.js" in html
    assert 'data-year="2026"' in html
    assert 'data-month="April"' in html
    assert 'data-tags="AI Agents,Workflow"' in html
