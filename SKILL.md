---
name: article_translator
description: Use when translating academic articles, long research papers, reviews, theses, PDFs, or literature with equations, figures, captions, section structure, terminology consistency, or HTML/PDF/DOCX reading output.
---

# Article Translator

## Overview

Translate academic literature as a reproducible project, not as one-off text chunks. Preserve technical meaning, mathematical notation, figures, captions, and section structure while producing a readable Chinese translation.

## When To Use

Use this skill for:

- Full-paper or chapter-by-chapter translation of PDFs, reviews, theses, arXiv papers, journal articles, and technical reports.
- Literature with equations, Greek symbols, superscripts/subscripts, figure captions, tables, references, or heavy terminology.
- Requests for readable outputs such as HTML, PDF, DOCX, or split Markdown translation files.
- Follow-up requests such as "translate the next chapter", "fix formulas", "add all figures", or "crop the figures".

Do not use this for short ordinary paragraphs unless the user wants a reusable literature translation workflow.

## Project Layout

For a PDF or long source document, create a project folder beside the source unless the user specifies another location:

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

Keep Markdown translation files as the editable source of truth. Generate HTML/PDF/DOCX from them for reading.

## Required Output Profile

Default mode is `full-reading-output`.

Unless the user explicitly requests `text-only`, do not finish with only Chinese translation text and a glossary. A completed long-article translation unit must update the translation source and the readable output.

Required deliverables for `full-reading-output`:

- Updated `translation/*.md` for the translated unit.
- Updated `glossary.md` when terminology decisions or explanations change.
- Updated `style-guide.md` when translation conventions change.
- Updated `alignment.json` for paragraph-level source/translation pairing.
- Updated reader-style HTML, normally `translation-reading.html`.
- Updated `figure-map.json` plus valid figure references and image assets for figures covered by the translated unit.
- MathJax or equivalent math rendering for inline and display formulas.
- A final verification report, normally `verification-report.md`, listing files changed, checks run, and any unresolved gaps.

If any required deliverable cannot be produced, do not silently downgrade to text-only. State the blocker, what remains incomplete, and what input or permission is needed.

Use `text-only` mode only when the user explicitly asks for plain translation without HTML, files, figures, or alignment. Even in `text-only`, preserve formulas, citations, and terminology decisions in the response.

## Workflow

1. Inspect the source file and identify title, abstract, table of contents, section boundaries, figures, tables, equations, and references.
2. Extract source text into page and section files. Preserve equation numbers, figure numbers, table numbers, citations, original section order, and stable paragraph/block ids.
3. Create or update `glossary.md` with key terms, translation policy, and short explanations for high-value specialist terms. Use consistent translations for recurring concepts and note uncertain terms.
4. Create or update `style-guide.md`: academic Chinese, faithful to original logic, no unexplained simplification, preserve symbols and equation labels.
5. Translate in manageable units, usually title/abstract first and then one chapter or section at a time.
6. When continuing a translation across Codex sessions, first read the existing project context: `glossary.md`, `style-guide.md`, `chapter-index.md`, completed files in `translation/`, the current reader HTML, and `figure-map.json` if present. Do not continue from memory alone.
7. Maintain `alignment.json` for paragraph-level source/translation pairing whenever original-vs-translation comparison is requested or useful for future review.
8. Maintain `figure-map.json` for each covered figure, including the figure number, source page or extraction source, final relative image path, caption block id, crop status, and unresolved issues.
9. After each unit, generate or update the readable HTML file unless the user explicitly requested `text-only`.
10. Verify formulas, figures, captions, links, alignment, required deliverables, and missing text before reporting completion.

## Translation Rules

- Preserve technical precision over fluency when there is tension.
- Keep equation labels, figure numbers, table numbers, citation numbers, and section numbers aligned with the source.
- Translate captions as text; do not bake translated captions into images.
- Do not translate variable names or mathematical symbols. Translate surrounding explanatory prose.
- Keep established English terms in parentheses on first important use when helpful, e.g. "超均匀性（hyperuniformity）".
- If a sentence is ambiguous, translate conservatively and optionally add a translator note only when the user asked for notes.

## Parallel Text Alignment

Use paragraph-level alignment for source-vs-translation comparison. This is the default comparison mode; sentence-level alignment is only for special review requests.

