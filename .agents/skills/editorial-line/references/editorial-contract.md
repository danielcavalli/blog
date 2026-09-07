# Editorial Contract

## Purpose

Writing must reduce the amount of information a reader needs to process
at one time without weakening the meaning. Concision is a consequence of
correct abstraction, not an objective that overrides information.

This contract governs writing and composition. It does not define current
product facts, select components, or settle architectural decisions. Those
truths belong to the canonical documentation and its requests for comments
(RFCs).

The argument may belong to a blog post, a connected series, or a technical
document. Identify the form and the reader's purpose before applying its
conventions. [Blog composition](blog-composition.md) supplies the post and
series guidance; technical-document metadata and lifecycle rules below apply
to those document types, not automatically to every piece of writing.

Editorial organization and prose quality require separate judgment. A clear
outline can still contain lifeless, mechanically sequential prose. Diagnose
which problem is present: changing the subject or adding headings does not
repair the way sentences express an otherwise sound thought.

## Select before compressing

Use four editorial operations in this order:

1. **Select** information required by the document's purpose and audience.
2. **Deduplicate** information that expresses the same governing idea.
3. **Abstract** related details into a precise higher-level statement.
4. **Relocate** details to the lower documentation layer where they belong.

Delete information when it does not contribute to the active documentation
system. Superseded assumptions, rejected requirements, and obsolete decisions
are irrelevant. Version control provides history; active documentation must
describe the current model and current decisions.

## Select for the reader, not for the source

When deriving one document from another, do not preserve information merely
because it remains valid at the target abstraction level. Start from the target
document's purpose and intended audience.

For every candidate idea, ask:

> Does the intended reader need this idea to achieve the stated purpose of this
> document?

If not, omit it or link to the document that owns it. A fact can be at the
correct abstraction level and still be unnecessary for the reader.

A derivative document is not a compressed copy of its source. It is a new
argument assembled from the subset of information required for its own purpose.
Source completeness creates no obligation to reproduce authoring policy,
maintenance rules, document taxonomy, or historical context for readers who do
not need them.

## Identify every canonical document

Begin every canonical technical document with a metadata table immediately
after its title. The table must name its accountable human `Author(s)` and give its
`Date` in `YYYY-MM-DD` format. Do not attribute authorship to an AI tool or
agent unless the user explicitly requires it.

Preserve role-specific metadata such as status, purpose, and audience when it
helps readers interpret the document. Preserve existing authorship and date
values unless the task explicitly changes them.

A blog retains its established frontmatter and displayed author/date
conventions. Do not turn a personal article into an RFC by adding metadata
tables, approval fields, or a lifecycle it does not have.

Every RFC metadata table must include `Reviewer(s)` and name the humans
expected to review the proposal. The field assigns review responsibility; it
does not record approval.

### Use a controlled RFC lifecycle

An RFC status must use one of these values:

- `Draft`;
- `Open`;
- `Revision Pending`;
- `Revised, Open`;
- `Completed`, followed by the linked architectural decision record (ADR) title.

`Draft` identifies a proposal still being authored. `Open` identifies an RFC
available for discussion and decision. `Revision Pending` identifies an RFC
that must incorporate review feedback before discussion continues. `Revised,
Open` identifies a revised RFC available for further discussion. `Completed`
identifies a decided RFC recorded in an ADR and must link to that ADR.

Status describes lifecycle stage, not the RFC's unresolved questions or
decision outcome. Record qualifications, progress, and the decision itself in
the RFC body. Do not append custom prose to a status value.

## Organize the documentation system as a Minto Pyramid

Apply the Minto Pyramid at two scales: across the documentation system and
within each document.

Across a blog, related posts can develop one subject through distinct arguments
as well as progressively deeper explanations. Use the series criteria in
[blog composition](blog-composition.md); a chronology of publication dates is
not by itself an intellectual structure.

### Across the documentation system

The established top-level overview explains the subject as a whole. It presents
the governing mental model, major concepts, boundaries, and capabilities, then
links to documents that own deeper treatment.

The documentation system descends from:

```text
Top-level overview
    -> concepts and boundaries
        -> capabilities and architecture
            -> decisions
                -> contracts and specifications
                    -> implementation and operations
```

The overview does not contain all documentation. It is the root document
through which the rest of the documentation is organized and discovered. The
documentation system consists of the overview and the documents reachable
beneath it. Use the project's established root; do not assume a particular
title or path.

A child document expands a concept introduced at the level above it. The parent
retains the governing abstraction and links to the child for additional
resolution.

### Maintain the reader navigation map

