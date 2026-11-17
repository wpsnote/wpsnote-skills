---
name: wpsnote
description: 通过云端 MCP（wpsnote）或云端 CLI（wpsnote-cli）读取、编辑和管理 WPS 笔记。基于 block 文档模型，正文内容以语义 XML 格式交换，文件级标签与回收站通过专用工具管理。当用户说"帮我看看笔记"、"搜索笔记"、"创建一篇笔记"、"编辑笔记内容"、"整理标签"、"恢复回收站笔记"，或提到 WPS 笔记、WPS Note、云笔记时使用。也适用于排查云端 MCP / CLI 调用与鉴权问题。
metadata:
  mcp-server: wpsnote
  version: "2.0.0"
  category: productivity
  tags: [note-taking, document-editing, wps, cloud]
---

# WPS Note Skill（wpsnote）

默认基于 **WPS 笔记云端 MCP**（`https://ainote.kdocs.cn/mcp-svc/mcp`）与 **云端 CLI**（`npm install -g wpsnote-cli`），不依赖 WPS 笔记桌面端运行。

核心操作模式：**先定位（list / search / outline）→ 再读取（read_note / read_section / read_blocks）→ 最后编辑（edit_block / batch_edit）**。所有正文内容以语义 XML 格式交换，块定位基于顶层 `block_id`。

## 快速接入

### 方式一：云端 MCP（推荐用于 IDE / 桌面 Agent）

