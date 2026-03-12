# WPS Note MCP — 用例手册

按复杂度递进组织的用例集，覆盖基础操作、组合工作流和端到端场景。组合工作流包含完整的请求/响应示例数据。

每个用例包含：**场景描述** → **用户 Prompt** → **预期工具调用** → **验证标准**

---

## L1 基础操作

单工具调用，含正常路径和边界情况。适用于 QA 验收和 Agent 快速参考。

---

### 1.1 读取工具

#### UC-R01：获取笔记大纲

**场景**：用户想快速了解一篇笔记的结构。

**Prompt**：`"帮我看看这篇笔记的结构"`

**调用**：
```
get_note_outline({ note_id: "<id>", include_preview: true })
```

**验证**：
- [ ] 返回 `ok: true`
- [ ] `data.blocks` 数组非空
- [ ] 每个 block 包含 `id`、`type`、`preview` 字段
- [ ] `heading` 类型的 block 包含 `attrs.level`

**边界**：
- `max_depth: 1`——只返回顶层标题
- `include_preview: false`——不含预览文本
- `preview_length: 10`——预览截断为 10 字符
- 空笔记——返回单个空 `paragraph` block

---

#### UC-R02：按 ID 读取 block

**场景**：Agent 需要读取特定段落的完整内容。

**Prompt**：`"读一下第二章的内容"`

**调用**：
```
read_blocks({ note_id: "<id>", block_ids: ["<block_id_1>", "<block_id_2>"] })
```

**验证**：
- [ ] 返回的每个 block 包含 `content`（XML 格式）
- [ ] 返回顺序与请求的 `block_ids` 一致
- [ ] `type` 字段与大纲中的类型匹配

**边界**：
- 读取 `embed` block——返回只读占位文本

---

#### UC-R03：读取笔记全文

**场景**：短笔记，直接读取全文。

**Prompt**：`"把这篇笔记完整读给我"`

**调用**：
```
read_note({ note_id: "<id>" })
```

**验证**：
- [ ] `data.content` 包含完整 XML
- [ ] 每个块级标签包含 `id` 属性（如 `<p id="xxx">`）
- [ ] `data.truncated` 为 `false`

**边界**：
- `max_length: 500`——内容截断，`truncated: true`
- 超大文档（>100K 字符）——考虑用 `read_section` 替代

---

#### UC-R04：笔记内搜索

**场景**：在一篇长文档中定位特定内容。

**Prompt**：`"找一下这篇笔记里提到'预算'的地方"`

**调用**：
```
search_note_content({ note_id: "<id>", query: "预算" })
```

**验证**：
- [ ] 返回匹配 block 的 `block_id`、`type`、`preview`
- [ ] `preview` 包含搜索关键词的上下文

**边界**：
- 无匹配结果——返回空数组，`ok: true`
- `max_results: 1`——只返回第一个匹配
- 搜索 `embed` block 中的内容——可能无法匹配（只读占位）

---

#### UC-R05：读取 block 上下文

**场景**：找到某个 block 后想看前后文。

**Prompt**：`"这段话的前后文是什么？"`

**调用**：
```
read_blocks({ note_id: "<id>", block_id: "<id>", before: 3, after: 3 })
```

**验证**：
- [ ] 返回锚点 block 及前后各 3 个 block 的内容
- [ ] 包含 block ID 标注

**边界**：
- 锚点在文档开头——`before` 返回不足 3 个
- `include_anchor: false`——不包含锚点本身
- `before: 0, after: 0`——仅可能返回锚点本身

---

#### UC-R06：按标题读取章节

**场景**：读取某个章节的完整内容。

**Prompt**：`"读一下'技术方案'这一章"`

**调用**：
```
read_section({ note_id: "<id>", heading_block_id: "<heading_id>" })
```

**验证**：
- [ ] 返回从标题到下一个同级标题之间的所有内容
- [ ] 包含子标题及其内容

**边界**：
- `include_subsections: false`——不含子标题内容
- `max_blocks: 5`——截断返回
- 文档最后一个章节——读到文档末尾

---

#### UC-R07：获取语音转写

**场景**：用户想查看笔记中某段录音的转写文本。

**Prompt**：`"帮我看看这段录音说了什么"`

**调用**：
```
1. get_note_outline({ note_id: "<id>" })
   → 找到 type="note_audio_card" 的 block，获取 attrs.shorthand_id
2. get_audio_transcript({ shorthand_id: "<shorthand_id>" })
   → 返回转写句子列表
```

