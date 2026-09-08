"""Exercise the real update command, durable runtime, and Rich progress lifecycle."""

from io import StringIO
from dataclasses import replace

import pytest
from rich.console import Console

import translations
from translation_v2 import console
from translation_v2.accepted import AcceptedTranslations
from translation_v2.opencode_runner import OpenCodeHeadlessRunner
from tests.test_translation_durability import source, TRANSLATION
from tests.test_opencode_provider_loop import (
    _FakeRunner, _translation_result,
)


@pytest.fixture
def update_context(tmp_path, monkeypatch):
    output = StringIO()
    monkeypatch.setattr(console, "_console", Console(file=output, width=58, force_terminal=False))
    monkeypatch.setattr(translations, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(translations, "TRANSLATION_CACHE", tmp_path / "_cache/cache.json")
    current = source()
    current["slug"] = "current"
    pending = source()
    pending["frontmatter"]["title"] = "Maré Rio: The Software I Want to Exist [red]"
    artifacts = [{"source": item, "attach_path": "/not-for-display/source.md"} for item in (current, pending)]
    monkeypatch.setattr(translations, "discover_artifacts", lambda: artifacts)
    store = AcceptedTranslations(tmp_path / "_source/translations")
    store.accept(current, TRANSLATION, {}, expected_revision=None)
    yield output, store, pending
    console.shutdown_console()


def scripted_update(monkeypatch, *, failure=None):
    runner = _FakeRunner([
        failure if failure is not None else _translation_result(TRANSLATION["content"]),
    ])
    frames = []

    def run(self, **kwargs):
        assert console._progress is not None, "The CLI did not connect the artifact view"
        view = Console(file=StringIO(), width=58, record=True)
        view.print(console._progress.render())
        frames.append(view.export_text())
        # The real subprocess runner reports these events in production.
        console.start_runner_status(stage=kwargs["stage"], attempt=1, max_attempts=3,
                                    model="test/model", attach_path=kwargs["attach_path"])
        result = runner.run_stage(**kwargs)
        if isinstance(result, BaseException):
            raise result
        return replace(result, run_id=kwargs["request"].run_id)

    monkeypatch.setattr(OpenCodeHeadlessRunner, "run_stage", run)
    return frames


def test_update_renders_real_work_and_does_not_mislabel_reuse(update_context, monkeypatch):
    output, store, pending = update_context
    frames = scripted_update(monkeypatch)
    assert translations.main(["update"]) == 0
    text = output.getvalue()
    assert "Translating blog" in text
    assert "1 current" in text and "1 updated" in text
    assert "Translations ready" in text and "Next: dan blog build" in text
    assert "accepted  post:" not in text
    assert "source_analysis" not in text and "runner" not in text and "attach=" not in text
    assert "test/model" not in text
    assert "Writing the localization" in frames[0] and "0:00" in frames[0]
    assert "Maré Rio: The Software I Want to Exist [red]" in frames[0]
    assert "EN-US → PT-BR" in frames[0]
    assert store.current(pending) is not None
    assert console._progress is None


def test_all_current_never_calls_a_model_or_claims_updates(update_context, monkeypatch):
    output, store, pending = update_context
    store.accept(pending, TRANSLATION, {}, expected_revision=None)
    monkeypatch.setattr(OpenCodeHeadlessRunner, "run_stage", lambda *a, **kw: pytest.fail("Model called"))
    assert translations.main(["update"]) == 0
    text = output.getvalue()
    assert "2 current" in text and "0 updated" in text
    assert "already current" in text
    assert "Writing the localization" not in text


def test_verbose_is_discoverable_and_opt_in(update_context, monkeypatch):
    output, _, _ = update_context
    scripted_update(monkeypatch)
    assert translations.main(["update", "--verbose"]) == 0
    assert "Model request" in output.getvalue()
    assert "test/model" in output.getvalue()
    assert "/not-for-display/source.md" in output.getvalue()


@pytest.mark.parametrize("failure,code,label", [
    (RuntimeError("Provider unavailable"), 1, "Translation failed"),
    (KeyboardInterrupt(), 130, "Translation interrupted"),
])
def test_failure_retains_title_and_accurate_totals(update_context, monkeypatch, failure, code, label):
    output, store, pending = update_context
    scripted_update(monkeypatch, failure=failure)
    assert translations.main(["update"]) == code
    text = output.getvalue()
    assert label in text
    assert "1 current" in text and "0 updated" in text
    assert "Maré Rio:" in text and "Accepted work is preserved" in text
    assert "Translations ready" not in text
    assert store.current(pending) is None
    assert console._progress is None


def test_candidate_footer_gives_review_command(update_context, monkeypatch, tmp_path):
    output, store, pending = update_context
    scripted_update(monkeypatch)
    assert translations.main(["update", "--candidate-dir", str(tmp_path / "candidate with spaces")]) == 0
    assert "Candidates ready" in output.getvalue()
    assert "dan blog diff --candidate-dir" in output.getvalue()
    assert store.current(pending) is None
