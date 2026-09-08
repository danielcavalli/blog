---
title: Intent Harness and the Grammar of Revisable Work
date: 2026-06-07
lang: en-us
excerpt: "When we change what we want from software, some of the work we accepted needs another look. Intent Harness is my attempt to keep track of which work, and why."
slug: intent-harness-and-the-grammar-of-revisable-work
tags:
- AI Agents
- Context Engineering
- software architecture
- Category Theory
- Tools
---

Suppose I ask an agent for a notes app I can use on my own. A version that reliably saves what I write and lets me find it again may do everything I need, right up to the moment I decide other people should be able to use it too. Now I need to know whether they could read my notes, and the tests that reassured me yesterday have nothing to say about that.

I started Intent Harness to make changes like this visible across the work I do with agents. The app may still do its original job perfectly well; what needs another look is my decision that the work is finished. As that decision becomes the basis for new tasks, the conditions attached to it have to travel with it. Otherwise, an agent can build on an approval without knowing what it actually covered.

## What acceptance depends on

A transcript can explain why I accepted the first version of the app, especially if someone has taken care to summarize the decision. What I need when I decide to share it, though, is to find the work that relied on that acceptance and understand why it relied on it. Even a careful summary leaves us reconstructing those dependencies unless they have been recorded explicitly.

