# Article Translator

`article_translator` is a Codex skill for translating academic papers as reproducible translation projects, not as one-off text snippets. It is designed for PDFs, journal articles, reviews, theses, technical reports, and other long-form literature that contains equations, figures, captions, tables, citations, and specialized terminology.

This repository contains the skill instructions for Codex. It is not a standalone translation application.

## What It Does

- Translates long academic documents into polished Chinese while preserving technical accuracy.
- Keeps Markdown as the editable source of truth and generates reader-friendly outputs from it.
- Uses a default `full-reading-output` workflow instead of stopping at plain translated text.
- Maintains terminology decisions in `glossary.md` and writing conventions in `style-guide.md`.
- Preserves equations, symbols, equation labels, figure numbers, table numbers, citations, and section structure.
- Extracts or maps figures through `figure-map.json` and keeps captions as translatable text.
- Builds paragraph-level `alignment.json` for source-left / translation-right parallel reading.
- Generates reader-style HTML with MathJax support, table of contents, terminology notes, parallel mode, and print/PDF CSS.
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

This makes long translations easier to resume, review, correct, and regenerate across Codex sessions.

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

### Reader-Style HTML Output

The default HTML output is meant to be a paper reader, not a raw Markdown dump. It should support:

- Chinese reading mode;
- source-left / translation-right parallel mode;
- clickable terminology explanations;
- table of contents and section navigation;
- MathJax for inline and display formulas;
- relative image paths;
- responsive layout;
- print/PDF styling.

## Repository Contents

```text
.
├── SKILL.md
└── agents/
    └── openai.yaml
```

- `SKILL.md` contains the main Codex skill instructions.
- `agents/openai.yaml` contains OpenAI-facing display metadata and the default prompt.

## Installation

Clone or copy this repository into your local Codex skills directory as `article_translator`:

```powershell
git clone https://github.com/waiwaifeng/codex-skill-article-translator.git C:\Users\歪歪风\.codex\skills\article_translator
```

If you already have a local `article_translator` skill, back it up before replacing it.

## Usage

In Codex, invoke the skill when working on an academic paper translation:

```text
Use $article_translator in full-reading-output mode to translate this academic article.
```

For cross-session continuation, ask Codex to read the existing project context first:

```text
Use $article_translator and first read glossary.md, style-guide.md, chapter-index.md, translation/, current reader HTML, alignment.json, and figure-map.json before continuing.
```

## Maintenance Notes

- Keep paper-specific content out of this skill. Put project-specific terminology, alignment, figures, and verification details inside the translation project.
- Update `SKILL.md` first when behavior changes.
- Update `agents/openai.yaml` when the default behavior for new sessions changes.
- After editing, validate the skill and check that the new rules are discoverable by keyword search.
