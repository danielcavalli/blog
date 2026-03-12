"""Tests for translator cache compatibility/migration behavior."""

import importlib
import os
import sys
import types


# Make _source importable without installing package.
_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


# Stub optional runtime deps before importing translator.
_google_stub = sys.modules.get("google", types.ModuleType("google"))
_genai_stub = sys.modules.get("google.genai", types.ModuleType("google.genai"))
_genai_types_stub = types.SimpleNamespace(HttpOptions=object)
setattr(_genai_stub, "types", _genai_types_stub)
setattr(_genai_stub, "Client", object)
sys.modules["google"] = _google_stub
sys.modules["google.genai"] = _genai_stub
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]

sys.modules.pop("translator", None)
translator = importlib.import_module("translator")


class _FakeCache:
    def __init__(self, by_slug):
        self.by_slug = by_slug
        self.stored = []

    def get_translation(self, slug, content_hash):
        entry = self.by_slug.get(slug)
        if entry and entry.get("hash") == content_hash:
            return entry.get("translation")
        return None

    def store_translation(self, slug, content_hash, translation):
        self.by_slug[slug] = {"hash": content_hash, "translation": translation}
        self.stored.append((slug, content_hash, translation))


def test_translate_post_reuses_legacy_hash_cache_without_api_call():
    t = object.__new__(translator.MultiAgentTranslator)
    t.enable_critique = False
    t.strict_validation = False

    slug = "sample-post"
    frontmatter = {"title": "Title", "excerpt": "Excerpt", "tags": ["one", "two"]}
    content = "some markdown content"
    source_locale = "en-us"
    target_locale = "pt-br"

    legacy_hash = t._calculate_hash(content + str(frontmatter))
    new_hash = t._calculate_hash(
        content + str(frontmatter) + f"|{source_locale}|{target_locale}"
    )

    translation = {
        "title": "Titulo",
        "excerpt": "Resumo",
        "tags": ["um", "dois"],
        "content": "conteudo traduzido",
    }

    cache = _FakeCache({slug: {"hash": legacy_hash, "translation": translation}})
    t.cache = cache

    called = {"translate": False}

    def _should_not_translate(*args, **kwargs):
        called["translate"] = True
        raise AssertionError("_translate should not be called on legacy cache hit")

    t._translate = _should_not_translate

    result = t.translate_post(
        slug,
        frontmatter,
        content,
        force=False,
        source_locale=source_locale,
        target_locale=target_locale,
    )

    assert called["translate"] is False
    assert result == translation
    assert cache.stored
    assert cache.stored[-1][0] == slug
    assert cache.stored[-1][1] == new_hash
