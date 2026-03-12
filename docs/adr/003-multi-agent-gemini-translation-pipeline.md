# ADR 3: Multi-Agent Gemini Translation Pipeline

## Context

The dan.rio blog is a bilingual site serving English and Brazilian Portuguese audiences. The author writes exclusively in English, so every post, the About page, and the CV must be translated to PT-BR before the site can be published. Doing this by hand would make publishing unsustainable: each post would require a fluent translator, and any content edit would require re-translation. The translation must therefore happen automatically at build time, producing natural Brazilian Portuguese that reads as if written by a bilingual engineer rather than passed through a machine.

Because the build system is a custom Python static site generator with no framework dependencies, the translation solution must integrate directly into the build pipeline defined in `_source/build.py`. The translated output is rendered to HTML and committed to the repository for GitHub Pages, which means LLM-generated content is inserted into the site's markup. This creates a security surface: a model could hallucinate script tags, event handlers, or javascript URIs into what should be prose. The build already converts Markdown to HTML via the `markdown` library, so any injected HTML would survive into the final pages unless explicitly stripped.

Google Gemini was selected as the translation provider because of its generous free tier, long context window, and strong multilingual performance. However, free-tier Gemini imposes aggressive rate limits, and model availability can be unpredictable. A single model failure during a build that translates six posts would leave the site half-translated. The system needs to tolerate quota exhaustion and temporary outages without operator intervention.

Finally, translation is the most expensive step in the build, both in wall-clock time and API cost. Retranslating unchanged content on every build is wasteful. The system needs a caching mechanism that can determine, cheaply and reliably, whether a post's source material has changed since its last successful translation.

## Decision

We will implement a three-stage LLM translation pipeline in `_source/translator.py`, organized as translate, critique, and refine agents. The translation agent receives the English frontmatter and Markdown body and produces a structured response with translated title, excerpt, tags, and content. The critique agent compares the translation against the original for semantic alignment, tone, and naturalness, returning either an approval or specific feedback. The refinement agent applies the critique feedback to produce an improved translation. Each stage is a separate Gemini API call with a purpose-built prompt.

We will disable the critique and refinement stages by default. In `_source/build.py`, the translator is initialized with `enable_critique=False` unless the operator passes the `--strict` flag or sets `STRICT_BUILD=1`. This means default builds use only the translation agent, making them roughly three times faster per post. The full pipeline is available for release-quality builds where translation fidelity justifies the extra time.

We will implement a model fallback chain configured in `_source/config.py` as `GEMINI_MODEL_CHAIN`, currently set to gemini-3-flash-preview, gemini-2.5-flash, and gemini-3.1-flash-lite. The `_call_api` method in the `MultiAgentTranslator` class iterates through this chain: each model gets three retry attempts with 90-second waits on quota errors before the next model is tried. Non-quota errors retry with a 10-second backoff. Only after all models exhaust all retries does the build fail.

We will enforce a 90-second minimum interval between all API calls via the `_rate_limit` method. This is deliberately conservative, prioritizing build stability over speed. For a six-post site, this means roughly nine minutes of wall-clock time for a full translation pass, but it guarantees the build never trips Gemini's rate limiter.

We will cache translations in `_cache/translation-cache.json`, keyed by post slug and a SHA-256 hash of the post content concatenated with its frontmatter. The `TranslationCache` class checks the hash on every build: if it matches, the cached translation is returned without any API call. This makes incremental builds near-instant when content has not changed. The same hashing approach is used in `_source/content_loader.py` for change detection in the sidecar metadata manifest.

We will validate every translation, whether freshly generated or loaded from cache, using the `validate_translation` function. This performs four offline checks: paragraph-level word overlap detection (flagging paragraphs with more than 70% word overlap after removing a curated technical glossary), consecutive identical sentence detection (three or more in a row signals an untranslated block), malformed output checks for unclosed code fences and HTML tags, and a length ratio warning for suspiciously short translations. In strict mode, validation errors are fatal and reject the translation. In default mode, they are logged as warnings.

We will apply defense-in-depth HTML sanitization to all LLM output before it reaches the final HTML. The `sanitize_translation_html` function strips script tags (both complete and unclosed), inline event handlers, and javascript URIs from translated body content. The `sanitize_translation_text` function strips all HTML tags from fields that should be plain text, such as titles, excerpts, and tags. These functions are applied in both `translate_if_needed` and `translate_about`, ensuring that no translation path bypasses sanitization.

## Status

Accepted.

## Consequences

The translation pipeline enables fully automated bilingual publishing. The author writes a post in English, runs the build, and gets both language versions without any manual translation step. The SHA-256 caching means that a typical build where only one post changed makes a single API call rather than retranslating the entire site, keeping both cost and latency low for iterative development.

The model fallback chain gives the build meaningful resilience against Gemini's unpredictable availability. In practice, when the primary preview model hits its free-tier quota, the build silently falls back to the stable Flash model and continues. The operator sees a log line noting the fallback but does not need to intervene. This has prevented several build failures that would otherwise have required manual retries or configuration changes.

The validation layer catches a real failure mode: Gemini occasionally returns untranslated English paragraphs, particularly in heavily technical sections where the model appears to decide the content is "already correct." The 70% word-overlap check, combined with the technical glossary that removes expected English loanwords like "machine learning" and "pipeline" from the comparison, reliably detects these failures while avoiding false positives on legitimately English-heavy passages.

The sanitization layer addresses the trust boundary between the LLM and the site's HTML output. While Gemini has not been observed injecting malicious content, the defense-in-depth approach means a compromised or misbehaving model cannot introduce script execution into the published site. This is a meaningful guarantee given that the translated HTML is committed to the repository and served to visitors without further processing.

The primary cost of this design is complexity. At roughly 1,700 lines, `_source/translator.py` is by far the largest module in the build system, larger than the build orchestrator, renderer, and content loader combined. It contains prompt engineering, response parsing, caching, rate limiting, retry logic, validation heuristics, and sanitization, all interleaved. A simpler system using a commercial translation API like DeepL would require perhaps a tenth of this code, at the cost of a paid subscription and less control over translation style. Human translation was considered and rejected on the grounds of turnaround time and the author's desire for instant publish cycles, though it remains the quality ceiling against which the pipeline's output should be measured.

The 90-second rate limit makes builds sequential and slow. A full retranslation of six posts takes approximately nine minutes even when the API responds instantly. This is acceptable for a small site but would not scale to dozens of posts without parallelization or a paid API tier with higher rate limits. The rate limit is a module-level constant and could be reduced if the API tier changes, but the current value reflects a deliberate choice to never encounter a quota error during a build.

The prompt-based architecture is inherently fragile. The translation, critique, and refinement prompts encode specific formatting expectations (section headers like "TITLE:", "CONTENT:") that the response parser depends on. If a Gemini model update changes how it interprets these prompts, the parser could silently produce empty or malformed translations. The validation layer mitigates this to some degree, but a model that returns well-formed Portuguese in an unexpected format would bypass validation and produce a broken page. There is no contract enforcement beyond string matching on the LLM's output.
