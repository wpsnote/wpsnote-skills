---
name: wps-note
description: 通过 MCP 工具读取、编辑和管理 WPS 笔记，基于 block 文档模型，所有内容以
  XML 格式交换。当用户说"帮我看看笔记"、"搜索笔记"、"创建一篇笔记"、"编辑笔记内容"、
  "整理标签"，或提到 WPS 笔记、WPS Note、云笔记时使用。也适用于排查 MCP 工具调用错误
  （BLOCK_NOT_FOUND、EDITOR_NOT_READY 等）。
metadata:
  mcp-server: wps-note
  version: "1.0.0"
  category: productivity
  tags: [note-taking, document-editing, wps]
---

# WPS Note MCP Skill

核心操作模式：**先定位（outline / search）→ 再读取（read）→ 最后编辑（write）**。所有内容以语义 XML 格式交换，所有定位基于 `block_id`（10 位字母数字）。

## 何时使用

- 用户提到 WPS 笔记、WPS Note、云笔记、金山笔记
- 用户要求读取、编辑、搜索、总结、翻译笔记内容
- 用户需要创建笔记、管理标签、整理笔记库
- 需要排查 MCP 工具调用失败（`BLOCK_NOT_FOUND`、`EDITOR_NOT_READY` 等错误）

**不适用于**：本地 Markdown 文件操作、WPS 文档/表格/演示等其他产品、纯概念讨论。

## 核心概念

### Block 模型

- 笔记由 block 组成，每个 block 有唯一的 `block_id`。
- block 类型：`paragraph`、`heading`、`blockquote`、`code_block`、`list`、`table`、`image`（单图/图片分栏）、`horizontal_rule`、`highlight_block`、`columns`、`embed`、`note_audio_card`。
- `embed` block（电子表格、视频、LaTeX、倒计时等）为**只读占位符**，不可编辑。
- `note_audio_card` block 为语音录音卡片（**只读**），在 XML 中显示为 `<NoteAudioCard/>`，使用 `get_audio_transcript` 工具获取转写内容。
- 表格必须**整表替换**，无法编辑单个单元格。

### note_id

- 大部分工具需要 `note_id` 来指定操作的笔记。
- 通过 `list_notes` 或 `search_notes` 获取 `note_id`；若用户要操作当前打开的笔记，可直接调用 `get_current_note` 获取。
- `get_note_info` 可获取笔记元数据（含标签），支持三种模式：单个 `note_id` 查询、批量 `note_ids` 查询（最多 100 个）、全量分页浏览（`page`/`page_size`/`limit`），无需读取全文内容。

### XML 输入输出

