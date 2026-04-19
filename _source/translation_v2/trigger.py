"""Trigger-facing contracts for translation_v2 invocation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .contracts import TranslationRequest


TRIGGER_EVENT_TYPE_POST_FINISHED = "post.finished"
TRIGGER_SCHEMA_VERSION = "v1"


def compute_source_hash(source_text: str) -> str:
    """Return deterministic SHA-256 hash for source content."""

    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def derive_idempotency_key(*, slug: str, source_text: str, target_locale: str) -> str:
    """Derive idempotency key as slug+hash+target_locale."""

    normalized_slug = slug.strip() or "post"
    normalized_locale = target_locale.strip().lower()
    return f"{normalized_slug}+{compute_source_hash(source_text)}+{normalized_locale}"


@dataclass(slots=True)
class TranslationTriggerEvent:
    """Versioned trigger payload for post translation requests."""

    schema_version: str
    event_type: str
    slug: str
    source_locale: str
    target_locale: str
    source_text: str
    frontmatter: dict[str, Any]
    correlation_id: str
    run_id: str
    idempotency_key: str


def build_post_finished_trigger_event(
    *,
    slug: str,
    source_locale: str,
    target_locale: str,
    source_text: str,
    frontmatter: dict[str, Any],
    correlation_id: str,
    run_id: str,
) -> TranslationTriggerEvent:
    """Build a versioned post.finished trigger payload."""

    normalized_slug = slug.strip() or "post"
    normalized_source = source_locale.strip().lower()
    normalized_target = target_locale.strip().lower()
    return TranslationTriggerEvent(
        schema_version=TRIGGER_SCHEMA_VERSION,
        event_type=TRIGGER_EVENT_TYPE_POST_FINISHED,
        slug=normalized_slug,
        source_locale=normalized_source,
        target_locale=normalized_target,
        source_text=source_text,
        frontmatter=dict(frontmatter),
        correlation_id=correlation_id,
        run_id=run_id,
        idempotency_key=derive_idempotency_key(
            slug=normalized_slug,
            source_text=source_text,
            target_locale=normalized_target,
        ),
    )


def build_request_from_trigger_event(
    *,
    event: TranslationTriggerEvent,
    prompt_version: str,
    attach_path: str | None = None,
) -> TranslationRequest:
    """Translate trigger payload into provider-facing request contract."""

    metadata: dict[str, Any] = {
        "slug": event.slug,
        "locale_direction": f"{event.source_locale}->{event.target_locale}",
        "title": event.frontmatter.get("title", ""),
        "excerpt": event.frontmatter.get("excerpt", ""),
        "tags": event.frontmatter.get("tags", []),
        "trigger": {
            "event_type": event.event_type,
            "schema_version": event.schema_version,
            "idempotency_key": event.idempotency_key,
            "correlation_id": event.correlation_id,
            "run_id": event.run_id,
        },
        "correlation_id": event.correlation_id,
        "build_run_id": event.run_id,
        "idempotency_key": event.idempotency_key,
    }
    if attach_path:
        metadata["attach_path"] = attach_path

    return TranslationRequest(
        run_id=f"{event.run_id}-{event.slug}-{event.target_locale}",
        source_locale=event.source_locale,
        target_locale=event.target_locale,
        source_text=event.source_text,
        prompt_version=prompt_version,
        metadata=metadata,
    )
