# Paper Reader 中文说明

`paper_reader` 是一个用于学术文献翻译与阅读的 skill（fork 自 [waiwaifeng/codex-skill-article-translator](https://github.com/waiwaifeng/codex-skill-article-translator)，在其基础上增加了交互式阅读和总结面板）。它的目标不是把论文临时翻成一段中文，而是把长篇学术文献翻译做成一个可复现、可继续、可审阅、可验证的翻译项目，并生成方便跳转的交互式阅读稿。

它适合处理 PDF、期刊论文、综述、学位论文、arXiv 论文、技术报告等长文档，尤其适合包含公式、图、图注、表格、引用、章节编号和大量专业术语的文献。

这个仓库保存的是 skill 指令，不是独立运行的翻译软件。

## 主要功能

- 将长篇学术文献翻译为准确、稳定的中文学术文本。
- 默认使用 `full-reading-output` 模式，不只输出纯中文译文。
- 使用 Markdown 作为可编辑源稿，并生成适合阅读的 HTML/PDF/DOCX 输出。
- 维护 `glossary.md`，记录术语译法、保留策略和解释。
- 维护 `style-guide.md`，统一学术中文风格和翻译约定。
- 维护 `alignment.json`，支持段落级中英文左右对照。
- 维护 `figure-map.json`，记录图编号、图片路径、图注和裁剪状态。
- 维护 `summary.md`，生成顶部“总结”面板，长论文快速通读。
- 保留公式、变量、希腊字母、上下标、图号、表号、引用编号和章节结构。
- 生成 reader-style HTML，支持目录、术语解释、MathJax、左右对照和打印样式。
- 交互式阅读：图/表/文献引用可点击跳转，悬停/聚焦显示标题提示，跳转目标高亮，点击空白处取消。
- 表格读取后重建为真正的 HTML 表格；图片按原文清晰度裁切并放在首次提及处。
- 附带确定性流水线（`make_inventory.py` + `build_reader.py` + `verify_translation_project.py`）：模型只产出结构化数据，HTML 由脚本稳定生成，换模型也能得到同样效果。
- 附带机械验证脚本，检查公式 source、并排公式块、图片引用、术语链接和 MathJax 配置。
- 输出 `verification-report.md`，记录检查结果、独立审查发现和未解决问题。

## 核心优势

### 1. 可复现的翻译项目

这个 skill 会把翻译组织成稳定的项目结构：

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

### 5. 机械验证脚本

仓库内置验证脚本，用来检查常见的 full-reading-output 生成问题：

```powershell
python scripts\verify_translation_project.py path\to\translation-project
```

它会检查 `type: equation` 记录是否使用真实 LaTeX/math source，`pair-eq-*` 英文左栏是否不是描述性占位，公式数量是否匹配，图片引用是否存在，`term-*` 链接是否能跳转，以及 MathJax 配置是否存在。

### 6. 更好读的 HTML 阅读稿

默认 HTML 输出应是 paper reader，而不是原始 Markdown 转 HTML。

它应支持：

- 顶部工具栏：总结、中文阅读、左右对照、术语说明、回到顶部、打开原 PDF；
- 中文阅读模式；
- 中英文左右对照模式；
- 可点击术语解释，格式为 `English term（中文译文）：中文解释`；
- 目录和章节导航；
- MathJax 公式渲染；
- 图/表/文献引用点击跳转，悬停或键盘聚焦显示标题提示，跳转目标高亮，点击空白处取消高亮；
- 表格重建为 HTML 表格，图片按原文清晰度裁切；
- `summary.md` 生成的“总结”面板，覆盖问题、方法、训练/方案变体、关键结果和局限；
- 相对图片路径；
- 响应式布局；
- 打印/PDF 样式；
- 长公式横向滚动；
- 图片、图注、公式和术语说明不重叠。

具体 DOM id、class 和跳转/高亮 JavaScript 约定见 `references/reader-contract.md`。

## 仓库内容

```text
.
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── reader-contract.md
│   └── pipeline.md
└── scripts/
    ├── make_inventory.py
    ├── make_alignment_skeleton.py
    ├── build_reader.py
    ├── verify_translation_project.py
    └── test_verify_translation_project.py
```

- `SKILL.md` 是主 skill 指令。
- `agents/openai.yaml` 是 OpenAI/Codex 使用的展示信息和默认提示。
- `references/reader-contract.md` 是交互式阅读稿的 DOM/class/JS 实现约定。
- `references/pipeline.md` 是确定性数据 schema 与端到端构建流程。
- `scripts/make_inventory.py` 把译文 Markdown 解析为稳定 block id。
- `scripts/make_alignment_skeleton.py` 生成固定结构的 `alignment.json` 骨架。
- `scripts/build_reader.py` 从 `alignment.json` 确定性生成交互式阅读稿。
- `scripts/verify_translation_project.py` 用于检查生成后的翻译项目。
- `scripts/test_verify_translation_project.py` 是验证脚本的回归测试。

## 安装方式

把仓库 clone 到一个工作目录并命名为 `paper_reader`，再软链到你使用的 agent。目录名必须是 `paper_reader`，且 `SKILL.md` 的 `name: paper_reader` 保持不变。

```bash
git clone https://github.com/Chronos22220399/codex-skill-article-translator.git ~/code/skill/paper_reader

# opencode（全局 skill）
ln -s ~/code/skill/paper_reader ~/.config/opencode/skills/paper_reader

# Codex
ln -s ~/code/skill/paper_reader ~/.codex/skills/paper_reader
```

添加后需要重启对应 agent 才会加载。如果你的环境不跟随软链，可改为直接 clone 或复制到 skills 目录。

如果你本地已经有同名 skill，替换前先备份。

## 使用方式

处理学术文献翻译时，可以这样调用：

```text
Use $paper_reader in full-reading-output mode to translate this academic article, with interactive jump links, tooltips, highlight-on-jump, English/Chinese parallel mode, and a 总结 summary panel.
```

如果是跨会话继续旧项目，建议明确要求先读取旧上下文：

```text
Use $paper_reader and first read glossary.md, style-guide.md, chapter-index.md, summary.md, translation/, current reader HTML, alignment.json, and figure-map.json before continuing.
```

## 维护建议

- 不要把具体论文内容写进这个 skill。
- 具体项目的术语、图、alignment、译文和验证报告应放在翻译项目目录中。
- 修改行为规则时，优先更新 `SKILL.md`。
- 如果影响新会话默认行为，同步更新 `agents/openai.yaml`。
- 修改后运行验证脚本，并用关键词检查新增规则是否存在。

## 发布到站点与多设备同步

生成的 reader 只是成品；发布到站点（`khronos-hub`）后才会被收录，并自动加上登录门禁与批注/书签挂件。

### 一条命令发布

```bash
~/code/skill/paper_reader/scripts/publish_to_site.sh <项目目录> ~/khronos-hub
```

脚本会：把项目拷入 `papers/<名字>-paper-reader/`（跳过 `.venv`、`source-pages/`、`page-renders/`、`.git`）；把原 PDF 拷入 `papers/`；运行 `site/build.py`；提交并推送。服务器约 10 分钟内自动上线。

手动等价：把项目和 PDF 放进 `~/khronos-hub/papers/`，`cd ~/khronos-hub && python3 site/build.py`，再 `git add -A && git commit -m "papers: add xxx" && git push`。

### 新设备（一次性配置）

先给该设备配置 GitHub SSH 公钥，并安装 `git / python3 / rsync`：

```bash
git clone git@github.com:Chronos22220399/codex-skill-article-translator.git ~/code/skill/paper_reader
ln -s ~/code/skill/paper_reader ~/.config/opencode/skills/paper_reader
git clone git@github.com:Chronos22220399/khronos-hub.git ~/khronos-hub
```

### 约定

- 项目目录：`papers/<名字>-paper-reader/`（目录名即模块 id）。
- 原 PDF 放 `papers/`，reader 的「打开原 PDF」指向 `../<pdf>`。
- 提交 `alignment.json`、`glossary.md`、`style-guide.md`、`translation/`、`references.json`、`figure-map.json`、`summary.md`，便于续译与复现。
- 不要手改 `translation-reading.html`，用 `scripts/build_reader.py` 重新生成。
- 每台设备把 skill 更新到同一提交：`git -C ~/code/skill/paper_reader pull`。

详细说明见 `references/merge-into-site.md`。