**验证**：
- [ ] outline 中 `note_audio_card` block 包含 `attrs.shorthand_id`
- [ ] 返回的 `sentences` 数组包含 `sentence_id`、`speaker_name`、`text`、`start_time`、`end_time`
- [ ] `sentence_count` 与 `sentences` 数组长度一致

---

#### UC-R08：获取当前光标所在 block

**场景**：用户正在编辑当前打开的笔记，希望围绕光标位置继续插入或替换。

**Prompt**：`"我现在光标停在哪一段？"`

**调用**：
```
get_cursor_block()
```

**验证**：
- [ ] 返回 `block_id`
- [ ] 返回 `block_type`
- [ ] 返回 `note_id`

**边界**：
- 光标位于高亮块（subdoc）内部——返回不支持错误
- 光标位于分栏（columns）内部——返回不支持错误
- 当前无打开的笔记——返回 `NO_ACTIVE_EDITOR_WINDOW`

---

#### UC-R09：获取 XML 格式参考

**场景**：首次编辑前，希望拿到完整 XML 标签与属性说明。

**Prompt**：`"给我一份 WPS Note XML 写入格式参考"`

**调用**：
```
get_xml_reference()
```

**验证**：
- [ ] 返回 `reference` 字段
- [ ] 内容包含块级标签、行内标签、属性说明和写入示例

---

### 1.2 写入工具

#### UC-W01：替换段落内容

**场景**：修改某段文字。

**Prompt**：`"把第二段改成……"`

**调用**：
```
edit_block({ note_id: "<id>", op: "replace", block_id: "<paragraph_id>", content: "<p>新的段落内容</p>" })
```

**验证**：
- [ ] 返回 `ok: true`
- [ ] 再次 `read_blocks` 确认内容已更新
- [ ] block ID 可能已变化

**边界**：
- 替换 `heading` block——内容变更，标题级别不变
- 替换 `embed` block——返回错误（只读）
- 内容含多个块级 XML 标签——block 可能拆分为多个

---

#### UC-W02：替换整个表格

**场景**：更新表格数据。

**Prompt**：`"把进度表更新一下"`

**调用**：
```
edit_block({
  note_id: "<id>",
  op: "replace",
  block_id: "<table_id>",
  content: "<table><tr><td><p>项目</p></td><td><p>进度</p></td></tr><tr><td><p>A</p></td><td><p>100%</p></td></tr><tr><td><p>B</p></td><td><p>80%</p></td></tr></table>"
})
```

**验证**：
- [ ] 表格整体替换成功
- [ ] 行数和列数符合新内容

**边界**：
- 尝试只替换单个单元格——不支持，必须整表

---

#### UC-W03：插入新内容

**场景**：在某段之后添加新段落。

**Prompt**：`"在引言后面加一段背景说明"`

**调用**：
```
edit_block({
  note_id: "<id>",
  op: "insert",
  anchor_id: "<intro_block_id>",
  position: "after",
  content: "<h2>背景</h2><p>本项目始于 2024 年第三季度...</p>"
})
```

**验证**：
- [ ] 返回 `new_block_ids` 数组
- [ ] 返回 `last_block_id`，可直接用于链式插入
- [ ] 新 block 位于锚点之后
- [ ] 标题层级正确

**边界**：
- `position: "before"`——插入到锚点前面
- 插入多段内容（含多个 block）——产生多个新 block ID
- 在文档末尾 block 后插入——正常追加
- content 可包含多个块级元素（如 `"<h2>...</h2><p>...</p>"`），按 XML 顺序插入，无需分多次调用

---

#### UC-W04：删除 block

**场景**：删除多余的段落。

**Prompt**：`"把那段过时的内容删掉"`

**调用**：
```
edit_block({ note_id: "<id>", op: "delete", block_ids: ["<block_id>"] })
```

**验证**：
- [ ] 返回 `deleted_ids` 包含已删除的 ID
- [ ] 大纲中不再包含该 block

**边界**：
- 删除所有 block——文档保留至少一个空 `paragraph`

---

#### UC-W05：修改 block 属性

**场景**：调整标题级别或段落对齐。

**Prompt**：`"把这个二级标题改成三级标题"`

