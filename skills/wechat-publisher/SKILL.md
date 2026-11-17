---
name: wechat-publisher
description: |
  【公众号发布助手】将 WPS 笔记排版并导出为微信公众号 HTML。
  当用户说"发公众号""排版公众号""导出到公众号""我要发布了""文章排版""发一下""排版这篇文章"时使用。
  这是创作流程的最后一步：内容已完成，需要排版发布到公众号。
  核心能力：1)自动套用排版模板 2)占位符标签转样式 3)生成可直接粘贴的 HTML。
  输入：WPS 笔记 ID（内容已完成的笔记）。输出：带内联样式的 HTML 文件。
  不要用于创作内容，只用于已完成的排版发布。
metadata:
  version: "1.1.0"
  category: publishing
  tags: [wechat, publishing, html-export, content-formatting]
  dependencies: [wpsnote]
---

# WeChat Publisher - 公众号发布助手

将已完成的 WPS 笔记内容，一键排版并导出为微信公众号 HTML 格式。这是创作流程的最后一步：内容已完成，只需排版发布。

## 使用场景

**典型工作流**：
1. 用 `content-creator` 创作文章内容
2. 保存到 WPS 笔记
3. **用本 skill 导出排版好的 HTML** ← 你在这里
4. 粘贴到公众号后台直接发布

---

## Contract（契约）

### Input Contract

**触发条件**：
- "发公众号"
- "排版公众号"
- "导出到公众号"
- "我要发布了"
- "文章排版"
- "生成公众号 HTML"
- "这篇可以发了"
- "帮我排版一下"

**输入类型**：
1. **WPS 笔记 ID**（必填）：内容已完成的笔记
2. **模板名称**（可选）：`default`/`minimal`/`elegant`，默认 `blue-theme`
3. **输出路径**（可选）：默认生成 `{标题}_formatted.html`

**前置条件**：
- 笔记内容已完成（不是空笔记）
- 笔记已保存并同步到云端
- 内容建议 < 20000 字符

### Output Contract

| 文件 | 说明 |
|------|------|
| `{标题}_formatted.html` | 带内联样式的公众号排版文件，可直接粘贴到公众号编辑器 |

**排版特性**：
- WPS 笔记 XML **直接转 HTML**（无 Markdown 中间层，样式精度更高）
- WPS 预设颜色（fontColor / fontHighlightColor）完整映射到内联样式
- 代码块语法高亮
- 图片自适应处理
- 移动端阅读优化

### Error Contract

| 错误场景 | 错误码 | 处理方式 |
|---------|--------|----------|
| 笔记不存在 | `NOTE_NOT_FOUND` | 检查 note_id 是否正确 |
| 笔记为空 | `EMPTY_CONTENT` | 提示先完成内容创作 |
| 内容过长 | `CONTENT_TOO_LONG` | 建议拆分为多篇发布 |
| 图片处理失败 | `IMAGE_ERROR` | 检查图片链接有效性 |

---

## 工具优先级策略

**优先使用 CLI，降级到 MCP**：

```
检查 wpsnote-cli 是否可用（wpsnote-cli auth status --json）
    ↓ 可用（推荐路径）
wpsnote-cli find / list  → 获取笔记 ID
wpsnote-cli read --note_id <id> --json → 获取笔记内容（XML）
    ↓ CLI 不可用（命令不存在 / 认证失败）
[降级] MCP: search_notes / list_notes
[降级] MCP: read_note
```

**AI 操作决策树**：

```
用户触发「排版发布」
    │
    ├─ 检测 wpsnote-cli
    │       ↓ 可用
    │   ① 无 note_id → wpsnote-cli list --limit 20 --json（列出供确认）或 find
    │     有 note_id → 直接跳到 ③
    │       ↓ 不可用
    │   ① 无 note_id → MCP: list_notes({ limit: 20 }) / search_notes(...)
    │
    ├─ ② 搜索确认（用户给了关键词）
    │     CLI:  wpsnote-cli find "xxx" --json
    │     MCP:  search_notes({ keywords: ["xxx"] })
    │
    ├─ ③ 读取笔记内容
    │     CLI:  wpsnote-cli read --note_id <id> --json
    │     MCP:  read_note({ note_id: <id> })
    │
    └─ ④ 执行导出脚本
          python scripts/export-to-html.py --note-id <id>
          → 生成 "{标题}_formatted.html"
```

---

## 快速开始

### 方式一：CLI 读取 + 脚本转换（推荐）

