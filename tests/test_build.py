"""Unit tests for pure helper functions in _source/build.py.

Run with:
    python3 -m pytest tests/ -v
"""

import json
import sys
import os
import types
from unittest import mock

# Make _source importable without installing the package
_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

# Stub heavy optional dependencies before importing build so that tests can run
# without a Gemini API key or google-genai installed.
_google_stub = types.ModuleType("google")
_genai_stub = types.ModuleType("google.genai")
sys.modules.setdefault("google", _google_stub)
sys.modules.setdefault("google.genai", _genai_stub)
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
# Provide a no-op load_dotenv so translator.py doesn't crash at import time.
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]

# translator.MultiAgentTranslator and validate_translation are imported at build
# module level; stub them out.
_translator_stub = types.ModuleType("translator")
_translator_stub.MultiAgentTranslator = mock.MagicMock()  # type: ignore[attr-defined]
_translator_stub.validate_translation = mock.MagicMock(return_value=(True, []))  # type: ignore[attr-defined]
sys.modules["translator"] = _translator_stub

import build


# ---------------------------------------------------------------------------
# tag_to_slug
# ---------------------------------------------------------------------------


class TestTagToSlug:
    def test_single_word(self):
        assert build.tag_to_slug("web") == "web"

    def test_two_words_with_space(self):
        assert build.tag_to_slug("home server") == "home-server"

    def test_mixed_case(self):
        assert build.tag_to_slug("View Transitions API") == "view-transitions-api"

    def test_already_lowercase(self):
        assert build.tag_to_slug("mlops") == "mlops"

    def test_special_characters_collapsed(self):
        # Multiple non-alphanumeric chars collapse to a single hyphen
        assert build.tag_to_slug("C++ programming") == "c-programming"

    def test_leading_trailing_stripped(self):
        assert build.tag_to_slug("  spaces  ") == "spaces"

    def test_numbers_preserved(self):
        assert build.tag_to_slug("cuda 12") == "cuda-12"

    def test_unicode_lowercased(self):
        # Non-ASCII chars become hyphens (regex [^a-z0-9])
        result = build.tag_to_slug("São Paulo")
        assert result == "s-o-paulo"

    def test_hyphen_input(self):
        assert build.tag_to_slug("machine-learning") == "machine-learning"

    def test_empty_string(self):
        # Edge case: empty string after strip should return empty
        assert build.tag_to_slug("") == ""


# ---------------------------------------------------------------------------
# calculate_reading_time
# ---------------------------------------------------------------------------


class TestCalculateReadingTime:
    def test_empty_content_is_one_minute(self):
        assert build.calculate_reading_time("") == 1

    def test_single_word_is_one_minute(self):
        assert build.calculate_reading_time("hello") == 1

    def test_exactly_200_words(self):
        content = " ".join(["word"] * 200)
        assert build.calculate_reading_time(content) == 1

    def test_201_words_rounds_to_one(self):
        content = " ".join(["word"] * 201)
        # 201/200 = 1.005, rounds to 1
        assert build.calculate_reading_time(content) == 1

    def test_400_words_is_two_minutes(self):
        content = " ".join(["word"] * 400)
        assert build.calculate_reading_time(content) == 2

    def test_1000_words_is_five_minutes(self):
        content = " ".join(["word"] * 1000)
        assert build.calculate_reading_time(content) == 5

    def test_minimum_is_one(self):
        # Even for very short content, minimum is 1
        assert build.calculate_reading_time("hi") >= 1


# ---------------------------------------------------------------------------
# format_reading_time
# ---------------------------------------------------------------------------


class TestFormatReadingTime:
    def test_english_singular(self):
        result = build.format_reading_time(1, "en")
        assert result == "1 min read"

    def test_english_plural(self):
        result = build.format_reading_time(5, "en")
        assert result == "5 min read"

    def test_portuguese(self):
        result = build.format_reading_time(3, "pt")
        assert result == "3 min de leitura"

    def test_zero_minutes(self):
        # format_reading_time doesn't enforce minimum; just formats what it gets
        result = build.format_reading_time(0, "en")
        assert result == "0 min read"


# ---------------------------------------------------------------------------
# format_date
# ---------------------------------------------------------------------------


