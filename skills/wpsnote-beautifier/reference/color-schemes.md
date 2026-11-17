# 预设配色方案

agent 根据文档类型和用户偏好选择配色方案。每个方案均严格选用 **WPS 笔记编辑器预设色板**（来自 `get_xml_reference`），**不可使用任意自定义 hex 色值**，否则编辑器会在写入后静默丢弃颜色属性。

---

## 方案 A：海洋蓝（默认 · 商务/学术）

冷静专业，适合工作报告、学术笔记、技术文档。

| 元素 | 属性 | 色值 |
|------|------|------|
| h1 / h2 标题 | fontColor | `#0E52D4` |
| h3 / h4 标题 | fontColor | `#116AF0` / `#0080A0` |
| 重点加粗 | fontColor | `#0E52D4` |
| 行内高亮 | fontHighlightColor | `#D9EEFB` |
| 高亮块-要点 | bg / border | `#E6EEFA` / `#98C1FF` |
| 高亮块-提示 | bg / border | `#FAF1E6` / `#FEC794` |
| 高亮块-警告 | bg / border | `#FAE6E6` / `#F2A7A7` |
| 分栏-正面 | columnBg | `#EBF2FF` |
| 分栏-负面 | columnBg | `#FFF5EB` |
| 分栏-中性 | columnBg | `#F2F2F2` |

---

## 方案 B：森林绿（自然 · 笔记/日记）

清新自然，适合读书笔记、个人总结、学习记录。

| 元素 | 属性 | 色值 |
|------|------|------|
| h1 / h2 标题 | fontColor | `#078654` |
| h3 / h4 标题 | fontColor | `#58A401` |
| 重点加粗 | fontColor | `#078654` |
| 行内高亮 | fontHighlightColor | `#DFF0C4` |
| 高亮块-要点 | bg / border | `#E6FAEB` / `#AFE3BB` |
| 高亮块-提示 | bg / border | `#FAF1E6` / `#FEC794` |
| 高亮块-警告 | bg / border | `#FAE6E6` / `#F2A7A7` |
| 分栏-正面 | columnBg | `#E8FCEF` |
| 分栏-负面 | columnBg | `#FFECEB` |
| 分栏-中性 | columnBg | `#EEFFEB` |

---

## 方案 C：暖橙（活力 · 创意/营销）

温暖有活力，适合创意策划、营销方案、产品文档。

| 元素 | 属性 | 色值 |
|------|------|------|
| h1 / h2 标题 | fontColor | `#DB7800` |
| h3 / h4 标题 | fontColor | `#D1A300` |
| 重点加粗 | fontColor | `#DB7800` |
| 行内高亮 | fontHighlightColor | `#F8D7B7` |
| 高亮块-要点 | bg / border | `#FAF1E6` / `#FEC794` |
| 高亮块-提示 | bg / border | `#E6EEFA` / `#98C1FF` |
| 高亮块-警告 | bg / border | `#FAE6E6` / `#F2A7A7` |
| 分栏-正面 | columnBg | `#FFF5EB` |
| 分栏-负面 | columnBg | `#FFECEB` |
| 分栏-中性 | columnBg | `#FEF6E7` |

---

## 方案 D：典雅紫（高端 · 设计/品牌）

沉稳优雅，适合品牌方案、设计文档、高端报告。

| 元素 | 属性 | 色值 |
|------|------|------|
| h1 / h2 / h3 / h4 标题 | fontColor | `#A639D7` |
| 重点加粗 | fontColor | `#A639D7` |
| 行内高亮 | fontHighlightColor | `#E6D6F0` |
| 高亮块-要点 | bg / border | `#F5EBFA` / `#E5B5FD` |
| 高亮块-提示 | bg / border | `#E6EEFA` / `#98C1FF` |
| 高亮块-警告 | bg / border | `#FAE6E6` / `#F2A7A7` |
| 分栏-正面 | columnBg | `#FAF0FF` |
| 分栏-负面 | columnBg | `#FFECEB` |
| 分栏-中性 | columnBg | `#F0EDFF` |

---

## 方案 E：石墨灰（极简 · 技术文档）

低调克制，适合技术文档、API 说明、系统设计。

| 元素 | 属性 | 色值 |
|------|------|------|
| h1 / h2 标题 | fontColor | `#080F17` |
| h3 / h4 标题 | fontColor | `#757575` |
| 重点加粗 | fontColor | `#080F17` |
| 行内高亮 | fontHighlightColor | `#E6E6E6` |
| 高亮块-要点 | bg / border | `#EBEBEB` / `#C5C5C5` |
| 高亮块-提示 | bg / border | `#FAF1E6` / `#FEC794` |
| 高亮块-警告 | bg / border | `#FAE6E6` / `#F2A7A7` |
| 分栏-正面 | columnBg | `#F2F2F2` |
| 分栏-负面 | columnBg | `#FFECEB` |
| 分栏-中性 | columnBg | `#EDEEF0` |

---

## 选择指南

| 文档类型 | 推荐方案 |
|----------|----------|
| 工作报告、会议纪要 | A 海洋蓝 |
| 读书笔记、学习总结 | B 森林绿 |
| 营销方案、创意策划 | C 暖橙 |
| 品牌文档、设计方案 | D 典雅紫 |
| 技术文档、代码笔记 | E 石墨灰 |
| 用户未指定 | A 海洋蓝（默认） |

如果用户提供了颜色偏好，必须从 WPS 预设色板（见 `wpsnote` Skill 或 `get_xml_reference`）中选择最接近的预设色值，不可写入非预设 hex 值。
