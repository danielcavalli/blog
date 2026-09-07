"""Compile article navigation and notes from rendered Markdown, without rewriting prose."""

from dataclasses import dataclass
import re
import xml.etree.ElementTree as ET

import html5lib

from markdown_refs import _dedupe_id, _slugify_anchor


@dataclass(frozen=True)
class ReadingLayout:
    content: str
    outline: str
    notes: str


def _html(element: ET.Element) -> str:
    return html5lib.serialize(
        element,
        tree="etree",
        quote_attr_values="always",
        omit_optional_tags=False,
        alphabetical_attributes=False,
    )


def _remove(parent: ET.Element, element: ET.Element) -> None:
    children = list(parent)
    index = children.index(element)
    if element.tail:
        if index:
            previous = children[index - 1]
            previous.tail = (previous.tail or "") + element.tail
        else:
            parent.text = (parent.text or "") + element.tail
    element.tail = None
    parent.remove(element)


def _heading_text(element: ET.Element) -> str:
    parts = [element.text or ""]
    for child in element:
        if "permalink-anchor" not in child.get("class", "").split():
            parts.extend(child.itertext())
        parts.append(child.tail or "")
    return " ".join("".join(parts).split())


def _strip_note_returns(note: ET.Element) -> None:
    """Drop footnote navigation while retaining source links and cross-references."""
    return_label = re.compile(
        r"(?:back|(?:get|go) back|return|voltar|retornar)"
        r"(?:\s+(?:to (?:the )?(?:text|reference|first use)|ao texto|à referência))?[.!]?",
        re.IGNORECASE,
    )
    for parent in list(note.iter()):
        for child in list(parent):
            classes = set(child.get("class", "").split())
            generated = classes.intersection(
                {"footnote-backref", "sidenote-backlink", "sidenote-returns"}
            ) or child.get("role") == "doc-backlink"
            authored = (
                child.tag == "a"
                and child.get("href", "").startswith("#")
                and return_label.fullmatch(" ".join("".join(child.itertext()).split()))
            )
            if generated or authored:
                _remove(parent, child)


def _retire_decoration(parent: ET.Element, element: ET.Element) -> None:
    """Keep existing fragment targets without an empty heading or divider."""
    identifiers = [e.attrib["id"] for e in element.iter() if e.get("id")]
    if not identifiers:
        _remove(parent, element)
        return
    tail = element.tail
    element.clear()
    element.tag = "span"
    element.set("id", identifiers[0])
    element.tail = tail
    for identifier in identifiers[1:]:
        ET.SubElement(element, "span", {"id": identifier})


def _remove_empty_reference_sections(
    root: ET.Element, original_children: list[ET.Element], moved: set[ET.Element],
) -> None:
    """Clean up labels left behind when their entries became sidenotes."""
    labels = {"sources", "references", "notes", "footnotes", "fontes", "referências", "notas"}

    def empty_anchor(element: ET.Element) -> bool:
        return element.tag in {"a", "span"} and not "".join(element.itertext()).strip()

    children = original_children
    for index, element in enumerate(children):
        is_heading = re.fullmatch(r"h[1-6]", str(element.tag))
        if not (is_heading or element.tag == "p"):
            continue
        if _heading_text(element).casefold().rstrip(":.") not in labels:
            continue
        remaining = []
        for sibling in children[index + 1 :]:
            if re.fullmatch(r"h[1-6]", str(sibling.tag)) and (
                not is_heading or sibling.tag <= element.tag
            ):
                break
            remaining.append(sibling)
        if any(e in moved for e in remaining) and all(e in moved or empty_anchor(e) for e in remaining):
            _retire_decoration(root, element)
            if index and children[index - 1].tag == "hr":
                _retire_decoration(root, children[index - 1])
    # Handwritten footnotes can have a divider without a section label.
    found_note = False
    for element in reversed(children):
        if element in moved:
            found_note = True
            continue
        if empty_anchor(element):
            continue
        if element.tag == "hr" and found_note and element in root:
            _retire_decoration(root, element)
        break


