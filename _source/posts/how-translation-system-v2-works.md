---
date: 2026-04-19
lang: en-us
excerpt: "Translation System v2 is the second serious attempt at making this blog bilingual without making the Portuguese read like imported English. It took more than a better model."
slug: how-translation-system-v2-works
tags:
- translation
- localization
- llms
- software architecture
- pt-br
title: How Translation System v2 Works
---

The original version of this system was built in 2024, although it only really took over the blog in 2025. That matters because 2024 was a very different moment to design around. Models were weaker, long agentic workflows were less trustworthy, and the sensible instinct was to keep the system narrow. Translate the post, preserve the markdown, cache the result, and move on with your life.

That system did exactly what it was designed to do. Unfortunately I designed it.

It could produce translations that were structurally fine and semantically understandable. If all I wanted was semantic transport, that would have been enough. The issue is that it was never what I wanted. I wanted the Portuguese version of the blog to sound like writing, not like evidence that a model had correctly identified the nouns.

That difference is where the redesign starts, and also where the earlier version runs out of excuses.

The old system would often preserve the information and damage the text. The meaning survived. The voice did not. The connective tissue between ideas got thinner. English borrowings in Brazilian Portuguese were handled as if each occurrence were a fresh philosophical question. A sentence that, in the original, was establishing credibility, softening a disagreement, and making a joke at the same time would come back in Portuguese doing one of those things with modest confidence. Most of the time not the right one.

At some point I stopped treating that as a translation problem. It was clearly a systems problem. v2 was not built as a nicer prompt. It was built as a different system with different assumptions about what the work actually is.

## The original sin was not model quality

It would be convenient to blame the whole thing on the models available at the time. That would let the earlier architecture off rather easily. Unfortunately the design itself was part of the problem.

The old pipeline behaved as if quality would emerge from being careful enough around structure. Keep the markdown intact. Protect code blocks. Reuse a cache. Ask the model to sound natural. Maybe run one review pass. This is all defensible if your main concern is not breaking the artifact. It is much less defensible if your main concern is whether a Brazilian reader would believe the Portuguese version had been written by the same person.

The distinction matters because "understandable" is a dangerously low bar. A lot of translated text is understandable. So is a machine-generated customer support email. That tells you almost nothing about whether the writing survived the trip.

The problem, in other words, was not that the old system failed in some spectacular fashion. It failed politely. Those are the dangerous ones. A system that explodes usually does you the favor of embarrassment. A system that produces plausible-looking output can waste a great deal more time.

## It starts with the build, not the prose

The first serious change in v2 is not linguistic. It is operational.

The build is now source-first. It builds source-language pages before translation starts, and it commits accepted translation work at the artifact boundary rather than at the vague end of the whole build. This sounds like sober plumbing, which it is, but it also fixes one of the more annoying failure modes of the earlier system.

The build contract is now closer to this:

```text
parse -> build source output -> translate -> accept -> cache -> artifacts -> rendered output
```

That is a better contract than "do a lot of work, keep some of it in memory, and hope nothing important fails later."

The practical consequence is simple. If a source page can be built, it should be built. If a translated artifact is accepted, it should be persisted immediately. A later failure in some unrelated part of the run should not erase work that already succeeded. That was previously happening often enough to be both expensive and insulting.

This also gives the build a cleaner shape. Source content is now a first-class output rather than something that happens to exist before the translation logic gets excited. That seems obvious after the fact. Most good fixes do.

## Six stages, mostly because the old system was lying about one

The translation path itself is also more explicit than it used to be. Instead of one general instruction to translate and perhaps behave, v2 splits the work into six stages:

```text
source_analysis
terminology_policy
translate
critique
revise
final_review
```

This is not stage inflation. It is an admission that the older pipeline was trying to do several different jobs with one vague instruction and then acting surprised when some of them were done badly.

