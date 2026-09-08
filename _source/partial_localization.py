"""Keep source-only builds navigable without inventing translated pages."""

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from config import BASE_PATH, SITE_URL


class _AvailableLinks(HTMLParser):
    def __init__(self, html: str, missing: dict[str, str], *, single_language: bool):
        super().__init__(convert_charrefs=False)
        self.html = html
        self.missing = missing
        self.single_language = single_language
        self.offsets = [0]
        for line in html.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.edits: list[tuple[int, int, str]] = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        original = self.get_starttag_text() or ""
        replacement = original
        href = attributes.get("href", "") or ""
        url = urlsplit(href)
        internal = not url.netloc or url.netloc == urlsplit(SITE_URL).netloc
        if internal and url.path in self.missing:
            if tag == "link" and attributes.get("rel") == "alternate":
                replacement = ""
            elif tag == "a":
                destination = self.missing[url.path]
                if "lang-toggle" in (attributes.get("class") or "").split():
                    destination = url.path.rsplit("/blog/", 1)[0] + "/index.html" if "/blog/" in url.path else url.path.rsplit("/", 1)[0] + "/index.html"
                localized_href = urlunsplit((url.scheme, url.netloc, destination, url.query, url.fragment))
                replacement = re.sub(
                    r'''\bhref\s*=\s*(["']).*?\1''',
                    lambda _: f'href="{escape(localized_href, quote=True)}"', original, count=1,
                    flags=re.IGNORECASE | re.DOTALL,
                )
        if self.single_language and tag == "meta" and attributes.get("property") == "og:locale:alternate":
            replacement = ""
        if replacement != original:
            line, column = self.getpos()
            start = self.offsets[line - 1] + column
            self.edits.append((start, start + len(original), replacement))

    def result(self) -> str:
        self.feed(self.html)
        rendered = self.html
        for start, end, replacement in reversed(self.edits):
            rendered = rendered[:start] + replacement + rendered[end:]
        return rendered


def adapt_unavailable_links(staging: Path, missing_pages: dict[str, str]) -> None:
    """Change only link tags, leaving article prose and embedded code byte-for-byte."""
    missing = {BASE_PATH + path: BASE_PATH + target for path, target in missing_pages.items()}
    for path in staging.rglob("*.html"):
        html = path.read_text(encoding="utf-8")
        rendered = _AvailableLinks(
            html, missing, single_language=BASE_PATH + "/" + path.relative_to(staging).as_posix() in missing.values(),
        ).result()
        if rendered != html:
            path.write_text(rendered, encoding="utf-8")
    sitemap = staging / "sitemap.xml"
    if sitemap.exists():
        tree = ET.parse(sitemap)
        root = tree.getroot()
        sitemap_ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
        xhtml_ns = "http://www.w3.org/1999/xhtml"
        for entry in list(root):
            loc = entry.find(f"{{{sitemap_ns}}}loc")
            if loc is not None and urlsplit(loc.text or "").path in missing:
                root.remove(entry)
                continue
            for alternate in list(entry.findall(f"{{{xhtml_ns}}}link")):
                if urlsplit(alternate.get("href", "")).path in missing:
                    entry.remove(alternate)
        ET.register_namespace("", sitemap_ns)
        ET.register_namespace("xhtml", xhtml_ns)
        tree.write(sitemap, encoding="utf-8", xml_declaration=True)