- Assign stable block ids during source extraction, e.g. `sec-03-p012`, `fig-04-caption`, `eq-058`.
- Use translated Markdown blocks as the primary output index for `alignment.json`; every visible translated block in the reader should have a corresponding alignment record when parallel mode is enabled.
- Keep translation blocks aligned to source blocks whenever possible, but never assume "Chinese block N = English extraction block N".
- Treat PDF extraction blocks as raw material only. Do not fill `source` by sequentially taking the next block from `blocks.json` or another PDF extraction stream.
- For PDF-derived sources, rebuild the English body flow before prose alignment: sort by page, column, vertical position, and horizontal position where available, then filter headers, DOI/journal metadata, authors, affiliations, figure captions, table text, footnotes, references, and other non-body noise.
- Align by block type: headings use section mappings; equations use equation ids or LaTeX source; figures, captions, tables, and reference notes use their own source streams; only ordinary prose paragraphs enter the body paragraph alignment flow.
- For prose paragraphs, use stable block ids, section anchors, paragraph-start anchor phrases, nearby citations/equation references, or structured parser output. If an anchor spans until the next body anchor, record that decision in `source_ids` and `notes`.
- If one source paragraph becomes multiple translation paragraphs, keep one alignment record with a translation array.
- If multiple source paragraphs must be merged, use a `source_ids` array and explain the merge in `notes`.
- Do not sacrifice translation quality just to force one sentence-to-one sentence alignment.
- Do not accept equal block counts as proof of alignment correctness. Count checks must be paired with content spot checks.

Recommended `alignment.json` shape:

```json
[
  {
    "id": "sec-03-p012",
    "section": "3. Local number fluctuations",
    "type": "paragraph",
    "source_ids": ["sec-03-p012"],
    "translation_ids": ["zh-sec-03-p012"],
    "source": "The structure factor S(k) ...",
    "translation": ["结构因子 S(k) ..."],
    "notes": ""
  },
  {
    "id": "fig-04-caption",
    "section": "2. Basic definitions",
    "type": "caption",
    "source_ids": ["fig-04-caption"],
    "translation_ids": ["zh-fig-04-caption"],
    "source": "Fig. 4. ...",
    "translation": ["图 4. ..."],
    "notes": "Caption aligned separately from the image."
  }
]
```

Allowed `type` values include `title`, `abstract`, `heading`, `paragraph`, `equation`, `caption`, `table`, `list-item`, and `reference-note`.

## Terminology Policy

Use a mixed Chinese-English terminology strategy when it improves accuracy.

- Keep English for domain terms whose Chinese translation would be misleading, uncommon, or less precise; author-defined terms; method/model names; abbreviations; and user-specified terms.
- Use Chinese plus English on first important mention for terms with stable Chinese translations that still benefit from anchoring, e.g. `结构因子（structure factor）`.
- For specialist terms marked `keep-English`, `keep-English-first`, or `translate-with-English`, preserve the complete English original in the translated text at first or important occurrences. Do not reduce the term to Chinese-only or acronym-only unless the source itself only uses the acronym after defining it.
- Use Chinese only for ordinary technical vocabulary with stable translations.
- Do not over-preserve English. If every sentence becomes bilingual, readability suffers.
- For kept-English or bilingual specialist terms, add a short explanation in `glossary.md` and, for HTML output, expose it through a clickable and keyboard-focusable term note.
- HTML term explanations must retain the English original and use this visible format: `English term（中文译文）：中文解释`.

Recommended `glossary.md` schema:

```markdown
| English term | Chinese rendering | Policy | Explanation | First seen |
|---|---|---|---|---|
| hyperuniformity | hyperuniformity / 超均匀性 | keep-English-first | 大尺度密度涨落异常受抑制的性质。 | Sec. 1 |
| structure factor | 结构因子（structure factor） | translate-with-English | 描述点过程或散射强度的核心函数 S(k)。 | Sec. 2 |
| stealthy hyperuniform systems | stealthy hyperuniform systems | keep-English | 在有限波数范围内 S(k)=0 的特殊超均匀体系。 | Sec. 3 |
```

When rendering glossary entries in HTML term notes, combine the English term, Chinese rendering, and explanation as `English term（中文译文）：中文解释`. For example: `structure factor（结构因子）：描述点过程或散射强度的核心函数 S(k)。`.

Policy values:

