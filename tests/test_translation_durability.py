"""Failure and recovery tests at the real persistence/provider boundaries."""

import json
import shutil
import sys

import pytest

from translation_v2.accepted import (
    AcceptedTranslations,
    digest,
    source_identity,
    matching_legacy_entry,
)
from accepted_content import AcceptedContent
from pathlib import Path
from translation_v2.orchestrator import TranslationV2PostOrchestrator
from translation_v2.artifacts import TranslationRunArtifacts
from translation_v2.durable import validate_artifact
from translation_v2.opencode_runner import OpenCodeHeadlessRunner
from translation_v2.providers.opencode import OpenCodeTranslationProvider
from translation_v2.errors import MissingFieldError
from tests.test_opencode_provider_loop import (
    _FakeRunner,
    _request,
    _source_analysis_result,
    _terminology_policy_result,
    _translation_result,
    _critique_result,
    _revision_result,
    _final_review_result,
)


def source(text="The system keeps its promises."):
    return source_identity(
        slug="example",
        source_text=text,
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="post",
        frontmatter={"title": "Example", "excerpt": "A summary", "tags": []},
    )


TRANSLATION = {
    "title": "Exemplo",
    "excerpt": "Um resumo",
    "tags": [],
    "content": "O sistema cumpre suas promessas.",
}


def test_accepted_revision_survives_recipe_change_and_corrupt_execution_cache(
    tmp_path, monkeypatch
):
    store = AcceptedTranslations(tmp_path / "accepted")
    store.accept(source(), TRANSLATION, {"translation_model": "old/model"}, expected_revision=None)
    cache = tmp_path / "cache.json"
    cache.write_text("broken cache")
    monkeypatch.setenv("TRANSLATION_V2_TRANSLATION_MODEL", "new/model")
    runtime = TranslationV2PostOrchestrator(
        strict_validation=True,
        cache_dir=tmp_path,
        accepted_path=store.root,
    )
    runtime.writing_style_fingerprint = "changed style"
    monkeypatch.setattr(runtime, "_run_pipeline", lambda *a, **k: pytest.fail("Model called"))
    original = source()
    result = runtime.translate_artifact_if_needed(
        slug=original["slug"],
        source_text=original["text"],
        frontmatter=original["frontmatter"],
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="post",
    )
    assert result == TRANSLATION
    assert cache.read_text() == "broken cache"


@pytest.mark.parametrize("change", ["text", "frontmatter"])
def test_source_changes_require_update_without_replacing_accepted_content(tmp_path, change):
    store = AcceptedTranslations(tmp_path / "accepted")
    initial = store.accept(source(), TRANSLATION, {}, expected_revision=None)
    reader = AcceptedContent(root=store.root)
    changed = source()
    changed[change] = "Different source" if change == "text" else {"title": "Different"}
    with pytest.raises(RuntimeError, match="outdated"):
        reader.read_artifact(
            slug="example",
            source_text=changed["text"],
            frontmatter=changed["frontmatter"],
            source_locale="en-us",
            target_locale="pt-br",
            artifact_type="post",
        )
    assert digest(store.current(source())) == initial


def test_accepted_history_and_concurrent_revision_conflict(tmp_path):
    store = AcceptedTranslations(tmp_path)
    first = store.accept(source(), TRANSLATION, {}, expected_revision=None)
    second = store.accept(
        source(), {**TRANSLATION, "title": "Revisado"}, {}, expected_revision=first
    )
    with pytest.raises(RuntimeError, match="changed during"):
        store.accept(source(), TRANSLATION, {}, expected_revision=first)
    assert digest(store.current(source())) == second
    assert len(list(tmp_path.rglob("revisions/*.json"))) == 2


def test_accepted_record_corruption_is_not_a_cache_miss(tmp_path):
    store = AcceptedTranslations(tmp_path)
    store.accept(source(), TRANSLATION, {}, expected_revision=None)
    path = next(tmp_path.rglob("revisions/*.json"))
    record = json.loads(path.read_text())
    record["translation"]["content"] = "Changed on disk"
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="damaged"):
        store.current(source())


