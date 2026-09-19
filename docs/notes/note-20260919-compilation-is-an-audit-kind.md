---
id: note-20260919-compilation-is-an-audit-kind
title: "A compilation is its own audit kind, and its prompt field is the rendered text"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, compile, audit-log, prompt-log]
links:
  - { to: design-compile-stage, rel: relates-to }
  - { to: spec-compile-stage, rel: relates-to }
  - { to: audit-log, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  The compile stage records each gate-passing compile as a `kind: compilation` audit entry rather
  than a `kind: prompt` one, so the /prompts lens never shows compiled text as if the operator
  typed it; the entry's `prompt` field carries the rendered compiled text so the unchanged lens
  lists it for reuse, and the structured record lives beside it in a `compiled` object. Blast
  radius: `AUDIT_KINDS` in audit-log.py, the audit viewer's kind badge, prompt-log's stack label.
---

# A compilation is its own audit kind (2026-09-19)

**Context.** `spec-compile-stage` says the compilation is "one audit entry naming the raw prompt id" and that raw and compiled prompts are logged together and shown side by side by `/prompts`. `audit-log.py` validates `--kind` against a fixed list that has no fitting value.

**Decision.** Add `compilation` to `AUDIT_KINDS`. The entry's `prompt` field is the **rendered compiled text**; the structured `compiled-prompt/1` object sits in a `compiled` field. A `compilation` entry never consumes a start marker (like `prompt`).

**Why not `kind: prompt` with a flag.** `prompt-log.py`'s `_adapt()` treats every `prompt` row as operator words; a flag would have to be checked in every reader, and one missed reader would replay compiled text as the operator's own request — the exact confusion the twin view exists to prevent.

**Consequences.** The audit viewer's kind badge gains `compilation`; `prompt-log.py list` suffixes such rows with `⟲ compiled from <raw_id>`; `search` matches both kinds unchanged. `selfcheck` treats `compilation` like `prompt` for goal-state presence (a compilation *is* a goal state, not a turn).

**Reopen if** a reader is found that enumerates kinds and breaks on the new one, or if the viewer needs a separate compilations tab (then a projection, never a second store).
