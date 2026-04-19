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
class VoiceIntentPacket:
    """Source-analysis output describing authorial and rhetorical intent."""

    author_voice_summary: str
    tone: str
    register: str
    sentence_rhythm: list[str] = field(default_factory=list)
    connective_tissue: list[str] = field(default_factory=list)
    rhetorical_moves: list[str] = field(default_factory=list)
    humor_signals: list[str] = field(default_factory=list)
    stance_markers: list[str] = field(default_factory=list)
    must_preserve: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TerminologyPolicyPacket:
    """Artifact-wide borrowing and localization policy."""

    keep_english: list[str] = field(default_factory=list)
    localize: list[str] = field(default_factory=list)
    context_sensitive: list[str] = field(default_factory=list)
    do_not_translate: list[str] = field(default_factory=list)
    consistency_rules: list[str] = field(default_factory=list)
    rationale_notes: list[str] = field(default_factory=list)
    resolved_decisions: list["TerminologyDecision"] = field(default_factory=list)
    education_degree_localization_policy: "EducationDegreeLocalizationPolicy | None" = None


@dataclass(slots=True)
class TerminologyDecision:
    """Resolved artifact-level decision for one ambiguous source term."""

    source_term: str
    preferred_rendering: str
    decision_type: str
    scope: str
    rationale: str
    applies_to: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EducationDegreePolicyException:
    """Allowed exception for degree-localization policy."""

    source_degree: str
    approved_rendering: str
    reason: str


@dataclass(slots=True)
class EducationDegreeLocalizationPolicy:
    """Explicit artifact-wide policy for education.degree localization."""

    decision: str
    apply_consistently: bool
    rule: str
    exceptions: list[EducationDegreePolicyException] = field(default_factory=list)


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
class CritiqueFinding:
    """Structured critique finding tied to source/target spans."""

    finding_id: str
    severity: str
    category: str
    source_span: str
    target_span: str
    description: str
    rewrite_instruction: str


@dataclass(slots=True)
class CritiqueOutput:
    """Structured output for critique stage."""

    score: float
    feedback: str
    needs_refinement: bool
    findings: list[CritiqueFinding] = field(default_factory=list)
    dimension_scores: dict[str, float] = field(default_factory=dict)
    critical_errors: int = 0
    major_core_errors: int = 0
    confidence: float = 1.0


@dataclass(slots=True)
class RevisionOutput:
    """Structured output for revision stage."""

    title: str
    excerpt: str
    tags: list[str]
    content: str
    applied_feedback: list[str] = field(default_factory=list)
    declined_feedback: list["RevisionDisposition"] = field(default_factory=list)
    rewrite_summary: list[str] = field(default_factory=list)
    unresolved_risks: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CVRevisionOutput:
    """Structured output for CV revision stage."""

    revised_cv: CVTranslationOutput
    revision_report: "CVRevisionReport"


@dataclass(slots=True)
class RevisionDisposition:
    """Disposition for a critique finding during revision."""

    finding_id: str
    status: str
    rationale: str


@dataclass(slots=True)
class RevisionAppliedFinding:
    """Concrete applied fix entry for revision reports."""

    finding_id: str
    field_path: str
    change_summary: str


@dataclass(slots=True)
class ProtectedFieldException:
    """Explicit protected-field exception for declined critique items."""

    finding_id: str
    field_path: str
    protected_value: str
    reason: str


@dataclass(slots=True)
class CVRevisionReport:
    """Structured report for CV revision outcomes."""

    applied_findings: list[RevisionAppliedFinding] = field(default_factory=list)
    declined_findings: list["RevisionDisposition"] = field(default_factory=list)
    protected_field_exceptions: list[ProtectedFieldException] = field(default_factory=list)


@dataclass(slots=True)
class FinalReviewOutput:
    """Structured output for final review stage."""

    accept: bool
    publish_ready: bool
    confidence: float
    residual_issues: list[str] = field(default_factory=list)
    voice_score: float = 0.0
    terminology_score: float = 0.0
    locale_naturalness_score: float = 0.0


RefinementOutput = RevisionOutput

ProviderPayload = (
    VoiceIntentPacket
    | TerminologyDecision
    | TerminologyPolicyPacket
    | TranslationOutput
    | CVTranslationOutput
    | CritiqueOutput
    | RevisionOutput
    | CVRevisionOutput
    | FinalReviewOutput
)
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


