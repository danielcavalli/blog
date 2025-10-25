# Multi-Agent Translation Pipeline

## Overview

The blog uses a **three-stage AI translation pipeline** for Brazilian Portuguese. Instead of a single translation, content goes through Translation → Critique → Refinement to ensure quality.

## Architecture

### Stage 1: Translation Agent
**Purpose**: Initial EN → PT-BR translation

**Input**:
- English frontmatter (title, excerpt, tags)
- Full markdown content

**Output**:
- Portuguese title, excerpt, tags
- Translated markdown content

**Prompt Strategy**:
- Direct, concise instructions
- Technical term preservation rules
- Brazilian idiom guidance
- Format preservation requirements

**Example**:
```
Translate this technical blog to Brazilian Portuguese.

Keep technical terms in English: machine learning, GPU, CUDA...
Use Brazilian idioms: "I am Daniel" = "Me chamo Daniel"
Preserve all Markdown exactly.

[content]
```

### Stage 2: Critique Agent
**Purpose**: Semantic alignment validation

**Input**:
- Original English content (snippet)
- Portuguese translation (snippet)

**Output**:
- `OK` - Translation approved
- `FEEDBACK: [issues]` - Specific problems identified

**Validation Criteria**:
- Same meaning and tone
- Natural Brazilian phrasing
- Technical accuracy
- No missing content

**Example Output**:
```
FEEDBACK: The intro paragraph sounds too formal for the conversational tone 
of the original. "Neste artigo" should be "Neste post" to match informality.
The section about GPU architecture lost the analogy to a city - restore it.
```

### Stage 3: Refinement Agent
**Purpose**: Apply critique to improve translation

**Input**:
- Original English content
- Current Portuguese translation
- Specific feedback from Critique Agent

**Output**:
- Refined Portuguese translation
- Same structure as Translation Agent output

**Example**:
```
Improve this Portuguese translation based on feedback.

FEEDBACK: Intro too formal, missing city analogy in GPU section.

[Apply changes while maintaining natural Brazilian Portuguese]
```

## Workflow

```
┌──────────────────┐
│ English Post     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Translation      │──┐
│ Agent            │  │
└────────┬─────────┘  │
         │            │
         ▼            │ Gemini 2.0
┌──────────────────┐  │ Flash API
│ Critique Agent   │  │
└────────┬─────────┘  │
         │            │
         ├─ OK ────────────► Use translation
         │            │
         ▼            │
    FEEDBACK         │
         │            │
         ▼            │
┌──────────────────┐  │
│ Refinement       │──┘
│ Agent            │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Final Portuguese │
│ Translation      │
└──────────────────┘
```

## Caching Strategy

**Hash-Only Cache**:
- Stores SHA-256 hash of English content
- NO translated content stored
- Fresh translation on every content change

**Why Not Cache Translations?**:
- Gemini API improves over time
- Bad translations persist forever in cache
- Hash-only approach forces regeneration
- Minimal performance cost (API is fast)

**Cache File**: `_cache/translation-cache.json`
```json
{
  "building-a-bilingual-blog": "a3f5d8c...",
  "modern-web-development": "b2e9f1a..."
}
```

## Quality Guarantees

### Translation Agent
- Preserves technical vocabulary
- Uses Brazilian Portuguese (PT-BR, not PT-PT)
- Maintains all Markdown and code blocks
- Natural conversational tone

### Critique Agent
- Validates semantic equivalence
- Checks for natural phrasing
- Identifies missing or altered content
- Verifies tone consistency

### Refinement Agent
- Applies specific feedback
- Maintains improvements from first pass
- Preserves structure and formatting
- Iterates on only identified issues

## Technical Terms Policy

**Always Keep in English**:
- Programming terms: `debug`, `commit`, `deploy`, `pipeline`
- AI/ML terms: `machine learning`, `GPU`, `CUDA`, `training`
- Web terms: `frontend`, `backend`, `API`, `framework`
- Modern concepts: `view transition`, `morphing`, `responsive`

