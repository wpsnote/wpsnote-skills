---
name: xiaohongshu-note-creator
description: |
  【笔记/文章转小红书】将用户已有的 WPS 笔记或文章内容，改写压缩为小红书图文方案。
  核心特征：用户已有原文内容（笔记、文章、推文、长文），需要转换格式发小红书。
  触发词："把笔记做成小红书""把这篇文章转小红书""把这篇推文发小红书""帮我生成小红书图文""把这篇笔记发小红书""笔记转小红书""小红书图文""生成小红书""这篇文章改成小红书""这个内容发小红书"。
  不适用于：从0到1写内容（用 content-creator）、纯文案排版（用 wechat-publisher）、没有已有内容只想"写小红书"（用 content-creator）。
metadata:
  version: "1.1.0"
  category: content-creation
  tags: [xiaohongshu, note, image, copywriting]
  dependencies: [wps-note, image-gen]
  scripts:
    - comm_script/image_gen.py
---

# Xiaohongshu Note Creator - 笔记转小红书图文

> **脚本路径说明**：本 Skill 依赖的 `image_gen.py` 位于此 SKILL.md **同目录的 `scripts/` 下**。
> AI 执行前，先确认脚本存在：`ls {SKILL所在目录}/scripts/image_gen.py`
> 运行命令时指定路径：`python3 {SKILL所在目录}/scripts/image_gen.py ...`

将 WPS 笔记内容转化为完整的小红书图文方案，包含每页图文、AI 配图和话题标签。

---

## 铁律（最高优先级）

### 0. 读图（必须在 Step 2 之前完成）

调用 `outline` 找出所有图片 block，逐张调用 `read-image` 读取并做视觉描述，记录每张图的画面内容、风格色调、适合用于哪页。

```bash
wpsnote-cli outline --note_id {note_id} --json
wpsnote-cli read-image --note_id {note_id} --block_id {block_id} --json
```
MCP 降级：`read_image({ note_id, block_id })`

读取完成后，在对话中汇报：「原文共 N 张图，图1 [画面描述]，适合 P{页码}；图2...」

原文无图时：说「原文无图」，继续。

---

### 1. 所有输出必须写入 WPS 笔记，禁止在对话中直接输出正文
- 禁止在对话消息里输出任何图文内容、文案正文、标签列表
- **唯一合法的输出方式**：通过 `create_note` + `batch_edit` / `edit_block` 写入 WPS 笔记
- 写入成功后对话中只说：笔记标题、页数、一句话摘要、「已写入笔记」
- 违反以上任一条，立刻停止并重新通过工具写入

### 2. 提问必须附备选项
对话中只能做两件事：**提问** + **状态通知**。
- 提问时必须附上 2-4 个备选选项
- 状态通知：调用工具前一句话告知正在做什么

### 4. 文案必须忠于原文（最容易犯错，最高优先级）

**核心原则：这是一个"改写压缩"任务，不是"重新创作"任务。**

- **每页正文必须来自原文对应章节的真实内容**，不得 AI 自由发散补充
- **直接改写原文段落**为口语化小红书风格，核心观点、数据、例子必须与原文一致
- **优先保留原文金句**，如"整理是 AI 的事，思考是用户的事"、"往里扔就行"等
- **每页对应原文哪个章节必须明确**（规划时就标注，如"P2 → 原文 01 笔记软件的周期律"）

**严禁的行为：**
```
❌ 用自己的话"总结"原文，丢失具体细节
❌ 添加原文没有的观点、类比、案例
❌ 用通用小红书套话替换原文独特表达
❌ 把多个不相关章节内容混写成一页
```

### 5. 生图必须优先使用原文图片垫图

**有原文图片时，禁止直接文生图：**
1. Step 2 读取源笔记时，必须扫描所有 `image` block，优先用 CLI 读取 base64 并**立刻用视觉理解描述图片内容**（见 Step 2 第 3 步）：
   ```bash
   wpsnote-cli read-image --note_id {note_id} --block_id {block_id} --json
   # 返回 data.image_base64 字段
   ```
   MCP 降级：`read_image({ note_id, block_id })`
2. 生图时，根据页面内容就近选取一张原文图片作为垫图：
   ```bash
   # 先将 base64 保存为临时文件
   python3 -c "import base64; open('/tmp/ref_pN.jpg','wb').write(base64.b64decode('{data.image_base64}'))"
   # 再传入 --image
   python3 scripts/image_gen.py ... --image /tmp/ref_pN.jpg
   ```
