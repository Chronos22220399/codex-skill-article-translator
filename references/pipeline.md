# Deterministic Reader Pipeline

The goal of this pipeline is that **any competent model produces the same reader**.
The model's job is to fill structured data; the bundled scripts render and validate.
Do not hand-write the reader HTML, and do not invent new DOM ids or classes.

## End-to-end steps

1. **Extract the source.** Produce `source.md` plus `source-sections/` (or
   `source-pages/`) with stable block ids. Preserve equation/figure/table/citation
   numbers and section order.
2. **Translate into Markdown.** Keep `translation/<unit>.md` as the editable source
   of truth. Follow `glossary.md` and `style-guide.md`.
3. **Build the block inventory.**
   ```bash
   python scripts/make_inventory.py --translation translation/article-zh.md \
       --output translation-blocks.json
   ```
   This assigns stable ids (`h-001`, `p-042`, `eq-003`, `fig-001`, `table-002`, ...)
   and records figure/table numbers.
4. **Create the `alignment.json` skeleton, then fill the sources.**
   ```bash
   python scripts/make_alignment_skeleton.py --blocks translation-blocks.json \
       --output alignment.json
   ```
   This writes one record per block with a fixed shape. Then fill each `source` with
   the real source text (reconstructed from the extraction, not a summary label); for
   equations put the canonical LaTeX in `source`; set `table`/`figure` numbers where
   they are missing. Re-run with `--merge` after editing the translation to preserve
   already-filled sources.
5. **Create the supporting data:** `references.json`, `figure-map.json`,
   `glossary.md`, and (when a summary is wanted) `summary.md`.
6. **Build the reader.**
   ```bash
   python scripts/build_reader.py PROJECT_DIR \
       --title "..." --pdf ../original.pdf
   ```
   Default output is `PROJECT_DIR/translation-reading.html`.
7. **Validate.**
   ```bash
   python scripts/verify_translation_project.py PROJECT_DIR
   ```
   Fix every reported error before continuing.
8. **Independent review.** Run a separate review agent over the extraction and the
   translation (missing/duplicated/mistranslated/malformed content, terminology
   violations), fix what it finds, and record the outcome in `verification-report.md`.

## Data schemas

### `translation-blocks.json` (produced by `make_inventory.py`)

```json
[
  { "id": "h-001", "type": "heading", "level": 1, "section": "...", "translation": "..." },
  { "id": "p-004", "type": "paragraph", "section": "...", "translation": "..." },
  { "id": "eq-002", "type": "equation", "section": "...", "translation": "$$...$$" },
  { "id": "fig-001", "type": "figure", "figure": 1, "path": "assets/figures/fig-1.png",
    "section": "...", "translation": "**图 1：** ..." },
  { "id": "table-002", "type": "table", "table": 2, "section": "...", "translation": "| ... |" }
]
```

Allowed `type`: `heading`, `paragraph`, `equation`, `list-item`, `caption`, `table`,
`figure`, `code`, `reference-note`.

### `alignment.json` (required; the reader's primary index)

```json
[
  {
    "id": "p-004",
    "section": "3. Modeling Costs of MPC",
    "type": "paragraph",
    "source_ids": ["src-p-004"],
    "translation_ids": ["p-004"],
    "source": "CostCO treats MPC cost modeling as a quadratic regression problem. ...",
    "translation": "CostCO 把 MPC 成本建模视为二次回归问题。……",
    "notes": ""
  },
  {
    "id": "eq-002",
    "section": "2.2.4 Protocol Mixing",
    "type": "equation",
    "source": "$$P=\\{\\texttt{arith},\\texttt{bool},\\texttt{yao}\\}.$$",
    "translation": "$$P=\\{\\texttt{arith},\\texttt{bool},\\texttt{yao}\\}.$$",
    "notes": "LaTeX is language-neutral."
  }
]
```

Rules:

- `id` comes from `translation-blocks.json`; one record per visible block.
- `source` is the real source text. For `type: equation` it MUST be renderable LaTeX
  (with `$$...$$` or `\tag{...}` when numbered). Never use prose placeholders such as
  "Definitions of ..." or "formulas".
- Figure records: `type: "caption"` (or `"figure"`) with a numeric `figure` field.
- Table records: `type: "table"` with a numeric `table` field; `translation` holds the
  Markdown table that the builder converts to real HTML.

### `references.json`

```json
[ { "id": 1, "text": "Cosku Acay, ... In PLDI, 2021." }, { "id": 2, "text": "..." } ]
```

Keep bibliographic text in the original language. `id` is the citation number.

### `figure-map.json`

```json
[
  { "id": "fig-1", "figure": "Figure 1", "path": "assets/figures/figure-1-workflow.png",
    "caption_id": "fig-001", "html_anchor": "fig-1", "crop_status": "reviewed", "notes": "" }
]
```

- `path` is relative to the project root and MUST exist.
- Crop each figure to its own image at source resolution; never use a whole-page render.

### `glossary.md`

```markdown
| English term | Chinese rendering | Policy | Explanation | First seen |
|---|---|---|---|---|
| structure factor | 结构因子（structure factor） | translate-with-English | 描述点过程或散射强度的核心函数 S(k)。 | Sec. 2 |
```

The builder turns each row into a `term-<slug>` anchor and marks the first important
occurrence in the translation. The explanation is shown as
`English term（中文译文）：中文解释`.

### `summary.md`

A Markdown subset: headings, paragraphs, lists, `**bold**`, `$inline math$`,
`$$display math$$`, `[N]` citations, and `图 N` / `表 N` references. The builder
renders it behind the toolbar `总结` button.

## Rendering contract (fixed by the builder)

- Chinese mode is the default; the toolbar also offers parallel mode, terminology
  notes, summary, and back-to-top.
- Inline `图 N` / `表 N` become `#fig-N` / `#table-N` links with hover/focus tooltips.
- Inline `[N]` becomes a `#ref-N` link with the bibliographic title as tooltip.
- Jump targets get `.highlight-target`, which auto-clears and also clears on a click
  outside a link/target.
- Equations are `.pair.pair-eq` blocks with the LaTeX in `.source-left`; the verifier
  counts these against the `type: equation` records.
- Figure/table ids are `fig-N` / `table-N`; reference ids are `ref-N`.

See `references/reader-contract.md` for the full DOM/CSS/JS reference.