- 所有内容以语义 XML 格式收发，使用标签如 `<p>`、`<h1>`-`<h6>`、`<blockquote>`、`<codeblock>`、`<table>`、`<highlightBlock>`、`<columns>` 等。
- 每个块级标签通过 `id` 属性标识 block_id，如 `<p id="aB3kLm9xZq">内容</p>`。
- **重要**：写入操作（`edit_block` 等）的 `block_id` / `anchor_id` 只接受顶层 block ID（由 `get_note_outline` 返回）。`read_note` XML 中容器（`<highlightBlock>`、`<columns>`、`<table>`）内部段落的 `id` 仅供阅读参考，不可用于写入操作。
- 写入时提供 XML 格式内容，系统自动转换为内部 block 模型。编辑已有 block 时保留 `id`，创建新 block 时省略 `id`。
- 行内 mark 使用语义标签：`<strong>粗体</strong>`、`<em>斜体</em>`、`<s>删除线</s>`、`<u>下划线</u>`、`<code>代码</code>`（可选属性 `backgroundColor`、`fontSize`）、`<a href="url">链接</a>`。
- 行内自闭合元素：`<emoji value="😀"/>`（表情）、`<latex formula="E=mc^2"/>`（行内公式）、`<br/>`（硬换行）。
- 样式属性通过 `<span>` 传递：`<span fontColor="#C21C13">红色文字</span>`。
- **颜色受预设色板约束**，任意 hex 色值会被编辑器静默丢弃。各类颜色预设值：
  - `fontColor`（12 色）：`#080F17` `#C21C13` `#DB7800` `#078654` `#0E52D4` `#0080A0` `#757575` `#DA326B` `#D1A300` `#58A401` `#116AF0` `#A639D7`
  - `fontHighlightColor`（9 色）：`#FBF5B3` `#F8D7B7` `#F7C7D3` `#DFF0C4` `#C6EADD` `#D9EEFB` `#D5DCF7` `#E6D6F0` `#E6E6E6`
  - `highlightBlock` 颜色（6 对 bg→border）：`#FAF1E6`→`#FEC794`、`#FAE6E6`→`#F2A7A7`、`#E6FAEB`→`#AFE3BB`、`#E6EEFA`→`#98C1FF`、`#F5EBFA`→`#E5B5FD`、`#EBEBEB`→`#C5C5C5`
  - `columnBackgroundColor`（42 色，含纯色和渐变）：
    - 6 基础色：`#FFF5EB` `#FFECEB` `#E8FCEF` `#EBF2FF` `#FAF0FF` `#F2F2F2`
    - 18 扩展纯色：`#FCFAE1` `#FEF6E7` `#FFF5ED` `#FFF2F0` `#FFF2F4` `#FFF0F7` `#EEFFEB` `#EBFFF5` `#E8FCFC` `#EBF8FF` `#EBF1FF` `#F0EDFF` `#F2E7E4` `#F0E6DA` `#F5EEDA` `#EDF0EB` `#EDEEF0` `#F0E4DD`
    - 6 饱和色：`#FEF49C` `#BCFAAF` `#ADF4FF` `#C2D3FF` `#FFC7C7` `#E0E0E0`
    - 12 渐变色：使用 CSS `linear-gradient()` 语法，如 `linear-gradient(133deg,#FFFAF7 2.14%,#FFEDFE 96.88%)`
- 完整 XML 格式参考已集成到 MCP Server Instructions 中自动注入（视客户端支持情况）。未注入时可调用 `get_xml_reference` 工具按需获取。

### 只读 Token

- 部分笔记 token 为只读，所有写入操作（包括 `edit_block`、`batch_edit`、`insert_image`、`create_note` 等）均会返回 `DOCUMENT_READ_ONLY`。
- 此时 `retryable: false`——不要重试，应告知用户。读取操作不受影响。

### 响应格式

所有工具返回统一的标准信封：

```json
{ "ok": true, "code": "OK", "message": "...", "retryable": false, "data": { ... }, "hints": [] }
```

- `ok`——调用是否成功。
- `code`——机器可读状态码（参见错误恢复）。
- `retryable`——为 `true` 时可直接重试。
- `hints`——建议的后续工具或操作。

## 工作流

### 1. 读取与理解笔记

```
get_current_note()                            → 获取当前打开笔记的 note_id
list_notes / search_notes                     → 按条件查找 note_id
get_note_outline(note_id)                     → 查看结构和 block ID
read_section(note_id, heading_id)             → 读取某个章节
read_blocks(note_id, block_ids)               → 批量读取指定 block
read_blocks(note_id, block_id, before, after) → 读取单个 block 及上下文
search_note_content(note_id, q)               → 在笔记内搜索文本
read_image(note_id, block_id)                 → 读取图片 block 的实际内容（base64）
get_audio_transcript(shorthand_id)            → 获取语音录音的转写内容
get_xml_reference()                           → 获取 XML 格式完整参考文档
```

**对于长笔记**，优先使用 `get_note_outline` → `read_section`，而非 `read_note`，以减少 token 开销。

### 2. 编辑笔记内容

