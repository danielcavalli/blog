"""The design system's fonts, cut to what dan.rio draws.

Maré ships Fraunces, Inter and Geist Mono whole: every script they cover and every axis, about
850 KB, which a phone downloads before the page reads in its own type. This writes, into
src/fonts/, the same faces cut to the Latin that English and Portuguese need (and the punctuation,
arrows, box drawing and symbols the posts and the design system's parts use), with Fraunces' SOFT
and WONK axes pinned where the design system leaves them (it never sets them) and the weight axis
kept to the span the design system uses (350 to 700). The optical-size axis stays whole, so every
size and weight the site sets looks as it does with the full files.

The full files stay in use for anything outside these ranges (src/fonts/fonts.css says so with
unicode-range), so a rare character still draws in the right face; it is fetched only if a page
uses one.

Run after raising the design system's version:

    uv run --with fonttools --with brotli python tools/fonts/subset.py
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "node_modules/@mare-rio/design-system/dist/fonts"
OUT = ROOT / "src/fonts"

RANGES = [
    (0x0020, 0x007E), (0x00A0, 0x00FF), (0x0131, 0x0131), (0x0152, 0x0153), (0x02C6, 0x02DC),
    (0x2000, 0x206F), (0x20A0, 0x20CF), (0x2100, 0x214F), (0x2190, 0x21FF), (0x2212, 0x2212), (0x2248, 0x2248),
    (0x2260, 0x2265), (0x2304, 0x2304), (0x2500, 0x257F), (0x25A0, 0x25FF), (0x2713, 0x2713), (0xFB01, 0xFB02),
]
# The weights the design system sets run from 360 (light) to 700; the axis keeps that span.
WEIGHTS = (350, 700)
FACES = {
    "fraunces.woff2": {"pin": {"SOFT": 0, "WONK": 1, "wght": WEIGHTS}},
    "fraunces-italic.woff2": {"pin": {"SOFT": 0, "WONK": 1, "wght": WEIGHTS}},
    "inter.woff2": {"pin": {"wght": WEIGHTS}},
    "geist-mono.woff2": {"pin": {"wght": WEIGHTS}},
}


def unicode_range(ranges: list[tuple[int, int]]) -> str:
    return ", ".join(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}" for a, b in ranges)


def complement(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out, at = [], 0
    for a, b in sorted(ranges):
        if a > at:
            out.append((at, a - 1))
        at = max(at, b + 1)
    if at <= 0x10FFFF:
        out.append((at, 0x10FFFF))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    record = {"design_system": json.loads((SOURCE.parents[1] / "package.json").read_text())["version"], "faces": {}}
    for name, how in FACES.items():
        font = TTFont(SOURCE / name)
        if how["pin"]:
            # (pinned, written out and read back: the pinned font's tables are then whole for the cut)
            pinned = io.BytesIO()
            instancer.instantiateVariableFont(font, how["pin"]).save(pinned)
            font = TTFont(io.BytesIO(pinned.getvalue()))
        options = subset.Options()
        options.flavor = "woff2"
        options.layout_features = ["*"]
        options.name_IDs = ["*"]
        options.name_languages = ["*"]
        options.notdef_outline = True
        options.hinting = False
        options.drop_tables += ["DSIG"]
        cutter = subset.Subsetter(options)
        cutter.populate(unicodes=[c for a, b in RANGES for c in range(a, b + 1)])
        cutter.subset(font)
        target = OUT / name.replace(".woff2", "-latin.woff2")
        font.flavor = "woff2"
        font.save(target)
        record["faces"][name] = {
            "source_sha256": hashlib.sha256((SOURCE / name).read_bytes()).hexdigest(),
            "source_bytes": (SOURCE / name).stat().st_size,
            "subset_bytes": target.stat().st_size,
        }
        print(f"{name}: {(SOURCE / name).stat().st_size // 1024} KB -> {target.stat().st_size // 1024} KB")
    record["weights"] = list(WEIGHTS)
    record["unicode_range"] = unicode_range(RANGES)
    record["rest"] = unicode_range(complement(RANGES))
    (OUT / "subsets.json").write_text(json.dumps(record, indent=2) + "\n")
    write_css(record)


CSS_HEAD = """/* The design system's three voices, cut to what dan.rio draws (tools/fonts/subset.py writes this file).
   Each face is declared twice: the cut, for the Latin the site uses, and the design system's whole
   file for everything else, fetched only if a page uses such a character.
   SIL Open Font License 1.1: node_modules/@mare-rio/design-system/dist/fonts/OFL-*.txt. */
"""
FAMILIES = [
    ("Fraunces", "normal", "fraunces"),
    ("Fraunces", "italic", "fraunces-italic"),
    ("Inter", "normal", "inter"),
    ("Geist Mono", "normal", "geist-mono"),
]


def write_css(record: dict) -> None:
    whole = "../../node_modules/@mare-rio/design-system/dist/fonts"
    weights = f"{record['weights'][0]} {record['weights'][1]}"
    lines = [CSS_HEAD]
    for family, style, stem in FAMILIES:
        lines.append(
            f'@font-face {{ font-family: "{family}"; font-style: {style}; font-weight: {weights}; font-display: swap; '
            f'src: url("./{stem}-latin.woff2") format("woff2"); unicode-range: {record["unicode_range"]}; }}'
        )
        # (the same weight span as the cut: a browser matches a family's faces by weight first, and of
        # two faces whose spans differ it takes only one, so the other's characters would never draw)
        lines.append(
            f'@font-face {{ font-family: "{family}"; font-style: {style}; font-weight: {weights}; font-display: swap; '
            f'src: url("{whole}/{stem}.woff2") format("woff2"); unicode-range: {record["rest"]}; }}'
        )
    (OUT / "fonts.css").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
