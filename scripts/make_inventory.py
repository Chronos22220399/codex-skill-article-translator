#!/usr/bin/env python3
"""Parse a translated Markdown unit into a stable block inventory.

This is the deterministic first step of the reader pipeline. It assigns stable
ids to every visible block so `alignment.json` stays stable across sessions and
models, and it tracks the current figure/table number so the reader builder can
emit `fig-*` and `table-*` anchors without guessing.

Usage:
    python scripts/make_inventory.py --translation translation/article-zh.md \
        --output translation-blocks.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value).strip("-").lower() or "section"


def parse(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    section = ""
    counters: dict[str, int] = {}
    last_table: int | None = None
    i = 0

    def nid(prefix: str) -> str:
        counters[prefix] = counters.get(prefix, 0) + 1
        return f"{prefix}-{counters[prefix]:03d}"

    def table_number(text: str) -> int | None:
        match = re.search(r"(?:表|Table)\s*([0-9]+)", text)
        return int(match.group(1)) if match else None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("<!--"):
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            section = title
            found = table_number(title)
            if found:
                last_table = found
            blocks.append({"id": nid("h"), "type": "heading", "level": level,
                           "section": section, "translation": title})
            i += 1
            continue
        if line.startswith("```"):
            language = line[3:].strip()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append({"id": nid("code"), "type": "code", "section": section,
                           "language": language, "translation": "\n".join(code)})
            continue
        image = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image:
            alt, path = image.groups()
            number_match = re.search(r"(?:图|Figure)\s*([0-9]+)", alt)
            lookahead = i + 1
            while lookahead < len(lines) and not lines[lookahead].strip():
                lookahead += 1
            caption = ""
            if lookahead < len(lines) and lines[lookahead].lstrip().startswith("**"):
                caption = lines[lookahead].strip()
                i = lookahead
            blocks.append({"id": nid("fig"), "type": "figure", "section": section,
                           "figure": int(number_match.group(1)) if number_match else None,
                           "path": path, "alt": alt, "translation": caption or alt})
            i += 1
            continue
        if stripped.startswith("$$"):
            blocks.append({"id": nid("eq"), "type": "equation", "section": section,
                           "translation": stripped})
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            number = last_table
            for ahead in lines[i:i + 4]:
                found = table_number(ahead)
                if found:
                    number = found
                    break
            blocks.append({"id": nid("table"), "type": "table", "section": section,
                           "table": number, "translation": "\n".join(rows)})
            continue
        if stripped.startswith("**") and re.search(r"(?:图|表|Figure|Table)\s*[0-9]+", stripped):
            found = table_number(stripped)
            if found:
                last_table = found
            blocks.append({"id": nid("cap"), "type": "caption", "section": section,
                           "translation": stripped})
            i += 1
            continue
        if stripped.startswith("> "):
            items = []
            while i < len(lines) and lines[i].startswith("> "):
                items.append(lines[i][2:].strip())
                i += 1
            blocks.append({"id": nid("quote"), "type": "reference-note", "section": section,
                           "translation": "\n".join(items)})
            continue
        if line.startswith("- ") or re.match(r"^\d+\.\s", line):
            ordered = bool(re.match(r"^\d+\.\s", line))
            while i < len(lines):
                current = lines[i]
                if ordered and not re.match(r"^\d+\.\s", current):
                    break
                if not ordered and not current.startswith("- "):
                    break
                item = re.sub(r"^(?:- |\d+\.\s)", "", current).strip()
                blocks.append({"id": nid("li"), "type": "list-item", "section": section,
                               "translation": item, "ordered": ordered})
                i += 1
            continue
        blocks.append({"id": nid("p"), "type": "paragraph", "section": section,
                       "translation": stripped})
        i += 1

    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a stable translated-block inventory.")
    parser.add_argument("--translation", required=True, help="Path to the translated Markdown file.")
    parser.add_argument("--output", required=True, help="Path to write the inventory JSON.")
    args = parser.parse_args()

    source = Path(args.translation)
    blocks = parse(source.read_text(encoding="utf-8").splitlines())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(blocks, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter

    counts = Counter(block["type"] for block in blocks)
    print(f"Wrote {len(blocks)} blocks to {output}")
    print(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
