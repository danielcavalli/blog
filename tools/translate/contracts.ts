// What every stage answers: its shape as JSON Schema, and its validation. The old engine's
// `contracts.py`, field for field.
//
// The schema is what the Hub is asked for (structured output); it is the shape each prompt's
// BEGIN_OUTPUT_JSON shows. The validator is what is accepted, as `contracts.py` accepted it: the same
// required fields and types, the same defaults for what may be left out, the same aliases, and the
// same normalized form, which is what the later stages are shown. A validator stops at the first
// violation, as the old one raised on it, and says it as a finding the model can act on.
//
// What a translation or a revision says (a post's title, excerpt, tags and body; the CV) is checked
// further by checks.ts. The CV's content has the CV's own shape, which for today's cv_data.yaml is
// the old `CVTranslationOutput` exactly.

import type { SourceDocument } from "./documents.ts";

// ---------- the stages' outputs, as the old dataclasses ----------

export interface VoiceIntentPacket {
  author_voice_summary: string;
  tone: string;
  register: string;
  sentence_rhythm: string[];
  connective_tissue: string[];
  rhetorical_moves: string[];
  humor_signals: string[];
  stance_markers: string[];
  must_preserve: string[];
}

export interface TerminologyDecision {
  source_term: string;
  preferred_rendering: string;
  decision_type: string;
  scope: string;
  rationale: string;
  applies_to: string[];
}

export interface EducationDegreePolicyException {
  source_degree: string;
  approved_rendering: string;
  reason: string;
}

export interface EducationDegreeLocalizationPolicy {
  decision: string;
  apply_consistently: boolean;
  rule: string;
  exceptions: EducationDegreePolicyException[];
}

export interface TerminologyPolicyPacket {
  keep_english: string[];
  localize: string[];
  context_sensitive: string[];
  do_not_translate: string[];
  consistency_rules: string[];
  rationale_notes: string[];
  resolved_decisions: TerminologyDecision[];
  education_degree_localization_policy: EducationDegreeLocalizationPolicy | null;
}

export interface TranslationOutput {
  title: string;
  excerpt: string;
  tags: string[];
  content: string;
}

export interface CritiqueFinding {
  finding_id: string;
  severity: string;
  category: string;
  source_span: string;
  target_span: string;
  description: string;
  rewrite_instruction: string;
}

export interface CritiqueOutput {
  score: number;
  feedback: string;
  needs_refinement: boolean;
  findings: CritiqueFinding[];
  dimension_scores: Record<string, number>;
  critical_errors: number;
  major_core_errors: number;
  confidence: number;
}

export interface RevisionDisposition {
  finding_id: string;
  status: string;
  rationale: string;
}

export interface RevisionOutput extends TranslationOutput {
  applied_feedback: string[];
  declined_feedback: RevisionDisposition[];
  rewrite_summary: string[];
  unresolved_risks: string[];
}

export interface RevisionAppliedFinding {
  finding_id: string;
  field_path: string;
  change_summary: string;
}

export interface ProtectedFieldException {
  finding_id: string;
  field_path: string;
  protected_value: string;
  reason: string;
}

export interface CVRevisionReport {
  applied_findings: RevisionAppliedFinding[];
  declined_findings: RevisionDisposition[];
  protected_field_exceptions: ProtectedFieldException[];
}

export interface CVRevisionOutput {
  revised_cv: Record<string, unknown>;
  revision_report: CVRevisionReport;
}

export interface FinalReviewOutput {
  accept: boolean;
  publish_ready: boolean;
  confidence: number;
  residual_issues: string[];
  voice_score: number;
  terminology_score: number;
  locale_naturalness_score: number;
}

// ---------- validation ----------

/** A value that passed its contract, or the first way it did not. */
export type Validated<T> = { value: T } | { finding: string };

class Violation extends Error {}

type Payload = Record<string, unknown>;

const isRecord = (value: unknown): value is Payload => typeof value === "object" && value !== null && !Array.isArray(value);

