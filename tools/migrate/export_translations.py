"""One-off migration: accepted translations become Markdown files beside their sources.

The old engine kept each accepted translation as a JSON revision under
`_source/translations/`. From here on a translation is an ordinary reef-spec
Markdown file next to the document it translates:

    posts/<slug>.md              the source, in the language it was written in
    posts/<slug>.<locale>.md     its translation

Run from the repository root with the old engine's environment:

    uv run python tools/migrate/export_translations.py

It reads the accepted store through the old engine (which verifies every
revision's hash), writes the files, and then rewrites cross-post links from the
old repository-root form (`_source/posts/x.md`) to links between sibling files,
which is what Reef follows.

Source digest, version 1
------------------------
A translation records which text it was made from as `source_digest`: the
SHA-256, in hex, of the UTF-8 bytes of

    title: <title>\n
    excerpt: <excerpt>\n
    tags: <tag>, <tag>, ...\n
    \n
    <body>

where `<body>` is the source file after its front matter and before its reef
trailer, with CRLF read as LF and whitespace trimmed at both ends. A missing
field is the empty string. Dates, slugs and other front matter do not count: a
translation is stale only when words a reader sees have changed.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import frontmatter
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_source"))

import paths  # noqa: E402

paths.POSTS_DIR = ROOT / "posts"

import translations  # noqa: E402
from translation_v2.accepted import AcceptedTranslations, digest  # noqa: E402

translations.POSTS_DIR = ROOT / "posts"

TRAILER = re.compile(r"\n<!-- reef [\s\S]*\Z")
OLD_LINK = re.compile(r"\]\((?:\./)?(?:_source/posts/)([a-z0-9-]+)\.md((?:[#?][^)]*)?)\)")


def body_of(text: str) -> str:
    """A file's body: after the front matter, before the trailer, trimmed."""
    content = frontmatter.loads(text).content.replace("\r\n", "\n")
    lines = content.split("\n")
    # The trailer is the final run of reef comments and blank lines.
    end = len(lines)
    inside = False
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]
        if not inside and line.strip() == "":
            continue
        if line.rstrip().endswith("-->"):
            inside = True
        if inside and line.startswith("<!-- reef "):
            end = index
            inside = False
            continue
        if not inside:
            break
    return "\n".join(lines[:end]).strip()


def source_digest(title: str, excerpt: str, tags: list[str], body: str) -> str:
    text = f"title: {title}\nexcerpt: {excerpt}\ntags: {', '.join(tags)}\n\n{body}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def front(fields: dict) -> str:
    dumped = yaml.safe_dump(fields, allow_unicode=True, sort_keys=False, width=10_000)
    return f"---\n{dumped}---\n\n"


def translated_at(provenance: dict) -> str | None:
    match = re.search(r"-(\d{4})(\d{2})(\d{2})\d{6}-", str(provenance.get("run_id", "")))
    return f"{match[1]}-{match[2]}-{match[3]}" if match else None


def translated_by(provenance: dict) -> str:
    model = provenance.get("translation_model") or "unknown model"
    effort = provenance.get("reasoning_effort")
    provider = provenance.get("provider") or "unknown provider"
    return f"{model}{f' ({effort})' if effort else ''}, via {provider}"