```bash
# 通过 note_id 直接导出
python scripts/export-to-html.py --note-id "abc123"

# 指定模板风格
python scripts/export-to-html.py --note-id "abc123" --template "elegant"

# 搜索笔记并导出
python scripts/export-to-html.py --search "文章标题"
```

### Python API

```python
from scripts.export_to_html import WPSNoteExporter

exporter = WPSNoteExporter()
exporter.export(
    note_id="abc123",
    template_name="default",
    output_path="./article.html"
)
```

### 方式二：MCP 工具方式（CLI 不可用时降级）

通过 `wpsnote` SKILL 的 MCP 工具读取笔记内容，再转换为 HTML：

```
# 1. 搜索并获取笔记
search_notes({ keywords: ["文章标题"] }) → note_id

# 2. 读取笔记内容
read_note({ note_id }) → xml_content

# 3. 转换为 HTML（本地脚本处理）
python scripts/export-to-html.py --note-id <id>
```

### 完整 MCP 工作流示例

```
# 步骤 1：搜索或列出目标笔记
list_notes({ keyword: "AI 工具介绍", limit: 20 })
→ notes[0].note_id = "abc123"

# 步骤 2：读取笔记内容（根据大小选择方式）
get_note_outline({ note_id: "abc123" })
→ blocks: [...]

read_note({ note_id: "abc123" })
→ xml_content: "<h1>AI 工具介绍</h1><p>...</p>"

# 步骤 3：导出为 HTML（本地脚本转换）
python scripts/export-to-html.py --note-id "abc123" --template blue-theme
→ 生成 "AI 工具介绍_formatted.html"
```

---

## 占位符标签（快速排版）

在 WPS 笔记中使用这些标签，导出时自动转换为对应样式：

| 标签 | 用法 | 效果 |
|------|------|------|
| `<b/>` | `<b/>文字</b>` | 橙色加粗（整段或行内） |
| `<h2/>` | `<h2/>大标题</h2>` | 蓝色大标题（一级章节） |
| `<h3/>` | `<h3/>小标题</h3>` | 蓝色小标题（二级分节） |
| `<bq/>` | `<bq/>引用文字</bq>` | 灰底蓝边引用块 |
| `<note/>` | `<note/>注释文字</note>` | 灰色小字注释 |

**使用示例**：

```
<h2/>01｜核心观点

<b/>整段橙色加粗，适合核心金句。</b>

<b/>行内加粗</b> 用于强调重点词汇。

<h3/>深入分析

正文段落正常书写...

<bq/>引用块适合摘录观点或补充说明。</bq>

<note/>注：本文仅代表个人观点。</note>
```

---

## WPS 笔记颜色 → HTML 颜色映射

WPS 笔记的 XML 中颜色受**预设色板**约束，导出时按下表映射为公众号内联样式 RGB 值：

### fontColor（字体颜色）

| WPS XML 值 | 含义 | HTML 输出 |
|-----------|------|----------|
| `#080F17` | 黑色 | `color: rgb(8,15,23)` |
| `#C21C13` | 红色 | `color: rgb(194,28,19)` |
| `#DB7800` | 橙色 | `color: rgb(219,120,0)` |
| `#078654` | 绿色 | `color: rgb(7,134,84)` |
| `#0E52D4` | 蓝色 | `color: rgb(14,82,212)` |
| `#0080A0` | 浅蓝 | `color: rgb(0,128,160)` |
| `#757575` | 灰色 | `color: rgb(117,117,117)` |
| `#DA326B` | 粉色 | `color: rgb(218,50,107)` |
| `#D1A300` | 金色 | `color: rgb(209,163,0)` |
| `#58A401` | 浅绿 | `color: rgb(88,164,1)` |
| `#116AF0` | 亮蓝 | `color: rgb(17,106,240)` |
| `#A639D7` | 紫色 | `color: rgb(166,57,215)` |

### fontHighlightColor（文字背景高亮）

| WPS XML 值 | 含义 | HTML 输出 |
|-----------|------|----------|
| `#FBF5B3` | 黄色 | `background-color: rgb(251,245,179); padding:0 2px; border-radius:2px` |
| `#F8D7B7` | 橙色 | `background-color: rgb(248,215,183); ...` |
| `#F7C7D3` | 粉色 | `background-color: rgb(247,199,211); ...` |
| `#DFF0C4` | 绿色 | `background-color: rgb(223,240,196); ...` |
| `#C6EADD` | 深绿 | `background-color: rgb(198,234,221); ...` |
| `#D9EEFB` | 蓝色 | `background-color: rgb(217,238,251); ...` |
| `#D5DCF7` | 浅蓝 | `background-color: rgb(213,220,247); ...` |
| `#E6D6F0` | 紫色 | `background-color: rgb(230,214,240); ...` |
| `#E6E6E6` | 灰色 | `background-color: rgb(230,230,230); ...` |

