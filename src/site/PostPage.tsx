// A post's body, laid out as the design system's reference of dan.rio lays it out
// (art/reference/proving/apps/blog.tsx): one reading column from its head on its ground wash, the
// contents beside the text and the notes in the margin beside their lines. On a narrow screen the
// contents fold into one line before the text, as the blog's outline always has, so the text is
// what a reader sees first.

import { Contents, MarginNote, Reading, ReadingBody, ReadingHead } from "@mare-rio/design-system/react";

import { Tree } from "../reef/Tree";
import type { PostModel } from "./models";
import { WORDS } from "./words";

export function PostBody({ post }: { post: PostModel }) {
  const { lang } = post;
  const words = WORDS[lang].post;
  const items = post.headings.map((heading) => ({ label: heading.label, href: `#${heading.id}`, level: heading.level }));
  return (
    <Reading>
      <ReadingHead
        back={{ label: words.back, href: `/${lang}/blog/` }}
        carry={`post-${post.slug}`}
        facts={post.facts}
        title={post.title}
        dek={post.dek}
        tags={post.tags.map((tag) => ({ label: tag, href: `/${lang}/blog/` }))}
      />
      <ReadingBody
        contents={items.length ? <Contents label={words.contents} items={items} /> : undefined}
        notes={post.notes.length ? <>{post.notes.map((note) => <MarginNote key={note.n} n={note.n}><Tree nodes={note.body} /></MarginNote>)}</> : undefined}
      >
        {items.length ? (
          <details className="dan-contents-fold">
            <summary className="mare-contents-label">{words.contents}</summary>
            <Contents label={words.contents} items={items} />
          </details>
        ) : null}
        <Tree nodes={post.body} />
      </ReadingBody>
    </Reading>
  );
}