def main() -> int:
    store = AcceptedTranslations(ROOT / "_source" / "translations")
    source_lang: dict[str, str] = {}
    written: list[Path] = []
    for artifact in translations.discover_artifacts():
        source = artifact["source"]
        kind, slug = source["artifact_type"], source["slug"]
        target = source["target_locale"]
        record = store.current(source)
        if record is None or record["source_hash"] != digest(source):
            raise SystemExit(f"{kind}:{slug} has no current accepted translation; update it first")
        translation, provenance = record["translation"], record["provenance"]
        if kind in {"post", "presentation"}:
            source_path = Path(artifact["attach_path"])
            source_lang[slug] = source["source_locale"]
            if source_path.stem != slug:
                raise SystemExit(f"{source_path.name}: file name and slug '{slug}' differ")
            raw = source_path.read_text(encoding="utf-8")
            meta = frontmatter.loads(raw).metadata
            fields = {
                "title": translation["title"],
                "excerpt": translation["excerpt"],
                "tags": list(translation["tags"]),
                "lang": target,
                "translation_of": source_path.name,
                "source_digest": source_digest(
                    str(meta.get("title", "")),
                    str(meta.get("excerpt", "")),
                    [str(tag) for tag in meta.get("tags", [])],
                    body_of(raw),
                ),
                "translated_by": translated_by(provenance),
            }
            when = translated_at(provenance)
            if when:
                fields["translated_at"] = when
            out = source_path.with_name(f"{slug}.{target}.md")
            out.write_text(front(fields) + translation["content"].strip() + "\n", encoding="utf-8")
            written.append(out)
        elif kind == "about":
            pages = ROOT / "pages"
            title, _, body = source["text"].partition("\n\n")
            source_title = title.removeprefix("# ").strip()
            source_body = body.strip()
            (pages / "about.md").write_text(
                front({"title": source_title, "lang": source["source_locale"]}) + source_body + "\n",
                encoding="utf-8",
            )
            t_title, _, t_body = translation["content"].partition("\n\n")
            fields = {
                "title": t_title.removeprefix("# ").strip() if t_title.startswith("# ") else translation["title"],
                "lang": target,
                "translation_of": "about.md",
                "source_digest": source_digest(source_title, "", [], source_body),
                "translated_by": translated_by(provenance),
            }
            when = translated_at(provenance)
            if when:
                fields["translated_at"] = when
            out = pages / f"about.{target}.md"
            out.write_text(
                front(fields) + (t_body if t_title.startswith("# ") else translation["content"]).strip() + "\n",
                encoding="utf-8",
            )
            written += [pages / "about.md", out]
        elif kind == "cv":
            out = ROOT / f"cv_data.{target}.yaml"
            out.write_text(
                yaml.safe_dump(translation, allow_unicode=True, sort_keys=False, width=10_000),
                encoding="utf-8",
            )
            written.append(out)

    # Cross-post links: a sibling file in the reader's language, as Reef follows them.
    relinked = 0
    for path in sorted((ROOT / "posts").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lang = str(frontmatter.loads(text).metadata.get("lang", "")).lower()

        def sibling(match: re.Match[str]) -> str:
            slug, rest = match[1], match[2]
            if slug not in source_lang:
                raise SystemExit(f"{path.name}: link to unknown post '{slug}'")
            name = f"{slug}.md" if source_lang[slug] == lang else f"{slug}.{lang}.md"
            return f"]({name}{rest})"

        updated, count = OLD_LINK.subn(sibling, text)
        if count:
            path.write_text(updated, encoding="utf-8")
            relinked += count

    for path in written:
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"{len(written)} files written, {relinked} cross-post links rewritten")
    # Rewriting links changed some sources, so the digests are taken last.
    print(f"{refresh_digests()} source digests refreshed")
    return 0


def refresh_digests() -> int:
    """Set every translation's `source_digest` from its source as the file stands now."""
    changed = 0
    for folder in (ROOT / "posts", ROOT / "pages"):
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta = frontmatter.loads(text).metadata
            if "translation_of" not in meta:
                continue
            raw = (path.parent / str(meta["translation_of"])).read_text(encoding="utf-8")
            source = frontmatter.loads(raw).metadata
            current = source_digest(
                str(source.get("title", "")),
                str(source.get("excerpt", "")),
                [str(tag) for tag in source.get("tags", [])],
                body_of(raw),
            )
            line = re.compile(r"^source_digest: .*$", re.MULTILINE)
            updated = line.sub(f"source_digest: {current}", text, count=1)
            if updated != text:
                path.write_text(updated, encoding="utf-8")
                changed += 1
    return changed


if __name__ == "__main__":
    if sys.argv[1:] == ["--digests"]:
        print(f"{refresh_digests()} source digests refreshed")
        raise SystemExit(0)
    raise SystemExit(main())
