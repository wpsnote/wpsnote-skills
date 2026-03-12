# WPS Note CLI — 命令行工具参考

`wpsnote-cli` 将 WPS 笔记 MCP 工具封装为终端命令，适用于脚本自动化、编辑器 Agent 和本地开发工作流。

## 安装与文件位置

当前 CLI 由 WPS 笔记桌面端负责安装和写入配置：

- 在桌面端 MCP 设置页点击安装 CLI
- 安装器会自动写入 `~/.wpsnote-cli/config.json`
- Windows 安装到 `%LOCALAPPDATA%/WPSNote/cli/wpsnote-cli.cmd`
- macOS / Linux 安装到 `~/.local/bin/wpsnote-cli`（链接到 `~/.wpsnote-cli/bin/wpsnote-cli`）
- 当前**不存在** `wpsnote-cli setup` 命令

注意：`wpsnote-cli status` 在“未配置”场景下仍会打印 `wpsnote-cli setup` 提示，这是遗留文案，不代表真实命令存在。

## 命令面与能力边界

- `wpsnote-cli --help` 当前暴露 `status`、`schema` 和 22 个 canonical 工具命令
- CLI 仍支持 fallback 直调 MCP tool：把工具名从 `snake_case` 改成 `kebab-case` 即可
- 当前可见但没有 canonical alias 的工具只有 `get_cursor_block`
- 当前隐藏但仍可 fallback 直调的兼容写工具有：`replace_block`、`insert_block`、`delete_blocks`、`update_block_attrs`
- fallback 命令当前只可靠支持 `--key=value`、`--json` 和 `--json-args=...`；不要依赖 `--key value` 这种分离写法
- MCP 的分页参数目前没有全部映射到 canonical 命令。需要手动分页时，优先改用 fallback 的 tool 风格命令：`get-note-outline`、`read-note`、`read-section`

## 全局选项

| 选项 | 说明 |
|------|------|
| `--json` | 以 JSON 格式输出；单个文本结果会直接解包为业务数据 |
| `--json-args <json>` | 以 JSON 传入全部参数；canonical 命令推荐这样传复杂对象/数组 |
| `-h, --help` | 显示帮助信息 |
| `-V, --version` | 显示版本号 |

## 命令速查表

### 元命令

| 命令 | 说明 |
|------|------|
| `status` | 检查连接状态，显示服务地址和可用工具数量 |
| `schema` | 输出 canonical 命令的 JSON Schema 描述（不含 fallback-only / hidden 工具） |

### 读取命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `list` | `list_notes` | 列出笔记，支持排序和分页 |
| `read` | `read_note` | 读取笔记全文；超大文档时实际返回 `pagination`。手动分页请用 fallback `read-note` |
| `outline` | `get_note_outline` | 获取笔记大纲；实际返回 `size_category`、`estimated_xml_chars`，大文档自动分页。手动分页请用 fallback `get-note-outline` |
| `section` | `read_section` | 读取标题章节。实际业务数据是 `{ heading, level, blocks, truncated, next_block_offset? }`；续读请用 fallback `read-section` |
| `read-blocks` | `read_blocks` | 按 ID 读取指定 block |
| `search` | `search_note_content` | 在笔记内搜索文本 |
| `read-image` | `read_image` | 读取图片；CLI 返回本地文件路径 |
| `audio` | `get_audio_transcript` | 获取语音转写文本 |
| `xml-ref` | `get_xml_reference` | 获取 XML 格式参考文档 |

### 管理命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `create` | `create_note` | 创建空白笔记 |
| `info` | `get_note_info` | 获取笔记元数据（含标签） |
| `current` | `get_current_note` | 获取当前编辑中的笔记；实际返回通常还会附带 `word_count`、`block_count`、`estimated_xml_chars`、`size_category` |
| `find` | `search_notes` | 搜索笔记（关键词 / 标签 / 时间范围） |
| `tags` | `find_tags` | 列出或搜索标签 |
| `sync` | `sync_note` | 同步笔记到云端 |
| `delete` | `delete_note` | 删除笔记（不可恢复） |
| `stats` | `get_note_stats` | 获取笔记使用统计 |

