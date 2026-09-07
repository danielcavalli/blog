"""Source links are portable authored content, resolved only for presentation."""

import html5lib
import pytest

import post_links
from build import _prepare_presentation_post
from content_loader import parse_markdown_post
from markdown_refs import render_markdown_with_internal_refs
from renderer import generate_post_html, generate_presentation_html


@pytest.fixture
def posts(tmp_path, monkeypatch):
    directory = tmp_path / "_source/posts"
    directory.mkdir(parents=True)
    (directory / "original name.md").write_text(
        "---\ntitle: Um assunto\nslug: published-slug\nlang: pt-br\ndate: 2026-09-06\n---\n"
        "## Uma seção {#stable-section}\n\nTexto.\n"
    )
    monkeypatch.setattr(post_links, "POSTS_DIR", directory)
    return directory


def anchors(content):
    return list(html5lib.parseFragment(content, namespaceHTMLElements=False).iter("a"))


@pytest.mark.parametrize("lang", ["en", "pt"])
@pytest.mark.parametrize("path", [
    "_source/posts/original%20name.md", "/_source/posts/original%20name.md",
    "./_source/posts/original%20name.md",
    "original%20name.md", "./original%20name.md", "../posts/original%20name.md",
    "absolute",
])
def test_source_paths_follow_frontmatter_slug_and_reader_language(posts, path, lang, monkeypatch):
    monkeypatch.setattr("helpers.BASE_PATH", "/site")
    if path == "absolute":
        path = str(posts / "original name.md")
    content = f'<p><a href="{path}?a=1&amp;b=2#stable-section" title="Read">Text</a></p>'
    result = post_links.resolve_post_links(content, lang=lang, source_path=str(posts / "current.md"))
    link, = anchors(result)
    assert link.get("href") == f"/site/{lang}/blog/published-slug.html?a=1&b=2#stable-section"
    assert link.get("title") == "Read"
    assert link.text == "Text"


def test_reference_links_and_sidenotes_resolve_without_changing_markdown(posts):
    markdown = """Read [the earlier post][earlier]. A detail.[^context]

[^context]: See [this section](original%20name.md#stable-section).

[earlier]: _source/posts/original%20name.md
"""
    path = posts / "current.md"
    path.write_text("---\ntitle: Current\ndate: 2026-09-06\n---\n" + markdown)
    original = path.read_bytes()
    post = parse_markdown_post(path)
    result = generate_post_html(post, 1, lang="pt")
    document = html5lib.parse(result, namespaceHTMLElements=False)
    links = [a.get("href") for a in document.iter("a")]
    assert "/pt/blog/published-slug.html" in links
    note = next(e for e in document.iter() if "sidenote" in e.get("class", "").split())
    assert any(a.get("href") == "/pt/blog/published-slug.html#stable-section" for a in note.iter("a"))
    assert path.read_bytes() == original
    assert post["raw_content"] == markdown.strip()


def test_other_links_images_and_code_remain_literal(posts):
    content = '''<p><a href="https://example.com/file.md">External</a>
<a href="//example.com/file.md">External</a><a href="/en/blog/old.html">Published</a>
<a href="#heading">Heading</a><a href="../../docs/example.md">Document</a>
<a href="/static/example.md">Download</a><img src="original%20name.md" alt="Example"></p>
<pre><code>&lt;a href="original%20name.md"&gt;Example&lt;/a&gt;</code></pre>
<code><a href="original%20name.md">Literal code</a></code>'''
    assert post_links.resolve_post_links(content, lang="en") == content
    # Resolving a neighboring real link must not rewrite any of the examples.
    changed = post_links.resolve_post_links(content + '<a href="original%20name.md">Real</a>', lang="en")
    assert [a.get("href") for a in anchors(changed)][:-1] == [a.get("href") for a in anchors(content)]
    document = html5lib.parseFragment(changed, namespaceHTMLElements=False)
    image = document.find(".//img")
    assert image is not None and image.get("src") == "original%20name.md"


@pytest.mark.parametrize("href", ["missing.md", "_source/posts/missing.md", "/_source/posts/../outside.md", "nested/post.md"])
def test_invalid_post_targets_fail_with_authored_location(posts, href):
    source_path = str(posts / "current.md")
    with pytest.raises(ValueError, match="Invalid source post link") as error:
        post_links.resolve_post_links(f'<a href="{href}">Missing</a>', lang="en", source_path=source_path)
    assert href in str(error.value)
    assert source_path in str(error.value)


def test_presentation_links_use_the_same_resolver(posts):
    path = posts / "slides.md"
    path.write_text('''---
title: Presentation
content_type: presentation
date: 2026-09-06
---
<!-- presentation:slide id="intro" layout="content" density="normal" -->
# Further reading

[The article](_source/posts/original%20name.md#stable-section)
<!-- /presentation:slide -->
''')
    post = _prepare_presentation_post(parse_markdown_post(path))
    result = generate_presentation_html(post, 1, lang="pt")
    assert 'href="/pt/blog/published-slug.html#stable-section"' in result


def test_markdown_code_examples_do_not_become_post_links(posts):
    markdown = "`[Example](missing.md)`\n\n```markdown\n[Example](missing.md)\n```"
    content = render_markdown_with_internal_refs(markdown)
    assert post_links.resolve_post_links(content, lang="pt") == content
