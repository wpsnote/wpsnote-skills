---
name: notes-to-flashcards
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户希望把 WPS 笔记转成可主动回忆的复习卡片时使用此 Skill。适合课程笔记复习、概念记忆、考前冲刺、误解修正后的再巩固，以及把静态笔记变成可刷卡片的学习材料。
---

# WPS Notes to Flashcards 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 一篇或多篇 WPS 学习笔记
- 可选的主题范围或考试范围
- 可选的卡片数量、难度重点或复习偏好

## Output

A structured WPS-ready flashcard deck，包含主动回忆卡片和轻量复习提示。

## What this skill should produce

目标不是机械摘句，而是把笔记真正转成可用于复习的卡片组。

建议包含这些部分：

1. `definition cards`
2. `distinction cards`
3. `example cards`
4. `application cards`
5. `easy-to-confuse cards`
6. `review order`

Use review timing as lightweight review hints, not a full spaced-repetition schedule.

## WPS-first rules

- 尽量标注来源笔记标题或原章节，方便回看。
- 卡片正面要短、清楚、能靠记忆回答。
- 容易混淆的卡片要单独标出来，优先复习。

## Quality rules

- 优先抽取定义、辨析、例子、应用四类高价值卡片。
- 轻量复习顺序可以提示 today / 3 days / 7 days，但不要假装这是完整排期系统。
- 如果原笔记不完整，要说明卡片覆盖面有限。

## Do not use when

- 用户要的是讲解脚本，而不是回忆卡片
- 原笔记内容太碎，无法稳定生成卡片
- 用户真正需要的是诊断型小测，而不是 flashcards

## Recommended next skill

Usually recommend:

- `misconception-finder`
- `notes-to-lesson-plan`
