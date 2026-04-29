import pytest

from presentation_compiler import (
    PresentationCompileError,
    compile_presentation_markdown,
    presentation_document_from_dict,
    presentation_document_to_dict,
)


def test_compiles_marked_markdown_slides_and_renders_html_without_post_permalinks() -> None:
    body = """Intro copy outside slides.

<!-- presentation:slide id="title" layout="lead" density="normal" -->
# Title

Opening text.
<!-- /presentation:slide -->

<!-- presentation:slide id="code" layout="code" density="dense" -->
```text
<!-- presentation:slide id="not-real" layout="content" density="normal" -->
```

| A | B |
| - | - |
| 1 | 2 |
<!-- /presentation:slide -->
"""

    document = compile_presentation_markdown(body, expected_slide_count=2)

    assert document.slide_count == 2
    assert document.ids == ("title", "code")
    assert document.slides[0].layout == "lead"
    assert document.slides[1].density == "dense"
    assert "<h1>Title</h1>" in document.slides[0].html
    assert '<div class="presentation-table-wrap" data-overflow="scroll"><table>' in (
        document.slides[1].html
    )
    assert "not-real" in document.slides[1].markdown
    assert "permalink-anchor" not in document.slides[0].html
    assert "linkable-block" not in document.slides[0].html


def test_rejects_duplicate_slide_ids() -> None:
    body = """<!-- presentation:slide id="same" layout="content" density="normal" -->
One
<!-- /presentation:slide -->
<!-- presentation:slide id="same" layout="content" density="normal" -->
Two
<!-- /presentation:slide -->
"""

    with pytest.raises(PresentationCompileError, match="Duplicate presentation slide id"):
        compile_presentation_markdown(body)


def test_promotes_structural_block_markers_to_semantic_html() -> None:
    body = """<!-- presentation:slide id="cards" layout="card_grid" density="normal" -->
<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Builder

Owns implementation.
<!-- /presentation:card -->
<!-- presentation:card -->
### Reviewer

Checks quality.
<!-- /presentation:card -->
<!-- /presentation:block -->
<!-- /presentation:slide -->

<!-- presentation:slide id="split" layout="split" density="normal" -->
<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Left

One side.
<!-- /presentation:column -->
<!-- presentation:column -->
### Right

Other side.
<!-- /presentation:column -->
<!-- /presentation:block -->
<!-- /presentation:slide -->
"""

    document = compile_presentation_markdown(body, expected_slide_count=2)

    cards_html = document.slides[0].html
    split_html = document.slides[1].html

    assert '<div class="presentation-card-grid presentation-block">' in cards_html
    assert cards_html.count('<article class="presentation-card">') == 2
    assert "<!-- presentation:card -->" not in cards_html
    assert '<div class="presentation-split presentation-block">' in split_html
    assert split_html.count('<section class="presentation-column">') == 2


def test_rejects_unknown_layout_and_density() -> None:
    unknown_layout = """<!-- presentation:slide id="one" layout="unknown" density="normal" -->
One
<!-- /presentation:slide -->
"""
    unknown_density = """<!-- presentation:slide id="one" layout="content" density="crowded" -->
One
<!-- /presentation:slide -->
"""

    with pytest.raises(PresentationCompileError, match="Unknown presentation slide layout"):
        compile_presentation_markdown(unknown_layout)

    with pytest.raises(PresentationCompileError, match="Unknown presentation slide density"):
        compile_presentation_markdown(unknown_density)


def test_rejects_missing_and_unbalanced_markers() -> None:
    with pytest.raises(PresentationCompileError, match="No presentation slide markers found"):
        compile_presentation_markdown("# Plain post")

    with pytest.raises(PresentationCompileError, match="missing a closing marker"):
        compile_presentation_markdown(
            """<!-- presentation:slide id="one" layout="content" density="normal" -->
One
"""
        )

    with pytest.raises(PresentationCompileError, match="without opener"):
        compile_presentation_markdown("<!-- /presentation:slide -->")


def test_validates_expected_slide_count() -> None:
    body = """<!-- presentation:slide id="one" layout="content" density="normal" -->
One
<!-- /presentation:slide -->
"""

    with pytest.raises(PresentationCompileError, match="Expected 2 presentation slides, found 1"):
        compile_presentation_markdown(body, expected_slide_count=2)


def test_serializes_and_deserializes_document_model() -> None:
    body = """<!-- presentation:slide id="one" layout="content" density="normal" -->
One
<!-- /presentation:slide -->
"""

    document = compile_presentation_markdown(body)
    payload = presentation_document_to_dict(document)
    restored = presentation_document_from_dict(payload)

    assert payload["slide_count"] == 1
    assert restored == document