- `translate`: use a Chinese translation.
- `translate-with-English`: Chinese translation with English on first important use.
- `keep-English`: keep the English term in running text.
- `keep-English-first`: keep English in key contexts and optionally include Chinese explanation nearby.
- `keep-symbol`: keep mathematical notation or variables unchanged.
- `review`: uncertain; preserve original and flag for later review.

## Math Rules

Mathematical fidelity is a hard requirement.

- Render Greek letters as symbols when the source uses symbols: `sigma` -> `σ`, `rho` -> `ρ`, `phi` -> `φ`, etc.
- Preserve superscripts and subscripts: `σ_N^2(R)` should render as `σ<sub>N</sub><sup>2</sup>(R)` or equivalent HTML/MathJax.
- Preserve operators and relation symbols: `≤`, `≥`, `≈`, `∼`, `→`, `∞`, `∫`, `∑`, `∂`.
- Prefer MathJax/LaTeX for complex formulas when available. If using custom HTML rendering, test Greek symbols and nested super/subscripts explicitly.
- When generating HTML with MathJax, configure TeX inline delimiters explicitly. MathJax does not always process `$...$` by default in every setup.
- Include MathJax configuration before the MathJax script, for example:

```html
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
  }
};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
```

- If HTML must work offline, bundle the MathJax asset locally or use a non-CDN renderer; do not silently fall back to showing raw `$...$`.
- Do not leave ASCII placeholders such as `sigma_N^2` in final reading output unless the original source literally uses that text.

## Figure Rules

All figures referenced by translated content must be present.

- Prefer extracting original embedded images from the PDF when they are complete and high quality.
- If direct extraction misses vector graphics or split image objects, render pages and crop figures manually or by script.
- Maintain `figure-map.json` so each figure number maps to its final relative asset path, caption/alignment id, extraction or crop source, and review status.
- Never use a whole-page screenshot as the final figure unless the user explicitly accepts it.
- Crop each figure as an independent image containing only the figure artwork, in-figure labels, axes, panel letters, arrows, and legends.
- Do not crop body text or `Fig. ...` caption text into the image. Captions belong in translated text.
- For multi-panel figures, keep panels together when the original treats them as one numbered figure.
- Generate a contact sheet or preview when cropping many figures, then inspect it before rebuilding output.

## Readable Layout Profile

The HTML output should be a paper reader, not a raw Markdown dump.

Default layout requirements:

- A top toolbar with mode controls such as Chinese reading, parallel source/translation, terminology notes, table of contents, and optional PDF export.
- A constrained main reading column for Chinese mode, usually `760-860px` wide on desktop.
- Chinese body text around `17-18px` with `1.75-1.9` line height.
- Clear vertical spacing around headings, paragraphs, equations, figures, captions, and tables.
- A left navigation area or collapsible table of contents for section jumps on long documents.
- A right terminology/notes panel on wide desktop screens when not in parallel mode.
- Responsive behavior: on narrow screens, collapse navigation and notes rather than squeezing the text.
- Print/PDF CSS so exported PDF pages keep readable margins, figure scaling, and formula overflow handling.

Visual rules:

- Keep the design quiet and reading-focused. Avoid decorative hero sections, oversized title treatments, gradients, nested cards, and dense bordered boxes.
- Use a neutral page background with high-contrast text and restrained accent color for links, active navigation, and terminology markers.
- Do not let formulas, figures, captions, or term notes overlap. Long equations should be horizontally scrollable if needed.
- Figures should be centered, scale to available width, and keep captions as separate text.
- In parallel mode, use two balanced columns: source on the left, translation on the right. Keep term notes as hover/focus notes, overlays, or collapsible panels instead of adding a fixed third column.
- Provide a quick way to switch between reading mode and parallel mode without regenerating the file when practical.

## HTML Reading Output

When the user wants HTML:

