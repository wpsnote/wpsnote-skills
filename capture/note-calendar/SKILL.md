---
name: note-calendar
description: 在 macOS 上打通 WPS 笔记与系统日历。支持查询日程、创建/移动/删除日历事件，以及笔记与日历的双向联动：把今日日程整理成笔记规划页、从笔记中提取事项落入日历、根据明日事件推断今日前置准备、全局时间块规划、收集散落各处的待办 checkbox。仅支持 macOS。当用户说「帮我查日程」「看看我的日历」「今天有什么安排」「日程写到笔记」「把笔记里的计划加进日历」「明天要出发今天准备什么」「帮我规划今天」「整理我的 TODO」时使用。
compatibility: 仅支持 macOS。日历操作依赖 bin/ 目录下的 cal-* 脚本（通过 osascript 调用 macOS Calendar App，兼容 iCloud、Exchange 等所有日历源）。笔记操作优先使用 wpsnote-cli，不可用时降级到 user-wpsnote MCP 服务。
metadata:
  author: Yicheng Xu
  version: "1.1.0"
  mcp-server: user-wpsnote
  tags: [calendar, schedule, wps-note, productivity, planning, macos]
---

# Note Calendar

## 前置检查（每次必须执行）

### 1. OS 检查

```bash
uname -s
```

返回不是 `Darwin` 则立即终止：`此 Skill 仅支持 macOS，当前系统不兼容。`

### 2. 笔记工具检查

```bash
wpsnote-cli status 2>/dev/null | grep -q "成功" && echo "CLI_OK" || echo "CLI_FAIL"
```

- `CLI_OK`：全程使用 `wpsnote-cli` 命令
- `CLI_FAIL`：降级到 `user-wpsnote` MCP 工具调用

确定模式后，后续所有笔记操作保持一致。

---

## 日历脚本（bin/）

所有脚本通过 `osascript` 操作 macOS Calendar App，首次运行因 iCloud 同步可能需要 30-60 秒。

```bash
# 查询
cal-query today                          # 今天
cal-query tomorrow                       # 明天
cal-query week                           # 本周（周一～周日）
cal-query next-week                      # 下周
cal-query +3                             # 3 天后当天
cal-query 2026-03-25                     # 指定日期
cal-query 2026-03-23 2026-03-29          # 指定范围
cal-query yesterday / last-week / weekend / ...  # 更多参数见脚本注释

# 写入（返回事件 UID，用于后续操作）
cal-add "<标题>" "<YYYY-MM-DD HH:MM>" "<YYYY-MM-DD HH:MM>"
cal-move <uid> "<YYYY-MM-DD HH:MM>" "<YYYY-MM-DD HH:MM>"
cal-delete <uid>

# 测试
cal-test        # 运行全量 CRUD 测试
```

---

## 功能模式

五种模式，根据用户说法自动判断：

| 用户说的话 | 进入模式 |
|-----------|---------|
| 「查日程」「今天有什么」「帮我看下周安排」 | **模式 A**：纯日历查询 |
| 「日程写到笔记」「今日规划」「帮我管今天日程」 | **模式 B**：日历 → 笔记 |
| 「根据笔记帮我加日程」「笔记里有 xxx 排进去」 | **模式 C**：笔记 → 日历 |
| 「明天要 xxx 今天要准备什么」「帮我前置一下」 | **模式 D**：智能前置 |
| 「帮我规划今天」「今天下午很满帮我排上午」 | **模式 E**：全局规划 |
| 「整理 TODO」「收集所有待办」 | **模式 F**：TODO 汇总 |
| 说法不明确 | 列出六个模式让用户选 |

> 笔记写入格式参考 `docs/note-templates.md`

---

## 模式 A：纯日历查询

直接调用 `cal-query`，返回结果格式化输出即可，不写笔记。

```bash
cal-query <参数>    # 根据用户描述选合适的参数
```

---

## 模式 B：日历 → 笔记

把今天日程整理成结构化规划页写入笔记。

1. 查询日程：
   ```bash
   cal-query today      # 今天
   cal-query tomorrow   # 明天（用于生成前置建议）
   ```