1. 打开 [https://ainote.kdocs.cn/mcp-svc/keys/page](https://ainote.kdocs.cn/mcp-svc/keys/page) 登录并生成 API Key（可选 `read` / `write` / `destructive` 权限）。
2. 在客户端的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "wpsnote": {
      "url": "https://ainote.kdocs.cn/mcp-svc/mcp",
      "headers": {
        "X-API-Key": "<your-api-key>"
      }
    }
  }
}
```

### 方式二：云端 CLI（推荐用于终端 Agent / 脚本）

要求 Node.js >= 20.12：

```bash
npm install -g wpsnote-cli
wpsnote-cli auth login          # 浏览器 OAuth PKCE 授权（推荐）
# 或从已有 MCP 配置导入 Key：
# wpsnote-cli auth import ~/.config/mcp.json
wpsnote-cli auth status --json  # 验证鉴权与可用工具数
```

> 若本机曾安装过旧版桌面端本地 `wpsnote-cli`，按提示在 WPS 笔记桌面端「AI 实验室 → 命令行工具 → 卸载」清理 `~/.wpsnote-cli` 后再安装云端版本。

## 权限与安全边界

云端服务按 API Key / OAuth Scope 动态过滤可见工具与调用权限：

| Scope | 包含能力 |
|---|---|
| `read` | 列出笔记/标签/回收站、读取元数据/大纲/正文/章节/块/图片/语音转写、全文搜索、获取 XML 参考 |
| `write` | 创建笔记、修改标题/星标、编辑正文、插入/生成图片、导入网页、管理/重命名标签、从回收站恢复 |
| `destructive` | `trash_note`（移入回收站）、`permanently_delete_note`（永久删除）、`delete_tag`（删除标签及子标签） |

- **高危操作必须确认**：`permanently_delete_note` 与 `delete_tag` 不可恢复；`trash_note` 在笔记为某标签最后一篇时可能触发空标签清理。CLI 中所有 `destructive` 工具必须显式传 `--yes`，且仅在用户明确确认后执行。
- **不返回/不猜测不可用工具**：若当前凭据为 `read` 或 `write` 权限，更高权限工具不会出现在 `tools/list` 中；请引导用户升级授权（如 `wpsnote-cli auth renew` 或重新签发 Key），不要绕过限制。

## 与旧版桌面端接口的关键差异

若你曾使用旧版桌面端接口，注意以下云端接口变化：

- **无客户端 UI 状态工具**：云端没有 `get_current_note`、`get_cursor_block`、`sync_note`、`get_note_stats`、`get_mcp_logs`，也没有旧隐藏工具 `replace_block` / `insert_block` / `delete_blocks` / `update_block_attrs`。
  - 未指定 `note_id` 时，用 `list_notes` / `search_notes` 定位目标笔记，必要时向用户确认。
  - 云端写入直接持久化，无需调用 `sync_note`。
- **删除分两步**：`delete_note` 已拆分为 `trash_note`（移入回收站）→ `restore_note`（恢复）或 `permanently_delete_note`（永久删除，须先在回收站中）。
- **`create_note` 不返回 outline**：返回 `{ note_id, title, starred, create_time, link_url }`（不再返回 `fileId` / `linkUrl` / `outline`）。写入正文前需先调用 `get_note_outline({ note_id })` 获取初始 `block_id`。
- **`list_notes` 参数与分页**：使用 `order_by`（`update_time`/`create_time`/`open_time`）、`order_direction`（`ASC`/`DESC`）、`cursor`、`limit`（20–100）、`keyword`（仅标题和简介）、`starred`、`has_todo`、`start_date` / `end_date`（`yyyy-mm-dd`）；不再使用 `sort` / `direction` / `page` / `page_size` / `since` / `before`。
- **`get_note_info` 仅支持单篇**：只接受单个 `note_id`，不再支持 `note_ids` 批量或 `page` 分页；批量浏览请用 `list_notes`。
- **`search_notes` 参数与延迟**：接受 `keywords`（数组，最多 10 项，优先于 `keyword`）、`mode`（`any`/`all`）、`search_type`（`text`/`image`/`audio`/`attachment`/`tag`）、`limit`（1–50）、`cursor`；不支持 `tags` / `since` / `before` / `starred` 筛选。刚写入的正文全文索引通常有十几秒到约 1 分钟延迟；按标题找用 `list_notes`，已知 `note_id` 找段落用 `search_note_content`。
- **按标签筛选笔记**：使用 `find_tags` / `list_tags` 获取 `tag_id` 或完整 `path`，再调用 `get_notes_by_tag`。
- **`insert_image` 输入方式**：`src`（公开 HTTP/HTTPS URL 或解码后 ≤ 2 MiB 的 `data:image/...;base64,...`）与 `attachment_id` 二选一，服务端不读取本地路径；使用云端 CLI 时可用 `--file ./img.png` 自动转为 data URI 上传。

## 核心概念

### Block 模型

- 笔记由 block 组成，每个顶层 block 有唯一 `block_id`。
- block 类型：`paragraph`、`heading`（`<h1>`–`<h6>`）、`blockquote`、`code_block`、`list`（`<p listType="bullet|ordered|todo">`）、`table`、`image`、`image_column`、`horizontal_rule`、`highlight_block`、`columns`、`embed`、`note_audio_card`。
- **只读块**：`<img/>`、`<imageColumn>`、`<embed/>`、`<NoteAudioCard/>` 不可通过 XML 创建或 `replace`；但 `edit_block(op="move")` 支持移动任意块（包括图片和嵌入块），且移动后 `block_id` 不变。
- **语音转写**：大纲中 `type="note_audio_card"` 的 `attrs.shorthand_id` 可传给 `get_audio_transcript` 获取转写文本（支持 `last_seconds`、`last_count`）。
- **图片读取**：大纲中 `type="image"` 的 `block_id` 可传给 `read_image` 获取实际图片（支持 ≤ 8 MiB 已持久化图片）。
- **表格与容器嵌套限制**：
  - 表格必须**整表替换**，不支持单独编辑单元格；`<td>` 仅支持简单块（段落、标题、引用、代码块、分隔线、图片），不可嵌套 `<highlightBlock>`、`<columns>`、`<table>`。
  - `<highlightBlock>` 内仅支持简单块，不可嵌套 `<highlightBlock>`、`<columns>`、`<table>`。
  - `<columns>` 的每个 `<column>` 内支持简单块和 `<highlightBlock>`，不可嵌套 `<table>` 或 `<columns>`。

### XML 输入输出

- 正文以语义 XML 收发：`<p>`、`<h1>`–`<h6>`、`<blockquote>`、`<codeblock lang="...">`、`<hr/>`、`<table>`、`<highlightBlock>`、`<columns>` 等。
- 行内标记：`<strong>`、`<em>`、`<s>`、`<u>`、`<a href="..." title="...">`、`<tag>`；行内自闭合元素：`<emoji value="😀"/>`、`<latex formula="E=mc^2"/>`、`<br/>`。
- 样式通过 `<span>` 传递：`fontColor`、`fontHighlightColor`、`fontSize`。
- **顶层 ID 约束**：`edit_block` / `batch_edit` / `insert_image` 的 `block_id` 与 `anchor_id` 只接受顶层 block ID（来自 `get_note_outline`）；容器内部段落的 `id` 仅供阅读参考。
- **ID 规则**：`replace` 时根块 `id` 可省略（若提供必须等于目标 `block_id`）；`insert` 时必须省略块级 `id`，系统自动分配新 ID。
- **颜色受预设色板约束**，任意 hex 色值会被静默丢弃：
  - `fontColor`（12 色）：`#080F17` `#C21C13` `#DB7800` `#078654` `#0E52D4` `#0080A0` `#757575` `#DA326B` `#D1A300` `#58A401` `#116AF0` `#A639D7`
  - `fontHighlightColor`（9 色）：`#FBF5B3` `#F8D7B7` `#F7C7D3` `#DFF0C4` `#C6EADD` `#D9EEFB` `#D5DCF7` `#E6D6F0` `#E6E6E6`
  - `highlightBlock`（6 对 bg→border）：`#FAF1E6`→`#FEC794`、`#FAE6E6`→`#F2A7A7`、`#E6FAEB`→`#AFE3BB`、`#E6EEFA`→`#98C1FF`、`#F5EBFA`→`#E5B5FD`、`#EBEBEB`→`#C5C5C5`
  - `columnBackgroundColor`（42 色）：
    - 6 基础色：`#FFF5EB` `#FFECEB` `#E8FCEF` `#EBF2FF` `#FAF0FF` `#F2F2F2`
    - 18 扩展纯色：`#FCFAE1` `#FEF6E7` `#FFF5ED` `#FFF2F0` `#FFF2F4` `#FFF0F7` `#EEFFEB` `#EBFFF5` `#E8FCFC` `#EBF8FF` `#EBF1FF` `#F0EDFF` `#F2E7E4` `#F0E6DA` `#F5EEDA` `#EDF0EB` `#EDEEF0` `#F0E4DD`
    - 6 饱和色：`#FEF49C` `#BCFAAF` `#ADF4FF` `#C2D3FF` `#FFC7C7` `#E0E0E0`
    - 12 渐变色：CSS `linear-gradient()`，如 `linear-gradient(133deg,#FFFAF7 2.14%,#FFEDFE 96.88%)`
