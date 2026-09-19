---
id: note-20260919-liveness-worktree-field-is-a-label
title: "The ledger's `worktree` field is the worktree's basename (a label), never a path; `tree` was never the carrier (F-3 as found)"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination P3"
tags: [decision-note, coordination, ledger, plat-b, worktree, f-3]
links:
  - { to: spec-liveness-and-track, rel: relates-to }
  - { to: coordination-p3-p5-p8, rel: relates-to }
  - { to: adr-0007-coordination-substrate, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  Plan finding F-3 names `tree` as the field carrying the absolute worktree path that gate 1b
  (PLAT-B) refuses. Grep over the primary's ledgers found 26 absolute paths, all in `worktree`,
  none in `tree` (which holds `primary|worktree`). The writer now records the basename in
  `worktree`; occupancy and cleanup compare labels (old absolute values are reduced to their
  basename on read, so no record is orphaned); `coord log portable` rewrites only that field in
  place, idempotently. Repo-relative was not possible: a linked worktree lies outside the repo.
---

# The `worktree` field is a label

- **Kind:** decision + correction of a plan finding
- **Confidence:** Verified (grep `"[a-z_]*": "/Users…"` over `.agents/log/*.jsonl`: 26 × `worktree`,
  0 × `tree`; `cmd_session` at `coord-core.py:2922-2963` writes `worktree: _worktree_key(cwd)` and
  `tree: session_tree_kind(...)`).
- **Decision:** `worktree` carries `os.path.basename` of the resolved worktree path. `coord session
  start/end`, `coord worktree new` and the heartbeat writer all write the label. Readers that compared
  `event["worktree"]` to `_worktree_key(cwd)` (occupancy in `cmd_session`, `live_keys` in `cmd_worktree
  cleanup`) compare labels, reducing any legacy absolute value to its basename first.
- **Why basename, not repo-relative:** a linked worktree is a sibling directory of the primary
  checkout, so no repo-relative form exists; the basename is what the coordination plans and
  `coord worktree list` already call the tree.
- **Cost accepted:** two worktrees with the same basename under different parents on one machine
  share a label; occupancy would refuse the second start and cleanup would hold both — the safe
  direction. `coord session list` still prints the label, so a human can tell.
- **Migration:** `coord log portable <file>...` — parse each line, rewrite only `worktree` values that
  contain a path separator, re-dump only those lines (`sort_keys=True`, as the writer does); other
  lines are copied byte-for-byte; a second run changes nothing. The coordinator runs it over the
  eleven track logs at the landing (plan F-3 disposition: "by the writer's own migration, never by
  hand").
