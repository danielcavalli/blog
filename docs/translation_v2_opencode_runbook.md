# OpenCode translation_v2 operations runbook

This runbook is the operational reference for the current translation runtime in `_source/build.py`.

## Scope and current routing

- Build translation runtime is OpenCode-only.
- The full translation pipeline is always active during builds.
- There is no build-time translate-only toggle.
- Post, About, and CV translation run through OpenCode by default.
- `--skip-about-cv-translation` is available only for focused bypass runs.
- `WRITING_STYLE.md` is injected into prompt context for translation, critique, and refine stages.
- `_source/translation_revision.yaml` is the committed interface for marking stale translations for revision.

## Current build CLI

Supported translation-related CLI surface:

- `--post _source/posts/<post-file>.md` (limit run to one post)
- `--skip-about-cv-translation` (optional bypass for focused runs)

Not used by current build CLI:

- `--translation-v2`
- `--translation-provider`
- translation failure-policy flags

## Build commands

### Full run (all posts + About + CV)

```bash
uv run python _source/build.py
```

### Strict quality-gate run

```bash
uv run python _source/build.py --strict
```

### One-file mode (operational/debug)

```bash
uv run python _source/build.py --post _source/posts/<post-file>.md
```

### One-file focused bypass (skip About/CV translation)

```bash
uv run python _source/build.py --post _source/posts/<post-file>.md --skip-about-cv-translation
```

## Revision workflow

Use `_source/translation_revision.yaml` to mark translations for reassessment:

```yaml
posts:
  post-slug:
    pt-br:
      reason: legacy ai studio translation
      notes: restore connective tissue and dry humor
```

Behavior:

- Existing cached translations are reused by default.
- Legacy cache entries are revision candidates automatically.
- Marked entries run an assess-and-revise flow against the current source text.
- If the existing translation passes critique, it is accepted as-is.
- If critique finds fixable issues, the build refines the existing translation.
- If revision cannot converge cleanly, the build falls back to the full translation loop.
- A satisfied revision marker is remembered in cache metadata, so the build does not re-run revision on every subsequent build unless the source or manifest entry changes.

### One-file CI lane (regression test command)

```bash
uv run --extra dev pytest tests/test_translation_v2_onefile_lane.py -q
```

## Quality gate behavior

- Bidirectional validation is active in the build quality gate.
- Validation runs per translated pair based on source locale direction (`EN -> PT` and `PT -> EN`).
- Default mode logs issues and continues.
- Strict mode (`--strict`) fails on error-level validation issues.

## Logs and artifacts

### Build output breadcrumb

Build logs print:

- `translation_v2 debug: run_id=<...> artifact_dir=<...>`

Use `run_id` as the primary key for triage.

### translation_v2 run artifacts (repo-local)

- Base dir: `_cache/translation-runs/` (or `TRANSLATION_V2_ARTIFACT_BASE_DIR`).
- Per-run dir: `_cache/translation-runs/<run_id>/`.
- Key files:
  - `<run_id>/stage-events.jsonl`
  - `<run_id>/posts/<slug>/trigger/event.json`
  - `<run_id>/posts/<slug>/<stage>/prompt.txt`
  - `<run_id>/posts/<slug>/<stage>/structured-response.json`
  - `<run_id>/posts/<slug>/<stage>/runner-attempt-<n>.json`
  - `<run_id>/posts/<slug>/<stage>/runner-stdout.log`
  - `<run_id>/posts/<slug>/<stage>/runner-stderr.log`
  - `<run_id>/posts/<slug>/<stage>/error.txt` (only on stage errors)

### OpenCode local session artifacts

OpenCode CLI artifacts are written under the user profile at:

- `~/.local/share/opencode/log/` (OpenCode process logs)
- `~/.local/share/opencode/storage/session/` (session records)
- `~/.local/share/opencode/tool-output/` (tool payload captures)

## Triage checklist (run_id/session guided)

1. Run one-file mode and capture output to a file.

   ```bash
   uv run python _source/build.py \
     --post _source/posts/<post-file>.md \
     --skip-about-cv-translation 2>&1 | tee /tmp/translation-v2-onefile.log
   ```

2. Extract `run_id` from the log and open `_cache/translation-runs/<run_id>/`.
3. Inspect `stage-events.jsonl` first to identify failing stage/attempt/outcome.
4. Open `posts/<slug>/<stage>/runner-attempt-<n>.json` for command, exit code, parse errors, stdout/stderr snapshot, and failure classification.
5. If runner output looks valid but contract fails, inspect `structured-response.json` and `error.txt` for schema mismatch details.
6. Correlate with OpenCode host artifacts (`~/.local/share/opencode/storage/session/`, `~/.local/share/opencode/tool-output/`, `~/.local/share/opencode/log/`) when failure appears external to build orchestration.