def _normalize_findings(
    payload: dict[str, Any], *, run_id: str, stage: str
) -> list[CritiqueFinding]:
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
        return [
            CritiqueFinding(
                finding_id=f"finding-{index + 1}",
                severity="major",
                category="general",
                source_span="",
                target_span="",
                description=item,
                rewrite_instruction=item,
            )
            for index, item in enumerate(findings)
        ]

    if all(isinstance(item, dict) for item in findings):
        normalized: list[CritiqueFinding] = []
        for index, item in enumerate(findings):
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
            normalized.append(
                CritiqueFinding(
                    finding_id=str(item.get("id", f"finding-{index + 1}")).strip()
                    or f"finding-{index + 1}",
                    severity=str(item.get("severity", "major")).strip() or "major",
                    category=str(item.get("dimension", item.get("category", "general"))).strip()
                    or "general",
                    source_span=str(item.get("source_span", "")).strip(),
                    target_span=str(item.get("target_span", "")).strip(),
                    description=description,
                    rewrite_instruction=str(
                        item.get("fix_hint", item.get("rewrite_instruction", description))
                    ).strip()
                    or description,
                )
            )
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


def validate_revision_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "revise"
) -> RevisionOutput:
    """Validate and parse structured revision output."""

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

    declined_feedback = _normalize_revision_dispositions(
        payload.get("declined_feedback", []),
        run_id=run_id,
        stage=stage,
        field_name="declined_feedback",
    )

    rewrite_summary = payload.get("rewrite_summary", [])
    if not isinstance(rewrite_summary, list) or not all(
        isinstance(item, str) for item in rewrite_summary
    ):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="rewrite_summary",
            expected_type="list[str]",
            actual_type=type(rewrite_summary).__name__,
        )

    unresolved_risks = payload.get("unresolved_risks", [])
    if not isinstance(unresolved_risks, list) or not all(
        isinstance(item, str) for item in unresolved_risks
    ):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="unresolved_risks",
            expected_type="list[str]",
            actual_type=type(unresolved_risks).__name__,
        )

    return RevisionOutput(
        title=base.title,
        excerpt=base.excerpt,
        tags=base.tags,
        content=base.content,
        applied_feedback=applied_feedback,
        declined_feedback=declined_feedback,
        rewrite_summary=rewrite_summary,
        unresolved_risks=unresolved_risks,
    )


def validate_cv_revision_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "revise"
) -> CVRevisionOutput:
    """Validate and parse structured CV revision output."""

    cv_payload = payload.get("revised_cv", payload.get("cv"))
    if not isinstance(cv_payload, dict):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="revised_cv",
            expected_type="dict",
            actual_type=type(cv_payload).__name__,
        )

    cv = validate_cv_translation_output(cv_payload, run_id=run_id, stage=stage)
    raw_report = payload.get("revision_report")
    if not isinstance(raw_report, dict):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field="revision_report",
            expected_type="dict",
            actual_type=type(raw_report).__name__,
        )

    return CVRevisionOutput(
        revised_cv=cv,
        revision_report=CVRevisionReport(
            applied_findings=_normalize_applied_findings(
                raw_report.get("applied_findings", []),
                run_id=run_id,
                stage=stage,
                field_name="revision_report.applied_findings",
            ),
            declined_findings=_normalize_declined_findings(
                raw_report.get("declined_findings", []),
                run_id=run_id,
                stage=stage,
                field_name="revision_report.declined_findings",
            ),
            protected_field_exceptions=_normalize_protected_field_exceptions(
                raw_report.get("protected_field_exceptions", []),
                run_id=run_id,
                stage=stage,
                field_name="revision_report.protected_field_exceptions",
            ),
        ),
    )


def validate_refinement_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "refine"
) -> RefinementOutput:
    """Backward-compatible alias for revision-stage parsing."""

    return validate_revision_output(payload, run_id=run_id, stage=stage)


def _normalize_declined_findings(
    payload: Any,
    *,
    run_id: str,
    stage: str,
    field_name: str,
) -> list[RevisionDisposition]:
    return _normalize_revision_dispositions(
        payload,
        run_id=run_id,
        stage=stage,
        field_name=field_name,
    )


def validate_voice_intent_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "source_analysis"
) -> VoiceIntentPacket:
    """Validate source-analysis output."""

    author_voice_summary = _require_field(
        payload,
        field_name="author_voice_summary",
        expected_type=str,
        run_id=run_id,
        stage=stage,
    )
    tone = _require_field(
        payload,
        field_name="tone",
        expected_type=str,
        run_id=run_id,
        stage=stage,
    )
    register = _require_field(
        payload,
        field_name="register",
        expected_type=str,
        run_id=run_id,
        stage=stage,
    )
    return VoiceIntentPacket(
        author_voice_summary=author_voice_summary,
        tone=tone,
        register=register,
        sentence_rhythm=_require_string_list(
            payload, field_name="sentence_rhythm", run_id=run_id, stage=stage
        ),
        connective_tissue=_require_string_list(
            payload, field_name="connective_tissue", run_id=run_id, stage=stage
        ),
        rhetorical_moves=_require_string_list(
            payload, field_name="rhetorical_moves", run_id=run_id, stage=stage
        ),
        humor_signals=_require_string_list(
            payload, field_name="humor_signals", run_id=run_id, stage=stage
        ),
        stance_markers=_require_string_list(
            payload, field_name="stance_markers", run_id=run_id, stage=stage
        ),
        must_preserve=_require_string_list(
            payload, field_name="must_preserve", run_id=run_id, stage=stage
        ),
    )


