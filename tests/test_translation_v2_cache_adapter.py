"""Tests for translation_v2 cache adapter legacy/v2 compatibility behavior."""

from __future__ import annotations

import json
import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.cache_adapter import (  # noqa: E402
    EVENT_LEGACY_HIT,
    EVENT_LEGACY_MALFORMED,
    EVENT_MISS,
    EVENT_V2_HIT,
    TranslationV2CacheAdapter,
    build_v2_cache_key,
    compute_source_hash,
)


def _request_kwargs() -> dict[str, str]:
    return {
        "slug": "post-one",
        "source_text": "source markdown body",
        "source_locale": "en-us",
        "target_locale": "pt-br",
        "provider": "opencode",
        "model": "openai/gpt-5.3-codex",
        "prompt_version": "v1",
    }


def test_legacy_hit_reads_compatible_entry(tmp_path):
    request = _request_kwargs()
    source_hash = compute_source_hash(request["source_text"])
    translation = {
        "title": "Titulo",
        "excerpt": "Resumo",
        "tags": ["tag"],
        "content": "conteudo",
    }
    cache_path = tmp_path / "translation-cache.json"
    cache_path.write_text(
        json.dumps(
            {
                request["slug"]: {
                    "hash": source_hash,
                    "translation": translation,
                }
            }
        ),
        encoding="utf-8",
    )

    adapter = TranslationV2CacheAdapter(cache_path=cache_path)
    cached = adapter.get_translation(**request)

    assert cached == translation
    assert [event["event"] for event in adapter.events] == [EVENT_LEGACY_HIT]


def test_legacy_hash_mismatch_treated_as_stale_source_miss(tmp_path):
    request = _request_kwargs()
    translation = {
        "title": "Titulo antigo",
        "excerpt": "Resumo antigo",
        "tags": ["tag"],
        "content": "conteudo antigo",
    }
    cache_path = tmp_path / "translation-cache.json"
    cache_path.write_text(
        json.dumps(
            {
                request["slug"]: {
                    "hash": compute_source_hash("different source markdown body"),
                    "translation": translation,
                }
            }
        ),
        encoding="utf-8",
    )

    adapter = TranslationV2CacheAdapter(cache_path=cache_path)
    cached = adapter.get_translation(**request)

    assert cached is None
    assert [event["event"] for event in adapter.events] == [
        EVENT_LEGACY_MALFORMED,
        EVENT_MISS,
    ]


def test_v2_hit_reads_namespaced_entry(tmp_path):
    request = _request_kwargs()
    legacy_slug = "legacy-post"
    legacy_translation = {
        "title": "Legacy",
        "excerpt": "Legacy excerpt",
        "tags": ["legacy"],
        "content": "legacy content",
    }
    translation = {
        "title": "Title",
        "excerpt": "Excerpt",
        "tags": ["tag"],
        "content": "content",
    }
    cache_path = tmp_path / "translation-cache.json"
    cache_path.write_text(
        json.dumps(
            {
                legacy_slug: {
                    "hash": compute_source_hash("legacy source"),
                    "translation": legacy_translation,
                }
            }
        ),
        encoding="utf-8",
    )
    adapter = TranslationV2CacheAdapter(cache_path=cache_path)

    key = adapter.store_translation(
        source_text=request["source_text"],
        source_locale=request["source_locale"],
        target_locale=request["target_locale"],
        provider=request["provider"],
        model=request["model"],
        prompt_version=request["prompt_version"],
        translation=translation,
    )

    expected_key = build_v2_cache_key(
        source_hash=compute_source_hash(request["source_text"]),
        source_locale=request["source_locale"],
        target_locale=request["target_locale"],
        provider=request["provider"],
        model=request["model"],
        prompt_version=request["prompt_version"],
    )
    assert key == expected_key
    assert key.startswith("schema=v2|")

    reloaded = TranslationV2CacheAdapter(cache_path=cache_path)
    cached = reloaded.get_translation(**request)

    assert cached == translation
    assert reloaded.events[-1]["event"] == EVENT_V2_HIT

    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert "__translation_v2__" in payload
    assert key in payload["__translation_v2__"]["entries"]
    assert payload[legacy_slug]["translation"] == legacy_translation


def test_v2_entry_persists_metadata(tmp_path):
    request = _request_kwargs()
    cache_path = tmp_path / "translation-cache.json"
    adapter = TranslationV2CacheAdapter(cache_path=cache_path)

    adapter.store_translation(
        source_text=request["source_text"],
        source_locale=request["source_locale"],
        target_locale=request["target_locale"],
        provider=request["provider"],
        model=request["model"],
        prompt_version=request["prompt_version"],
        translation={
            "title": "Title",
            "excerpt": "Excerpt",
            "tags": ["tag"],
            "content": "content",
        },
        metadata={"workflow": "revision", "revision_marker": "abc123"},
    )

    record = adapter.get_translation_record(**request)

    assert record is not None
    assert record.source == "v2"
    assert record.metadata == {
        "workflow": "revision",
        "revision_marker": "abc123",
    }


def test_miss_emits_miss_event(tmp_path):
    request = _request_kwargs()
    cache_path = tmp_path / "translation-cache.json"
    adapter = TranslationV2CacheAdapter(cache_path=cache_path)

    cached = adapter.get_translation(**request)

    assert cached is None
    assert adapter.events[-1]["event"] == EVENT_MISS


def test_malformed_legacy_entry_falls_back_to_miss(tmp_path):
    request = _request_kwargs()
    source_hash = compute_source_hash(request["source_text"])
    cache_path = tmp_path / "translation-cache.json"
    cache_path.write_text(
        json.dumps(
            {
                request["slug"]: {
                    "hash": source_hash,
                    "translation": "bad-shape",
                }
            }
        ),
        encoding="utf-8",
    )

    adapter = TranslationV2CacheAdapter(cache_path=cache_path)
    cached = adapter.get_translation(**request)

    assert cached is None
    assert [event["event"] for event in adapter.events] == [
        EVENT_LEGACY_MALFORMED,
        EVENT_MISS,
    ]
