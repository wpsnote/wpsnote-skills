# WPS Note MCP — 错误码参考

完整的错误码参考、hints 系统说明和恢复模式。

## 错误码表

| 错误码 | 含义 | 可重试 | 恢复方法 |
|--------|------|--------|----------|
| `OK` | 操作成功 | — | — |
| `INVALID_PARAMS` | 参数缺失或类型错误 | 否 | 检查 inputSchema，修正参数类型和必填字段 |
| `EDITOR_NOT_READY` | 笔记编辑器仍在加载中 | 是 | 等待片刻后重试 |
| `NO_ACTIVE_EDITOR_WINDOW` | 没有打开的笔记窗口 | 是 | 请用户打开笔记窗口，然后重试 |
| `NOTE_NOT_FOUND` | 指定的 note_id 无效或笔记不存在 | 否 | 使用 `list_notes` 或 `search_notes` 获取有效 note_id；若当前笔记则用 `get_current_note` |
| `BLOCK_NOT_FOUND` | 文档中不存在该 block ID | 否 | 重新获取大纲（`get_note_outline`）或搜索（`search_note_content`）以获取有效 block ID |
| `INVALID_BLOCK_TYPE` | 操作所需的 block 类型不匹配 | 否 | 检查 block 类型是否正确（如 `read_section` 需要 `heading`） |
| `INVALID_CONTENT` | XML/Markdown 内容无法解析为有效 blocks | 否 | 检查 message 中的具体 warnings，修正不合规的标签或结构后重试 |

| `DOCUMENT_READ_ONLY` | 笔记 token 为只读 | 否 | 无法写入此笔记——告知用户 |
| `FRONTEND_TIMEOUT` | 前端未在规定时间内响应 | 是 | 尝试缩小读取范围或稍后重试 |
| `IMAGE_FETCH_FAILED` | 图片 URL 无法访问或非有效图片 | 是 | 检查 URL 是否直接指向图片资源（非 HTML 页面），修正后重试 |
| `GENERATE_IMAGE_FAILED` | 文生图失败（白名单未授权/内容违规/Prompt 过长/未登录） | 否 | 根据具体原因修改 prompt 或联系管理员 |
| `RATE_LIMITED` | 调用频率超限 | 是 | 等待 60 秒后重试（`generate_image` 每用户每分钟限 1 次） |
| `WEBSOCKET_NOT_CONNECTED` | 网络断开或 WebSocket 未连接 | 是 | 检查网络连接，等待 WebSocket 自动重连后重试 |
| `INTERNAL_ERROR` | 服务端未预期错误 | 是 | 重试；若持续失败，检查 `get_mcp_logs` 获取诊断信息 |

## Hints 系统

工具调用失败时，响应中可能包含 `hints` 数组，提供建议的后续操作：

```json
{
  "ok": false,
  "code": "BLOCK_NOT_FOUND",
  "message": "Block not found: xY7nPq2wRt",
  "retryable": false,
  "hints": [
    { "tool": "search_note_content", "reason": "先搜索定位有效的 block_id，再执行写入操作" },
    { "tool": "get_note_outline", "reason": "刷新大纲并重新确认 block_id" }
  ]
}
```

### Hint 字段

| 字段 | 说明 |
|------|------|
| `tool` | （可选）建议接下来调用的 MCP 工具 |
| `reason` | 解释为什么推荐此操作 |

**当响应包含 hints 时，请始终遵循其建议。** 它们提供了最快的恢复路径。

### 成功响应中的 hints

block 编辑工具（`edit_block`、`batch_edit`、`insert_block`、`replace_block`、`delete_blocks`、`update_block_attrs`、`insert_image`）成功执行后，响应中也会包含 `hints`，根据返回值智能区分：

**含 `last_block_id` 时**（insert 操作）——引导链式插入，避免冗余 outline 调用：

```json
{
  "ok": true,
  "code": "OK",
  "data": { "new_block_ids": ["abc"], "last_block_id": "abc" },
  "hints": [
    { "reason": "Block IDs have changed. For sequential inserts, use the returned last_block_id as anchor_id directly. For operations on other blocks, call get_note_outline first to refresh IDs." }
  ]
}
```

**无 `last_block_id` 时**（replace / delete / update_attrs 等）——引导刷新 outline：

```json
{
  "ok": true,
  "code": "OK",
  "data": { ... },
  "hints": [
    { "tool": "get_note_outline", "reason": "Block IDs may have changed after this edit. Call get_note_outline to get fresh block IDs before your next write operation." }
  ]
}
```

## 错误恢复模式

### NOTE_NOT_FOUND → 获取有效 note_id

传入的 `note_id` 无效或笔记不存在（如路径找不到、ENOENT、无效 ID）。

```
1. list_notes({ limit: 50 }) 或 search_notes({ query: "..." })  → 获取有效 note_id
2. 若操作的是当前打开的笔记：get_current_note()  → 获取当前 note_id
3. 使用新的 note_id 重试原操作
```

### BLOCK_NOT_FOUND → 重新定位 block

这是编辑过程中最常见的错误。任何写入操作后，block ID 都可能失效。

```
1. get_note_outline({ note_id })        → 获取最新的 block 列表
2. search_note_content({ note_id, query: "你要定位的文本" })
   → 找到新的 block_id
3. 使用新的 block_id 重试原写入操作
```

