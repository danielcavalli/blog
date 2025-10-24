# Bilingual Blog Architecture

## Overview
The blog now supports automatic English/Portuguese language detection with smooth transitions between languages. The system uses Google's Gemini API for high-quality technical translations with intelligent caching to minimize API costs.

## Directory Structure

```
blog/
├── index.html                    # Root: auto-detects language & redirects
├── en/                           # English site
│   ├── index.html
│   ├── about.html
│   └── blog/
│       ├── post-1.html
│       └── post-2.html
├── pt/                           # Portuguese site
│   ├── index.html
│   ├── about.html
│   └── blog/
│       ├── post-1.html
│       └── post-2.html
├── blog-posts/                   # Source markdown (English)
│   ├── post-1.md
│   └── post-2.md
├── styles.css                    # Shared styles
├── theme.js                      # Theme toggle logic
├── transitions.js                # View Transitions API
├── filter.js                     # Post filtering
├── build.py                      # Build system
├── config.py                     # Site configuration
├── translator.py                 # Gemini translation module
├── translation-cache.json        # Translation cache (gitignored)
├── post-metadata.json            # Post metadata & timestamps
├── .env                          # API keys (gitignored)
└── requirements.txt              # Python dependencies
```

## Key Components

### 1. Root Index (Auto Language Detection)

**File**: `index.html` (root)

Automatically detects user's browser language:
- Brazilian Portuguese (`pt-*`) → redirects to `/pt/index.html`
- All other languages → redirects to `/en/index.html`
- Fallback: `<noscript>` redirects to English

```javascript
const userLang = navigator.language || navigator.userLanguage;
const isBrazilian = userLang.toLowerCase().startsWith('pt');
const targetLang = isBrazilian ? 'pt' : 'en';
window.location.href = `/${targetLang}/index.html`;
```

### 2. Language Toggle Button

**Location**: Top navigation bar (all pages)

**Features**:
- Globe icon with language label
- Links directly to equivalent page in other language
- Smooth 180° rotation on hover
- Works with View Transitions API for smooth cross-fade

**Implementation**:
```python
def generate_lang_toggle_html(current_lang: str, current_page: str) -> str:
    other_lang = get_alternate_lang(current_lang)
    other_lang_label = LANGUAGES[other_lang]['label']
    other_lang_path = get_lang_path(other_lang, current_page)
    return f'''<a href="{other_lang_path}" class="lang-toggle">...</a>'''
```

### 3. Translation System

**File**: `translator.py`

**Architecture**:
```
GeminiTranslator
├── translate_post() - Core translation with caching
├── translate_if_needed() - Post dict convenience method
└── TranslationCache - Content hash-based caching
```

**Caching Strategy**:
- Uses MD5 hash of English content
- Only re-translates if content changes
- Cache stored in `translation-cache.json`
- Reduces API costs to zero for unchanged posts

**Translation Prompt**:
- Maintains technical English terms (ML, GPU, CUDA, etc.)
- Preserves Markdown formatting exactly
- Natural Brazilian Portuguese style
- Separates title, excerpt, tags, content

### 4. Build Pipeline

**File**: `build.py`

**Process**:
1. Parse English markdown posts
2. Translate each post to Portuguese (with caching)
3. Generate English site in `/en/`
4. Generate Portuguese site in `/pt/`
5. Generate root `index.html` with language detection

**Key Functions**:
```python
generate_post_html(post, post_number, lang='en')
generate_index_html(posts, lang='en')
generate_about_html(lang='en')
generate_post_card(post, post_number, lang='en')
generate_root_index()  # Root language detector
```

### 5. Configuration

**File**: `config.py`

```python
LANGUAGES = {
    'en': {
        'name': 'English',
        'code': 'en',
        'dir': 'en',
        'label': 'EN'
    },
    'pt': {
        'name': 'Português',
        'code': 'pt-BR',
        'dir': 'pt',
        'label': 'PT'
    }
}

DEFAULT_LANGUAGE = 'en'
```

## Path Generation

All paths are language-aware:

```python
def get_lang_path(lang: str, path: str = '') -> str:
    """Generate language-specific path"""
    return f"/en/{path}" if lang == 'en' else f"/pt/{path}"
```

**Examples**:
- Blog post: `/en/blog/post-slug.html` → `/pt/blog/post-slug.html`
- Index: `/en/index.html` → `/pt/index.html`
- About: `/en/about.html` → `/pt/about.html`

## Dependencies

```
markdown>=3.5.0              # Markdown parsing
python-frontmatter>=1.0.0    # YAML frontmatter
google-generativeai>=0.3.0   # Gemini API
python-dotenv>=1.0.0         # Environment variables
```

