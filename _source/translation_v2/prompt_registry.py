"""Versioned prompt pack loader and fingerprint helpers for translation_v2."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Mapping


PROMPT_STAGES: tuple[str, str, str] = ("translate", "critique", "refine")
DEFAULT_PROMPT_VERSION = "v1"
PROMPTS_ROOT = Path(__file__).with_name("prompts")
_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}")


def prompt_template_path(
    stage: str, *, prompt_version: str = DEFAULT_PROMPT_VERSION, artifact_type: str = "post"
) -> Path:
    """Return the template path for a stage/version pair."""

    _validate_stage(stage)
    return PROMPTS_ROOT / prompt_version / _template_filename(stage, artifact_type=artifact_type)


def load_prompt_template(
    stage: str, *, prompt_version: str = DEFAULT_PROMPT_VERSION, artifact_type: str = "post"
) -> str:
    """Load a stage template from disk and fail fast when missing."""

    path = prompt_template_path(
        stage,
        prompt_version=prompt_version,
        artifact_type=artifact_type,
    )
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt template not found for stage '{stage}' and version '{prompt_version}': {path}"
        )
    return path.read_text(encoding="utf-8")


def render_prompt_template(
    stage: str,
    *,
    context: Mapping[str, str],
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    artifact_type: str = "post",
) -> str:
    """Render a stage prompt with strict placeholder substitution."""

    template = load_prompt_template(
        stage,
        prompt_version=prompt_version,
        artifact_type=artifact_type,
    )
    placeholders = set(_PLACEHOLDER_PATTERN.findall(template))
    provided_keys = set(context.keys())

    missing_keys = sorted(placeholders - provided_keys)
    if missing_keys:
        raise KeyError(
            "Missing required prompt placeholders: " + ", ".join(missing_keys)
        )

    extra_keys = sorted(provided_keys - placeholders)
    if extra_keys:
        raise ValueError(
            "Unexpected context keys for prompt template: " + ", ".join(extra_keys)
        )

    rendered = template
    for key in sorted(placeholders):
        rendered = re.sub(
            rf"\{{\{{\s*{re.escape(key)}\s*\}}\}}",
            lambda _match, replacement=context[key]: replacement,
            rendered,
        )

    unresolved = _PLACEHOLDER_PATTERN.findall(rendered)
    if unresolved:
        unique_unresolved = sorted(set(unresolved))
        raise ValueError(
            "Prompt template contains unresolved placeholders after rendering: "
            + ", ".join(unique_unresolved)
        )

    return rendered


def load_prompt_pack(
    *, prompt_version: str = DEFAULT_PROMPT_VERSION, artifact_type: str = "post"
) -> dict[str, str]:
    """Load all stage templates for a prompt version."""

    return {
        stage: load_prompt_template(
            stage,
            prompt_version=prompt_version,
            artifact_type=artifact_type,
        )
        for stage in PROMPT_STAGES
    }


def compute_prompt_pack_fingerprint(
    *, prompt_version: str = DEFAULT_PROMPT_VERSION, artifact_type: str = "post"
) -> str:
    """Compute a deterministic fingerprint for one prompt pack version."""

    return compute_prompt_pack_fingerprint_from_templates(
        templates_by_stage=load_prompt_pack(
            prompt_version=prompt_version,
            artifact_type=artifact_type,
        ),
        prompt_version=prompt_version,
        artifact_type=artifact_type,
    )


def compute_prompt_pack_fingerprint_from_templates(
    *,
    templates_by_stage: Mapping[str, str],
    prompt_version: str,
    artifact_type: str = "post",
) -> str:
    """Compute fingerprint from in-memory templates for testability."""

    for stage in PROMPT_STAGES:
        if stage not in templates_by_stage:
            raise KeyError(f"Missing template for stage '{stage}'")

    digest = hashlib.sha256()
    digest.update(f"prompt-pack:{prompt_version}:{artifact_type}\n".encode("utf-8"))
    for stage in PROMPT_STAGES:
        digest.update(f"stage:{stage}\n".encode("utf-8"))
        digest.update(templates_by_stage[stage].encode("utf-8"))
        digest.update(b"\n--template-boundary--\n")
    return digest.hexdigest()


def build_prompt_cache_key(
    base_key: str, *, prompt_version: str, prompt_fingerprint: str
) -> str:
    """Attach prompt version/fingerprint to a cache key."""

    return (
        f"{base_key}|prompt_version={prompt_version}|"
        f"prompt_fingerprint={prompt_fingerprint}"
    )


def build_prompt_artifact_metadata(
    *,
    stage: str,
    prompt_version: str,
    prompt_fingerprint: str,
) -> dict[str, str]:
    """Build prompt metadata that can be attached to run artifacts."""

    _validate_stage(stage)
    return {
        "stage": stage,
        "prompt_version": prompt_version,
        "prompt_fingerprint": prompt_fingerprint,
    }


def _validate_stage(stage: str) -> None:
    if stage not in PROMPT_STAGES:
        raise ValueError(
            f"Unsupported prompt stage '{stage}'. Expected one of: {', '.join(PROMPT_STAGES)}"
        )


def _template_filename(stage: str, *, artifact_type: str) -> str:
    if artifact_type == "cv":
        return f"cv_{stage}.md"
    return f"{stage}.md"
