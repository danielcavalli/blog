"""One-off migration: a post's pictures and files move beside it and are linked as Markdown.

The old site kept them under /static/ and wrote each picture as an HTML figure holding two images,
one for the light theme and one for the dark. Reef cannot follow a path from the site's root, and the
figure is not Markdown. From here on a post's files live in `posts/<slug>.assets/`, and a picture is

    ![what it shows](<slug>.assets/hub-day.jpg "its caption")

The same picture under another light is the file beside it with that light's name in place of `day`
(`hub-night.jpg`, `hub-dusk.jpg`); the site shows the one for the reader's light.

    uv run python tools/migrate/figures.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOVED = {
    "/static/images/mare-rio/": "mare-rio-and-mare-hub.assets/",
    "/static/images/mare-agent/": "adding-an-agent-to-a-mare-app.assets/",
    "/static/images/presentations/how-i-use-ai-agents/": "how-i-use-ai-agents.assets/",
    "/static/examples/mare-agent/": "adding-an-agent-to-a-mare-app.assets/",
}
FIGURE = re.compile(r"<figure class=\"post-figure theme-media\">([\s\S]*?)</figure>")
LIGHT = re.compile(r"data-theme-variant=\"light\"[^>]*>\s*<img\b[^>]*?\bsrc=\"([^\"]+)\"[^>]*?\balt=\"([^\"]*)\"")
CAPTION = re.compile(r"<figcaption>([\s\S]*?)</figcaption>")


def moved(path: str) -> str:
    for old, new in MOVED.items():
        if path.startswith(old):
            return new + path[len(old):]
    raise SystemExit(f"no new place for {path}")


def figure(match: re.Match[str]) -> str:
    inner = match[1]
    light = LIGHT.search(inner)
    caption = CAPTION.search(inner)
    if not light:
        raise SystemExit(f"a figure without a light picture: {inner[:80]}")
    alt = html.unescape(light[2]).replace("[", "(").replace("]", ")")
    line = f"![{alt}]({moved(light[1])}"
    if caption:
        words = html.unescape(re.sub(r"\s+", " ", caption[1]).strip())
        if "<" in words:
            raise SystemExit(f"a caption with markup, to convert by hand: {words}")
        line += ' "' + words.replace('"', '\\"') + '"'
    return line + ")"


def main() -> None:
    changed = 0
    for path in sorted((ROOT / "posts").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        updated = FIGURE.sub(figure, text)
        for old in MOVED:
            updated = re.sub(re.escape(old) + r"([^\s\")]+)", lambda m: moved(m[0]), updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed += 1
            print(f"rewrote {path.relative_to(ROOT)}")
    print(f"{changed} files rewritten")


if __name__ == "__main__":
    main()
