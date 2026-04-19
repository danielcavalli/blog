"""Integration tests for build translation_v2 orchestration wiring.

Run only this fast suite:
    uv run --extra dev pytest tests/test_build_translation_v2_integration.py -q
"""

from __future__ import annotations

import os
import sys
import types
import json
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


_google_stub = types.ModuleType("google")
_genai_stub = types.ModuleType("google.genai")
_genai_stub.types = types.SimpleNamespace(HttpOptions=lambda **_: None)  # type: ignore[attr-defined]
sys.modules.setdefault("google", _google_stub)
sys.modules.setdefault("google.genai", _genai_stub)
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]


import build  # noqa: E402  # imported after dependency stubs by design
from translation_v2.cache_adapter import TranslationV2CacheAdapter  # noqa: E402


def _mk_post(slug: str, lang: str) -> dict:
    return {
        "title": slug,
        "date": "2026-03-12",
        "published_date": "2026-03-12",
        "year": "2026",
        "month": "March",
        "excerpt": "excerpt",
        "slug": slug,
        "order": 0,
        "tags": ["tag"],
        "lang": lang,
        "content": "<p>content</p>",
        "raw_content": "content",
        "created_date": "2026-03-12T00:00:00",
        "updated_date": "2026-03-12T00:00:00",
        "reading_time": "1 min read",
    }


def _cache_source(
    *,
    source_text: str,
    frontmatter: dict,
    source_locale: str,
    target_locale: str,
    artifact_type: str,
) -> str:
    stable_frontmatter = json.dumps(frontmatter, ensure_ascii=False, sort_keys=True)
    return (
        source_text
        + "\n---translation-v2-meta---\n"
        + f"source_locale={source_locale.lower()}\n"
        + f"target_locale={target_locale.lower()}\n"
        + f"artifact_type={artifact_type}\n"
        + f"prompt_fingerprint=fake:{artifact_type}:v2\n"
        + f"author_voice_fingerprint=none\n"
        + f"writing_style_fingerprint=none\n"
        + f"frontmatter={stable_frontmatter}"
    )


