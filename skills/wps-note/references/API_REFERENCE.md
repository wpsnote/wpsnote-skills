# WPS Note MCP — API 参考

全部 MCP 工具的完整 inputSchema 和返回类型。包含默认展示工具和隐藏工具（标注为"隐藏"）。

## 响应信封

所有工具返回统一信封 `{ ok, code, message, retryable, data, hints }`，字段说明见 SKILL.md 响应格式章节。

---

## 读取工具

### get_note_outline

获取笔记结构化大纲。返回 title、word_count、block_count、estimated_xml_chars、size_category 和 blocks 列表（每个 block 含 id、type、preview、attrs）——这是获取有效 block_id 和判断文档规模的主要方式，后续所有读取和编辑操作都依赖 block_id。超大文档自动分页返回 pagination（含 has_more、next_offset）。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "max_depth": { "type": "number", "description": "大纲最大层级深度，默认不限制" },
  "include_preview": { "type": "boolean", "description": "是否包含文本预览，默认 true" },
  "preview_length": { "type": "number", "description": "预览文本长度，默认 50" },
  "offset": { "type": "number", "description": "从第几个 block 开始（0-based），默认 0。has_more 时用 next_offset 续读" },
  "block_limit": { "type": "number", "description": "单次最多返回的 block 数量（仅控制读取分页，笔记本身无 block 数量上限）。不指定时返回全部（小文档），超大文档自动分页" }
}
```

**返回** `data`：
```json
{
  "title": "2025年度工作总结",
  "word_count": 8520,
  "block_count": 45,
  "estimated_xml_chars": 13230,
  "size_category": "medium",
  "blocks": [
    { "id": "aB3kLm9xZq", "type": "heading", "depth": 0, "preview": "第一章 项目进展", "word_count": 0, "children_count": 0, "attrs": { "level": 1 } },
    { "id": "xY7nPq2wRt", "type": "paragraph", "depth": 0, "preview": "本季度完成了三个核心项目...", "word_count": 156, "children_count": 0 }
  ],
  "pagination": { "offset": 0, "limit": 100, "total_blocks": 350, "returned_blocks": 100, "has_more": true, "next_offset": 100 }
}
```

分页说明：文档超过 200 blocks 时自动分页返回。`pagination.limit` 是本次读取的页大小，可通过 `block_limit` 参数自定义。`has_more: true` 时使用 `next_offset` 续读：`get_note_outline({ note_id, offset: next_offset })`。

---

### read_blocks

按 ID 批量读取指定 block，或读取单个 block 及其上下文。支持两种调用模式：

**模式 1：批量读取**——传入 `block_ids` 数组，读取多个指定 block。

**模式 2：上下文读取**——传入 `block_id`（单个），可选 `before`/`after` 指定上下文范围。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "block_ids": { "type": "array", "items": "string", "description": "要读取的 block ID 数组（模式 1，与 block_id 二选一）" },
  "block_id": { "type": "string", "description": "锚点 block ID（模式 2，与 block_ids 二选一）" },
  "before": { "type": "number", "description": "锚点前读取的 block 数量，默认 0（仅模式 2）" },
  "after": { "type": "number", "description": "锚点后读取的 block 数量，默认 0（仅模式 2）" },
  "include_anchor": { "type": "boolean", "description": "是否包含锚点 block 本身，默认 true（仅模式 2）" }
}
```

**返回** `data`：`{ id, type, content, attrs }` 数组，其中 `content` 为 XML。

---

### read_note

