---
name: news-to-note
description: >
  基于 WPS 笔记知识库的新闻智能解读。将新闻存入笔记，搜索用户整个笔记库找到关联内容，
  产出个性化 insight 分析。也支持批量新闻收集写入简报。
  当用户说「找新闻」「热点汇总」「新闻简报」「帮我读这篇文章」「看看这个链接」
  「这条新闻和我的项目有什么关系」或谈论/分享任何具体新闻资讯时使用。
  不适用于：笔记的常规读写编辑、非新闻类内容的保存、纯知识问答。
metadata:
  version: 1.0.0
  mcp-server: wpsnote
  tags: [news, insight, knowledge-base, wps-note]
---

# 新闻智能解读 — 用你的笔记知识库读懂每一条新闻

## 核心理念

**纯新闻没有价值，新闻 × 你的知识库 = 有价值的洞察。**

任何应用都能搜索新闻，但只有 WPS 笔记知道用户关心什么、在做什么项目、参加过什么会议、记录过什么想法。本 Skill 的核心能力：

1. 将新闻/资讯存入 WPS 笔记（沉淀为知识资产）
2. 在用户的**整个笔记库**中检索关联内容（工作笔记、会议记录、项目文档等）
3. 将新闻与用户已有知识连接，产出**个性化 insight**

## 两种工作流

| 工作流 | 触发场景 | 产出 |
|--------|----------|------|
| **A — 新闻收集** | "找新闻""热点汇总""新闻简报" | 当日简报笔记 |
| **B — 新闻解读** | 用户接触到任何具体新闻/资讯 | 笔记存档 + 个性化深度分析 |

判断规则：
- 用户接触到**具体新闻**（发链接、提话题、贴正文、讨论新闻事件） → B
- 用户要求**批量搜索**、做简报汇总 → A
- 模糊时默认 B

**不适用于**：笔记的常规读写编辑（用 wps-note Skill）、非新闻类内容保存、纯知识问答。

---

## 工作流 A：新闻收集

批量搜索 → 去重筛选 → 写入简报笔记。

### 步骤

1. **构造搜索词**：至少含主题词 + 时效词，用 `site:` 限定来源，2-4 组查询。模板见 [query-recipes.md](references/query-recipes.md)。
2. **规范化与去重**：清除 `utm_*` 等跟踪参数，以 URL 去重，避免重复写入。
3. **定位目标笔记**：标题格式 `新闻简报 YYYY-MM-DD`，先搜后建。
4. **写入内容**：刷新大纲获取 `block_id`，用 `edit_block(op=insert)` 追加 `<h2>` 标题 + `<p><a>` 链接 + `<p>` 摘要。
5. **同步**：`sync_note`，回报插入条数。

---

## 工作流 B：新闻解读（核心）

**这是本 Skill 的核心差异化能力。** 用户接触到任何新闻时触发。

### B1. 获取新闻内容

| 输入类型 | 获取方式 |
|----------|----------|
| 有 URL | `web_fetch` 抓取全文；失败回退 `web_search` |
| 有话题无链接 | `web_search` 搜索 → 选最佳 1-2 篇 → `web_fetch` 抓取 |
| 直接贴正文 | 直接使用，提取标题和来源 |

清洗内容：去除导航栏、广告、评论区等非正文内容。

### B2. 保存到 WPS 笔记

以文章标题为笔记标题。标题和元信息一次性写入，**正文必须分次写入**。

**一次性写入 — 创建笔记 + 元信息：**

```
create_note(title=文章标题)
get_note_outline → 获取锚点 block_id
edit_block(op=insert) 写入元信息：
```

```xml
<h1>文章标题</h1>
<p><tag>#新闻</tag> <tag>#新闻//领域标签</tag></p>
<highlightBlock emoji="🔗" highlightBlockBackgroundColor="#E6EEFA" highlightBlockBorderColor="#98C1FF">
  <p><strong>来源：</strong><a href="原文URL">来源名称</a></p>
  <p><strong>发布时间：</strong>YYYY-MM-DD</p>
</highlightBlock>
<h2>正文</h2>
```

**分次追加 — 正文分段写入：**

正文按段落分批写入，每次 insert 使用上一次返回的 `last_block_id` 作为锚点：

```
edit_block(op=insert, anchor_id=last_block_id, position=after)
  → 写入 3-5 个 <p> 段落
  → 拿到新的 last_block_id

edit_block(op=insert, anchor_id=新的last_block_id, position=after)
  → 写入下一批 3-5 个 <p> 段落
  → 重复直到正文写完
```

**关键规则：**
- 标题、标签、来源等元信息可以一次性写入。
- **正文禁止一次性写入**，必须分批追加，每批 3-5 个 `<p>` 段落。
- 连续 insert 直接使用返回的 `last_block_id` 做锚点，无需每次刷新大纲。
- 最后一批写完后调用 `sync_note` 同步。

标签策略：始终加 `#新闻`，按内容加二级标签如 `#新闻//AI`、`#新闻//金融`，每篇 1-3 个。

