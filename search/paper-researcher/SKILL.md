---
name: paper-researcher
description: 学术论文全流程助手：搜索论文、下载 PDF、存入 WPS 笔记、精读分析。当用户说"搜论文"、"找论文"、"下载论文"、"读论文"、"帮我找 paper"、"搜一下 XXX 相关的论文"、"把这篇论文存到笔记"、"分析这篇论文"、"帮我做文献调研"时触发。支持 arXiv 和 OpenAlex 两个数据源，自动完成搜索→下载→转文本→写入 WPS 笔记→分析的完整闭环。
---

# Paper Researcher — 论文全流程助手

## 前置检查

启动本 Skill 的第一步，检查 `wpsnote-cli` 是否可用：

```bash
wpsnote-cli status --json
```

- **可用** → 后续 WPS 笔记操作全部使用 `wpsnote-cli` 命令
- **不可用** → 降级使用 MCP 工具（`user-wpsnote` 服务）操作 WPS 笔记

---

## CLI 工具约定（wpsnote-cli 可用时）

```bash
wpsnote-cli <子命令> [参数]
# 复杂参数一律通过 --json-args 传入
wpsnote-cli <子命令> --json-args '{"key": "value"}'
```

| 操作 | CLI 命令 |
|------|---------|
| 搜索笔记 | `wpsnote-cli search-notes --query "关键词" --json` |
| 列出笔记 | `wpsnote-cli list --json` |
| 读取笔记全文 | `wpsnote-cli read --note_id <id> --json` |
| 新建笔记 | `wpsnote-cli create --json-args '{"title":"标题","content":"<h1>...</h1>"}'` |
| 插入 block | `wpsnote-cli edit --json-args '{"note_id":"...","op":"insert","anchor_id":"...","content":"<p>...</p>"}'` |
| 获取标签列表 | `wpsnote-cli tags --json` |

---

## 核心脚本

搜索与下载操作通过 `scripts/paper.py` 完成，路径：`<skill目录>/scripts/paper.py`。

```bash
# 首次使用安装依赖
pip install arxiv markitdown pymupdf

# 搜索（默认 arXiv，推荐英文关键词）
python3 /path/to/scripts/paper.py search "transformer attention" --top 5
python3 /path/to/scripts/paper.py search "LoRA fine-tuning" --source openalex --top 5
python3 /path/to/scripts/paper.py search "diffusion model" --category cs.CV

# 下载 PDF 并转 Markdown
python3 /path/to/scripts/paper.py get 1706.03762 --markdown
python3 /path/to/scripts/paper.py get 1706.03762 --output ~/papers --markdown
```

脚本实际路径：读取本 SKILL.md 的目录下的 `scripts/paper.py`，执行前先用 `ls` 确认路径存在。

### PDF → Markdown 转换说明

加 `--markdown` 参数后，脚本按以下顺序尝试转换，成功即停止：

1. **markitdown**（首选）：调用 `MarkItDown().convert(pdf_path)`，转换质量最高，保留结构
2. **pymupdf**（备选）：逐页提取文字，拼接为 `## Page N` 格式的 Markdown
3. 两种方法均失败 → 打印警告，返回空字符串（通常是扫描版 PDF）

转换结果保存为同名 `.md` 文件，路径与 PDF 相同，如 `~/papers/1706.03762.md`。

转换完成后，用 Shell `cat` 命令读取 `.md` 文件内容，再进行分析。

---

## 工作流程

### 场景 A：搜索 + 精读（最常见）

```
1. 运行 paper.py search  →  展示结果，请用户选择
2. 用户确认后，运行 paper.py get <ID> --markdown
3. Shell 读取生成的 .md 文件：cat ~/papers/<ID>.md
4. 按分析框架输出结构化摘要
5. 存入 WPS 笔记（CLI 优先，见存档流程）
```

### 场景 B：用户直接提供 PDF 路径

```
1. 用 Read 工具读取 PDF（Cursor 内置支持）
2. 若内容为空 → 运行 paper.py get <id> --markdown 转换后再读
3. 分析并存档
```

### 场景 C：批量文献调研

```
1. 多次搜索，收集论文 ID 列表
2. 批量执行 get --markdown 下载
3. 逐篇分析，最后输出横向对比表
4. 汇总写入 WPS 笔记的"文献综述"笔记
```

---

## 分析框架

精读论文时按以下维度输出：

| 维度 | 内容 |
|------|------|
| **元信息** | 标题、作者、机构、年份、期刊/会议 |
| **研究问题** | 解决什么问题，为什么重要 |
| **方法** | 核心技术路线、关键创新点 |
| **实验** | 数据集、评估指标、关键数值结果 |
| **结论** | 主要发现，对领域的贡献 |
| **局限** | 作者承认的不足或未来工作 |
| **个人评价** | 创新性、实用性、可复现性 |

---

## WPS 笔记存档流程

### 使用 wpsnote-cli（优先）

```bash
# 1. 先查是否已有同名笔记
wpsnote-cli search-notes --query "论文标题" --json

# 2a. 无同名笔记 → 新建
wpsnote-cli create --json-args '{
  "title": "论文标题",
  "content": "<h1>论文标题</h1><p><tag>#论文/NLP</tag></p>"
}'

# 2b. 有同名笔记 → 追加内容到末尾
wpsnote-cli edit --json-args '{
  "note_id": "<id>",
  "op": "insert",
  "anchor_id": "<last_block_id>",
  "content": "<p>追加内容</p>"
}'
```

### 使用 MCP（wpsnote-cli 不可用时）

调用 `user-wpsnote` MCP 服务的 `search_notes`、`create_note`、`edit_block` 等工具完成相同操作。

### 笔记内容模板

笔记 XML 结构模板见 [references/note-template.md](references/note-template.md)。

- **单篇**：标签 `#论文/[领域]`，如 `#论文/NLP`、`#论文/CV`
- **综述**：标签 `#论文/综述` + `#论文/[领域]`

---

## 数据源选择

| 场景 | 推荐数据源 |
|------|------------|
| AI/ML 论文 | `arxiv`（默认） |
| 医学、生物、社科 | `openalex`（开放获取率高） |
| 不确定 | 先 arxiv，结果少则换 openalex |

arXiv 分类过滤参考：`cs.AI` `cs.LG` `cs.CV` `cs.CL` `cs.NE` `stat.ML`

---

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| `arxiv` 包缺失 | `pip3 install arxiv` |
| PDF 下载失败 | 脚本自动重试 3 次；仍失败则直接访问 `https://arxiv.org/pdf/<ID>` 手动下载 |
| Markdown 转换为空 | PDF 可能是扫描件；确认 `pip install pymupdf` 已安装后重试 |
| OpenAlex 无结果 | 改用 arxiv；或换更通用的英文关键词 |
| wpsnote-cli 不可用 | 降级使用 MCP `user-wpsnote` 服务 |
