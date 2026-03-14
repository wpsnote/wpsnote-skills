---
name: web-importer
description: >
  将网页内容无损导入到 WPS 笔记，保留原文格式并按原文位置插入图片。
  支持微信公众号文章和任意通用网页两种来源，统一入口自动识别。
  当用户说「把这个网页存到笔记」「导入这篇文章」「抓取这个页面到笔记」
  「把公众号文章存到 WPS 笔记」「收藏这个链接」「网页转笔记」时触发。
  不适用于：新闻智能解读（用 news-to-note）、本地文档导入（用 doc-importer）。
author: 洛小山 <itshen>
version: 1.0.0
metadata:
  mcp-server: user-wpsnote
  category: capture
  tags: [web, scraping, wechat, import, note]
---

# Web Importer — 网页无损导入 WPS 笔记

将网页或微信公众号文章抓取为 Markdown，保留标题层级、加粗、列表、代码块等格式，图片按原文位置插入 WPS 笔记。

## 快速决策

```
收到 URL
  ↓
是 mp.weixin.qq.com？
  ├─ 是 → 用 download_articles.py（微信专用）
  └─ 否 → 用 web_to_md.py（通用网页）
  ↓
本地生成: content.md + images/
  ↓
创建 WPS 笔记 → 写入正文 → 逐张插入图片 → sync
```

---

## 完整工作流

### 第一步：运行爬取脚本

**脚本路径**：`capture/web-importer/scripts/`（两个脚本的原始版本在仓库根目录，统一入口为 `web_import.py`）

```bash
# 统一入口（自动识别 URL 类型）
python3.11 scripts/web_import.py "https://example.com/article"
python3.11 scripts/web_import.py "https://mp.weixin.qq.com/s/xxxxx"

# 指定输出目录
python3.11 scripts/web_import.py "URL" -o /tmp/my_article

# 通用网页指定过滤级别（0=最小 1=中等 2=激进，默认2）
python3.11 scripts/web_import.py "URL" -f 1
```

**脚本输出结构：**
```
<输出目录>/
  ├── content.md      ← 正文 Markdown（含来源、标题等元信息）
  ├── original.html   ← 原始 HTML 备份
  └── images/         ← 下载的图片（img_001.jpg, img_002.png ...）
```

脚本执行完毕后，**从 `content.md` 读取标题和正文，图片列表从 `images/` 目录获取**。

---

### 第二步：解析 Markdown → WPS XML

将 `content.md` 的内容按以下规则转换为 WPS XML：

| Markdown 元素 | WPS XML |
|------------|---------|
| `# 标题` | `<h1>标题</h1>` |
| `## 二级标题` | `<h2>标题</h2>` |
| 普通段落 | `<p>内容</p>` |
| `**粗体**` | `<p><strong>粗体</strong></p>` |
| `*斜体*` | `<p><em>斜体</em></p>` |
| `- 无序列表` | `<p listType="bullet" listLevel="0">内容</p>` |
| `1. 有序列表` | `<p listType="ordered" listLevel="0" listId="list1">内容</p>` |
| `` `code` `` 行内代码 | `<p><strong>code</strong></p>`（WPS 无行内代码，退化为加粗） |
| \`\`\`代码块\`\`\` | `<codeblock lang="python">代码内容</codeblock>` |
| `> 引用` | `<blockquote><p>引用内容</p></blockquote>` |
| `---` 分割线 | `<hr/>` |
| `[文本](url)` | `<p><a href="url">文本</a></p>` |
| `![alt](图片路径)` | 见"图片处理"章节 |

**来源 highlightBlock**：`content.md` 开头的元信息（来源 URL、作者、时间）写成 highlightBlock：

```xml
<highlightBlock emoji="🔗" highlightBlockBackgroundColor="#E6EEFA" highlightBlockBorderColor="#98C1FF">
  <p><strong>来源：</strong><a href="{原文URL}">{域名}</a></p>
  <p><strong>抓取时间：</strong>{YYYY-MM-DD HH:MM}</p>
</highlightBlock>
```

---

### 第三步：创建笔记并写入正文

**推荐使用 wpsnote-cli**（比 MCP 通信开销更小，批量写入更稳定）。

```bash
# 1. 检查连接
wpsnote-cli status

# 2. 创建笔记
NOTE_ID=$(wpsnote-cli create --title "文章标题" --json | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['fileId'])")

# 3. 等待初始化（新建后必须 sync + 等待）
wpsnote-cli sync --note_id "$NOTE_ID" --json && sleep 2

