"""Reading navigation and citation identity survive localization and layout changes."""

import html5lib
import pytest

from markdown_refs import render_markdown_with_internal_refs
from reading_layout import compile_reading_layout
from translation_v2.durable import validate_artifact
from tests.test_translation_durability import source, TRANSLATION


def fragment(html):
    return html5lib.parseFragment(html, treebuilder="etree", namespaceHTMLElements=False)


def render(text, **kwargs):
    return compile_reading_layout(render_markdown_with_internal_refs(text), **kwargs)


def test_outline_keeps_every_heading_level_nested_and_excludes_permalink_labels():
    result = render("## One\n\n### Two\n\n#### Three\n\n## Four")
    nav = fragment(result.outline)
    assert [a.text for a in nav.iter("a")] == ["One", "Two", "Three", "Four"]
    assert nav.find(".//ol/li/ol/li/ol/li/a").get("href") == "#three"
    assert nav.findall(".//details/ol/li")[-1].find("a").get("href") == "#four"


def test_localized_outline_uses_source_heading_anchors():
    content = render_markdown_with_internal_refs(
        "## Decisão\n\nTexto", source_markdown="## Decision\n\nText"
    )
    result = compile_reading_layout(content, lang="pt")
    assert 'href="#decision">Decisão</a>' in result.outline
    assert 'aria-label="Neste artigo"' in result.outline


def test_outline_handles_skipped_heading_levels():
    result = render("## Parent\n\n#### Deeper\n\n### Sibling\n\n# Next")
    nav = fragment(result.outline)
    assert [a.text for a in nav.findall(".//details/ol/li/a")] == ["Parent", "Next"]
    assert [a.text for a in nav.findall(".//details/ol/li/ol/li/a")] == ["Deeper", "Sibling"]


def test_repeated_footnote_has_one_rich_note_without_return_links():
    result = render(
        "First[^note].\n\nAgain[^note].\n\n[^note]: A **rich** note with [a link](https://example.com)."
    )
    notes = fragment(result.notes)
    assert len(list(notes.iter("section"))) == 1
    assert "rich" == next(notes.iter("strong")).text
    returns = [a for a in notes.iter("a") if a.get("role") == "doc-backlink"]
    assert not returns
    assert [a.get("href") for a in notes.iter("a")] == ["https://example.com"]
    complete = fragment(result.content + result.notes)
    ids = [e.get("id") for e in complete.iter() if e.get("id")]
    assert len(ids) == len(set(ids))
    for anchor in complete.iter("a"):
        if anchor.get("href", "").startswith("#"):
            assert anchor.get("href")[1:] in ids


def test_existing_numeric_references_move_without_changing_original_targets():
    result = render("A finding [7].\n\n[7] Evidence from [the paper](https://example.com).")
    assert 'href="#ref-7"' in result.content
    assert 'id="ref-7"' in result.notes
    assert "Evidence from" not in result.content
    assert "Evidence from" in result.notes


def test_authored_named_footnote_and_first_use_anchors_survive():
    result = render(
        'Text <a id="first-use-pack"></a>Pack<sup>[1](#footnote-pack)</sup>.\n\n'
        '<a id="footnote-pack"></a>\n**[1] Pack:** Definition. [Back.](#first-use-pack)'
    )
    assert 'id="first-use-pack"' in result.content
    assert 'id="footnote-pack"' in result.notes
    assert "<strong>Pack:</strong>" in result.notes
    assert 'href="#first-use-pack"' not in result.notes


@pytest.mark.parametrize("label", ["**Sources:**", "**Fontes:**", "## References"])
def test_empty_sources_label_and_divider_disappear_when_entries_move(label):
    result = render(f"A finding [7].\n\n---\n\n{label}\n\n[7] The source.")
    body = fragment(result.content)
    assert not list(body.iter("hr"))
    assert not result.outline
    assert not any(word in "".join(body.itertext()) for word in ("Sources", "Fontes", "References"))
    assert "The source." in result.notes
    if label.startswith("##"):
        assert 'id="references"' in result.content


def test_source_section_with_uncited_entries_or_prose_is_preserved():
    result = render("A finding [7].\n\n## Sources\n\n[7] Cited.\n\n[8] Further reading.")
    assert 'href="#sources"' in result.outline
    assert "Further reading." in result.content


@pytest.mark.parametrize("label", ["Back to text.", "Voltar ao texto.", "Get back to reference", "Back to first use."])
def test_handwritten_return_links_are_removed_but_source_links_remain(label):
    result = render(
        f'A finding [7].\n\n[7] A source. [{label}](#block-001) '
        '[Read the discussion](#block-001). [Back](https://example.com).'
    )
    links = list(fragment(result.notes).iter("a"))
    assert [a.text for a in links] == ["Read the discussion", "Back"]


def test_uncited_references_and_code_examples_remain_in_the_article():
    result = render("```markdown\n## Code heading\n[7] Example\n```\n\n[8] Uncited source")
    assert not result.outline
    assert not result.notes
    assert "Code heading" in result.content
    assert "Uncited source" in result.content


def test_notes_do_not_remove_unrelated_trailing_headings_or_dividers():
    result = render("A finding [7].\n\n[7] Evidence.\n\n## Sources\n\n---")
    assert 'href="#sources"' in result.outline
    assert list(fragment(result.content).iter("hr"))


def test_translation_cannot_drop_or_rename_a_footnote_reference():
    original = "Read this[^note].\n\n[^note]: Supporting detail."
    with pytest.raises(RuntimeError, match="footnote identifiers"):
        validate_artifact(
            source(original),
            {**TRANSLATION, "content": "Leia isto.\n\n[^note]: Detalhe."},
            strict=False,
        )
    validate_artifact(
        source(original),
        {**TRANSLATION, "content": "Leia isto[^note].\n\n[^note]: Detalhe."},
        strict=False,
    )
