---
id: note-20260919-liveness-heartbeat-renews-the-leader
title: "A sampled heartbeat from the session that holds refs/coord/leader renews the designation; it never reclaims one that lapsed (F-1 accepted)"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination P3"
tags: [decision-note, coordination, liveness, leader, heartbeat, f-1]
links:
  - { to: spec-liveness-and-track, rel: relates-to }
  - { to: spec-leader-designation, rel: relates-to }
  - { to: coordination-p3-p5-p8, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  D13's leader lease (TTL 300 s, renew 100 s) was tuned for a running process; an interactive
  coordinator lapsed between renews and reclaimed at every join (plan F-1). The heartbeat is
  sampled into the ledger at most once per 100 s - the same cadence as the renew - so a sampled
  beat from the holder calls the existing renew path. An expired designation is not reclaimed by a
  heartbeat: a reclaim advances the epoch and is an explicit act. Blast radius: `heartbeat_tick`,
  the heartbeat row's `leader_renewed` field, the F-1 row of the plan.
---

# A sampled heartbeat from the leader renews the designation

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback weight.*

- **Kind:** decision (plan `coordination-p3-p5-p8` finding F-1, assigned to P3)
- **Confidence:** Verified for the mechanism (`leader_decide("renew")` is the existing path;
  `HEARTBEAT_SAMPLE == LEADER_RENEW == 100 s`, `coord-core.py`); Verified by test
  (`test_coord_liveness.py::LeaderRenew*`, red before the change).
- **Decision:** when `heartbeat_tick` writes a sampled row and the session is the live holder of
  `refs/coord/leader`, it renews (same TTL, epoch unchanged) and records `leader_renewed: true`.
  When the designation has expired it records `leader_renewed: "expired"` and touches nothing —
  the coordinator runs `coord leader reclaim` on purpose, as before. When the session is not the
  holder (or the ref is absent or unreadable) the field is `null`.
- **Why not renew on every hook call:** the sample window already bounds the ledger write to one
  per 100 s; a git `update-ref` per tool call would put a subprocess on the hot path for no
  additional liveness (D13 chose 100 s for a reason).
- **Why not reclaim from a heartbeat:** a reclaim changes the epoch the join fences on; an
  implicit epoch advance from a background hook would make a stale plan's epoch fail with no
  visible act to explain it.
- **Alternatives struck:** a longer TTL (masks a dead leader for longer); a renew in the doorbell
  (the doorbell is a read; mixing a write into it breaks its "hint, never state" contract).