def test_legacy_import_verifies_source_with_original_recipe():
    cache = json.loads(Path("tests/fixtures/translation_v2/legacy-cache.json").read_text())
    assert matching_legacy_entry(cache, source()) is not None
    assert matching_legacy_entry(cache, source("Changed")) is None
    changed = source()
    changed["frontmatter"]["title"] = "Changed title"
    assert matching_legacy_entry(cache, changed) is None


def test_import_command_preserves_legacy_cache_and_existing_acceptance(tmp_path, monkeypatch):
    import translations

    cache = tmp_path / "legacy.json"
    fixture = Path("tests/fixtures/translation_v2/legacy-cache.json").read_bytes()
    cache.write_bytes(fixture)
    monkeypatch.setattr(translations, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(translations, "TRANSLATION_CACHE", cache)
    monkeypatch.setattr(translations, "discover_artifacts", lambda: [{"source": source(), "attach_path": "example.md"}])
    assert translations.main(["import-cache", "example"]) == 0
    store = AcceptedTranslations(tmp_path / "_source/translations")
    accepted = store.current(source())
    assert accepted["translation"] == TRANSLATION
    assert accepted["provenance"]["imported_from"] == "translation-cache-v2"
    assert translations.main(["import-cache", "example"]) == 0
    assert store.current(source()) == accepted
    assert cache.read_bytes() == fixture

    cache.write_text("broken cache")
    assert translations.main(["import-cache", "example"]) == 1
    assert store.current(source()) == accepted
    assert cache.read_text() == "broken cache"


def test_update_command_resumes_failure_and_reuses_acceptance_after_cache_loss(tmp_path, monkeypatch):
    import translations

    cache = tmp_path / "_cache"
    monkeypatch.setattr(translations, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(translations, "TRANSLATION_CACHE", cache / "translation-cache.json")
    monkeypatch.setattr(translations, "discover_artifacts", lambda: [{"source": source(), "attach_path": "example.md"}])
    first = _FakeRunner([
        _source_analysis_result(), _terminology_policy_result(),
        _translation_result("O sistema cumpre suas promessas."), _critique_result(0.95),
        RuntimeError("review provider unavailable"),
    ])
    monkeypatch.setattr(OpenCodeHeadlessRunner, "run_stage", lambda self, **kwargs: first.run_stage(**kwargs))
    store = AcceptedTranslations(tmp_path / "_source/translations")
    assert translations.main(["update", "example"]) == 1
    assert store.current(source()) is None

    resumed = _FakeRunner([_final_review_result(accept=True, publish_ready=True)])
    monkeypatch.setattr(OpenCodeHeadlessRunner, "run_stage", lambda self, **kwargs: resumed.run_stage(**kwargs))
    assert translations.main(["update", "example"]) == 0
    assert [call["stage"] for call in resumed.calls] == ["final_review"]
    accepted = store.current(source())
    assert accepted["translation"]["content"] == "O sistema cumpre suas promessas."
    assert accepted["provenance"]["editorial_review"]["accept"] is True

    shutil.rmtree(cache)
    monkeypatch.setenv("TRANSLATION_V2_TRANSLATION_MODEL", "different/model")
    monkeypatch.setattr(OpenCodeHeadlessRunner, "run_stage", lambda *a, **k: pytest.fail("Accepted text was regenerated"))
    assert translations.main(["update", "example"]) == 0
    assert store.current(source()) == accepted


def make_provider(tmp_path, runner, run):
    return OpenCodeTranslationProvider(
        runner=runner,
        default_attach_path="source.md",
        artifacts=TranslationRunArtifacts(run, tmp_path / "runs"),
        checkpoint_dir=tmp_path / "checkpoints",
    )


def test_late_failure_resumes_completed_stages_with_new_run_id(tmp_path):
    first = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _translation_result("Traduzido"),
            RuntimeError("provider unavailable"),
        ]
    )
    with pytest.raises(RuntimeError, match="unavailable"):
        make_provider(tmp_path, first, "first").run_translation_pipeline(_request())
    second = _FakeRunner(
        [_critique_result(0.95), _final_review_result(accept=True, publish_ready=True)]
    )
    request = _request()
    request.run_id = "second-run"
    result = make_provider(tmp_path, second, "second").run_translation_pipeline(request)
    assert result.final_translation.content == "Traduzido"
    assert [c["stage"] for c in second.calls] == ["critique", "final_review"]
    events = [
        json.loads(line)
        for line in (tmp_path / "runs/second/stage-events.jsonl").read_text().splitlines()
    ]
    assert [e["outcome"] for e in events[:3]] == ["resumed"] * 3


