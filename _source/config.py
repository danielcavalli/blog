"""Blog Configuration Module.

This module contains all configuration constants for the bilingual blog system.
It defines site metadata, language-specific UI strings, paths, and social links.

The Portuguese post pipeline is translated during build using the translation_v2
OpenCode runtime.

CV data source of truth:
    The canonical English CV source is cv_data.yaml (project root).
    build.py loads it via load_cv_data() for EN, and translates the
    loaded result for PT.  This module holds only UI-string and metadata
    configuration; no CV structured data is stored here.

Environment:
    Local development uses BASE_PATH = ""
    GitHub Pages deployment uses BASE_PATH = "/blog"

Constants:
    BASE_PATH (str): Root path prefix for all generated links
    GEMINI_MODEL_CHAIN (list[str]): Ordered list of Gemini models for translation.
        The translator tries each in sequence when the current model hits a rate
        limit, quota exhaustion, or unavailability error.
    GEMINI_MODEL (str): Backward-compatible alias for the primary (first) model.
    LANGUAGES (dict): Bilingual configuration with EN/PT UI strings and metadata
    DEFAULT_LANGUAGE (str): Fallback language code (en)
    SITE_NAME (str): Display name for the blog
    SITE_DESCRIPTION (str): SEO meta description
    AUTHOR (str): Blog author name
    AUTHOR_BIO (str): Short author biography
    SOCIAL_LINKS (dict): Social media profile URLs
"""

import os

# Base path for GitHub Pages deployment
# Use "" for local development, "/blog" for GitHub Pages at username.github.io/blog/
BASE_PATH = ""

# ---------------------------------------------------------------------------
# Gemini model fallback chain for translation
# ---------------------------------------------------------------------------
# The translator tries models in order.  When a model returns a rate-limit
# (429), quota-exhaustion (RESOURCE_EXHAUSTED), or service-unavailability
# error and exhausts its per-model retry budget, the next model is tried.
#
#   Primary  : gemini-3-flash-preview          — latest preview Flash (v1beta required)
#   Fallback1: gemini-2.5-flash               — stable Flash model
#   Fallback2: gemini-2.0-flash-lite          — lightweight, more quota
GEMINI_MODEL_CHAIN: list = [
    "gemini-3-flash-preview",  # Primary (requires v1beta)
    "gemini-2.5-flash",  # Fallback 1 (stable v1)
    "gemini-3.1-flash-lite",  # Fallback 2 (stable v1)
]

# Backward-compatible alias — points to the primary model in the chain.
GEMINI_MODEL: str = GEMINI_MODEL_CHAIN[0]

