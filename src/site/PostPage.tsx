// A post's page, laid out with the design system's parts as its own reference of dan.rio lays it out
// (art/reference/proving/apps/blog.tsx in the Maré Design System): the bar, one reading column from
// its head to its foot, the contents beside the text and the notes in the margin.

import {
  BarEnd,
  Contents,
  Foot,
  Languages,
  Link,
  MarginNote,
  Nav,
  NavItem,
  Page,
  Reading,
  ReadingBody,
  ReadingHead,
  ThemeToggle,
  TopBar,
  Wordmark,
} from "@mare-rio/design-system/react";

import { formatDate, postOfFile, postUrl, readingTime, type Lang, type Post } from "../content/documents";
import { renderDocument } from "../reef/render";

const WORDS = {
  en: { blog: "blog", about: "about", cv: "cv", back: "Back to Blog", contents: "On this page", foot: "© Daniel Cavalli" },
  pt: { blog: "blog", about: "sobre", cv: "cv", back: "Voltar ao Blog", contents: "Neste artigo", foot: "© Daniel Cavalli" },
};

export function Bar({ lang, at }: { lang: Lang; at: "blog" | "about" | "cv" }) {
  const words = WORDS[lang];
  return (
    <TopBar>
      <Wordmark href={`/${lang}/`}>dan.rio</Wordmark>
      <Nav>
        <NavItem href={`/${lang}/blog/`} current={at === "blog"}>{words.blog}</NavItem>
        <NavItem href={`/${lang}/about`} current={at === "about"}>{words.about}</NavItem>
        <NavItem href={`/${lang}/cv`} current={at === "cv"}>{words.cv}</NavItem>
      </Nav>
      <BarEnd>
        <Languages choices={["EN", "PT"]} current={lang.toUpperCase()} />
        <ThemeToggle />
      </BarEnd>
    </TopBar>
  );
}

export function SiteFoot({ lang }: { lang: Lang }) {
  return (
    <Foot
      left={WORDS[lang].foot}
      right={
        <>
          <Link href="https://x.com/dancavlli">x</Link> <Link href="https://github.com/danielcavalli">github</Link>{" "}
          <Link href="https://www.linkedin.com/in/cavallidaniel/">linkedin</Link>
        </>
      }
    />
  );
}

/** A link between posts is written as a link to the file beside it; on the site it is that post's page. */
function linkIn(lang: Lang) {
  return (href: string) => {
    const match = /^(?:\.\/)?([^/#?]+\.md)(#.*)?$/.exec(href);
    const post = match && postOfFile(match[1]);
    return post ? postUrl(post, post.in[lang] ? lang : post.written) + (match[2] ?? "") : href;
  };
}

export function PostPage({ post, lang }: { post: Post; lang: Lang }) {
  const document = post.in[lang]!;
  const words = WORDS[lang];
  // A translation's sections keep the ids of the text it translates.
  const source = post.in[post.written]!;
  const headingIds = document === source ? undefined : renderDocument(source.body).headings.map((heading) => heading.id);
  const { body, headings, notes } = renderDocument(document.body, { link: linkIn(lang), headingIds });
  return (
    <Page variant="reading" box="folha">
      <Bar lang={lang} at="blog" />
      <Reading>
        <ReadingHead
          back={{ label: words.back, href: `/${lang}/blog/` }}
          carry={`post-${post.slug}`}
          facts={[formatDate(post.date, lang), readingTime(document)]}
          title={document.title}
          dek={document.excerpt}
          tags={document.tags.map((tag) => ({ label: tag, href: `/${lang}/blog/` }))}
        />
        <ReadingBody
          contents={headings.length ? <Contents label={words.contents} items={headings.map((heading) => ({ label: heading.label, href: `#${heading.id}`, level: heading.level }))} /> : undefined}
          notes={notes.length ? <>{notes.map((note) => <MarginNote key={note.n} n={note.n}>{note.body}</MarginNote>)}</> : undefined}
        >
          {body}
        </ReadingBody>
      </Reading>
      <SiteFoot lang={lang} />
    </Page>
  );
}
