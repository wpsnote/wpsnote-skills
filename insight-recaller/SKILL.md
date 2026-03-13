---
name: insight-recaller
description: Use this skill when a user is writing, studying, revising, or preparing content in WPS Note and needs the most useful older notes or insights surfaced at the right time. It is especially useful for revision, synthesis, writing, research, and presentation prep when the user asks what old notes matter now, what they may have forgotten, or what earlier insight should be brought back into the current note.
---

# WPS Insight Recaller 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- a current WPS note, writing task, study task, or revision topic
- earlier WPS notes that may contain reusable insights
- optional time range or task context

## Output

A structured WPS-ready selective recall note that surfaces the most useful prior notes for the current task.

## Retrieval rules

- Search for notes that are useful now, not just topically similar.
- Prefer a small set of high-signal recalls.
- When possible, balance theory, contrast, and example notes.

## What this skill should produce

Required sections:

1. `most useful prior notes now`
2. `why each is worth recalling`
3. `how it connects to the current task`
4. `what can be reused directly`
5. `where to insert or link it`

This skill should recall useful prior notes, not perform full cross-note mapping.

## WPS-first rules

- Always name the old note titles explicitly.
- If a direct quote or section is not available, summarize rather than pretend precision.
- Keep the recall list short and actionable.

## Do not use when

- the goal is to build explicit backlinks between notes
- the user wants a broad literature synthesis instead of selective recall
- there are no meaningful prior notes to recall

## Recommended next skill

Usually recommend:

- `study-note-linker`
- `class-note-builder`
