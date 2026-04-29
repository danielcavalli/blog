---
title: How I Use AI Agents
slug: how-i-use-ai-agents
date: 2026-04-30
excerpt: What I built, what broke, and what survived.
tags:
- AI Agents
- Workflow
- Tools
lang: en-us
content_type: presentation
---

<!-- presentation:slide id="title" layout="lead" density="normal" -->

# How I Use AI Agents

## What I built, what broke, and what survived

Daniel Cavalli | dan.rio

<!-- /presentation:slide -->

<!-- presentation:slide id="bio-and-agenda" layout="bio" density="dense" -->

# Daniel Cavalli

Senior Machine Learning Engineer at Nubank

Graduated in Economics from UFRJ with a focus on Causal Modeling. Nine years of experience working in ML, ranging from building models, AI platforms for multiple companies and, now, playing with AI Agents and Behavioural World Models as a research line.

![Daniel Cavalli](/static/images/presentations/how-i-use-ai-agents/profile-picture.png)

| # | Section | Claim |
| - | ------- | ----- |
| 1 | Foundation | Continuity is engineered |
| 2 | Agent PM | Planning beats dispatch |
| 3 | Knowledge Base | Memory needs structure |
| 4 | Distribution | Copying is not adoption |
| 5 | Translation Pipeline | Voice needs process |

<!-- /presentation:slide -->

<!-- presentation:slide id="foundation" layout="divider" density="normal" -->

# The Foundation

## Continuity is an illusion you engineer, not something the model gives you

<!-- /presentation:slide -->

<!-- presentation:slide id="stateless-model" layout="dark_content" density="dense" -->

# The model is stateless

Every time you press Enter, the harness rebuilds the full context from scratch. The model responds. Then it forgets everything.

> The continuity you experience is built from context that someone, or something, chose to put back. It is not memory. It is reconstruction.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Sessions accumulate residue
Dead ends, mixed goals, stale constraints. The model anchors on what came first, not what came last.
<!-- /presentation:card -->
<!-- presentation:card -->
### More context can mean worse output
Most people's instinct is to keep more history alive. The model starts hedging, qualifying, trying to reconcile things that no longer matter.
<!-- /presentation:card -->
<!-- presentation:card -->
### The real skill is removal
Not expanding context. Knowing what to collapse, what to discard, and what to carry forward as a handoff artifact.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="four-rules" layout="card_grid" density="very_dense" -->

# Four Rules

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. One session, one task
Research sessions produce research notes. Spec sessions produce implementation packets. Implementation starts fresh from the packet. They never share a session.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Curate what the model sees
Every tool schema, every MCP instruction, every stale fragment competes for attention. Irrelevant context does not just waste tokens. It actively degrades output.
<!-- /presentation:card -->
<!-- /presentation:block -->
<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 3. Sandbox everything
Catch errors outside the context window so they never consume tokens to debug. A hook that formats code on save or validates YAML costs zero tokens and prevents problems the model would otherwise spend dozens of messages fixing.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Multi-agent is the obvious next step
Once you accept isolated sessions, the question becomes how to split work across them. Each agent gets only what it needs. Decompose, parallelize, integrate.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="humans-job" layout="emphasis" density="dense" -->

# The Human's Job

> Agents are remarkably good at single-domain work. But the moment you need to pull threads from multiple domains into the same argument, they fall apart.

The human advantage is not "thinking" in general. It is cross-domain synthesis: holding three different contexts in your head, cross-referencing them, knowing which constraints are real and which are inherited from a conversation that no longer applies.

The agent executes. Your job is deciding what it should execute.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm" layout="divider" density="normal" -->

# Agent PM

## Because I have too many ideas and agents made the problem worse

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-problem" layout="split" density="dense" -->

# The Problem

I am overly enthusiastic about new ideas, which leads me to explore too many paths at once.

Before agents, this was bounded by how fast I could type. With agents, the bound disappeared. I could pursue multiple directions simultaneously and check results later.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### What I gained
Actual parallel exploration. Multiple hypotheses running at once. Results waiting for me when I checked back.
<!-- /presentation:column -->
<!-- presentation:column -->
### What I lost
The ability to distinguish priorities from distractions. I needed a system to decompose ideas, dispatch them to agents, and track what came back.
<!-- /presentation:column -->
<!-- /presentation:block -->

Agent PM started as a way to manage my own focus. It became an orchestrator because the same principles that made it useful for tracking also made it useful for dispatching.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-what-it-is" layout="split" density="very_dense" -->

