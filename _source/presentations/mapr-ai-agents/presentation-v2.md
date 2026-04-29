---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
  section {
    background: #ffffff;
    color: #111111;
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    font-size: 22px;
    line-height: 1.5;
    padding: 48px 64px;
  }
  h1, h2, h3 {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    color: #1A6B7A;
    letter-spacing: -0.03em;
  }
  h1 {
    font-size: 1.8em;
    font-weight: 600;
    margin-bottom: 0.5em;
  }
  h2 {
    font-size: 1.3em;
    font-weight: 500;
    letter-spacing: -0.02em;
    margin-top: 0;
  }
  code {
    background: #F4F4F4;
    color: #1A6B7A;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.9em;
  }
  pre {
    background: #1A1A1A !important;
    border-radius: 8px;
    padding: 16px 24px !important;
    font-size: 0.78em;
    margin: 8px 0;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
  }
  figure, img { border: none !important; outline: none !important; }
  pre code {
    background: transparent;
    color: #e0e0e0;
    padding: 0;
  }
  a { color: #1A6B7A; }
  table { font-size: 0.78em; width: 100%; margin: 12px 0; border-collapse: collapse; border-spacing: 0; }
  table, thead, tbody, tr, th, td { border: none !important; outline: none !important; border-style: none !important; }
  th {
    background: #1A6B7A;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
  }
  th:first-child { border-radius: 8px 0 0 0; }
  th:last-child { border-radius: 0 8px 0 0; }
  td {
    background: #F5F5F5;
    padding: 8px 16px;
  }
  blockquote {
    border-left: 3px solid #1A6B7A;
    background: #F4F4F4;
    padding: 12px 24px;
    margin: 12px 0;
    font-size: 0.95em;
    color: #333333;
    border-radius: 0 8px 8px 0;
  }
  ul, ol { margin: 6px 0; }
  li { margin: 4px 0; }
  p { margin: 10px 0; }
  section::after { color: #6B6B6B; }
  strong { color: #1A1A1A; }
  section.lead {
    background: #152D38;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  section.lead h1 {
    font-size: 2.6em;
    text-align: center;
    color: #ffffff;
  }
  section.lead h2 {
    text-align: center;
    font-size: 1.2em;
    color: #8CC8D4;
    font-weight: 400;
  }
  section.lead p {
    text-align: center;
    color: #B8DEE6;
    font-size: 1.05em;
  }
  section.divider {
    background: #152D38;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  section.divider h1 {
    font-size: 2.4em;
    text-align: center;
    color: #ffffff;
  }
  section.divider h2 {
    text-align: center;
    color: #8CC8D4;
    font-size: 1.1em;
    font-weight: 400;
  }
  section.emphasis {
    background: #F4F4F4;
  }
  section.emphasis blockquote {
    background: #ffffff;
    font-size: 1.15em;
    padding: 24px 32px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .bio-layout {
    display: flex;
    gap: 48px;
    align-items: flex-start;
    margin-top: 0;
  }
  .bio-content { flex: 1; }
  .bio-content h1 { margin-bottom: 4px; }
  .bio-photo {
    flex-shrink: 0;
    margin-top: 8px;
  }
  .bio-photo img {
    width: 260px;
    height: 260px;
    border-radius: 16px;
    object-fit: cover;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  }
  .bio-detail {
    color: #6B6B6B;
    font-size: 0.88em;
    margin: 2px 0;
  }
  .card-row {
    display: flex;
    gap: 20px;
    margin-top: 16px;
  }
  .card {
    flex: 1;
    background: #F5F5F5;
    border-radius: 10px;
    padding: 20px 24px;
    border-left: 3px solid #1A6B7A;
  }
  .card h3 {
    font-size: 0.95em;
    margin: 0 0 8px 0;
  }
  .card p {
    font-size: 0.82em;
    color: #555;
    margin: 0;
    line-height: 1.45;
  }
  .card-dark {
    background: #152D38;
    border-left: 3px solid #8CC8D4;
  }
  .card-dark h3 { color: #8CC8D4; }
  .card-dark p { color: #B8DEE6; }
  .split {
    display: flex;
    gap: 40px;
    align-items: flex-start;
  }
  .split > div { flex: 1; }
  .split > div + div { border-left: 2px solid #E0E0E0; padding-left: 40px; }
  .dim { color: #6B6B6B; font-size: 0.85em; }
  .small { font-size: 0.8em; }
  section.dark-content {
    background: #1A1A1A;
    color: #E0E0E0;
    padding: 36px 56px 28px;
  }
  section.dark-content h1 {
    color: #ffffff;
    font-size: 1.5em;
    margin: 0 0 20px 0;
  }
  section.dark-content blockquote {
    background: #252525;
    color: #B8DEE6;
    border-left-color: #1A6B7A;
  }
  footer {
    color: #6B6B6B;
    font-size: 0.65em;
  }
footer: Daniel Cavalli | dan.rio
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

# How I Use AI Agents

## What I built, what broke, and what survived

Daniel Cavalli | dan.rio

---

<!-- _paginate: false -->
<!-- _footer: '' -->

<div class="bio-layout">
  <div class="bio-content">
    <h1 style="margin-bottom: 4px;">Daniel Cavalli</h1>
    <p class="bio-detail">Senior Machine Learning Engineer at Nubank</p>
    <p class="bio-detail">9 years in ML. Studied economics. Writes at dan.rio</p>
    <div style="margin-top: 28px;">
      <table>
        <tr><th></th><th>Section</th><th>Focus</th></tr>
        <tr><td>1</td><td>The Foundation</td><td>Why context is everything</td></tr>
        <tr><td>2</td><td>Agent PM</td><td>Multi-agent orchestration from specs</td></tr>
        <tr><td>3</td><td>The Knowledge Base</td><td>Graph search for agent memory</td></tr>
        <tr><td>4</td><td>Distribution</td><td>Why copying skills is the wrong idea</td></tr>
        <tr><td>5</td><td>Translation Pipeline</td><td>Same patterns applied to localization</td></tr>
      </table>
    </div>
  </div>
  <div class="bio-photo">
    <img src="./assets/profile-picture.png" />
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# The Foundation

## Continuity is an illusion you engineer, not something the model gives you

---

<!-- _class: dark-content -->

# The model is stateless

Every time you press Enter, the harness rebuilds the full context from scratch. The model responds. Then it forgets everything.

> The continuity you experience is built from context that someone, or something, chose to put back. It is not memory. It is reconstruction.

<div class="card-row">
  <div class="card card-dark">
    <h3>Sessions accumulate residue</h3>
    <p>Dead ends, mixed goals, stale constraints. The model anchors on what came first, not what came last.</p>
  </div>
  <div class="card card-dark">
    <h3>More context can mean worse output</h3>
    <p>Most people's instinct is to keep more history alive. The model starts hedging, qualifying, trying to reconcile things that no longer matter.</p>
  </div>
  <div class="card card-dark">
    <h3>The real skill is removal</h3>
    <p>Not expanding context. Knowing what to collapse, what to discard, and what to carry forward as a handoff artifact.</p>
  </div>
</div>

---

# Four Rules

<div class="card-row">
  <div class="card">
    <h3>1. One session, one task</h3>
    <p>Research sessions produce research notes. Spec sessions produce implementation packets. Implementation starts fresh from the packet. They never share a session.</p>
  </div>
  <div class="card">
    <h3>2. Curate what the model sees</h3>
    <p>Every tool schema, every MCP instruction, every stale fragment competes for attention. Irrelevant context does not just waste tokens. It actively degrades output.</p>
  </div>
</div>
<div class="card-row">
  <div class="card">
    <h3>3. Sandbox everything</h3>
    <p>Catch errors outside the context window so they never consume tokens to debug. A hook that formats code on save or validates YAML costs zero tokens and prevents problems the model would otherwise spend dozens of messages fixing.</p>
  </div>
  <div class="card">
    <h3>4. Multi-agent is the obvious next step</h3>
    <p>Once you accept isolated sessions, the question becomes how to split work across them. Each agent gets only what it needs. Decompose, parallelize, integrate.</p>
  </div>
</div>

---

<!-- _class: emphasis -->

# The Human's Job

> Agents are remarkably good at single-domain work. But the moment you need to pull threads from multiple domains into the same argument, they fall apart.

The human advantage is not "thinking" in general. It is cross-domain synthesis: holding three different contexts in your head, cross-referencing them, knowing which constraints are real and which are inherited from a conversation that no longer applies.

The agent executes. Your job is deciding what it should execute.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Agent PM

## Because I have too many ideas and agents made the problem worse

---

# The Problem

I am overly enthusiastic about new ideas, which leads me to explore too many paths at once.

Before agents, this was bounded by how fast I could type. With agents, the bound disappeared. I could pursue multiple directions simultaneously and check results later.

<div class="split">
  <div>
    <h3>What I gained</h3>
    <p>Actual parallel exploration. Multiple hypotheses running at once. Results waiting for me when I checked back.</p>
  </div>
  <div>
    <h3>What I lost</h3>
    <p>The ability to distinguish priorities from distractions. I needed a system to decompose ideas, dispatch them to agents, and track what came back.</p>
  </div>
</div>

Agent PM started as a way to manage my own focus. It became an orchestrator because the same principles that made it useful for tracking also made it useful for dispatching.

---

# What It Is

Everything is YAML in a `.pm/` directory, version-controlled alongside code. Ships as a global CLI (`pm`), an MCP server (14+ tools), and a set of Claude Code slash commands.

<div class="split">
  <div>

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

  </div>
  <div>

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

  </div>
</div>

---

# The Flow

<div class="card-row">
  <div class="card" style="text-align: center;">
    <h3>1. Spec</h3>
    <p>I write it. Current state, target state, constraints, pitfalls, exclusions. The spec is the final output of research, not the beginning of it.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>2. Refine</h3>
    <p><code>/pm-refine-epic</code> reads the spec, surveys the codebase. Produces epics and stories with dependencies forming a DAG. Human approves before execution.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>3. Execute</h3>
    <p><code>/pm-work-on-project</code> builds a dependency graph, classifies into tiers, dispatches agents in parallel per tier. Failure context propagates forward.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>4. Monitor</h3>
    <p><code>/supervisor</code> triages: Blocked > Stale > Completed > Running. Batch decisions across agents. Under 3 minutes per round.</p>
  </div>
</div>

<p style="margin-top: 20px;">The spec is where all the real thinking happens. Everything downstream depends on how well you did here.</p>

---

# Tiered Dispatch

`/pm-work-on-project` builds the dependency graph and classifies stories:

- **Tier 1:** No unmet dependencies. Dispatched in parallel.
- **Tier 2:** Dependencies all in Tier 1. Dispatched after Tier 1 completes.
- **Tier N:** Dependencies all in tiers < N.

Each sub-agent runs in isolation. On completion, it files an **execution report** with decisions, assumptions, tradeoffs, and potential conflicts with parallel agents.

![w:1100 center](./assets/phased-dispatch.png)

---

# Agent PM vs. Symphony vs. Agent Teams

| Dimension            | Agent PM                          | OpenAI Symphony                   | Anthropic Agent Teams             |
| -------------------- | --------------------------------- | --------------------------------- | --------------------------------- |
| Planning layer       | Built-in (`/pm-refine-epic`)      | None                              | None                              |
| Work queue           | Local YAML in `.pm/`              | Linear (external)                 | Native to harness                 |
| Dispatch model       | Tier-based: complete N, then N+1  | Poll every 30s, fill open slots   | Session-managed                   |
| Agent identity       | Heterogeneous roles               | Homogeneous (same prompt)         | Homogeneous                       |
| State persistence    | Filesystem (survives crashes)     | In-memory + Linear                | Session-bound                     |

Symphony is elegant. Elixir OTP supervision, hot-reloadable WORKFLOW.md, Linear as the control plane. But it is a dispatcher, not a planner. Agent Teams is deeply integrated but less customizable. Agent PM includes the planning step.

---

# What I Learned

Both times, the custom solution worked. Both times, it proved the concept. Both times, it was obsolete within weeks.

<div class="split">
  <div>
    <h3>Agent PM vs. Agent Teams</h3>
    <p>Agent PM existed for two months before Anthropic released Agent Teams (March 2026). Native multi-agent orchestration with deeper integration.</p>
  </div>
  <div>
    <h3>Custom IPC vs. Shared Memory</h3>
    <p>I built escalation and shared context via Agent PM's task infrastructure. Anthropic shipped session-shared memories with hooks. The native solution replaced mine.</p>
  </div>
</div>

> The lesson is not "don't build." It is that anything you build on a platform this fast-moving is a proof of concept, whether you intended it to be or not.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# The Knowledge Base

## Because agents kept forgetting what other agents learned

---

# The Problem

Once Agent PM grew into a full orchestrator, knowledge created in one session had no way to survive into the next.

<div class="card-row">
  <div class="card">
    <h3>First attempt: worker packets</h3>
    <p>Comments on stories, managed by the orchestrator after each run. Worked for simple handoffs.</p>
  </div>
  <div class="card">
    <h3>Where it broke</h3>
    <p>Research agents needed a source of truth. Two agents investigating the same question would reach different conclusions because neither could see the other's work.</p>
  </div>
  <div class="card">
    <h3>What it became</h3>
    <p>A shared knowledge base. Simple grep over markdown stopped scaling past 50 notes, once the relationships between them started to matter.</p>
  </div>
</div>

---

# What a Note Looks Like

Every note is a markdown file with structured frontmatter. Agents write through the MCP server (which validates schemas, resolves tags, and updates backlinks); humans read in Obsidian.

<div class="split">
  <div>

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

  </div>
  <div>
    <h3>6 note types</h3>
    <p><strong>plans</strong>, <strong>research</strong>, <strong>concepts</strong>, <strong>insights</strong>, <strong>decisions</strong>, <strong>references</strong></p>
    <h3 style="margin-top: 16px;">Relationships are explicit</h3>
    <p><code>depends_on</code>, <code>parent</code>, <code>implements</code>, <code>supersedes</code> in frontmatter. <code>[[wikilinks]]</code> in the body. Shared tags as weak connections.</p>
    <h3 style="margin-top: 16px;">80+ notes across 7 projects</h3>
    <p>The MCP server runs as a shared HTTP process, so all Claude Code sessions share one index.</p>
  </div>
</div>

---

# How Search Works

Embedding-based retrieval (RAG) flattens relationships: two notes about the same topic get similar embeddings regardless of whether one supersedes the other. The KB instead combines three signals via Reciprocal Rank Fusion.

<div class="card-row">
  <div class="card">
    <h3>BM25 (FTS5)</h3>
    <p>Full-text search with porter stemming. Finds notes by what they say.</p>
  </div>
  <div class="card">
    <h3>Personalized PageRank</h3>
    <p>Walks the note graph seeded from text hits. Finds notes by what they connect to.</p>
  </div>
  <div class="card">
    <h3>Trust adjustments</h3>
    <p>Verified notes rank higher. Notes whose dependencies have been updated rank lower until reviewed.</p>
  </div>
</div>

No embeddings means no model dependency, no drift, and every result explains why it was ranked where it is.

---

# The Consolidation Pipeline

An overnight agent system (`/consolidate`) that turns the day's scattered work into durable knowledge entries.

<div class="card-row">
  <div class="card" style="text-align: center;">
    <h3>Phase 0: Structure</h3>
    <p>3 parallel agents fix link integrity, triage inbox, repair broken references</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Phase 1: Harvest</h3>
    <p>4 parallel agents extract from session logs, PRs, calendar, Slack</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Phase 2: Synthesize</h3>
    <p>Opus analyzes read-only, Sonnet agents execute edits, Opus reviews the diff</p>
  </div>
</div>

The pipeline feeds from `kb_stale`: a tool that flags notes for dependency drift, broken links, age, or community orphaning. Notes that need attention surface automatically.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Distribution

## Building the KB installer changed how I think about sharing software

---

<!-- _class: emphasis -->

# A Caveat

> Everything I've shown you today is built for how I think. These are my tools, shaped by my problems, my habits, and my tolerance for overengineering.

The point is not to copy them. It is to show what becomes possible when you build for your own workflow instead of adopting someone else's solution to someone else's problem.

---

# The Problem with Copying

There are 44,000+ skills on distribution platforms and 36,900+ stars on awesome-cursorrules. People share configuration files, copy them, and run them unchanged.

We are so different from one another in how we structure our work that this will only produce suboptimal workflows. Everything can be made custom, and AI makes this trivially easy. So instead of looking for the right template, take the idea and rebuild it until it fits the way you think.

But that raises a question: if copying is wrong, how *should* we distribute AI-native software?

---

# Dry Run: Phase A - Core Setup

<p class="dim">The installer asks one question at a time. No batching.</p>

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

---

# Dry Run: Phase B - Components

<p class="dim">Each component is presented with what it does and what you lose without it.</p>

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

---

# Dry Run: Phase C - Research

<p class="dim">This is where a traditional installer cannot follow. One parallel agent per source, all running simultaneously.</p>

```
Researching integrations for your 3 sources...

  [Agent 1] Searching: "GitHub MCP server" + "GitHub Claude Code integration"
  [Agent 2] Searching: "Slack MCP server" + "Slack Claude Code integration"
  [Agent 3] Searching: "Google Calendar MCP server" + "Google Calendar integration"

  All 3 research agents completed.
```

Each agent searches for MCP servers, CLI tools, and REST APIs. For each option found, it checks: is it from a trusted source? What permissions does it require? Is it actively maintained? Are there known security concerns?

---

# Dry Run: Phase D - Findings

<p class="dim">The installer presents what it found, checks what is already installed, and runs smoke tests.</p>

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

---

# Dry Run: Phase E - Source Configuration

<p class="dim">Targeted questions per source, adapted to the tools the research phase found.</p>

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

---

# Dry Run: Phase F - Customization

<p class="dim">This is where the installer stops being a form. The user can request features, and the installer checks feasibility against the actual codebase.</p>

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

---

# Dry Run: Phase G-J - Finalize and Generate

<div class="split">
  <div>

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

  </div>
  <div>

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

  </div>
</div>

---

# The Installer Reads Your History

Before the conversation begins, the installer scans Claude Code session telemetry: session count, tool diversity, sub-agent usage, configured MCP servers, project directories, custom skills and hooks. It uses this to calibrate the conversation without ever disclosing the profiling.

<div class="card-row">
  <div class="card">
    <h3>Depth of explanation</h3>
    <p>An amateur gets full component descriptions with tradeoffs. An experienced user gets a table and a "which of these?" prompt. The information is the same; the delivery adapts.</p>
  </div>
  <div class="card">
    <h3>Proactive suggestions</h3>
    <p>The installer does not wait for the user to describe their workflow. It already sees 14 projects under ~/dev/, MCPs configured, Python hooks active. It suggests a project registry, MCP-backed harvesting, and tag vocabulary seeded from existing projects.</p>
  </div>
  <div class="card">
    <h3>Customization surface</h3>
    <p>Power users are offered deeper options (custom intents, note type extensions, consolidation tuning) that would overwhelm a beginner. The options are not hidden; they are surfaced at the right level for the user.</p>
  </div>
</div>

---

# Two Users, Same Installer

<div class="split">
  <div>
    <h3>Someone with 10 sessions</h3>

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

<p class="dim" style="margin-top: 12px;">Full explanation. Concrete usage example. Clear recommendation.</p>

  </div>
  <div>
    <h3>Someone with 500 sessions</h3>

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

<p class="dim" style="margin-top: 12px;">Same information, different depth. Proactive suggestions drawn from what it found in the user's environment.</p>

  </div>
</div>

---

# Three Agents, One Conversation

The user sees a single conversation. Behind it, three agents with different roles.

<div class="card-row">
  <div class="card">
    <h3>Installer</h3>
    <p>User-facing, long-lived. Owns the conversation, generates standard artifacts, spawns sub-agents when needed. The user never sees the orchestration.</p>
  </div>
  <div class="card">
    <h3>Evaluator</h3>
    <p>Background, short-lived, spawned per request. Reads the server codebase and assesses feasibility of user requests. Strictly read-only.</p>
  </div>
  <div class="card">
    <h3>Builder</h3>
    <p>Background, potentially long-lived. Receives a specification co-designed by Installer and user. Plans implementation, writes code, tests, validates.</p>
  </div>
</div>

The developer builds a legible codebase. The AI reads it, understands it, and reshapes it to fit each user. The "product" is the installation prompt and a codebase clear enough for an AI to navigate.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# The Translation Pipeline

## Same patterns, different domain

---

# The Problem

My blog (dan.rio) is bilingual. The first version of the translation system worked the obvious way: hand the model a post and ask for a Portuguese version.

The output was always correct. It was also always flat: the kind of text that communicates without engaging. The meaning crossed over; the voice, the rhythm, the rhetorical texture did not.

---

# The Insight

The fix did not come from a better model or a longer prompt. It came from reading what translation institutes actually recommend.

They do not say "translate better." They say: analyze the source as authored writing before you touch it, settle terminology disputes before drafting, keep the critic independent from the translator, and verify that revisions actually addressed what the critique found.

Each of those recommendations became a stage in a 7,500-line pipeline, built with Claude Code.

```
source_analysis → terminology_policy → translate → [critique → revise] × N → final_review
```

Stages 1-2 run once and produce binding policy documents that constrain everything downstream. Translation and revision use GPT-5.4 high for generative work. Critique and final review use GPT-5.2 medium: a deliberately different model, to prevent the translator from grading its own homework.

---

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

---

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

---

# The Quality Gate

The pipeline does not ask the model whether the translation is good enough. It uses a deterministic rubric with weighted dimensions and hard thresholds.

<div class="split">
  <div>

| Dimension             | Weight |
| --------------------- | ------ |
| Accuracy              | 30%    |
| Terminology           | 20%    |
| Markdown fidelity     | 20%    |
| Linguistic conventions | 10%   |
| Style and register    | 10%    |
| Locale conventions    | 5%     |
| Audience clarity      | 5%     |

  </div>
  <div>
    <h3>Decision thresholds</h3>
    <p><strong>Accept:</strong> score >= 92, zero major errors</p>
    <p><strong>Refine:</strong> score 88-92, loop back to critique</p>
    <p><strong>Escalate:</strong> score 75-88, or stalled for 2 loops</p>
    <p><strong>Fail:</strong> score < 60, or any critical error</p>
    <h3 style="margin-top: 12px;">Hard gates</h3>
    <p>Accuracy >= 85, terminology >= 80, markdown fidelity >= 95. If any of these fail, the pipeline refines regardless of the overall score.</p>
  </div>
</div>

---

# Where This Goes Next

The pipeline works. The translations read like Portuguese, not like English wearing a Portuguese costume. But there is room to improve.

<div class="card-row">
  <div class="card">
    <h3>GEPA for prompt optimization</h3>
    <p>Early exploration into using GEPA to optimize the stage prompts systematically rather than by hand-tuning. Nothing conclusive yet, but the pipeline's typed contracts make it a good candidate: each stage has measurable inputs and outputs.</p>
  </div>
  <div class="card">
    <h3>Document-level coherence</h3>
    <p>The pipeline currently translates per-post. Cross-paragraph coherence within a post is handled by the terminology policy, but there is no mechanism for coherence across posts in a series.</p>
  </div>
  <div class="card">
    <h3>MQM error classification</h3>
    <p>The critique categories are hand-defined. Moving to MQM (Multidimensional Quality Metrics) would align with how professional translation quality is actually measured.</p>
  </div>
</div>

---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

# Thanks

## Questions welcome

dan.rio | github.com/danielcavalli
