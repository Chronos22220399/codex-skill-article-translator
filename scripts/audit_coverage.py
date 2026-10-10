#!/usr/bin/env python3
"""Check that the translation actually covers the source.

The whole point of this skill is that nothing gets dropped. But the renderer only
checks structure, so a translation that quietly compresses half a paper still
"passes". This script is the missing coverage check.

What it can catch reliably:
  - the translation is far shorter than the source (a whole section got summarized);
  - the source has equations but the translation has none;
  - a numbered table / figure / protocol / algorithm is in the source but missing
    from the translation.

What it can NOT catch: a single dropped sentence, or a formula that got silently
rewritten. Those are the independent review's job. This script is a net, not a
proof.

Usage:
    python scripts/audit_coverage.py --source source.md \
        --translation translation/article-zh.md \
        --output coverage-report.md

Exit code is non-zero when a hard gap is found.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TABLE_LABEL = re.compile(r"\b(?:TABLE|Table|Tab\.)\s+([IVXLC]+|\d+)\b")
FIGURE_LABEL = re.compile(r"\b(?:Fig\.?|Figure)\s+(\d+)\b", re.IGNORECASE)
# Captions are the reliable signal. Matching every inline "protocol 2" phrase
# creates false positives when a PDF line break turns "mixed-protocol" and
# "2-party" into a fake label.
PROTOCOL_LABEL = re.compile(
    r"(?:^|\n)\s*\**(?:Protocol|Listing|Algorithm)\s+(\d+)\b", re.IGNORECASE
)

CJK = re.compile(r"[\u4e00-\u9fff]")
WORD = re.compile(r"[A-Za-z0-9]+")
MATHY = re.compile(r"[=≡≈≤≥⊕∧∑∈]|\\[a-zA-Z]+|\bpmod\b|\bmod\b|[⟨⟩σℓκφ]|_\{")

# Scale ratio = (CJK chars + latin words) in the translation / source words.
# Chinese packs more meaning per word, so a faithful translation usually lands
# around 1.2-1.8. Way below that means someone summarized.
RATIO_HARD = 0.8
RATIO_WARN = 1.05


def roman_to_int(value: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = prev = 0
    for char in reversed(value.upper()):
        current = values.get(char, 0)
        if current < prev:
            total -= current
        else:
            total += current
            prev = current
    return total


def numbers(text: str, pattern: re.Pattern) -> set[int]:
    found: set[int] = set()
    for raw in pattern.findall(text):
        found.add(roman_to_int(raw) if raw.isalpha() else int(raw))
    return found


def read_translation(path: Path) -> str:
    if path.is_dir():
        return "\n\n".join(
            f.read_text(encoding="utf-8") for f in sorted(path.glob("*.md"))
        )
    return path.read_text(encoding="utf-8")


def source_stats(source: str) -> dict:
    return {
        "words": len(WORD.findall(source)),
        "tables": numbers(source, TABLE_LABEL),
        "figures": numbers(source, FIGURE_LABEL),
        "protocols": numbers(source, PROTOCOL_LABEL),
        "has_math": bool(MATHY.search(source)),
    }


def translation_stats(text: str) -> dict:
    tables = {int(n) for n in re.findall(r"表\s*(\d+)", text)}
    figures = {int(n) for n in re.findall(r"图\s*(\d+)", text)}
    protocols = {
        int(n)
        for n in re.findall(
            r"(?:协议|算法|清单|代码清单|Listing|Algorithm)\s*(\d+)", text
        )
    }
    table_blocks = len(
        re.findall(r"^\s*\|?[\s:|-]*-{3,}[\s:|-]*\|?\s*$", text, re.MULTILINE)
    )
    return {
        "units": len(CJK.findall(text)) + len(WORD.findall(text)),
        "proxy_cjk": len(CJK.findall(text)),
        "display_equations": text.count("$$") // 2,
        "tables": tables,
        "table_blocks": table_blocks,
        "figures": figures,
        "protocols": protocols,
        "headings": len(re.findall(r"^#{1,6}\s+\S", text, re.MULTILINE)),
    }


def shortfall(
    label: str, source_numbers: set[int], trans_numbers: set[int], trans_blocks: int = 0
) -> list[str]:
    if not source_numbers:
        return []
    missing = sorted(source_numbers - trans_numbers)
    if missing:
        shown = "、".join(str(n) for n in missing)
        return [f"{label}缺少编号：{shown}（原文有、译文没提到）"]
    return []


def compare(
    source_path: Path, translation_path: Path
) -> tuple[dict, dict, float, list[str], list[str]]:
    source = source_path.read_text(encoding="utf-8")
    translation = read_translation(translation_path)
    src = source_stats(source)
    trans = translation_stats(translation)
    errors: list[str] = []
    warnings: list[str] = []

    ratio = trans["units"] / max(src["words"], 1)

    if src["has_math"] and trans["display_equations"] == 0:
        errors.append("原文含公式，但译文里没有任何独立公式块（$$...$$）")

    if ratio < RATIO_HARD:
        errors.append(
            f"译文篇幅明显偏短：字符/词比 {ratio:.2f}（硬性下限 {RATIO_HARD}），疑似整段被压缩"
        )
    elif ratio < RATIO_WARN:
        warnings.append(
            f"译文篇幅偏短：字符/词比 {ratio:.2f}（参考值 {RATIO_WARN}），请核对是否漏译"
        )

    warnings += shortfall("表格", src["tables"], trans["tables"])
    warnings += shortfall("图", src["figures"], trans["figures"])
    warnings += shortfall("协议/算法", src["protocols"], trans["protocols"])

    return src, trans, ratio, errors, warnings


def write_report(
    output: Path,
    source_path: Path,
    translation_path: Path,
    src,
    trans,
    ratio,
    errors,
    warnings,
) -> None:
    lines = [
        "# 覆盖审计报告（Coverage Audit）",
        "",
        f"- 原文：`{source_path}`",
        f"- 译文：`{translation_path}`",
        "",
        "## 规模对比",
        "",
        "| 项目 | 原文 | 译文 |",
        "|---|---:|---:|",
        f"| 词数（原文）/ 加权字符数（译文） | {src['words']} | {trans['units']} |",
        f"| 篇幅比（译/原） | - | {ratio:.2f} |",
        f"| 标题数 | - | {trans['headings']} |",
        f"| 独立公式块 | 含公式：{'是' if src['has_math'] else '否'} | {trans['display_equations']} |",
        f"| 表格编号 | {len(src['tables'])} | {len(trans['tables'])} |",
        f"| 图编号 | {len(src['figures'])} | {len(trans['figures'])} |",
        f"| 协议/算法编号 | {len(src['protocols'])} | {len(trans['protocols'])} |",
        "",
    ]
    if errors:
        lines += ["## 硬性缺口（必须修复）", ""]
        lines += [f"- {item}" for item in errors]
        lines += [""]
    if warnings:
        lines += ["## 需要人工复核", ""]
        lines += [f"- {item}" for item in warnings]
        lines += [""]
    if not errors and not warnings:
        lines += ["未发现明显缺口。", ""]
    lines += [
        "> 这是启发式检查：能发现「整段/公式/表/图整体缺失」，但不能替代逐节人工或独立评审。",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit translation coverage against the source."
    )
    parser.add_argument(
        "--source", required=True, help="Extracted source Markdown (source.md)."
    )
    parser.add_argument(
        "--translation", required=True, help="Translated Markdown file or directory."
    )
    parser.add_argument("--output", help="Write a coverage-report.md to this path.")
    args = parser.parse_args()

    source_path = Path(args.source)
    translation_path = Path(args.translation)
    src, trans, ratio, errors, warnings = compare(source_path, translation_path)

    if args.output:
        write_report(
            Path(args.output),
            source_path,
            translation_path,
            src,
            trans,
            ratio,
            errors,
            warnings,
        )

    for item in warnings:
        print(f"  warning: {item}")
    if errors:
        print("Coverage audit failed:")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"Coverage audit passed (scale ratio {ratio:.2f}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