const typeName = (value: unknown): string =>
  value === undefined ? "missing" : value === null ? "null" : Array.isArray(value) ? "a list" : isRecord(value) ? "an object" : `a ${typeof value}`;

const TYPES = {
  str: (value: unknown): value is string => typeof value === "string",
  number: (value: unknown): value is number => typeof value === "number" && Number.isFinite(value),
  bool: (value: unknown): value is boolean => typeof value === "boolean",
  list: (value: unknown): value is unknown[] => Array.isArray(value),
  dict: isRecord,
};

const NAMES: Record<keyof typeof TYPES, string> = { str: "a string", number: "a number", bool: "a boolean", list: "a list", dict: "an object" };

const mismatch = (field: string, expected: string, value: unknown): never => {
  throw new Violation(`Field "${field}" must be ${expected}, and is ${typeName(value)}`);
};

// `_require_field`: present, and of the type.
function required<K extends keyof typeof TYPES>(payload: Payload, field: string, type: K, at = field) {
  if (!(field in payload)) throw new Violation(`Missing required field "${at}"`);
  const value = payload[field];
  if (!TYPES[type](value)) mismatch(at, NAMES[type], value);
  return value as K extends "str" ? string : K extends "number" ? number : K extends "bool" ? boolean : K extends "list" ? unknown[] : Payload;
}

const isStrings = (value: unknown): value is string[] => Array.isArray(value) && value.every((item) => typeof item === "string");

// `_require_string_list`.
function strings(payload: Payload, field: string, at = field): string[] {
  const value = required(payload, field, "list", at);
  if (!isStrings(value)) mismatch(at, "a list of strings", value);
  return [...(value as string[])];
}

// A list that may be left out (`payload.get(field, [])`) and is otherwise a list of strings.
function optionalStrings(payload: Payload, field: string, at = field): string[] {
  const value = payload[field] ?? [];
  if (!isStrings(value)) mismatch(at, "a list of strings", value);
  return [...(value as string[])];
}

// `_require_nested_string`: a string inside a nested object, where missing is a type mismatch.
function nested(payload: Payload, field: string, parent: string): string {
  const value = payload[field];
  if (typeof value !== "string") mismatch(`${parent}.${field}`, "a string", value);
  return value as string;
}

// `_require_nested_string_alias`: the first of these names that holds a string.
function alias(payload: Payload, fields: string[], parent: string): string {
  for (const field of fields) if (typeof payload[field] === "string") return payload[field] as string;
  return mismatch(`${parent}.${fields[0]}`, "a string", payload[fields[0]!]);
}

// A list of objects, each read by `read`, that may be left out.
function records<T>(payload: Payload, field: string, read: (item: Payload, at: string) => T, at = field): T[] {
  const value = payload[field] ?? [];
  if (!Array.isArray(value)) mismatch(at, "a list of objects", value);
  return (value as unknown[]).map((item, index) => {
    if (!isRecord(item)) mismatch(`${at}[${index}]`, "an object", item);
    return read(item as Payload, at);
  });
}

// A text field written as `str(item.get(field, default)).strip() or default`.
const text = (value: unknown, fallback: string): string => (value == null ? fallback : String(value).trim() || fallback);

function contract<T>(read: (payload: Payload) => T): (answer: unknown) => Validated<T> {
  return (answer) => {
    try {
      if (!isRecord(answer)) throw new Violation(`The answer must be one JSON object, and is ${typeName(answer)}`);
      return { value: read(answer) };
    } catch (error) {
      if (error instanceof Violation) return { finding: error.message };
      throw error;
    }
  };
}

const readVoiceIntent = (payload: Payload): VoiceIntentPacket => ({
  author_voice_summary: required(payload, "author_voice_summary", "str"),
  tone: required(payload, "tone", "str"),
  register: required(payload, "register", "str"),
  sentence_rhythm: strings(payload, "sentence_rhythm"),
  connective_tissue: strings(payload, "connective_tissue"),
  rhetorical_moves: strings(payload, "rhetorical_moves"),
  humor_signals: strings(payload, "humor_signals"),
  stance_markers: strings(payload, "stance_markers"),
  must_preserve: strings(payload, "must_preserve"),
});

