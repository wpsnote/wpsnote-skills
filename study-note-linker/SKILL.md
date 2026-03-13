---
name: study-note-linker
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户希望把当前 WPS 学习笔记和已有旧笔记连起来，而不是让新笔记继续孤立存在时使用此 Skill。适合复习串讲、知识网络梳理、课程回看、专题学习和研究型笔记关联等场景。
---

# WPS Study Note Linker 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 当前正在阅读或整理的一篇 WPS 学习笔记
- 可能相关的历史 WPS 笔记
- 可选的课程、考试、专题或项目背景

## Output

A structured WPS-ready 笔记关联分析，包含关系类型、推荐回看顺序和建议插入的双链语句。

## What this skill should produce

目标不是“找几篇看起来相似的笔记”，而是帮用户建立有学习意义的笔记关系。

建议包含这些部分：

1. `top related notes`
2. `relation type`
3. `why it matters now`
4. `recommended reading order`
5. `suggested backlink sentence`
6. `what this note still lacks`

## WPS-first rules

- 在 WPS 笔记里先检索已有旧笔记，再判断关系，不要凭空猜。
- 输出时要明确写出旧笔记标题，方便用户直接回搜。
- 宁可给 3 条高价值关联，也不要堆 10 条泛泛相关。

## Quality rules

- 关系优先按学习价值排序，不只按关键词相似度排序。
- 明确区分 prerequisite、same topic extension、contrast、example、revision companion。
- 如果没有足够强的旧笔记可连，要直接说清楚。

This skill should prioritize note relationship building, not selective recall for immediate writing or study tasks.

## Do not use when

- 用户主要只是想快速召回几篇旧笔记立刻复用
- 当前没有可连接的历史笔记
- 用户想要的是主题总结，而不是笔记到笔记的连接

## Recommended next skill

Usually recommend:

- `insight-recaller`
- `prerequisite-gap-finder`