**调用**：
```
edit_block({ note_id: "<id>", op: "update_attrs", block_id: "<heading_id>", attrs: { level: 3 } })
```

**验证**：
- [ ] 标题级别变为 3
- [ ] 标题文本内容不变

**更多属性**：
```
// 段落居中
edit_block({ ..., op: "update_attrs", attrs: { textAlign: "center" } })

// 代码块语言
edit_block({ ..., op: "update_attrs", attrs: { language: "python" } })

// 待办事项勾选
edit_block({ ..., op: "update_attrs", attrs: { checked: true } })
```

---

#### UC-W06：AI 生成图片并插入

**场景**：为笔记生成一张配图。

**Prompt**：`"帮我生成一张系统架构图，插到这段描述后面"`

**调用**：
```
1. generate_image({ prompt: "系统架构图，展示前端、API网关和微服务集群的关系，简洁线条风格" })
   → { image_url: "https://...", task_id: "t_abc", width: 2688, height: 1536 }
2. insert_image({ note_id: "<id>", anchor_id: "<paragraph_id>", position: "after", src: "<image_url>", alt: "系统架构图" })
   → { block_id: "new_img_id", dimensions: { width, height } }
```

**验证**：
- [ ] `generate_image` 返回有效的 `image_url`
- [ ] `insert_image` 成功插入图片
- [ ] 图片出现在指定位置

**边界**：
- 速率限制——每分钟 1 次，超限返回 `RATE_LIMITED`
- 内容违规——返回 `GENERATE_IMAGE_FAILED`
- Prompt 超 500 字符——返回 `GENERATE_IMAGE_FAILED`

---

#### UC-W07：插入已有图片

**场景**：在笔记中某段文字后面插入一张图片。

**Prompt**：`"在这段描述后面加一张架构图"`

**调用**：
```
insert_image({
  note_id: "<id>",
  anchor_id: "<paragraph_id>",
  position: "after",
  src: "https://example.com/architecture.png",
  alt: "系统架构图"
})
```

**验证**：
- [ ] 返回 `ok: true`
- [ ] `data.block_id` 包含新插入的 block ID
- [ ] `data.dimensions` 包含图片尺寸
- [ ] 再次 `read_blocks` 确认图片 block 存在

**边界**：
- `src` 为 base64 data URI——正常插入
- `src` 为本地文件路径——当前不支持直接传入，需先转为 base64 data URI
- 通过 XML（`<img/>`）创建图片——被拒绝，必须使用 `insert_image`

---

#### UC-W08：原子化批量编辑

**场景**：同时执行多个编辑操作。

**Prompt**：`"删掉旧章节，更新摘要，加个新段落"`

**调用**：
```
batch_edit({
  note_id: "<id>",
  operations: [
    { op: "delete", block_ids: ["<old_section_id>"] },
    { op: "replace", block_id: "<summary_id>", content: "<p>更新后的摘要</p>" },
    { op: "insert", anchor_id: "<last_id>", position: "after", content: "<p>新增段落内容</p>" }
  ]
})
```

**验证**：
- [ ] 所有操作在同一个事务中完成
- [ ] 执行顺序为 delete → replace → update_attrs → insert
- [ ] 任一操作失败则全部回滚

**边界**：
- 空 `operations` 数组——返回成功（无操作）
- 单种操作类型——等价于调用对应的单工具
- 操作引用已被 delete 删掉的 block ID——replace/update_attrs 该条失败

---

### 1.3 管理工具

#### UC-M01：列出笔记

**Prompt**：`"看看我最近的笔记"`

**调用**：
```
list_notes({ sort: "update_time", direction: "desc", limit: 10 })
```

**验证**：
- [ ] 返回按更新时间倒序排列的笔记列表
- [ ] `meta.has_more` 正确反映是否还有更多

**边界**：
- 无参数——默认分页返回
- `page: 2, page_size: 5`——第二页
- `since` / `before` 时间过滤——结果在范围内

---

#### UC-M02：创建空白笔记

**Prompt**：`"帮我新建一篇笔记叫'周报模板'"`

**调用**：
```
create_note({ title: "周报模板" })
```

**验证**：
- [ ] 返回 `fileId` 和 `title`
- [ ] 笔记为空白（仅含一个空 `paragraph`）

**边界**：
- 无 `title`——默认"Untitled"
- 重复标题——允许创建（不同 `note_id`）

---

#### UC-M03：全文搜索笔记

