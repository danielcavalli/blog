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
            "copy_section_link": "Copy section link",
            "copy_passage_link": "Copy passage link",
            "link_copied": "Link copied",
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
            "meta_about": "Daniel Cavalli – Machine Learning Engineer. Blog on AI, systems design, and understanding how things actually work.",
            "meta_cv": "Daniel Cavalli – Machine Learning Engineer at Nubank. Experience in MLOps, distributed systems, and AI infrastructure powering hundreds of Data Scientists.",
            "author_bio": "Machine Learning Engineer, focused on distributed training and CUDA optimization.",
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
            "p1": "My name is Daniel Cavalli. I'm a Machine Learning Engineer who studied economics, which, at the very least, gave me a formal excuse to be suspicious of systems that appear to work before I understand why they work.",
            "p2": "Not that I needed formal education for that. That instinct has been fairly consistent in my life, and even as a child I would {{STRIKETHROUGH:constantly}} at times get in trouble for taking apart something that was \"broken\", to better understand how it works.",
            "p3": "Well, having formal education meant applying this same mentality to other, uhm, less concrete, topics. Sometimes it leads to distributed training stacks being repurposed, CUDA kernels being written for pipelines that were working, but barely. Other times it leads to surfboards being built in the storage room of my kitchen (with all the fiberglass, tools and dust that comes with it) or a washing machine that had been operating perfectly well, until I decided it should now contribute to science!",
            "p4": "The object changes, but the interest is usually the same: finding the real logic underneath things, where the friction actually is, which parts are carrying their weight, and what can be made simpler in order to make it better.",
            "p5": "My family, while supportive of this behavior, still gives me the occasional look here and there. Unwavering in my intent to break things in order to learn, this blog is where that habit becomes easier to justify. I write about artificial intelligence, systems design, networking and whatever else seems worth understanding properly rather than merely using. Partly to explain things and share some knowledge or opinions, but mostly to see whether my own explanations survive contact with structure and opposing views. Proud to say that they usually don't, which is useful.",
            "p6": "I live in Copacabana, stay as close to the ocean as ordinary life allows, and have found that surfing, engineering, and writing are similar in at least one respect: all three are less impressed by intention than by timing, feel, and whether you actually understand the medium you're working with.",
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
            "copy_section_link": "Copiar link da seção",
            "copy_passage_link": "Copiar link do trecho",
            "link_copied": "Link copiado",
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
            "meta_about": "Daniel Cavalli – Engenheiro de Machine Learning. Blog sobre IA, design de sistemas e entender como as coisas realmente funcionam.",
            "meta_cv": "Daniel Cavalli – Engenheiro de Machine Learning no Nubank. Experiência em MLOps, sistemas distribuídos e infraestrutura de IA para centenas de Cientistas de Dados.",
            "author_bio": "Engenheiro de Machine Learning, focado em treinamento distribuído e otimização CUDA.",
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
    "Machine Learning Engineer, focused on distributed training and CUDA optimization."
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