### EDITOR_NOT_READY → 等待后重试

编辑器仍在初始化中，通常 1-2 秒内可恢复。

```
1. 短暂等待
2. 重试相同的工具调用
3. 若重试 3 次仍失败，请用户检查笔记应用是否正常响应
```

### NO_ACTIVE_EDITOR_WINDOW → 确保窗口已打开

当前没有活跃的笔记编辑器窗口。

```
1. 告知用户："请在 WPS 笔记中打开一篇笔记"
2. 用户确认窗口已打开后重试
```

### INVALID_CONTENT → 检查 warnings 并修正 XML/内容

XML 或 Markdown 内容解析后未能产生任何有效 block。`message` 字段中包含解析器收集的具体 warnings，指明哪些标签或结构不合规。

常见原因：
- 使用了不支持的 XML 标签（如 `<div>`、`<section>` 等 HTML 标签）
- XML 结构嵌套违规（如 `<p>` 内嵌套 `<table>`）
- 使用了只读标签（`<img/>`、`<embed/>`、`<imageColumn/>`）——应使用 `insert_image` 工具
- 容器结构不完整（如 `<table>` 缺少 `<tr>`、`<columns>` 缺少 `<column>`）
- Schema content model 校验不通过（子节点组合不符合节点类型定义）

```
1. 阅读 message 中的 warnings 列表，定位具体的问题标签
2. 参考 MCP Server Instructions 中注入的 XML 格式说明，据此修正内容
3. 重试写入操作
```

### DOCUMENT_READ_ONLY → 不可重试

笔记拥有只读 token，写入操作无法成功。

```
1. 不要重试——这是该 token 的永久状态
2. 告知用户此笔记为只读
3. 所有读取操作仍可正常使用
```

### FRONTEND_TIMEOUT → 缩小范围或重试

前端操作超时，通常由文档过大导致。

```
1. 如果是读取：使用 read_note 的分页参数（offset + block_limit）分批读取，
   或使用 read_section / read_blocks 缩小范围
2. 如果是写入：尝试拆分为更小的 batch_edit 操作
3. 重试操作
```

### 分页相关：offset 越界

**现象**：`read_note` 传入的 `offset` 大于等于文档总 block 数，或 `read_section` 的 `block_offset` 超过章节 block 数。

**说明**：这不是错误，工具仍返回 `ok: true`，但内容为空：
- `read_note`：`content` 为空，`pagination.has_more: false`，`pagination.returned_blocks: 0`
- `read_section`：`blocks` 为空数组，`truncated: false`

**处理**：当 `has_more: false` 时停止分页，无需继续调用。

### INVALID_BLOCK_TYPE → 使用正确的 block 类型

操作要求特定的 block 类型，但实际不匹配。

最常见场景：`read_section` 需要 `heading` block，但传入了 `paragraph`。

```
1. get_note_outline({ note_id })  → 检查 block 类型
2. 选择具有正确类型的 block
3. 重试操作
```

### IMAGE_FETCH_FAILED → 修正图片来源

`insert_image` 工具无法获取或识别提供的图片来源。

常见原因：
- 当前实现走在线上传，调用时设备处于离线状态
- URL 返回 HTTP 4xx/5xx（如 404 Not Found）——URL 路径错误或资源已下架
- URL 指向 HTML 页面而非图片文件——需使用图片的直接链接（如 Wikimedia 的 `upload.wikimedia.org/...` 而非文件描述页面）
- URL 存在重定向但最终未返回图片内容
- 响应的 MIME 类型不是 `image/*`（不支持的格式）
- 直接传入本地文件路径——当前环境不允许直接读取，需转为 base64 data URI

```
1. 检查 message 中的具体错误原因（HTTP 状态码、MIME 类型等）
2. 修正 src 参数：确保 URL 直接返回图片内容；若来源是本地文件，先读取文件并转为 base64 data URI
3. 使用修正后的 src 重试 insert_image
```

### GENERATE_IMAGE_FAILED → 修正 prompt 或联系管理员

`generate_image` 工具的专属错误码，涵盖多种失败场景。

```
1. 检查 message 中的具体原因：
   - "Whitelist check failed" → 用户未获授权，联系管理员
   - "content violation" / "内容违规" → 修改 prompt，移除违规内容
   - "Prompt is too long" → 缩短 prompt 到 500 字符以内
   - "not logged in" → 用户需登录后重试
2. 修正后再重试 generate_image
```

### RATE_LIMITED → 等待后重试

调用频率超出限制。`generate_image` 为每用户每分钟 1 次。

```
1. 等待 60 秒
2. 重试相同的工具调用
3. 若仍失败，告知用户等待更长时间
```

### WEBSOCKET_NOT_CONNECTED → 等待重连

网络断开或 WebSocket 连接中断，通常由网络切换或长时间后台导致。

```
1. 检查网络连接是否正常
2. 等待 WebSocket 自动重连（通常几秒内恢复）
3. 重试操作
4. 若持续失败，请用户检查网络环境
```

### INTERNAL_ERROR → 通过日志诊断

服务端发生了未预期的错误。

```
1. 先重试一次——瞬态错误可能自行恢复
2. 若持续失败：get_mcp_logs({ limit: 10 })  → 查看最近的错误日志
3. 仍然失败则将错误日志详情反馈给用户
```
