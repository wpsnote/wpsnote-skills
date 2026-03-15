---
name: web-importer
description: >
  将网页内容高质量导入到 WPS 笔记，保留原文颜色、粗体、标题格式，图片按原文位置插入。
  支持微信公众号文章、X/Twitter 推文/Thread 和任意通用网页，统一入口自动识别，加 --wps 参数直接写入 WPS 笔记。
  当用户说「把这个网页存到笔记」「导入这篇文章」「抓取这个页面到笔记」
  「把公众号文章存到 WPS 笔记」「把这条推文存到笔记」「收藏这个链接」「网页转笔记」时触发。
  不适用于：新闻智能解读（用 news-to-note）、本地文档批量导入（用 doc-importer）。
author: 洛小山 <itshen>
version: 1.3.0
metadata:
  mcp-server: user-wpsnote
  category: capture
  tags: [web, scraping, wechat, twitter, x, import, note, html, rich-text]
---

# Web Importer — 网页高质量导入 WPS 笔记

将网页或微信公众号文章直接导入 WPS 笔记，**保留原文的颜色、粗体、标题推断、blockquote 高亮块**，图片按位置插入。
**现已支持 X/Twitter 推文和 Thread**：使用 Playwright 渲染动态页面，自动展开整个 Thread，图片原样下载入笔记。

---

## 核心原则

**不要走 Markdown 中转**。历史上的做法是"HTML → markdownify → Markdown → WPS XML"，这条链路会把所有内联样式（`color:rgb(...)`、`font-weight:700`、大字体标题）全部丢掉。

正确路径：
```
网页 URL
  ↓
爬取原始 HTML，下载图片到本地
  ↓
html_to_segments（BeautifulSoup 直接解析内联样式）
  ↓
write_content_with_placeholders（正文 + 图片占位符写入 WPS）
  ↓
find_and_insert_images（翻页找占位符，逐张插图）
```

---

## 快速使用

```bash
# 统一入口，加 --wps 即高质量模式
python3.11 scripts/web_import.py "https://mp.weixin.qq.com/s/xxxxx" --wps
python3.11 scripts/web_import.py "https://example.com/article" --wps

# X/Twitter 推文 / Thread（自动识别，使用 Playwright 渲染）
python3.11 scripts/web_import.py "https://x.com/user/status/xxx" --wps
python3.11 scripts/web_import.py "https://twitter.com/user/status/xxx" --wps

# 也可直接调用 Twitter 专用模块
python3.11 scripts/twitter_import.py "https://x.com/user/status/xxx" --wps

# 不加 --wps → 仅保存本地 Markdown 文件（旧行为，不导入 WPS）
python3.11 scripts/web_import.py "URL"

# 通用网页指定过滤级别（0=最小 1=中等 2=激进，默认2）
python3.11 scripts/web_import.py "URL" --wps -f 1

# 单独调用微信模块（--wps 同样适用）
python3.11 scripts/download_articles.py "https://mp.weixin.qq.com/s/xxxxx" --wps
python3.11 scripts/download_articles.py --latest --wps
```

---

## 两种模式对比

| | 默认模式（无 `--wps`） | 高质量模式（`--wps`） |
|---|---|---|
| 输出 | `content.md` + `images/` | 直接写入 WPS 笔记 |
| 颜色保留 | ❌ 丢失 | ✅ 映射到 WPS 预设色 |
| 粗体保留 | 部分（`**bold**`） | ✅ `font-weight:700` 识别 |
| 标题推断 | ❌ 只识别原生 h 标签 | ✅ 18px 以上大字体也识别 |
| blockquote | `> 引用文本` | ✅ 转 WPS 蓝色 highlightBlock |
| 图片 | 本地文件 | ✅ 按位置插入 WPS |
| 需要 wpsnote-cli | ❌ | ✅ |

---

## X/Twitter 支持说明

X 的内容由 JavaScript 动态渲染，普通 `requests` 无法获取推文正文。本模块使用 **Playwright** 模拟浏览器完整渲染。

### 安装额外依赖

```bash
pip3.11 install playwright
python3.11 -m playwright install chromium
```

### 工作流程

```
X 推文 URL
  ↓
Playwright 渲染页面（无头 Chromium）
  ↓
自动向下滚动 × 5，展开完整 Thread
  ↓
解析 article[data-testid="tweet"]，提取正文 + 图片
  ↓
只保留主作者推文（过滤他人回复）
  ↓
下载图片到本地（pbs.twimg.com/media/ → 最大尺寸）
  ↓
写入 WPS 笔记（--wps 模式）
```

### 注意事项

| 场景 | 说明 |
|------|------|
| 已登录推文 | 无需登录即可查看大多数公开推文 |
| 需要登录的推文 | Playwright 无法绕过，会提示无内容 |
| 长 Thread | 自动展开，最多爬取 50 条推文 |
| 视频 | 仅保存封面图，视频本体不下载 |
| 转推 / 引用推文 | 只保留主作者内容，转推内容过滤 |

---

## html_to_segments 解析逻辑

