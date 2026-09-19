---
id: kb-multi-agent-coordination-sota
title: "State of the art — multi-agent coordination"
type: knowledge
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [multi-agent, coordination, harness-primitives, protocols, leases, leader-election]
links:
  - { to: kb-multi-agent-coordination, rel: refines }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  Current best practice across four fields the pack must draw on: orchestration patterns and
  harness-native multi-agent surfaces (2026), peer-to-peer membership and messaging at small
  scale, distributed work scheduling and lease/fencing discipline, and quorum/leader election —
  each with where it wins, where it fails, and what is over-engineered at 2–20 sessions.
---

# State of the art — multi-agent coordination

Citation tags: `[AC-n]` agentic-coordination track · `[P2P-n]` p2p track · `[SCH-n]` scheduling
track · `[QLE-n]` quorum/leader-election track · `[SPK-n]` executed spike · `[OBS-n]` observed in
this Claude Code session · `[REPO-…]` repository evidence. Full list in `sources.md`.

## 1. Orchestration patterns (agentic)

- **Orchestrator-worker over read work** — lead plans, spawns isolated-context workers, *one*
  agent synthesises. The only pattern with published production numbers: Opus lead + Sonnet
  workers beat single Opus by 90.2% on Anthropic's research eval; ~15× chat tokens; token usage
  explains 80% of variance. Delegation must carry objective, output format, tool/source guidance
  and explicit boundaries or workers duplicate each other. *(Verified, [AC-1])*
- **Blackboard over a shared repository for write work** — Anthropic's C-compiler run: 16 Opus
  4.6 instances, ~2,000 sessions, ~$20k, coordinated by git plus `current_tasks/<task>.txt`
  lock files and *no messaging*; failed on the monolithic kernel task (all agents fixed the same
  bug and overwrote each other); succeeded where a test oracle (GCC) and granular tasks existed.
  Claude Code agent teams are the productised hybrid: file-locked shared task list + per-agent
  mailbox. *(Verified, [AC-4][AC-5])* **Blackboard is the only pattern that survives a
  cross-process, cross-harness boundary, because its substrate is the filesystem.**
- **Supervisor / hierarchical** (LangGraph) — simpler and more accurate routing at a latency
  cost; graduate to swarm only with data. **Handoff vs agent-as-tool** (OpenAI Agents SDK) —
  a handoff transfers the conversation; agent-as-tool keeps the caller's continuity. For a
  Coordinator, agent-as-tool is the default; a handoff destroys the Coordinator's state.
  *(Verified, [AC-29][AC-30])*
- **Swarm / group chat** — no leader ⇒ no single place to enforce a review gate; poor fit for
  an Owner role. *(Verified pattern, Flagged efficacy, [AC-5][AC-30])*
- **Managed hierarchy as a product** — Claude Managed Agents (beta 2026-04-08; multi-agent
  orchestration 2026-05-06): lead + specialists on a shared filesystem, persistent events, a
  first-class *steer-or-interrupt* API. The closest commercial instance of Owner / Coordinator /
  Sub-Agent. *(Verified, [AC-27][AC-28])*
- **Where the frontier is honest:** Anthropic — "most coding tasks involve fewer truly
  parallelizable tasks than research"; Cognition — parallel sub-agents make conflicting implicit
  decisions; LangChain reconciles both on the read/write axis. *(Verified, [AC-1][AC-2][AC-3])*

## 2. Harness-native multi-agent surfaces (2026-09, official docs)