class TestFormatDate:
    def test_english_january(self):
        assert build.format_date("2024-01-15", "en") == "January 15, 2024"

    def test_english_december(self):
        assert build.format_date("2023-12-01", "en") == "December 01, 2023"

    def test_portuguese_january(self):
        assert build.format_date("2024-01-15", "pt") == "15 de Janeiro de 2024"

    def test_portuguese_july(self):
        assert build.format_date("2024-07-04", "pt") == "04 de Julho de 2024"

    def test_invalid_date_returns_original(self):
        assert build.format_date("not-a-date", "en") == "not-a-date"

    def test_none_returns_string_none(self):
        assert build.format_date(None, "en") == "None"

    def test_day_zero_padded(self):
        # Day 5 should be formatted as "05"
        result = build.format_date("2024-03-05", "en")
        assert result == "March 05, 2024"


# ---------------------------------------------------------------------------
# format_iso_date
# ---------------------------------------------------------------------------


class TestFormatIsoDate:
    def test_basic_iso(self):
        assert build.format_iso_date("2024-01-15T10:30:00") == "January 15, 2024"

    def test_date_only(self):
        # datetime.fromisoformat handles date-only strings in Python 3.7+
        assert build.format_iso_date("2024-06-20") == "June 20, 2024"

    def test_invalid_returns_original(self):
        assert build.format_iso_date("garbage") == "garbage"

    def test_none_returns_string_none(self):
        assert build.format_iso_date(None) == "None"


# ---------------------------------------------------------------------------
# calculate_content_hash
# ---------------------------------------------------------------------------


class TestCalculateContentHash:
    def test_returns_hex_string(self):
        result = build.calculate_content_hash("hello")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex chars

    def test_deterministic(self):
        assert build.calculate_content_hash("abc") == build.calculate_content_hash(
            "abc"
        )

    def test_different_content_different_hash(self):
        assert build.calculate_content_hash("abc") != build.calculate_content_hash(
            "xyz"
        )

    def test_empty_string(self):
        result = build.calculate_content_hash("")
        assert len(result) == 64


# ---------------------------------------------------------------------------
# get_lang_path
# ---------------------------------------------------------------------------


class TestGetLangPath:
    def test_english_path(self):
        result = build.get_lang_path("en", "index.html")
        assert result.endswith("en/index.html")

    def test_portuguese_path(self):
        result = build.get_lang_path("pt", "blog/post.html")
        assert result.endswith("pt/blog/post.html")

    def test_empty_path(self):
        # When path is empty, returns the language root without trailing slash
        result = build.get_lang_path("en", "")
        assert result.endswith("/en")


# ---------------------------------------------------------------------------
# get_alternate_lang
# ---------------------------------------------------------------------------


class TestGetAlternateLang:
    def test_en_returns_pt(self):
        assert build.get_alternate_lang("en") == "pt"

    def test_pt_returns_en(self):
        assert build.get_alternate_lang("pt") == "en"

    def test_unknown_returns_en(self):
        # Anything that isn't 'en' falls through to 'en'
        assert build.get_alternate_lang("fr") == "en"


# ---------------------------------------------------------------------------
# locale routing helpers
# ---------------------------------------------------------------------------


class TestLocaleRoutingHelpers:
    def test_locale_to_lang_key_en_us(self):
        assert build.locale_to_lang_key("en-us") == "en"

    def test_locale_to_lang_key_pt_br(self):
        assert build.locale_to_lang_key("pt-br") == "pt"

    def test_get_target_locale_from_en(self):
        assert build.get_target_locale("en-us") == "pt-br"

    def test_get_target_locale_from_pt(self):
        assert build.get_target_locale("pt-br") == "en-us"

    def test_pt_br_source_routes_translated_output_to_en_path(self):
        target_locale = build.get_target_locale("pt-br")
        target_lang = build.locale_to_lang_key(target_locale)
        assert target_lang == "en"
        assert build.LANG_DIRS[target_lang].name == "en"


# ---------------------------------------------------------------------------
# render_theme_toggle_svg
# ---------------------------------------------------------------------------


