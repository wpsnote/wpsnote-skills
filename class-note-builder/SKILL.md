---
name: class-note-builder
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户希望把课堂逐字稿、OCR 笔记、截图资料或零散学习内容整理成结构化的 WPS 学习笔记时使用此 Skill。适合课堂记录整理、培训复盘、补课笔记汇总、课程主笔记构建等场景，尤其适合原始材料很乱、但最终需要一篇可复习、可回看、可继续补充的主笔记时。
---

# WPS Class Note Builder 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 课堂逐字稿
- 白板、板书、PPT 或截图的 OCR 文本
- 零散学习笔记或课后补充内容
- 可选的课程名、章节名、日期

## Output

A structured WPS-ready 主学习笔记，包含清晰的知识结构、待澄清问题和下一轮复习任务。

## What this skill should produce

输出的重点不是“整理得更干净”，而是形成一篇真正适合后续复习的课堂主笔记。

建议包含这些部分：

1. `30-second summary`
2. `core concepts`
3. `definitions / formulas / key claims`
4. `teacher emphasis or repeated points`
5. `examples and cases`
6. `easy to confuse`
7. `still unclear`
8. `next review tasks`

## WPS-first rules

- 如果用户已经有目标 WPS 笔记，优先在原笔记基础上补强，而不是另起一篇重复笔记。
- 如果还没有主笔记，再创建一篇标题清晰的课程笔记。
- 段落尽量短，适合在 WPS 里快速扫读。
- 把没讲清、没听懂、证据不足的部分明确标出来，方便后续补记。

## Quality rules

- 去掉口语废话、重复内容和无关闲聊。
- 在不影响理解的前提下，尽量保留老师原本的讲解顺序。
- 不确定的内容要标记出来，不要假装已经确认。
- 如果来源信息本身就不完整，加一个 `missing from source` 小节。

## Do not use when

- 原始内容已经是一篇结构很清晰的正式笔记
- 用户只想要一版很短的重点提炼
- 用户真正想做的是误解诊断，而不是主笔记构建

## Recommended next skill

Usually recommend:

- `lecture-focus-extractor`
- `misconception-finder`
