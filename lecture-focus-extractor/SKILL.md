---
name: lecture-focus-extractor
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户手上已经有一篇较长的课堂笔记、逐字稿或学习记录，但只想提取最值得复习的重点时使用此 Skill。适合课程录音整理、复习提纲抽取、考前过重点、快速补课等场景。
---

# WPS Lecture Focus Extractor 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 一篇较长的课堂笔记、逐字稿或学习记录
- 可选的主题、课程名或考试范围
- 可选的复习目标，例如考前速看、补课、查重点

## Output

A structured WPS-ready 重点提炼页，把必须复习的内容和背景性内容清楚分开。

## What this skill should produce

目标不是做一篇普通摘要，而是提炼“最值得复习的部分”。

建议包含这些部分：

1. `must remember`
2. `definitions / formulas / principles`
3. `teacher emphasis`
4. `likely forget points`
5. `one-minute recap`
6. `10-minute review list`

## WPS-first rules

- 重点优先用短条目表达，不要写成长段总结。
- 最后一部分最好能直接拿去做考前速看。
- 如果原笔记已经有清晰结构，不要为了压缩而把层次全部打平。

## Quality rules

- 更优先保留重复出现、被强调、容易混淆、容易忘记的内容。
- 能体现规则的例子，比纯定义更值得留下。
- 如果某一部分只是背景补充，要明确告诉用户“了解即可”。

## Do not use when

- 用户需要的是一篇完整的结构化主笔记
- 原始内容本身已经很短、很聚焦
- 用户真正想直接生成闪卡，而不是先提炼重点

## Recommended next skill

Usually recommend:

- `notes-to-flashcards`
- `class-note-builder`
