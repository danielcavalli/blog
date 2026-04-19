"""Unit tests for translation_v2 contracts and provider interface."""

import os
import sys
from typing import Any

import pytest


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.contracts import (  # noqa: E402
    CVTranslationOutput,
    CritiqueOutput,
    TranslationOutput,
    TranslationRequest,
    validate_cv_translation_output,
    validate_critique_output,
    validate_refinement_output,
    validate_translation_output,
)
from translation_v2.errors import MissingFieldError, TypeMismatchError  # noqa: E402
from translation_v2.mock_provider import DeterministicMockTranslationProvider  # noqa: E402
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


def test_translation_provider_interface_exposes_required_methods():
    class IncompleteProvider(TranslationProvider):
        pass

    incomplete_ctor: Any = IncompleteProvider
    with pytest.raises(TypeError):
        incomplete_ctor()


def test_translation_provider_implementation_round_trip():
    provider = DeterministicMockTranslationProvider(
        {
            "fixture-post": {
                "translated": {
                    "title": "Titulo",
                    "excerpt": "Resumo",
                    "tags": ["ia"],
                    "content": "conteudo",
                },
                "critique": {
                    "score": 91,
                    "feedback": "No critical issues",
                    "needs_refinement": False,
                    "findings": [],
                },
                "refined": {
                    "title": "Titulo",
                    "excerpt": "Resumo",
                    "tags": ["ia"],
                    "content": "conteudo",
                    "applied_feedback": [],
                },
            }
        }
    )

    request = TranslationRequest(
        run_id="run-provider",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="Hello world",
        prompt_version="v1",
        metadata={"slug": "fixture-post"},
    )

    translated = provider.translate(request)
    critiqued = provider.critique(request, translated.payload)
    refined = provider.refine(request, translated.payload, critiqued.payload)

    assert translated.stage == "translate"
    assert critiqued.stage == "critique"
    assert refined.stage == "refine"
