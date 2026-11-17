# XML 写入模板

美化操作常用的 XML 模板。所有模板中的新建 block 不需要 id 属性（系统自动分配）。
色值以方案 A（海洋蓝）为例，实际使用时替换为所选方案的对应色值。

---

## 1. 带颜色的标题

### 一级标题

```xml
<h1><span fontColor="#0E52D4">文档主标题</span></h1>
```

### 二级标题

```xml
<h2><span fontColor="#0E52D4">章节标题</span></h2>
```

### 三级标题

```xml
<h3><span fontColor="#116AF0">子章节标题</span></h3>
```

---

## 2. 强调文字

### 加粗 + 颜色

```xml
<p>普通文字中的<strong><span fontColor="#0E52D4">重点关键词</span></strong>需要突出。</p>
```

### 行内高亮

```xml
<p>这个<span fontHighlightColor="#D9EEFB">关键概念</span>需要注意。</p>
```

### 加粗 + 行内高亮（双重强调）

```xml
<p>这是<strong><span fontHighlightColor="#D9EEFB">最核心的结论</span></strong>。</p>
```

---

## 3. 高亮块

### 要点/结论型

```xml
<highlightBlock emoji="💡" highlightBlockBackgroundColor="#E6EEFA" highlightBlockBorderColor="#98C1FF">
  <p><strong>核心要点</strong></p>
  <p>这里放需要强调的结论或关键发现。</p>
</highlightBlock>
```

### 提示/注意型

```xml
<highlightBlock emoji="⚠️" highlightBlockBackgroundColor="#FAF1E6" highlightBlockBorderColor="#FEC794">
  <p><strong>注意事项</strong></p>
  <p>这里放需要提醒读者注意的内容。</p>
</highlightBlock>
```

### 警告/风险型

```xml
<highlightBlock emoji="❗" highlightBlockBackgroundColor="#FAE6E6" highlightBlockBorderColor="#F2A7A7">
  <p><strong>重要警告</strong></p>
  <p>这里放风险提示或错误警告。</p>
</highlightBlock>
```

### 引用/摘要型

```xml
<highlightBlock emoji="📖" highlightBlockBackgroundColor="#E6EEFA" highlightBlockBorderColor="#98C1FF">
  <p><em>引用的原文或文献摘要内容放在这里。</em></p>
</highlightBlock>
```

### 定义/术语型

```xml
<highlightBlock emoji="📝" highlightBlockBackgroundColor="#F5EBFA" highlightBlockBorderColor="#E5B5FD">
  <p><strong>术语名称</strong></p>
  <p>术语的定义和解释。</p>
</highlightBlock>
```

### 高亮块内包含列表

```xml
<highlightBlock emoji="✅" highlightBlockBackgroundColor="#E6EEFA" highlightBlockBorderColor="#98C1FF">
  <p><strong>关键步骤</strong></p>
  <p listType="ordered" listLevel="0" listId="hl1">第一步操作</p>
  <p listType="ordered" listLevel="0" listId="hl1">第二步操作</p>
  <p listType="ordered" listLevel="0" listId="hl1">第三步操作</p>
</highlightBlock>
```

---

## 4. 分栏

### 二栏对比（优缺点）

```xml
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <p><strong><span fontColor="#0E52D4">✅ 优势</span></strong></p>
    <p>优势点一</p>
    <p>优势点二</p>
    <p>优势点三</p>
  </column>
  <column columnBackgroundColor="#FFF5EB">
    <p><strong><span fontColor="#DB7800">❌ 劣势</span></strong></p>
    <p>劣势点一</p>
    <p>劣势点二</p>
    <p>劣势点三</p>
  </column>
</columns>
```

### 二栏对比（方案 A vs B）

```xml
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <p><strong><span fontColor="#0E52D4">方案 A</span></strong></p>
    <p>方案 A 的核心要点</p>
    <p>方案 A 的特色</p>
  </column>
  <column columnBackgroundColor="#FAF0FF">
    <p><strong><span fontColor="#A639D7">方案 B</span></strong></p>
    <p>方案 B 的核心要点</p>
    <p>方案 B 的特色</p>
  </column>
</columns>
```

### 三栏并列（概念对比）

```xml
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <p><strong><span fontColor="#0E52D4">概念 A</span></strong></p>
    <p>说明文字</p>
  </column>
  <column columnBackgroundColor="#E8FCEF">
    <p><strong><span fontColor="#078654">概念 B</span></strong></p>
    <p>说明文字</p>
  </column>
  <column columnBackgroundColor="#FFF5EB">
    <p><strong><span fontColor="#DB7800">概念 C</span></strong></p>
    <p>说明文字</p>
  </column>
</columns>
```

