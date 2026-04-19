"""Compatibility adapter for v2 translation caching.

The legacy translation cache file (``_cache/translation-cache.json``) stores entries
under post slugs:

    {
      "post-slug": {
        "hash": "<sha256>",
        "translation": { ... }
      }
    }

This adapter keeps that format readable while adding a namespaced v2 section in the
same file so existing build flows are not disrupted:

    {
      "post-slug": { ...legacy... },
      "__translation_v2__": {
        "schema_version": "v2",
        "entries": {
          "schema=v2|source_hash=...|source_locale=...|target_locale=...|provider=...|model=...|prompt_version=...": {
            "schema_version": "v2",
            "source_hash": "...",
            "source_locale": "...",
            "target_locale": "...",
            "provider": "...",
            "model": "...",
            "prompt_version": "...",
            "translation": { ... }
          }
        }
      }
    }

Cache read events are emitted as one of: ``legacy_hit``, ``v2_hit``, ``miss``,
or ``legacy_malformed``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, overload

from paths import TRANSLATION_CACHE

CACHE_SCHEMA_VERSION = "v2"
V2_NAMESPACE = "__translation_v2__"

EVENT_LEGACY_HIT = "legacy_hit"
EVENT_V2_HIT = "v2_hit"
EVENT_MISS = "miss"
EVENT_LEGACY_MALFORMED = "legacy_malformed"


@dataclass(slots=True)
class TranslationCacheRecord:
    """Resolved translation cache entry with provenance metadata."""

    translation: dict[str, Any]
    source: str
    source_hash: str | None = None
    source_locale: str | None = None
    target_locale: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_legacy(self) -> bool:
        return self.source == "legacy"


def compute_source_hash(source_text: str) -> str:
    """Compute a deterministic source hash used by both key formats."""

    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def build_v2_cache_key(
    *,
    source_hash: str,
    source_locale: str,
    target_locale: str,
    provider: str,
    model: str,
    prompt_version: str,
    schema_version: str = CACHE_SCHEMA_VERSION,
) -> str:
    """Build a deterministic v2 cache key.

    The key intentionally includes schema version so future schema evolutions can
    coexist in one cache file without key collisions.
    """

    return (
        f"schema={schema_version}|source_hash={source_hash}|"
        f"source_locale={source_locale}|target_locale={target_locale}|"
        f"provider={provider}|model={model}|prompt_version={prompt_version}"
    )


class TranslationV2CacheAdapter:
    """Read/write adapter for mixed legacy + v2 translation cache records."""

    def __init__(
        self,
        cache_path: str | Path = TRANSLATION_CACHE,
        *,
        event_handler: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.cache_path = Path(cache_path)
        self._event_handler = event_handler
        self.events: list[dict[str, Any]] = []
        self.cache = self._load_cache()

    def get_translation(
        self,
        *,
        slug: str,
        source_text: str,
        source_locale: str,
        target_locale: str,
        provider: str,
        model: str,
        prompt_version: str,
    ) -> dict[str, Any] | None:
        """Resolve translation with v2-first lookup and legacy fallback."""
        record = self.get_translation_record(
            slug=slug,
            source_text=source_text,
            source_locale=source_locale,
            target_locale=target_locale,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
        )
        return None if record is None else record.translation

    def get_translation_record(
        self,
        *,
        slug: str,
        source_text: str,
        source_locale: str,
        target_locale: str,
        provider: str,
        model: str,
        prompt_version: str,
    ) -> TranslationCacheRecord | None:
        """Resolve translation with v2-first lookup and legacy fallback."""

        source_hash = compute_source_hash(source_text)
        key = build_v2_cache_key(
            source_hash=source_hash,
            source_locale=source_locale,
            target_locale=target_locale,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
        )

        v2_entry = self._v2_entry_for_key(key)
        if v2_entry is not None:
            self._emit_event(EVENT_V2_HIT, slug=slug, key=key)
            return v2_entry

        legacy_entry = self.cache.get(slug)
        if legacy_entry is not None:
            legacy_error = self._legacy_error(legacy_entry, expected_hash=source_hash)
            if legacy_error is not None:
                self._emit_event(
                    EVENT_LEGACY_MALFORMED,
                    slug=slug,
                    key=key,
                    reason=legacy_error,
                )
            else:
                translation = legacy_entry["translation"]
                self._emit_event(EVENT_LEGACY_HIT, slug=slug, key=key)
                return TranslationCacheRecord(
                    translation=translation,
                    source="legacy",
                    source_hash=source_hash,
                    source_locale=source_locale,
                    target_locale=target_locale,
                )

        self._emit_event(EVENT_MISS, slug=slug, key=key)
        return None

    def store_translation(
        self,
        *,
        source_text: str,
        source_locale: str,
        target_locale: str,
        provider: str,
        model: str,
        prompt_version: str,
        translation: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persist a v2 entry and return its deterministic cache key."""

        source_hash = compute_source_hash(source_text)
        key = build_v2_cache_key(
            source_hash=source_hash,
            source_locale=source_locale,
            target_locale=target_locale,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
        )

        v2_root = self._v2_root(create=True)
        entries = v2_root["entries"]
        entries[key] = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "source_hash": source_hash,
            "source_locale": source_locale,
            "target_locale": target_locale,
            "provider": provider,
            "model": model,
            "prompt_version": prompt_version,
            "translation": translation,
            "metadata": dict(metadata or {}),
        }
        self._save_cache()
        return key

    def _load_cache(self) -> dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        if isinstance(payload, dict):
            return payload
        return {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self.cache, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @overload
    def _v2_root(self, *, create: Literal[True]) -> dict[str, Any]: ...

    @overload
    def _v2_root(self, *, create: Literal[False]) -> dict[str, Any] | None: ...

    def _v2_root(self, *, create: bool) -> dict[str, Any] | None:
        existing = self.cache.get(V2_NAMESPACE)
        if isinstance(existing, dict) and isinstance(existing.get("entries"), dict):
            existing.setdefault("schema_version", CACHE_SCHEMA_VERSION)
            return existing

        if not create:
            return None

        root: dict[str, Any] = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "entries": {},
        }
        self.cache[V2_NAMESPACE] = root
        return root

    def _v2_entry_for_key(self, key: str) -> TranslationCacheRecord | None:
        root = self._v2_root(create=False)
        if root is None:
            return None
        entry = root.get("entries", {}).get(key)
        if isinstance(entry, dict) and isinstance(entry.get("translation"), dict):
            metadata = entry.get("metadata")
            return TranslationCacheRecord(
                translation=entry["translation"],
                source="v2",
                source_hash=entry.get("source_hash"),
                source_locale=entry.get("source_locale"),
                target_locale=entry.get("target_locale"),
                provider=entry.get("provider"),
                model=entry.get("model"),
                prompt_version=entry.get("prompt_version"),
                metadata=dict(metadata) if isinstance(metadata, dict) else {},
            )
        return None

    def _legacy_error(self, legacy_entry: Any, *, expected_hash: str) -> str | None:
        if not isinstance(legacy_entry, dict):
            return "legacy entry is not an object"

        legacy_hash = legacy_entry.get("hash")
        if not isinstance(legacy_hash, str):
            return "legacy entry missing string hash"

        if legacy_hash != expected_hash:
            return "legacy hash mismatch"

        translation = legacy_entry.get("translation")
        if not isinstance(translation, dict):
            return "legacy entry missing translation object"

        return None

    def _emit_event(self, event: str, **payload: Any) -> None:
        record = {"event": event, **payload}
        self.events.append(record)
        if self._event_handler is not None:
            self._event_handler(record)
