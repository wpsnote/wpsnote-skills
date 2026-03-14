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
  mcp-server: user-wpsnote
  category: productivity
  tags: [obsidian, siyuan, wechat, html, import, pdf, docx, pptx, markdown]
---

# 文档导入器（Doc Importer）

将本地文档（Obsidian、思源笔记、微信公众号 HTML、下载目录或任意目录）批量导入到 WPS 笔记。

---

## 快速开始

**优先使用 `wpsnote-cli` 脚本方式**，比 MCP 逐步操作更快：

```bash
# 确认 CLI 连接正常
wpsnote-cli status

# 一键导入整个目录
python3 scripts/import_to_wps.py ~/Documents/MyVault

# 只导入没有导入过的（根据标题去重）
python3 scripts/import_to_wps.py ~/Downloads --resume

# 演习模式（不实际写入）
python3 scripts/import_to_wps.py ~/Downloads --dry-run
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

## WPS API 关键限制（必读）

在实际导入前，必须了解以下 WPS 笔记 API 的重要限制，否则会导致内容丢失或图片插入失败。

### 1. `get_note_outline` 默认只返回 100 个 block

`outline` 接口默认分页，`blocks` 数组最多 100 条，但 `block_count` 字段会返回真实总数。

**影响**：大文章（> 100 个 block）用 outline 查占位符时，只能找到前 100 个，后半段图片全部丢失。

**解决方案**：用 `read-blocks` 翻页续读：

```python
def get_all_blocks(note_id):
    """翻页获取笔记全部 blocks"""
    # 第一页用 outline（有 preview 字段）
    r = cli(['outline', '--note_id', note_id])
    data = r.get('data', {})
    total = data.get('block_count', 0)
    blocks = list(data.get('blocks', []))
    last_id = blocks[-1]['id'] if blocks else None

    # 超过 100 时用 read-blocks 续读
    while len(blocks) < total and last_id:
        r2 = cli(['read-blocks', '--note_id', note_id,
                  '--block_id', last_id, '--after', '100',
                  '--include_anchor', 'false'])
        new_blocks = (r2.get('data') or {}).get('blocks', [])
        if not new_blocks:
            break
        blocks.extend(new_blocks)
        last_id = new_blocks[-1]['id']

    return blocks
```

> `outline` 返回的 block 有 `preview` 字段；`read-blocks` 返回的有 `content`（完整 XML）字段，但没有 `preview`。

---

### 2. `insert_image` 在旧版 WPS 中只能插到前台笔记

**旧版本（< 0.1.4）**：`insert_image` 的图片 `fileID` 绑定到当前 WPS 客户端 UI 中打开的笔记，即使传了 `note_id` 参数，图片也会错误地关联到前台笔记。

**新版本（>= 0.1.4）**：已修复，`insert_image` 可以直接后台插图到任意笔记，无需切换前台。

**处理策略**：
- 优先检测版本，确认是否支持后台插图
- 如果是旧版，导入完文字后需要等 WPS 自动切换到新建笔记再插图（或提示用户手动切换）
- 推荐升级到最新版本

```bash
wpsnote-cli --version  # 检查版本
```

---

### 3. `list` 接口返回大数据时可能截断

`wpsnote-cli list` 返回 JSON 数据量较大时，Python 的 `subprocess` 读取输出可能出现 UTF-8 截断。

**解决方案**：用 `bytes` 模式读取，忽略编码错误：

```python
r = subprocess.run(['wpsnote-cli', 'list', '--limit', '100', '--json'],
                   capture_output=True, timeout=30)  # 注意：不加 text=True
raw = r.stdout.decode('utf-8', errors='ignore')
```

---

### 4. anchor 失效导致内容静默丢失

连续调用 `batch_edit` 插入内容时，WPS 内部可能重新索引，导致前一次操作返回的 `anchor_id` 失效。如果不处理，后续内容会静默跳过，造成文章后半段内容丢失。

**必须实现重试逻辑**：

```python
def do_insert(note_id, content, get_anchor_fn, max_retries=4):
    """带重试的内容插入，自动刷新 anchor"""
    anchor = get_anchor_fn()
    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(1.5 * attempt)
            anchor = get_anchor_fn()  # 重新获取最新 anchor
        res = batch_edit(note_id, [{
            'op': 'insert', 'anchor_id': anchor,
            'position': 'after', 'content': content
        }])
        if res.get('ok') is not False:
            anchor = get_anchor_fn()
            return True
    return False  # 4次都失败才放弃
