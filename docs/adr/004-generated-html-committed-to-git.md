# ADR 4: Generated HTML Committed to Git

## Status

Accepted

## Context

The dan.rio blog is a bilingual static site hosted on GitHub Pages with a custom domain. The build system is a custom Python static site generator that reads Markdown posts from `_source/posts/`, translates them from English to Brazilian Portuguese using the Gemini API, and writes generated HTML into `en/`, `pt/`, `index.html`, and `sitemap.xml`. GitHub Pages is configured to serve directly from the main branch, with a CNAME file mapping to the custom domain dan.rio and a .nojekyll file bypassing Jekyll processing.

The build process requires a GEMINI_API_KEY environment variable to call the Gemini translation API. It also depends on a local translation cache stored in `_cache/translation-cache.json`, which is git-ignored. Without the cache, a full rebuild must re-translate every post, incurring API costs and rate-limit delays. This means the build cannot run in a clean CI environment without either provisioning the API key as a secret and accepting re-translation costs, or devising a way to persist and restore the translation cache between runs.

The CI pipeline defined in `.github/workflows/validate.yml` runs only syntax checks on the Python source files and executes the pytest suite. It does not attempt to build the site. This is a deliberate choice, not an oversight.

The project has a single author. There are no external contributors, no pull request review workflow, and no branch protection rules that would benefit from a CI-enforced build gate. The repository is small: `en/` and `pt/` together occupy roughly 400 KB on disk, and the git history totals under 1 MB.

## Decision

We will commit all generated HTML output to the main branch in git. This includes the `en/` directory, the `pt/` directory, `index.html` at the repository root, and `sitemap.xml`. The developer builds the site locally by running `uv run python _source/build.py`, commits the resulting output alongside any source changes, and pushes to GitHub. GitHub Pages serves the contents of the main branch directly. There is no CI build step, no deployment pipeline, and no separate publishing branch.

We will document this convention in `.gitignore` with an explicit comment noting that generated HTML files are tracked, so that future contributors understand the intent rather than assuming it is accidental. The `_cache/` directory and `_staging/` directory remain git-ignored, as they are local build artifacts that should not be shared.

## Consequences

Deployment is reduced to `git push`. There is no build server to provision, no deployment secrets to rotate, and no CI minutes to consume. GitHub Pages serves whatever is on main, which means what the developer sees locally is exactly what gets published. This eliminates an entire class of "works on my machine" deployment bugs.

Rollback is straightforward. Because every deployed state is a git commit, reverting a bad deploy is just `git revert`. There is no need to trigger a rebuild or wait for a pipeline. This is particularly valuable for a personal blog where downtime, however minor, is an unnecessary distraction.

The CI pipeline in `validate.yml` stays simple and fast. It validates Python syntax and runs tests without needing access to the Gemini API key. This means CI requires zero secrets, which reduces the attack surface and simplifies repository configuration.

On the other hand, generated files dominate the commit history. Of the 35 commits in the repository, 26 touch generated output. Diffs for content changes are noisy because they include both the Markdown source edit and the resulting HTML changes across two language directories. This makes `git log` and `git diff` less useful for understanding what actually changed in the source.

Repository size will grow over time as every rebuild writes new versions of every HTML file into git history. At the current scale of roughly 400 KB of generated output this is negligible, but it compounds. A blog with hundreds of posts and frequent rebuilds would eventually produce a bloated repository. Git does compress well across similar files, but the growth is monotonic and irreversible without history rewriting.

There is a real risk of stale output. If the developer edits source files but forgets to run the build before committing, the generated HTML will not reflect the latest changes. Nothing in the current workflow enforces that the output is fresh. A pre-commit hook running the build would mitigate this but has not been implemented.

Merge conflicts in generated files are theoretically possible if the project ever moves to a multi-contributor model. Two developers editing different posts would both regenerate the index pages, producing conflicts in files that nobody authored by hand. This is a non-issue today with a single author but would become painful quickly.

Alternatives were considered. A CI-based build using GitHub Actions would keep generated files out of the repository but would require storing the GEMINI_API_KEY as a repository secret and solving the translation cache problem, either by caching it as a CI artifact or accepting the cost and latency of full re-translation on every push. Managed hosting platforms like Netlify or Vercel would handle the build automatically but introduce a dependency on a third-party service for what is currently a zero-dependency deployment. A git orphan branch strategy, where source lives on main and generated output is force-pushed to a separate gh-pages branch, would separate concerns but add workflow complexity for a single-person project. None of these alternatives are ruled out permanently, but none offers a better tradeoff at the current scale and team size.
