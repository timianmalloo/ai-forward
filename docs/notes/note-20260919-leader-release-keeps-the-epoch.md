---
id: note-20260919-leader-release-keeps-the-epoch
title: "A leader release clears the holder and keeps the epoch; no verb deletes refs/coord/leader; the quiet period applies to an expiry, not to a release"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, leader, epoch, fencing]
links:
  - { to: spec-leader-designation, rel: relates-to }
  - { to: note-20260919-leadership-in-a-ref-not-the-ledger, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  If `coord leader release` deleted the ref, the next pin would restart at epoch 1 and the join fence
  would let a stale epoch-2 plan through; so release writes `leader: null` with the epoch kept, and
  every later pin or reclaim advances it. The 30 s quiet period guards an invalidated holder that may
  still be writing; a holder that released knows it is done, so a pin after a release is immediate.
  Blast radius: the five verbs, the fence, the metrics' leader-loss count.
---

# A leader release clears the holder and keeps the epoch

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback
weight. One note per call; written before the session that made it closes.*

- **Kind:** decision
- **Confidence:** Verified for the mechanism (`git update-ref` over a blob: create-with-zeros 0, stale
  old 128, delete-with-stale-old **1**, blob survives `gc --prune=now`; git 2.54.0, 2026-09-19);
  Inferred for the quiet-period scoping (Consul's lock-delay rationale, `data-and-constants.md` [QLE-10])
- **Made during:** `/specify` of `spec-leader-designation` (Track P2, session `p2-leader`)

## The call

1. **Release never deletes the ref.** `coord leader release` compare-and-swaps the blob to
   `{leader: null, epoch: <unchanged>, released_at: <now>, ...}`. The epoch is the fencing token; a
   deleted ref forgets it and a later `pin` would create epoch 1 again, so a plan carrying epoch 2
   from before the release would pass the fence. Only a human `git update-ref -d` removes the ref,
   and `who` then reports *absent* (the read succeeded), never NOT CHECKED.
2. **Every change of holder advances the epoch by exactly one** — `pin` on a released ref, and
   `reclaim` on an expired one. `renew` never advances it.
3. **The quiet period (30 s, D13) applies after an *expiry*, not after a *release*.** The lock-delay
   exists so an invalidated holder that may still believe it leads can finish or die before a
   successor writes. A holder that released is not in that state. So: `pin` on `released` succeeds
   at once (epoch + 1); `pin` on `expired` is refused with the remedy "reclaim after the quiet
   period"; `reclaim` on `expired` inside the quiet period is refused with the seconds remaining.

## Alternatives dismissed

- *Delete the ref on release* — loses the epoch (above); also `update-ref -d` with a stale old exits 1,
  not 128, a second code path to test for nothing.
- *Apply the quiet period to release too* — costs every clean hand-over 30 s for a hazard the
  releasing holder cannot present. Re-open if a released leader's in-flight join is ever observed
  after its release; it is a one-constant change.
- *Let `pin` advance over an expiry* — makes `reclaim` redundant and the quiet period bypassable.

## Validation condition

Holds while the fence compares integers from one ref. Re-check if the ref is ever pushed across
machines (two clocks) or if a second leader ref is introduced.