```
get_note_outline(note_id)                      → 获取最新 block ID
read_blocks(note_id, [target_id])              → 确认当前内容
insert_image(note_id, anchor_id, pos, src)     → 插入图片（独立工具，不走 XML）
generate_image(prompt, width?, height?)        → AI 文生图，返回图片 URL（配合 insert_image 插入笔记）
edit_block(note_id, op, ...)                   → 单个编辑操作（替换、插入、删除、更新属性）
batch_edit(note_id, operations)                → 多个操作合并为一次原子事务
```

**关键**：写入前必须刷新 block ID。编辑后 ID 可能发生变化。

### 3. 批量编辑（原子事务）

单个操作使用 `edit_block`，多个操作使用 `batch_edit` 合并为原子事务：

```
# 单个操作
edit_block(note_id, op: "replace", block_id: "id1", content: "...")
edit_block(note_id, op: "insert", anchor_id: "id2", position: "after", content: "...")

# 多个操作（原子事务）
batch_edit(note_id, operations: [
  { op: "delete",       block_ids: ["id1"] },
  { op: "replace",      block_id: "id2", content: "..." },
  { op: "update_attrs", block_id: "id3", attrs: { level: 2 } },
  { op: "insert",       anchor_id: "id4", position: "after", content: "..." }
])
```

**执行顺序固定**（`batch_edit`）：delete → replace → update_attrs → insert（与数组顺序无关）。

### 4. 管理笔记与标签

```
get_note_info(note_id)                      → 获取单个笔记元数据（含标签）
get_note_info(note_ids: [...])              → 批量获取多个笔记元数据（最多 100 个）
get_note_info(page, page_size)              → 分页浏览所有笔记元数据
search_notes(keyword, tags, since, before)  → 搜索笔记（也可按标签筛选笔记）
create_note(title)                          → 创建空白笔记（需用 edit_block 添加内容）
delete_note(note_id)                        → 不可恢复——必须与用户确认
sync_note(note_id)                          → 触发同步
find_tags()                                 → 列出所有标签
find_tags(keyword)                          → 搜索标签
get_note_stats(detailed)                    → 使用统计
```

## 工具速查表

### 读取工具

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `get_note_outline` | 获取结构大纲（含 title、word_count、block_count、blocks 列表）——获取 block_id 的主要方式 | `note_id`、`max_depth?`、`include_preview?` |
| `read_blocks` | 按 ID 批量读取 block 的 XML 内容和属性，或读取单个 block 及前后上下文 | `note_id`、`block_ids`（批量）或 `block_id`+`before?`+`after?`（上下文） |
| `read_note` | 读取笔记全文（XML），返回 content + truncated 标记。大文档建议用 `read_section` | `note_id`、`max_length?` |
| `search_note_content` | 在笔记内搜索文本，返回匹配 block 的 block_id/type/preview，用于编辑前定位 | `note_id`、`query`、`max_results?` |
| `read_section` | 按标题读取完整章节（到下一同级标题），`heading_block_id` 须为 heading 类型 | `note_id`、`heading_block_id`、`max_blocks?` |
| `read_image` | 读取图片 block 的实际内容（base64），可供视觉理解 | `note_id`、`block_id` |
| `get_audio_transcript` | 获取语音录音（NoteAudioCard）的转写文本，返回句子列表（含说话人、时间戳） | `shorthand_id`（从 outline 的 `note_audio_card` block attrs 获取） |
| `get_xml_reference` | 获取 XML 格式完整参考文档（所有标签、属性、写入示例），首次编辑前建议调用 | *（无参数）* |

**示例：**

```
get_note_outline({ note_id: "abc123" })
read_blocks({ note_id: "abc123", block_ids: ["aB3kLm9xZq", "xY7nPq2wRt"] })
read_blocks({ note_id: "abc123", block_id: "xY7nPq2wRt", before: 2, after: 3 })
read_note({ note_id: "abc123" })
search_note_content({ note_id: "abc123", query: "季度总结" })
read_section({ note_id: "abc123", heading_block_id: "aB3kLm9xZq" })
read_image({ note_id: "abc123", block_id: "imgBlock01" })
get_audio_transcript({ shorthand_id: "sh_abc123" })
get_xml_reference()
```

