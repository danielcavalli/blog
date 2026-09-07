"""Resolve authored Markdown post paths to the reader's language at render time."""

from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

import frontmatter
import html5lib

from helpers import get_lang_path
from paths import POSTS_DIR


def resolve_post_links(content: str, *, lang: str, source_path: str | None = None) -> str:
    """Keep source links literal in stored content; resolve actual HTML anchors only."""
    root = html5lib.parseFragment(content, namespaceHTMLElements=False)
    posts_dir = POSTS_DIR.resolve()
    source_dir = Path(source_path).resolve().parent if source_path else posts_dir
    protected = {
        anchor for element in root.iter() if element.tag in {"pre", "code"}
        for anchor in element.iter("a")
    }
    changed = False
    for anchor in root.iter("a"):
        href = anchor.get("href", "")
        if anchor in protected:
            continue
        url = urlsplit(href)
        if url.scheme or url.netloc:
            continue
        path = unquote(url.path).removeprefix("./")
        if not path.endswith(".md"):
            continue
        repository_path = path.lstrip("/").startswith("_source/posts/")
        if repository_path:
            target = (posts_dir.parent.parent / path.lstrip("/")).resolve()
        else:
            target = (source_dir / path).resolve()
        if not repository_path and not target.is_relative_to(posts_dir):
            continue
        # Match the builder's source discovery: only Markdown files directly in posts/.
        if target.parent != posts_dir or not target.is_file():
            raise ValueError(
                f"Invalid source post link {href!r} in {source_path or 'rendered content'}: "
                f"expected a Markdown file directly in {posts_dir}."
            )
        slug = frontmatter.load(str(target)).get("slug", target.stem)
        anchor.set("href", urlunsplit((
            "", "", get_lang_path(lang, f"blog/{slug}.html"), url.query, url.fragment,
        )))
        changed = True
    if not changed:
        return content
    return html5lib.serialize(
        root, tree="etree", quote_attr_values="always", omit_optional_tags=False,
        alphabetical_attributes=False,
    )