- Build a single readable HTML file from translated Markdown sections.
- Support a Chinese reading mode and a paragraph-level parallel mode when `alignment.json` exists.
- In parallel mode, render source text on the left and Chinese translation on the right, paired by `alignment.json` records.
- Keep each aligned pair in a shared block so scrolling preserves source/translation proximity.
- If source-left and translation-right content do not correspond, first inspect and regenerate `alignment.json`; the HTML renderer is usually only reflecting the alignment data it was given.
- For equations, figures, and tables, align by block id and avoid duplicating large images in both columns unless the user asks for it.
- Render kept-English or bilingual specialist terms as clickable and keyboard-focusable anchors in the translated text. Activating a term should jump to, scroll to, or reveal its Chinese explanation.
- Term note targets should have stable ids derived from glossary entries, e.g. `term-structure-factor`, so repeated occurrences link to the same explanation.
- When parallel mode is active, term explanations should become clickable/focus notes, an overlay, or a collapsible panel rather than a fixed third column.
- Keep source order and section navigation clear.
- Insert figure blocks near their translated captions.
- For kept-English or bilingual specialist terms, support a right-side explanation area on desktop. Keep explanations concise, usually 1-3 sentences, and show them only for first or important occurrences.
- Display term explanations as `English term（中文译文）：中文解释`, preserving the English original in the explanation label.
- On narrow screens, collapse term explanations below the paragraph or behind accessible hover/focus details instead of forcing a side column.
- Use relative image paths so the HTML works inside the project folder.
- Ensure CSS does not hide long formulas, crop images, or cause captions to overlap.
- Ensure term notes do not crowd formulas, figures, or captions.
- Apply the Readable Layout Profile; do not ship a plain unstyled Markdown-to-HTML dump as the main reading output.
- Rebuild HTML after any figure-map, translation, or formula-rendering change.

## Verification Checklist

Before saying a chapter or output is complete, verify:

- The active output profile is clear: `full-reading-output` by default, or explicit user-requested `text-only`.
- In `full-reading-output`, the result is not only Chinese translation text plus `glossary.md`.
- Updated deliverables exist as applicable: `translation/*.md`, `glossary.md`, `style-guide.md`, `alignment.json`, `figure-map.json`, reader-style HTML, figure assets, and `verification-report.md`.
- HTML applies the Readable Layout Profile: top toolbar, readable text width, table of contents/navigation, terminology notes behavior, responsive layout, and print/PDF CSS.
- The translated section exists and follows the source section boundaries.
- For cross-session continuation, existing `glossary.md`, `style-guide.md`, `chapter-index.md`, completed translation files, current reader HTML, and `figure-map.json` if present were read before translating.
- If parallel comparison is enabled, `alignment.json` exists and includes records for all translated source blocks in the completed section.
- Each alignment record has stable `id`, `source_ids`, `translation_ids`, `source`, `translation`, `section`, and `type` fields.
- `alignment.json` is indexed by translated Markdown blocks, not by raw PDF extraction order.
- PDF extraction noise such as page headers, DOI/journal metadata, authors, affiliations, captions, tables, footnotes, and references was filtered or routed into the correct non-body block type before prose alignment.
- Headings, equations, figures, captions, tables, and reference notes were aligned by their own structural sources instead of being consumed from the prose paragraph stream.
- HTML parallel mode renders source-left and translation-right from `alignment.json` without losing formulas, captions, or figure/table references.
- Representative alignment spot checks pass across the document, including abstract, introduction, at least one core technical section, conclusion or discussion, and back matter such as conflicts of interest, acknowledgements, or references when present.
- Specialist terms marked `keep-English`, `keep-English-first`, or `translate-with-English` in `glossary.md` are handled consistently in the translated text.
- Specialist terms marked `keep-English`, `keep-English-first`, or `translate-with-English` preserve the complete English original at first or important occurrences, not only the Chinese rendering or an acronym.
- Kept-English specialist terms have concise explanations in `glossary.md`, and HTML term notes appear only at first or important occurrences.
- HTML specialist terms are clickable and keyboard-focusable, and activation jumps to, scrolls to, or reveals the matching Chinese explanation.
- HTML term explanations use the format `English term（中文译文）：中文解释` and keep the English original visible in the explanation label.
- No obvious untranslated English paragraphs remain except citations, names, references, or requested bilingual terms.
- Greek symbols and super/subscripts render correctly in the reading output.
- HTML using MathJax includes explicit `inlineMath` configuration for `$...$` and `\(...\)` delimiters before loading MathJax.
- Rendered HTML does not visibly show raw inline math delimiters such as `$S(k)$` or `$...$` in prose.
- Every figure number used in the translated chapters has an image.
- `figure-map.json` maps every covered figure number to a final relative image path and caption/alignment id, with any unresolved crop or extraction issue recorded.
- HTML image paths point to final figure files, not temporary whole-page renders.
- Figure images do not include body text or figure captions.
- Captions are present as translated text.
- Tables, equation numbers, and citation markers remain aligned with the source.

Report any unresolved uncertainty directly instead of silently guessing.