| Harness | Fan-out primitive | Push into a running session | Headless (executed `--help` on this machine, 2026-09-19, unless noted) | Isolation | Hard limits |
|---|---|---|---|---|---|
| **Claude Code 2.1.278** | Agent tool (subagents, `model` override, `isolation: worktree`, background); agent teams (experimental, lead + full sessions, file-locked task list, mailbox); `Workflow`; `/batch`; **background sessions** (`--bg`; `claude agents|attach|logs|stop|rm|respawn`) | **Yes** — per-session UDS/named pipe + token, file registry (`~/.claude/sessions/<pid>.json` observed), delivered between tool calls or as a new turn when idle; `SendMessage`/`ListAgents`/`notify_when_idle` observed; Channels (research preview) | `claude -p` · `--output-format json|stream-json` · `--json-schema` · `--input-format stream-json` · `--permission-mode` · `--permission-prompts` · `--agents <json>` · `--resume` · `--bare` (no hooks, no inbox socket) | worktree per subagent optional; teammates **not** isolated | one team per session; **no nested teams; lead fixed for life**; teammates absent under `-p`; ~7× tokens in plan mode |
| **Codex 0.155.0** | manager + sandboxed workers (caps still Flagged); `codex agents` browses sessions on the shared local app-server daemon | **Yes** — `codex queue --thread <uuid|name> --message <text>` queues a message into an existing session; `app-server --listen stdio://|unix://|ws://IP:PORT`; `--remote` + `--remote-auth-token-env`; `remote-control start|stop|pair` | `codex exec --json -o <last-message-file> --output-schema <file> --worktree -C <dir> --sandbox <mode> --approve-for-me`; `codex exec resume` | `--worktree` = managed git worktree; sandbox | approvals: `--approve-for-me` routes through automatic review; the bypass flag is labelled "EXTREMELY DANGEROUS" |
| **Copilot CLI** | `/fleet` (orchestrator + background subagents, own context each) | **Hook-drained inbox only (docs, 2026-09-19)** — `preToolUse` returns `additionalContext`; `agentStop` / `subagentStop` return `decision: "block"` + `reason`, injected as the next prompt (8 consecutive blocks → runaway guard, `stop_hook_active`); `sessionStart`/`userPromptSubmitted` for counts; `bash`/`powershell` arms; `preToolUse` exit 2 fail-closed [AC-41][AC-42]. No process-level push into a session | `copilot -p`; `--allow-all-tools` = user's full access — **not installed on this machine; docs only** | undocumented (Flagged) | "inherently sequential ⇒ no benefit" |
| **Antigravity 1.2.7** | `invoke_subagent` / `define_subagent`; `.agents/agents/<name>.md`; peer-to-peer subagent messaging by conversation id; workspace `inherit|branch|share` | **Spawned only** — `--input-format stream-json` reads one NDJSON message per line from stdin and runs a turn for each (requires `--output-format stream-json`): a per-turn push into a print-mode child. No process-level push into an interactive session; `--remote-control` daemon exists. **Hooks (docs, 2026-09-19):** `PreToolUse`, `PostToolUse`, `PreInvocation` → `injectSteps` (context pushed into the trajectory), `PostInvocation` with `terminationBehavior: force_continue` (keeps the agent working), `Stop` — an inbox drained at `PreInvocation` is a real doorbell [AC-40] | `agy -p|--print|--prompt` · `--output-format text|json|stream-json` · `--json-schema` · `--print-timeout` · `--mode accept-edits|plan` · `--model` · `--effort low|medium|high` · `--agent` · `--conversation <id>` · `--dangerously-skip-permissions` · `--sandbox` | `branch` = worktree | nesting depth 10; process-global MCP registration race on spawn-many [QLE-19] |
| **Grok Build** | `spawn_subagent --parallel` (≤ 8); `--agents <JSON>` inline definitions; `--no-subagents` | none found in `--help` | `grok -p|--single <prompt>` · `--output-format plain|json|streaming-json (ACP updates)|streaming-messages-json` · `--json-schema` · `--max-turns` · `--permission-mode` · `--allow/--deny` · `--worktree[=name]` · `--worktree-ref` · `--resume/--session-id/--fork-session` · `--cwd` | worktree per child; `--worktree` for the session | ≤ 8 parallel |

Sources: *(Verified, [AC-5][AC-6][AC-7][AC-8][AC-9][AC-18][AC-19][AC-21][AC-23][AC-24][OBS-1][OBS-2][OBS-4])*.
**Consequence (revised after the CLI probes):** S2 is fully supported on all five today; **S1 is
achievable today as a spawned subprocess on Claude Code, Codex, Antigravity and Grok** (each has
a print mode with JSON output and a schema), with mid-run steering for Claude Code (inbox
socket), Codex (`queue`, app-server) and Antigravity (stdin `stream-json` turns); Copilot is
docs-only here. S3 has zero protocol support anywhere and must be built on the shared substrate.
*(Verified by execution, [OBS-4])*

## 3. Inter-agent protocols (2026-09)

- **MCP 2026-07-28**: stateless core, MRTR (mid-call input without a held stream), Tasks moved
  to an extension, **Roots, Sampling and Logging deprecated** (12-month runway), HTTP+SSE
  deprecated in favour of Streamable HTTP; universally adopted by the five harnesses.
  *(Verified, [AC-11][AC-12][AC-34])*
