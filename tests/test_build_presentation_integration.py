"""Build integration coverage for Markdown-backed presentation posts."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


_google_stub = types.ModuleType("google")
_genai_stub = types.ModuleType("google.genai")
sys.modules.setdefault("google", _google_stub)
sys.modules.setdefault("google.genai", _genai_stub)
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]


import build  # noqa: E402


PRESENTATION_MARKDOWN = """<!-- presentation:slide id="intro" layout="lead" density="normal" -->
# MAPR

[Docs](https://example.com/docs)

<!-- /presentation:slide -->

<!-- presentation:slide id="code" layout="code" density="dense" -->
```python
print("hello")
```

![Diagram](/static/img/diagram.png)
<!-- /presentation:slide -->
"""


def _mk_post() -> dict:
    return {
        "title": "MAPR",
        "date": "2026-04-29",
        "published_date": "2026-04-29",
        "updated_fm_date": "",
        "year": "2026",
        "month": "April",
        "excerpt": "Presentation excerpt",
        "slug": "mapr-ai-agents",
        "content_type": "presentation",
        "order": 0,
        "tags": ["AI Agents"],
        "en_tags": ["AI Agents"],
        "lang": "en-us",
        "content": "<p>regular markdown should not be rendered</p>",
        "raw_content": PRESENTATION_MARKDOWN,
        "created_date": "2026-04-29T00:00:00",
        "updated_date": "2026-04-29T00:00:00",
        "reading_time": 1,
    }


class _FakePresentationOrchestrator:
    def __init__(self):
        self.run_id = "test-run"
        self.prompt_version = "v2"
        self.correlation_id = "test-correlation"
        self.persist_calls: list[dict] = []

    def translate_if_needed_unpersisted(
        self,
        post,
        *,
        target_locale="pt-br",
        force_revision_reason=None,  # noqa: ARG002
    ):
        translated = post.copy()
        translated["lang"] = target_locale
        translated["title"] = "MAPR PT"
        translated["excerpt"] = "Resumo da apresentacao"
        translated["tags"] = ["Agentes de IA"]
        translated["raw_content"] = PRESENTATION_MARKDOWN.replace("# MAPR", "# MAPR traduzido")
        translated["content"] = "<p>translated markdown should not be rendered</p>"
        return translated

    def consume_artifact_persist_context(self, *, slug, artifact_type):  # noqa: ARG002
        return {"outcome": "cache_miss", "revised_from_cache_source": None}

    def persist_artifact_translation(self, **kwargs):  # noqa: ANN003
        self.persist_calls.append(kwargs)
        return "cache-key"


def _configure(monkeypatch, tmp_path: Path):
    posts_dir = tmp_path / "_source" / "posts"
    posts_dir.mkdir(parents=True)
    (posts_dir / "mapr-ai-agents.md").write_text(
        "---\ntitle: MAPR\ncontent_type: presentation\n---\n" + PRESENTATION_MARKDOWN,
        encoding="utf-8",
    )
    en_dir = tmp_path / "en"
    pt_dir = tmp_path / "pt"
    (en_dir / "blog").mkdir(parents=True)
    (pt_dir / "blog").mkdir(parents=True)

    monkeypatch.setattr(build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(build, "LANG_DIRS", {"en": en_dir, "pt": pt_dir})
    monkeypatch.setattr(build, "STAGING_DIR", tmp_path / "_staging")
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
    monkeypatch.setattr(build, "parse_markdown_post", lambda *_a, **_k: _mk_post())
    monkeypatch.setattr(build, "generate_about_html", lambda *a, **k: "<html>about</html>")
    monkeypatch.setattr(build, "generate_cv_html", lambda *a, **k: "<html>cv</html>")
    monkeypatch.setattr(build, "generate_root_index", lambda: "<html>root</html>")
    monkeypatch.setattr(build, "TranslationV2PostOrchestrator", lambda **_: _FakePresentationOrchestrator())
    monkeypatch.setattr(build, "validate_translation", lambda *a, **k: (True, []))

    validate_mod = types.ModuleType("validate")
    validate_mod.run_validation = lambda *_a, **_k: True  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "validate", validate_mod)


def test_markdown_presentation_builds_source_translation_indexes_and_sitemap(
    monkeypatch,
    tmp_path,
):
    _configure(monkeypatch, tmp_path)
    rendered_presentations: list[tuple[str, str, dict]] = []

    def _render_presentation(post, post_number, lang="en"):  # noqa: ARG001
        rendered_presentations.append((lang, post["slug"], post))
        return f"<html>{lang}:{post['slug']}:presentation.js</html>"

    monkeypatch.setattr(build, "generate_presentation_html", _render_presentation)
    monkeypatch.setattr(
        build,
        "generate_post_html",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("used post renderer")),
    )
    monkeypatch.setattr(
        build,
        "generate_index_html",
        lambda posts, lang="en": "|".join([lang, *[post["slug"] for post in posts]]),
    )
    monkeypatch.setattr(
        build,
        "generate_sitemap",
        lambda posts_en, posts_pt: "|".join(
            ["sitemap", *[post["slug"] for post in posts_en], *[post["slug"] for post in posts_pt]]
        ),
    )

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert (tmp_path / "en" / "blog" / "mapr-ai-agents.html").read_text(
        encoding="utf-8"
    ) == "<html>en:mapr-ai-agents:presentation.js</html>"
    assert (tmp_path / "pt" / "blog" / "mapr-ai-agents.html").read_text(
        encoding="utf-8"
    ) == "<html>pt:mapr-ai-agents:presentation.js</html>"
    assert "mapr-ai-agents" in (tmp_path / "en" / "index.html").read_text(encoding="utf-8")
    assert "mapr-ai-agents" in (tmp_path / "pt" / "index.html").read_text(encoding="utf-8")
    assert "mapr-ai-agents" in (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert [(lang, slug) for lang, slug, _post in rendered_presentations] == [
        ("en", "mapr-ai-agents"),
        ("pt", "mapr-ai-agents"),
    ]
    assert all("presentation" in post for _lang, _slug, post in rendered_presentations)