class TestRenderThemeToggleSvg:
    def test_returns_string(self):
        result = build.render_theme_toggle_svg()
        assert isinstance(result, str)

    def test_contains_sun_icon(self):
        result = build.render_theme_toggle_svg()
        assert 'class="sun-icon"' in result

    def test_contains_moon_icon(self):
        result = build.render_theme_toggle_svg()
        assert 'class="moon-icon"' in result

    def test_deterministic(self):
        assert build.render_theme_toggle_svg() == build.render_theme_toggle_svg()


# ---------------------------------------------------------------------------
# render_skip_link
# ---------------------------------------------------------------------------


class TestRenderSkipLink:
    def test_english(self):
        result = build.render_skip_link("en")
        assert "Skip to content" in result
        assert 'class="skip-link"' in result
        assert 'href="#main-content"' in result

    def test_portuguese(self):
        result = build.render_skip_link("pt")
        assert "Pular para o conte" in result  # "Pular para o conteúdo"


# ---------------------------------------------------------------------------
# render_jsonld_script
# ---------------------------------------------------------------------------


class TestRenderJsonldScript:
    def test_basic_dict(self):
        data = {"@type": "Person", "name": "Alice"}
        result = build.render_jsonld_script(data)
        assert result.startswith('<script type="application/ld+json">')
        assert result.endswith("</script>")
        # Parse the JSON payload back
        payload = result[len('<script type="application/ld+json">') : -len("</script>")]
        parsed = json.loads(payload)
        assert parsed == data

    def test_escapes_closing_script_tag(self):
        # A value containing "</" must not break the <script> element
        data = {"content": "foo</script>bar"}
        result = build.render_jsonld_script(data)
        assert "</script>bar" not in result  # raw closing tag must be escaped
        assert "<\\/" in result

    def test_non_ascii_preserved(self):
        data = {"name": "São Paulo"}
        result = build.render_jsonld_script(data)
        assert "São Paulo" in result  # ensure_ascii=False

    def test_list_input(self):
        data = [{"@type": "A"}, {"@type": "B"}]
        result = build.render_jsonld_script(data)
        payload = result[len('<script type="application/ld+json">') : -len("</script>")]
        parsed = json.loads(payload)
        assert len(parsed) == 2


# ---------------------------------------------------------------------------
# render_person_jsonld
# ---------------------------------------------------------------------------


class TestRenderPersonJsonld:
    def test_returns_dict(self):
        result = build.render_person_jsonld()
        assert isinstance(result, dict)

    def test_type_is_person(self):
        result = build.render_person_jsonld()
        assert result["@type"] == "Person"

    def test_has_required_fields(self):
        result = build.render_person_jsonld()
        assert "name" in result
        assert "url" in result
        assert "sameAs" in result
        assert "knowsAbout" in result

    def test_same_as_is_list(self):
        result = build.render_person_jsonld()
        assert isinstance(result["sameAs"], list)
        assert len(result["sameAs"]) > 0


# ---------------------------------------------------------------------------
# generate_lang_toggle_html
# ---------------------------------------------------------------------------


class TestGenerateLangToggleHtml:
    def test_en_toggle_links_to_pt(self):
        result = build.generate_lang_toggle_html("en", "index.html")
        assert "/pt/" in result

    def test_pt_toggle_links_to_en(self):
        result = build.generate_lang_toggle_html("pt", "index.html")
        assert "/en/" in result

    def test_en_active_class(self):
        result = build.generate_lang_toggle_html("en", "index.html")
        assert "lang-en active" in result
        # PT should NOT have active class
        assert "lang-pt active" not in result

    def test_pt_active_class(self):
        result = build.generate_lang_toggle_html("pt", "index.html")
        assert "lang-pt active" in result
        assert "lang-en active" not in result

    def test_aria_label_en(self):
        result = build.generate_lang_toggle_html("en", "index.html")
        assert "aria-label=" in result
        # Should mention switching to Portuguese
        assert "Portugu" in result  # "Português"

    def test_aria_label_pt(self):
        result = build.generate_lang_toggle_html("pt", "index.html")
        assert "aria-label=" in result
        # PT template: "Mudar para English (atualmente Português)"
        assert "Mudar para" in result

    def test_data_current_lang_attribute(self):
        result = build.generate_lang_toggle_html("en", "index.html")
        assert 'data-current-lang="en"' in result

    def test_page_path_preserved(self):
        result = build.generate_lang_toggle_html("en", "blog/my-post.html")
        assert "blog/my-post.html" in result


