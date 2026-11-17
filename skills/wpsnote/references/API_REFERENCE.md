# WPS Note Cloud MCP — API 参考

本文档对应云端 MCP 服务（`https://ainote.kdocs.cn/mcp-svc/mcp`）的 31 个实时工具（含 1 个已弃用兼容别名 `read_note_content`）。

## 认证与权限分层（Scopes）

通过 `X-API-Key` 或 OAuth Bearer Token 认证。服务端按当前凭据的 Scope 自动过滤 `tools/list` 返回的工具，并在 `tools/call` 时强制校验：

- `read`：只读读取与搜索
- `write`：创建、修改、标签写入、恢复、生图、导入网页
- `destructive`：`trash_note`、`permanently_delete_note`、`delete_tag`

---

## 一、读取与定位工具（`read` scope）

### 1. `list_notes`

获取用户的笔记列表，用于浏览、排序与按元信息筛选。

```json
{
  "order_by": { "type": "string", "description": "update_time（默认）| create_time | open_time" },
  "order_direction": { "type": "string", "description": "DESC（默认）| ASC" },
  "starred": { "type": ["null", "boolean"], "description": "true 仅星标；false 仅非星标；不传返回全部" },
  "has_todo": { "type": ["null", "boolean"], "description": "true 仅含待办；false 仅无待办；不传返回全部" },
  "keyword": { "type": "string", "description": "仅匹配标题与简介（全文搜索请用 search_notes）" },
  "start_date": { "type": "string", "description": "创建时间起始，格式 yyyy-mm-dd" },
  "end_date": { "type": "string", "description": "创建时间结束，格式 yyyy-mm-dd" },
  "limit": { "type": "integer", "description": "每页数量 20–100，默认 20" },
  "cursor": { "type": "string", "description": "游标，来自上一次返回的 next_cursor" }
}
```

**返回**：`{ notes: Note[], total, next_cursor, has_more }`（每个 `Note` 含 `note_id`、`title`、`file_name`、`intro`、`starred`、`has_todo`、`create_time`、`update_time`、`open_time`、`trash_status` 等；注意列表项默认不返回 `tags` 字段，查看某篇笔记的标签请调用 `get_note_info`）。

---

### 2. `get_note_info`

获取单篇笔记的元信息与标签列表（不返回正文）。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" }
}
```

**返回**：`{ note: Note, tags: Tag[] }`。注：云端不支持批量 `note_ids` 或 `page` 分页。

---

### 3. `get_note_outline`

获取笔记的文档结构大纲与规模统计，是获取顶层 `block_id` 的主要入口。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "max_depth": { "type": ["null", "integer"], "description": "标题最大深度，不传返回全部层级" },
  "include_preview": { "type": ["null", "boolean"], "description": "是否返回块预览，默认 true" },
  "preview_length": { "type": ["null", "integer"], "description": "预览字符数，默认 50" },
  "offset": { "type": ["null", "integer"], "description": "分页起始偏移量，默认 0" },
  "block_limit": { "type": ["null", "integer"], "description": "每次返回最大块数（默认约 100，传入须 > 0）" }
}
```

**返回要点**：`title`、`word_count`（全篇总字数）、`block_count`、`size_category`、`blocks[]`（含 `id`、`type`、`preview`、`attrs`）、`pagination`（含 `has_more`、`next_offset`）。

- `type === "image"`：可把 `id` 传给 `read_image`。
- `type === "note_audio_card"`：可把 `attrs.shorthand_id` 传给 `get_audio_transcript`。

---

### 4. `read_note`（及兼容别名 `read_note_content`）