### 写入工具

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `edit_block` | 单个编辑操作（推荐入口），编辑后 block_id 可能变化需重新获取 | `note_id`、`op`（replace/insert/delete/update_attrs）、`block_id`/`anchor_id`/`block_ids`、`content`/`attrs` |
| `batch_edit` | 多个操作的原子事务（全部成功或全部回滚），执行顺序固定 | `note_id`、`operations[]` |
| `insert_image` | 插入图片（图片不可通过 XML 创建，必须用此工具），返回 block_id 和尺寸 | `note_id`、`anchor_id`、`position`、`src`、`alt?` |
| `generate_image` | AI 文生图，返回图片 URL（配合 `insert_image` 插入笔记）。每用户每分钟限 1 次，耗时 30-120 秒 | `prompt`、`width?`（默认 2688）、`height?`（默认 1536） |

**`edit_block` / `batch_edit` 操作类型：**

| `op` | 必填字段 |
|------|----------|
| `"replace"` | `block_id`、`content` |
| `"insert"` | `anchor_id`、`position`（"before"/"after"）、`content` |
| `"delete"` | `block_ids` |
| `"update_attrs"` | `block_id`、`attrs` |

**示例：**

```
// 单个操作 — edit_block
edit_block({ note_id: "abc123", op: "replace", block_id: "xY7nPq2wRt", content: "<p>更新后的段落文本</p>" })
edit_block({ note_id: "abc123", op: "insert", anchor_id: "aB3kLm9xZq", position: "after", content: "<h2>新章节</h2><p>这里是新内容。</p>" })
edit_block({ note_id: "abc123", op: "delete", block_ids: ["xY7nPq2wRt", "kL5mNp8vBc"] })
edit_block({ note_id: "abc123", op: "update_attrs", block_id: "aB3kLm9xZq", attrs: { level: 2 } })

// 多个操作（原子事务） — batch_edit
batch_edit({ note_id: "abc123", operations: [
  { op: "replace", block_id: "xY7nPq2wRt", content: "<p>更新后的段落文本</p>" },
  { op: "insert", anchor_id: "aB3kLm9xZq", position: "after", content: "<h2>新章节</h2>" }
]})

// 图片
insert_image({ note_id: "abc123", anchor_id: "aB3kLm9xZq", position: "after", src: "https://example.com/photo.png", alt: "示意图" })

// AI 文生图 → 插入笔记
generate_image({ prompt: "一只橘猫坐在窗台上，水彩画风格，暖色调" })
→ { image_url: "https://...", task_id: "...", width: 2688, height: 1536 }
// 然后用 insert_image 将返回的 image_url 插入笔记
```

### 隐藏写入工具

以下工具仍可用但默认不展示，适用于需要单独调用的场景：

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `replace_block` | 替换单个 block 内容 | `note_id`、`block_id`、`content` |
| `insert_block` | 在指定位置前后插入 | `note_id`、`anchor_id`、`position`、`content` |
| `delete_blocks` | 删除 block | `note_id`、`block_ids` |
| `update_block_attrs` | 修改 block 属性 | `note_id`、`block_id`、`attrs` |

### 管理工具

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `list_notes` | 列出笔记，支持排序和分页，返回 { notes, meta } | `limit?`、`sort?`、`direction?`、`page?`、`page_size?` |
| `create_note` | 创建空白笔记（仅含空段落），返回 { fileId, title } | `title?` |
| `get_note_info` | 获取笔记元数据（不读全文），返回 title、时间、intro、tags | `note_id`（单个）、`note_ids`（批量）、`page`+`page_size`（分页） |
| `get_current_note` | 获取当前打开的笔记 ID 和元数据 | *（无参数）* |
| `search_notes` | 搜索笔记（关键词 + 标签交集 + 时间范围），也可仅传 tags 按标签浏览 | `keyword?`、`tags?`、`since?`、`before?`、`sort?`、`direction?`、`limit?` |
| `find_tags` | 列出或搜索标签，返回 { id, name } 数组 | `keyword?`（不传列出全部，传入则搜索） |
| `sync_note` | 触发笔记与云端同步 | `note_id` |
| `delete_note` | 永久删除笔记（不可恢复），须先与用户确认 | `note_id` 或 `note_ids`（批量，最多 100） |
| `get_note_stats` | 使用统计（总笔记数、标签数、分布等） | `detailed?` |
| `get_mcp_logs` | MCP 调用日志，用于诊断 `INTERNAL_ERROR` | `limit?` |