### B3. 检索用户知识库（关键步骤）

**核心差异化：不只搜新闻，搜用户的所有笔记。**

提取 3-5 个关键词，在**整个笔记库**中多维度检索：
- 按关键词全文搜索（公司名、技术名、行业名、人物名）
- 按领域标签搜索历史新闻
- 按时间范围搜索近期笔记

工作笔记、会议记录、项目文档都是有价值的关联源。详细检索策略见 [knowledge-search-strategy.md](references/knowledge-search-strategy.md)。

### B4. 读取关联笔记

- `get_note_outline` 预览结构，判断相关性
- 高相关笔记用 `read_note` / `read_section` 读取，最多 5 篇
- 重点提取用户的个人观点、决策、计划

### B5. 产出个性化 insight

**不是新闻摘要，而是"这条新闻对我意味着什么"。**

回答结构：
1. **新闻要点** — 2-3 句话概括
2. **与你的关联** — 引用用户笔记："你在 [笔记标题] 中提到过..."，指出对当前工作的潜在影响
3. **深度洞察** — 趋势判断、对比分析、行动建议
4. **延伸阅读** — 推荐笔记库中值得重读的关联笔记

要求：去掉用户笔记关联后回答就变平庸，这才说明 insight 做对了。若无关联笔记，诚实说明并给通用分析。

---

## 示例

### 示例 1：用户发链接

用户说：「帮我看看这篇 https://36kr.com/p/xxx OpenAI融资的新闻」

操作：
1. `web_fetch` 抓取全文 → 提取标题"OpenAI 获 1100 亿美元融资"
2. `create_note` → `edit_block` 写入元信息和标签 → 分次追加正文段落 → `sync_note`
3. `search_notes(keyword="OpenAI")` + `search_notes(keyword="AI 融资")` + `search_notes(keyword="大模型")` 检索知识库
4. 发现用户有"AI 战略规划"笔记和"竞品分析"文档 → `read_note` 读取
5. 输出：新闻要点 + "你在'AI 战略规划'中提到关注 OpenAI 的 API 定价策略，这笔融资可能加速其降价节奏" + 行动建议

结果：新闻已存入笔记，用户收到个性化的深度分析。

### 示例 2：用户聊新闻话题

用户说：「DeepSeek 最近怎么样了」

操作：
1. `web_search("DeepSeek 最新动态 2026")` → 找到最权威报道 → `web_fetch` 抓取
2. 保存到笔记，打 `#新闻//AI` 标签
3. `search_notes(keyword="DeepSeek")` + `search_notes(keyword="开源模型")` 检索知识库
4. 发现用户之前保存过一篇"DeepSeek-V3 发布"的新闻 → 对比时间线
5. 输出：最新动态 + "对比你之前收藏的 DeepSeek-V3 报道..." + 趋势分析

结果：新闻已存入笔记，用户看到事件的发展脉络。

### 示例 3：批量搜索简报

用户说：「帮我搜一下今天的 AI 新闻」

操作：
1. 构造 2-3 组搜索查询，抓取最新 AI 新闻
2. 去重筛选出 5-8 条高价值条目
3. 创建/定位"新闻简报 2026-03-12"笔记
4. 写入分类简报（带链接和摘要）
5. 同步笔记

结果：当日 AI 新闻简报已写入笔记。

---

## MCP 调用模式

### 工作流 A

1. 搜索工具获取新闻 → 2. `search_notes` / `create_note` 定位笔记 → 3. `get_note_outline` → 4. `edit_block(op="insert")` → 5. `sync_note`

### 工作流 B

1. `web_fetch` / `web_search` 获取新闻 → 2. `create_note` → 3. `edit_block(op="insert")` 写入元信息 → 4. **分次** `edit_block(op="insert")` 追加正文（每次 3-5 段，用 `last_block_id` 做锚点） → 5. `sync_note` → 6. 多组 `search_notes` 检索知识库 → 7. `read_note` / `read_section` 读取关联 → 8. 输出 insight

始终遵循：定位 → 读取/刷新 → 写入。

## 异常处理

| 错误场景 | 处理方式 |
|----------|----------|
| `EDITOR_NOT_READY` / `FRONTEND_TIMEOUT` | 短暂等待后重试 |
| `BLOCK_NOT_FOUND` | `get_note_outline` 刷新后重试 |
| `DOCUMENT_READ_ONLY` | 停止写入，告知用户 |
| 搜索结果为空（A） | 回报"无新增"，不写入空内容 |
| 新闻获取失败（B） | 有链接回退 `web_search`；无链接扩大搜索；仍无则告知用户 |
| 知识库无关联（B） | 正常保存，给通用分析，提示"随着笔记积累分析会更精准" |
| 文章过长 | 分段写入；分析聚焦关键段落 |

## 资源

- [query-recipes.md](references/query-recipes.md)：新闻搜索的查询模板与来源过滤策略
- [knowledge-search-strategy.md](references/knowledge-search-strategy.md)：知识库检索的详细策略与示例
