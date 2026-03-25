---
name: content-digest
description: 将任意内容提炼为结构化知识笔记，自动保存到 WPS 笔记。只要用户给出任何内容（链接、图片、本地文件、粘贴文字）并有保存笔记的意图，就应使用此 skill。常见触发词：「总结」「提炼」「做笔记」「读书笔记」「学习笔记」「整理成笔记」「帮我看看」「帮我解读」「记一下」「存下来」「整理一下」「帮我归纳」。也适用于用户直接给出 URL、@图片、@文件但没有明确说「存笔记」的情况——只要内容值得保存，主动使用此 skill。支持网页、公众号、本地 PDF/Word/TXT/Markdown/图片/截图、粘贴文本；所有图片（本地截图、网络图片、PDF 图片页、笔记内图片）均可自动视觉解读；输出一句话概括、核心观点、金句摘录、我的思考；多篇合并为一篇笔记。不用于：代码重构、纯技术问答、文件编辑、仅讨论链接（无保存意图）、日常聊天。
allowed-tools: "Read WebFetch Bash(pip3:*) Bash(python3:*)"
compatibility: 需要 wps-note MCP 服务器已连接；需要 Python 3 环境（用于图片类 PDF 转换，首次运行会自动安装 pymupdf）；需要支持读取本地文件和图片、WebFetch 工具抓取网页内容。
metadata:
  author: zoez
  mcp-server: wps-note
  version: "3.7.1"
  category: productivity
  tags: [content-digest, summarization, knowledge-capture, image-analysis]
---

# Content Digest — 万能内容提炼

将任意来源的内容转化为结构化知识笔记，自动保存到 WPS 笔记。

## 工作流

### 第一步：识别输入类型并获取内容

| 输入类型 | 获取方式 | 图片解读路径 |
|---------|---------|------------|
| URL / 网页 / 公众号链接 | `WebFetch(url)` 提取正文；若被拦截 → 笔记写「访问受限，如需提炼请手动复制原文到 AI 工具处理」| 正文中如有图片 URL → 提取后走「网络图片」流程 |
| 本地文件（文本类 PDF/Word）| `Read(绝对路径)`；若提取文字 < 50 字 → 执行「图片类 PDF 转换流程」| 转 PNG 后逐页 `Read` 视觉解读 |
| 本地图片（jpg/png/gif/webp）| `Read(图片路径)` → AI 视觉分析（不尝试插入，MCP 不支持本地路径）| 直接 `Read` |
| 网络图片 URL | `insert_image(url)` 插入笔记 → `read_image(note_id, block_id)` 取 base64 → AI 视觉解读 | `read_image` ← **WPS 笔记原生识图能力** |
| 笔记内已有图片 | `get_note_outline` 定位 image block → `read_image(note_id, block_id)` 取 base64 → AI 视觉解读 | `read_image` ← **WPS 笔记原生识图能力** |
| 直接粘贴文本 / 邮件 | 无需获取，直接进入第二步；判断依据：消息中无 URL 也无文件路径 | — |
| 多篇内容 | 全部提炼后合并，标题用「内容提炼合集 · YYYY-MM-DD」| 每类图片按对应路径处理 |

> 支持的完整文件格式见 [references/supported-formats.md](references/supported-formats.md)
> 图片处理细节：本地图片 → `Read` 直接视觉分析；网络图片 → `insert_image` 插入笔记再 `read_image` 取 base64 解读；网页内嵌图片 → 从正文提取 URL 后走网络图片流程；笔记内已有图片 → `get_note_outline` 定位后 `read_image` 解读；PDF/PPT 图片页 → 见下方处理流程。

### 第二步：提炼内容

**文字类：**
- 一句话概括：不超过 50 字，动词开头，忠实原文
- 核心观点：用自己的语言转述，不直接复制原文句子
- 金句摘录：必须是原文原句，逐字引用，不改动
- 我的思考：用户未提供则留 `[待补充]`，**不编造**

**图片类（所有来源统一使用以下模块）：**
- 📌 一句话概括：图片的核心内容，10 字以内
- 🔍 内容解读：分点描述图片内容（文字/界面/人物/图表/图形设计等）；有文字则逐字提取；有数据则标明数值
- 💡 核心信息：图片传达的主要观点或信息
- 💬 我的思考：图片适用场景、设计亮点或可借鉴之处

> 图片解读不能跳过：笔记的核心价值是把「看过就忘」的图片变成可检索的文字。哪怕图片模糊或内容抽象，也必须描述所能观察到的一切——否则笔记等于空白。

