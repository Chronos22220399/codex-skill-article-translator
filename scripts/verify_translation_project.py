#!/usr/bin/env python3
"""Mechanical checks for article_translator full-reading-output projects."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


PLACEHOLDER_PHRASES = (
    "definitions of",
    "angular-averaged",
    "volume-fraction variance",
    "formula",
    "formulas",
)

MATH_PATTERN = re.compile(
    r"(\$\$.*?\$\$|\$[^$]+\$|\\\(.*?\\\)|\\\[.*?\\\]|\\begin\{[^}]+\}|\\tag\{[^}]+\}|"
    r"\\(?:frac|sum|int|prod|sqrt|left|right|partial|alpha|beta|gamma|delta|sigma|rho|phi|theta|mu|chi|mathbf|mathrm|mathcal)\b|"
    r"[A-Za-z0-9)}\]]\s*(?:=|<|>|≤|≥|≈|\\le|\\ge|\\sim)\s*[A-Za-z0-9({\[]|[\^_∫∑∞≤≥≈→])",
    re.DOTALL,
)

DISPLAY_MATH_PATTERN = re.compile(
    r"(\$\$.*?\$\$|\\\[.*?\\\]|\\begin\{[^}]+\}|\\tag\{[^}]+\})",
    re.DOTALL,
)


def flatten_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(flatten_text(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def strip_tags(raw_html: str) -> str:
    text = re.sub(r"<script\b.*?</script>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style\b.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def has_placeholder_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in PLACEHOLDER_PHRASES)


def looks_like_renderable_math(text: str) -> bool:
    return bool(MATH_PATTERN.search(text or ""))


def count_visible_formula_units(text: str) -> int:
    text = text or ""
    display_count = len(DISPLAY_MATH_PATTERN.findall(text))
    if display_count:
        return display_count
    return 1 if looks_like_renderable_math(text) else 0


def load_alignment(project_dir: Path, errors: list[str]) -> list[dict]:
    alignment_path = project_dir / "alignment.json"
    if not alignment_path.exists():
        errors.append("alignment.json is missing")
        return []
    try:
        data = json.loads(alignment_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"alignment.json is invalid JSON: {exc}")
        return []
    if not isinstance(data, list):
        errors.append("alignment.json must be a list of alignment records")
        return []
    return [record for record in data if isinstance(record, dict)]


def verify_equation_records(records: list[dict]) -> list[str]:
    errors = []
    for record in records:
        if str(record.get("type", "")).lower() != "equation":
            continue
        record_id = record.get("id", "<missing-id>")
        source = flatten_text(record.get("source")).strip()
        translation = flatten_text(record.get("translation")).strip()

        if not source:
            errors.append(f"{record_id}: equation source is empty")
            continue
        if has_placeholder_phrase(source):
            errors.append(f"{record_id}: equation source appears to be a prose placeholder: {source[:120]}")
        if not looks_like_renderable_math(source):
            errors.append(f"{record_id}: equation source does not contain renderable LaTeX/math")

        source_units = count_visible_formula_units(source)
        translation_units = count_visible_formula_units(translation)
        if translation_units and source_units < translation_units:
            errors.append(
                f"{record_id}: equation source has fewer formula units ({source_units}) than translation ({translation_units})"
            )
    return errors


def find_html_files(project_dir: Path, explicit_html: str | None) -> list[Path]:
    if explicit_html:
        return [Path(explicit_html)]
    preferred = [
        project_dir / "translation-reading.html",
        project_dir / "zh_parallel.html",
    ]
    found = [path for path in preferred if path.exists()]
    if found:
        return found
    return sorted(project_dir.glob("*.html"))


def extract_pair_eq_blocks(raw_html: str) -> dict[str, str]:
    pair_matches = list(re.finditer(r'(?:id|data-[\w-]+)=["\'](pair-eq-[^"\']+)["\']', raw_html))
    blocks = {}
    for index, match in enumerate(pair_matches):
        pair_id = match.group(1)
        if pair_id in blocks:
            continue
        start = max(raw_html.rfind("<div", 0, match.start()), raw_html.rfind("<section", 0, match.start()), 0)
        next_start = len(raw_html)
        for next_match in pair_matches[index + 1 :]:
            if next_match.group(1) != pair_id:
                next_start = next_match.start()
                break
        blocks[pair_id] = raw_html[start:next_start]
    return blocks


def extract_source_left_text(block_html: str) -> str:
    match = re.search(
        r'<(?P<tag>[a-zA-Z0-9]+)[^>]*class=["\'][^"\']*\bsource-left\b[^"\']*["\'][^>]*>(?P<body>.*?)</(?P=tag)>',
        block_html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return ""
    return strip_tags(match.group("body"))


def verify_mathjax(raw_html: str, html_path: Path) -> list[str]:
    errors = []
    if "window.MathJax" not in raw_html:
        errors.append(f"{html_path.name}: MathJax configuration is missing")
    if "inlineMath" not in raw_html:
        errors.append(f"{html_path.name}: MathJax inlineMath configuration is missing")
    if "['$', '$']" not in raw_html and '["$", "$"]' not in raw_html:
        errors.append(f"{html_path.name}: MathJax inlineMath does not include $...$ delimiters")
    if "\\\\(" not in raw_html and "\\(" not in raw_html:
        errors.append(f"{html_path.name}: MathJax inlineMath does not include \\(...\\) delimiters")
    return errors


def verify_images(raw_html: str, project_dir: Path, html_path: Path) -> list[str]:
    errors = []
    for src in re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', raw_html, flags=re.IGNORECASE):
        if re.match(r"^(https?:|data:|mailto:)", src, flags=re.IGNORECASE):
            continue
        clean_src = unquote(src.split("?", 1)[0].split("#", 1)[0])
        if not (html_path.parent / clean_src).exists() and not (project_dir / clean_src).exists():
            errors.append(f"{html_path.name}: image reference is missing: {src}")
    return errors


def verify_term_links(raw_html: str, html_path: Path) -> list[str]:
    errors = []
    href_targets = set(re.findall(r'href=["\']#(term-[^"\']+)["\']', raw_html, flags=re.IGNORECASE))
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', raw_html, flags=re.IGNORECASE))
    names = set(re.findall(r'\bname=["\']([^"\']+)["\']', raw_html, flags=re.IGNORECASE))
    available = ids | names
    for target in sorted(href_targets):
        if target not in available:
            errors.append(f"{html_path.name}: term href #{target} has no matching id/name target")
    return errors


def verify_pair_equations(raw_html: str, equation_count: int, html_path: Path) -> list[str]:
    errors = []
    pair_blocks = extract_pair_eq_blocks(raw_html)
    if len(pair_blocks) != equation_count:
        errors.append(
            f"{html_path.name}: pair-eq-* block count ({len(pair_blocks)}) does not match alignment equation records ({equation_count})"
        )
    for pair_id, block in sorted(pair_blocks.items()):
        source_left = extract_source_left_text(block)
        if not source_left:
            errors.append(f"{html_path.name} {pair_id}: source-left equation block is missing")
            continue
        if has_placeholder_phrase(source_left):
            errors.append(f"{html_path.name} {pair_id}: source-left equation appears to be a prose placeholder")
        if not looks_like_renderable_math(source_left):
            errors.append(f"{html_path.name} {pair_id}: source-left equation does not contain renderable LaTeX/math")
    return errors


def verify_html(project_dir: Path, html_path: Path, equation_count: int) -> list[str]:
    errors = []
    if not html_path.exists():
        return [f"HTML file is missing: {html_path}"]
    raw_html = html_path.read_text(encoding="utf-8")
    errors.extend(verify_mathjax(raw_html, html_path))
    errors.extend(verify_pair_equations(raw_html, equation_count, html_path))
    errors.extend(verify_images(raw_html, project_dir, html_path))
    errors.extend(verify_term_links(raw_html, html_path))
    return errors


def verify_project(project_dir: str | Path, html_path: str | None = None) -> list[str]:
    project_dir = Path(project_dir)
    errors = []
    records = load_alignment(project_dir, errors)
    equation_records = [record for record in records if str(record.get("type", "")).lower() == "equation"]
    errors.extend(verify_equation_records(records))

    html_files = find_html_files(project_dir, html_path)
    if not html_files:
        errors.append("No HTML reading output found")
    for path in html_files:
        if not path.is_absolute():
            path = project_dir / path
        errors.extend(verify_html(project_dir, path, len(equation_records)))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify article_translator full-reading-output project files.")
    parser.add_argument("project_dir", help="Translation project directory containing alignment.json and HTML output.")
    parser.add_argument("--html", help="Optional HTML file path to check instead of auto-discovery.")
    args = parser.parse_args(argv)

    errors = verify_project(args.project_dir, args.html)
    if errors:
        print("Verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
