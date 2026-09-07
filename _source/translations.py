#!/usr/bin/env python3
"""Manage translation content without rendering or publishing the site."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
from pathlib import Path

from config import LANGUAGES
from paths import PROJECT_ROOT, POSTS_DIR, TRANSLATION_CACHE
from content_loader import parse_markdown_post
from cv_parser import load_cv_data
from translation_v2.accepted import (
    AcceptedTranslations,
    digest,
    matching_legacy_entry,
    source_identity,
)
from translation_v2.durable import validate_artifact
from translation_v2.errors import TranslationV2Error
from translation_v2.storage import file_lock, read_json
from translation_v2.console import shutdown_console


def discover_artifacts() -> list[dict]:
    artifacts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        post = parse_markdown_post(path)
        source_locale = post["lang"].lower()
        frontmatter = {k: post[k] for k in ("title", "excerpt", "tags")}
        if post["content_type"] == "presentation":
            frontmatter["content_type"] = "presentation"
        artifacts.append(
            {
                "source": source_identity(
                    slug=post["slug"],
                    source_text=post["raw_content"],
                    frontmatter=frontmatter,
                    source_locale=source_locale,
                    target_locale="en-us" if source_locale.startswith("pt") else "pt-br",
                    artifact_type=post["content_type"],
                ),
                "attach_path": str(path),
            }
        )
    about = LANGUAGES["en"]["about"]
    paragraphs = sorted(
        (k for k in about if k.startswith("p") and k[1:].isdigit()), key=lambda k: int(k[1:])
    )
    artifacts.append(
        {
            "source": source_identity(
                slug="about",
                artifact_type="about",
                source_locale="en-us",
                target_locale="pt-br",
                source_text="\n\n".join(
                    [f"# {about['title'].strip()}"] + [about[k].strip() for k in paragraphs]
                ),
                frontmatter={"title": about["title"], "excerpt": "", "tags": []},
            ),
            "attach_path": str(PROJECT_ROOT / "_source" / "config.py"),
        }
    )
    cv = load_cv_data()
    if cv is None:
        raise RuntimeError("CV source is missing")
    artifacts.append(
        {
            "source": source_identity(
                slug="cv",
                artifact_type="cv",
                source_locale="en-us",
                target_locale="pt-br",
                source_text=json.dumps(cv, ensure_ascii=False, sort_keys=True, indent=2),
                frontmatter={"title": cv["name"], "excerpt": cv["tagline"], "tags": ["cv"]},
            ),
            "attach_path": str(PROJECT_ROOT / "cv_data.yaml"),
            "do_not_translate_entities": [
                "Nubank",
                "PicPay",
                "M4U",
                "Oi S.A",
                "frete.com",
                "Kubeflow",
                "Dagster",
                "Argo",
                "Tekton",
                "Pulumi",
                "AWS",
                "SageMaker",
                "GPU",
                "CUDA",
                "MLOps",
            ],
        }
    )
    return artifacts


def select_artifacts(artifacts: list[dict], selectors: list[str]) -> list[dict]:
    if not selectors:
        return artifacts
    selected = []
    for selector in selectors:
        matches = [
            a
            for a in artifacts
            if selector == a["source"]["slug"] or Path(selector).stem == Path(a["attach_path"]).stem
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one artifact for {selector}, found {len(matches)}")
        if matches[0] not in selected:
            selected.append(matches[0])
    return selected


def recover_previous_source(cache: dict, source: dict) -> tuple[dict, tuple] | None:
    """Recover an older accepted revision from its recorded source, never HTML."""
    runs = TRANSLATION_CACHE.parent / "translation-runs"
    events = sorted(
        runs.glob(f"*/posts/{source['slug']}/trigger/event.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in events:
        event = read_json(path)
        if not event or (event.get("slug"), event.get("target_locale")) != (
            source["slug"],
            source["target_locale"],
        ):
            continue
        previous = source_identity(
            slug=event["slug"],
            source_text=event["source_text"],
            source_locale=event["source_locale"],
            target_locale=event["target_locale"],
            frontmatter=event["frontmatter"],
            artifact_type=source["artifact_type"],
        )
        match = matching_legacy_entry(cache, previous)
        if match:
            return previous, match
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "import-cache", "update", "diff", "accept"))
    parser.add_argument("artifacts", nargs="*", help="Post slugs, about, or cv; defaults to all")
    parser.add_argument(
        "--refresh", action="store_true", help="Reassess already-current translations"
    )
    parser.add_argument("--model", help="Translation/revision model for this explicit update")
    parser.add_argument(
        "--candidate-dir", type=Path, help="Isolated candidate store; required for accept"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Also enforce overlap/length heuristics"
    )
    parser.add_argument(
        "--json", action="store_true", help="Structured status for CLI integrations"
    )
    args = parser.parse_args(argv)
    if args.json and args.command != "status":
        parser.error("--json currently applies to status")
    if args.command in {"accept", "diff"} and args.candidate_dir is None:
        parser.error(f"{args.command} requires --candidate-dir")
    if (args.model or args.refresh) and args.command != "update":
        parser.error("--model and --refresh apply only to update")
    root = PROJECT_ROOT / "_source" / "translations"
    if args.candidate_dir and args.candidate_dir.resolve() == root.resolve():
        parser.error("Candidate directory must be separate from accepted translations")
    try:
        artifacts = select_artifacts(discover_artifacts(), args.artifacts)
        if args.candidate_dir and args.command == "update":
            if not args.candidate_dir.exists():
                if root.exists():
                    shutil.copytree(
                        root, args.candidate_dir, ignore=shutil.ignore_patterns(".locks")
                    )
                else:
                    args.candidate_dir.mkdir(parents=True)
        store = AcceptedTranslations(args.candidate_dir or root)
        runtime = None
        if args.command == "update":
            from translation_v2.orchestrator import TranslationV2PostOrchestrator

            if args.model:
                os.environ["TRANSLATION_V2_TRANSLATION_MODEL"] = args.model
                os.environ["TRANSLATION_V2_REVISION_MODEL"] = args.model
            runtime = TranslationV2PostOrchestrator(
                strict_validation=args.strict,
                cache_dir=TRANSLATION_CACHE.parent,
                accepted_path=store.root,
                refresh=args.refresh,
            )
        cache = read_json(TRANSLATION_CACHE) if args.command == "import-cache" else None
        missing = 0
        status_rows = []
        for artifact in artifacts:
            source = artifact["source"]
            current = store.current(source)
            label = f"{source['artifact_type']}:{source['slug']}:{source['target_locale']}"
            if args.command == "status":
                state = (
                    "missing"
                    if current is None
                    else ("current" if current["source_hash"] == digest(source) else "outdated")
                )
                missing += state != "current"
                status_rows.append(
                    {
                        "state": state,
                        "artifact_type": source["artifact_type"],
                        "slug": source["slug"],
                        "target_locale": source["target_locale"],
                    }
                )
                if not args.json:
                    print(f"{state:8} {label}")
            elif args.command == "import-cache":
                if current is not None:
                    print(f"preserved {label}")
                    continue
                match = matching_legacy_entry(cache or {}, source)
                if match is None:
                    previous = recover_previous_source(cache or {}, source)
                    if previous is None:
                        print(f"unmatched {label}")
                        missing += 1
                        continue
                    source, match = previous
                    print(f"recovered previous source for {label}; an update is still required")
                key, entry = match
                validate_artifact(source, entry["translation"], strict=args.strict)
                store.accept(
                    source,
                    entry["translation"],
                    {
                        **entry.get("metadata", {}),
                        "imported_from": "translation-cache-v2",
                        "legacy_cache_key": key,
                        "provider": entry["provider"],
                        "translation_model": entry["model"],
                        "prompt_version": entry["prompt_version"],
                    },
                    expected_revision=None,
                )
                print(f"imported  {label}")
            elif args.command == "diff":
                accepted = AcceptedTranslations(root).current(source)

                def text(record):
                    if not record:
                        return []
                    translation = dict(record["translation"])
                    content = translation.pop("content", None)
                    rendered = json.dumps(translation, ensure_ascii=False, indent=2) + "\n"
                    if content is not None:
                        rendered += "\n" + content + "\n"
                    return rendered.splitlines(keepends=True)

                print(f"\n{label}")
                print(
                    "".join(
                        difflib.unified_diff(
                            text(accepted),
                            text(current),
                            fromfile="accepted",
                            tofile="candidate",
                        )
                    )
                )
            elif args.command == "accept":
                if current is None or current["source_hash"] != digest(source):
                    raise RuntimeError(f"Candidate missing or outdated: {label}")
                validate_artifact(source, current["translation"], strict=args.strict)
                destination = AcceptedTranslations(root)
                existing = destination.current(source)
                if existing == current:
                    print(f"unchanged {label}")
                    continue
                destination.promote(store, source)
                print(f"accepted  {label}")
            else:
                assert runtime is not None
                with file_lock(store.root / ".locks" / f"{digest(source)}.lock", blocking=False):
                    runtime.translate_artifact_if_needed(
                        slug=source["slug"],
                        source_text=source["text"],
                        source_locale=source["source_locale"],
                        target_locale=source["target_locale"],
                        artifact_type=source["artifact_type"],
                        frontmatter=source["frontmatter"],
                        attach_path=artifact["attach_path"],
                        do_not_translate_entities=artifact.get("do_not_translate_entities"),
                    )
                print(f"accepted  {label}")
        if args.json:
            print(
                json.dumps(
                    {"schema_version": "1", "ready": missing == 0, "artifacts": status_rows},
                    ensure_ascii=False,
                )
            )
        return 1 if missing else 0
    except (RuntimeError, ValueError, OSError, TranslationV2Error) as exc:
        print(f"Translation operation failed: {exc}")
        return 1
    except KeyboardInterrupt:
        print("Interrupted; completed stages can be resumed and accepted work is preserved.")
        return 130
    finally:
        shutdown_console()


if __name__ == "__main__":
    raise SystemExit(main())