读取笔记全文或分页读取（XML 格式），每个块级标签通过 `id` 属性标识 block_id。返回 title、word_count、content、truncated 和 pagination 分页信息。超大文档自动分页。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "max_length": { "type": "number", "description": "最大返回字符数，默认不限制" },
  "offset": { "type": "number", "description": "从第几个 block 开始读取（0-based），默认 0" },
  "block_limit": { "type": "number", "description": "单次最多读取的 block 数量（仅控制读取分页，笔记本身无 block 数量上限）。超大文档未指定时自动分页" }
}
```

**返回** `data`：
```json
{
  "title": "我的笔记",
  "word_count": 2400,
  "content": "<h1 id=\"aB3kLm9xZq\">第一章</h1>\n\n<p id=\"xY7nPq2wRt\">段落文本...</p>",
  "truncated": true,
  "pagination": {
    "offset": 0,
    "limit": 100,
    "total_blocks": 350,
    "returned_blocks": 100,
    "has_more": true,
    "next_offset": 100
  }
}
```

**分页说明**：
- `pagination.limit` 是本次读取的页大小，可通过 `block_limit` 参数自定义
- 文档超过 200 blocks 时自动分页返回，无需额外参数
- `has_more: true` 时使用 `next_offset` 继续读取：`read_note({ note_id, offset: next_offset })`
- 手动控制：`offset: 50, block_limit: 30` → 读取第 50–79 个 block
- `offset >= total_blocks` → 返回空 content，`has_more: false`
- 小文档（<=200 blocks）不传新参数时行为与原来完全一致

---

### search_note_content

在笔记中搜索文本，返回匹配 block 的 block_id、type 和包含关键词上下文的 preview。用于在编辑前精确定位目标 block。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "query": { "type": "string", "required": true, "description": "搜索关键词" },
  "max_results": { "type": "number", "description": "最大返回结果数，默认 10" }
}
```

**返回** `data`：`{ block_id, type, preview }` 数组。

---

### read_section

读取由标题定义的完整章节（从标题 block 到下一个同级或更高级标题的所有 block）。`heading_block_id` 必须指向 heading 类型的 block，否则报 `INVALID_BLOCK_TYPE`。章节过大被截断时，返回 `next_block_offset` 用于续读。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "heading_block_id": { "type": "string", "required": true, "description": "标题 block ID" },
  "max_blocks": { "type": "number", "description": "最大读取 block 数量，默认 50" },
  "include_subsections": { "type": "boolean", "description": "是否包含子标题下内容，默认 true" },
  "block_offset": { "type": "number", "description": "章节内 block 偏移量（0-based），用于续读截断章节。首次不传，截断时返回 next_block_offset" }
}
```

**返回** `data`：
```json
{
  "heading": "技术方案",
  "level": 2,
  "blocks": [{ "id": "...", "type": "paragraph", "content": "<p>...</p>", "attrs": {} }],
  "truncated": true,
  "next_block_offset": 50
}
```

- `truncated: true` 且 `next_block_offset` 存在时，使用 `read_section({ ..., block_offset: 50 })` 续读
- `truncated: false` 时章节已完整返回

---

### read_image

读取笔记中指定图片 block 的实际图片内容，返回 base64 编码的图片数据，可供视觉理解。通过 `get_note_outline` 找到 `type="image"` 的 block，使用其 `block_id` 调用此工具。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "block_id": { "type": "string", "required": true, "description": "图片 block 的 block_id（必须来自 get_note_outline 且 type=\"image\"）" }
}
```

**返回** `data`：base64 编码的图片数据，包含 MIME 类型信息。

---

### get_audio_transcript

获取语音录音卡片（NoteAudioCard）的转写文本。通过 `get_note_outline` 找到 `type="note_audio_card"` 的 block，使用其 `attrs.shorthand_id` 调用此工具。返回转写句子列表，包含说话人、文本、时间戳等信息。

```json
{
  "shorthand_id": { "type": "string", "required": true, "description": "语音录音的 shorthand_id（从 get_note_outline 中 type=\"note_audio_card\" 的 block attrs 获取）" }
}
```

**返回** `data`：
```json
{
  "shorthand_id": "sh_abc123",
  "status": "completed",
  "is_complete": true,
  "sentence_count": 42,
  "sentences": [
    {
      "sentence_id": "s1",
      "speaker_name": "Speaker 1",
      "text": "今天我们讨论一下项目进度...",
      "start_time": 0,
      "end_time": 5000,
      "is_optimized": true
    }
  ]
}
```

