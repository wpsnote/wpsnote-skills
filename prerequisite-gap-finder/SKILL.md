---
name: prerequisite-gap-finder
description: Use this skill when a user feels stuck, says a topic is hard to follow, or wants to know which missing foundations are blocking understanding in WPS Note. It is especially useful for course revision, self-study, exam prep, and note review when the user asks what they should learn first, what background they are missing, or why a current note still feels difficult.
---

# WPS Prerequisite Gap Finder 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- a current WPS study note or topic that feels difficult
- earlier WPS notes that may cover foundations
- optional course, exam, or difficulty context

## Output

A structured WPS-ready prerequisite gap report with missing foundations, repair steps, and self-checks.

## What this skill should produce

Do not stop at "you have a gap". Turn the gap into a repair path.

Required sections:

1. `required prerequisites`
2. `covered in existing notes`
3. `missing or weak`
4. `why this blocks understanding`
5. `repair plan`
6. `self-check after repair`

## Prioritization rules

Classify each gap as:

- blocker
- important but recoverable
- optional depth

This skill should identify prerequisite gaps, not diagnose all misunderstandings in the current note.

## WPS-first rules

- Name the exact old notes worth revisiting when available.
- If no supporting note exists, say that clearly.
- Convert the repair plan into small tasks with estimated effort.

## Do not use when

- the user wants error diagnosis within the note itself
- the topic is already well understood and only needs review extraction
- there is no meaningful topic scope to trace prerequisite chains

## Recommended next skill

Usually recommend:

- `misconception-finder`
- `study-note-linker`