/** `validate_voice_intent_output`: the source analysis. */
export const validateVoiceIntent = contract(readVoiceIntent);

function readDegreePolicy(payload: Payload): EducationDegreeLocalizationPolicy | null {
  const field = "education_degree_localization_policy";
  const raw = payload[field];
  if (raw == null) return null;
  if (!isRecord(raw)) return mismatch(field, "an object", raw);
  const exceptions = records(
    raw,
    "exceptions",
    (item, at) => ({
      source_degree: nested(item, "source_degree", at),
      approved_rendering: nested(item, "approved_rendering", at),
      reason: nested(item, "reason", at),
    }),
    `${field}.exceptions`,
  );
  const decision = nested(raw, "decision", field);
  if (typeof raw.apply_consistently !== "boolean") mismatch(`${field}.apply_consistently`, "a boolean", raw.apply_consistently);
  return { decision, apply_consistently: raw.apply_consistently as boolean, rule: nested(raw, "rule", field), exceptions };
}

const readTerminologyPolicy = (payload: Payload): TerminologyPolicyPacket => ({
  keep_english: strings(payload, "keep_english"),
  localize: strings(payload, "localize"),
  context_sensitive: strings(payload, "context_sensitive"),
  do_not_translate: strings(payload, "do_not_translate"),
  consistency_rules: strings(payload, "consistency_rules"),
  rationale_notes: strings(payload, "rationale_notes"),
  resolved_decisions: records(payload, "resolved_decisions", (item, at) => ({
    source_term: nested(item, "source_term", at),
    preferred_rendering: alias(item, ["preferred_rendering", "approved_rendering"], at),
    decision_type: alias(item, ["decision_type", "decision"], at),
    scope: nested(item, "scope", at),
    rationale: alias(item, ["rationale", "notes"], at),
    applies_to: optionalStrings(item, "applies_to", `${at}.applies_to`),
  })),
  education_degree_localization_policy: readDegreePolicy(payload),
});

/** `validate_terminology_policy_output`: the terminology and borrowing policy. */
export const validateTerminologyPolicy = contract(readTerminologyPolicy);

const readTranslation = (payload: Payload): TranslationOutput => {
  const title = required(payload, "title", "str");
  const excerpt = required(payload, "excerpt", "str");
  const content = required(payload, "content", "str");
  return { title, excerpt, tags: strings(payload, "tags"), content };
};

/** `validate_translation_output`: a post's, a page's or a presentation's draft. */
export const validateTranslation = contract(readTranslation);

// `_normalize_findings`: a list of strings or a list of objects, never a mix.
function readFindings(payload: Payload): CritiqueFinding[] {
  const findings = payload.findings ?? [];
  if (!Array.isArray(findings)) return mismatch("findings", "a list", findings);
  if (findings.every((item) => typeof item === "string")) {
    return findings.map((item: string, index) => ({
      finding_id: `finding-${index + 1}`,
      severity: "major",
      category: "general",
      source_span: "",
      target_span: "",
      description: item,
      rewrite_instruction: item,
    }));
  }
  if (!findings.every(isRecord)) return mismatch("findings", "a list of strings or a list of objects", findings);
  return findings.map((item, index) => {
    const description = item.description;
    if (typeof description !== "string") return mismatch("findings.description", "a string", description);
    return {
      finding_id: text(item.id, `finding-${index + 1}`),
      severity: text(item.severity, "major"),
      category: text(item.dimension ?? item.category, "general"),
      source_span: text(item.source_span, ""),
      target_span: text(item.target_span, ""),
      description,
      rewrite_instruction: text(item.fix_hint ?? item.rewrite_instruction, description),
    };
  });
}

const CORE_DIMENSIONS = ["accuracy_completeness", "terminology_entities", "markdown_code_link_fidelity"];