An existing reader navigation guide maps reader questions to the canonical
documents that own their answers. Identify it from the project's documentation
rather than assuming a particular filename, section title, or publishing tool.

If such a map exists, inspect it before completing any documentation change.
Update it in the same change when:

- a canonical document is added, removed, renamed, or moved;
- a document's primary job changes;
- ownership of a reader question moves between documents; or
- the recommended entry point into a documentation branch changes.

Do not add every file merely because it exists. The map selects reader-relevant
branches and document owners rather than reproducing the filesystem. Leave it
unchanged when an edit does not affect how a reader navigates the system.

### Within a document

Each document also follows a top-down argument:

- state the governing idea first;
- group its supporting ideas underneath it;
- keep sibling ideas at comparable levels of abstraction;
- let deeper sections answer questions raised by the sections above them.

A document may represent any level of the broader documentation pyramid. Its
internal structure still follows the same top-down logic.

## Give every document one primary job

A piece should have a primary purpose: it might develop an argument from
experience, define a concept, establish a boundary, make a decision, describe
an architecture, specify a contract, or describe an operation. Its supporting
sections contribute to that purpose at compatible levels of abstraction.

Consider a separate linked document when a section:

- can evolve independently;
- has a different accountable owner;
- introduces its own decision or alternatives;
- requires a substantial new vocabulary;
- becomes a specification inside a conceptual document; or
- can be read meaningfully on its own.

These signals matter when the material has acquired a purpose that deserves
its own treatment. A self-contained example alone does not require another
document. For blog work, apply the post, reference, and series distinctions in
[blog composition](blog-composition.md).

Do not continue elaborating a document merely because it is already open. A new
document boundary is appropriate when the information has acquired its own
purpose, lifecycle, or audience. The parent should retain the governing
abstraction and link to the child that owns the deeper treatment.

## Make every level independently understandable

A reader who stops at a particular level must leave with a correct, though less
detailed, understanding. Higher levels are therefore lossy in detail but
lossless in meaning.

For example, a high-level document may say:

> Authors approve changes to their work.

A deeper document may explain:

> Reviewers propose revisions. Authors accept or reject each proposal before
> publication.

A specification may then define review states, revision records, and approval
procedures. The higher-level statement is not an incomplete specification. It
is the correct representation of the same concept at a higher level of
abstraction.

## Summarize by abstraction, not omission

When compressing several statements, first identify the concept that makes them
belong together.

Prefer:

> Authors retain final approval throughout review.

over several independent paragraphs saying that reviewers do not approve
changes to the title, argument, examples, and conclusion. Detailed ownership
boundaries can remain in a linked document.

A good abstraction preserves the important distinction while removing the
mechanics.

## Deduplicate governing ideas, not only sentences

Semantic repetition often survives because related statements use different
words or describe different implications. Reduce each paragraph or section to
the claim it contributes. If several claims depend on the same governing idea
and do not add independent consequences needed by the reader, state that idea
once and organize the distinct consequences beneath it.

For example, statements that the overview presents a correct high-level
model, supports stopping at any level, increases resolution through deeper
documents, and does not flatten the knowledge base may all support one thesis:

> The overview presents a correct high-level model and lets readers reveal
> detail progressively.

The document should state that governing idea once. Later sections should add
new consequences rather than repeatedly re-expressing the thesis.

## Never abstract away a distinction that matters

Compression becomes destructive when different concepts are merged merely
because they sound related.

Do not collapse authorship, review, and approval into "oversight" when their
responsibilities differ at the level being documented.

Do not collapse a draft, a revision, and a published edition into "document"
when their separate identities matter to the argument.

Use the highest abstraction that preserves the distinctions required at the
current level.

## Give each section a governing level of abstraction

A section must not freely alternate between product concepts, architecture,
implementation components, repository names, interface fields, and operational
procedures.

Give the section a governing level and make its changes in depth deliberate.
A concrete example, diagram, or brief code excerpt can substantiate the
current point without becoming a separate document. A treatment that needs
its own argument, vocabulary, or implementation procedure belongs at a
deeper level. In a blog, decide whether that level is a subsection, a linked
reference, or another post using the reader's need, not the presence of code.

This distinction is particularly important for capabilities and components. A
feature or capability is part of the product contract. The component providing
it is malleable and may change. Documentation must discuss component options and
their trade-offs without making the selected component synonymous with the
capability.

## Describe capabilities before components

Describe the durable product or architectural capability before naming its
implementation. A component can implement a capability without defining it.