# 4. 获取初始 block_id
FIRST_ID=$(wpsnote-cli outline --note_id "$NOTE_ID" --json | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['blocks'][0]['id'])")
```

**关键稳定性规则：**

```
BATCH_SIZE = 4        # 每次 batch-edit 最多 4 个块，越小越稳定，不超过 8
INSERT_RETRIES = 4    # anchor 失效时最多重试 4 次
每次重试前：sleep 1.5s × 重试次数，然后重新获取 last block_id 作为新 anchor
```

**写入流程（图片先用占位符）：**

```
1. replace first_id → <h1>文章标题</h1>
2. insert after first_id → 来源 highlightBlock
3. 分批写入正文（每批 ≤ 4 个块）：
   - 纯文字块：直接 batch-edit insert
   - 图片位置：插入占位符 <p>[图片占位-001:img_001.jpg]</p>
4. 每次 insert 用上一次返回的 last_block_id 作为 anchor
   （anchor 失效时刷新 outline 获取最新 last block id）
```

**outline 只返回前 100 个 block**，文章超过 100 块时翻页读取：

```bash
# 获取第 100 块之后的内容
wpsnote-cli read-blocks --note_id "$NOTE_ID" \
  --block_id "$LAST_ID" --after 100 --include_anchor false --json
# 重复直到 blocks 为空
```

---

### 第四步：逐张插入图片

写完全部正文后，处理图片。图片**不能通过 XML 写入**，必须用 `insert-image`。

**定位占位符（翻页扫 blocks，不用 search_note_content）：**

```bash
# 翻页获取全部 blocks，在 preview 或 content 字段里匹配 [图片占位-NNN:...]
wpsnote-cli outline --note_id "$NOTE_ID" --json
# → 找到 {"id": "xxx", "preview": "[图片占位-001:img_001.jpg]"}
```

**插入图片（统一使用 --src_file，避免命令行长度限制）：**

```bash
# 将图片编码写入临时文件
EXT="jpg"
echo "data:image/jpeg;base64,$(base64 -i images/img_001.jpg)" > /tmp/wps_img.txt

# 插入到占位符后面
wpsnote-cli insert-image \
  --note_id "$NOTE_ID" \
  --anchor_id "$PLACEHOLDER_BLOCK_ID" \
  --position after \
  --src_file /tmp/wps_img.txt --json

# 删除占位符
wpsnote-cli batch-edit --note_id "$NOTE_ID" \
  --operations '[{"op":"delete","block_ids":["$PLACEHOLDER_BLOCK_ID"]}]' --json

# 清理
rm -f /tmp/wps_img.txt
```

**插图前检查防重复（断点续跑保护）：**

```
翻页扫 blocks，统计 type=="image" 的 block 数量
如果已有图片数 > 0 → 跳过插图步骤（说明之前已经插过了）
```

图片插入间隔：每张之间 sleep 0.8s，避免速率限制。

---

### 第五步：同步并汇报

```bash
wpsnote-cli sync --note_id "$NOTE_ID" --json
```

完成后向用户汇报：
```
✅ 导入完成！
  标题：{文章标题}
  来源：{域名}
  正文：约 {N} 个段落
  图片：{M} 张（成功 {X} 张，跳过 {Y} 张）
  WPS 笔记：{笔记标题}
```

---

## 异常处理

| 场景 | 处理方式 |
|------|---------|
| `wpsnote-cli` 未连接 | `wpsnote-cli status` 确认，失败则退回 MCP 方式 |
| 脚本依赖缺失 | `pip3.11 install requests beautifulsoup4 readability-lxml markdownify lxml` |
| 微信链接已过期 | 告知用户链接已失效，无法抓取 |
| 图片下载失败 | 跳过该图片，继续导入正文，汇报标注跳过数 |
| `EDITOR_NOT_READY` / `FRONTEND_TIMEOUT` | sleep 2s 后重试，最多 3 次 |
| anchor 失效（insert 返回 Block not found） | 重新获取 last block_id，最多重试 4 次 |
| 占位符未找到（outline 扫不到） | `read-blocks` 翻页继续找；仍未找到则跳过该图片 |
| 笔记超 100 个块 | 翻页获取 blocks（`--after 100` 参数） |

---

## 依赖项

| 工具 | 安装 |
|------|------|
| `requests` | `pip3.11 install requests` |
| `beautifulsoup4` | `pip3.11 install beautifulsoup4` |
| `readability-lxml` | `pip3.11 install readability-lxml` |
| `markdownify` | `pip3.11 install markdownify` |
| `lxml` | `pip3.11 install lxml` |

一键安装：
```bash
pip3.11 install requests beautifulsoup4 readability-lxml markdownify lxml
```