**示例：**

```
list_notes({ sort: "update_time", direction: "desc", limit: 10 })
search_notes({ keyword: "项目方案", tags: ["工作"], since: "2025-01-01T00:00:00Z" })
search_notes({ tags: ["工作"] })  // 按标签筛选笔记（替代原 list_tag_notes）
create_note({ title: "会议记录 2025-03-03" })
get_current_note()
get_note_info({ note_id: "abc123" })              // 单个笔记元数据（含标签）
get_note_info({ note_ids: ["abc123", "def456"] }) // 批量查询
get_note_info({ page: 1, page_size: 20 })         // 分页浏览所有笔记
get_note_info({ limit: 5 })                       // 仅获取前 5 条
find_tags()                       // 列出所有标签
find_tags({ keyword: "工作" })    // 搜索标签
delete_note({ note_id: "abc123" })  // 不可恢复——必须先与用户确认！
get_mcp_logs({ limit: 20 })       // 查看最近的工具调用日志
```

## Block 类型与 XML 标签

| Block 类型 | XML 标签 | 说明 |
|-----------|----------|------|
| `paragraph` | `<p>` | 支持行内 mark（`<strong>`、`<em>`、`<s>`、`<u>`、`<code>`、`<a>`、`<tag>`）。`<tag>` 为笔记标签引用（**只读**，写入时自动降级为纯文本） |
| `heading` | `<h1>`-`<h6>` | 级别由标签名或 `attrs.level` 控制 |
| `blockquote` | `<blockquote>` | 支持行内 mark |
| `code_block` | `<codeblock lang="...">` | 纯文本内容；语言通过 `lang` 属性指定 |
| `list` | `<p listType="bullet\|ordered\|todo">` | 通过 `listType`、`listLevel`、`checked` 属性控制。有序列表额外支持 `listId`（分组连续编号项）和 `listValue`（编号样式：`arabicNum`、`alphabet` 等） |
| `table` | `<table>` | `<tr>` → `<td>` 结构；必须整表替换 |
| `highlight_block` | `<highlightBlock>` | 高亮块，包含 block 元素 |
| `columns` | `<columns>` → `<column>` | 分栏布局，每个 column 包含 block 元素 |
| `image` | `<img/>` | **只读**——不可通过 XML 创建或修改，使用 `insert_image` 工具插入单张图片 |
| `image_column` | `<imageColumn>` | **只读**——图片分栏展示，不可通过 XML 创建 |
| `horizontal_rule` | `<hr/>` | 分隔线 |
| `embed` | `<embed type="..."/>` | **只读**——不可编辑或替换 |
| `note_audio_card` | `<NoteAudioCard/>` | **只读**——语音录音卡片，使用 `get_audio_transcript` 获取转写内容 |

### `update_block_attrs` 支持的属性

| Block 类型 | 属性 | 可选值 |
|-----------|------|--------|
| `heading` | `level` | 1–6 |
| `heading` | `textAlign` | `"left"`、`"center"`、`"right"` |
| `paragraph` | `textAlign` | `"left"`、`"center"`、`"right"` |
| `code_block` | `language` | 语言标识字符串 |
| `todo_list` 子项 | `checked` | `true` / `false` |

## Troubleshooting

### block ID 失效（`BLOCK_NOT_FOUND`）

