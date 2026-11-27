// The index: the newest post as the page's head on its ground wash, then every other post by year.
// The reader orders it by when a post was published or last changed, narrows it to a year or a tag,
// or searches every post's text; each change is a turn of the one canvas, not a new page.

import { useEffect, useState } from "react";

import { Button, Choice, Empty, Entries, Entry, Field, Mark, Page, PageHead, Reading, ReadingHead, Tag, Tags, turn } from "@mare-rio/design-system/react";

import { Bar, SiteFoot } from "./chrome";
import type { IndexModel } from "./models";
import { search, type Searchable } from "./search";
import { WORDS } from "./words";

const lower = (text: string) => text.toLowerCase();

export function IndexPage({ index }: { index: IndexModel }) {
  const { lang, posts } = index;
  const words = WORDS[lang];
  const orders = [words.index.published, words.index.updated];
  const [order, setOrder] = useState<string>(orders[0]);
  const [filters, setFilters] = useState(false);
  const [pick, setPick] = useState("");
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState("");
  const [texts, setTexts] = useState<Searchable[]>();

  // The posts' words are fetched the first time the reader searches.
  useEffect(() => {
    if (!searching || texts) return;
    let gone = false;
    fetch(`/${lang}/search.json`)
      .then((answer) => answer.json())
      .then((all: Searchable[]) => { if (!gone) setTexts(all); })
      .catch(() => { if (!gone) setTexts([]); });
    return () => { gone = true; };
  }, [searching, texts, lang]);
  const asked = searching && query.trim().length > 1;
  const found = asked && texts ? search(texts, query) : [];

  const by = order === orders[0] ? "created" : "updated";
  let shown = [...posts].sort((a, b) => b[by].localeCompare(a[by]) || a.slug.localeCompare(b.slug));
  if (pick) shown = shown.filter((post) => post.year === pick || post.tags.some((tag) => lower(tag) === pick));
  const feature = pick ? undefined : shown[0];
  const rest = feature ? shown.slice(1) : shown;
  const years = [...new Set(rest.map((post) => post.year))];

  // What it can be narrowed to: the years, then the tags more than one post has, the most used first.
  const uses = new Map<string, number>();
  for (const post of posts) for (const tag of post.tags) uses.set(lower(tag), (uses.get(lower(tag)) ?? 0) + 1);
  const chips = [...new Set(posts.map((post) => post.year))].concat(
    [...uses].filter(([, count]) => count > 1).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([tag]) => tag),
  );

  return (
    <Page variant="reading">
      <Bar lang={lang} at="blog" alternates={index.alternates} />
      <Reading measure="index">
        <PageHead title={words.index.title} note={`${words.posts(posts.length)} · en / pt`}>
          <Choice label={words.index.sortBy} named="beside" of="view" options={orders} value={order} onChange={(next) => turn(() => setOrder(next))} />
          <Button size="small" onPress={() => turn(() => setFilters(!filters))}>{words.index.filter}</Button>
          <Mark glyph="search" label={words.index.search} expanded={searching} onPress={() => turn(() => { setSearching(!searching); setQuery(""); })} />
        </PageHead>
        {searching ? <Field label={words.index.search} bare autoFocus example={words.index.searchFor} value={query} onChange={setQuery} /> : null}
        {asked ? (
          found.length ? (
            <Entries name={words.index.found} note={words.posts(found.length)}>
              {found.map((post) => (
                <Entry key={post.slug} href={post.href} carry={`post-${post.slug}`} lead={post.date} title={post.title} tags={post.tags.map(lower)}>
                  {post.passage}
                </Entry>
              ))}
            </Entries>
          ) : texts ? (
            <Empty title={words.index.nothing}>{words.index.nothingHelp}</Empty>
          ) : null
        ) : null}
        {!asked && filters ? (
          <Tags label={lower(words.index.filter)}>
            {chips.map((chip) => (
              <Tag key={chip} chosen={pick === chip} onPress={() => turn(() => setPick(pick === chip ? "" : chip))}>{chip}</Tag>
            ))}
          </Tags>
        ) : null}
        {!asked && feature ? (
          <ReadingHead
            href={feature.href}
            carry={`post-${feature.slug}`}
            facts={[words.index.latest, feature.date]}
            title={feature.title}
            dek={feature.excerpt}
            tags={feature.tags.map((tag) => ({ label: tag, href: `/${lang}/blog/` }))}
          />
        ) : null}
        {!asked && years.map((year) => {
          const of = rest.filter((post) => post.year === year);
          return (
            <Entries key={year} name={year} note={words.posts(of.length)}>
              {of.map((post) => (
                <Entry key={post.slug} href={post.href} carry={`post-${post.slug}`} lead={post.date} title={post.title} tags={post.tags.map(lower)}>
                  {post.excerpt}
                </Entry>
              ))}
            </Entries>
          );
        })}
      </Reading>
      <SiteFoot lang={lang} />
    </Page>
  );
}
