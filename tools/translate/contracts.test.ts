import assert from "node:assert/strict";
import { test } from "node:test";

import {
  schemaFor,
  unquoted,
  validateCritique,
  validateCvRevision,
  validateFinalReview,
  validateRevision,
  validateTerminologyPolicy,
  validateTranslation,
  validateVoiceIntent,
} from "./contracts.ts";
import type { CvDocument, ProseDocument } from "./documents.ts";

// The old engine's tests of contracts.py (tests/test_translation_v2_contracts.py), case for case,
// and the normalized form the later stages are shown.

const value = <T>(validated: { value: T } | { finding: string }): T => {
  assert.ok("value" in validated, "finding" in validated ? validated.finding : "");
  return validated.value;
};
const finding = (validated: { value: unknown } | { finding: string }): string => {
  assert.ok("finding" in validated, "expected a finding");
  return validated.finding;
};

test("a translation needs a title, an excerpt, a body and a list of string tags", () => {
  assert.deepEqual(value(validateTranslation({ title: "T", excerpt: "E", tags: ["a"], content: "C" })), { title: "T", excerpt: "E", tags: ["a"], content: "C" });
  assert.equal(finding(validateTranslation({ title: "T", excerpt: "E", tags: [] })), 'Missing required field "content"');
  assert.equal(finding(validateTranslation({ title: "T", excerpt: "E", tags: ["ok", 1], content: "C" })), 'Field "tags" must be a list of strings, and is a list');
  assert.equal(finding(validateTranslation("text")), "The answer must be one JSON object, and is a string");
});

test("a critique with findings that are not a list is refused", () => {
  assert.equal(finding(validateCritique({ score: 88, feedback: "Looks mostly good", needs_refinement: false, findings: "not-a-list" })), 'Field "findings" must be a list, and is a string');
});

test("a critique in the older structured form is read as the old engine read it", () => {
  const critique = value(
    validateCritique({
      overall_score: 93,
      decision_hint: "auto_refine",
      confidence: 0.82,
      dimensions: [
        { name: "accuracy_completeness", score_100: 94 },
        { name: "terminology_entities", score_100: 79 },
        { name: "markdown_code_link_fidelity", score_100: 97 },
      ],
      error_summary: { minor: 2, major: 1, critical: 0 },
      feedback: "Terminology needs one pass",
      findings: [{ description: "One term is mistranslated", source_span: "throughput", target_span: "taxa" }],
    }),
  );
  assert.equal(critique.score, 93);
  assert.equal(critique.needs_refinement, true, "a decision hint other than accept asks for refinement");
  assert.equal(critique.dimension_scores.terminology_entities, 79);
  assert.equal(critique.critical_errors, 0);
  assert.equal(critique.major_core_errors, 1);
  assert.equal(critique.confidence, 0.82);
  assert.deepEqual(critique.findings[0], {
    finding_id: "finding-1",
    severity: "major",
    category: "general",
    source_span: "throughput",
    target_span: "taxa",
    description: "One term is mistranslated",
    rewrite_instruction: "One term is mistranslated",
  });
});

test("a simple critique keeps its defaults: no errors, confidence 1, the score for every core dimension", () => {
  const critique = value(validateCritique({ score: 91, feedback: "Looks mostly good", needs_refinement: false, findings: ["Minor punctuation issue"] }));
  assert.equal(critique.needs_refinement, false);
  assert.equal(critique.critical_errors, 0);
  assert.equal(critique.major_core_errors, 0);
  assert.equal(critique.confidence, 1);
  assert.deepEqual(critique.dimension_scores, { accuracy_completeness: 91, terminology_entities: 91, markdown_code_link_fidelity: 91 });
  assert.equal(critique.findings[0]!.description, "Minor punctuation issue");
});

test("a critique as the prompt asks for it is normalized to the old CritiqueFinding", () => {
  const critique = value(
    validateCritique({
      score: 81.5,
      feedback: "Two calques.",
      needs_refinement: true,
      dimension_scores: { accuracy_completeness: 90, terminology_entities: 88, markdown_code_link_fidelity: 99, locale_naturalness: 70, borrowing_consistency: 85, rhetorical_structure: 80 },
      critical_errors: 0,
      major_core_errors: 1,
      confidence: 0.8,
      findings: [{ id: "finding-1", severity: "major", dimension: "locale_naturalness", source_span: "S", target_span: "T", description: "Calque.", fix_hint: "Rebuild it." }],
    }),
  );
  assert.deepEqual(critique.findings, [
    { finding_id: "finding-1", severity: "major", category: "locale_naturalness", source_span: "S", target_span: "T", description: "Calque.", rewrite_instruction: "Rebuild it." },
  ]);
  assert.equal(finding(validateCritique({ score: 1, feedback: "f", needs_refinement: true, critical_errors: -1 })), 'Field "critical_errors" must be a whole number, zero or more, and is a number');
  assert.equal(finding(validateCritique({ score: 1, feedback: "f" })), 'Missing required field "needs_refinement"');
});

