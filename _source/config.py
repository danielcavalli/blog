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
    GEMINI_MODEL (str): Gemini model to use for translations
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
BASE_PATH = ""

# Gemini translation model
GEMINI_MODEL = "gemini-2.5-flash"

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
            'about': 'ABOUT',
            'cv': 'CV'
        },
        'months': {
            'January': 'January', 'February': 'February', 'March': 'March',
            'April': 'April', 'May': 'May', 'June': 'June',
            'July': 'July', 'August': 'August', 'September': 'September',
            'October': 'October', 'November': 'November', 'December': 'December'
        },
        'about': {
            'title': 'ABOUT',
            'p1': "My name is Daniel Cavalli, and I’ve always been drawn to understanding how things work. I like to take things apart, whether it’s a CUDA kernel, a surfboard, or a washing machine, and see what makes them move. There’s something deeply satisfying about breaking something open, learning its logic, and putting it back together in a way that feels cleaner, more honest, more complete.",
            'p2': "I work as a Machine Learning Engineer at Nubank, where I spend most of my time making systems faster, simpler, and easier to understand. I care about efficiency, but not the kind that strips things down until they lose meaning. What I look for is clarity, the kind of simplicity where everything has a purpose and moves with intention. I like when things just work, quietly and well.",
            'p3': "This blog is an extension of that way of thinking. Building and writing are how I make sense of the world. When I put ideas into code or words, I can see their edges more clearly, what holds, what doesn’t, and what needs to be rebuilt. It’s less about publishing and more about refining my own understanding of how things connect.",
            'p4': "Outside of work, I try to keep my life close to the ocean. I surf, bike, build things with my hands, and spend time with Moana, my dog. I live in Copacabana, where the sea is part of the backdrop of everything. Here, even an ordinary day ends with people standing by the water, just watching the light fade. That rhythm, fast, grounded and sometimes even chaotic, is what I try to keep in everything I do.",
        },
        'cv': {
            'title': 'CURRICULUM VITAE',
            'tagline': 'Machine Learning Engineer · Distributed Systems · CUDA Optimization',
            'experience': [
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'Nubank',
                    'location': 'São Paulo, Brazil',
                    'period': 'Present',
                    'description': 'Building and optimizing distributed training systems. Focus on making ML infrastructure faster, simpler, and more reliable. Work spans CUDA kernel optimization, multi-GPU training orchestration, and production ML systems.'
                }
            ],
            'skills': {
                'core': ['Python', 'CUDA', 'PyTorch', 'Distributed Training'],
                'systems': ['DDP', 'FSDP', 'Multi-GPU', 'Performance Optimization'],
                'infrastructure': ['Kubernetes', 'CI/CD', 'ML Operations']
            },
            'education': 'Computer Engineering',
            'location': 'Copacabana, Rio de Janeiro, Brazil',
            'contact': {
                'email': 'Available on request',
                'github': 'danielcavalli',
                'linkedin': 'cavallidaniel'
            }
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
            'about': 'SOBRE',
            'cv': 'CV'
        },
        'months': {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        },
        # Note: 'about' content is automatically translated during build using Gemini
        'cv': {
            'title': 'CURRICULUM VITAE',
            'tagline': 'Engenheiro de Machine Learning · Sistemas Distribuídos · Otimização CUDA',
            'experience': [
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'Nubank',
                    'location': 'São Paulo, Brasil',
                    'period': '2021 - Presente',
                    'description': 'Desenvolvendo sistemas de treinamento distribuído e otimização CUDA para modelos de ML em escala. Foco em performance, eficiência de GPU e infraestrutura de ML.'
                }
            ],
            'skills': {
                'core': ['Python', 'CUDA', 'PyTorch', 'Treinamento Distribuído'],
                'systems': ['DDP', 'FSDP', 'Multi-GPU', 'Otimização de Performance'],
                'infrastructure': ['Kubernetes', 'CI/CD', 'Operações de ML']
            },
            'education': 'Engenharia da Computação',
            'location': 'Copacabana, Rio de Janeiro, Brasil',
            'contact': {
                'email': 'Disponível mediante solicitação',
                'github': 'danielcavalli',
                'linkedin': 'cavallidaniel'
            }
        }
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
