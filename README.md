# WPS 笔记 Skills

[![WPS 笔记首页](https://img.shields.io/badge/WPS笔记-首页-blue?style=flat-square)](https://ainote.kdocs.cn/)
[![下载 WPS 笔记](https://img.shields.io/badge/WPS笔记-下载-green?style=flat-square)](https://ainote.kdocs.cn/wps-notes-hub/)
[![加入交流群](https://img.shields.io/badge/微信-加入交流群-07C160?style=flat-square&logo=wechat)](https://365.kdocs.cn/l/cau3Z9vsAUQt)

笔记，是思想落地的地方。

Claude Code、Cursor、OpenClaw，几乎所有主流 AI Agent，都可以通过本仓库的 Skill 直接驱动 WPS 笔记：往里写、从里读、让它有序、让它被找到。

笔记不再是你自己整理的地方，而是 Agent 替你打理的记忆层。

---

## 仓库定位

本仓库以 `wps-note` 为基础能力底座，上层按功能类型分组，每个目录是一类场景 Skill 的集合。

| 目录 | 定位 |
|------|------|
| `wps-note/` | 基础能力层，提供通用读写、搜索、管理能力，是所有场景 Skill 的依赖基础 |
| `note-tools/` | 笔记处理工具：美化排版、内容打磨、标签整理 |
| `content/` | 内容创作与发布：从写作到公众号排版的完整闭环 |
| `search/` | 搜索与阅读：新闻解读、智能深搜、文献阅读、论文全流程 |
| `capture/` | 信息捕获与记录：音频转写、文档导入、编码技术文档、日历联动 |
| `document-skills/` | 本地文档处理：PDF、Word、Excel、PowerPoint 读写与转换 |
| `insight-engine/` | 灵感引擎：记忆检索、想法连接、洞见生成 |
| `learning/` | 学习场景：课堂笔记、复习卡片、知识关联 |
| `novel-writer/` | AI 陪伴式长篇小说创作（MCP 版） |
| `novel-writer-cli/` | AI 陪伴式长篇小说创作（CLI 版） |
| `skill-creator/` | 工具：Skill 创建、迭代与评估 |

---

## 快速接入

WPS 笔记同时支持 **CLI** 和 **MCP Server** 两种接入方式，**推荐优先使用 CLI**。

### CLI（推荐）

适合 Claude Code / Cursor / OpenClaw 等终端型 Agent。

- **直接可调**：`wpsnote-cli <command>` 即可操作笔记，Agent 把它当普通 shell 命令调用
- **覆盖完整**：22 个命令覆盖读取、写入、搜索、图片、音频、标签、统计等全部能力

```bash
# 安装：在 WPS 笔记桌面端 MCP 设置页点击安装 CLI
# macOS / Linux 安装到 ~/.local/bin/wpsnote-cli

wpsnote-cli status          # 检查连接
wpsnote-cli list            # 列出笔记
wpsnote-cli read --help     # 查看某命令用法
```

详细命令参考：[CLI_REFERENCE.md](./wps-note/references/CLI_REFERENCE.md)

### MCP Server

适合 Cherry Studio 等图形化 Agent，或需要工具调用协议的场景。图形化配置，开箱即用，20+ 工具与 CLI 命令一一对应。

---

两种方式底层能力完全一致，Agent 是操作者，笔记是落点，你不需要做任何搬运。

---

## 目录结构

```text
wps-note/                        # 基础能力层：WPS 笔记通用读写、搜索、管理

note-tools/                      # 笔记处理工具
  wpsnote-beautifier/            # 智能美化，统一配色与排版
  note-copilot/                  # 笔记打磨，处理援助标记
  tag-organize/                  # 标签整理与分类优化（MCP 版）
  tag-organize-cli/              # 标签整理与分类优化（CLI 版）

content/                         # 内容创作与发布
  content-creator/               # 从 0 到 1 的内容创作工作流
  wechat-publisher/              # 公众号排版发布，导出微信公众号 HTML
  short-video-copywriter/        # 短视频文案创作
  xiaohongshu-note-creator/      # 笔记转小红书图文，含每页配图与话题标签
  image-gen/                     # AI 图像生成（文生图+图生图），内置加密 Key 管理

comm_script/                     # 公共脚本（跨 Skill 复用）
  image_gen.py                   # 统一图像生成脚本，支持 OpenRouter / 百炼 / 火山方舟 / Gemini，内置 AES Key 加密管理

search/                          # 搜索与阅读
  news-to-note/                  # 新闻智能解读与知识库关联
  wps-note-intelligent-search/   # 智能深度搜索，跨笔记关联挖掘
  literature-reader/             # 学术文献阅读与结构化概要生成
  paper-researcher/              # 论文全流程：搜索→下载→精读→存档

capture/                         # 信息捕获与记录
  live-transcript-summary/       # 实时音频转写监听与自动总结
  doc-importer/                  # 文档导入与格式转换
  web-importer/                  # 网页无损导入：公众号/通用网页 → WPS 笔记（含图片）
  coding-assistant/              # 编码助手，自动生成技术文档
  note-calendar/                 # WPS 笔记与系统日历双向联动

document-skills/                 # 本地文档处理
  pdf/                           # PDF 读取、文本提取、结构化分析
  docx/                          # Word 文档读写与内容提取
  xlsx/                          # Excel 表格读写与数据处理
  pptx/                          # PowerPoint 演示文稿读写

insight-engine/                  # 灵感引擎：记忆检索、想法连接、洞见生成
  ie-engine/                     # 统一入口，完整流水线
  ie-retrieve-memory/            # 记忆检索层
  ie-connect-dots/               # 想法连接层
  ie-generate-insight/           # 洞见生成层
  ie-recall-memory/              # 选择性召回

learning/                        # 学习场景 Skill 集合
  class-note-builder/            # 课堂笔记整理与主笔记构建
  lecture-focus-extractor/       # 从长篇笔记/转写中提取复习重点
  misconception-finder/          # 检查学习笔记中的理解错误与概念混淆
  notes-to-flashcards/           # 将笔记转为可主动回忆的复习卡片
  notes-to-lesson-plan/          # 将笔记整理为讲解结构/teach-back 提纲
  prerequisite-gap-finder/       # 找出学习卡点与前置知识缺口
  study-note-linker/             # 将新笔记与旧笔记关联，构建知识网络

novel-writer/                    # AI 陪伴式长篇小说创作（MCP 版）
novel-writer-cli/                # AI 陪伴式长篇小说创作（CLI 版）

skill-creator/                   # 工具：Skill 创建、迭代与评估
```

---

## 主要模块

### `wps-note` · 基础能力层

统一封装底层笔记操作，是本仓库所有场景 Skill 的依赖基础。通过 MCP 读取、编辑、搜索和管理 WPS 笔记，也通过 `wpsnote-cli` 提供命令行接入方式。

- [Skill 定义](./wps-note/SKILL.md) · [MCP API](./wps-note/references/API_REFERENCE.md) · [CLI 参考](./wps-note/references/CLI_REFERENCE.md) · [错误码](./wps-note/references/ERROR_CODES.md)

---

### `note-tools/` · 笔记处理工具

| Skill | 说明 |
|-------|------|
| `wpsnote-beautifier` | 智能美化笔记文档，优化标题层级、用高亮块强调结论、用分栏展示对比内容，全文统一一种配色 |
| `note-copilot` | 笔记协作打磨，识别并处理 `***` 和 `///` 援助标记，发现逻辑错误时以着色提醒 |
| `tag-organize` | 清理混乱标签、重构标签体系、优化分类结构（MCP 版） |
| `tag-organize-cli` | 与 `tag-organize` 功能相同，通过 `wpsnote-cli` 命令行驱动（CLI 版） |

---

### `content/` · 内容创作与发布

| Skill | 说明 |
|-------|------|
| `content-creator` | 完整创作工作流：风格画像→需求确认→大纲→深度研究→文章→定稿，与 `wechat-publisher` 形成闭环 |
| `wechat-publisher` | 将笔记内容一键排版导出为微信公众号 HTML，支持多种模板风格，是创作流程的最后一步 |
| `short-video-copywriter` | 短视频文案创作，适配抖音、视频号等平台风格 |
| `xiaohongshu-note-creator` | 将 WPS 笔记转化为完整小红书图文方案，含每页文案、AI 配图和话题标签 |
| `image-gen` | AI 图像生成升级方案，支持文生图 + 图生图，对接 OpenRouter / 百炼 / 火山方舟 / Gemini，内置 RSA 加密 Key 管理 |

### `comm_script/` · 公共脚本

跨 Skill 复用的底层脚本，不独立触发，由各 Skill 调用。

| 脚本 | 说明 |
|------|------|
| `image_gen.py` | 统一图像生成脚本，支持文生图 + 图生图，支持 4 个服务商，内置 AES Key 加密管理（`encrypt-key` 子命令） |

---

### `search/` · 搜索与阅读

| Skill | 说明 |
|-------|------|
| `news-to-note` | 新闻智能解读，搜索笔记库找关联内容，产出个性化 insight 分析，也支持批量写入简报 |
| `wps-note-intelligent-search` | 深度搜索，跨笔记关联挖掘与知识图谱构建，不同于简单关键词搜索 |
| `literature-reader` | 学术文献阅读与结构化概要生成，支持 PDF 论文元信息提取、方法论梳理、多篇横向对比 |
| `paper-researcher` | 论文全流程助手：搜索（arXiv/OpenAlex）→下载 PDF→转 Markdown→精读分析→存入 WPS 笔记 |

---

### `capture/` · 信息捕获与记录

| Skill | 说明 |
|-------|------|
| `live-transcript-summary` | 实时音频转写监听与自动总结，每 60 秒循环一次，适用于会议、听课、播客、采访 |
| `doc-importer` | 文档导入与格式转换，将外部文档结构化写入 WPS 笔记 |
| `web-importer` | 网页无损导入，将微信公众号文章或任意网页抓取为结构化笔记，图片按原文位置插入 |
| `coding-assistant` | 多平台编码助手，自动将核心技术梳理为技术文档，含架构概览、核心代码、调用链等标准模块 |
| `note-calendar` | WPS 笔记与 macOS 系统日历双向联动，日程写入笔记或从笔记提取事项落入日历 |

---

### `document-skills/` · 本地文档处理

处理本地文件，不依赖 WPS 笔记，可独立使用：

| Skill | 说明 |
|-------|------|
| `pdf` | PDF 文本提取、结构化内容分析 |
| `docx` | Word 文档读写与内容提取 |
| `xlsx` | Excel 表格读写与数据处理 |
| `pptx` | PowerPoint 演示文稿读写 |

---

### `insight-engine/` · 灵感引擎

串联记忆检索、想法连接和洞见生成的完整流水线，按层拆分、可独立调用也可组合：

| 子 Skill | 职责 |
|----------|------|
| `ie-engine` | 统一入口，运行完整流水线 |
| `ie-retrieve-memory` | 从历史笔记中检索相关知识 |
| `ie-connect-dots` | 发现笔记之间的隐含关联与主题模式 |
| `ie-generate-insight` | 将分析结果转化为可阅读的启发性内容 |
| `ie-recall-memory` | 选择性召回：当前最该想起哪些旧笔记 |

- [灵感引擎入口](./insight-engine/ie-engine/SKILL.md)

---

### `learning/` · 学习场景

由 Loki Mao（赛博小熊猫）贡献，覆盖从课堂记录到复习巩固的完整学习工作流：

| Skill | 适用场景 |
|-------|----------|
| `class-note-builder` | 把课堂逐字稿、OCR 笔记、零散材料整理成结构化主笔记 |
| `lecture-focus-extractor` | 从长篇笔记或转写中提取最值得复习的重点 |
| `misconception-finder` | 检查笔记里是否存在理解错误、概念混淆或逻辑跳步 |
| `notes-to-flashcards` | 将笔记转为可主动回忆的复习卡片 |
| `notes-to-lesson-plan` | 将笔记整理为可讲给别人听的 teach-back 提纲 |
| `prerequisite-gap-finder` | 找出学习卡点与缺失的前置知识 |
| `study-note-linker` | 将新笔记与旧笔记关联，构建个人知识网络 |

---

### `novel-writer/` · 长篇小说创作（MCP 版）

AI 陪伴式长篇小说创作，有记忆、懂上下文、不穿帮的持续创作。冷启动建档（世界观+人物设定+AI生图）、按章写作、全程归档 WPS 笔记，通过 MCP 服务操作笔记。

### `novel-writer-cli/` · 长篇小说创作（CLI 版）

与 `novel-writer` 功能相同，通过 `wpsnote-cli` 命令行操作笔记，适合 Claude Code 等终端型 Agent。

---

### `skill-creator/` · 创作工具

Skill 创建与迭代参考，指导如何组织目录、编写 `SKILL.md`、拆分 `references/`、补充评估与测试。新增任何 Skill 前建议优先阅读。

- [Skill Creator](./skill-creator/SKILL.md)

---

## 命令速查

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
| 写入 | `wpsnote-cli edit` | `edit_block` | 单个编辑操作（replace / insert / delete / update_attrs） |
| 写入 | `wpsnote-cli batch-edit` | `batch_edit` | 多个操作原子事务 |
| 写入 | `wpsnote-cli insert-image` | `insert_image` | 插入图片（不可用 XML 代替） |
| 写入 | `wpsnote-cli gen-image` | `generate_image` | AI 文生图，返回图片 URL |
| 管理 | `wpsnote-cli find` | `search_notes` | 搜索笔记，获取 note_id |
| 管理 | `wpsnote-cli list` | `list_notes` | 列出笔记 |
| 管理 | `wpsnote-cli create` | `create_note` | 创建空白笔记 |
| 管理 | `wpsnote-cli info` | `get_note_info` | 获取笔记元数据（含标签） |
| 管理 | `wpsnote-cli current` | `get_current_note` | 获取当前编辑中的笔记 |
| 管理 | `wpsnote-cli tags` | `find_tags` | 列出或搜索标签 |
| 管理 | `wpsnote-cli stats` | `get_note_stats` | 获取笔记和标签统计 |
| 管理 | `wpsnote-cli sync` | `sync_note` | 触发云端同步 |
| 管理 | `wpsnote-cli delete` | `delete_note` | 永久删除（不可恢复，须确认） |
| 调试 | `wpsnote-cli logs` | `get_mcp_logs` | 查看最近工具调用日志 |

---

## 新增 Skill 建议

1. 涉及通用的 WPS 笔记读写、搜索、管理能力时，优先复用 `wps-note`
2. 新建 Skill 时，判断它属于哪个功能分组（`note-tools/`、`content/`、`search/`、`capture/`、`learning/`），在对应目录下新建子文件夹
3. 找不到合适分组时，可以先开 Issue 讨论，或者在根目录临时放置，等积累同类 Skill 后再归组
4. 创建新的 Skill 结构、触发描述或评估流程时，优先参考 `skill-creator/`

---

## 加入 AI Skill 共创社区

写了一段绝佳的 AI Skill，只留给自己用岂不是太可惜了。

WPS 笔记的庞大用户基数，就是你 AI 创意的最佳放大器。加入 AI Skill 共创社区，让你的本地 Skill 直接跃入无数人的业务工作流。

**你的 Skill 能带来真实改变：**

- **海量的真实调用**：一段精妙的 Prompt 或触发逻辑，能迅速成为无数人每天高频唤醒的效率利器
- **定义官方规范**：优秀的底层能力和防冲突设计，将沉淀为官方仓库的底层标准，指引后来的伙伴
- **永久的极客署名**：成功合并进主分支的优质 Skill，每一次 Commit 都会保留你的 ID，永久刻在核心贡献者名单里

### 第一步：用 `skill-creator` 创作

不要从空白文档开始写。先打开 Cursor 或 Claude Code，告诉 Agent 你想创建一个什么 Skill，它会调用 `skill-creator` 帮你走完完整的流程——从 SKILL.md 结构，到 description 的精准措辞，到 evals 验证效果。

参考：[skill-creator/SKILL.md](./skill-creator/SKILL.md)

### 第二步：在 Description 中注明作者

在你的 `SKILL.md` 的 YAML 元数据中，加入 `author` 字段：

```yaml
---
name: your-skill-name
description: 一句话描述这个 Skill 做什么，以及何时触发它
author: 你的名字 <your-github-username>
version: 1.0.0
---
```

`description` 是 Agent 判断"什么时候用这个 Skill"的唯一依据，请务必写清楚触发时机，要有**明确的边界**——什么场景用，什么场景不用。可以参考仓库里已有的 Skill 写法。

### 第三步：检查是否与已有 Skill 冲突

提交前，请逐一对照仓库中现有的 Skill，确认：

- **触发描述不重叠**：你的 `description` 不应该在相同场景下与其他 Skill 产生歧义，避免 Agent 在同一场景下同时触发两个 Skill
- **能力不重复**：如果已有 Skill 能覆盖你的需求，优先考虑扩展已有 Skill，而不是新建一个
- **底层能力复用**：涉及 WPS 笔记读写时，应复用 `wps-note` 提供的能力，不要重新实现底层操作

### 第四步：带上代码或脑洞，认领你的阵地

**方式一：带着代码来（Pull Request）**
- Fork 本仓库，判断你的 Skill 属于哪个功能分组（`note-tools/`、`content/`、`search/`、`capture/`、`learning/`），在对应目录下新建子文件夹
- 确保包含完整的 `SKILL.md`，以及必要的 `references/`、`scripts/` 等
- 在 PR 描述里写清楚：这个 Skill 解决什么问题、放在哪个分组下、触发条件是什么、与哪些已有 Skill 做过冲突排查

**方式二：带着脑洞来（Issue）**
- 想到一个高价值的空白场景？直接开一个 Issue 抛出你的想法
- 社区里永远有手痒的小伙伴，会接力把你的好点子变成现实

你的每一个灵感，都可能成为 WPS 笔记未来的原生 AI 能力。扫码加入群聊，一起来：

[![加入 AI Skill 共创社区](https://img.shields.io/badge/WPS笔记-加入共创社区-FF6B35?style=flat-square)](https://365.kdocs.cn/l/cau3Z9vsAUQt)

## 贡献者

每一个 Skill，都是有人把自己摸索出来的工作方式，提炼成了别人也能用的技巧。

感谢你们愿意把私藏的经验，变成公共的财富。

<!-- 如果你贡献了 Skill，欢迎通过 PR 把自己加到这里 -->

<a href="https://github.com/gaotianxiang" title="gaotianxiang"><img src="https://github.com/gaotianxiang.png?size=64" width="48" height="48" hspace="4" alt="@gaotianxiang"/></a><a href="https://github.com/itshen" title="itshen"><img src="https://github.com/itshen.png?size=64" width="48" height="48" hspace="4" alt="@itshen"/></a><a href="https://github.com/loki2046-mao" title="loki2046-mao"><img src="https://github.com/loki2046-mao.png?size=64" width="48" height="48" hspace="4" alt="@loki2046-mao"/></a><a href="https://github.com/KevinYoung-Kw" title="KevinYoung-Kw"><img src="https://github.com/KevinYoung-Kw.png?size=64" width="48" height="48" hspace="4" alt="@KevinYoung-Kw"/></a><a href="https://github.com/liminwanqing" title="liminwanqing"><img src="https://github.com/liminwanqing.png?size=64" width="48" height="48" hspace="4" alt="@liminwanqing"/></a><a href="https://github.com/songjialiang" title="songjialiang"><img src="https://github.com/songjialiang.png?size=64" width="48" height="48" hspace="4" alt="@songjialiang"/></a><a href="https://github.com/dengchunlan" title="dengchunlan"><img src="https://github.com/dengchunlan.png?size=64" width="48" height="48" hspace="4" alt="@dengchunlan"/></a><a href="https://github.com/chadyi" title="chadyi"><img src="https://github.com/chadyi.png?size=64" width="48" height="48" hspace="4" alt="@chadyi"/></a><a href="https://github.com/oaeen" title="oaeen"><img src="https://github.com/oaeen.png?size=64" width="48" height="48" hspace="4" alt="@oaeen"/></a><a href="https://github.com/Naruto-mitsubishi" title="Naruto-mitsubishi"><img src="https://github.com/Naruto-mitsubishi.png?size=64" width="48" height="48" hspace="4" alt="@Naruto-mitsubishi"/></a><a href="https://github.com/wps-x" title="wps-x"><img src="https://github.com/wps-x.png?size=64" width="48" height="48" hspace="4" alt="@wps-x"/></a>

---

> 所有内容，都值得等到被用到的那天。