The Parametric Intent Graph is the model I am developing for that record. It represents decisions, specifications, tasks, evidence, and deliveries as versioned nodes. Their relations distinguish a decision that `constrains` a specification from a patch that `implements` a task, or a test that `verifies` a claim. A review can then `promote` the evidence: accept it as a basis for subsequent work under stated conditions. [[1]](#ref-3)

Those conditions include who had authority to approve the work, what evidence they accepted, and a dependency snapshot recording the upstream versions on which the acceptance relied. The snapshot lets us preserve a valid historical decision without quietly extending it to circumstances nobody reviewed. For the notes app, evidence that saving and retrieving notes works remains useful, while sharing the app requires new evidence that one user cannot read another's notes.

This dependence on constraints is why the product thesis uses the analogy of CAD for agentic software work. Changing a dimension in a CAD model can affect geometry elsewhere; changing a decision can affect work several tasks away. I want the harness to identify those dependencies and carry the revised intent into whatever needs to be reconsidered. An agent rerunning a task may write different code, but it must still receive the goals, constraints, and evidence requirements the work is meant to satisfy. [[1]](#ref-3), [[2]](#ref-4)

For a declared graph, checking which upstream versions changed and following their dependencies can obey fixed rules. Deciding whether a change in meaning requires a fresh review, an adjustment, or a complete rerun still calls for judgment from agents and reviewers.

## Which work needs to be reopened

A graph becomes much more demanding once its edges are expected to justify reopening accepted work. Two documents may discuss the same subject without either depending on the other. For an operational dependency, a change in the source must be capable of affecting something consequential in the target: its scope, result, authority, or the evidence needed to accept it. Similarity helps us find candidates; it cannot establish that relation.

Semantic Dependency Mapping is the research into how to identify, preserve, explain, and correct these relations. An inferred edge needs a source span, a passage a reviewer can inspect to judge whether the dependency exists. When a change affects work several steps away, the system also needs to explain the path between them. Otherwise, we have traded the effort of reconstructing a conversation for the effort of interrogating a graph. [[3]](#ref-5), [[4]](#ref-6)

Some dependencies belong to a set of sources. A gate might require both a passing test and human approval before work can proceed. Two generic links would not tell us whether both are required or either will do. The workbench uses hyperedges to retain the source set and the condition it must satisfy, so the approval cannot disappear merely because the test passed.

The error I most want to measure is a *false-safe* result: work treated as safe to rely on when it should have been invalidated or reviewed. False alarms waste attention, which is a renewable resource only in planning documents. False safety lets someone ship or delegate on the strength of an acceptance whose conditions no longer hold.

The current workbench compares dependency closure, following the graph through all affected downstream nodes, with baselines based on immediate neighbors, keyword and title similarity, and retrieval methods such as TF-IDF and BM25. The closure method recovers the declared dependencies well. Since the expected answers were themselves derived from the graph and correction fixtures, that result largely confirms that the machinery follows the relations it was given. It does not establish that those are the right relations in the world. [[4]](#ref-6)

The evaluation still relies on graph-derived labels, often called *silver* labels, and synthetic model consensus. Independent human judgments remain necessary to establish which changes matter, what they affect, and which evidence or approval they require. The external-model extraction results are diagnostic too, rather than a fresh independent baseline. In operation, a gate unable to support its decision with source text or a dependency path should leave the work awaiting review, however persuasive the model's explanation sounds.

## What category theory asks of the graph

Intent Harness began before I knew Category Theory as a field. I was trying to keep human intent intact through revisions and agent sessions; encountering the mathematics gave me a more exact way to examine what I meant by "intact."

A category consists of objects and arrows between them, called morphisms, with identity arrows and rules for composing compatible arrows. Composition is associative, and composing with an identity leaves an arrow unchanged. Using the language seriously means specifying those operations and showing that the laws hold for the proposed model. [Jean-Pierre Marquis's introduction](https://plato.stanford.edu/entries/category-theory/) gives the formal account. [[5]](#ref-2)

For Intent Harness, composition brings an immediate design question into focus. If a decision constrains a specification, and that specification constrains a task, what obligation reaches the task through the two steps? Following the path is useful only if we retain the relevant constraint along it. If two paths are meant to justify the same acceptance, we also need to establish that they support compatible claims, rather than assume agreement because they end at the same record.

Functors, mappings between categories that preserve identities and composition, suggest a similar standard for translating work between forms. Research notes become plans; plans become task packets that an agent executes. A packet might reproduce a plan's wording faithfully while dropping the requirement for human approval. The sentences survived, but the agent has received different instructions about what it may decide. Calling the translation structure-preserving would require a precise account of those obligations and evidence that the mapping preserves them.

Task splits and merges expose a related problem. Keeping a task's name after rewriting it tells us little about which obligations survived. The workbench includes small fixtures for this question of semantic identity; a general account of identity across branches and revisions remains unfinished.

## When the grammar changes

In the notes example, we have added a requirement to a model that already knows how to represent requirements. A more difficult revision changes the model itself. We might discover that rejected alternatives deserve their own records, or that decisions about taste require an authority boundary our schema cannot express. Adding the fields is straightforward compared with deciding what the existing records mean under the new rules.

An old acceptance may still apply, apply to a narrower claim, or need to be reopened. Some obligations may only become visible because the revised schema gives us a way to describe them. A successful database migration tells us that the records fit the new structure; it leaves the validity of the work to be established.

Fiona Wang and Markus Buehler examine a related problem in their [preprint on self-revising discovery systems](https://arxiv.org/abs/2606.01444v1). Their framework distinguishes work within an established representational regime from discovery that changes the available types, operations, or verifiers. They use a construction called a left Kan extension to transport artifact states into a changed regime, then compare what that transport supplies with the state reached after the transition. The residual identifies content that the transport alone did not provide. [[6]](#ref-1)

I find that useful as an analogy for Intent Harness: changing the rules for describing work does not, by itself, do the work those rules now demand. The preprint supplies a formal treatment in a different domain. Whether a comparable treatment can preserve the obligations in my software work still has to be demonstrated.

The philosophical questions are already present in those implementation choices. To treat a rewritten task as the same task is to make a judgment about identity; to accept a test as grounds for delivery is to make one about evidence. Letting an agent approve a change to product behavior assigns authority. The schema and workflow will embody answers whether we examine them or let the implementation supply them.

This is why I expect reasoning-heavy fields to need more philosophy as they automate more of their work. Systems that infer, revise, and act faster than we can inspect every step make our assumptions more consequential. Leaving those assumptions implicit gives defaults and fluent answers room to decide what counts as evidence or who gets to approve a result. It is another form of [outsourcing the thinking](dont-outsource-the-thinking.html), this time through the design of the tools.

Intent Harness is my attempt to make those commitments inspectable at the moment they matter. When I decide to share the notes app, I want to see what the earlier approval covered, which work needs another look, and who can accept the result. The original tests can keep passing while all of that remains unresolved.

---

**Sources:**

<a id="ref-3"></a>[1] `intent-harness.idea`, especially the working definition, Parametric Intent Graph, dependency snapshots, invalidation protocol, gates, and research lines.

<a id="ref-4"></a>[2] `intent-harness.product-thesis.md`, especially the claim that conversation history is the wrong unit of state for AI software work and the scoped CAD analogy.

<a id="ref-5"></a>[3] `artifacts/research/RESEARCH-0002-semantic-dependency-mapping.md`, especially source-span attribution, operational dependency mapping, false-safe risk, graph authority, and non-goals.

<a id="ref-6"></a>[4] `artifacts/research/semantic_dependency_mapping_workbench/README.md`, `thesis/thesis_draft.md`, `thesis/claims_evidence_matrix.md`, and the related specs and results under `artifacts/research/semantic_dependency_mapping_workbench/`, especially graph formalism, node and edge semantics, snapshots, gates, semantic preservation, semantic identity, hyperedges, annotation requirements, experiment reports, baseline results, and current limitations.

<a id="ref-2"></a>[5] Jean-Pierre Marquis, *Category Theory*, Stanford Encyclopedia of Philosophy. [plato.stanford.edu/entries/category-theory](https://plato.stanford.edu/entries/category-theory/)

<a id="ref-1"></a>[6] Fiona Y. Wang and Markus J. Buehler, *Self-Revising Discovery Systems for Science: A Categorical Framework for Agentic Artificial Intelligence*, arXiv:2606.01444v1, 2026. [Version 1, May 31, 2026](https://arxiv.org/abs/2606.01444v1).