**Prompt**：`"搜一下所有提到'季度目标'的笔记"`

**调用**：
```
search_notes({ keyword: "季度目标" })
```

**验证**：
- [ ] 返回匹配的笔记列表
- [ ] 每条包含 `note_id` 和 `title`

**边界**：
- 组合筛选 `tags + since + keyword`
- 无结果——空数组，`ok: true`

---

#### UC-M04：标签操作

**Prompt**：`"看看我有哪些标签" / "找标签里带'项目'的"`

**调用**：
```
find_tags()
→ [{ id: "tag_001", name: "工作" }, { id: "tag_002", name: "草稿" }, { id: "tag_003", name: "已发布" }]

find_tags({ keyword: "项目" })
→ [{ id: "tag_010", name: "项目管理" }]

search_notes({ tags: ["项目管理"], sort: "update_time", direction: "desc" })
→ { notes: [{ note_id: "nr_d1", title: "项目方案 v2" }], meta: { total: 1, has_more: false } }

get_note_info({ note_id: "nr_d1" })
→ { notes: [{ note_id: "nr_d1", title: "项目方案 v2",
    tags: [{ id: "tag_010", name: "项目管理" }] }] }
```

**关键模式**：使用 `find_tags` → `search_notes({ tags })` 按标签浏览。标签是笔记的属性，通过 `get_note_info` 查看详情，通过 `search_notes({ tags })` 按标签筛选笔记。

**验证**：
- [ ] `find_tags` 返回所有标签
- [ ] `find_tags({ keyword })` 结果与关键词相关
- [ ] `search_notes({ tags })` 返回该标签下的笔记

---

#### UC-M05：获取当前光标位置

**Prompt**：`"告诉我当前正在编辑的位置"`

**调用**：
```
get_cursor_block()
```

**验证**：
- [ ] 返回当前笔记 `note_id`
- [ ] 返回当前 block 的 `block_id`
- [ ] 返回当前 block 的 `block_type`

**边界**：
- 光标位于高亮块/分栏内部——返回不支持错误

---

#### UC-M06：删除笔记（高危）

**Prompt**：`"删掉那篇过期的草稿"`

**调用**：
```
// 必须先与用户确认！
delete_note({ note_id: "<id>" })
```

**验证**：
- [ ] 返回成功
- [ ] 再次 `get_note_info` 该 ID——应失败或返回空

**边界**：
- 批量删除 `note_ids: ["id1", "id2"]`——最多 100 个

---

#### UC-M07：同步与诊断

**Prompt**：`"同步一下这篇笔记" / "看看最近的调用日志"`

**调用**：
```
sync_note({ note_id: "<id>" })
get_note_stats({ detailed: true })
get_mcp_logs({ limit: 20 })
```

**验证**：
- [ ] `sync_note` 返回同步状态
- [ ] `get_note_stats` 包含总笔记数、标签数
- [ ] `get_mcp_logs` 返回最近的工具调用记录

---

## L2 组合工作流

2-4 个工具串联完成一个任务。适用于 Agent 编排和用户场景展示。

---

### UC-C01：搜索定位 → 读取理解

**场景**：用户记得关键词但不记得笔记名。

**Prompt**：`"我之前写过一篇关于技术选型的笔记，帮我找出来，看看第一章写了什么"`

**工具链**：
```
1. search_notes({ keyword: "技术选型" })
   → { notes: [{ note_id: "nr_a1b2c3", title: "技术选型方案" }] }
2. get_note_outline({ note_id: "nr_a1b2c3" })
   → { blocks: [
       { id: "h1_intro", type: "heading", preview: "前言", attrs: { level: 1 } },
       { id: "h1_arch",  type: "heading", preview: "架构设计", attrs: { level: 1 } },
       { id: "h1_plan",  type: "heading", preview: "实施计划", attrs: { level: 1 } }
     ] }
3. read_section({ note_id: "nr_a1b2c3", heading_block_id: "h1_intro", max_blocks: 20 })
   → { content: "<h1>前言</h1><p>本方案涵盖...</p>" }
```

**关键模式**：先用 `get_note_outline` 了解结构，再用 `read_section` 按需加载章节，避免一次性加载全文。

**验证**：
- [ ] 能从关键词定位到目标笔记
- [ ] 大纲正确反映文档结构
- [ ] 章节内容完整返回

---

### UC-C02：读取 → 编辑 → 验证