def compile_reading_layout(content: str, *, lang: str = "en") -> ReadingLayout:
    root = html5lib.parseFragment(content, treebuilder="etree", namespaceHTMLElements=False)
    parents = {child: parent for parent in root.iter() for child in parent}
    original_children = list(root)
    moved: set[ET.Element] = set()
    used_ids = {e.get("id", "") for e in root.iter()}
    pt = lang.startswith("pt")
    definitions: dict[str, ET.Element] = {}
    for element in root.iter():
        identifier = element.get("id", "")
        if element.tag == "li" and identifier.startswith("fn:"):
            definitions[identifier] = element
        elif element.tag in {"span", "a"} and re.fullmatch(
            r"(?:ref-\d+|footnote-[\w-]+)", identifier
        ):
            parent = parents[element]
            # A reference paragraph is one note. Ambiguous multi-reference blocks
            # remain in the references section with their original links intact.
            refs = [
                e
                for e in parent.iter()
                if re.fullmatch(r"(?:ref-\d+|footnote-[\w-]+)", e.get("id", ""))
            ]
            if parent.tag == "p" and len(refs) == 1:
                definitions[identifier] = parent

    references: dict[str, list[ET.Element]] = {}
    definition_elements = {
        child for definition in definitions.values() for child in definition.iter()
    }
    for anchor in root.iter("a"):
        if anchor in definition_elements:
            continue
        target = anchor.get("href", "").removeprefix("#")
        if anchor.get("href", "").startswith("#") and target in definitions:
            references.setdefault(target, []).append(anchor)

    notes = ET.Element(
        "aside", {"class": "article-notes", "aria-label": "Notas" if pt else "Notes"}
    )
    if references:
        ET.SubElement(notes, "h2", {"class": "notes-heading"}).text = "Notas" if pt else "Notes"
    for target, anchors in references.items():
        definition = definitions[target]
        number = "".join(anchors[0].itertext()).strip("[] ")
        note_id = _dedupe_id(f"sidenote-{target}", used_ids)
        note = ET.SubElement(
            notes,
            "section",
            {
                "class": "sidenote",
                "id": note_id,
                "role": "doc-footnote",
                "tabindex": "-1",
            },
        )
        ET.SubElement(
            note, "span", {"class": "sidenote-label", "aria-hidden": "true"}
        ).text = number
        _remove(parents[definition], definition)
        moved.add(definition)
        if definition.tag == "li":
            definition.tag = "div"
        else:
            marker = next(e for e in definition.iter() if e.get("id") == target)
            if re.fullmatch(r"\[\d+\]", marker.text or ""):
                marker.text = None
            marker.tail = re.sub(r"^\[\d+\]\s*", "", marker.tail or "")
            for child in definition:
                if child.tag == "strong" and child.text:
                    child.text = re.sub(r"^\[\d+\]\s*", "", child.text)
                    break
        _strip_note_returns(definition)
        note.append(definition)
        for index, anchor in enumerate(anchors, 1):
            reference_id = anchor.get("id") or _dedupe_id(f"cite-{target}-{index}", used_ids)
            anchor.set("id", reference_id)
            anchor.set("class", (anchor.get("class", "") + " note-reference").strip())
            anchor.set("role", "doc-noteref")
            anchor.set("data-note-target", note_id)

    # Remove the generated footnote wrapper, then any now-empty source section.
    for element in list(root.iter()):
        if "footnote" in element.get("class", "").split() and not list(element.iter("li")):
            _remove(parents[element], element)
    if references:
        _remove_empty_reference_sections(root, original_children, moved)

    headings = [e for e in root.iter() if re.fullmatch(r"h[1-6]", str(e.tag))]
    outline = ""
    if headings:
        nav = ET.Element(
            "nav",
            {"class": "article-outline", "aria-label": "Neste artigo" if pt else "On this page"},
        )
        details = ET.SubElement(nav, "details", {"open": ""})
        ET.SubElement(details, "summary").text = "Neste artigo" if pt else "On this page"
        listing = ET.SubElement(details, "ol", {"class": "outline-list"})
        ancestors: list[tuple[int, ET.Element]] = []
        for heading in headings:
            text = _heading_text(heading)
            if not text:
                continue
            identifier = heading.get("id")
            if not identifier:
                identifier = _dedupe_id(_slugify_anchor(text), used_ids)
                heading.set("id", identifier)
            level = int(heading.tag[1])
            while ancestors and level <= ancestors[-1][0]:
                ancestors.pop()
            parent_list = listing
            if ancestors:
                parent = ancestors[-1][1]
                parent_list = parent.find("ol")
                if parent_list is None:
                    parent_list = ET.SubElement(parent, "ol")
            item = ET.SubElement(parent_list, "li")
            ET.SubElement(item, "a", {"href": f"#{identifier}"}).text = text
            ancestors.append((level, item))
        outline = _html(nav)
    return ReadingLayout(_html(root), outline, _html(notes) if references else "")
