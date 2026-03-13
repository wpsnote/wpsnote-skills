---
name: class-note-builder
description: Use this skill when a user wants to turn lecture transcripts, OCR, screenshots, or scattered study fragments into a structured WPS Note that is easy to review later. It is especially useful for class notes, workshop notes, training notes, course catch-up, and post-lecture consolidation. Prefer it when the raw material is messy and the user needs a clean main note with unresolved questions, likely review points, and obvious next actions.
---

# WPS Class Note Builder 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- lecture transcripts
- OCR text from whiteboards, slides, or screenshots
- scattered study fragments or raw class notes
- optional course title, session title, or date

## Output

A structured WPS-ready main study note with clear sections, unresolved questions, and review follow-ups.

## What this skill should produce

Build a study-ready main note, not just a cleaned summary.

Required sections:

1. `30-second summary`
2. `core concepts`
3. `definitions / formulas / key claims`
4. `teacher emphasis or repeated points`
5. `examples and cases`
6. `easy to confuse`
7. `still unclear`
8. `next review tasks`

## WPS-first rules

- If the user already has a target WPS note, enrich that note.
- If no note exists, create a new one with a course-friendly title.
- Keep paragraphs short and skimmable.
- Convert unresolved issues into todo-style follow-ups.

## Quality rules

- Remove filler talk and duplicates.
- Preserve the original teaching order when it helps understanding.
- Mark uncertain content instead of pretending it is confirmed.
- If source coverage is weak, add a `missing from source` subsection.

## Do not use when

- the source is already a clean and well-structured note
- the user only wants a short highlight summary
- the user wants misconception diagnosis rather than note construction

## Recommended next skill

Usually recommend:

- `lecture-focus-extractor`
- `misconception-finder`
