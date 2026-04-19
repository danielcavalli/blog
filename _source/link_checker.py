#!/usr/bin/env python3
"""Check generated HTML files for broken internal links."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel", "javascript", "data"}


@dataclass
class HtmlFileData:
    """Collected metadata from an HTML file."""

    ids: set[str] = field(default_factory=set)
    hrefs: list[str] = field(default_factory=list)


class _HtmlCollector(HTMLParser):
    """Collect anchor href values and all element ids."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        element_id = attrs_dict.get("id")
        if element_id:
            self.ids.add(element_id)

        if tag == "a":
            href = attrs_dict.get("href")
            if href:
                self.hrefs.append(href)


def _is_external_link(href: str) -> bool:
    parsed = urlsplit(href)
    if parsed.scheme:
        return parsed.scheme.lower() in EXTERNAL_SCHEMES or bool(parsed.netloc)
    if parsed.netloc:
        return True
    return False


def _collect_html_files(site_root: Path, html_roots: tuple[str, ...]) -> list[Path]:
    html_files: set[Path] = set()

    root_index = site_root / "index.html"
    if root_index.exists() and root_index.is_file():
        html_files.add(root_index)

    for root in html_roots:
        base = site_root / root
        if not base.exists() or not base.is_dir():
            continue
        html_files.update(base.rglob("*.html"))
    return sorted(html_files)


def _collect_file_data(html_files: list[Path]) -> dict[Path, HtmlFileData]:
    data_by_file: dict[Path, HtmlFileData] = {}
    for html_file in html_files:
        parser = _HtmlCollector()
        parser.feed(html_file.read_text(encoding="utf-8"))
        data_by_file[html_file] = HtmlFileData(ids=parser.ids, hrefs=parser.hrefs)
    return data_by_file


def _resolve_candidate(site_root: Path, source_file: Path, href: str) -> tuple[Path | None, str]:
    parsed = urlsplit(href)
    path = parsed.path
    fragment = parsed.fragment

    if not path:
        target = source_file
    elif path.startswith("/"):
        target = site_root / path.lstrip("/")
    else:
        target = source_file.parent / path

    normalized = Path(os.path.normpath(str(target)))

    try:
        normalized.relative_to(site_root)
    except ValueError:
        return None, fragment

    if normalized.is_dir():
        normalized = normalized / "index.html"

    if not normalized.exists() and normalized.suffix == "":
        html_candidate = normalized.with_suffix(".html")
        index_candidate = normalized / "index.html"
        if html_candidate.exists():
            normalized = html_candidate
        elif index_candidate.exists():
            normalized = index_candidate

    return normalized, fragment


def check_internal_links(
    site_root: Path,
    html_roots: tuple[str, ...] = ("en", "pt"),
) -> list[str]:
    """Return a list of broken internal link diagnostics."""
    html_files = _collect_html_files(site_root, html_roots)
    if not html_files:
        roots = ", ".join(html_roots)
        return [f"No HTML files found under site roots: {roots}"]

    data_by_file = _collect_file_data(html_files)
    errors: list[str] = []

    for source_file, file_data in data_by_file.items():
        for href in file_data.hrefs:
            stripped = href.strip()
            if not stripped or stripped == "#":
                continue
            if _is_external_link(stripped):
                continue

            target_file, fragment = _resolve_candidate(site_root, source_file, stripped)
            source_rel = source_file.relative_to(site_root).as_posix()

            if target_file is None:
                errors.append(f"{source_rel}: internal link escapes site root: {stripped}")
                continue

            if not target_file.exists():
                target_rel = target_file.relative_to(site_root).as_posix()
                errors.append(
                    f"{source_rel}: broken internal link '{stripped}' (missing {target_rel})"
                )
                continue

            if fragment:
                target_data = data_by_file.get(target_file)
                if target_data is None:
                    parser = _HtmlCollector()
                    parser.feed(target_file.read_text(encoding="utf-8"))
                    target_data = HtmlFileData(ids=parser.ids, hrefs=parser.hrefs)
                    data_by_file[target_file] = target_data

                if fragment not in target_data.ids:
                    target_rel = target_file.relative_to(site_root).as_posix()
                    errors.append(f"{source_rel}: broken fragment '#{fragment}' in {target_rel}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated site for broken internal links")
    parser.add_argument(
        "--site-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Repository root containing generated site directories",
    )
    parser.add_argument(
        "--roots",
        nargs="+",
        default=["en", "pt"],
        help="Site subdirectories to scan for HTML files",
    )
    args = parser.parse_args()

    site_root = Path(args.site_root).resolve()
    errors = check_internal_links(site_root, tuple(args.roots))

    if errors:
        print(f"Internal link check failed ({len(errors)} issue(s)):")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Internal link check passed: no broken internal links found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