- 不确定 XML 写法时，调用 `get_xml_reference`（或读取 MCP Resource `note://xml-reference`；CLI 用 `wpsnote-cli xml-ref`）。

### 标签规则

- **文件级标签优先用专用工具**：`manage_note_tags`、`add_note_tags`、`remove_note_tags`、`rename_tag`、`delete_tag`，不要用 `edit_block` / `batch_edit` 修改标签。
- 多级标签用 `/` 分隔（如 `工作/项目/前端`）；每级 1–20 个字符、最多 10 级；禁止 `\ : * ? " < > |` 和 emoji。
- 调用 `manage_note_tags` / `add_note_tags` 时参数**不要带 `#` 前缀**；XML `<tag>` 内文本必须以 `#` 开头（如 `<tag>#工作/项目</tag>`）。
- 调用 `manage_note_tags` 的 `remove` 或 `get_notes_by_tag` 时，优先传 `tag_id` 或完整 `path`（避免同名末级标签产生歧义）。

## 工具总览（31 个）

### 1. 读取与定位（12 个，均为 `read` scope）

| MCP 工具 | CLI 短命令 | 用途 |
|---|---|---|
| `list_notes` | `list` | 列出笔记，支持 `order_by`/`order_direction`/`starred`/`has_todo`/`keyword`（仅标题和简介）/`start_date`/`end_date`/`limit`(20–100)/`cursor` |
| `get_note_info` | `info` | 获取单个笔记元信息与标签（仅 `note_id`） |
| `get_note_outline` | `outline` | 获取大纲（`title`/`word_count`/`block_count`/`size_category`/`blocks`/`pagination`），支持轻量模式 `max_depth`/`include_preview:false` |
| `read_note` | `read` | 读取正文 XML（>200 blocks 自动分页，用 `pagination.next_offset` 续读） |
| `read_note_content` | — | `read_note` 的已弃用兼容别名，新调用请用 `read_note` |
| `read_section` | `section` | 按标题 `heading_block_id` 读取章节，支持 `include_subsections`、`max_blocks`、`block_offset` |
| `read_blocks` | `read-blocks` | 按 `block_ids` 批量读取，或按 `block_id` + `before`/`after` 读上下文 |
| `search_note_content` | `search` | 单篇内搜索，优先传 `keywords`（数组），兼容 `query` |
| `search_notes` | `find` | 全局全文搜索（`keywords`、`mode: any\|all`、`search_type: text\|image\|audio\|attachment\|tag`、`limit` 1–50、`cursor`） |
| `read_image` | `read-image` | 读取已持久化图片块（≤ 8 MiB）的 base64 与尺寸信息 |
| `get_audio_transcript` | `audio` | 获取语音卡片（`shorthand_id`）的录音状态与转写句子（含 `speaker_name`） |
| `get_xml_reference` | `xml-ref` | 获取完整 XML 格式参考文档 |

