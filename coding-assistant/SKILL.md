---
name: coding-assistant
description: 多平台编码助手。遵循各平台官方文档做编码规范、单测与编译/lint；协助将核心技术梳理为完整 WPS 笔记技术文档。生成的笔记必须包含 7 个二级标题（核心技术、核心代码、关键技术点、核心类和职责、调用链、架构概览、注意事项）；其中架构、核心技术、调用链的图示优先用 WPS 笔记的 generate_image 根据描述生成图片再用 insert_image 插入。用户新增标题时根据诉求补充内容；用户未关闭当前笔记期间约 1 分钟后主动更新直至关闭。当用户使用 Cursor、Codex、Claude Code、AS code 且提到架构、设计图、核心方法、关键技术或技术文档时，自动读写在 WPS 笔记。先 list_notes 先查后编；核心代码可从注释、复制、剪切板、选中或指定函数获取。子 skill review-notes 与 reference 负责流程细节。每30s监控一个笔记内容是否变动，如果变动自动更新文档。
---

# Coding Assistant（编码助手）

在 Cursor 中编写或审查**多平台**代码时，统一遵循**各平台官方文档**与项目约定。保存为 `SKILL.md` 放到 `~/.cursor/skills/coding-assistant/` 或项目 `.cursor/skills/` 即可生效。

**参考文档（优先以官网为准）：**

- **Android**：遵循 Android 官方标准。Android 开发者（中文）<https://developer.android.com/?hl=zh-cn>；Jetpack Compose <https://developer.android.com/develop/ui?hl=zh-cn>。
- **iOS**：遵循 iOS 官方文档标准。Apple Developer（开发文档、Swift、UIKit/SwiftUI）<https://developer.apple.com/documentation/>；Swift <https://swift.org/documentation/>。
- **其他语言 / 框架**：优先参考该语言或框架的**官网文档**（如 Rust、Python、Go、React、Vue 等以各自官网与官方风格为准）。

## 二、编码规范与参考

- 以**当前项目所用平台/语言**的官方文档为第一参考；无明确规范时保持与项目现有风格一致。
- **文件头**：新建文件顶部需包含功能简介、作者、日期、版本（格式按该语言惯例，如 JSDoc、KDoc、Swift 注释等）。
- **命名与注释**：与类/模块职责相关；重要函数注明「做什么」与「为什么这样实现」；职责分离，无关逻辑抽到独立模块。

## 三、新建文件头

按当前语言惯例，在文件顶部包含：功能简介、作者、日期、版本。示例（类 C/Java 风格）：

```text
/**
 * 功能：xxx 模块的 ViewModel，负责 UI 状态与业务逻辑。
 * 作者：Your Name
 * 日期：2025-03-12
 * 版本：1.0.0
 */
```

Swift / 其他语言可采用对应注释风格。

## 四、类与函数规范

- **命名**：与类/模块职责相关，优先使用类名简写或约定前缀。
- **注释与原理**：重要函数说明「做什么」及「为什么这样实现」。
- **职责分离**：与当前类/模块无关的逻辑抽到独立 Util、Handler、Repository 或等价模块。

## 五、单文件/单类长度

单文件或单类长度不超过 3000 行（或按项目约定）。超过时通过拆分类、提取模块、扩展函数等方式拆分。

## 六、开发结束后的检查

- **Android**：运行 `./gradlew assembleDebug`（或项目约定任务）、`./gradlew lint`；失败时根据报错修改后重试。
- **iOS**：使用 Xcode 构建及静态分析（或 `xcodebuild`、SwiftLint 等按项目约定）；失败时根据报错修改后重试。
- **其他**：按项目约定的编译、lint、格式化命令执行，直至通过。

## 七、开发过程中的单元测试

- 为新增或修改的类/函数编写单元测试（JUnit、XCTest、pytest 或项目已有框架）。
- 运行测试（如 `./gradlew test`、`xcodebuild test`、`pytest` 等），确保相关测试通过。
- **落盘策略**：仅在单元测试通过后，再将本次改动写入磁盘；未通过则先修复再保存。

## 十、核心技术文档与笔记