### 编辑命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `edit` | `edit_block` | 编辑 block（replace / insert / delete / update_attrs） |
| `batch-edit` | `batch_edit` | 批量原子编辑 |
| `insert-image` | `insert_image` | 插入图片 |
| `gen-image` | `generate_image` | AI 文生图，返回图片 URL |

### 调试命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `logs` | `get_mcp_logs` | 查看 MCP 调试日志 |

### fallback-only / hidden 工具

以下命令不在 `--help` / `schema` 的 canonical 命令面里，但当前 CLI 可以直接调用：

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `get-cursor-block` | `get_cursor_block` | 获取当前光标所在顶层 block |
| `replace-block` | `replace_block` | 隐藏兼容工具，推荐优先用 `edit --op replace` |
| `insert-block` | `insert_block` | 隐藏兼容工具，推荐优先用 `edit --op insert` |
| `delete-blocks` | `delete_blocks` | 隐藏兼容工具，推荐优先用 `edit --op delete` |
| `update-block-attrs` | `update_block_attrs` | 隐藏兼容工具，推荐优先用 `edit --op update_attrs` |

## 当前 CLI 与 MCP 的差异

### 分页参数未完全映射到 canonical 命令

MCP 已支持以下分页参数，但当前 canonical 命令还没有显式注册：

- `get_note_outline`: `offset`、`block_limit`
- `read_note`: `offset`、`block_limit`
- `read_section`: `block_offset`

需要手动分页时，直接使用 fallback 的 tool 风格命令：

```bash
wpsnote-cli get-note-outline --note_id=<id> --offset=100 --block_limit=50 --json
wpsnote-cli read-note --note_id=<id> --offset=100 --block_limit=50 --json
wpsnote-cli read-section --note_id=<id> --heading_block_id=<bid> --block_offset=50 --json
```

### `read_section` 的真实返回值是结构化 blocks

当前 `schema` / `--help` 的命令描述仍写着“返回 XML 内容”，但底层实际返回的是：

```json
{
  "heading": "详细设计",
  "level": 2,
  "blocks": [
    { "id": "abc123", "type": "paragraph", "content": "<p>...</p>", "attrs": {} }
  ],
  "truncated": true,
  "next_block_offset": 50
}
```

### `get_current_note` 的真实返回值包含文档统计

当当前笔记对应的编辑器已就绪时，CLI 实际会拿到并透传：

- `word_count`
- `block_count`
- `estimated_xml_chars`
- `size_category`

## CLI 特有行为

### `--json` 会解包业务数据

CLI 的 JSON 模式不是直接打印原始 MCP `CallToolResult`，而是尽量解包：

- 单个文本 JSON 结果：直接输出业务对象
- 单个纯文本结果：直接输出文本
- 多段内容结果：输出 `{ "content": [...] }`

### `read-image` 返回本地路径

CLI 会自动为 `read_image` 注入 `prefer_path=true`，因此默认拿到的是本地临时文件路径，而不是 base64。

```bash
wpsnote-cli read-image --note_id <id> --block_id <id>
# 输出: Image: C:\Users\...\AppData\Local\Temp\wpsnote-img-xxx.png (image/png, 800x600)
```

### `insert-image` 支持 `src_file`

CLI 新增 `--src_file` 参数，从文件读取 data URI 或 base64，绕过命令行长度限制：

```bash
# 直接传 URL
wpsnote-cli insert-image --note_id <id> --anchor_id <id> --position after --src "https://example.com/photo.png"

# 通过文件传入 data URI / base64
wpsnote-cli insert-image --note_id <id> --anchor_id <id> --position after --src_file /path/to/image.txt
```

`src_file` 文件内容可以是：

- 完整的 data URI（推荐，如 `data:image/png;base64,...`）
- 纯 base64 字符串。CLI 当前会把它包装成 `data:application/octet-stream;base64,...`

### 工具命令会自动尝试拉起桌面端

普通工具命令在 MCP 服务不可达时，会先探测 `/health`：

- 若服务已就绪，直接连接
- 若服务不可达，尝试启动 WPS 笔记桌面端
- 最长轮询等待 30 秒