2. 对每个事件标题搜索关联笔记：
   - CLI：`wpsnote-cli find --keyword "<事件关键词>" --limit 3 --json`
   - MCP：`search_notes(keyword="<事件关键词>", limit=3)`

3. 确认写入位置：
   - CLI：`wpsnote-cli current --json` / MCP：`get_current_note()`
   - 有打开的笔记 → 询问「写入当前笔记，还是新建？」
   - 无 → 新建：`wpsnote-cli create --title "📋 今日规划 YYYY-MM-DD" --json`

4. 按 `docs/note-templates.md` 模式 B 结构写入

5. 输出摘要：`✓ 今日规划已写入「📋 今日规划 YYYY-MM-DD」｜日程 N 条 ｜ 关联笔记 N 篇`

---

## 模式 C：笔记 → 日历

从当前笔记提取有时间意图的内容，确认后写入日历。

1. 读取当前笔记：
   - CLI：`wpsnote-cli current --json` → `wpsnote-cli read --note_id <id> --json`
   - 大文档：`wpsnote-cli outline` + `wpsnote-cli search --query "计划|打算|明天|下周|时间"`
   - MCP：`get_current_note()` → `read_note` 或 `get_note_outline` + `search_note_content`

2. 识别可落日历的内容：
   - ✅ 明确时间 + 事项：「3月25日 15:00 产品评审」
   - ✅ 相对时间 + 事项：「下周二开周会」「明天下午复习」
   - ✅ TODO + 截止时间：`- [ ] 提交报告（周五前）`
   - ✅ 计划关键词：「计划明天...」「打算下周...」
   - ❌ 不识别：历史记录、数据里的时间（「版本 1.0 于 2024 年」）

3. 必须先确认，再写入：
   ```
   📌 在「[笔记标题]」中识别到以下可落日历的事项：
     1. ✅ 产品评审 — 2026-03-25 15:00-16:00
     2. ⚠ 时间模糊：「下周提交报告」— 请补充具体时间
   确认哪些写入日历？（回复「全部」或编号）
   ```

4. 写入：`cal-add "<标题>" "<start>" "<end>"`，成功后在笔记对应 block 追加标注

---

## 模式 D：智能前置

根据未来事件推断今天需要做的准备。

1. 拉取未来 3 天日程：`cal-query today` / `cal-query tomorrow` / `cal-query +2`

2. 识别触发词：

   | 关键词 | 推断准备事项 |
   |--------|------------|
   | 出行、旅游、飞机、高铁、出差 | 收拾行李、确认票务、备充电宝和证件 |
   | 考试、测验、exam | 复习相关笔记、准备文具、调好闹钟 |
   | 演讲、汇报、presentation | 整理材料、检查设备、演练一遍 |
   | 面试 | 查公司背景、准备自我介绍 |
   | 约会、聚餐、饭局 | 确认地点、查路线、预留出行时间 |

3. 搜索相关笔记：
   - CLI：`wpsnote-cli find --keyword "<事件关键词>" --limit 3 --json`
   - MCP：`search_notes(keyword="<事件关键词>", limit=3)`

4. 写入前置任务块（格式见 `docs/note-templates.md` 模式 D）

5. 询问是否追加到今天日历（可选）

---

## 模式 E：全局规划

综合日历和待办，给出完整今日时间分配建议。

1. 收集信息：
   ```bash
   cal-query today     # 固定时间块
   cal-query tomorrow  # 判断今晚是否要早休
   ```
   待办来源：优先读取用户已有的 TODO 笔记（见**跨笔记 TODO 提取**），作为「任务池」

2. 分析：
   - 计算空闲时段（固定事件之间的间隙）
   - 识别高负载时段（连续 3 个以上会议无间隙）
   - 标记适合深度工作的轻松时段

3. 按 `docs/note-templates.md` 模式 E 结构写入时间线规划

---

## 模式 F：TODO 汇总

收集散落各处的未完成 checkbox，整合到用户已有的 TODO 笔记。

**核心原则：跟着用户已有的 TODO 笔记走，绝不另起炉灶。**

见**跨笔记 TODO 提取**完整流程。

---

## 跨笔记 TODO 提取（通用流程）

