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
            'title': 'DANIEL CAVALLI',
            'tagline': 'Machine Learning Engineer · MLOps · Distributed Systems',
            'location': 'Rio de Janeiro, Brazil',
            'summary': "Machine Learning Engineer at Nubank, helping build and scale the company's AI platform that powers hundreds of Data Scientists across multiple business units. My work bridges infrastructure and applied ML, optimizing distributed training with multi-cluster, multi-GPU strategies and designing deployment workflows through Argo and Tekton. I focus on creating reliable, reusable systems that turn complex models into production-ready services.",
            'experience': [
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'Nubank',
                    'location': 'São Paulo, Brazil',
                    'period': 'Sep 2023 — Present',
                    'description': "Evolving Nubank's AI Platform to empower hundreds of Data Scientists with reproducible training pipelines and scalable infrastructure.",
                    'achievements': [
                        'Enhanced the AI Platform by improving integrations across Kubeflow, Dagster, Clojure Services, Argo, and the in-house CPW library, adding new features and revamping core components to increase reliability and reusability.',
                        'Increased model-training throughput through multi-cluster, multi-GPU distribution strategies and reproducible, optimized job assets.',
                        "Led the international expansion of Nubank's AI Platform, adapting infrastructure, governance, and deployment pipelines to support new GEOs and enable the company's global growth."
                    ]
                },
                {
                    'title': 'Senior Machine Learning Engineer',
                    'company': 'PicPay',
                    'location': 'Brazil',
                    'period': 'May 2022 — Sep 2023',
                    'description': "Laid the foundation for the ML and Data Infrastructure of PicPay's High Income business unit, establishing scalable systems that bridged Data Engineering and MLOps practices.",
                    'achievements': [
                        'Designed and maintained an end-to-end MLOps environment for real-time model deployment, monitoring, and experimentation using AWS SageMaker.',
                        'Built DataOps pipelines for efficient DAG deployment and EMR cluster management, improving performance and maintainability across workflows.',
                        "Developed data pipelines fully integrated with the company's DataLake, ensuring reliability, consistency, and seamless access for analytics and model training."
                    ]
                },
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'frete.com',
                    'location': 'Brazil',
                    'period': 'Nov 2021 — May 2022',
                    'description': "Developed early MLOps foundations and machine learning models to enhance the company's risk management and fraud detection systems for truck drivers and freight operations.",
                    'achievements': [
                        'Designed ML models to expand risk management and fraud prevention tools while improving model deployment efficiency through internal MLOps solutions.',
                        'Evaluated and integrated external data providers to improve model performance and cost-effectiveness across analytics workflows.'
                    ]
                },
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'M4U',
                    'location': 'Brazil',
                    'period': 'Sep 2020 — Nov 2021',
                    'description': "Led the design and implementation of the company's first Anti-Fraud solution and AI Platform, transforming internal operations and establishing ML infrastructure as a core product capability.",
                    'achievements': [
                        'Spearheaded the development of an end-to-end anti-fraud system combining a rule-based engine and a machine learning model, built on top of a new MLOps platform using GitOps, AWS SageMaker, and Terraform.',
                        'Advocated for and defined the Anti-Fraud platform as a key product initiative, aligning engineering and business teams around its strategic value.',
                        'Designed scalable deployment and monitoring workflows, ensuring reliability and compliance across multiple production environments.'
                    ]
                },
                {
                    'title': 'Junior Data Scientist',
                    'company': 'M4U',
                    'location': 'Brazil',
                    'period': 'May 2019 — Sep 2020',
                    'description': "Contributed across the full ML workflow while helping shape the early data foundations that later evolved into the company's AI Platform.",
                    'achievements': [
                        'Designed and maintained observability tools for ML models in staging and production, enabling data and concept drift detection.',
                        'Conducted exploratory and descriptive analyses across multiple M4U products, creating visual reports that accelerated operational diagnostics and insight generation.'
                    ]
                },
                {
                    'title': 'Junior Data Scientist',
                    'company': 'Oi S.A',
                    'location': 'Rio de Janeiro, Brazil',
                    'period': 'Nov 2018 — May 2019',
                    'description': "Started my career within Oi's UX Research Lab, where I combined analytics, user research, and data science to improve digital experiences for millions of users of the Minha Oi platform.",
                    'achievements': [
                        'Developed an early NLP model leveraging BERT, before the rise of LLMs, to analyze open-text feedback from user surveys, automatically extracting insights for product and design teams.',
                        'Conducted analytical and exploratory studies to validate hypotheses raised by the UX team regarding user behavior and engagement patterns.',
                        'Retrieved and structured data that served as the foundation for UX improvements and decision-making across web and mobile channels.'
                    ]
                }
            ],
            'skills': {
                'core': ['Distributed Systems', 'Machine Learning Infrastructure', 'MLOps'],
                'tools': ['Kubeflow', 'Dagster', 'Argo', 'Tekton', 'AWS SageMaker', 'Terraform'],
                'languages': ['Python', 'Clojure', 'SQL']
            },
            'education': [
                {
                    'degree': 'Bachelor of Economics',
                    'school': 'Federal University of Rio de Janeiro',
                    'period': '2017 — 2023'
                },
                {
                    'degree': 'Associate Degree in Game Development & Software Engineering',
                    'school': 'NAVE - Núcleo Avançado em Educação',
                    'period': '2014 — 2016'
                }
            ],
            'languages_spoken': ['Portuguese (Native)', 'English (Professional)'],
            'contact': {
                'email': 'daniel@cavalli.dev',
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
            'title': 'DANIEL CAVALLI',
            'tagline': 'Engenheiro de Machine Learning · MLOps · Sistemas Distribuídos',
            'location': 'Rio de Janeiro, Brasil',
            'summary': "Engenheiro de Machine Learning no Nubank, ajudando a construir e escalar a plataforma de IA da empresa que capacita centenas de Cientistas de Dados em múltiplas unidades de negócio. Meu trabalho faz a ponte entre infraestrutura e ML aplicado, otimizando treinamento distribuído com estratégias multi-cluster e multi-GPU e projetando fluxos de deployment através de Argo e Tekton. Foco em criar sistemas confiáveis e reutilizáveis que transformam modelos complexos em serviços prontos para produção.",
            'experience': [
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'Nubank',
                    'location': 'São Paulo, Brasil',
                    'period': 'Set 2023 — Presente',
                    'description': "Evoluindo a Plataforma de IA do Nubank para capacitar centenas de Cientistas de Dados com pipelines de treinamento reproduzíveis e infraestrutura escalável.",
                    'achievements': [
                        'Aprimorei a Plataforma de IA melhorando integrações entre Kubeflow, Dagster, Serviços Clojure, Argo e a biblioteca interna CPW, adicionando novas funcionalidades e reformulando componentes centrais para aumentar confiabilidade e reusabilidade.',
                        'Aumentei o throughput de treinamento de modelos através de estratégias de distribuição multi-cluster e multi-GPU e assets de jobs reproduzíveis e otimizados.',
                        "Liderei a expansão internacional da Plataforma de IA do Nubank, adaptando infraestrutura, governança e pipelines de deployment para suportar novas geografias e possibilitar o crescimento global da empresa."
                    ]
                },
                {
                    'title': 'Senior Machine Learning Engineer',
                    'company': 'PicPay',
                    'location': 'Brasil',
                    'period': 'Mai 2022 — Set 2023',
                    'description': "Construí a fundação da Infraestrutura de ML e Dados da unidade de negócios High Income do PicPay, estabelecendo sistemas escaláveis que conectavam práticas de Engenharia de Dados e MLOps.",
                    'achievements': [
                        'Projetei e mantive um ambiente MLOps de ponta a ponta para deployment de modelos em tempo real, monitoramento e experimentação usando AWS SageMaker.',
                        'Construí pipelines de DataOps para deployment eficiente de DAGs e gerenciamento de clusters EMR, melhorando performance e manutenibilidade dos fluxos de trabalho.',
                        "Desenvolvi pipelines de dados totalmente integrados com o DataLake da empresa, garantindo confiabilidade, consistência e acesso transparente para analytics e treinamento de modelos."
                    ]
                },
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'frete.com',
                    'location': 'Brasil',
                    'period': 'Nov 2021 — Mai 2022',
                    'description': "Desenvolvi fundações iniciais de MLOps e modelos de machine learning para aprimorar os sistemas de gestão de risco e detecção de fraude da empresa para motoristas de caminhão e operações de frete.",
                    'achievements': [
                        'Projetei modelos de ML para expandir ferramentas de gestão de risco e prevenção de fraude, melhorando a eficiência de deployment de modelos através de soluções internas de MLOps.',
                        'Avaliei e integrei provedores externos de dados para melhorar performance dos modelos e custo-efetividade nos fluxos de analytics.'
                    ]
                },
                {
                    'title': 'Machine Learning Engineer',
                    'company': 'M4U',
                    'location': 'Brasil',
                    'period': 'Set 2020 — Nov 2021',
                    'description': "Liderei o design e implementação da primeira solução de Anti-Fraude e Plataforma de IA da empresa, transformando operações internas e estabelecendo infraestrutura de ML como capacidade central do produto.",
                    'achievements': [
                        'Liderai o desenvolvimento de um sistema anti-fraude de ponta a ponta combinando um motor de regras e um modelo de machine learning, construído sobre uma nova plataforma MLOps usando GitOps, AWS SageMaker e Terraform.',
                        'Defendi e defini a plataforma Anti-Fraude como iniciativa estratégica de produto, alinhando times de engenharia e negócios em torno de seu valor estratégico.',
                        'Projetei fluxos de deployment e monitoramento escaláveis, garantindo confiabilidade e conformidade em múltiplos ambientes de produção.'
                    ]
                },
                {
                    'title': 'Junior Data Scientist',
                    'company': 'M4U',
                    'location': 'Brasil',
                    'period': 'Mai 2019 — Set 2020',
                    'description': "Contribuí em todo o fluxo de ML enquanto ajudava a moldar as fundações de dados iniciais que mais tarde evoluíram para a Plataforma de IA da empresa.",
                    'achievements': [
                        'Projetei e mantive ferramentas de observabilidade para modelos de ML em staging e produção, habilitando detecção de data drift e concept drift.',
                        'Conduzi análises exploratórias e descritivas em múltiplos produtos da M4U, criando relatórios visuais que aceleraram diagnósticos operacionais e geração de insights.'
                    ]
                },
                {
                    'title': 'Junior Data Scientist',
                    'company': 'Oi S.A',
                    'location': 'Rio de Janeiro, Brasil',
                    'period': 'Nov 2018 — Mai 2019',
                    'description': "Comecei minha carreira no Lab de Pesquisa UX da Oi, onde combinei analytics, pesquisa de usuário e ciência de dados para melhorar experiências digitais para milhões de usuários da plataforma Minha Oi.",
                    'achievements': [
                        'Desenvolvi um modelo NLP pioneiro utilizando BERT, antes da ascensão dos LLMs, para analisar feedback em texto aberto de pesquisas de usuários, extraindo automaticamente insights para times de produto e design.',
                        'Conduzi estudos analíticos e exploratórios para validar hipóteses levantadas pelo time de UX sobre comportamento e padrões de engajamento dos usuários.',
                        'Coletei e estruturei dados que serviram como fundação para melhorias de UX e tomada de decisão nos canais web e mobile.'
                    ]
                }
            ],
            'skills': {
                'core': ['Sistemas Distribuídos', 'Infraestrutura de Machine Learning', 'MLOps'],
                'tools': ['Kubeflow', 'Dagster', 'Argo', 'Tekton', 'AWS SageMaker', 'Terraform'],
                'languages': ['Python', 'Clojure', 'SQL']
            },
            'education': [
                {
                    'degree': 'Bacharelado em Economia',
                    'school': 'Universidade Federal do Rio de Janeiro',
                    'period': '2017 — 2023'
                },
                {
                    'degree': 'Técnico em Desenvolvimento de Jogos e Engenharia de Software',
                    'school': 'NAVE - Núcleo Avançado em Educação',
                    'period': '2014 — 2016'
                }
            ],
            'languages_spoken': ['Português (Nativo)', 'Inglês (Profissional)'],
            'contact': {
                'email': 'daniel@cavalli.dev',
                'github': 'danielcavalli',
                'linkedin': 'cavallidaniel'
            }
        }
    }
}
DEFAULT_LANGUAGE = 'en'

# Site metadata
SITE_URL = "https://dan.rio"
SITE_NAME = "dan.rio"
SITE_DESCRIPTION = "Daniel Cavalli's blog on machine learning, AI, CUDA optimization, distributed training, and software engineering."
AUTHOR = "Daniel Cavalli"
AUTHOR_BIO = "Machine Learning Engineer at Nubank, focused on distributed training and CUDA optimization."

# Social links
SOCIAL_LINKS = {
    "twitter": "https://x.com/dancavlli",
    "github": "https://github.com/danielcavalli",
    "linkedin": "https://www.linkedin.com/in/cavallidaniel/"
}