If this sounds overengineered, I do understand the instinct. I had it too. The cleaner story is always that one strong model should be able to read a post, translate it, notice what it got wrong, and fix itself. That is a reasonable instinct. It is also roughly where the old system landed. The problem is that these are different jobs. More to the point, they fail differently. Once you accept that, splitting them starts to look less like ceremony and more like basic honesty.

### Source analysis

The first stage tries to understand the source as writing rather than as portable content. It extracts tone, register, sentence rhythm, connective habits, rhetorical moves, humor signals, and the parts of the text that absolutely have to survive localization.

That may sound suspiciously literary for a build pipeline. It is also true. If the system cannot distinguish between a sentence that merely states a fact and one that is quietly doing argument, tone management, and credibility work at the same time, then the later stages are operating half blind and full of confidence, which is not an improvement.

The older system treated this mostly as prompt taste. The current one treats it as working memory.

### Terminology policy

The second stage settles terminology and borrowing before any draft is written.

This is one of those things that sounds bureaucratic until you have seen what happens without it. English to Brazilian Portuguese technical writing is full of terms that should remain in English, terms that should obviously be localized, and terms that depend on context, audience, and register. If the model makes those decisions one occurrence at a time, the output starts sounding socially wrong even when the meaning is intact.

That is a very common failure mode in localization. It is also the sort of thing that English speakers often underestimate because the text remains legible to them. Brazilians, unfortunately for the system, can read too, and some of us are even vindictive enough to notice when "natural Portuguese" is doing a very convincing impression of translated English.

It decides what should stay in English, what should be localized, what remains context-sensitive, and what should not be translated at all. More importantly, it resolves ambiguous cases at the artifact level rather than sprinkling hints into the prompt and hoping for character.

### Translation

Only then does the system produce a draft.

The translation stage currently uses `GPT-5.4` with high reasoning effort. That is not because I enjoy expensive numbers. It is because this is the part of the workflow that actually has to rewrite. A cheaper model can fail in very creative ways here while still looking helpful.

The key change, though, is not only the model choice. It is that the translator is no longer being asked to preserve surface form. It is being asked to preserve effect. If a sentence needs to be rebuilt so it reads like authored Portuguese rather than English carried across the border with paperwork attached, then the sentence gets rebuilt. The point is to preserve the writing, not the crime scene.

This is the point where translation starts becoming localization instead of bilingual copying.

### Critique

Critique now exists as a real diagnostic stage, not as a polite rubber stamp.

It evaluates the draft on several dimensions: factual fidelity, terminology consistency, markdown and protected-span integrity, locale naturalness, borrowing consistency, and rhetorical structure.

That stage runs on `GPT-5.2`. I prefer that split. Translation and revision are generative jobs. Critique is a diagnostic one. They benefit from different habits, and there is no particular reason to make the same model do all of them simply because it can.

Also, if a pipeline is going to lie, I would rather have it lie in fewer voices.

### Revision

Revision exists because a good critique is not the same thing as a good rewrite.

One problem with weaker translation pipelines is that they quietly assume the first draft needs to be almost right for the workflow to succeed. That makes the whole system brittle. v2 treats revision as a first-class rewrite stage. If the critique says the text still sounds translated, the answer is not to swap a few terms and congratulate oneself for respecting structure. The answer is to rewrite the sentence or paragraph properly.

Translation and revision both use `GPT-5.4` high for exactly that reason. This is where the system does the hardest stylistic work.

### Final review

Final review is the actual gate.

This stage verifies that the revised artifact is faithful, native in the target language, internally consistent, structurally intact, and still recognizably authored. It also checks whether critique findings were actually resolved rather than merely acknowledged in a confident tone.

This makes the architecture more boring than the phrase "multi-agent translation workflow" might suggest. I take that as a compliment. Systems improve when the impressive part moves from the name to the behavior.

## PT-BR needed a policy layer, not a motivational speech

The largest recent improvement to the system is the PT-BR localization layer.

