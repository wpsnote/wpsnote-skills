# WPS Note Cloud — 用例手册

覆盖云端 MCP 与云端 `wpsnote-cli` 的常见单步操作与端到端组合工作流。

## L1 基础读取与搜索

### UC-01：按时间浏览或按标题筛选笔记

**MCP**：
```json
// 最近更新的 20 篇笔记
list_notes({ "order_by": "update_time", "order_direction": "DESC", "limit": 20 })

// 筛选星标且包含待办的笔记
list_notes({ "starred": true, "has_todo": true, "limit": 20 })

// 按创建时间范围与标题关键词筛选
list_notes({ "keyword": "周报", "start_date": "2026-11-01", "end_date": "2026-11-16", "limit": 20 })
```

**CLI**：
```bash
wpsnote-cli list --limit 20 --order_by update_time --order_direction DESC
wpsnote-cli list --starred true --has_todo true
```

---

### UC-02：全文搜索与单篇精确定位

**MCP**：
```json
// 全局搜索同时包含「Q4」和「预算」的段落
search_notes({ "keywords": ["Q4", "预算"], "mode": "all", "search_type": "text", "limit": 20 })

// 在已知 note_id 内搜索匹配块
search_note_content({ "note_id": "<id>", "keywords": ["预算"] })

// 读取匹配块及前后上下文
read_blocks({ "note_id": "<id>", "block_id": "<match_block_id>", "before": 2, "after": 2 })
```

**CLI**：
```bash
wpsnote-cli find --keywords '["Q4","预算"]' --mode all
wpsnote-cli search --note_id <id> --keywords '["预算"]'
wpsnote-cli read-blocks --note_id <id> --block_id <match_block_id> --before 2 --after 2
```

---

### UC-03：大文档按章节与分页读取

```json
// 1. 轻量查看大纲与规模
get_note_outline({ "note_id": "<id>", "include_preview": false })
// 若 blocks > 200 返回 pagination.has_more=true，使用 pagination.next_offset 续读

// 2. 按 heading_block_id 读取目标章节
read_section({ "note_id": "<id>", "heading_block_id": "<h_id>", "max_blocks": 50 })
// 若 truncated=true，传 block_offset: pagination.next_offset 续读
```

---

## L2 笔记创建、编辑与图片/语音处理

### UC-04：创建笔记 → 打标签 → 写入结构化正文

```json
// 1. 创建空白笔记（不返回 outline）
create_note({ "title": "项目架构评审 2026-11-16" })
// → { note_id: "<id>", title: "...", link_url: "https://..." }

// 2. 分配文件级标签（不带 #）
manage_note_tags({ "note_id": "<id>", "add": ["工作/架构"] })

// 3. 获取初始空 block_id
get_note_outline({ "note_id": "<id>" })
// → blocks[0].id = "<empty_block_id>"

// 4. 一次性写入完整结构
edit_block({
  "note_id": "<id>",
  "op": "replace",
  "block_id": "<empty_block_id>",
  "content": "<h1>项目架构评审</h1><h2>一、背景</h2><p>核心目标与约束条件。</p><h2>二、待办</h2><p listType=\"todo\" listLevel=\"0\" checked=\"0\">确认接口协议</p>"
})
```

---

### UC-05：连续追加长内容与批量原子修改

**连续追加（链式 `last_block_id`）**：
```json
edit_block({
  "note_id": "<id>",
  "op": "insert",
  "anchor_id": "<last_id>",
  "position": "after",
  "content": "<h2>章节三</h2><p>第一段内容...</p><p>第二段内容...</p>"
})
// → 返回 last_block_id: "<new_last_id>"，下一次 insert 直接复用它作 anchor_id
```

**批量原子修改（`batch_edit`）**：
```json
batch_edit({
  "note_id": "<id>",
  "operations": [
    { "op": "delete", "block_ids": ["<obsolete_id>"] },
    { "op": "replace", "block_id": "<summary_id>", "content": "<p>更新后的摘要</p>" },
    { "op": "update_attrs", "block_id": "<h_id>", "attrs": { "level": 2 } },
    { "op": "move", "block_id": "<img_id>", "anchor_id": "<summary_id>", "position": "after" },
    { "op": "insert", "anchor_id": "<end_id>", "position": "after", "content": "<h2>结论</h2><p>已完成评审。</p>" }
  ]
})
```

---

### UC-06：文生图与插图、读图、语音转写

```json
// 1. AI 文生图 → 插入笔记
generate_image({ "prompt": "扁平矢量风格的系统架构图，蓝白色调，简洁留白" })
// → { image_url: "https://...", task_id: "..." }
insert_image({ "note_id": "<id>", "anchor_id": "<block_id>", "position": "after", "src": "<image_url>", "alt": "架构图" })

// 2. CLI 插入本地图片（自动编码为 data URI，≤ 2 MiB）
// wpsnote-cli insert-image --note_id <id> --anchor_id <block_id> --position after --file ./diagram.png

// 3. 读取笔记内已有图片 / 语音卡片转写
get_note_outline({ "note_id": "<id>" })
read_image({ "note_id": "<id>", "block_id": "<image_block_id>" })
get_audio_transcript({ "shorthand_id": "<audio_attrs_shorthand_id>", "last_seconds": 90 })
```

---

## L3 标签体系与回收站管理

### UC-07：按标签浏览与整理标签

```json
// 1. 列出或搜索标签
find_tags({ "keywords": ["项目"] })
// 或分页遍历全量标签：list_tags({ "limit": 100 })

// 2. 查询某标签下的笔记（优先传 tag_id 或完整 path）
get_notes_by_tag({ "tag_id": "<tag_id_or_path>", "limit": 50 })

// 3. 重命名标签（全局生效，无需逐篇改笔记）
rename_tag({ "tag_id": "<tag_id>", "new_name": "归档项目" })

// 4. 批量给多篇笔记打标/去标
manage_note_tags({
  "operations": [
    { "note_id": "<id1>", "add": ["工作/归档项目"], "remove": ["<old_tag_id>"] },
    { "note_id": "<id2>", "add": ["工作/归档项目"] }
  ]
})
```

---

### UC-08：安全删除与回收站恢复

```json
// 1. 移入回收站（可恢复）
trash_note({ "note_id": "<id>" })

// 2. 查看回收站
list_trash({ "limit": 20 })

// 3. 误删恢复
restore_note({ "note_id": "<id>" })

// 4. 彻底永久删除（须经用户明确确认，且笔记必须在回收站中）
permanently_delete_note({ "note_id": "<id>" })
```

CLI 对应操作（`destructive` 工具必须显式 `--yes`）：
```bash
wpsnote-cli trash --note_id <id> --yes
wpsnote-cli trash-list --limit 20
wpsnote-cli restore --note_id <id>
wpsnote-cli purge --note_id <id> --yes
```
