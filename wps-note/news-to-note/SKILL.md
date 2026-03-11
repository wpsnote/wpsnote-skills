---
name: search-news-to-wps-note
description: 使用搜索工具在网上查找最新新闻，去重后通过 wpsnote-cli 保存为结构化的 WPS Note 新闻简报。适用于用户提出“找新闻”“热点汇总”“新闻简报”“把新闻保存到笔记”等需求。仅使用搜索流程，不使用 RSS 工作流或直连新闻 API 工作流。
---

# 搜索新闻并写入 WPS Note

## 概述

使用搜索工具收集新闻结果，完成去重与筛选后，追加写入 WPS Note。

固定执行顺序：
1. 搜索新闻结果。
2. 去重并筛选高价值条目。
3. 定位或创建目标简报笔记。
4. 以 XML 形式插入简报内容块。
5. 同步并输出结果摘要。

## 前置条件

- 确保可使用搜索工具。
- 确保可通过 MCP 或 `wpsnote-cli` 调用 WPS Note 写入能力。

如果 WPS Note 写入工具不可用，立即停止并明确提示缺失依赖。

## 工作流

### 1. 构造搜索词

- 至少包含一个主题词和一个时效词。
- 使用 `site:` 限定来源，提高结果质量。
- 查询组数量控制在 2-4 条，避免重复噪音。

示例：
- `AI 行业 新闻 过去24小时 site:36kr.com OR site:ifanr.com OR site:infoq.cn`
- `新能源 资讯 今日 site:caixin.com OR site:thepaper.cn`

更多模板见 [query-recipes.md](references/query-recipes.md)。

### 2. 规范化与去重

- 去重前先规范化 URL。
- 删除跟踪参数（`utm_*`、`fbclid`、`gclid`）。
- 以规范化 URL 作为去重键。
- 避免重复写入目标笔记中已存在的链接。

### 3. 定位目标笔记

- 优先使用日期标题：`新闻简报 YYYY-MM-DD`。
- 先按标题关键词搜索已有笔记。
- 仅在无匹配时创建新笔记。

### 4. 安全写入内容

- 插入前先刷新大纲并获取最新 `block_id`。
- 使用 `edit_block(op=insert)` 或 CLI `edit --op insert` 进行写入。
- XML 保持简单且合法：
  - `<h2>` 简报标题
  - `<p><a href="...">标题</a></p>`
  - `<p>摘要</p>`
- 对标题和摘要做 XML 转义。

### 5. 同步与校验

- 写入后执行同步。
- 回报插入条数并展示已写入链接。

## MCP 调用模式

推荐工具链：
1. 调用搜索工具获取新闻链接。
2. `search_notes` 或 `list_notes` 定位简报笔记。
3. 若不存在则调用 `create_note`。
4. 用 `get_note_outline` 获取最新锚点 `block_id`。
5. 使用 `edit_block(op="insert")` 追加简报 XML。
6. 调用 `sync_note`。

始终遵循：定位 -> 读取/刷新 -> 写入。

## CLI 兜底模式

通过 CLI 操作时使用以下命令：

```bash
wpsnote-cli find --keyword "新闻简报 2026-03-11" --json
wpsnote-cli create --title "新闻简报 2026-03-11" --json
wpsnote-cli outline --note_id <NOTE_ID> --json
wpsnote-cli edit --note_id <NOTE_ID> --op insert --anchor_id <BLOCK_ID> --position after --content "<h2>...</h2><p>...</p>" --json
wpsnote-cli sync --note_id <NOTE_ID> --json
```

## 异常处理

- `EDITOR_NOT_READY` / `FRONTEND_TIMEOUT`：短暂等待后重试。
- `BLOCK_NOT_FOUND`：刷新大纲，使用最新 block id 重试。
- `DOCUMENT_READ_ONLY`：停止写入并告知用户。
- 搜索结果为空：只回报“无新增”，不要写入空内容块。

## 资源

- [query-recipes.md](references/query-recipes.md)：高质量新闻检索的查询模板与来源过滤策略。
