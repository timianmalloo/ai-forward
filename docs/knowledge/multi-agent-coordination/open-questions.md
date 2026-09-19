---
id: kb-multi-agent-coordination-open-questions
title: "Open questions & domain failure modes — multi-agent coordination"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, open-questions, failure-modes, disconfirmation]
links:
  - { to: kb-multi-agent-coordination, rel: refines }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  What the research could not settle (with the cheapest probe for each), the domain's known
  failure modes, and the disconfirming views deliberately sought and how each fared.
---

# Open questions & domain failure modes

## Unresolved by research (Flagged) — with the cheapest probe

| # | Question | Why it matters | Cheapest probe |
|---|---|---|---|
| Q1 | Can Copilot CLI, Antigravity, Grok Build and Codex run a **blocking stop-class hook** (exit 2 keeps the agent working)? | Decides how far the portable push reaches beyond Claude Code | One doc page per harness; Copilot hook names (`agentStop`, `subagentStop`) are secondary-sourced only |
| Q2 | ~~Antigravity **headless flags**~~ **Resolved 2026-09-19 by execution:** `agy 1.2.7` has `-p/--print`, `--output-format json|stream-json`, `--json-schema`, `--input-format stream-json` (NDJSON turns from stdin), `--print-timeout`, `--mode`, `--model`, `--effort`, `--conversation` resume | agy can both host S1 and be an S1 spoke | done — see `state-of-the-art.md` §2 |
| Q3 | Copilot `/fleet` **isolation and merge semantics**; Codex subagent caps. Copilot CLI is **not installed on this machine**, so its rows stay docs-only; Codex `exec --help` executed (`--json`, `-o`, `--output-schema`, `--worktree`, `--sandbox`, `--approve-for-me`), subagent caps still not surfaced | S2 on those harnesses | Install Copilot CLI and run `/fleet` on a two-file task watching `git status`; `codex features` for subagent flags |
| Q4 | **Merge-conflict rate between parallel AI agents in worktrees** | The number the design most wants; only the 16% human baseline exists | Instrument the swarm: files per item, pairwise intersection, conflict yes/no, minutes to resolve |
| Q5 | ~~Does `merge=union` behave identically under **cherry-pick**?~~ **Resolved 2026-09-19 by execution:** cherry-pick of an appending commit onto a branch with its own appended line converges to three lines with zero conflict markers, exit 0 | Ledger convergence claim holds under merge, rebase and cherry-pick | done |
| Q6 | `memberlist` suspicion-timeout **log base** | Only if a borrowed constant is used | Read `suspicion.go` |
| Q7 | Current **MCP spec revision** beyond 2026-07-28 | Sampling deprecation clock | Read the spec version banner |
| Q8 | Chubby's exact KeepAlive/extension figures (12 s / 60 s are secondary) | Constants only | `pdftotext` the OSDI paper |
| Q9 | Windows **named-pipe ACL** restricted to the current SID in .NET | If ai-de hosts a pipe | C# spike with `PipeSecurity` |
| Q10 | Whether ownership → quality survives modern code review (Thongtanunam 2016) | Strength of "one owner per artifact" | Read the ICSE 2016 abstract |
| Q11 | Magentic-UI's "+71%" uplift (secondary) | Owner-review benefit sizing | §Evaluation of arXiv 2507.22358 |
| Q12 | Cognition's revised 2026 position (X post) | Disconfirmation currency | Read the post |
| Q13 | Copilot **session-start** hook and **deny at the edit boundary** on this machine | HARNESS_STATUS currency; still 2026-08 spike results | Re-qualify per version (pack rule) |

**Negative result:** *"AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared
Workspace (arXiv:2608.23740)"*, cited by both prior proposals, **could not be found** under that
title, identifier or author. Do not cite it until a URL is produced.

## Known failure modes of this domain

- **Lost updates under a lease** — a paused holder resumes after expiry and overwrites; only
  resource-side fencing prevents it (Jepsen 18% loss; HBase). *[QLE-6][SCH-12]*
- **Split-brain leadership after laptop sleep** — Linux monotonic clocks stop during suspend,
  macOS's do not; an NTP step after wake expires a live lease instantly. *[QLE-17]*
- **Union-merged claims both "win"** — the ledger records two leaders; nothing refuses one. *[SPK-3]*
- **`--force` silently defeating `--force-with-lease`.** *[SPK-2]*
- **Registration without enlistment** — sessions start and never end (58% in ai-de), claims
  never release (19%); liveness read from a ledger lies Alive (DC-067, DC-024). *[REPO-ai-de]*
- **Pull that nothing reads** — a board with zero callers; standing files nobody opens; stalls
  discovered by the operator (8,143 s). *[REPO-ai-de]* (COORD-O, p57)
- **Free-text ACK loops** — request/resolve without typed states produces "your quote is not the
  consumer evidence" churn; 28% of requests never resolve. *[REPO-ai-de]*
- **Step repetition and termination-unaware loops** (15.7% + 12.4% of MAST failures) — invisible
  to a liveness heartbeat. *[AC-25]*
- **Duplicate work from vague delegation**; **telephone-game summarisation** through model
  contexts. *[AC-1][AC-2]*
- **Same-file / same-slice overwrites** — the C-compiler kernel task; Claude Code teammates not
  worktree-isolated. *[AC-4][AC-5]*
