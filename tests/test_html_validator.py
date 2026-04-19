"""Tests for generated-site HTML validation."""

from pathlib import Path

import sys


_SOURCE = Path(__file__).resolve().parent.parent / "_source"
sys.path.insert(0, str(_SOURCE))

from html_validator import validate_generated_html  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_validate_generated_html_accepts_valid_html(tmp_path: Path):
    _write(
        tmp_path / "en" / "index.html",
        "<!doctype html><html><head><title>Home</title></head><body><p>OK</p></body></html>",
    )

    errors = validate_generated_html(tmp_path, ("en",))

    assert errors == []


def test_validate_generated_html_reports_malformed_html(tmp_path: Path):
    _write(
        tmp_path / "en" / "index.html",
        "<!doctype html><html><head><title>Broken</title></head><body></div></body></html>",
    )

    errors = validate_generated_html(tmp_path, ("en",))

    assert len(errors) >= 1
    assert any("en/index.html" in error for error in errors)


def test_validate_generated_html_reports_when_no_html_found(tmp_path: Path):
    errors = validate_generated_html(tmp_path, ("en", "pt"))

    assert len(errors) == 1
    assert "No generated HTML files found" in errors[0]