### 2. 创建、编辑与导入（7 个，均为 `write` scope）

| MCP 工具 | CLI 短命令 | 用途 |
|---|---|---|
| `create_note` | `create` | 创建空白笔记（仅 `title?`），返回 `note_id`、`title`、`starred`、`create_time`、`link_url` |
| `update_note_info` | `update-info` | 修改笔记 `title` 或 `starred` 状态 |
| `edit_block` | `edit` | 单操作编辑：`replace` / `insert` / `delete` / `update_attrs` / `move` |
| `batch_edit` | `batch-edit` | 原子批量编辑，执行顺序固定：`delete → replace → update_attrs → move → insert` |
| `insert_image` | `insert-image` | 插入图片，`src`（公开 URL 或 ≤ 2 MiB data URI）与 `attachment_id` 二选一；CLI 可用 `--file` |
| `generate_image` | `gen-image` | AI 同步文生图，返回 `{ image_url, task_id }`（需配合 `insert_image` 插入） |
| `import_web_page` | `import-web` | 从白名单域名（公众号、知乎、豆瓣等）导入网页创建新笔记，返回 `{ note_id, title, link_url, message }` |

### 3. 标签管理（8 个）

| MCP 工具 | CLI 短命令 | Scope | 用途 |
|---|---|---|---|
| `list_tags` | `tags` | `read` | 分页获取全量标签（返回 `tags`、`next_token`、`has_more`） |
| `find_tags` | `find-tags` | `read` | 搜索标签（`keywords` / `mode` / `keyword`），不传关键词返回全部（超过 1000 时 `truncated=true`） |
| `get_notes_by_tag` | `get-notes-by-tag` | `read` | 按 `tag_id`（优先 ID 或完整 `path`）列出标签下的笔记 |
| `manage_note_tags` | `manage-tags` | `write` | 单篇（`note_id` + `add`/`remove`）或批量（`operations`，最多 100 项）管理笔记标签 |
| `add_note_tags` | `add-note-tags` | `write` | 向笔记追加标签（`tag_names[]`），不存在自动创建 |
| `remove_note_tags` | `remove-note-tags` | `write` | 按 `tag_ids[]` 从笔记移除标签 |
| `rename_tag` | `rename-tag` | `write` | 重命名标签末级名称（`tag_id`、`new_name`） |
| `delete_tag` | `delete-tag` | `destructive` | 永久删除标签及其子标签（高危，须先确认） |

### 4. 回收站（4 个）

