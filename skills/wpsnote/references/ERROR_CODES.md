# WPS Note Cloud — 错误码与恢复参考

云端 MCP 服务与云端 `wpsnote-cli` 的错误格式、常见业务错误码及处理策略。

## 云端 MCP 错误响应格式

工具调用失败时，云端 MCP 返回 `CallToolResult`（`isError: true`），错误内容为 JSON：

```json
{
  "code": 4048002108,
  "message": "block not found",
  "retryable": false,
  "request_id": "mcp-173174..."
}
```

- `code`：10 位数字业务错误码（`note-mcp-server` 统一 `bizerr` 体系）。
- `message`：安全公开的错误说明。
- `retryable`：为 `true` 时可直接短暂等待后重试。
- `request_id`：请求追踪 ID，排查服务端问题时提供给技术支持。

## 常见错误码速查

### 鉴权与权限（401 / 403）

| 错误码 | 说明 | 可重试 | 恢复方法 |
|---|---|---|---|
| `4018001701` | 缺少 API Key / Bearer Token | 否 | 配置 `X-API-Key` 或运行 `wpsnote-cli auth login` |
| `4018001702` | API Key 无效或已过期 | 否 | 前往 [https://ainote.kdocs.cn/mcp-svc/keys/page](https://ainote.kdocs.cn/mcp-svc/keys/page) 重新生成，或 `wpsnote-cli auth renew` |
| `4018001703` | 绑定的 WPS 登录态已失效 | 否 | 重新登录 WPS 并刷新 Key / 执行 `wpsnote-cli auth renew` |
| `4018000001` | 用户认证失败 | 否 | 检查认证头与登录态 |
| `4038001704` | API Key Scope 权限不足 | 否 | 换用具备对应 scope（`write` / `destructive`）的凭据重新授权 |
| `4038000001` | 无权访问或只读权限受限 | 否 | 确认目标笔记属于当前账号且有写权限 |

### 参数与资源不存在（400 / 404）

| 错误码 | 说明 | 可重试 | 恢复方法 |
|---|---|---|---|
| `4008000001` / `4008000003` / `4008000004` / `4008000005` | 参数不合法、缺参、类型或范围错误 | 否 | 对照工具 `inputSchema`（CLI 可跑 `wpsnote-cli schema <tool>`）修正参数 |
| `4048001802` | 工具不存在或当前 Scope 未开放 | 否 | 运行 `tools/list` 或 `wpsnote-cli tools list` 检查可用工具 |
| `4048001901` | 笔记不存在或已在回收站中 | 否 | 用 `list_notes` / `search_notes` / `list_trash` 确认有效 `note_id` |
| `4048002001` | 标签不存在 | 否 | 用 `find_tags` / `list_tags` 获取有效 `tag_id` 或 `path` |
| `4048002107` | 语音转写不存在或 `shorthand_id` 无效 | 否 | 从 `get_note_outline` 中 `note_audio_card` 的 `attrs.shorthand_id` 获取 |
| `4048002108` | `block_id` / `anchor_id` 不存在或不是顶层块 | 否 | 调用 `get_note_outline` 刷新顶层 `block_id`（勿传容器内部子块 id） |

### 内容与媒体校验（400）

| 错误码 | 说明 | 可重试 | 恢复方法 |
|---|---|---|---|
| `4008002103` | 不支持通过 XML 创建图片 | 否 | 使用 `insert_image` 工具（或 `wpsnote-cli insert-image --file ...`） |
| `4008002104` | 目标 block 类型不符合要求（如 `read_section` 传入非 `heading` 块） | 否 | 检查 `get_note_outline` 中该块的 `type` |
| `4008002105` | XML 内容格式或嵌套结构不合法 | 否 | 调用 `get_xml_reference` 核对标签、属性、闭合和嵌套规则；注意 `content` 必须是 XML 字符串 |
| `4008002106` | `insert_image` 获取图片失败（URL 不可访问、非图片 MIME、或 data URI 超过 2 MiB） | 是/否 | 改用直接返回 `image/*` 的公开 URL、≤ 2 MiB 的栅格图 data URI，或先上传附件后传 `attachment_id` |

### 超时、繁忙与服务端异常（5xx）

| 错误码 | 说明 | 可重试 | 恢复方法 |
|---|---|---|---|
| `5038002102` | 内容服务繁忙（队列满） | **是** | 短暂退避等待后重试 |
| `5048002101` | 内容服务请求超时 | 是 | 读取时减小 `block_limit` 分页；写入时拆分过大的 `batch_edit` |
| `5008001801` / `5008000001` | 工具执行失败或内部错误 | 是 | 先回读目标笔记确认是否已部分生效，避免重复写入，再决定是否重试 |

## 云端 CLI 特有错误码

| 错误码 | 含义 | 处理方法 |
|---|---|---|
| `AUTH_FAILED` | 本地缓存凭据无效、已过期，或绑定的 WPS 登录态已失效 | 运行 `wpsnote-cli auth renew` 重新授权（或重新执行 `auth login` / `auth import`） |
| `SCOPE_REQUIRED` | 调用了超出当前凭据 Scope 的短命令 | 按提示运行 `wpsnote-cli auth login --scope write` 或 `--scope destructive` |
| `CONFIRMATION_REQUIRED` | 调用 `destructive` 工具未传 `--yes` | 经用户确认后显式加上 `--yes` |
| `MISSING_ARGUMENTS` / `INVALID_ARGUMENT` / `INVALID_JSON` | 必填参数缺失或 `--args` JSON 格式错误 | 检查 `wpsnote-cli schema <tool>`，复杂内容改用 `--args-file` |
| `TOOL_FAILED` | MCP 工具返回 `isError: true` | 查看 stderr/stdout 中的服务端错误码与 `request_id` |

## 典型故障恢复模式

1. **写入报 `4048002108`（block not found）**：编辑会使其他块 ID 变化，或传入了容器内部段落 ID → 立即调用 `get_note_outline` 重新获取顶层 `block_id`。
2. **`search_notes` 搜不到刚写入的笔记**：云端全文索引有十几秒到约 1 分钟延迟 → 改用 `list_notes({ keyword })` 按标题筛选，或已知 `note_id` 时用 `search_note_content` 直接检索。
3. **写操作返回超时或未知错误**：重试前先调用 `get_note_outline` 或 `read_note` 检查前一次写入是否已落库，避免重复插入内容。
