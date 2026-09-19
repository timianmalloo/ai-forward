---
id: kb-multi-agent-coordination-glossary
title: "Glossary — multi-agent coordination"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, glossary, ubiquitous-language]
links:
  - { to: kb-multi-agent-coordination, rel: refines }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  The ubiquitous language for the Owner / Coordinator / Sub-Agent model and the distributed-
  systems terms it borrows — each with the near-miss it must not be confused with.
---

# Glossary — ubiquitous language

Use these exact terms in specs, code and ledger events.

## Roles and relationships

- **Owner (seat)** — the most capable model available in a hierarchy; reviews decision requests,
  issues rulings, holds the veto, escalates to the human when a ruling exceeds the mandate.
  *Not:* the human (in ai-de the human ruling seat is also called Owner — say **human operator**
  for the person). *Not:* a grantor of leases. *(Inferred; [AC-1][AC-26][REPO-ai-de])*
- **Coordinator (seat)** — decomposes work for minimal contention and maximum accountability,
  dispatches sub-agents under delegation contracts, watches progress, joins. Never authors track
  work itself. *Not:* ai-de's **AgentPlane conductor**, a product that spawns engines. *(Verified, [REPO-ai-forward] execute-with-coordination)*
- **Sub-agent (seat)** — a fit-for-purpose model executing one delegation contract in one
  worktree, returning artifact references. *Not:* a peer; it cannot re-plan or spawn teams.
- **Leader (S3)** — the Coordinator in the harness the human designated to coordinate across
  harnesses; holds the leader lease. *Not:* an Owner of the other harnesses' work.
- **Spawned relationship** — the parent holds the child's process (stdin/stdout/exit/tool
  results): push, liveness and join are free. **Registered relationship** — independent peers
  that share only files and git: push is best-effort and every request needs a termination
  variant. *(Inferred from [AC-9][P2P-24])*
- **Session Card** — a session's advertisement: harness, model, roles, worktree, branch, listen
  address, epoch. Shaped like an A2A Agent Card; not an A2A dependency. *(Verified shape, [AC-13])*

## Coordination objects

- **Delegation contract (five-part)** — objective · artifact path / output schema · tools and
  sources in bounds · boundaries (paths, budget, fan-out cap) · **termination condition**.
  *(Verified four parts [AC-1]; fifth from MAST [AC-25])*
- **Decision request** — a typed artifact the Coordinator sends to the Owner: options, evidence,
  recommendation, reversibility, blast radius. **Ruling** — the Owner's numbered answer, defined
  by a heading, cited by number; a number that defines nothing is "a number with a reputation".
  *(Verified, ai-de `verify-ruling-citations.py`)*
- **Seam request** — an append-only `request-add` / `request-resolve` pair across tracks
  (`coord request`). **ACK-as-written** — the consumer's acknowledgement pinned to the blob hash
  of the frozen contract revision (ai-de handshake r2..r7). *(Verified, [REPO-ai-de])*
- **Running track** — the fold-derived view of work in flight / completed / remaining.
  *Not:* a second store.
- **Join** — the single script (`conductor-join.py` / `join.json`) that merges, verifies,
  regenerates, commits, gates and pushes; exit status never behind a pipe; state file with a
  terminal `complete` key (COORD-J). *(Verified, [REPO-ai-de][REPO-ai-forward])*
- **Proof of done** — the artifact reference plus gate results a sub-agent returns; the artifact
  is the proof, prose is not. *(Inferred; [AC-1] "filesystem not telephone")*

## Distributed-systems terms

- **Lease** — a time-bounded grant the holder must renew; expiry self-releases a dead holder;
  failures cost performance, not correctness. *Not:* mutual exclusion. *[SCH-9][QLE-6]*
- **Efficiency lock vs correctness lock** — Kleppmann's split: path leases are efficiency locks
  (stop wasted work); the leader lease is a correctness lock and needs fencing. *[SCH-12]*
- **Fencing token / epoch / sequencer** — a monotonic number minted by the consistent store on
  each acquisition, carried to the resource, which rejects lower tokens. A token nobody checks is
  theatre. *[SCH-12][QLE-7][QLE-9]*
- **Compare-and-swap (CAS) cell** — a store that updates only if the current value equals the
  expected one; git refs via `update-ref <ref> <new> <old>` and `--force-with-lease=<ref>:<expect>`.
  *[SPK-1][SPK-2]*
- **Lock-delay / quiet period** — an interval after lease invalidation during which no one may
  re-acquire, so a still-live old holder can notice. *[QLE-10]*
- **Grace period** — Chubby's 45 s window in which a client with an expired session reconnects
  and re-reports held locks. *[QLE-9]*
- **Witness** — an external voter that lets a two-node system break ties; here, the human. *[QLE-16]*
- **Designation vs election** — appointment by an authority with explicit handover, vs an
  algorithm choosing a leader; election never terminates in all runs (FLP). *[QLE-1][QLE-20]*
- **Leadership transfer** — incumbent stops accepting work, brings the successor up to date,
  hands over explicitly; the **reorganisation phase** finishes or discards pending work. *[QLE-3][QLE-15]*
- **Split-brain** — two holders each believing they lead after a partition or pause. *[QLE-16]*
- **Liveness vs progress** — presence of a process vs evidence of work (tool calls, files,
  tokens since last beat); a heartbeat without progress is not progress. *[SCH-8]*
- **Anti-entropy** — a periodic full-state reconciliation (full re-fold) independent of event
  delivery. *[P2P-3]*
- **G-Set / union merge** — a grow-only set whose merge is set union; an append-only ledger under
  `merge=union`; converges on membership, not order. *[P2P-13][P2P-18]*
- **Hybrid logical clock (HLC)** — `(wall_ms, counter, session)` stamp that stays monotonic
  across clock steps. *[P2P-14]*
- **Outbox** — write the state change and the event in one place (the ledger line); a relay
  delivers; at-least-once + idempotency key = effectively once. *[P2P-27]*
- **Turn injection** — delivering a message into a running agent between tool calls, or as a new
  turn when idle; the push primitive. *[P2P-24]*
- **Stop-class hook** — a lifecycle hook that can block completion (exit 2) and feed text back;
  the portable way to turn an inbox into a push. *[P2P-26][AC-5]*
- **Shared-state optimistic scheduling** — schedulers act on a copy of state and commit
  optimistically; conflicts detected at commit (Omega). *[SCH-1]*
- **Critical path / span (T∞)**, **upward rank (HEFT)**, **USL coherency term (β)** — see
  `data-and-constants.md`. *[SCH-6][SCH-14][SCH-7]*
- **Simultaneously changed files** — the strongest predictor of merge conflict; the
  Coordinator's contention signal. *[SCH-17]*
- **Circuit breaker (per work item)** — after N failed assignments, stop reassigning and escalate
  to the Owner. *[SCH-35]*
- **Non-ACK termination variant** — the pre-declared deadline and fallback action a
  cross-harness request carries so a silent peer cannot block progress. *(Inferred; [REPO-ai-de])*
- **MAST** — Multi-Agent System failure Taxonomy: specification 41.8%, inter-agent misalignment
  36.9%, verification 21.3%. *[AC-25]*