# Bilingual support
LANGUAGES = {
    "en": {
        "name": "English",
        "code": "en",
        "dir": "en",
        "label": "EN",
        "og_locale": "en_US",
        "ui": {
            "latest_posts": "Latest Posts",
            "sort_by": "Sort by",
            "last_updated": "Last Updated",
            "published_at": "Published At",
            "filter": "Filter",
            "all_years": "All Years",
            "all_months": "All Months",
            "clear_filters": "Clear Filters",
            "blog": "BLOG",
            "about": "ABOUT",
            "cv": "CV",
            "back_to_blog": "← Back to Blog",
            "last_updated_label": "Last updated",
            "min_read": "min read",
            "skip_to_content": "Skip to content",
            "toggle_theme": "Toggle theme",
            "toggle_sort_order": "Toggle sort order",
            "toggle_filters": "Toggle filters",
            "switch_language": "Switch to {target} (currently {current})",
            "about_jsonld_name": "About {author}",
            "all_rights_reserved": "All Rights Reserved",
            "cv_contact": "Contact",
            "cv_summary": "Summary",
            "cv_experience": "Experience",
            "cv_skills": "Skills",
            "cv_education": "Education",
            "cv_languages": "Languages",
            "landing_blog": "Blog",
            "landing_about": "About Me",
            "landing_cv": "CV",
            "meta_index": "Daniel Cavalli – Machine Learning Engineer. Blog on MLOps, distributed systems, CUDA optimization, and AI infrastructure.",
            "meta_about": "Daniel Cavalli – Machine Learning Engineer at Nubank. Background in MLOps, distributed systems, and AI infrastructure.",
            "meta_cv": "Daniel Cavalli – Machine Learning Engineer at Nubank. Experience in MLOps, distributed systems, and AI infrastructure powering hundreds of Data Scientists.",
            "author_bio": "Machine Learning Engineer at Nubank, focused on distributed training and CUDA optimization.",
            "date_format": "{month} {day}, {year}",
        },
        "months": {
            "January": "January",
            "February": "February",
            "March": "March",
            "April": "April",
            "May": "May",
            "June": "June",
            "July": "July",
            "August": "August",
            "September": "September",
            "October": "October",
            "November": "November",
            "December": "December",
        },
        "about": {
            "title": "ABOUT",
            "p1": "My name is Daniel Cavalli, and I've always been drawn to understanding how things work. I like to take things apart, whether it's a CUDA kernel, a surfboard, or a washing machine, and see what makes them move. There's something deeply satisfying about breaking something open, learning its logic, and putting it back together in a way that feels cleaner, more honest, more complete.",
            "p2": "I work as a Machine Learning Engineer at Nubank, where I spend most of my time making systems faster, simpler, and easier to understand. I care about efficiency, but not the kind that strips things down until they lose meaning. What I look for is clarity, the kind of simplicity where everything has a purpose and moves with intention. I like when things just work, quietly and well.",
            "p3": "This blog is an extension of that way of thinking. Building and writing are how I make sense of the world. When I put ideas into code or words, I can see their edges more clearly, what holds, what doesn't, and what needs to be rebuilt. It's less about publishing and more about refining my own understanding of how things connect.",
            "p4": "Outside of work, I try to keep my life close to the ocean. I surf, bike, build things with my hands, and spend time with Moana, my dog. I live in Copacabana, where the sea is part of the backdrop of everything. Here, even an ordinary day ends with people standing by the water, just watching the light fade. That rhythm, fast, grounded and sometimes even chaotic, is what I try to keep in everything I do.",
        },
    },
    "pt": {
        "name": "Português",
        "code": "pt-BR",
        "dir": "pt",
        "label": "PT",
        "og_locale": "pt_BR",
        "ui": {
            "latest_posts": "Posts Recentes",
            "sort_by": "Ordenar por",
            "last_updated": "Última Atualização",
            "published_at": "Data de Publicação",
            "filter": "Filtrar",
            "all_years": "Todos os Anos",
            "all_months": "Todos os Meses",
            "clear_filters": "Limpar Filtros",
            "blog": "BLOG",
            "about": "SOBRE",
            "cv": "CV",
            "back_to_blog": "← Voltar ao Blog",
            "last_updated_label": "Última atualização",
            "min_read": "min de leitura",
            "skip_to_content": "Pular para o conteúdo",
            "toggle_theme": "Alternar tema",
            "toggle_sort_order": "Alternar ordem",
            "toggle_filters": "Alternar filtros",
            "switch_language": "Mudar para {target} (atualmente {current})",
            "about_jsonld_name": "Sobre {author}",
            "all_rights_reserved": "Todos os Direitos Reservados",
            "cv_contact": "Contato",
            "cv_summary": "Resumo",
            "cv_experience": "Experiência",
            "cv_skills": "Habilidades",
            "cv_education": "Formação",
            "cv_languages": "Idiomas",
            "landing_blog": "Blog",
            "landing_about": "Sobre Mim",
            "landing_cv": "CV",
            "meta_index": "Daniel Cavalli – Engenheiro de Machine Learning. Blog sobre MLOps, sistemas distribuídos, otimização CUDA e infraestrutura de IA.",
            "meta_about": "Daniel Cavalli – Engenheiro de Machine Learning no Nubank. Experiência em MLOps, sistemas distribuídos e infraestrutura de IA.",
            "meta_cv": "Daniel Cavalli – Engenheiro de Machine Learning no Nubank. Experiência em MLOps, sistemas distribuídos e infraestrutura de IA para centenas de Cientistas de Dados.",
            "author_bio": "Engenheiro de Machine Learning no Nubank, focado em treinamento distribuído e otimização CUDA.",
            "date_format": "{day} de {month} de {year}",
        },
        "months": {
            "January": "Janeiro",
            "February": "Fevereiro",
            "March": "Março",
            "April": "Abril",
            "May": "Maio",
            "June": "Junho",
            "July": "Julho",
            "August": "Agosto",
            "September": "Setembro",
            "October": "Outubro",
            "November": "Novembro",
            "December": "Dezembro",
        },
        # Note: 'about' content is automatically translated during build using Gemini
    },
}
DEFAULT_LANGUAGE = "en"