**`status` 可选值**：

| status | 含义 |
|--------|------|
| `recording` | 正在录音 |
| `paused` | 录音暂停 |
| `stopping` | 正在停止（过渡态） |
| `stopped` | 录音已停止，等待智能处理 |
| `processing` | 智能处理中（优化/总结） |
| `completed` | 全部处理完成 |
| `unknown` | 状态未知（获取状态失败时） |

**`is_complete`**：当 `status` 为 `completed` 或 `stopped` 时为 `true`，表示转写内容已稳定可读取。

**错误场景**：
- 网络断开或 WebSocket 未连接 → `WEBSOCKET_NOT_CONNECTED`（retryable）
- 请求超时（10s） → `FRONTEND_TIMEOUT`（retryable）

---

### get_xml_reference

获取 XML 格式完整参考文档，包含所有标签、属性、子节点结构和写入示例。首次编辑笔记前建议调用，尤其在 MCP Server Instructions 未自动注入 XML 参考时。

```json
{}
```

无参数。

**返回** `data`：
```json
{
  "reference": "=== XML Format Reference ===\n..."
}
```

---

## 写入工具

### edit_block

编辑笔记 block（推荐的单操作编辑入口）。通过 `op` 指定操作：`replace`（block_id + content）替换内容、`insert`（anchor_id + position + content）插入新块、`delete`（block_ids）删除块、`update_attrs`（block_id + attrs）更新属性。只填写当前 `op` 需要的字段。编辑后 block_id 可能变化，需重新获取。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "op": { "type": "string", "enum": ["replace", "insert", "delete", "update_attrs"], "required": true, "description": "操作类型" },
  "block_id": { "type": "string", "description": "目标顶层 block ID（replace / update_attrs 时必填）" },
  "block_ids": { "type": "array", "items": "string", "description": "要删除的顶层 block ID 数组（delete 时必填）" },
  "anchor_id": { "type": "string", "description": "锚点顶层 block ID（insert 时必填）" },
  "position": { "type": "string", "enum": ["before", "after"], "description": "插入位置（insert 时必填）" },
  "content": { "type": "string", "description": "完整 XML 字符串（replace / insert 时必填）。不能传纯文本、Markdown 或自然语言编辑指令；例如 '<p>正文</p>' 或 '<h2>标题</h2><p>正文</p>'" },
  "attrs": { "type": "object", "description": "要更新的属性（update_attrs 时必填）" }
}
```

**注意**：

- `replace` / `insert` 的 `content` 必须直接填写 XML，而不是 `"把第二段改成……"` 这类文字指令。
- `replace` 时 `content` 根块 `id` 可省略；若显式传入，必须与 `block_id` 一致。
- `insert` 时 `content` 中的块级标签应省略 `id`，系统会分配新的 `block_id`。

**文件引用参数**（Electron 主进程预处理，对所有 MCP 客户端透明）：

| 参数 | 说明 |
|------|------|
| `content_file` | 文件路径，读取内容填入 `content`（与 `content` 二选一；`content` 显式传入时 `content_file` 被忽略） |
| `__args_file` | JSON 文件路径，读取后整体 merge 到参数中（最低优先级，不覆盖已有字段） |

文件引用在 Electron 主进程层解析（`server.js`），前端 bridge 无感知。无 `_file` 参数时为空操作，零开销。

**返回** `data`：`{ success, results[], message? }`。

---

### batch_edit

在单次原子事务中执行多个编辑操作（多步操作需要全部成功或全部回滚时使用）。执行顺序固定：`delete` → `replace` → `update_attrs` → `insert`，与数组顺序无关。每个操作只填写其 `op` 对应字段；`replace` / `insert` 的 `content` 必须是完整 XML 字符串。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "operations": { "type": "array", "required": true, "description": "编辑操作数组" }
}
```

**操作 schema：**

