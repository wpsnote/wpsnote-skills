# WPS 笔记 Skills

**WPS 笔记是 AI Agent 的记忆中枢。**

Claude Code、Cursor、OpenClaw，几乎所有主流 AI Agent，都可以通过本仓库的 Skill 直接驱动 WPS 笔记：往里写、从里读、让它有序、让它被找到。

笔记不再是你自己整理的地方，而是 Agent 替你打理的记忆层。

---

## 仓库定位

本仓库按"基础能力层 + 上层场景层"组织，以 `wps-note` 为底座，提供 WPS 笔记的完整 MCP 能力与 `wpsnote-cli` 参考；其他 Skill 在此基础上封装具体业务场景。

- **基础能力**：`wps-note` 提供 WPS 笔记的通用读写、搜索、管理能力，以及 CLI 参考文档
- **场景 Skill**：如新闻写入、图片转笔记等，复用 `wps-note` 的基础能力，不重复定义底层操作
- **创建参考**：`skill-creator` 提供创建、修改和迭代 Skill 的方法说明，适合作为新增 Skill 的起点

---

## 快速接入

WPS 笔记提供两种接入方式，覆盖从普通用户到开发者的完整场景：

**MCP Server**（适合 Cherry Studio 等图形化 Agent）

图形化配置，开箱即用。19+ 工具覆盖笔记完整生命周期——创建、编辑、搜索、归档、图片插入、音频卡片、标签管理、跨笔记本检索、分段内容返回。

**CLI**（适合 OpenClaw / Claude Code / Cursor）

零配置成本，无缝集成进任何 Agent 工作流。不需要单独跑 MCP Server，写代码的同时笔记同步更新。

两种方式覆盖的是同一件事：Agent 是操作者，笔记是落点，你不需要做任何搬运。

---

## 目录结构

```text
wps-note/
  SKILL.md
  references/
    API_REFERENCE.md
    CLI_REFERENCE.md
    ERROR_CODES.md
    USE_CASES.md

news-to-note/
  SKILL.md

note-from-image/
  SKILL.md

skill-creator/
  SKILL.md
```

---

## 主要模块

### `wps-note`

WPS 笔记基础能力层，统一封装底层笔记操作，是本仓库所有场景 Skill 的依赖基础：

- 通过 MCP 读取、编辑、搜索和管理 WPS 笔记
- 通过 `wpsnote-cli` 提供命令行调用方式（CLI 参考中区分 help/schema 可见的 canonical 命令与 fallback alias）
- 为上层场景 Skill 提供稳定的能力入口和参考资料

相关文档：

- [Skill 定义](./wps-note/SKILL.md)
- [MCP API 参考](./wps-note/references/API_REFERENCE.md)
- [CLI 参考](./wps-note/references/CLI_REFERENCE.md)
- [错误码参考](./wps-note/references/ERROR_CODES.md)
- [用例参考](./wps-note/references/USE_CASES.md)

### `news-to-note`

基于 `wps-note` 的新闻检索与写入场景 Skill，用于将结构化新闻内容保存到 WPS 笔记。

- [Skill 定义](./news-to-note/SKILL.md)

### `note-from-image`

基于 `wps-note` 的图片识别场景 Skill，读取笔记中的图片，生成结构化文字内容回写到笔记。

- [Skill 定义](./note-from-image/SKILL.md)

### `skill-creator`

Skill 创建与迭代参考，用于指导如何组织目录、编写 `SKILL.md`、拆分 `references/`、补充评估与测试。

新增 Skill 时，建议优先阅读：

- [Skill Creator](./skill-creator/SKILL.md)

---

## MCP 工具速查

| 分类 | 工具 | 用途 |
|------|------|------|
| 读取 | `get_note_outline` | 获取结构大纲，所有 block_id 的来源 |
| 读取 | `read_blocks` | 按 ID 批量读取 block 内容 |
| 读取 | `read_note` | 读取笔记全文 XML |
| 读取 | `search_note_content` | 笔记内搜索，编辑前精确定位 |
| 读取 | `read_section` | 按标题读取完整章节 |
| 读取 | `read_image` | 读取图片 block（base64） |
| 读取 | `get_audio_transcript` | 获取语音录音转写文本 |
| 写入 | `edit_block` | 单个编辑操作（replace / insert / delete / update_attrs） |
| 写入 | `batch_edit` | 多个操作原子事务 |
| 写入 | `insert_image` | 插入图片（必须用此工具，不可用 XML） |
| 管理 | `list_notes` / `search_notes` | 查找笔记，获取 note_id |
| 管理 | `create_note` | 创建空白笔记 |
| 管理 | `get_note_info` | 获取笔记元数据（含标签） |
| 管理 | `find_tags` | 列出或搜索标签 |
| 管理 | `get_current_note` | 获取当前打开的笔记 |
| 管理 | `sync_note` | 触发云端同步 |
| 管理 | `delete_note` | 永久删除（不可恢复，须确认） |

**核心操作模式**：先定位（`outline` / `search`）→ 再读取（`read`）→ 最后编辑（`write`）

所有内容以语义 XML 格式交换，所有定位基于 block_id（10 位字母数字）。

---

## 设计分层

### 基础能力层

`wps-note` 负责提供可复用的通用笔记能力，是本仓库其他场景 Skill 的依赖基础。

### 上层场景层

`news-to-note`、`note-from-image` 等目录聚焦具体任务流程，复用 `wps-note` 的 MCP 或 CLI 能力完成业务目标。

这种分层的目的，是将"通用能力"与"业务场景"分离，降低重复实现和维护成本。

---

## 新增 Skill 建议

1. 涉及通用的 WPS 笔记读写、搜索、管理能力时，优先复用 `wps-note`
2. 面向特定任务流时，在仓库根目录下新建独立场景 Skill，而不是把场景逻辑直接写入 `wps-note`
3. 创建新的 Skill 结构、触发描述或评估流程时，优先参考 `skill-creator`

---

## 适用方式

- 维护底层笔记能力时，主要修改 `wps-note/`
- 扩展具体场景时，新增或调整独立场景 Skill
- 设计新 Skill 时，先参考 `skill-creator/` 的组织方式与编写方法

---

> 所有内容，都值得等到被用到的那天。