3. **视觉描述（prompt）必须基于图片的真实画面来写**，不是凭空编写氛围图：
   ```
   ✅ 原图是：男生坐在电脑前，周围漂浮着笔记软件图标，困惑表情，线条插画风
      → prompt：年轻男生坐在书桌前，Notion/Obsidian图标环绕飘散，眉头紧皱，同款线条插画风，奶油色调，竖版构图
   ❌ 凭空写：温馨书房，女生整理笔记，日系风格（完全不参考原图）
   ```
4. 只有在以下情况才允许纯文生图：
   - 原文没有图片
   - provider 是 dashscope（不支持垫图）
   - provider 是 ark（即梦）且只有本地图片（ark 只支持公网 URL）

### 3. WPS 笔记写入规范（违反必报错）

**`batch_edit` operations 字段名必须是 `op`，不是 `type`：**
```
✅ { "op": "insert", "anchor_id": "...", "position": "after", "content": "..." }
❌ { "type": "insert", ... }
```
`op` 合法值只有：`replace` / `insert` / `delete` / `update_attrs`

**`insert` 的 `position` 只能是 `"before"` 或 `"after"`，`anchor_id` 必须是真实 block id，不能为 null：**
```
✅ { "op": "insert", "anchor_id": "aB3kLm9xZq", "position": "after", "content": "..." }
❌ { "op": "insert", "anchor_id": null, "position": "begin", ... }
❌ { "op": "insert", "anchor_id": null, "position": "end", ... }
```
**想在笔记末尾追加**：先 `get_note_outline` 取最后一个 block 的 id → `anchor_id` 填该 id，`position` 填 `"after"`

**content 必须是纯 XML 字符串，不是数组、不是自然语言：**
```
✅ content: "<h2>封面页（P1）</h2><p>内容...</p>"
❌ content: [{"type": "text", "text": "..."}]
❌ content: "把第二段改成..."
```

**多段内容一次性拼入，不要分多次 insert：**
```
✅ 一次 insert，content 里拼多个块级标签
❌ 每个块单独 insert 一次（容易乱序、锚点失效）
```

**连续追加时用 last_block_id 做链式锚点（必须分批时）：**
```
第一次 insert → 返回 last_block_id: "id_A"
第二次 insert → anchor_id 用 "id_A"，不要重新 outline
```

---

## 核心流程

```
加载偏好 → 读取源笔记 → 分析内容 → 规划图文结构 → 生成各页文案 → 逐页生图 → 生成标签 → 确认是否更新偏好
```

---

## Step 1：加载偏好

使用 `search_notes` 搜索关键词 `小红书创作偏好`。

- **找到偏好笔记** → 读取并提取偏好参数，告知用户：
  ```
  已加载小红书偏好：风格={风格} | 页数={页数} | 字数/页={字数} | 话题方向={方向}
  ```