**现象**：写入操作报 `BLOCK_NOT_FOUND`，即使之前刚读取过该 block。
**原因**：编辑操作会导致 block ID 变化，缓存的 ID 已过期。
**解决**：写入前总是先 `get_note_outline` 或 `search_note_content` 刷新 ID。

### 表格编辑失败

**现象**：尝试编辑表格单元格时报错或内容丢失。
**原因**：表格只支持整表替换，不能编辑单个单元格。
**解决**：用 `edit_block` 的 `replace` 操作传入完整的 XML 表格（含表头分隔行）。

### embed block 不可写

**现象**：对 embed block 调用 `edit_block` 的 `replace` 操作返回错误。
**原因**：电子表格、视频、音频、LaTeX 等嵌入内容为只读占位符。
**解决**：跳过 embed block，仅操作其他可编辑 block 类型。

### 笔记只读（`DOCUMENT_READ_ONLY`）

**现象**：所有写入操作均返回 `DOCUMENT_READ_ONLY`。
**原因**：当前笔记 token 为只读权限，不可重试。
**解决**：告知用户此笔记为只读。读取操作仍正常。

### 编辑器未就绪（`EDITOR_NOT_READY`）

**现象**：操作返回 `EDITOR_NOT_READY`。
**原因**：笔记编辑器仍在初始化，通常 1-2 秒可恢复。
**解决**：等待片刻后重试。若 3 次仍失败，请用户检查笔记应用。

### WebSocket 未连接（`WEBSOCKET_NOT_CONNECTED`）

**现象**：`get_audio_transcript` 返回 `WEBSOCKET_NOT_CONNECTED`。
**原因**：网络断开或 WebSocket 连接中断。
**解决**：检查网络连接，等待 WebSocket 自动重连后重试。

### 其他注意事项