- **Cost blow-ups** — 15× / 7× multipliers; sub-agent runaways of 3–4 M tokens (SP-07); main line
  at 91% of spend (SP-19). *[AC-1][REPO-ai-forward]*
- **Lock-holding collapse** — equal-status agents holding locks too long: 20 agents → throughput
  of 2–3 (Flagged, secondary). *[P2P-38]*
- **Mailbox corruption blocking delivery** (Claude Code pre-2.1.207) — validate and repair on
  read; per-writer-owned files. *[P2P-25]*
- **Localhost is not a boundary** — DNS rebinding against unauthenticated loopback HTTP. *[P2P-20]*
- **Control currency** — a worktree branched before a control exists enforces yesterday's rules
  (COORD-I / DC-226). *[REPO-ai-forward]*
- **Coordination doctrine with no home** — rules spread across WT, CT27, GO7/GO14a/GO19, two
  skills and six ADRs; no always-loaded document (drm-0010 p58). *[REPO-ai-forward]*
- **Parent enters a worktree after delegating** — sub-agents spawned before the parent's
  `EnterWorktree` lose their Bash tool to the worktree guard for the rest of their run; observed
  four times in this session (each researcher delivered inline instead of to disk). *(Verified
  by observation, [OBS-3])*

## Disconfirming views we deliberately sought

| View | Strongest form | How it fared |
|---|---|---|
| "Single strong agent beats multi-agent" | Cognition: parallel sub-agents make conflicting implicit decisions; use one linear agent + context compression. Agentless beats agent frameworks on SWE-bench Lite at $0.70. | **Survives for writes without an oracle; fails as a universal rule.** Research (+90.2%) and the C-compiler run are counterexamples, each with the enabling condition (read-only work; a strong oracle). Multi-agent for review and research is well-evidenced; for implementation it must earn parallelism. *[AC-2][SCH-31][AC-1][AC-4]* |
| "Multi-agent costs more" | AssetOpsBench: single-agent used ~2× the tokens (121k vs 63k). | **Does not overturn 15×/7×** — the authors attribute it to scenario mix. Never compare token totals across architectures without fixing the task distribution. *[AC-38]* |
| "You don't need a bus — git is enough" | Coordination is git history plus a 5-minute cron sync. | **Survives for durable, auditable state; fails for latency and interruption.** The vendor shipping this feature chose a per-session socket with turn injection. Git is the ledger, not the bus. *[P2P-30S][P2P-24]* |
| "Polling at 5 s is fine for N < 10" | Meteor's 5 s fallback; polling coalesces writes. | **Survives as anti-entropy backstop, fails as primary** — a polled inbox only helps an agent already in a loop; push wakes a teammate out of retry backoff. *[P2P-34][P2P-25]* |
| "Phi-accrual is overkill" | Akka monitors all-to-all below 9 nodes. | **Upheld decisively.** Fixed-TTL lease + process liveness. *[P2P-6]* |
| "Use a real CRDT for shared state" | Automerge 3 / y-crdt are excellent and current. | **Rejected for this scope** — leases must be refused, not merged; CodeCRDT −39% worst case. *[P2P-15][P2P-17]* |
| "You never need election with a human present" | ICS, STO, FLP, no STONITH. | **Mostly survives, one carve-out:** a leader that dies at 02:00 must be reclaimable automatically after lease expiry — reclamation yes, contested promotion no. *[QLE-1][QLE-20]* |
| "Raft for 3 nodes on a laptop is absurd; use a lease file" | Chubby's service-over-library rationale. | **First clause survives, second fails** — a lease file is `flock`/`O_EXCL` with no epoch and no resource-side check; use git-ref CAS + epoch + join check. *[QLE-9][QLE-12][QLE-13]* |
| "Epochs without a fenced store are theatre" | A practitioner modelled fencing tokens and still violated mutual exclusion because the resource never checked. | **Survives completely and changes the design:** the epoch is checked where the effect lands (the join / `update-ref`). *[QLE-22]* |
| "The union-merged ledger can hold the leadership claim" | First append wins; the fold is the total order. | **Fails by execution** — both claims survive with exit 0. *[SPK-3]* |
| "An LLM judge can break ties" | Cheap arbitration. | **Fails** — non-deterministic, loops without arbitration rules, confident-wrong; use a lexicographic rule. *[QLE-18][QLE-27]* |
| "The harness gives you a coordinator" | Agent teams, `/fleet`, subagents. | **Survives fully** — lead fixed for life, no nested teams, no cross-harness anything; durable state must live in the pack. *[AC-5][AC-18]* |
| "Agents can coordinate approvals among themselves" | A Coordinator approving for the human. | **Survives as a hard constraint** — the harness forbids it by design. *[AC-5][AC-6]* |
| "Central assignment beats stealing at small N" | Sharing wins below load ≈ 0.618. | **Partly** — stealing wins under high duration variance, but conflicts with ownership alignment; central for the first and any seam-touching item, stealing only from a seam-free queue. *[SCH-38][SCH-15]* |
| "Durable execution is overkill for < 20 tasks" | Temporal for a laptop. | **Supported** — import the timeout taxonomy and the DLQ ladder, not the runtime. *[SCH-8]* |
| "Parallel agents produce more conflicts than they save time" | 16% human base rate; Cognition; MAST 37% misalignment. | **Best-evidenced objection** — answered only by interface-first splitting, one owner per artifact, zero tolerance for two tracks in one slice, and measuring the rate (Q4). *[SCH-16][SCH-17][SCH-19]* |
