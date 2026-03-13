---
name: notes-to-lesson-plan
description: Use this skill when a user wants to turn WPS study notes into a teach-back plan, mini lesson, presentation outline, or explanation flow. It is useful not only for teachers but also for learners who want to test mastery by teaching a topic, preparing a study group session, or rehearsing an explanation.
---

# WPS Notes to Lesson Plan 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- one or more WPS study notes
- optional audience type, teaching context, or teach-back goal
- optional time limit or format constraint

## Output

A structured WPS-ready teacher-facing mini lesson plan or learner-facing teach-back script.

## What this skill should produce

Treat teaching as a mastery check.

Required sections:

1. `teaching goal`
2. `what the learner should explain clearly`
3. `what will likely be hard to explain`
4. `example flow`
5. `teach-back questions`
6. `practice task`

This can produce either a teacher-facing mini lesson plan or a learner-facing teach-back script.

## WPS-first rules

- Support both teacher mode and self-study mode.
- If the user is a learner, frame the output as a teach-back script.
- Favor clear speaking order over academic completeness.

## Do not use when

- the user only wants flashcards or a review checklist
- the source note is too shallow to support teaching flow
- the user wants misconception diagnosis instead of explanation planning

## Recommended next skill

Usually recommend:

- `misconception-finder`
- `notes-to-flashcards`
