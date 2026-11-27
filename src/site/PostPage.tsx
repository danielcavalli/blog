// A post's page, laid out as the design system's reference of dan.rio lays it out
// (art/reference/proving/apps/blog.tsx): the bar, one reading column from its head on its ground
// wash to its foot, the contents beside the text and the notes in the margin beside their lines.

import { Contents, MarginNote, Page, Reading, ReadingBody, ReadingHead } from "@mare-rio/design-system/react";

import { Tree } from "../reef/Tree";
import { Bar, SiteFoot } from "./chrome";
import type { PostModel } from "./models";
import { WORDS } from "./words";

export function PostPage({ post }: { post: PostModel }) {
  const { lang } = post;
  const words = WORDS[lang].post;
  return (
    <Page variant="reading" box="folha">
      <Bar lang={lang} at="blog" alternates={post.alternates} />
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
          contents={post.headings.length ? <Contents label={words.contents} items={post.headings.map((heading) => ({ label: heading.label, href: `#${heading.id}`, level: heading.level }))} /> : undefined}
          notes={post.notes.length ? <>{post.notes.map((note) => <MarginNote key={note.n} n={note.n}><Tree nodes={note.body} /></MarginNote>)}</> : undefined}
        >
          <Tree nodes={post.body} />
        </ReadingBody>
      </Reading>
      <SiteFoot lang={lang} />
    </Page>
  );
}