test("the source analysis needs every field of the voice packet", () => {
  const packet = {
    author_voice_summary: "Dry, technical, structurally aware.",
    tone: "technical",
    register: "professional",
    sentence_rhythm: ["medium cadence"],
    connective_tissue: ["contrastive pivots"],
    rhetorical_moves: ["claim then qualification"],
    humor_signals: ["understated irony"],
    stance_markers: ["first-person ownership"],
    must_preserve: ["OpenCode"],
  };
  assert.deepEqual(value(validateVoiceIntent(packet)), packet);
  const { must_preserve: _, ...short } = packet;
  assert.equal(finding(validateVoiceIntent(short)), 'Missing required field "must_preserve"');
});

test("the terminology policy reads its decisions under the old names, and its degree policy", () => {
  const policy = value(
    validateTerminologyPolicy({
      keep_english: ["cache adapter"],
      localize: ["latency => latência"],
      context_sensitive: ["rollout"],
      do_not_translate: ["OpenCode"],
      resolved_decisions: [
        { source_term: "AI Platform", approved_rendering: "AI Platform", decision: "keep_english", scope: "artifact-wide", applies_to: ["summary"], notes: "Internal product name." },
      ],
      education_degree_localization_policy: {
        decision: "localize_equivalent",
        apply_consistently: true,
        rule: "Use recruiter-facing PT-BR degree names consistently.",
        exceptions: [{ source_degree: "Bachelor of Economics", approved_rendering: "Bacharelado em Economia", reason: "Idiomatic." }],
      },
      consistency_rules: ["Keep terminology stable."],
      rationale_notes: ["Borrow infra terms when PT-BR usage expects it."],
    }),
  );
  assert.deepEqual(policy.resolved_decisions, [
    { source_term: "AI Platform", preferred_rendering: "AI Platform", decision_type: "keep_english", scope: "artifact-wide", rationale: "Internal product name.", applies_to: ["summary"] },
  ]);
  assert.equal(policy.education_degree_localization_policy!.apply_consistently, true);
  const post = value(
    validateTerminologyPolicy({ keep_english: [], localize: [], context_sensitive: [], do_not_translate: [], consistency_rules: [], rationale_notes: [] }),
  );
  assert.deepEqual([post.resolved_decisions, post.education_degree_localization_policy], [[], null], "decisions may be left out; a post has no degree policy");
  assert.equal(
    finding(validateTerminologyPolicy({ keep_english: [], localize: [], context_sensitive: [], do_not_translate: [], consistency_rules: [], rationale_notes: [], resolved_decisions: [{ source_term: "x", scope: "s", notes: "n", decision: "d" }] })),
    'Field "resolved_decisions.preferred_rendering" must be a string, and is missing',
  );
});

test("a revision is a translation with its report: each finding applied or declined, with why", () => {
  const revision = value(
    validateRevision({
      title: "Title",
      excerpt: "Summary",
      tags: ["ia"],
      content: "Revised content",
      applied_feedback: [{ finding_id: "finding-1", rationale: "fixed terminology" }],
      declined_feedback: [{ finding_id: "finding-2", reason: "the source says it" }],
      rewrite_summary: ["re-anchored the second paragraph in the source"],
    }),
  );
  assert.deepEqual(revision.applied_feedback, [{ finding_id: "finding-1", status: "applied", rationale: "fixed terminology" }]);
  assert.deepEqual(revision.declined_feedback, [{ finding_id: "finding-2", status: "declined", rationale: "the source says it" }]);
  assert.equal(finding(validateRevision({ title: "T", excerpt: "E", tags: [], content: "C", applied_feedback: ["fixed terminology"] })), 'Field "applied_feedback[0]" must be an object, and is a string');
  assert.deepEqual(revision.unresolved_risks, []);
  assert.equal(finding(validateRevision({ title: "T", excerpt: "E", tags: ["ok", 1], content: "C", applied_feedback: [] })), 'Field "tags" must be a list of strings, and is a list');
  assert.equal(finding(validateRevision({ title: "T", excerpt: "E", tags: [], content: "C", declined_feedback: [{ finding_id: "f" }] })), 'Field "declined_feedback.rationale" must be a string, and is missing', "a decline says why");
});

