"""Render the old translation_v2 engine's stage prompts for a small post, cut into sections.

usage: (cd <old worktree at 2d9a250> && uv run python old_engine.py old-engine.json <old worktree at 8c6735a> old-engine.json)

The inputs, read from the fixture itself (a post, a candidate translation of it, and one canned
answer per stage), are rendered through every v2 stage template with the engine's own context
builders. Each rendered prompt is cut at the template's headings. A section that holds a guidance
file whole (the locale brief, the writing references) is kept as its sha256, with the "None" the
engine appended to the brief set apart (see _merge_text_blocks); a section that holds a guidance
list is kept as its items (the engine rendered each list as one Python repr, see
_merge_string_lists); every other section is kept verbatim. The headings of the same templates at
8c6735a are added as they are.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

inputs_file, old_dir, fixture_file = sys.argv[1:4]
sys.path.insert(0, str(Path.cwd() / "_source"))

from translation_v2 import contracts as c  # noqa: E402
from translation_v2.artifacts import TranslationRunArtifacts  # noqa: E402
from translation_v2.contracts import StageResult, TranslationRequest  # noqa: E402
from translation_v2.prompt_registry import load_prompt_template, render_prompt_template  # noqa: E402
from translation_v2.providers.opencode import OpenCodeTranslationProvider  # noqa: E402
from translation_v2.source_analysis import build_source_analysis_context  # noqa: E402
from translation_v2.style_loader import load_writing_style_brief  # noqa: E402
from translation_v2.terminology_policy import build_terminology_policy_context  # noqa: E402

inputs = json.loads(Path(inputs_file).read_text(encoding="utf-8"))
post, candidate, payloads = inputs["post"], inputs["candidate"], inputs["payloads"]

request = TranslationRequest(
    run_id="reference", source_locale="en-us", target_locale="pt-br", source_text=post["body"], prompt_version="v2",
    metadata={
        "slug": "tide", "locale_direction": "en-us->pt-br", "title": post["title"], "excerpt": post["excerpt"],
        "tags": post["tags"], "artifact_type": "post", "writing_style_brief": load_writing_style_brief(),
    },
)


class Recorder:
    model_id = "reference"

    def run_stage(self, **_):
        raise AssertionError("not used")


provider = OpenCodeTranslationProvider(runner=Recorder(), artifacts=TranslationRunArtifacts("r", tempfile.mkdtemp()), default_attach_path="x")
lists = provider._policy_lists(request)
common = {key: lists[key] for key in (
    "style_constraints", "localization_brief", "borrowing_conventions", "punctuation_conventions",
    "discourse_conventions", "register_conventions", "review_checks")}
analysis = c.validate_voice_intent_output(payloads["source_analysis"], run_id="r", stage="source_analysis")
policy = c.validate_terminology_policy_output(payloads["terminology_policy"], run_id="r", stage="terminology_policy")
draft = c.validate_translation_output(candidate, run_id="r", stage="translate")
critique = c.validate_critique_output(payloads["critique"], run_id="r", stage="critique")
dump = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)  # noqa: E731
shared = {
    **provider._translation_context(request, source_analysis=analysis, terminology_policy=policy),
    "translated_json": dump(asdict(draft)),
    "critique_json": dump(asdict(critique)),
}
contexts = {
    "source_analysis": build_source_analysis_context(
        request, writing_style_brief=request.metadata["writing_style_brief"],
        glossary_entries=lists["glossary"], do_not_translate_entities=lists["do_not_translate_entities"], **common),
    "terminology_policy": build_terminology_policy_context(
        request, source_analysis=analysis, glossary_entries=lists["glossary"],
        do_not_translate_entities=lists["do_not_translate_entities"], **common),
    **{stage: shared for stage in ("translate", "critique", "revise", "final_review")},
}

HEADING = re.compile(r"^[A-Z][A-Z0-9_ ()-]+$")
FILES = {"LOCALIZATION BRIEF", "WRITING STYLE BRIEF", "AUTHORING CONTEXT (PRESERVE THE AUTHORED SOURCE)"}
LISTS = {"STYLE CONSTRAINTS", "BORROWING CONVENTIONS", "PUNCTUATION CONVENTIONS", "DISCOURSE CONVENTIONS",
         "REGISTER CONVENTIONS", "LOCALE REVIEW CHECKS", "GLOSSARY", "DO_NOT_TRANSLATE_ENTITIES"}


def items(body: str) -> list[str]:
    found: list[str] = []
    for line in body.splitlines():
        for item in ast.literal_eval(line[2:]):
            found.append(f"{item['source']} => {item['target']}" if isinstance(item, dict) else str(item))
    return found


def cut(stage: str, text: str) -> list[dict]:
    headings = [line for line in load_prompt_template(stage).splitlines() if HEADING.match(line)]
    lines = text.split("\n")
    starts, at = [], 0
    for heading in headings:
        at = lines.index(heading, at)
        starts.append(at)
    sections = []
    for index, (heading, start) in enumerate(zip(headings, starts)):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        body = "\n".join(lines[start + 1:end]).strip("\n")
        if heading in FILES:
            # _merge_text_blocks turned the missing override into the text "None" after the brief.
            appended = "\n\nNone" if heading == "LOCALIZATION BRIEF" and body.endswith("\n\nNone") else ""
            body = body.removesuffix(appended)
            sections.append({"heading": heading, "sha256": hashlib.sha256(body.encode()).hexdigest(),
                             **({"old_engine_appended": appended} if appended else {})})
        elif heading in LISTS:
            sections.append({"heading": heading, "items": items(body)})
        else:
            sections.append({"heading": heading, "text": body})
    return sections


stages = {stage: cut(stage, render_prompt_template(stage, context=context, prompt_version="v2", artifact_type="post"))
          for stage, context in contexts.items()}
old = {}
for stage in contexts:
    template = (Path(old_dir) / "_source/translation_v2/prompts/v2" / f"{stage}.md").read_text(encoding="utf-8")
    old[stage] = [line for line in template.splitlines() if HEADING.match(line)]
fixture = {
    "about": "The old engine's v2 stage prompts for this post: rendered at 2d9a250 (the wording in use), and the headings of the same templates at 8c6735a. Made by old_engine.py, beside this file.",
    "post": post,
    "candidate": candidate,
    "payloads": payloads,
    "rendered_2d9a250": stages,
    "headings_8c6735a": old,
}
Path(fixture_file).write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print({stage: len(sections) for stage, sections in stages.items()})
