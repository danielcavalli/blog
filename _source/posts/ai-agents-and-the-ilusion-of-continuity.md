---
date: 2026-04-13
lang: en-us
excerpt: 'AI agents feel like they remember. They don''t. The software around them
  is just good at faking it. Once you see that, the interesting question stops being
  about the model and starts being about how you manage information.'
slug: ai-agents-and-the-illusion-of-continuity
tags:
- AI Agents
- LLMs
- Context Engineering
- Workflows
title: AI Agents and the Illusion of Continuity
---

Resume an agent session after a few hours and it picks up exactly where you left off. It remembers an earlier decision, continues a line of work, uses the same tools. As if no time had passed.

That is not memory. Across API calls, the model carries nothing forward by itself. What persists is everything around it: stored messages, tool outputs, summaries, notes, whatever the harness replays into the next request [[1]](#ref-1)[[2]](#ref-2). The model is stateless. The continuity you experience is built from context that someone, or something, chose to put back.

Once you accept that continuity is a product of context engineering, not of the model, the interesting questions change. It stops being about whether the model "understands" and starts being about what you feed it, when, and how cleanly you separate one task from the next.

## More Context Is Not A Strategy

Most people's first instinct is to keep more history alive. A reasonable instinct. Any human learning a subject would take on as much information as possible to derive their conclusion, so it is only logical that providing more information to an agent would result in better reasoning. Past a point, though, the opposite happens.

Relevant information gets harder to recover when it drifts into the middle of a long prompt [[4]](#ref-4), models anchor on stale or self-generated context [[6]](#ref-6), and longer inputs can hurt performance even when retrieval is technically perfect [[5]](#ref-5). Context windows keep getting bigger, but the model does not get better at guessing which parts are relevant to what you actually want. The more you give it, the more possibilities it has to choose from, and it will pick whichever one looks optimal from where it stands.

What matters more than how much context you can fit is which context you choose to keep active, and what you collapse into an artifact or let go entirely [[1]](#ref-1)[[2]](#ref-2)[[3]](#ref-3). Provider features help with cost and latency, but that selection problem still lands on you.

## What I Think Matters More Than Skills

There is a lot of conversation right now about agent skills, custom prompts, reusable templates, carefully tuned instructions. They can help, but I think most of the leverage is in proper context management, planning, and system design. Less about what the skill does and more about how well the information feeding the model has been curated.

Having made the mistake of overcomplicating things, I can confidently advise against it. Besides the periodic urge to overdo things, my setup is fairly simple now. Essentially I have a knowledge base, similar to Karpathy's [[7]](#ref-7), and a custom multi-agent orchestrator that I built earlier this year and decided to keep around out of laziness (and custom). What I want to say, in the end, is that the setup specifics barely matter. The value is in deciding how work gets broken down, what each session sees, and what artifact it has to leave behind.

Right now, and probably for the next 6-12 months, models are very good at execution against a clear target. Not so much when the plan is blurry and lacking definition. Closing open loops and designing a plan cleanly enough that each piece can be executed in isolation is hard, but it pays off a lot in the long run. So I would rather spend my energy on problem framing, tradeoffs, and artifact quality than on building elaborate agent setups that will mostly amount to marginal improvements over baseline performance.

## One Session, One Task

If I had to turn the above into a single rule, it would be one session, one task. Not because longer sessions never work, but because they accumulate residue. Dead ends, mixed goals, stale constraints, abandoned branches that still look locally plausible. The longer a session runs, the more of that residue builds up, and the harder it becomes to tell what is still relevant from what should have been left behind.

The session that researches a problem should not write the final spec. The session that writes the spec should not implement it. Research is divergent, it is supposed to explore options, reject ideas, surface unknowns. A spec is convergent, it is supposed to decide. Implementation is narrower even: it does not need to know of potential decisions that were never made, just execute against a target goal.

When one session does all three, the implementation context ends up carrying rejected approaches, half-decided constraints, and exploratory reasoning that was useful earlier but is harmful now. That is exactly the kind of context that gets revived by accident.

So the handoff artifact matters more than the session itself. A research session leaves a research note: options considered, chosen direction, rejection reasons, open questions. A spec session tries to close those questions and remaining decisions and turns that into an implementation packet: scope, acceptance criteria, constraints, non-goals. The implementation session starts fresh from that packet. If something important changes, stop and spin a new session instead of dragging the old context forward.

To me, this is the most practical form of continuity where a chain of clean artifacts is laid until a final conclusion in place of a stretched out immortal session.

## Personal Workflow, Not Doctrine

And following the advice of my lawyers, I should say that all of this is a personal opinion. An informed one, perhaps. I use these tools daily and spend a fair amount of time researching how the models behind them work. An opinion nonetheless. I can (and probably am) wrong on a lot of this. Nobody really knows the best way to work with AI yet, and a lot will change in the coming years. That said, I do not expect the center of gravity to move that much in the next few months. For now, I still think the leverage is in context management, planning, and system design more than in ever-fancier session persistence.

That is also why I am skeptical of copying someone else's setup wholesale. Most people still treat AI workflows like traditional software: find something that works, copy it, use it as-is. Someone finds a useful skill and copies the markdown file as if they had found a packaged solution that cannot really be changed. To me, that is a sign they have not yet noticed what makes working with AI different. Everything can be made custom. Every single aspect of a workflow can have your taste in it, your own silly little changes and quirks. So instead of looking for the right template, take the idea and rebuild it until it fits the way you think.

The tools will get better, the models will get better. But I think the people who learn to work well with what we have right now will have a much better time than those waiting for the next leap. Understanding that you are the continuity layer, not whatever the tool you are using tries to make you believe, will help a lot with that.

---

**Sources:**

[1] OpenAI, *Conversation state*. `previous_response_id`, stored responses, and conversation objects. [platform.openai.com/docs/guides/conversation-state](https://platform.openai.com/docs/guides/conversation-state)

[2] Anthropic, *Messages API*. Documents stateless multi-turn conversations through repeated message replay. [docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages)

[3] Anthropic, *Compaction*. Recommends compaction for long-running conversations and agentic workflows. [docs.anthropic.com/en/docs/build-with-claude/compaction](https://docs.anthropic.com/en/docs/build-with-claude/compaction)

[4] Liu, N. F. et al., *Lost in the Middle: How Language Models Use Long Contexts*, TACL 2024. [arxiv.org/abs/2307.03172](https://arxiv.org/abs/2307.03172)

[5] Du, X. et al., *Context Length Alone Hurts LLM Performance Despite Perfect Retrieval*, Findings of EMNLP 2025. [arxiv.org/abs/2510.05381](https://arxiv.org/abs/2510.05381)

[6] Tan, H. et al., *Blinded by Generated Contexts: How Language Models Merge Generated and Retrieved Contexts When Knowledge Conflicts?*, ACL 2024. [aclanthology.org/2024.acl-long.337](https://aclanthology.org/2024.acl-long.337/)

[7] Karpathy, A., *Context Engineering*. [x.com/karpathy/status/2040470801506541998](https://x.com/karpathy/status/2040470801506541998)
