# WPS Note Cloud CLI — 命令行工具参考

`wpsnote-cli` 是基于云端 MCP（`https://ainote.kdocs.cn/mcp-svc/mcp`）的官方命令行工具，按当前凭据权限动态发现 MCP 工具并生成命令参数，**不依赖 WPS 笔记桌面端或前端运行**。

## 环境要求与安装

- Node.js `>= 20.12.0`

```bash
npm install -g wpsnote-cli
# 或免安装临时运行：
npx wpsnote-cli --help
```

> **与旧版桌面端本地 CLI 冲突处理**：如果本机曾安装过桌面端自带的本地 `wpsnote-cli`，安装时会给出提示。请先升级桌面端，并在 WPS 笔记桌面端左下角账号菜单 → **AI 实验室** → **命令行工具** → **卸载**（清理旧 `~/.wpsnote-cli`），随后再使用云端 `wpsnote-cli`。

## 鉴权管理（`auth`）

### 方式一：浏览器 OAuth PKCE 登录（推荐）

```bash
wpsnote-cli auth login                 # 打开浏览器授权（交互选择权限范围）
wpsnote-cli auth login --scope read    # 指定只读
wpsnote-cli auth login --scope write   # 指定读写
wpsnote-cli auth login --scope destructive  # 读写+删除（Agent/--json 非交互默认）
wpsnote-cli auth login --no-browser    # 无浏览器环境打印授权 URL，等待本地回调
wpsnote-cli auth status --json         # 检查连接状态、过期时间、Scopes 与工具数量
wpsnote-cli auth renew                 # 凭据到期或 WPS 登录态失效后重新授权
wpsnote-cli auth logout                # 退出并清理本地凭据
```

### 方式二：导入 MCP 配置文件或 API Key

