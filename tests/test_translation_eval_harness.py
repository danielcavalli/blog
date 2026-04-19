"""One-file tests for translation_v2 evaluation harness.

Canonical command:
    uv run --extra dev pytest tests/test_translation_eval_harness.py -q
"""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
if _SOURCE not in sys.path:
    sys.path.insert(0, _SOURCE)
_mock_provider_stub = types.ModuleType("translation_v2.mock_provider")
_mock_provider_stub.DeterministicMockTranslationProvider = object
sys.modules.setdefault("translation_v2.mock_provider", _mock_provider_stub)

from translation_v2.eval_harness import (  # noqa: E402
    HARD_FAIL_GATES,
    EvalThresholds,
    MetricResult,
    compare_runs,
    evaluate_outputs,
    load_regression_cases,
    load_thresholds,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "translation_v2" / "eval"
CASES_FIXTURE = FIXTURES_DIR / "regression_cases.json"
BASELINE_FIXTURE = FIXTURES_DIR / "baseline_outputs.json"
CANDIDATE_FIXTURE = FIXTURES_DIR / "candidate_outputs.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_regression_fixtures_cover_target_categories():
    cases = load_regression_cases(CASES_FIXTURE)

    by_id = {case.case_id: case for case in cases}
    assert "terminology-entities" in by_id
    assert "placeholder-integrity" in by_id
    assert "locale-formatting" in by_id
    assert "tone-constraints" in by_id
    assert "voice-terminology-packets" in by_id

    assert by_id["terminology-entities"].required_terminology
    assert by_id["placeholder-integrity"].required_placeholders
    assert by_id["locale-formatting"].locale_required_patterns
    assert by_id["tone-constraints"].tone_forbidden_phrases
    assert by_id["voice-terminology-packets"].required_terminology
    assert by_id["voice-terminology-packets"].tone_forbidden_phrases


def test_hard_failures_cover_schema_empty_tag_and_placeholder_integrity():
    cases = load_regression_cases(CASES_FIXTURE)
    by_id = {case.case_id: case for case in cases}

    broken_outputs = {
        "placeholder-integrity": {
            "title": "",
            "excerpt": "",
            "content": "placeholder perdido",
        },
    }
    run = evaluate_outputs(
        cases=[by_id["placeholder-integrity"]],
        outputs_by_case_id=broken_outputs,
        run_label="candidate",
    )
    hard_fails = run.case_results[0].hard_failures
    assert any(item.startswith("schema_validation:") for item in hard_fails)

    partially_broken_outputs = {
        "placeholder-integrity": {
            "title": "Seguranca de template",
            "excerpt": "Sem placeholders completos.",
            "tags": ["translation", "ops"],
            "content": "Mantem apenas {{APP_NAME}} e remove RUN_ID.",
        }
    }
    run = evaluate_outputs(
        cases=[by_id["placeholder-integrity"]],
        outputs_by_case_id=partially_broken_outputs,
        run_label="candidate",
    )
    hard_fails = run.case_results[0].hard_failures
    assert (
        "tag_integrity: expected=['translation', 'qa'] actual=['translation', 'ops']"
        in hard_fails
    )
    assert "placeholder_integrity: missing={{RUN_ID}}" in hard_fails
    assert HARD_FAIL_GATES == (
        "schema_validation",
        "non_empty_output",
        "tag_integrity",
        "placeholder_integrity",
    )


def test_quality_hooks_are_configurable_for_future_metrics():
    class SemanticStubHook:
        name = "semantic_stub"

        def evaluate(self, case, output):  # noqa: ANN001
            return MetricResult(
                name=self.name,
                score=0.40,
                details=[f"stub metric for {case.case_id}: {output.title}"],
            )

    cases = load_regression_cases(CASES_FIXTURE)
    candidate_outputs = _load_json(CANDIDATE_FIXTURE)
    run = evaluate_outputs(
        cases=[cases[0]],
        outputs_by_case_id=candidate_outputs,
        run_label="candidate",
        hooks=[SemanticStubHook()],
    )

    result = run.case_results[0]
    assert result.metric_scores == {"semantic_stub": 0.40}
    assert result.case_score == 0.40
    assert result.metric_details["semantic_stub"][0].startswith("stub metric")


def test_compare_runs_renders_baseline_vs_candidate_report_and_threshold_source(
    monkeypatch,
):
    monkeypatch.setenv("TRANSLATION_EVAL_MIN_RUN_AVG_SCORE", "0.85")
    thresholds = load_thresholds(config={"source": "packet-config"})

    cases = load_regression_cases(CASES_FIXTURE)
    baseline_outputs = _load_json(BASELINE_FIXTURE)
    candidate_outputs = _load_json(CANDIDATE_FIXTURE)
    report = compare_runs(
        cases=cases,
        baseline_outputs_by_case_id=baseline_outputs,
        candidate_outputs_by_case_id=candidate_outputs,
        thresholds=thresholds,
    )

    rendered = report.render_text()
    assert "translation_v2 evaluation report" in rendered
    assert "threshold_source: env:TRANSLATION_EVAL_MIN_RUN_AVG_SCORE" in rendered
    assert (
        "hard_fail_gates: schema_validation, non_empty_output, tag_integrity, placeholder_integrity"
        in rendered
    )
    assert "run_scores: baseline=" in rendered
    assert "candidate_passes_thresholds: yes" in rendered
    assert "- placeholder-integrity:" in rendered
    assert report.candidate.average_score > report.baseline.average_score
    assert report.candidate.hard_fail_count == 0
    assert report.candidate_passes_thresholds is True


def test_voice_and_terminology_packet_regression_case_rewards_candidate_alignment():
    cases = load_regression_cases(CASES_FIXTURE)
    case = next(current for current in cases if current.case_id == "voice-terminology-packets")

    baseline_outputs = _load_json(BASELINE_FIXTURE)
    candidate_outputs = _load_json(CANDIDATE_FIXTURE)

    baseline_run = evaluate_outputs(
        cases=[case],
        outputs_by_case_id=baseline_outputs,
        run_label="baseline",
    )
    candidate_run = evaluate_outputs(
        cases=[case],
        outputs_by_case_id=candidate_outputs,
        run_label="candidate",
    )

    baseline_case = baseline_run.case_results[0]
    candidate_case = candidate_run.case_results[0]

    assert baseline_case.metric_scores["terminology_coverage"] < 1.0
    assert baseline_case.metric_scores["tone_constraints"] < 1.0
    assert candidate_case.metric_scores["terminology_coverage"] == 1.0
    assert candidate_case.metric_scores["tone_constraints"] == 1.0
    assert candidate_case.case_score > baseline_case.case_score


def test_threshold_source_defaults_to_configurable_packet_values(monkeypatch):
    monkeypatch.delenv("TRANSLATION_EVAL_MIN_CASE_SCORE", raising=False)
    monkeypatch.delenv("TRANSLATION_EVAL_MIN_RUN_AVG_SCORE", raising=False)
    monkeypatch.delenv("TRANSLATION_EVAL_FAIL_ON_HARD_FAILURE", raising=False)

    thresholds = load_thresholds(
        config={
            "min_case_score": 0.70,
            "min_run_avg_score": 0.78,
            "fail_on_any_hard_failure": True,
            "source": "packet-thresholds",
        }
    )

    assert isinstance(thresholds, EvalThresholds)
    assert thresholds.min_case_score == 0.70
    assert thresholds.min_run_avg_score == 0.78
    assert thresholds.fail_on_any_hard_failure is True
    assert thresholds.source == "packet-thresholds"
