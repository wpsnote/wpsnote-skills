# web-importer 状态定义

本说明只描述 Codex 侧的 outcome-only 三态验收，不约束笔记 Agent 在内部如何调度工具。

## original_state

- 目标标题对应的笔记不存在，或同标题匹配数为 `0`
- 控制笔记完整快照已采集，用于检查是否发生无关污染
- 对降级 case，不要求记录中间过程；只要求在执行前确认尚未生成目标笔记

## expected_state

- 新增一篇网页导入笔记
- 标题与来源链接与网页一致
- 标题层级、关键段落、引用块、图片数量满足 case 约束
- 控制笔记保持不变
- 同标题匹配数为 `1`，避免重复创建
- 如果是降级导入，最终回答必须明确说明：
  - 保留了什么
  - 缺失了什么
  - 当前结果是降级导入

## final_state

- 使用与 `original_state` 同一类 collector 重新读取最终结果：
  - 导入笔记快照
  - 同标题匹配数
  - 控制笔记快照
  - 降级 case 的最终回答
- 只判断 `final_state` 相对 `original_state` 是否满足 `expected_state`
- 不判断内部调用链，不区分 Agent 走的是哪条工具路径

## 推荐 collectors

- `search_note_by_title`
- `search_note_by_title_count`
- `note_snapshot`
- `response_payload`

## 结果重点

- 是否创建了正确标题的笔记
- 是否保留了关键结构和图片
- 是否保留了来源链接
- 是否避免污染无关笔记
- 是否在降级场景下清楚说明限制

## 额外建议

- 如果后续要补幂等性/去重回归，可以继续沿用“同标题匹配数应为 1”这一条断言