// `_extract_dimension_scores`: `dimension_scores`, or the older `dimensions` list, with the core
// dimensions always present.
function readDimensionScores(payload: Payload, fallback: number): Record<string, number> {
  const scores: Record<string, number> = {};
  let structured = false;
  if ("dimension_scores" in payload) {
    const raw = payload.dimension_scores;
    if (!isRecord(raw)) mismatch("dimension_scores", "an object of numbers", raw);
    for (const [key, value] of Object.entries(raw as Payload)) {
      if (!TYPES.number(value)) mismatch(`dimension_scores.${key}`, "a number", value);
      scores[key] = value as number;
    }
    structured = true;
  } else if ("dimensions" in payload) {
    const raw = payload.dimensions;
    if (!Array.isArray(raw)) mismatch("dimensions", "a list of objects", raw);
    for (const item of raw as unknown[]) {
      if (!isRecord(item) || typeof item.name !== "string" || !TYPES.number(item.score_100)) {
        mismatch("dimensions", "a list of {name, score_100}", item);
      }
      scores[(item as Payload).name as string] = (item as Payload).score_100 as number;
    }
    structured = true;
  }
  for (const name of CORE_DIMENSIONS) if (!(name in scores)) scores[name] = structured ? 0 : fallback;
  return scores;
}

// `_extract_nonnegative_int`, with the older `error_summary` as where else to look.
function count(payload: Payload, field: string, fallback: [string, string]): number {
  let value: unknown = 0;
  if (field in payload) value = payload[field];
  else {
    const parent = payload[fallback[0]];
    if (isRecord(parent)) value = parent[fallback[1]];
  }
  if (!Number.isInteger(value) || (value as number) < 0) mismatch(field, "a whole number, zero or more", value);
  return value as number;
}

const readCritique = (payload: Payload): CritiqueOutput => {
  const scoreField = "overall_score" in payload ? "overall_score" : "score";
  const score = required(payload, scoreField, "number");
  const hint = typeof payload.decision_hint === "string" ? payload.decision_hint : null;
  let feedback = payload.feedback;
  if (feedback == null && hint !== null) feedback = `Decision hint: ${hint}`;
  if (feedback == null) throw new Violation('Missing required field "feedback"');
  if (typeof feedback !== "string") mismatch("feedback", "a string", feedback);
  let needsRefinement = payload.needs_refinement;
  if (needsRefinement == null && hint !== null) needsRefinement = hint !== "accept";
  if (needsRefinement == null) throw new Violation('Missing required field "needs_refinement"');
  if (typeof needsRefinement !== "boolean") mismatch("needs_refinement", "a boolean", needsRefinement);
  const findings = readFindings(payload);
  const dimension_scores = readDimensionScores(payload, score);
  const critical_errors = count(payload, "critical_errors", ["error_summary", "critical"]);
  const major_core_errors = count(payload, "major_core_errors", ["error_summary", "major"]);
  const confidence = payload.confidence ?? 1;
  if (!TYPES.number(confidence)) mismatch("confidence", "a number", confidence);
  return {
    score,
    feedback: feedback as string,
    needs_refinement: needsRefinement as boolean,
    findings,
    dimension_scores,
    critical_errors,
    major_core_errors,
    confidence: confidence as number,
  };
};

/** `validate_critique_output`: the critic's report. */
export const validateCritique = contract(readCritique);

// `_normalize_revision_dispositions`.
const readDispositions = (payload: Payload, field: string, at = field): RevisionDisposition[] =>
  records(
    payload,
    field,
    (item, where) => ({
      finding_id: nested(item, "finding_id", where),
      status: text(item.status, "declined"),
      rationale: alias(item, ["rationale", "reason"], where),
    }),
    at,
  );

const readRevision = (payload: Payload): RevisionOutput => ({
  ...readTranslation(payload),
  applied_feedback: optionalStrings(payload, "applied_feedback"),
  declined_feedback: readDispositions(payload, "declined_feedback"),
  rewrite_summary: optionalStrings(payload, "rewrite_summary"),
  unresolved_risks: optionalStrings(payload, "unresolved_risks"),
});

