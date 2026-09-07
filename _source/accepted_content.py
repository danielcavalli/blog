"""Read accepted localization for rendering, with no generation or cache writes."""

from pathlib import Path
from typing import Any

from markdown_refs import render_markdown_with_internal_refs
from translation_common import sanitize_translation_html
from translation_v2.accepted import AcceptedTranslations, digest, source_identity
from translation_v2.durable import validate_artifact


class AcceptedContent:
    def __init__(self, *, root: Path, strict_validation: bool = False):
        self.store = AcceptedTranslations(root)
        self.strict_validation = strict_validation

    def read_artifact(self, **identity: Any) -> dict[str, Any]:
        source = source_identity(**identity)
        record = self.store.current(source)
        if record is None or record["source_hash"] != digest(source):
            state = "missing" if record is None else "outdated"
            raise RuntimeError(
                f"Accepted translation {state}: {source['slug']} ({source['target_locale']}). "
                f"Run dan blog translate {source['slug']}, then rebuild."
            )
        validate_artifact(source, record["translation"], strict=self.strict_validation)
        return dict(record["translation"])

    def read_post(self, post: dict[str, Any], *, target_locale: str) -> dict[str, Any]:
        kind = post.get("content_type", "post")
        frontmatter = {key: post[key] for key in ("title", "excerpt", "tags")}
        if kind == "presentation":
            frontmatter["content_type"] = kind
        translation = self.read_artifact(
            slug=post["slug"], source_text=post["raw_content"],
            source_locale=post["lang"], target_locale=target_locale,
            artifact_type=kind, frontmatter=frontmatter,
        )
        return {
            **post,
            **{key: translation[key] for key in ("title", "excerpt", "tags")},
            "lang": target_locale,
            "raw_content": translation["content"],
            "content": sanitize_translation_html(render_markdown_with_internal_refs(
                translation["content"], source_markdown=post["raw_content"],
            )),
        }
