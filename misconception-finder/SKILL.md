---
name: misconception-finder
description: Use this skill when a user wants a WPS study note checked for false understanding, concept confusion, weak reasoning, or vague phrasing. It is especially useful after note-taking, before revision, before teaching others, or when the user asks whether they really understood a topic rather than merely wrote it down.
---

# WPS Misconception Finder 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- a WPS study note, explanation draft, or revision note
- optional topic label
- optional reference material, textbook summary, or answer key

## Output

A structured WPS-ready misconception diagnosis with repair suggestions and self-check questions.

## What this skill should produce

This is a diagnosis-and-repair skill, not a style-polishing skill.

Required sections:

1. `overall understanding diagnosis`
2. `high-confidence errors`
3. `possible misunderstandings`
4. `missing evidence or examples`
5. `better phrasing for understanding repair`
6. `mini self-test`

## Diagnosis rules

Separate:

- clearly wrong
- likely confused
- too vague to trust

If confidence is low, say why.

## WPS-first rules

- Quote or point to the learner's own phrasing when possible.
- Keep fixes specific and teachable.
- Add at least one self-check question per major error.

## Do not use when

- the user only wants writing polish
- the source note is too thin to support diagnosis
- the user wants prerequisite analysis rather than misconception repair

## Recommended next skill

Usually recommend:

- `notes-to-flashcards`
- `prerequisite-gap-finder`