**场景**：确认内容后再修改，修改后验证结果。

**Prompt**：`"把项目状态从'进行中'改成'已完成'"`

**工具链**：
```
1. search_note_content({ note_id, query: "进行中" })
   → 定位目标 block
2. read_blocks({ note_id, block_ids: [target_id] })
   → 确认当前内容
3. edit_block({ note_id, op: "replace", block_id: target_id, content: "<p>更新后的内容</p>" })
   → 执行修改（返回 hints 提示刷新 outline）
4. get_note_outline({ note_id })
   → 获取新的 block_id
5. read_blocks({ note_id, block_ids: [new_block_id] })
   → 验证修改结果（注意 block_id 可能已变化）
```

**验证**：
- [ ] 搜索正确定位
- [ ] 替换后内容正确
- [ ] 验证步骤使用新的 block_id

---

### UC-C03：创建 → 填充模板

**场景**：按模板创建新笔记并填入结构化内容。

**Prompt**：`"帮我新建一篇周报，按照固定模板填好框架"`

**工具链**：
```
1. create_note({ title: "2025-03-03 周报" })
   → { fileId: "nr_new1", title: "2025-03-03 周报" }
2. get_note_outline({ note_id: "nr_new1" })
   → { blocks: [{ id: "p_empty", type: "paragraph", preview: "" }] }
3. batch_edit({ note_id: "nr_new1", operations: [
     { op: "replace", block_id: "p_empty", content: "<h1>2025-03-03 周报</h1>" },
     { op: "insert", anchor_id: "p_empty", position: "after",
       content: "<h2>本周完成</h2><p listType=\"bullet\" listLevel=\"0\"> </p><h2>进行中</h2><p listType=\"bullet\" listLevel=\"0\"> </p><h2>下周计划</h2><p listType=\"bullet\" listLevel=\"0\"> </p><h2>风险与阻塞</h2><p listType=\"bullet\" listLevel=\"0\"> </p>" }
   ]})
   → { success: true }
```

**关键模式**：`create_note` 创建空白笔记。使用 `batch_edit` 的 replace + insert 组合在一次原子操作中填充内容。单次 insert 的 content 可包含多个块级元素（如上例的 4 个 `<h2>` + `<p>` 对），按 XML 顺序依次插入，无需分多次调用。

**验证**：
- [ ] 新笔记创建成功
- [ ] 模板结构完整（4 个二级标题）
- [ ] 每个章节含占位内容

---

### UC-C04：笔记内批量搜索替换

**场景**：将文档中的某个术语统一更名。

**Prompt**：`"把笔记里所有的'旧系统'改成'新平台'"`

**工具链**：
```
1. search_note_content({ note_id: "nr_proj1", query: "旧系统" })
   → [
       { block_id: "p_ref1", type: "paragraph", preview: "...交由旧系统团队..." },
       { block_id: "t_row1", type: "table", preview: "旧系统 | 进行中 | 75%" }
     ]
2. read_blocks({ note_id: "nr_proj1", block_ids: ["p_ref1", "t_row1"] })
   → [
       { id: "p_ref1", content: "<p>该任务交由<strong>旧系统</strong>团队执行。</p>" },
       { id: "t_row1", content: "<table><tr><td><p>项目</p></td><td><p>状态</p></td></tr><tr><td><p>旧系统</p></td><td><p>进行中</p></td></tr></table>" }
     ]
3. batch_edit({ note_id: "nr_proj1", operations: [
     { op: "replace", block_id: "p_ref1",
       content: "<p>该任务交由<strong>新平台</strong>团队执行。</p>" },
     { op: "replace", block_id: "t_row1",
       content: "<table><tr><td><p>项目</p></td><td><p>状态</p></td></tr><tr><td><p>新平台</p></td><td><p>进行中</p></td></tr></table>" }
   ]})
   → { success: true }
```

**关键模式**：搜索 → 读取完整内容 → 批量替换。表格需替换整个 XML 表格。

**验证**：
- [ ] 所有出现位置都被替换
- [ ] 表格中的出现也被处理（整表替换）
- [ ] 不影响未匹配的 block

---

### UC-C05：文档结构重组

**场景**：调整章节顺序或标题层级。

**Prompt**：`"把'总结'章节移到'引言'前面，并降为二级标题"`

