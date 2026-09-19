---
id: kb-multi-agent-coordination-comparables
title: "Comparable solutions & problem framings — multi-agent coordination"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, comparables]
links:
  - { to: kb-multi-agent-coordination, rel: refines }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  How existing systems frame and solve the three scenarios — harness-native fleets, managed
  hierarchies, blackboard-over-git, cluster schedulers, lock services and the two in-house
  attempts (ai-de and the pack's coord layer) — with what each does well and badly.
---

# Comparable solutions & problem framings

| Solution / source | How it frames the problem | Approach | Does well | Does badly | Confidence |
|---|---|---|---|---|---|
| **Claude Code agent teams + cross-session messaging** [AC-5][AC-6][P2P-24] | Fleet of full sessions under a fixed lead; sessions on one machine message each other | File-locked task list, per-agent mailbox, per-session socket + token, turn injection, hooks exit 2 | Push that reaches an idle session; loop self-termination; permission laundering forbidden by design | Lead cannot be transferred; no nested teams; teammates not worktree-isolated; absent under `-p`; ~7× tokens | Verified |
| **Claude Managed Agents** [AC-27][AC-28] | Lead + specialists on a shared filesystem with persistent events | Cloud sessions, steer-or-interrupt API, per-specialist model/prompt/tools | The cleanest Owner/Coordinator/Sub-Agent instance; mid-run steering | Cloud only; stateful sessions (no ZDR); not a CLI harness | Verified |
| **Anthropic C-compiler run** [AC-4] | 16 parallel Claudes over one repo, no messaging | git + `current_tasks/*.txt` lock files + READMEs/progress files + a strong oracle (GCC) | Write-parallelism at scale with an oracle | Monolithic tasks: agents overwrite each other; ~$20k | Verified |
| **Copilot CLI `/fleet`** [AC-18] | Main agent becomes orchestrator, dispatches background subagents | Own context per subagent; explicit dependencies | S2 on Copilot | No documented isolation, merge or cap semantics; no push | Verified / Flagged |
| **Antigravity subagents** [AC-21] | Concurrent sessions with roles; peer messaging by conversation id; workspace `branch` = worktree | `invoke_subagent` / `define_subagent`, nesting ≤ 10 | Only harness with first-class peer-to-peer subagent messaging | No external push; headless flags unverified; process-global MCP registration race on spawn-many [QLE-19] | Verified / Flagged |
| **Codex** [AC-23] | Manager + sandboxed workers; app-server as control plane | `codex exec --json`, `app-server --listen ws://`, `--remote` | The only non-Claude harness with a socket control plane | Subagent caps undocumented; open issue for a shared bus (#21027) [P2P-32] | Verified / Flagged |
| **pact** [QLE-19] | Cross-harness orchestrator (Claude Code, Copilot, Codex, Gemini, Antigravity) in worktrees | SQLite/WAL coordinator MCP, advisory file claims | Worktree isolation across five harnesses | Its own README: claims "not yet reliable under concurrency" | Verified |
| **ai-de (consuming repo, live lab)** [REPO-ai-de] | Five harnesses on one product, files-in-one-repo as the channel | Session-contract ownership register; `.agents/` ledgers (tracked); 15 s watcher poll; handshake revisions frozen by blob hash with PRODUCER/CONSUMER ACK; numbered Rulings defined by headings; join contract as a script | The handshake + ruling register is the only cross-harness protocol that measurably worked; ownership register single-sourced | 58% of sessions never end, 19% of claims never release, 28% of 901 requests unresolved; free-text ACK loops; PreToolUse not wired; 8,143 s stall in a background node; 44.8% of conductor time in joins | Verified (read this session) |
| **AI-Forward coord layer (Phases 1–4)** [REPO-ai-forward] | Claims not commits; append-only per-session JSONL folded on demand; no daemon | 21 `coord` verbs; leases 300/900 s; artifact classes + merge drivers; allocator; seam requests; worktree lifecycle; two skills | Fail-to-NOT-CHECKED discipline; artifact classification removes most contention; stdlib only | No leader, inbox, board, heartbeat or push; liveness = 8-hour staleness window; `HARNESS_STATUS` a constant; ledgers gitignored by default | Verified |
| **Omega / Borg / Mesos** [SCH-1][SCH-2][SCH-3] | Cluster scheduling: monolithic vs two-level vs shared-state optimistic | Optimistic transactions on shared cell state; conflicts at commit | Names the architecture the pack has; incremental transactions | Offer-based locking for slow deciders | Verified |
| **Chubby / etcd / Consul / ZooKeeper** [QLE-9][QLE-21][QLE-10][QLE-14] | Lock/lease services with sequencers, lock-delay, ephemeral nodes | Coarse locks (minutes–hours), fencing via generation numbers, 45 s grace, 15 s lock-delay | The vocabulary and constants for a fenced leader lease | A cluster to run for five local processes | Verified |
| **Kubernetes leader election (`client-go`)** [QLE-5] | Lease object with holder identity | 15 s / 10 s / 2 s defaults, jitter 1.2 | Worked clock-skew example (60 s / 30 s for 2×) | Says in source: no fencing; alpha API | Verified |
| **Temporal / durable execution** [SCH-8][SCH-36] | Deterministic replay, heartbeats with progress, timeout taxonomy | Workflow + activities | The timeout classes and progress heartbeat | A runtime the fleet does not need | Verified / vendor |
| **CodeCRDT** [P2P-17] | Agents coordinate by observing a CRDT of the code | Claim TODO placeholders in shared state | 100% syntactic convergence | +21% best / −39% worst; 5–10% semantic conflicts; task structure decides outcome | Verified |
| **Magentic-UI** [AC-26] | Human in the loop with co-planning and action guards | Plan editor, approval before irreversible actions | Where the Owner's gates belong | Browser-task domain | Verified |

## Adjacent problems worth borrowing from

- **Incident command / single-threaded owner** — appointed leadership with explicit handover;
  a defined reorganisation phase on takeover. *(Verified, [QLE-20][QLE-34][QLE-15])*
- **Transactional outbox** — write the state change and the event in one place (the ledger
  line), relay from it; at-least-once + idempotency key = effectively once. *(Verified, [P2P-27])*
- **Merge-conflict prediction (ConE, Owhadi-Kareshk)** — simultaneously-changed files as the
  contention signal for decomposition. *(Verified, [SCH-17][SCH-18])*
- **Code ownership → defects (Bird et al.)** — one owner per artifact as a quality control.
  *(Verified, [SCH-15])*
- **Transport parity (Node `net`, Claude Code)** — Unix socket on POSIX, named pipe on Windows;
  reap stale socket files on POSIX only. *(Verified, [P2P-22][P2P-24])*
- **Meteor file watching** — 5 s stat polling as a fallback/anti-entropy, not the primary channel.
  *(Verified, [P2P-34])*
