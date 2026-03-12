"""Unit tests for bidirectional translation routing/prompt behavior."""

import os
import sys
import types
import importlib

# Make _source importable without installing package.
_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

# Stub optional runtime deps before importing translator.
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


class TestTranslatorDirection:
    def test_translation_prompt_pt_br_to_en_us_has_english_rules(self):
        t = object.__new__(translator.MultiAgentTranslator)
        prompt = t._build_translation_prompt(  # type: ignore[attr-defined]
            {"title": "Titulo", "excerpt": "Resumo", "tags": ["rede"]},
            "conteudo",
            source_locale="pt-br",
            target_locale="en-us",
        )
        assert "from pt-br to en-us" in prompt
        assert "Source locale: pt-br" in prompt
        assert "Target locale: en-us" in prompt
        assert "to English" in prompt
        assert "to Portuguese" not in prompt

    def test_translation_prompt_en_us_to_pt_br_has_portuguese_rules(self):
        t = object.__new__(translator.MultiAgentTranslator)
        prompt = t._build_translation_prompt(  # type: ignore[attr-defined]
            {"title": "Title", "excerpt": "Summary", "tags": ["network"]},
            "content",
            source_locale="en-us",
            target_locale="pt-br",
        )
        assert "from en-us to pt-br" in prompt
        assert "Source locale: en-us" in prompt
        assert "Target locale: pt-br" in prompt
        assert "to Portuguese" in prompt

    def test_critique_and_refinement_prompts_include_direction(self):
        t = object.__new__(translator.MultiAgentTranslator)
        critique = t._build_critique_prompt(  # type: ignore[attr-defined]
            {"title": "Titulo", "excerpt": "Resumo"},
            "conteudo",
            {"title": "Title", "excerpt": "Summary", "content": "content"},
            source_locale="pt-br",
            target_locale="en-us",
        )
        refine = t._build_refinement_prompt(  # type: ignore[attr-defined]
            {"title": "Titulo", "excerpt": "Resumo"},
            "conteudo",
            {
                "title": "Title",
                "excerpt": "Summary",
                "tags": ["network"],
                "content": "content",
            },
            "fix tone",
            source_locale="pt-br",
            target_locale="en-us",
        )
        assert "Source locale: pt-br" in critique
        assert "Target locale: en-us" in critique
        assert "natural for en-us" in critique
        assert "Source locale: pt-br" in refine
        assert "Target locale: en-us" in refine
        assert "Do not drift from the source meaning in pt-br" in refine

    def test_translate_if_needed_pt_br_to_en_us_updates_lang(self):
        t = object.__new__(translator.MultiAgentTranslator)

        def fake_translate_post(*args, **kwargs):
            return {
                "title": "English Title",
                "excerpt": "English excerpt",
                "tags": ["network"],
                "content": "Translated **content**",
            }

        t.translate_post = fake_translate_post  # type: ignore[attr-defined]

        post = {
            "slug": "meu-post",
            "title": "Titulo",
            "excerpt": "Resumo",
            "tags": ["rede"],
            "content": "<p>Conteudo</p>",
            "raw_content": "Conteudo",
            "lang": "pt-br",
        }

        translated = t.translate_if_needed(post, target_locale="en-us")
        assert translated is not None
        assert translated["lang"] == "en-us"
        assert translated["title"] == "English Title"
        assert translated["raw_content"] == "Translated **content**"
        assert "<strong>content</strong>" in translated["content"]