从 [https://ainote.kdocs.cn/mcp-svc/keys/page](https://ainote.kdocs.cn/mcp-svc/keys/page) 生成 API Key 后，可导入标准 MCP JSON 配置：

```bash
wpsnote-cli auth import ~/.config/mcp.json --json
# 若已知准确到期时间：
wpsnote-cli auth import ~/.config/mcp.json --expires-at 2026-12-31T23:59:59+08:00
```

也支持 stdin 导入或环境变量（优先级高于本地凭据文件）：

```bash
printf '%s' "$WPS_NOTE_API_KEY" | wpsnote-cli auth login --api-key-stdin
# 或在 CI/脚本中直接使用环境变量：
export WPS_NOTE_API_KEY="<your-api-key>"
# 或 export WPS_NOTE_ACCESS_TOKEN="<your-bearer-token>"
```

凭据默认保存在 `~/.wpsnote-cli/credentials.json`（权限 `0600`），非敏感配置在 `~/.wpsnote-cli/config.json`；可通过 `WPSNOTE_CLI_CONFIG_DIR` 覆盖目录。

## 发现工具与查看 Schema

云端 CLI 会根据当前凭据的 Scope 动态拉取可用工具：

```bash
wpsnote-cli tools list --json          # 列出当前凭据可调用的工具与 scope
wpsnote-cli tools describe edit_block  # 查看指定工具完整 inputSchema
wpsnote-cli schema                     # 导出全部可用工具 Schema
wpsnote-cli schema list_notes          # 查看单个工具 Schema
```

## 命令映射表

CLI 为常用 MCP 工具提供了 25 个内置短命令；其余工具可直接使用 kebab-case 名称（如 `get-notes-by-tag`、`add-note-tags`、`remove-note-tags`、`rename-tag`、`delete-tag`）或 `wpsnote-cli call <tool_name>`：

| CLI 命令 | MCP 工具 | Scope |
|---|---|---|
| `list` | `list_notes` | `read` |
| `info` | `get_note_info` | `read` |
| `find` | `search_notes` | `read` |
| `outline` | `get_note_outline` | `read` |
| `read` | `read_note` | `read` |
| `section` | `read_section` | `read` |
| `read-blocks` | `read_blocks` | `read` |
| `search` | `search_note_content` | `read` |
| `read-image` | `read_image` | `read` |
| `audio` | `get_audio_transcript` | `read` |
| `xml-ref` | `get_xml_reference` | `read` |
| `tags` | `list_tags` | `read` |
| `find-tags` | `find_tags` | `read` |
| `get-notes-by-tag` | `get_notes_by_tag` | `read` |
| `trash-list` | `list_trash` | `read` |
| `create` | `create_note` | `write` |
| `update-info` | `update_note_info` | `write` |
| `edit` | `edit_block` | `write` |
| `batch-edit` | `batch_edit` | `write` |
| `insert-image` | `insert_image` | `write` |
| `gen-image` | `generate_image` | `write` |
| `import-web` | `import_web_page` | `write` |
| `manage-tags` | `manage_note_tags` | `write` |
| `add-note-tags` | `add_note_tags` | `write` |
| `remove-note-tags` | `remove_note_tags` | `write` |
| `rename-tag` | `rename_tag` | `write` |
| `restore` | `restore_note` | `write` |
| `trash` | `trash_note` | `destructive` |
| `purge` | `permanently_delete_note` | `destructive` |
| `delete-tag` | `delete_tag` | `destructive` |

## 通用参数与输出格式

### 调用选项

| 选项 | 说明 |
|---|---|
| `--<field> <value>` | 按工具 `inputSchema` 动态生成的字段选项（如 `--note_id`、`--limit`） |
| `--args <json>` / `--json-args <json>` | 以 JSON 字符串传入参数对象 |
| `--args-file <path>` | 从 JSON 文件读取参数（强烈推荐用于含 XML、数组、嵌套对象的写操作） |
| `--set <key=value>` | 单独覆盖某个字段，可重复使用 |
| `--file <path>` | 仅用于 `insert-image`，读取本地图片（png/jpeg/gif/webp/bmp/ico，≤ 2 MiB）自动编码为 data URI 传入 `src` |
| `--dry-run` | 仅校验并输出将要发送的 `{ ok, dryRun, tool, scope, arguments }`，不实际执行 |
| `--yes` | `destructive` 工具必须显式传入，确认执行高危操作 |
| `--json` | 原样打印 JSON（工具调用会输出 MCP `CallToolResult` 对象） |
| `--lang <zh-CN\|en>` | 指定输出语言 |
| `--no-update-notice` | 禁止打印版本更新提示 |

> **参数优先级（低 → 高）**：`--args-file` < `--args` / `--json-args` < `--set` < 显式 `--<field>` 与位置参数。

### `--json` 输出结构说明

需要注意云端 CLI 与旧版桌面端 CLI 的输出区别：

- **非 `--json` 模式**：自动提取 `result.content` 中文本 JSON 并格式化打印。
- **`--json` 模式**：输出完整 MCP `CallToolResult`：
  ```json
  {
    "content": [{ "type": "text", "text": "{\"notes\":[...]}" }],
    "structuredContent": { "notes": [...] },
    "isError": false
  }
  ```
  脚本解析时优先读取 `structuredContent`；若无 `structuredContent`，再解析 `content[0].text` 为 JSON。工具返回错误时 CLI 以非 0 退出码退出。

> **脚本解析注意**：存在可更新版本时，CLI 默认会在 stdout 输出更新提示从而破坏 `json.loads()`。脚本化调用务必加上 `--no-update-notice`（如 `wpsnote-cli --no-update-notice list --json`）。

## 常用示例

### 读取与搜索

```bash
wpsnote-cli list --limit 20 --order_by update_time --order_direction DESC
wpsnote-cli find "季度总结"
wpsnote-cli info --note_id <id>
wpsnote-cli outline --note_id <id>
wpsnote-cli read --note_id <id>
wpsnote-cli tags
wpsnote-cli get-notes-by-tag --tag_id "<tag_id或path>"
```

### 编辑与插图

```bash
wpsnote-cli create --title "项目周报"
wpsnote-cli outline --note_id <id>

cat > /tmp/edit.json <<'EOF'
{
  "note_id": "<id>",
  "op": "insert",
  "anchor_id": "<block_id>",
  "position": "after",
  "content": "<h2>本周进展</h2><p>已完成云端迁移。</p>"
}
EOF
wpsnote-cli edit --args-file /tmp/edit.json --dry-run
wpsnote-cli edit --args-file /tmp/edit.json

# 插入本地图片（≤ 2 MiB 栅格图）
wpsnote-cli insert-image --note_id <id> --anchor_id <block_id> --position after --file ./diagram.png
```

### 标签与回收站

```bash
wpsnote-cli add-note-tags --note_id <id> --tag_names '["工作/周报"]'
wpsnote-cli trash --note_id <id> --yes        # 移入回收站（可恢复）
wpsnote-cli restore --note_id <id>            # 从回收站恢复
wpsnote-cli purge --note_id <id> --yes        # 永久删除（不可恢复，须先确认）
```

## 诊断与内置 Skill

```bash
wpsnote-cli doctor --json       # 检查 Node.js、配置权限、MCP 连通性与更新状态
wpsnote-cli update check        # 检查 npm 新版本
wpsnote-cli skills install      # 安装 CLI 内置的 wpsnote-cli Skill 到本地 Agent 目录
```