# ---------------------------------------------------------------------------
# Derived helpers – keep language logic config-driven instead of hardcoding
# ---------------------------------------------------------------------------


def get_language_codes() -> list[str]:
    """Return all configured language codes."""
    return list(LANGUAGES.keys())


def get_alternate_language(lang: str) -> str:
    """Return the other language code (for 2-language setups).

    For configurations with more than two languages, returns the first
    code that isn't *lang*.
    """
    codes = get_language_codes()
    return [c for c in codes if c != lang][0] if len(codes) >= 2 else codes[0]


def get_language_dirs() -> dict[str, str]:
    """Return mapping of lang code to output directory name."""
    return {k: v["dir"] for k, v in LANGUAGES.items()}


def get_og_locale(lang: str) -> str:
    """Return the Open Graph locale string for a language code.

    Falls back to ``lang`` itself if no ``og_locale`` key is configured.
    """
    return LANGUAGES[lang].get("og_locale", lang)


# Site metadata
SITE_URL = "https://dan.rio"
SITE_NAME = "dan.rio"
SITE_DESCRIPTION = "Daniel Cavalli's blog on machine learning, AI, CUDA optimization, distributed training, and software engineering."
AUTHOR = "Daniel Cavalli"
AUTHOR_BIO = (
    "Machine Learning Engineer at Nubank, focused on distributed training and CUDA optimization."
)

# Social links
SOCIAL_LINKS = {
    "twitter": "https://x.com/dancavlli",
    "github": "https://github.com/danielcavalli",
    "linkedin": "https://www.linkedin.com/in/cavallidaniel/",
}


# Translation provider defaults for build/runtime routing.
DEFAULT_TRANSLATION_PROVIDER = "opencode"
DEFAULT_TRANSLATION_V2_PROVIDER = "opencode"
DEFAULT_TRANSLATION_V2_ENABLED = True
DEFAULT_TRANSLATION_V2_FAILURE_POLICY = "strict"


def get_translation_provider(default: str = DEFAULT_TRANSLATION_PROVIDER) -> str:
    """Return normalized translation provider from environment.

    Environment variable: TRANSLATION_PROVIDER
    """
    provider = (os.getenv("TRANSLATION_PROVIDER") or default or "").strip().lower()
    return provider or DEFAULT_TRANSLATION_PROVIDER


def get_translation_v2_enabled(
    default: bool = DEFAULT_TRANSLATION_V2_ENABLED,
) -> bool:
    """Return whether translation_v2 build routing is enabled."""

    value = os.getenv("TRANSLATION_V2_ENABLED")
    if value is None:
        return bool(default)
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def get_translation_v2_provider(
    default: str = DEFAULT_TRANSLATION_V2_PROVIDER,
) -> str:
    """Return normalized translation_v2 provider from environment."""

    provider = (os.getenv("TRANSLATION_V2_PROVIDER") or default or "").strip().lower()
    return provider or DEFAULT_TRANSLATION_V2_PROVIDER


def get_translation_v2_failure_policy(
    default: str = DEFAULT_TRANSLATION_V2_FAILURE_POLICY,
) -> str:
    """Return translation_v2 build failure policy from environment."""

    policy = (os.getenv("TRANSLATION_V2_FAILURE_POLICY") or default or "").strip().lower()
    if policy not in {"partial", "strict"}:
        return DEFAULT_TRANSLATION_V2_FAILURE_POLICY
    return policy
