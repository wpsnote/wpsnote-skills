---
name: ie-recall-memory
author: Loki Mao (赛博小熊猫 Loki)
description: “Selectively recalls the most relevant prior WPS notes for a current writing task, study session, or research thread. Use when the user is drafting new content, preparing a presentation, doing topic review, or organizing research and wants to surface past notes worth re-reading — focuses on 'what should I remember right now' rather than full cross-note mapping.”
---

# WPS Insight Recaller 2.0

Selectively recall the most valuable prior WPS notes for the user's current task. This is not a general search — it answers “what past notes are worth re-reading right now?”

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Current note or task | Yes | The WPS note, writing task, or study topic being worked on |
| Candidate old notes | Yes | Prior WPS notes that may be relevant |
| Time range or context | No | Optional scope filter (e.g. “this semester”, “project X”) |

## Workflow

1. **Read the current note** — identify the core topic, open questions, and what the user is trying to accomplish
2. **Search prior notes** — use `wpsnote-cli find` or `search_notes` to locate candidates by topic, tags, or keywords
3. **Rank by immediate usefulness** — prioritize notes the user can act on now, not just topically similar ones
4. **Extract reusable content** — identify specific paragraphs, examples, or frameworks worth pulling forward
5. **Write the recall report** — output the structured result directly into WPS or present to user

## Output Structure

Produce a structured WPS-ready recall report with these sections:

1. **Most useful prior notes now** — ranked list of 3–5 notes, each with its WPS title
2. **Why each is worth recalling** — one sentence per note explaining current relevance
3. **How it connects to the current task** — map each recalled note to a specific part of the current work
4. **What can be reused directly** — exact paragraphs, frameworks, or examples to pull forward
5. **Where to insert or link it** — suggest placement in the current note

### Example output snippet

```markdown
## 召回结果

### 1. 《分布式系统一致性笔记》
- **为什么现在有用**：当前写的 CAP 定理分析直接依赖这篇的 Paxos 对比
- **可直接复用**：第三节的”三种一致性模型对比表”可整段引入
- **建议插入位置**：当前笔记”理论背景”章节之后
- **置信度**：Confirmed from notes
```

## WPS-first rules

- Always include the exact WPS note title so the user can find it directly
- If the original paragraph is not accessible, provide a faithful summary — never disguise inference as an exact quote
- Keep recall count small (3–5 notes max) — prioritize quality over quantity
- Use the confidence labels from the shared workflow: `Confirmed from notes`, `Likely inference`, `Still missing`

## Quality rules

- Prioritize notes the user can act on immediately over notes that are merely topically similar
- Balance across content types — mix theory, comparisons, and examples rather than recalling only one kind
- Clearly separate “reuse directly now” from “worth expanding on later”
- Each recalled note must have a specific connection to the current task — no generic “related to your topic” entries

## Do not use when

- The goal is to build explicit bi-directional note links or a relationship graph → use `study-note-linker`
- The user wants a broad literature review, not selective recall
- There are not enough meaningful prior notes to recall from

## Recommended next skill

- `study-note-linker` — to formalize the connections discovered here into a knowledge network
- `class-note-builder` — to restructure recalled content into a coherent study note
