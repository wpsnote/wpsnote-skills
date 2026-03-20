# WPS 笔记写入模板

## 模式 B：今日规划页结构（日历 → 笔记）

```xml
<h1>📋 今日规划 YYYY-MM-DD（周X）</h1>
<h2>📅 今日日程</h2>

<highlightBlock emoji="🕐" highlightBlockBackgroundColor="#EBF2FF" highlightBlockBorderColor="#98C1FF">
  <h3>HH:MM–HH:MM｜[事件标题]</h3>
  <p>[日历名]</p>
  <p>📎 <a href="wps://note/[note_id]">[关联笔记标题]</a></p>
</highlightBlock>

<h2>📝 今日待办</h2>
<p listType="todo" listLevel="0" checked="0"> </p>

<h2>💡 AI 建议</h2>
<p listType="bullet" listLevel="0">⚡ [建议内容]</p>
```

**AI 建议生成规则：**
- 时间冲突：事件时间重叠时提示
- 高密度预警：连续 3 个以上事件无间隙
- 前置提示：基于明日事件（见模式 C 触发词表）

---

## 模式 C：已落日历标注（笔记 → 日历）

写入日历成功后，在笔记对应 block 后追加：

```xml
<p><span fontColor="#078654">✓ 已添加到日历（YYYY-MM-DD HH:MM）</span></p>
```

---

## 模式 D：前置任务块（智能前置）

```xml
<h2>🔮 明日预判 · 今日需要做的准备</h2>

<highlightBlock emoji="⚠️" highlightBlockBackgroundColor="#FAF1E6" highlightBlockBorderColor="#FEC794">
  <h3>明天：[事件标题]（YYYY-MM-DD HH:MM）</h3>
  <p listType="todo" listLevel="0" checked="0">收拾行李</p>
  <p listType="todo" listLevel="0" checked="0">确认票务</p>
  <p listType="todo" listLevel="0" checked="0">备好充电宝和证件</p>
  <p>📎 <a href="wps://note/[note_id]">[相关笔记标题]</a></p>
</highlightBlock>
```

---

## 模式 E：全局时间线（全局规划）

```xml
<h2>⏰ 今日时间线</h2>

<columns>
  <column columnBackgroundColor="#EBF2FF">
    <h3>🌅 上午</h3>
    <p listType="todo" listLevel="0" checked="0">09:00 深度工作：[来自待办]</p>
    <p>10:30 [已有日历事件]</p>
  </column>
  <column columnBackgroundColor="#E8FCEF">
    <h3>☀️ 下午（高密）</h3>
    <p>14:00 [日历事件1]</p>
    <p>15:30 [日历事件2]</p>
    <p>16:30 [日历事件3]</p>
  </column>
</columns>

<h2>📌 今日核心 3 件事</h2>
<p listType="ordered" listLevel="0" listId="top3">最重要的事（来自笔记待办）</p>
<p listType="ordered" listLevel="0" listId="top3">第二重要的事</p>
<p listType="ordered" listLevel="0" listId="top3">第三重要的事</p>
```
