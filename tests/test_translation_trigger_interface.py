"""Requests and explicit revisions through the accepted-content update path."""

import json

from translation_v2.accepted import AcceptedTranslations, digest
from translation_v2.orchestrator import TranslationV2PostOrchestrator
from translation_v2.revision_manifest import TranslationRevisionManifest
from translation_v2.trigger import derive_idempotency_key
from tests.test_translation_durability import source, TRANSLATION


def make_runtime(tmp_path):
    return TranslationV2PostOrchestrator(
        strict_validation=False, cache_dir=tmp_path / "cache",
        accepted_path=tmp_path / "accepted", run_id="update-example",
    )


def update(runtime, original=None, **kwargs):
    original = original or source()
    return runtime.translate_artifact_if_needed(
        slug=original["slug"], source_text=original["text"],
        source_locale=original["source_locale"], target_locale=original["target_locale"],
        artifact_type=original["artifact_type"], frontmatter=original["frontmatter"], **kwargs,
    )


def test_request_and_saved_trigger_preserve_source_and_correlation(tmp_path, monkeypatch):
    runtime = make_runtime(tmp_path)
    requests = []

    def pipeline(request, *, existing_translation=None):
        assert existing_translation is None
        requests.append(request)
        return TRANSLATION

    monkeypatch.setattr(runtime, "_run_pipeline", pipeline)
    assert update(runtime, do_not_translate_entities=["CUDA"]) == TRANSLATION
    request = requests[0]
    assert request.source_text == source()["text"]
    assert request.metadata["artifact_type"] == "post"
    assert {key: request.metadata[key] for key in ("title", "excerpt", "tags")} == source()["frontmatter"]
    assert request.metadata["writing_style_brief"]
    assert request.metadata["do_not_translate_entities"] == ["CUDA"]
    assert request.metadata["correlation_id"] == runtime.run_id
    expected = derive_idempotency_key(slug="example", source_text=source()["text"], target_locale="pt-br")
    assert request.metadata["idempotency_key"] == expected
    event = json.loads((runtime.artifacts.run_dir / "posts/example/trigger/event.json").read_text())
    assert event["source_text"] == source()["text"]
    assert event["idempotency_key"] == expected
    assert event["correlation_id"] == runtime.run_id
    assert AcceptedTranslations(tmp_path / "accepted").current(source())["translation"] == TRANSLATION


def test_revision_notes_are_applied_once_and_preserved_with_acceptance(tmp_path, monkeypatch):
    runtime = make_runtime(tmp_path)
    store = AcceptedTranslations(tmp_path / "accepted")
    store.accept(source(), TRANSLATION, {}, expected_revision=None)
    manifest = tmp_path / "revision.yaml"
    manifest.write_text("posts:\n  example:\n    pt-br:\n      notes: Preserve the dry humor\n")
    runtime.revision_manifest = TranslationRevisionManifest(manifest)
    requests = []

    def pipeline(request, *, existing_translation=None):
        assert existing_translation == TRANSLATION
        requests.append(request)
        return {**TRANSLATION, "title": "Revisado"}

    monkeypatch.setattr(runtime, "_run_pipeline", pipeline)
    assert update(runtime)["title"] == "Revisado"
    accepted = store.current(source())
    assert requests[0].metadata["revision_request"]["notes"] == "Preserve the dry humor"
    assert accepted["provenance"]["revision_marker"] == runtime.revision_manifest.get(slug="example", target_locale="pt-br").marker
    assert update(runtime)["title"] == "Revisado"
    assert len(requests) == 1
    assert digest(store.current(source())) == digest(accepted)


def test_source_revision_preserves_previous_acceptance_and_supplies_both_sources(tmp_path, monkeypatch):
    runtime = make_runtime(tmp_path)
    store = AcceptedTranslations(tmp_path / "accepted")
    previous = store.accept(source(), TRANSLATION, {}, expected_revision=None)
    original = source("The revised source makes a different point.")

    def pipeline(request, *, existing_translation=None):
        assert existing_translation == TRANSLATION
        assert request.source_text == original["text"]
        assert request.metadata["previous_source"] == source()
        return {**TRANSLATION, "content": "A fonte revisada apresenta outra ideia."}

    monkeypatch.setattr(runtime, "_run_pipeline", pipeline)
    translated = update(runtime, original)
    current = store.current(original)
    assert current["translation"] == translated
    assert current["source"] == original
    assert current["parent_revision"] == previous
    assert store.revision(source(), previous)["translation"] == TRANSLATION


def test_presentations_use_their_structural_gate_in_strict_updates(tmp_path, monkeypatch):
    runtime = make_runtime(tmp_path)
    runtime.strict_validation = True
    original = source('<!-- presentation:slide id="intro" layout="lead" density="normal" -->\n# Daniel Cavalli\n\n<content>literal transcript text\n<!-- /presentation:slide -->')
    original["artifact_type"] = "presentation"
    translated = {**TRANSLATION, "content": original["text"]}
    monkeypatch.setattr(runtime, "_run_pipeline", lambda *a, **k: translated)

    def fail(*a, **k):
        raise AssertionError("generic prose heuristics cannot validate a presentation")

    monkeypatch.setattr("translation_v2.durable.validate_translation", fail)
    assert update(runtime, original) == translated