> **注意**：任意 hex 色值在 WPS 编辑器中会被静默丢弃，导出脚本只处理上述预设色板中的颜色，其他值忽略不渲染。

---

## 模板风格

| 模板 | 特点 | 适用场景 |
|------|------|----------|
| `blue-theme` ⭐默认 | 蓝色强调色，现代简洁 | 科技、企业、正式文档 |
| `default` | 橙色风格，专业美观 | 通用场景 |
| `minimal` | 极简风格，干净利落 | 技术文档、教程 |
| `elegant` | 优雅精致，细节丰富 | 深度长文、品牌内容 |

### blue-theme 蓝色主题

基于样本 HTML 的蓝色主题，特点：
- **主色**: `rgb(36, 91, 219)` 深蓝色
- **正文字号**: 15px（比默认更小更紧凑）
- **行距**: 2.0（更舒适的可读性）
- **引用块**: 左边框 3px + 浅灰背景
- **分栏**: Flex 布局，居中对齐

使用方法：
```bash
python scripts/export-to-html.py --note-id "abc123" --template blue-theme
```

---

## 与 content-creator 的组合

```
创作流程：

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  content-       │     │   WPS 笔记      │     │  wechat-        │
│  creator        │ --> │   （内容完成）   │ --> │  publisher      │
│  （创作内容）    │     │                 │     │  （排版发布）    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              你在这里 ↑
```

**完整示例**：

```bash
# 1. 创作内容
python scripts/create-content.py --topic "AI 工具介绍"

# 2. 通过 wpsnote 写入 WPS 笔记（MCP create_note + batch_edit，或 wpsnote-cli create / batch-edit）

# 3. 排版发布（本 skill）
python scripts/export-to-html.py --search "AI 工具介绍"
```

---

## 转换流程

```
WPS 笔记 XML
    │
    ├─ 占位符处理（<b/> <h2/> <bq/> <note/>）
    │
    ├─ xml_to_html()：逐块渲染
    │   ├─ <h1>/<h2>       → <h2 style="...蓝色...">
    │   ├─ <h3>-<h6>       → <p><span style="...蓝色...">
    │   ├─ <p>             → <p><span style="...灰色正文...">
    │   ├─ <p listType>    → 橙色圆点 / 橙色数字列表
    │   ├─ <blockquote>    → 灰底蓝边引用块
    │   ├─ <codeblock>     → 语法高亮代码框
    │   ├─ <table>         → 蓝色表头表格
    │   ├─ <highlightBlock>→ 高亮提示块（保留 WPS 配色）
    │   ├─ <columns>       → Flex 分栏
    │   ├─ <span fontColor>→ WPS 预设颜色 → RGB 内联样式
    │   └─ <strong>/<em>  → 加粗 / 斜体
    │
    └─ 套入 template.html 壳 → {标题}_formatted.html
                                      │
                                      └─ 浏览器打开 → 点「复制内容」→ 粘贴到公众号
```

## 文件结构

```
wechat-publisher/
├── SKILL.md               # 本文件
├── scripts/
│   ├── export-to-html.py  # 核心导出脚本（WPS XML → HTML 直接转换）
│   └── md_to_html.py      # 独立 MD 转 HTML 脚本（本地 .md 文件用）
├── templates/
│   ├── template.html      # HTML 输出壳（含复制按钮）
│   ├── preview.html       # 排版样例（各元素效果预览）
│   ├── default.yaml       # 默认模板（橙色风格）
│   ├── blue-theme.yaml    # 蓝色主题模板
│   ├── minimal.yaml       # 极简模板
│   └── elegant.yaml       # 优雅模板
└── references/
    └── format-guide.md    # 格式规范
```

---

## 常用编排模式

### 模式 1：按最近笔记导出

列出最近笔记确认后导出：

```bash
# CLI 方式（推荐）
wpsnote-cli list --limit 20 --json
python scripts/export-to-html.py --note-id <id> --template blue-theme

# MCP 方式（降级）
list_notes({ limit: 20 }) → note_id
python scripts/export-to-html.py --note-id <id> --template blue-theme
```

### 模式 2：搜索后导出

