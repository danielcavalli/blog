"""Read real Markdown without hidden metadata or filesystem writes."""

import pytest
import html5lib

from content_loader import parse_markdown_post


@pytest.mark.parametrize(
    "language_field,locale",
    [("", "en-us"), ("lang: pt-br\n", "pt-br"), ("source_language: es-es\n", "es-es")],
)
def test_authored_frontmatter_and_heading_anchors(tmp_path, language_field, locale):
    path = tmp_path / "example.md"
    original = (
        "---\ntitle: Example\ndate: 2026-05-01\nupdated: 2026-05-02\n"
        + language_field + "tags: [writing]\n---\n## Topic\n\nOriginal text.\n"
    )
    path.write_text(original)
    post = parse_markdown_post(path)
    assert post["lang"] == locale
    assert post["slug"] == "example"
    assert post["published_date"] == "2026-05-01"
    assert post["updated_fm_date"] == "2026-05-02"
    assert post["tags"] == ["writing"]
    document = html5lib.parseFragment(post["content"], namespaceHTMLElements=False)
    heading = document.find(".//h2[@id='topic']")
    assert heading is not None and heading.text == "Topic"
    assert parse_markdown_post(path) == post
    assert path.read_text() == original
    assert list(tmp_path.iterdir()) == [path]


def test_legacy_build_timestamps_do_not_replace_editorial_dates(tmp_path):
    path = tmp_path / "example.md"
    path.write_text(
        "---\ntitle: Example\ndate: 2025-01-01\ncreated_at: 2026-02-01\n"
        "updated_at: 2026-03-01\ncontent_hash: obsolete\n---\nText.\n"
    )
    post = parse_markdown_post(path)
    assert post["published_date"] == "2025-01-01"
    assert post["updated_fm_date"] == ""
    assert not {"created_date", "updated_date", "content_hash"} & post.keys()
