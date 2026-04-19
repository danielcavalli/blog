"""Tests for generated-site internal link checking."""

from pathlib import Path

import sys


_SOURCE = Path(__file__).resolve().parent.parent / "_source"
sys.path.insert(0, str(_SOURCE))

from link_checker import check_internal_links  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_check_internal_links_accepts_valid_internal_targets(tmp_path: Path):
    _write(
        tmp_path / "en" / "index.html",
        '<html><body><a href="/en/about.html">About</a></body></html>',
    )
    _write(
        tmp_path / "en" / "about.html",
        '<html><body><h1 id="top">About</h1><a href="#top">Top</a></body></html>',
    )

    errors = check_internal_links(tmp_path, ("en",))

    assert errors == []


def test_check_internal_links_reports_missing_target_file(tmp_path: Path):
    _write(
        tmp_path / "en" / "index.html",
        '<html><body><a href="/en/missing.html">Missing</a></body></html>',
    )

    errors = check_internal_links(tmp_path, ("en",))

    assert len(errors) == 1
    assert "missing en/missing.html" in errors[0]


def test_check_internal_links_reports_missing_fragment(tmp_path: Path):
    _write(
        tmp_path / "en" / "index.html",
        '<html><body><a href="/en/about.html#details">Details</a></body></html>',
    )
    _write(
        tmp_path / "en" / "about.html",
        "<html><body><h1>About</h1></body></html>",
    )

    errors = check_internal_links(tmp_path, ("en",))

    assert len(errors) == 1
    assert "broken fragment '#details'" in errors[0]


def test_check_internal_links_ignores_external_links(tmp_path: Path):
    _write(
        tmp_path / "en" / "index.html",
        (
            '<html><body><a href="https://example.com/x">x</a>'
            '<a href="mailto:test@example.com">mail</a></body></html>'
        ),
    )

    errors = check_internal_links(tmp_path, ("en",))

    assert errors == []


def test_check_internal_links_reports_root_escape(tmp_path: Path):
    _write(
        tmp_path / "en" / "index.html",
        '<html><body><a href="../../secret.txt">Bad</a></body></html>',
    )

    errors = check_internal_links(tmp_path, ("en",))

    assert len(errors) == 1
    assert "escapes site root" in errors[0]


def test_check_internal_links_reports_when_no_html_found(tmp_path: Path):
    errors = check_internal_links(tmp_path, ("en", "pt"))

    assert len(errors) == 1
    assert "No HTML files found" in errors[0]
