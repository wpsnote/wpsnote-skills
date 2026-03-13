---
name: insight-recaller
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户在 WPS 里写新内容、做专题复习、准备讲稿或整理研究思路时，希望把过去真正有用的旧笔记重新召回到眼前，就使用此 Skill。它更适合“现在最该想起什么”，而不是做完整的笔记建链。
---

# WPS Insight Recaller 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 当前正在处理的一篇 WPS 笔记、写作任务或复习主题
- 可能相关的旧 WPS 笔记
- 可选的时间范围或任务上下文

## Output

A structured WPS-ready 选择性召回结果，指出当前最值得重看的旧笔记和可直接复用的内容。

## What this skill should produce

重点不是“多找一些相似笔记”，而是召回当下最有价值的旧内容。

建议包含这些部分：

1. `most useful prior notes now`
2. `why each is worth recalling`
3. `how it connects to the current task`
4. `what can be reused directly`
5. `where to insert or link it`

This skill should recall useful prior notes, not perform full cross-note mapping.

## WPS-first rules

- 输出时要写明旧笔记标题，方便用户直接在 WPS 里找到。
- 如果拿不到原段落，就做可信的概括，不要伪装成精确引用。
- 召回数量宁少勿滥，优先高价值内容。

## Quality rules

- 优先挑“现在就用得上”的旧笔记，而不是“有点像”的旧笔记。
- 尽量在理论、对比、案例之间做平衡，不要只召回同一种内容。
- 对“可直接复用”和“适合后面展开”的内容要区分清楚。

## Do not use when

- 目标是建立明确的笔记双链或关系图
- 用户真正想做的是大范围综述，而不是选择性召回
- 没有足够有意义的旧笔记可供召回

## Recommended next skill

Usually recommend:

- `study-note-linker`
- `class-note-builder`
