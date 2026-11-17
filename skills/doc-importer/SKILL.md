---
name: doc-importer
description: >
  将本地文档批量导入到 WPS 笔记。支持扫描 Obsidian Vault、思源笔记、微信公众号存档、
  下载目录或任意用户指定目录，自动识别 HTML、Markdown、PDF、DOCX、PPTX、XLSX 等格式，
  转换为 WPS 笔记可读内容并保留图片和富文本格式。
  当用户说「导入文档到 WPS 笔记」「把我的 Obsidian 笔记导入」「导入思源笔记」
  「把下载的 PDF/Word/PPT 导入笔记」「把公众号文章导入笔记」「同步本地文档到 WPS 笔记」时触发。
  不适用于直接编辑 WPS 笔记内容、文档格式转换（不导入到笔记）。
license: MIT
metadata:
  author: 洛小山 (itshen)
  version: 1.2.0
  category: productivity
  tags: [obsidian, siyuan, wechat, html, import, pdf, docx, pptx, markdown]
---

# 文档导入器（Doc Importer）

将本地文档（Obsidian、思源笔记、微信公众号 HTML、下载目录或任意目录）批量导入到 WPS 笔记。

---

## 快速开始

> WPS 笔记接口见 [wpsnote](../wpsnote/SKILL.md)；CLI 调用与大文档分页/重试已统一在 [comm_script/wps_cli.py](../../comm_script/wps_cli.py)。

```text
参考实现：
- read_file("scripts/scan_docs.py")        # 目录扫描与来源识别
- read_file("scripts/import_to_wps.py")    # 文档转换与导入主流程（复用 comm_script/wps_cli.py）
```

---

## 支持的文档来源

| 来源 | 说明 | 典型目录结构 |
|------|------|------------|
| **Obsidian Vault** | 扫描 .md 文件，保留 wiki 链接、Callout、标签 | `Vault/笔记名.md` + `attachments/` |
| **思源笔记** | 扫描 .sy 文件（JSON格式），提取 Block Tree | `SiYuan/data/笔记本/文档.sy` |
| **微信公众号** | 解析 `原文.html`（含富文本格式、内联样式） | `文章名/原文.html` + `图片/` |
| **任意目录** | 用户指定路径，递归扫描子目录 | 任意 |

---

## 支持的文件格式

| 格式 | 转换方式 | 图片处理 | 富文本保留 |
|------|----------|----------|-----------|
| `.html` | BeautifulSoup 解析内联样式 | 本地图片 base64 | ✅ 颜色/粗体/标题 |
| `.md` / `.markdown` | 直接解析，转 WPS XML | 本地图片 base64 | 基本格式 |
| `.pdf` | pdfplumber 提取文本 + pdfimages 提取图片 | 提取嵌入图片 | 标题推断 |
| `.docx` | pandoc 转 markdown，提取 word/media/ | 解包提取 | 基本格式 |
| `.pptx` | markitdown 提取文本 + 解包媒体 | 解包提取 | 幻灯片结构 |
| `.xlsx` | pandas 读取，转 WPS table | 不含图片 | 表格结构 |
| `.txt` | 直接读取 | 不含图片 | 无 |
| `.sy` | JSON 解析思源 Block Tree | 提取 assets 图片 | 全部 |

---

## 批量导入稳定性约定（已内置于脚本）

通用 API 规则见核心 skill [wpsnote](../wpsnote/SKILL.md)；针对大文档批量导入，脚本已内置以下保障：

1. **分页读取全部 block**：`get_note_outline` 默认只返回首批 100 个 block，超出时通过 `read_blocks` 续读（见 `comm_script/wps_cli.py` `cli_get_all_blocks`），避免大文章后半段图片占位符遗漏。
2. **去重收敛范围**：按标题关键词用 `list_notes(keyword=...)` / `search_notes` 检索，不做无过滤全量扫描。
3. **anchor 失效重试与分批大小**：`BATCH_SIZE = 4`（不要超过 8），`batch_edit` 连续写入出现 anchor 失效时自动刷新末尾 `block_id` 并最多重试 4 次。

```python
BATCH_SIZE = 4  # 不要超过 8，否则容易出现 anchor 失效
```

---

## 完整工作流

### 第一步：确定扫描目录

**优先根据用户已给出的目录 / 文件线索判断来源类型，不足时再 `ask_user` 补最少必要信息：**

```text
优先识别这些常见来源线索：
- Obsidian Vault：`.md` 文件 + `attachments/` 或同类附件目录
- 思源笔记：`.sy` 文件 + `data/assets/`
- 微信公众号存档：`原文.html` + 图片目录 + `meta.json`
- 下载目录混合导入：PDF / DOCX / PPTX / XLSX / Markdown / HTML 混合存在
```

---

### 第二步：扫描文档列表