/** `validate_revision_output`: a post's, a page's or a presentation's revision and its report. */
export const validateRevision = contract(readRevision);

const readCvRevision = (payload: Payload): CVRevisionOutput => {
  const cv = payload.revised_cv ?? payload.cv;
  if (!isRecord(cv)) return mismatch("revised_cv", "an object", cv);
  const report = payload.revision_report;
  if (!isRecord(report)) return mismatch("revision_report", "an object", report);
  return {
    revised_cv: cv,
    revision_report: {
      applied_findings: records(
        report,
        "applied_findings",
        (item, at) => ({
          finding_id: nested(item, "finding_id", at),
          field_path: nested(item, "field_path", at),
          change_summary: nested(item, "change_summary", at),
        }),
        "revision_report.applied_findings",
      ),
      declined_findings: readDispositions(report, "declined_findings", "revision_report.declined_findings"),
      protected_field_exceptions: records(
        report,
        "protected_field_exceptions",
        (item, at) => ({
          finding_id: nested(item, "finding_id", at),
          field_path: nested(item, "field_path", at),
          protected_value: nested(item, "protected_value", at),
          reason: nested(item, "reason", at),
        }),
        "revision_report.protected_field_exceptions",
      ),
    },
  };
};

/** `validate_cv_revision_output`: the CV's revision and its report. */
export const validateCvRevision = contract(readCvRevision);

const readFinalReview = (payload: Payload): FinalReviewOutput => {
  const accept = required(payload, "accept", "bool");
  const publish_ready = required(payload, "publish_ready", "bool");
  const confidence = required(payload, "confidence", "number");
  const voice_score = required(payload, "voice_score", "number");
  const terminology_score = required(payload, "terminology_score", "number");
  const locale_naturalness_score = required(payload, "locale_naturalness_score", "number");
  return {
    accept,
    publish_ready,
    confidence,
    residual_issues: strings(payload, "residual_issues"),
    voice_score,
    terminology_score,
    locale_naturalness_score,
  };
};

/** `validate_final_review_output`: the final review's verdict. */
export const validateFinalReview = contract(readFinalReview);

// ---------- the shapes asked of the Hub ----------

export interface Schema {
  name: string;
  schema: Record<string, unknown>;
}

const object = (properties: Record<string, unknown>): Record<string, unknown> => ({
  type: "object",
  properties,
  required: Object.keys(properties),
  additionalProperties: false,
});

const STRING = { type: "string" };
const NUMBER = { type: "number" };
const INTEGER = { type: "integer" };
const BOOLEAN = { type: "boolean" };
const STRINGS = { type: "array", items: STRING };
const listOf = (properties: Record<string, unknown>) => ({ type: "array", items: object(properties) });

// The shape of a value, as JSON Schema: the CV's translation has the shape of the CV.
export function shapeOf(value: unknown): Record<string, unknown> {
  if (Array.isArray(value)) return { type: "array", items: value.length ? entryShape(value) : STRING };
  if (isRecord(value)) return object(Object.fromEntries(Object.entries(value).map(([key, child]) => [key, shapeOf(child)])));
  return { type: value === null ? "null" : typeof value };
}

// The entries of a list as one shape: every key any entry has, required where every entry has it.
function entryShape(entries: unknown[]): Record<string, unknown> {
  const found = entries.filter(isRecord);
  if (found.length !== entries.length) return shapeOf(entries[0]);
  const properties: Record<string, unknown> = {};
  for (const record of found) for (const [key, child] of Object.entries(record)) properties[key] ??= shapeOf(child);
  const required = Object.keys(properties).filter((key) => found.every((record) => key in record));
  return { ...object(properties), required };
}

const PROSE = { title: STRING, excerpt: STRING, tags: STRINGS, content: STRING };