读取笔记全文或分页正文（语义 XML 格式，块级标签含 `id` 属性）。`read_note_content` 为兼容旧客户端的已弃用别名，新调用统一使用 `read_note`。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "max_length": { "type": ["null", "integer"], "description": "返回最大字符数" },
  "offset": { "type": ["null", "integer"], "description": "分页起始偏移量，默认 0" },
  "block_limit": { "type": ["null", "integer"], "description": "每次返回最大块数（> 0）" }
}
```

**返回要点**：`{ title, word_count, content, truncated, pagination }`。超过 200 blocks 自动分页，使用 `pagination.next_offset` 续读。

---

### 5. `read_section`

按标题读取完整章节（从目标标题到下一个同级或更高级标题之间的全部 block）。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "heading_block_id": { "type": "string", "required": true, "description": "必须是 get_note_outline 返回的 heading 类型 block_id" },
  "include_subsections": { "type": ["null", "boolean"], "description": "是否包含子章节，默认 true" },
  "max_blocks": { "type": ["null", "integer"], "description": "最大返回块数，默认 50" },
  "block_offset": { "type": ["null", "integer"], "description": "截断时续读偏移量，填 pagination.next_offset" }
}
```

**返回**：`{ heading, level, word_count, content, truncated, pagination?, blocks?, next_block_offset? }`。

---

### 6. `read_blocks`

按 ID 批量读取指定块，或读取单个锚点块及其前后上下文。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "block_ids": { "type": ["null", "array"], "items": "string", "description": "模式 1：批量读取的 block_id 列表（与 block_id 二选一）" },
  "block_id": { "type": "string", "description": "模式 2：锚点 block_id（与 block_ids 二选一）" },
  "before": { "type": ["null", "integer"], "description": "锚点之前的块数" },
  "after": { "type": ["null", "integer"], "description": "锚点之后的块数" },
  "include_anchor": { "type": ["null", "boolean"], "description": "是否包含锚点本身，默认 true" }
}
```

**返回**：`{ blocks?: ContentBlock[], anchor_id?: string, word_count: number, content: string }`。

---

### 7. `search_note_content`

在单篇笔记内搜索文本，返回匹配块的 `block_id`、`type`、`content`（XML）和 `preview`。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "keywords": { "type": ["null", "array"], "items": "string", "description": "搜索关键词数组（优先使用；云端合并为一次查询）" },
  "query": { "type": "string", "description": "兼容单关键词，新调用优先用 keywords" },
  "max_results": { "type": ["null", "integer"], "description": "最大结果数，默认 10" }
}
```

**返回**：`{ results: [{ block_id, type, content, preview }] }`。

---

### 8. `search_notes`

全局全文搜索所有笔记，返回匹配摘要片段（`snippet`）和相关度评分（`score`）。

```json
{
  "keywords": { "type": ["null", "array"], "items": "string", "description": "关键词数组，最多 10 项（优先于 keyword）" },
  "mode": { "type": "string", "description": "any（默认）| all（同一索引分块需包含全部关键词）" },
  "keyword": { "type": "string", "description": "兼容单关键词" },
  "search_type": { "type": "string", "description": "text | image | audio | attachment | tag（不传搜全部）" },
  "limit": { "type": "integer", "description": "每页数量 1–50，默认 50" },
  "cursor": { "type": "string", "description": "分页游标，翻页时需保持 keywords/mode/search_type 不变" }
}
```

**返回**：`{ items: [{ note_id, title, snippet, score, update_time }], total, has_more, next_cursor, message }`。

> **注意**：不支持 `tags` / `since` / `before` / `starred` 参数。新写入的正文存在十几秒到约 1 分钟的全文索引延迟。

---

### 9. `read_image`

读取已持久化图片块（不超过 8 MiB）的实际内容，返回 MCP `ImageContent`（base64）及尺寸/alt 等元信息。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "block_id": { "type": "string", "required": true, "description": "来自 get_note_outline 且 type=image 的 block_id" }
}
```

---

### 10. `get_audio_transcript`

读取语音卡片（`NoteAudioCard`）的录音状态与转写句子。

```json
{
  "shorthand_id": { "type": "string", "required": true, "description": "来自 get_note_outline 中 note_audio_card 块的 attrs.shorthand_id" },
  "last_seconds": { "type": ["null", "integer"], "description": "仅返回最近多少秒内结束的句子（> 0）" },
  "last_count": { "type": ["null", "integer"], "description": "最多返回最后多少条句子（> 0）" }
}
```

**返回**：`{ shorthand_id, status, is_complete, duration, total_sentence_count, sentence_count, sentences: [{ sentence_id, speaker_name, text, start_time, end_time, is_optimized }] }`。

---

### 11. `get_xml_reference`

无参数。获取完整 XML 格式参考文档（同 MCP Resource `note://xml-reference`）。

