"""Authoring policy is read as context; source and locale rules retain authority."""

import pytest

from translation_v2.style_loader import AUTHORING_REFERENCES, load_writing_style_brief
from translation_v2.artifacts import TranslationRunArtifacts
from translation_v2.providers.opencode import OpenCodeTranslationProvider
from tests.test_opencode_provider_loop import (
    _FakeRunner, _request_without_locale_metadata, _source_analysis_result,
    _terminology_policy_result, _translation_result, _critique_result,
    _revision_result, _final_review_result,
)


def test_each_authoring_reference_is_loaded_once():
    context = load_writing_style_brief()
    for _, path in AUTHORING_REFERENCES:
        assert context.count(path.read_text().strip()) == 1


def test_missing_or_empty_authoring_context_cannot_silently_weaken_translation(tmp_path):
    path = tmp_path / "missing.md"
    with pytest.raises(FileNotFoundError):
        load_writing_style_brief(path)
    path.write_text("\n")
    with pytest.raises(ValueError, match="Empty authoring reference"):
        load_writing_style_brief(path)


@pytest.mark.parametrize("locales", [("en-us", "pt-br"), ("pt-br", "en-us")])
def test_every_localization_stage_preserves_source_authority(tmp_path, locales):
    request = _request_without_locale_metadata(source_locale=locales[0], target_locale=locales[1])
    request.metadata["writing_style_brief"] = load_writing_style_brief()
    original = request.source_text
    runner = _FakeRunner([
        _source_analysis_result(), _terminology_policy_result(), _translation_result("Texto localizado."),
        _critique_result(95, needs_refinement=True), _revision_result("Texto localizado."), _final_review_result(accept=True, publish_ready=True),
    ])
    provider = OpenCodeTranslationProvider(runner=runner, default_attach_path=str(tmp_path), artifacts=TranslationRunArtifacts(
        run_id="authoring-boundary", base_dir=tmp_path,
    ))
    provider.run_translation_pipeline(request)
    assert request.source_text == original
    assert len(runner.calls) == 6
    for call in runner.calls:
        assert "The source is already authored and is authoritative." in call["prompt_text"]
        assert "Revision instructions apply to the localized artifact." in call["prompt_text"]
    analysis = runner.calls[0]["prompt_text"]
    assert load_writing_style_brief() in analysis
    assert "LOCALIZATION BRIEF" in analysis
    assert f"Target locale: {locales[1]}" in analysis
