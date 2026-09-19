---
id: note-20260919-coordination-decisions-ratified
title: "Coordination decisions ratified: local message layer with git as the fallback, a board for humans, tracked ledgers, lease constants"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, messaging, board, leases, skills]
links:
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
  - { to: kb-multi-agent-coordination, rel: relates-to }
  - { to: note-20260919-leadership-in-a-ref-not-the-ledger, rel: relates-to }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  On 2026-09-19 the maintainer answered the proposal's four open questions and ratified four of
  its five design decisions; on the fifth (push channels) they asked for a formal local message
  layer with a human-readable board, keeping git as the fallback. D9 is revised, D12 and D13 are
  new, the build plan gains P6-P8 (board, compile stage, skill evolution). Blast radius: the two
  coordination skills first, then every skill that dispatches or is dispatched.
---

# Coordination decisions ratified (2026-09-19)

**Record:** `docs/proposals/owner-coordinator-subagent-coordination.md` §4b, §7, §7b, §9, §10.

## The rulings, verbatim in substance

| # | Question or decision | Ruling | Effect |
|---|---|---|---|
| Q1 | Ledger tracking default | **Change it** — the pack default tracks `.agents/log/` | D10 ratified; `pack-apply` stops ignoring the ledgers; `coord doctor` reports which mode a repo is in |
| Q2 | Leader lease constants | **TTL 300 s, quiet period 30 s** | D13: renew every 100 s (TTL/3), retry 20 s; tuned from `coord metrics`, never hand-edited |
| Q3 | Copilot as an S1 target | **Probe first; inbox + commit floor is acceptable** | Docs probe done the same day: `agentStop`/`subagentStop` return `decision: "block"` + `reason`, `preToolUse` returns `additionalContext`; a real stop-class doorbell. Status `observed-only` until a live drain is seen |
| Q4 | Antigravity hook surface | **Probe it** | Docs probe done the same day: `PreToolUse`, `PostToolUse`, `PreInvocation` (`injectSteps`), `PostInvocation` (`terminationBehavior: force_continue`), `Stop`. Heartbeat (P3) and doorbell (P4) both have a hook to hang on |
| D1 | Leadership by designation in a ref | **Yes** | unchanged |
| D2 | Path leases stay efficiency locks at 300/900 s | **Ack** | unchanged |
| D3 | Five-part delegation contract | **Yes** | the contract is also the compiled prompt's shape (P7) |
| D4 | Owner review as decision request → numbered ruling | **Ack** | unchanged |
| D5 | Push channels | **Not as proposed.** A **board** for human transparency instead of reading git; **git stays the fallback**; **formalise local message passing** across harnesses, because a Claude Code session with inter-agent messaging is far more effective than one without | D9 revised, D12 new; §4b; P4 and P6 |

Added the same day by the maintainer, folded into the same spec:

- **Skills must evolve with the spec** — every skill that dispatches or is dispatched is re-cut for seats, contracts, mail, board and Owner review (§7b, P8).
- **A compile stage** — the operator's prose is compiled into the harness- and model-specific starting prompt *before* `/optimize-graph` or `/prepare-for-coordination` run (§7b, P7).

## Why the message layer is not the struck "bus"

The struck item was a **daemon or broker as the store**. The ratified layer keeps the store in files (`.agents/mail/<session>.jsonl`), uses each harness's own doorbell for the push, and degrades to the inbox plus the union-merged ledger plus a deadline when no doorbell exists. That is Claude Code's shipped design generalised, and it satisfies the fallback rule the maintainer set: nothing is lost if the doorbell never rings.

## What would reopen this

- A live session on Copilot or Antigravity that does **not** drain the inbox at the documented hook — the adapter drops to `unsupported` and the floor carries it (D8).
- `coord metrics` showing false leader takeovers at 300/30 — lengthen, never shorten, first.
- A board that people stop reading (read-rate zero after two sprints) — the same trigger that struck the earlier board.