test("the CV's revision is the revised CV and its report", () => {
  const revision = value(validateCvRevision({ revised_cv: { name: "D" }, revision_report: { applied_findings: [{ finding_id: "f1", field_path: "summary", change_summary: "c" }] } }));
  assert.deepEqual(revision, {
    revised_cv: { name: "D" },
    revision_report: { applied_findings: [{ finding_id: "f1", field_path: "summary", change_summary: "c" }], declined_findings: [], protected_field_exceptions: [] },
  });
  assert.equal(finding(validateCvRevision({ revised_cv: { name: "D" } })), 'Field "revision_report" must be an object, and is missing');
});

test("the final review needs every field of its gate", () => {
  const review = { accept: true, publish_ready: true, confidence: 0.91, residual_issues: [], voice_score: 94, terminology_score: 96, locale_naturalness_score: 93 };
  assert.deepEqual(value(validateFinalReview(review)), review);
  assert.equal(finding(validateFinalReview({ ...review, publish_ready: "yes" })), 'Field "publish_ready" must be a boolean, and is a string');
});

test("a residual issue quotes a passage and names what it violates, and the passage must be in the text", () => {
  const issue = { passage: "Deveria soar familiar.", violates: "Review checks: literal calques", failure: "a calque" };
  const review = { accept: false, publish_ready: false, confidence: 0.9, residual_issues: [issue], voice_score: 80, terminology_score: 80, locale_naturalness_score: 60 };
  assert.deepEqual(value(validateFinalReview(review)).residual_issues, [issue]);
  assert.match(finding(validateFinalReview({ ...review, residual_issues: [{ ...issue, passage: " " }] })), /residual_issues\[0\] quotes no passage/);
  assert.match(finding(validateFinalReview({ ...review, residual_issues: [{ ...issue, violates: "" }] })), /residual_issues\[0\] names nothing it violates/);
  assert.match(finding(validateFinalReview({ ...review, residual_issues: ["stiff prose"] })), /must be an object with `passage`, `violates` and `failure`/);
  const texts = [{ content: "A maré sobe.\n\nDeveria  soar\nfamiliar." }, ["The tide comes in."]];
  assert.deepEqual(unquoted([issue, { ...issue, passage: "«A maré … familiar.»" }, { ...issue, passage: "The tide comes in." }], ...texts), []);
  assert.deepEqual(unquoted([{ ...issue, passage: "A maré desce." }], ...texts), [
    'residual_issues[0] quotes "A maré desce.", which is in neither the candidate nor the source: quote the passage exactly as it is written',
  ]);
});

test("each stage asks the Hub for the shape its prompt shows", () => {
  const post = { kind: "post" } as ProseDocument;
  const cv = { kind: "cv", data: { name: "D", contact: { email: "e" } } } as unknown as CvDocument;
  const keys = (schema: { schema: Record<string, unknown> }) => schema.schema.required;
  assert.deepEqual(keys(schemaFor("source_analysis", post)), ["author_voice_summary", "tone", "register", "sentence_rhythm", "connective_tissue", "rhetorical_moves", "humor_signals", "stance_markers", "must_preserve"]);
  assert.deepEqual(keys(schemaFor("terminology_policy", post)), ["keep_english", "localize", "context_sensitive", "do_not_translate", "resolved_decisions", "consistency_rules", "rationale_notes"]);
  assert.ok((keys(schemaFor("terminology_policy", cv)) as string[]).includes("education_degree_localization_policy"));
  assert.deepEqual(keys(schemaFor("translate", post)), ["title", "excerpt", "tags", "content"]);
  assert.equal(schemaFor("translate", cv).name, "cv_translation");
  assert.deepEqual(keys(schemaFor("critique", post)), ["score", "feedback", "needs_refinement", "dimension_scores", "critical_errors", "major_core_errors", "confidence", "findings"]);
  assert.deepEqual(keys(schemaFor("revise", post)), ["title", "excerpt", "tags", "content", "applied_feedback", "declined_feedback", "rewrite_summary", "unresolved_risks"]);
  assert.deepEqual(schemaFor("revise", post, { owner: true }).name, "owner_revision");
  assert.ok((keys(schemaFor("revise", post, { owner: true })) as string[]).includes("comments"));
  assert.deepEqual(keys(schemaFor("revise", cv)), ["revised_cv", "revision_report"]);
  assert.deepEqual(keys(schemaFor("final_review", post)), ["accept", "publish_ready", "confidence", "residual_issues", "voice_score", "terminology_score", "locale_naturalness_score"]);
});
