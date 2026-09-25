# Interactive Reader Contract: Implementation Reference

This file is the concrete implementation of the **Interactive Reader Contract** in
`SKILL.md`. It fixes the DOM ids, classes, and JavaScript behaviors so a reader
generated in one session looks and behaves the same in the next. Adjust styling
freely, but keep the ids and behaviors stable — the verification script and the
skill checklist depend on them.

## Stable DOM ids and classes

| Purpose | Convention | Example |
|---|---|---|
| Figure block | `id="fig-<n>"`, class `paper-figure` | `<figure class="paper-figure" id="fig-1">` |
| Figure caption | text inside `<figcaption>` | `<figcaption>图 1：...</figcaption>` |
| Table block | `id="table-<n>"`, class `table-wrap` | `<div class="table-wrap" id="table-2"><table>...` |
| Table caption | pair block rendered next to the table | `<div class="pair pair-caption">` |
| Reference entry | `id="ref-<n>"` | `<li id="ref-25">...` |
| Term explanation target | `id="term-<slug>"` | `<dt id="term-share-assignment">...` |
| Alignment equation pair | `id="pair-eq-<i>"` | `<div class="pair pair-eq" id="pair-eq-0">` |
| Inline citation | class `citation tooltip`, `href="#ref-n"`, `data-tooltip` | `<a class="citation tooltip" href="#ref-25" data-tooltip="...">[25]</a>` |
| Inline asset reference | class `asset-ref tooltip`, `href="#fig-n"` / `#table-n` | `<a class="asset-ref tooltip" href="#table-2" data-tooltip="...">表 2</a>` |
| Inline term link | class `term term-ref`, `href="#term-slug"` | `<a class="term term-ref" href="#term-css">调用点相似性</a>` |
| Highlighted jump target | class `highlight-target` | added on click, removed on timeout/blank click |
| Parallel pair | class `pair`, with `.source-left` and `.translation-right` |  |

## Toolbar

A sticky toolbar with, at minimum:

```html
<div class="toolbar">
  <button id="btn-summary" type="button">总结</button>
  <button id="btn-zh" class="active" type="button">中文阅读</button>
  <button id="btn-parallel" type="button">左右对照</button>
  <button id="btn-glossary" type="button">术语说明</button>
  <button id="btn-top" type="button">回到顶部</button>
  <a href="../original.pdf" target="_blank">打开原 PDF</a>
</div>
```

## CSS essentials

```css
.citation,.asset-ref,.term-ref { position:relative; text-decoration:none; border-bottom:1px dotted currentColor; }
.term-ref { border-bottom:1px dashed var(--accent); color:inherit; }

.tooltip::after {
  content:attr(data-tooltip); position:absolute; left:50%; bottom:calc(100% + 8px);
  transform:translateX(-50%); width:max-content; max-width:320px; padding:7px 9px;
  color:#fff; background:#25353a; border-radius:4px; font-size:12px; line-height:1.45;
  opacity:0; pointer-events:none; transition:opacity .12s; z-index:12;
}
.tooltip:hover::after,.tooltip:focus-visible::after { opacity:1; }

.highlight-target { background:var(--mark); outline:2px solid #e0bd36; outline-offset:4px; }

/* Chinese mode hides the source column; parallel mode shows a two-column pair. */
body.mode-zh .source-left { display:none; }
body.mode-parallel .pair { display:grid; grid-template-columns:1fr 1fr; gap:0 28px; }
body.mode-parallel .pair .source-left { color:var(--src); }

/* Summary panel is collapsed until the toolbar button toggles it. */
.summary { display:none; }
.summary.open { display:block; }

/* Print */
@media print { .toolbar,aside { display:none; } .paper-figure,.table-wrap { break-inside:avoid; } }
```

## JavaScript behaviors

```js
function clearHighlights() {
  document.querySelectorAll('.highlight-target').forEach(el => el.classList.remove('highlight-target'));
}
function highlightFromHash() {
  const id = location.hash.slice(1); if (!id) return;
  const target = document.getElementById(id); if (!target) return;
  clearHighlights();
  target.classList.add('highlight-target');
  setTimeout(() => target.classList.remove('highlight-target'), 4200);
}
document.querySelectorAll('.citation,.asset-ref,.term-ref')
  .forEach(link => link.addEventListener('click', () => setTimeout(highlightFromHash, 0)));
document.addEventListener('click', event => {
  if (!event.target.closest('.citation,.asset-ref,.term-ref,.references-list li,.paper-figure,.table-wrap,.glossary dt'))
    clearHighlights();
});
window.addEventListener('hashchange', highlightFromHash);
highlightFromHash();

// Match the initial hash target if the reader loads with one.
```

Summary toggle:

```js
const summary = document.getElementById('summary');
const btnSummary = document.getElementById('btn-summary');
btnSummary.addEventListener('click', () => {
  const open = summary.classList.toggle('open');
  btnSummary.classList.toggle('active', open);
  if (open) {
    summary.scrollIntoView({ behavior:'smooth', block:'start' });
    if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise();
  }
});
```

Reading-mode toggle:

```js
function setMode(mode) {
  document.body.classList.toggle('mode-zh', mode === 'zh');
  document.body.classList.toggle('mode-parallel', mode === 'parallel');
  if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise();
}
```

## MathJax configuration

Must appear before the MathJax script and include explicit delimiters:

```html
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true, processEnvironments: true
  },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }
};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
```

## Generation notes

- Generate the reader from `alignment.json` (translated blocks as the index), not
  from raw Markdown concatenation, so parallel mode and ids stay consistent.
- Emit one `.pair` block per alignment record; in Chinese mode hide `.source-left`.
- Emit equations as `.pair.pair-eq` with a `.source-left` containing the LaTeX so
  `scripts/verify_translation_project.py` can find and validate them.
- Rebuild the reader after any translation, figure-map, formula, or summary change.
