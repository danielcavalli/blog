---
date: 2026-04-13
lang: en-us
excerpt: 'AI agents feel continuous because the software around them is good at
  reconstruction. But reconstruction has failure modes, and understanding where
  continuity actually lives changes how you build, debug, and trust these systems.'
slug: ai-agents-and-the-illusion-of-continuity
tags:
- AI Agents
- LLMs
- Context Engineering
- Workflows
title: AI Agents and the Illusion of Continuity
---

Resume an agent session after a few hours and it picks up exactly where you left off. It refers back to an earlier decision, continues a line of work, uses the same tools, as if no time had passed.

It is tempting to read that as evidence of a persistent mind. I think that picture is mostly wrong. Across ordinary API calls, the model is not carrying the thread forward by itself. What persists is software state around it: stored messages, tool outputs, summaries, notes, and whatever the harness decides to replay into the next request [1][2].

That is the first distinction that matters. During an active generation, the model can keep temporary inference state such as a KV cache, but that is request-local. It is not the same thing as durable memory across pauses, resumptions, or fresh calls [4][8]. When an agent feels continuous, what you are seeing is successful reconstruction.

Once I started looking at agents that way, a lot of the usual conversation felt backwards. The interesting problem is not whether the model has hidden continuity. The interesting problem is how you package, partition, and reactivate context. That is where most of the reliability comes from, and that is also where most failures come from.

## More Context Is Not A Strategy

The obvious reaction is to keep more history alive. In practice, that is not a great default. Long context is useful, but it is not uniform. Relevant information becomes harder to recover when it drifts into the middle of a long prompt, models can get anchored by stale or self-generated context, and longer inputs can hurt performance even when retrieval is perfect [5][6][7]. A bigger context window is not a permission slip to stop making editorial decisions.

That is why I care more about context selection than context size. Provider-side conversations, stored responses, prompt caches, and compaction features all help with cost, latency, or ergonomics, but they do not fully solve the real question: what should still be active for this turn, and what should be collapsed into an artifact instead [1][2][3][4]. In most practical workflows, that selection problem still lands on you.

## What I Think Matters More Than Skills

This is where I part ways a bit with the current agent discourse. I do not think skills are where most of the leverage is. They can help, but only if they improve the real work: context management, planning discipline, and system design.

My setup today is pretty simple. I keep a knowledge base in the Karpathy sense: notes, decisions, fragments, and artifacts that outlive any one session. On top of that, I use a custom subagent orchestrator. I built it before newer team-style agent features existed, and at this point I am used to it. But the exact orchestrator matters less than people think. The value is not in some magical reusable skill prompt. The value is in deciding how work gets broken down, what each session is allowed to see, and what artifact it must leave behind.

That also matches where current models seem strongest. They are very good at execution against a reasonably clear target. Coding is often the easy part. Planning is still harder. Closing the open loops is harder. Designing a system cleanly enough that execution can stay local is harder. So I would rather spend more time on problem framing, tradeoffs, and artifact quality than on trying to squeeze one giant session into acting like a durable brain.

## One Session, One Task

My default is one session, one task. Not because longer sessions never work, but because they accumulate residue: dead ends, mixed goals, stale constraints, and abandoned branches that still look locally plausible.

The boundary I care about most is phase separation. The session that researches a problem should usually not write the final spec. The session that writes the spec should usually not be the session that implements it. Research is divergent. It is supposed to explore options, reject ideas, and surface unknowns. A spec is convergent. It is supposed to decide. Implementation is narrower still: it should execute against a target, not keep reopening the whole design space.

If you let one session do all three, you get contamination. The implementation context now contains rejected approaches, half-decided constraints, and exploratory reasoning that was useful earlier but is harmful now. That is exactly the kind of context that later gets revived by accident.

So the handoff artifact matters more than the raw session. A research session should leave a research note: options considered, the chosen direction, rejection reasons, open questions. A spec session should turn that into an implementation packet: scope, acceptance criteria, constraints, tests, non-goals. Then the implementation session should start fresh from that packet. If something important changes, stop and spin a new research or spec session instead of dragging the old context forward.

To me, this is the most practical form of continuity: not one immortal thread, but a chain of clean artifacts.

## Personal Workflow, Not Doctrine

All of this is personal workflow advice, not a claim that the field has converged on the one correct pattern. Nobody really knows the best way to work with AI yet. I also do not expect the center of gravity to move that much in the next few months. For now, I still think the leverage is in context management, planning, and system design more than in ever-fancier session persistence.

That is also why I am skeptical of copying someone else's skills wholesale. Workflows are personal. They depend on your codebase, your review habits, your risk tolerance, your taste for specs, and the kinds of mistakes you keep seeing. Borrow the idea if it helps. Then rebuild it for your own context and constraints.

That, at least, is the workflow that has held up best for me: narrow sessions, explicit handoffs, strong artifacts, and a lot of respect for how easily context turns from asset into liability.

---

**Sources:**

[1] OpenAI, *Conversation state*. `previous_response_id`, stored responses, and conversation objects. [platform.openai.com/docs/guides/conversation-state](https://platform.openai.com/docs/guides/conversation-state)

[2] Anthropic, *Messages API*. Documents stateless multi-turn conversations through repeated message replay. [docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages)

[3] Anthropic, *Compaction*. Recommends compaction for long-running conversations and agentic workflows. [docs.anthropic.com/en/docs/build-with-claude/compaction](https://docs.anthropic.com/en/docs/build-with-claude/compaction)

[4] Hugging Face Transformers, *Caching*. Explains KV caching as an inference optimization during generation. [huggingface.co/docs/transformers/main/cache_explanation](https://huggingface.co/docs/transformers/main/cache_explanation)

[5] Liu, N. F. et al., *Lost in the Middle: How Language Models Use Long Contexts*, TACL 2024. [arxiv.org/abs/2307.03172](https://arxiv.org/abs/2307.03172)

[6] Du, X. et al., *Context Length Alone Hurts LLM Performance Despite Perfect Retrieval*, Findings of EMNLP 2025. [arxiv.org/abs/2510.05381](https://arxiv.org/abs/2510.05381)

[7] Tan, H. et al., *Blinded by Generated Contexts: How Language Models Merge Generated and Retrieved Contexts When Knowledge Conflicts?*, ACL 2024. [aclanthology.org/2024.acl-long.337](https://aclanthology.org/2024.acl-long.337/)

[8] Vaswani, A. et al., *Attention Is All You Need*, NeurIPS 2017. Introduces the Transformer architecture underlying modern autoregressive LLM inference. [arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762)
