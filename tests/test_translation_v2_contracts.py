"""Unit tests for translation_v2 contracts and provider interface."""

import os
import sys
import types
from typing import Any

import pytest


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)
_mock_provider_stub = types.ModuleType("translation_v2.mock_provider")
_mock_provider_stub.DeterministicMockTranslationProvider = object
sys.modules.setdefault("translation_v2.mock_provider", _mock_provider_stub)

from translation_v2.contracts import (  # noqa: E402
    CVTranslationOutput,
    CritiqueOutput,
    FinalReviewOutput,
    RevisionOutput,
    TerminologyPolicyPacket,
    TranslationOutput,
    TranslationRequest,
    VoiceIntentPacket,
    validate_cv_translation_output,
    validate_critique_output,
    validate_final_review_output,
    validate_revision_output,
    validate_terminology_policy_output,
    validate_voice_intent_output,
    validate_refinement_output,
    validate_translation_output,
)
from translation_v2.errors import MissingFieldError, TypeMismatchError  # noqa: E402
from translation_v2.provider import TranslationProvider  # noqa: E402


def test_validate_translation_output_accepts_valid_payload():
    payload = {
        "title": "Titulo",
        "excerpt": "Resumo",
        "tags": ["ia", "agentes"],
        "content": "Conteudo traduzido",
    }

    result = validate_translation_output(payload, run_id="run-1")

    assert result == TranslationOutput(
        title="Titulo",
        excerpt="Resumo",
        tags=["ia", "agentes"],
        content="Conteudo traduzido",
    )


def test_validate_translation_output_rejects_missing_field_with_metadata():
    payload = {
        "title": "Title",
        "excerpt": "Summary",
        "content": "Translated content",
    }

    with pytest.raises(MissingFieldError) as excinfo:
        validate_translation_output(payload, run_id="run-missing", stage="translate")

    err = excinfo.value
    assert err.field == "tags"
    assert err.run_id == "run-missing"
    assert err.stage == "translate"


def test_validate_cv_translation_output_accepts_valid_payload():
    payload = {
        "name": "Daniel Cavalli",
        "tagline": "Engenheiro de ML",
        "location": "Rio de Janeiro, Brazil",
        "contact": {"linkedin": "https://example.com/in/dan"},
        "skills": ["MLOps", "Kubeflow"],
        "languages_spoken": ["Portuguese", "English"],
        "summary": "Resumo profissional",
        "experience": [
            {
                "title": "Senior Machine Learning Engineer",
                "company": "Nubank",
                "location": "Brazil",
                "period": "2026 - Present",
                "description": "Liderando evolucao da plataforma.",
                "achievements": ["Construiu pipelines distribuidos."],
            }
        ],
        "education": [
            {
                "degree": "Bacharelado em Economia",
                "school": "Federal University of Rio de Janeiro",
                "period": "2017 - 2023",
            }
        ],
    }

    result = validate_cv_translation_output(payload, run_id="run-cv")

    assert isinstance(result, CVTranslationOutput)
    assert result.name == "Daniel Cavalli"
    assert result.contact["linkedin"] == "https://example.com/in/dan"
    assert result.experience[0].company == "Nubank"
    assert result.experience[0].achievements == ["Construiu pipelines distribuidos."]


def test_validate_cv_translation_output_rejects_invalid_nested_field():
    payload = {
        "name": "Daniel Cavalli",
        "tagline": "Engenheiro de ML",
        "location": "Rio de Janeiro, Brazil",
        "contact": {"linkedin": "https://example.com/in/dan"},
        "skills": ["MLOps", "Kubeflow"],
        "languages_spoken": ["Portuguese", "English"],
        "summary": "Resumo profissional",
        "experience": [
            {
                "title": "Senior Machine Learning Engineer",
                "company": "Nubank",
                "location": "Brazil",
                "period": "2026 - Present",
                "description": "Liderando evolucao da plataforma.",
                "achievements": ["ok", 1],
            }
        ],
        "education": [
            {
                "degree": "Bacharelado em Economia",
                "school": "Federal University of Rio de Janeiro",
                "period": "2017 - 2023",
            }
        ],
    }

    with pytest.raises(TypeMismatchError) as excinfo:
        validate_cv_translation_output(payload, run_id="run-cv-bad", stage="translate")

    err = excinfo.value
    assert err.field == "experience[0].achievements"
    assert err.run_id == "run-cv-bad"
    assert err.stage == "translate"


def test_validate_critique_output_rejects_invalid_findings_shape():
    payload = {
        "score": 88,
        "feedback": "Looks mostly good",
        "needs_refinement": False,
        "findings": "not-a-list",
    }

    with pytest.raises(TypeMismatchError) as excinfo:
        validate_critique_output(payload, run_id="run-critique", stage="critique")

    err = excinfo.value
    assert err.field == "findings"
    assert err.run_id == "run-critique"
    assert err.stage == "critique"