# What It Is

Everything is YAML in a `.pm/` directory, version-controlled alongside code. Ships as a global CLI (`pm`), an MCP server (14+ tools), and a set of Claude Code slash commands.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
.pm/
  project.yaml          # Project definition
  index.yaml            # Auto-maintained summary
  epics/
    E001-auth.yaml      # Epic with embedded stories
  reports/
    E001-S001-report.yaml
  agents/
    agent-abc.yaml      # Heartbeats + state
  adrs/
    ADR-001.yaml        # Decision records
```

<!-- /presentation:column -->
<!-- presentation:column -->

```yaml
stories:
  - id: S001
    title: "JWT middleware"
    acceptance_criteria:
      - "JWT tokens validated on every request"
      - "Expired tokens return 401"
    depends_on: []
    story_points: 3
    priority: high
```

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-flow" layout="card_grid" density="very_dense" -->

# The Flow

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. Spec
I write it. Current state, target state, constraints, pitfalls, exclusions. The spec is the final output of research, not the beginning of it.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Refine
`/pm-refine-epic` reads the spec, surveys the codebase. Produces epics and stories with dependencies forming a DAG. Human approves before execution.
<!-- /presentation:card -->
<!-- presentation:card -->
### 3. Execute
`/pm-work-on-project` builds a dependency graph, classifies into tiers, dispatches agents in parallel per tier. Failure context propagates forward.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Monitor
`/supervisor` triages: Blocked > Stale > Completed > Running. Batch decisions across agents. Under 3 minutes per round.
<!-- /presentation:card -->
<!-- /presentation:block -->

The spec is where all the real thinking happens. Everything downstream depends on how well you did here.

<!-- /presentation:slide -->

<!-- presentation:slide id="tiered-dispatch" layout="table" density="dense" -->

# Tiered Dispatch

`/pm-work-on-project` builds the dependency graph and classifies stories:

- **Tier 1:** No unmet dependencies. Dispatched in parallel.
- **Tier 2:** Dependencies all in Tier 1. Dispatched after Tier 1 completes.
- **Tier N:** Dependencies all in tiers < N.

Each sub-agent runs in isolation. On completion, it files an **execution report** with decisions, assumptions, tradeoffs, and potential conflicts with parallel agents.

| Tier | Eligibility | Dispatch behavior |
| ---- | ----------- | ----------------- |
| Tier 1 | No unmet dependencies | Dispatched in parallel immediately |
| Tier 2 | Dependencies all in Tier 1 | Dispatched after Tier 1 completes |
| Tier N | Dependencies all in earlier tiers | Dispatched after all required earlier tiers complete |

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-comparison" layout="table" density="dense" -->

# Agent PM vs. Symphony vs. Agent Teams

| Dimension            | Agent PM                          | OpenAI Symphony                   | Anthropic Agent Teams             |
| -------------------- | --------------------------------- | --------------------------------- | --------------------------------- |
| Planning layer       | Built-in (`/pm-refine-epic`)      | None                              | None                              |
| Work queue           | Local YAML in `.pm/`              | Linear (external)                 | Native to harness                 |
| Dispatch model       | Tier-based: complete N, then N+1  | Poll every 30s, fill open slots   | Session-managed                   |
| Agent identity       | Heterogeneous roles               | Homogeneous (same prompt)         | Homogeneous                       |
| State persistence    | Filesystem (survives crashes)     | In-memory + Linear                | Session-bound                     |

Symphony is elegant. Elixir OTP supervision, hot-reloadable WORKFLOW.md, Linear as the control plane. But it is a dispatcher, not a planner. Agent Teams is deeply integrated but less customizable. Agent PM includes the planning step.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-lessons" layout="split" density="dense" -->

# What I Learned

Both times, the custom solution worked. Both times, it proved the concept. Both times, it was obsolete within weeks.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Agent PM vs. Agent Teams
Agent PM existed for two months before Anthropic released Agent Teams (March 2026). Native multi-agent orchestration with deeper integration.
<!-- /presentation:column -->
<!-- presentation:column -->
### Custom IPC vs. Shared Memory
I built escalation and shared context via Agent PM's task infrastructure. Anthropic shipped session-shared memories with hooks. The native solution replaced mine.
<!-- /presentation:column -->
<!-- /presentation:block -->

> The lesson is not "don't build." It is that anything you build on a platform this fast-moving is a proof of concept, whether you intended it to be or not.

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base" layout="divider" density="normal" -->

# The Knowledge Base

## Because agents kept forgetting what other agents learned

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-problem" layout="card_grid" density="dense" -->

# The Problem

Once Agent PM grew into a full orchestrator, knowledge created in one session had no way to survive into the next.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### First attempt: worker packets
Comments on stories, managed by the orchestrator after each run. Worked for simple handoffs.
<!-- /presentation:card -->
<!-- presentation:card -->
### Where it broke
Research agents needed a source of truth. Two agents investigating the same question would reach different conclusions because neither could see the other's work.
<!-- /presentation:card -->
<!-- presentation:card -->
### What it became
A shared knowledge base. Simple grep over markdown stopped scaling past 50 notes, once the relationships between them started to matter.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="note-structure" layout="split" density="very_dense" -->

# What a Note Looks Like

Every note is a markdown file with structured frontmatter. Agents write through the MCP server (which validates schemas, resolves tags, and updates backlinks); humans read in Obsidian.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```yaml
---
title: AI Native Software Distribution
type: concept
project: kb-system
tags: [kb-system, architecture, open-source]
status: active
confidence:
  source_type: specification
  verified: false
