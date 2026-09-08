"""Build real accepted files; exercise publication without a model or cache mock."""

import json
import os
import shutil
import subprocess
import sys

import pytest

import build
from accepted_content import AcceptedContent
from content_loader import parse_markdown_post
from translation_v2.accepted import AcceptedTranslations, source_identity


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_importing_content_commands_needs_no_generator_or_filesystem_initialization(tmp_path):
    source = tmp_path / "_source"
    shutil.copytree(
        build.PROJECT_ROOT / "_source", source,
        ignore=shutil.ignore_patterns("posts", "translations", "tools", "presentations", "__pycache__"),
    )
    before = snapshot(tmp_path)
    result = subprocess.run(
        [sys.executable, "-B", "-c", """
import sys
for module in ('orchestrator', 'opencode_runner', 'providers.opencode',
               'mock_provider', 'eval_harness', 'prompt_registry'):
    sys.modules['translation_v2.' + module] = None
import build
import translations
"""],
        cwd=tmp_path, env={**os.environ, "PYTHONPATH": str(source)},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert snapshot(tmp_path) == before
    assert set(tmp_path.iterdir()) == {source}


@pytest.fixture
def site(tmp_path, monkeypatch):
    monkeypatch.setattr("translation_v2.opencode_runner.OpenCodeHeadlessRunner.run_stage",
                        lambda *a, **k: pytest.fail("Unmocked localization agent in build test"))
    repository = build.PROJECT_ROOT
    posts = tmp_path / "_source/posts"
    posts.mkdir(parents=True)
    (tmp_path / "static").symlink_to(repository / "static", target_is_directory=True)
    for language in ("en", "pt"):
        (tmp_path / language).mkdir()
        for page in ("about", "cv"):
            (tmp_path / language / f"{page}.html").write_text("<!doctype html><p>Previous page</p>")
    monkeypatch.setattr(build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build, "POSTS_DIR", posts)
    monkeypatch.setattr("post_links.POSTS_DIR", posts)
    monkeypatch.setattr(build, "LANG_DIRS", {lang: tmp_path / lang for lang in ("en", "pt")})
    monkeypatch.setattr(build, "STAGING_DIR", tmp_path / "_staging")
    monkeypatch.setattr(build, "_out", lambda path, stage: stage / path.relative_to(tmp_path))
    return tmp_path


def add_post(root, slug="example", locale="en-us", *, source=None, localized=None):
    source = source or "## Responsibility\n\nThe author owns the final wording."
    localized = localized or "## Responsabilidade\n\nO autor decide a redação final."
    if locale == "pt-br":
        source, localized = localized, source
    path = root / "_source/posts" / f"{slug}.md"
    path.write_text(f"---\ntitle: Example\nslug: {slug}\nlang: {locale}\ndate: 2026-09-05\n---\n\n{source}")
    post = parse_markdown_post(path)
    identity = source_identity(
        slug=post["slug"], source_text=post["raw_content"], source_locale=locale,
        target_locale=build.get_target_locale(locale), artifact_type="post",
        frontmatter={k: post[k] for k in ("title", "excerpt", "tags")},
    )
    translation = {"title": "Exemplo", "excerpt": "", "tags": [], "content": localized}
    store = AcceptedTranslations(root / "_source/translations")
    store.accept(identity, translation, {"translation_model": "previous/model"}, expected_revision=None)
    return path, identity, translation


@pytest.mark.parametrize("locale", ["en-us", "pt-br"])
def test_real_build_preserves_source_and_acceptance_without_generation(site, monkeypatch, locale):
    path, identity, translation = add_post(site, locale=locale)
    authored = snapshot(site / "_source")
    monkeypatch.setenv("TRANSLATION_V2_TRANSLATION_MODEL", "unavailable/model")
    monkeypatch.setenv("TRANSLATION_V2_PROMPT_VERSION", "missing-prompt")
    monkeypatch.setattr("translation_v2.orchestrator.load_writing_style_brief", lambda: pytest.fail("Policy loaded"))
    monkeypatch.setattr("translation_v2.opencode_runner.OpenCodeHeadlessRunner.__init__", lambda *a, **k: pytest.fail("Runner initialized"))
    (site / "_cache").mkdir()
    cache = site / "_cache/translation-cache.json"
    cache.write_text("damaged disposable cache")

    assert build.build(strict=True, skip_about_cv_translation=True)
    output = site / build.locale_to_lang_key(identity["target_locale"]) / "blog/example.html"
    assert translation["title"] in output.read_text()
    assert snapshot(site / "_source") == authored
    assert cache.read_text() == "damaged disposable cache"
    assert not (site / "_cache/translation-runs").exists()
    assert not (site / "_cache/translation-stages").exists()


@pytest.mark.parametrize("failure", ["outdated", "missing", "broken_link"])
def test_failed_build_preserves_the_entire_previous_site(site, monkeypatch, failure):
    path, _, _ = add_post(site)
    assert build.build(strict=True, skip_about_cv_translation=True)
    before = {lang: snapshot(site / lang) for lang in ("en", "pt")}
    if failure == "outdated":
        path.write_text(path.read_text() + "\n\nThe source has changed.")
    elif failure == "missing":
        (site / "_source/posts/new.md").write_text("---\ntitle: New\n---\n\nA new post.")
    else:
        # Source and acceptance are still current; complete-site validation must fail.
        (site / "en/about.html").write_text('<!doctype html><a href="/missing.html">Missing</a>')
        before["en"] = snapshot(site / "en")
    def unavailable(*args, **kwargs):
        raise RuntimeError("Localization provider unavailable")
    monkeypatch.setattr("translation_v2.opencode_runner.OpenCodeHeadlessRunner.run_stage", unavailable)
    assert not build.build(strict=True, skip_about_cv_translation=True)
    assert {lang: snapshot(site / lang) for lang in ("en", "pt")} == before


def test_full_build_renders_each_page_and_collection_once(site, monkeypatch):
    add_post(site, "first")
    add_post(site, "second", "pt-br")
    counts = {name: 0 for name in ("generate_post_html", "generate_index_html", "generate_sitemap")}
    for name in counts:
        original = getattr(build, name)

        def counted(*args, _name=name, _original=original, **kwargs):
            counts[_name] += 1
            return _original(*args, **kwargs)

        monkeypatch.setattr(build, name, counted)
    assert build.build(strict=True, skip_about_cv_translation=True)
    assert counts == {"generate_post_html": 4, "generate_index_html": 2, "generate_sitemap": 1}


def test_build_reports_all_pending_translations_before_writing_pages(site, monkeypatch, capsys):
    for slug in ("first", "second"):
        path, _, _ = add_post(site, slug)
        path.write_text(path.read_text() + "\n\nNew source wording.")
    monkeypatch.setattr(build, "generate_post_html", lambda *a, **k: pytest.fail("Rendered before freshness check"))
    def unavailable(*args, **kwargs):
        raise RuntimeError("Localization provider unavailable")
    monkeypatch.setattr("translation_v2.opencode_runner.OpenCodeHeadlessRunner.run_stage", unavailable)
    assert not build.build(strict=True, skip_about_cv_translation=True)
    output = capsys.readouterr().out
    assert "first: Localization provider unavailable" in output
    assert "second: Localization provider unavailable" in output
    assert not (site / "_staging").exists()


def test_about_and_cv_use_accepted_structured_content(site):
    add_post(site)
    about = dict(build.LANGUAGES["en"]["about"])
    cv = build.load_cv_data()
    assert cv is not None
    store = AcceptedTranslations(site / "_source/translations")
    about_translation = {
        "title": "SOBRE", "excerpt": "", "tags": [],
        "content": "\n\n".join(f"Parágrafo traduzido {i}." for i, _ in enumerate(build._about_paragraph_keys(about))),
    }
    for slug, text, frontmatter, translation in (
        ("about", build._serialize_about_artifact(about), {"title": about["title"], "excerpt": "", "tags": []}, about_translation),
        ("cv", json.dumps(cv, ensure_ascii=False, sort_keys=True, indent=2), {"title": cv["name"], "excerpt": cv["tagline"], "tags": ["cv"]}, cv),
    ):
        identity = source_identity(slug=slug, artifact_type=slug, source_text=text,
            source_locale="en-us", target_locale="pt-br", frontmatter=frontmatter)
        store.accept(identity, translation, {}, expected_revision=None)
    assert build.build()
    assert "Parágrafo traduzido" in (site / "pt/about.html").read_text()
    assert cv["name"] in (site / "pt/cv.html").read_text()


def test_rendered_translation_preserves_accepted_frontmatter_verbatim(site):
    path, identity, translation = add_post(site)
    translation["title"] = "An API & its constraints"
    store = AcceptedTranslations(site / "_source/translations")
    current = store.current(identity)
    from translation_v2.accepted import digest
    store.accept(identity, translation, {}, expected_revision=digest(current))
    rendered = AcceptedContent(root=store.root).read_post(parse_markdown_post(path), target_locale="pt-br")
    assert rendered["title"] == translation["title"]


def test_source_links_build_in_both_languages_without_changing_acceptance(site):
    target, _, _ = add_post(site, "target-slug", "pt-br")
    target.rename(target.with_name("target-filename.md"))
    link = "_source/posts/target-filename.md#responsabilidade"
    add_post(site, "linked", source=f"Read [this article]({link}).",
             localized=f"Leia [este artigo]({link}).")
    authored = snapshot(site / "_source")
    assert build.build(strict=True, skip_about_cv_translation=True)
    for lang in ("en", "pt"):
        result = (site / lang / "blog/linked.html").read_text()
        assert f'href="/{lang}/blog/target-slug.html#responsabilidade"' in result
        assert link not in result
    assert snapshot(site / "_source") == authored
    assert build.build(strict=True, skip_about_cv_translation=True, post_selector="linked")
    assert snapshot(site / "_source") == authored


@pytest.mark.parametrize("link", ["missing.md", "example.md#missing-heading"])
def test_bad_source_link_never_replaces_previous_publication(site, link, capsys):
    add_post(site)
    assert build.build(strict=True, skip_about_cv_translation=True)
    before = snapshot(site / "en"), snapshot(site / "pt"), (site / "sitemap.xml").read_bytes()
    add_post(site, "linked", source=f"Read [this article]({link}).",
             localized=f"Leia [este artigo]({link}).")
    assert not build.build(strict=True, skip_about_cv_translation=True)
    assert (snapshot(site / "en"), snapshot(site / "pt"), (site / "sitemap.xml").read_bytes()) == before
    output = capsys.readouterr().out
    assert "missing.md" in output if link == "missing.md" else "missing-heading" in output


def test_translated_markup_filter_preserves_code_and_prose():
    import html5lib
    from markdown_refs import render_markdown_with_internal_refs
    from translation_common import sanitize_translation_html

    text = '''The example uses `onclick="run()"`.

```html
<button onclick="run()">Run</button>
```

<p>Before<script>run()</script> after <a onclick="run()" href="javascript:run()">link</a>.</p>
'''
    rendered = render_markdown_with_internal_refs(text)
    clean = html5lib.parseFragment(sanitize_translation_html(rendered), namespaceHTMLElements=False)
    original = html5lib.parseFragment(rendered, namespaceHTMLElements=False)
    assert [e.text for e in clean.iter("code")] == [e.text for e in original.iter("code")]
    assert not list(clean.iter("script"))
    assert "Before after " in "".join(clean.itertext())
    assert not any(name.startswith("on") or value.startswith("javascript:")
        for element in clean.iter() for name, value in element.attrib.items())


@pytest.mark.parametrize("locale", ["en-us", "pt-br"])
def test_strict_build_localizes_only_uncached_source_then_reuses_it(site, monkeypatch, locale):
    from dataclasses import replace
    from tests.test_opencode_provider_loop import _translation_result

    path, identity, translation = add_post(site, locale=locale)
    shutil.rmtree(site / "_source/translations")
    original = path.read_bytes()
    prompts = []

    def localize(self, **kwargs):
        prompts.append(kwargs["prompt_text"])
        assert kwargs["stage"] == "translate"
        return replace(_translation_result(translation["content"]), run_id=kwargs["request"].run_id)

    monkeypatch.setattr("translation_v2.opencode_runner.OpenCodeHeadlessRunner.run_stage", localize)
    assert build.build(strict=True, skip_about_cv_translation=True)
    assert len(prompts) == 1
    assert "UNATTENDED LOCALIZATION AGENT" in prompts[0]
    assert "Do not ask questions" in prompts[0]
    assert "LOCALIZATION BRIEF" in prompts[0] and "WRITING STYLE BRIEF" in prompts[0]
    assert "Keep parenthetical asides in parentheses" in prompts[0]
    store = AcceptedTranslations(site / "_source/translations")
    accepted = store.current(identity)
    assert accepted is not None
    assert set(accepted["provenance"]["stage_models"]) == {"translate"}
    assert "editorial_review" not in accepted["provenance"]
    assert build.build(strict=True, skip_about_cv_translation=True)
    assert len(prompts) == 1
    assert store.current(identity) == accepted and path.read_bytes() == original


@pytest.mark.parametrize("locale", ["en-us", "pt-br"])
def test_non_strict_build_without_translation_has_no_broken_language_links(site, locale):
    from html_validator import validate_generated_html
    from link_checker import check_internal_links

    path, identity, _ = add_post(site, locale=locale)
    shutil.rmtree(site / "_source/translations")
    assert build.build(strict=False, skip_about_cv_translation=True)
    source_lang = build.locale_to_lang_key(locale)
    target_lang = build.locale_to_lang_key(identity["target_locale"])
    assert (site / source_lang / "blog/example.html").exists()
    assert not (site / target_lang / "blog/example.html").exists()
    html = (site / source_lang / "blog/example.html").read_text()
    assert f'href="/{target_lang}/index.html" class="lang-toggle"' in html
    assert f'hreflang="{target_lang}"' not in html
    assert f'/{source_lang}/blog/example.html' in (site / "sitemap.xml").read_text()
    assert f'/{target_lang}/blog/example.html' not in (site / "sitemap.xml").read_text()
    assert validate_generated_html(site) == []
    assert check_internal_links(site) == []


def test_non_strict_source_links_fall_back_to_available_language(site):
    target, identity, _ = add_post(site, "target", "pt-br")
    shutil.rmtree(site / "_source/translations/post/target")
    add_post(site, "linked", source="Read [this article](_source/posts/target.md#responsabilidade).",
             localized="Leia [este artigo](_source/posts/target.md#responsabilidade).")
    assert build.build(strict=False, skip_about_cv_translation=True)
    html = (site / "en/blog/linked.html").read_text()
    assert 'href="/pt/blog/target.html#responsabilidade"' in html


def test_non_strict_build_can_omit_about_and_cv_translations(site):
    from link_checker import check_internal_links

    add_post(site)
    assert build.build(strict=False)
    assert (site / "en/about.html").exists() and (site / "en/cv.html").exists()
    assert not (site / "pt/about.html").exists() and not (site / "pt/cv.html").exists()
    assert check_internal_links(site) == []


def test_explicit_no_strict_overrides_environment(monkeypatch):
    modes = []
    monkeypatch.setenv("STRICT_BUILD", "1")
    monkeypatch.setattr(build, "build", lambda **kwargs: modes.append(kwargs["strict"]) or True)
    assert build.main(["--no-strict"]) == 0
    assert build.main(["--strict"]) == 0
    assert build.main([]) == 0
    assert modes == [False, True, True]


def test_strict_content_validation_runs_once_in_the_source_locale_direction(site, monkeypatch):
    add_post(site, locale="pt-br")
    from translation_v2 import durable
    validate = durable.validate_translation
    calls = []

    def record(source, translated, **kwargs):
        calls.append(kwargs)
        return validate(source, translated, **kwargs)

    monkeypatch.setattr(durable, "validate_translation", record)
    assert build.build(strict=True, skip_about_cv_translation=True)
    assert calls == [{"source_locale": "pt-br", "target_locale": "en-us"}]


def test_strict_content_validation_failure_preserves_site(site, monkeypatch):
    add_post(site, locale="pt-br")
    previous = snapshot(site)
    monkeypatch.setattr("translation_v2.durable.validate_translation",
                        lambda *a, **k: (False, ["ERROR: paragraph 1 appears untranslated"]))
    assert not build.build(strict=True, skip_about_cv_translation=True)
    assert all((site / name).read_bytes() == content for name, content in previous.items())
    assert not (site / "_staging").exists()


def test_presentation_marker_damage_fails_before_any_render(site, monkeypatch):
    from tests.test_translation_v2_presentation_markers import SOURCE
    path = site / "_source/posts/deck.md"
    path.write_text("---\ntitle: Deck\ndate: 2026-09-07\nlang: en-us\ncontent_type: presentation\n---\n" + SOURCE)
    post = parse_markdown_post(path)
    identity = source_identity(
        slug=post["slug"], source_text=post["raw_content"], source_locale="en-us",
        target_locale="pt-br", artifact_type="presentation",
        frontmatter={k: post[k] for k in ("title", "excerpt", "tags", "content_type")},
    )
    AcceptedTranslations(site / "_source/translations").accept(identity, {
        "title": "Deck", "excerpt": "", "tags": [],
        "content": SOURCE.replace('layout="lead"', 'layout="content"'),
    }, {}, expected_revision=None)
    monkeypatch.setattr(build, "generate_presentation_html", lambda *a, **k: pytest.fail("Rendered damaged content"))
    assert not build.build(strict=False, skip_about_cv_translation=True)
    assert not (site / "_staging").exists()
