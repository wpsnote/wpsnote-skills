# Outcome-Only E2E 三态评测

本目录提供仓库级的 outcome-only E2E 评测骨架。

设计原则只有一条：

- 只看最终结果，不看工具调度链、不看 trace、不评估中间推理过程。

## 三态模型

每个 case 都围绕三种状态展开：

- `original_state`: `seed` 完成后、`invoke` 前采集的真实基线状态
- `expected_state`: 理想目标状态，使用可机器判断的约束表达
- `final_state`: Agent 执行结束后的真实观测状态

判分逻辑固定为：

- `actual_delta = final_state - original_state`
- `actual_delta` 必须满足 `expected_state.required_changes`
- `actual_delta` 不能触发 `expected_state.forbidden_changes`
- `expected_state.tolerance_rules` 允许的差异不判失败

## 目录结构

```text
evals/
├── README.md
├── cases/
│   └── golden/
├── fixtures/
├── schemas/
│   ├── normalized_state.schema.json
│   ├── tri_state_case.schema.json
│   └── tri_state_report.schema.json
├── scripts/
│   └── tri_state_eval.py
├── state-guides/
└── tests/
```

## 标准化状态格式

采集器最终需要把远端真实状态规整成统一 JSON，便于跨 skill 对比。推荐顶层字段：

- `notes`: 以别名或稳定 ID 为 key 的笔记快照
- `tags`: 标签树或标签摘要
- `response`: Agent 最终回答的结构化抽取
- `stats`: 统计信息

典型 `note` 快照字段：

- `title`
- `tags`
- `body_xml`
- `key_paragraphs`
- `image_count`
- `quote_count`
- `metadata`
- `hash`

完整约束见 [schemas/normalized_state.schema.json](./schemas/normalized_state.schema.json)。

## MCP 采集约定

这里的 `collectors` 指的是**如何用真实 WPS Note MCP 采样最终状态**，不是过程评分项。

首版建议只围绕这类 MCP 能力实现采集器：

- `create_note` / `update_note_info`
- `list_notes` / `search_notes` / `get_note_info`
- `get_note_outline` / `read_note_content` / `read_section` / `read_blocks`
- `list_tags` / `find_tags` / `get_notes_by_tag`
- `add_note_tags` / `remove_note_tags` / `rename_tag`
- `import_web_page`

推荐的 collector 映射：

- `note_snapshot`
  使用 `get_note_info` + `read_note_content`，必要时补 `read_blocks`
- `tag_tree`
  使用 `list_tags` / `find_tags`
- `title_match_count`
  使用 `list_notes` 或 `search_notes`
- `query_corpus_snapshot`
  使用 `search_notes`、`get_note_info`、`read_note_content`
- `response_payload`
  解析 Agent 最终回答，不依赖 trace

明确不做：

- 不采“调用了哪些工具”
- 不采“工具顺序”
- 不采 Agent 内部 trace
- 不把宿主层工具包装名当成评分依据

## Case 结构

每个 case 固定字段：

- `id`
- `skill`
- `prompt`
- `seed`
- `original_state_collectors`
- `expected_state`
- `final_state_collectors`
- `grader`
- `cleanup`

`expected_state` 固定包含：

- `entities_expected_created`
- `entities_expected_updated`
- `entities_expected_unchanged`
- `required_changes`
- `forbidden_changes`
- `tolerance_rules`

完整 schema 见 [schemas/tri_state_case.schema.json](./schemas/tri_state_case.schema.json)。

## 支持的断言

当前 grader 支持以下 `kind`：

- `path_exists`
- `path_missing`
- `path_changed`
- `path_unchanged`
- `value_equals`
- `value_contains`
- `value_contains_all`
- `value_not_contains`
- `count_equals`
- `count_at_least`
- `count_between`
- `set_equals`
- `regex_matches`

`tolerance_rules` 当前支持：

- `ignore_paths`

这足够覆盖首版 4 个 skill 的 golden cases。需要更细粒度容错时，优先先把状态标准化，再扩展断言类型。

## 使用方式

校验 case：

```bash
python3 evals/scripts/tri_state_eval.py validate evals/cases
```

对单个 case 评分：

```bash
python3 evals/scripts/tri_state_eval.py grade \
  --case evals/cases/golden/doc-importer/create-rich-import.json \
  --original evals/fixtures/doc-importer/create-rich-import.original.json \
  --final evals/fixtures/doc-importer/create-rich-import.final.json
```

输出 Markdown 报告：

```bash
python3 evals/scripts/tri_state_eval.py grade \
  --case evals/cases/golden/wps-deep-search/time-bounded-query.json \
  --original evals/fixtures/wps-deep-search/time-bounded-query.original.json \
  --final evals/fixtures/wps-deep-search/time-bounded-query.final.json \
  --format markdown
```

## 结果分级

- `pass`: 所有必需变化满足，且没有禁改污染
- `assert_fail`: 最终状态可读，但不满足预期
- `run_fail`: Agent 未产出可验收结果，或执行中断
- `bootstrap_fail`: `seed`、快照采集、清理等基础步骤失败

## 约定

- case 里的 `collectors` 是采集协议，而不是过程评分项
- 不要求证明 Agent “调用了哪些工具”
- 不要求证明 Agent “按什么顺序调用”
- 只要求 `final_state` 相对 `original_state` 达到了 `expected_state`