depends_on:
  - kb-system-installer-ux-findings
aliases:
  - ai-native-distribution
---
```

<!-- /presentation:column -->
<!-- presentation:column -->
### 6 note types
**plans**, **research**, **concepts**, **insights**, **decisions**, **references**
### Relationships are explicit
`depends_on`, `parent`, `implements`, `supersedes` in frontmatter. `[[wikilinks]]` in the body. Shared tags as weak connections.
### 80+ notes across 7 projects
The MCP server runs as a shared HTTP process, so all Claude Code sessions share one index.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-search" layout="card_grid" density="dense" -->

# How Search Works

Embedding-based retrieval (RAG) flattens relationships: two notes about the same topic get similar embeddings regardless of whether one supersedes the other. The KB instead combines three signals via Reciprocal Rank Fusion.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### BM25 (FTS5)
Full-text search with porter stemming. Finds notes by what they say.
<!-- /presentation:card -->
<!-- presentation:card -->
### Personalized PageRank
Walks the note graph seeded from text hits. Finds notes by what they connect to.
<!-- /presentation:card -->
<!-- presentation:card -->
### Trust adjustments
Verified notes rank higher. Notes whose dependencies have been updated rank lower until reviewed.
<!-- /presentation:card -->
<!-- /presentation:block -->

No embeddings means no model dependency, no drift, and every result explains why it was ranked where it is.

<!-- /presentation:slide -->

<!-- presentation:slide id="consolidation-pipeline" layout="card_grid" density="dense" -->

# The Consolidation Pipeline

An overnight agent system (`/consolidate`) that turns the day's scattered work into durable knowledge entries.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Phase 0: Structure
3 parallel agents fix link integrity, triage inbox, repair broken references
<!-- /presentation:card -->
<!-- presentation:card -->
### Phase 1: Harvest
4 parallel agents extract from session logs, PRs, calendar, Slack
<!-- /presentation:card -->
<!-- presentation:card -->
### Phase 2: Synthesize
Opus analyzes read-only, Sonnet agents execute edits, Opus reviews the diff
<!-- /presentation:card -->
<!-- /presentation:block -->

The pipeline feeds from `kb_stale`: a tool that flags notes for dependency drift, broken links, age, or community orphaning. Notes that need attention surface automatically.

<!-- /presentation:slide -->

<!-- presentation:slide id="distribution" layout="divider" density="normal" -->

# Distribution

## Building the KB installer changed how I think about sharing software

<!-- /presentation:slide -->

<!-- presentation:slide id="copying-caveat" layout="emphasis" density="normal" -->

# A Caveat

> Everything I've shown you today is built for how I think. These are my tools, shaped by my problems, my habits, and my tolerance for overengineering.

The point is not to copy them. It is to show what becomes possible when you build for your own workflow instead of adopting someone else's solution to someone else's problem.

<!-- /presentation:slide -->

<!-- presentation:slide id="problem-with-copying" layout="content" density="dense" -->

# The Problem with Copying

There are 44,000+ skills on distribution platforms and 36,900+ stars on awesome-cursorrules. People share configuration files, copy them, and run them unchanged.

We are so different from one another in how we structure our work that this will only produce suboptimal workflows. Everything can be made custom, and AI makes this trivially easy. So instead of looking for the right template, take the idea and rebuild it until it fits the way you think.

But that raises a question: if copying is wrong, how *should* we distribute AI-native software?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-core-setup" layout="code" density="dense" -->

# Dry Run: Phase A - Core Setup

*The installer asks one question at a time. No batching.*

```
KB System Installer
===================

