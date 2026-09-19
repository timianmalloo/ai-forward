---
id: note-20260919-leadership-in-a-ref-not-the-ledger
title: "Leadership is held in a git ref by compare-and-swap; the union-merged ledger only records it"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, leader, fencing, git]
links:
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
  - { to: kb-multi-agent-coordination, rel: relates-to }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  Executed spikes on 2026-09-18 showed two competing leader claims both survive a union merge
  (exit 0), while `git update-ref <ref> <new> <old>` and `--force-with-lease=<ref>:<expect>`
  refuse a stale expectation. Any leader or epoch the pack introduces therefore lives in
  `refs/coord/leader` and is only recorded in `.agents/log`; the join checks the epoch. Blast
  radius: P2 of the proposal, and both prior proposals' election designs.
---

# Leadership is held in a git ref by compare-and-swap; the union-merged ledger only records it

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback
weight. Promote to an ADR when P2 is specified.*

- **Kind:** decision
- **Confidence:** Verified (by execution — scripts in the session scratchpad, results in
  `docs/knowledge/multi-agent-coordination/data-and-constants.md`)
- **Made during:** `/collectknowledge` multi-agent-coordination, while critiquing
  `active-multi-harness-coordination.md` §6.1 ("first append wins; the fold is the total order")

## The call

The ledger under ADR-0007 is append-only per-session JSONL merged with `merge=union`. Union
merge is a grow-only set: it accepts both sides' lines by construction, so two sessions each
appending `leader-claim` for epoch 1 both land (observed: merge exit 0, both lines present;
rebase the same). A reader can apply a deterministic post-hoc rule, but that is last-writer-wins
by another name and provides no exclusion at write time. Git refs, by contrast, are a
compare-and-swap cell: `update-ref refs/coord/leader <new> <old>` exits 128 on a stale `<old>`
and `push --force-with-lease=refs/coord/leader:<expect>` is rejected with "stale info" — unless
`--force` is also passed, which silently overrides the lease. So: **the ref decides, the ledger
records, the join fences** (it refuses a plan carrying an epoch lower than the ref's).

## Alternatives dismissed

- *Ledger total order by HLC stamp* — post-hoc; no write-time exclusion; clock skew across harnesses.
- *A lease file (`flock` / `O_EXCL`)* — no epoch, no resource-side check, platform-divergent semantics.
- *A consensus store (etcd/ZooKeeper)* — a daemon and a cluster for five local processes; contradicts ADR-0007's fail-open constraint.
- *An LLM tie-break* — non-deterministic and non-monotonic.

## Validation condition

Holds while the pack's durable record is git. Re-check if the record moves off git, or if a
harness ships a fenced coordination store the pack adopts.