### 二栏数据摘要

```xml
<columns>
  <column columnBackgroundColor="#F2F2F2">
    <p><strong>📊 关键指标</strong></p>
    <p><span fontColor="#0E52D4" fontSize="20">85%</span></p>
    <p>用户满意度</p>
  </column>
  <column columnBackgroundColor="#F2F2F2">
    <p><strong>📈 增长趋势</strong></p>
    <p><span fontColor="#078654" fontSize="20">+23%</span></p>
    <p>同比增长率</p>
  </column>
</columns>
```

---

## 5. 列表美化

### 带颜色的有序列表

```xml
<p listType="ordered" listLevel="0" listId="lst1"><strong><span fontColor="#0E52D4">第一步</span></strong> — 具体操作说明</p>
<p listType="ordered" listLevel="0" listId="lst1"><strong><span fontColor="#0E52D4">第二步</span></strong> — 具体操作说明</p>
<p listType="ordered" listLevel="0" listId="lst1"><strong><span fontColor="#0E52D4">第三步</span></strong> — 具体操作说明</p>
```

### 嵌套无序列表

```xml
<p listType="bullet" listLevel="0">一级要点</p>
<p listType="bullet" listLevel="1">二级细节 A</p>
<p listType="bullet" listLevel="1">二级细节 B</p>
<p listType="bullet" listLevel="0">另一个一级要点</p>
```

---

## 6. 分隔线

在章节之间插入分隔线增加视觉分隔：

```xml
<hr/>
```

---

## 7. 组合模板

### 章节开头摘要 + 正文

```xml
<h2><span fontColor="#0E52D4">章节标题</span></h2>
<highlightBlock emoji="📌" highlightBlockBackgroundColor="#E6EEFA" highlightBlockBorderColor="#98C1FF">
  <p>本章节核心：一句话概括本节要讲什么。</p>
</highlightBlock>
<p>正文段落开始……</p>
```

### 对比分析段落

```xml
<h3><span fontColor="#116AF0">方案对比分析</span></h3>
<p>以下从多个维度对比两种方案：</p>
<columns>
  <column columnBackgroundColor="#EBF2FF">
    <p><strong><span fontColor="#0E52D4">方案 A</span></strong></p>
    <p>方案描述</p>
  </column>
  <column columnBackgroundColor="#FFF5EB">
    <p><strong><span fontColor="#DB7800">方案 B</span></strong></p>
    <p>方案描述</p>
  </column>
</columns>
<highlightBlock emoji="💡" highlightBlockBackgroundColor="#E6FAEB" highlightBlockBorderColor="#AFE3BB">
  <p><strong>推荐结论</strong></p>
  <p>综合考虑，推荐方案 X，因为……</p>
</highlightBlock>
```

### 步骤流程段落

```xml
<h3><span fontColor="#116AF0">操作步骤</span></h3>
<highlightBlock emoji="⚠️" highlightBlockBackgroundColor="#FAF1E6" highlightBlockBorderColor="#FEC794">
  <p>开始前请确保已完成前置准备。</p>
</highlightBlock>
<p listType="ordered" listLevel="0" listId="steps"><strong><span fontColor="#0E52D4">准备阶段</span></strong> — 说明</p>
<p listType="ordered" listLevel="0" listId="steps"><strong><span fontColor="#0E52D4">执行阶段</span></strong> — 说明</p>
<p listType="ordered" listLevel="0" listId="steps"><strong><span fontColor="#0E52D4">验证阶段</span></strong> — 说明</p>
<highlightBlock emoji="✅" highlightBlockBackgroundColor="#E6FAEB" highlightBlockBorderColor="#AFE3BB">
  <p><strong>完成标志</strong></p>
  <p>当看到 XXX 时表示操作成功。</p>
</highlightBlock>
```

---

## 8. batch_edit 示例

将多个操作合并为一次 batch_edit 调用：

```json
{
  "note_id": "xxx",
  "operations": [
    {
      "op": "replace",
      "block_id": "aaa",
      "content": "<h2><span fontColor=\"#0E52D4\">新标题</span></h2>"
    },
    {
      "op": "insert",
      "anchor_id": "bbb",
      "position": "after",
      "content": "<highlightBlock emoji=\"💡\" highlightBlockBackgroundColor=\"#E6EEFA\" highlightBlockBorderColor=\"#98C1FF\"><p><strong>核心要点</strong></p><p>要点内容。</p></highlightBlock>"
    },
    {
      "op": "replace",
      "block_id": "ccc",
      "content": "<p>普通文字中的<strong><span fontColor=\"#0E52D4\">重点</span></strong>被突出。</p>"
    }
  ]
}
```
