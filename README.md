# WPS 笔记 Skills

[![WPS 笔记首页](https://img.shields.io/badge/WPS笔记-首页-blue?style=flat-square)](https://ainote.kdocs.cn/)
[![下载 WPS 笔记](https://img.shields.io/badge/WPS笔记-下载-green?style=flat-square)](https://ainote.kdocs.cn/wps-notes-hub/)
[![WPS 社区](https://img.shields.io/badge/WPS社区-交流反馈-FF6B35?style=flat-square)](https://bbs.wps.cn/topics/node/28)

笔记，是思想落地的地方。

本仓库以 `wpsnote` 为基础能力，让灵犀、WorkBuddy、豆包办公、千问办公、Grok Bot 等主流 AI Agent 通过**云端 MCP** 或**云端 CLI** 直接读写、搜索、整理和管理 WPS 笔记——不依赖桌面端运行。

---

## 快速接入：云端 MCP 与云端 CLI

云端 MCP 与云端 CLI 对接同一个云端服务端，工具能力完全一致，按客户端形态任选其一即可：

### 方式一：配置云端 MCP（推荐用于办公 AI / 桌面 Agent）

适用于灵犀、WorkBuddy、豆包办公、千问办公、Grok Bot、Cherry Studio 等支持 Streamable HTTP MCP 的客户端：

1. 前往 [https://ainote.kdocs.cn/mcp-svc/keys/page](https://ainote.kdocs.cn/mcp-svc/keys/page) 登录 WPS 账号并生成 API Key（按需勾选 `read` / `write` / `destructive` 权限）。
2. 在客户端 MCP 配置文件中加入 `wpsnote`：

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

### 方式二：安装云端 CLI（推荐用于终端型 Agent / 脚本自动化）

适用于终端型 Agent、自动化 Bot 及批量导入导出脚本（需 Node.js ≥ 20.12）：

```bash
# 1. 全局安装云端 CLI
npm install -g wpsnote-cli

# 2. 登录授权（浏览器 OAuth，无浏览器环境可加 --no-browser）
wpsnote-cli auth login

# 或直接从 MCP JSON 导入 / 通过环境变量鉴权
wpsnote-cli auth import <mcp.json>
# export WPS_NOTE_API_KEY="<your-api-key>"

# 3. 验证连接、权限与到期时间
wpsnote-cli auth status --json

# 4. 常用命令测试
wpsnote-cli list --limit 10
wpsnote-cli read --help
```

> 若此前安装过旧桌面端附带的 `~/.wpsnote-cli`，按安装提示在桌面端「AI 实验室 → 命令行工具 → 卸载」清理后再使用云端 `wpsnote-cli`。  
> 在脚本或管道中解析 `--json` 输出时，建议固定追加 `--no-update-notice` 参数避免升级提示混入标准输出。详细文档见 [CLI_REFERENCE.md](./skills/wpsnote/references/CLI_REFERENCE.md) 与 [API_REFERENCE.md](./skills/wpsnote/references/API_REFERENCE.md)。

### 方式三：安装 Skills 插件（支持插件市场的客户端）

在支持插件市场的 AI 客户端中注册本仓库并按需安装 Skill 组：

```text
/plugin marketplace add wpsnote/wpsnote-skills
```

建议优先安装 `core-skills`（包含基础 skill `wpsnote`），再按需安装各场景组：

```text
/plugin install core-skills@wpsnote-skills
/plugin install note-ops-skills@wpsnote-skills
/plugin install content-skills@wpsnote-skills
/plugin install capture-skills@wpsnote-skills
/plugin install learning-skills@wpsnote-skills
```

---

## Skill 分类（共 13 个）

- [./skills](./skills)：全部 Skill（每个文件夹内含独立 `SKILL.md`）
- [./comm_script](./comm_script)：跨 Skill 复用的公共脚本（[wps_cli.py](./comm_script/wps_cli.py)、[image_gen.py](./comm_script/image_gen.py)）

### 核心能力（`core-skills`）

| Skill | 说明 |
|-------|------|
| [wpsnote](./skills/wpsnote) | 通过云端 MCP（`wpsnote`）和云端 CLI（`wpsnote-cli`）读取、编辑、搜索和管理 WPS 笔记 |

### 笔记整理与辅助（`note-ops-skills`）

| Skill | 说明 |
|-------|------|
| [wpsnote-beautifier](./skills/wpsnote-beautifier) | 智能美化笔记，优化标题层级、高亮块与分栏排版，严格使用 WPS 预设色板 |
| [tag-organize](./skills/tag-organize) | 清理混乱标签、重构多级标签体系、优化分类结构 |

### 内容创作（`content-skills`）

| Skill | 说明 |
|-------|------|
| [content-creator](./skills/content-creator) | 完整创作工作流：风格画像 → 需求确认 → 大纲 → 深度研究 → 文章 → 定稿 |
| [wechat-publisher](./skills/wechat-publisher) | 将 WPS 笔记排版导出为微信公众号 HTML，支持多种模板风格 |
| [xiaohongshu-note-creator](./skills/xiaohongshu-note-creator) | 将笔记 / 文章转化为小红书图文方案，含每页文案、配图和话题标签 |

### 搜索与阅读（`content-skills`）

| Skill | 说明 |
|-------|------|
| [content-digest](./skills/content-digest) | 万能内容提炼：URL / 图片 / PDF / 粘贴文本 → 结构化知识笔记，支持图片视觉解读 |
| [news-to-note](./skills/news-to-note) | 新闻智能解读，结合已有笔记库输出个性化 insight，支持新闻简报 |
| [paper-researcher](./skills/paper-researcher) | 学术论文全流程：arXiv / OpenAlex 搜索 → 下载 PDF → 精读分析 → 存入笔记 |

### 信息捕获（`capture-skills`）

| Skill | 说明 |
|-------|------|
| [doc-importer](./skills/doc-importer) | 批量导入本地文档（Obsidian / 思源 / PDF / Word / HTML 等）到 WPS 笔记 |
| [web-importer](./skills/web-importer) | 网页无损导入：公众号 / X(Twitter) / 通用网页 → WPS 笔记，保留样式与按位插图 |

### 学习场景（`learning-skills`）

| Skill | 说明 |
|-------|------|
| [study-assistant](./skills/study-assistant) | 课堂逐字稿整理为主笔记、重点提炼与闪卡、误区与前置补缺、费曼提纲及旧知关联 |
| [note-review-coach](./skills/note-review-coach) | 基于已有笔记生成不提前泄题的自测题，作答后按原文证据批改并输出复习建议 |

---

## 命令速查

**核心操作模式**：先定位（`outline` / `find` / `search`）→ 再读取（`read` / `section` / `read-blocks`）→ 最后编辑（`edit` / `batch-edit`）

正文以语义 XML 格式交换，块定位基于顶层 `block_id`（10 位字母数字）；文件级标签与回收站使用专用命令/工具管理。

| 分类 | CLI 命令 | MCP 工具 | 说明 |
|------|----------|----------|------|
| 读取 | `wpsnote-cli outline` | `get_note_outline` | 获取结构大纲与 `block_id`，支持分页 |
| 读取 | `wpsnote-cli read` | `read_note` | 读取笔记全文 XML |
| 读取 | `wpsnote-cli section` | `read_section` | 按标题读取章节，支持 `block_offset` 续读 |
| 读取 | `wpsnote-cli read-blocks` | `read_blocks` | 按 ID 批量读取 block |
| 读取 | `wpsnote-cli search` | `search_note_content` | 笔记内搜索，编辑前精确定位 |
| 读取 | `wpsnote-cli read-image` | `read_image` | 读取已持久化图片内容（base64） |
| 读取 | `wpsnote-cli audio` | `get_audio_transcript` | 获取语音录音转写内容 |
| 读取 | `wpsnote-cli xml-ref` | `get_xml_reference` | 获取 XML 标签、预设色板与写入示例 |
| 写入 | `wpsnote-cli edit` | `edit_block` | 单个编辑操作 |
| 写入 | `wpsnote-cli batch-edit` | `batch_edit` | 多个操作原子事务（`delete → replace → update_attrs → insert`） |
| 写入 | `wpsnote-cli insert-image` | `insert_image` | 插入图片（CLI 支持 `--file` 传本地图片） |
| 写入 | `wpsnote-cli gen-image` | `generate_image` | AI 文生图 |
| 管理 | `wpsnote-cli find` | `search_notes` | 全文搜索笔记 |
| 管理 | `wpsnote-cli list` | `list_notes` | 列出笔记（支持 `order_by`、`starred`、`has_todo`、`cursor`） |
| 管理 | `wpsnote-cli create` | `create_note` | 创建空白笔记（返回 `note_id`） |
| 管理 | `wpsnote-cli info` | `get_note_info` | 获取单篇笔记元数据与标签 |
| 管理 | `wpsnote-cli update-info` | `update_note_info` | 修改笔记标题或星标状态 |
| 标签 | `wpsnote-cli tags` | `list_tags` | 分页获取全部标签 |
| 标签 | `wpsnote-cli find-tags` | `find_tags` | 搜索或列出标签（含 `tag_id` 与 `path`） |
| 标签 | `wpsnote-cli get-notes-by-tag` | `get_notes_by_tag` | 查看某个标签下的笔记 |
| 标签 | `wpsnote-cli manage-tags` | `manage_note_tags` | 单篇或批量管理笔记文件级标签 |
| 标签 | `wpsnote-cli add-note-tags` / `remove-note-tags` | `add_note_tags` / `remove_note_tags` | 向笔记增量追加/移除标签 |
| 标签 | `wpsnote-cli rename-tag` / `delete-tag` | `rename_tag` / `delete_tag` | 全局重命名或删除标签（删除需 `--yes`） |
| 导入 | `wpsnote-cli import-web` | `import_web_page` | 导入支持域名的网页内容 |
| 回收站 | `wpsnote-cli trash-list` | `list_trash` | 查看回收站笔记 |
| 回收站 | `wpsnote-cli trash` / `restore` | `trash_note` / `restore_note` | 移入回收站（`--yes`）/ 从回收站恢复 |
| 回收站 | `wpsnote-cli purge` | `permanently_delete_note` | 永久删除回收站中的笔记（不可恢复，需 `--yes`） |

---

## 创建与贡献 Skill

在 `skills/<your-skill-name>/SKILL.md` 下新建文件，保持结构聚焦于具体业务场景：

```markdown
---
name: my-skill-name
description: 一句话说明 Skill 的能力范围与触发条件
---

# Skill 名称

> WPS 笔记接口、XML 与通用错误码规范见 [wpsnote](../wpsnote/SKILL.md)。

[在此编写业务场景的工作流、输入输出格式与质量要求]
```

编写规范详见 [claude-skills-complete-guide.md](./claude-skills-complete-guide.md)。

### 贡献步骤

1. **独立场景边界**：编写 `SKILL.md` 时明确 `name` 与带清晰触发边界的 `description`，避免与现有 Skill 重叠。
2. **复用基础能力**：笔记读写、标签管理、XML 格式与错误处理均直接引用 [wpsnote](./skills/wpsnote/SKILL.md)（Python 批量脚本统一复用 [comm_script/wps_cli.py](./comm_script/wps_cli.py)），不在场景 Skill 中重复抄写接口细节。
3. **更新索引并提交 PR**：同步更新 `.claude-plugin/marketplace.json` 与 `README.md` 中的 Skill 列表，或通过 [Issue](https://github.com/wpsnote/wpsnote-skills/issues) / [WPS 社区](https://bbs.wps.cn/topics/node/28) 交流反馈。

[![加入 WPS 社区](https://img.shields.io/badge/WPS笔记-加入WPS社区-FF6B35?style=flat-square)](https://bbs.wps.cn/topics/node/28)

## 贡献者

每一个 Skill，都是有人把自己摸索出来的工作方式，提炼成了别人也能用的技巧。

<!-- 如果你贡献了 Skill，欢迎通过 PR 把自己加到这里 -->

<a href="https://github.com/itshen" title="itshen"><img src="https://github.com/itshen.png?size=64" width="48" height="48" hspace="4" alt="@itshen"/></a><a href="https://github.com/wps-x" title="wps-x"><img src="https://github.com/wps-x.png?size=64" width="48" height="48" hspace="4" alt="@wps-x"/></a><a href="https://github.com/loki2046-mao" title="loki2046-mao"><img src="https://github.com/loki2046-mao.png?size=64" width="48" height="48" hspace="4" alt="@loki2046-mao"/></a><a href="https://github.com/KevinYoung-Kw" title="KevinYoung-Kw"><img src="https://github.com/KevinYoung-Kw.png?size=64" width="48" height="48" hspace="4" alt="@KevinYoung-Kw"/></a><a href="https://github.com/chadyi" title="chadyi"><img src="https://github.com/chadyi.png?size=64" width="48" height="48" hspace="4" alt="@chadyi"/></a><a href="https://github.com/dengchunlan" title="dengchunlan"><img src="https://github.com/dengchunlan.png?size=64" width="48" height="48" hspace="4" alt="@dengchunlan"/></a><a href="https://github.com/liminwanqing" title="liminwanqing"><img src="https://github.com/liminwanqing.png?size=64" width="48" height="48" hspace="4" alt="@liminwanqing"/></a><a href="https://github.com/oaeen" title="oaeen"><img src="https://github.com/oaeen.png?size=64" width="48" height="48" hspace="4" alt="@oaeen"/></a><a href="https://github.com/Naruto-mitsubishi" title="Naruto-mitsubishi"><img src="https://github.com/Naruto-mitsubishi.png?size=64" width="48" height="48" hspace="4" alt="@Naruto-mitsubishi"/></a>

---

> 所有内容，都值得等到被用到的那天。
