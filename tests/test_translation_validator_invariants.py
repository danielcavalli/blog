"""Tests for validate_translation invariant-heading behavior."""

import importlib
import os
import sys
import types


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


_google_stub = sys.modules.get("google", types.ModuleType("google"))
_genai_stub = sys.modules.get("google.genai", types.ModuleType("google.genai"))
_genai_types_stub = types.SimpleNamespace(HttpOptions=object)
setattr(_genai_stub, "types", _genai_types_stub)
setattr(_genai_stub, "Client", object)
sys.modules["google"] = _google_stub
sys.modules["google.genai"] = _genai_stub
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]

sys.modules.pop("translator", None)
translator = importlib.import_module("translator")


def test_validate_translation_allows_known_invariant_headings_without_errors():
    original = "\n\n".join(
        [
            "Translated body paragraph about context engineering.",
            "**Fontes:**",
            "## TL;DR",
            "## View Transitions API",
        ]
    )
    translated = "\n\n".join(
        [
            "Paragrafo traduzido sobre engenharia de contexto.",
            "**Fontes:**",
            "## TL;DR",
            "## View Transitions API",
        ]
    )

    is_valid, issues = translator.validate_translation(original, translated)

    assert is_valid is True
    assert issues == []


def test_validate_translation_still_flags_non_invariant_identical_block():
    original = "\n\n".join(
        [
            "Paragraph one translated to Portuguese.",
            "This exact English sentence should not pass unchanged.",
        ]
    )
    translated = "\n\n".join(
        [
            "Paragrafo um traduzido para portugues.",
            "This exact English sentence should not pass unchanged.",
        ]
    )

    is_valid, issues = translator.validate_translation(original, translated)

    assert is_valid is False
    assert any("appears untranslated" in issue for issue in issues)


def test_validate_translation_pt_br_to_en_us_accepts_translated_content():
    original = "\n\n".join(
        [
            "Este sistema reduz latencia em picos de trafego.",
            "Tambem melhora a confiabilidade da plataforma.",
        ]
    )
    translated = "\n\n".join(
        [
            "This system reduces latency during traffic spikes.",
            "It also improves platform reliability.",
        ]
    )

    is_valid, issues = translator.validate_translation(
        original,
        translated,
        source_locale="pt-br",
        target_locale="en-us",
    )

    assert is_valid is True
    assert issues == []


def test_validate_translation_pt_br_to_en_us_flags_untranslated_block():
    original = "\n\n".join(
        [
            "Este paragrafo deveria ser traduzido para ingles.",
            "Ele nao pode permanecer em portugues.",
        ]
    )
    translated = original

    is_valid, issues = translator.validate_translation(
        original,
        translated,
        source_locale="pt-br",
        target_locale="en-us",
    )

    assert is_valid is False
    assert any("appears untranslated" in issue for issue in issues)
