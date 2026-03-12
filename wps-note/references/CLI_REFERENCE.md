# WPS Note CLI — 命令行工具参考

`wpsnote-cli` 是 WPS 笔记的命令行工具，将 MCP 工具封装为 shell 命令，适用于脚本自动化、终端工作流和 AI Agent 集成。

## 初始化方式

当前版本的 CLI 由 WPS 笔记桌面端负责安装和写入配置：

- 在桌面端 MCP 设置页点击安装 CLI
- 安装器会自动写入 `~/.wpsnote-cli/config.json`
- 当前**不存在** `wpsnote-cli setup` 命令

## 命令命名约定

- 本文档表格中的命令名以 `wpsnote-cli --help` / `wpsnote-cli schema` 可见的 **canonical 命令** 为准。
- 对少数未显式注册的工具，CLI 仍支持 **fallback alias**：把命令名从 `kebab-case` 自动映射为 MCP tool 名后直接调用。
- 因此像 `get-xml-reference`、`generate-image` 这类 tool 风格命令仍可运行，但它们不是 help/schema 主命令面。


## 全局选项

| 选项 | 说明 |
|------|------|
| `--json` | 以 JSON 格式输出（输出已解包为业务数据，无额外嵌套） |
| `--json-args <json>` | 以 JSON 传入全部参数（适用于数组/对象等复杂参数） |
| `-h, --help` | 显示帮助信息 |
| `-V, --version` | 显示版本号 |

## 命令速查表

### 元命令

| 命令 | 说明 |
|------|------|
| `status` | 检查与 MCP 服务的连接状态，显示服务地址和可用工具数量 |
| `schema` | 输出全部命令的 JSON Schema 描述（供 AI 使用） |

### 读取命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `list` | `list_notes` | 列出笔记（支持排序和分页） |
| `read` | `read_note` | 读取笔记全文（XML） |
| `outline` | `get_note_outline` | 获取笔记大纲和 block ID |
| `section` | `read_section` | 读取标题定义的章节 |
| `read-blocks` | `read_blocks` | 按 ID 读取指定 block |
| `search` | `search_note_content` | 在笔记内搜索文本 |
| `read-image` | `read_image` | 读取图片（CLI 返回本地文件路径） |
| `audio` | `get_audio_transcript` | 获取语音转写文本 |
| `xml-ref` | `get_xml_reference` | 获取 XML 格式参考文档 |

### 管理命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `create` | `create_note` | 创建空白笔记 |
| `info` | `get_note_info` | 获取笔记元数据（含标签） |
| `current` | `get_current_note` | 获取当前编辑中的笔记 |
| `find` | `search_notes` | 搜索笔记（关键词/标签/时间） |
| `tags` | `find_tags` | 列出或搜索标签 |
| `sync` | `sync_note` | 同步笔记到云端 |
| `delete` | `delete_note` | 删除笔记（不可恢复） |
| `stats` | `get_note_stats` | 获取笔记使用统计 |

### 编辑命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `edit` | `edit_block` | 编辑 block（replace/insert/delete/update_attrs） |
| `batch-edit` | `batch_edit` | 批量原子编辑 |
| `insert-image` | `insert_image` | 插入图片 |
| `gen-image` | `generate_image` | AI 文生图，返回图片 URL |

### 调试命令

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `logs` | `get_mcp_logs` | 查看 MCP 调试日志 |

### Fallback-only 工具

以下工具当前没有显式注册到 `wpsnote-cli --help` / `schema` 的 canonical 命令面，但可以通过 fallback 直接调用：

| CLI 命令 | MCP 工具 | 说明 |
|----------|----------|------|
| `get-cursor-block` | `get_cursor_block` | 获取当前光标所在顶层 block 的 `block_id`、`block_type` 和 `note_id` |

## CLI 特有行为

与 MCP 工具调用相比，CLI 有以下差异：

### read-image 返回本地路径

CLI 模式下 `read-image` 返回图片的**本地文件路径**而非 base64 数据，可直接用文件管理器或图片查看器打开。

```bash
wpsnote-cli read-image --note_id <id> --block_id <id>
# 输出: Image: /tmp/wpsnote-img-xxx.png (image/png, 800x600)
```

### insert-image 支持 src_file 参数

CLI 新增 `--src_file` 参数，从文件读取 base64 数据或 data URI，避免 shell 命令行长度限制。与 `--src` 二选一。

```bash
# 方式 1：直接传 URL
wpsnote-cli insert-image --note_id <id> --anchor_id <id> --position after --src "https://example.com/photo.png"

# 方式 2：通过文件传入 base64（适用于大图片）
wpsnote-cli insert-image --note_id <id> --anchor_id <id> --position after --src_file /path/to/base64.txt
```

`src_file` 文件内容可以是：
- 完整的 data URI（`data:image/png;base64,...`）
- 纯 base64 字符串（CLI 自动添加 `data:image/png;base64,` 前缀）

