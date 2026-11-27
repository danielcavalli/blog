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

Daniel Cavalli · dan.rio · April 2026

<!-- /presentation:slide -->

<!-- presentation:slide id="bio-and-agenda" layout="bio" density="normal" -->

# Daniel Cavalli

Senior Machine Learning Engineer · Nubank

Economics at UFRJ, causal modeling. Nine years in ML: models, AI platforms, and now agents and behavioural world models.

![Daniel Cavalli](how-i-use-ai-agents.assets/profile-picture.png)

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

<!-- presentation:slide id="stateless-model" layout="dark_content" density="normal" -->

# The model is stateless

Every time you press Enter, the harness rebuilds the context from scratch. **It is not memory. It is reconstruction.**

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Sessions accumulate residue
The model anchors on what came first, not what came last.
<!-- /presentation:card -->
<!-- presentation:card -->
### More context, worse output
The model hedges, trying to reconcile things that no longer matter.
<!-- /presentation:card -->
<!-- presentation:card -->
### The real skill is removal
Know what to collapse, what to discard, and what to hand off.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="four-rules" layout="card_grid" density="normal" -->

# Four rules

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. One session, one task
Research, spec and implementation never share a session. Each starts from the last one's output.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Curate what the model sees
Irrelevant context does not just waste tokens. It degrades the output.
<!-- /presentation:card -->
<!-- /presentation:block -->
<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 3. Sandbox everything
Catch errors outside the context window. A hook that formats on save costs zero tokens.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Then go multi-agent
Once sessions are isolated, split the work. Each agent gets only what it needs.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="humans-job" layout="emphasis" density="normal" -->

# The human's job

> Agents are remarkably good at single-domain work. The moment you pull threads from several domains into one argument, they fall apart.

The agent executes. Your job is deciding what it should execute.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm" layout="divider" density="normal" -->

# Agent PM

## Because I have too many ideas and agents made the problem worse

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-problem" layout="split" density="normal" -->

# The problem

Before agents, my ideas were bounded by how fast I could type. **With agents, the bound disappeared.**

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### What I gained
Multiple hypotheses running at once.
<!-- /presentation:column -->
<!-- presentation:column -->
### What I lost
The ability to distinguish priorities from distractions.
<!-- /presentation:column -->
<!-- /presentation:block -->

Agent PM started as a way to manage my own focus.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-what-it-is" layout="split" density="normal" -->

# What it is

YAML in a `.pm/` directory, versioned with the code. A CLI, an MCP server and Claude Code commands.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
.pm/
  project.yaml      # the project
  index.yaml        # summary, kept by pm
  epics/
    E001-auth.yaml  # an epic, its stories
  reports/
    E001-S001-report.yaml
  agents/
    agent-abc.yaml  # heartbeat, state
  adrs/
    ADR-001.yaml    # a decision
```

<!-- /presentation:column -->
<!-- presentation:column -->

```yaml
stories:
  - id: S001
    title: "JWT middleware"
    acceptance_criteria:
      - "JWT validated on every request"
      - "Expired tokens return 401"
    depends_on: []
    story_points: 3
    priority: high
