#!/usr/bin/env python3
"""
Multi-Agent Translation Pipeline for Brazilian Portuguese

Three-stage pipeline:
1. Translation Agent: Translates English to PT-BR
2. Critique Agent: Reviews translation quality and semantic alignment
3. Refinement Agent: Applies feedback to improve translation
"""

import os
import re
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from google import genai
from google.genai import types
from dotenv import load_dotenv
from config import GEMINI_MODEL_CHAIN
from markdown_refs import render_markdown_with_internal_refs

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
TRANSLATION_CACHE_FILE = PROJECT_ROOT / "_cache" / "translation-cache.json"

# Rate limiting: Set to 90 seconds to ensure we NEVER hit API rate limits
# This is extremely conservative but guarantees stability
# Total time for 6 posts: ~9 minutes (6 posts × 90 seconds)
MIN_REQUEST_INTERVAL = 90.0  # seconds between API calls (ultra-safe margin)


# ---------------------------------------------------------------------------
# PT-aware translation glossary
# ---------------------------------------------------------------------------
# English terms that are commonly kept as-is in Brazilian Portuguese technical
# writing.  The validator uses this set to avoid false positives when checking
# whether a translation was actually performed.  All entries are stored in
# **lowercase** so lookups are case-insensitive.  Multi-word entries are
# matched as sub-strings after lower-casing the text under test.
TECH_GLOSSARY: set = {
    # AI / ML
    "machine learning",
    "deep learning",
    "data science",
    "mlops",
    "training",
    "inference",
    "model",
    "dataset",
    "benchmark",
    "feature",
    "batch",
    "streaming",
    "transformer",
    "fine-tuning",
    # Hardware / low-level
    "cuda",
    "gpu",
    "cpu",
    "kernel",
    "runtime",
    "hardware",
    "software",
    "thread",
    "overhead",
    # Infrastructure / DevOps
    "docker",
    "kubernetes",
    "cloud",
    "deploy",
    "pipeline",
    "backend",
    "frontend",
    "full-stack",
    "serverless",
    "microservice",
    "container",
    "orchestration",
    "stack",
    "cluster",
    "cache",
    "hash",
    "token",
    "endpoint",
    "ci/cd",
    "devops",
    "sre",
    "latency",
    "throughput",
    # Web / API
    "api",
    "rest",
    "graphql",
    "framework",
    "dashboard",
    "payload",
    "metadata",
    # Dev workflow
    "debug",
    "log",
    "commit",
    "merge",
    "branch",
    "pull request",
    "code review",
    "sprint",
    "agile",
    "scrum",
    # General tech
    "open source",
    "build",
    "tooling",
    "workflow",
    # Brand names / proper nouns
    "nubank",
    "picpay",
    "aws",
    "sagemaker",
    "kubeflow",
    "dagster",
    "gemini",
    "pytorch",
    "tensorflow",
    "python",
    "javascript",
    "github",
    "gitlab",
}

# Regex for fenced code blocks (``` … ```)
_RE_FENCED_CODE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
# Regex for inline code (`…`)
_RE_INLINE_CODE = re.compile(r"`[^`]+`")
# Regex for markdown / HTML tags we want to ignore during overlap analysis
_RE_MD_TAGS = re.compile(r"<[^>]+>|!\[.*?\]\(.*?\)|\[.*?\]\(.*?\)")

# Heading patterns that are expected to remain invariant across languages.
# These are ignored by untranslated-content checks.
_INVARIANT_HEADING_PATTERNS = (
    re.compile(r"^(?:#+\s*)?(?:\*\*)?\s*(?:fontes|sources)\s*:?(?:\*\*)?$", re.IGNORECASE),
    re.compile(r"^(?:#+\s*)?(?:\*\*)?\s*tl;dr\s*(?:\*\*)?$", re.IGNORECASE),
    re.compile(
        r"^(?:#+\s*)?(?:\*\*)?\s*view\s+transitions\s+api\s*:?(?:\*\*)?$",
        re.IGNORECASE,
    ),
)
_REFERENCE_ENTRY_PREFIX = re.compile(r"^\s*(?:\[\d+\]|\d+\.|;\s*)")