---

## 二、创建、编辑与导入工具（`write` scope）

### 12. `create_note`

创建空白笔记。

```json
{
  "title": { "type": ["null", "string"], "description": "笔记标题，不传默认「未命名笔记」" }
}
```

**返回**：`{ note_id, title, starred, create_time, link_url }`。注意：云端不返回初始 `outline`，写正文前需调用 `get_note_outline({ note_id })`。

---

### 13. `update_note_info`

修改笔记标题或星标状态（不支持改正文或标签）。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "title": { "type": ["null", "string"], "description": "新标题（不可为空字符串；null 或不传不修改）" },
  "starred": { "type": ["null", "boolean"], "description": "是否星标（null 或不传不修改）" }
}
```

**返回**：`{ note, message }`。

---

### 14. `edit_block`

单操作编辑正文块。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "op": { "type": "string", "required": true, "description": "replace | insert | delete | update_attrs | move" },
  "block_id": { "type": "string", "description": "replace / update_attrs / move 目标顶层 block_id" },
  "block_ids": { "type": ["null", "array"], "items": "string", "description": "delete 目标顶层 block_id 数组" },
  "anchor_id": { "type": "string", "description": "insert / move 锚点顶层 block_id" },
  "position": { "type": "string", "description": "insert / move 相对位置：before | after" },
  "content": { "type": "string", "description": "replace / insert 的完整 XML 字符串（禁止纯文本、Markdown 或 [{type:\"text\"}] 数组）" },
  "attrs": { "type": "object", "description": "update_attrs 属性：heading {level, textAlign} | paragraph {textAlign} | code_block {language}" }
}
```

---

### 15. `batch_edit`

在同一笔记写锁事务内原子执行多个编辑操作（全部成功或全部回滚）。执行顺序固定：`delete → replace → update_attrs → move → insert`。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "operations": {
    "type": ["null", "array"],
    "required": true,
    "description": "操作对象列表，每项字段同 edit_block（含 op 及对应必需参数）"
  }
}
```

---

### 16. `insert_image`

在指定锚点前或后插入图片（图片不可通过 XML `<img/>` 创建）。

```json
{
  "note_id": { "type": "string", "required": true, "description": "笔记 ID" },
  "anchor_id": { "type": "string", "required": true, "description": "顶层锚点 block_id" },
  "position": { "type": "string", "required": true, "description": "before | after" },
  "src": { "type": "string", "description": "公开 HTTP/HTTPS 图片 URL 或解码后 ≤ 2 MiB 的 data URI（与 attachment_id 二选一）" },
  "attachment_id": { "type": "string", "description": "已上传到当前笔记的 KDocs 附件 object_id（与 src 二选一）" },
  "alt": { "type": "string", "description": "替代文本（可选）" }
}
```

**返回**：`{ block_id, attachment_id, width, height }`。

---

### 17. `generate_image`

AI 同步文生图，返回可访问图片 URL（配合 `insert_image` 插入笔记）。

```json
{
  "prompt": { "type": "string", "required": true, "description": "生图提示词（中英文均可）" },
  "width": { "type": "integer", "description": "宽度（像素），0 或不传默认 2688" },
  "height": { "type": "integer", "description": "高度（像素），0 或不传默认 1536" }
}
```

**返回**：`{ image_url, task_id }`。

---

### 18. `import_web_page`

从白名单域名（微信公众号、知乎、豆瓣等）抓取并转换网页为新笔记。

```json
{
  "url": { "type": "string", "required": true, "description": "白名单域名网页 URL" }
}
```

**返回**：`{ note_id, title, link_url, message, warnings? }`。

---

## 三、标签管理工具

> 标签名规范：多级用 `/` 分隔（如 `工作/项目`）；每级 1–20 字符、最多 10 级；禁止 `\ : * ? " < > |` 和 emoji。

