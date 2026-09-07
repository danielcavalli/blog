# Blog Composition

## Give the reader a thought worth following

A blog post develops something the author has understood, observed, or has
reason to argue. It may explain an engineering system in considerable detail,
but its purpose is determined by what that explanation lets the reader see.
A tour of components or a chronology of work is useful only when the sequence
itself explains something the reader needs to understand.

Establish the intended reader, the governing thought, and the experience or
evidence supporting it. Let those determine the treatment. A clear argument
can still sound elementary when every sentence reports another event; use
the prose contract to repair that expression without inventing a different
argument.

## Earn the opening

The opening must give the reader something to understand and a reason to
follow it. Begin with a substantive observation, question, consequence, or
difficulty grounded in the author's material. Give enough context for a
reader unfamiliar with the project to grasp its significance. Announcing
plans, ambitions, or a collection of features does not do this work.

Introduce an unfamiliar project through the purpose that makes it relevant.
An architectural answer needs an intelligible problem; a brand definition
cannot supply one. A familiar situation can make the problem visible without
inventing an anecdote. Do not force every opening into a complaint, paradox,
or problem-and-solution formula. The subject determines the approach.

Review the opening before accepting it:

- What can the reader understand now that they could not before?
- What consequence, question, or difficulty makes continuing worthwhile?
- Does the reader have the context to assess the proposed idea?

As a diagnostic, remove the project name. If the remaining prose could
introduce almost any project, find the missing observation or reasoning.
Restore substance; do not merely add names, implementation details, a hook,
or more emphatic promises. Apply the same standard to the excerpt.

## Decide what belongs in one post

Length alone does not decide whether a subject needs a series. A long post may
develop one argument through several necessary steps; a short draft may
already contain two unrelated conclusions.

Consider the reader's next question and what it takes to answer it:

- **Keep it in the post** when it supports the governing thought and can be
  understood with the context already established. Use a section or example
  when that makes the relationship clearer.
- **Link to a deeper reference** when the reader needs optional specifications,
  complete code, measurements, or procedures, without another argument from
  the author. A full JSON file need not become a blog post.
- **Propose a series** when the material contains distinct arguments with their
  own conclusions, evidence, or stakes, and developing each would repeatedly
  interrupt the others. Each proposed post must repay reading on its own.

Useful signals for a series include changes in the question being answered,
substantial new context or vocabulary, a different intended reader, and
several conclusions that could each sustain a piece. These are prompts for
judgment, not automatic split rules. Different components, several headings,
or exceeding a reading-time target do not by themselves establish a series.

Before splitting, try stating the draft's governing thought in one sentence.
Then state what each proposed post would contribute. If every proposed post
merely names a step needed to reach the same conclusion, keep the argument
together unless the reader has a real reason to take those steps separately.

## A series has an argument at both scales

A series can deepen one subject or examine it from several related angles.
The series has a governing question or claim; each post makes a distinct
contribution to it, with enough context to understand that contribution.

When proposing a series, provide a compact reading map:

- the shared question or governing claim;
- each post's working title, reader question, and intended conclusion;
- what context or evidence belongs in that post;
- the useful reading order and any actual prerequisites.

Keep this map proportional to the proposal. Inspect existing posts first:
an existing article may already answer one of the questions. The next piece
should advance that discussion, with a brief linked recap where needed,
rather than reconstruct the entire argument.

Present the concrete proposal before replacing an agreed single post with
several pieces, unless the user has already authorized that split. Continue
research and prose work that does not depend on the decision. Do not silently
create a publication schedule, unfinished sequels, or promises of future posts.

Each installment delivers its own conclusion. It can rely on stated
prerequisites, but should not withhold the answer it promised merely to send
the reader to the next installment. Published links must point to existing
material; planned titles belong in the proposal until the material exists.

## Use headings to expose the movement of thought

Choose headings that identify what a section contributes. Their sequence,
together with the opening paragraphs, should let a reader recover the main
argument. Use subheadings to develop a real question within a section, not
to label every new paragraph or implementation step.

There is no fixed number or grammatical formula. A descriptive heading can
orient the reader; a claim can carry the argument; a question can be useful
when it is the actual question the section answers. Avoid interchangeable
labels such as "Introduction" and "Conclusion" when a more specific heading
would help, and avoid dramatic promises that the section cannot repay.

Conversational prose still needs navigation. Headings do not replace the
connections between paragraphs, and a tidy outline does not prove that the
sentences read well.

The renderer derives the article outline from the headings already in the
post. Write the hierarchy the argument needs; do not add a manual table of
contents or extra headings to fill the margin. The post title belongs in the
frontmatter, with sections normally beginning at `##`.

## Match technical depth to the question

An engineer's blog can be technical. Keep the contracts, mechanisms, code, and
diagrams that explain the point; supply context at first meaningful use.
Do not remove precise engineering content to simulate accessibility, or add
a complete implementation reference merely because the source is available.

Use a diagram when ownership, state, or information flow becomes clearer in
it. It should earn the attention it takes, rather than repeat a simple list.
Place optional detail in notes or links so a reader can descend without
losing the main thread. Preserve the publication's own metadata conventions.

## Write notes for the reading layout

Use native Markdown footnotes with stable semantic labels:

```markdown
The distinction matters here[^ownership].

[^ownership]: Supporting context and a [source](https://example.com).
```

The renderer numbers notes by first use and places them beside the relevant
passage on wide screens. On smaller screens, the citation opens the note in
the article. Repeated citations share a note. Do not author return links,
manual superscripts, or a Sources heading for these notes. A bibliography
that serves an independent reading purpose can remain an ordinary section.

Keep reasoning needed to follow the argument in the body. Notes hold context,
evidence, or qualifications whose placement there would interrupt the thought;
they are not a place to hide a necessary premise. Existing handwritten note
anchors remain supported, so layout changes do not require rewriting old posts.

## Localize the authored work

Once the source is written, its argument, organization, and wording are the
authority. Translation reads composition, prose, and voice guidance to understand
those choices. It does not use them to edit the source or give the translation
a different argument. The locale references govern how sentence movement,
idiom, register, and punctuation carry the same effect into PT-BR or EN-US.

Editorial revision of a source and localization of that source are separate
operations. Keep authoring judgments with the author; preserve accepted
translations until a source change or an explicit translation revision calls
for new work.

## Check the boundary with concrete cases

- **One post:** Why a shared agent runtime helps coding agents build personal
  apps. Discovery, a JSON excerpt, and one execution diagram can all support
  the same claim; their different technical subjects do not require sequels.
- **Post plus reference:** The same article with the full declaration schema
  and field-by-field validation rules. Keep the argument in the article and
  link the complete contract for readers who need to implement it.
- **Potential series:** A draft separately argues how agents change the
  economics of personal software, how a runtime should divide responsibility,
  and how recommendation quality should be evaluated. If each has its own
  evidence and conclusion, propose connected posts rather than abbreviating
  all three arguments into one tour.
- **Prose revision:** A coherent article sounds like "I did this, then this
  happened." Improve sentence relationships and emphasis. Splitting that
  article would distribute the same prose problem across several posts.

These cases illustrate decisions. They do not prescribe a Maré series or a
template for future subjects.