class _FakePostOrchestrator:
    def __init__(
        self,
        *,
        cache_path: Path,
        should_fail: bool = False,
        fail_post_slugs: set[str] | None = None,
        post_translate_hook=None,
        artifact_translate_hook=None,
    ):
        self.should_fail = should_fail
        self.fail_post_slugs = set(fail_post_slugs or set())
        self.run_id = "test-run"
        self.prompt_version = "v2"
        self.correlation_id = "test-correlation"
        self.provider_name = "opencode"
        self.model_id = "fake/model"
        self.artifact_calls: list[dict] = []
        self.persist_calls: list[dict] = []
        self.revision_requests: list[dict] = []
        self.cache = TranslationV2CacheAdapter(cache_path=cache_path)
        self._artifact_persist_context: dict[tuple[str, str], dict] = {}
        self.post_translate_hook = post_translate_hook
        self.artifact_translate_hook = artifact_translate_hook

    def _cache_lookup(self, *, slug, source_text, source_locale, target_locale, frontmatter):
        return self.cache.get_translation(
            slug=slug,
            source_text=_cache_source(
                source_text=source_text,
                frontmatter=frontmatter,
                source_locale=source_locale,
                target_locale=target_locale,
                artifact_type="post" if slug not in {"about", "cv"} else slug,
            ),
            source_locale=source_locale,
            target_locale=target_locale,
            provider=self.provider_name,
            model=self.model_id,
            prompt_version=self.prompt_version,
        )

    def _store_cache(self, *, slug, source_text, source_locale, target_locale, frontmatter, artifact_type, translation):
        cache_source = _cache_source(
            source_text=source_text,
            frontmatter=frontmatter,
            source_locale=source_locale,
            target_locale=target_locale,
            artifact_type=artifact_type,
        )
        self.cache.store_translation(
            source_text=cache_source,
            source_locale=source_locale,
            target_locale=target_locale,
            provider=self.provider_name,
            model=self.model_id,
            prompt_version=self.prompt_version,
            translation=translation,
            metadata={"artifact_type": artifact_type},
        )

    def _translate_post(
        self,
        post,
        target_locale="pt-br",
        *,
        persist_cache=True,
        force_revision_reason=None,
    ):
        slug = post["slug"]
        source_locale = post["lang"]
        source_text = post["raw_content"]
        frontmatter = {
            "title": post["title"],
            "excerpt": post["excerpt"],
            "tags": post["tags"],
        }
        if self.post_translate_hook is not None:
            self.post_translate_hook(
                slug=slug,
                source_locale=source_locale,
                target_locale=target_locale,
                force_revision_reason=force_revision_reason,
            )
        cached = self._cache_lookup(
            slug=slug,
            source_text=source_text,
            source_locale=source_locale,
            target_locale=target_locale,
            frontmatter=frontmatter,
        )
        if cached is not None:
            if force_revision_reason is not None:
                self.revision_requests.append(
                    {
                        "artifact_type": "post",
                        "slug": slug,
                        "reason": force_revision_reason,
                    }
                )
                self._artifact_persist_context[("post", slug)] = {
                    "outcome": "revision",
                    "revised_from_cache_source": "v2",
                }
                translated = post.copy()
                translated["lang"] = target_locale
                translated["title"] = f"revised::{cached['title']}"
                translated["excerpt"] = f"revised::{cached['excerpt']}"
                translated["tags"] = [f"revised::{tag}" for tag in cached["tags"]]
                translated["raw_content"] = f"revised::{cached['content']}"
                translated["content"] = f"<p>revised::{cached['content']}</p>"
                if persist_cache:
                    self._store_cache(
                        slug=slug,
                        source_text=source_text,
                        source_locale=source_locale,
                        target_locale=target_locale,
                        frontmatter=frontmatter,
                        artifact_type="post",
                        translation={
                            "title": translated["title"],
                            "excerpt": translated["excerpt"],
                            "tags": translated["tags"],
                            "content": translated["raw_content"],
                        },
                    )
                return translated
            self._artifact_persist_context[("post", slug)] = {
                "outcome": "cache_hit",
                "revised_from_cache_source": None,
            }
            translated = post.copy()
            translated["lang"] = target_locale
            translated["title"] = cached["title"]
            translated["excerpt"] = cached["excerpt"]
            translated["tags"] = cached["tags"]
            translated["raw_content"] = cached["content"]
            translated["content"] = f"<p>{cached['content']}</p>"
            return translated
        if self.should_fail or slug in self.fail_post_slugs:
            raise RuntimeError("simulated orchestrator failure")
        translated = post.copy()
        self._artifact_persist_context[("post", slug)] = {
            "outcome": "cache_miss",
            "revised_from_cache_source": None,
        }
        translated["lang"] = target_locale
        translated["title"] = f"pt::{post['title']}"
        translated["excerpt"] = f"pt::{post['excerpt']}"
        translated["tags"] = [f"pt::{tag}" for tag in post["tags"]]
        translated["raw_content"] = f"pt::{post['raw_content']}"
        translated["content"] = f"<p>pt::{post['raw_content']}</p>"
        if persist_cache:
            self._store_cache(
                slug=slug,
                source_text=source_text,
                source_locale=source_locale,
                target_locale=target_locale,
                frontmatter=frontmatter,
                artifact_type="post",
                translation={
                    "title": translated["title"],
                    "excerpt": translated["excerpt"],
                    "tags": translated["tags"],
                    "content": translated["raw_content"],
                },
            )
        return translated

    def translate_if_needed(self, post, target_locale="pt-br", force_revision_reason=None):
        return self._translate_post(
            post,
            target_locale=target_locale,
            persist_cache=True,
            force_revision_reason=force_revision_reason,
        )

    def translate_if_needed_unpersisted(
        self,
        post,
        target_locale="pt-br",
        force_revision_reason=None,
    ):
        return self._translate_post(
            post,
            target_locale=target_locale,
            persist_cache=False,
            force_revision_reason=force_revision_reason,
        )

    def _run_pipeline(self, request):
        if self.should_fail:
            raise RuntimeError("simulated orchestrator failure")
        return {
            "title": f"pt::{request.metadata.get('slug', '')}",
            "excerpt": "",
            "tags": [],
            "content": f"pt::{request.source_text}",
        }

    def translate_artifact_if_needed(
        self,
        *,
        slug,
        source_text,
        source_locale,
        target_locale,
        artifact_type,
        frontmatter=None,
        attach_path=None,
        do_not_translate_entities=None,
        persist_cache=True,
        force_revision_reason=None,
    ):
        if self.artifact_translate_hook is not None:
            self.artifact_translate_hook(
                slug=slug,
                artifact_type=artifact_type,
                source_locale=source_locale,
                target_locale=target_locale,
                force_revision_reason=force_revision_reason,
            )
        cached = self._cache_lookup(
            slug=slug,
            source_text=source_text,
            source_locale=source_locale,
            target_locale=target_locale,
            frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
        )
        if cached is not None:
            if force_revision_reason is not None:
                self.revision_requests.append(
                    {
                        "artifact_type": artifact_type,
                        "slug": slug,
                        "reason": force_revision_reason,
                    }
                )
                if artifact_type == "about":
                    paragraphs = [
                        part.strip()
                        for part in str(cached["content"]).split("\n\n")
                        if part.strip()
                    ]
                    heading = str(cached.get("title", "ABOUT"))
                    body = [
                        f"revised::{paragraph}"
                        for paragraph in paragraphs
                        if not paragraph.startswith("# ")
                    ]
                    translation = {
                        "title": f"revised::{heading}",
                        "excerpt": "",
                        "tags": [],
                        "content": "\n\n".join([f"# revised::{heading}", *body]),
                    }
                    if persist_cache:
                        self._store_cache(
                            slug=slug,
                            source_text=source_text,
                            source_locale=source_locale,
                            target_locale=target_locale,
                            frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
                            artifact_type=artifact_type,
                            translation=translation,
                        )
                    return translation
                if artifact_type == "cv":
                    translation = dict(cached)
                    translation["summary"] = f"revised::{cached['summary']}"
                    if persist_cache:
                        self._store_cache(
                            slug=slug,
                            source_text=source_text,
                            source_locale=source_locale,
                            target_locale=target_locale,
                            frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
                            artifact_type=artifact_type,
                            translation=translation,
                        )
                    return translation
            return cached
        if self.should_fail:
            raise RuntimeError("simulated orchestrator failure")
        self.artifact_calls.append(
            {
                "slug": slug,
                "source_text": source_text,
                "source_locale": source_locale,
                "target_locale": target_locale,
                "artifact_type": artifact_type,
                "frontmatter": frontmatter,
                "attach_path": attach_path,
                "do_not_translate_entities": do_not_translate_entities,
            }
        )
        if artifact_type == "about":
            parts = [part.strip() for part in source_text.split("\n\n") if part.strip()]
            title = parts[0][2:].strip()
            paragraphs = parts[1:]
            translation = {
                "title": f"pt::{title}",
                "excerpt": "",
                "tags": [],
                "content": "\n\n".join(
                    [f"# pt::{title}", *[f"pt::{paragraph}" for paragraph in paragraphs]]
                ),
            }
            if persist_cache:
                self._store_cache(
                    slug=slug,
                    source_text=source_text,
                    source_locale=source_locale,
                    target_locale=target_locale,
                    frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
                    artifact_type=artifact_type,
                    translation=translation,
                )
            return translation
        if artifact_type == "cv":
            translation = {
                "name": "Daniel Cavalli",
                "tagline": "pt::tagline",
                "location": "Rio de Janeiro, Brazil",
                "contact": {"linkedin": "https://www.linkedin.com/in/cavallidaniel/"},
                "skills": ["MLOps", "Kubeflow"],
                "languages_spoken": ["pt::English (Full Professional)"],
                "summary": "pt::summary",
                "experience": [
                    {
                        "title": "Senior Machine Learning Engineer",
                        "company": "Nubank",
                        "location": "Brazil",
                        "period": "2026 - Present",
                        "description": "pt::description",
                        "achievements": ["pt::achievement"],
                    }
                ],
                "education": [
                    {
                        "degree": "pt::Bachelor of Economics",
                        "school": "Federal University of Rio de Janeiro",
                        "period": "2017 - 2023",
                    }
                ],
            }
            if persist_cache:
                self._store_cache(
                    slug=slug,
                    source_text=source_text,
                    source_locale=source_locale,
                    target_locale=target_locale,
                    frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
                    artifact_type=artifact_type,
                    translation=translation,
                )
            return translation
        translation = {
            "title": f"pt::{slug}",
            "excerpt": "",
            "tags": [],
            "content": f"pt::{source_text}",
        }
        if persist_cache:
            self._store_cache(
                slug=slug,
                source_text=source_text,
                source_locale=source_locale,
                target_locale=target_locale,
                frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
                artifact_type=artifact_type,
                translation=translation,
            )
        return translation

    def persist_artifact_translation(
        self,
        *,
        slug,
        source_text,
        source_locale,
        target_locale,
        artifact_type,
        frontmatter=None,
        translation,
        revised_from_cache_source=None,
    ):
        self.persist_calls.append(
            {
                "slug": slug,
                "artifact_type": artifact_type,
                "target_locale": target_locale,
            }
        )
        self._store_cache(
            slug=slug,
            source_text=source_text,
            source_locale=source_locale,
            target_locale=target_locale,
            frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
            artifact_type=artifact_type,
            translation=translation,
        )

    def consume_artifact_persist_context(self, *, slug, artifact_type):
        return self._artifact_persist_context.pop(
            (artifact_type, slug),
            {"outcome": "cache_hit", "revised_from_cache_source": None},
        )


