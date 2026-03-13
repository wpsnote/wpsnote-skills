---
name: misconception-finder
author: Loki Mao (赛博小熊猫 Loki)
description: 当用户希望检查一篇 WPS 学习笔记里是否存在理解错误、概念混淆、逻辑跳步或表述过虚时使用此 Skill。适合课后自查、复习前校正、讲给别人之前自检，以及“我是不是以为自己懂了其实没懂”的场景。
---

# WPS Misconception Finder 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- 一篇 WPS 学习笔记、解释稿或复习笔记
- 可选的主题标签
- 可选的教材摘要、答案要点或参考资料

## Output

A structured WPS-ready 误解诊断结果，包含问题定位、修正建议和小型自测问题。

## What this skill should produce

这是一个“诊断 + 修复”型 skill，不是语言润色器。

建议包含这些部分：

1. `overall understanding diagnosis`
2. `high-confidence errors`
3. `possible misunderstandings`
4. `missing evidence or examples`
5. `better phrasing for understanding repair`
6. `mini self-test`

## WPS-first rules

- 尽量引用用户笔记里的原句，告诉用户具体哪里出了问题。
- 修正建议要能直接回填到笔记里，而不是只给抽象评价。
- 每个关键误解最好都附一条自测题，方便立刻验证。

## Quality rules

- 明确区分 clearly wrong、likely confused、too vague to trust。
- 低置信度的问题要说明为什么只是“可能误解”。
- “better phrasing” 的目标是修正理解，不是把句子写得更华丽。

## Do not use when

- 用户只是想润色文字表达
- 原始笔记内容太薄，无法支撑有效诊断
- 用户真正要做的是前置知识缺口分析

## Recommended next skill

Usually recommend:

- `notes-to-flashcards`
- `prerequisite-gap-finder`
