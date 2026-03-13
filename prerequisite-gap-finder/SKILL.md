---
name: prerequisite-gap-finder
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户觉得一个主题看不懂、学得卡住，或者想知道自己到底缺了哪些前置基础时使用此 Skill。适合课程复习、自学卡点分析、考前查漏补缺、回看旧笔记时发现“明明记了但还是不会”的场景。
---

# WPS Prerequisite Gap Finder 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 当前感觉吃力的一篇 WPS 学习笔记或主题
- 可能覆盖基础知识的旧 WPS 笔记
- 可选的课程阶段、考试背景或难度说明

## Output

A structured WPS-ready 前置知识缺口报告，包含缺失基础、修复路径和补完后的自测项。

## What this skill should produce

目标不只是告诉用户“这里有缺口”，而是进一步说明：缺什么、为什么卡、先补什么、补完后怎么验。

建议包含这些部分：

1. `required prerequisites`
2. `covered in existing notes`
3. `missing or weak`
4. `why this blocks understanding`
5. `repair plan`
6. `self-check after repair`

## WPS-first rules

- 如果旧笔记里已经有能补基础的内容，要明确点出对应笔记标题。
- 如果没有可回看的旧笔记，也要直说，不要硬编。
- 修复计划尽量拆成小动作，并给出大致投入量。

## Quality rules

- 把缺口分成 blocker、important but recoverable、optional depth 三档。
- 更关注“阻断理解”的基础，而不是所有相关背景都一股脑列出来。
- 缺口说明要和当前主题直接挂钩，让用户知道为什么这里会卡。

This skill should identify prerequisite gaps, not diagnose all misunderstandings in the current note.

## Do not use when

- 用户想找的是当前笔记内部的错误或误解
- 主题本身已经理解得差不多，只需要抽复习重点
- 当前主题范围太散，无法形成有意义的前置链条

## Recommended next skill

Usually recommend:

- `misconception-finder`
- `study-note-linker`
