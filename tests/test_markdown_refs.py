"""Tests for numeric in-document markdown references."""

import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from markdown_refs import (  # noqa: E402
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