- **未找到偏好笔记** → 进入 [首次配置流程](#首次配置流程)

---

## Step 2：读取源笔记

询问用户：
> "请告诉我要转换哪篇笔记的标题或 ID，我来帮你生成小红书图文方案。"

获取笔记标识后：
1. 使用 `search_notes` 或 `get_note_outline` 定位笔记
2. 使用 `read_note` 读取完整内容
3. **扫描并理解原文图片（重要）**：
   - 调用 `get_note_outline` / `wpsnote-cli outline --note_id {id} --json` 找出所有 `image` 类型的 block
   - 对每张图片，优先用 CLI 读取（降级用 MCP）：
     ```bash
     wpsnote-cli read-image --note_id {note_id} --block_id {block_id} --json
     ```
     MCP 降级：`read_image({ note_id, block_id })`
   - **读到 base64 后，立刻用视觉理解描述这张图的画面内容**，记录格式：
     ```
     图片1：block_id=xxx，位置第N页附近
       画面内容：{描述图里有什么：人物/场景/元素/布局}
       风格色调：{插画/摄影/扁平/日系/科技感/色调}
       可用于：P{页码}（与该页主题最相关）
     ```
   - 没有图片 → 记录"无原文图片，使用纯文生图"
4. 分析以下要素：
   - 核心主题（1句话）
   - 关键知识点（3-7个）
   - 内容类型（干货教程 / 经验分享 / 知识科普 / 情感故事）
   - 受众画像（初学者 / 有经验者 / 特定人群）
   - 适合转化的亮点

告知用户：「已读取笔记《{标题}》，识别为「{内容类型}」，核心是「{主题}」。原文含 {N} 张图片，将优先用于垫图生成配图。」

---

## Step 3：规划图文结构

根据内容类型和偏好中的页数设置，规划每页主题：

### 标准图文结构（推荐 6-9 页）

| 页码 | 类型 | 作用 |
|------|------|------|
| P1 | **封面页** | 标题 + 核心钩子，让人点进来 |
| P2-PN-1 | **内容页** | 每页一个知识点/步骤/亮点 |
| PN | **结尾页** | 总结/金句 + 引导互动（点赞/收藏/评论） |

### 页数建议

| 内容类型 | 推荐页数 |
|---------|---------|
| 干货教程 | 7-9 页（步骤拆解） |
| 经验分享 | 6-7 页（故事 + 提炼） |
| 知识科普 | 6-8 页（概念 + 案例） |
| 情感故事 | 5-6 页（节奏紧凑） |

规划完成后，调用 `create_note` 新建笔记（标题：`{源笔记标题} - 小红书图文`），用 `batch_edit` 写入规划结构（仅占位）后告知用户页数分配，**不等用户确认直接继续**。

> 规划每页主题时，**必须标注对应原文的章节或段落**（如"P2 → 原文 01 笔记软件的周期律"），确保每页都有原文锚点，不得无中生有。

---

## Step 4：生成图文内容

### 写入前必须做的准备

1. 调用 `get_note_outline(note_id)` 获取当前 block 结构，记录最后一个 block 的 id 作为首次 `anchor_id`
2. **将所有页面内容一次性拼成完整 XML 字符串**，用一次 `edit_block` 的 `insert` 写入，避免分多次调用导致乱序或 block_id 失效
3. 如必须分批写入：每次 insert 后取返回的 `last_block_id` 作为下次的 `anchor_id`，**禁止复用旧 id**

### 每页内容结构

每页包含：
- **页面标题**：6-12 字，醒目有力，**必须提炼自原文，不得自造**
- **正文文案**：根据偏好字数/页，口语化改写原文，**禁止凭空发挥**（见铁律第 4 条）
- **视觉描述**（生图 prompt）：主体 + 场景 + 风格 + 色调，**优先参考原文图片风格**（见铁律第 5 条）

### 写入笔记的完整结构

```xml
<h1>{源笔记标题} - 小红书图文</h1>
<p><tag>#小红书</tag></p>
<p>来源笔记：{标题} | 页数：{N}页 | 风格：{风格}</p>

<h2>封面页（P1）</h2>
<p><strong>页面标题：</strong>{封面标题，12字以内，有爆款感}</p>
<p><strong>副标题：</strong>{副标题/钩子句，20字以内}</p>
<p><strong>视觉描述：</strong>{生图prompt}</p>
<p><strong>配图：</strong>生成中…</p>

<h2>内容页 P2：{页面主题}</h2>
<p><strong>页面标题：</strong>{标题}</p>
<p><strong>正文：</strong>{内容文案}</p>
<p><strong>视觉描述：</strong>{生图prompt}</p>
<p><strong>配图：</strong>生成中…</p>

<!-- 更多内容页… -->

<h2>结尾页（PN）</h2>
<p><strong>页面标题：</strong>{金句或总结}</p>
<p><strong>正文：</strong>{互动引导文案，如：觉得有用就收藏吧～}</p>
<p><strong>视觉描述：</strong>{生图prompt}</p>
<p><strong>配图：</strong>生成中…</p>

<h2>发布文案</h2>
<p><strong>标题：</strong>{发布标题，含关键词，≤20字}</p>
<p><strong>正文：</strong>{完整发布正文，200-500字，首行必须吸引眼球}</p>
<p><strong>话题标签：</strong></p>
<p>{标签1} {标签2} {标签3} … （8-15个）</p>

<h2>推荐发布时间</h2>
<p>{工作日 / 周末} {上午 / 午休 / 晚间}，约 {具体时段}</p>
```

写入后告知：「图文方案已写入，共 {N} 页。」然后进入 Step 5 检查生图 Key。

---

## Step 5：逐页配图

### 铁律6：生图 Key 检查（必须在所有生图之前执行一次）

如果偏好中已设置外部 provider：
1. 搜索笔记库中标题含 `图像生成 Key` 的笔记，找到对应 provider 的 `ciphertext_b64`
2. 找到 → 用 **note 模式**（`--key note:{笔记ID} --ciphertext {密文}`）
3. 找不到 → 停下来，询问用户：

```
没有找到你的 {provider} Key，无法生图。请选择：
A. 现在提供 Key（可选择是否保存到笔记）
B. 跳过配图，只保留文案方案
```

**严禁静默降级到内置工具**，必须等用户明确选择后才能继续。

---

### 每页配图决策（按此顺序判断，不可跳过）

```
铁律0 已读取到该页原文图片（read-image base64）？
├─ 是 → provider 支持垫图（openrouter / gemini）？
│        ├─ 是 → 【方式A】原图 + 文案 → 排版生图
│        └─ 否（ark / dashscope）→ ⛔ 跳过，该页不配图，占位文字保留
└─ 否（原文无图）→ 【方式B】纯文生图（兜底）
```

- **ark / dashscope 遇到有原图的页面：直接跳过，不降级文生图，不生任何图**
- 用户明确说"重新生图""不用原图"→ 才允许对该页改用方式B

---

### 【方式A】原图 + 文案 → 排版生图（首选）

**核心思路**：把原文图片 + 当页文案同时传给生图 AI，AI 直接输出排好版的小红书竖版卡片图。AI 拿着你的图、拿着你的文，负责排版。

**执行步骤**：

```bash
# Step 1：将 read-image 取到的 base64 存为临时文件
python3 -c "
import base64
data = '{从read-image取到的完整base64字符串}'
with open('/tmp/ref_p{页码}.jpg', 'wb') as f:
    f.write(base64.b64decode(data))
print('saved')
"

# Step 2：把原图 + 排版文案一起传给生图 AI
python3 scripts/image_gen.py \
    --provider "{偏好provider}" \
    --model "{对应模型，见下表}" \
    --key "note:{key笔记id}" --ciphertext "{密文}" \
    --image /tmp/ref_p{页码}.jpg \
    --prompt "小红书竖版卡片排版，3:4 比例。
页面标题（大字居中）：{当页标题}
正文内容：{当页文案，不超过80字}
风格：参考输入图片的画风、色调和视觉元素，保持一致。
要求：文字清晰可读，留白充足，符合小红书视觉审美。" \
    --aspect "3:4" \
    --out "./output"
```

provider 对应模型（硬编码，不可修改）：

| provider | 模型 | 是否支持本地文件垫图 |
|----------|------|------------------|
| openrouter | `google/gemini-3.1-flash-image-preview` | ✅ 支持 |
| gemini | `gemini-3-pro-image-preview` | ✅ 支持 |
| ark（即梦） | `doubao-seedream-5-0-260128` | ❌ 不支持 → 跳过该页 |
| dashscope | `qwen-image-2.0-pro` | ❌ 不支持 → 跳过该页 |

---

### 【方式B】纯文生图（原文无图时使用）

原文该页本身没有图片 / 用户明确要求重新生图时使用。ark / dashscope 用户有原图的页面不走此路径。

```bash
python3 scripts/image_gen.py \
    --provider "{偏好provider}" \
    --model "{对应模型}" \
    --key "note:{key笔记id}" --ciphertext "{密文}" \
    --prompt "小红书竖版卡片排版，3:4 比例。
页面标题（大字居中）：{当页标题}
正文内容：{当页文案，不超过80字}
视觉风格：简约插画风，奶油色调
要求：文字清晰可读，留白充足，符合小红书视觉审美。" \
    --aspect "3:4" \
    --out "./output"
```

**内置工具降级（image_gen.py 无法使用时）**：
```bash
wpsnote-cli gen-image \
    --prompt "{排版指令+文案}" \
    --width 1080 --height 1350 --json
```
或 MCP：`generate_image({ prompt: "...", width: 1080, height: 1350 })`

> ⚠️ 内置工具限速每分钟 1 张，多页生成前告知用户预计耗时（页数 × 约 60 秒）

### 配图回填步骤

每张图生成后按以下顺序执行：

**1. 获取图片 URL**
- `image_gen.py` 生图：从 `[saved] {路径}` 取本地路径，作为 `--src` 传入
- `wpsnote-cli gen-image` 生图：从 JSON 输出取 `data.image_url`，直接作为 URL 传入

**2. 刷新 outline 获取 anchor_id**
```bash
wpsnote-cli outline --note_id "{笔记ID}" --json
```
找到"配图：生成中…"所在段落对应的 block_id 作为 `anchor_id`（在写入笔记结构时已记录各页"配图"占位块的位置，取其上一个 block 的 id 作为 anchor）。

**3. 插入图片（优先 CLI）**
```bash
wpsnote-cli insert-image \
    --note_id "{笔记ID}" \
    --anchor_id "{占位段落的前一个block_id}" \
    --position "after" \
    --src "{URL或本地路径}" \
    --json
```

**4. 删除占位段落**
插入成功后，用 `edit_block` delete 删除"配图：生成中…"的占位段落。

**5. 降级：CLI 失败则用 MCP**
```
insert_image({ note_id: "...", anchor_id: "...", position: "after", src: "..." })
```

> ⚠️ `insert-image` 要求笔记在 WPS 编辑器中打开，否则报 `INTERNAL_ERROR`。遇到此错误提示用户打开笔记后重试。

每张完成后说：「第 {N} 张配图（{页面类型}）已写入」。全部完成后说：「共 {N} 页配图已全部写入笔记《{笔记标题}》。」

---

## Step 6：确认是否更新偏好

询问：「这次用的是「{风格}」风格，{N} 页方案。有需要调整的参数吗？A. 更新偏好 B. 不用」

- 用户说更新 → `edit_block` 整表替换偏好笔记，完成后说「偏好已更新」
- 用户说不用 → 结束

---

## 首次配置流程

未找到偏好笔记时，询问：

```
我没找到你的小红书创作偏好，先配置一下：

1. 内容风格？（知识干货 / 生活分享 / 情感共鸣 / 时尚美妆）
2. 默认页数？（6页 / 8页 / 10页 / 自动判断）
3. 每页字数？（50字以内 / 80字左右 / 100字以上）
4. 主要话题方向？（如：职场/读书/设计/健康/育儿/...）
5. 图片风格偏好？（插画风 / 摄影风 / 信息图表风 / 自动匹配）
6. 生图服务商？（openrouter需代理 / dashscope百炼国内直连 / ark即梦国内直连 / gemini需代理 / 用内置工具）
```

收到后：
1. 调用 `create_note` 创建标题 `小红书创作偏好` 的笔记
2. 将偏好以表格写入（见下方模板）
3. 告知「偏好已保存，下次自动加载」
4. 继续执行 Step 2

### 偏好笔记模板

```xml
<h1>小红书创作偏好</h1>
<p><tag>#小红书</tag></p>
<table>
  <tr>
    <td><p><strong>配置项</strong></p></td>
    <td><p><strong>当前值</strong></p></td>
    <td><p><strong>可选项</strong></p></td>
  </tr>
  <tr>
    <td><p>内容风格</p></td>
    <td><p>{风格}</p></td>
    <td><p>知识干货 / 生活分享 / 情感共鸣 / 时尚美妆</p></td>
  </tr>
  <tr>
    <td><p>默认页数</p></td>
    <td><p>{页数}</p></td>
    <td><p>6页 / 8页 / 10页 / 自动判断</p></td>
  </tr>
  <tr>
    <td><p>每页字数</p></td>
    <td><p>{字数}</p></td>
    <td><p>50字以内 / 80字左右 / 100字以上</p></td>
  </tr>
  <tr>
    <td><p>话题方向</p></td>
    <td><p>{方向}</p></td>
    <td><p>职场 / 读书 / 设计 / 健康 / 育儿 等</p></td>
  </tr>
  <tr>
    <td><p>图片风格</p></td>
    <td><p>{图片风格}</p></td>
    <td><p>插画风 / 摄影风 / 信息图表风 / 自动匹配</p></td>
  </tr>
  <tr>
    <td><p>生图服务商</p></td>
    <td><p>{provider}</p></td>
    <td><p>openrouter / dashscope（百炼） / ark（即梦） / gemini / 内置工具</p></td>
  </tr>
</table>
```

---

## 话题标签生成规则

生成 8-15 个标签，分三层：

| 层级 | 数量 | 示例 |
|------|------|------|
| 核心话题（大流量） | 2-3 个 | `#读书笔记` `#学习方法` |
| 内容话题（中流量） | 4-6 个 | `#高效阅读` `#知识管理` `#笔记整理` |
| 长尾话题（精准流量） | 2-4 个 | `#{内容具体关键词}` |

---

## 常见问题处理

| 场景 | 处理方式 |
|------|---------|
| 源笔记内容太少（<200字） | 提示用户：内容较少，将尽量丰富延伸，是否继续 |
| 源笔记内容太多（>5000字） | 用 `search_note_content` 定位核心段落，提炼后转化 |
| 用户要求减少页数 | 合并相近主题的页，保留最核心的知识点 |
| image_gen.py 生图失败 | 自动降级到 `wpsnote-cli gen-image`，再失败降级到 MCP |
| 所有生图均失败 | 保留"视觉描述"文字占位，告知用户可手动配图 |
| 偏好未设置 provider | 直接用内置工具生图，提示用户可在偏好中配置外部服务商 |
| 用户说「风格不对」 | 询问具体调整方向：配色/插画/文字排版/情绪 |
