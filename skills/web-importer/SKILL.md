---
name: web-importer
description: >
  将网页内容高质量导入到 WPS 笔记，保留原文颜色、粗体、标题格式，图片按原文位置插入。
  支持微信公众号文章、X/Twitter 推文/Thread 和任意通用网页，统一入口自动识别，使用 web_fetch、web_search、batch_web_search、create_note、batch_edit、insert_image、sync_note 直接写入 WPS 笔记。
  当用户说「把这个网页存到笔记」「导入这篇文章」「抓取这个页面到笔记」
  「把公众号文章存到 WPS 笔记」「把这条推文存到笔记」「收藏这个链接」「网页转笔记」时触发。
  不适用于：新闻智能解读（用 news-to-note）、本地文档批量导入（用 doc-importer）。
author: 洛小山 <itshen>
version: 1.3.0
metadata:
  category: capture
  tags: [web, scraping, wechat, twitter, x, import, note, html, rich-text]
---

# Web Importer — 网页高质量导入 WPS 笔记

将网页或微信公众号文章直接导入 WPS 笔记，**保留原文的颜色、粗体、标题推断、blockquote 高亮块**，图片按位置插入。
**现已支持 X/Twitter 推文和 Thread**：统一通过 `web_fetch` 获取当前可见内容，抓到图片链接时按原文位置插入笔记。

---

## 核心原则

**不要把抓取回来的 Markdown 原样写进 WPS 笔记**。当前入口是 `web_fetch` / `web_search`，抓回来的主内容需要先整理为 WPS XML，再写入笔记；图片仍然单独插入。

正确路径：
```
网页 URL
  ↓
web_fetch / web_search / batch_web_search
  ↓
网页正文 + 图片链接
  ↓
整理成 WPS XML
  ↓
create_note + batch_edit（正文 + 图片占位符写入 WPS）
  ↓
get_note_outline / read_blocks（找占位符）
  ↓
insert_image（逐张插图）
```

---

## 快速使用

```text
# 用户直接给 URL
web_fetch "https://mp.weixin.qq.com/s/xxxxx"
create_note
batch_edit
insert_image
sync_note

# 用户只给标题或模糊描述
web_search "文章标题或关键词"
ask_user（候选链接不唯一时）
web_fetch "确认后的 URL"
create_note
batch_edit
insert_image
sync_note
```

---

## 两种模式对比

| | 直接抓取模式 | 搜索定位模式 |
|---|---|---|
| 入口 | 用户直接给 URL | 用户只给标题 / 关键词 |
| 获取正文 | `web_fetch` | `web_search` / `batch_web_search` + `web_fetch` |
| 输出 | 直接写入 WPS 笔记 | 直接写入 WPS 笔记 |
| 候选确认 | 一般不需要 | 多个候选时用 `ask_user` |
| 图片 | `insert_image` 按位置插入 | `insert_image` 按位置插入 |
| 回读验收 | `read_note` / `read_section` / `read_blocks` | `read_note` / `read_section` / `read_blocks` |

---

## X/Twitter 支持说明

X 的内容仍然可能受到动态渲染、登录态和线程展开限制影响。当前 Skill 统一依赖 `web_fetch` 返回的可见正文和图片链接，不额外假设浏览器渲染能力。

### 工作流程

```
X 推文 URL
  ↓
web_fetch 获取当前可见正文
  ↓
提取正文 + 图片链接
  ↓
整理成 WPS XML
  ↓
写入 WPS 笔记
```

### 注意事项

| 场景 | 说明 |
|------|------|
| 公开推文 | 优先导入当前可见正文 |
| 需要登录的推文 | 可能拿不到正文，需明确告诉用户 |
| 长 Thread | 只导入当前工具能稳定抓到的内容 |
| 视频 | 仅保留可见文字与可插入图片，不承诺视频本体 |
| 转推 / 引用推文 | 以当前抓到的主内容为准 |

---

## html_to_segments 解析逻辑

当前不再依赖 `html_to_segments` 本地脚本，但处理目标不变：把网页结构整理为 WPS XML，并尽量保留原文层级和重点样式。

### 网页内容 → WPS XML 映射

| 网页结构 / Markdown | WPS XML |
|---|---|
| `**加粗**` / 粗体语义 | `<strong>` |
| `*斜体*` / 斜体语义 | `<em>` |
| 一级到三级标题 | `<h1>` / `<h2>` / `<h3>` |
| 引用块 | `<blockquote>` |
| 无序 / 有序列表 | `<ul>` / `<li>` |
| 表格 | `<table>` |
| 链接 | 在段落中保留文本和 URL |

### 颜色映射精度

如果抓取结果能明确保留颜色语义，可在 WPS XML 中映射到可用样式；如果抓取结果已丢失颜色信息，就不要伪造颜色。

### section 展平逻辑

网页存在多层嵌套时，按最终阅读顺序展平为标题、正文、引用、列表、表格和图片占位符，再写入 WPS。

---

## WPS 写入稳定性规则

与现有笔记编辑工具的稳定写入规则保持一致，关键约束如下：

```text
正文优先用 batch_edit
少量修补可用 edit_block
图片只能用 insert_image
编辑前必须先拿到 block_id
```

**anchor 失效重试**：图片插入或补写前，如果 block_id 已变化，先重新 `get_note_outline`，必要时再 `read_blocks` 精确定位。

**outline 翻页**：长文导入后如果需要回找图片占位符或补写位置，先重新获取最新 outline，再按需要分段读取。

**防重复插图**：重试时先回读当前笔记，确认图片是否已经插入，避免重复写入。

---

## 下载后的目录结构

当前 Skill 的最终产物是 WPS 笔记，不要求保留本地下载目录。导入完成后，笔记中至少应有：

```text
笔记标题
来源信息（原网页链接）
正文结构（标题 / 段落 / 引用 / 列表 / 表格）
按位置插入的图片
```

---

## 微信公众号标题提取优先级

按顺序尝试：

1. `web_fetch` 返回的页面标题
2. `web_search` 命中的候选标题
3. 用户在请求里明确给出的文章标题
4. 以上均失败 → 用链接或“未命名文章”作为兜底

---

## 异常处理

| 场景 | 处理方式 |
|------|---------|
| `web_fetch` 无法抓到正文 | 告知用户当前链接无法导入，不创建空笔记 |
| 正文不完整 | 允许降级导入已抓到的部分，并明确说明缺失内容 |
| 图片下载 / 插入失败 | 跳过该图片，继续导入正文，汇报跳过数 |
| block_id 失效 | 重新获取 outline 和目标 block 后再继续 |
| 占位符未找到 | 回读正文重新定位；仍未找到则跳过该图片并说明 |
| X/Twitter 内容不可见 | 提示用户当前内容无法公开获取或线程未完整展开 |
| 搜索结果不唯一 | 使用 `ask_user` 让用户确认链接 |

---

## 依赖项

| 工具 | 用途 |
|------|------|
| `web_fetch` | 抓取网页正文 |
| `web_search` / `batch_web_search` | 在缺少精确链接时定位网页 |
| `create_note` | 创建导入目标笔记 |
| `get_note_outline` | 获取 block_id 和最新结构 |
| `batch_edit` / `edit_block` | 写入正文和少量修补 |
| `insert_image` | 按位置插入图片 |
| `read_note` / `read_section` / `read_blocks` | 回读验收 |
| `sync_note` | 导入后同步 |
| `ask_user` | 链接不明确时确认候选 |
