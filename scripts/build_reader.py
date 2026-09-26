#!/usr/bin/env python3
"""Deterministically build the interactive reader from project data.

Models should NOT hand-write the reader HTML. They produce structured data and
this script renders the stable interactive reader:

Inputs (in the project directory):
    alignment.json   required  translated blocks as the primary index; records with
                              id/section/type/source/translation (+ optional table,
                              figure, level) plus optional source_ids/translation_ids/notes
    references.json  optional  [{"id": 1, "text": "..."}, ...]
    figure-map.json  optional  [{"id": "fig-1", "figure": "Figure 1", "path": "assets/figures/..."}]
    glossary.md      optional  | English term | Chinese rendering | Policy | Explanation | First seen |
    summary.md       optional  summary panel content (Markdown subset)

Output:
    <project>/translation-reading.html

Usage:
    python scripts/build_reader.py PROJECT_DIR
    python scripts/build_reader.py PROJECT_DIR --output translation-reading.html \
        --title "..." --pdf ../original.pdf
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

TERM_KEY_FALLBACK = re.compile(r"[\u4e00-\u9fff]{2,}")


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value).strip("-").lower() or "section"


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def load_references(project: Path) -> dict[int, str]:
    items = load_json(project / "references.json", [])
    refs: dict[int, str] = {}
    for item in items:
        if isinstance(item, dict) and "id" in item:
            refs[int(item["id"])] = item.get("text", "")
    return refs


def load_figure_paths(project: Path) -> dict[int, str]:
    paths: dict[int, str] = {}
    for item in load_json(project / "figure-map.json", []):
        match = re.search(r"([0-9]+)", str(item.get("figure", item.get("id", ""))))
        if match:
            paths[int(match.group(1))] = item.get("path", "")
    return paths


def load_terms(project: Path) -> list[dict]:
    path = project / "glossary.md"
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or "English term" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        english, chinese, policy, explanation = cells[0], cells[1], cells[2], cells[3]
        base = re.sub(r"（[^）]*）|\([^)]*\)", "", chinese).strip()
        key = base or english
        label = english
        if chinese.strip() != english:
            stripped = chinese.strip()
            if stripped.startswith(english):
                stripped = stripped[len(english):].strip().strip("（）() ").strip()
            label = f"{english}（{stripped}）" if stripped else english
        entries.append({
            "id": f"term-{slug(english)}",
            "key": key,
            "english": english,
            "note": f"{label}：{explanation}",
        })
    return entries


def is_figure(record: dict) -> bool:
    if record.get("type") == "figure" or record.get("figure") or record.get("asset"):
        return True
    rid = str(record.get("id", "")).lower()
    return record.get("type") == "caption" and "fig" in rid


def figure_number(record: dict) -> int | None:
    number = record.get("figure")
    if number:
        return int(number)
    zh = record.get("translation", "")
    if isinstance(zh, list):
        zh = " ".join(zh)
    match = re.search(r"(?:图|Figure)\s*([0-9]+)", zh)
    if match:
        return int(match.group(1))
    rid = str(record.get("id", ""))
    match = re.search(r"([0-9]+)", rid)
    return int(match.group(1)) if ("fig" in rid.lower() and match) else None


def table_number(record: dict) -> int | None:
    number = record.get("table")
    if number:
        return int(number)
    zh = record.get("translation", "")
    if isinstance(zh, list):
        zh = " ".join(zh)
    match = re.search(r"(?:表|Table)\s*([0-9]+)", record.get("section", "") + " " + zh)
    return int(match.group(1)) if match else None


def build_tooltip_maps(records: list[dict]) -> tuple[dict[int, str], dict[int, str]]:
    figures: dict[int, str] = {}
    tables: dict[int, str] = {}
    for record in records:
        translation = record.get("translation", "")
        if isinstance(translation, list):
            translation = " ".join(translation)
        source = record.get("source", "")
        if isinstance(source, list):
            source = " ".join(source)
        if is_figure(record):
            number = figure_number(record)
            if number:
                figures[number] = source or translation
        if record.get("type") == "table" or record.get("table"):
            number = table_number(record)
            if number:
                tables[number] = translation
    return figures, tables


def mark_terms(text: str, terms: list[dict], used: set[str]) -> str:
    """Mark the first occurrence of each term, never nesting inside another mark."""
    taken: list[tuple[int, int]] = []
    matches: list[tuple[int, int, str, str]] = []
    for term in terms:
        if term["id"] in used:
            continue
        key = term["key"]
        index = text.find(key)
        if index < 0:
            fallback = TERM_KEY_FALLBACK.search(key)
            if fallback:
                key = fallback.group(0)
                index = text.find(key)
        if index < 0:
            continue
        end = index + len(key)
        if any(not (end <= start or index >= stop) for start, stop in taken):
            continue
        taken.append((index, end))
        matches.append((index, end, term["id"], key))
        used.add(term["id"])
    for index, end, term_id, key in sorted(matches, reverse=True):
        text = f"{text[:index]}\x01TERM:{term_id}\x02{key}\x03/TERM\x04{text[end:]}"
    return text


def with_block_id(block: str, rid) -> str:
    """Attach a stable data-block-id to a block's first element.

    The id comes from the alignment record so client-side annotation anchors can
    reference a block that survives re-rendering.
    """
    rid = "" if rid is None else str(rid)
    if not rid or "data-block-id=" in block:
        return block
    match = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)\b", block)
    if not match:
        return block
    attr = f' data-block-id="{html.escape(rid, quote=True)}"'
    return block[: match.end()] + attr + block[match.end():]


class Renderer:
    def __init__(self, refs: dict[int, str], figures: dict[int, str],
                 tables: dict[int, str], terms: list[dict], figure_paths: dict[int, str]):
        self.refs = refs
        self.figures = figures
        self.tables = tables
        self.terms = terms
        self.figure_paths = figure_paths
        self.used_terms: set[str] = set()
        self.eq_counter = 0

    def inline(self, text: str, mark: bool = True) -> str:
        if mark:
            text = mark_terms(text, self.terms, self.used_terms)
        text = html.escape(text, quote=False)

        def detoken(match: re.Match[str]) -> str:
            term_id = match.group(1)
            return f'<a class="term term-ref" href="#{term_id}" data-term="{term_id}">{match.group(2)}</a>'

        def cite(match: re.Match[str]) -> str:
            parts = []
            for value in (int(v) for v in match.group(1).split(",")):
                if value in self.refs:
                    parts.append(
                        f'<a class="citation tooltip" href="#ref-{value}" '
                        f'data-tooltip="{html.escape(self.refs[value], quote=True)}">[{value}]</a>'
                    )
                else:
                    parts.append(f"[{value}]")
            return ", ".join(parts)

        text = re.sub(r"\x01TERM:([a-z0-9-]+)\x02(.*?)\x03/TERM\x04", detoken, text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
        text = re.sub(r"\[((?:[1-9]\d*)(?:,\s*[1-9]\d*)*)\]", cite, text)

        def figure(match: re.Match[str]) -> str:
            number = int(match.group(1))
            note = self.figures.get(number, f"图 {number}")
            return (f'<a class="asset-ref tooltip" href="#fig-{number}" '
                    f'data-tooltip="{html.escape(note, quote=True)}">图 {number}</a>')

        def table(match: re.Match[str]) -> str:
            number = int(match.group(1))
            note = self.tables.get(number, f"表 {number}")
            return (f'<a class="asset-ref tooltip" href="#table-{number}" '
                    f'data-tooltip="{html.escape(note, quote=True)}">表 {number}</a>')

        text = re.sub(r"图\s*([1-9][0-9]*)", figure, text)
        text = re.sub(r"表\s*([1-9][0-9]*)", table, text)
        return text

    def table_html(self, markdown: str, number: int | None) -> str:
        rows = []
        for line in markdown.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and not all(set(cell) <= {"-", ":", " "} for cell in cells):
                rows.append(cells)
        if not rows:
            return ""
        ident = f' id="table-{number}"' if number else ""
        out = [f'<div class="table-wrap span"{ident}><table><thead><tr>']
        header, body = rows[0], rows[1:]
        out.append("".join(f"<th>{self.inline(cell, mark=False)}</th>" for cell in header))
        out.append("</tr></thead><tbody>")
        for row in body:
            row = row + [""] * (len(header) - len(row))
            out.append("<tr>" + "".join(
                f"<td>{self.inline(cell, mark=False)}</td>" for cell in row[: len(header)]) + "</tr>")
        out.append("</tbody></table></div>")
        return "".join(out)

    def render(self, record: dict) -> tuple[str, dict | None]:
        rtype = record.get("type", "paragraph")
        zh = record.get("translation", "")
        en = record.get("source", "")
        rid = record.get("id", "block")
        if isinstance(zh, list):
            zh = " ".join(zh)
        if isinstance(en, list):
            en = " ".join(en)

        if rtype in ("title", "abstract", "heading"):
            level = record.get("level")
            if not level:
                level = 1 if rtype == "title" else 2
                if rtype == "heading":
                    if re.match(r"^\d+\.\d+\.\d+", zh):
                        level = 4
                    elif re.match(r"^\d+\.\d+", zh) or re.match(r"^[A-Z]\.\d", zh):
                        level = 3
            tag = {1: "h1", 2: "h2", 3: "h3", 4: "h4"}.get(level, "h4")
            ident = f"h-{rid}"
            block = (f'<div class="pair pair-heading" id="{ident}">'
                     f'<div class="source-left"><{tag}>{self.inline(en, mark=False)}</{tag}></div>'
                     f'<div class="translation-right"><{tag}>{self.inline(zh)}</{tag}></div></div>')
            if rtype == "title":
                return block, None
            return block, {"level": level, "id": ident, "title": zh}

        if rtype == "equation":
            ident = f"pair-eq-{self.eq_counter}"
            self.eq_counter += 1
            block = (f'<div class="pair pair-eq" id="{ident}">'
                     f'<div class="source-left eq">{html.escape(en or zh)}</div>'
                     f'<div class="translation-right eq">{html.escape(zh)}</div></div>')
            return block, None

        if is_figure(record):
            number = figure_number(record)
            path = self.figure_paths.get(number, record.get("asset", ""))
            caption = self.inline(zh)
            if number:
                caption = re.sub(
                    rf'<a class="asset-ref tooltip" href="#fig-{number}"[^>]*>图 {number}</a>',
                    f"图 {number}", caption)
            image = f'<img src="{html.escape(path, quote=True)}" alt="图 {number}">' if path else ""
            block = (f'<figure class="paper-figure span" id="fig-{number}">{image}'
                     f'<figcaption>{caption}</figcaption>'
                     f'<div class="source-caption">Source: {self.inline(en, mark=False)}</div></figure>')
            return block, None

        if rtype == "table":
            number = table_number(record)
            block = self.table_html(zh, number)
            if en:
                block += f'<div class="source-caption span-only">Source: {self.inline(en, mark=False)}</div>'
            return block, None

        if rtype == "caption":
            zh_html = self.inline(zh)
            match = re.search(r"表\s*([0-9]+)", zh)
            if match:
                number = match.group(1)
                zh_html = re.sub(
                    rf'<a class="asset-ref tooltip" href="#table-{number}"[^>]*>表 {number}</a>',
                    f"表 {number}", zh_html)
            block = (f'<div class="pair pair-caption">'
                     f'<div class="source-left">{self.inline(en, mark=False)}</div>'
                     f'<div class="translation-right">{zh_html}</div></div>')
            return block, None

        if rtype == "code":
            block = (f'<div class="pair pair-code">'
                     f'<div class="source-left"><pre><code>{html.escape(en or zh)}</code></pre></div>'
                     f'<div class="translation-right"><pre><code>{html.escape(zh)}</code></pre></div></div>')
            return block, None

        if rtype == "reference-note":
            block = (f'<div class="pair pair-note">'
                     f'<div class="source-left">{self.inline(en, mark=False)}</div>'
                     f'<div class="translation-right"><blockquote>{self.inline(zh)}</blockquote></div></div>')
            return block, None

        block = (f'<div class="pair pair-{rtype}">'
                 f'<div class="source-left"><p>{self.inline(en, mark=False)}</p></div>'
                 f'<div class="translation-right"><p>{self.inline(zh)}</p></div></div>')
        return block, None


def render_summary(markdown: str, renderer: Renderer) -> str:
    out: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append(f"<p>{renderer.inline(' '.join(paragraph), mark=False)}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_kind and items:
            tag = "ol" if list_kind == "ol" else "ul"
            out.append(f"<{tag}>" + "".join(
                f"<li>{renderer.inline(item, mark=False)}</li>" for item in items) + f"</{tag}>")
        items.clear()
        list_kind = None

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = min(len(heading.group(1)) + 1, 4)
            tag = {2: "h2", 3: "h3", 4: "h4"}.get(level, "h4")
            out.append(f"<{tag}>{renderer.inline(heading.group(2).strip(), mark=False)}</{tag}>")
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            if list_kind != "ul":
                flush_list()
                list_kind = "ul"
            items.append(bullet.group(1).strip())
            continue
        if ordered:
            flush_paragraph()
            if list_kind != "ol":
                flush_list()
                list_kind = "ol"
            items.append(ordered.group(1).strip())
            continue
        flush_list()
        paragraph.append(line.strip())
    flush_paragraph()
    flush_list()
    return "".join(out)


TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --ink:#1b2428; --muted:#607078; --line:#d8e0e2; --paper:#fff; --bg:#eef2f0; --accent:#0b6e59; --link:#075f87; --mark:#fff0ac; --soft:#f3f7f5; --src:#5b6b70; }
* { box-sizing:border-box; }
html { scroll-behavior:smooth; -webkit-text-size-adjust:100%; text-size-adjust:100%; }
body { margin:0; color:var(--ink); background:var(--bg); font:16px/1.78 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; overflow-wrap:break-word; -webkit-tap-highlight-color:transparent; }
.shell { max-width:1840px; margin:auto; display:grid; grid-template-columns:245px minmax(0,860px); gap:28px; align-items:start; justify-content:center; }
body.mode-parallel .shell { grid-template-columns:245px minmax(0,1280px); }
aside { position:sticky; top:0; height:100vh; overflow:auto; padding:24px 8px 24px 20px; }
aside strong { display:block; margin-bottom:14px; font-size:14px; color:var(--accent); }
.toc { display:flex; flex-direction:column; gap:4px; }
.toc a { display:block; padding:4px 8px; color:var(--muted); text-decoration:none; font-size:13px; line-height:1.45; }
.toc a:hover,.toc a.active { color:var(--accent); background:#e1eee9; }
.toc-3 { padding-left:20px !important; }
main { min-width:0; background:var(--paper); min-height:100vh; padding:30px clamp(20px,3vw,50px) 80px; box-shadow:0 0 0 1px rgba(0,0,0,.03); }
.toolbar { position:sticky; top:0; z-index:5; display:flex; gap:8px; flex-wrap:wrap; padding:8px 0 14px; background:linear-gradient(var(--paper) 80%, transparent); }
.toolbar button,.toolbar a { border:1px solid var(--line); padding:5px 10px; color:var(--link); text-decoration:none; font-size:13px; background:#fff; cursor:pointer; }
.toolbar button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
h1,h2,h3,h4 { line-height:1.25; letter-spacing:0; scroll-margin-top:80px; }
h1 { font-size:clamp(2rem,4vw,3.2rem); margin:28px 0 14px; max-width:820px; }
h2 { border-top:2px solid var(--ink); padding-top:14px; margin:52px 0 18px; font-size:1.65rem; }
h3 { margin:34px 0 10px; font-size:1.25rem; }
h4 { margin:25px 0 8px; font-size:1.06rem; }
p { margin:12px 0; }
/* Chinese body paragraphs indent two characters; source column and notes do not. */
.translation-right p, .summary p { text-indent:2em; }
body.mode-parallel .source-left p { text-indent:0; }
.pair-note .translation-right blockquote p, blockquote p, figcaption p, .glossary p { text-indent:0; }
a { color:var(--link); }
code { padding:1px 4px; background:#eef2f3; border-radius:3px; font:0.92em ui-monospace,SFMono-Regular,Menlo,monospace; }
pre { overflow:auto; padding:16px 18px; background:#1f2b30; color:#eef8f5; border-radius:5px; line-height:1.55; }
pre code { padding:0; background:transparent; border-radius:0; color:inherit; font:inherit; }
blockquote { margin:18px 0; padding:11px 16px; border-left:4px solid var(--accent); background:var(--soft); color:#33484d; }
ul,ol { padding-left:28px; }
li { margin:4px 0; }
.paper-figure { margin:28px 0; padding:12px 0; text-align:center; scroll-margin-top:84px; }
.paper-figure img { display:block; max-width:100%; height:auto; max-height:720px; margin:auto; }
.paper-figure figcaption { max-width:760px; margin:10px auto 0; color:var(--muted); font-size:14px; text-align:left; }
.source-caption { max-width:760px; margin:8px auto 0; color:var(--src); font-size:12.5px; text-align:left; }
.table-wrap { overflow-x:auto; margin:20px 0; scroll-margin-top:84px; }
table { width:100%; min-width:610px; border-collapse:collapse; font-size:14px; }
th,td { border:1px solid var(--line); padding:8px 9px; text-align:left; vertical-align:top; }
th { background:#eaf2ef; font-weight:700; }
.citation,.asset-ref,.term-ref { position:relative; text-decoration:none; border-bottom:1px dotted currentColor; }
.term-ref { border-bottom:1px dashed var(--accent); color:inherit; }
.term-ref:focus-visible,.term-ref:hover { background:#e1eee9; }
.tooltip::after { content:attr(data-tooltip); position:absolute; left:50%; bottom:calc(100% + 8px); transform:translateX(-50%); width:max-content; max-width:320px; padding:7px 9px; color:#fff; background:#25353a; border-radius:4px; font-size:12px; line-height:1.45; opacity:0; pointer-events:none; transition:opacity .12s; z-index:12; }
.tooltip:hover::after,.tooltip:focus-visible::after { opacity:1; }
.references-list { padding-left:38px; }
.references-list li { padding:6px 8px; scroll-margin-top:84px; }
.highlight-target { background:var(--mark); outline:2px solid #e0bd36; outline-offset:4px; }
.ref-number { color:var(--accent); font-weight:700; }
.muted { color:var(--muted); }
.summary { margin:0 0 30px; padding:18px 22px 22px; background:#f7faf9; border:1px solid var(--line); border-left:5px solid var(--accent); scroll-margin-top:80px; display:none; }
.summary.open { display:block; }
.summary h2 { border:0; margin:22px 0 8px; padding:0; font-size:1.18rem; }
.summary h3 { margin:16px 0 6px; font-size:1.04rem; }
.summary p { margin:8px 0; }
.summary ul,.summary ol { margin:8px 0; }
.summary li { margin:4px 0; }
.glossary { margin-top:40px; border-top:2px solid var(--ink); padding-top:12px; display:none; scroll-margin-top:80px; }
.glossary.open { display:block; }
.glossary h2 { border:0; margin-top:8px; }
.glossary dt { font-weight:700; margin-top:12px; scroll-margin-top:84px; }
.glossary dd { margin:4px 0 0; color:#33484d; }
body.mode-parallel .source-caption { display:block; }
body.mode-zh .source-caption { display:none; }
body.mode-zh .source-left { display:none; }
body.mode-parallel .pair { display:grid; grid-template-columns:1fr 1fr; gap:0 28px; align-items:start; border-top:1px solid #eef2f0; padding-top:6px; }
body.mode-parallel .pair .source-left { font-size:14.5px; color:var(--src); }
body.mode-parallel .pair .source-left h1 { font-size:1.9rem; }
body.mode-parallel .pair .source-left h2 { font-size:1.2rem; }
body.mode-parallel .pair .source-left h3 { font-size:1.02rem; }
body.mode-parallel .pair .source-left h4 { font-size:0.95rem; }
body.mode-parallel .pair .source-left p,body.mode-parallel .pair .translation-right p { margin:0 0 12px; }
.pair .source-left .eq,.pair .translation-right .eq { display:block; overflow-x:auto; }
body.mode-parallel .pair-eq { background:#fafcfb; }
body.mode-parallel .span { grid-column:1 / -1; }
.source-caption.span-only { display:none; }
body.mode-parallel .source-caption.span-only { display:block; }
@media (max-width:1280px) { .shell { gap:20px; } }
@media (max-width:1100px) { .shell, body.mode-parallel .shell { display:block; } aside { position:static; height:auto; padding:14px 18px 4px; } .toc { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:2px 12px; max-height:38vh; overflow:auto; } main { box-shadow:none; padding:18px clamp(14px,3vw,28px) 60px; } body.mode-parallel .pair { grid-template-columns:1fr; } }
@media (max-width:820px) { body { font-size:17px; } .toolbar { gap:6px; } .toolbar button, .toolbar a { padding:8px 12px; font-size:14px; } h1 { font-size:clamp(1.7rem,6vw,2.4rem); } h2 { font-size:1.4rem; } h3 { font-size:1.18rem; } .toc { grid-template-columns:1fr 1fr; } table { font-size:13px; min-width:520px; } .paper-figure img { max-height:none; } }
@media (max-width:560px) { body { font-size:16px; } .toc { display:block; max-height:200px; } table { font-size:12px; min-width:480px; } .summary { padding:14px 16px 18px; } }
@media print { body { background:#fff; } aside,.toolbar { display:none; } .shell { display:block; } main { padding:0; box-shadow:none; } .paper-figure,.table-wrap { break-inside:avoid; } a { color:inherit; text-decoration:none; } body.mode-zh .source-left { display:none; } }
</style>
<script>
window.MathJax = { tex: { inlineMath: [['$', '$'], ['\\(', '\\)']], displayMath: [['$$', '$$'], ['\\[', '\\]']], processEscapes: true, processEnvironments: true }, options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] } };
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body class="mode-zh">
<div class="shell">
<aside><strong>__SIDEBAR_TITLE__</strong><nav class="toc" aria-label="章节目录">__TOC__</nav></aside>
<main>
<div class="toolbar">
<button id="btn-summary" type="button">总结</button>
<button id="btn-zh" class="active" type="button">中文阅读</button>
<button id="btn-parallel" type="button">左右对照</button>
<button id="btn-glossary" type="button">术语说明</button>
<button id="btn-top" type="button">回到顶部</button>
<a href="__PDF__" target="_blank">打开原 PDF</a>
</div>
__SUMMARY__
__BODY__
__GLOSSARY__
__REFERENCES__
<p class="muted">译文源稿见项目内译文 Markdown；图像来自原 PDF 的裁切；参考文献保留原书目信息；数学公式使用 MathJax 渲染。</p>
</main></div>
<script>
function clearHighlights() { document.querySelectorAll('.highlight-target').forEach(el => el.classList.remove('highlight-target')); }
function highlightFromHash() { const id = location.hash.slice(1); if (!id) return; const target = document.getElementById(id); if (!target) return; clearHighlights(); target.classList.add('highlight-target'); setTimeout(() => target.classList.remove('highlight-target'), 4200); }
document.querySelectorAll('.citation,.asset-ref,.term-ref').forEach(link => link.addEventListener('click', () => setTimeout(highlightFromHash, 0)));
document.addEventListener('click', event => { if (!event.target.closest('.citation,.asset-ref,.term-ref,.references-list li,.paper-figure,.table-wrap,.glossary dt')) clearHighlights(); });
window.addEventListener('hashchange', highlightFromHash); highlightFromHash();
const tocLinks = [...document.querySelectorAll('.toc a')];
const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) tocLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id)); }), { rootMargin:'-20% 0px -70% 0px' });
document.querySelectorAll('h2[id],h3[id]').forEach(h => observer.observe(h));
const btnZh = document.getElementById('btn-zh');
const btnParallel = document.getElementById('btn-parallel');
function setMode(mode) { document.body.classList.toggle('mode-zh', mode === 'zh'); document.body.classList.toggle('mode-parallel', mode === 'parallel'); btnZh.classList.toggle('active', mode === 'zh'); btnParallel.classList.toggle('active', mode === 'parallel'); if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise(); }
btnZh.addEventListener('click', () => setMode('zh'));
btnParallel.addEventListener('click', () => setMode('parallel'));
const glossary = document.getElementById('glossary');
if (glossary) document.getElementById('btn-glossary').addEventListener('click', () => { glossary.classList.toggle('open'); if (glossary.classList.contains('open')) glossary.scrollIntoView({ behavior:'smooth', block:'start' }); });
const summary = document.getElementById('summary');
const btnSummary = document.getElementById('btn-summary');
if (summary) btnSummary.addEventListener('click', () => { const open = summary.classList.toggle('open'); btnSummary.classList.toggle('active', open); if (open) { summary.scrollIntoView({ behavior:'smooth', block:'start' }); if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise(); } });
document.getElementById('btn-top').addEventListener('click', () => window.scrollTo({ top:0, behavior:'smooth' }));
</script>
</body>
</html>
'''


def build(project: Path, output: str, title: str, pdf: str) -> Path:
    records = load_json(project / "alignment.json", [])
    if not isinstance(records, list):
        raise SystemExit("alignment.json must be a list of records")
    refs = load_references(project)
    figure_paths = load_figure_paths(project)
    terms = load_terms(project)
    figure_notes, table_notes = build_tooltip_maps(records)

    renderer = Renderer(refs, figure_notes, table_notes, terms, figure_paths)
    body: list[str] = []
    toc: list[dict] = []
    for record in records:
        block, toc_item = renderer.render(record)
        block = with_block_id(block, record.get("id", ""))
        body.append(block)
        if toc_item:
            toc.append(toc_item)

    toc_html = "".join(
        f'<a class="toc-{item["level"]}" href="#{item["id"]}">{html.escape(item["title"])}</a>'
        for item in toc if item["level"] in (2, 3)
    )

    summary_path = project / "summary.md"
    summary_html = ""
    if summary_path.exists():
        summary_html = ('<section class="summary" id="summary">'
                        + render_summary(summary_path.read_text(encoding="utf-8"), renderer)
                        + "</section>")

    glossary_html = ""
    if terms:
        glossary_html = ['<section class="glossary" id="glossary"><h2>术语说明</h2><dl>']
        for term in terms:
            glossary_html.append(f'<dt id="{term["id"]}">{html.escape(term["english"])}</dt>'
                                 f'<dd>{html.escape(term["note"])}</dd>')
        glossary_html.append("</dl></section>")
        glossary_html = "".join(glossary_html)

    ref_html = ""
    if refs:
        ref_html = ['<section id="references"><h2>参考文献</h2><ol class="references-list">']
        for number in sorted(refs):
            text = renderer.inline(refs[number], mark=False)
            ref_html.append(f'<li id="ref-{number}"><span class="ref-number">[{number}]</span> {text}</li>')
        ref_html.append("</ol></section>")
        ref_html = "".join(ref_html)

    document = (TEMPLATE
                .replace("__TITLE__", html.escape(title))
                .replace("__SIDEBAR_TITLE__", html.escape(title))
                .replace("__PDF__", html.escape(pdf, quote=True))
                .replace("__TOC__", toc_html)
                .replace("__SUMMARY__", summary_html)
                .replace("__BODY__", "".join(body))
                .replace("__GLOSSARY__", glossary_html)
                .replace("__REFERENCES__", ref_html))

    output_path = project / output
    output_path.write_text(document, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the interactive reader from project data.")
    parser.add_argument("project_dir", nargs="?", default=".", help="Translation project directory.")
    parser.add_argument("--output", default="translation-reading.html", help="Output HTML filename.")
    parser.add_argument("--title", default="", help="Reader title (defaults to the title record).")
    parser.add_argument("--pdf", default="", help="Relative path to the original PDF.")
    args = parser.parse_args()

    project = Path(args.project_dir).resolve()
    records = load_json(project / "alignment.json", [])
    title = args.title
    if not title:
        for record in records:
            if record.get("type") == "title":
                value = record.get("translation", "")
                title = value if isinstance(value, str) else " ".join(value)
                break
    if not title:
        title = project.name

    output_path = build(project, args.output, title, args.pdf)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