This will set up a personal knowledge base with some or all of:
- A structured markdown vault (Obsidian-compatible)
- A /kb skill for filing content from any AI coding session
- An overnight consolidation pipeline
- An MCP server for ranked search and write validation

I'll walk you through the components, research your tools, then install everything.

What should I call you?
> Sarah

Where would you like your knowledge base? (full path)
> ~/dev/kb

  I'll create a new vault at ~/dev/kb.

What sources of information would you like the system to harvest?
For example: code changes (GitHub), messaging (Slack), calendar, documents.
> GitHub, Slack, and Google Calendar
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-components" layout="code" density="dense" -->

# Dry Run: Phase B - Components

*Each component is presented with what it does and what you lose without it.*

```
The foundation is a structured markdown vault with frontmatter-based notes,
wikilinks, an index, and a log. This is always installed.

The /kb skill lets any Claude Code session file content to your KB as a
background task. You'd use it like /kb <content> or /kb context save <project>.
Without it, you'd write notes manually.

  Include the /kb skill? (recommended)
  > Yes

The consolidation pipeline runs on a schedule, harvesting GitHub, Slack, and
Google Calendar into the KB. Without it, only what you explicitly file gets in.

  Include the consolidation pipeline? (recommended)
  > Yes

  Detected Python 3.12.8

The MCP server provides ranked search (BM25 + graph signals), write validation,
and staleness detection. Without it, agents use Glob/Grep with no ranking.

  Include the MCP server? (recommended)
  > Yes
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-research" layout="code" density="normal" -->

# Dry Run: Phase C - Research

*This is where a traditional installer cannot follow. One parallel agent per source, all running simultaneously.*

```
Researching integrations for your 3 sources...

  [Agent 1] Searching: "GitHub MCP server" + "GitHub Claude Code integration"
  [Agent 2] Searching: "Slack MCP server" + "Slack Claude Code integration"
  [Agent 3] Searching: "Google Calendar MCP server" + "Google Calendar integration"

  All 3 research agents completed.
```

Each agent searches for MCP servers, CLI tools, and REST APIs. For each option found, it checks: is it from a trusted source? What permissions does it require? Is it actively maintained? Are there known security concerns?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-findings" layout="code" density="dense" -->

# Dry Run: Phase D - Findings

*The installer presents what it found, checks what is already installed, and runs smoke tests.*

```
Source: GitHub
  Approach: gh CLI (official, already installed)
  Smoke test: gh api user → PASS
  Status: Ready

Source: Slack
  Approach: @anthropic/slack-mcp (official Anthropic MCP)
  Status: Not installed
  "Want me to help set this up, or skip for now?"
  > Set it up

Source: Google Calendar
  Approach: google-workspace MCP (already configured)
  Smoke test: calendar_listEvents → PASS
  Status: Ready
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-source-configuration" layout="code" density="dense" -->

# Dry Run: Phase E - Source Configuration

*Targeted questions per source, adapted to the tools the research phase found.*

```
For GitHub: Which repositories matter most?
> All repos under my-org/

For Slack: Which channels should consolidation scan?
> #engineering, #incidents, and any DM with my name

For Calendar: Which calendar?
> Primary. Meeting notes live in Google Docs.


Here's what we have so far:
  - Vault at ~/dev/kb with note types: plan, research, concept,
    insight, decision, reference
  - /kb skill, consolidation, MCP server all enabled
  - Sources: GitHub (gh), Slack (MCP), Calendar (MCP)

Is there anything you'd like to customize?
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-customization" layout="code" density="dense" -->

# Dry Run: Phase F - Customization

*This is where the installer stops being a form. The user can request features, and the installer checks feasibility against the actual codebase.*

```
> I want an ADR note type for architecture decisions. And I'd like
  the consolidation to tag notes by project automatically.

  ADR note type: I'll add notes/adrs/ to the vault structure and
  register "adr" as a note type with fields for status, context,
  decision, and consequences.

  Auto-tagging by project: let me check if the server supports this.

  [Evaluator agent spawned → reading kb-server codebase...]

  Assessment: config-only change. The server already infers project
  from vault path. Adding tag inference requires a new config
  section in kb-server.yaml. No code changes needed.

  Both customizations will be included. Anything else?
> That's it.
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-finalize-generate" layout="split" density="very_dense" -->