**工具链**：
```
1. get_note_outline({ note_id: "nr_doc1" })
   → { blocks: [
       { id: "h_intro",   type: "heading", preview: "引言", attrs: { level: 1 } },
       { id: "h_detail",  type: "heading", preview: "详细内容", attrs: { level: 1 } },
       { id: "h_summary", type: "heading", preview: "执行摘要", attrs: { level: 1 } },
       { id: "p_summ1",   type: "paragraph", preview: "核心发现..." }
     ] }
2. read_section({ note_id: "nr_doc1", heading_block_id: "h_summary" })
   → { content: "<h1>执行摘要</h1><p>核心发现包括...</p>" }
3. batch_edit({ note_id: "nr_doc1", operations: [
     { op: "delete", block_ids: ["h_summary", "p_summ1"] },
     { op: "insert", anchor_id: "h_intro", position: "before",
       content: "<h1>执行摘要</h1><p>核心发现包括...</p>" }
   ]})
   → { success: true }
```

**关键模式**：`batch_edit` 确保删除和插入作为原子操作执行。注意执行顺序固定为 delete → insert。

**验证**：
- [ ] 章节出现在新位置
- [ ] 标题级别已调整
- [ ] 原位置不再包含该章节

---

### UC-C06：标签筛选浏览

**场景**：按标签找到一组笔记并快速浏览。

**Prompt**：`"看看'产品需求'标签下有哪些笔记，每篇的大纲列一下"`

**工具链**：
```
1. search_notes({ tags: ["产品需求"] })
   → 获取笔记列表
2. 对每篇笔记:
   get_note_outline({ note_id })
   → 获取大纲
```

**验证**：
- [ ] 标签下笔记列表正确
- [ ] 每篇笔记的大纲可正常获取

---

### UC-C07：上下文感知编辑

**场景**：修改某段内容前先看看前后文，确保连贯。

**Prompt**：`"找到提到'预算超支'的段落，看看上下文，帮我改一下措辞"`

**工具链**：
```
1. search_note_content({ note_id, query: "预算超支" })
   → 定位 block
2. read_blocks({ note_id, block_id: target_id, before: 2, after: 2 })
   → 读取上下文
3. edit_block({ note_id, op: "replace", block_id: target_id, content: "<p>改善后的表述...</p>" })
   → 修改内容
```

**验证**：
- [ ] 上下文帮助 Agent 理解语境
- [ ] 修改后的内容与上下文连贯

---

### UC-C08：批量调整标题层级

**场景**：文档标题层级混乱，需要统一规范。

**Prompt**：`"把所有三级标题升为二级"`

**工具链**：
```
1. get_note_outline({ note_id })
   → 筛选 type=heading, attrs.level=3 的 block
2. batch_edit({ note_id, operations: [
     { op: "update_attrs", block_id: "h1", attrs: { level: 2 } },
     { op: "update_attrs", block_id: "h2", attrs: { level: 2 } },
     ...
   ]})
   → 批量修改属性
```

**验证**：
- [ ] 所有原三级标题变为二级
- [ ] 标题内容不变
- [ ] 其他级别标题不受影响

---

## L3 端到端场景

完整用户意图 → Prompt → 工具调用链 → 验证标准。适用于产品演示、测试验收和用户教育。

---

### UC-E01：会议记录整理

**用户角色**：项目经理

**场景**：会议结束后，根据粗略笔记整理出规范的会议纪要。

**Prompt**：
```
帮我整理一下今天的产品评审会议记录。标题改为"产品评审会 2025-03-03"，
补充会议结论和行动项，每个行动项标注负责人和截止日期。
```

**完整调用链**：
```
1. search_notes({ keyword: "产品评审" })
   → 定位笔记

2. get_note_outline({ note_id })
   → 理解当前结构

3. read_note({ note_id })
   → 读取完整内容

4. batch_edit({ note_id, operations: [
     // 更新标题
     { op: "replace", block_id: title_id,
       content: "<h1>产品评审会 2025-03-03</h1>" },
     // 在末尾追加结论和行动项
     { op: "insert", anchor_id: last_block_id, position: "after",
       content: "<h2>会议结论</h2><p listType=\"ordered\" listLevel=\"0\" listId=\"c1\">功能 A 方案通过...</p><h2>行动项</h2><p listType=\"todo\" listLevel=\"0\" checked=\"0\">张三：完成原型设计（截止 3/7）</p><p listType=\"todo\" listLevel=\"0\" checked=\"0\">李四：输出技术方案（截止 3/10）</p>" }
   ]})

5. read_note({ note_id })
   → 验证最终结果
```

