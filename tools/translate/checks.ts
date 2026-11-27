// The deterministic checks a model's answer must pass before it is written.
//
// They are the old engine's (`durable.py`, `protected_markdown.py`, `translation_common.py`,
// `presentation_translation.py`), following the content's new layout in two places: a link to
// another document points to that document's file in the reader's language, and a picture is a
// Markdown image whose path stays while its alt text and caption are translated.
//
// Every check returns findings, never throws: a finding is a sentence the model can act on, and all
// of them go into the one repair call.

import { sorted } from "./digest.ts";
import {
  deck,
  destinations,
  fenceSignatures,
  footnoteLabels,
  images,
  lf,
  parentheticals,
  protectedFences,
  shapeOf,
  stripFences,
} from "./markdown.ts";
import type { Destination } from "./markdown.ts";

export type ProseKind = "post" | "presentation" | "about";

/** The document being translated, as the checks need it. */
export interface ProseSource {
  kind: ProseKind;
  lang: string;
  target: string;
  title: string;
  excerpt: string;
  tags: string[];
  body: string;
  /** A link destination as it must read in the translation (a link to another document moves to its file in the target language). */
  mapLink: (destination: string) => string;
}

/** What the model answers for a post, a presentation or a page. */
export interface ProseAnswer {
  title: string;
  excerpt: string;
  tags: string[];
  content: string;
}

