#!/usr/bin/env python3
"""
Multi-Agent Translation Pipeline for Brazilian Portuguese

Three-stage pipeline:
1. Translation Agent: Translates English to PT-BR
2. Critique Agent: Reviews translation quality and semantic alignment
3. Refinement Agent: Applies feedback to improve translation
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv
from config import GEMINI_MODEL

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
TRANSLATION_CACHE_FILE = PROJECT_ROOT / "_cache" / "translation-cache.json"

# Rate limiting: Set to 90 seconds to ensure we NEVER hit API rate limits
# This is extremely conservative but guarantees stability
# Total time for 6 posts: ~9 minutes (6 posts × 90 seconds)
MIN_REQUEST_INTERVAL = 90.0  # seconds between API calls (ultra-safe margin)


class TranslationCache:
    """Persistent cache for translated content using content hashing.
    
    Stores translations indexed by post slug and content hash to avoid
    unnecessary API calls when content hasn't changed. Cache is saved
    as JSON to survive between build runs.
    
    The cache structure:
        {
            "post-slug": {
                "hash": "sha256_hash_of_content",
                "translation": {
                    "title": "Translated Title",
                    "excerpt": "Translated excerpt",
                    "tags": ["tag1", "tag2"],
                    "content": "<p>Translated HTML content</p>"
                }
            }
        }
    
    Attributes:
        cache (Dict): In-memory cache dictionary loaded from JSON file.
    """
    
    def __init__(self):
        """Initialize cache by loading from disk if available."""
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from JSON file.
        
        Returns:
            Dict: Loaded cache dictionary, or empty dict if file doesn't exist
                  or is corrupted.
        """
        if TRANSLATION_CACHE_FILE.exists():
            try:
                with open(TRANSLATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self):
        """Persist cache to disk as JSON with UTF-8 encoding.
        
        Writes the entire cache dictionary to the cache file, overwriting
        any existing content. Uses indent=2 for human readability and
        ensure_ascii=False to preserve Unicode characters.
        """
        with open(TRANSLATION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def get_translation(self, slug: str, content_hash: str) -> Optional[Dict]:
        """Retrieve cached translation if content hasn't changed.
        
        Args:
            slug (str): Post identifier (filename without extension).
            content_hash (str): SHA256 hash of current content.
        
        Returns:
            Optional[Dict]: Translation dict if found and hash matches,
                           None otherwise.
        """
        entry = self.cache.get(slug)
        if entry and isinstance(entry, dict) and entry.get('hash') == content_hash:
            return entry.get('translation')
        return None
    
    def store_translation(self, slug: str, content_hash: str, translation: Dict):
        """Store translation in cache and persist to disk.
        
        Args:
            slug (str): Post identifier.
            content_hash (str): SHA256 hash of source content.
            translation (Dict): Translation result containing title, excerpt,
                              tags, and content.
        """
        self.cache[slug] = {
            'hash': content_hash,
            'translation': translation
        }
        self.save()


class MultiAgentTranslator:
    """Three-stage translation pipeline using Gemini API.
    
    This translator uses a multi-agent approach:
        1. Translation Agent: Translates English content to Brazilian Portuguese
        2. Critique Agent: Reviews translation for semantic accuracy and naturalness
        3. Refinement Agent: Applies feedback to improve translation quality
    
    The pipeline includes:
        - Content-based caching to avoid redundant API calls
        - Rate limiting to respect API quotas (10 requests per minute)
        - Automatic retry with exponential backoff for rate limit errors
        - Natural Brazilian Portuguese output with technical terms in English
    
    Attributes:
        api_key (str): Gemini API key from environment.
        model: Configured Gemini generative model.
        cache (TranslationCache): Persistent translation cache.
        enable_critique (bool): Whether to run critique/refinement stages.
        last_api_call (float): Timestamp of last API call for rate limiting.
    """
    
    def __init__(self, enable_critique: bool = True):
        """Initialize translator with API credentials and cache.
        
        Args:
            enable_critique (bool): If True, runs full 3-stage pipeline.
                                   If False, skips critique and refinement.
        
        Raises:
            ValueError: If GEMINI_API_KEY environment variable is not set.
        """
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.cache = TranslationCache()
        self.enable_critique = enable_critique
        self.last_api_call = 0
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content for cache validation.
        
        Args:
            content (str): Content to hash (typically post content + frontmatter).
        
        Returns:
            str: Hexadecimal SHA256 hash string.
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _clean_backticks_from_text(self, text: str) -> str:
        """Remove backticks wrapping isolated English technical terms.
        
        This fixes the common issue where LLMs wrap English terms in backticks
        when translating to Portuguese, making the text look unnatural.
        
        Preserves:
        - Code blocks (```...```)
        - Inline code with multiple words or special characters
        - Legitimate code references
        
        Removes backticks from:
        - Single technical English words: `GPU` -> GPU
        - Short technical phrases: `machine learning` -> machine learning
        
        Args:
            text (str): Text that may contain backtick-wrapped terms.
        
        Returns:
            str: Text with backticks removed from isolated technical terms.
        """
        import re
        
        # Pattern: backtick, word characters/spaces/hyphens (2-30 chars), backtick
        # But NOT if preceded/followed by more backticks (code blocks)
        # This preserves code blocks (```) and inline code with actual code content
        pattern = r'(?<!`)` *([A-Za-z][\w\s\-]{1,30}?) *`(?!`)'
        
        # Replace backticks around simple technical terms
        cleaned = re.sub(pattern, r'\1', text)
        
        return cleaned
    
    def _rate_limit(self):
        """Enforce minimum interval between API calls.
        
        Blocks execution if insufficient time has passed since last API call.
        Uses MIN_REQUEST_INTERVAL (10 seconds) to stay under API rate limits.
        """
        elapsed = time.time() - self.last_api_call
        if elapsed < MIN_REQUEST_INTERVAL:
            sleep_time = MIN_REQUEST_INTERVAL - elapsed
            time.sleep(sleep_time)
        self.last_api_call = time.time()
    
    def _call_api(self, prompt: str, retries: int = 10) -> Optional[str]:
        """Call Gemini API with rate limiting and retry logic.
        
        Handles rate limits by waiting 90 seconds for quota reset.
        For other errors, retries with 10-second delays.
        
        Args:
            prompt (str): Translation prompt to send to Gemini.
            retries (int): Maximum number of retry attempts (default: 10).
        
        Returns:
            Optional[str]: API response text, or None if all retries exhausted.
        
        Raises:
            Exception: If API fails after all retries or encounters fatal error.
        """
        for attempt in range(retries):
            try:
                self._rate_limit()
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                error_msg = str(e)
                # Log the error received from Gemini
                print(f"      Gemini API error: {error_msg[:500]}")
                
                # Check if it's a rate limit error
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    # Wait 90 seconds for rate limits to reset
                    print(f"      Rate limit detected - waiting 90s for quota to reset...")
                    time.sleep(90)
                    continue
                
                # For other errors, retry with delay
                if attempt < retries - 1:
                    print(f"      Retrying in 10s ({attempt + 2}/{retries})...")
                    time.sleep(10)
                else:
                    print(f"      FATAL: API failed after {retries} attempts")
                    raise Exception(f"Translation API failed: {error_msg}")
        
        raise Exception("Translation API exhausted all retries")
    
    def translate_post(self, slug: str, frontmatter: Dict, content: str, force: bool = False) -> Optional[Dict]:
        """Multi-agent translation pipeline for blog posts.
        
        Orchestrates the three-stage translation process:
            1. Initial translation to Brazilian Portuguese
            2. Quality critique (if enabled)
            3. Refinement based on feedback (if needed)
        
        Uses cache to avoid retranslating unchanged content. Automatically
        retranslates if cached translation has empty content field.
        
        Args:
            slug (str): Post identifier (filename without extension).
            frontmatter (Dict): Post metadata (title, excerpt, tags).
            content (str): Post body content in Markdown/HTML.
            force (bool): If True, bypasses cache and forces new translation.
        
        Returns:
            Optional[Dict]: Translation dict with title, excerpt, tags, content.
                           None if translation fails.
        """
        content_hash = self._calculate_hash(content + str(frontmatter))
        
        if not force:
            cached = self.cache.get_translation(slug, content_hash)
            if cached:
                # Check if cached translation has empty content - if so, retranslate
                if not cached.get('content', '').strip():
                    print(f"   Cached translation has empty content, retranslating: {slug}")
                    force = True
                else:
                    print(f"   Content unchanged: {slug}")
                    return cached
        
        print(f"   Translating: {slug}")
        
        translation = self._translate(frontmatter, content)
        if not translation:
            return None
        
        if not self.enable_critique:
            print(f"      Translation complete (critique disabled)")
            self.cache.store_translation(slug, content_hash, translation)
            return translation
        
        print(f"      Reviewing translation...")
        
        critique_result, feedback = self._critique(frontmatter, content, translation)
        
        if critique_result == "OK":
            print(f"      Translation approved")
            self.cache.store_translation(slug, content_hash, translation)
            return translation
        
        print(f"      Refining based on feedback...")
        
        refined = self._refine(frontmatter, content, translation, feedback)
        
        if refined:
            print(f"      Translation refined")
            self.cache.store_translation(slug, content_hash, refined)
            return refined
        
        print(f"      Using initial translation")
        self.cache.store_translation(slug, content_hash, translation)
        return translation
    
    def _translate(self, frontmatter: Dict, content: str) -> Optional[Dict]:
        """Stage 1: Initial translation agent.
        
        Translates English blog post to Brazilian Portuguese with focus on:
        - Natural, culturally appropriate language
        - Technical term conventions (keeping known terms in English)
        - Proper translation of title, excerpt, tags, and content
        
        Args:
            frontmatter (Dict): Post metadata with title, excerpt, tags.
            content (str): Post body content to translate.
        
        Returns:
            Optional[Dict]: Dict with translated title, excerpt, tags, content.
                           None if API call fails or response can't be parsed.
        """
        prompt = self._build_translation_prompt(frontmatter, content)
        
        response_text = self._call_api(prompt)
        if not response_text:
            return None
        
        parsed = self._parse_response(response_text, frontmatter)
        
        # Post-process to remove backticks around English technical terms
        if parsed and parsed.get('content'):
            parsed['content'] = self._clean_backticks_from_text(parsed['content'])
        if parsed and parsed.get('title'):
            parsed['title'] = self._clean_backticks_from_text(parsed['title'])
        if parsed and parsed.get('excerpt'):
            parsed['excerpt'] = self._clean_backticks_from_text(parsed['excerpt'])
        
        return parsed
    
    def _critique(self, frontmatter: Dict, content: str, translation: Dict) -> Tuple[str, str]:
        """Stage 2: Quality critique agent.
        
        Reviews translation quality by checking:
        - Semantic alignment with original meaning
        - Natural Brazilian Portuguese usage
        - Technical term conventions
        - Formatting preservation
        
        Args:
            frontmatter (Dict): Original English metadata.
            content (str): Original English content.
            translation (Dict): Translated Portuguese version.
        
        Returns:
            Tuple[str, str]: (status, feedback) where:
                - status: "OK" if approved, "FEEDBACK" if needs refinement
                - feedback: Empty if OK, improvement suggestions if FEEDBACK
        """
        prompt = self._build_critique_prompt(frontmatter, content, translation)
        
        response_text = self._call_api(prompt)
        if not response_text:
            # If critique fails, assume OK
            return ("OK", "")
        
        result = response_text.strip()
        
        if result.startswith("OK"):
            return ("OK", "")
        elif result.startswith("FEEDBACK:"):
            feedback = result.replace("FEEDBACK:", "").strip()
            return ("FEEDBACK", feedback)
        else:
            # Unclear response, assume OK
            return ("OK", "")
    
    def _refine(self, frontmatter: Dict, content: str, translation: Dict, feedback: str) -> Optional[Dict]:
        """Stage 3: Refinement agent.
        
        Applies critique feedback to improve translation while maintaining:
        - Original semantic meaning
        - Brazilian Portuguese naturalness
        - All formatting and structure
        
        Args:
            frontmatter (Dict): Original English metadata.
            content (str): Original English content.
            translation (Dict): Current Portuguese translation.
            feedback (str): Improvement suggestions from critique agent.
        
        Returns:
            Optional[Dict]: Refined translation dict, or None if refinement fails.
        """
        prompt = self._build_refinement_prompt(frontmatter, content, translation, feedback)
        
        response_text = self._call_api(prompt)
        if not response_text:
            return None
        
        refined = self._parse_response(response_text, frontmatter)
        
        # Post-process to remove backticks around English technical terms
        if refined and refined.get('content'):
            refined['content'] = self._clean_backticks_from_text(refined['content'])
        if refined and refined.get('title'):
            refined['title'] = self._clean_backticks_from_text(refined['title'])
        if refined and refined.get('excerpt'):
            refined['excerpt'] = self._clean_backticks_from_text(refined['excerpt'])
        
        return refined
    
    def _build_translation_prompt(self, frontmatter: Dict, content: str) -> str:
        """Build prompt for Stage 1 translation agent.
        
        Creates detailed prompt with translation rules, technical conventions,
        and strict output formatting requirements.
        
        Args:
            frontmatter (Dict): Post metadata (title, excerpt, tags).
            content (str): Post content to translate.
        
        Returns:
            str: Formatted translation prompt for Gemini API.
        """
        title = frontmatter.get('title', '')
        excerpt = frontmatter.get('excerpt', '')
        tags = ', '.join(frontmatter.get('tags', []))
        
        return f"""Translate this technical blog post to natural Brazilian Portuguese.

TRANSLATION RULES:
- Write as a bilingual Brazilian engineer would naturally speak
- Keep ONLY these technical terms in English (no special formatting): GPU, CUDA, API, ML, AI, machine learning, deep learning, backend, frontend, framework, pipeline, cache, build, deploy, commit, debug, kernel, thread, hardware, software, benchmark, throughput, latency, overhead, runtime, tooling, workflow, endpoint, payload, metadata
- TRANSLATE these common words to Portuguese: port/ports → porta/portas, switch → switch (same), setup → configuração, network → rede, traffic → tráfego, rule/rules → regra/regras, mode → modo, alert → alerta, blocking → bloqueio, segmentation → segmentação
- TRANSLATE ALL section headings/titles to Portuguese (##, ###, etc.)
- CRITICAL: English technical terms must appear as plain text within Portuguese sentences - never wrap them in backticks, quotes, or any other formatting
- Use natural Brazilian idioms: "I am Daniel" = "Me chamo Daniel" (not "Sou Daniel")
- Preserve ALL Markdown syntax, code blocks, and formatting EXACTLY
- Do NOT add explanations, notes, or JSON blocks
- Output ONLY the sections below in the exact format shown

INPUT:
Title: {title}
Excerpt: {excerpt}
Tags: {tags}

Content:
{content}

OUTPUT FORMAT (provide ONLY these sections, nothing else):

TITLE:
[translated title here]

EXCERPT:
[translated excerpt here]

TAGS:
[comma-separated translated tags]

CONTENT:
[full translated content with all markdown preserved]"""
    
    def _build_critique_prompt(self, frontmatter: Dict, content: str, translation: Dict) -> str:
        """Build prompt for Stage 2 critique agent.
        
        Creates comparison prompt asking agent to review translation quality,
        semantic alignment, and naturalness.
        
        Args:
            frontmatter (Dict): Original English metadata.
            content (str): Original English content.
            translation (Dict): Translated Portuguese version.
        
        Returns:
            str: Formatted critique prompt for Gemini API.
        """
        return f"""Compare the English original with the Portuguese translation.

Check if they convey the same ideas, tone, and meaning.

ORIGINAL ENGLISH:
Title: {frontmatter.get('title', '')}
Excerpt: {frontmatter.get('excerpt', '')}
Content: {content[:1500]}...

PORTUGUESE TRANSLATION:
Title: {translation.get('title', '')}
Excerpt: {translation.get('excerpt', '')}
Content: {translation.get('content', '')[:1500]}...

If the translation is semantically aligned and sounds natural, respond:
OK

If there are issues (wrong meaning, unnatural phrasing, missing content, wrong tone), respond:
FEEDBACK: [specific issues to fix]

Your response:"""
    
    def _build_refinement_prompt(self, frontmatter: Dict, content: str, translation: Dict, feedback: str) -> str:
        """Build prompt for Stage 3 refinement agent.
        
        Creates prompt asking agent to apply critique feedback while
        maintaining translation quality and formatting.
        
        Args:
            frontmatter (Dict): Original English metadata (unused but kept for consistency).
            content (str): Original English content.
            translation (Dict): Current Portuguese translation.
            feedback (str): Critique feedback to address.
        
        Returns:
            str: Formatted refinement prompt for Gemini API.
        """
        return f"""Improve this Portuguese translation based on feedback.

ORIGINAL ENGLISH:
{content}

CURRENT TRANSLATION:
{translation.get('content', '')}

FEEDBACK:
{feedback}

Apply the feedback while maintaining natural Brazilian Portuguese.

OUTPUT:

TITLE:
{translation.get('title', '')}

EXCERPT:
{translation.get('excerpt', '')}

TAGS:
{', '.join(translation.get('tags', []))}

CONTENT:
[improved translation]"""
    
    def _parse_response(self, response: str, original: Dict) -> Dict:
        """Parse structured response from translation/refinement agents.
        
        Handles multiple output formats:
        1. Section headers on separate lines (TITLE:\\n[text])
        2. Inline sections (TITLE: [text])
        3. Stops parsing at JSON blocks, code fences, or explanatory text
        
        Falls back to original values if sections are missing/empty.
        
        Args:
            response (str): API response text with structured sections.
            original (Dict): Original metadata for fallback values.
        
        Returns:
            Dict: Parsed translation with title, excerpt, tags, content.
        """
        result = {
            'title': original.get('title', ''),
            'excerpt': original.get('excerpt', ''),
            'tags': original.get('tags', []),
            'content': ''
        }
        
        lines = response.strip().split('\n')
        current = None
        buffer = []
        
        for line in lines:
            stripped = line.strip()
            upper = stripped.upper()
            
            # Skip empty lines when not in a section
            if not stripped and not current:
                continue
            
            # Skip "OUTPUT:" header if present
            if upper == 'OUTPUT:':
                continue
            
            # Check for section markers (with or without trailing content)
            if upper.startswith('TITLE:'):
                # Save previous section
                if current == 'content' and buffer:
                    result['content'] = '\n'.join(buffer).strip()
                elif current == 'excerpt' and buffer:
                    result['excerpt'] = ' '.join(buffer).strip()
                elif current == 'tags' and buffer:
                    result['tags'] = [t.strip() for t in ' '.join(buffer).split(',') if t.strip()]
                
                current = 'title'
                buffer = []
                # Check if title is on same line
                if len(stripped) > 6:
                    title_text = stripped[6:].strip()
                    if title_text:
                        buffer.append(title_text)
                continue
                
            elif upper.startswith('EXCERPT:'):
                if current == 'title' and buffer:
                    result['title'] = ' '.join(buffer).strip()
                current = 'excerpt'
                buffer = []
                # Check if excerpt is on same line
                if len(stripped) > 8:
                    excerpt_text = stripped[8:].strip()
                    if excerpt_text:
                        buffer.append(excerpt_text)
                continue
                
            elif upper.startswith('TAGS:'):
                if current == 'excerpt' and buffer:
                    result['excerpt'] = ' '.join(buffer).strip()
                current = 'tags'
                buffer = []
                # Check if tags are on same line
                if len(stripped) > 5:
                    tags_text = stripped[5:].strip()
                    if tags_text:
                        buffer.append(tags_text)
                continue
                
            elif upper.startswith('CONTENT:'):
                if current == 'tags' and buffer:
                    result['tags'] = [t.strip() for t in ' '.join(buffer).split(',') if t.strip()]
                current = 'content'
                buffer = []
                continue
            
            # Accumulate content for current section
            if current:
                buffer.append(line)
        
        # Process final section
        if current == 'content' and buffer:
            result['content'] = '\n'.join(buffer).strip()
        elif current == 'title' and buffer:
            result['title'] = ' '.join(buffer).strip()
        elif current == 'excerpt' and buffer:
            result['excerpt'] = ' '.join(buffer).strip()
        elif current == 'tags' and buffer:
            result['tags'] = [t.strip() for t in ' '.join(buffer).split(',') if t.strip()]
        
        return result
    
    def translate_about(self, about_text: Dict, force: bool = False) -> Optional[Dict]:
        """Translate About page content.
        
        Translates About page paragraphs with cache validation. Automatically
        retranslates if any paragraph is empty in cached version.
        
        Args:
            about_text (Dict): About page content with p1-p4 paragraph keys.
            force (bool): If True, bypasses cache and forces new translation.
        
        Returns:
            Optional[Dict]: Translation dict with p1-p4 keys for paragraphs.
                           None if translation fails.
        """
        content = json.dumps(about_text, sort_keys=True)
        content_hash = self._calculate_hash(content)
        slug = 'about-page'
        
        if not force:
            cached = self.cache.get_translation(slug, content_hash)
            if cached:
                # Check if any paragraph is empty - if so, retranslate
                has_empty = any(not cached.get(f'p{i}', '').strip() for i in range(1, 5))
                if has_empty:
                    print(f"   Cached About has empty content, retranslating")
                    force = True
                else:
                    print(f"   Content unchanged: About")
                    return cached
        
        print(f"   Translating: About")
        
        prompt = f"""Translate this About page content to natural Brazilian Portuguese.

RULES:
- Keep technical terms and company names (Nubank, CUDA, etc.) in original language as plain text - never wrap in backticks or quotes
- English technical terms should appear naturally within Portuguese sentences without special formatting
- Use natural Brazilian expressions and idioms
- "I'm Daniel" = "Me chamo Daniel" (not "Eu sou Daniel")
- Do NOT add explanations or extra text
- Output ONLY the sections below

INPUT:
Title: {about_text.get('title', '')}
P1: {about_text.get('p1', '')}
P2: {about_text.get('p2', '')}
P3: {about_text.get('p3', '')}
P4: {about_text.get('p4', '')}

OUTPUT FORMAT (provide ONLY these sections):

TITLE:
[translated title]

P1:
[translated paragraph 1]

P2:
[translated paragraph 2]

P3:
[translated paragraph 3]

P4:
[translated paragraph 4]"""
        
        response_text = self._call_api(prompt)
        if not response_text:
            return None
        
        translated = self._parse_about_response(response_text, about_text)
        
        # Post-process to remove backticks around English technical terms
        for key in ['title', 'p1', 'p2', 'p3', 'p4']:
            if translated.get(key):
                translated[key] = self._clean_backticks_from_text(translated[key])
        
        self.cache.store_translation(slug, content_hash, translated)
        return translated
    
    def _parse_about_response(self, response: str, original: Dict) -> Dict:
        """Parse About page translation response.
        
        Extracts translated title and paragraphs (p1-p4) from structured response.
        Falls back to original values if sections are missing.
        
        Args:
            response (str): API response with TITLE:/P1:/P2:/P3:/P4: sections.
            original (Dict): Original About content for fallback values.
        
        Returns:
            Dict: Parsed translation with title and p1-p4 paragraph keys.
        """
        result = {
            'title': original.get('title', ''),
            'p1': original.get('p1', ''),
            'p2': original.get('p2', ''),
            'p3': original.get('p3', ''),
            'p4': original.get('p4', '')
        }
        
        lines = response.strip().split('\n')
        current = None
        buffer = []
        
        for line in lines:
            upper = line.strip().upper()
            
            if upper == 'TITLE:':
                if current and buffer:
                    result[current] = '\n'.join(buffer).strip()
                current = 'title'
                buffer = []
            elif upper == 'P1:':
                if current == 'title' and buffer:
                    result['title'] = ' '.join(buffer).strip()
                current = 'p1'
                buffer = []
            elif upper == 'P2:':
                if current and buffer:
                    result[current] = '\n'.join(buffer).strip()
                current = 'p2'
                buffer = []
            elif upper == 'P3:':
                if current and buffer:
                    result[current] = '\n'.join(buffer).strip()
                current = 'p3'
                buffer = []
            elif upper == 'P4:':
                if current and buffer:
                    result[current] = '\n'.join(buffer).strip()
                current = 'p4'
                buffer = []
            else:
                if current:
                    buffer.append(line)
        
        if current and buffer:
            result[current] = '\n'.join(buffer).strip()
        
        return result
    
    def translate_if_needed(self, post: Dict, target_lang: str = 'pt') -> Optional[Dict]:
        """Translate complete post - returns translated post with Portuguese content"""
        if target_lang != 'pt':
            return post  # Return original for non-PT languages
        
        frontmatter = {
            'title': post.get('title', ''),
            'excerpt': post.get('excerpt', ''),
            'tags': post.get('tags', [])
        }
        
        # Use raw markdown content for translation, not HTML
        content_to_translate = post.get('raw_content', post.get('content', ''))
        
        translated = self.translate_post(
            post['slug'],
            frontmatter,
            content_to_translate,
            force=False
        )
        
        # If translation failed, return None
        if not translated:
            return None
        
        # Build translated post from translation results (works for both new and cached)
        translated_post = post.copy()
        translated_post['title'] = translated.get('title', post['title'])
        translated_post['excerpt'] = translated.get('excerpt', post['excerpt'])
        translated_post['tags'] = translated.get('tags', post['tags'])
        
        # Convert translated markdown to HTML
        import markdown as md_lib
        translated_html = md_lib.markdown(
            translated.get('content', post.get('raw_content', '')),
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        translated_post['content'] = translated_html
        
        return translated_post


def translate_if_needed(slug: str, frontmatter: Dict, content: str, force: bool = False) -> Optional[Dict]:
    """Entry point for post translation from build system.
    
    Convenience function that creates MultiAgentTranslator instance and
    handles initialization errors gracefully.
    
    Args:
        slug (str): Post identifier (filename without extension).
        frontmatter (Dict): Post metadata (title, excerpt, tags).
        content (str): Post content in Markdown/HTML.
        force (bool): If True, bypasses cache and forces new translation.
    
    Returns:
        Optional[Dict]: Translation dict with title/excerpt/tags/content,
                       or None if GEMINI_API_KEY not set or translation fails.
    """
    try:
        translator = MultiAgentTranslator()
        return translator.translate_post(slug, frontmatter, content, force=force)
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            return None
        raise
    except Exception as e:
        print(f"Translation error: {e}")
        return None
