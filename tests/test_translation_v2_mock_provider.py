"""Deterministic one-file tests for translation_v2 mock provider.

Run only this fast suite:
    uv run --extra dev pytest tests/test_translation_v2_mock_provider.py -q
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.contracts import TranslationRequest  # noqa: E402
from translation_v2.mock_provider import DeterministicMockTranslationProvider  # noqa: E402


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "translation_v2"
MARKDOWN_FIXTURE_PATH = FIXTURES_DIR / "representative_post.md"
EXPECTED_FIXTURE_PATH = FIXTURES_DIR / "representative_post_expected.json"


def _load_expected_post_case() -> dict:
    fixture = json.loads(EXPECTED_FIXTURE_PATH.read_text(encoding="utf-8"))
    return fixture["posts"]["deterministic-mock-post"]


def _build_request() -> TranslationRequest:
    markdown_source = MARKDOWN_FIXTURE_PATH.read_text(encoding="utf-8")
    return TranslationRequest(
        run_id="mock-provider-run-1",
        source_locale="en-us",
        target_locale="pt-br",
        source_text=markdown_source,
        prompt_version="mock-fixture-v1",
        metadata={"slug": "deterministic-mock-post"},
    )


def test_mock_provider_round_trip_matches_expected_sections():
    expected = _load_expected_post_case()
    provider = DeterministicMockTranslationProvider.from_fixture_file(
        EXPECTED_FIXTURE_PATH
    )
    request = _build_request()

    translated = provider.translate(request)
    critiqued = provider.critique(request, translated.payload)
    refined = provider.refine(request, translated.payload, critiqued.payload)

    assert translated.stage == "translate"
    assert critiqued.stage == "critique"
    assert refined.stage == "refine"

    assert translated.payload.title == expected["translated"]["title"]
    assert translated.payload.excerpt == expected["translated"]["excerpt"]
    assert translated.payload.tags == expected["translated"]["tags"]
    assert "## Contexto" in translated.payload.content

    assert critiqued.payload.score == float(expected["critique"]["score"])
    assert (
        critiqued.payload.needs_refinement is expected["critique"]["needs_refinement"]
    )
    assert critiqued.payload.findings == expected["critique"]["findings"]

    assert refined.payload.title == expected["refined"]["title"]
    assert refined.payload.tags == expected["refined"]["tags"]
    assert refined.payload.applied_feedback == expected["refined"]["applied_feedback"]


def test_mock_provider_falls_back_to_only_fixture_without_slug():
    provider = DeterministicMockTranslationProvider.from_fixture_file(
        EXPECTED_FIXTURE_PATH
    )
    markdown_source = MARKDOWN_FIXTURE_PATH.read_text(encoding="utf-8")
    request = TranslationRequest(
        run_id="mock-provider-run-2",
        source_locale="en-us",
        target_locale="pt-br",
        source_text=markdown_source,
        prompt_version="mock-fixture-v1",
    )

    translated = provider.translate(request)

    assert translated.payload.title.startswith("Por que fixtures")


def test_mock_provider_requires_no_network_calls(monkeypatch):
    provider = DeterministicMockTranslationProvider.from_fixture_file(
        EXPECTED_FIXTURE_PATH
    )
    request = _build_request()

    def _fail_network(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("network call attempted")

    monkeypatch.setattr(socket, "create_connection", _fail_network)
    monkeypatch.setattr(socket, "socket", _fail_network)

    translated = provider.translate(request)
    critiqued = provider.critique(request, translated.payload)
    refined = provider.refine(request, translated.payload, critiqued.payload)

    assert translated.model == "mock/deterministic-translation-v2"
    assert critiqued.model == "mock/deterministic-translation-v2"
    assert refined.model == "mock/deterministic-translation-v2"