# ---------------------------------------------------------------------------
# render_nav
# ---------------------------------------------------------------------------


class TestRenderNav:
    def test_contains_nav_element(self):
        result = build.render_nav("en", "blog", "<a>toggle</a>")
        assert "<nav" in result

    def test_active_blog(self):
        result = build.render_nav("en", "blog", "")
        assert 'class="active"' in result

    def test_lang_toggle_injected(self):
        toggle = '<a class="lang-toggle">EN/PT</a>'
        result = build.render_nav("en", "blog", toggle)
        assert toggle in result

    def test_portuguese_labels(self):
        result = build.render_nav("pt", "about", "")
        assert "SOBRE" in result  # PT for "ABOUT"
        assert "BLOG" in result


# ---------------------------------------------------------------------------
# render_footer
# ---------------------------------------------------------------------------


class TestRenderFooter:
    def test_contains_footer_element(self):
        result = build.render_footer("en")
        assert "<footer" in result
        assert "</footer>" in result

    def test_english_copyright(self):
        result = build.render_footer("en")
        assert "All Rights Reserved" in result

    def test_portuguese_copyright(self):
        result = build.render_footer("pt")
        assert "Todos os Direitos Reservados" in result

    def test_contains_social_links(self):
        result = build.render_footer("en")
        assert 'aria-label="Twitter"' in result
        assert 'aria-label="GitHub"' in result
        assert 'aria-label="LinkedIn"' in result


# ---------------------------------------------------------------------------
# generate_post_card
# ---------------------------------------------------------------------------


class TestGeneratePostCard:
    """Test the pure post card HTML generator."""

    SAMPLE_POST = {
        "title": "Test Post Title",
        "slug": "test-post",
        "excerpt": "A short excerpt for testing.",
        "tags": ["python", "web"],
        "en_tags": ["python", "web"],
        "year": "2024",
        "month": "06",
        "date": "2024-06-15",
        "published_date": "2024-06-15",
        "updated_fm_date": "",
        "reading_time": "3 min read",
    }

    def test_returns_article_element(self):
        result = build.generate_post_card(self.SAMPLE_POST, 1, "en")
        assert "<article" in result

    def test_title_uppercased(self):
        result = build.generate_post_card(self.SAMPLE_POST, 1, "en")
        assert "TEST POST TITLE" in result

    def test_view_transition_names(self):
        result = build.generate_post_card(self.SAMPLE_POST, 3, "en")
        assert "post-container-3" in result
        assert "post-title-3" in result
        assert "post-date-3" in result

    def test_tags_rendered(self):
        result = build.generate_post_card(self.SAMPLE_POST, 1, "en")
        assert "python" in result
        assert "web" in result
        assert "tag-pill" in result

    def test_no_tags(self):
        post = {**self.SAMPLE_POST, "tags": [], "en_tags": []}
        result = build.generate_post_card(post, 1, "en")
        assert "tag-pill" not in result

    def test_data_attributes(self):
        result = build.generate_post_card(self.SAMPLE_POST, 1, "en")
        assert 'data-year="2024"' in result
        assert 'data-month="06"' in result
        assert 'data-created="2024-06-15"' in result

    def test_en_link_path(self):
        result = build.generate_post_card(self.SAMPLE_POST, 1, "en")
        assert "/en/blog/test-post.html" in result

    def test_pt_link_path(self):
        result = build.generate_post_card(self.SAMPLE_POST, 1, "pt")
        assert "/pt/blog/test-post.html" in result

    def test_pt_date_format(self):
        result = build.generate_post_card(self.SAMPLE_POST, 1, "pt")
        assert "15 de Junho de 2024" in result

    def test_html_escaping(self):
        post = {
            **self.SAMPLE_POST,
            "title": "A <script> Test",
            "excerpt": 'Excerpt & "quotes"',
        }
        result = build.generate_post_card(post, 1, "en")
        # Title is uppercased first, then escaped — produces correct entities
        assert "&lt;SCRIPT&gt;" in result
        assert "&amp;" in result
        assert "&quot;" in result