核心函数位于 `doc-importer/scripts/import_to_wps.py`，web-importer 动态加载复用。

### 内联样式 → WPS XML 映射

| HTML/CSS | WPS XML |
|---|---|
| `font-weight: 700/bold` | `<strong>` |
| `font-style: italic` | `<em>` |
| `color: rgb(194,28,19)` | `<span fontColor="#C21C13">` |
| `font-size >= 18px` 且文字 < 60 字 | `<h2>` |
| `<blockquote>` | `<highlightBlock emoji="📌" ...>` 蓝色高亮块 |
| `<ul>/<ol>/<li>` | `<p listType="bullet/ordered" listLevel="0">` |
| `<a href>` | `<a href="...">` |

### 颜色映射精度

颜色从 CSS `rgb(R,G,B)` 映射到 WPS 12 种预设色，使用欧氏距离最近邻。包含微信专属颜色的精确条目：

| 微信常用颜色 | 映射到 |
|---|---|
| `rgb(255,41,65)` 微信红 | `#C21C13` |
| `rgb(25,156,255)` 章节蓝 | `#116AF0` |
| `rgb(255,104,39)` 橙色 | `#DB7800` |
| `rgb(100,106,115)` 正文灰 | **跳过**（正文默认色，无需标注） |
| 色差 < 20 的中性灰 | **跳过** |

### section 展平逻辑

微信 HTML 常见多层 `section > section > p` 嵌套，自动展平：
- 容器 section（无直接图片且直接子元素 > 3 个）→ 递归展平
- 叶子 section（含直接图片或子元素 ≤ 3）→ 按普通块处理

---

## WPS 写入稳定性规则

与 `doc-importer` 共用同一套稳定写入逻辑，关键参数：

```python
BATCH_SIZE   = 4    # 每次 batch_edit 最多 4 个块，不超过 8
INSERT_RETRIES = 4  # anchor 失效时最多重试 4 次
IMG_INTERVAL = 0.8  # 图片插入间隔（秒）
```

**anchor 失效重试**：每次失败后 `sleep 1.5s × 重试次数`，然后重新 `outline` 获取最新 `last_block_id` 再重试。

**outline 翻页**：`outline` 默认只返回前 100 个 block。文章 > 100 块时自动用 `read-blocks --after 100` 翻页续读，确保占位符全部找到。

**防重复插图**：插图前统计笔记中已有 `type==image` 的 block 数量，大于 0 则跳过（断点续跑保护）。

---

## 下载后的目录结构

无论是否加 `--wps`，本地都会保留原始文件备份：

```
<输出目录>/
  ├── 原文.html       ← 原始 HTML（微信）
  ├── original.html   ← 原始 HTML（通用网页）
  ├── meta.json       ← {title, author, publish_time, url, images_count}
  ├── 终稿.md         ← Markdown 备份（微信，不加 --wps 时主文件）
  ├── content.md      ← Markdown 备份（通用网页）
  └── 图片素材/       ← 下载的图片（image_001.jpg, image_002.png ...）
```

---

## 微信公众号标题提取优先级

`download_articles.py` 内置多重兜底，按顺序尝试：

1. `og:title` meta 标签（最稳定）
2. `class="js_title_inner"` span
3. `class="rich_media_title"` h1/h2
4. 正则提取 `var msg_title = "..."`
5. 以上均失败 → "未命名文章"

---

## 异常处理

| 场景 | 处理方式 |
|------|---------|
| `wpsnote-cli` 未连接 | 自动降级为保存本地 Markdown 文件 |
| `import_to_wps.py` 找不到 | 打印警告，降级为 Markdown |
| `html_to_segments` 返回空 | 打印警告，降级为 Markdown |
| 微信链接已过期 | 告知用户链接已失效，无法抓取 |
| 图片下载失败 | 跳过该图片，继续导入正文，汇报跳过数 |
| anchor 失效（Block not found） | 重新获取 last_block_id，最多重试 4 次 |
| 占位符未找到 | `read-blocks` 翻页继续找；仍未找到则跳过该图片 |
| 笔记超 100 个块 | 自动翻页（`--after 100`） |
| X/Twitter Playwright 未安装 | 打印安装指引，退出 |
| X/Twitter 推文不可见（需登录） | 提示用户推文无法公开访问 |
| X/Twitter 推文已删除 | 提示内容无法获取 |

---

## 依赖项

```bash
# 通用依赖
pip3.11 install requests beautifulsoup4 readability-lxml markdownify lxml

# X/Twitter 额外依赖（Playwright）
pip3.11 install playwright
python3.11 -m playwright install chromium
```

| 工具 | 用途 |
|------|------|
| `requests` | 网页请求 |
| `beautifulsoup4` | HTML 解析 |
| `readability-lxml` | 通用网页正文提取 |
| `markdownify` | Markdown 模式备用（默认模式） |
| `lxml` | HTML 解析加速 |
| `playwright` | X/Twitter 动态页面渲染（JS 渲染） |
| `wpsnote-cli` | WPS 笔记写入（`--wps` 模式必须） |
