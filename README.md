# WPS笔记 Skills

通过 MCP（Model Context Protocol）和 CLI 实现对 WPS 笔记的读取、编辑与管理。

## 概述

本仓库提供了 WPS笔记 Skill，让 Agent 可以通过自然语言指令直接操作 WPS 笔记。

### 核心能力

- **笔记读取** — 大纲浏览、分段读取、全文搜索、图片识别、语音转写
- **内容编辑** — 段落替换、内容插入、批量删除、属性更新、图片插入
- **批量操作** — 原子事务支持，多个编辑操作一次提交，全部成功或全部回滚
- **笔记管理** — 创建、删除、同步、标签管理、使用统计
- **CLI 工具** — `wpsnote-cli` 命令行工具，将 MCP 工具封装为 shell 命令，支持脚本自动化

## 项目结构

```
wps-note/
  SKILL.md                       # 技能定义（触发条件、工作流、工具速查）
  references/
    API_REFERENCE.md             # 全部 MCP 工具的完整 inputSchema
    CLI_REFERENCE.md             # wpsnote-cli 命令行工具参考
    ERROR_CODES.md               # 错误码详情、hints 系统与恢复策略
    USE_CASES.md                 # 按复杂度递进的用例集与 Prompt 模板
```

## 安装

将本仓库克隆到 支持 Skills 的应用目录中：


## 使用示例

安装后，直接用自然语言与 Agent 交互即可：

```
"帮我搜索包含'季度总结'的笔记"
"读取当前笔记的大纲"
"把第二章的摘要替换成新版本"
"创建一篇会议记录，标题为 2025-03-11 周会"
```