This had been missing for too long.

Earlier versions of the prompts already contained variations of "sound natural in Brazilian Portuguese," which is one of those instructions that manages to be both true and useless. The system needed something much more specific. So it now carries a first-class PT-BR localization brief plus explicit conventions for borrowing, punctuation, discourse movement, register, and review checks.

The borrowing policy is the most obvious part of it. Technical Brazilian Portuguese is not simply Portuguese with some English nouns left in. It has conventions, habits, and community expectations. Some terms stay borrowed because that is how Brazilian technical readers actually use them. Some are naturally localized. Some depend on context. Product names and branded terms are another category entirely. Treating all of that as a sequence of local lexical choices is how you produce text that is grammatical and slightly embarrassing, which is one of the least useful combinations in software.

Punctuation and discourse matter just as much. Portuguese does not merely translate English clauses. It often reorganizes them. It handles pauses differently. It uses the travessão differently. It tolerates different connective movement. If a system preserves English clause order and simply swaps vocabulary, the result can be perfectly understandable and still feel imported.

That is why the locale brief now encodes things that earlier versions left to model instinct. It is also why critique and final review explicitly score locale naturalness, borrowing consistency, and rhetorical structure instead of pretending all of that can be compressed into one friendly number called fluency.

## The cache is still there, but it now behaves like part of a system

The translation cache still lives in `_cache/translation-cache.json`. I did not replace it with something more fashionable because there was no real reason to. Replacing a broken idea with a trendy noun is one of the least productive habits in software, and this system had already suffered enough from ideas pretending to be solutions.

What changed instead is how the cache relates to the rest of the pipeline.

There are now effectively three persistence layers: the translation cache, the per-run artifacts under `_cache/translation-runs/...`, and the rendered site output. Those layers do different jobs. The cache exists for reuse. The run artifacts exist for inspection. The rendered output exists because a reader eventually needs a page. Earlier versions of the system blurred those concerns enough that successful work could still feel non-durable in practice. v2 is stricter about the boundaries.

There is also now a more sensible distinction between "cache hit" and "state I trust." If a cached translation exists but the rendered translated HTML is missing, the system does not quietly repaint the page from cache and call it a day. It marks the artifact for revision and sends it back through the normal workflow.

That is the right behavior. Missing output is not just a rendering inconvenience. It is evidence that the artifact state is inconsistent. Quietly papering over that would make the system look calmer while making it less trustworthy. Calm systems are wonderful. Systems pretending to be calm usually are not.

## The model split is practical, not mystical

The current model assignments are:

- `GPT-5.4` high for translation
- `GPT-5.2` for critique
- `GPT-5.4` high for revision
- `GPT-5.2` for final review

This is not a metaphysical statement about which model understands prose more deeply. It is simply a statement about how I want the work divided.

Translation and revision require sustained rewrite ability. Critique and final review require structured judgment, consistency, and enough distance from the draft to reject it when necessary. There is no reason those have to be the same path. In practice, separating them also makes the whole pipeline easier to reason about when something goes wrong, which is not a glamorous property but is usually the one that matters.

## Future work starts where sentence-level systems run out of excuses

v2 is much better than the system it replaced. It is also not the endpoint.

There are at least four directions that would take it meaningfully further, and none of them amount to writing an even stricter prompt.

### Document-level coherence

Most practical translation systems still behave too much like sentence translators with extra paperwork. Research on document-level machine translation has been pointing at the same thing for years: broader context helps with coherence, consistency, and discourse interpretation, even if using that context well is harder than simply concatenating neighboring sentences.

The current system already works at the artifact level in prompt terms, which is better than sentence isolation. Still, it does not yet carry a strong internal model of document-level coherence as such. A future version should care more explicitly about cross-paragraph continuity, recurring argument structures, pronoun resolution, and the way rhetorical force accumulates over a whole post rather than inside a single local span.

### MQM-style evaluation

