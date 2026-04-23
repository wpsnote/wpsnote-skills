# wpsnote-beautifier 状态定义

`wpsnote-beautifier` 是写入型排版 skill，验收核心是“结构与可读性是否提升、语义是否保持、无关对象是否不受影响”。

## original_state

- 目标笔记完整快照：`body_xml`、`heading_levels`、`highlight_blocks`、`key_paragraphs`、`hash`。
- 同批中的复杂笔记、简单笔记与控制笔记快照（用于污染对照）。
- 响应骨架和统计字段（例如 `beautified_note_count`）。

## expected_state

- 主路径：
  - 目标笔记结构被重排（标题层级、强调块数量、噪声清理）。
  - 关键语义段落必须保留，不允许“美化导致改义”。
  - 仅目标笔记发生变化，无关笔记保持不变。
- 边界路径（短笔记）：
  - 轻量美化，不可过度加结构和样式。
  - 仍需保留核心信息并去除明显噪声。
- 失败/降级路径（锁定或只读）：
  - 目标笔记不得被半写入。
  - 不创建半成品副本。
  - 最终回答需明确说明失败原因并给可执行结构建议。

## final_state

- 用与 `original_state` 相同的 collector 回读全部对象。
- 重点比较：
  - 目标笔记结构变化与语义保持
  - 非目标笔记是否完全未变
  - 降级说明是否充分
- 不评分内部工具调用与顺序，只按 outcome 判定。