- **A2A v1.0** (Apr 2026, Linux Foundation / AAIF with MCP since 2026-08-17): Agent Card, eight
  task states, SSE + webhook push, mTLS/OAuth2 — **no harness in scope implements it**, and it
  specifies no leader election. Treat as a future optional transport. *(Verified spec, Flagged
  adoption, [AC-13][AC-14][AC-15])*
- **"ACP" is four protocols.** Zed's Agent Client Protocol (editor↔agent, stdio JSON-RPC) is
  adopted by Claude Code, Codex, Copilot, Gemini CLI; IBM's merged into A2A; Cisco/AGNTCY's is
  archived. *(Verified, [AC-16][AC-17][AC-33])*
- **ANP** (did:wba, federated messaging) — "not yet ecosystem-ready". *(Verified existence,
  Flagged adoption, [AC-32])*

## 4. Peer coordination at small scale (p2p)

- **The shipped reference implementation is not a bus.** Claude Code cross-session messaging =
  file-registry discovery + one socket per session + per-session token + turn injection; loops
  self-terminate (per-sender rate limit, identical-repeat drop, ≤50 queued, ≤100 held, 5-minute
  held-message expiry, ~1 M-char cap). *(Verified, [P2P-24])*
- **Membership/failure detection:** SWIM's detection time is constant in N (≈1.58 protocol
  periods) — no value at N ≤ 20 on one host; memberlist's *Local* profile constants (probe 1 s,
  timeout 200 ms, anti-entropy 15 s) are reusable. Phi-accrual (Akka: threshold 8 ≈ fires at
  5.5 s) is for variable network latency; Akka stops all-to-all monitoring only above 9 nodes.
  **Lease expiry is a failure detector you do not have to build.** *(Verified, [P2P-2][P2P-3][P2P-6][P2P-8])*
- **Gossip is the wrong tool at N ≤ 20** (gossipsub `D_high = 12` exceeds the fleet; the mesh is
  the full graph). Keep only the *anti-entropy* idea: a periodic full re-fold. *(Verified, [P2P-9][P2P-10])*
- **Convergence:** a union-merged append-only JSONL is a grow-only set — commutative, idempotent,
  but **order-free and duplicate-tolerant**; order and identity must be *in the line* (HLC-shaped
  stamp `(wall_ms, counter, session)` + stable id) and resolved at fold time; `merge=union` must
  be path-scoped to ledgers only. Executed: merge and rebase both converge; identical lines added
  on both sides collapse to one by git's ordinary three-way merge. *(Verified, [P2P-13][P2P-14][P2P-18][SPK-3])*
- **Push vs pull evidence:** push wakes a teammate out of API-retry backoff; pull-only designs
  must *park* a finished agent in a sleep-poll loop to keep it addressable. A `Stop`-class hook
  that drains an inbox and exits 2 is the portable push. *(Verified, [P2P-25][P2P-26][P2P-29])*
- **Security:** loopback binding is not a boundary (CVE-2025-66414, DNS rebinding against
  localhost MCP servers, CVSS 8.1; stdio unaffected). On one machine the OS user is the trust
  boundary; Claude Code restricts the socket to the OS user and requires a token on Windows.
  mTLS/DID (A2A/ANP) defend a boundary this fleet does not have. *(Verified, [P2P-20][P2P-21][P2P-24])*

## 5. Work scheduling, leases and fencing (distributed scheduling)

- **The architecture has a name: shared-state optimistic scheduling (Omega).** Coordinator owns
  the plan, workers hold leases, git is the shared cell state, conflicts are detected at commit.
  Works while conflict rates stay low; degrades with schedulers × decision time. Offer-based
  (Mesos) allocation locks a resource for the whole decision — wrong for minutes-long thinkers.
  A single monolithic coordinator is not the bottleneck at 3–15 workers (Borg scale).
  *(Verified taxonomy, [SCH-1][SCH-2][SCH-4])*
- **Leases are efficiency locks; fencing tokens are correctness.** Kleppmann: the token "by
  itself does nothing" — the *resource* rejects lower tokens; HBase had the bug. Chubby shipped
  it in 2006 as the sequencer (name + mode + lock generation) plus lock-delay. Git's
  `update-ref` CAS is the free fencing store; its multi-ref transaction is atomic for writers but
  **not isolated for readers** — read the ledger at one commit, never ref-by-ref.
  *(Verified, [SCH-10][SCH-12][SCH-13][SPK-1])*