用户不记得笔记 ID，先搜索再导出：

```bash
# CLI 方式（推荐）
python scripts/export-to-html.py --search "文章标题"

# MCP 方式（降级）
search_notes({ keywords: ["文章标题"] }) → note_id
python scripts/export-to-html.py --note-id <id>
```

---

## Troubleshooting

### CLI 不可用

**现象**：`wpsnote-cli` 命令未找到或认证失败
**解决**：自动降级使用 MCP 工具，流程不变

### 笔记读取失败 (NOTE_NOT_FOUND)

**现象**：`search_notes` 或 `read_note` 返回笔记不存在（`4048001901`）
**原因**：笔记 ID 错误或笔记已移入回收站
**解决**：
1. 用 `list_notes` 或 `search_notes` 重新确认正确的 `note_id`
2. 检查笔记是否被移入回收站（可用 `list_trash` 查看并通过 `restore_note` 恢复）

### 内容为空或格式错乱

**现象**：导出的 HTML 内容为空或格式异常
**原因**：笔记 XML 解析失败、包含不支持的 block 类型
**解决**：
1. 检查笔记是否确实包含内容（不是空笔记）
2. 查看笔记是否包含 embed、note_audio_card 等只读内容
3. 手动检查 XML 结构是否有异常标签

### 图片无法显示

**现象**：公众号后台图片显示为空白或红叉
**原因**：图片 URL 失效、本地图片未正确转 base64、图片格式不支持
**解决**：
1. 网络图片：检查 URL 是否直接指向图片资源（不是 HTML 页面）
2. 本地图片：确认已转为 base64 data URI
3. 图片格式：优先使用 PNG、JPG，避免 WebP

### 占位符标签不生效

**现象**：`<b/>`、`<h2/>` 等标签在 HTML 中显示为纯文本
**原因**：标签格式错误、嵌套不当
**解决**：
1. 确保标签正确闭合：`<b/>文字</b>` ✓ `<b/>文字` ✗
2. 检查标签是否嵌套在其他标签内导致解析失败
3. 参考占位符标签章节的正确用法

### 模板加载失败

**现象**：指定模板后样式未生效，使用默认样式
**原因**：模板名称拼写错误、模板文件缺失、YAML 解析错误
**解决**：
1. 检查模板名称拼写（`blue-theme`、`default`、`minimal`、`elegant`）
2. 确认 `templates/` 目录存在对应 `.yaml` 文件
3. 检查模板 YAML 格式是否正确

### HTML 粘贴到公众号后样式丢失

**现象**：本地预览正常，但粘贴到公众号后台样式错乱
**原因**：公众号编辑器过滤部分 CSS、微信内置浏览器兼容性问题
**解决**：
1. 使用内联样式（`style="..."`），避免 class 选择器
2. 避免使用复杂 CSS 特性（grid、flex 谨慎使用）
3. 在公众号后台预览后，用手机扫码查看实际效果

### MCP 工具调用失败

**现象**：`wpsnote` MCP 的 `read_note` 等工具报错
**原因**：笔记不存在、`block_id` 过期、API Key 权限不足或网络异常
**解决**：
1. 检查云端 MCP `X-API-Key` 配置与网络连通性（或执行 `wpsnote-cli auth status`）
2. 重新调用 `list_notes` / `get_note_outline` 获取最新 `note_id` 或 `block_id`
3. 参考 `wpsnote` SKILL 的 Troubleshooting / `ERROR_CODES.md`

---

## 注意事项

1. **这是最后一步**：只用于内容已完成的笔记，不要在这里创作
2. **CLI 优先**：`wpsnote-cli` 可用时总是首选，速度快且更稳定
3. **行内代码**：WPS XML 不支持行内代码，会被转为纯文本
4. **内容长度**：超过 20000 字符建议拆分多篇
5. **图片处理**：WPS 笔记里的图片 `src` 是 WPS CDN 地址，导出时**直接引用**，微信公众号可正常加载；不做 base64 转换（本地路径上传公众号容易失败）
6. **图片说明**：带 `caption` 属性的图片，导出后会在图片下方生成灰色居中小字说明
7. **颜色约束**：WPS 笔记只支持预设色板，任意 hex 会被编辑器静默丢弃；导出脚本按预设色板映射到 RGB，非预设色值直接忽略

---

## Resources

- 格式规范：`references/format-guide.md`
- 模板配置：`templates/`
- 核心脚本：`scripts/export-to-html.py`
- MD 转换脚本：`scripts/md_to_html.py`