```text
如需对照扫描规则，用 `read_file("scripts/scan_docs.py")` 查看来源识别和输出字段约定；
整理后的清单至少要包含路径、标题、时间、格式、图片数和预计 block 数。
```

**输出 JSON 格式：**
```json
{
  "source_type": "wechat_mp",
  "root_path": "/Users/xxx/Documents/articles",
  "files": [
    {
      "path": "/Users/xxx/Documents/articles/文章名/原文.html",
      "rel_path": "文章名/原文.html",
      "title": "文章标题",
      "publish_time": "2025-04-21 18:30",
      "size_bytes": 204800,
      "modified": "2025-04-22T10:00:00",
      "format": "html",
      "estimated_images": 12,
      "estimated_blocks": 180
    }
  ],
  "total": 71,
  "formats": {"html": 71}
}
```

> `estimated_blocks` 帮助预判是否会超过 100 block，提前提示用户。

---

### 第三步：展示文件清单，询问选择

```
扫描到 71 个文件：
  - HTML: 71 个

文件列表：
 1. AutoGLM 发布之后，如今国产大模型终于长出了手。  (2025-03-31, 12张图)
 2. 你可能看不懂扣子空间为什么重要…                 (2025-04-21, 17张图)
 ...（超过20个时截断，告知总数）

请问你想如何导入？
 [A] 全部导入（71个文件）
 [B] 手动选择（输入文件编号，如：1,3,5-10）
 [S] 跳过已有标题的笔记（根据笔记标题去重）
```

---

### 第四步：去重检测

导入前通过标题检查 WPS 笔记中是否已存在同名笔记。

**注意**：不要把无过滤 `list_notes` 当成去重主入口，改用 `list_notes(keyword=...)` 按标题关键词精准搜索（或用 `search_notes(keywords=[...])`）：

```python
def check_exists(title):
    r = list_notes(keyword=title[:40], limit=20)
    data = r.get('data') or r
    notes = data.get('notes') or data.get('items') or []
    return next((n for n in notes if n.get('title') == title), None)
```

**发现重复时询问用户：**
```
发现以下笔记在 WPS 中已存在：
 - 《AutoGLM 发布之后…》（最后更新：2025-05-01）

如何处理？
 [O] 覆盖  [S] 跳过  [A] 追加  [RA] 对所有冲突应用相同策略
```

---

### 第五步：转换并导入

**推荐流程（以 HTML 富文本为例）：**

```python
# 1. 解析 HTML，提取内容段落和图片
segments = html_to_segments(html_path, img_dir)
# segments 格式：[('xml', '<p>文字</p>'), ('img', Path('图片/image_001.jpg')), ...]

# 2. 创建笔记
note_id = create_note(title)

# 3. 写入标题行 + meta 行（时间、标签）
write_header(note_id, title, publish_time, tag)

# 4. 批量写入正文（图片先插占位符）
write_content_with_placeholders(note_id, segments)

# 5. 翻页查找所有占位符 block_id（用 get_all_blocks）
ph_map = find_placeholders(note_id)

# 6. 逐个插入真实图片，替换占位符
for idx, img_path in img_list:
    insert_image(note_id, ph_map[idx]['block_id'], img_path)
    delete_placeholder(note_id, ph_map[idx]['block_id'])
```

**Meta 行格式**（根据来源类型灵活调整）：

```python
# 微信公众号：简洁的时间 + 标签
f'<p>{publish_time} | <tag id="{tag_id}">#推文</tag></p>'

# 通用文档：完整 meta blockquote
"""
<blockquote>
  <p>📄 <strong>来源</strong>：{rel_path}</p>
  <p>🕒 <strong>修改时间</strong>：{modified_time}</p>
  <p>🔄 <strong>导入时间</strong>：{import_time}</p>
</blockquote>
"""
```

---

### 第六步：进度报告

```
[3/71] AutoGLM 发布之后…
  解析完成: 95 段文字, 12 张图片
  ✓ 创建笔记: 501435173515
  ✓ 文字写入完成
  ✓ 图片插入: 12/12
  用时: 8.3s

进度：████████░░░░  42% (30/71)  预计剩余 ~12 分钟
```

---

## 转换脚本参考（需要查看实现时）

```text
优先阅读这些文件来理解不同来源的导入逻辑：
- read_file("scripts/import_to_wps.py")  # 主导入流程、去重、图片插入
- read_file("scripts/scan_docs.py")      # 目录扫描、来源判断、筛选
- read_file("references/conversion-guide.md")  # 格式映射细节
```

---

## 笔记工具逐步写入（需要手动接管时）