**验证标准**：
- [ ] 标题已更新
- [ ] 原有讨论记录保留
- [ ] 新增结论和行动项章节
- [ ] 行动项格式为 todo list，含负责人和日期

---

### UC-E02：长文档摘要生成

**用户角色**：知识工作者

**场景**：一篇 2 万字的年度报告，需要生成 300 字摘要插入到文档开头。

**Prompt**：
```
帮我总结这篇年度报告的要点，生成 300 字左右的执行摘要，插到文档开头。
```

**完整调用链**：
```
1. get_note_outline({ note_id })
   → 获取结构，识别各章节标题

2. 对每个一级标题:
   read_section({ note_id, heading_block_id })
   → 逐章读取（避免全文加载）

3. Agent 生成 300 字摘要

4. edit_block({
     note_id,
     op: "insert",
     anchor_id: first_heading_id,
     position: "before",
     content: "<h2>执行摘要</h2><p>[生成的摘要内容]</p>"
   })

5. read_blocks({ note_id, block_id: new_summary_id, after: 3 })
   → 验证摘要位置和格式
```

**验证标准**：
- [ ] 摘要插入到文档最前面
- [ ] 未加载全文（使用 `read_section` 分段读取）
- [ ] 摘要内容涵盖各章核心观点
- [ ] 原文内容无损

---

### UC-E03：文档翻译

**用户角色**：内容创作者

**场景**：将一篇中文笔记的正文逐段翻译为英文。

**Prompt**：
```
帮我把这篇笔记翻译成英文，逐段替换。
```

**完整调用链**：
```
1. get_note_outline({ note_id })
   → 获取所有 block ID 和类型

2. read_note({ note_id })
   → 读取全文内容（短文档）

3. batch_edit({ note_id, operations: [
     // 对每个非 embed 的 block 做翻译替换
     { op: "replace", block_id: "heading_1", content: "<h1>Translated Title</h1>" },
     { op: "replace", block_id: "para_1", content: "<p>Translated paragraph...</p>" },
     { op: "replace", block_id: "table_1", content: "<table><tr><td><p>Col1</p></td><td><p>Col2</p></td></tr><tr><td><p>val1</p></td><td><p>val2</p></td></tr></table>" },
     // embed block 跳过
   ]})

4. read_note({ note_id })
   → 验证翻译结果
```

**验证标准**：
- [ ] 所有非 embed block 已翻译
- [ ] embed block 保持不变
- [ ] 表格结构保留
- [ ] XML 格式正确（行内 mark 如 `<strong>`、`<a>` 等保留）

---

### UC-E04：项目周报聚合

**用户角色**：项目经理

**场景**：从多篇日常笔记中提取本周进展，汇总到一篇新的周报。

**Prompt**：
```
帮我从本周的工作笔记中提取进展，汇总成一篇周报。
```

**完整调用链**：
```
1. search_notes({
     tags: ["工作日志"],
     since: "2025-02-24T00:00:00Z",
     before: "2025-03-01T00:00:00Z"
   })
   → 获取本周所有工作日志

2. 对每篇笔记:
   get_note_outline({ note_id }) → 了解结构
   read_section({ note_id, heading_block_id }) → 读取关键章节

3. create_note({ title: "周报 2025-W09" })
   → 创建周报笔记

4. get_note_outline({ note_id: new_note_id })
   → 获取空 block ID

5. batch_edit({ note_id: new_note_id, operations: [
     { op: "replace", block_id: empty_id, content: "<h1>周报 2025-W09</h1>" },
     { op: "insert", anchor_id: empty_id, position: "after",
       content: "<h2>本周完成</h2><p>[从各笔记聚合的进展]</p><h2>关键成果</h2><p>[提炼的成果]</p><h2>下周计划</h2><p>[汇总的计划]</p>" }
   ]})

6. sync_note({ note_id: new_note_id })
   → 同步到云端
```

**验证标准**：
- [ ] 周报笔记已创建
- [ ] 内容来源于多篇日志的聚合
- [ ] 结构化为完成/成果/计划三部分
- [ ] 已同步

---

### UC-E05：待办事项管理

**用户角色**：个人用户

