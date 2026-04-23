# wps-deep-search 状态定义

`wps-deep-search` 是只读型查询 skill。评测只看结果，不看工具调度链，也不看中间 trace。

## original_state

- 在 `seed` 完成后、触发 skill 前采集。
- 必须同时记录：
  - 查询语料快照 `notes`
  - 空的响应归一化骨架 `response`
- `notes` 至少包含：
  - 标题
  - 标签集合
  - 关键证据片段
  - 用于对比的稳定摘要或 hash
- 每个 case 至少保留 1 个无关对照对象，用来检查误命中和只读约束。

## expected_state

- `wps-deep-search` 通常不创建也不更新笔记实体。
- `entities_expected_created` 与 `entities_expected_updated` 一般为空。
- 所有 seed 语料都应列入 `entities_expected_unchanged`。
- `required_changes` 只约束最终答案必须体现的结果：
  - 命中的核心笔记集合
  - 至少一组真实证据片段
  - 明确使用的搜索维度
- `forbidden_changes` 重点约束：
  - 无关对照笔记不得误命中
  - 查询语料不得被写坏或被改写
- `response` 是从最终自然语言回答里抽取出的归一化结果，不要求 Agent 直接输出 JSON。

## final_state

- 触发 skill 后，使用与 `original_state` 相同的 collectors 重新采集。
- `notes` 应与 `original_state` 保持一致；任何正文、标签、元数据变化都视为污染。
- `response` 记录从最终回答中抽取出的规范化字段，通常包括：
  - `response.text`
  - `response.hits`
  - `response.evidence`
  - `response.search_dimensions`
  - `response.uncovered_gaps`
- 判分依据是 `original_state -> final_state` 的结果变化是否满足 `expected_state`，不评价内部过程是否优雅。
