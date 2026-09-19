---
id: kb-multi-agent-coordination
title: "Multi-Agent Coordination — domain knowledge (agentic coordination · p2p protocols · distributed scheduling · quorum & leader election)"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, multi-harness, p2p, scheduling, leases, fencing, leader-election, quorum, owner-coordinator-subagent]
links:
  - { to: architecture-agent-coordination, rel: refines }
  - { to: spec-agent-coordination, rel: relates-to }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
  - { to: adr-0005-harness-runner-boundary, rel: depends-on }
  - { to: design-coord-collaboration-phase4, rel: relates-to }
  - { to: kb-graph-and-loop-engineering, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  Sourced, confidence-labelled evidence base for coordinating an Owner / Coordinator / Sub-Agent
  hierarchy across one or several CLI harnesses (Claude Code, Codex, Copilot CLI, Antigravity,
  Grok Build) on one or two developer machines: what the harnesses actually ship, what
  distributed-systems theory forbids (leases are not mutual exclusion; a union-merged ledger
  cannot elect a leader), which scheduling and ownership results predict conflict, and the
  constants practitioners use. Four research tracks plus three executed git spikes.
---

# Multi-Agent Coordination — domain knowledge

**Domain & problem:** the AI-Forward Pack must support three coordination scenarios under one
role model — **Owner** (the most capable model; reviews, rules, escalates to the human),
**Coordinator** (decomposes for minimal contention and maximum accountability, dispatches,
joins), **Sub-Agents** (fit-for-purpose models executing bounded work). **S1:** one harness hosts
Owner + Coordinator and dispatches sub-agents to other harnesses. **S2:** everything inside one
harness session using its native multi-agent mode. **S3:** several harnesses each running a
self-contained hierarchy, with one designated leader coordinating across them.

**Canonical framing:** the field frames this as **orchestrator-worker** for read-heavy work
(Anthropic), **blackboard over a shared repository** for write-heavy work (Anthropic's C-compiler
run, Claude Code agent teams), and **shared-state optimistic scheduling** in cluster terms
(Omega). The distributed-systems half (leases, fencing, epochs, quorum) is old and settled. The
pack's own framing — *claims, not commits, are the unit of coordination*, recorded as an
append-only git ledger — remains novel; no production coding system was found to use it.
**Divergence noted:** the user's S3 asks for an *elected* leader; the evidence says
*designated* leader with a reclamation lease (finding 3).

**Compiled:** 2026-09-18 · **Lead:** Domain Researcher (four parallel tracks: agentic
coordination · p2p protocols · distributed scheduling · quorum & leader election) · **Executed
spikes:** three (git ref CAS, `--force-with-lease`, union merge) · **Status:** fresh.

The companion base in the consuming repo, `ai-de/docs/knowledge/multi-agent-coordination/`
(compiled 2026-08-23), is **extended, not contradicted**: its fencing-token finding, the 15×
multiplier, MAST, METR and Cognition are reconfirmed here from primary sources; what is new is
the harness-primitive survey, the leadership result, the scheduling/ownership literature and the
executed spikes. One correction to a claim made in both prior proposals: **"AgentRoom
(arXiv:2608.23740)" could not be found** and must not be cited (open-questions.md).

## Headline findings

1. **A lease never provides mutual exclusion; only a fenced resource does.** Jepsen's etcd
   analysis lost ~18% of acknowledged updates with 2 s TTLs and 5 s pauses; Kubernetes'
   `client-go` says in source it "does not guarantee that only one client is acting as a leader".
   Safety must live where the effect lands. — *(Verified, [QLE-5][QLE-6][QLE-7])*
2. **Git refs are the one compare-and-swap cell already in the stack; the union-merged JSONL
   ledger is not one.** Executed: `git update-ref <ref> <new> <old>` refuses a stale `old`
   (exit 128); `git push --force-with-lease=<ref>:<expect>` refuses a stale expect
   ("stale info", exit 1) and permits a non-fast-forward with a correct one; adding `--force`
   **silently overrides the lease**; two competing `leader-claim` lines union-merge with exit 0
   and both survive. — *(Verified by execution, [SPK-1][SPK-2][SPK-3])*
3. **At 2–10 crash-only sessions with a human present, election is the wrong tool; designation
   with a reclamation lease is the right one.** Two nodes cannot self-elect (a witness is
   required); FLP says no election terminates in all runs; incident command and single-threaded
   ownership are appointed, never elected. The carve-out: a leader that dies at 02:00 must be
   *reclaimable* automatically by a strictly-higher-epoch CAS after its lease expires — never
   *contested* automatically. — *(Verified components, Inferred synthesis, [QLE-1][QLE-16][QLE-20][QLE-34])*
4. **Three harnesses expose a supported push into a running session; four have a headless
   print mode with JSON output.** Claude Code: per-session Unix socket / named pipe, file
   registry, per-session token, delivered *between tool calls* or as a *new turn when idle*;
   cross-session `SendMessage` and `notify_when_idle` observed in this session; background
   sessions via `--bg` and `claude agents`. Codex: `codex queue --thread … --message …` and
   `app-server --listen ws://…`. Antigravity: `--input-format stream-json` runs one turn per
   stdin line in a spawned print-mode child (no push into an interactive session). Grok: print
   mode, no push found. Copilot CLI: docs-only here (not installed). **Every harness has native
   sub-agent fan-out; none has a cross-harness coordinator.** — *(Verified by `--help` execution
   2026-09-19, [AC-5][AC-6][AC-23][P2P-24][OBS-1][OBS-4])*
5. **A spawned child is a push channel by construction; a registered peer is not.** Under S1
   the Coordinator holds each dispatched harness's stdin/stdout/exit (`claude -p`, `codex exec`,
   `copilot -p`); under S3 nobody holds anybody, so every cross-harness request needs a
   **non-acknowledgement termination variant**. ai-de improvised exactly this ("not waiting on
   Codex") after 28% of 901 seam requests went unresolved. — *(Verified, [AC-9][REPO-ai-de])*
6. **Push must be turn-injection, not a mailbox the agent is told to check.** A `Stop` /
   `TeammateIdle` hook that drains an inbox and exits 2 turns a pull into a push with no socket —
   the portable primitive across harnesses that have a stop-class hook. — *(Verified for Claude
   Code, [P2P-25][P2P-26]; Flagged for Copilot / Antigravity / Grok / Codex — R7)*
7. **Liveness must be read from the world and heartbeats must carry progress.** Temporal's
   heartbeat carries progress details so a stuck-but-alive worker is caught by the heartbeat
   timeout, not the start-to-close timeout; MAST's *Step Repetition* (15.7%) is invisible to a
   liveness ping. Practitioner ratio: renew at TTL/3–TTL/4, ≥3 missed beats before "dead"
   (Kubernetes 10 s / 40 s; etcd 100 ms / 1 s). Phi-accrual is over-engineered below ~9 nodes
   (Akka's own all-to-all cutoff). — *(Verified, [SCH-8][SCH-22][SCH-27][P2P-6])*
8. **Contention is predicted by one feature — files changed simultaneously on both branches —
   and ownership concentration predicts defects.** Owhadi-Kareshk et al. found it the only
   strong predictor; Microsoft's ConE productionized it (>70% of 775 warnings useful); Bird et
   al. tie low-expertise contributors and weak top-owner share to faults. One owner per
   artifact is a quality control. — *(Verified, [SCH-15][SCH-17][SCH-18])*
9. **Parallelism has a finite optimum, and coding parallelises worse than research.** Multi-agent
   costs ~15× a chat turn (agent teams ~7×); the Universal Scalability Law's coherency term grows
   as N²; vendor guidance is 3–5 workers. Anthropic's C-compiler run (16 agents, ~$20k) shows
   write-parallelism works only with a strong test oracle and granular tasks, and failed on the
   monolithic kernel task where "every agent would hit the same bug … and overwrite each other's
   changes". — *(Verified, [AC-1][AC-4][AC-10][SCH-7])*
10. **Verification is 21% of measured multi-agent failures, and the harness will not gate plans
    for you.** MAST: specification 41.8% · misalignment 36.9% · verification 21.3%. Claude Code
    auto-approves a teammate's plan in the lead's session "without the lead reviewing it";
    Copilot's `--allow-all-tools` collapses the gate. An Owner review of plans and irreversible
    actions must be built by the pack, as a hook with a deterministic exit code where possible.
    — *(Verified, [AC-5][AC-19][AC-25][AC-26])*
11. **An agent message is never consent.** Claude Code forbids a teammate answering a permission
    prompt, relaying a denied action through a peer, or changing settings because another
    session asked; in auto mode a classifier reviews every inter-agent message. The Owner's
    authority is over *work*, never over *permission*. — *(Verified, [AC-5][AC-6])*
12. **Do not build:** SWIM, gossipsub, phi-accrual, a source-code CRDT (CodeCRDT: −39% worst case,
    5–10% semantic conflicts), a consensus store, a required daemon, A2A as a dependency
    (no harness in scope implements it), mTLS/DID on one machine (the OS user *is* the trust
    boundary), or anything leaning on MCP *sampling* (deprecated in the 2026-07-28 revision).
    — *(Verified, [AC-11][P2P-17][P2P-20][QLE-9])*

## Confidence summary

Verified: 41 headline-bearing claims (all harness primitives read from official docs dated
2026-09-18; all distributed-systems mechanisms from primary papers, vendor source or Jepsen; the
three spikes by execution). Inferred: the synthesis rules (designation over election, the
spawned/registered split, the recommended constants). Flagged and load-bearing: **(a)** whether
Copilot CLI, Antigravity, Grok Build and Codex can run a *blocking* stop-class hook (decides how
far the portable push reaches); **(b)** Antigravity headless flags (decides whether agy can host
S1); **(c)** the merge-conflict rate between parallel AI agents in worktrees — **no public
measurement exists**; the 16% human baseline is the only number.

## Design implications (what the next phase should do with this)

- **Design by control relationship, not by harness.** Two relationships exist: *spawned*
  (parent holds the process: push, liveness and join are free) and *registered* (peers share
  only files and git: push is best-effort, every request carries a deadline and a fallback).
  S2 is spawned-native; S1 is spawned-remote; S3 is registered. [finding 5]
- **Hold leadership in a git ref, record it in the ledger, fence it at the join.** `coord leader
  pin` writes `refs/coord/leader` by CAS with an epoch; every leader-authored artifact carries the
  epoch; the join refuses a lower epoch; the ledger only *records* the transition. Never pass
  `--force` alongside `--force-with-lease`; always use the three-part form. [findings 1–3, SPK-1..3]
- **Designate, don't elect.** `coord leader pin <session>` by the human is the default; an
  expired leader lease is reclaimable by CAS with a strictly higher epoch after a quiet period
  (Consul lock-delay analogue, 15–30 s); a contested claim is never resolved automatically — it
  pages the human. Deterministic tie-break if ever needed: lowest session id, never a model judge.
- **Demote path leases to efficiency locks; keep TTL 300 s default / 900 s cap.** Git is the
  correctness arbiter (three-way merge + ref CAS). No code path may assume a lease was honoured;
  instrument lease hold time as a first-class metric (Cursor-style lock-holding collapse at 20
  agents). [finding 1, D5 in p2p]
- **Liveness from the world; heartbeats that carry progress.** Presence = process liveness (PID
  + start time; `OpenProcess` on Windows) and worktree/ledger activity; progress = tool calls,
  files touched, tokens since last beat. Constants to start: renew every TTL/3, suspect at 3
  missed, dead at TTL, anti-entropy full re-fold every 15 s. No phi-accrual until a baseline
  exists. [finding 7]
- **Push by the cheapest channel that reaches the target, with a termination variant.** Claude
  Code → native cross-session message (turn injection). Codex → app-server WebSocket. Any
  harness with a stop-class hook → inbox drain + exit 2. Otherwise → inbox file + SessionStart
  count injection + the request's deadline/fallback. Never advertise a channel not executed on
  this machine. [findings 4–6]
- **Decompose for disjoint authored sets, interface-first, one owner per artifact.** The
  Coordinator authors shared contracts *before* fan-out; refuses two tracks in one file or one
  MVC slice; ranks work by longest remaining dependency chain (HEFT) and puts the serial spine
  first; caps width at 3–5 with the USL optimum in mind; runs write-parallelism only where a test
  oracle exists. [findings 8–9]
- **Five-part delegation contract:** objective · artifact path / output schema · tools and
  sources in bounds · boundaries (paths, budget, fan-out cap) · **termination condition**
  (the fifth part MAST demands). Results return as artifact references, never prose. [finding 10]
- **Owner review is mechanical, not prose.** Decision requests (options, evidence,
  recommendation, reversibility, blast radius) answered by numbered, heading-defined rulings
  (ai-de's register discipline); gate at *plan* and at *irreversible action*, implemented as
  hooks with deterministic exit codes where the harness offers them; the reviewer never clears
  its own veto; an agent message is never consent. [findings 10–11]
- **Cost is a first-class axis.** Declare the ~15× / ~7× multiplier per plan; budget the main
  line, not only delegates (CTX-M); prefer Sonnet/Haiku-tier workers, Opus/Fable-tier Owner.

## How to use this base

Personas and the design skills cite these files as evidence (BoK §III.1). The proposal
`docs/proposals/owner-coordinator-subagent-coordination.md` is the first consumer. Constants
live in `data-and-constants.md`; the executed spike results are there too. Refresh when a
harness ships a new multi-agent surface (the fastest-moving facts here are Claude Code v2.1.x
features marked experimental / research preview) — re-run `/collectknowledge` and bump the date.
