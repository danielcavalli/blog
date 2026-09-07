"""Versioned accepted content. Model and prompt changes never expire this store."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .storage import atomic_json, file_lock, read_json


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def source_identity(
    *,
    slug: str,
    source_text: str,
    frontmatter: dict[str, Any],
    source_locale: str,
    target_locale: str,
    artifact_type: str,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "text": source_text,
        "frontmatter": frontmatter,
        "source_locale": source_locale.lower(),
        "target_locale": target_locale.lower(),
        "artifact_type": artifact_type,
    }


class AcceptedTranslations:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _directory(self, source: dict[str, Any]) -> Path:
        parts = [source["artifact_type"], source["slug"], source["target_locale"]]
        if any(not isinstance(p, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", p) for p in parts):
            raise ValueError("Unsafe translation artifact identifier")
        return self.root.joinpath(*parts)

    def current(self, source: dict[str, Any]) -> dict[str, Any] | None:
        directory = self._directory(source)
        pointer = read_json(directory / "current.json")
        if pointer is None:
            return None
        return self.revision(source, pointer.get("revision", ""))

    def revision(self, source: dict[str, Any], revision: str) -> dict[str, Any]:
        directory = self._directory(source)
        if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{64}", revision):
            raise RuntimeError(f"Invalid accepted translation pointer: {directory}")
        record = read_json(directory / "revisions" / f"{revision}.json")
        if record is None or digest(record) != revision:
            raise RuntimeError(f"Missing or damaged accepted translation: {directory}")
        stored_source = record.get("source", {})
        if record.get("schema_version") != 1 or record.get("source_hash") != digest(stored_source):
            raise RuntimeError(f"Invalid accepted translation source: {directory}")
        for key in ("slug", "target_locale", "artifact_type"):
            if stored_source.get(key) != source[key]:
                raise RuntimeError(f"Accepted translation identity mismatch: {directory}")
        return record

    def promote(self, candidate: "AcceptedTranslations", source: dict[str, Any]) -> str:
        """Promote a candidate branch only when it descends from current acceptance."""
        chosen = candidate.current(source)
        if chosen is None or chosen["source_hash"] != digest(source):
            raise RuntimeError("Candidate source is missing or outdated")
        with file_lock(self.root / ".locks" / "write.lock"):
            current = self.current(source)
            base = digest(current) if current else None
            records = []
            record = chosen
            while digest(record) != base:
                records.append(record)
                parent = record.get("parent_revision")
                if parent == base:
                    break
                if parent is None:
                    raise RuntimeError(
                        "Accepted translation changed since this candidate was created"
                    )
                record = candidate.revision(source, parent)
            directory = self._directory(source)
            for record in reversed(records):
                path = directory / "revisions" / f"{digest(record)}.json"
                if not path.exists():
                    atomic_json(path, record)
            revision = digest(chosen)
            atomic_json(directory / "current.json", {"revision": revision})
            return revision

    def accept(
        self,
        source: dict[str, Any],
        translation: dict[str, Any],
        provenance: dict[str, Any],
        *,
        expected_revision: str | None,
    ) -> str:
        """Persist immutable history, then compare-and-swap the accepted pointer."""
        directory = self._directory(source)
        record = {
            "schema_version": 1,
            "source": source,
            "source_hash": digest(source),
            "translation": translation,
            "provenance": provenance,
            "parent_revision": expected_revision,
        }
        revision = digest(record)
        with file_lock(self.root / ".locks" / "write.lock"):
            current = self.current(source)
            actual = digest(current) if current is not None else None
            if actual != expected_revision:
                raise RuntimeError(f"Translation changed during this run: {source['slug']}; retry")
            path = directory / "revisions" / f"{revision}.json"
            if not path.exists():
                atomic_json(path, record)
            atomic_json(directory / "current.json", {"revision": revision})
        return revision


def matching_legacy_entry(cache: dict[str, Any], source: dict[str, Any]) -> tuple[str, dict] | None:
    """Import only accepted v2 entries whose complete source can be verified.

    Old source hashes included recipe fingerprints. Reconstruct that exact input
    with each entry's own provenance; never label a changed source as current.
    """
    entries = cache.get("__translation_v2__", {}).get("entries", {})
    frontmatter = json.dumps(source["frontmatter"], ensure_ascii=False, sort_keys=True)
    for key, entry in reversed(list(entries.items())):
        metadata = entry.get("metadata", {})
        fields = ("prompt_fingerprint", "writing_style_fingerprint", "author_voice_fingerprint")
        if not all(isinstance(metadata.get(f), str) for f in fields):
            continue
        if (entry.get("source_locale"), entry.get("target_locale")) != (
            source["source_locale"],
            source["target_locale"],
        ) or metadata.get("artifact_type") != source["artifact_type"]:
            continue
        old_input = (
            source["text"]
            + frontmatter
            + f"|{source['source_locale']}|{source['target_locale']}|artifact={source['artifact_type']}"
            + "".join(f"|{f}={metadata[f]}" for f in fields)
        )
        if hashlib.sha256(old_input.encode()).hexdigest() == entry.get("source_hash"):
            return key, entry
    return None