const SOURCE_ANALYSIS = object({
  author_voice_summary: STRING,
  tone: STRING,
  register: STRING,
  sentence_rhythm: STRINGS,
  connective_tissue: STRINGS,
  rhetorical_moves: STRINGS,
  humor_signals: STRINGS,
  stance_markers: STRINGS,
  must_preserve: STRINGS,
});

const POLICY = {
  keep_english: STRINGS,
  localize: STRINGS,
  context_sensitive: STRINGS,
  do_not_translate: STRINGS,
  resolved_decisions: listOf({ source_term: STRING, approved_rendering: STRING, decision: STRING, scope: STRING, applies_to: STRINGS, notes: STRING }),
};
const POLICY_NOTES = { consistency_rules: STRINGS, rationale_notes: STRINGS };
const DEGREE_POLICY = object({
  decision: STRING,
  apply_consistently: BOOLEAN,
  rule: STRING,
  exceptions: listOf({ source_degree: STRING, approved_rendering: STRING, reason: STRING }),
});

const CRITIQUE = object({
  score: NUMBER,
  feedback: STRING,
  needs_refinement: BOOLEAN,
  dimension_scores: object(
    Object.fromEntries(
      ["accuracy_completeness", "terminology_entities", "markdown_code_link_fidelity", "locale_naturalness", "borrowing_consistency", "rhetorical_structure"].map(
        (name) => [name, NUMBER],
      ),
    ),
  ),
  critical_errors: INTEGER,
  major_core_errors: INTEGER,
  confidence: NUMBER,
  findings: listOf({ id: STRING, severity: STRING, dimension: STRING, source_span: STRING, target_span: STRING, description: STRING, fix_hint: STRING }),
});

const REVISION_REPORT = {
  applied_feedback: STRINGS,
  declined_feedback: listOf({ finding_id: STRING, status: STRING, rationale: STRING }),
  rewrite_summary: STRINGS,
  unresolved_risks: STRINGS,
};

const CV_REVISION_REPORT = object({
  applied_findings: listOf({ finding_id: STRING, field_path: STRING, change_summary: STRING }),
  declined_findings: listOf({ finding_id: STRING, reason: STRING }),
  protected_field_exceptions: listOf({ finding_id: STRING, field_path: STRING, protected_value: STRING, reason: STRING }),
});

const FINAL_REVIEW = object({
  accept: BOOLEAN,
  publish_ready: BOOLEAN,
  confidence: NUMBER,
  residual_issues: STRINGS,
  voice_score: NUMBER,
  terminology_score: NUMBER,
  locale_naturalness_score: NUMBER,
});

const OWNER_COMMENTS = { type: "array", items: object({ id: INTEGER, addressed: BOOLEAN, note: STRING }) };

export type Stage = "source_analysis" | "terminology_policy" | "translate" | "critique" | "revise" | "final_review";

/** The structured output a stage asks for. The owner's revision also accounts for each of his comments. */
export function schemaFor(stage: Stage, source: SourceDocument, { owner = false } = {}): Schema {
  const cv = source.kind === "cv";
  switch (stage) {
    case "source_analysis":
      return { name: "source_analysis", schema: SOURCE_ANALYSIS };
    case "terminology_policy":
      return {
        name: "terminology_policy",
        schema: object(cv ? { ...POLICY, education_degree_localization_policy: DEGREE_POLICY, ...POLICY_NOTES } : { ...POLICY, ...POLICY_NOTES }),
      };
    case "translate":
      return cv ? { name: "cv_translation", schema: shapeOf(source.data) } : { name: "translation", schema: object(PROSE) };
    case "critique":
      return { name: "critique", schema: CRITIQUE };
    case "revise":
      if (cv) return { name: "cv_revision", schema: object({ revised_cv: shapeOf(source.data), revision_report: CV_REVISION_REPORT }) };
      if (owner) return { name: "owner_revision", schema: object({ ...PROSE, ...REVISION_REPORT, comments: OWNER_COMMENTS }) };
      return { name: "revision", schema: object({ ...PROSE, ...REVISION_REPORT }) };
    case "final_review":
      return { name: "final_review", schema: FINAL_REVIEW };
  }
}
