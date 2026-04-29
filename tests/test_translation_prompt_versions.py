"""Prompt pack versioning tests for translation_v2.

Run only this suite:
    uv run --extra dev pytest tests/test_translation_prompt_versions.py -q
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.artifacts import TranslationRunArtifacts  # noqa: E402
from translation_v2.prompt_registry import (  # noqa: E402
    PROMPT_STAGES,
    PROMPT_STAGES_V1,
    PROMPT_STAGES_V2,
    build_prompt_artifact_metadata,
    build_prompt_cache_key,
    compute_prompt_pack_fingerprint,
    compute_prompt_pack_fingerprint_from_templates,
    load_prompt_pack,
    load_prompt_template,
    prompt_template_path,
    render_prompt_template,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "translation_v2"
PROMPT_CASE_PATH = FIXTURES_DIR / "prompt_policy_regression_case.json"


def test_prompt_pack_loads_for_all_stages_and_stage_selection_is_valid():
    prompt_pack = load_prompt_pack(prompt_version="v2")
    cv_prompt_pack = load_prompt_pack(prompt_version="v2", artifact_type="cv")
    presentation_prompt_pack = load_prompt_pack(prompt_version="v2", artifact_type="presentation")

    assert tuple(prompt_pack.keys()) == PROMPT_STAGES_V2
    assert PROMPT_STAGES == PROMPT_STAGES_V2
    for stage in PROMPT_STAGES:
        template = load_prompt_template(stage, prompt_version="v2")
        assert template == prompt_pack[stage]
        assert prompt_template_path(stage, prompt_version="v2").exists()

        cv_template = load_prompt_template(stage, prompt_version="v2", artifact_type="cv")
        assert cv_template == cv_prompt_pack[stage]
        assert prompt_template_path(stage, prompt_version="v2", artifact_type="cv").exists()

        presentation_template = load_prompt_template(
            stage,
            prompt_version="v2",
            artifact_type="presentation",
        )
        assert presentation_template == presentation_prompt_pack[stage]
        assert (
            prompt_template_path(stage, prompt_version="v2", artifact_type="presentation").exists()
        )

    with pytest.raises(ValueError):
        load_prompt_template("unknown-stage", prompt_version="v2")

    assert tuple(load_prompt_pack(prompt_version="v1").keys()) == PROMPT_STAGES_V1


def test_all_stage_prompts_include_strict_output_contract_markers():
    required_contract_markers = (
        "OUTPUT CONTRACT",
        "BEGIN_OUTPUT_JSON",
        "END_OUTPUT_JSON",
    )

    for stage in PROMPT_STAGES:
        template = load_prompt_template(stage, prompt_version="v2")
        for marker in required_contract_markers:
            assert marker in template


def test_prompts_include_protected_token_policy_constraints():
    expected_markers = {
        "translate": ("inline code", "fenced code", "placeholders", "citation", "DO_NOT_TRANSLATE_ENTITIES"),
        "critique": ("placeholders", "citation", "DO_NOT_TRANSLATE_ENTITIES"),
        "revise": ("markdown links", "inline code", "fenced code", "placeholders", "citation", "DO_NOT_TRANSLATE_ENTITIES"),
    }

    for stage, markers in expected_markers.items():
        template = load_prompt_template(stage, prompt_version="v2")
        normalized = template.lower()
        for marker in markers:
            assert marker.lower() in normalized


def test_post_prompts_explicitly_guard_against_translationese():
    translate_template = load_prompt_template("translate", prompt_version="v2")
    critique_template = load_prompt_template("critique", prompt_version="v2")
    refine_template = load_prompt_template("revise", prompt_version="v2")

    assert "native {{target_locale}} prose" in translate_template
    assert "imported or translated" in translate_template
    assert "LOCALIZATION BRIEF" in translate_template
    assert "BORROWING CONVENTIONS" in translate_template
    assert "PUNCTUATION CONVENTIONS" in translate_template
    assert "DISCOURSE CONVENTIONS" in translate_template
    assert "calque" in critique_template.lower()
    assert "locale_naturalness" in critique_template
    assert "borrowing_consistency" in critique_template
    assert "rhetorical_structure" in critique_template
    assert "translated span" in critique_template.lower()
    assert "translated candidate" in refine_template.lower()


def test_cv_prompts_explicitly_guard_against_translationese():
    translate_template = load_prompt_template(
        "translate",
        prompt_version="v2",
        artifact_type="cv",
    )
    critique_template = load_prompt_template(
        "critique",
        prompt_version="v2",
        artifact_type="cv",
    )
    refine_template = load_prompt_template(
        "revise",
        prompt_version="v2",
        artifact_type="cv",
    )

    assert "native {{target_locale}} material" in translate_template
    assert "LOCALIZATION BRIEF" in translate_template
    assert "calque" in critique_template.lower()
    assert "locale_naturalness" in critique_template
    assert "translated span" in critique_template.lower()
    assert "education degree localization policy" in refine_template


def test_presentation_prompts_are_artifact_specific():
    post_translate_template = load_prompt_template("translate", prompt_version="v2")
    presentation_translate_template = load_prompt_template(
        "translate",
        prompt_version="v2",
        artifact_type="presentation",
    )
    presentation_revise_template = load_prompt_template(
        "revise",
        prompt_version="v2",
        artifact_type="presentation",
    )
    presentation_critique_template = load_prompt_template(
        "critique",
        prompt_version="v2",
        artifact_type="presentation",
    )

    assert presentation_translate_template != post_translate_template
    assert "<!-- presentation:slide ... -->" in presentation_translate_template
    assert "<!-- /presentation:slide -->" in presentation_translate_template
    assert "ids, layout, density" in presentation_translate_template
    assert "image destinations" in presentation_translate_template
    assert "simulated dialogue/transcript prose" in presentation_translate_template
    assert "<!-- presentation:slide ... -->" in presentation_revise_template
    assert presentation_critique_template == load_prompt_template("critique", prompt_version="v2")


def test_render_prompt_template_requires_exact_placeholder_set():
    with pytest.raises(KeyError):
        render_prompt_template(
            "translate",
            prompt_version="v2",
            context={
                "source_locale": "en-us",
                "target_locale": "pt-br",
                "locale_direction": "en-us->pt-br",
                "style_constraints": "- Keep concise",
                "localization_brief": "PT-BR localization brief",
                "borrowing_conventions": "- Keep expected borrowings stable",
                "punctuation_conventions": "- Normalize punctuation",
                "discourse_conventions": "- Rebuild connective flow",
                "register_conventions": "- Keep serious technical prose",
                "review_checks": "- Flag translationese",
                "writing_style_brief": "Dry, layered, structurally aware.",
                "glossary_entries": "- throughput => vazão",
            },
        )

    rendered = render_prompt_template(
        "translate",
        prompt_version="v2",
        context={
            "source_locale": "en-us",
            "target_locale": "pt-br",
            "locale_direction": "en-us->pt-br",
            "style_constraints": "- Keep concise",
            "localization_brief": "PT-BR localization brief",
            "borrowing_conventions": "- Keep expected borrowings stable",
            "punctuation_conventions": "- Normalize punctuation",
            "discourse_conventions": "- Rebuild connective flow",
            "register_conventions": "- Keep serious technical prose",
            "review_checks": "- Flag translationese",
            "writing_style_brief": "Dry, layered, structurally aware.",
            "glossary_entries": "- throughput => vazão",
            "do_not_translate_entities": "OpenAI",
            "source_markdown": "content",
            "source_analysis_json": "{}",
            "terminology_policy_json": "{}",
            "resolved_terminology_decisions_json": "[]",
            "education_degree_localization_policy_json": "{}",
            "extra": "unexpected",
        },
    )
    assert "unexpected" not in rendered


def test_render_prompt_template_treats_backslashes_as_literal_content():
    source_markdown = r"""Use \1 and \g<1> literally in docs.
