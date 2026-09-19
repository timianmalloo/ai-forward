---
id: note-20260919-seam-request-terminal-by-deadline
title: "A seam request is terminal by its deadline or it is refused; the fallback is copied onto the expire row; staleness is derived from the cited path's current blob, never stored"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, seam-request, deadline, fallback, stale-ack, ctx-r, id-a]
links:
  - { to: spec-typed-seam-requests, rel: relates-to }
  - { to: design-typed-seam-requests, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Four calls made while building P1: (1) `request add` refuses (exit 2) rather than defaulting a
  missing deadline or fallback - a default would make the termination variant invisible again;
  (2) `deadline_at` is the one stored deadline quantity, the seconds are the input; (3) the expire
  row carries a copy of the fallback text as the outcome fact, so `tail` and the ledger read whole;
  (4) `stale` and `status` are folded at read time, never written. Also: the monotonic id stamp
  moved from coord-mail.py into coord_ids.new_id so every prefix gets it (ID-A sweep).
---

# Decision note: seam requests end by their deadline, never in silence

**Context.** ai-de's `.agents/requests.jsonl` shows 253 of 901 request events (28%) never reaching a resolution; MAST's termination-unaware class is 12.4%. The pre-P1 `coord request add` accepted free text with no deadline and no fallback.

**Decisions.**
1. **Refuse, do not default.** `add` without `--deadline` or `--fallback` exits 2 with `COORD-REQUEST-INCOMPLETE`. `--deadline default` applies `REQUEST_DEADLINE` (900 s) *explicitly*. Rationale: a silently applied default recreates the untyped shape with a number attached; the requester must say what it will do.
2. **One stored deadline quantity.** `deadline_at = at + seconds`; no `deadline_s` field (DM7 — two definitions of one quantity is the defect signature).
3. **The expire row copies the fallback.** `request-expire` carries `outcome: fallback` and the fallback text: the row is the record of what was taken and must stand alone. Accepted duplication, not two definitions.
4. **Derive `status`, `stale`, `overdue`.** Fold at read time; `stale` is `True`/`False` only when an ack pinned a blob *and* the cited path hashes now (git's blob formula, in-process, spiked against `git hash-object`); otherwise the string `not recorded` — never `false` over an absent comparison.
5. **`--except` on the claim event, honoured by `lease_covers`.** A directory lease minus a peer's named files (class CTX-R); doctor's `lease overlap` WARN is the belt.
6. **The monotonic millisecond stamp lives in `coord_ids.new_id`.** `coord-mail.py` keeps passing its own explicit stamp (honoured as given); `req-`, `allocate`, register placeholders and `audit-log.py`'s `al-`/`cl-` (when its import succeeds) all inherit strict per-process order (ID-A).

**Surfaced, not decided here.** Two tests in `tests/docs_explorer/test_coord_core.py` add requests without a deadline and assert the old `open` status; the Coordinator resolves them at the join (`req-01M2XGPYW5ZNC39094ZCM0WHRW`, amended by `req-01M2XHE3K1XBPTJCS09092R754`). `audit-log.py`'s sequential `al-NNNN` fallback (`COORD_LEGACY_IDS` or a failed import) is outside the monotonic guarantee — reported, read-only for this track.

**Blast radius.** `coord request` (six verbs), `claim --except`, `check`, `doctor`, `metrics`, `collaborate summary` (reads the non-terminal states), `pack-doctor.py` `requests` line, `coord_ids.new_id`.
