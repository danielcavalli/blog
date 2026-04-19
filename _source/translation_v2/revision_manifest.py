"""Committed translation revision manifest helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from paths import PROJECT_ROOT


REVISION_MANIFEST_PATH = PROJECT_ROOT / "_source" / "translation_revision.yaml"
_RESERVED_KEYS = {"target_locales", "all", "reason", "notes", "style_mode"}


@dataclass(frozen=True, slots=True)
class RevisionRequest:
    """Normalized revision request for one slug/target-locale pair."""

    slug: str
    target_locale: str
    payload: dict[str, Any]
    marker: str


class TranslationRevisionManifest:
    """Read-only access to the committed revision manifest."""

    def __init__(self, path: str | Path = REVISION_MANIFEST_PATH) -> None:
        self.path = Path(path)
        self._data = self._load()

    def get(self, *, slug: str, target_locale: str) -> RevisionRequest | None:
        entries = self._entries_root()
        if not isinstance(entries, dict):
            return None

        raw_entry = entries.get(slug)
        if raw_entry is None:
            return None

        payload = _normalize_revision_entry(raw_entry, target_locale=target_locale)
        if payload is None:
            return None

        marker = hashlib.sha256(
            json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return RevisionRequest(
            slug=slug,
            target_locale=target_locale,
            payload=payload,
            marker=marker,
        )

    def _entries_root(self) -> dict[str, Any]:
        posts = self._data.get("posts")
        if isinstance(posts, dict):
            return posts

        artifacts = self._data.get("artifacts")
        if isinstance(artifacts, dict):
            return artifacts

        return {}

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"posts": {}}
        try:
            payload = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            return {"posts": {}}
        if isinstance(payload, dict):
            return payload
        return {"posts": {}}


def _normalize_revision_entry(raw_entry: Any, *, target_locale: str) -> dict[str, Any] | None:
    normalized_target = target_locale.strip().lower()

    if isinstance(raw_entry, str):
        cleaned = raw_entry.strip()
        if not cleaned:
            return None
        return {"reason": cleaned}

    if isinstance(raw_entry, list):
        locales = [str(item).strip().lower() for item in raw_entry if str(item).strip()]
        if normalized_target in locales:
            return {"target_locales": sorted(set(locales))}
        return None

    if not isinstance(raw_entry, dict):
        return None

    locale_payload = raw_entry.get(normalized_target)
    if isinstance(locale_payload, (str, dict, list)):
        payload = _normalize_revision_entry(locale_payload, target_locale=normalized_target)
        if payload is not None:
            return payload

    target_locales = raw_entry.get("target_locales")
    if isinstance(target_locales, list):
        locales = [str(item).strip().lower() for item in target_locales if str(item).strip()]
        if normalized_target in locales:
            payload = {
                key: value for key, value in raw_entry.items() if key not in _RESERVED_KEYS
            }
            for key in ("reason", "notes", "style_mode"):
                if key in raw_entry:
                    payload[key] = raw_entry[key]
            payload["target_locales"] = sorted(set(locales))
            return payload

    if raw_entry.get("all") is True:
        payload = {key: value for key, value in raw_entry.items() if key != "all"}
        return payload or {"all": True}

    locale_keys = [key for key in raw_entry if key.strip().lower() == normalized_target]
    if locale_keys:
        nested = raw_entry[locale_keys[0]]
        return _normalize_revision_entry(nested, target_locale=normalized_target)

    if any(key in raw_entry for key in ("reason", "notes", "style_mode")):
        return dict(raw_entry)

    return None
