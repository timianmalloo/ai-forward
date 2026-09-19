---
id: kb-multi-agent-coordination-data
title: "Domain data, constants & invariants — multi-agent coordination"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, constants, measurements, spikes]
links:
  - { to: kb-multi-agent-coordination, rel: refines }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  The numbers: measured fleet telemetry from ai-de and the pack's profiler, practitioner
  constants for leases, heartbeats, election and messaging, the scheduling formulae, cost
  multipliers, and the three executed git spikes with their exit codes.
---

# Domain data, constants & invariants

## Executed spikes (this session, macOS, git 2.54.0) — Verified by execution

| Spike | Case | Result |
|---|---|---|
| **SPK-1** local CAS `git update-ref <ref> <new> <old>` | create with `old` = 40 zeros, ref absent | exit 0 |
| | update with wrong `old` | exit 128 (refused) |
| | update with correct `old` | exit 0 |
| | create with zeros, ref present | exit 128 (refused) |
| **SPK-2** remote CAS `git push --force-with-lease=<ref>:<expect>` | correct expect, non-fast-forward, no `--force` | exit 0, "(forced update)" — the lease alone permits it |
| | stale expect, no `--force` | exit 1, "! [rejected] … (stale info)", remote unchanged |
| | stale expect **with** `--force` also passed | exit 0 — **`--force` overrides the lease**. Never combine. |
| **SPK-3** `merge=union` on an append-only ledger | two branches each append a `leader-claim` (epoch 1) | merge exit 0, **both lines survive** — the ledger cannot refuse a competing claim |
| | rebase instead of merge | exit 0, both lines, order differs from merge |
| | cherry-pick of an appending commit onto a branch with its own append | exit 0, three lines, zero conflict markers |
| | identical line appended on both sides | one line survives (git's ordinary three-way merge, union driver not invoked) |

## Harness CLI contracts executed on this machine (2026-09-19; `--help` read, not recalled)

| Harness · version | Headless entry | Structured output | Push into a running session | Isolation / resume |
|---|---|---|---|---|
| Claude Code 2.1.278 | `claude -p` | `--output-format json|stream-json`, `--json-schema`, `--input-format stream-json` | inbox socket (docs) · `--bg` background sessions with `claude agents|attach|logs|stop|rm|respawn` | `--resume <id>`; `--bare` skips hooks and binds no inbox socket |
| Codex 0.155.0 | `codex exec` | `--json` (JSONL events), `-o <file>` last message, `--output-schema <file>` | `codex queue --thread <uuid|name> --message <text>`; `app-server --listen stdio://|unix://|ws://`; `remote-control start|stop|pair` | `--worktree` (managed git worktree), `-C <dir>`, `--sandbox`, `--approve-for-me`; `codex exec resume`; `codex agents` lists daemon sessions |
| Antigravity 1.2.7 | `agy -p|--print|--prompt` | `--output-format text|json|stream-json`, `--json-schema` | `--input-format stream-json` — one NDJSON message per line runs one turn each (spawned child only); `--remote-control` daemon | `--conversation <id>` resume; `--mode accept-edits|plan`; `--model`; `--effort`; `--print-timeout`; `--sandbox` |
| Grok Build (installed) | `grok -p|--single <prompt>` | `--output-format plain|json|streaming-json (ACP)|streaming-messages-json`, `--json-schema` | none found | `--worktree[=name]`, `--worktree-ref`, `--resume`, `--session-id`, `--fork-session`, `--cwd`, `--max-turns`, `--permission-mode`, `--agents <JSON>`, `--no-subagents` |
| Copilot CLI | `copilot -p` (docs) | — | hooks only: `preToolUse` `additionalContext`; `agentStop`/`subagentStop` `decision: "block"` + `reason` (docs) | **not installed here** — docs-only |
| Shell hazard | zsh `"$C1:refs/x"` | `:r` modifier eats the variable; write `"${C1}:refs/x"` |

### Hook surfaces usable as a doorbell or a heartbeat (docs probes, 2026-09-19; execution pending except Claude Code)

| Harness | Tool boundary | Turn / invocation boundary | Stop-class | Push shape | Source |
|---|---|---|---|---|---|
| Claude Code 2.1.278 | `PreToolUse` / `PostToolUse` | `UserPromptSubmit`, `SessionStart` | `Stop`, `SubagentStop`, `TaskCompleted` (exit 2 blocks) | native cross-session message (socket + registry) — no hook needed | [P2P-26] |
| Codex 0.155.0 | — | — | — | `codex queue --thread --message` | [AC-6] |
| Antigravity 1.2.7 | `PreToolUse` / `PostToolUse` | `PreInvocation` → `injectSteps`; `PostInvocation` `terminationBehavior: force_continue` | `Stop` | inbox drained at `PreInvocation`, injected as steps | [AC-40] |
| Grok Build | Claude-format `PreToolUse` | `UserPromptSubmit` (`additionalContext`) | — | pull at the edge only | deployed hooks, observed |
| Copilot CLI | `preToolUse` (`additionalContext`; exit 2 fail-closed) | `sessionStart`, `userPromptSubmitted` | `agentStop`, `subagentStop` (`decision: "block"` + `reason`; 8-block guard) | pointer in `reason` becomes the next prompt | [AC-41][AC-42] |

A doorbell carries a **count and a pointer, never a body** (the body stays in the inbox file); a hook that injects the body would make the harness the store. Antigravity's `injectSteps` and Copilot's `reason` are the two channels that could smuggle a body in — the adapter contract forbids it.


## Measured fleet telemetry (read this session)

| Quantity | Value | Source |
|---|---|---|
| ai-de ledger events / sessions | 6,557 / 206 | `.agents/log/*.jsonl` |
| claims / releases → never released | 3,370 / 2,722 → 648 (19%) | same |
| session-start / session-end → never ended | 318 / 135 → 183 (58%) | same; DC-067 |
| enforcement decisions: allowed / not_checked / refused | 12,131 / 132 / 59 (0.48%) | `.agents/decisions/*.jsonl` |
| seam requests: add / resolve → unresolved | 577 / 324 → ~253 (28%) | `.agents/requests.jsonl` |
| watcher poll interval | 15 s | `session-contracts.md:2711` |
| longest measured stall (background node, `EnterWorktree` refusal) | 8,143 s | `addendum-cd.md:180`, DC-206 |
| conductor active time in joins/gates · in coordination logic | 44.8% · 0.7% | `addendum-cd.md` |
| two joins queued behind one lease | ~50 min | DC-163 |
| coordination sessions started in the primary checkout (one fleet) | 0 of 88 | `addendum-cd.md:188` |
| worktrees existing vs profiled sessions running inside one (3 repos, 48 sessions) | 16 vs 0 | `coord-core.py:2162`, SP-15 |
| main line share of session cost · per-request cost vs delegates | 91–92% · 10.4–11.6× | SP-19, sp-0004/5/8 |
| sub-agent runaway examples | 123 calls / 3.0 M tokens; 100 calls / 4.16 M tokens | SP-07 |
| pack lease TTL default / cap · session staleness window | 300 s / 900 s · 8 h | `coord-core.py:27-32` |
| Rulings defined by headings; numbers that defined nothing | 1–139; 8 (6 frozen) | `verify-ruling-citations.py` |

## Practitioner constants (Verified unless marked)

| Constant | Value | Source |
|---|---|---|
| Kubernetes leader lease: duration / renew deadline / retry / jitter | 15 s / 10 s / 2 s / 1.2; constraints `lease > renew`, `renew > retry × 1.2` | [QLE-5] |
| Kubernetes 2× clock-skew example | 60 s / 30 s | [QLE-5] |
| Kubernetes node liveness: update / grace / eviction | 10 s / 40 s / 5 min; `grace ≥ 3 × update` | [SCH-22] |
| etcd heartbeat / election | 100 ms / 1,000 ms; `broadcastTime ≪ electionTimeout ≪ MTBF` | [SCH-32] |
| etcd session TTL default · fencing token | 60 s · leader-key creation revision | [QLE-21] |
| Chubby: lock hold · grace period · KeepAlive · lease extension | minutes–hours · 45 s · ~12 s (Inferred) · ~60 s (Inferred) | [QLE-9][QLE-33] |
| Consul lock-delay | 15 s default, 0–60 s | [QLE-10] |
| Jepsen etcd lock loss | ~18% of acknowledged updates at 2 s TTL + 5 s pause | [QLE-6] |
| Raft election timeout (recommended) | 150–300 ms randomized (Inferred as recommendation) | [QLE-2] |
| memberlist Local profile: probe / timeout / indirect / suspicion mult / anti-entropy | 1 s / 200 ms / 1 / 3 / 15 s | [P2P-3] |
| Akka phi-accrual: heartbeat / threshold / acceptable pause / fires at / all-to-all cutoff | 1 s / 8.0 / 3 s / ≈5.5 s / 9 members | [P2P-6][P2P-7] |
| SWIM detection time | ≈1.58 protocol periods, independent of N | [P2P-2] |
| gossipsub v1.0 mesh | D=6, D_low=4, D_high=12, heartbeat 1 s, seen_ttl 2 min | [P2P-9] |
| Claude Code cross-session: size cap / queued / held / held expiry / line timeout / idle-notice TTL | ~1,000,000 chars / 50 / 100 / 5 min / 30 s / 12 h | [P2P-24] |
| Claude Code teams guidance | 3–5 teammates; ~7× tokens in plan mode; subagent cache TTL 5 min unless `subagentPromptCacheTtl: "1h"` | [AC-5][AC-10] |
| Claude Code `-p` background wait ceiling | 10 min idle | [AC-9] |
| Antigravity nesting · Grok Build parallel cap | 10 · 8 | [AC-21][AC-24] |
| Airflow zombie: heartbeat / threshold (Inferred) | 75 s / 300 s | [SCH-23] |
| Retry: full jitter · decorrelated (Inferred) | `random(0, min(cap, base·2^n))` · `min(cap, random(base, 3·prev))` | [SCH-20] |
| DLQ threshold (Inferred) | maxReceiveCount 3–5 | [SCH-21] |
| Outbox lag alarm (Flagged) | unpublished > 30 s | [P2P-28] |
| File-watch polling fallback | 5 s (0.5 s when native events unavailable) | [P2P-34] |
| CockroachDB HLC uncertainty (Flagged) | 500 ms | [P2P-14] |
| Merge conflicts in human development | 16% of merges | [SCH-16] |
| Conflict classifier (safe / conflicting P·R·F1) | 1.00·0.96·0.97 / 0.63·0.96·0.68 | [SCH-17] |
| ConE production | 234 repos, 26k PRs, 775 warnings, >70% useful | [SCH-18] |
| Token multipliers: agent vs chat · multi-agent vs chat · agent teams | ~4× · ~15× · ~7× | [AC-1][AC-10] |
| Multi-agent research lift · variance explained by tokens | +90.2% · 80% | [AC-1] |
| C-compiler run | 16 agents, ~2,000 sessions, 2 B in / 140 M out tokens, ~$20k, ~2 weeks | [AC-4] |
| MAST categories · top modes | spec 41.8% · misalignment 36.9% · verification 21.3%; step repetition 15.7%, termination-unaware 12.4%, disobey spec 11.8% | [AC-25] |
| CodeCRDT | +21.1% / −39.4%; 5–10% semantic conflicts; 600 trials | [P2P-17] |
| Agentless on SWE-bench Lite (Inferred) | 32.0%, $0.70 / instance | [SCH-31] |
| Google code review median latency (Inferred) | < 4 h | [SCH-34] |
| CVE-2025-66414 | CVSS 8.1 (v3); fixed MCP TS SDK 1.24.0; stdio unaffected | [P2P-20] |

## Formulae

- **Brent / work-span:** `T_P ≤ T1/P + T∞`; work stealing achieves `T1/P + O(T∞)`. Once
  `T1/P < T∞`, more workers buy nothing. *[SCH-5][SCH-6]*
- **Amdahl:** `S(N) = N / (1 + σ(N−1))`, ceiling ≈ `1/σ`. **USL:** `S(N) = N / (1 + α(N−1) + βN(N−1))`;
  `β > 0` ⇒ throughput declines past an optimum. β is the cross-agent merge/review cost. *[SCH-7]*
- **SWIM detection time:** `T' / (1 − e^(−q_f))`. *[P2P-2]*
- **memberlist suspicion timeout:** `SuspicionMult · log(N+1) · ProbeInterval` (log base Flagged). *[P2P-3]*
- **Phi:** `φ ≈ −log10 P(heartbeat merely late)`; φ = 8 ≈ 1 in 10⁸. *[P2P-7]*
- **Flexible quorums:** `|Q1| + |Q2| > N`; majority `⌊N/2⌋ + 1`; N = 2 ⇒ no survivor majority. *[QLE-4][QLE-16]*

## Recommended starting constants for this fleet (Inferred from the above — measure, then tune)

| Knob | Start value | Derivation |
|---|---|---|
| Leader lease duration / renew / retry | 300 s / 150 s / 20 s | k8s ×20 for a sleeping laptop fleet; 2× skew example |
| Quiet period after leader-lease invalidation | 30 s | Consul lock-delay ×2 |
| Path lease TTL default / cap | 300 s / 900 s (unchanged) | `coord-core.py`; DC-163 |
| Progress heartbeat interval / suspect / dead | TTL/3 / 3 missed / TTL | k8s, etcd, Airflow convergence |
| Anti-entropy full re-fold | 15 s | memberlist Local `PushPullInterval` |
| Worker width | 3–5 | Claude Code guidance; USL |
| Kicks per work item before escalation | 2 | prior proposal's cap, unmeasured — keep and count |
| Cross-harness request deadline | explicit per request; fallback recorded | ai-de "not waiting on Codex" |

## Invariants

1. A lease is an efficiency hint; a fenced write at the resource is the only mutual exclusion. *[QLE-6][QLE-7]*
2. Leadership lives in a CAS cell (a git ref) and is *recorded* in the ledger; a union-merged ledger cannot arbitrate. *[SPK-2][SPK-3]*
3. `--force` and `--force-with-lease` are never passed together; the three-part form is always used. *[SPK-2][QLE-11]*
4. The ledger is read at one commit, never ref-by-ref, because ref transactions are not reader-isolated. *[SCH-13]*
5. Every ledger line carries a stable id and an HLC-shaped stamp; order and dedup are fold-time properties. *[P2P-18][SPK-3]*
6. A heartbeat without a progress payload is not evidence of progress. *[SCH-8][AC-25]*
7. An empty fleet view is `NOT CHECKED`, never "all quiet" (R4, unchanged). *[REPO-ai-forward]*
8. An agent message is never consent; a denied action is never relayed through a peer. *[AC-5][AC-6]*
9. Two tracks never author one file or one MVC slice in the same window. *[SCH-17][SCH-19]*
10. A cross-harness request without a deadline and a recorded fallback is incomplete. *[REPO-ai-de]*
