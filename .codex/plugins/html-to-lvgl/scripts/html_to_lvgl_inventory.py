#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


CONTROL_TAGS = {"button", "select", "input", "textarea", "option", "label"}
STRUCTURE_TAGS = {"main", "section", "article", "nav", "header", "footer", "form"}


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    text_parts: list[str] = field(default_factory=list)
    children: list["Node"] = field(default_factory=list)

    @property
    def text(self) -> str:
        value = " ".join(part.strip() for part in self.text_parts if part.strip())
        return html.unescape(re.sub(r"\s+", " ", value)).strip()

    @property
    def classes(self) -> list[str]:
        return [c for c in self.attrs.get("class", "").split() if c]

    @property
    def ident(self) -> str:
        return self.attrs.get("id", "")


class InventoryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag.lower(), {k.lower(): v or "" for k, v in attrs})
        self.stack[-1].children.append(node)
        self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.stack[-1].text_parts.append(data)


def walk(node: Node) -> Iterable[Node]:
    yield node
    for child in node.children:
        yield from walk(child)


def label_for(node: Node) -> str:
    candidates = [
        node.text,
        node.attrs.get("aria-label", ""),
        node.attrs.get("title", ""),
        node.attrs.get("value", ""),
        node.attrs.get("placeholder", ""),
        node.ident,
        " ".join(node.classes),
    ]
    return next((c.strip() for c in candidates if c.strip()), node.tag)


def lvgl_guess(node: Node) -> str:
    tag = node.tag
    role = node.attrs.get("role", "")
    input_type = node.attrs.get("type", "").lower()
    classes = " ".join(node.classes).lower()
    marker = " ".join([node.ident.lower(), classes, node.attrs.get("name", "").lower()])

    if tag == "canvas" and ("wheel" in marker or "picker" in marker or "color" in marker):
        return "lv_colorwheel or image/canvas"
    if tag == "canvas":
        return "lv_canvas/image; inspect manually"
    if tag == "input" and input_type == "range":
        return "lv_slider"
    if tag == "input" and input_type in {"checkbox", "radio"}:
        return "lv_checkbox"
    if tag == "input" and input_type == "color":
        return "lv_colorwheel"
    if tag == "select":
        return "lv_dropdown"
    if tag == "button" or role == "button":
        return "lv_btn"
    if "wheel" in marker and ("color" in marker or "picker" in marker):
        return "lv_colorwheel"
    if tag == "nav" or "tab" in classes:
        return "lv_btn row"
    if tag in STRUCTURE_TAGS:
        return "lv_obj section"
    if "card" in classes or "panel" in classes:
        return "lv_obj card"
    if "scroll" in classes:
        return "lv_obj scrollable"
    return "lv_label/lv_obj"


def classify(node: Node) -> str:
    tag = node.tag
    classes = " ".join(node.classes).lower()
    marker = " ".join([node.ident.lower(), classes])
    if tag == "canvas" and ("wheel" in marker or "picker" in marker or "color" in marker):
        return "control"
    if tag == "canvas":
        return "control"
    if tag in CONTROL_TAGS or node.attrs.get("role") == "button":
        return "control"
    if tag in STRUCTURE_TAGS:
        return "section"
    if "tab" in classes:
        return "tab"
    if "card" in classes or "panel" in classes:
        return "card"
    return "text"


def extract_inventory(path: Path) -> dict[str, object]:
    parser = InventoryParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    items = []
    for node in walk(parser.root):
        if node.tag in {"document", "script", "style"}:
            continue
        category = classify(node)
        if category == "text" and (not node.text or len(node.text) < 2):
            continue
        items.append(
            {
                "tag": node.tag,
                "id": node.ident,
                "class": node.classes,
                "type": node.attrs.get("type", ""),
                "label": label_for(node)[:120],
                "category": category,
                "lvgl": lvgl_guess(node),
            }
        )

    summary: dict[str, int] = {}
    for item in items:
        key = str(item["lvgl"])
        summary[key] = summary.get(key, 0) + 1

    return {"source": str(path), "summary": summary, "items": items}


def emit_markdown(inventory: dict[str, object]) -> str:
    lines = [f"# LVGL Inventory: `{inventory['source']}`", "", "## Summary", ""]
    summary = inventory["summary"]
    assert isinstance(summary, dict)
    for key, count in sorted(summary.items()):
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Candidate Components", ""])
    lines.append("| Category | HTML | Label | LVGL guess |")
    lines.append("| --- | --- | --- | --- |")
    items = inventory["items"]
    assert isinstance(items, list)
    for item in items:
        assert isinstance(item, dict)
        html_name = str(item["tag"])
        if item.get("id"):
            html_name = f"{html_name}#{item['id']}"
        classes = item.get("class") or []
        if classes:
            html_name = f"{html_name}.{'.'.join(classes[:3])}"
        lines.append(f"| {item['category']} | `{html_name}` | {item['label']} | `{item['lvgl']}` |")
    lines.extend(
        [
            "",
            "## Porting Notes",
            "",
            "- Treat this as an inventory, not an automatic conversion.",
            "- Group repeated controls into LVGL helper functions.",
            "- Keep shell/tabs fixed and make long content scroll vertically.",
            "- Verify emitted commands against firmware protocol.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--format", choices=["md", "json"], default="md")
    args = parser.parse_args()
    inventory = extract_inventory(args.html_file)
    if args.format == "json":
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
    else:
        print(emit_markdown(inventory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