def validate_terminology_policy_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "terminology_policy"
) -> TerminologyPolicyPacket:
    """Validate terminology policy output."""

    return TerminologyPolicyPacket(
        keep_english=_require_string_list(
            payload, field_name="keep_english", run_id=run_id, stage=stage
        ),
        localize=_require_string_list(
            payload, field_name="localize", run_id=run_id, stage=stage
        ),
        context_sensitive=_require_string_list(
            payload, field_name="context_sensitive", run_id=run_id, stage=stage
        ),
        do_not_translate=_require_string_list(
            payload, field_name="do_not_translate", run_id=run_id, stage=stage
        ),
        consistency_rules=_require_string_list(
            payload, field_name="consistency_rules", run_id=run_id, stage=stage
        ),
        rationale_notes=_require_string_list(
            payload, field_name="rationale_notes", run_id=run_id, stage=stage
        ),
        resolved_decisions=_require_terminology_decisions(
            payload,
            field_name="resolved_decisions",
            run_id=run_id,
            stage=stage,
        ),
        education_degree_localization_policy=_require_education_degree_policy(
            payload,
            field_name="education_degree_localization_policy",
            run_id=run_id,
            stage=stage,
        ),
    )


def validate_final_review_output(
    payload: dict[str, Any], *, run_id: str, stage: str = "final_review"
) -> FinalReviewOutput:
    """Validate final review stage output."""

    accept = _require_field(
        payload,
        field_name="accept",
        expected_type=bool,
        run_id=run_id,
        stage=stage,
    )
    publish_ready = _require_field(
        payload,
        field_name="publish_ready",
        expected_type=bool,
        run_id=run_id,
        stage=stage,
    )
    confidence = _require_field(
        payload,
        field_name="confidence",
        expected_type=(int, float),
        run_id=run_id,
        stage=stage,
    )
    voice_score = _require_field(
        payload,
        field_name="voice_score",
        expected_type=(int, float),
        run_id=run_id,
        stage=stage,
    )
    terminology_score = _require_field(
        payload,
        field_name="terminology_score",
        expected_type=(int, float),
        run_id=run_id,
        stage=stage,
    )
    locale_naturalness_score = _require_field(
        payload,
        field_name="locale_naturalness_score",
        expected_type=(int, float),
        run_id=run_id,
        stage=stage,
    )
    return FinalReviewOutput(
        accept=accept,
        publish_ready=publish_ready,
        confidence=float(confidence),
        residual_issues=_require_string_list(
            payload, field_name="residual_issues", run_id=run_id, stage=stage
        ),
        voice_score=float(voice_score),
        terminology_score=float(terminology_score),
        locale_naturalness_score=float(locale_naturalness_score),
    )


def _require_terminology_decisions(
    payload: dict[str, Any], *, field_name: str, run_id: str, stage: str
) -> list[TerminologyDecision]:
    raw = payload.get(field_name, [])
    if not isinstance(raw, list):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="list",
            actual_type=type(raw).__name__,
        )
    normalized: list[TerminologyDecision] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field=f"{field_name}[{index}]",
                expected_type="dict",
                actual_type=type(item).__name__,
            )
        normalized.append(
            TerminologyDecision(
                source_term=_require_nested_string(item, "source_term", run_id, stage, field_name),
                preferred_rendering=_require_nested_string_alias(
                    item,
                    ("preferred_rendering", "approved_rendering"),
                    run_id,
                    stage,
                    field_name,
                ),
                decision_type=_require_nested_string_alias(
                    item,
                    ("decision_type", "decision"),
                    run_id,
                    stage,
                    field_name,
                ),
                scope=_require_nested_string(item, "scope", run_id, stage, field_name),
                rationale=_require_nested_string_alias(
                    item,
                    ("rationale", "notes"),
                    run_id,
                    stage,
                    field_name,
                ),
                applies_to=_require_nested_string_list_optional(
                    item,
                    "applies_to",
                    run_id,
                    stage,
                    field_name,
                ),
            )
        )
    return normalized


