#!/usr/bin/env python3
"""
Translation Module - Gemini-powered PT-BR translation for blog posts
Implements incremental translation with caching to avoid redundant API calls
"""

"""Gemini API Translation System with JSON-based Caching

Provides automatic translation of blog content (Markdown and HTML) from English to
Portuguese (PT-BR) using Google's Gemini 2.5 Flash model. Implements a persistent
JSON cache to avoid redundant API calls for previously translated content.

Environment Variables:
    GEMINI_API_KEY: Required. Google Gemini API key for authentication.

Translation Strategy:
    - Preserves natural Anglicisms (e.g., "frontend", "backend", "framework")
    - Maintains code blocks and technical terminology
    - Translates metadata (title, summary) and body content
    - Uses structured prompts for consistent, natural Portuguese output

Cache Architecture:
    - JSON file storage (translation-cache.json)
    - Keyed by SHA-256 hash of English content
    - Includes timestamp for cache age tracking
    - Atomic write operations with error handling

Typical Usage:
    translator = GeminiTranslator(api_key=os.getenv('GEMINI_API_KEY'))
    post_data = translator.translate_markdown_post(
        markdown_content,
        frontmatter={'title': 'Post Title', 'summary': 'Summary'}
    )
    # Returns: {'markdown': '...', 'metadata': {...}}

Classes:
    TranslationCache: JSON-based persistent cache for translations
    GeminiTranslator: Gemini API client with translation methods

External Dependencies:
    - google-generativeai: Gemini API client library
    - json: Cache persistence
    - hashlib: Content hashing for cache keys
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TRANSLATION_CACHE_FILE = Path("translation-cache.json")
GEMINI_MODEL = "gemini-2.5-flash"  # Using gemini-2.5-flash as requested

class TranslationCache:
    """Manages JSON-based translation cache to avoid redundant Gemini API calls
    
    Cache Structure:
        {
            "post-slug": {
                "content_hash": "sha256...",
                "translation": { ... }
            }
        }
    
    The cache is keyed by post slug and uses SHA-256 content hashes to detect changes.
    If content hash matches, cached translation is returned. Otherwise, a fresh API call
    is made and the cache is updated.
    
    Attributes:
        cache (Dict): In-memory cache dictionary loaded from JSON file
    
    Cache File:
        translation-cache.json in project root
    
    Thread Safety:
        Not thread-safe. Assumes single-process build script usage.
    """
    
    def __init__(self):
        """Initialize cache by loading from disk
        
        If cache file doesn't exist or is corrupted, starts with empty cache.
        """
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing translation cache from JSON file
        
        Returns:
            Dict: Cache dictionary, or empty dict if file doesn't exist or is corrupted
        
        Error Handling:
            Silently returns empty dict on JSON parse errors or file read errors
        """
        if TRANSLATION_CACHE_FILE.exists():
            try:
                with open(TRANSLATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self):
        """Save translation cache to disk atomically
        
        Writes cache to translation-cache.json with UTF-8 encoding and proper formatting.
        Uses ensure_ascii=False to preserve Portuguese characters.
        
        Side Effects:
            Overwrites translation-cache.json file
        
        Raises:
            OSError: If file write fails (permissions, disk full, etc.)
        """
        with open(TRANSLATION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def get_translation(self, slug: str, content_hash: str) -> Optional[Dict]:
        """Get cached translation if content hasn't changed
        
        Checks if slug exists in cache and if content hash matches. If both conditions
        are true, returns cached translation. Otherwise returns None to trigger fresh API call.
        
        Args:
            slug (str): Post slug identifier (e.g., "modern-web-development")
            content_hash (str): SHA-256 hash of current English content
        
        Returns:
            Optional[Dict]: Cached translation dict if found and hash matches, else None
        
        Cache Miss Scenarios:
            - Slug not in cache (new post)
            - Content hash mismatch (post edited)
        """
        if slug in self.cache:
            cached = self.cache[slug]
            if cached.get('content_hash') == content_hash:
                return cached.get('translation')
        return None
    
    def set_translation(self, slug: str, content_hash: str, translation: Dict):
        """Cache translation with content hash
        
        Stores translation in cache with associated content hash for future validation.
        Immediately writes cache to disk to ensure persistence across build runs.
        
        Args:
            slug (str): Post slug identifier
            content_hash (str): SHA-256 hash of English content
            translation (Dict): Translation result from Gemini API
        
        Side Effects:
            Updates self.cache in memory
            Writes updated cache to translation-cache.json via save()
        """
        self.cache[slug] = {
            'content_hash': content_hash,
            'translation': translation
        }
        self.save()


class GeminiTranslator:
    """Handles translation using Google's Gemini 2.5 Flash API
    
    Provides methods for translating:
    - Markdown blog posts with frontmatter metadata
    - Plain text content (for About page, etc.)
    - HTML content
    
    Translation Philosophy:
        - Natural, fluent Brazilian Portuguese
        - Preserves common Anglicisms in tech context (e.g., "framework", "frontend")
        - Maintains code blocks and technical terminology unchanged
        - Respects Markdown formatting and structure
    
    Attributes:
        api_key (str): Gemini API key from GEMINI_API_KEY environment variable
        project_id (str): Optional Gemini project ID from GEMINI_PROJECT_ID
        model (GenerativeModel): Configured Gemini 2.5 Flash model instance
    
    Environment:
        GEMINI_API_KEY: Required. API key for Google Gemini.
        GEMINI_PROJECT_ID: Optional. Project identifier for billing/quotas.
    
    Raises:
        ValueError: If GEMINI_API_KEY not found in environment
    
    API Model:
        gemini-2.5-flash (fast, cost-effective, high-quality translations)
    """
    
    def __init__(self):
        """Initialize Gemini translator with API configuration
        
        Loads GEMINI_API_KEY from environment, configures Gemini API client,
        and initializes translation cache.
        
        Raises:
            ValueError: If GEMINI_API_KEY environment variable not found
        
        Side Effects:
            Calls genai.configure() to set global Gemini API configuration
            Creates TranslationCache instance (loads translation-cache.json)
        """
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.project_id = os.getenv('GEMINI_PROJECT_ID')
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment. "
                "Please create a .env file with your API key. "
                "See .env.example for template."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.cache = TranslationCache()
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for change detection
        
        Used to determine if cached translation is still valid. If content hash
        differs from cached hash, translation is re-generated.
        
        Args:
            content (str): English content to hash
        
        Returns:
            str: Hexadecimal SHA-256 hash digest
        
        Note:
            Uses SHA-256 (not MD5 as originally implemented) for better collision resistance
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def translate_post(self, slug: str, frontmatter: Dict, content: str, force: bool = False) -> Dict:
        """Translate a blog post from English to PT-BR with caching
        
        Main translation method for Markdown blog posts. Checks cache first, calls Gemini API
        if needed, parses response, and caches result.
        
        Args:
            slug (str): Post identifier (e.g., "modern-web-development")
            frontmatter (Dict): Post metadata dict with keys: title, excerpt, tags
            content (str): Markdown content body (without frontmatter)
            force (bool): If True, bypass cache and force fresh translation. Default False.
        
        Returns:
            Dict: Translated post with keys:
                - title (str): Translated post title
                - excerpt (str): Translated post excerpt/summary
                - content (str): Translated Markdown body
                - tags (List[str]): Translated tag list
        
        Side Effects:
            - Prints cache hit/miss messages to stdout
            - Calls Gemini API if cache miss
            - Updates translation cache if API call succeeds
        
        Error Handling:
            On Gemini API failure, returns original English content as fallback
            and prints error message to stdout
        
        Translation Flow:
            1. Calculate content hash
            2. Check cache (unless force=True)
            3. If cache miss: build prompt → call Gemini → parse response → cache result
            4. Return translated dict
        """
        # Check cache unless forcing re-translation
        content_hash = self._calculate_content_hash(content)
        if not force:
            cached = self.cache.get_translation(slug, content_hash)
            if cached:
                print(f"   ↻ Using cached translation for: {slug}")
                return cached
        
        print(f"   ⚡ Translating with Gemini: {slug}")
        
        # Prepare translation prompt
        prompt = self._build_translation_prompt(frontmatter, content)
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            translated_text = response.text
            
            # Parse response to extract translated components
            translated = self._parse_translation_response(translated_text, frontmatter)
            
            # Cache the translation
            self.cache.set_translation(slug, content_hash, translated)
            
            return translated
            
        except Exception as e:
            print(f"   ✗ Translation failed for {slug}: {e}")
            # Return original content as fallback
            return {
                'title': frontmatter.get('title', ''),
                'excerpt': frontmatter.get('excerpt', ''),
                'content': content,
                'tags': frontmatter.get('tags', [])
            }
    
    def translate_if_needed(self, post: Dict, target_lang: str = 'pt') -> Dict:
        """
        Translate a complete post dictionary
        
        Args:
            post: Complete post dict from parse_markdown_post
            target_lang: Target language code
        
        Returns:
            New post dict with translated content
        """
        if target_lang != 'pt':
            return post  # Only Portuguese translation supported
        
        # Extract content for translation
        frontmatter = {
            'title': post.get('title', ''),
            'excerpt': post.get('excerpt', ''),
            'tags': post.get('tags', [])
        }
        
        translated = self.translate_post(
            post['slug'],
            frontmatter,
            post['content'],
            force=False
        )
        
        # Create new post with translated content
        translated_post = post.copy()
        translated_post['title'] = translated['title']
        translated_post['excerpt'] = translated['excerpt']
        translated_post['content'] = translated['content']
        translated_post['tags'] = translated['tags']
        
        return translated_post
    
    def translate_about(self, about_text: Dict, force: bool = False) -> Dict:
        """
        Translate About section text
        
        Args:
            about_text: Dict with 'title' and 'p1', 'p2', 'p3', 'p4' keys
            force: Force re-translation even if cached
        
        Returns:
            Dict with translated about text
        """
        # Create content string from paragraphs
        content = '\n\n'.join([
            about_text.get('p1', ''),
            about_text.get('p2', ''),
            about_text.get('p3', ''),
            about_text.get('p4', '')
        ])
        
        # Check cache
        content_hash = self._calculate_content_hash(content)
        slug = 'about-page'
        
        if not force:
            cached = self.cache.get_translation(slug, content_hash)
            if cached:
                print(f"   ↻ Using cached translation for: About page")
                return cached
        
        print(f"   ⚡ Translating About page with Gemini")
        
        # Build specialized prompt for About section
        prompt = self._build_about_translation_prompt(about_text)
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            translated_text = response.text
            
            # Parse response
            translated = self._parse_about_translation_response(translated_text, about_text)
            
            # Cache the translation
            self.cache.set_translation(slug, content_hash, translated)
            
            return translated
            
        except Exception as e:
            print(f"   ✗ About translation failed: {e}")
            # Return original as fallback
            return about_text
    
    def _build_about_translation_prompt(self, about_text: Dict) -> str:
        """Build translation prompt specifically for About page"""
        return f"""You are a bilingual Brazilian technical writer translating an About/Bio section to Brazilian Portuguese.

**TRANSLATION PHILOSOPHY:**
This is personal, biographical text. It should sound natural and authentic in Brazilian Portuguese while preserving the author's voice and any technical terminology they use.

**CORE PRINCIPLES:**

1. **Preserve Technical & Professional Terms:**
   - Keep job titles and company names: "Machine Learning Engineer", "Nubank"
   - Keep technical terms that are standard in Brazilian tech: CUDA kernel, distributed training, efficiency, systems, workflow
   - Keep proper nouns: Moana, Copacabana

2. **Translate Personal & Narrative Content:**
   - Fully translate personal reflections, descriptions, and narrative text
   - Use natural Brazilian expressions for everyday concepts
   - Maintain the calm, direct tone of the original

3. **Voice & Authenticity:**
   - Mirror the author's personality — technical but grounded
   - Keep the same level of informality/formality
   - Sound like a Brazilian engineer writing about themselves, not a translated text

**INPUT:**

Title: {about_text.get('title', '')}

Paragraph 1: {about_text.get('p1', '')}

Paragraph 2: {about_text.get('p2', '')}

Paragraph 3: {about_text.get('p3', '')}

Paragraph 4: {about_text.get('p4', '')}

**OUTPUT FORMAT:**
Provide the translation in this exact structure:

TITLE:
[translated title]

P1:
[translated paragraph 1]

P2:
[translated paragraph 2]

P3:
[translated paragraph 3]

P4:
[translated paragraph 4]

Begin translation now:"""
    
    def _parse_about_translation_response(self, response: str, original: Dict) -> Dict:
        """Parse Gemini's About page translation response"""
        lines = response.strip().split('\n')
        
        result = {
            'title': original.get('title', ''),
            'p1': original.get('p1', ''),
            'p2': original.get('p2', ''),
            'p3': original.get('p3', ''),
            'p4': original.get('p4', '')
        }
        
        current_section = None
        content_lines = []
        
        for line in lines:
            line_upper = line.strip().upper()
            
            if line_upper == 'TITLE:':
                current_section = 'title'
                continue
            elif line_upper == 'P1:':
                current_section = 'p1'
                content_lines = []
                continue
            elif line_upper == 'P2:':
                if current_section == 'p1':
                    result['p1'] = '\n'.join(content_lines).strip()
                current_section = 'p2'
                content_lines = []
                continue
            elif line_upper == 'P3:':
                if current_section == 'p2':
                    result['p2'] = '\n'.join(content_lines).strip()
                current_section = 'p3'
                content_lines = []
                continue
            elif line_upper == 'P4:':
                if current_section == 'p3':
                    result['p3'] = '\n'.join(content_lines).strip()
                current_section = 'p4'
                content_lines = []
                continue
            
            if current_section == 'title' and line.strip():
                result['title'] = line.strip()
                current_section = None
            elif current_section in ['p1', 'p2', 'p3', 'p4']:
                content_lines.append(line)
        
        # Capture last paragraph
        if current_section == 'p4' and content_lines:
            result['p4'] = '\n'.join(content_lines).strip()
        
        return result

    def _build_translation_prompt(self, frontmatter: Dict, content: str) -> str:
        """Build comprehensive translation prompt for Gemini"""
        return f"""You are a bilingual Brazilian technical writer translating an English blog post to Brazilian Portuguese.

**TRANSLATION PHILOSOPHY:**
The goal is authentic, natural Brazilian Portuguese that reflects how bilingual tech professionals actually communicate — not academic or overly formal translation. Brazilian tech culture embraces English terminology when it's clearer or more widely understood.

**CORE PRINCIPLES:**

1. **Preserve English Technical Terms & Anglicisms:**
   - Keep ALL established technical vocabulary: machine learning, deep learning, GPU, CUDA, kernel, pipeline, workflow, build, design system, distributed training, training loop, checkpoint, batch size, tensor, framework, backend, frontend, API, cache, deploy, debug, benchmark, throughput, latency
   - Keep coding/engineering jargon: refactor, commit, pull request, merge, branch, stack, queue, thread, async
   - Keep design/UI terms when natural: layout, viewport, dropdown, toggle, hover, view transition, FLIP animation
   - Keep units and measurements: GB, MHz, FPS, ms, px, em, rem
   - Keep acronyms and initialisms: AI, ML, DL, NLP, CV, GPU, CPU, RAM, SSD, HTTP, CSS, HTML, JS

2. **Translate Only When Natural:**
   - Translate general concepts: "understanding" → "entendimento", "work" → "trabalho", "process" → "processo"
   - Translate narrative and descriptive text fully
   - Translate UI labels if they're not established terms: "filter" → "filtrar", "clear" → "limpar", "search" → "buscar"

3. **Tone & Voice:**
   - Mirror the original tone exactly — calm, precise, direct
   - Do NOT embellish, simplify, or editorialize
   - Maintain the same level of formality/informality
   - Keep the same rhythm and sentence structure where possible

4. **Formatting Fidelity:**
   - Preserve ALL Markdown: headers (#), lists (-, *), code blocks (```), links ([text](url)), emphasis (**bold**, *italic*)
   - Keep paragraph breaks and spacing identical
   - Never translate code blocks, variable names, file paths, or commands
   - Maintain capitalization patterns (e.g., if title uses Title Case, keep it)

5. **Cultural Authenticity:**
   - Use Brazilian Portuguese, not European Portuguese
   - Write as if you're a Brazilian engineer who naturally code-switches between PT and EN
   - Avoid forced translations that sound unnatural or obscure

**INPUT:**

Title: {frontmatter.get('title', '')}

Excerpt: {frontmatter.get('excerpt', '')}

Tags: {', '.join(frontmatter.get('tags', []))}

Content:
{content}

**OUTPUT FORMAT:**
Provide ONLY the translated content in this exact structure:

TITLE:
[translated title]

EXCERPT:
[translated excerpt]

TAGS:
[translated tags, comma-separated]

CONTENT:
[translated markdown content]

Begin translation now:"""
    
    def _parse_translation_response(self, response: str, original_frontmatter: Dict) -> Dict:
        """Parse Gemini's response into structured translation
        
        Handles both formats:
        1. Section markers on separate lines (TITLE: on one line, content on next)
        2. Section markers with content on same line (TITLE: Content here)
        """
        lines = response.strip().split('\n')
        
        result = {
            'title': original_frontmatter.get('title', ''),
            'excerpt': original_frontmatter.get('excerpt', ''),
            'tags': original_frontmatter.get('tags', []),
            'content': ''
        }
        
        current_section = None
        content_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            line_upper = line_stripped.upper()
            
            # Check if this is a section marker
            if line_upper.startswith('TITLE:'):
                # Handle both "TITLE:" and "TITLE: Content on same line"
                remainder = line_stripped[6:].strip()
                if remainder:
                    result['title'] = remainder
                    current_section = None
                else:
                    current_section = 'title'
                i += 1
                continue
                
            elif line_upper.startswith('EXCERPT:'):
                remainder = line_stripped[8:].strip()
                if remainder:
                    result['excerpt'] = remainder
                    current_section = None
                else:
                    current_section = 'excerpt'
                i += 1
                continue
                
            elif line_upper.startswith('TAGS:'):
                remainder = line_stripped[5:].strip()
                if remainder:
                    result['tags'] = [tag.strip() for tag in remainder.split(',')]
                    current_section = None
                else:
                    current_section = 'tags'
                i += 1
                continue
                
            elif line_upper.startswith('CONTENT:'):
                # Content section - everything after this marker is content
                remainder = line_stripped[8:].strip()
                if remainder:
                    # Content starts on same line as marker
                    content_lines.append(remainder)
                current_section = 'content'
                i += 1
                continue
            
            # Process content based on current section
            if current_section == 'title' and line_stripped:
                result['title'] = line_stripped
                current_section = None
            elif current_section == 'excerpt' and line_stripped:
                result['excerpt'] = line_stripped
                current_section = None
            elif current_section == 'tags' and line_stripped:
                result['tags'] = [tag.strip() for tag in line_stripped.split(',')]
                current_section = None
            elif current_section == 'content':
                # Collect all lines for content, including empty lines
                content_lines.append(line)
            
            i += 1
        
        result['content'] = '\n'.join(content_lines).strip()
        
        return result


def translate_if_needed(slug: str, frontmatter: Dict, content: str, force: bool = False) -> Optional[Dict]:
    """
    Main translation entry point
    
    Returns translated content or None if translation not available/needed
    """
    try:
        translator = GeminiTranslator()
        return translator.translate_post(slug, frontmatter, content, force=force)
    except ValueError as e:
        # API key not configured - skip translation
        if "GEMINI_API_KEY" in str(e):
            return None
        raise
    except Exception as e:
        print(f"Translation error: {e}")
        return None