**Translate Concepts**:
- "Building" → "Construindo"
- "Guide" → "Guia"
- "Learning" → "Aprendizado"
- "Performance" → "Performance" OR "Desempenho" (context-dependent)

## Brazilian Portuguese Guidelines

### Idioms
- "I am X" → "Me chamo X" (not "Eu sou X")
- "I work at" → "Trabalho na" (not "Eu trabalho em")
- Casual tone preferred for tech blogs

### Formal vs Informal
- Use "você" (informal) not "vossa senhoria"
- Contractions OK: "tá", "pra", "pro"
- First person: natural and personal

### Technical Writing
- Direct and clear
- Active voice preferred
- Short sentences
- Examples and code unchanged

## Integration with Build System

The `build.py` script calls the translator:

```python
from translator import MultiAgentTranslator

translator = MultiAgentTranslator()

# For each post needing translation
translation = translator.translate_post(
    slug='post-name',
    frontmatter={'title': '...', 'excerpt': '...', 'tags': [...]},
    content='markdown content',
    force=False  # Skip if hash unchanged
)

if translation:
    # Use translated title, excerpt, content, tags
    ...
```

## Performance

**Typical Post Translation**:
- Translation: ~2-5 seconds (Gemini 2.0 Flash)
- Critique: ~1-2 seconds
- Refinement (if needed): ~2-5 seconds
- **Total**: 3-12 seconds per post

**Optimization**:
- Hash-based caching skips unchanged posts
- Parallel translation possible (not implemented)
- Critique can be disabled for drafts

## Error Handling

**Translation Failures**:
- Falls back to English (no partial pages)
- Logs error details
- Continues with other posts

**Critique Failures**:
- Assumes "OK" (optimistic)
- Uses original translation
- Logs warning

**Refinement Failures**:
- Uses original translation
- Marks as translated (prevents retry loop)
- Logs error

## Future Improvements

**Potential Enhancements**:
1. **Parallel Translation**: Translate multiple posts simultaneously
2. **Quality Metrics**: Track critique approval rate
3. **User Feedback Loop**: Learn from manual corrections
4. **Multi-language**: Extend to Spanish, French, etc.
5. **A/B Testing**: Compare single-pass vs multi-agent quality

**Current Limitations**:
- No manual override mechanism
- Single critique pass (no re-refinement)
- No quality scoring/ranking
- No translation memory between posts

## Monitoring

**Key Metrics**:
- Critique approval rate (target: >80%)
- Translation time per post
- Cache hit rate
- API cost per month

**Debugging**:
```bash
# Force re-translate all posts
python _source/build.py --force-translate

# Clear cache
rm _cache/translation-cache.json

# Single post test
python -c "
from translator import MultiAgentTranslator
t = MultiAgentTranslator()
result = t.translate_post(
    'test-slug',
    {'title': 'Test', 'excerpt': 'Test', 'tags': []},
    'Content here',
    force=True
)
print(result)
"
```

## Configuration

**Environment Variables**:
- `GEMINI_API_KEY`: Required for translation
- Model: `gemini-2.0-flash-exp` (hardcoded)

**Settings** (in `translator.py`):
- `TRANSLATION_CACHE_FILE`: Cache location
- `GEMINI_MODEL`: Model version

## Deployment

**Build Process**:
1. Parse all markdown posts
2. Check translation cache
3. For changed posts:
   - Translation Agent
   - Critique Agent
   - Refinement Agent (if needed)
4. Generate HTML with translations
5. Update cache with new hashes

**No Runtime Translation**:
- All translation happens at build time
- Static HTML files contain final Portuguese
- No client-side translation logic
- No API calls from browser

---

**Last Updated**: 2025-01-27
**System Version**: Multi-Agent v1.0
**Model**: Gemini 2.0 Flash