- **Heartbeat/timeout ratios cluster at 3–4×** (k8s 10 s / 40 s; Airflow 75 s / 300 s; etcd 10×).
  Temporal's four timeout classes (schedule-to-start, start-to-close, heartbeat, schedule-to-
  close) and heartbeats that *carry progress* are the semantics to import without the runtime.
  Retry with full or decorrelated jitter; a per-item circuit breaker stops reassigning a poison
  item to fresh workers — the Owner is the breaker's fallback path. *(Verified, [SCH-8][SCH-20][SCH-22][SCH-35])*
- **Decomposition:** Brent `T_P ≤ T1/P + T∞` — shorten the critical path before widening;
  USL's coherency term βN(N−1) makes the optimum worker count finite; HEFT ranks by longest
  remaining path and assigns to the tier finishing earliest (heterogeneous by premise); mirroring
  imprints the partition on the code (up to 8× in change propagation). *(Verified/Inferred, [SCH-5][SCH-6][SCH-7][SCH-14][SCH-33])*
- **Conflict predictors:** 16% of human merges conflict; the strongest predictor is files
  changed simultaneously on both branches; same-MVC-slice contributions and larger contributions
  conflict more; ConE productionized "extent of overlap" + "rarely concurrently edited files".
  *(Verified, [SCH-16][SCH-17][SCH-18][SCH-19])*
- **Assignment:** central assignment for the first item and any seam-touching item (ownership
  alignment, Bird et al.); stealing only from an explicitly seam-free ready queue via CAS. Contract
  Net's announce/bid/award is a cheap capability probe at one extra round trip. *(Inferred, [SCH-15][SCH-24][SCH-38])*

## 6. Leader election and quorum (quorum & leader election)

- **FLP:** no deterministic election terminates in all runs; bound it and escalate to the human.
  **Two nodes cannot self-elect**; every HA product adds a witness — the human is the cheapest
  correct witness in this fleet. *(Verified, [QLE-1][QLE-16][QLE-36])*
- **Raft/Paxos/ZAB protect a replicated log; git already is that log.** Chubby's rationale for a
  service over a Paxos library applies. Reusable ideas only: monotonic terms/epochs minted by a
  consistent store; pre-vote; leadership *transfer* (stop accepting work → bring successor up to
  date → explicit handover); Garcia-Molina's reorganisation phase (pending work finished or
  discarded). *(Verified, [QLE-2][QLE-3][QLE-9][QLE-14][QLE-15])*
- **Lease-based leadership, correctly:** epoch minted by the CAS store, stamped on every
  effectful action, rejected at the resource when lower, expiry computed with a skew budget on
  both sides (`RenewDeadline < LeaseDuration`), a lock-delay quiet period after invalidation,
  and a clock that behaves the same across suspend — Linux `CLOCK_MONOTONIC` stops during
  suspend while macOS's does not; Windows has no boottime clock. *(Verified, [QLE-5][QLE-10][QLE-17])*
- **Designation beats election when the set is small and known, a human is present on the
  failure timescale, a wrong automatic decision costs more than a stall, and no STONITH exists.**
  Incident Commander and Single-Threaded Owner are appointed and handed over. An LLM judge is
  a worse tiebreak than a lexicographic rule. *(Verified precedent, Inferred mapping, [QLE-20][QLE-34][QLE-18])*
- **2026 tooling evidence:** `pact` (worktree isolation across Claude Code / Copilot / Codex /
  Gemini / Antigravity) ships with "file-claim coordination is advisory/experimental, not yet
  reliable under concurrency" and documents an Antigravity process-global MCP registration race
  on spawn-many. *(Verified, [QLE-19])*

## 7. Human-in-the-loop and the Owner seat

- Magentic-UI: co-planning (edit the plan before any action), action guards before irreversible
  actions with configurable frequency; human help needed on ~10% of tasks. *(Verified, [AC-26])*
- Claude Code auto-approves a teammate's plan in the lead's session; `TaskCompleted` /
  `TeammateIdle` hooks exit 2 to reject and feed back — review as a process, not a model turn.
  *(Verified, [AC-5])*
- MAST: verification is 21.3% of failures; a dedicated verifier (CitationAgent) is Anthropic's
  answer. *(Verified, [AC-25][AC-1])*