```python
# 1. 创建笔记
create_note(title="文档标题")

# 2. 获取初始 block ID
get_note_outline(note_id=note_id)

# 3. 写入内容（分批，每批 4 个 block）
batch_edit(note_id=note_id, operations=[
    {"op": "replace", "block_id": first_block_id, "content": "<h1>标题</h1>"},
    {"op": "insert", "anchor_id": first_block_id, "position": "after",
     "content": "<p>2025-04-21 18:30</p>"},
])

# 4. 添加文件级标签（单斜杠分层，不带 #）
manage_note_tags(note_id=note_id, add=["导入/推文"])

# 5. 插入图片（支持后台直接插图）
insert_image(note_id=note_id, anchor_id=placeholder_block_id,
             position="before", src="data:image/jpeg;base64,...")
```

---

## 各来源特殊处理

### 微信公众号 HTML（`原文.html`）

微信公众号文章使用内联 CSS 样式表达富文本，需要从 HTML 解析格式：

**目录结构：**
```
文章目录/
  原文.html        ← 完整 HTML，含内联样式
  meta.json        ← {"title": "...", "publish_time": "2025-04-21 18:30", "url": "..."}
  图片/            ← 本地图片文件
    image_001.jpg
    image_002.jpg
```

**HTML 解析要点：**
- 正文在 `#js_content` 容器内
- 图片在 `<img data-src="https://...">` 属性中（不是 `src`）
- 标题通过 `font-size >= 18px` 的 span 推断
- 颜色通过 span 的 `color: rgb(...)` 样式提取，需映射到 WPS 预设色
- 粗体通过 `font-weight: 700` 或 `bold` 识别

**内联样式 → WPS XML 映射：**
```python
# font-size >= 18px → <h2>
# font-weight: 700|bold → <strong>
# font-style: italic → <em>
# color: rgb(R,G,B) → <span fontColor="#WPS预设色">（需颜色映射）
```

详细颜色映射规则见 `references/conversion-guide.md` 第 10 节。

---

### Obsidian Vault

1. **Wiki 链接**：`[[文件名]]` → 纯文本；`[[文件名|显示名]]` → `显示名`
2. **标签**：提取 `#标签名` 后通过 `manage_note_tags({ note_id, add: ["标签名"] })`（CLI 用 `add-note-tags`）写入文件级标签
3. **Callouts**：`> [!NOTE]` → WPS `<highlightBlock>`
4. **Frontmatter**：YAML 头部提取为 meta 信息
5. **图片路径**：先找同目录 → 再找 `attachments/` → 再找 Vault 根目录

---

### 思源笔记（SiYuan）

- `.sy` 文件是 JSON 格式的 Block Tree
- 图片路径格式为 `assets/xxx.png`，实际文件在 `<工作空间>/data/assets/`
- 详细节点类型映射见 `references/conversion-guide.md` 第 6 节

---

## 故障排查

### `get_note_outline` 只返回 100 个 block，后面内容丢失

使用翻页方案，见"批量导入稳定性约定"第 1 条。

### `insert_image` 报 `IMAGE_FETCH_FAILED`

- 检查 base64 data URI 格式：必须是 `data:image/jpeg;base64,<数据>`（不能是 `data:application/octet-stream`）
- 大图片优先使用稳定 URL；如果只能传 base64，确保传入的是完整 data URI

### anchor 失效导致内容截断

实现 4 次重试逻辑，每次失败后重新获取 `last_block_id`，见"批量导入稳定性约定"第 3 条。

### `list_notes` / `search_notes` 返回结果过多

缩小筛选范围或主动分页，见"批量导入稳定性约定"第 2 条。

### pandoc 未安装
```bash
brew install pandoc  # macOS
```

### pdfplumber 未安装
```bash
pip3 install pdfplumber
```

### PDF 扫描版无文字（需要 OCR）
```bash
pip3 install pytesseract pdf2image
brew install tesseract
```

---

## 依赖项清单

| 工具 | 用途 | 安装 |
|------|------|------|
| 笔记 Agent 工具（`create_note` / `get_note_outline` / `batch_edit` / `insert_image` / `read_note` / `read_blocks` / `search_notes` / `list_notes`） | WPS 笔记写入、去重与回读（必须） | 宿主提供 |
| `beautifulsoup4` | HTML 解析（公众号/网页） | `pip3 install beautifulsoup4` |
| `lxml` | HTML 解析加速 | `pip3 install lxml` |
| `pandoc` | DOCX → Markdown | `brew install pandoc` |
| `pdfplumber` | PDF 文本/表格提取 | `pip3 install pdfplumber` |
| `pypdf` | PDF 图片提取备选 | `pip3 install pypdf` |
| `markitdown` | PPTX → Markdown | `pip3 install "markitdown[pptx]"` |
| `pandas` | XLSX 读取 | `pip3 install pandas openpyxl` |
| `pillow` | 图片处理/base64转换 | `pip3 install pillow` |
| `python-frontmatter` | YAML Frontmatter 解析 | `pip3 install python-frontmatter` |

详细转换逻辑见 `references/conversion-guide.md`。
