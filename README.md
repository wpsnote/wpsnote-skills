# WPS 笔记 Skills

[![WPS 笔记首页](https://img.shields.io/badge/WPS笔记-首页-blue?style=flat-square)](https://ainote.kdocs.cn/)
[![下载 WPS 笔记](https://img.shields.io/badge/WPS笔记-下载-green?style=flat-square)](https://ainote.kdocs.cn/wps-notes-hub/)
[![加入交流群](https://img.shields.io/badge/微信-加入交流群-07C160?style=flat-square&logo=wechat)](https://365.kdocs.cn/l/cau3Z9vsAUQt)

笔记，是思想落地的地方。

本仓库以 `wps-note` 为基础能力底座，让 Claude Code、Cursor、OpenClaw 等主流 AI Agent 直接驱动 WPS 笔记——往里写、从里读、让它有序、让它被找到。

笔记不再是你自己整理的地方，而是 Agent 替你打理的记忆层。

# 关于本仓库

本仓库包含 WPS 笔记场景下的完整 Skill 生态，覆盖笔记处理、内容创作、搜索阅读、信息捕获、灵感引擎、学习、长篇创作等场景。每个 Skill 独立在自己的文件夹中，包含一个 `SKILL.md` 定义文件。浏览这些 Skill 可以获取灵感，或了解不同的设计模式与实现方法。

# Skill 分类

- [./skills](./skills): 全部 Skill，按功能分组如下
- [./comm_script](./comm_script): 公共脚本（跨 Skill 复用）

### 核心能力

| Skill | 说明 |
|-------|------|
| [wps-note](./skills/wps-note) | 基础能力层，通过 MCP / CLI 读取、编辑、搜索和管理 WPS 笔记，是所有场景 Skill 的依赖基础 |
| [wpsnote-beautifier](./skills/wpsnote-beautifier) | 智能美化笔记，优化标题层级、用高亮块强调结论、用分栏展示对比内容，全文统一一种配色 |
| [note-copilot](./skills/note-copilot) | 笔记协作打磨，识别并处理 `***` 和 `///` 援助标记，发现逻辑错误时以着色提醒 |
| [tag-organize](./skills/tag-organize) | 清理混乱标签、重构标签体系、优化分类结构（MCP 版） |
| [tag-organize-cli](./skills/tag-organize-cli) | 与 tag-organize 功能相同，通过 CLI 驱动 |
| [skill-creator](./skills/skill-creator) | Skill 创建、迭代与评估工具 |

### 内容创作

| Skill | 说明 |
|-------|------|
| [content-creator](./skills/content-creator) | 完整创作工作流：风格画像 → 需求确认 → 大纲 → 深度研究 → 文章 → 定稿 |
| [wechat-publisher](./skills/wechat-publisher) | 将笔记排版导出为微信公众号 HTML，支持多种模板风格 |
| [short-video-copywriter](./skills/short-video-copywriter) | 将原稿改写为短视频口播文案，支持分镜脚本与 AI 配图 |
| [xiaohongshu-note-creator](./skills/xiaohongshu-note-creator) | 将笔记 / 文章转化为小红书图文方案，含每页文案、AI 配图和话题标签 |
| [image-gen](./skills/image-gen) | AI 图像生成（文生图 + 图生图），对接 OpenRouter / 百炼 / 火山方舟 / Gemini |

### 搜索与阅读

| Skill | 说明 |
|-------|------|
| [content-digest](./skills/content-digest) | 万能内容提炼：URL / 图片 / PDF / 粘贴文本 → 结构化知识笔记，支持多篇合并与图片视觉解读 |
| [news-to-note](./skills/news-to-note) | 新闻智能解读，搜索笔记库找关联内容，产出个性化 insight，也支持批量新闻简报 |
| [wps-note-intelligent-search](./skills/wps-note-intelligent-search) | 深度搜索，跨笔记关联挖掘与知识图谱构建 |
| [literature-reader](./skills/literature-reader) | 学术文献阅读与结构化概要，支持元信息提取、方法论梳理、多篇横向对比 |
| [paper-researcher](./skills/paper-researcher) | 论文全流程：搜索（arXiv / OpenAlex）→ 下载 PDF → 精读分析 → 存入笔记 |

### 信息捕获

| Skill | 说明 |
|-------|------|
| [live-transcript-summary](./skills/live-transcript-summary) | 实时音频转写监听与自动总结，适用于会议、听课、播客、采访 |
| [doc-importer](./skills/doc-importer) | 批量导入本地文档（Obsidian / 思源 / PDF / Word 等）到 WPS 笔记 |
| [web-importer](./skills/web-importer) | 网页无损导入：公众号 / 推文 / 通用网页 → WPS 笔记，保留格式与图片 |
| [coding-assistant](./skills/coding-assistant) | 多平台编码助手，自动将核心技术梳理为标准化技术文档 |
| [note-calendar](./skills/note-calendar) | WPS 笔记与 macOS 系统日历双向联动 |

### 灵感引擎

串联记忆检索、想法连接和洞见生成的完整流水线，按层拆分、可独立调用也可组合。

| Skill | 说明 |
|-------|------|
| [ie-engine](./skills/ie-engine) | 统一入口，运行完整灵感生成流水线 |
| [ie-retrieve-memory](./skills/ie-retrieve-memory) | 记忆层：从历史笔记中检索相关知识 |
| [ie-connect-dots](./skills/ie-connect-dots) | 推理层：语义聚类、发现隐含关联与主题模式 |
| [ie-generate-insight](./skills/ie-generate-insight) | 洞见层：将分析结果转化为可阅读的启发性内容 |
| [ie-recall-memory](./skills/ie-recall-memory) | 选择性召回：当前最该想起哪些旧笔记 |

### 学习场景

覆盖从课堂记录到复习巩固的完整学习工作流。

| Skill | 说明 |
|-------|------|
| [class-note-builder](./skills/class-note-builder) | 把课堂逐字稿、OCR 笔记、零散材料整理成结构化主笔记 |
| [lecture-focus-extractor](./skills/lecture-focus-extractor) | 从长篇笔记 / 转写中提取最值得复习的重点 |
| [misconception-finder](./skills/misconception-finder) | 检查笔记中的理解错误、概念混淆或逻辑跳步 |
| [notes-to-flashcards](./skills/notes-to-flashcards) | 将笔记转为可主动回忆的复习卡片 |
| [notes-to-lesson-plan](./skills/notes-to-lesson-plan) | 将笔记整理为可讲给别人听的 teach-back 提纲 |
| [prerequisite-gap-finder](./skills/prerequisite-gap-finder) | 找出学习卡点与缺失的前置知识 |
| [study-note-linker](./skills/study-note-linker) | 将新笔记与旧笔记关联，构建知识网络 |

### 长篇创作

| Skill | 说明 |
|-------|------|
| [novel-writer](./skills/novel-writer) | AI 陪伴式长篇小说创作，有记忆、懂上下文、不穿帮（MCP 版） |
| [novel-writer-cli](./skills/novel-writer-cli) | 与 novel-writer 功能相同，通过 CLI 驱动 |

# 在 Claude Code、Cursor 和 MCP 中使用

## Claude Code

在 Claude Code 中注册本仓库为插件市场：

```
/plugin marketplace add wpsnote/wpsnote-skills
```

然后安装需要的 Skill 组：

1. 选择 `Browse and install plugins`
2. 选择 `wpsnote-skills`
3. 选择 `core-skills`、`content-skills`、`capture-skills`、`creative-skills` 或 `learning-skills`
4. 点击 `Install now`

或直接安装：

```
/plugin install core-skills@wpsnote-skills
/plugin install content-skills@wpsnote-skills
/plugin install capture-skills@wpsnote-skills
/plugin install creative-skills@wpsnote-skills
/plugin install learning-skills@wpsnote-skills
```

## CLI（推荐）

适合 Claude Code / Cursor / OpenClaw 等终端型 Agent。`wpsnote-cli <command>` 即可操作笔记，20+ 命令覆盖全部能力。

```bash
# 安装：在 WPS 笔记桌面端 MCP 设置页点击安装 CLI
wpsnote-cli status          # 检查连接
wpsnote-cli list            # 列出笔记
wpsnote-cli read --help     # 查看某命令用法
```

详细命令参考：[CLI_REFERENCE.md](./skills/wps-note/references/CLI_REFERENCE.md)

## MCP Server

适合 Cherry Studio 等图形化 Agent，或需要工具调用协议的场景。图形化配置，开箱即用，20+ 工具与 CLI 命令一一对应。

---

两种方式底层能力完全一致，Agent 是操作者，笔记是落点。

# 创建 Skill

使用 下面的的模板快速开始：

```markdown
---
name: my-skill-name
description: 一句话描述这个 Skill 做什么，以及何时触发它
---

# Skill 名称

[在此编写 Agent 执行时遵循的指令]

## 示例
- 使用场景 1
- 使用场景 2

## 规则
- 规则 1
- 规则 2
```

frontmatter 必需字段：

- `name` — Skill 唯一标识（小写，用连字符分隔）
- `description` — 完整描述 Skill 功能与触发时机（这是 Agent 判断何时使用的**唯一依据**，务必写清触发边界）

创建新 Skill 的完整指南，请参考 [skill-creator](./skills/skill-creator/SKILL.md) 与 [claude-skills-complete-guide.md](./claude-skills-complete-guide.md)。

# 命令速查

**核心操作模式**：先定位（`outline` / `search`）→ 再读取（`read`）→ 最后编辑（`edit`）

所有内容以语义 XML 格式交换，所有定位基于 block_id（10 位字母数字）。

| 分类 | CLI 命令 | MCP 工具 | 说明 |
|------|----------|----------|------|
| 读取 | `wpsnote-cli outline` | `get_note_outline` | 获取结构大纲与 block_id，超大文档自动分页 |
| 读取 | `wpsnote-cli read` | `read_note` | 读取笔记全文 XML |
| 读取 | `wpsnote-cli section` | `read_section` | 按标题读取章节，支持 `block_offset` 续读 |
| 读取 | `wpsnote-cli read-blocks` | `read_blocks` | 按 ID 批量读取 block |
| 读取 | `wpsnote-cli search` | `search_note_content` | 笔记内搜索，编辑前精确定位 |
| 读取 | `wpsnote-cli read-image` | `read_image` | 读取图片 block |
| 读取 | `wpsnote-cli audio` | `get_audio_transcript` | 获取语音录音转写文本 |
| 读取 | `wpsnote-cli xml-ref` | `get_xml_reference` | 获取 XML 标签与写入示例 |
| 写入 | `wpsnote-cli edit` | `edit_block` | 单个编辑操作 |
| 写入 | `wpsnote-cli batch-edit` | `batch_edit` | 多个操作原子事务 |
| 写入 | `wpsnote-cli insert-image` | `insert_image` | 插入图片 |
| 写入 | `wpsnote-cli gen-image` | `generate_image` | AI 文生图 |
| 管理 | `wpsnote-cli find` | `search_notes` | 搜索笔记 |
| 管理 | `wpsnote-cli list` | `list_notes` | 列出笔记 |
| 管理 | `wpsnote-cli create` | `create_note` | 创建空白笔记 |
| 管理 | `wpsnote-cli info` | `get_note_info` | 获取笔记元数据 |
| 管理 | `wpsnote-cli current` | `get_current_note` | 获取当前编辑中的笔记 |
| 管理 | `wpsnote-cli tags` | `find_tags` | 列出或搜索标签 |
| 管理 | `wpsnote-cli stats` | `get_note_stats` | 获取统计 |
| 管理 | `wpsnote-cli sync` | `sync_note` | 触发云端同步 |
| 管理 | `wpsnote-cli delete` | `delete_note` | 永久删除 |
| 调试 | `wpsnote-cli logs` | `get_mcp_logs` | 查看工具调用日志 |

# 社区与贡献

写了一段绝佳的 Skill，只留给自己用岂不是太可惜了。加入 WPS笔记 AI Skill 共创社区，让你的本地 Skill 直接跃入无数人的业务工作流。

### 贡献步骤

1. **用 `skill-creator` 创作**：告诉 Agent 你想创建什么 Skill，它会调用 [skill-creator](./skills/skill-creator/SKILL.md) 帮你走完完整流程
2. **在 SKILL.md 中注明作者**：
   ```yaml
   ---
   name: your-skill-name
   description: 一句话描述这个 Skill 做什么，以及何时触发它
   author: 你的名字 <your-github-username>
   version: 1.0.0
   ---
   ```
3. **检查冲突**：确认触发描述不与已有 Skill 重叠，底层能力复用 `wps-note`
4. **提交 PR**：在 `skills/` 目录下新建子文件夹，确保包含完整的 `SKILL.md`

**方式二**：有想法但没时间写代码？直接开一个 [Issue](https://github.com) 抛出你的脑洞。

[![加入 AI Skill 共创社区](https://img.shields.io/badge/WPS笔记-加入共创社区-FF6B35?style=flat-square)](https://365.kdocs.cn/l/cau3Z9vsAUQt)

<p align="center">
  <img src="./assets/wechat-group-qr.png" alt="微信交流群二维码" width="300" />
  <br/>
  <sub>微信扫码加入交流群</sub>
</p>

## 贡献者

每一个 Skill，都是有人把自己摸索出来的工作方式，提炼成了别人也能用的技巧。

<!-- 如果你贡献了 Skill，欢迎通过 PR 把自己加到这里 -->

<a href="https://github.com/itshen" title="itshen"><img src="https://github.com/itshen.png?size=64" width="48" height="48" hspace="4" alt="@itshen"/></a><a href="https://github.com/wps-x" title="wps-x"><img src="https://github.com/wps-x.png?size=64" width="48" height="48" hspace="4" alt="@wps-x"/></a><a href="https://github.com/loki2046-mao" title="loki2046-mao"><img src="https://github.com/loki2046-mao.png?size=64" width="48" height="48" hspace="4" alt="@loki2046-mao"/></a><a href="https://github.com/KevinYoung-Kw" title="KevinYoung-Kw"><img src="https://github.com/KevinYoung-Kw.png?size=64" width="48" height="48" hspace="4" alt="@KevinYoung-Kw"/></a><a href="https://github.com/chadyi" title="chadyi"><img src="https://github.com/chadyi.png?size=64" width="48" height="48" hspace="4" alt="@chadyi"/></a><a href="https://github.com/dengchunlan" title="dengchunlan"><img src="https://github.com/dengchunlan.png?size=64" width="48" height="48" hspace="4" alt="@dengchunlan"/></a><a href="https://github.com/liminwanqing" title="liminwanqing"><img src="https://github.com/liminwanqing.png?size=64" width="48" height="48" hspace="4" alt="@liminwanqing"/></a><a href="https://github.com/oaeen" title="oaeen"><img src="https://github.com/oaeen.png?size=64" width="48" height="48" hspace="4" alt="@oaeen"/></a><a href="https://github.com/Naruto-mitsubishi" title="Naruto-mitsubishi"><img src="https://github.com/Naruto-mitsubishi.png?size=64" width="48" height="48" hspace="4" alt="@Naruto-mitsubishi"/></a>

---

> 所有内容，都值得等到被用到的那天。