- **图片必须使用 `insert_image` 工具**：图片不可通过 XML 创建（`<img/>` 标签为只读）。`insert_image` 支持 base64 data URI 和 HTTP/HTTPS URL。**本地文件请先读取并转为 base64 data URI 再传入**。**URL 必须直接指向图片资源（返回 image/* 内容类型），不可为 HTML 页面链接**。若 URL 返回 404 或非图片内容，将报 `IMAGE_FETCH_FAILED` 错误。`edit_block` 中也不支持图片子操作。
- **`generate_image` 为 AI 文生图**：返回图片 URL 而非直接插入笔记。需配合 `insert_image` 将生成的图片 URL 插入到指定位置。每用户每分钟限 1 次，生成耗时约 30-120 秒。Prompt 限 500 字符以内，不可包含违规内容。
- **`batch_edit` 执行顺序固定**：delete → replace → update_attrs → insert，与数组顺序无关。
- **`create_note` 创建空白笔记**：不支持初始内容，需用 `edit_block` 填充。
- **`read_section` 仅限标题**：`heading_block_id` 必须指向 `heading` block，否则报 `INVALID_BLOCK_TYPE`。
- **`delete_note` 不可恢复**：必须先与用户确认。
- 当响应包含 `hints` 时，**遵循其建议**——它们指明了最快的恢复路径。

### 错误码速查

| 错误码 | 可重试 | 恢复方法 |
|--------|--------|----------|
| `INVALID_PARAMS` | 否 | 按 inputSchema 修正参数 |
| `EDITOR_NOT_READY` | 是 | 等待后重试 |
| `NO_ACTIVE_EDITOR_WINDOW` | 是 | 请用户打开笔记窗口 |
| `BLOCK_NOT_FOUND` | 否 | 刷新大纲获取有效 ID |
| `INVALID_BLOCK_TYPE` | 否 | 检查 block 类型 |
| `INVALID_CONTENT` | 否 | 修正内容格式 |
| `DOCUMENT_READ_ONLY` | 否 | 告知用户 |
| `FRONTEND_TIMEOUT` | 是 | 缩小范围或重试 |
| `IMAGE_FETCH_FAILED` | 是 | 检查图片 URL 是否直接指向图片资源，修正后重试 |
| `GENERATE_IMAGE_FAILED` | 否 | 检查 prompt（内容违规/过长/未授权/未登录），修正后重试 |
| `RATE_LIMITED` | 是 | 等待 60 秒后重试（`generate_image` 每用户每分钟限 1 次） |
| `WEBSOCKET_NOT_CONNECTED` | 是 | 检查网络，等待 WebSocket 重连后重试 |
| `INTERNAL_ERROR` | 是 | 重试；查 `get_mcp_logs`（隐藏工具） |

完整错误详情参见 `references/ERROR_CODES.md`。

## 常用编排模式

三种最高频的多工具组合，无需查阅完整用例手册即可使用。

**模式 1：搜索定位 → 分段读取**（长文档优先）
```
search_notes({ keyword }) → note_id
get_note_outline({ note_id }) → heading block ID
read_section({ note_id, heading_block_id }) → 按需读取章节
```

**模式 2：笔记内批量搜索替换**
```
search_note_content({ note_id, query }) → 匹配的 block_id 列表
read_blocks({ note_id, block_ids }) → 读取完整内容
batch_edit({ note_id, operations: [{ op: "replace", ... }, ...] }) → 原子替换
```

**模式 3：创建 → 填充模板**
```
create_note({ title }) → note_id（空白笔记）
get_note_outline({ note_id }) → 获取空 block ID
batch_edit({ note_id, operations: [
  { op: "replace", block_id, content: "<h1>标题</h1>" },
  { op: "insert", anchor_id, position: "after", content: "<p>模板内容...</p>" }
]})
```

更多组合模式和端到端场景参见 `references/USE_CASES.md`。

## 完整示例

**用户说**："帮我找到 Q1 报告，更新摘要部分，加一个结论"

**步骤 1**：定位笔记
```
search_notes({ keyword: "Q1 报告" })
→ data.notes[0].note_id = "note_xyz"
```

**步骤 2**：读取结构
```
get_note_outline({ note_id: "note_xyz" })
→ blocks: [
    { id: "h1abc", type: "heading", preview: "Q1 报告" },
    { id: "p1def", type: "paragraph", preview: "执行摘要..." },
    { id: "h2ghi", type: "heading", preview: "营收" },
    { id: "h2jkl", type: "heading", preview: "下一步计划" },
    { id: "p3mno", type: "paragraph", preview: "继续监控..." }
  ]
```

**步骤 3**：确认当前内容
```
read_blocks({ note_id: "note_xyz", block_ids: ["p1def"] })
→ "本季度各部门..."
```

**步骤 4**：原子编辑（替换摘要 + 插入结论）
```
batch_edit({ note_id: "note_xyz", operations: [
  { op: "replace", block_id: "p1def",
    content: "<p>本报告涵盖 2025 年 Q1 各部门业绩表现。营收超出目标 15%。</p>" },
  { op: "insert", anchor_id: "p3mno", position: "after",
    content: "<h2>总结</h2><p>2025 年 Q1 是强劲的一个季度，所有关键指标均实现显著增长。</p>" }
]})
→ ok: true
```

**步骤 5**：验证结果
```
read_section({ note_id: "note_xyz", heading_block_id: "h1abc", max_blocks: 5 })
→ 确认摘要已更新、结论已添加
```

**结果**：笔记摘要已替换为新内容，文末新增"总结"章节。

## 参考文档

- [API 参考](references/API_REFERENCE.md)——全部工具的完整 inputSchema
- [CLI 参考](references/CLI_REFERENCE.md)——`wpsnote-cli` 命令行工具的完整命令、参数和使用示例
- [错误码](references/ERROR_CODES.md)——详细错误码、hints 系统和恢复模式
- [用例手册](references/USE_CASES.md)——按复杂度递进的完整用例集（含端到端工作流示例）、Prompt 模板和异常处理速查