### 19. `list_tags`（`read`）

分页获取全量标签（含所有层级）。

- 参数：`cursor?`（string）、`limit?`（integer, 1–100，默认 20）
- 返回：`{ tags: Tag[], next_token, has_more }`（注意分页游标字段为 `next_token`）

### 20. `find_tags`（`read`）

按关键词搜索标签，不传关键词时返回全部标签（超过 1000 个时 `truncated: true`）。

- 参数：`keywords?`（string[]，最多 10 项）、`mode?`（`any` | `all`）、`keyword?`（兼容单关键词）
- 返回：`{ tags: Tag[], total, truncated? }`（每个 `Tag` 含 `tag_id`、`name`、`path`、`level`、`parent_id`、`has_child` 等）

### 21. `get_notes_by_tag`（`read`）

获取指定标签下的笔记列表。

- 参数：`tag_id`（必填，优先传 `tag_id` 或完整 `path`，名称全局唯一时也可传标签名）、`order_by?`、`order_direction?`、`keyword?`、`limit?`（1–100，默认 20）、`cursor?`
- 返回：`{ tag_id, notes: Note[], next_cursor, has_more }`

### 22. `manage_note_tags`（`write`）

单篇或批量管理笔记文件级标签。

- 单篇模式：`note_id`、`add?`（标签名数组，不存在自动创建）、`remove?`（优先 `tag_id` 或完整 `path`；与 `add` 合计最多 100 项）
- 批量模式：`operations`（最多 100 项，每项 `{ note_id, add?, remove? }`，建议每批 ≤ 50 项；单项失败不回滚其他笔记）
- 兼容参数：`add_tag_names`、`remove_tag_ids`
- 返回：`{ mode, status, current_tags?, warnings?, results? }`

### 23. `add_note_tags`（`write`）

向单篇笔记增量追加标签（不存在自动创建）。

- 参数：`note_id`（必填）、`tag_names`（必填，`string[]`）
- 返回：`{ current_tags, warnings? }`

### 24. `remove_note_tags`（`write`）

从单篇笔记移除指定标签。

- 参数：`note_id`（必填）、`tag_ids`（必填，`string[]`）
- 返回：`{ current_tags, warnings? }`

### 25. `rename_tag`（`write`）

重命名标签末级名称，不影响笔记关联和子标签结构。

- 参数：`tag_id`（必填）、`new_name`（必填，单级名，不含 `/`）
- 返回：`{ tag }`

### 26. `delete_tag`（`destructive`）

⚠️ 永久删除指定标签及其所有子标签，并解除相关笔记的标签关联。

- 参数：`tag_id`（必填）

---

## 四、回收站管理工具

### 27. `list_trash`（`read`）

列出回收站中的笔记。

- 参数：`order_by?`（`update_time` | `create_time`）、`order_direction?`（`ASC` | `DESC`）、`keyword?`、`limit?`（1–50，默认 20）、`cursor?`
- 返回：`{ notes, next_cursor, has_more }`

### 28. `trash_note`（`destructive`）

将笔记移入回收站（可用 `restore_note` 恢复）。若为某标签下最后一篇笔记，相关空标签可能被自动清理。

- 参数：`note_id`（必填）
- 返回：`{ deleted_note_id, deleted_tag_ids, disconnected_tags, is_last_note, message }`

### 29. `restore_note`（`write`）

从回收站恢复笔记及其标签关联。

- 参数：`note_id`（必填，来自 `list_trash`）
- 返回：`{ restored_note_id, restored_tags, message }`

### 30. `permanently_delete_note`（`destructive`）

⚠️ 永久删除**已在回收站中**的笔记（不可恢复）。

- 参数：`note_id`（必填，须先通过 `trash_note` 移入回收站）
- 返回：`{ deleted_note_id, message }`
