---
name: note-copilot
description: 笔记协作助手：帮用户打磨当前 WPS 笔记，识别并处理笔记中的 *** 和 /// 援助标记，同时在发现明显逻辑错误时以着色方式提醒。当用户说「帮我打磨笔记」「打磨一下」「帮我看看笔记」「处理一下标记」「定期帮我打磨」，或提到笔记中有 *** 或 /// 需要处理时使用此 skill。
metadata:
  author: Yicheng Xu
  version: "1.0.0"
  tags: [wps-note, note-editing, copilot, writing-assistant]
---

# 笔记协作助手

陪伴用户打磨笔记的 AI 助手。扫描当前笔记，处理用户留下的 `***`（补全）和 `///`（引用）标记，并在发现明显逻辑错误时轻提醒。

## 核心工作流

```
用户发起后：
  1. 判断是否首次使用 → 首次输出引导说明
  2. get_current_note()             → 获取当前笔记 note_id
  3. read_note(note_id)             → 读取全文 XML
  4. 扫描所有 *** 和 /// 标记       → 收集待处理列表
  5. 逐一处理每个标记（*** 补全 / /// 引用）
  6. 检查明显逻辑错误 → 高阈值，仅标注真正的矛盾
  7. 输出处理摘要

定期模式（用户明确说「定期帮我打磨」时才启动）：
  执行一次打磨 → sleep 300秒 → 重复
  用户说「停止」时退出
```

## 首次使用引导

**判断方式**：本次对话中是否已经输出过引导说明。若未输出过，则在开始打磨前先输出：

```
笔记协作助手已就绪 ✓

我可以帮你打磨当前笔记，处理你留下的标记：

  ★ 补全内容：在任意位置输入 ***
    AI 会结合上下文，以你的写作风格自动补全
    例：「本次会议的核心问题是 ***，我们决定...」

  ★ 引用资料：在任意位置输入 ///
    AI 会搜索相关笔记或网络资料，以引用形式写入
    例：「关于这个概念，/// 可以补充说明」

  注意：*** 和 /// 在代码块中不会被处理。
  处理完成后，标记会自动删除。

开始打磨...
```

## Step 1：获取当前笔记

```
get_current_note()
→ { note_id, title }
```

若返回 `NO_ACTIVE_EDITOR_WINDOW`：提示用户打开笔记后重试，停止执行。

## Step 2：读取笔记内容

笔记较短（大纲 block 数 ≤ 80）：
```
read_note(note_id)
→ 获取完整 XML 内容
```

笔记较长（block 数 > 80）：
```
get_note_outline(note_id)                     → 获取所有 block 的 id、type、preview
search_note_content(note_id, query="***")     → 精确定位含 *** 的 block
search_note_content(note_id, query="///")     → 精确定位含 /// 的 block
```

## Step 3：识别援助标记

扫描笔记内容，找出所有 `***` 和 `///`。

### 识别规则：是援助请求还是占位符/代码？

| 场景 | 判断 | 处理 |
|------|------|------|
| block type 为 `codeblock` | 不处理 | 跳过 |
| `***` / `///` 出现在 `` ` `` 包裹的行内代码中 | 不处理 | 跳过 |
| `***` 紧邻正则、公式等逻辑性符号（如 `\d***`、`a***b`） | 不处理 | 跳过 |
| `///` 紧邻 URL 或路径（如 `http:///`、`path///file`） | 不处理 | 跳过 |
| 普通段落 `<p>`、标题 `<h1>`~`<h6>`、列表项中的独立 `***` 或 `///` | **援助请求** | 处理 |
| `<blockquote>` 中的 `***` 或 `///` | **援助请求** | 处理 |

**原则**：优先保守判断。若不确定，跳过并在摘要中告知用户。

## Step 4：处理 *** — 补全内容

### 获取上下文

```
read_blocks(note_id, block_id=<含***的block>, before=5, after=5)
→ 获取该 block 及前后各 5 个 block 的完整 XML
```

### 分析文风

分析前后文的以下维度，生成时严格匹配：

| 维度 | 观察点 |
|------|-------|
| 语气 | 口语（「感觉」「其实」）vs 书面（「经分析」「综上」） |
| 人称 | 第一人称 vs 客观陈述 |
| 详略 | 每条字数，是否展开说明 |
| 格式 | 所在 block 的 type（p/h/li），是否有加粗/斜体 |
| 标点习惯 | 惯用标点，中英混写程度 |

### 生成补全

- 严格基于笔记上下文生成，不凭空发明信息
- 保持所在 block 的原始 type 和格式属性不变
- 不引入新的排版元素（不新增标题、色块、表格）
- 补全内容替换 `***` 本身，其余文字保持不变

### 写回

```
// 读取该 block 完整 XML
read_blocks(note_id, block_ids=[<block_id>])

// 将 XML 中的 *** 替换为补全内容，用 replace 写回
edit_block(note_id, op="replace", block_id=<block_id>, content=<替换后的完整XML>)
```

**注意**：每次 edit_block 后 block_id 会变化，后续操作需重新 `get_note_outline` 或 `search_note_content` 获取新 ID。