Only make a component part of the product definition when the architecture
intentionally requires that specific component. Otherwise, keep the product
statement stable and place component selection, alternatives, trade-offs, and
maintainability consequences in the appropriate architecture document or RFC.

Repository structure is implementation evidence, not proof of the conceptual
architecture. Do not derive the product model directly from the components that
happen to be most visible in code.

## Use vertical and horizontal logic

### Vertical logic

A child exists because it answers a natural question raised by its parent.

If a parent says:

> The process separates review from approval.

the next level may answer:

- Who reviews the work?
- Who approves the work?
- Why are those responsibilities separated?

Do not introduce a subsection merely because it is related to the subject.
It must support or decompose a statement above it.

### Horizontal logic

Sibling ideas form a coherent group and do not unnecessarily overlap. If the
major stages are drafting, review, and publication, each must represent a
distinct part of the process at approximately the same conceptual level.

Avoid lists where one item is a major stage, another is a specific tool,
and another is a quality criterion.

## Lead with the governing statement

The first sentence of a section should normally contain the most important
information in that section. Everything below it supports, decomposes,
qualifies, or links from that statement.

A reader scanning only the title, abstract, headings, first paragraph of each
section, and diagrams should still reconstruct the essential argument. Apply
this as a quality test, especially to the top-level overview.

Headings expose the progression of the argument and give readers places to
return to. Use subheadings where they clarify a real subdivision. Neither
conversational writing nor concision calls for an uninterrupted wall of text;
equally, a heading above every paragraph fragments the thought. The blog
guidance develops this distinction without imposing a fixed heading count.

The same structure applies inside paragraphs:

```text
claim -> necessary explanation -> consequence
```

These functions may share a sentence or develop across a paragraph. Do not
write one short sentence for each function, or append an explicit conclusion
that repeats what the explanation already makes clear.

For example:

> Authors retain approval of the final text. Reviewers therefore submit
> recommendations for authors to accept or reject. A change of reviewer does
> not transfer approval authority.

Do not require the reader to infer the conclusion from several implementation
facts.

## Replace enumeration with structure

Turning every fact into a bullet shortens prose but does not reduce cognitive
load. When a list becomes long, determine whether its items first belong under
a smaller number of concepts.

Instead of presenting purpose, audience, scope, claims, evidence, links,
terminology, and sentence clarity as eight unrelated items, group them where
appropriate:

- **Document role:** purpose, audience, and scope.
- **Argument:** claims, evidence, and links.
- **Prose:** terminology and sentence clarity.

Keep the expanded list only where the individual items matter.

## Treat links as part of the compression model

A link is an edge to the next level of the pyramid, not merely a citation.
State the governing claim at the current level, then link the concept that
receives deeper treatment instead of reproducing its detailed rules,
examples, and semantics.

Links should answer a predictable next question. Avoid generic phrases such as
"more information here." Link the concept being expanded.

## Preserve evidence without making it the narrative

Current rationale, implementation evidence, experiments, repository analysis,
and operational findings can matter without belonging in the main argument.
Place relevant material in RFCs, specifications, evidence records, experiment
documents, or linked source material according to its role.

Evidence should support a current claim or active decision. Do not retain an
obsolete claim merely because evidence once supported it, and do not turn the
active documentation set into an archive of earlier designs.

## Separate information density from information quantity

A short document can remain difficult if every sentence introduces unrelated
detail. Good compression reduces the number of concepts the reader must hold
simultaneously.

Optimize for:

> few concepts per level, high precision within each concept, and depth through
> deliberate links

rather than maximum facts per paragraph.

## Use diagrams as semantic compression

Use a diagram when relationships are materially easier to understand visually:
containment, ownership, information flow, lifecycle, dependency, or separation
of responsibilities.

Do not plan decorative visuals or repeat a simple list as a diagram. The diagram
must reduce cognitive work. Use Mermaid blocks for documentation diagrams unless
another format is required.

## Use semantic compression before sentence compression

When a passage is too long, do not begin by shortening sentences. Ask:

1. Are several sentences making the same claim?
2. Are several details instances of one higher-level concept?
3. Does some information belong one level deeper?
4. Can a diagram represent the relationships more efficiently?
5. Is historical explanation being mixed with the current model?

Only after the structure is correct should individual sentences be shortened.
Structural compression normally produces much larger gains than stylistic
compression.

At that point, identify each paragraph's assertions and their relationships,
then rewrite it as connected thought. A sentence can earn its place by adding
information, drawing an inference, orienting the reader, or creating an effect
that matters to the author's meaning. Do not preserve wording merely because
it is valid, or confuse a longer sentence with a more mature one. Keep
qualifications that change meaning, scope, stance, or behavior.

