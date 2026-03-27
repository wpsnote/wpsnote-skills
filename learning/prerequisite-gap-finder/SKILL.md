---
name: prerequisite-gap-finder
author: Loki Mao (赛博小熊猫 Loki)
description: “Identifies missing prerequisite knowledge that blocks understanding of a WPS study note or topic. Use when a user feels stuck on a subject, wants to know what foundational concepts they are missing, is doing exam prep or self-study gap analysis, or re-reads old notes and realizes they still do not understand — produces a gap report with repair plan and self-check items.”
---

# WPS Prerequisite Gap Finder 2.0

Diagnose which foundational knowledge gaps are blocking the user's understanding, then provide a concrete repair plan. This goes beyond “you have a gap” — it explains what is missing, why it causes confusion, what to study first, and how to verify the gap is closed.

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Current note or topic | Yes | The WPS study note or subject the user finds difficult |
| Prior notes with basics | Yes | Existing WPS notes that may cover foundational knowledge |
| Course stage or context | No | Exam timeline, difficulty level, or curriculum position |

## Workflow

1. **Read the current note** — identify which concepts the user is trying to learn and where the explanation breaks down
2. **List required prerequisites** — enumerate the foundational concepts needed to understand this topic
3. **Search prior notes** — use `wpsnote-cli find` or `search_notes` to check which prerequisites are already covered in the user's note library
4. **Classify each gap** — assign a severity level to each missing prerequisite (see severity tiers below)
5. **Build repair plan** — for each gap, provide specific study actions with estimated effort
6. **Generate self-check** — create verification questions the user can answer after filling each gap
7. **Write the report** — output directly into WPS or present to user

## Output Structure

Produce a structured WPS-ready gap report with these sections:

1. **Required prerequisites** — complete list of foundational concepts needed
2. **Covered in existing notes** — which prerequisites the user's WPS library already addresses (with note titles)
3. **Missing or weak** — gaps classified by severity tier
4. **Why this blocks understanding** — for each gap, explain the causal link to the current confusion
5. **Repair plan** — ordered study steps with estimated time per step
6. **Self-check after repair** — 2–3 verification questions per gap

### Severity tiers

| Tier | Label | Meaning |
|------|-------|---------|
| 1 | Blocker | Cannot proceed without this — fix first |
| 2 | Important but recoverable | Causes confusion but can work around temporarily |
| 3 | Optional depth | Nice to know, not blocking current understanding |

### Example output snippet

```markdown
## 前置知识缺口报告

### Blocker：线性代数基础
- **缺什么**：矩阵乘法和特征值分解
- **为什么卡**：当前笔记的 PCA 推导直接依赖特征值分解，跳过会导致整段公式无法理解
- **已有笔记**：《线性代数期中复习》覆盖了矩阵乘法，但没有特征值部分
- **修复步骤**：(1) 复习《线性代数期中复习》第三章 ~15 min (2) 补学特征值分解概念 ~30 min (3) 手算一个 2x2 矩阵的特征值 ~10 min
- **自测**：给定矩阵 A = [[2,1],[1,2]]，能否求出特征值？能否解释特征值的几何含义？
```

## WPS-first rules

- If an existing note covers a prerequisite, cite the exact WPS note title so the user can navigate directly
- If no prior note exists for a gap, say so explicitly — do not fabricate references
- Break repair steps into small, actionable tasks with rough time estimates
- Use confidence labels: `Confirmed from notes`, `Likely inference`, `Still missing`

## Quality rules

- Focus on gaps that actually block understanding, not every related background topic
- Each gap explanation must link directly to the current topic — show the user why this specific gap causes their confusion
- Repair plans should be ordered: fix blockers first, then important gaps, then optional depth
- Keep the total gap list manageable (typically 3–7 items) — more signals a topic mismatch, not a gap analysis

## Do not use when

- The user wants to find errors or misconceptions within the current note → use `misconception-finder`
- The topic is already well-understood and only needs review focus extraction → use `lecture-focus-extractor`
- The topic scope is too broad or scattered to form a meaningful prerequisite chain

## Recommended next skill

- `misconception-finder` — to check for understanding errors after filling gaps
- `study-note-linker` — to connect the repaired knowledge to the broader note network
