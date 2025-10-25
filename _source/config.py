"""Blog Configuration Module.

This module contains all configuration constants for the bilingual blog system.
It defines site metadata, language-specific UI strings, paths, and social links.

The Portuguese 'about' section is automatically translated during the build process
using the Gemini translation system; see translator.py for implementation details.

Environment:
    Local development uses BASE_PATH = ""
    GitHub Pages deployment uses BASE_PATH = "/blog"

Constants:
    BASE_PATH (str): Root path prefix for all generated links
    LANGUAGES (dict): Bilingual configuration with EN/PT UI strings and metadata
    DEFAULT_LANGUAGE (str): Fallback language code (en)
    SITE_NAME (str): Display name for the blog
    SITE_DESCRIPTION (str): SEO meta description
    AUTHOR (str): Blog author name
    AUTHOR_BIO (str): Short author biography
    SOCIAL_LINKS (dict): Social media profile URLs
"""

# Base path for GitHub Pages deployment
# Use "" for local development, "/blog" for GitHub Pages at username.github.io/blog/
BASE_PATH = "/blog"

# Bilingual support
LANGUAGES = {
    'en': {
        'name': 'English',
        'code': 'en',
        'dir': 'en',
        'label': 'EN',
        'ui': {
            'latest_posts': 'Latest Posts',
            'sort_by': 'Sort by',
            'last_updated': 'Last Updated',
            'published_at': 'Published At',
            'filter': 'Filter',
            'all_years': 'All Years',
            'all_months': 'All Months',
            'clear_filters': 'Clear Filters',
            'blog': 'BLOG',
            'about': 'ABOUT'
        },
        'months': {
            'January': 'January', 'February': 'February', 'March': 'March',
            'April': 'April', 'May': 'May', 'June': 'June',
            'July': 'July', 'August': 'August', 'September': 'September',
            'October': 'October', 'November': 'November', 'December': 'December'
        },
        'about': {
            'title': 'ABOUT',
            'p1': "I'm Daniel Cavalli. I like understanding how things work by taking them apart. It doesn't matter if it's a CUDA kernel, a surfboard, or a bike crankset. The process is the same: break it open, study the pieces, build it better.",
            'p2': "I work as a Machine Learning Engineer at Nubank, where I care about efficiency. I like when systems are clean and do what they should without noise. My work is an extension of that mindset, finding simpler paths that make everything move faster and with less friction.",
            'p3': "Writing helps me think. It forces precision and makes me see where my ideas actually hold.",
            'p4': "Outside of work I stay close to the ocean. I surf, bike, build things with my hands, and spend time with Moana, my dog. I live in Copacabana, where the sea is part of the background of everything."
        }
    },
    'pt': {
        'name': 'Português',
        'code': 'pt-BR',
        'dir': 'pt',
        'label': 'PT',
        'ui': {
            'latest_posts': 'Posts Recentes',
            'sort_by': 'Ordenar por',
            'last_updated': 'Última Atualização',
            'published_at': 'Data de Publicação',
            'filter': 'Filtrar',
            'all_years': 'Todos os Anos',
            'all_months': 'Todos os Meses',
            'clear_filters': 'Limpar Filtros',
            'blog': 'BLOG',
            'about': 'SOBRE'
        },
        'months': {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        # Note: 'about' content is automatically translated during build using Gemini
    }
}
DEFAULT_LANGUAGE = 'en'

# Site metadata
SITE_NAME = "dan.rio"
SITE_DESCRIPTION = "Personal blog by Daniel Cavalli on machine learning, CUDA, distributed training, and engineering."
AUTHOR = "Daniel Cavalli"
AUTHOR_BIO = "Machine Learning Engineer at Nubank, focused on distributed training and CUDA optimization."

# Social links
SOCIAL_LINKS = {
    "twitter": "https://x.com/dancavlli",
    "github": "https://github.com/danielcavalli",
    "linkedin": "https://www.linkedin.com/in/cavallidaniel/"
}