```

**获取最新 anchor（最后一个 block）**：

```python
def get_last_block_id(note_id):
    r = cli(['outline', '--note_id', note_id])
    blocks = (r.get('data') or {}).get('blocks', [])
    return blocks[-1]['id'] if blocks else None
```

---

### 5. 批量写入的稳定参数

大量内容写入时，`BATCH_SIZE`（每次 `batch_edit` 的 block 数）建议设为 **4**，过大会增加 anchor 失效概率。

```python
BATCH_SIZE = 4  # 不要超过 8，否则容易出现 anchor 失效
```

---

## 完整工作流

### 第一步：确定扫描目录

**优先自动探测，不要直接问用户：**

```bash
# Obsidian Vault（macOS）
ls ~/Documents/ | grep -i obsidian
ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/ 2>/dev/null

# 思源笔记（macOS）
ls ~/Documents/SiYuan/ 2>/dev/null
ls ~/SiYuan/ 2>/dev/null

# 微信公众号存档（常见目录结构）
ls ~/Documents/ | grep -i "mp\|公众号\|推文\|文章"

# 下载目录
ls ~/Downloads/ | grep -E "\.(pdf|docx|pptx|xlsx|md|html)$" | head -10
```

---

### 第二步：扫描文档列表

```bash
python3 scripts/scan_docs.py <目录路径> [--recursive] [--days N] [--source TYPE]
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

**注意**：不要用 `list` 接口（数据量大时会截断），改用 `find` 按关键词搜索：

```python
def check_exists(title):
    r = cli(['find', '--keyword', title[:20], '--limit', '5'])
    notes = (r.get('data') or {}).get('notes', [])
    return next((n for n in notes if n['title'] == title), None)
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

## CLI 脚本方式（推荐）

```bash
# 全量导入
python3 scripts/import_to_wps.py ~/Documents/mp_format/历史推文

# 断点续跑（跳过已有标题的笔记）
python3 scripts/import_to_wps.py ~/Documents/mp_format/历史推文 --resume

# 指定来源类型
python3 scripts/import_to_wps.py ~/Documents/MyVault --source obsidian

# 只导入最近7天的 PDF 和 Word
python3 scripts/import_to_wps.py ~/Downloads --days 7 --formats pdf,docx

# 添加额外标签
python3 scripts/import_to_wps.py ~/Downloads --tag "#项目A"

# 跳过冲突（不询问）
python3 scripts/import_to_wps.py ~/Downloads --on-conflict skip

# 预先选择文件编号
python3 scripts/import_to_wps.py ~/Downloads --select 1,3,5-10
```

---

## MCP 逐步操作（CLI 不可用时）

```python
# 1. 创建笔记
create_note(title="文档标题")

# 2. 获取初始 block ID
get_note_outline(note_id=note_id)

# 3. 写入内容（分批，每批 4 个 block）
batch_edit(note_id=note_id, operations=[
    {"op": "replace", "block_id": first_block_id, "content": "<h1>标题</h1>"},
    {"op": "insert", "anchor_id": first_block_id, "position": "after",
     "content": "<p>2025-04-21 18:30 | <tag>#推文</tag></p>"},
])

# 4. 插入图片（新版 WPS 支持后台插图）
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
2. **标签**：`#标签名` → `<tag>#标签名</tag>`
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

使用翻页方案，见"WPS API 关键限制"第 1 条。

### 图片插入后点击显示加载失败

旧版 WPS（< 0.1.4）`insert_image` 的 fileID 绑定到前台笔记，升级到最新版本可解决。

### `insert_image` 报 `IMAGE_FETCH_FAILED`

- 检查 base64 data URI 格式：必须是 `data:image/jpeg;base64,<数据>`（不能是 `data:application/octet-stream`）
- 使用 `--src_file` 参数传入包含完整 data URI 的文件（适用于大图片，避免命令行长度限制）

```bash
# 正确方式（大图片）
echo "data:image/jpeg;base64,$(base64 -i image.jpg)" > /tmp/img.txt
wpsnote-cli insert-image --note_id "$ID" --anchor_id "$BID" --position before --src_file /tmp/img.txt
```

### anchor 失效导致内容截断

实现 4 次重试逻辑，每次失败后重新获取 `last_block_id`，见"WPS API 关键限制"第 4 条。

### `wpsnote-cli list` 返回乱码或截断

使用 `bytes` 模式读取，见"WPS API 关键限制"第 3 条。

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
| `wpsnote-cli` | CLI 操作 WPS 笔记（必须） | 见 wpsnote-cli 文档 |
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
