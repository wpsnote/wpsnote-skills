---
name: skill-creator
description: Create new skills or improve existing skills by clarifying intent, drafting SKILL.md instructions, organizing supporting resources, and doing lightweight manual review. Use when users want to create a skill from scratch, revise a skill, package a skill, or improve a skill's trigger description.
---

# Skill Creator

This skill helps create and refine agent skills without assuming a heavy assessment framework. Keep the work practical: clarify what the skill should do, write the smallest useful instruction set, add supporting files only when they reduce repeated work, and validate the result with simple review prompts or real usage examples when helpful.

## Working Style

- Prefer clear skill boundaries over broad, generic behavior.
- Keep `SKILL.md` readable and focused. Move long reference material into `references/`, reusable code into `scripts/`, and reusable templates or static files into `assets/`.
- Do not create formal scoring harnesses by default. If the user asks for deeper validation, agree on the method first and keep it outside the published skill unless it is mature enough to maintain.
- Use the repository's existing skill style when modifying a skill in an existing collection.
- When in doubt, optimize for a skill that a future agent can load quickly and follow reliably.

## Workflow

### 1. Capture Intent

Start by extracting what the user wants the skill to enable. If the current conversation already contains the workflow, derive the answer from that context before asking follow-up questions.

Clarify:

1. What task or workflow should the skill help with?
2. When should the skill trigger, and when should it not trigger?
3. What inputs does the skill expect?
4. What output or side effect should the user receive?
5. What tools, files, apps, MCP servers, or external services are required?

Ask only for missing details that materially affect the skill design.

### 2. Draft the Skill

Create or update `SKILL.md` with:

- YAML frontmatter containing `name` and `description`.
- A concise overview of what the skill does.
- Trigger boundaries and non-goals when they prevent confusion.
- Step-by-step operating instructions.
- Tooling notes, file locations, and safety constraints.
- Output expectations.

The `description` is the main trigger signal. Make it specific enough that an agent can decide when to load the skill from metadata alone.

### 3. Organize Supporting Files

Use bundled resources only when they are useful:

- `scripts/`: deterministic helpers, validators, converters, or repeatable setup code.
- `references/`: longer instructions, schemas, examples, or domain notes that do not need to be loaded every time.
- `assets/`: templates, static files, sample images, or other files used by the skill.

Reference these files from `SKILL.md` with clear instructions on when to read or run them.

### 4. Review With Examples

For nontrivial skills, propose 2-3 realistic example prompts and inspect whether the instructions would lead to the intended behavior. Keep this lightweight:

- Use examples that resemble actual user requests.
- Check trigger fit, required tools, output shape, and edge cases.
- Revise the skill when an example exposes ambiguity or unnecessary complexity.
- Do not add formal scoring files or long-running comparison workflows unless the user explicitly asks for them.

### 5. Validate And Package

When a runnable skill folder exists, use the included helpers when appropriate:

```bash
python skills/skill-creator/scripts/quick_validate.py <skill-directory>
python skills/skill-creator/scripts/package_skill.py <skill-directory> [output-directory]
```

Validation checks the basic skill shape and frontmatter. Packaging creates a distributable skill archive.

## Writing Guide

### Skill Anatomy

```text
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

Only `SKILL.md` is required. Add other folders when they make the skill easier to maintain or more reliable.

### Frontmatter

```yaml
---
name: example-skill
description: What this skill does and when to use it.
---
```

Use kebab-case for `name`. Keep `description` concrete, including important trigger phrases and boundaries.

### Instruction Quality

- Explain why an instruction matters when the reason helps future agents make good tradeoffs.
- Prefer direct workflow steps over vague principles.
- Keep examples short and representative.
- Avoid absolute rules unless violating the rule would clearly break the workflow.
- Keep unrelated policy, product, and implementation details out of the skill body.

### Updating Existing Skills

When improving an existing skill:

1. Read the current `SKILL.md` and any directly referenced resource files.
2. Identify what behavior should change.
3. Preserve working conventions unless they are causing the issue.
4. Make scoped edits.
5. Re-read the changed file to verify the instructions are coherent.

## Deliverable

Finish by summarizing:

- Which skill was created or changed.
- Important trigger or workflow changes.
- Any helper files added, removed, or kept.
- Whether quick validation or packaging was run.