## Apply the contract according to the task

The editorial contract remains the same across documentation tasks, but its
application depends on the requested mode.

### Drafting

Establish the document's purpose, audience, governing claim, abstraction level,
and audience-selected supporting claims before writing detailed prose. Decide
what the document will not own so adjacent concerns have explicit destinations.

### Reviewing

Inspect purpose, audience relevance, scope, hierarchy, abstraction, semantic
duplication, misplaced detail, document boundaries, and missing links before
editing sentences. Report structural problems before copy-editing problems.

### Compressing

Follow the AI compression protocol and account for what happened to substantive
information. Compression must improve the information hierarchy rather than
merely reduce word count.

### Expanding

Do not interpret expansion as exhaustiveness. Add only information appropriate
to the document's job and current abstraction level. When useful detail belongs
lower in the pyramid, propose or create a linked document instead of absorbing
it into the current one.

## Make compression reversible where information remains relevant

A well-designed hierarchy allows a reader to move downward and recover the
detail hidden by abstraction. For every compressed statement, ask:

> Where would a reader go to understand this one level deeper?

If there is no answer, either the detail has genuinely been judged irrelevant
or the documentation hierarchy has lost information.

This requirement does not oblige the active documentation to preserve
superseded material. Once a claim is obsolete, remove it rather than giving it a
permanent address.

## AI compression protocol

When asked to shorten documentation, do not immediately summarize the prose.
Perform these steps in order:

1. State the target document's purpose and intended audience.
2. Select only the ideas that audience needs to achieve that purpose.
3. Identify the governing claims among the selected ideas.
4. Deduplicate claims by meaning, not only by wording.
5. Group supporting details beneath their governing claim.
6. Identify details at a lower level of abstraction.
7. Move those details to existing linked documents or propose a destination.
8. Preserve distinctions affecting architecture, ownership, behavior, or
   decisions.
9. Remove superseded and irrelevant material.
10. Rewrite the remaining text so governing claims appear first.
11. Reconstruct each paragraph from its assertions and their relationships using
    [the prose contract](../../prose-style/references/prose-contract.md).

Account for removed substantive information as retained through abstraction,
deduplicated, moved to another document, excluded as unnecessary for the stated
purpose and audience, or removed as irrelevant or superseded. "Shortened" is
not itself a valid explanation.

## Top-level overview test

For every proposed detail in the overview, ask:

> Does the reader need this information to construct the correct high-level
> mental model of the subject?

Then apply the document-specific test:

> Does this reader need this information to achieve the stated purpose of this
> document?

Keep the detail only when it passes both tests.

If the reader needs to know only that the concept exists, state it and link
downward. If the information explains implementation, move it down the pyramid.
If it concerns a decision that can change independently, move it to the owning
RFC or ADR. If it is reference material, move it to a specification.

The overview exposes the structure of the subject. It does not flatten the
entire knowledge base into one document.

## Use the footer deliberately

In canonical technical documentation, use the footer to explain novel
concepts, expressions, and naming choices. A footer definition should help
the reader understand why a term exists and which distinction it preserves.
For a blog, explain what is needed to follow the argument at first meaningful
use; reserve a note or linked reference for detail that would interrupt it.
Do not create a glossary merely to give the article a scholarly appearance.

Number references by their first appearance in the body, starting at one in
each post or document. This applies to source citations as well as term notes.
Repeated citations reuse the source's assigned number, and the source list or
footer follows the same order. After revising or moving prose, check the order
again and update citation labels and source entries together, preserving each
citation's source association.

When the footer defines a term, keep the term itself as plain text and append a
numbered superscript reference that links to the definition. Begin each footer
entry with the corresponding bracketed number. Keep semantic anchors in the
link targets so inserting another definition does not invalidate existing
external links.

For canonical technical documentation with footer definitions, the definition
must include a link back to the first use so the reader can
return to the argument without finding the previous location again. Use this
shape:

```markdown
<a id="first-use-term"></a>Term<sup>[1](#footnote-term)</sup>

---

<a id="footnote-term"></a>
**[1] Term:** The definition. [Back to first use.](#first-use-term)
```

Blog posts use the publication's native Markdown sidenotes instead. Follow
[blog composition](blog-composition.md#write-notes-for-the-reading-layout):
stable semantic note labels, numbering by first use, and no authored return
links or empty Sources section. The renderer owns their placement and numbering.

Do not place load-bearing behavior, ownership, or contract semantics only in a
footnote. Those belong in the main argument or a linked specification.