## Step 5：处理 /// — 引用外部内容

### 提取关键词

读取 `///` 所在 block 及前后 5 个 block，分析：
- `///` 前的主题词/问题
- 整体笔记的主题（来自标题和已有内容）

### 判断搜索范围（AI 自由决策）

优先搜索 WPS 笔记，必要时联网补充：

**搜索笔记**：
```
search_notes(keyword="<关键词>", limit=5, sort="update_time", direction="desc")
→ 找到相关笔记后，read_note(note_id) 读取内容
→ 提取最相关的 3-5 句
```

**联网搜索**（笔记中无相关内容，或需要补充外部资料时）：
```
WebFetch 或内置搜索能力
→ 提取最相关段落（不超过 5 句）
```

### 生成引用内容

引用格式（贴合前后文，不引入新视觉层级）：

```xml
<!-- 来自笔记 -->
<blockquote>[引用内容摘要，3-5 句]</blockquote>
<p><span fontColor="#757575">来源：[笔记标题]</span></p>

<!-- 来自网络 -->
<blockquote>[引用内容摘要，3-5 句]</blockquote>
<p><span fontColor="#757575">来源：[页面标题]（[URL]）</span></p>
```

若搜索无结果：
```xml
<p><span fontColor="#757575">（未找到相关内容，请手动填写）</span></p>
```

### 写回

```
// 1. 刷新大纲，获取含 /// 的 block 的最新 ID
get_note_outline(note_id)

// 2. 原子操作：删除含 ///  的 block，在其位置插入引用内容
batch_edit(note_id, operations=[
  { op: "delete", block_ids: [<///所在block_id>] },
  { op: "insert", anchor_id: <前一个block_id>, position: "after",
    content: "<blockquote>...</blockquote><p><span fontColor=\"#757575\">来源：...</span></p>" }
])
```

**注意**：`batch_edit` 执行顺序固定为 delete → insert，无需担心顺序问题。若 `///` 是笔记第一个 block，用后面 block 作为 anchor，position 设为 `"before"`。

## Step 6：逻辑标注（高阈值）

整理完标记后，通读笔记内容，**仅在以下情况才标注**：

**触发标准（必须满足其一）**：
- 同一笔记中两处内容直接矛盾（如「A 导致 B」和「B 导致 A」）
- 数字/数据明显自相矛盾（如前文「共 5 项」，后文列了 7 项）
- 因果关系明显颠倒

**不触发**：
- 内容不够完整（让用户用 `***` 补）
- 表达不够清晰但没有逻辑错误
- 观点有争议但非错误
- 任何「可以更好」的建议

**标注方式**：在问题 block **之后**插入一行提醒：
```
edit_block(note_id, op="insert", anchor_id=<问题block_id>, position="after",
  content='<p><span fontHighlightColor="#F8D7B7">⚠ [一句话描述问题，如「此处结论与第2段相矛盾」]</span></p>')
```

**幂等检查**：在插入前，先 `search_note_content(note_id, query="⚠")` 确认该处是否已有标注，避免重复。

## Step 7：输出处理摘要

```
✓ 笔记打磨完成「[笔记标题]」

  *** 处理：N 处
  /// 处理：N 处（引用了 [来源]）
  逻辑提醒：N 处
  跳过（代码/占位）：N 处
```

若无任何标记且无逻辑问题：
```
✓ 已扫描「[笔记标题]」，未发现需处理的标记。
```

定期模式下追加：
```
下一轮：5 分钟后
```

## 幂等与防重原则

- **处理完的标记必须删除**：`***` 通过 replace 替换，`///` 通过 delete + insert 替换，原标记不保留
- **未处理的标记不动**：本轮跳过的标记（代码块中等），保持原样，不添加任何内容
- **逻辑标注不重复**：插入前先检查是否已标注
- **定期模式有上下文时不重复提示**：同一处已处理内容，本对话内不再重复说明

## 定期模式

仅当用户明确说「定期帮我打磨」「每 5 分钟帮我打磨」时启动：

```
启动时：
  告知用户：「已开启定期打磨，每 5 分钟自动扫描当前笔记。说「停止」可随时退出。」

loop:
  执行完整打磨流程（Step 1-7）
  sleep 300 秒
  重复（直到用户说「停止」「结束」「stop」）

退出时：
  输出「已停止定期打磨。」
```

## 错误处理

| 错误 | 处理方式 |
|------|---------|
| `NO_ACTIVE_EDITOR_WINDOW` | 提示用户打开笔记后重试，停止执行 |
| `BLOCK_NOT_FOUND` | 重新 `get_note_outline` 刷新 ID 后重试一次 |
| `EDITOR_NOT_READY` | 等待 2 秒后重试写入 |
| `DOCUMENT_READ_ONLY` | 告知用户笔记为只读，停止处理 |
| 搜索（`///`）无结果 | 在该处插入灰色提示「未找到相关内容，请手动填写」 |
| `read_note` 内容被截断（`truncated: true`） | 改用 `get_note_outline` + `search_note_content` 定位标记，再 `read_blocks` 读取上下文 |
