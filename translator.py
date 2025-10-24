#!/usr/bin/env python3
"""
Translation Module - Gemini-powered PT-BR translation for blog posts
Implements incremental translation with caching to avoid redundant API calls
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
GEMINI_MODEL = "gemini-2.0-flash-exp"  # Using latest flash model

class TranslationCache:
    """Manages translation cache to avoid redundant API calls"""
    
    def __init__(self):
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing translation cache"""
        if TRANSLATION_CACHE_FILE.exists():
            try:
                with open(TRANSLATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self):
        """Save translation cache to disk"""
        with open(TRANSLATION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def get_translation(self, slug: str, content_hash: str) -> Optional[Dict]:
        """Get cached translation if content hasn't changed"""
        if slug in self.cache:
            cached = self.cache[slug]
            if cached.get('content_hash') == content_hash:
                return cached.get('translation')
        return None
    
    def set_translation(self, slug: str, content_hash: str, translation: Dict):
        """Cache translation with content hash"""
        self.cache[slug] = {
            'content_hash': content_hash,
            'translation': translation
        }
        self.save()


class GeminiTranslator:
    """Handles translation using Google's Gemini API"""
    
    def __init__(self):
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
        """Calculate MD5 hash of content for change detection"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def translate_post(self, slug: str, frontmatter: Dict, content: str, force: bool = False) -> Dict:
        """
        Translate a blog post from English to PT-BR
        
        Args:
            slug: Post identifier
            frontmatter: Post metadata (title, excerpt, tags, etc.)
            content: Markdown content body
            force: Force re-translation even if cached
        
        Returns:
            Dict with translated frontmatter and content
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
    
    def _build_translation_prompt(self, frontmatter: Dict, content: str) -> str:
        """Build comprehensive translation prompt for Gemini"""
        return f"""You are a professional technical translator specializing in AI, engineering, and design content.

Translate the following blog post from English to Brazilian Portuguese (PT-BR).

**CRITICAL INSTRUCTIONS:**
1. **Tone**: Maintain the natural, precise, and calm voice of the original. Do not embellish or rewrite.
2. **Technical Terms**: Keep English technical terms for AI, engineering, or design when they are commonly used in Portuguese tech communities (e.g., "machine learning", "deep learning", "GPU", "CUDA", "distributed training", "View Transitions", "FLIP animation"). Only translate if it significantly improves readability.
3. **Formatting**: Preserve ALL Markdown formatting exactly (headers, lists, code blocks, links, emphasis).
4. **Structure**: Maintain paragraph breaks, line spacing, and document flow.
5. **Code**: Never translate code blocks, variable names, or technical identifiers.
6. **Style**: Natural Brazilian Portuguese, avoiding literal translations that sound awkward.

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
        """Parse Gemini's response into structured translation"""
        lines = response.strip().split('\n')
        
        result = {
            'title': original_frontmatter.get('title', ''),
            'excerpt': original_frontmatter.get('excerpt', ''),
            'tags': original_frontmatter.get('tags', []),
            'content': ''
        }
        
        current_section = None
        content_lines = []
        
        for line in lines:
            line_upper = line.strip().upper()
            
            if line_upper == 'TITLE:':
                current_section = 'title'
                continue
            elif line_upper == 'EXCERPT:':
                current_section = 'excerpt'
                continue
            elif line_upper == 'TAGS:':
                current_section = 'tags'
                continue
            elif line_upper == 'CONTENT:':
                current_section = 'content'
                continue
            
            if current_section == 'title' and line.strip():
                result['title'] = line.strip()
                current_section = None
            elif current_section == 'excerpt' and line.strip():
                result['excerpt'] = line.strip()
                current_section = None
            elif current_section == 'tags' and line.strip():
                result['tags'] = [tag.strip() for tag in line.split(',')]
                current_section = None
            elif current_section == 'content':
                content_lines.append(line)
        
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