def _require_education_degree_policy(
    payload: dict[str, Any], *, field_name: str, run_id: str, stage: str
) -> EducationDegreeLocalizationPolicy | None:
    raw = payload.get(field_name)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="dict",
            actual_type=type(raw).__name__,
        )
    exceptions_raw = raw.get("exceptions", [])
    if not isinstance(exceptions_raw, list):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=f"{field_name}.exceptions",
            expected_type="list[object]",
            actual_type=type(exceptions_raw).__name__,
        )
    exceptions: list[EducationDegreePolicyException] = []
    for index, item in enumerate(exceptions_raw):
        if not isinstance(item, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field=f"{field_name}.exceptions[{index}]",
                expected_type="dict",
                actual_type=type(item).__name__,
            )
        exceptions.append(
            EducationDegreePolicyException(
                source_degree=_require_nested_string(
                    item, "source_degree", run_id, stage, f"{field_name}.exceptions"
                ),
                approved_rendering=_require_nested_string(
                    item, "approved_rendering", run_id, stage, f"{field_name}.exceptions"
                ),
                reason=_require_nested_string(
                    item, "reason", run_id, stage, f"{field_name}.exceptions"
                ),
            )
        )
    decision = _require_nested_string(raw, "decision", run_id, stage, field_name)
    apply_consistently = raw.get("apply_consistently")
    if not isinstance(apply_consistently, bool):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=f"{field_name}.apply_consistently",
            expected_type="bool",
            actual_type=type(apply_consistently).__name__,
        )
    rule = _require_nested_string(raw, "rule", run_id, stage, field_name)
    return EducationDegreeLocalizationPolicy(
        decision=decision,
        apply_consistently=apply_consistently,
        rule=rule,
        exceptions=exceptions,
    )


def _normalize_revision_dispositions(
    payload: Any,
    *,
    run_id: str,
    stage: str,
    field_name: str,
) -> list[RevisionDisposition]:
    if not isinstance(payload, list):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="list[object]",
            actual_type=type(payload).__name__,
        )

    normalized: list[RevisionDisposition] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field=f"{field_name}[{index}]",
                expected_type="dict",
                actual_type=type(item).__name__,
            )
        normalized.append(
            RevisionDisposition(
                finding_id=_require_nested_string(item, "finding_id", run_id, stage, field_name),
                status=str(item.get("status", "declined")).strip() or "declined",
                rationale=_require_nested_string_alias(
                    item,
                    ("rationale", "reason"),
                    run_id,
                    stage,
                    field_name,
                ),
            )
        )
    return normalized


def _normalize_applied_findings(
    payload: Any,
    *,
    run_id: str,
    stage: str,
    field_name: str,
) -> list[RevisionAppliedFinding]:
    if not isinstance(payload, list):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="list[object]",
            actual_type=type(payload).__name__,
        )
    normalized: list[RevisionAppliedFinding] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field=f"{field_name}[{index}]",
                expected_type="dict",
                actual_type=type(item).__name__,
            )
        normalized.append(
            RevisionAppliedFinding(
                finding_id=_require_nested_string(item, "finding_id", run_id, stage, field_name),
                field_path=_require_nested_string(item, "field_path", run_id, stage, field_name),
                change_summary=_require_nested_string(
                    item, "change_summary", run_id, stage, field_name
                ),
            )
        )
    return normalized


def _normalize_protected_field_exceptions(
    payload: Any,
    *,
    run_id: str,
    stage: str,
    field_name: str,
) -> list[ProtectedFieldException]:
    if not isinstance(payload, list):
        raise TypeMismatchError(
            message="Field type mismatch",
            run_id=run_id,
            stage=stage,
            field=field_name,
            expected_type="list[object]",
            actual_type=type(payload).__name__,
        )
    normalized: list[ProtectedFieldException] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise TypeMismatchError(
                message="Field type mismatch",
                run_id=run_id,
                stage=stage,
                field=f"{field_name}[{index}]",
                expected_type="dict",
                actual_type=type(item).__name__,
            )
        normalized.append(
            ProtectedFieldException(
                finding_id=_require_nested_string(item, "finding_id", run_id, stage, field_name),
                field_path=_require_nested_string(item, "field_path", run_id, stage, field_name),
                protected_value=_require_nested_string(
                    item, "protected_value", run_id, stage, field_name
                ),
                reason=_require_nested_string(item, "reason", run_id, stage, field_name),
            )
        )
    return normalized


def _require_nested_string_alias(
    payload: dict[str, Any],
    field_names: tuple[str, ...],
    run_id: str,
    stage: str,
    parent: str,
) -> str:
    for field_name in field_names:
        value = payload.get(field_name)
        if isinstance(value, str):
            return value
    raise TypeMismatchError(
        message="Field type mismatch",
        run_id=run_id,
        stage=stage,
        field=f"{parent}.{field_names[0]}",
        expected_type="str",
        actual_type="missing",
    )


def _require_nested_string_list_optional(
    payload: dict[str, Any],
    field_name: str,
    run_id: str,
    stage: str,
    parent: str,
) -> list[str]:
    value = payload.get(field_name, [])
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