def _configure(
    tmp_path: Path,
    monkeypatch,
    source_post: dict,
    *,
    should_fail: bool = False,
    fail_post_slugs: set[str] | None = None,
    post_translate_hook=None,
    artifact_translate_hook=None,
) -> tuple[list[dict], list[_FakePostOrchestrator]]:
    posts_dir = tmp_path / "_source" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    (posts_dir / f"{source_post['slug']}.md").write_text(
        "---\ntitle: x\n---\nbody", encoding="utf-8"
    )

    en_dir = tmp_path / "en"
    pt_dir = tmp_path / "pt"
    (en_dir / "blog").mkdir(parents=True, exist_ok=True)
    (pt_dir / "blog").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(build, "LANG_DIRS", {"en": en_dir, "pt": pt_dir})
    monkeypatch.setattr(build, "STAGING_DIR", tmp_path / "_staging")
    monkeypatch.setattr(build, "TRANSLATION_CACHE", tmp_path / "_cache" / "translation-cache.json")
    monkeypatch.setattr(
        build,
        "_out",
        lambda rel_path, staging_dir: rel_path
        if staging_dir is None
        else staging_dir / rel_path.relative_to(tmp_path),
    )

    monkeypatch.setattr(build, "load_post_metadata", lambda: {})
    monkeypatch.setattr(build, "save_post_metadata", lambda *_: None)
    monkeypatch.setattr(build, "load_cv_data", lambda: {"name": "x"})
    monkeypatch.setattr(build, "parse_markdown_post", lambda *_a, **_k: source_post.copy())
    monkeypatch.setattr(build, "generate_post_html", lambda *a, **k: "<html>post</html>")
    monkeypatch.setattr(build, "generate_index_html", lambda *a, **k: "<html>index</html>")
    monkeypatch.setattr(build, "generate_about_html", lambda *a, **k: "<html>about</html>")
    monkeypatch.setattr(build, "generate_cv_html", lambda *a, **k: "<html>cv</html>")
    monkeypatch.setattr(build, "generate_root_index", lambda: "<html>root</html>")
    monkeypatch.setattr(build, "generate_sitemap", lambda *a, **k: "<xml />")
    monkeypatch.setitem(
        build.LANGUAGES,
        "en",
        {
            **build.LANGUAGES["en"],
            "about": {
                "title": "ABOUT",
                "p1": "English paragraph one.",
                "p2": "English paragraph two.",
                "p3": "English paragraph three.",
                "p4": "English paragraph four.",
                "p5": "English paragraph five.",
                "p6": "English paragraph six.",
            },
        },
    )
    monkeypatch.setitem(
        build.LANGUAGES,
        "pt",
        {
            **build.LANGUAGES["pt"],
            "about": {
                "title": "",
                "p1": "",
                "p2": "",
                "p3": "",
                "p4": "",
                "p5": "",
                "p6": "",
            },
        },
    )

    validate_mod = types.ModuleType("validate")
    validate_mod.run_validation = lambda *_a, **_k: True  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "validate", validate_mod)

    init_calls: list[dict] = []
    orchestrators: list[_FakePostOrchestrator] = []

    def _fake_orchestrator_factory(**kwargs):
        init_calls.append(kwargs)
        orchestrator = _FakePostOrchestrator(
            cache_path=kwargs["cache_path"],
            should_fail=should_fail,
            fail_post_slugs=fail_post_slugs,
            post_translate_hook=post_translate_hook,
            artifact_translate_hook=artifact_translate_hook,
        )
        orchestrators.append(orchestrator)
        return orchestrator

    monkeypatch.setattr(build, "TranslationV2PostOrchestrator", _fake_orchestrator_factory)
    return init_calls, orchestrators


