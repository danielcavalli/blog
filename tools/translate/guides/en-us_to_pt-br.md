# en-us to pt-br

## Style constraints

- Localize for Brazilian Portuguese readership; do not mirror English sentence order just because the meaning is recoverable.
- Preserve the author's voice, argumentative pressure, caveats, humor, and connective logic instead of flattening them into generic explanatory prose.
- Rewrite idioms, metaphors, and discourse moves idiomatically in PT-BR; preserve effect and meaning, not English imagery.
- If a sentence sounds imported from English, rewrite it fully in natural Brazilian Portuguese instead of patching individual words.
- Match the source's personal register and force; technical precision does not require making the author more formal, sober, or restrained.
- Apply borrowing decisions artifact-wide. Do not oscillate between English and Portuguese renderings for the same concept without an explicit contextual reason.
- Localize clause order and connective phrasing; preserve parentheses around asides and deliberate rhetorical punctuation.
- Keep technical precision and implementation detail; do not add claims not present in the source.
- Preserve markdown structure exactly, including headings, lists, tables, blockquotes, and protected spans.

## Borrowing conventions

- Treat English borrowings as a policy problem, not a token-by-token whim.
- Keep established technical borrowings in English when that is what Brazilian technical readers expect.
- Localize terms that are naturally written in Portuguese in serious Brazilian technical prose.
- Keep product names, branded platforms, and unmistakable identifiers exactly as named in the source.
- When a term is context-sensitive, decide once per artifact and apply the decision consistently.

## Punctuation conventions

- Prefer PT-BR clause rhythm and punctuation over copied English pauses.
- Use the travessão correctly when you need an inciso; do not substitute a hyphen for it.
- Do not place a comma before the opening travessão in parenthetical structures.
- Avoid overusing travessões when commas, parênteses, or sentence recasting would read more naturally.
- Use commas according to Portuguese syntax and explanatory structure, not English pacing habits.

## Discourse conventions

- Rebuild connective tissue in PT-BR instead of preserving English clause sequencing mechanically.
- Let concessive, contrastive, and causal movement sound like authored Brazilian prose.
- Prefer paragraph and sentence movement that a Brazilian technical writer would naturally publish.
- Preserve the author's layered argument structure, not only the facts carried by each sentence.

## Register conventions

- Use contemporary Brazilian technical-editorial prose, not bureaucratic officialese.
- Keep the source's conviction, irritation, enthusiasm, and humor without adding hedges or explanations of jokes.
- Preserve the author's restraint, confidence, and dry humor where present.
- Do not neutralize strong opinions into generic informational language.

## Review checks

- Flag literal calques, especially when the wording sounds understandable but socially wrong in PT-BR.
- Flag inconsistent English borrowings across title, headings, body, tags, and summary fields.
- Flag imported English punctuation or clause movement that makes the prose feel translated.
- Flag flattened rhetoric, lost connective texture, or disappearance of understated humor or soft disagreement.
- Flag PT-BR that is grammatical but not publishable as native Brazilian technical writing.

## Glossary

- throughput => vazão
- latency => latência
- fine-tuning => ajuste fino
- prompt engineering => engenharia de prompts
- feature flag => feature flag
- rollout => rollout
- rollback => rollback
- observability => observabilidade
- dataset => conjunto de dados
- cache invalidation => invalidação de cache
- benchmark => benchmark
- runbook => runbook

## Do not translate

- OpenCode
- CUDA
- Kubernetes
- Docker
- PostgreSQL
- Redis
- OpenAPI
- RFC 9110
- GitHub Actions
- package.json
- pyproject.toml
- requirements.txt
- README.md
- /etc/nginx/nginx.conf