```json
{ "op": "replace", "block_id": "string", "content": "<p>...</p>" }
{ "op": "insert", "anchor_id": "string", "position": "before|after", "content": "<h2>...</h2><p>...</p>" }
{ "op": "delete", "block_ids": ["string"] }
{ "op": "update_attrs", "block_id": "string", "attrs": { ... } }
```

**文件引用参数**（同 `edit_block`）：

| 参数 | 说明 |
|------|------|
| `operations_file` | JSON 文件路径，读取后解析为 `operations` 数组（与 `operations` 二选一） |
| `__args_file` | JSON 文件路径，读取后整体 merge 到参数中 |

`operations` 数组中的每个操作项也支持 `content_file` 引用。

**返回** `data`：`{ success, results[], message? }`。

---

### insert_image

在笔记中指定位置插入图片（图片不可通过 XML 创建，必须用此工具）。当前走在线上传，调用时需联网。支持 base64 data URI 和 HTTP/HTTPS URL。本地文件请先读取并转为 base64 data URI 再传入。返回 block_id 和图片尺寸 { width, height }。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "anchor_id": { "type": "string", "required": true, "description": "锚点 block ID" },
  "position": { "type": "string", "enum": ["before", "after"], "required": true, "description": "插入位置" },
  "src": { "type": "string", "required": true, "description": "图片来源：(1) base64 data URI（格式 data:image/png;base64,...）；(2) HTTP/HTTPS URL（须直接指向图片资源，返回 image/* 内容类型）。本地文件路径受安全限制，请先读取文件并转为 base64 data URI" },
  "alt": { "type": "string", "description": "图片替代文本（可选）" }
}
```

**返回** `data`：`{ success, block_id, attachment_id, dimensions: { width, height }, message? }`。

---

### generate_image

根据文字描述生成一张图片，返回图片 URL。生成后可使用 `insert_image` 将图片插入笔记。适用于创意配图、场景可视化、概念设计等。注意：每用户每分钟限 1 次，生成耗时约 30-120 秒。

```json
{
  "prompt": { "type": "string", "required": true, "description": "图片描述（中英文均可）。描述越具体效果越好，建议包含：主体、风格、色调、构图。例如：'一只橘猫坐在窗台上，水彩画风格，暖色调'。限 500 字符以内" },
  "width": { "type": "integer", "description": "图片宽度（像素）。横版推荐 2688，竖版推荐 1536，正方形推荐 2048。默认 2688" },
  "height": { "type": "integer", "description": "图片高度（像素）。横版推荐 1536，竖版推荐 2688，正方形推荐 2048。默认 1536" }
}
```

**返回** `data`：
```json
{
  "image_url": "https://...",
  "task_id": "t_abc123",
  "prompt": "原始 prompt",
  "width": 2688,
  "height": 1536
}
```

**错误场景**：
- 速率限制（每分钟 1 次） → `RATE_LIMITED`（retryable，等待 60 秒）
- Prompt 内容违规 → `GENERATE_IMAGE_FAILED`（修改 prompt 后重试）
- Prompt 过长（>500 字符） → `GENERATE_IMAGE_FAILED`（缩短 prompt）
- 白名单未授权 → `GENERATE_IMAGE_FAILED`（联系管理员）
- 用户未登录 → `GENERATE_IMAGE_FAILED`（登录后重试）

---

### import_web_page

从指定 URL 导入网页内容为笔记。仅支持白名单域名（微信公众号、知乎、豆瓣等）。创建新笔记并将网页内容转换后写入，返回笔记 ID、标题和摘要。转换耗时约 5-30 秒。

```json
{
  "url": { "type": "string", "required": true, "description": "要导入的网页 URL。必须是白名单域名，例如微信公众号文章链接" }
}
```

**返回** `data`：
```json
{
  "fileId": "123456",
  "title": "文章标题",
  "intro": "文章摘要前 100 字...",
  "linkUrl": "https://xxx/note/123456"
}
```

- `fileId`：新创建的笔记 ID，可直接用于后续 `read_note`、`edit_block` 等操作
- `title`：从网页内容中提取的标题
- `intro`：从网页内容中提取的摘要（最长 100 字）
- `linkUrl`：笔记的 Web 访问链接（可选）

**错误场景**：
- 不支持的域名 → `INVALID_PARAMS`（仅白名单域名可导入，检查 URL 后修正）
- 创建云文档失败 → `INTERNAL_ERROR`（retryable，网络问题或服务异常）
- 网页内容转换失败 → `INTERNAL_ERROR`（retryable，重试或检查 URL 是否可访问）

---

## 管理工具

### list_notes

列出笔记，支持按 update_time/create_time 排序和分页。返回 { notes, meta }，meta 包含 has_more 分页标记。

```json
{
  "limit": { "type": "number", "description": "最大返回笔记数，必须为正整数" },
  "sort": { "type": "string", "enum": ["update_time", "create_time"], "description": "排序字段，默认 update_time" },
  "direction": { "type": "string", "enum": ["desc", "asc"], "description": "排序方向，默认 desc" },
  "since": { "type": "string", "description": "起始时间（ISO 8601）" },
  "before": { "type": "string", "description": "结束时间（ISO 8601）" },
  "page": { "type": "number", "description": "页码，默认 1（兼容模式）" },
  "page_size": { "type": "number", "description": "每页条数，默认 20（兼容模式）" },
  "starred": { "type": "boolean", "description": "为 true 时仅返回已收藏笔记" }
}
```

无必填参数。

**返回** `data`：
```json
{
  "notes": [{ "note_id": "abc123", "title": "...", "starred": true, "..." : "..." }],
  "meta": { "has_more": true, "next_token": "...", "truncated": false, "fetched_pages": 1 }
}
```

---

### create_note

创建空白笔记（仅含一个空段落 block）。不支持初始内容——创建后需用 `edit_block` 或 `batch_edit` 填充。

```json
{
  "title": { "type": "string", "description": "笔记标题" }
}
```

无必填参数。未传 `title` 时默认为"Untitled"。

**返回** `data`：`{ fileId, title, linkUrl? }`。

---

### get_note_info

获取笔记元数据（含标签），不读取全文内容。支持三种查询模式：

**模式 1：单个查询**——传入 `note_id`，返回单个笔记的完整元数据。

**模式 2：批量查询**——传入 `note_ids` 数组（最多 100 个），返回多个笔记的元数据。

**模式 3：全量分页**——不传 ID，通过 `page`/`page_size` 分页浏览，或用 `limit` 限制返回数量。

```json
{
  "note_id": { "type": "string", "description": "单个笔记 ID（模式 1）" },
  "note_ids": { "type": "array", "items": "string", "description": "批量查询的笔记 ID 列表，最多 100 个（模式 2）" },
  "limit": { "type": "number", "description": "最大返回笔记数（模式 3）" },
  "page": { "type": "number", "description": "页码，默认 1（模式 3）" },
  "page_size": { "type": "number", "description": "每页条数，默认 20（模式 3）" }
}
```

无必填参数。优先级：`note_id` > `note_ids` > 全量分页。

**返回** `data`（三种模式统一返回结构）：
```json
{
  "notes": [
    {
      "note_id": "abc123",
      "title": "我的笔记",
      "create_time": "2024-01-01T00:00:00.000Z",
      "update_time": "2024-01-02T00:00:00.000Z",
      "link_id": "link-abc",
      "intro": "笔记简介...",
      "tags": [{ "id": "t1", "name": "工作" }],
      "starred": true
    }
  ],
  "meta": {
    "total": 1,
    "has_more": false,
    "page": 1,
    "page_size": 20,
    "requested_limit": null
  }
}
```

- `notes[].starred`：是否已收藏（`true` / `false`）
- `notes[].tags`：笔记关联的标签列表，自动从全部标签中反向映射
- `meta.page` / `meta.page_size`：仅在分页模式下返回
- `meta.requested_limit`：仅在 limit 模式下返回

---

### get_current_note

获取当前正在编辑的笔记的 ID、元数据和文档统计（word_count、block_count、size_category、estimated_xml_chars）。若用户未打开笔记则返回错误。大文档时根据 size_category 决定后续读取策略。

```json
{}
```

无参数。

**返回** `data`：
```json
{
  "note_id": "abc123",
  "title": "项目方案",
  "create_time": "2024-01-01T00:00:00.000Z",
  "update_time": "2024-06-15T10:30:00.000Z",
  "link_id": "link-abc",
  "intro": "本文档描述了...",
  "tags": [{ "id": "t1", "name": "工作" }],
  "word_count": 52000,
  "block_count": 980,
  "estimated_xml_chars": 74200,
  "size_category": "large"
}
```

`size_category` 取值：`small`（<5K 字）、`medium`（5K-20K）、`large`（20K-80K）、`very_large`（>80K）。large/very_large 时 hints 会建议使用 `search_note_content` 精准定位；`get_note_outline` 支持分页读取（offset/block_limit），可按需获取结构。

---

### get_cursor_block

获取当前光标所在的顶层 block 信息，适合围绕当前编辑位置进行插入、替换等操作。返回 `block_id`、`block_type` 和 `note_id`。若光标位于高亮块（subdoc）或分栏（columns）内部，返回不支持错误。

```json
{}
```

无参数。

**返回** `data`：
```json
{
  "block_id": "aB3kLm9xZq",
  "block_type": "paragraph",
  "note_id": "note_abc123"
}
```

**错误场景**：
- 光标位于高亮块或分栏内部 → 当前会返回 `INTERNAL_ERROR`，message 包含 `UNSUPPORTED_POSITION`
- 当前无打开的笔记 → `NO_ACTIVE_EDITOR_WINDOW`

---

### search_notes

搜索笔记。支持 keyword 全文匹配、tags 标签筛选（多标签取交集）、since/before 时间范围，可排序和限制数量。也可仅传 tags 实现按标签浏览笔记。

```json
{
  "keyword": { "type": "string", "description": "搜索关键词" },
  "tags": { "type": "array", "items": "string", "description": "标签名称或 ID（取交集筛选）" },
  "since": { "type": "string", "description": "起始时间（ISO 8601）" },
  "before": { "type": "string", "description": "结束时间（ISO 8601）" },
  "sort": { "type": "string", "enum": ["update_time", "create_time"], "description": "排序字段，默认 update_time" },
  "direction": { "type": "string", "enum": ["desc", "asc"], "description": "排序方向，默认 desc" },
  "limit": { "type": "number", "description": "最大返回结果数" },
  "starred": { "type": "boolean", "description": "为 true 时仅在已收藏笔记中搜索" }
}
```

无必填参数。

**返回** `data`：匹配笔记数组，每个笔记包含 `starred` 布尔字段。

---

### find_tags

列出所有标签或按关键词搜索标签。不传 `keyword` 列出全部，传 `keyword` 进行搜索。

```json
{
  "keyword": { "type": "string", "description": "标签关键词（可选，不传则列出所有标签）" }
}
```

无必填参数。

**返回** `data`：标签数组。

> **注意**：原 `list_tag_notes` 功能已移除，可使用 `search_notes({ tags: [...] })` 按标签筛选笔记。

---

### manage_note_tags

管理笔记的文件级标签——添加或移除标签。不传 `add`/`remove` 时返回当前标签列表。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "add": { "type": "array", "items": "string", "description": "要添加的标签名数组。已有同名标签自动复用，不存在的标签自动创建。多级标签用 / 分隔（如 '工作/项目'）" },
  "remove": { "type": "array", "items": "string", "description": "要移除的标签名或标签 ID 数组。不存在的标签静默跳过" }
}
```