### fallback 参数建议统一写成 `--key=value`

由于 fallback 走的是轻量参数解析器，推荐统一使用：

```bash
wpsnote-cli get-cursor-block --json
wpsnote-cli get-note-outline --note_id=<id> --offset=100 --json
wpsnote-cli replace-block --json-args='{"note_id":"<id>","block_id":"<bid>","content":"<p>新内容</p>"}' --json
```

## 使用示例

### 基础操作

```bash
wpsnote-cli status
wpsnote-cli list --limit 5
wpsnote-cli find --keyword "会议记录"
wpsnote-cli read --note_id <id>
wpsnote-cli outline --note_id <id> --json
wpsnote-cli get-cursor-block --json
```

### 手动分页读取大文档

```bash
wpsnote-cli get-note-outline --note_id=<id> --offset=0 --block_limit=100 --json
wpsnote-cli get-note-outline --note_id=<id> --offset=100 --block_limit=100 --json
wpsnote-cli read-note --note_id=<id> --offset=100 --block_limit=50 --json
wpsnote-cli read-section --note_id=<id> --heading_block_id=<bid> --block_offset=50 --json
```

### 编辑操作

```bash
wpsnote-cli edit --note_id <id> --op replace --block_id <bid> --content "<p>新内容</p>"
wpsnote-cli edit --note_id <id> --op insert --anchor_id <bid> --position after --content "<h2>新标题</h2><p>新段落</p>"
wpsnote-cli edit --note_id <id> --op delete --block_ids '["bid1","bid2"]'
wpsnote-cli batch-edit --json-args '{
  "note_id": "<id>",
  "operations": [
    { "op": "replace", "block_id": "<bid>", "content": "<p>更新</p>" },
    { "op": "insert", "anchor_id": "<bid>", "position": "after", "content": "<p>新段落</p>" }
  ]
}'
```

### 图片与文生图

```bash
wpsnote-cli read-image --note_id <id> --block_id <bid>
wpsnote-cli insert-image --note_id <id> --anchor_id <bid> --position after --src_file /path/to/image.txt
wpsnote-cli gen-image --prompt "一只橘猫坐在窗台上，水彩画风格，暖色调" --json
```

`gen-image --json` 的输出字段是解包后的业务对象，例如：

```json
{
  "url": "https://..."
}
```

把这个 `url` 再传给 `insert-image --src` 即可。

### 获取当前笔记并继续处理

```bash
wpsnote-cli current --json
wpsnote-cli find --keyword "周报" --json
wpsnote-cli schema
```

## 输出格式

### 默认模式（人类可读）

```text
title: 2025年度工作总结
word_count: 8520
block_count: 45
blocks: [45 items]
  - {"id":"aB3kLm9xZq","type":"heading","preview":"第一章"}
```

### JSON 模式（`--json`）

直接输出业务数据，无额外包装层：

```json
{
  "title": "2025年度工作总结",
  "word_count": 8520,
  "block_count": 45,
  "estimated_xml_chars": 13230,
  "size_category": "medium",
  "blocks": []
}
```

工具调用失败时，`--json` 会直接输出标准错误对象，进程退出码为 1：

```json
{
  "ok": false,
  "code": "BLOCK_NOT_FOUND",
  "message": "Block not found: xY7nPq2wRt",
  "retryable": false
}
```

## 错误处理

| 错误类型 | 场景 | 提示 |
|----------|------|------|
| `ConnectionError` | MCP 服务不可达 | 确认 WPS 笔记已运行且 MCP 服务已开启 |
| `AuthError` | API Key 无效或权限不足 | 重新通过桌面端安装 CLI，刷新配置 |
| `ToolError` | MCP 工具调用失败 | 参考错误码表（`ERROR_CODES.md`）进行恢复 |

CLI 层错误与 MCP 工具层错误相互独立：CLI 层处理连接、鉴权和拉起应用；工具层错误码（如 `BLOCK_NOT_FOUND`、`EDITOR_NOT_READY`、`RATE_LIMITED`）通过业务结果透传。
