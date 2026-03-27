---
name: coding-assistant
description: "Multi-platform coding assistant that enforces official coding standards and automatically generates structured technical documentation in WPS Notes. Use when the user is writing, reviewing, or refactoring code in any language and mentions architecture, design diagrams, core methods, key techniques, or technical documentation — produces a WPS note with 7 required sections including architecture overview, call chains, and core code."
---

# Coding Assistant（编码助手）

Multi-platform coding assistant that enforces official platform standards and generates structured technical documentation in WPS Notes. Works with Cursor, Codex, Claude Code, AS Code, and other agent-based coding tools.

## When to activate

- User mentions **architecture**, **design diagrams**, **core methods**, **key techniques**, **technical documentation**, "记入笔记", or "生成技术文档"
- Code involves complex scenarios: concurrency, JNI/NDK, state management, performance optimization, or security

## Coding standards

Follow the **official documentation** for the current platform/language as the primary reference. When no explicit standard exists, match the project's existing style.

| Area | Rule |
|------|------|
| **File headers** | New files include: purpose, author, date, version (format per language convention) |
| **Naming** | Aligned with class/module responsibility; use established prefixes |
| **Comments** | Important functions document "what it does" and "why this approach" |
| **Separation of concerns** | Unrelated logic extracted to Util, Handler, Repository, or equivalent |
| **File length** | Max 3000 lines per file/class; split via extraction when exceeded |

## Development workflow

1. **Write code** following platform standards above
2. **Write unit tests** for new or modified classes/functions (JUnit, XCTest, pytest, or project framework)
3. **Run tests** — only save changes to disk after tests pass
4. **Run build and lint** on completion — use the project's configured build and lint commands

## Technical documentation in WPS Notes

Automatically generate structured technical notes when the activation conditions are met. Full workflow details in sub-skill [review-notes](review-notes/SKILL.md) and [reference/reference.md](reference/reference.md).

### Required note structure (7 sections)

Every generated WPS technical note **must** include these 7 second-level headings:

| Section | Content | Illustration |
|---------|---------|--------------|
| **核心技术** (Core Technology) | Key technologies and frameworks used | Required — use `generate_image` |
| **核心代码** (Core Code) | Critical code snippets with explanation | Code blocks via `edit_block` |
| **关键技术点** (Key Technical Points) | Implementation decisions and trade-offs | — |
| **核心类和职责** (Core Classes) | Class responsibilities and relationships | — |
| **调用链** (Call Chain) | Execution flow in mermaid format | Optional — `generate_image` or mermaid |
| **架构概览** (Architecture Overview) | System architecture diagram and explanation | Required — use `generate_image` |
| **注意事项** (Caveats) | Pitfalls, edge cases, and maintenance notes | — |

### WPS collaboration workflow

```bash
# 1. Check for existing tech doc before creating
wpsnote-cli find --query "项目名 技术文档"

# 2. Create or get current note
wpsnote-cli current          # get active note
wpsnote-cli create --title "MyProject 技术文档"  # or create new

# 3. Get structure for editing
wpsnote-cli outline --note-id <id>   # returns block IDs

# 4. Insert content (e.g., core code section)
wpsnote-cli edit --note-id <id> --block-id <block> --op insert --content '<code lang="kotlin">fun main() { ... }</code>'

# 5. Batch edit for multiple sections
wpsnote-cli batch-edit --note-id <id> --ops '[{"block_id":"<b1>","op":"insert","content":"..."},{"block_id":"<b2>","op":"replace","content":"..."}]'

# 6. Generate and insert architecture diagram
wpsnote-cli gen-image --prompt "Architecture diagram showing ..."
wpsnote-cli insert-image --note-id <id> --block-id <block> --url <image_url>

# 7. Sync and tag
wpsnote-cli sync --note-id <id>
wpsnote-cli tags --query "技术"      # find existing tags to reuse
```

**Error handling:**
- On `BLOCK_NOT_FOUND`: re-run `outline` to refresh block IDs, then retry the edit
- On `generate_image` failure: fall back to mermaid code block for diagrams
- On duplicate note found via `find`: edit the existing note instead of creating a new one

### Core code sources

Include code in the note when obtained from any of these:

- Comments containing "核心代码", "关键实现", "技术要点", or "生成技术文档"
- Code blocks the user explicitly copies or selects
- Clipboard content the user references
- A specific function the user names (include full function body)

### Auto-update behavior

While the user's note remains open, proactively refresh and update the document approximately every minute — add new subsections, update call chains, or incorporate newly reviewed code. Stop when the user closes the note. When the user adds a new heading, fill in content under it based on their intent.
