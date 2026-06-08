# Article Translator 中文说明

`article_translator` 是一个用于 Codex 的学术文献翻译 skill。它的目标不是把论文临时翻成一段中文，而是把长篇学术文献翻译做成一个可复现、可继续、可审阅、可验证的翻译项目。

它适合处理 PDF、期刊论文、综述、学位论文、arXiv 论文、技术报告等长文档，尤其适合包含公式、图、图注、表格、引用、章节编号和大量专业术语的文献。

这个仓库保存的是 Codex skill 指令，不是独立运行的翻译软件。

## 主要功能

- 将长篇学术文献翻译为准确、稳定的中文学术文本。
- 默认使用 `full-reading-output` 模式，不只输出纯中文译文。
- 使用 Markdown 作为可编辑源稿，并生成适合阅读的 HTML/PDF/DOCX 输出。
- 维护 `glossary.md`，记录术语译法、保留策略和解释。
- 维护 `style-guide.md`，统一学术中文风格和翻译约定。
- 维护 `alignment.json`，支持段落级中英文左右对照。
- 维护 `figure-map.json`，记录图编号、图片路径、图注和裁剪状态。
- 保留公式、变量、希腊字母、上下标、图号、表号、引用编号和章节结构。
- 生成 reader-style HTML，支持目录、术语解释、MathJax、左右对照和打印样式。
- 输出 `verification-report.md`，记录检查结果和未解决问题。

## 核心优势

### 1. 可复现的翻译项目

这个 skill 会把翻译组织成稳定的项目结构：

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

这种结构让长文献翻译可以跨会话继续，也方便后续重建 HTML、修正术语、检查对照关系和补充图片。

### 2. 更适合学术文本

相比普通翻译提示词，这个 skill 明确要求：

- 技术准确性优先于语言润色；
- 数学变量和符号不翻译；
- 希腊字母、上下标和公式编号必须正确；
- 图号、表号、章节号和引用编号必须保留；
- 图注作为文本翻译，不嵌入图片；
- 表格、公式、图和正文按照结构分别处理。

### 3. 术语更稳定

术语使用中英混合策略，支持：

- `keep-English`
- `keep-English-first`
- `translate-with-English`
- `translate`
- `keep-symbol`
- `review`

对关键专业术语，译文需要在首次或重要出现处保留完整英文原词。HTML 阅读稿中的术语应可点击，并显示中文解释，格式为：

```text
English term（中文译文）：中文解释
```

示例：

```text
structure factor（结构因子）：描述点过程或散射强度的核心函数 S(k)。
```

这样既保留英文概念锚点，又能给中文读者提供解释。

### 4. 更可靠的中英文对照

这个 skill 避免使用脆弱的顺序块匹配，例如“中文第 N 块 = 英文 PDF 抽取第 N 块”。

它要求：

- `alignment.json` 以译文 Markdown blocks 为主索引；
- PDF 抽取块只能作为原料，不能直接当作正文顺序；
- 页眉、DOI、作者、单位、期刊信息、图题、表格、脚注和参考文献等噪声要过滤或分流；
- 标题、公式、图、图注、表格、参考文献说明要按结构来源单独对齐；
- 完成后必须抽样检查摘要、引言、核心章节、结论和附录/致谢等代表性段落。

这可以显著降低左右对照 HTML 中“英文栏和中文栏错位”的风险。

### 5. 更好读的 HTML 阅读稿

默认 HTML 输出应是 paper reader，而不是原始 Markdown 转 HTML。

它应支持：

- 中文阅读模式；
- 中英文左右对照模式；
- 可点击术语解释；
- 目录和章节导航；
- MathJax 公式渲染；
- 相对图片路径；
- 响应式布局；
- 打印/PDF 样式；
- 长公式横向滚动；
- 图片、图注、公式和术语说明不重叠。

## 仓库内容

```text
.
├── SKILL.md
└── agents/
    └── openai.yaml
```

- `SKILL.md` 是主 skill 指令。
- `agents/openai.yaml` 是 OpenAI/Codex 使用的展示信息和默认提示。

## 安装方式

把这个仓库 clone 或复制到本地 Codex skills 目录，并命名为 `article_translator`：

```powershell
git clone https://github.com/waiwaifeng/codex-skill-article-translator.git C:\Users\歪歪风\.codex\skills\article_translator
```

如果你本地已经有 `article_translator`，替换前先备份。

## 使用方式

在 Codex 中处理学术文献翻译时，可以这样调用：

```text
Use $article_translator in full-reading-output mode to translate this academic article.
```

如果是跨会话继续旧项目，建议明确要求先读取旧上下文：

```text
Use $article_translator and first read glossary.md, style-guide.md, chapter-index.md, translation/, current reader HTML, alignment.json, and figure-map.json before continuing.
```

## 维护建议

- 不要把具体论文内容写进这个 skill。
- 具体项目的术语、图、alignment、译文和验证报告应放在翻译项目目录中。
- 修改行为规则时，优先更新 `SKILL.md`。
- 如果影响新会话默认行为，同步更新 `agents/openai.yaml`。
- 修改后运行验证脚本，并用关键词检查新增规则是否存在。