**行动清单（可选模块）：**

行动清单只在内容包含明确可执行建议时生成，不是每篇都需要：
- ✅ 适合生成：教程/指南类（「三步完成 X」）、方法论文章（「你应该做 Y」）、含待办事项的邮件、任务型文档
- ❌ 不适合生成：纯观点/叙述类文章、数据分析报告、故事类内容、图片笔记

有疑问时默认不生成，比强行生成空洞的行动清单更好。

> 输出 XML 模板（含配色）见 [references/output-templates.md](references/output-templates.md)  
> 来源标识与原文附录规则见 [references/source-rules.md](references/source-rules.md)

### 排版规范（写入时强制执行）

| 区域 | 排版方式 | 颜色 |
|-----|---------|------|
| 来源元信息 | `<blockquote>` | 无 |
| 一句话概括 | `<h2>📌 一句话概括</h2>` + `<p>` | 无 |
| 核心观点 | `<h2>💡 核心观点</h2>` + `<columns><column columnBackgroundColor="#EBF2FF">` | 浅蓝（`highlightBlock` 颜色不生效，改用 columns） |
| 金句摘录 | `<h2>⭐ 金句摘录</h2>` + `<columns><column columnBackgroundColor="#FFF5EB">` | 浅橙（同上） |
| 我的思考 | `<h2>💬 我的思考</h2>` + `<p>` | 无 |
| 行动清单 | `<h2>✅ 行动清单</h2>` + `<p listType="todo" checked="0">` | 无 |

**强制规则（及原因）：**
- **笔记主标题（H1）不加 emoji**——WPS 笔记列表视图直接显示 H1 作为标题，emoji 前缀会在列表里显得杂乱，影响快速扫描
- 所有正文标题统一 H2，禁止 H3/H4——避免层级嵌套增加认知负担，笔记是信息摘要不是文档
- 来源链接**只写在首行 blockquote**，文末不重复——多篇合并时重复来源会产生大量噪音；首行位置醒目足够
- 多篇合并：每章节末「我的思考」后插入两个 `<p></p>` 空行——视觉上明确分隔各章节，避免内容粘连
- 只有纯粘贴文本才在文末附 H2「原文」章节——URL/文件有原始来源可追溯，无需保留全文；粘贴文本无法追溯，附原文保证可验证

### 第三步：新建笔记并写入

> ⚠️ **`batch_edit` 写入规则**：
> - **多个独立 `insert` 操作指向同一锚点**时，实际顺序与数组顺序**相反**（WPS MCP 行为）→ 需倒序排列
> - **单个 `insert` 操作内部包含多个 block 的 XML 字符串**时，块的顺序就是文档中出现的顺序 → **无需倒序**，按正常阅读顺序写即可

```
1. create_note({ title: "[内容标题] · 提炼 [YYYY-MM-DD]" })
2. get_note_outline(note_id)         → 获取初始 block ID
3. batch_edit(note_id, [...])        → 倒序排列，一次性写入全部内容
4. sync_note(note_id)                → 同步到云端（失败时见故障排查）
```

写入后若需追加内容，必须先调用 `get_note_outline` 刷新 block ID，再进行下一次写入——WPS MCP 写入后 block ID 可能变化，使用缓存 ID 会导致 `BLOCK_NOT_FOUND`。

### 质量检查（写入前必做）
- 每个模板定义的模块已完整输出，无跳过（文字类：一句话概括 / 核心观点 / 金句摘录；图片类：一句话概括 / 内容解读 / 核心信息）
- 图片已经过视觉分析，不以「图片无法处理」为由跳过
- 来源只在首行 blockquote，文末无重复来源
- 使用了最新的 block ID（来自 `get_note_outline`，非缓存）

---

## 示例

### 示例 1：提炼网页文章
用户说：「https://example.com/article 帮我总结一下」
执行：
1. `WebFetch(url)` 获取正文
2. 提炼一句话概括、核心观点、金句摘录
3. `create_note` → `batch_edit` 写入笔记；URL 只写在首行 blockquote，文末不重复

### 示例 2：解读本地图片（路径 A）
用户说：「@/Users/zoez/Desktop/screenshot.png 帮我解读」或直接拖入截图
执行：
1. `Read(图片路径)` → AI 视觉分析，提取图片内所有文字、图表、界面元素
2. `create_note` 创建「[图片主题] · 提炼 YYYY-MM-DD」
3. `batch_edit` 写入：📌 一句话概括 / 🔍 内容解读 / 💡 核心信息 / 💬 我的思考