def test_validate_critique_output_accepts_structured_metrics_payload():
    payload = {
        "overall_score": 93,
        "decision_hint": "auto_refine",
        "confidence": 0.82,
        "dimensions": [
            {"name": "accuracy_completeness", "score_100": 94},
            {"name": "terminology_entities", "score_100": 79},
            {"name": "markdown_code_link_fidelity", "score_100": 97},
        ],
        "error_summary": {"minor": 2, "major": 1, "critical": 0},
        "feedback": "Terminology needs one pass",
        "findings": [
            {
                "description": "One term is mistranslated",
                "source_span": "throughput",
                "target_span": "taxa",
            }
        ],
    }

    result = validate_critique_output(payload, run_id="run-structured")

    assert isinstance(result, CritiqueOutput)
    assert result.score == 93.0
    assert result.needs_refinement is True
    assert result.dimension_scores["terminology_entities"] == 79.0
    assert result.critical_errors == 0
    assert result.major_core_errors == 1
    assert result.confidence == 0.82


def test_validate_critique_output_keeps_simple_payload_compatibility():
    payload = {
        "score": 91,
        "feedback": "Looks mostly good",
        "needs_refinement": False,
        "findings": ["Minor punctuation issue"],
    }

    result = validate_critique_output(payload, run_id="run-simple")

    assert result.score == 91.0
    assert result.needs_refinement is False
    assert result.critical_errors == 0
    assert result.major_core_errors == 0
    assert result.dimension_scores["accuracy_completeness"] == 91.0


def test_validate_voice_intent_output_accepts_expected_packet_shape():
    payload = {
        "author_voice_summary": "Dry, technical, structurally aware.",
        "tone": "technical",
        "register": "professional",
        "sentence_rhythm": ["medium cadence"],
        "connective_tissue": ["contrastive pivots"],
        "rhetorical_moves": ["claim then qualification"],
        "humor_signals": ["understated irony"],
        "stance_markers": ["first-person ownership"],
        "must_preserve": ["OpenCode"],
    }

    result = validate_voice_intent_output(payload, run_id="run-source-analysis")

    assert isinstance(result, VoiceIntentPacket)
    assert result.tone == "technical"
    assert result.must_preserve == ["OpenCode"]


def test_validate_terminology_policy_output_accepts_expected_packet_shape():
    payload = {
        "keep_english": ["cache adapter"],
        "localize": ["latency => latência"],
        "context_sensitive": ["rollout"],
        "do_not_translate": ["OpenCode"],
        "resolved_decisions": [
            {
                "source_term": "AI Platform",
                "approved_rendering": "AI Platform",
                "decision": "keep_english",
                "scope": "artifact-wide",
                "applies_to": ["summary", "experience[].description"],
                "notes": "Internal product name in this artifact.",
            }
        ],
        "education_degree_localization_policy": {
            "decision": "localize_equivalent",
            "apply_consistently": True,
            "rule": "Use recruiter-facing PT-BR degree names consistently.",
            "exceptions": [
                {
                    "source_degree": "Bachelor of Economics - BBA, Economics",
                    "approved_rendering": "Bacharelado em Economia",
                    "reason": "Prefer idiomatic PT-BR credential naming.",
                }
            ],
        },
        "consistency_rules": ["Keep terminology stable."],
        "rationale_notes": ["Borrow infra terms when PT-BR usage expects it."],
    }

    result = validate_terminology_policy_output(payload, run_id="run-terminology-policy")

    assert isinstance(result, TerminologyPolicyPacket)
    assert result.keep_english == ["cache adapter"]
    assert result.do_not_translate == ["OpenCode"]
    assert result.resolved_decisions[0].preferred_rendering == "AI Platform"
    assert result.education_degree_localization_policy is not None
    assert result.education_degree_localization_policy.apply_consistently is True


def test_validate_refinement_output_rejects_non_string_tag_values():
    payload = {
        "title": "Title",
        "excerpt": "Summary",
        "tags": ["ok", 1],
        "content": "Refined content",
        "applied_feedback": ["fixed terminology"],
    }

    with pytest.raises(TypeMismatchError) as excinfo:
        validate_refinement_output(payload, run_id="run-refine", stage="refine")

    err = excinfo.value
    assert err.field == "tags"
    assert err.run_id == "run-refine"
    assert err.stage == "refine"


def test_validate_revision_output_accepts_rewrite_summary_and_unresolved_risks():
    payload = {
        "title": "Title",
        "excerpt": "Summary",
        "tags": ["ia"],
        "content": "Revised content",
        "applied_feedback": ["fixed terminology"],
        "rewrite_summary": ["re-anchored the second paragraph in the source"],
        "unresolved_risks": [],
    }

    result = validate_revision_output(payload, run_id="run-revise")

    assert isinstance(result, RevisionOutput)
    assert result.applied_feedback == ["fixed terminology"]
    assert result.rewrite_summary == ["re-anchored the second paragraph in the source"]


def test_validate_final_review_output_requires_explicit_acceptance_gate_fields():
    payload = {
        "accept": True,
        "publish_ready": True,
        "confidence": 0.91,
        "residual_issues": [],
        "voice_score": 94,
        "terminology_score": 96,
        "locale_naturalness_score": 93,
    }

    result = validate_final_review_output(payload, run_id="run-final-review")

    assert isinstance(result, FinalReviewOutput)
    assert result.accept is True
    assert result.publish_ready is True
    assert result.voice_score == 94.0


def test_translation_provider_interface_exposes_required_methods():
    class IncompleteProvider(TranslationProvider):
        pass

    incomplete_ctor: Any = IncompleteProvider
    with pytest.raises(TypeError):
        incomplete_ctor()