`note_id` 必填，`add` 和 `remove` 至少传一个（都不传则为查询模式）。

**返回** `data`：
```json
{
  "note_id": "abc123",
  "tags": [
    { "id": "tag_001", "name": "工作" },
    { "id": "tag_002", "name": "项目/Q1" }
  ],
  "added": ["工作", "项目/Q1"],
  "removed": ["草稿"]
}
```

- `tags`：更新后笔记的完整文件级标签列表
- `added`：本次实际新增的标签名（已存在的标签不重复添加）
- `removed`：本次实际移除的标签名（不存在的标签静默跳过）

**标签命名规则**：
- 多级标签用 `/` 分隔（如 "工作/项目"），调用参数不要带 `#` 前缀
- 每级最多 20 字符，最多 10 级
- 禁用 `\ : * ? " < > \|` 与 emoji

**错误场景**：
- `note_id` 未传 → `INVALID_PARAMS`
- 当前环境不支持文件级标签 → `INTERNAL_ERROR`

---

### sync_note

触发指定笔记与云端的同步，确保本地编辑已保存到远端。

```json
{
  "note_id": { "type": "string", "required": true, "description": "要同步的笔记 ID" }
}
```

**返回** `data`：同步状态。

---

### delete_note

**高危操作**：永久删除一个或多个笔记，此操作不可恢复。

