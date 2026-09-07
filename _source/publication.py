"""Recoverable publication of a staged file set, including focused builds."""

from __future__ import annotations

import shutil
import tempfile
import os
from pathlib import Path

from translation_v2.storage import atomic_json, read_json, sync_directory


def validate_staged(root: Path, staging: Path, *, full: bool, preserve_static: bool) -> None:
    """Check the complete proposed site, including untouched focused-build files."""
    from html_validator import validate_generated_html
    from link_checker import check_internal_links

    with tempfile.TemporaryDirectory(prefix="blog-validate-") as directory:
        view = Path(directory)
        for name in ("static", "en", "pt"):
            if (root / name).exists() and (name == "static" or not full):
                shutil.copytree(root / name, view / name)
        for name in ("index.html", "sitemap.xml"):
            if not full and (root / name).exists():
                shutil.copy2(root / name, view / name)
        if full and preserve_static:
            for language in ("en", "pt"):
                for name in ("about.html", "cv.html"):
                    source = root / language / name
                    if source.exists():
                        (view / language).mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, view / language / name)
        shutil.copytree(staging, view, dirs_exist_ok=True)
        errors = validate_generated_html(view) + check_internal_links(view)
        if errors:
            raise RuntimeError("Staged site validation failed:\n" + "\n".join(errors))


def recover_publication(root: Path) -> None:
    journal_path = root / "_cache" / "publication.json"
    journal = read_json(journal_path)
    if journal is None:
        return
    backup = root / "_cache" / "publication-backup"
    if journal["state"] != "committed":
        for item in journal["files"]:
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError("Unsafe publication journal path")
            target = root / relative
            if item["existed"]:
                original = backup / relative
                if not original.is_file():
                    raise RuntimeError(f"Publication backup missing: {original}")
                target.parent.mkdir(parents=True, exist_ok=True)
                # Keep the backup intact until the entire rollback succeeds.
                temporary = target.with_name(f".{target.name}.rollback")
                shutil.copy2(original, temporary)
                with temporary.open("rb") as handle:
                    os.fsync(handle.fileno())
                temporary.replace(target)
            else:
                target.unlink(missing_ok=True)
            if target.parent.exists():
                sync_directory(target.parent)
    journal_path.unlink()
    sync_directory(journal_path.parent)
    shutil.rmtree(backup, ignore_errors=True)


def publish_staged(
    root: Path,
    staging: Path,
    *,
    full: bool,
    language_dirs: list[str],
    preserve_static: bool = False,
) -> None:
    """Replace touched files only; restore all of them on errors or interruption.

    Individual replacements are atomic. A journal recovers process crashes on
    the next build. GitHub Pages receives the completed tree via its git commit.
    """
    recover_publication(root)
    staged = {p.relative_to(staging) for p in staging.rglob("*") if p.is_file()}
    removed: set[Path] = set()
    if full:
        for directory in language_dirs:
            for path in (root / directory).rglob("*.html"):
                relative = path.relative_to(root)
                if preserve_static and relative.name in {"about.html", "cv.html"}:
                    continue
                if relative not in staged:
                    removed.add(relative)
    touched = sorted(staged | removed)
    backup = root / "_cache" / "publication-backup"
    if backup.exists():
        shutil.rmtree(backup)
    records = []
    for relative in touched:
        target = root / relative
        existed = target.is_file()
        records.append({"path": str(relative), "existed": existed})
        if existed:
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
            with saved.open("rb") as handle:
                os.fsync(handle.fileno())
            sync_directory(saved.parent)
    if backup.exists():
        for directory in sorted((p for p in backup.rglob("*") if p.is_dir()), reverse=True):
            sync_directory(directory)
        sync_directory(backup)
        sync_directory(backup.parent)
    journal = {"state": "prepared", "files": records}
    journal_path = root / "_cache" / "publication.json"
    atomic_json(journal_path, journal)
    try:
        for relative in touched:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative in staged:
                with (staging / relative).open("rb") as handle:
                    os.fsync(handle.fileno())
                (staging / relative).replace(target)
            else:
                target.unlink(missing_ok=True)
            sync_directory(target.parent)
        atomic_json(journal_path, {**journal, "state": "committed"})
    except BaseException:
        recover_publication(root)
        raise
    recover_publication(root)
    shutil.rmtree(staging)