# ---------------------------------------------------------------------------
# Defense-in-depth: sanitize LLM-produced HTML
# ---------------------------------------------------------------------------
# Patterns that should NEVER appear in translated output.  These are matched
# case-insensitively against rendered HTML to guard against malformed model
# responses that could inject scripts or event handlers.
_RE_SCRIPT_TAG = re.compile(r"<\s*script[\s>].*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
_RE_SCRIPT_OPEN = re.compile(r"<\s*script[\s>]", re.IGNORECASE)
_RE_EVENT_HANDLER = re.compile(r"""\bon[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|\S+)""", re.IGNORECASE)
_RE_JAVASCRIPT_URI = re.compile(
    r"""(?:href|src|action)\s*=\s*"""
    r"""(?:"\s*javascript:[^"]*"|'\s*javascript:[^']*'|\s*javascript:\S*)""",
    re.IGNORECASE,
)


def sanitize_translation_html(html: str) -> str:
    """Strip dangerous HTML patterns from LLM-produced translation output.

    This is a defense-in-depth measure: the translation pipeline asks the
    model for markdown/plain text, but models can hallucinate HTML.  We
    strip ``<script>`` tags (complete and unclosed), inline event handlers
    (``onload``, ``onerror``, etc.), and ``javascript:`` URIs.

    The function intentionally does NOT strip all HTML — legitimate tags
    produced by the markdown renderer (``<p>``, ``<code>``, ``<a>``, etc.)
    must pass through.

    Args:
        html: Rendered HTML string from translated markdown.

    Returns:
        Sanitized HTML string.
    """
    html = _RE_SCRIPT_TAG.sub("", html)
    html = _RE_SCRIPT_OPEN.sub("&lt;script", html)
    html = _RE_EVENT_HANDLER.sub("", html)
    html = _RE_JAVASCRIPT_URI.sub("", html)
    return html


def sanitize_translation_text(text: str) -> str:
    """Strip HTML tags from text that should be plain (title, excerpt, tags).

    Translated titles and excerpts are interpolated into attribute values
    and text nodes.  Any embedded HTML would either break the template or
    create an injection vector.  This strips all ``<…>`` sequences.

    Args:
        text: Plain-text string from translation output.

    Returns:
        Cleaned text with angle-bracket sequences removed.
    """
    return re.sub(r"<[^>]*>", "", text)


def _strip_code_and_tags(text: str) -> str:
    """Remove fenced code blocks, inline code, and markdown/HTML tags.

    The returned text is suitable for natural-language comparison but should
    NOT be used as a rendered output.

    Args:
        text: Raw markdown/HTML text.

    Returns:
        Text with code and tags removed.
    """
    text = _RE_FENCED_CODE.sub("", text)
    text = _RE_INLINE_CODE.sub("", text)
    text = _RE_MD_TAGS.sub("", text)
    return text


def _remove_glossary_terms(text: str) -> str:
    """Remove TECH_GLOSSARY terms from *text* (case-insensitive).

    Multi-word glossary entries are removed first (longest-first) to prevent
    partial matches, then single-word entries.

    Args:
        text: Lowercased plain text.

    Returns:
        Text with glossary terms replaced by whitespace.
    """
    # Sort by length descending so "machine learning" is removed before
    # "machine" (if it were in the glossary).
    for term in sorted(TECH_GLOSSARY, key=len, reverse=True):
        text = text.replace(term, " ")
    return text


def _normalize_heading_candidate(text: str) -> str:
    """Normalize markdown heading-like text for invariant checks."""
    normalized = text.strip().lower()
    normalized = re.sub(r"^#+\s*", "", normalized)
    normalized = re.sub(r"^\*\*\s*|\s*\*\*$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _is_allowed_invariant_heading(text: str) -> bool:
    """Return True when *text* matches an allowed invariant heading pattern."""
    candidate = _normalize_heading_candidate(text)
    if not candidate:
        return False
    return any(pattern.match(candidate) for pattern in _INVARIANT_HEADING_PATTERNS)


def _is_reference_entry(text: str) -> bool:
    """Return True for bibliography/source-list fragments.

    Reference entries often preserve publisher names, source titles, product
    names, and URLs across locales. Treating them like prose creates false
    positives in untranslated-content checks.
    """
    candidate = text.strip()
    if not candidate:
        return False
    return bool(_REFERENCE_ENTRY_PREFIX.match(candidate))


def _word_set(text: str) -> set:
    """Return the set of non-trivial words in *text*.

    Strips punctuation and drops very short tokens (len <= 1) to reduce
    noise from articles and conjunctions.
    """
    return {w for w in re.findall(r"[a-záàâãéêíóôõúüç]+", text.lower()) if len(w) > 1}


def _split_sentences(text: str) -> List[str]:
    """Naively split text into sentences on period/exclamation/question mark.

    Returns only non-empty sentences.
    """
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


def normalize_locale(locale: str) -> str:
    """Normalize locale identifiers to lowercase hyphenated form."""
    return str(locale or "").strip().lower().replace("_", "-")


def validate_translation(
    original_en: str,
    translated_pt: str,
    *,
    source_locale: str = "en-us",
    target_locale: str = "pt-br",
) -> Tuple[bool, List[str]]:
    """Validate a translation for supported EN<->PT directions.

    Performs fast, offline checks designed to catch common translation
    failures (e.g. the model returning English instead of Portuguese)
    while respecting the fact that Brazilian Portuguese tech writing
    naturally retains many English terms.

    Checks performed:
        1. **Paragraph-level near-copy** – after stripping code and glossary
           terms, any paragraph with >70 % word overlap with the original is
           flagged as untranslated.
        2. **Consecutive identical sentences** – 3+ consecutive sentences
           that are *identical* in original and translation signal an
           untranslated block.
        3. **Malformed output** – unclosed fenced code blocks or unclosed
           HTML tags ``<tag>`` without ``</tag>``.
        4. **Suspiciously short translation** – translation < 50 % of
           original character count (warning, not failure).

    Args:
        original_en: Source text (markdown/HTML).
        translated_pt: Translated text (markdown/HTML).
        source_locale: Source locale (default: ``en-us``).
        target_locale: Target locale (default: ``pt-br``).

    Returns:
        Tuple of ``(is_valid, issues)`` where *is_valid* is ``False`` when
        hard errors are found and *issues* is a list of human-readable
        descriptions (errors prefixed with ``ERROR:`` and warnings with
        ``WARNING:``).
    """
    issues: List[str] = []

    source = normalize_locale(source_locale)
    target = normalize_locale(target_locale)
    run_untranslated_checks = (source.startswith("en") and target.startswith("pt")) or (
        source.startswith("pt") and target.startswith("en")
    )

    # -- 0. Trivial guard: empty translation is always invalid -----------
    if not translated_pt or not translated_pt.strip():
        return False, ["ERROR: translation is empty"]

    # -- 1. Strip code blocks/inline code for natural-language analysis --
    source_clean = _strip_code_and_tags(original_en)
    target_clean = _strip_code_and_tags(translated_pt)

    # -- 2. Paragraph-level near-copy detection --------------------------
    if run_untranslated_checks:
        source_paragraphs = [p.strip() for p in source_clean.split("\n\n") if p.strip()]
        target_paragraphs = [p.strip() for p in target_clean.split("\n\n") if p.strip()]

        for idx, (source_para, target_para) in enumerate(zip(source_paragraphs, target_paragraphs)):
            if source_para.strip() == target_para.strip() and _is_allowed_invariant_heading(
                source_para
            ):
                continue
            if _is_reference_entry(source_para) or _is_reference_entry(target_para):
                continue
            source_filtered = _remove_glossary_terms(source_para.lower())
            target_filtered = _remove_glossary_terms(target_para.lower())
            source_words = _word_set(source_filtered)
            target_words = _word_set(target_filtered)
            if not source_words:
                continue
            overlap = len(source_words & target_words) / len(source_words)
            if overlap > 0.70:
                snippet = source_para[:80].replace("\n", " ")
                issues.append(
                    f"ERROR: paragraph {idx + 1} appears untranslated "
                    f"({overlap:.0%} word overlap after removing glossary terms): "
                    f'"{snippet}…"'
                )

    # -- 3. Consecutive identical sentences (>3) -------------------------
    if run_untranslated_checks:
        source_sentences = _split_sentences(source_clean)
        target_sentences = _split_sentences(target_clean)

        consecutive = 0
        for source_sentence, target_sentence in zip(source_sentences, target_sentences):
            if _is_reference_entry(source_sentence) or _is_reference_entry(target_sentence):
                consecutive = 0
                continue
            if source_sentence.strip() == target_sentence.strip():
                if _is_allowed_invariant_heading(source_sentence):
                    consecutive = 0
                    continue
                consecutive += 1
                if consecutive > 3:
                    snippet = source_sentence.strip()[:80]
                    issues.append(
                        f"ERROR: {consecutive} consecutive identical sentences "
                        f"detected — section appears untranslated near: "
                        f'"{snippet}…"'
                    )
                    break
            else:
                consecutive = 0

    # -- 4. Malformed output checks --------------------------------------
    # 4a. Unclosed fenced code blocks (odd number of ``` delimiters)
    fence_count = len(re.findall(r"^```", translated_pt, re.MULTILINE))
    if fence_count % 2 != 0:
        issues.append(
            f"ERROR: unclosed fenced code block "
            f"({fence_count} ``` delimiter(s) found — expected even number)"
        )

    # 4b. Unclosed HTML tags (very simple heuristic: opening without closing)
    open_tags = re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b[^/>]*>", translated_pt)
    close_tags = re.findall(r"</([a-zA-Z][a-zA-Z0-9]*)\s*>", translated_pt)
    # Self-closing tags (br, hr, img, etc.) don't need closing
    void_tags = {
        "br",
        "hr",
        "img",
        "input",
        "meta",
        "link",
        "area",
        "base",
        "col",
        "embed",
        "source",
        "track",
        "wbr",
    }
    open_counts: Dict[str, int] = {}
    close_counts: Dict[str, int] = {}
    for tag in open_tags:
        t = tag.lower()
        if t not in void_tags:
            open_counts[t] = open_counts.get(t, 0) + 1
    for tag in close_tags:
        t = tag.lower()
        close_counts[t] = close_counts.get(t, 0) + 1
    for tag, count in open_counts.items():
        closed = close_counts.get(tag, 0)
        if count > closed:
            issues.append(f"ERROR: {count - closed} unclosed <{tag}> tag(s) in translation")

    # -- 5. Suspiciously short translation (warning only) ----------------
    source_len = len(original_en.strip())
    target_len = len(translated_pt.strip())
    if source_len > 0 and target_len < source_len * 0.50:
        issues.append(
            f"WARNING: translation is suspiciously short "
            f"({target_len} chars vs {source_len} original — "
            f"{target_len / source_len:.0%} of source length)"
        )

    has_errors = any(issue.startswith("ERROR:") for issue in issues)
    return (not has_errors, issues)


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
                with open(TRANSLATION_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save(self):
        """Persist cache to disk as JSON with UTF-8 encoding.

        Writes the entire cache dictionary to the cache file, overwriting
        any existing content. Uses indent=2 for human readability and
        ensure_ascii=False to preserve Unicode characters.
        """
        with open(TRANSLATION_CACHE_FILE, "w", encoding="utf-8") as f:
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
        if entry and isinstance(entry, dict) and entry.get("hash") == content_hash:
            return entry.get("translation")
        return None

    def store_translation(self, slug: str, content_hash: str, translation: Dict):
        """Store translation in cache and persist to disk.

        Args:
            slug (str): Post identifier.
            content_hash (str): SHA256 hash of source content.
            translation (Dict): Translation result containing title, excerpt,
                              tags, and content.
        """
        self.cache[slug] = {"hash": content_hash, "translation": translation}
        self.save()


class MultiAgentTranslator:
    """Three-stage translation pipeline using Gemini API with model fallback.

    This translator uses a multi-agent approach:
        1. Translation Agent: Translates English content to Brazilian Portuguese
        2. Critique Agent: Reviews translation for semantic accuracy and naturalness
        3. Refinement Agent: Applies feedback to improve translation quality

    Model fallback chain:
        API calls are attempted against each model in ``config.GEMINI_MODEL_CHAIN``
        in order.  When a model hits a rate-limit (429), quota exhaustion
        (RESOURCE_EXHAUSTED), or unavailability error and exhausts its per-model
        retry budget (default: 3 attempts), the next model in the chain is tried.
        Each fallback is logged so the build output shows which model is active.

    The pipeline includes:
        - Content-based caching to avoid redundant API calls
        - Rate limiting to respect API quotas (MIN_REQUEST_INTERVAL between calls)
        - Per-model retry with 90-second waits for quota errors
        - Natural Brazilian Portuguese output with technical terms in English

    Attributes:
        api_key (str): Gemini API key from environment.
        client: Google GenAI client instance.
        model_chain (list[str]): Ordered list of model names to try.
        model_name (str): Primary model name (first in chain; backward-compat).
        cache (TranslationCache): Persistent translation cache.
        enable_critique (bool): Whether to run critique/refinement stages.
        strict_validation (bool): Whether validation errors are fatal.
        last_api_call (float): Timestamp of last API call for rate limiting.
    """

    def __init__(self, enable_critique: bool = True, strict_validation: bool = False):
        """Initialize translator with API credentials and cache.

        Reads ``GEMINI_API_KEY`` from the environment and sets up the model
        fallback chain from ``config.GEMINI_MODEL_CHAIN``.

        Args:
            enable_critique (bool): If True, runs full 3-stage pipeline.
                                   If False, skips critique and refinement.
            strict_validation (bool): If True, translation validation errors
                                     cause translate_post() to return None.
                                     If False, validation issues are logged as
                                     warnings but translation is still returned.

        Raises:
            ValueError: If GEMINI_API_KEY environment variable is not set.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")

        self.client = genai.Client(
            api_key=self.api_key, http_options=types.HttpOptions(api_version="v1beta")
        )
        self.model_chain = GEMINI_MODEL_CHAIN
        self.model_name = self.model_chain[0]  # primary model (backward-compat reference)
        self.cache = TranslationCache()
        self.enable_critique = enable_critique
        self.strict_validation = strict_validation
        self.last_api_call = 0

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content for cache validation.

        Args:
            content (str): Content to hash (typically post content + frontmatter).

        Returns:
            str: Hexadecimal SHA256 hash string.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

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
        # Pattern: backtick, word characters/spaces/hyphens (2-30 chars), backtick
        # But NOT if preceded/followed by more backticks (code blocks)
        # This preserves code blocks (```) and inline code with actual code content
        pattern = r"(?<!`)` *([A-Za-z][\w\s\-]{1,30}?) *`(?!`)"

        # Replace backticks around simple technical terms
        cleaned = re.sub(pattern, r"\1", text)

        return cleaned

    def _rate_limit(self):
        """Enforce minimum interval between API calls.

        Blocks execution if insufficient time has passed since last API call.
        Uses MIN_REQUEST_INTERVAL (90 seconds) to stay under API rate limits.
        """
        elapsed = time.time() - self.last_api_call
        if elapsed < MIN_REQUEST_INTERVAL:
            sleep_time = MIN_REQUEST_INTERVAL - elapsed
            time.sleep(sleep_time)
        self.last_api_call = time.time()

    def _call_api(self, prompt: str, retries_per_model: int = 3) -> Optional[str]:
        """Call Gemini API with model fallback chain, rate limiting, and retry logic.

        Iterates through ``self.model_chain`` (defined in ``config.GEMINI_MODEL_CHAIN``).
        Each model is given ``retries_per_model`` attempts before the next model is
        tried.

        Error classification:
            - **Quota / rate-limit** (``429``, ``RESOURCE_EXHAUSTED``, ``quota``,
              ``unavailable``): wait 90 s then retry the same model; after all
              per-model attempts are exhausted, fall back to the next model.
            - **Other transient errors**: wait 10 s then retry the same model; after
              all per-model attempts are exhausted, raise immediately (these errors
              are not model-specific).

        Args:
            prompt (str): Translation prompt to send to Gemini.
            retries_per_model (int): Maximum attempts per model before falling back
                to the next one (default: 3).

        Returns:
            str: API response text.

        Raises:
            Exception: If all models exhaust all retries, or a non-quota error
                persists after the retry budget for that model is spent.
        """
        last_error: str = ""

        for model_idx, model_name in enumerate(self.model_chain):
            is_fallback = model_idx > 0
            if is_fallback:
                print(f"      [model] Falling back to: {model_name}")
            else:
                print(f"      [model] Using primary: {model_name}")

            for attempt in range(retries_per_model):
                try:
                    self._rate_limit()
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    if is_fallback:
                        print(f"      [model] Success with fallback model: {model_name}")
                    return response.text

                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg

                    is_quota_error = (
                        "429" in error_msg
                        or "RESOURCE_EXHAUSTED" in error_msg
                        or "quota" in error_msg.lower()
                        or "unavailable" in error_msg.lower()
                    )

                    print(
                        f"      Gemini API error [{model_name}, "
                        f"attempt {attempt + 1}/{retries_per_model}]: "
                        f"{error_msg[:400]}"
                    )

                    if is_quota_error:
                        if attempt < retries_per_model - 1:
                            print(
                                f"      Rate limit on {model_name} — "
                                f"waiting 90s for quota to reset..."
                            )
                            time.sleep(90)
                        else:
                            # This model's retry budget is spent; move to next.
                            next_model = (
                                self.model_chain[model_idx + 1]
                                if model_idx + 1 < len(self.model_chain)
                                else None
                            )
                            if next_model:
                                print(
                                    f"      [model] {model_name} exhausted "
                                    f"({retries_per_model} attempts) — "
                                    f"falling back to {next_model}"
                                )
                            else:
                                print(
                                    f"      FATAL: {model_name} exhausted and "
                                    f"no more fallback models available"
                                )
                            break  # break inner loop → advance to next model
                    else:
                        # Non-quota error: retry with short delay.
                        if attempt < retries_per_model - 1:
                            print(f"      Retrying in 10s ({attempt + 2}/{retries_per_model})...")
                            time.sleep(10)
                        else:
                            print(
                                f"      FATAL: {model_name} failed after "
                                f"{retries_per_model} attempts (non-quota error)"
                            )
                            raise Exception(f"Translation API failed: {error_msg}")

        raise Exception(
            f"Translation API exhausted all models in chain "
            f"({', '.join(self.model_chain)}). "
            f"Last error: {last_error}"
        )

    def _validate_and_log(
        self,
        slug: str,
        original_content: str,
        translation: Dict,
        *,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> bool:
        """Run translation validation and log results.

        Calls :func:`validate_translation` on the translated content and
        prints any issues.  Returns ``True`` when the translation may be
        used (either no errors, or non-strict mode where errors are
        demoted to warnings).

        Args:
            slug: Post identifier for log messages.
            original_content: English source content.
            translation: Translation dict (must contain ``content`` key).

        Returns:
            True if the translation should be accepted, False if it must
            be rejected (only in strict_validation mode).
        """
        translated_content = translation.get("content", "")
        is_valid, issues = validate_translation(
            original_content,
            translated_content,
            source_locale=source_locale,
            target_locale=target_locale,
        )

        if not issues:
            return True

        for issue in issues:
            print(f"      [validation] {slug}: {issue}")

        if not is_valid and self.strict_validation:
            print(f"      Validation FAILED for {slug} (strict mode) — translation rejected")
            return False

        return True

    def translate_post(
        self,
        slug: str,
        frontmatter: Dict,
        content: str,
        force: bool = False,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> Optional[Dict]:
        """Multi-agent translation pipeline for blog posts.

        Orchestrates the three-stage translation process:
            1. Initial translation to Brazilian Portuguese
            2. Quality critique (if enabled)
            3. Refinement based on feedback (if needed)

        After translation is produced (and optionally refined), the result
        is passed through :func:`validate_translation`.  In strict
        validation mode, validation errors cause the translation to be
        rejected (returns None).  In non-strict mode, issues are logged
        as warnings but the translation is still returned.

        Uses cache to avoid retranslating unchanged content. Automatically
        retranslates if cached translation has empty content field.

        Args:
            slug (str): Post identifier (filename without extension).
            frontmatter (Dict): Post metadata (title, excerpt, tags).
            content (str): Post body content in Markdown/HTML.
            force (bool): If True, bypasses cache and forces new translation.
            source_locale (str): Source locale identifier (e.g., en-us, pt-br).
            target_locale (str): Target locale identifier (e.g., pt-br, en-us).

        Returns:
            Optional[Dict]: Translation dict with title, excerpt, tags, content.
                           None if translation fails.
        """
        content_hash = self._calculate_hash(
            content + str(frontmatter) + f"|{source_locale}|{target_locale}"
        )
        # Backward-compatibility cache key from before locale direction was
        # included in the hash. This allows existing caches to be reused
        # without re-spending tokens, then migrated in-place.
        legacy_hash = self._calculate_hash(content + str(frontmatter))

        if not force:
            cached = self.cache.get_translation(slug, content_hash)
            if not cached:
                legacy_cached = self.cache.get_translation(slug, legacy_hash)
                if legacy_cached:
                    if not legacy_cached.get("content", "").strip():
                        print(f"   Cached translation has empty content, retranslating: {slug}")
                        force = True
                    else:
                        print(f"   Content unchanged (migrated cache): {slug}")
                        self.cache.store_translation(slug, content_hash, legacy_cached)
                        return legacy_cached
            if cached:
                # Check if cached translation has empty content - if so, retranslate
                if not cached.get("content", "").strip():
                    print(f"   Cached translation has empty content, retranslating: {slug}")
                    force = True
                else:
                    print(f"   Content unchanged: {slug}")
                    return cached

        print(f"   Translating: {slug}")

        translation = self._translate(
            frontmatter,
            content,
            source_locale=source_locale,
            target_locale=target_locale,
        )
        if not translation:
            return None

        if not self.enable_critique:
            print("      Translation complete (critique disabled)")
            if not self._validate_and_log(
                slug,
                content,
                translation,
                source_locale=source_locale,
                target_locale=target_locale,
            ):
                return None
            self.cache.store_translation(slug, content_hash, translation)
            return translation

        print("      Reviewing translation...")

        critique_result, feedback = self._critique(
            frontmatter,
            content,
            translation,
            source_locale=source_locale,
            target_locale=target_locale,
        )

        if critique_result == "OK":
            print("      Translation approved")
            if not self._validate_and_log(
                slug,
                content,
                translation,
                source_locale=source_locale,
                target_locale=target_locale,
            ):
                return None
            self.cache.store_translation(slug, content_hash, translation)
            return translation

        print("      Refining based on feedback...")

        refined = self._refine(
            frontmatter,
            content,
            translation,
            feedback,
            source_locale=source_locale,
            target_locale=target_locale,
        )

        if refined:
            print("      Translation refined")
            if not self._validate_and_log(
                slug,
                content,
                refined,
                source_locale=source_locale,
                target_locale=target_locale,
            ):
                return None
            self.cache.store_translation(slug, content_hash, refined)
            return refined

        print("      Using initial translation")
        if not self._validate_and_log(
            slug,
            content,
            translation,
            source_locale=source_locale,
            target_locale=target_locale,
        ):
            return None
        self.cache.store_translation(slug, content_hash, translation)
        return translation

    def _translate(
        self,
        frontmatter: Dict,
        content: str,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> Optional[Dict]:
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
        prompt = self._build_translation_prompt(
            frontmatter,
            content,
            source_locale=source_locale,
            target_locale=target_locale,
        )

        response_text = self._call_api(prompt)
        if not response_text:
            return None

        parsed = self._parse_response(response_text, frontmatter)

        # Post-process to remove backticks around English technical terms
        if parsed and parsed.get("content"):
            parsed["content"] = self._clean_backticks_from_text(parsed["content"])
        if parsed and parsed.get("title"):
            parsed["title"] = self._clean_backticks_from_text(parsed["title"])
        if parsed and parsed.get("excerpt"):
            parsed["excerpt"] = self._clean_backticks_from_text(parsed["excerpt"])

        return parsed

    def _critique(
        self,
        frontmatter: Dict,
        content: str,
        translation: Dict,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> Tuple[str, str]:
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
        prompt = self._build_critique_prompt(
            frontmatter,
            content,
            translation,
            source_locale=source_locale,
            target_locale=target_locale,
        )

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

    def _refine(
        self,
        frontmatter: Dict,
        content: str,
        translation: Dict,
        feedback: str,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> Optional[Dict]:
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
        prompt = self._build_refinement_prompt(
            frontmatter,
            content,
            translation,
            feedback,
            source_locale=source_locale,
            target_locale=target_locale,
        )

        response_text = self._call_api(prompt)
        if not response_text:
            return None

        refined = self._parse_response(response_text, frontmatter)

        # Post-process to remove backticks around English technical terms
        if refined and refined.get("content"):
            refined["content"] = self._clean_backticks_from_text(refined["content"])
        if refined and refined.get("title"):
            refined["title"] = self._clean_backticks_from_text(refined["title"])
        if refined and refined.get("excerpt"):
            refined["excerpt"] = self._clean_backticks_from_text(refined["excerpt"])

        return refined

    def _build_translation_prompt(
        self,
        frontmatter: Dict,
        content: str,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> str:
        """Build prompt for Stage 1 translation agent.

        Creates detailed prompt with translation rules, technical conventions,
        and strict output formatting requirements.

        Args:
            frontmatter (Dict): Post metadata (title, excerpt, tags).
            content (str): Post content to translate.

        Returns:
            str: Formatted translation prompt for Gemini API.
        """
        title = frontmatter.get("title", "")
        excerpt = frontmatter.get("excerpt", "")
        tags = ", ".join(frontmatter.get("tags", []))

        source = source_locale.lower()
        target = target_locale.lower()

        if target.startswith("pt"):
            style_rule = "Write as a bilingual Brazilian engineer would naturally speak"
            heading_rule = "TRANSLATE ALL section headings/titles to Portuguese (##, ###, etc.)"
            lexical_rule = (
                "TRANSLATE these common words to Portuguese: "
                "port/ports -> porta/portas, setup -> configuracao, network -> rede, "
                "traffic -> trafego, rule/rules -> regra/regras, mode -> modo, "
                "alert -> alerta, blocking -> bloqueio, segmentation -> segmentacao"
            )
            critical_rule = (
                "CRITICAL: English technical terms must appear as plain text within "
                "Portuguese sentences - never wrap them in backticks, quotes, or any "
                "other formatting"
            )
        elif target.startswith("en"):
            style_rule = "Write as a bilingual software engineer would naturally speak in English"
            heading_rule = "TRANSLATE ALL section headings/titles to English (##, ###, etc.)"
            lexical_rule = (
                "TRANSLATE these common words to English when they appear in Portuguese: "
                "porta/portas -> port/ports, configuracao -> setup, rede -> network, "
                "trafego -> traffic, regra/regras -> rule/rules, modo -> mode, "
                "alerta -> alert, bloqueio -> blocking, segmentacao -> segmentation"
            )
            critical_rule = (
                "CRITICAL: Keep technical terms as plain text in English sentences - "
                "never wrap them in backticks, quotes, or any other formatting"
            )
        else:
            style_rule = (
                f"Write naturally for target locale {target_locale}, preserving technical "
                "precision and tone"
            )
            heading_rule = (
                f"TRANSLATE ALL section headings/titles to {target_locale} (##, ###, etc.)"
            )
            lexical_rule = "Translate non-technical terms naturally to the target locale."
            critical_rule = (
                "CRITICAL: Keep technical terms as plain text when needed - no backticks, "
                "quotes, or extra formatting"
            )

        return f"""Translate this technical blog post from {source} to {target}.

TRANSLATION RULES:
- Source locale: {source}
- Target locale: {target}
- {style_rule}
- Keep ONLY these technical terms in English (no special formatting): GPU, CUDA, API, ML, AI, machine learning, deep learning, backend, frontend, framework, pipeline, cache, build, deploy, commit, debug, kernel, thread, hardware, software, benchmark, throughput, latency, overhead, runtime, tooling, workflow, endpoint, payload, metadata
- {lexical_rule}
- {heading_rule}
- {critical_rule}
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

    def _build_critique_prompt(
        self,
        frontmatter: Dict,
        content: str,
        translation: Dict,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> str:
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
        return f"""Compare the source content with the translation.

Source locale: {source_locale}
Target locale: {target_locale}

Check if they convey the same ideas, tone, and meaning.
Focus on naturalness in the target locale ({target_locale}) and fidelity to the source locale ({source_locale}).

ORIGINAL ({source_locale.upper()}):
Title: {frontmatter.get("title", "")}
Excerpt: {frontmatter.get("excerpt", "")}
Content: {content[:1500]}...

TRANSLATION ({target_locale.upper()}):
Title: {translation.get("title", "")}
Excerpt: {translation.get("excerpt", "")}
Content: {translation.get("content", "")[:1500]}...

If the translation is semantically aligned and sounds natural for {target_locale}, respond:
OK

If there are issues (wrong meaning, unnatural phrasing, missing content, wrong tone), respond:
FEEDBACK: [specific issues to fix]

Your response:"""

    def _build_refinement_prompt(
        self,
        frontmatter: Dict,
        content: str,
        translation: Dict,
        feedback: str,
        source_locale: str = "en-us",
        target_locale: str = "pt-br",
    ) -> str:
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
        return f"""Improve this translation based on feedback.

Source locale: {source_locale}
Target locale: {target_locale}

ORIGINAL ({source_locale.upper()}):
{content}

CURRENT TRANSLATION:
{translation.get("content", "")}

FEEDBACK:
{feedback}

Apply the feedback while maintaining natural language for {target_locale}.
Do not drift from the source meaning in {source_locale}.

OUTPUT:

TITLE:
{translation.get("title", "")}

EXCERPT:
{translation.get("excerpt", "")}

TAGS:
{", ".join(translation.get("tags", []))}

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
            "title": original.get("title", ""),
            "excerpt": original.get("excerpt", ""),
            "tags": original.get("tags", []),
            "content": "",
        }

        lines = response.strip().split("\n")
        current = None
        buffer = []

        for line in lines:
            stripped = line.strip()
            upper = stripped.upper()

            # Skip empty lines when not in a section
            if not stripped and not current:
                continue

            # Skip "OUTPUT:" header if present
            if upper == "OUTPUT:":
                continue

            # Check for section markers (with or without trailing content)
            if upper.startswith("TITLE:"):
                # Save previous section
                if current == "content" and buffer:
                    result["content"] = "\n".join(buffer).strip()
                elif current == "excerpt" and buffer:
                    result["excerpt"] = " ".join(buffer).strip()
                elif current == "tags" and buffer:
                    result["tags"] = [t.strip() for t in " ".join(buffer).split(",") if t.strip()]

                current = "title"
                buffer = []
                # Check if title is on same line
                if len(stripped) > 6:
                    title_text = stripped[6:].strip()
                    if title_text:
                        buffer.append(title_text)
                continue

            elif upper.startswith("EXCERPT:"):
                if current == "title" and buffer:
                    result["title"] = " ".join(buffer).strip()
                current = "excerpt"
                buffer = []
                # Check if excerpt is on same line
                if len(stripped) > 8:
                    excerpt_text = stripped[8:].strip()
                    if excerpt_text:
                        buffer.append(excerpt_text)
                continue

            elif upper.startswith("TAGS:"):
                if current == "excerpt" and buffer:
                    result["excerpt"] = " ".join(buffer).strip()
                current = "tags"
                buffer = []
                # Check if tags are on same line
                if len(stripped) > 5:
                    tags_text = stripped[5:].strip()
                    if tags_text:
                        buffer.append(tags_text)
                continue

            elif upper.startswith("CONTENT:"):
                if current == "tags" and buffer:
                    result["tags"] = [t.strip() for t in " ".join(buffer).split(",") if t.strip()]
                current = "content"
                buffer = []
                continue

            # Accumulate content for current section
            if current:
                buffer.append(line)

        # Process final section
        if current == "content" and buffer:
            result["content"] = "\n".join(buffer).strip()
        elif current == "title" and buffer:
            result["title"] = " ".join(buffer).strip()
        elif current == "excerpt" and buffer:
            result["excerpt"] = " ".join(buffer).strip()
        elif current == "tags" and buffer:
            result["tags"] = [t.strip() for t in " ".join(buffer).split(",") if t.strip()]

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
        slug = "about-page"

        if not force:
            cached = self.cache.get_translation(slug, content_hash)
            if cached:
                # Check if any paragraph is empty - if so, retranslate
                has_empty = any(not cached.get(f"p{i}", "").strip() for i in range(1, 5))
                if has_empty:
                    print("   Cached About has empty content, retranslating")
                    force = True
                else:
                    print("   Content unchanged: About")
                    return cached

        print("   Translating: About")

        prompt = f"""Translate this About page content to natural Brazilian Portuguese.

RULES:
- Keep technical terms and company names (Nubank, CUDA, etc.) in original language as plain text - never wrap in backticks or quotes
- English technical terms should appear naturally within Portuguese sentences without special formatting
- Use natural Brazilian expressions and idioms
- "I'm Daniel" = "Me chamo Daniel" (not "Eu sou Daniel")
- Do NOT add explanations or extra text
- Output ONLY the sections below

INPUT:
Title: {about_text.get("title", "")}
P1: {about_text.get("p1", "")}
P2: {about_text.get("p2", "")}
P3: {about_text.get("p3", "")}
P4: {about_text.get("p4", "")}

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
        for key in ["title", "p1", "p2", "p3", "p4"]:
            if translated.get(key):
                translated[key] = self._clean_backticks_from_text(translated[key])

        # Defense-in-depth: strip any dangerous patterns from LLM output.
        # About fields are plain text (interpolated into <p> and attributes).
        for key in ["title", "p1", "p2", "p3", "p4"]:
            if translated.get(key):
                translated[key] = sanitize_translation_text(translated[key])

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
            "title": original.get("title", ""),
            "p1": original.get("p1", ""),
            "p2": original.get("p2", ""),
            "p3": original.get("p3", ""),
            "p4": original.get("p4", ""),
        }

        lines = response.strip().split("\n")
        current = None
        buffer = []

        for line in lines:
            upper = line.strip().upper()

            if upper == "TITLE:":
                if current and buffer:
                    result[current] = "\n".join(buffer).strip()
                current = "title"
                buffer = []
            elif upper == "P1:":
                if current == "title" and buffer:
                    result["title"] = " ".join(buffer).strip()
                current = "p1"
                buffer = []
            elif upper == "P2:":
                if current and buffer:
                    result[current] = "\n".join(buffer).strip()
                current = "p2"
                buffer = []
            elif upper == "P3:":
                if current and buffer:
                    result[current] = "\n".join(buffer).strip()
                current = "p3"
                buffer = []
            elif upper == "P4:":
                if current and buffer:
                    result[current] = "\n".join(buffer).strip()
                current = "p4"
                buffer = []
            else:
                if current:
                    buffer.append(line)

        if current and buffer:
            result[current] = "\n".join(buffer).strip()

        return result

    def translate_cv(self, cv_data: Dict, force: bool = False) -> Optional[Dict]:
        """Translate CV content to Brazilian Portuguese.

        Translates the prose content of the CV (summary, descriptions,
        achievements, education degrees, languages spoken) while keeping
        technical terms, company names, skills, and contact info unchanged.

        Args:
            cv_data (Dict): CV data from load_cv_data() (cv_data.yaml).
            force (bool): If True, bypasses cache and forces new translation.

        Returns:
            Optional[Dict]: Translated CV data dict with same structure as input.
                           None if translation fails.
        """
        content = json.dumps(cv_data, sort_keys=True)
        content_hash = self._calculate_hash(content)
        slug = "cv-page"

        if not force:
            cached = self.cache.get_translation(slug, content_hash)
            if cached:
                # Validate cached data has the expected structure
                if cached.get("summary") and cached.get("experience"):
                    print("   Content unchanged: CV")
                    return cached
                else:
                    print("   Cached CV has incomplete data, retranslating")
                    force = True

        print("   Translating: CV")

        # Build experience block for the prompt
        experience_block = ""
        for i, exp in enumerate(cv_data.get("experience", []), 1):
            achievements_text = ""
            if exp.get("achievements"):
                achievements_text = "\n".join(f"  - {a}" for a in exp["achievements"])
                achievements_text = f"\n  Achievements:\n{achievements_text}"
            experience_block += f"""
EXP_{i}:
  Company: {exp.get("company", "")}
  Title: {exp.get("title", "")}
  Period: {exp.get("period", "")}
  Location: {exp.get("location", "")}
  Description: {exp.get("description", "")}{achievements_text}
"""

        # Build education block
        education_block = ""
        for i, edu in enumerate(cv_data.get("education", []), 1):
            education_block += f"""
EDU_{i}:
  Degree: {edu.get("degree", "")}
  School: {edu.get("school", "")}
  Period: {edu.get("period", "")}
"""

        # Build languages block
        languages_block = "\n".join(cv_data.get("languages_spoken", []))

        prompt = f"""Translate this CV/resume content to natural Brazilian Portuguese.

RULES:
- CRITICAL: Maintain FIRST-PERSON voice throughout. The author is describing their own work.
  English CVs often use implicit first-person ("Led the team", "Built pipelines").
  In Portuguese, use explicit first-person: "Liderei a equipe", "Construí pipelines".
  NEVER use third-person ("Liderou", "Construiu") — this is MY resume, not someone else describing me.
- Keep company names (Nubank, PicPay, M4U, Oi S.A, frete.com, etc.) EXACTLY as they are
- Keep technical terms (MLOps, CUDA, GPU, AWS, SageMaker, Kubeflow, Dagster, etc.) in English
- Keep job titles in English (Machine Learning Engineer, Senior Machine Learning Engineer, etc.)
- Keep proper nouns and product names unchanged
- Keep date periods EXACTLY as they are (e.g. "September 2023 - Present")
- Keep location names unchanged
- Keep school names unchanged
- Translate descriptions, achievements, and summary to natural Brazilian Portuguese
- Translate degree names to Portuguese
- Translate language proficiency descriptions to Portuguese
- Do NOT add explanations or extra text
- Output ONLY the sections below in the exact format specified

INPUT:

TAGLINE: {cv_data.get("tagline", "")}

SUMMARY: {cv_data.get("summary", "")}

EXPERIENCE:
{experience_block}

EDUCATION:
{education_block}

LANGUAGES_SPOKEN:
{languages_block}

OUTPUT FORMAT (provide ONLY these sections, keep the exact labels):

TAGLINE:
[translated tagline]

SUMMARY:
[translated summary]

{self._build_cv_output_format(cv_data)}"""

        response_text = self._call_api(prompt)
        if not response_text:
            return None

        translated = self._parse_cv_response(response_text, cv_data)

        # Post-process to remove backticks
        for key in ["tagline", "summary"]:
            if translated.get(key):
                translated[key] = self._clean_backticks_from_text(translated[key])
        for exp in translated.get("experience", []):
            if exp.get("description"):
                exp["description"] = self._clean_backticks_from_text(exp["description"])
            exp["achievements"] = [
                self._clean_backticks_from_text(a) for a in exp.get("achievements", [])
            ]

        # Defense-in-depth: strip any dangerous patterns from LLM output.
        # CV fields are plain text (interpolated into text nodes/attributes).
        for key in ["tagline", "summary"]:
            if translated.get(key):
                translated[key] = sanitize_translation_text(translated[key])
        for exp in translated.get("experience", []):
            for fld in ["title", "company", "location", "description", "period"]:
                if exp.get(fld):
                    exp[fld] = sanitize_translation_text(exp[fld])
            exp["achievements"] = [
                sanitize_translation_text(a) for a in exp.get("achievements", [])
            ]
        for edu in translated.get("education", []):
            for fld in ["degree", "school", "period"]:
                if edu.get(fld):
                    edu[fld] = sanitize_translation_text(edu[fld])
        translated["languages_spoken"] = [
            sanitize_translation_text(language)
            for language in translated.get("languages_spoken", [])
        ]

        self.cache.store_translation(slug, content_hash, translated)
        return translated

    def _build_cv_output_format(self, cv_data: Dict) -> str:
        """Build the expected output format section of the CV translation prompt.

        Args:
            cv_data (Dict): Original CV data to determine number of entries.

        Returns:
            str: Prompt section describing expected output format.
        """
        lines = []
        for i, exp in enumerate(cv_data.get("experience", []), 1):
            ach_lines = ""
            if exp.get("achievements"):
                ach_lines = "\n".join("  - [translated achievement]" for _ in exp["achievements"])
                ach_lines = f"\n  Achievements:\n{ach_lines}"
            lines.append(f"""EXP_{i}:
  Description: [translated description]{ach_lines}
""")

        for i in range(1, len(cv_data.get("education", [])) + 1):
            lines.append(f"""EDU_{i}:
  Degree: [translated degree]
""")

        lines.append("""LANGUAGES_SPOKEN:
[translated language 1]
[translated language 2]
...""")

        return "\n".join(lines)

    def _parse_cv_response(self, response: str, original: Dict) -> Dict:
        """Parse CV translation response into structured data.

        Extracts translated fields from the structured API response and
        merges them back into the original CV data structure, preserving
        all untranslated fields (names, dates, contacts, skills).

        Args:
            response (str): API response with labeled sections.
            original (Dict): Original CV data for fallback/untranslated fields.

        Returns:
            Dict: Complete translated CV data with same structure as input.
        """
        import re as re_mod

        result = {
            "name": original.get("name", ""),
            "tagline": original.get("tagline", ""),
            "location": original.get("location", ""),
            "contact": original.get("contact", {}),
            "skills": original.get("skills", []),
            "languages_spoken": list(original.get("languages_spoken", [])),
            "summary": original.get("summary", ""),
            "experience": [dict(exp) for exp in original.get("experience", [])],
            "education": [dict(edu) for edu in original.get("education", [])],
        }

        # Extract TAGLINE
        tagline_match = re_mod.search(r"TAGLINE:\s*\n(.+)", response)
        if tagline_match:
            result["tagline"] = tagline_match.group(1).strip()

        # Extract SUMMARY (everything between SUMMARY: and next top-level section)
        summary_match = re_mod.search(r"SUMMARY:\s*\n(.*?)(?=\nEXP_1:|$)", response, re_mod.DOTALL)
        if summary_match:
            result["summary"] = summary_match.group(1).strip()

        # Extract each EXP_N block
        for i in range(len(result["experience"])):
            exp_num = i + 1
            next_section = (
                f"EXP_{exp_num + 1}:" if exp_num < len(result["experience"]) else "EDU_1:"
            )
            pattern = rf"EXP_{exp_num}:\s*\n(.*?)(?=\n{re_mod.escape(next_section)}|$)"
            exp_match = re_mod.search(pattern, response, re_mod.DOTALL)

            if exp_match:
                exp_block = exp_match.group(1)

                # Extract description
                desc_match = re_mod.search(
                    r"Description:\s*(.+?)(?=\n\s*Achievements:|$)",
                    exp_block,
                    re_mod.DOTALL,
                )
                if desc_match:
                    result["experience"][i]["description"] = desc_match.group(1).strip()

                # Extract achievements
                ach_match = re_mod.search(r"Achievements:\s*\n(.*)", exp_block, re_mod.DOTALL)
                if ach_match:
                    ach_text = ach_match.group(1)
                    achievements = []
                    for line in ach_text.split("\n"):
                        line = line.strip()
                        if line.startswith("- "):
                            achievements.append(line[2:].strip())
                        elif line.startswith("* "):
                            achievements.append(line[2:].strip())
                    if achievements:
                        result["experience"][i]["achievements"] = achievements

        # Extract education degrees
        for i in range(len(result["education"])):
            edu_num = i + 1
            next_section = (
                f"EDU_{edu_num + 1}:" if edu_num < len(result["education"]) else "LANGUAGES_SPOKEN:"
            )
            pattern = rf"EDU_{edu_num}:\s*\n(.*?)(?=\n{re_mod.escape(next_section)}|$)"
            edu_match = re_mod.search(pattern, response, re_mod.DOTALL)

            if edu_match:
                edu_block = edu_match.group(1)
                degree_match = re_mod.search(r"Degree:\s*(.+)", edu_block)
                if degree_match:
                    result["education"][i]["degree"] = degree_match.group(1).strip()

        # Extract translated languages spoken
        lang_match = re_mod.search(r"LANGUAGES_SPOKEN:\s*\n(.*)", response, re_mod.DOTALL)
        if lang_match:
            lang_lines = [
                language.strip()
                for language in lang_match.group(1).strip().split("\n")
                if language.strip()
            ]
            if lang_lines:
                result["languages_spoken"] = lang_lines

        return result

    def translate_if_needed(self, post: Dict, target_locale: str = "pt-br") -> Optional[Dict]:
        """Translate complete post to the requested target locale."""
        source_locale = str(post.get("lang") or "en-us")
        if source_locale.lower() == target_locale.lower():
            return post

        frontmatter = {
            "title": post.get("title", ""),
            "excerpt": post.get("excerpt", ""),
            "tags": post.get("tags", []),
        }

        # Use raw markdown content for translation, not HTML
        content_to_translate = post.get("raw_content", post.get("content", ""))

        translated = self.translate_post(
            post["slug"],
            frontmatter,
            content_to_translate,
            force=False,
            source_locale=source_locale,
            target_locale=target_locale,
        )

        # If translation failed, return None
        if not translated:
            return None

        # Build translated post from translation results (works for both new and cached)
        translated_post = post.copy()
        translated_post["lang"] = target_locale
        translated_post["title"] = sanitize_translation_text(translated.get("title", post["title"]))
        translated_post["excerpt"] = sanitize_translation_text(
            translated.get("excerpt", post["excerpt"])
        )
        translated_post["tags"] = [
            sanitize_translation_text(t) for t in translated.get("tags", post["tags"])
        ]

        # Convert translated markdown to HTML, then sanitize
        translated_markdown = translated.get("content", post.get("raw_content", ""))
        translated_html = render_markdown_with_internal_refs(
            translated_markdown,
            source_markdown=content_to_translate,
        )
        translated_post["raw_content"] = translated_markdown
        translated_post["content"] = sanitize_translation_html(translated_html)

        return translated_post


def translate_if_needed(
    slug: str,
    frontmatter: Dict,
    content: str,
    force: bool = False,
    enable_critique: bool = True,
    strict_validation: bool = False,
    source_locale: str = "en-us",
    target_locale: str = "pt-br",
) -> Optional[Dict]:
    """Entry point for post translation from build system.

    Convenience function that creates MultiAgentTranslator instance and
    handles initialization errors gracefully.

    Args:
        slug (str): Post identifier (filename without extension).
        frontmatter (Dict): Post metadata (title, excerpt, tags).
        content (str): Post content in Markdown/HTML.
        force (bool): If True, bypasses cache and forces new translation.
        enable_critique (bool): Whether to run critique/refinement stages.
        strict_validation (bool): Whether validation errors are fatal.

    Returns:
        Optional[Dict]: Translation dict with title/excerpt/tags/content,
                       or None if GEMINI_API_KEY not set or translation fails.
    """
    try:
        translator = MultiAgentTranslator(
            enable_critique=enable_critique,
            strict_validation=strict_validation,
        )
        return translator.translate_post(
            slug,
            frontmatter,
            content,
            force=force,
            source_locale=source_locale,
            target_locale=target_locale,
        )
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            return None
        raise
    except Exception as e:
        print(f"Translation error: {e}")
        return None
