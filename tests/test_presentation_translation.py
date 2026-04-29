import pytest

from presentation_translation import (
    LinkDestination,
    PresentationTranslationInvariantError,
    assert_presentation_translation_invariants,
    compare_presentation_translation_invariants,
    extract_fenced_code_blocks,
    extract_markdown_destinations,
)


SOURCE = """<!-- presentation:slide id="intro" layout="content" density="normal" -->
# Context

Read [the docs](https://example.com/docs) and inspect ![diagram](./diagram.png).

```yaml
service:
  name: agent
```
<!-- /presentation:slide -->

<!-- presentation:slide id="closing" layout="quote" density="dense" -->
> Keep the structure stable.

<a href="/en/blog/source.html">Source</a>
<img src="./profile.png" alt="Profile">
<!-- /presentation:slide -->
"""


TRANSLATED = """<!-- presentation:slide id="intro" layout="content" density="normal" -->
# Contexto

Leia [a documentacao](https://example.com/docs) e inspecione ![diagrama](./diagram.png).

```yaml
service:
  name: agent
```
<!-- /presentation:slide -->

<!-- presentation:slide id="closing" layout="quote" density="dense" -->
> Mantenha a estrutura estavel.

<a href="/en/blog/source.html">Fonte</a>
<img src="./profile.png" alt="Perfil">
<!-- /presentation:slide -->
"""


def test_accepts_translated_text_when_structural_invariants_hold() -> None:
    issues = compare_presentation_translation_invariants(
        SOURCE,
        TRANSLATED,
        expected_slide_count=2,
    )

    assert issues == []


def test_reports_marker_drift_for_id_layout_and_density_changes() -> None:
    changed = TRANSLATED.replace('id="intro"', 'id="abertura"', 1)
    changed = changed.replace('layout="quote"', 'layout="content"', 1)
    changed = changed.replace('density="dense"', 'density="normal"', 1)

    issues = compare_presentation_translation_invariants(SOURCE, changed)

    assert {issue.code for issue in issues} >= {"slide_ids", "layout", "density"}


def test_reports_changed_code_fences_by_default() -> None:
    changed = TRANSLATED.replace("```yaml", "```json")

    issues = compare_presentation_translation_invariants(SOURCE, changed)

    assert any(issue.code == "code_fences" and issue.slide_id == "intro" for issue in issues)


def test_allows_localized_code_fence_content_when_structure_is_stable() -> None:
    changed = TRANSLATED.replace("name: agent", "name: agente")

    issues = compare_presentation_translation_invariants(
        SOURCE,
        changed,
    )

    assert not any(issue.code == "code_fences" for issue in issues)


def test_can_skip_code_fence_structure_preservation_when_requested() -> None:
    changed = TRANSLATED.replace("```yaml", "```json")

    issues = compare_presentation_translation_invariants(
        SOURCE,
        changed,
        preserve_code_fences=False,
    )

    assert not any(issue.code == "code_fences" for issue in issues)


def test_reports_changed_markdown_and_html_destinations() -> None:
    changed = TRANSLATED.replace("https://example.com/docs", "https://example.com/pt")
    changed = changed.replace("./profile.png", "./perfil.png")

    issues = compare_presentation_translation_invariants(SOURCE, changed)

    assert any(issue.code == "destinations" and issue.slide_id == "intro" for issue in issues)
    assert any(issue.code == "destinations" and issue.slide_id == "closing" for issue in issues)


def test_reports_missing_or_invalid_markers_in_translation() -> None:
    missing_close = TRANSLATED.replace("<!-- /presentation:slide -->", "", 1)

    issues = compare_presentation_translation_invariants(SOURCE, missing_close)

    assert any(issue.code == "translated_markers" for issue in issues)


def test_strict_assertion_raises_structured_error() -> None:
    changed = TRANSLATED.replace("./diagram.png", "./diagram-pt.png")

    with pytest.raises(PresentationTranslationInvariantError) as exc_info:
        assert_presentation_translation_invariants(SOURCE, changed)

    assert [issue.code for issue in exc_info.value.issues] == ["destinations"]


def test_extractors_ignore_marker_text_and_links_inside_code_fences() -> None:
    markdown = """Before [link](https://example.com).

```text
<!-- presentation:slide id="fake" layout="content" density="normal" -->
[not a link](https://changed.example)
```
"""

    assert extract_fenced_code_blocks(markdown) == [
        """```text
<!-- presentation:slide id="fake" layout="content" density="normal" -->
[not a link](https://changed.example)
```
"""
    ]
    assert extract_markdown_destinations(markdown) == [
        LinkDestination("link", "https://example.com"),
    ]