def test_owner_revision_notes_reach_every_stage(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _critique_result(0.8, needs_refinement=True),
            _revision_result("Revisado"),
            _final_review_result(accept=True, publish_ready=True),
        ]
    )
    request = _request()
    request.metadata["revision_request"] = {"notes": "OWNER_CORRECTION_SENTINEL"}
    make_provider(tmp_path, runner, "notes").run_translation_pipeline(
        request,
        existing_translation=_translation_result("Anterior").payload,
    )
    assert len(runner.calls) == 5
    assert all("OWNER_CORRECTION_SENTINEL" in c["prompt_text"] for c in runner.calls)


def test_final_review_feedback_reaches_next_critique(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _translation_result("Traduzido"),
            _critique_result(0.95),
            _final_review_result(
                accept=False, publish_ready=False, residual_issues=["FIX_THE_FINAL_SENTENCE"]
            ),
            _critique_result(0.8, needs_refinement=True),
            _revision_result("Revisado"),
            _final_review_result(accept=True, publish_ready=True),
        ]
    )
    make_provider(tmp_path, runner, "review").run_translation_pipeline(_request())
    assert "FIX_THE_FINAL_SENTENCE" in runner.calls[5]["prompt_text"]


def test_schema_repair_preserves_completed_work_and_resumes_success(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _translation_result("Traduzido"),
            MissingFieldError("missing quality_score", run_id="test", stage="critique"),
            _critique_result(0.95),
            _final_review_result(accept=True, publish_ready=True),
        ]
    )
    result = make_provider(tmp_path, runner, "repair").run_translation_pipeline(_request())
    assert result.final_translation.content == "Traduzido"
    assert [call["stage"] for call in runner.calls].count("translate") == 1
    assert "missing quality_score" in runner.calls[4]["prompt_text"]
    # A successfully repaired typed result is reusable on the original request.
    resumed = _FakeRunner([])
    make_provider(tmp_path, resumed, "resume-repair").run_translation_pipeline(_request())
    assert resumed.calls == []


@pytest.mark.parametrize("repair_succeeds", [True, False])
def test_deterministic_repair_is_bounded_and_never_accepts_broken_links(
    tmp_path, monkeypatch, repair_succeeds
):
    original = source("Read [the docs](https://example.com/v1).")
    broken = {**TRANSLATION, "content": "Leia [a documentação](https://example.com/v2)."}
    repaired = {**TRANSLATION, "content": "Leia [a documentação](https://example.com/v1)."}
    store = AcceptedTranslations(tmp_path / "accepted")
    runtime = TranslationV2PostOrchestrator(
        strict_validation=False,
        cache_dir=tmp_path,
        accepted_path=store.root,
    )
    calls = []

    def pipeline(request, *, existing_translation=None):
        if existing_translation is None:
            return broken
        assert existing_translation == broken
        calls.append(request.metadata["deterministic_findings"])
        return repaired if repair_succeeds else broken

    monkeypatch.setattr(runtime, "_run_pipeline", pipeline)

    def run():
        return runtime.translate_artifact_if_needed(
            slug=original["slug"],
            source_text=original["text"],
            source_locale="en-us",
            target_locale="pt-br",
            artifact_type="post",
            frontmatter=original["frontmatter"],
        )

    if repair_succeeds:
        assert run() == repaired
        assert store.current(original)["translation"] == repaired
    else:
        with pytest.raises(RuntimeError, match="protected link"):
            run()
        assert store.current(original) is None
    assert len(calls) == 1
    assert "protected link" in calls[0]


def test_candidate_branch_can_be_revised_repeatedly_then_promoted(tmp_path):
    main = AcceptedTranslations(tmp_path / "main")
    base = main.accept(source(), TRANSLATION, {}, expected_revision=None)
    shutil.copytree(main.root, tmp_path / "candidate")
    candidate = AcceptedTranslations(tmp_path / "candidate")
    first = candidate.accept(
        source(), {**TRANSLATION, "title": "First"}, {}, expected_revision=base
    )
    last = candidate.accept(
        source(), {**TRANSLATION, "title": "Final"}, {}, expected_revision=first
    )
    assert main.promote(candidate, source()) == last
    assert len(list(main.root.rglob("revisions/*.json"))) == 3