在编码过程中协助梳理核心技术，并调用 **create_note** 能力将技术笔记写入 **WPS 笔记**。完整流程（含先查后编、mermaid 调用链、核心代码来源、等待用户指令直接辅助等）见子 skill [review-notes](review-notes/SKILL.md) 与 [reference/reference.md](reference/reference.md)。与 WPS 协作时：优先 **get_current_note**；编辑前 **get_note_outline** 取最新 block_id，编辑后 **sync_note**；遇 BLOCK_NOT_FOUND 则刷新 outline 后重试；多步编辑尽量用 **batch_edit**。详见 reference §7。以下为要点摘要。

**何时启动 WPS 笔记技术文档**（满足其一即启动读取与写入 WPS 笔记、生成技术文档）：

- **编码工具 + 关键词**：用户使用 **Cursor、Codex、Claude Code、AS code** 等编码工具进行**编写、审查或优化代码**时，且用户提到「**架构**」「**设计图**」「**核心方法**」「**关键技术**」或「技术文档」「记入笔记」等时，自动读取当前文件/工程上下文并写入 WPS 笔记，生成或更新技术文档。
- **用语/场景**：审阅代码、技术文档、总结关键代码、记录关键技术点、记入笔记、生成技术文档；或类/函数注释中出现「生成技术文档」；或代码涉及复杂场景（多线程/协程、JNI/NDK、复杂状态与导航、性能优化、安全与加密等）时视情况纳入。

**完整笔记结构**：生成的 WPS 笔记**必须完整**，且**必须包含**以下 7 个二级标题：**核心技术**（须配图）、**核心代码**、**关键技术点**、**核心类和职责**、**调用链**（mermaid，并可配图）、**架构概览**（须配图）、**注意事项**。详见 reference §0.2。

**架构 / 核心技术 / 调用链配图**：优先使用 **WPS 笔记的 generate_image** 根据调用链描述、架构描述、核心技术描述生成图片，再用 **insert_image** 插入笔记；若 generate_image 不可用，则用 mermaid 或从官网/掘金/维基 insert_image。详见 reference §2.1。

**保存前**：先 **list_notes** 查看已有技术文档；再 **create_note**（或先查后编，匹配则直接编辑不新建）并将内容写入该笔记。

**调用链**：笔记中的「调用链」须用 **mermaid** 格式（flowchart 或 sequenceDiagram）；可同时用 generate_image 根据调用链描述生成示意图并用 insert_image 插入。

**核心代码**（满足任一即纳入笔记）：(1) **注释内关键字**：注释中出现「核心代码」「关键实现」「技术要点」「生成技术文档」等时，读取对应行/块或函数体。(2) **用户复制的代码块**：用户选中并复制后告知（如「已复制」「这段是核心代码」）。(3) **剪切板中的代码块**：用户告知剪切板已粘贴代码；若无法读取剪切板则从当前文件提取最相关函数/块作为备选。(4) **本文件选中代码**。(5) **指定函数**：取该函数完整函数体。写入笔记时用 insert_block/replace_block 以代码块形式写入。

**用户新增标题**：当用户在笔记中添加新二级标题或其他小标题时，**根据用户诉求**在该标题下补充相应内容（insert_block）。**主动更新**：在用户未关闭当前笔记期间，**约 1 分钟后**或适当时机**主动刷新并更新**该笔记（如补充小节、更新调用链/核心代码等），**直至用户主动关闭当前笔记**。详见 reference §0.3、§0.4、§7。

**标签**：笔记完成后调用 **list_tags** 按用户风格生成核心标签或输出建议标签。

## 八、元数据与结构参考

Skill 元数据与目录结构可参考：<https://github.com/Drjacky/claude-android-ninja/tree/master>（含 SKILL.md、references、templates）。

## 九、何时使用本 Skill

在用户进行 **Android / iOS / 其他语言** 开发、代码评审、新增文件、重构或询问各平台官方规范时，自动应用本 Skill。**WPS 笔记技术文档**：当用户使用 Cursor、Codex、Claude Code、AS code 等编码工具进行编写、审查或优化代码，且用户提到「架构」「设计图」「核心方法」「关键技术」或「技术文档」「记入笔记」等时，自动启动读取与写入 WPS 笔记、生成或更新技术文档（先 list_notes 查已有笔记，匹配则编辑不新建）；涉及的核心代码可从注释内关键字、用户复制的代码块、剪切板中的代码块、选中代码或指定函数体获取。开发过程中单元测试通过后才落盘；开发结束后协助执行该平台的编译与 lint。与 WPS 协作时遵循 get_current_note、get_note_outline、sync_note、batch_edit 等规则。
