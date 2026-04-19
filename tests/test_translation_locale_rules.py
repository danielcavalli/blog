"""Locale-rule regression tests for translation_v2."""

from __future__ import annotations

import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.locale_rules import get_default_locale_rules  # noqa: E402


def test_en_us_to_pt_br_locale_rules_include_localization_brief_and_correct_orthography():
    rules = get_default_locale_rules(source_locale="en-us", target_locale="pt-br")

    glossary = {
        entry["source"]: entry["target"]
        for entry in rules["glossary"]
        if isinstance(entry, dict)
    }

    assert glossary["throughput"] == "vazão"
    assert glossary["latency"] == "latência"
    assert glossary["cache invalidation"] == "invalidação de cache"
    assert "publishable Brazilian Portuguese technical-editorial prose" in rules["localization_brief"]
    assert any(
        "Treat English borrowings as a policy problem" in item
        for item in rules["borrowing_conventions"]
    )
    assert "travessão" in " ".join(rules["punctuation_conventions"]).lower()
    assert "connective" in " ".join(rules["discourse_conventions"]).lower()
    review_checks = " ".join(rules["review_checks"]).lower()
    assert "calques" in review_checks
    assert "native brazilian technical writing" in review_checks


def test_pt_br_to_en_us_locale_rules_include_reverse_localization_brief():
    rules = get_default_locale_rules(source_locale="pt-br", target_locale="en-us")

    assert "publishable US English technical-editorial prose" in rules["localization_brief"]
    assert "Portuguese-influenced syntax" in " ".join(rules["review_checks"])
