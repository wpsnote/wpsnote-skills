---
name: notes-to-flashcards
description: Use this skill when a user wants WPS notes turned into active-recall material for revision. It is useful for course notes, reading notes, concept review, exam prep, and misconception repair when the user asks for flashcards, recall questions, drill cards, or a compact review deck based on one or more notes.
---

# WPS Notes to Flashcards 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- one or more WPS notes
- optional topic or exam scope
- optional preferred card count or difficulty emphasis

## Output

A structured WPS-ready flashcard deck with active-recall cards and lightweight review hints.

## What this skill should produce

Generate cards that help memory and understanding, not just copy sentences.

Required sections:

1. `definition cards`
2. `distinction cards`
3. `example cards`
4. `application cards`
5. `easy-to-confuse cards`
6. `review order`

Use review timing as lightweight review hints, not a full spaced-repetition schedule.

## WPS-first rules

- Include the source note title or section when possible.
- Keep fronts short and answerable from memory.
- Mark high-risk confusion cards clearly.

## Review logic

When useful, group cards into:

- review today
- review in 3 days
- review in 7 days

This is only a lightweight spaced-review hint, not a full scheduler.

## Do not use when

- the user wants a teaching script rather than recall cards
- the note is too incomplete to support card generation
- the user needs a diagnostic quiz instead of flashcards

## Recommended next skill

Usually recommend:

- `misconception-finder`
- `notes-to-lesson-plan`
