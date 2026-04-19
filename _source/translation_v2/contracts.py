"""Typed contracts and schema validators for translation_v2 stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from .errors import MissingFieldError, TypeMismatchError


@dataclass(slots=True)
class TranslationRequest:
    """Input payload shared by translation stages."""

    run_id: str
    source_locale: str
    target_locale: str
    source_text: str
    prompt_version: str
    content_type: str = "markdown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TranslationOutput:
    """Structured output for the translation stage."""

    title: str
    excerpt: str
    tags: list[str]
    content: str


@dataclass(slots=True)
class CVExperienceEntry:
    title: str
    company: str
    location: str
    period: str
    description: str
    achievements: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CVEducationEntry:
    degree: str
    school: str
    period: str


@dataclass(slots=True)
class CVTranslationOutput:
    """Structured output for full CV translation."""

    name: str
    tagline: str
    location: str
    contact: dict[str, str]
    skills: list[str]
    languages_spoken: list[str]
    summary: str
    experience: list[CVExperienceEntry]
    education: list[CVEducationEntry]


@dataclass(slots=True)
class CritiqueOutput:
    """Structured output for critique stage."""

    score: float
    feedback: str
    needs_refinement: bool
    findings: list[str] = field(default_factory=list)
    dimension_scores: dict[str, float] = field(default_factory=dict)
    critical_errors: int = 0
    major_core_errors: int = 0
    confidence: float = 1.0


@dataclass(slots=True)
class RefinementOutput:
    """Structured output for refinement stage."""

    title: str
    excerpt: str
    tags: list[str]
    content: str
    applied_feedback: list[str] = field(default_factory=list)


ProviderPayload = TranslationOutput | CVTranslationOutput | CritiqueOutput | RefinementOutput
StagePayloadT = TypeVar("StagePayloadT", bound=ProviderPayload, covariant=True)


@dataclass(slots=True)
class StageResult(Generic[StagePayloadT]):
    """Envelope for stage output metadata."""

    run_id: str
    stage: str
    model: str
    payload: StagePayloadT
    raw_response: dict[str, Any] | None = None


def _require_field(
    payload: dict[str, Any],
    *,
    field_name: str,
    expected_type: type[Any] | tuple[type[Any], ...],
    run_id: str,
    stage: str,
) -> Any:
    if field_name not in payload:
        raise MissingFieldError(
            message="Missing required field",
            run_id=run_id,
            stage=stage,
            field=field_name,
        )

    value = payload[field_name]
    if not isinstance(value, expected_type):
        expected_name = _readable_type_name(expected_type)
        actual_name = type(value).__name__
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type=expected_name,
            actual_type=actual_name,
        )
    return value


def _readable_type_name(
    expected_type: type[Any] | tuple[type[Any], ...],
) -> str:
    if isinstance(expected_type, tuple):
        return "|".join(typ.__name__ for typ in expected_type)
    return expected_type.__name__


def _require_string_list(
    payload: dict[str, Any], *, field_name: str, run_id: str, stage: str
) -> list[str]:
    values = _require_field(
        payload,
        field_name=field_name,
        expected_type=list,
        run_id=run_id,
        stage=stage,
    )
    if not all(isinstance(value, str) for value in values):
        raise TypeMismatchError(
            message="List contains non-string values",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="list[str]",
            actual_type="mixed",
        )
    return values


def _require_string_mapping(
    payload: dict[str, Any], *, field_name: str, run_id: str, stage: str
) -> dict[str, str]:
    value = _require_field(
        payload,
        field_name=field_name,
        expected_type=dict,
        run_id=run_id,
        stage=stage,
    )
    if not all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="dict[str,str]",
            actual_type="mixed",
        )
    return dict(value)


def _require_nested_string(
    payload: dict[str, Any],
    field_name: str,
    run_id: str,
    stage: str,
    parent: str,
) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=f"{parent}.{field_name}",
            expected_type="str",
            actual_type=type(value).__name__,
        )
    return value


def _require_nested_string_list(
    payload: dict[str, Any],
    field_name: str,
    run_id: str,
    stage: str,
    parent: str,
) -> list[str]:
    value = payload.get(field_name)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=f"{parent}.{field_name}",
            expected_type="list[str]",
            actual_type=type(value).__name__,
        )
    return list(value)


def _require_experience_entries(
    payload: dict[str, Any], *, run_id: str, stage: str
) -> list[CVExperienceEntry]:
    entries = _require_field(
        payload,
        field_name="experience",
        expected_type=list,
        run_id=run_id,
        stage=stage,
    )
    normalized: list[CVExperienceEntry] = []
    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field=f"experience[{index}]",
                expected_type="dict",
                actual_type=type(item).__name__,
            )
        normalized.append(
            CVExperienceEntry(
                title=_require_nested_string(item, "title", run_id, stage, f"experience[{index}]"),
                company=_require_nested_string(item, "company", run_id, stage, f"experience[{index}]"),
                location=_require_nested_string(item, "location", run_id, stage, f"experience[{index}]"),
                period=_require_nested_string(item, "period", run_id, stage, f"experience[{index}]"),
                description=_require_nested_string(item, "description", run_id, stage, f"experience[{index}]"),
                achievements=_require_nested_string_list(
                    item, "achievements", run_id, stage, f"experience[{index}]"
                ),
            )
        )
    return normalized


def _require_education_entries(
    payload: dict[str, Any], *, run_id: str, stage: str
) -> list[CVEducationEntry]:
    entries = _require_field(
        payload,
        field_name="education",
        expected_type=list,
        run_id=run_id,
        stage=stage,
    )
    normalized: list[CVEducationEntry] = []
    for index, item in enumerate(entries):
        if not isinstance(item, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field=f"education[{index}]",
                expected_type="dict",
                actual_type=type(item).__name__,
            )
        normalized.append(
            CVEducationEntry(
                degree=_require_nested_string(item, "degree", run_id, stage, f"education[{index}]"),
                school=_require_nested_string(item, "school", run_id, stage, f"education[{index}]"),
                period=_require_nested_string(item, "period", run_id, stage, f"education[{index}]"),
            )
        )
    return normalized


def validate_translation_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "translate"
) -> TranslationOutput:
    """Validate and parse structured translation output."""

    title = _require_field(
        payload,
        field_name="title",
        expected_type=str,
        run_id=run_id,
        stage=stage,
    )
    excerpt = _require_field(
        payload,
        field_name="excerpt",
        expected_type=str,
        run_id=run_id,
        stage=stage,
    )
    content = _require_field(
        payload,
        field_name="content",
        expected_type=str,
        run_id=run_id,
        stage=stage,
    )
    tags = _require_string_list(payload, field_name="tags", run_id=run_id, stage=stage)
    return TranslationOutput(title=title, excerpt=excerpt, tags=tags, content=content)


def validate_cv_translation_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "translate"
) -> CVTranslationOutput:
    """Validate and parse structured CV translation output."""

    return CVTranslationOutput(
        name=_require_field(
            payload,
            field_name="name",
            expected_type=str,
            run_id=run_id,
            stage=stage,
        ),
        tagline=_require_field(
            payload,
            field_name="tagline",
            expected_type=str,
            run_id=run_id,
            stage=stage,
        ),
        location=_require_field(
            payload,
            field_name="location",
            expected_type=str,
            run_id=run_id,
            stage=stage,
        ),
        contact=_require_string_mapping(
            payload,
            field_name="contact",
            run_id=run_id,
            stage=stage,
        ),
        skills=_require_string_list(payload, field_name="skills", run_id=run_id, stage=stage),
        languages_spoken=_require_string_list(
            payload,
            field_name="languages_spoken",
            run_id=run_id,
            stage=stage,
        ),
        summary=_require_field(
            payload,
            field_name="summary",
            expected_type=str,
            run_id=run_id,
            stage=stage,
        ),
        experience=_require_experience_entries(payload, run_id=run_id, stage=stage),
        education=_require_education_entries(payload, run_id=run_id, stage=stage),
    )


def validate_critique_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "critique"
) -> CritiqueOutput:
    """Validate and parse structured critique output."""

    score_source = "overall_score" if "overall_score" in payload else "score"
    score = _require_field(
        payload,
        field_name=score_source,
        expected_type=(int, float),
        run_id=run_id,
        stage=stage,
    )

    feedback = payload.get("feedback")
    if feedback is None and isinstance(payload.get("decision_hint"), str):
        feedback = f"Decision hint: {payload['decision_hint']}"
    if feedback is None:
        raise MissingFieldError(
            message="Missing required field",
            run_id=run_id,
            stage=stage,
            field="feedback",
        )
    if not isinstance(feedback, str):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="feedback",
            expected_type="str",
            actual_type=type(feedback).__name__,
        )

    needs_refinement = payload.get("needs_refinement")
    if needs_refinement is None and isinstance(payload.get("decision_hint"), str):
        needs_refinement = payload["decision_hint"] != "accept"
    if needs_refinement is None:
        raise MissingFieldError(
            message="Missing required field",
            run_id=run_id,
            stage=stage,
            field="needs_refinement",
        )
    if not isinstance(needs_refinement, bool):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="needs_refinement",
            expected_type="bool",
            actual_type=type(needs_refinement).__name__,
        )

    findings = _normalize_findings(payload, run_id=run_id, stage=stage)
    dimension_scores = _extract_dimension_scores(
        payload,
        run_id=run_id,
        stage=stage,
        fallback_score=float(score),
    )
    critical_errors = _extract_nonnegative_int(
        payload,
        field_name="critical_errors",
        run_id=run_id,
        stage=stage,
        fallback_path=("error_summary", "critical"),
        default=0,
    )
    major_core_errors = _extract_nonnegative_int(
        payload,
        field_name="major_core_errors",
        run_id=run_id,
        stage=stage,
        fallback_path=("error_summary", "major"),
        default=0,
    )

    confidence = payload.get("confidence", 1.0)
    if not isinstance(confidence, (int, float)):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="confidence",
            expected_type="int|float",
            actual_type=type(confidence).__name__,
        )

    return CritiqueOutput(
        score=float(score),
        feedback=feedback,
        needs_refinement=needs_refinement,
        findings=findings,
        dimension_scores=dimension_scores,
        critical_errors=critical_errors,
        major_core_errors=major_core_errors,
        confidence=float(confidence),
    )


def _normalize_findings(payload: dict[str, Any], *, run_id: str, stage: str) -> list[str]:
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="findings",
            expected_type="list[str]|list[object]",
            actual_type=type(findings).__name__,
        )

    if all(isinstance(item, str) for item in findings):
        return findings

    if all(isinstance(item, dict) for item in findings):
        normalized: list[str] = []
        for item in findings:
            description = item.get("description")
            if not isinstance(description, str):
                raise TypeMismatchError(
                    message="Field type mismatch",
                    run_id=run_id,
                    stage=stage,
                    field="findings.description",
                    expected_type="str",
                    actual_type=type(description).__name__,
                )
            normalized.append(description)
        return normalized

    raise TypeMismatchError(
        message="Field type mismatch",
        run_id=run_id,
        stage=stage,
        field="findings",
        expected_type="list[str]|list[object]",
        actual_type="mixed",
    )


def _extract_dimension_scores(
    payload: dict[str, Any],
    *,
    run_id: str,
    stage: str,
    fallback_score: float,
) -> dict[str, float]:
    dimension_scores: dict[str, float] = {}
    parsed_from_structured = False

    if "dimension_scores" in payload:
        raw_scores = payload["dimension_scores"]
        if not isinstance(raw_scores, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field="dimension_scores",
                expected_type="dict[str, int|float]",
                actual_type=type(raw_scores).__name__,
            )

        for key, value in raw_scores.items():
            if not isinstance(key, str) or not isinstance(value, (int, float)):
                raise TypeMismatchError(
                    message="Field type mismatch",
                    run_id=run_id,
                    stage=stage,
                    field="dimension_scores",
                    expected_type="dict[str, int|float]",
                    actual_type="mixed",
                )
            dimension_scores[key] = float(value)
        parsed_from_structured = True
    elif "dimensions" in payload:
        raw_dimensions = payload["dimensions"]
        if not isinstance(raw_dimensions, list):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field="dimensions",
                expected_type="list[object]",
                actual_type=type(raw_dimensions).__name__,
            )

        for item in raw_dimensions:
            if not isinstance(item, dict):
                raise TypeMismatchError(
                    message="Field type mismatch",
                    run_id=run_id,
                    stage=stage,
                    field="dimensions",
                    expected_type="list[object]",
                    actual_type="mixed",
                )
            name = item.get("name")
            score_100 = item.get("score_100")
            if not isinstance(name, str) or not isinstance(score_100, (int, float)):
                raise TypeMismatchError(
                    message="Field type mismatch",
                    run_id=run_id,
                    stage=stage,
                    field="dimensions",
                    expected_type="list[{name:str,score_100:int|float}]",
                    actual_type="mixed",
                )
            dimension_scores[name] = float(score_100)
        parsed_from_structured = True

    core_dimensions = (
        "accuracy_completeness",
        "terminology_entities",
        "markdown_code_link_fidelity",
    )
    for name in core_dimensions:
        if name not in dimension_scores:
            if parsed_from_structured:
                dimension_scores[name] = 0.0
            else:
                dimension_scores[name] = fallback_score
    return dimension_scores


def _extract_nonnegative_int(
    payload: dict[str, Any],
    *,
    field_name: str,
    run_id: str,
    stage: str,
    fallback_path: tuple[str, str] | None,
    default: int,
) -> int:
    if field_name in payload:
        value = payload[field_name]
    elif fallback_path is not None:
        parent_key, child_key = fallback_path
        parent = payload.get(parent_key)
        value = parent.get(child_key) if isinstance(parent, dict) else default
    else:
        value = default

    if not isinstance(value, int) or value < 0:
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="int>=0",
            actual_type=type(value).__name__,
        )
    return value


def validate_refinement_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "refine"
) -> RefinementOutput:
    """Validate and parse structured refinement output."""

    base = validate_translation_output(payload, run_id=run_id, stage=stage)
    applied_feedback = payload.get("applied_feedback", [])
    if not isinstance(applied_feedback, list) or not all(
        isinstance(item, str) for item in applied_feedback
    ):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="applied_feedback",
            expected_type="list[str]",
            actual_type=type(applied_feedback).__name__,
        )

    return RefinementOutput(
        title=base.title,
        excerpt=base.excerpt,
        tags=base.tags,
        content=base.content,
        applied_feedback=applied_feedback,
    )
