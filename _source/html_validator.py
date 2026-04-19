#!/usr/bin/env python3
"""Validate generated HTML files and fail on parse errors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import html5lib


def collect_generated_html_files(site_root: Path, html_roots: tuple[str, ...]) -> list[Path]:
    """Collect generated HTML files from language roots and root index."""
    html_files: set[Path] = set()

    root_index = site_root / "index.html"
    if root_index.exists() and root_index.is_file():
        html_files.add(root_index)

    for root in html_roots:
        language_root = site_root / root
        if not language_root.exists() or not language_root.is_dir():
            continue
        html_files.update(language_root.rglob("*.html"))

    return sorted(html_files)


def validate_html_file(html_file: Path) -> list[str]:
    """Return html5lib parse diagnostics for one HTML file."""
    parser = html5lib.HTMLParser(strict=False)
    parser.parse(html_file.read_text(encoding="utf-8"))

    diagnostics: list[str] = []
    for (line, column), code, data in parser.errors:
        details = ""
        if data:
            detail_parts = [f"{key}={value}" for key, value in sorted(data.items())]
            details = f" ({', '.join(detail_parts)})"
        diagnostics.append(f"line {line}, col {column}: {code}{details}")
    return diagnostics


def validate_generated_html(
    site_root: Path, html_roots: tuple[str, ...] = ("en", "pt")
) -> list[str]:
    """Validate generated HTML files and return diagnostics."""
    html_files = collect_generated_html_files(site_root, html_roots)
    if not html_files:
        roots = ", ".join(html_roots)
        return [f"No generated HTML files found under site roots: {roots}"]

    errors: list[str] = []
    for html_file in html_files:
        file_errors = validate_html_file(html_file)
        if not file_errors:
            continue

        rel_path = html_file.relative_to(site_root).as_posix()
        for diagnostic in file_errors:
            errors.append(f"{rel_path}: {diagnostic}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated HTML files")
    parser.add_argument(
        "--site-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Repository root containing generated site directories",
    )
    parser.add_argument(
        "--roots",
        nargs="+",
        default=["en", "pt"],
        help="Site subdirectories to scan for generated HTML",
    )
    args = parser.parse_args()

    site_root = Path(args.site_root).resolve()
    errors = validate_generated_html(site_root, tuple(args.roots))

    if errors:
        print(f"HTML validation failed ({len(errors)} issue(s)):")
        for error in errors:
            print(f" - {error}")
        return 1

    print("HTML validation passed: no parse errors found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
