---
id: "note-20260818-dream-rerun-unchanged-corpus"
title: "Re-running /dream over an unchanged corpus re-surfaces already-promoted classes under new proposal ids"
type: decision-note
status: draft
owner: "@timianmalloo"
phase: "dreaming"
tags: [decision-note, dreaming, continuous-improvement, idempotency]
links:
  - { to: architecture-dreaming, rel: relates-to }
  - { to: spec-dreaming, rel: relates-to }
review-by: "2027-02-14"
review-suggested: []
summary: >-
  Observed in drm-0004: a dream over a corpus unchanged since the prior dream re-emits the same
  control-upgrade/marker/mitigation proposals under fresh (dream, proposal) ids, and apply-decisions'
  per-(dream,proposal) idempotency does not treat them as duplicates — so approving them re-appends
  the same class to the fleet store. Push-stage slug dedup ("latest wins per class slug") absorbs the
  downstream harm, so the correct operating response is Defer/Reject at the review gate, not a code change.
---

# Re-running /dream over an unchanged corpus re-surfaces already-promoted classes under new proposal ids

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback weight.*

- **Kind:** resolved-question
- **Confidence:** Verified *(observed directly: drm-0003 and drm-0004 produced the same 7 proposals over a corpus whose register, mitigations, change-log, and markers were identical; `learnings/promoted.jsonl` holds `drm-0003/p2..p7` but not the equivalent `drm-0004/*` keys).*
- **Made during:** `/dream` run producing drm-0004 (session ad91aa43)

## The call
Running `/dream` again when nothing substantive has changed in the corpus (no new defect classes,
mitigations, change-log decisions, or markers) is **expected** to re-emit the previous dream's
proposals — the deterministic harness scores the same recurring partially-controlled classes
(PACK-C/D/E/H), the same `simplify:`/`assume:` marker harvest, and the same confirmed mitigation.
Because `apply-decisions`' idempotency ledger keys on `(dream, proposal)` and each dream mints fresh
proposal ids, these re-surfaced proposals are **not** recognised as already-promoted; approving them
would append duplicate class rows to `learnings/fleet-classes.jsonl`. The practical harm is bounded:
the `/apply-learnings` push dedupes the fleet store by class slug ("latest wins"), so a target repo
never receives a duplicate. **Therefore the response is operational, not a code change:** at the review
gate, **Defer or Reject** proposals already promoted by an earlier dream (check `learnings/promoted.jsonl`
and the fleet store first), and prefer not to run `/dream` until the corpus has actually moved.

## Alternatives dismissed
- *Change the idempotency guard to key on class slug across dreams* — a real fix, but it is a pack-code
  change to `dream.py` that belongs behind `/extendaibundle` with a red-first control, not a mid-dream
  decision; and the push-stage slug dedup already prevents the only harm that reaches a target repo.
- *Suppress re-surfaced proposals inside `run`* — would hide legitimately still-open classes (a
  partially-controlled class that genuinely still lacks a control *should* keep surfacing until it is
  controlled — CI6); silencing it would defeat the point of the register.

## Validation condition
Holds until/unless `dream.py apply-decisions` is changed to dedupe by class signature/slug across
dreams (making cross-dream re-promotion idempotent), or the fleet store stops deduping on push. When
either trips, re-validate this note: confirm (bump `review-by`), retire (`status: superseded`), or
promote to an ADR if the idempotency model is formally changed.

## Promotion rule
If this starts bearing load — e.g. the fleet store accumulates enough duplicate rows to mislead a
maintainer, or a second capability depends on cross-dream idempotency — promote to an ADR that changes
the idempotency key, link it `supersedes` this note, and set this note `status: superseded`.