Translation quality has a bad habit of collapsing into arguments about vibes. MQM is useful precisely because it refuses that escape hatch. It gives you a structured error typology and forces the conversation into categories that can be compared, tracked, and argued about properly.

This system should eventually adopt something MQM-like for its internal evaluation layer. Not the whole framework by religious obligation, but the basic discipline of typed quality failures. Right now the pipeline already scores fidelity, terminology, and locale naturalness. The next step is to classify failure modes more rigorously:

- calque
- borrowing inconsistency
- locale unnaturalness
- rhetorical flattening
- structural drift
- protection failure

That would make the system much easier to improve because it would tell me not just that a translation failed, but what kind of failure it was and whether the same failure keeps coming back in the same places.

### Richer localization metadata in the source

W3C's internationalization and localization work is useful here for a simple reason. It treats content annotation as part of the system instead of pretending every localizer should reconstruct intent from prose and hope.

This blog does not need industrial localization markup tomorrow morning, but I can easily imagine a future version carrying richer source-side metadata for protected terms, glossary candidates, locale notes, and authorial hints about register and borrowing. That would be cleaner than forcing every downstream decision to be inferred again from the same text.

### Trusted translation memory

Translation memory is only as good as what you allow into it. Localization platforms understand this quite well, which is why reviewed output often gets privileged treatment compared to machine-generated drafts.

The current cache is already much better behaved than the old one, but there is still a useful distinction to draw between "accepted in a run" and "good enough to become durable localization memory." A stronger future policy might split short-lived workflow cache from approved translation memory. The second should probably be fed only by outputs that clear the full review chain with enough confidence to deserve reuse rather than mere survival.

That would make the memory layer less permissive and, as a result, more trustworthy.

## What changed is what the system thinks it is doing

That, in the end, is the real difference.

The original pipeline treated translation as a constrained text transformation problem. v2 treats it as localization work inside a build system that has to preserve authored writing, survive failure, and remain inspectable when something goes wrong. Those are not the same problem, so they do not produce the same architecture.

The rebuild did not happen because I suddenly became interested in turning a blog translator into a minor bureaucracy. It happened because the simpler system kept failing in the same way. It would hand me text that was good enough for a benchmark shaped like itself and bad enough for a reader shaped like an actual person. After a while that stops feeling like a model problem and starts feeling like complicity.

That is not a very useful kind of success.

v2 is better because it is more explicit. It has clearer stages, clearer durability semantics, clearer PT-BR policy, clearer rejection criteria, and clearer ideas about what still remains unsolved. That last part matters more than it might seem. Translation systems become dangerous precisely when they are just good enough to sound finished, because that is the point at which people stop checking them carefully and start forgiving them professionally.

This one is not finished. It is, however, finally honest about what the work is. For now, that is enough. Not for the translations, unfortunately. For the system.

## Sources and further reading

- [Google Developer Documentation Style Guide, "Write for a global audience"](https://developers.google.com/style/translation)
- [Microsoft Style Guide, "Writing tips"](https://learn.microsoft.com/pt-br/style-guide/global-communications/writing-tips)
- [W3C, Internationalization and Localization Markup Requirements](https://www.w3.org/TR/itsreq/)
- [MQM, Multidimensional Quality Metrics](https://themqm.org/)
- [Zheng et al., "Towards Making the Most of Context in Neural Machine Translation"](https://www.ijcai.org/Proceedings/2020/551)
- [Nayak et al., "Investigating Contextual Influence in Document-Level Translation"](https://www.mdpi.com/2078-2489/13/5/249)
- [Tan, Zhang, Zhou, "Document-Level Neural Machine Translation with Hierarchical Modeling of Global Context"](https://jcst.ict.ac.cn/article/cstr/32374.14.s11390-021-0286-3)
- [Transifex, "Introduction to Translation Memory"](https://help.transifex.com/en/articles/6224636-introduction-to-translation-memory)
