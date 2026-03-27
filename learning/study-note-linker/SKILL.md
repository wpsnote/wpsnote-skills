---
name: study-note-linker
author: Loki Mao (赛博小熊猫 Loki)
description: “Connects a current WPS study note to related prior notes by identifying meaningful learning relationships — prerequisite chains, topic extensions, contrasts, and examples. Use when a user wants to link new notes to existing ones instead of leaving them isolated, is building a personal knowledge network, doing revision across related topics, or organizing notes for a course or research project.”
---

# WPS Study Note Linker 2.0

Build meaningful connections between the user's current WPS study note and their existing note library. The goal is not “find similar notes” — it is to establish learning-relevant relationships that form a knowledge network.

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Current note | Yes | The WPS study note being read or organized |
| Historical notes | Yes | Prior WPS notes that may be related |
| Course or project context | No | Optional scope (course name, exam, research project) |

## Workflow

1. **Read the current note** — identify its core concepts, arguments, and open threads
2. **Search prior notes** — use `wpsnote-cli find` or `search_notes` to locate candidates by topic, tags, and shared terminology
3. **Classify relationships** — for each candidate, determine the relationship type (see types below)
4. **Rank by learning value** — prioritize connections that deepen understanding, not just keyword overlap
5. **Draft backlink sentences** — write ready-to-insert link text for the current note
6. **Identify gaps** — note what the current note still lacks that no existing note covers
7. **Write the analysis** — output into WPS or present to user

## Relationship Types

| Type | Meaning | Example |
|------|---------|---------|
| `prerequisite` | Must understand A before B | 线性代数 → PCA 推导 |
| `same-topic-extension` | Deepens or extends the same concept | 基础 CNN → 残差网络 |
| `contrast` | Presents an alternative view or approach | 频率学派 vs 贝叶斯学派 |
| `example` | Provides concrete cases for abstract theory | 排序算法理论 → 快排实现笔记 |
| `revision-companion` | Best reviewed together | 期中复习笔记 ↔ 期末总结 |

## Output Structure

Produce a structured WPS-ready analysis with these sections:

1. **Top related notes** — 3–5 notes ranked by learning value, each with its WPS title
2. **Relation type** — one of the types above for each connection
3. **Why it matters now** — how this connection helps with the user's current study goal
4. **Recommended reading order** — suggested sequence for reviewing the linked notes
5. **Suggested backlink sentence** — a ready-to-paste sentence for the current note
6. **What this note still lacks** — topics or perspectives not covered by any existing note

### Example output snippet

```markdown
## 笔记关联分析

### 1. 《概率论基础笔记》
- **关系类型**：prerequisite
- **为什么现在重要**：当前贝叶斯推断笔记的后验公式直接依赖条件概率，这篇有完整推导
- **建议回看顺序**：先复习条件概率章节（约 10 min），再回到当前笔记
- **建议双链语句**：「本文贝叶斯公式推导的前置知识见 →《概率论基础笔记》第二章·条件概率」

### 2. 《频率学派 vs 贝叶斯学派对比》
- **关系类型**：contrast
- **为什么现在重要**：帮助理解为什么选择贝叶斯方法而非频率方法
- **建议双链语句**：「两种推断范式的对比分析见 →《频率学派 vs 贝叶斯学派对比》」
```

## WPS-first rules

- Always search the user's WPS note library first — never guess connections without checking
- Include the exact WPS note title for every linked note so the user can navigate directly
- Prefer 3 high-value connections over 10 superficial ones
- Use confidence labels: `Confirmed from notes`, `Likely inference`, `Still missing`

## Quality rules

- Rank connections by learning value, not keyword similarity
- Explicitly classify each relationship type — mixed or vague types reduce usefulness
- If no strong connections exist, say so directly rather than forcing weak links
- Backlink sentences should be concrete and insertable, not generic (“see also...”)

## Do not use when

- The user mainly wants to quickly recall a few old notes for immediate reuse → use `ie-recall-memory`
- There are no historical notes to connect to
- The user wants a topic summary, not note-to-note connections

## Recommended next skill

- `ie-recall-memory` — to selectively surface the most useful recalled content for immediate writing
- `prerequisite-gap-finder` — to check for missing foundational knowledge in the linked network
