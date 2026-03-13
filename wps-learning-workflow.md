# WPS 学习工作流

这套工作流用于约束整组学习类 Skill 在 WPS 笔记中的协作方式。

## 核心原则

不要停留在“分析一下”。

这组 Skill 的目标应该是把用户往前推进一步：

- 从课堂记录推进到结构化笔记
- 从原始笔记推进到复习重点
- 从卡壳推进到查漏补缺
- 从理解偏差推进到修正与自测
- 从孤立笔记推进到知识网络

## 标准流程

1. 课堂记录或原始材料进入 WPS 笔记
2. 整理成结构化主笔记
3. 抽取关键知识点和复习重点
4. 识别易混淆点与误解
5. 检查前置知识缺口
6. 关联历史笔记与旧洞见
7. 生成闪卡、讲解提纲或下一轮复习任务

## 标准输出块

在适合的情况下，优先使用这些学习友好的输出块：

- `30-second summary`
- `must remember`
- `easy to confuse`
- `missing prerequisites`
- `examples / evidence`
- `repair tasks`
- `self-check`
- `next review`

## 信息置信度处理

当来源不完整、课堂记录较乱或 OCR 质量一般时，要分清：

- `Confirmed from notes`
- `Likely inference`
- `Still missing`

这样可以避免把不确定内容包装成确定知识点。

## Skill 串联建议

整组 skill 最好形成一个学习闭环，而不是分散使用：

- `class-note-builder` -> `lecture-focus-extractor`
- `lecture-focus-extractor` -> `notes-to-flashcards`
- `study-note-linker` -> `insight-recaller`
- `prerequisite-gap-finder` -> `misconception-finder`
- `misconception-finder` -> `notes-to-flashcards`
- `notes-to-flashcards` -> 进入下一轮复习
- `notes-to-lesson-plan` -> 用讲给别人听的方式检验掌握程度

## WPS 场景下的额外要求

- 尽量先复用已有 WPS 笔记，再决定是否新建。
- 输出要适合在 WPS 里快速扫读，不要堆成长段。
- 如果引用旧笔记，要明确写出笔记标题，方便检索。
- 每次输出后，尽量给出下一步动作：待办、复习顺序、自测题或建议继续运行的 skill。