def test_candidate_cannot_replace_a_concurrent_accepted_revision(tmp_path):
    main = AcceptedTranslations(tmp_path / "main")
    base = main.accept(source(), TRANSLATION, {}, expected_revision=None)
    shutil.copytree(main.root, tmp_path / "candidate")
    candidate = AcceptedTranslations(tmp_path / "candidate")
    candidate.accept(source(), {**TRANSLATION, "title": "Candidate"}, {}, expected_revision=base)
    changed = main.accept(
        source(), {**TRANSLATION, "title": "Owner edit"}, {}, expected_revision=base
    )
    with pytest.raises(RuntimeError, match="changed since"):
        main.promote(candidate, source())
    assert digest(main.current(source())) == changed


@pytest.mark.parametrize(
    "original, translated",
    [
        ('```python\nprint("hello")\n```', '```python\nprint("olá")\n```'),
        ("[Docs](https://example.com/v1)", "[Documentação](https://example.com/v2)"),
    ],
)
def test_protected_code_and_links_are_gates_even_without_strict_heuristics(original, translated):
    with pytest.raises(RuntimeError, match="protected"):
        validate_artifact(source(original), {**TRANSLATION, "content": translated}, strict=False)


MERMAID = """```mermaid
%%{init: {"flowchart": {"nodeSpacing": 24}}}%%
flowchart TB
    accTitle: Request flow
    accDescr: The app invokes the agent.
    A["App<br/>Call"] -->|invoke| B["Agent"]
    click A "https://example.com/docs"
```
"""


def test_mermaid_visible_text_can_be_localized_without_changing_the_graph():
    translated = (
        MERMAID.replace("Request flow", "Fluxo da solicitação")
        .replace("The app invokes the agent.", "O aplicativo invoca o agente.")
        .replace("App<br/>Call", "Aplicativo<br/>Chamada")
        .replace("|invoke|", "|invocar|")
        .replace('["Agent"]', '["Agente"]')
    )
    validate_artifact(source(MERMAID), {**TRANSLATION, "content": translated}, strict=False)
    validate_artifact(
        source("```mermaid\nflowchart TB\nA[App] --> B[Agent]\n```"),
        {**TRANSLATION, "content": "```mermaid\nflowchart TB\nA[Aplicativo] --> B[Agente]\n```"},
        strict=False,
    )


@pytest.mark.parametrize(
    "before, after",
    [
        ("24", "25"),
        ("-->||", "---||"),
        (' B["Agent"]', ' C["Agent"]'),
        ("https://example.com/docs", "https://example.com/other"),
        ("<br/>", '<a href="https://other.example">'),
    ],
)
def test_mermaid_structure_configuration_and_links_remain_protected(before, after):
    original = MERMAID.replace("-->|invoke|", "-->||")
    with pytest.raises(RuntimeError, match="protected fenced code"):
        validate_artifact(
            source(original),
            {**TRANSLATION, "content": original.replace(before, after)},
            strict=False,
        )


def test_runner_timeout_terminates_the_process(monkeypatch):
    monkeypatch.setenv("TRANSLATION_STAGE_TIMEOUT_SECONDS", "0.05")
    result = OpenCodeHeadlessRunner._default_executor(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        "",
    )
    assert result.exit_code == 124
    assert "timeout" in result.stderr


def test_runner_has_no_repository_tools_or_working_directory(monkeypatch):
    observed = {}

    def execute(command, prompt, **kwargs):
        observed.update(kwargs)
        return None

    monkeypatch.setattr(OpenCodeHeadlessRunner, "_execute_process", execute)
    OpenCodeHeadlessRunner._default_executor(["opencode"], "prompt")
    config = json.loads(observed["env"]["OPENCODE_CONFIG_CONTENT"])
    assert config["agent"]["blog-translator"]["tools"] == {"*": False}
    assert config["agent"]["blog-translator"]["permission"] == {"*": "deny"}
    assert "blog-translation-stage-" in observed["cwd"]
