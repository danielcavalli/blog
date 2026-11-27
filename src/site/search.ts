// The index's search: every post in the reader's language, looked through in the browser. The posts'
// words (/<lang>/search.json) are fetched when the reader first asks.

export interface Searchable {
  slug: string;
  href: string;
  title: string;
  excerpt: string;
  tags: string[];
  date: string;
  text: string;
}

export interface Found extends Searchable {
  /** The passage where the words were found, or what the post says of itself. */
  passage: string;
}

/** Lower case, without accents: "nao" finds "não". */
export const plain = (text: string) => text.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

const count = (text: string, word: string) => text.split(word).length - 1;

/** The posts that hold every word asked for, the best first: a word in the title counts most, then a tag, then what the post says of itself, then its text. */
export function search(posts: readonly Searchable[], query: string): Found[] {
  const words = plain(query).split(/\s+/).filter((word) => word.length > 1);
  if (!words.length) return [];
  const found: { post: Found; weight: number }[] = [];
  for (const post of posts) {
    const title = plain(post.title);
    const tags = plain(post.tags.join(" "));
    const excerpt = plain(post.excerpt);
    const text = plain(post.text);
    let weight = 0;
    let every = true;
    for (const word of words) {
      const here = count(title, word) * 12 + count(tags, word) * 6 + count(excerpt, word) * 3 + Math.min(count(text, word), 12);
      if (!here) every = false;
      weight += here;
    }
    if (!every) continue;
    // The sentence of the text that holds the first word, when the text holds it.
    const at = text.indexOf(words[0]);
    let passage = post.excerpt;
    if (at >= 0 && !excerpt.includes(words[0])) {
      const from = Math.max(post.text.lastIndexOf("\n", at) + 1, post.text.lastIndexOf(". ", at) + 2, at - 160);
      const stops = [post.text.indexOf("\n", at), post.text.indexOf(". ", at) + 1].filter((stop) => stop > 0);
      const to = Math.min(stops.length ? Math.min(...stops) : post.text.length, at + 220);
      passage = post.text.slice(from, to).trim();
    }
    found.push({ post: { ...post, passage }, weight });
  }
  return found.sort((a, b) => b.weight - a.weight).map((entry) => entry.post);
}