模式 C、E、F 都依赖此流程。

### 第一步：找候选笔记

```bash
for kw in "任务" "计划" "记得" "需要" "安排"; do
  wpsnote-cli find --keyword "$kw" --limit 10 --json
done
```

合并去重，得到候选笔记列表。

### 第二步：提取 unchecked checkbox

```bash
wpsnote-cli read --note_id <id> --json > /tmp/note_<id>.json
```

```python
import re, json
with open('/tmp/note_<id>.json', encoding='utf-8') as f:
    content = json.load(f)['data']['content']
todos = re.findall(
    r'<p\s[^>]*listType="todo"[^>]*checked="0"[^>]*>(.*?)</p>',
    content, re.DOTALL
)
items = [re.sub('<[^>]+>', '', t).strip() for t in todos if t.strip()]
```

- `checked="0"` = 未完成，只收集这类
- 与笔记标题命名无关，直接识别 checkbox 格式

MCP 降级：`read_note(note_id)` 获取内容后同样解析

### 第三步：确定写入目标（先找，再问，绝不新建）

```bash
wpsnote-cli find --keyword "TODO" --limit 10 --json
wpsnote-cli find --keyword "待办" --limit 10 --json
wpsnote-cli find --keyword "任务清单" --limit 5 --json
```

找标题含「TODO / 待办 / 任务清单 / 清单」的笔记：

- **找到 1 篇**：直接用，写入前告知：`将把待办写入你已有的「[笔记标题]」`
- **找到多篇**：列出让用户选
- **一篇都没有**：才询问是否新建

### 第四步：按用户已有格式写入

先读目标笔记前 30 个 block，观察组织方式（按周/按项目/平铺），追加内容跟着走，不引入新结构。

来自其他笔记的条目附上来源备注：
```xml
<p><span fontColor="#757575">↑ 来自「[原笔记标题]」</span></p>
```

---

## 工具速查

### 日历（macOS 独占）

| 操作 | 命令 |
|------|------|
| 查日程 | `cal-query <today\|tomorrow\|week\|+N\|YYYY-MM-DD>` |
| 创建事件 | `cal-add "<title>" "<YYYY-MM-DD HH:MM>" "<YYYY-MM-DD HH:MM>"` |
| 移动事件 | `cal-move <uid> "<YYYY-MM-DD HH:MM>" "<YYYY-MM-DD HH:MM>"` |
| 删除事件 | `cal-delete <uid>` |

### 笔记（CLI 优先 / MCP 降级）

| 操作 | CLI | MCP |
|------|-----|-----|
| 连接检查 | `wpsnote-cli status` | — |
| 当前笔记 | `wpsnote-cli current --json` | `get_current_note()` |
| 搜索笔记 | `wpsnote-cli find --keyword "..." --limit N --json` | `search_notes(keyword=..., limit=N)` |
| 搜索内容 | `wpsnote-cli search --note_id <id> --query "..." --json` | `search_note_content(note_id, query=...)` |
| 读取全文 | `wpsnote-cli read --note_id <id> --json` | `read_note(note_id)` |
| 读取大纲 | `wpsnote-cli outline --note_id <id> --json` | `get_note_outline(note_id)` |
| 新建笔记 | `wpsnote-cli create --title "..." --json` | `create_note(title=...)` |
| 编辑 block | `wpsnote-cli edit --note_id <id> --op insert/replace ...` | `edit_block(note_id, op=..., ...)` |

---

## 错误处理

| 错误 | 处理 |
|------|------|
| OS 不是 macOS | 立即终止，提示仅支持 macOS |
| `wpsnote-cli status` 失败 | 降级到 MCP；MCP 也不可用则提示检查笔记服务 |
| `NO_ACTIVE_EDITOR_WINDOW` | 询问写入哪篇笔记，或新建 |
| `BLOCK_NOT_FOUND` | 重新获取大纲刷新 ID 后重试一次 |
| `cal-query` 超时 | 提示日历同步中，等待后重试（首次可能需要 60s） |
| `cal-add` 失败 | 打印错误，询问是否手动指定日历名 |
| 笔记搜索无结果 | 跳过关联步骤，仅处理日历数据本身 |