```json
{
  "note_id": { "type": "string", "description": "要删除的笔记 ID（单个）" },
  "note_ids": { "type": "array", "items": "string", "description": "批量删除的笔记 ID 列表，最多 100 个" }
}
```

`note_id`（单个）和 `note_ids`（批量）二选一，不可同时传入。

**返回** `data`：删除结果。

---

### get_note_stats

获取笔记使用统计（总笔记数、总标签数等）。设置 `detailed=true` 可额外获取 notes_by_tag 分布和活跃度趋势。

```json
{
  "detailed": { "type": "boolean", "description": "为 true 时返回详细分析" }
}
```

无必填参数。

**返回** `data`：统计信息对象。

---

### get_mcp_logs

获取最近 MCP 工具调用日志和内存统计。当工具返回 `INTERNAL_ERROR` 时可用此诊断问题。

```json
{
  "limit": { "type": "number", "description": "最大返回日志条数，默认 50" }
}
```

无必填参数。

**返回** `data`：日志条目数组和内存统计。

---

## 隐藏工具

以下工具仍可用但默认不展示给 LLM，适用于特定场景下的单独调用。

### replace_block（隐藏）

替换指定 block 的内容。表格会整表替换。已隐藏，不会默认展示给 LLM。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "block_id": { "type": "string", "required": true, "description": "要替换的 block ID" },
  "content": { "type": "string", "required": true, "description": "新的 XML 内容" }
}
```

**返回** `data`：`{ success, block_id, message? }`。

---

### insert_block（隐藏）

在指定锚点 block 的前面或后面插入新内容。已隐藏，不会默认展示给 LLM。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "anchor_id": { "type": "string", "required": true, "description": "锚点 block ID" },
  "position": { "type": "string", "enum": ["before", "after"], "required": true, "description": "插入位置" },
  "content": { "type": "string", "required": true, "description": "要插入的 XML 内容" }
}
```

**返回** `data`：`{ success, new_block_ids, message? }`。

---

### delete_blocks（隐藏）

按 ID 删除一个或多个 block。已隐藏，不会默认展示给 LLM。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "block_ids": { "type": "array", "items": "string", "required": true, "description": "要删除的 block ID 数组" }
}
```

**返回** `data`：`{ success, deleted_ids, message? }`。

---

### update_block_attrs（隐藏）

在不修改内容的情况下更新 block 属性。已隐藏，不会默认展示给 LLM。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "block_id": { "type": "string", "required": true, "description": "block ID" },
  "attrs": { "type": "object", "required": true, "description": "要更新的属性（与现有属性合并，如 { level: 2 }）" }
}
```

**支持的属性**：`heading.level`、`heading.textAlign`、`paragraph.textAlign`、`code_block.language`、`todo.checked`。

**返回** `data`：`{ success, block_id, message? }`。
