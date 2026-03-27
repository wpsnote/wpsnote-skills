---
name: misconception-finder
author: Loki Mao (赛博小熊猫 Loki)
description: “Diagnoses understanding errors, concept confusion, logic gaps, and vague claims in a WPS study note. Use when a user wants to self-check a note after class, verify understanding before an exam, prepare to explain a topic to someone else, or suspects they think they understand something but actually do not — produces a diagnostic report with corrections and self-test questions.”
---

# WPS Misconception Finder 2.0

Diagnose understanding errors in a study note — this is a “diagnose + repair” skill, not a language polisher. It finds what the user got wrong, what is confused, and what is too vague to trust, then provides corrective rewrites and self-test questions.

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Study note | Yes | A WPS learning note, explanation draft, or revision note |
| Topic tags | No | Help narrow the domain for more accurate diagnosis |
| Reference material | No | Textbook excerpts, answer keys, or authoritative sources to check against |

## Workflow

1. **Read the note thoroughly** — understand what the user is trying to explain or learn
2. **Identify claims** — extract every factual statement, definition, causal explanation, and logical step
3. **Classify each claim** — assign a confidence level (see tiers below)
4. **Draft corrections** — for each error or confusion, write a replacement that can be pasted directly into the note
5. **Generate self-test questions** — one question per key misconception for immediate verification
6. **Write the diagnostic report** — output into WPS or present to user

## Confidence Tiers

| Tier | Label | Meaning |
|------|-------|---------|
| High | `clearly wrong` | Factual error or logical contradiction — must fix |
| Medium | `likely confused` | Plausible but probably reflects a misunderstanding — should verify |
| Low | `too vague to trust` | Not wrong per se, but so imprecise it could mislead — should sharpen |

## Output Structure

Produce a structured WPS-ready diagnostic report with these sections:

1. **Overall understanding diagnosis** — one paragraph summary of the note's accuracy level
2. **High-confidence errors** — factual mistakes with the original quote, explanation of the error, and corrected version
3. **Possible misunderstandings** — statements that are probably confused, with reasoning for why this is flagged
4. **Missing evidence or examples** — claims that need supporting evidence the note does not provide
5. **Better phrasing for understanding repair** — rewritten sentences that fix the understanding (not just polish the prose)
6. **Mini self-test** — 2–5 questions the user can answer to verify their understanding after corrections

### Example output snippet

```markdown
## 误解诊断

### Clearly wrong
**原句**：「TCP 三次握手的第三步是服务器发送 ACK」
**问题**：第三步是客户端发送 ACK，不是服务器。服务器在第二步发送 SYN-ACK。
**修正**：「TCP 三次握手的第三步是客户端发送 ACK 确认连接建立」
**自测**：画出 TCP 三次握手的完整时序图，标注每一步的发送方和报文类型。

### Likely confused
**原句**：「HTTP 是无状态的，所以每次请求都要重新建立 TCP 连接」
**问题**：HTTP 无状态指不保留请求间的状态信息，但 HTTP/1.1 默认使用持久连接（keep-alive），不需要每次重建 TCP。
**修正**：「HTTP 是无状态的（不保留请求间状态），但 HTTP/1.1 通过持久连接复用 TCP，无需每次重建」
```

## WPS-first rules

- Quote the user's exact words when pointing out errors — show specifically where the problem is
- Corrections must be directly pasteable into the note, not abstract advice
- Attach a self-test question to every key misconception for immediate verification
- Use confidence labels from the shared workflow: `Confirmed from notes`, `Likely inference`, `Still missing`

## Quality rules

- Clearly distinguish between the three confidence tiers — do not mix “clearly wrong” with “possibly confused”
- For low-confidence flags, explain why it is only a possible misunderstanding
- “Better phrasing” repairs understanding, not writing style — the goal is conceptual accuracy
- If the note is substantially correct, say so — do not manufacture errors to fill the report

## Do not use when

- The user only wants to polish writing style or improve prose → not a language editing skill
- The note content is too thin to support meaningful diagnosis
- The user's real need is prerequisite gap analysis → use `prerequisite-gap-finder`

## Recommended next skill

- `notes-to-flashcards` — to convert corrected understanding into active recall cards
- `prerequisite-gap-finder` — if diagnosis reveals foundational knowledge gaps rather than surface errors
