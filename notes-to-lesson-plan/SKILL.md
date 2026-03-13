---
name: notes-to-lesson-plan
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户希望把 WPS 学习笔记整理成一份可讲给别人听的讲解结构、迷你教案或 teach-back 提纲时使用此 Skill。它不仅适合老师，也适合自学者用“能不能讲出来”来检验自己是否真正掌握。
---

# WPS Notes to Lesson Plan 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 一篇或多篇 WPS 学习笔记
- 可选的讲解对象、使用场景或 teach-back 目标
- 可选的时间限制或输出形式要求

## Output

A structured WPS-ready 迷你教案或 teach-back 讲解提纲，可面向老师使用，也可面向学习者自讲自测。

## What this skill should produce

这里的重点不是完整教学设计模板，而是通过“能讲出来”来检验掌握程度。

建议包含这些部分：

1. `teaching goal`
2. `what the learner should explain clearly`
3. `what will likely be hard to explain`
4. `example flow`
5. `teach-back questions`
6. `practice task`

This can produce either a teacher-facing mini lesson plan or a learner-facing teach-back script.

## WPS-first rules

- 同时兼容老师视角和自学者视角。
- 如果用户本身是学习者，优先转成可讲给别人听的提纲。
- 更强调讲解顺序和表达清晰度，而不是教研级完备度。

## Quality rules

- 尽量让输出能直接用于自我讲述、带同学复习或做小组分享。
- 要指出哪里最容易“讲不清”，帮助用户发现掌握薄弱点。
- 例子和提问比空泛定义更能检验是否真会讲。

## Do not use when

- 用户只想要闪卡或复习清单
- 原始笔记太浅，撑不起讲解流程
- 用户真正想做的是误解诊断，而不是讲解规划

## Recommended next skill

Usually recommend:

- `misconception-finder`
- `notes-to-flashcards`
