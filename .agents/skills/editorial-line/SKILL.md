---
name: editorial-line
description: Shape or review the argument, scope, and information hierarchy of blog posts, connected series, and technical documentation. Use when deciding what belongs in a piece, how its sections develop the argument, or whether it needs separate linked treatments.
---

# Editorial Line

Use this skill to establish the editorial shape of a post or document, or to
review whether its material belongs together.

Before taking documentation action, read
[the editorial contract](references/editorial-contract.md) completely. Treat it
as the governing writing and composition standard.

For blog work, also read [blog composition](references/blog-composition.md).
It governs post boundaries, series, headings, and the application of this
contract to a publication rather than a documentation hierarchy.

## Diagnose the problem before choosing the intervention

Distinguish problems in the argument, its organization, and its expression.
A passage can contain the right facts in the right order and still read as
an elementary account of successive actions. When the problem is cadence,
emphasis, or sentence relationships, use the [prose skill](../prose-style/SKILL.md)
without inventing a new thesis or reorganizing sound material.

For a blog, first check whether the opening gives the reader something worth
understanding. A topic, project name, or declaration of ambition does not
establish that reason. If it is missing, recover the observation and its
significance from the author's material before polishing sentences. Apply
[the opening review](references/blog-composition.md#earn-the-opening).

Use the author's established voice reference alongside these contracts. For
Daniel's blog, the [writing-style skill](../writing-style/SKILL.md) routes to
that reference. Structure and voice are complementary requirements.

## Locate the established documentation structure

Identify the canonical documentation root and reader navigation guide from the
project's instructions and existing documentation. Do not assume a particular
filename, directory, product, or organization. If the root is not established,
surface that uncertainty before making a structural decision that depends on it.

A top-level overview is one specific human-facing document. The documentation
system is that overview plus the documents reachable beneath it. Do not infer
canonical authority from filename, backlinks, length, or prominence. A document
can contribute to the overview without becoming the overview.

If a reader navigation guide exists, inspect it before completing a
documentation task. Update its reading map when the task adds, removes,
renames, or moves a canonical document; changes a document's primary job; or
changes which document owns a reader's question. Leave the map unchanged for
edits that do not affect navigation.

Author canonical documentation in the project's established location. Treat
source material, investigations, and drafts according to their declared roles.
Do not promote them into canonical authority merely because they exist. Select
relevant information and write a new argument for the target document; do not
copy the source's organization or link to drafts as canonical child documents.

## Establish the document's role

State the document's purpose and intended audience before selecting its content.
Use this test for every candidate idea:

> Does the intended reader need this idea to achieve the stated purpose of this
> document?

If not, omit it or link to the document that owns it. A derivative document is
a new argument assembled for its own purpose, not a compressed copy of its
source.

Identify the document's intended place in the documentation pyramid before
editing it:

- top-level overview;
- standalone blog argument or a contribution to a connected series;
- product concept or boundary;
- capability or architecture;
- component-selection request for comments (RFC) or architectural decision;
- contract or specification;
- implementation or operations;
- evidence or investigation;
- experiment;
- presentation.

Do not infer current product facts from this skill. Read the relevant canonical
documents and use explicit user corrections as authoritative. If two active
documents disagree, expose the conflict instead of blending their claims.

Give the piece one primary job, such as developing an argument from experience,
defining a concept, establishing a boundary, making a decision, describing an
architecture, specifying a contract, or describing an operation. For a blog,
assess whether it contains one argument or several independently worthwhile
ones before polishing it. A section may need a separate linked treatment when
it acquires its own purpose, lifecycle, audience, or substantial supporting
argument. Use the contract's document boundaries and the blog's series criteria
to distinguish that need from a useful subsection or example.

## Apply the contract according to the task

- **Drafting:** establish the purpose, governing claim, abstraction level, and
  audience-selected supporting claims before writing detailed prose.
- **Reviewing:** inspect scope, hierarchy, abstraction, duplication, misplaced
  detail, audience relevance, document boundaries, and missing links before
  editing sentences.
- **Compressing:** follow the compression protocol and account for what happened
  to substantive information.
- **Expanding:** add only information appropriate to the current level. Do not
  interpret expansion as exhaustiveness; propose deeper documents for
  lower-level detail.

## Authoring and restructuring protocol

Perform semantic work before sentence editing:

1. State the target document's purpose and intended audience.
2. Select only the ideas that audience needs to achieve that purpose.
3. Identify the governing claims among the selected ideas.
4. Deduplicate claims by meaning, including statements that express different
   consequences of the same governing idea.
5. Group supporting details beneath their governing claim and abstract related
   details where appropriate.
6. Separate ideas that belong at different levels of abstraction.
7. Move lower-level material to an existing owner or propose a precise
   destination.
8. Preserve distinctions that affect product meaning, architecture, ownership,
   behavior, contracts, or decisions.
9. Remove superseded material from the active documentation set.
10. Rewrite the remaining material with the governing statement first.
11. After the hierarchy is correct, reconstruct each paragraph from its
    assertions and the relationships among them using the
    [prose skill](../prose-style/SKILL.md). A list of facts is preparation for
    prose, not its final sentence pattern.

When decomposing or compressing an existing document, account for substantive
material as one of:

- retained through abstraction;
- deduplicated;
- moved to a named destination;
- excluded because the target audience does not need it for the document's
  purpose;
- removed as irrelevant or superseded.

Do not use "shortened" as a reason for losing information.

## Writing requirements

- Begin every canonical technical document with a metadata table immediately
  after its title. Include `Author(s)` and a `Date` in `YYYY-MM-DD` format. Preserve
  additional role-specific metadata such as status, purpose, and audience.
  Name the accountable human authors; do not list an AI tool or agent as an
  author unless the user explicitly requires it.
  Blog posts retain the publication's frontmatter and rendered author/date
  conventions; do not add a duplicate metadata table.
- Include `Reviewer(s)` in every RFC metadata table. Name the humans expected
  to review the proposal. The field assigns review responsibility; it does not
  record approval.
- Limit RFC status metadata to `Draft`, `Open`, `Revision Pending`, `Revised,
  Open`, or `Completed` followed by the linked architectural decision record
  (ADR) title. A completed RFC must link to the ADR that records its decision.
  Put qualifications and decision progress in the RFC body rather than
  appending them to the status.
- Give each section a governing level of abstraction. Use examples to support
  that point and make deeper treatment a deliberate subsection or linked work.
- Describe the durable product or architectural capability before naming its
  implementation. A component can implement a capability without defining it.
  Make a component part of the product definition only when the architecture
  intentionally requires that specific component.
- Make the relationship between claim, necessary explanation, and consequence
  clear. These are logical functions, not a mandatory three-sentence pattern.
- Ensure sibling sections form a coherent, non-overlapping group at comparable
  levels of abstraction.
- Explain a child section because it answers a natural question raised by its
  parent.
- Use links as paths to the next level of detail, not as generic citations.
- Prefer conceptual grouping over long flat enumerations.
- Use diagrams only when relationships are materially clearer than prose. Use
  Mermaid for documentation diagrams unless another format is required.
- In canonical technical documentation, define novel concepts, expressions,
  and naming choices in the document footer.
  Keep the term itself as plain text and append a numbered superscript reference
  that links to its footer definition. Number references by first-use order
  within each document. Begin the footer definition with the same number and
  link it back to the first use.
  Do not hide specification-level behavior in footnotes.
  For blog terminology and notes, follow the audience and depth rules in
  [blog composition](references/blog-composition.md).
- Keep evidence available at the appropriate lower level without forcing it
  into the main argument.
- Do not preserve obsolete claims, rejected requirements, or superseded
  decisions in active documents unless the user explicitly requests a
  historical record.

## Review standard

Review the document in four passes:

1. **Purpose and audience:** Does the intended reader need each governing idea
   to achieve the document's stated purpose? For a blog, does the opening make
   the subject and the reason to examine it understandable before asking for
   interest in the author's project?
2. **Documentation system:** Does the document own this information, and are its
   links valid downward edges in the pyramid? Does the existing reading map
   still route readers to the current document owners?
3. **Document argument:** Does this piece sustain one argument, or contain a
   series of independently worthwhile arguments? Can a reader reconstruct the
   essential model by
   scanning the title, abstract, headings, first paragraph of each section, and
   diagrams? Does each section add a new claim or consequence rather than orbit
   an earlier thesis?
4. **Prose:** Do the paragraphs develop connected thought with a clear main
   point? Does each sentence earn its place through substance, necessary
   orientation, or a deliberate effect? Does syntax express relationships
   and emphasis, or merely give successive facts equal weight?

Report actual structural problems before copy-editing problems. Once the
structure is sound, work on the prose rather than redesigning the outline in
response to criticism of how the piece sounds.