### 示例 3：多篇内容合并
用户说：「https://a.com https://b.com 还有这段文字 [粘贴内容] 帮我一起整理成笔记」
执行：
1. 依次获取每篇内容
2. `create_note` 标题为「内容提炼合集 · YYYY-MM-DD」
3. 每篇作为独立章节（一、二、三…）写入同一篇笔记
4. 粘贴文本在末尾附完整原文；URL 只附链接

### 示例 4：网络图片解读（路径 B，使用 WPS 笔记原生识图）
用户说：「https://example.com/infographic.png 帮我解读」
执行：
1. `create_note` 创建笔记
2. `insert_image(url)` 将图片插入笔记，获取 block_id
3. `read_image(note_id, block_id)` 取回 base64
4. AI 视觉解读 base64 内容
5. `edit_block` 在图片下方追加解读文字

### 示例 5：解读笔记内已有图片（路径 D）
用户说：「帮我解读一下笔记里那张图」
执行：
1. `get_note_outline(note_id)` 找到 type="image" 的 block_id
2. `read_image(note_id, block_id)` → base64
3. AI 视觉解读
4. `edit_block` 在图片下方 insert 解读内容

---

## 图片类 PDF/PPT 处理流程

当 `Read(pdf路径)` 提取的文字少于 50 字时，判定为图片类文档，执行以下流程：

### 1. 运行转换脚本
```bash
python3 scripts/pdf_to_images.py /path/to/file.pdf
```
脚本会自动安装 pymupdf（已装则秒过），将每页保存为 `/tmp/pdf_pages_<pid>/page_NN.png`（PID 隔离，避免并发覆盖）。完整脚本见 [scripts/pdf_to_images.py](scripts/pdf_to_images.py)。

### 2. 逐页视觉读取
对脚本输出目录中的每张 `page_NN.png` 调用 `Read(图片路径)` 进行 AI 视觉分析，提取页面中所有可见文字和图表信息。

### 3. 汇总后正常提炼
将所有页面内容合并，按照标准流程提炼核心观点、金句摘录等。

> 最多处理 40 页；超过 40 页则处理前 40 页并在笔记中注明「仅提炼前 40 页内容，共 N 页」。网页内嵌图片同理：先从正文提取图片 URL，再走网络图片处理路径（`insert_image` + `read_image`）。

## 故障排查

| 情况 | 处理方式 |
|------|---------|
| URL 被拦截 / 返回空 | 按正常笔记结构写入：首行 blockquote 保留来源 URL，然后用 h2「❗ 访问受限」+ p「该网页访问受限，如需提炼请手动复制原文到 AI 工具处理」，不重试 |
| PDF/PPT 为图片页 | **执行图片转换流程**：① `pip3 install pymupdf -q`（已装则跳过）② 运行 `pdf_to_images.py` 将每页转为 PNG ③ 逐页 `Read(页面图片)` 视觉分析 ④ 汇总所有页面内容后正常提炼 |
| `.docx` 读取乱码 | 提示用户另存为 `.txt` 后重试 |
| 内容超长（>1 万字）| 分段提炼后合并，提示用户正在分段处理 |
| 内容为空 | 告知「未找到可提炼内容」，不创建笔记 |
| 无法识别标题 | 从正文首句 / H1 / 文件名推断；推断不出则用「无题内容提炼」|
| 多语言内容 | 提炼结果统一用中文输出 |
| 图片格式不支持（Read 工具）| 仅支持 `.png` `.jpg` `.jpeg` `.gif` `.webp`；其他格式用 Shell 转换：`sips -s format jpeg 原文件 --out 新文件.jpg` |
| `IMAGE_FETCH_FAILED` | 图片 URL 必须直接返回 image/* 内容；若失败改用 `Read(url图片)` 直接视觉分析 |
| `read_image` 返回空 | 图片 block 刚插入可能需 1-2 秒渲染，稍等后重试；确认 block_id 来自 `get_note_outline` 而非缓存 |
| 网页图片无法提取 | WebFetch 无法下载图片二进制；改用 `insert_image(img_url)` + `read_image` 路径 |
| `BLOCK_NOT_FOUND` | 重新调用 `get_note_outline` 获取最新 block ID，不使用缓存 ID |
| `sync_note` 失败 | 笔记内容已写入本地，提示用户「同步失败，笔记内容已保存，请在 WPS 笔记客户端中手动同步」；不重新创建笔记 |
| `WEBSOCKET_NOT_CONNECTED` | 提示用户检查 WPS 笔记是否已打开并登录 |
