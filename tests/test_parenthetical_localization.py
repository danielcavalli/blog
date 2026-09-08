"""An author's aside stays an aside regardless of a model's quality rating."""

import json
import shutil
from pathlib import Path

import pytest

from translation_v2.protected_markdown import parenthetical_structure, validate_parenthetical_asides
from translation_v2.durable import validate_artifact, validate_new_translation
from tests.test_translation_durability import TRANSLATION, source


@pytest.mark.parametrize("translated", [
    "Não me incomoda pagar para construírem coisas (e ainda assim vê-las divergir).",
    "Não me incomoda pagar para construírem coisas (e ainda assim\nvê-las divergir).",
])
def test_localized_parenthetical_contents_can_change(translated):
    validate_parenthetical_asides(
        "I don't mind paying them to build things (and even then seeing them drift apart).",
        translated,
    )


@pytest.mark.parametrize("translated", [
    "Não me incomoda pagar para construírem coisas e, mesmo assim, vê-las divergir.",
    "Não me incomoda pagar para construírem coisas — e mesmo assim vê-las divergir.",
    "Não me incomoda pagar para construírem coisas. E mesmo assim elas divergem.",
    "Não me incomoda pagar para construírem coisas (e mesmo assim vê-las divergir.",
])
def test_lost_or_repunctuated_aside_is_rejected(translated):
    with pytest.raises(RuntimeError, match="parenthetical asides"):
        validate_parenthetical_asides(
            "I don't mind paying them to build things (and even then seeing them drift apart).",
            translated,
        )


def test_nested_asides_survive_links_formatting_and_code():
    original = '''A thought (with **emphasis**, [a link](https://example.com/a(b)), and `call(x)` (yes)).

```python
print("(not prose)")
```

<figure><img alt="(attribute)" src="/images/(example).jpg"><figcaption>Caption (an aside).</figcaption></figure>

1) A list marker, with [reference][r].

[r]: https://example.com/path(foo) "Title (metadata)"
'''
    assert parenthetical_structure(original) == ["(())", "()"]
    validate_parenthetical_asides(original, "Uma ideia (com ênfase (sim)).\n\nLegenda (um comentário).")
    with pytest.raises(RuntimeError, match="parenthetical asides"):
        validate_parenthetical_asides(original, "Uma ideia (com ênfase), sim.\n\nLegenda (um comentário).")


@pytest.mark.parametrize("url", ["https://example.com", "https://example.com/a(b)"])
def test_url_does_not_hide_the_closing_delimiter_of_an_aside(url):
    assert parenthetical_structure(f"A thought (see {url}).") == ["()"]
    assert parenthetical_structure(f"See {url} for the source.") == []
    with pytest.raises(RuntimeError, match="parenthetical asides"):
        validate_parenthetical_asides(f"A thought (see {url}).", f"Uma ideia, veja {url}.")


def test_new_gate_does_not_invalidate_already_accepted_content():
    original = source("This system (as I said) keeps its promises.")
    translated = {**TRANSLATION, "content": "Este sistema, como eu disse, cumpre suas promessas."}
    validate_artifact(original, translated, strict=False)
    with pytest.raises(RuntimeError, match="parenthetical asides"):
        validate_new_translation(original, translated, strict=False)


def test_parentheses_in_frontmatter_are_also_preserved():
    original = source()
    original["frontmatter"]["title"] = "My system (again)"
    with pytest.raises(RuntimeError, match="parenthetical asides"):
        validate_new_translation(original, TRANSLATION, strict=False)


def test_candidate_with_lost_aside_cannot_replace_accepted_content(tmp_path, monkeypatch):
    import translations
    from translation_v2.accepted import AcceptedTranslations

    original = source("This system (as I said) keeps its promises.")
    accepted = AcceptedTranslations(tmp_path / "_source/translations")
    previous = {**TRANSLATION, "content": "Este sistema (como eu disse) cumpre suas promessas."}
    accepted.accept(original, previous, {}, expected_revision=None)
    candidate = AcceptedTranslations(tmp_path / "candidate")
    shutil.copytree(accepted.root, candidate.root)
    current = candidate.current(original)
    candidate.accept(original, TRANSLATION, {"editorial_review": {"accept": True}},
                     expected_revision=translations.digest(current))
    monkeypatch.setattr(translations, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(translations, "discover_artifacts", lambda: [{"source": original, "attach_path": "example.md"}])
    assert translations.main(["accept", "example", "--candidate-dir", str(candidate.root)]) == 1
    assert accepted.current(original)["translation"] == previous


def test_failed_generated_repair_leaves_accepted_revision_unchanged(tmp_path, monkeypatch):
    from translation_v2.accepted import AcceptedTranslations
    from translation_v2.orchestrator import TranslationV2PostOrchestrator

    original = source("This system (as I said) keeps its promises.")
    store = AcceptedTranslations(tmp_path / "accepted")
    good = {**TRANSLATION, "content": "Este sistema (como eu disse) cumpre suas promessas."}
    store.accept(original, good, {}, expected_revision=None)
    before = store.current(original)
    runtime = TranslationV2PostOrchestrator(
        strict_validation=False, cache_dir=tmp_path / "cache", accepted_path=store.root, refresh=True,
    )
    requests = []

    def bad_model(request, **kwargs):
        requests.append(dict(request.metadata))
        return dict(TRANSLATION)

    monkeypatch.setattr(runtime, "_run_pipeline", bad_model)
    with pytest.raises(RuntimeError, match="parenthetical asides"):
        runtime.translate_artifact_if_needed(
            slug="example", source_text=original["text"], source_locale="en-us",
            target_locale="pt-br", artifact_type="post", frontmatter=original["frontmatter"],
        )
    assert len(requests) == 2
    assert "parenthetical asides" in requests[1]["deterministic_findings"]
    assert store.current(original) == before


def test_reported_loss_is_present_in_fixed_regression_fixture():
    case = json.loads(Path("tests/fixtures/translation_v2/pt_br_voice_regression.json").read_text())
    with pytest.raises(RuntimeError, match="parenthetical asides"):
        validate_parenthetical_asides(case["source"], case["rejected_translation"])
    validate_parenthetical_asides(case["source"], case["localized_example"])