# Dry Run: Phase G-J - Finalize and Generate

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
Which model for analysis agents?
  (default: claude-opus-4-6)
> Default is fine

Which model for execution agents?
  (default: claude-sonnet-4-6)
> Default

When should consolidation run?
> 2 AM, weekdays only

Proceed with installation?
> Yes
```

<!-- /presentation:column -->
<!-- presentation:column -->

```
Installation Summary
====================

Components: vault, /kb skill,
  consolidation, MCP server
Sources: GitHub (gh), Slack (MCP),
  Calendar (MCP)
Custom: ADR note type,
  auto-tagging by project
Models: opus/sonnet
Schedule: 02:00 weekdays

Generating 9 artifacts...
  ✓ kb-protocol.md
  ✓ kb/skill.md
  ✓ consolidate.md
  ✓ kb-server.yaml
  ✓ consolidate-gather.sh
  ✓ com.kb-system.consolidate.plist
  ✓ intent.yaml
  ✓ CLAUDE.md injection
  ✓ installed.json

Done. Vault initialized at ~/dev/kb
```

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="installer-reads-history" layout="card_grid" density="dense" -->

# The Installer Reads Your History

Before the conversation begins, the installer scans Claude Code session telemetry: session count, tool diversity, sub-agent usage, configured MCP servers, project directories, custom skills and hooks. It uses this to calibrate the conversation without ever disclosing the profiling.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Depth of explanation
An amateur gets full component descriptions with tradeoffs. An experienced user gets a table and a "which of these?" prompt. The information is the same; the delivery adapts.
<!-- /presentation:card -->
<!-- presentation:card -->
### Proactive suggestions
The installer does not wait for the user to describe their workflow. It already sees 14 projects under ~/dev/, MCPs configured, Python hooks active. It suggests a project registry, MCP-backed harvesting, and tag vocabulary seeded from existing projects.
<!-- /presentation:card -->
<!-- presentation:card -->
### Customization surface
Power users are offered deeper options (custom intents, note type extensions, consolidation tuning) that would overwhelm a beginner. The options are not hidden; they are surfaced at the right level for the user.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="two-users-same-installer" layout="split" density="very_dense" -->

# Two Users, Same Installer

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Someone with 10 sessions

```
The /kb skill lets any Claude Code
session file content to your KB as a
background task. You'd use it like
/kb <content> or /kb context save.
Without it, you'd write notes
manually.

Include the /kb skill? (recommended)
> Yes
```

*Full explanation. Concrete usage example. Clear recommendation.*

<!-- /presentation:column -->
<!-- presentation:column -->
### Someone with 500 sessions

```
Components:

| Component      | Requires     |
|----------------|--------------|
| Vault          | (always)     |
| /kb skill      | nothing      |
| Consolidation  | schedule     |
| MCP server     | Python 3.12+ |

Which do you want?
> All of them.

