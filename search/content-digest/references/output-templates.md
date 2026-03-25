# Content Digest 输出模板

## 配色与格式规范

只使用 WPS 笔记预设格式。**`<highlightBlock>` 颜色属性不生效（WPS MCP 静默丢弃），改用 `<columns>` 实现底色块。**

| 用途 | 元素 | 颜色属性 | 说明 |
|-----|------|---------|------|
| 来源元信息（首行）| `<blockquote>` | 无 | 引用格式，放在章节标题正下方 |
| 核心观点标题 | `<h2>💡 核心观点</h2>` | — | 灯泡 emoji |
| 核心观点内容 | `<columns><column columnBackgroundColor="#EBF2FF">` | 浅蓝底色 | 内含 bullet 列表，用单列 columns 实现底色 |
| 金句摘录标题 | `<h2>⭐ 金句摘录</h2>` | — | 五角星 emoji |
| 金句摘录内容 | `<columns><column columnBackgroundColor="#FFF5EB">` | 浅橙底色 | 内含 `<p>`，用单列 columns 实现底色 |
| 一句话概括 | `<p>` | 无 | 普通段落，H2 标题下方 |
| 我的思考 | `<p>` | 无 | 普通段落 |
| 行动清单 | `<p listType="todo" checked="0">` | 无 | todo 列表 |

**强制规则：**
- 所有标题统一使用 H2
- 来源链接/文件路径**只在首行 blockquote 中出现**，不在文末重复
- 核心观点和金句摘录使用 `<columns>` 底色块（不用 `<highlightBlock>` 颜色）
- 多篇合并笔记：每个章节的「我的思考」后插入两个 `<p></p>` 空行再接下一章节标题
- 只有纯粘贴文本（无 URL 无文件路径）才在文末附 H2「原文」章节

---

## 文字类笔记模板

```xml
<h1>[内容标题] · 提炼 [YYYY-MM-DD]</h1>

<!-- ⚠️ H1 标题不加 emoji，emoji 只用于 H2 各模块 -->

<!-- 来源元信息：引用格式，首行 -->
<blockquote>来源：[URL 或本地路径] · 类型：[网页 / 公众号 / PDF / 书籍 / 邮件] · 日期：[YYYY-MM-DD]</blockquote>

<!-- 一句话概括：H2 + 普通段落 -->
<h2>📌 一句话概括</h2>
<p>[不超过 50 字，动词开头，忠实原文]</p>

<!-- 核心观点：H2 + 浅蓝底色列 -->
<h2>💡 核心观点</h2>
<columns>
<column columnBackgroundColor="#EBF2FF">
<p listType="bullet">[观点 1：用自己的语言转述，非原文照搬]</p>
<p listType="bullet">[观点 2]</p>
<p listType="bullet">[观点 3]</p>
</column>
</columns>

<!-- 金句摘录：H2 + 浅橙底色列 -->
<h2>⭐ 金句摘录</h2>
<columns>
<column columnBackgroundColor="#FFF5EB">
<p>[原文金句，逐字引用，不改动]</p>
</column>
</columns>

<!-- 我的思考：H2 + 普通段落 -->
<h2>💬 我的思考</h2>
<p>[与自身经历/工作的结合点，或质疑延伸；用户未提供则留 [待补充]，不编造]</p>

<!-- 行动清单：H2 + todo -->
<h2>✅ 行动清单</h2>
<p listType="todo" checked="0">[读完后要做的具体行动]</p>
```

> 无「原始来源」章节——来源已在首行 blockquote 中。

---

## 图片类笔记模板

```xml
<h1>[图片主题] · 解读 [YYYY-MM-DD]</h1>

<!-- ⚠️ H1 标题不加 emoji，emoji 只用于 H2 各模块 -->

<!-- 图片类无外部来源，首行写类型和日期 -->
<blockquote>类型：[截图 / 设计图 / 照片 / 图表 / 文档扫描] · 日期：[YYYY-MM-DD]</blockquote>

<!-- 一句话概括：10 字以内 -->
<h2>📌 一句话概括</h2>
<p>[图片核心内容，10 字以内]</p>

<!-- 内容解读：逐字提取文字、标明数值、描述界面/图表/人物要素 -->
<h2>🔍 内容解读</h2>
<p>[分点描述图片内容；有文字则逐字提取；有数据则标明数值]</p>

<!-- 核心信息：浅蓝底色列 -->
<h2>💡 核心信息</h2>
<columns>
<column columnBackgroundColor="#EBF2FF">
<p listType="bullet">[图片传达的主要观点或信息 1]</p>
<p listType="bullet">[要点 2]</p>
</column>
</columns>

<!-- 我的思考：适用场景、设计亮点或可借鉴之处 -->
<h2>💬 我的思考</h2>
<p>[图片适用场景、设计亮点或可借鉴之处；用户未提供则留 [待补充]]</p>
```

> 图片类笔记不需要「原文」模块。

---

## 多篇内容合并模板

笔记标题：`内容提炼合集 · [YYYY-MM-DD]`

```xml
<h1>内容提炼合集 · [YYYY-MM-DD]</h1>

<!-- ⚠️ H1 标题不加 emoji -->

<!-- 第一篇 -->
<h2>一、[第一篇标题]</h2>
<blockquote>来源：[...] · 类型：[...] · 日期：[...]</blockquote>
<h2>📌 一句话概括</h2>
<p>[...]</p>
<h2>💡 核心观点</h2>
<columns>
<column columnBackgroundColor="#EBF2FF">
<p listType="bullet">[...]</p>
</column>
</columns>
<h2>⭐ 金句摘录</h2>
<columns>
<column columnBackgroundColor="#FFF5EB">
<p>[...]</p>
</column>
</columns>
<h2>💬 我的思考</h2>
<p>[待补充]</p>
<p></p>
<p></p>

<!-- 第二篇（结构同上）-->
<h2>二、[第二篇标题]</h2>
...
```

---

## 纯粘贴文本的原文附录（仅限无 URL、无文件路径的纯文本输入）

```xml
<h2>原文</h2>
<p>[原文第一段，原样保留，不做任何修改]</p>
<p>[原文第二段]</p>
```