def test_translation_v2_routes_en_source_to_pt_output(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert (tmp_path / "en" / "blog" / "deterministic-post.html").exists()
    assert (tmp_path / "pt" / "blog" / "deterministic-post.html").exists()
    assert (tmp_path / "en" / "about.html").exists()
    assert (tmp_path / "pt" / "about.html").exists()
    assert (tmp_path / "en" / "cv.html").exists()
    assert (tmp_path / "pt" / "cv.html").exists()


def test_translation_v2_routes_pt_source_to_en_output(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "pt-br")
    _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert (tmp_path / "pt" / "blog" / "deterministic-post.html").exists()
    assert (tmp_path / "en" / "blog" / "deterministic-post.html").exists()


def test_build_always_initializes_full_pipeline_for_posts(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    init_calls, _ = _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert init_calls
    assert init_calls[0]["provider_name"] == "opencode"
    assert "enable_critique" not in init_calls[0]
    assert init_calls[0]["strict_validation"] is False


def test_translation_failure_fails_build_without_partial_bypass(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post, should_fail=True)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is False
    assert (tmp_path / "en" / "blog" / "deterministic-post.html").exists()
    assert not (tmp_path / "pt" / "blog" / "deterministic-post.html").exists()


def test_default_build_translates_about_and_cv_via_translation_v2(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post)

    cv_data = {
        "name": "Daniel Cavalli",
        "tagline": "Senior Machine Learning Engineer @ Nubank",
        "location": "Rio de Janeiro, Brazil",
        "contact": {"linkedin": "https://www.linkedin.com/in/cavallidaniel/"},
        "skills": ["MLOps", "Kubeflow"],
        "languages_spoken": ["English (Full Professional)"],
        "summary": "I build ML systems.",
        "experience": [
            {
                "title": "Senior Machine Learning Engineer",
                "company": "Nubank",
                "location": "Brazil",
                "period": "2026 - Present",
                "description": "Leading platform evolution.",
                "achievements": ["Built distributed pipelines."],
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Economics",
                "school": "Federal University of Rio de Janeiro",
                "period": "2017 - 2023",
            }
        ],
    }
    monkeypatch.setattr(build, "load_cv_data", lambda: cv_data)

    captured: dict = {}

    def _capture_about_html(*, lang="en", translated_about=None):
        if lang == "pt":
            captured["translated_about"] = translated_about
        return "<html>about</html>"

    def _capture_cv_html(*, lang="en", translated_cv=None):
        if lang == "pt":
            captured["translated_cv"] = translated_cv
        return "<html>cv</html>"

    monkeypatch.setattr(build, "generate_about_html", _capture_about_html)
    monkeypatch.setattr(build, "generate_cv_html", _capture_cv_html)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert ok is True
    about_pt = build.LANGUAGES["pt"]["about"]
    assert set(about_pt.keys()) == {"title", "p1", "p2", "p3", "p4", "p5", "p6"}
    assert all(
        str(about_pt[key]).startswith("pt::")
        for key in ["title", "p1", "p2", "p3", "p4", "p5", "p6"]
    )
    assert captured["translated_about"] == about_pt

    translated_cv = captured["translated_cv"]
    assert set(translated_cv.keys()) == {
        "name",
        "tagline",
        "location",
        "contact",
        "skills",
        "languages_spoken",
        "summary",
        "experience",
        "education",
    }
    assert translated_cv["name"] == cv_data["name"]
    assert translated_cv["location"] == cv_data["location"]
    assert translated_cv["contact"] == cv_data["contact"]
    assert translated_cv["experience"][0]["company"] == cv_data["experience"][0]["company"]
    assert translated_cv["experience"][0]["location"] == cv_data["experience"][0]["location"]
    assert translated_cv["tagline"].startswith("pt::")
    assert translated_cv["summary"].startswith("pt::")
    assert translated_cv["experience"][0]["description"].startswith("pt::")
    assert translated_cv["experience"][0]["achievements"][0].startswith("pt::")
    assert translated_cv["education"][0]["degree"].startswith("pt::")
    assert translated_cv["languages_spoken"][0].startswith("pt::")


def test_about_and_cv_translate_as_artifact_units(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _init_calls, orchestrators = _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert ok is True
    assert len(orchestrators) == 1
    artifact_calls = orchestrators[0].artifact_calls
    assert [call["artifact_type"] for call in artifact_calls] == ["about", "cv"]

    about_call = artifact_calls[0]
    assert about_call["slug"] == "about"
    assert about_call["target_locale"] == "pt-br"
    assert about_call["attach_path"].endswith("_source/config.py")
    assert about_call["do_not_translate_entities"] is None
    assert about_call["source_text"].startswith("# ")
    assert "\n\n" in about_call["source_text"]

    cv_call = artifact_calls[1]
    assert cv_call["slug"] == "cv"
    assert cv_call["target_locale"] == "pt-br"
    assert cv_call["attach_path"].endswith("cv_data.yaml")
    assert cv_call["do_not_translate_entities"] is not None
    assert "Nubank" in cv_call["do_not_translate_entities"]
    assert "Kubeflow" in cv_call["do_not_translate_entities"]
    assert '"name": "x"' in cv_call["source_text"]


def test_en_source_builds_source_output_before_pt_translation_starts(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")

    def _post_translate_hook(**kwargs):
        assert kwargs["slug"] == "deterministic-post"
        assert (tmp_path / "en" / "blog" / "deterministic-post.html").exists()

    _configure(
        tmp_path,
        monkeypatch,
        source_post,
        post_translate_hook=_post_translate_hook,
    )

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True


def test_pt_source_builds_source_output_before_en_translation_starts(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "pt-br")

    def _post_translate_hook(**kwargs):
        assert kwargs["slug"] == "deterministic-post"
        assert (tmp_path / "pt" / "blog" / "deterministic-post.html").exists()

    _configure(
        tmp_path,
        monkeypatch,
        source_post,
        post_translate_hook=_post_translate_hook,
    )

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True


def test_about_and_cv_source_pages_exist_before_static_translation_lane_starts(
    monkeypatch, tmp_path
):
    source_post = _mk_post("deterministic-post", "en-us")

    def _artifact_translate_hook(**kwargs):
        if kwargs["artifact_type"] in {"about", "cv"}:
            assert (tmp_path / "en" / "about.html").exists()
            assert (tmp_path / "en" / "cv.html").exists()

    _configure(
        tmp_path,
        monkeypatch,
        source_post,
        artifact_translate_hook=_artifact_translate_hook,
    )

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert ok is True


def test_successful_about_and_cv_commit_live_output_before_later_post_failure(
    monkeypatch, tmp_path
):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post, fail_post_slugs={"deterministic-post"})

    monkeypatch.setattr(
        build,
        "generate_about_html",
        lambda *, lang="en", translated_about=None: f"<html>{(translated_about or {}).get('title', 'about')}</html>",
    )
    monkeypatch.setattr(
        build,
        "generate_cv_html",
        lambda *, lang="en", translated_cv=None: f"<html>{(translated_cv or {}).get('summary', 'cv')}</html>",
    )

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert ok is False
    assert (tmp_path / "pt" / "about.html").read_text(encoding="utf-8") == "<html>pt::ABOUT</html>"
    assert (tmp_path / "pt" / "cv.html").read_text(encoding="utf-8") == "<html>pt::summary</html>"


def test_successful_about_and_cv_commit_to_staging_before_later_post_failure(
    monkeypatch, tmp_path
):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post, fail_post_slugs={"deterministic-post"})

    monkeypatch.setattr(
        build,
        "generate_about_html",
        lambda *, lang="en", translated_about=None: f"<html>{(translated_about or {}).get('title', 'about')}</html>",
    )
    monkeypatch.setattr(
        build,
        "generate_cv_html",
        lambda *, lang="en", translated_cv=None: f"<html>{(translated_cv or {}).get('summary', 'cv')}</html>",
    )

    ok = build.build(strict=True, use_staging=False, skip_about_cv_translation=False)

    assert ok is False
    assert not (tmp_path / "pt" / "about.html").exists()
    assert not (tmp_path / "pt" / "cv.html").exists()
    assert (tmp_path / "_staging" / "pt" / "about.html").read_text(encoding="utf-8") == "<html>pt::ABOUT</html>"
    assert (tmp_path / "_staging" / "pt" / "cv.html").read_text(encoding="utf-8") == "<html>pt::summary</html>"


def test_successful_translated_post_commits_output_and_cache_before_later_failure(
    monkeypatch, tmp_path
):
    posts_dir = tmp_path / "_source" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    (posts_dir / "first.md").write_text("---\ntitle: first\n---\nbody", encoding="utf-8")
    (posts_dir / "second.md").write_text("---\ntitle: second\n---\nbody", encoding="utf-8")

    first_post = _mk_post("first", "en-us")
    second_post = _mk_post("second", "en-us")
    _configure(tmp_path, monkeypatch, first_post, fail_post_slugs={"second"})
    monkeypatch.setattr(build, "POSTS_DIR", posts_dir)

    def _parse_markdown_post(filepath, _metadata_store=None):  # noqa: ARG001
        if Path(filepath).name == "first.md":
            return first_post.copy()
        return second_post.copy()

    monkeypatch.setattr(build, "parse_markdown_post", _parse_markdown_post)
    monkeypatch.setattr(
        build,
        "generate_post_html",
        lambda post, *_a, **_k: f"<html>{post['slug']}::{post['raw_content']}</html>",
    )

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is False
    assert (tmp_path / "pt" / "blog" / "first.html").read_text(encoding="utf-8") == "<html>first::pt::content</html>"
    assert not (tmp_path / "pt" / "blog" / "second.html").exists()

    adapter = TranslationV2CacheAdapter(cache_path=tmp_path / "_cache" / "translation-cache.json")
    cached = adapter.get_translation(
        slug="first",
        source_text=_cache_source(
            source_text="content",
            frontmatter={"title": "first", "excerpt": "excerpt", "tags": ["tag"]},
            source_locale="en-us",
            target_locale="pt-br",
            artifact_type="post",
        ),
        source_locale="en-us",
        target_locale="pt-br",
        provider="opencode",
        model="fake/model",
        prompt_version="v2",
    )
    assert cached is not None
    assert cached["content"] == "pt::content"


def test_next_build_reuses_about_and_cv_cache_after_partial_failure(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post, fail_post_slugs={"deterministic-post"})

    first_ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert first_ok is False

    _init_calls, orchestrators = _configure(tmp_path, monkeypatch, source_post)
    second_ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert second_ok is True
    assert len(orchestrators) == 1
    assert orchestrators[0].artifact_calls == []


def test_cached_translation_with_missing_rendered_output_enters_revision_path(
    monkeypatch, tmp_path
):
    source_post = _mk_post("deterministic-post", "en-us")
    _init_calls, orchestrators = _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    translated_output = tmp_path / "pt" / "blog" / "deterministic-post.html"
    translated_output.unlink()

    _init_calls, orchestrators = _configure(tmp_path, monkeypatch, source_post)
    second_ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert second_ok is True
    assert len(orchestrators) == 1
    assert orchestrators[0].revision_requests == [
        {
            "artifact_type": "post",
            "slug": "deterministic-post",
            "reason": "translated output missing",
        }
    ]
    assert translated_output.exists()
