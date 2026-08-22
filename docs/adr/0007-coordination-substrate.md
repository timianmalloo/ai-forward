---
id: adr-0007-coordination-substrate
title: "ADR-0007: A git-tracked append-only record folded on demand — no daemon, no database"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, substrate, event-sourcing, fold, latency, spike]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  Coordination state lives in an append-only JSONL record, one file per session, git-tracked, and
  every piece of state is a fold over it. The daemon and the SQLite read model the draft proposed are
  both cut, because a measured full fold of a 10,000-event record costs 47 ms p95 against a 100 ms
  budget — and because a service introduces an availability dependency into an offline local tool.
---

# ADR-0007: A git-tracked append-only record, folded on demand

- **Status:** Accepted · **Date:** 2026-08-20 · **Deciders:** Enterprise Architect, Data & Persistence Architect, Tech Lead, the Simplifier, SRE
- **Context spec/architecture:** `docs/specs/agent-coordination.md`, `docs/architecture-agent-coordination.md`

## Context

The spec requires a pre-edit check under **100 ms p95** on a repository with ≥5,000 tracked files and a 10,000-event record (`NFR-P1`), **no daemon that must be started before an agent can work** (`NFR-P2`), and **fold idempotence** (`NFR-R1`). The draft proposed a local daemon owning SQLite, on the assumption that replaying a log per edit would be too slow. That assumption was never measured.

LOA P2 (determinism at the floor) applies with unusual force here: this component is the deterministic substrate beneath non-deterministic actors, and its own failure mode must be legible.

## Decision

We will store coordination state as an **append-only JSONL record, one file per session, git-tracked**, and derive **all** state — leases, work-item status, blocked-on edges, the operator view — as a **fold** over that record. There is **no daemon and no database**. A snapshot may be maintained as a **labelled, rebuildable cache**, never as a source.

**Grain:** one row is exactly one event emitted by one session at one instant. **Compaction trigger, taken from measurement rather than feel:** more than 10,000 live events, or a measured check p95 above 60 ms, whichever comes first. Compaction archives closed work items and never rewrites a retained line.

## Alternatives considered

- **Local daemon + SQLite (the draft's proposal).** Rejected on measurement and on failure mode. **Spike S2:** a full fold of a 10,000-event, 1.45 MB, 12-file record plus a glob match, invoked *as a subprocess the way a hook actually invokes it*, costs **median 45 ms / p95 47 ms** — of which **14 ms is bare interpreter startup** that no design can remove. The budget is met with roughly 2x headroom. The daemon therefore buys no latency this system needs, while adding a startup story, a liveness problem, crash recovery, and a failure mode — *the service is down, so nobody can work* — that directly violates `NFR-P2`. The chosen shape fails differently: the record is unreadable, so the layer says `NOT CHECKED` and degrades to advisory. For a control whose recorded ancestors failed by **reporting success**, a loud non-blocking failure is worth more than 20 ms.
- **Git-ignored local store.** Rejected: does not survive a clone, is invisible in review, and gives up the audit property the spec asks for.
- **Hosted store (cloud table + queue).** Rejected for v1 as the spec's explicit non-goal. Nothing in the model assumes a shared filesystem or a single clock, so a later multi-machine substrate needs no protocol change.
- **One shared record file instead of one per session.** Rejected — but **not for the reason the draft gives**. **Spike S3** shows a single `O_APPEND` write is atomic on Windows across 6 concurrent processes writing 200 records of ~4 kB each: 1,200 lines, 0 unparseable, 0 interleaved. A shared file is therefore *safe*. One-file-per-session is kept because it makes a session's authorship reviewable in a diff and removes any merge surface at all. Recording the real reason matters: a maintainer told "concurrent appends corrupt the file" would have been told something false.

## Consequences

- **+** No service to install, start, supervise or recover. An agent can work the moment it has the repo.
- **+** The record survives a clone, is reviewable in a PR, and is replayable — the audit property is structural rather than bolted on.
- **+** Fold idempotence is testable as a property: replay twice, compare state.
- **−** Current-state reads cost a replay. Priced at 47 ms p95, with a measured compaction trigger rather than a guessed one.
- **−** **No atomic compare-and-set.** Two simultaneous intersecting claims are both recorded and resolved by the total order in the record; the loser is refused on its *next* check. This is stated as advisory-until-checked rather than sold as mutual exclusion (see the Distributed Systems veto in the architecture gate).
- **−** The `LOG-A` seam is inherited: an append onto a file that does not end in a newline fuses two records and loses both. The writer must check the final byte and heal it. This is the record writer's first test, not a later hardening.
- **C-criteria:** deterministic floor (P2); no ambient-credential action; the read model is a labelled, rebuildable cache and never a second source of truth (DM7).