### 自动启动应用

当 MCP 服务不可达时，CLI 会自动尝试启动 WPS 笔记应用，并轮询等待服务就绪（最长 30 秒）

### Fallback 命令

未注册的命令名会自动转换为 MCP 工具名（将 `-` 替换为 `_`）并直接调用，无需预定义。适合临时直调 tool，但对外文档和自动化脚本优先使用 canonical 命令。

```bash
# canonical 命令
wpsnote-cli xml-ref --json

# fallback alias，等同于调用 MCP 工具 get_xml_reference
wpsnote-cli get-xml-reference --json

# canonical 命令
wpsnote-cli gen-image --prompt "系统架构图"

# fallback alias，等同于调用 MCP 工具 generate_image
wpsnote-cli generate-image --prompt "系统架构图"

# fallback-only 工具，当前无 canonical alias
wpsnote-cli get-cursor-block --json
```

## 使用示例

### 基础操作

```bash
# 检查连接状态
wpsnote-cli status

# 列出最近 5 篇笔记
wpsnote-cli list --limit 5

# 以 JSON 格式输出
wpsnote-cli list --limit 5 --json

# 搜索笔记
wpsnote-cli find --keyword "会议记录"

# 按标签筛选
wpsnote-cli find --tags '["工作"]'

# 读取笔记全文
wpsnote-cli read --note_id <id>

# 获取大纲
wpsnote-cli outline --note_id <id>

# 获取当前光标所在 block（fallback-only）
wpsnote-cli get-cursor-block --json

# 读取章节
wpsnote-cli section --note_id <id> --heading_block_id <block_id>
```

### 编辑操作

```bash
# 替换 block 内容
wpsnote-cli edit --note_id <id> --op replace --block_id <bid> --content "<p>新内容</p>"

# 插入 block
wpsnote-cli edit --note_id <id> --op insert --anchor_id <bid> --position after --content "<h2>新标题</h2>"

# 删除 block
wpsnote-cli edit --note_id <id> --op delete --block_ids '["bid1","bid2"]'

# 批量编辑（使用 --json-args 传入复杂参数）
wpsnote-cli batch-edit --json-args '{
  "note_id": "<id>",
  "operations": [
    { "op": "replace", "block_id": "<bid>", "content": "<p>更新</p>" },
    { "op": "insert", "anchor_id": "<bid>", "position": "after", "content": "<p>新段落</p>" }
  ]
}'
```

### 图片操作

```bash
# 读取图片（返回本地路径）
wpsnote-cli read-image --note_id <id> --block_id <bid>

# 通过 URL 插入图片
wpsnote-cli insert-image --note_id <id> --anchor_id <bid> --position after --src "https://example.com/photo.png"

# 通过文件插入大图片
wpsnote-cli insert-image --note_id <id> --anchor_id <bid> --position after --src_file /path/to/base64.txt
```

### AI 文生图

```bash
# 生成图片（返回图片 URL）
wpsnote-cli gen-image --prompt "一只橘猫坐在窗台上，水彩画风格，暖色调"

# 指定尺寸（竖版）
wpsnote-cli gen-image --prompt "山水画" --width 1536 --height 2688

# 生成并插入笔记（组合使用）
IMG_URL=$(wpsnote-cli gen-image --prompt "系统架构图" --json | jq -r '.data.image_url')
wpsnote-cli insert-image --note_id <id> --anchor_id <bid> --position after --src "$IMG_URL"
```

### 脚本自动化

```bash
# 获取当前笔记 ID 并读取大纲
NOTE_ID=$(wpsnote-cli current --json | jq -r '.data.note_id')
wpsnote-cli outline --note_id "$NOTE_ID" --json

# 搜索并批量处理
wpsnote-cli find --keyword "周报" --json | jq -r '.data.notes[].note_id' | while read id; do
  wpsnote-cli outline --note_id "$id" --json
done

# 输出全部命令的 JSON Schema（供 AI 集成）
wpsnote-cli schema
```

## 输出格式

### 默认模式（人类可读）

```
title: 2025年度工作总结
word_count: 8520
block_count: 45
blocks: [45 items]
  - {"id":"aB3kLm9xZq","type":"heading","preview":"第一章"}
  ...
```

### JSON 模式（`--json`）

直接输出业务数据，无额外包装层：

```json
{
  "ok": true,
  "code": "OK",
  "data": {
    "title": "2025年度工作总结",
    "word_count": 8520,
    "block_count": 45,
    "blocks": [...]
  }
}
```

工具调用失败时进程退出码为 1：

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
| `ToolError` | MCP 工具调用失败 | 参考错误码表（`ERROR_CODES.md`）进行恢复 |

CLI 层错误与 MCP 工具层错误相互独立——CLI 层处理连接状态，工具层错误码（如 `BLOCK_NOT_FOUND`、`EDITOR_NOT_READY`）通过工具返回值透传。
