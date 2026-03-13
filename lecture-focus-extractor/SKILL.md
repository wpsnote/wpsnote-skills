---
name: lecture-focus-extractor
description: Use this skill when a user has a long lecture note, transcript, or study note in WPS Note and needs the real exam-worthy or review-worthy points separated from noise. It works best for class recordings, dense summaries, workshop notes, or catch-up material where the user asks for the main points, must-remember items, one-minute review, or what matters most.
---

# WPS Lecture Focus Extractor 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- a long lecture note, transcript, or dense study note
- optional topic or course label
- optional exam or revision context

## Output

A structured WPS-ready focus sheet that separates must-review material from background material.

## What this skill should produce

Extract the parts most worth reviewing, not just a generic summary.

Required sections:

1. `must remember`
2. `definitions / formulas / principles`
3. `teacher emphasis`
4. `likely forget points`
5. `one-minute recap`
6. `10-minute review list`

## Prioritization rules

Give higher weight to:

- repeated ideas
- explicit warnings
- exam hints
- examples that reveal the rule
- places where the learner is likely to confuse concepts

## WPS-first rules

- Prefer short bullets over long paragraphs.
- Make the final section usable as a quick pre-review checklist.
- If the note is already structured, do not flatten everything into one blob.

## Do not use when

- the user wants a full structured main note
- the source is already short and focused
- the goal is to generate flashcards directly

## Recommended next skill

Usually recommend:

- `notes-to-flashcards`
- `class-note-builder`