```

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-flow" layout="card_grid" density="normal" -->

# The flow

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. Spec
I write it. Current state, target state, constraints, pitfalls, exclusions.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Refine
`/pm-refine-epic` produces epics and stories with dependencies. Human approves before execution.
<!-- /presentation:card -->
<!-- presentation:card -->
### 3. Execute
`/pm-work-on-project` dispatches agents in parallel per tier.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Monitor
`/supervisor` triages: Blocked > Stale > Completed > Running.
<!-- /presentation:card -->
<!-- /presentation:block -->

The spec is where all the real thinking happens.

<!-- /presentation:slide -->

<!-- presentation:slide id="tiered-dispatch" layout="table" density="normal" -->

# Tiered dispatch

`/pm-work-on-project` builds the dependency graph and classifies stories into tiers.

| Tier | Eligibility | Dispatch |
| ---- | ----------- | -------- |
| Tier 1 | No unmet dependencies | In parallel, immediately |
| Tier 2 | Dependencies all in Tier 1 | After Tier 1 completes |
| Tier N | Dependencies all in earlier tiers | After those tiers complete |

Each sub-agent runs in isolation and files an execution report on completion.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-comparison" layout="table" density="normal" -->

# Agent PM vs. Symphony vs. Agent Teams

Symphony and Agent Teams dispatch. Agent PM also plans.

|            | Agent PM                     | OpenAI Symphony    | Anthropic Agent Teams |
| ---------- | ---------------------------- | ------------------ | --------------------- |
| Planning   | Built in (`/pm-refine-epic`) | None               | None                  |
| Work queue | Local YAML in `.pm/`         | Linear (external)  | Native to the harness |
| Dispatch   | By tier: finish N, then N+1  | Polls every 30 s   | Session-managed       |
| Agents     | Different roles              | One prompt for all | One prompt for all    |
| State      | Files: survives crashes      | In memory + Linear | Ends with the session |

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-lessons" layout="split" density="normal" -->

# What I learned

Both times, the custom solution worked. **Both times, it was obsolete within weeks.**

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Agent PM vs. Agent Teams
Agent PM existed for two months before Anthropic released Agent Teams.
<!-- /presentation:column -->
<!-- presentation:column -->
### Custom IPC vs. shared memory
Anthropic shipped session-shared memories. The native solution replaced mine.
<!-- /presentation:column -->
<!-- /presentation:block -->

> The lesson is not "don't build." It is that anything you build on a platform this fast-moving is a proof of concept.

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base" layout="divider" density="normal" -->

# The Knowledge Base

## Because agents kept forgetting what other agents learned

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-problem" layout="card_grid" density="normal" -->

# The problem

Knowledge created in one session had no way to survive into the next.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### First try: worker packets
Comments on stories, managed by the orchestrator. Worked for simple handoffs.
<!-- /presentation:card -->
<!-- presentation:card -->
### Where it broke
Two agents investigating the same question would reach different conclusions.
<!-- /presentation:card -->
<!-- presentation:card -->
### What it became
A shared knowledge base. Simple grep over markdown stopped scaling past 50 notes.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="note-structure" layout="split" density="normal" -->

# What a note looks like

Every note is a markdown file with structured frontmatter. Agents write through the MCP server; humans read in Obsidian.

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
---
```

<!-- /presentation:column -->
<!-- presentation:column -->
### 6 note types
plans, research, concepts, insights, decisions, references
### Relationships are explicit
`depends_on`, `parent`, `implements`, `supersedes` in frontmatter. `[[wikilinks]]` in the body.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-search" layout="card_grid" density="normal" -->

# How search works

Embedding-based retrieval (RAG) flattens relationships. The KB instead combines three signals via Reciprocal Rank Fusion.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### BM25 (FTS5)
Finds notes by what they say.
<!-- /presentation:card -->
<!-- presentation:card -->
### Personalized PageRank
Finds notes by what they connect to.
<!-- /presentation:card -->
<!-- presentation:card -->
### Trust adjustments
Verified notes rank higher. Notes with updated dependencies rank lower until reviewed.
<!-- /presentation:card -->
<!-- /presentation:block -->

No embeddings means no model dependency, no drift, and every result explains its rank.

<!-- /presentation:slide -->

<!-- presentation:slide id="consolidation-pipeline" layout="card_grid" density="normal" -->

# The consolidation pipeline

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

<!-- /presentation:slide -->

<!-- presentation:slide id="distribution" layout="divider" density="normal" -->

# Distribution

## Building the KB installer changed how I think about sharing software

<!-- /presentation:slide -->

<!-- presentation:slide id="copying-caveat" layout="emphasis" density="normal" -->

# A caveat

> Everything I've shown you today is built for how I think. These are my tools, shaped by my problems, my habits, and my tolerance for overengineering.

The point is not to copy them.

<!-- /presentation:slide -->

<!-- presentation:slide id="problem-with-copying" layout="content" density="normal" -->