| MCP 工具 | CLI 短命令 | Scope | 用途 |
|---|---|---|---|
| `list_trash` | `trash-list` | `read` | 列出回收站笔记（`order_by`/`order_direction`/`keyword`/`limit` 1–50/`cursor`） |
| `trash_note` | `trash` | `destructive` | 将笔记移入回收站（可恢复） |
| `restore_note` | `restore` | `write` | 从回收站恢复笔记及其标签 |
| `permanently_delete_note` | `purge` | `destructive` | 永久删除回收站中的笔记（不可恢复，须先确认；笔记必须已在回收站中） |

## 核心工作流与文档规模策略

### 文档规模读取策略

先调 `get_note_outline({ note_id, include_preview: false })` 查看 `word_count`、`block_count` 与 `size_category`：

| `size_category` | 字数范围 | 策略 |
|---|---|---|
| `small` | < 5K 字 | 直接 `read_note` 读取全文 |
| `medium` | 5K–20K 字 | `get_note_outline` → `read_section` 按章节读取 |
| `large` / `very_large` | > 20K 字 | `search_note_content` 精确定位 → `read_blocks` 读上下文 → `edit_block` 编辑 |

### 常用编排模式

**1. 创建并填充新笔记：**
```
create_note({ title: "Q1 总结" })                  → { note_id, link_url }
manage_note_tags({ note_id, add: ["工作/总结"] })  → 分配标签
get_note_outline({ note_id })                      → 取首个空 block_id
edit_block({ note_id, op: "replace", block_id, content: "<h1>Q1 总结</h1><p>第一段...</p>" })
```

**2. 连续追加长内容：**
- 优先在单次 `insert` 的 `content` 中拼接多个块级 XML（如 `"<h2>A</h2><p>...</p><h2>B</h2><p>...</p>"`），减少往返次数。
- 若必须分批追加，直接用上一次返回的 `last_block_id` 作为下一次 `insert` 的 `anchor_id`，无需反复调用 `get_note_outline`。

**3. 批量修改多个已知块：**
```
search_note_content({ note_id, keywords: ["关键词"] }) → results[].block_id
read_blocks({ note_id, block_ids: ["id1", "id2"] })    → 读完整 XML
batch_edit({ note_id, operations: [
  { op: "replace", block_id: "id1", content: "<p>...</p>" },
  { op: "replace", block_id: "id2", content: "<p>...</p>" }
]})
```

**4. 安全删除笔记：**
```
trash_note({ note_id })              → 移入回收站（可随时 restore_note 恢复）
# 仅在用户明确要求彻底清除时：
permanently_delete_note({ note_id }) → 永久删除（不可恢复）
```

## 常见注意点

- **全局搜索索引延迟**：`search_notes` 对刚写入或刚修改的正文有十几秒到约 1 分钟的索引延迟；按标题查找请用 `list_notes({ keyword })`，已知 `note_id` 查正文请用 `search_note_content`。
- **`edit_block` 后 ID 变化**：除 `insert` 可链式使用 `last_block_id`、`move` 不改变 `block_id` 外，其他修改后若继续编辑其他块，应重新调用 `get_note_outline` 刷新 ID。
- **复杂参数与大正文（CLI）**：使用 `wpsnote-cli` 时，数组、嵌套对象或长 XML 优先使用 `--args-file <path>` 传参，不熟悉的参数先用 `wpsnote-cli schema <tool>` 查看并在写操作前加 `--dry-run` 验证。

## 参考文档

- [API 参考](references/API_REFERENCE.md)——全部 31 个云端 MCP 工具的完整参数、Scope 与返回结构
- [CLI 参考](references/CLI_REFERENCE.md)——云端 `wpsnote-cli` 安装、OAuth/API Key 鉴权、短命令与 `--args-file`/`--file`/`--yes` 用法
- [错误码参考](references/ERROR_CODES.md)——云端 MCP 错误格式、业务错误码、CLI 错误与恢复模式
- [用例手册](references/USE_CASES.md)——覆盖读取、编辑、标签、回收站、图片/语音与 CLI 端到端用例
