---
name: study-note-linker
description: Use this skill when a user wants a WPS study note connected to earlier notes instead of staying isolated. It is useful for review planning, concept mapping, course revision, research notes, and any case where the user asks what old notes are related, what should be linked, what to revisit first, or how a new note fits into an existing knowledge trail.
---

# WPS Study Note Linker 2.0

Follow the shared workflow in [../wps-learning-workflow.md](../wps-learning-workflow.md).

## Inputs

- a current WPS study note or topic
- earlier WPS notes that may be related
- optional course, exam, or project context

## Output

A structured WPS-ready note-linking analysis with relation types, reading order, and backlink suggestions.

## Retrieval rules

- Search WPS notes before making assumptions.
- Favor notes that are conceptually related, not just keyword matches.
- Rank by study usefulness, not just similarity.

## What this skill should produce

Required sections:

1. `top related notes`
2. `relation type`
3. `why it matters now`
4. `recommended reading order`
5. `suggested backlink sentence`
6. `what this note still lacks`

## Relation types

Use clear relation labels:

- prerequisite
- same topic extension
- contrast / opposing view
- example / application
- revision companion

This skill should prioritize note relationship building, not selective recall for immediate writing or study tasks.

## WPS-first rules

- Always name the referenced notes explicitly so the user can find them in WPS.
- Prefer top 3 to top 5 high-signal links over long noisy lists.
- If nothing strong is found, say so instead of fabricating relevance.

## Do not use when

- the user mainly needs a few old notes recalled for immediate reuse
- there are no earlier notes available to connect
- the user wants a topic summary instead of note-to-note linking

## Recommended next skill

Usually recommend:

- `insight-recaller`
- `prerequisite-gap-finder`