# The problem with copying

There are 44,000+ skills on distribution platforms and 36,900+ stars on awesome-cursorrules. **People copy them and run them unchanged.**

This will only produce suboptimal workflows. Take the idea and rebuild it until it fits the way you think.

If copying is wrong, how *should* we distribute AI-native software?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-core-setup" layout="code" density="normal" -->

# Dry run: core setup

The installer asks one question at a time.

```
KB System Installer

I'll walk you through the components,
research your tools, then install it all.

What should I call you?
> Sarah

Where would you like your knowledge base?
> ~/dev/kb

What sources should the system harvest?
> GitHub, Slack, and Google Calendar
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-components" layout="code" density="normal" -->

# Dry run: components

Each component is presented with what it does and **what you lose without it**.

```
The consolidation pipeline runs on a schedule,
harvesting GitHub, Slack, and Google Calendar.
Without it, only what you explicitly file gets in.

  Include the consolidation pipeline? (recommended)
  > Yes

The MCP server provides ranked search and write
validation. Without it, agents use Glob/Grep with
no ranking.

  Include the MCP server? (recommended)
  > Yes
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-research" layout="code" density="normal" -->

# Dry run: research

This is where a traditional installer cannot follow.

```
Researching integrations for your 3 sources...

  [Agent 1] Searching: "GitHub MCP server"
  [Agent 2] Searching: "Slack MCP server"
  [Agent 3] Searching: "Google Calendar MCP server"

  All 3 research agents completed.
```

Each agent checks every option it finds: trusted source? Permissions? Actively maintained? Known security concerns?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-findings" layout="code" density="normal" -->

# Dry run: findings

The installer presents what it found, checks what is already installed, and runs smoke tests.

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
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-source-configuration" layout="code" density="normal" -->

# Dry run: source configuration

Targeted questions per source, adapted to the tools the research phase found.

```
For GitHub: Which repositories matter most?
> All repos under my-org/

For Slack: Which channels should consolidation scan?
> #engineering, #incidents, and any DM with my name

For Calendar: Which calendar?
> Primary. Meeting notes live in Google Docs.

Is there anything you'd like to customize?
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-customization" layout="code" density="normal" -->

# Dry run: customization

This is where the installer stops being a form.

```
> I'd like the consolidation to tag notes by project
  automatically.

  Auto-tagging by project: let me check if the server
  supports this.

  [Evaluator agent spawned → reading kb-server codebase...]

  Assessment: config-only change. The server already
  infers project from vault path. No code changes needed.
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-finalize-generate" layout="split" density="normal" -->

# Dry run: finalize and generate

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
Which model for analysis agents?
  (default: claude-opus-4-6)
> Default is fine

When should consolidation run?
> 2 AM, weekdays only

Proceed with installation?
> Yes
```

<!-- /presentation:column -->
<!-- presentation:column -->

```
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

<!-- presentation:slide id="installer-reads-history" layout="card_grid" density="normal" -->

# The installer reads your history

Before the conversation begins, the installer scans Claude Code session telemetry. It uses this to calibrate the conversation without ever disclosing the profiling.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Depth of explanation
The information is the same; the delivery adapts.
<!-- /presentation:card -->
<!-- presentation:card -->
### Proactive suggestions
The installer does not wait for the user to describe their workflow.
<!-- /presentation:card -->
<!-- presentation:card -->
### Customization surface
Power users are offered deeper options that would overwhelm a beginner.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="two-users-same-installer" layout="split" density="dense" -->

# Two users, same installer

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Someone with 10 sessions

```
The /kb skill lets any Claude Code
session file content to your KB as a
background task. Without it, you'd
write notes manually.

Include the /kb skill? (recommended)
> Yes
```