export interface Verdict {
  /** Why the answer cannot be written. Empty when it can. */
  findings: string[];
  /** Worth a look, and not a reason to refuse. */
  warnings: string[];
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const isStrings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((item) => typeof item === "string");

const typeName = (value: unknown): string =>
  value === null ? "null" : Array.isArray(value) ? "list" : typeof value === "object" ? "object" : typeof value;

const clip = (text: string, length = 120): string => {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > length ? `${flat.slice(0, length)}…` : flat;
};

// ---------- the answer's shape ----------

/** The findings about the shape of a prose answer: `title`, `excerpt`, `tags`, `content`. */
export function proseShape(answer: unknown): string[] {
  if (!isRecord(answer)) return [`The answer must be one JSON object, and is a ${typeName(answer)}`];
  const findings: string[] = [];
  for (const field of ["title", "excerpt", "content"]) {
    if (!(field in answer)) findings.push(`Missing required field "${field}"`);
    else if (typeof answer[field] !== "string") {
      findings.push(`Field "${field}" must be a string, and is a ${typeName(answer[field])}`);
    }
  }
  if (!("tags" in answer)) findings.push('Missing required field "tags"');
  else if (!isStrings(answer.tags)) findings.push('Field "tags" must be a list of strings');
  return findings;
}

// ---------- prose ----------

function footnotes(source: string, translated: string): string[] {
  const before = footnoteLabels(source);
  const after = footnoteLabels(translated);
  const differences: string[] = [];
  for (const name of new Set([...before.keys(), ...after.keys()])) {
    const [was, is] = [before.get(name) ?? 0, after.get(name) ?? 0];
    if (was !== is) differences.push(`[^${name}] appears ${was} time(s) in the source and ${is} in the translation`);
  }
  return differences.length
    ? [`Translation changed footnote identifiers or reference counts: ${differences.join("; ")}`]
    : [];
}

// About was written as a fixed run of paragraphs, and stays one.
function paragraphs(text: string): string[] {
  const parts = text.split("\n\n").map((part) => part.trim()).filter(Boolean);
  return parts[0]?.startsWith("# ") ? parts.slice(1) : parts;
}

function fences(source: string, translated: string): string[] {
  const before = protectedFences(source);
  const after = protectedFences(translated);
  if (before.length !== after.length) {
    return [
      `Translation changed protected fenced code: the source has ${before.length} fenced block(s) and the translation ${after.length}`,
    ];
  }
  const at = before.findIndex((block, index) => block !== after[index]);
  if (at === -1) return [];
  const mermaid = /^\s*(?:`{3,}|~{3,})mermaid/.test(before[at]!);
  return [
    `Translation changed protected fenced code: fenced block ${at + 1} (starting "${clip(before[at]!, 60)}") must be ` +
      (mermaid
        ? "the source's except for its visible labels and accessibility text"
        : "byte for byte the source's"),
  ];
}

const named = ({ kind, destination }: Destination): string => `${kind} \`${destination}\``;

function expected(source: ProseSource, text: string): Destination[] {
  return destinations(text).map((found) =>
    found.kind === "link" ? { kind: found.kind, destination: source.mapLink(found.destination) } : found,
  );
}

// The same destinations, each as many times: where they sit in the text is the translator's.
function sameDestinations(source: ProseSource, translated: string): string[] {
  const tally = new Map<string, number>();
  for (const wanted of expected(source, source.body)) tally.set(named(wanted), (tally.get(named(wanted)) ?? 0) + 1);
  for (const found of destinations(translated)) tally.set(named(found), (tally.get(named(found)) ?? 0) - 1);
  const missing = [...tally].filter(([, n]) => n > 0).map(([name]) => name);
  const unexpected = [...tally].filter(([, n]) => n < 0).map(([name]) => name);
  if (!missing.length && !unexpected.length) return [];
  const parts = [];
  if (missing.length) parts.push(`missing ${missing.join(", ")}`);
  if (unexpected.length) parts.push(`not in the source ${unexpected.join(", ")}`);
  return [`Translation changed protected link destinations: ${parts.join("; ")}`];
}

// A picture keeps its path (the destinations say so); its alt text and caption are translated, so
// neither may be dropped or invented.
function pictures(source: string, translated: string): string[] {
  const before = images(source);
  const after = images(translated);
  if (before.length !== after.length) return []; // the destinations already say which
  const findings: string[] = [];
  before.forEach((image, index) => {
    const other = after[index]!;
    if (image.path !== other.path) return;
    if (Boolean(image.alt.trim()) !== Boolean(other.alt.trim())) {
      findings.push(
        `Image \`${image.path}\` ${image.alt.trim() ? "lost its alt text: translate it" : "gained alt text the source does not have"}`,
      );
    }
    if (Boolean(image.title?.trim()) !== Boolean(other.title?.trim())) {
      findings.push(
        `Image \`${image.path}\` ${image.title?.trim() ? 'lost its title (the caption, in quotes after the path): translate it' : "gained a title the source does not have"}`,
      );
    }
  });
  return findings;
}

/** Parenthetical asides stay in parentheses, around the same thoughts, nested as they were. */
export function asides(source: string, translated: string, where = ""): string[] {
  const before = parentheticals(source);
  const after = parentheticals(translated);
  const [was, is] = [before.map(shapeOf), after.map(shapeOf)];
  if (was.length === is.length && was.every((shape, index) => shape === is[index])) return [];
  const rule =
    `Translation changed parenthetical asides${where}: preserve parentheses around the same thoughts, ` +
    "including nested asides; localize their contents without replacing the delimiters with commas or dashes. ";
  if (was.length === is.length) {
    // The same number of asides, so the one that differs is nested differently.
    const at = was.findIndex((shape, index) => shape !== is[index]);
    return [`${rule}Aside ${at + 1} is "${clip(before[at]!)}" in the source and "${clip(after[at]!)}" in the translation`];
  }
  // One was dropped or added somewhere: which one, only reading both can say.
  const listed = before.slice(0, 80).map((group, index) => `${index + 1}. "${clip(group, 60)}"`);
  return [
    `${rule}The source has ${was.length} and the translation ${is.length}. ` +
      `The source's${before.length > listed.length ? ` first ${listed.length}` : ""}, in order: ${listed.join(" ") || "none"}`,
  ];
}

function slides(source: ProseSource, translated: string): string[] {
  const before = deck(source.body);
  const after = deck(translated);
  if (before.error) return [`Source presentation markers are invalid: ${before.error}`];
  const findings: string[] = [];
  if (after.error) findings.push(`Translated presentation markers are invalid: ${after.error}`);
  if (before.markers.length !== after.markers.length) {
    findings.push(
      `Presentation markers changed: the source has ${before.markers.length} and the translation ${after.markers.length}; ` +
        "every `<!-- presentation:… -->` comment must remain byte for byte, in order",
    );
  } else {
    const at = before.markers.findIndex((marker, index) => marker !== after.markers[index]);
    if (at !== -1) {
      findings.push(
        `Presentation markers changed: marker ${at + 1} is \`${before.markers[at]}\` in the source and ` +
          `\`${after.markers[at]}\` in the translation; markers must remain byte for byte`,
      );
    }
  }
  if (findings.length || before.slides.length !== after.slides.length) return findings;
  before.slides.forEach((slide, index) => {
    const other = after.slides[index]!;
    if (JSON.stringify(fenceSignatures(slide.markdown)) !== JSON.stringify(fenceSignatures(other.markdown))) {
      findings.push(`Code fence structure changed in slide "${slide.id}": keep each fence's delimiters and language label`);
    }
    const wanted = expected(source, slide.markdown).map(named);
    const found = destinations(other.markdown).map(named);
    if (JSON.stringify(wanted) !== JSON.stringify(found)) {
      findings.push(
        `Image/link destinations changed in slide "${slide.id}": expected ${wanted.join(", ") || "none"}; found ${found.join(", ") || "none"}`,
      );
    }
  });
  return findings;
}

// ---------- is it translated at all ----------

// Terms that are the same in both languages, and so say nothing about whether a paragraph was translated.
const TECH_GLOSSARY = [
  "machine learning", "deep learning", "data science", "mlops", "training", "inference", "model", "dataset",
  "benchmark", "feature", "batch", "streaming", "transformer", "fine-tuning", "cuda", "gpu", "cpu", "kernel",
  "runtime", "hardware", "software", "thread", "overhead", "docker", "kubernetes", "cloud", "deploy", "pipeline",
  "backend", "frontend", "full-stack", "serverless", "microservice", "container", "orchestration", "stack",
  "cluster", "cache", "hash", "token", "endpoint", "ci/cd", "devops", "sre", "latency", "throughput", "api",
  "rest", "graphql", "framework", "dashboard", "payload", "metadata", "debug", "log", "commit", "merge", "branch",
  "pull request", "code review", "sprint", "agile", "scrum", "open source", "build", "tooling", "workflow",
  "nubank", "picpay", "aws", "sagemaker", "kubeflow", "dagster", "gemini", "pytorch", "tensorflow", "python",
  "javascript", "github", "gitlab",
].sort((a, b) => b.length - a.length || (a < b ? -1 : 1));

const INVARIANT_HEADINGS = [
  /^(?:#+\s*)?(?:\*\*)?\s*(?:fontes|sources)\s*:?(?:\*\*)?$/i,
  /^(?:#+\s*)?(?:\*\*)?\s*tl;dr\s*(?:\*\*)?$/i,
  /^(?:#+\s*)?(?:\*\*)?\s*view\s+transitions\s+api\s*:?(?:\*\*)?$/i,
];

const stripCodeAndTags = (text: string): string =>
  text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`[^`]+`/g, "")
    .replace(/<[^>]+>|!\[.*?\]\(.*?\)|\[.*?\]\(.*?\)/g, "");

const withoutGlossary = (text: string): string =>
  TECH_GLOSSARY.reduce((left, term) => left.replaceAll(term, " "), text);

const wordsOf = (text: string): Set<string> =>
  new Set((text.toLowerCase().match(/[a-záàâãéêíóôõúüç]+/g) ?? []).filter((word) => word.length > 1));

function isInvariantHeading(text: string): boolean {
  const candidate = text
    .trim()
    .toLowerCase()
    .replace(/^#+\s*/, "")
    .replace(/^\*\*\s*|\s*\*\*$/g, "")
    .replace(/\s+/g, " ");
  return candidate !== "" && INVARIANT_HEADINGS.some((pattern) => pattern.test(candidate));
}

const isReferenceEntry = (text: string): boolean => /^\s*(?:\[\d+\]|\d+\.|;\s*)/.test(text) && text.trim() !== "";

const sentencesOf = (text: string): string[] =>
  text
    .trim()
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);

/** Paragraphs and runs of sentences that came back in the source's language. */
export function untranslated(source: string, translated: string): string[] {
  const findings: string[] = [];
  const [before, after] = [stripCodeAndTags(source), stripCodeAndTags(translated)];
  const split = (text: string) => text.split("\n\n").map((part) => part.trim()).filter(Boolean);
  const [was, is] = [split(before), split(after)];
  for (let index = 0; index < Math.min(was.length, is.length); index++) {
    const [original, other] = [was[index]!, is[index]!];
    if (original === other && isInvariantHeading(original)) continue;
    if (isReferenceEntry(original) || isReferenceEntry(other)) continue;
    const words = wordsOf(withoutGlossary(original.toLowerCase()));
    if (!words.size) continue;
    const shared = wordsOf(withoutGlossary(other.toLowerCase()));
    const overlap = [...words].filter((word) => shared.has(word)).length / words.size;
    if (overlap > 0.7) {
      findings.push(
        `Paragraph ${index + 1} appears untranslated (${Math.round(overlap * 100)}% word overlap after removing glossary terms): "${clip(original, 80)}"`,
      );
    }
  }
  let run = 0;
  const [said, says] = [sentencesOf(before), sentencesOf(after)];
  for (let index = 0; index < Math.min(said.length, says.length); index++) {
    const [original, other] = [said[index]!, says[index]!];
    if (isReferenceEntry(original) || isReferenceEntry(other) || original !== other || isInvariantHeading(original)) {
      run = 0;
      continue;
    }
    if (++run > 3) {
      findings.push(`${run} consecutive identical sentences: a section appears untranslated near "${clip(original, 80)}"`);
      break;
    }
  }
  return findings;
}

const VOID_TAGS = new Set(["br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed", "source", "track", "wbr"]);

// How many of each HTML tag are left open, outside fenced code.
function openTags(text: string): Map<string, number> {
  const prose = stripFences(text);
  const balance = new Map<string, number>();
  for (const match of prose.matchAll(/<([a-zA-Z][a-zA-Z0-9]*)\b[^/>]*>/g)) {
    const tag = match[1]!.toLowerCase();
    if (!VOID_TAGS.has(tag)) balance.set(tag, (balance.get(tag) ?? 0) + 1);
  }
  for (const match of prose.matchAll(/<\/([a-zA-Z][a-zA-Z0-9]*)\s*>/g)) {
    const tag = match[1]!.toLowerCase();
    balance.set(tag, (balance.get(tag) ?? 0) - 1);
  }
  return balance;
}

// The translation leaves no HTML tag open that the source closes.
function unclosedTags(source: string, translated: string): string[] {
  const before = openTags(source);
  return [...openTags(translated)]
    .filter(([tag, open]) => open > Math.max(0, before.get(tag) ?? 0))
    .map(([tag, open]) => `${open - Math.max(0, before.get(tag) ?? 0)} unclosed <${tag}> tag(s) in the translation`);
}

/** Every check on a post, a presentation or a page. `answer` is whatever the model returned. */
export function checkProse(source: ProseSource, answer: unknown): Verdict {
  const shape = proseShape(answer);
  if (shape.length) return { findings: shape, warnings: [] };
  const { title, excerpt, content: raw } = answer as ProseAnswer;
  const body = lf(source.body).trim();
  const content = lf(raw).trim();
  if (!content) return { findings: ["Cannot accept an empty translation"], warnings: [] };

  const findings: string[] = [];
  const warnings: string[] = [];
  if (source.title.trim() && !title.trim()) findings.push("The translated title is empty");
  if (source.excerpt.trim() && !excerpt.trim()) findings.push("The translated excerpt is empty");
  findings.push(...footnotes(body, content));
  if (source.kind === "about" && paragraphs(body).length !== paragraphs(content).length) {
    findings.push(
      `About translation changed the paragraph count: the source has ${paragraphs(body).length} paragraphs and the translation ${paragraphs(content).length}`,
    );
  }
  if (source.kind === "presentation") {
    findings.push(...slides({ ...source, body }, content));
  } else {
    findings.push(...fences(body, content));
    findings.push(...sameDestinations({ ...source, body }, content));
    if (source.lang.slice(0, 2) !== source.target.slice(0, 2)) findings.push(...untranslated(body, content));
    findings.push(...unclosedTags(body, content));
  }
  findings.push(...pictures(body, content));
  findings.push(...asides(body, content));
  findings.push(...asides(source.title, title, " in the title"));
  findings.push(...asides(source.excerpt, excerpt, " in the excerpt"));
  if (content.length < body.length * 0.5) {
    warnings.push(
      `The translation is suspiciously short: ${content.length} characters against the source's ${body.length}`,
    );
  }
  return { findings, warnings };
}

// ---------- the CV ----------

// The translation has the source's shape exactly: the same keys, the same number of entries in
// every list, the same kind of value everywhere.
function sameShape(source: unknown, translated: unknown, at: string, findings: string[]): void {
  const here = at || "the CV";
  if (typeName(source) !== typeName(translated)) {
    findings.push(`CV translation changed ${here}: a ${typeName(source)} in the source, a ${typeName(translated)} in the translation`);
    return;
  }
  if (Array.isArray(source) && Array.isArray(translated)) {
    if (source.length !== translated.length) {
      findings.push(
        `CV translation changed the number of ${at || "top-level"} entries: ${source.length} in the source, ${translated.length} in the translation`,
      );
      return;
    }
    source.forEach((item, index) => sameShape(item, translated[index], `${at}[${index}]`, findings));
    return;
  }
  if (isRecord(source) && isRecord(translated)) {
    for (const key of Object.keys(source)) {
      const child = at ? `${at}.${key}` : key;
      if (!(key in translated)) findings.push(`CV translation is missing ${child}`);
      else sameShape(source[key], translated[key], child, findings);
    }
    for (const key of Object.keys(translated)) {
      if (!(key in source)) findings.push(`CV translation has ${at ? `${at}.${key}` : key}, which the source does not`);
    }
    return;
  }
  if (typeof source === "string" && source.trim() && !(translated as string).trim()) {
    findings.push(`CV translation left ${here} empty`);
  }
}

/** Every check on the CV: the source's shape and entry counts, and contact details untouched. */
export function checkCv(source: unknown, answer: unknown): Verdict {
  if (!isRecord(answer)) return { findings: [`The answer must be one JSON object, and is a ${typeName(answer)}`], warnings: [] };
  const findings: string[] = [];
  sameShape(source, answer, "", findings);
  const contact = isRecord(source) ? source.contact : undefined;
  if (JSON.stringify(sorted(contact)) !== JSON.stringify(sorted(answer.contact))) {
    findings.push("CV translation changed contact details: every value under `contact` must be the source's, byte for byte");
  }
  return { findings, warnings: [] };
}
