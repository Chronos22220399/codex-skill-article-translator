# Paper Reader

[中文版本](README.zh-CN.md)

`paper_reader` is a skill for translating academic papers as reproducible translation projects, not as one-off text snippets, and for turning them into an interactive reader. It is a fork of [waiwaifeng/codex-skill-article-translator](https://github.com/waiwaifeng/codex-skill-article-translator) that adds interactive jump links, hover tooltips, highlight-on-jump, and a summary panel.

It is designed for PDFs, journal articles, reviews, theses, technical reports, and other long-form literature that contains equations, figures, captions, tables, citations, and specialized terminology.

This repository contains the skill instructions. It is not a standalone translation application.

## What It Does

- Translates long academic documents into polished Chinese while preserving technical accuracy.
- Keeps Markdown as the editable source of truth and generates reader-friendly outputs from it.
- Uses a default `full-reading-output` workflow instead of stopping at plain translated text.
- Maintains terminology decisions in `glossary.md` and writing conventions in `style-guide.md`.
- Preserves equations, symbols, equation labels, figure numbers, table numbers, citations, and section structure.
- Extracts or maps figures through `figure-map.json` and keeps captions as translatable text.
- Builds paragraph-level `alignment.json` for source-left / translation-right parallel reading.
- Generates reader-style HTML with MathJax support, table of contents, terminology notes, parallel mode, and print/PDF CSS.
- Makes figure, table, and citation mentions clickable: jump to the target, show a hover/focus tooltip, highlight the target, and clear the highlight when clicking elsewhere.
- Rebuilds source tables as real HTML tables and crops figures at source resolution, placing each at its first mention.
- Builds a `summary.md`-driven summary panel behind a top-toolbar `总结` button.
- Requires an independent review agent pass before completion.
- Ships a mechanical verification script for equation sources, parallel equation blocks, image references, term links, and MathJax configuration.
- Requires a final `verification-report.md` so each translation unit is auditable.

## Key Advantages

### Reproducible Translation Projects

The skill treats translation as a project with stable files and repeatable outputs:

```text
translation-project/
  source.md
  chapter-index.md
  glossary.md
  style-guide.md
  summary.md
  alignment.json
  figure-map.json
  verification-report.md
  source-pages/
  source-sections/
  translation/
  assets/
    images/
    figures/
    page-renders/
    previews/
```

This makes long translations easier to resume, review, correct, and regenerate across sessions.

### Academic Fidelity

The skill prioritizes technical accuracy over fluent paraphrase. It explicitly preserves:

- mathematical variables and symbols;
- Greek letters and super/subscripts;
- equation, figure, table, citation, and section numbers;
- captions as text rather than baked into images;
- source structure and paragraph-level alignment.

### Better Terminology Handling

Specialized terms are managed with a mixed Chinese-English policy:

- `keep-English`
- `keep-English-first`
- `translate-with-English`
- `translate`
- `keep-symbol`
- `review`

For key specialist terms, the translation keeps the complete English original at first or important occurrences. HTML output should make terms clickable and show explanations in this format:

```text
English term（中文译文）：中文解释
```

Example:

```text
structure factor（结构因子）：描述点过程或散射强度的核心函数 S(k)。
```

### Reliable Parallel Text

The skill avoids fragile block-order matching such as "Chinese block N = English PDF block N". Instead, it requires translation-led and anchor-based paragraph alignment:

- `alignment.json` is indexed by translated Markdown blocks.
- PDF extraction blocks are treated only as raw material.
- headings, equations, figures, captions, tables, and references are aligned by their own structural sources.
- representative sections must be spot-checked, not just counted.

This helps prevent source-left / translation-right mismatch in parallel HTML readers.

### Mechanical Verification

The bundled script checks common full-reading-output failure modes:

```powershell
python scripts\verify_translation_project.py path\to\translation-project
```

It verifies that `type: equation` records use real LaTeX/math source, `pair-eq-*` source-left blocks are not prose placeholders, equation counts match, image references exist, `term-*` links resolve, and MathJax is configured.

### Reader-Style HTML Output

The default HTML output is meant to be a paper reader, not a raw Markdown dump. It should support:

- a top toolbar with Summary (总结), Chinese reading, parallel mode, terminology notes, back-to-top, and open-PDF;
- Chinese reading mode;
- source-left / translation-right parallel mode;
- clickable terminology explanations formatted as `English term（中文译文）：中文解释`;
- a `summary.md`-driven summary panel covering problem, method, variants, key results, and limitations;
- clickable figure/table/citation mentions with hover/focus tooltips, highlight-on-jump, and click-elsewhere-to-clear;
- tables rebuilt as real HTML and figures cropped at source resolution;
- table of contents and section navigation;
- MathJax for inline and display formulas;
- relative image paths;
- responsive layout;
- print/PDF styling.

The concrete DOM id/class conventions and the jump/highlight JavaScript are documented in `references/reader-contract.md`.

## Repository Contents

```text
.
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/
│   └── openai.yaml
├── references/
│   └── reader-contract.md
└── scripts/
    ├── verify_translation_project.py
    └── test_verify_translation_project.py
```

- `SKILL.md` contains the main skill instructions.
- `agents/openai.yaml` contains OpenAI-facing display metadata and the default prompt.
- `references/reader-contract.md` documents the interactive reader DOM/class/JS conventions.
- `scripts/verify_translation_project.py` checks generated translation projects.
- `scripts/test_verify_translation_project.py` contains regression tests for the verifier.

## Installation

Clone or copy this repository into your local skills directory as `paper_reader`, for example as a global opencode skill:

```bash
git clone https://github.com/Chronos22220399/codex-skill-article-translator.git ~/code/skill/paper_reader
ln -s ~/code/skill/paper_reader ~/.config/opencode/skills/paper_reader
```

If you already have a skill with the same name, back it up before replacing it.

## Usage

Invoke the skill when working on an academic paper translation:

```text
Use $paper_reader in full-reading-output mode to translate this academic article, with interactive jump links, tooltips, highlight-on-jump, English/Chinese parallel mode, and a 总结 summary panel.
```

For cross-session continuation, ask the agent to read the existing project context first:

```text
Use $paper_reader and first read glossary.md, style-guide.md, chapter-index.md, summary.md, translation/, current reader HTML, alignment.json, and figure-map.json before continuing.
```

## Maintenance Notes

- Keep paper-specific content out of this skill. Put project-specific terminology, alignment, figures, and verification details inside the translation project.
- Update `SKILL.md` first when behavior changes.
- Update `agents/openai.yaml` when the default behavior for new sessions changes.
- After editing, validate the skill and check that the new rules are discoverable by keyword search.
