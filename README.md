# WPS笔记 Skills

本仓库提供了 WPS笔记 Skill，让 Agent 可以通过自然语言指令直接操作 WPS 笔记。按“基础能力层”和“上层场景层”组织。仓库以 `wps-note` 为底座，提供 WPS 笔记的 MCP 能力与 `wpsnote-cli` 参考；其他 Skill 在此基础上封装具体业务场景。

## 仓库定位

本仓库包含三类内容：

- 基础能力：`wps-note` 提供 WPS 笔记的通用读写、搜索、管理能力，以及 CLI 参考文档。
- 场景 Skill：如新闻写入、图片转笔记等，上层场景复用 `wps-note` 的基础能力，不重复定义底层操作。
- 创建参考：`skill-creator` 提供创建、修改和迭代 Skill 的方法说明，适合作为新增 Skill 的起点。

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

## 主要模块

### `wps-note`

WPS 笔记基础能力层，负责统一封装底层笔记操作能力，包括：

- 通过 MCP 读取、编辑、搜索和管理 WPS 笔记
- 通过 `wpsnote-cli` 提供命令行调用方式
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

基于 `wps-note` 的图片识别场景 Skill，用于读取笔记中的图片，并生成结构化文字内容回写到笔记。

- [Skill 定义](./note-from-image/SKILL.md)

### `skill-creator`

Skill 创建与迭代参考，用于指导如何组织目录、编写 `SKILL.md`、拆分 `references/`、补充评估与测试。

新增 Skill 时，建议优先阅读：

- [Skill Creator](./skill-creator/SKILL.md)

## 设计分层

### 基础能力层

`wps-note` 负责提供可复用的通用笔记能力，是本仓库其他场景 Skill 的依赖基础。

### 上层场景层

`news-to-note`、`note-from-image` 等目录聚焦具体任务流程，复用 `wps-note` 的 MCP 或 CLI 能力完成业务目标。

这种分层的目的，是将“通用能力”与“业务场景”分离，降低重复实现和维护成本。

## 新增 Skill 建议

如果要在本仓库中新增 Skill，建议遵循以下原则：

1. 涉及通用的 WPS 笔记读写、搜索、管理能力时，优先复用 `wps-note`。
2. 面向特定任务流时，在仓库根目录下新建独立场景 Skill，而不是把场景逻辑直接写入 `wps-note`。
3. 创建新的 Skill 结构、触发描述或评估流程时，优先参考 `skill-creator`。

## 适用方式

- 维护底层笔记能力时，主要修改 `wps-note/`
- 扩展具体场景时，新增或调整独立场景 Skill
- 设计新 Skill 时，先参考 `skill-creator/` 的组织方式与编写方法