**场景**：查找笔记中所有未完成的待办事项，标记已完成的，汇总未完成的。

**Prompt**：
```
帮我检查一下这篇笔记里的待办事项，把已经做完的勾上，列出还没完成的。
```

**完整调用链**：
```
1. get_note_outline({ note_id })
   → 识别所有 list 类型的 block

2. read_blocks({ note_id, block_ids: [list_block_ids] })
   → 读取完整 todo 内容

3. 与用户确认哪些已完成

4. batch_edit({ note_id, operations: [
     { op: "update_attrs", block_id: "todo_1", attrs: { checked: true } },
     { op: "update_attrs", block_id: "todo_3", attrs: { checked: true } },
   ]})
   → 批量勾选

5. read_blocks({ note_id, block_ids: [remaining_todo_ids] })
   → 返回未完成列表
```

**验证标准**：
- [ ] 已完成项正确勾选
- [ ] 未完成项清单准确
- [ ] 其他内容未被修改

---

### UC-E06：长文拆分为系列文章

**用户角色**：内容创作者

**场景**：一篇超长文章需要拆分为多篇独立笔记。

**Prompt**：
```
这篇文章太长了，帮我按一级标题拆分成独立的笔记，每篇保留原标题。
```

**完整调用链**：
```
1. get_note_outline({ note_id, max_depth: 1 })
   → 获取所有一级标题

2. 对每个一级标题:
   a. read_section({ note_id, heading_block_id })
      → 读取该章节完整内容
   b. create_note({ title: "章节标题" })
      → 创建新笔记
   c. get_note_outline({ note_id: new_id })
      → 获取空 block
   d. batch_edit({ note_id: new_id, operations: [
        { op: "replace", block_id: empty_id, content: "<h1>章节标题</h1>" },
        { op: "insert", anchor_id: empty_id, position: "after",
          content: "<p>章节完整内容...</p>" }
      ]})

3. get_note_stats()
   → 确认新增了预期数量的笔记
```

**验证标准**：
- [ ] 每个一级章节对应一篇新笔记
- [ ] 新笔记内容完整（含子标题和正文）
- [ ] 原笔记未被修改

---

### UC-E07：清理过期草稿

**用户角色**：知识管理者

**场景**：清理 3 个月前标记为"草稿"且未更新的笔记。

**Prompt**：
```
帮我找出 3 个月没更新的草稿笔记，列出来让我确认后删掉。
```

**完整调用链**：
```
1. search_notes({ tags: ["草稿"] })
   → 获取所有草稿笔记

2. 对每篇笔记:
   get_note_info({ note_id })
   → 检查 update_time

3. 筛选出 update_time < 3个月前 的笔记

4. 展示列表给用户确认

5. 用户确认后:
   delete_note({ note_ids: [confirmed_ids] })
   → 批量删除（需明确二次确认！）
```

**验证标准**：
- [ ] 仅展示超过 3 个月未更新的草稿
- [ ] 用户确认前不执行删除
- [ ] 删除操作不可恢复——已明确提醒
- [ ] 删除后笔记不再出现在列表中

---

### UC-E08：文档格式规范化

**用户角色**：团队 leader

**场景**：一篇格式混乱的文档，需要统一标题层级、修正对齐、补充代码块语言标识。

**Prompt**：
```
帮我规范化这篇文档的格式：标题层级从 H1 开始递增，代码块标注语言，段落左对齐。
```

**完整调用链**：
```
1. get_note_outline({ note_id })
   → 分析当前标题层级分布

2. read_note({ note_id })
   → 识别代码块、段落的格式问题

3. batch_edit({ note_id, operations: [
     // 修正标题层级
     { op: "update_attrs", block_id: "h1", attrs: { level: 1 } },
     { op: "update_attrs", block_id: "h2", attrs: { level: 2 } },
     // 补充代码块语言
     { op: "update_attrs", block_id: "code1", attrs: { language: "javascript" } },
     { op: "update_attrs", block_id: "code2", attrs: { language: "python" } },
     // 修正段落对齐
     { op: "update_attrs", block_id: "p1", attrs: { textAlign: "left" } },
   ]})

4. get_note_outline({ note_id })
   → 验证标题层级已规范
```

**验证标准**：
- [ ] 标题层级从 H1 开始连续递增
- [ ] 代码块均标注了语言
- [ ] 段落对齐统一为左对齐
- [ ] 文本内容未变化
