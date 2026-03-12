# 查询模板

使用这些模板从搜索工具中拿到高信噪比的新闻结果。

## 基础模板

- `"{topic} 新闻 过去24小时"`
- `"{topic} 今日 资讯 深度"`
- `"{topic} breaking news today"`

## 来源约束模板

为提升质量，在搜索词后追加来源约束：

- `site:36kr.com OR site:ifanr.com OR site:infoq.cn`
- `site:caixin.com OR site:thepaper.cn OR site:stcn.com`
- `site:reuters.com OR site:bloomberg.com OR site:ft.com`

示例：

`AI 芯片 新闻 过去24小时 site:reuters.com OR site:bloomberg.com`

## 主题组合

### AI

- `大模型 新闻 过去24小时 site:36kr.com OR site:infoq.cn`
- `AI agent 今日 资讯 site:theverge.com OR site:techcrunch.com`

### Finance

- `美联储 利率 新闻 今日 site:reuters.com OR site:ft.com`
- `A股 行业 政策 新闻 过去24小时 site:stcn.com OR site:caixin.com`

### Semiconductor

- `半导体 产能 新闻 过去24小时 site:digitimes.com OR site:eejournal.com`
- `NVIDIA AMD 芯片 新闻 今日 site:reuters.com OR site:bloomberg.com`

## 筛选规则

- 优先保留标题或摘要中带明确时间信息的新闻。
- 优先一手报道，弱化搬运与二次转载。
- 去掉无标题或摘要不可读的链接。
- 每期简报控制在 5-10 条，避免笔记过长。