Windows path: C:\temp\build\artifact.txt
"""
    rendered = render_prompt_template(
        "translate",
        prompt_version="v2",
        context={
            "source_locale": "en-us",
            "target_locale": "pt-br",
            "locale_direction": "en-us->pt-br",
            "style_constraints": "- Keep concise",
            "localization_brief": "PT-BR localization brief",
            "borrowing_conventions": "- Keep expected borrowings stable",
            "punctuation_conventions": "- Normalize punctuation",
            "discourse_conventions": "- Rebuild connective flow",
            "register_conventions": "- Keep serious technical prose",
            "review_checks": "- Flag translationese",
            "writing_style_brief": "Dry, layered, structurally aware.",
            "glossary_entries": "- throughput => vazão",
            "do_not_translate_entities": "OpenCode",
            "source_markdown": source_markdown,
            "source_analysis_json": "{}",
            "terminology_policy_json": "{}",
            "resolved_terminology_decisions_json": "[]",
            "education_degree_localization_policy_json": "{}",
        },
    )

    assert source_markdown in rendered


def test_prompt_pack_fingerprint_is_stable_and_detects_template_changes():
    baseline = compute_prompt_pack_fingerprint(prompt_version="v2")
    repeated = compute_prompt_pack_fingerprint(prompt_version="v2")
    assert baseline == repeated

    cv_baseline = compute_prompt_pack_fingerprint(prompt_version="v2", artifact_type="cv")
    cv_repeated = compute_prompt_pack_fingerprint(prompt_version="v2", artifact_type="cv")
    assert cv_baseline == cv_repeated

    prompt_pack = load_prompt_pack(prompt_version="v2")
    mutated_pack = dict(prompt_pack)
    mutated_pack["translate"] = mutated_pack["translate"] + "\nMUTATION"

    mutated_fingerprint = compute_prompt_pack_fingerprint_from_templates(
        templates_by_stage=mutated_pack,
        prompt_version="v2",
    )
    assert mutated_fingerprint != baseline
    assert cv_baseline != baseline

    cache_key = build_prompt_cache_key(
        "slug:hash:base",
        prompt_version="v2",
        prompt_fingerprint=baseline,
    )
    assert "prompt_version=v2" in cache_key
    assert f"prompt_fingerprint={baseline}" in cache_key


def test_cv_prompt_pack_fingerprint_uses_cv_templates():
    prompt_pack = load_prompt_pack(prompt_version="v2", artifact_type="cv")
    mutated_pack = dict(prompt_pack)
    mutated_pack["translate"] = mutated_pack["translate"] + "\nCV-ONLY-MUTATION"

    baseline = compute_prompt_pack_fingerprint(prompt_version="v2", artifact_type="cv")
    mutated = compute_prompt_pack_fingerprint_from_templates(
        templates_by_stage=mutated_pack,
        prompt_version="v2",
        artifact_type="cv",
    )

    assert mutated != baseline


def test_cv_prompt_templates_render_with_artifact_specific_contract():
    rendered = render_prompt_template(
        "translate",
        prompt_version="v1",
        artifact_type="cv",
        context={
            "source_locale": "en-us",
            "target_locale": "pt-br",
            "locale_direction": "en-us->pt-br",
            "style_constraints": "- Preserve tone",
            "writing_style_brief": "Opinionated, layered, structurally aware, dry.",
            "glossary_entries": "- throughput => vazão",
            "do_not_translate_entities": "- Nubank\n- Kubeflow",
            "source_markdown": '{"name":"Daniel","summary":"I build ML systems."}',
        },
    )

    assert '"experience"' in rendered
    assert '"education"' in rendered
    assert "Nubank" in rendered
    assert "Kubeflow" in rendered


def test_fixture_driven_prompt_regression_for_technical_markdown_and_citations(
    tmp_path,
):
    case = json.loads(PROMPT_CASE_PATH.read_text(encoding="utf-8"))
    entity_lines = "\n".join(f"- {item}" for item in case["do_not_translate_entities"])

    translate_prompt = render_prompt_template(
        "translate",
        prompt_version="v1",
        context={
            "source_locale": case["source_locale"],
            "target_locale": case["target_locale"],
            "locale_direction": f"{case['source_locale']}->{case['target_locale']}",
            "style_constraints": "- Keep an engineering blog tone",
            "writing_style_brief": "Opinionated, layered, structurally aware, dry.",
            "glossary_entries": "- throughput => vazão",
            "do_not_translate_entities": entity_lines,
            "source_markdown": case["source_markdown"],
        },
    )

    assert "[@smith2024]" in translate_prompt
    assert "{{USER_ID}}" in translate_prompt
    assert "%BUILD_SHA%" in translate_prompt
    assert "https://example.com/runbook" in translate_prompt
    assert "```bash" in translate_prompt
    for entity in case["do_not_translate_entities"]:
        assert entity in translate_prompt

    critique_prompt = render_prompt_template(
        "critique",
        prompt_version="v1",
        context={
            "source_locale": case["source_locale"],
            "target_locale": case["target_locale"],
            "locale_direction": f"{case['source_locale']}->{case['target_locale']}",
            "style_constraints": "- Keep an engineering blog tone",
            "writing_style_brief": "Opinionated, layered, structurally aware, dry.",
            "glossary_entries": "- throughput => vazão",
            "do_not_translate_entities": entity_lines,
            "source_markdown": case["source_markdown"],
            "translated_json": case["translated_json"],
        },
    )
    assert "TRANSLATED CANDIDATE JSON" in critique_prompt

    refine_prompt = render_prompt_template(
        "refine",
        prompt_version="v1",
        context={
            "source_locale": case["source_locale"],
            "target_locale": case["target_locale"],
            "locale_direction": f"{case['source_locale']}->{case['target_locale']}",
            "style_constraints": "- Keep an engineering blog tone",
            "writing_style_brief": "Opinionated, layered, structurally aware, dry.",
            "glossary_entries": "- throughput => vazão",
            "do_not_translate_entities": entity_lines,
            "source_markdown": case["source_markdown"],
            "translated_json": case["translated_json"],
            "critique_json": case["critique_json"],
        },
    )
    assert "CRITIQUE JSON" in refine_prompt

    fingerprint = compute_prompt_pack_fingerprint(prompt_version="v1")
    metadata = build_prompt_artifact_metadata(
        stage="translate",
        prompt_version="v1",
        prompt_fingerprint=fingerprint,
    )
    artifacts = TranslationRunArtifacts(run_id="prompt-regression", base_dir=tmp_path)
    artifacts.write_prompt(
        "technical-post",
        "translate",
        translate_prompt,
        prompt_version=metadata["prompt_version"],
        prompt_fingerprint=metadata["prompt_fingerprint"],
    )

    stage_dir = artifacts.stage_dir("technical-post", "translate")
    metadata_path = stage_dir / "prompt-metadata.json"
    written = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert written == {
        "prompt_version": "v1",
        "prompt_fingerprint": fingerprint,
    }
