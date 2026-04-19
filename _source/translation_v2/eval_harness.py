"""Deterministic regression harness for translation_v2 evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
import re
from typing import Any, Mapping, Protocol

from .contracts import TranslationOutput, validate_translation_output
from .errors import ContractValidationError


HARD_FAIL_GATES: tuple[str, ...] = (
    "schema_validation",
    "non_empty_output",
    "tag_integrity",
    "placeholder_integrity",
)


@dataclass(slots=True)
class EvalThresholds:
    """Configurable threshold values for quality checks and pass/fail policy."""

    min_case_score: float = 0.75
    min_run_avg_score: float = 0.80
    fail_on_any_hard_failure: bool = True
    source: str = "defaults"


def load_thresholds(
    *,
    config: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
) -> EvalThresholds:
    """Load thresholds from config and/or environment with deterministic precedence."""

    config = config or {}
    env = env or os.environ

    min_case_score = float(config.get("min_case_score", 0.75))
    min_run_avg_score = float(config.get("min_run_avg_score", 0.80))
    fail_on_any_hard_failure = bool(config.get("fail_on_any_hard_failure", True))
    source = str(config.get("source", "defaults"))

    if "TRANSLATION_EVAL_MIN_CASE_SCORE" in env:
        min_case_score = float(env["TRANSLATION_EVAL_MIN_CASE_SCORE"])
        source = "env:TRANSLATION_EVAL_MIN_CASE_SCORE"
    if "TRANSLATION_EVAL_MIN_RUN_AVG_SCORE" in env:
        min_run_avg_score = float(env["TRANSLATION_EVAL_MIN_RUN_AVG_SCORE"])
        source = "env:TRANSLATION_EVAL_MIN_RUN_AVG_SCORE"
    if "TRANSLATION_EVAL_FAIL_ON_HARD_FAILURE" in env:
        fail_on_any_hard_failure = _as_bool(env["TRANSLATION_EVAL_FAIL_ON_HARD_FAILURE"])
        source = "env:TRANSLATION_EVAL_FAIL_ON_HARD_FAILURE"

    return EvalThresholds(
        min_case_score=min_case_score,
        min_run_avg_score=min_run_avg_score,
        fail_on_any_hard_failure=fail_on_any_hard_failure,
        source=source,
    )


def _as_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class RegressionCase:
    """Regression test case loaded from JSON fixtures."""

    case_id: str
    source_title: str
    source_excerpt: str
    source_content: str
    expected_tags: list[str]
    required_placeholders: list[str] = field(default_factory=list)
    required_terminology: list[str] = field(default_factory=list)
    locale_required_patterns: list[str] = field(default_factory=list)
    tone_forbidden_phrases: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MetricResult:
    """Outcome of one quality hook for a case."""

    name: str
    score: float
    details: list[str] = field(default_factory=list)


class QualityMetricHook(Protocol):
    """Protocol for pluggable quality scoring hooks."""

    name: str

    def evaluate(self, case: RegressionCase, output: TranslationOutput) -> MetricResult:
        """Return deterministic metric score and details for a case."""
        ...


@dataclass(slots=True)
class TerminologyCoverageHook:
    """Score based on presence of required terms in translated output."""

    name: str = "terminology_coverage"

    def evaluate(self, case: RegressionCase, output: TranslationOutput) -> MetricResult:
        if not case.required_terminology:
            return MetricResult(name=self.name, score=1.0)

        translated_text = _joined_output(output)
        missing = [term for term in case.required_terminology if term not in translated_text]
        coverage = 1.0 - (len(missing) / len(case.required_terminology))
        details = [f"missing terminology: {term}" for term in missing]
        return MetricResult(name=self.name, score=max(0.0, coverage), details=details)


@dataclass(slots=True)
class LocaleFormattingHook:
    """Score locale formatting constraints using required regex patterns."""

    name: str = "locale_formatting"

    def evaluate(self, case: RegressionCase, output: TranslationOutput) -> MetricResult:
        if not case.locale_required_patterns:
            return MetricResult(name=self.name, score=1.0)

        translated_text = _joined_output(output)
        misses: list[str] = []
        for pattern in case.locale_required_patterns:
            if not re.search(pattern, translated_text):
                misses.append(pattern)
        score = 1.0 - (len(misses) / len(case.locale_required_patterns))
        details = [f"missing locale pattern: {pattern}" for pattern in misses]
        return MetricResult(name=self.name, score=max(0.0, score), details=details)


@dataclass(slots=True)
class ToneConstraintHook:
    """Score tone constraints by penalizing forbidden phrases."""

    name: str = "tone_constraints"

    def evaluate(self, case: RegressionCase, output: TranslationOutput) -> MetricResult:
        if not case.tone_forbidden_phrases:
            return MetricResult(name=self.name, score=1.0)

        translated_text = _joined_output(output)
        found = [phrase for phrase in case.tone_forbidden_phrases if phrase in translated_text]
        penalty = len(found) / len(case.tone_forbidden_phrases)
        details = [f"forbidden tone phrase present: {phrase}" for phrase in found]
        return MetricResult(name=self.name, score=max(0.0, 1.0 - penalty), details=details)


@dataclass(slots=True)
class CaseEvaluation:
    """Evaluation result for one fixture case."""

    case_id: str
    hard_failures: list[str]
    metric_scores: dict[str, float]
    metric_details: dict[str, list[str]]
    case_score: float

    @property
    def passed_hard_fail_gates(self) -> bool:
        return len(self.hard_failures) == 0


@dataclass(slots=True)
class RunEvaluation:
    """Evaluation result for one run (baseline or candidate)."""

    run_label: str
    case_results: list[CaseEvaluation]

    @property
    def average_score(self) -> float:
        if not self.case_results:
            return 0.0
        return sum(case.case_score for case in self.case_results) / len(self.case_results)

    @property
    def hard_fail_count(self) -> int:
        return sum(len(case.hard_failures) for case in self.case_results)


@dataclass(slots=True)
class ComparisonReport:
    """Baseline-vs-candidate report and rollout recommendation."""

    threshold_source: str
    hard_fail_gates: tuple[str, ...]
    baseline: RunEvaluation
    candidate: RunEvaluation
    candidate_passes_thresholds: bool

    def render_text(self) -> str:
        """Render a deterministic baseline-vs-candidate report."""

        lines = [
            "translation_v2 evaluation report",
            f"threshold_source: {self.threshold_source}",
            "hard_fail_gates: " + ", ".join(self.hard_fail_gates),
            (
                "run_scores: "
                f"baseline={self.baseline.average_score:.3f} "
                f"candidate={self.candidate.average_score:.3f} "
                f"delta={self.candidate.average_score - self.baseline.average_score:+.3f}"
            ),
            (
                "run_hard_fails: "
                f"baseline={self.baseline.hard_fail_count} "
                f"candidate={self.candidate.hard_fail_count}"
            ),
            "per_case:",
        ]

        baseline_by_case = {case.case_id: case for case in self.baseline.case_results}
        candidate_by_case = {case.case_id: case for case in self.candidate.case_results}
        for case_id in sorted(candidate_by_case.keys()):
            baseline_case = baseline_by_case[case_id]
            candidate_case = candidate_by_case[case_id]
            lines.append(
                (
                    f"- {case_id}: "
                    f"baseline_score={baseline_case.case_score:.3f} "
                    f"candidate_score={candidate_case.case_score:.3f} "
                    f"delta={candidate_case.case_score - baseline_case.case_score:+.3f} "
                    f"baseline_hard_fails={len(baseline_case.hard_failures)} "
                    f"candidate_hard_fails={len(candidate_case.hard_failures)}"
                )
            )

        lines.append(
            f"candidate_passes_thresholds: {'yes' if self.candidate_passes_thresholds else 'no'}"
        )
        return "\n".join(lines)


def default_quality_hooks() -> list[QualityMetricHook]:
    """Return default deterministic quality metric hooks."""

    return [
        TerminologyCoverageHook(),
        LocaleFormattingHook(),
        ToneConstraintHook(),
    ]


def load_regression_cases(fixture_path: Path) -> list[RegressionCase]:
    """Load regression cases from JSON fixture."""

    raw_cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [RegressionCase(**raw_case) for raw_case in raw_cases]


def evaluate_outputs(
    *,
    cases: list[RegressionCase],
    outputs_by_case_id: Mapping[str, Mapping[str, Any]],
    run_label: str,
    hooks: list[QualityMetricHook] | None = None,
) -> RunEvaluation:
    """Evaluate one run against regression cases."""

    hooks = hooks or default_quality_hooks()
    case_results: list[CaseEvaluation] = []
    for case in cases:
        payload = outputs_by_case_id[case.case_id]
        case_results.append(_evaluate_case(case=case, payload=payload, hooks=hooks))
    return RunEvaluation(run_label=run_label, case_results=case_results)


def compare_runs(
    *,
    cases: list[RegressionCase],
    baseline_outputs_by_case_id: Mapping[str, Mapping[str, Any]],
    candidate_outputs_by_case_id: Mapping[str, Mapping[str, Any]],
    thresholds: EvalThresholds,
    hooks: list[QualityMetricHook] | None = None,
) -> ComparisonReport:
    """Compare baseline and candidate runs with threshold policy."""

    baseline = evaluate_outputs(
        cases=cases,
        outputs_by_case_id=baseline_outputs_by_case_id,
        run_label="baseline",
        hooks=hooks,
    )
    candidate = evaluate_outputs(
        cases=cases,
        outputs_by_case_id=candidate_outputs_by_case_id,
        run_label="candidate",
        hooks=hooks,
    )

    candidate_has_hard_fail = candidate.hard_fail_count > 0
    candidate_passes_thresholds = (
        candidate.average_score >= thresholds.min_run_avg_score
        and all(case.case_score >= thresholds.min_case_score for case in candidate.case_results)
        and (not thresholds.fail_on_any_hard_failure or not candidate_has_hard_fail)
    )

    return ComparisonReport(
        threshold_source=thresholds.source,
        hard_fail_gates=HARD_FAIL_GATES,
        baseline=baseline,
        candidate=candidate,
        candidate_passes_thresholds=candidate_passes_thresholds,
    )


def _evaluate_case(
    *,
    case: RegressionCase,
    payload: Mapping[str, Any],
    hooks: list[QualityMetricHook],
) -> CaseEvaluation:
    hard_failures: list[str] = []
    try:
        output = validate_translation_output(
            dict(payload),
            run_id=f"eval-{case.case_id}",
            stage="eval_harness",
        )
    except ContractValidationError as exc:
        return CaseEvaluation(
            case_id=case.case_id,
            hard_failures=[f"schema_validation: {exc}"],
            metric_scores={},
            metric_details={},
            case_score=0.0,
        )

    if not _has_non_empty_text(output):
        hard_failures.append("non_empty_output: title/excerpt/content must be non-empty")

    if output.tags != case.expected_tags:
        hard_failures.append(f"tag_integrity: expected={case.expected_tags} actual={output.tags}")

    missing_placeholders = _missing_placeholders(case=case, output=output)
    if missing_placeholders:
        hard_failures.append("placeholder_integrity: missing=" + ", ".join(missing_placeholders))

    metric_scores: dict[str, float] = {}
    metric_details: dict[str, list[str]] = {}
    for hook in hooks:
        result = hook.evaluate(case, output)
        metric_scores[result.name] = result.score
        metric_details[result.name] = result.details

    if metric_scores:
        case_score = sum(metric_scores.values()) / len(metric_scores)
    else:
        case_score = 1.0
    return CaseEvaluation(
        case_id=case.case_id,
        hard_failures=hard_failures,
        metric_scores=metric_scores,
        metric_details=metric_details,
        case_score=case_score,
    )


def _has_non_empty_text(output: TranslationOutput) -> bool:
    return bool(output.title.strip() and output.excerpt.strip() and output.content.strip())


def _missing_placeholders(case: RegressionCase, output: TranslationOutput) -> list[str]:
    if not case.required_placeholders:
        return []
    translated_text = _joined_output(output)
    return [token for token in case.required_placeholders if token not in translated_text]


def _joined_output(output: TranslationOutput) -> str:
    return "\n".join([output.title, output.excerpt, output.content])