## Environment Variables

**File**: `.env` (not committed)

```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_PROJECT_ID=your_project_id_here
```

Get API key: https://aistudio.google.com/app/apikey

## CSS Changes

**File**: `styles.css`

```css
.lang-toggle {
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0 0.75rem;
    /* ... */
}

.lang-toggle:hover svg {
    transform: rotate(180deg);
}
```

## Metadata Tracking

**File**: `post-metadata.json`

Tracks creation/update dates and content hashes:
```json
{
  "post-slug": {
    "created_date": "2025-01-15T10:30:00",
    "updated_date": "2025-01-20T14:45:00",
    "content_hash": "abc123..."
  }
}
```

## Translation Quality

**Preserved Elements**:
- Technical terms (machine learning, GPU, CUDA, View Transitions, FLIP)
- Code blocks (never translated)
- Markdown formatting (headers, lists, links, emphasis)
- Document structure (paragraph breaks, spacing)

**Translated Elements**:
- Natural language text
- Article titles and excerpts
- Tags (when appropriate)

## Cost Optimization

**Strategies**:
1. **Content Hash Caching**: Only translate changed posts
2. **Flash Model**: Uses `gemini-2.0-flash-exp` (fast & cheap)
3. **Incremental Builds**: Cache persists across builds
4. **Fallback Handling**: Uses English if translation fails

**Typical Costs**:
- Initial build: ~3 API calls (3 posts)
- Subsequent builds: 0 API calls (cached)
- Content update: 1 API call (only changed post)

## View Transitions

**File**: `transitions.js`

Language switching uses the View Transitions API for smooth cross-fade:
```css
@view-transition {
    navigation: auto;
}
```

No JavaScript navigation needed - pure HTML links with enhanced animation.

## User Experience Flow

1. **First Visit**: 
   - User hits `/` (root index.html)
   - JavaScript detects language (navigator.language)
   - Redirects to `/en/` or `/pt/`

2. **Language Switch**:
   - User clicks globe icon
   - Browser navigates to equivalent page in other language
   - View Transitions API provides smooth cross-fade
   - Language preference not stored (respects fresh detection each visit)

3. **Internal Navigation**:
   - All links language-specific
   - Stays within chosen language
   - Can switch at any time via globe icon

## Build Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env with your Gemini API key

# Build site
python build.py
```

## Files Modified for Bilingual Support

### New Files
- `translator.py` - Translation module (280 lines)
- `.env.example` - API key template
- `translation-cache.json` - Translation cache (gitignored)
- `BILINGUAL_ARCHITECTURE.md` - This document

### Modified Files
- `build.py` - Bilingual build pipeline (+150 lines)
- `config.py` - Added LANGUAGES configuration (+15 lines)
- `styles.css` - Added .lang-toggle styles (+35 lines)
- `requirements.txt` - Added google-generativeai, python-dotenv (+2 lines)
- `.gitignore` - Added .env, translation-cache.json (+2 lines)

### Directory Changes
- Created `/en/` and `/en/blog/` directories
- Created `/pt/` and `/pt/blog/` directories
- Root `index.html` now language detector (was English index)

## Maintenance

### Adding New Posts
1. Write markdown in `blog-posts/` (English)
2. Run `python build.py`
3. Translation happens automatically
4. Both `/en/` and `/pt/` sites updated

### Updating Posts
1. Edit markdown in `blog-posts/`
2. Run `python build.py`
3. Only changed posts re-translated
4. Metadata updated with new timestamp

### Forcing Re-translation
```python
# In translator.py
translator.translate_post(slug, frontmatter, content, force=True)
```

### Reviewing Translations
1. Check `translation-cache.json` for cached translations
2. Open `/pt/blog/post-name.html` to review
3. If unsatisfactory, force re-translate or edit cache directly

## Performance Metrics

**Build Time**:
- First build (3 posts): ~30 seconds (API calls)
- Cached build (3 posts): ~2 seconds (no API calls)
- Single post update: ~10 seconds (1 API call)

**Page Load**:
- Root redirect: <100ms (JavaScript + redirect)
- Language pages: Same as before (no overhead)
- Language switch: Smooth via View Transitions

**Cache Size**:
- ~50KB per post in translation-cache.json
- 3 posts: ~150KB cache file

## Future Enhancements

**Potential Additions**:
1. Language preference cookie (optional persistence)
2. Additional languages (Spanish, German, etc.)
3. Translation quality metrics
4. Admin UI for translation review
5. A/B testing between languages