*Full explanation. Clear recommendation.*

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
```

*Same information, different depth.*

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="three-agents-one-conversation" layout="card_grid" density="normal" -->

# Three agents, one conversation

The user sees a single conversation. Behind it, three agents with different roles.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Installer
User-facing, long-lived. Owns the conversation, spawns sub-agents when needed.
<!-- /presentation:card -->
<!-- presentation:card -->
### Evaluator
Background, short-lived. Assesses feasibility of user requests. Strictly read-only.
<!-- /presentation:card -->
<!-- presentation:card -->
### Builder
Background, potentially long-lived. Plans implementation, writes code, tests, validates.
<!-- /presentation:card -->
<!-- /presentation:block -->

The "product" is the installation prompt and a codebase clear enough for an AI to navigate.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-pipeline" layout="divider" density="normal" -->

# The Translation Pipeline

## Same patterns, different domain

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-problem" layout="content" density="normal" -->

# The problem

My blog is bilingual. The first version of the translation system worked the obvious way: hand the model a post and ask for a Portuguese version.

The output was always correct. **It was also always flat.** The meaning crossed over; the voice, the rhythm, the rhetorical texture did not.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-insight" layout="code" density="normal" -->

# The insight

The fix was not a better model. It was doing what translation institutes recommend.

```
source_analysis → terminology_policy → translate → [critique → revise] × N → final_review
```

A different model critiques than translates, so the translator never grades its own homework.

<!-- /presentation:slide -->

<!-- presentation:slide id="terminology-policy" layout="code" density="normal" -->

# What a terminology policy looks like

Before any translation begins, Stage 2 produces a terminology policy. **Every downstream stage is bound by its decisions.**

```json
{
  "keep_english": ["Claude Code", "MCP", "API", "Agent PM"],
  "localize": ["knowledge base" → "base de conhecimento"],
  "resolved_decisions": [{
    "source_term": "harness",
    "preferred_rendering": "harness",
    "scope": "artifact-wide",
    "rationale": "localizing to 'arnês' would lose
                  the metaphor"
  }]
}
```

<!-- /presentation:slide -->

<!-- presentation:slide id="critique-finding" layout="code" density="normal" -->

# What a critique finding looks like

The critique stage does not say "the translation is 78% good." **It produces span-based findings.**

```json
{
  "severity": "major",
  "category": "tone_flattening",
  "source_span": "the voice did not survive the trip",
  "target_span": "a voz não sobreviveu",
  "description": "Lost the rhetorical weight of 'the trip'
    as a metaphor for the act of translation itself",
  "fix_hint": "Restore the journey metaphor:
    'a voz não sobreviveu à travessia'"
}
```

The final review checks whether the revision actually applied the fixes: verify, do not trust.

<!-- /presentation:slide -->

<!-- presentation:slide id="quality-gate" layout="split" density="dense" -->

# The quality gate

A fixed rubric decides, not the model.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

| Dimension              | Weight |
| ---------------------- | ------ |
| Accuracy               | 30%    |
| Terminology            | 20%    |
| Markdown fidelity      | 20%    |
| Linguistic conventions | 10%    |
| Style and register     | 10%    |
| Locale conventions     | 5%     |
| Audience clarity       | 5%     |

<!-- /presentation:column -->
<!-- presentation:column -->

| Score                     | Then           |
| ------------------------- | -------------- |
| ≥ 92, no major error      | Accept         |
| 88–92                     | Critique again |
| 75–88, or 2 stalled loops | Escalate       |
| < 60, or a critical error | Fail           |

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="where-this-goes-next" layout="card_grid" density="normal" -->

# Where this goes next

The translations read like Portuguese, not like English wearing a Portuguese costume. But there is room to improve.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### GEPA prompt optimization
Optimizing the stage prompts systematically, not by hand. Nothing conclusive yet.
<!-- /presentation:card -->
<!-- presentation:card -->
### Document-level coherence
There is no mechanism for coherence across posts in a series.
<!-- /presentation:card -->
<!-- presentation:card -->
### MQM error classification
The critique categories are hand-defined. Moving to MQM would align them with how professional translation quality is measured.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="thanks" layout="lead" density="normal" -->

# Thanks

## The agent executes. Your job is deciding what it should execute.

dan.rio · github.com/danielcavalli

<!-- /presentation:slide -->
