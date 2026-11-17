---
name: study-assistant
description: WPS 笔记学习助手：把课堂逐字稿、OCR/截图整理为结构化主笔记，提炼复习重点与主动回忆闪卡，诊断理解误区与缺失前置知识，生成费曼讲授提纲，并关联已有旧笔记。适合听课整理、考前过重点、卡壳补缺与知识网络串联。不用于互动出题与逐题批改（请用 note-review-coach）。
metadata:
  author: Loki Mao (赛博小熊猫 Loki)
  version: "2.0.0"
  category: learning
  tags: [study, note-taking, flashcards, review, wpsnote]
---

# WPS 学习助手（Study Assistant）

> 笔记读写与标签操作遵循 [wpsnote](../wpsnote/SKILL.md)；需要互动出题与按原文批改闭环时，配合 [note-review-coach](../note-review-coach/SKILL.md)。

将课堂整理、重点提取、错因诊断、前置补缺与旧知关联收口在一个工作流里，推进学习任务从“记下来”走到“能复习、能补缺、能串联”。

## 能力模式（按用户意图选用）

| 模式 | 适用请求 | 核心输出 |
|------|---------|---------|
| **1. 课堂主笔记整理** | 逐字稿 / OCR / 板书截图 / 零散笔记整理为主笔记 | `30-second summary`、核心概念与公式、老师反复强调点、案例、易混点、`still unclear`、`next review tasks` |
| **2. 重点提炼与闪卡** | 从长笔记提炼复习重点，或转为可刷题的 QA 复习卡片 | `must remember`、`easy to confuse`、`self-check`（单卡仅考 1 个要点，正面不泄露答案，注明出处标题） |
| **3. 误区诊断与前置补缺** | 看不懂、学卡住、想检查笔记中的逻辑跳步或概念混淆 | 问题定位、正确解释、缺失前置概念顺序、`repair tasks` |
| **4. 费曼讲授提纲（Teach-Back）** | 准备把一个概念讲给别人听、检验是否真懂 | 用通俗语言串联的讲解顺序、类比案例与常见追问 |
| **5. 知识关联与旧知召回** | 新笔记写完想找相关旧笔记、建知识联系，或写前想起可用旧笔记 | 值得重看/关联的旧笔记标题、互补/对比/前置关系、可直接复用片段与插入位置 |

## 共同约束

- **优先复用已有笔记**：目标笔记已存在时在原笔记上补强，不重复另建；跨笔记引用必须写出准确的旧笔记标题，方便检索。
- **区分置信度**：原始逐字稿或 OCR 不完整时，明确标注 `Confirmed from notes`、`Likely inference` 或 `Still missing`（以及 `missing from source`），不把猜测包装成确定结论。
- **输出适合扫读**：段落简短分点，避免大段堆砌；每次输出末尾给出 1–2 个明确下一步动作（如补充缺失前置、转入 `note-review-coach` 自测等）。