I see you work across 3 Kubernetes
projects with heavy use of ADRs in
your git history. Want me to add an
ADR note type with Nygard-style
fields and seed the tag vocabulary
from your existing project names?
```

*Same information, different depth. Proactive suggestions drawn from what it found in the user's environment.*

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="three-agents-one-conversation" layout="card_grid" density="dense" -->

# Three Agents, One Conversation

The user sees a single conversation. Behind it, three agents with different roles.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Installer
User-facing, long-lived. Owns the conversation, generates standard artifacts, spawns sub-agents when needed. The user never sees the orchestration.
<!-- /presentation:card -->
<!-- presentation:card -->
### Evaluator
Background, short-lived, spawned per request. Reads the server codebase and assesses feasibility of user requests. Strictly read-only.
<!-- /presentation:card -->
<!-- presentation:card -->
### Builder
Background, potentially long-lived. Receives a specification co-designed by Installer and user. Plans implementation, writes code, tests, validates.
<!-- /presentation:card -->
<!-- /presentation:block -->

The developer builds a legible codebase. The AI reads it, understands it, and reshapes it to fit each user. The "product" is the installation prompt and a codebase clear enough for an AI to navigate.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-pipeline" layout="divider" density="normal" -->

# The Translation Pipeline

## Same patterns, different domain

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-problem" layout="content" density="normal" -->

# The Problem

My blog (dan.rio) is bilingual. The first version of the translation system worked the obvious way: hand the model a post and ask for a Portuguese version.

The output was always correct. It was also always flat: the kind of text that communicates without engaging. The meaning crossed over; the voice, the rhythm, the rhetorical texture did not.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-insight" layout="code" density="dense" -->

# The Insight

The fix did not come from a better model or a longer prompt. It came from reading what translation institutes actually recommend.

They do not say "translate better." They say: analyze the source as authored writing before you touch it, settle terminology disputes before drafting, keep the critic independent from the translator, and verify that revisions actually addressed what the critique found.

Each of those recommendations became a stage in a 7,500-line pipeline, built with Claude Code.

```
source_analysis → terminology_policy → translate → [critique → revise] × N → final_review
```

Stages 1-2 run once and produce binding policy documents that constrain everything downstream. Translation and revision use GPT-5.4 high for generative work. Critique and final review use GPT-5.2 medium: a deliberately different model, to prevent the translator from grading its own homework.

<!-- /presentation:slide -->

<!-- presentation:slide id="terminology-policy" layout="code" density="dense" -->

# What a Terminology Policy Looks Like

Before any translation begins, Stage 2 produces an artifact-wide terminology policy. Every downstream stage receives this document and is bound by its decisions.

```json
{
  "keep_english": ["Claude Code", "MCP", "API", "Agent PM"],
  "localize": ["knowledge base" → "base de conhecimento",
               "pull request" → "pull request"],
  "resolved_decisions": [
    {
      "source_term": "AI Platform",
      "preferred_rendering": "AI Platform",
      "scope": "artifact-wide",
      "rationale": "team name, not a generic concept"
    },
    {
      "source_term": "harness",
      "preferred_rendering": "harness",
      "scope": "artifact-wide",
      "rationale": "technical term used throughout; localizing to 'arnês'
                    would lose the metaphor"
    }
  ]
}
```

<!-- /presentation:slide -->

<!-- presentation:slide id="critique-finding" layout="code" density="dense" -->

# What a Critique Finding Looks Like

The critique stage does not say "the translation is 78% good." It produces span-based findings: here is the source text, here is what you wrote, here is what is wrong with it, and here is how to fix it.

```json
{
  "severity": "major",
  "category": "tone_flattening",
  "source_span": "the voice did not survive the trip",
  "target_span": "a voz não sobreviveu",
  "description": "Lost the rhetorical weight of 'the trip' as a metaphor
                  for the act of translation itself",
  "fix_hint": "Restore the journey metaphor: 'a voz não sobreviveu
              à travessia'"
}
```

The revision stage receives these findings and must address each one. The final review stage then checks whether the revision actually applied the fixes or merely claimed to: verify, do not trust.

<!-- /presentation:slide -->

<!-- presentation:slide id="quality-gate" layout="split" density="very_dense" -->

# The Quality Gate

The pipeline does not ask the model whether the translation is good enough. It uses a deterministic rubric with weighted dimensions and hard thresholds.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

| Dimension             | Weight |
| --------------------- | ------ |
| Accuracy              | 30%    |
| Terminology           | 20%    |
| Markdown fidelity     | 20%    |
| Linguistic conventions | 10%   |
| Style and register    | 10%    |
| Locale conventions    | 5%     |
| Audience clarity      | 5%     |

<!-- /presentation:column -->
<!-- presentation:column -->
### Decision thresholds
**Accept:** score >= 92, zero major errors
**Refine:** score 88-92, loop back to critique
**Escalate:** score 75-88, or stalled for 2 loops
**Fail:** score < 60, or any critical error
### Hard gates
Accuracy >= 85, terminology >= 80, markdown fidelity >= 95. If any of these fail, the pipeline refines regardless of the overall score.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="where-this-goes-next" layout="card_grid" density="dense" -->

# Where This Goes Next

The pipeline works. The translations read like Portuguese, not like English wearing a Portuguese costume. But there is room to improve.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### GEPA for prompt optimization
Early exploration into using GEPA to optimize the stage prompts systematically rather than by hand-tuning. Nothing conclusive yet, but the pipeline's typed contracts make it a good candidate: each stage has measurable inputs and outputs.
<!-- /presentation:card -->
<!-- presentation:card -->
### Document-level coherence
The pipeline currently translates per-post. Cross-paragraph coherence within a post is handled by the terminology policy, but there is no mechanism for coherence across posts in a series.
<!-- /presentation:card -->
<!-- presentation:card -->
### MQM error classification
The critique categories are hand-defined. Moving to MQM (Multidimensional Quality Metrics) would align with how professional translation quality is actually measured.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="thanks" layout="lead" density="normal" -->

# Thanks

## The agent executes. Your job is deciding what it should execute.

dan.rio | github.com/danielcavalli

<!-- /presentation:slide -->
