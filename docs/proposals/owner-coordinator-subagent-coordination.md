---
id: proposal-owner-coordinator-subagent-coordination
title: "Proposal: Owner / Coordinator / Sub-Agent coordination across one, several, and federated harnesses"
type: doc
status: in-review
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, multi-harness, owner-coordinator-subagent, leader-designation, leases, fencing, worktrees, rfc]
links:
  - { to: spec-agent-coordination, rel: refines }
  - { to: architecture-agent-coordination, rel: refines }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
  - { to: adr-0005-harness-runner-boundary, rel: depends-on }
  - { to: design-coord-collaboration-phase4, rel: refines }
  - { to: kb-multi-agent-coordination, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-12-18"
review-suggested: []
summary: >-
  Replaces the two prior coordination proposals with a smaller design grounded in what the
  harnesses ship, what ai-de measured, and three executed git spikes. One role model (Owner /
  Coordinator / Sub-Agent) and two control relationships (spawned, registered) cover the three
  scenarios. Leadership is human-designated and held in a git ref by compare-and-swap, never
  elected and never in the union-merged ledger. Path leases are demoted to efficiency locks; the
  join is the fence. Push uses the cheapest channel each harness actually has, and every
  cross-harness request carries a deadline and a fallback. No bus, no relay, no daemon in scope;
  each is a measured trigger, not a phase.
---

# Proposal: Owner / Coordinator / Sub-Agent coordination across one, several, and federated harnesses

*Critique of the two prior proposals and a replacement design. Nothing here is implemented.
Rendered companion: [`owner-coordinator-subagent-coordination.html`](./owner-coordinator-subagent-coordination.html).
Evidence base: [`docs/knowledge/multi-agent-coordination/`](../knowledge/multi-agent-coordination/index.md)
(four research tracks, three executed spikes, both repositories read on 2026-09-18).*

| | |
|---|---|
| **Date** | 2026-09-19 |
| **Tier** | T2 — sits on the edit path of every harness the pack serves |
| **Supersedes (proposed)** | `active-multi-harness-coordination.md` (landed on `main` at `28fda01` on 2026-09-19, after this branch was cut from `4e0f3b0`) and `proactive-multi-harness-coordination.md` (untracked in the primary checkout) — both critiqued in §2 |
| **Grounded in** | ai-forward `main` @ `4e0f3b0` (coord-core Phases 1–4, the two coordination skills, drm-0010, sp-0001…0008); ai-de `main` @ `62e3ed29` (`.agents/` ledgers, session contracts, rulings, join contract, addendum C/D); the knowledge base above |
| **Harnesses in scope** | Claude Code, OpenAI Codex, GitHub Copilot CLI, Google Antigravity, Grok Build |

**Goal state for this proposal.** *Goal:* one coordination model the pack can implement that
serves S1, S2 and S3 with the least new mechanism. *Done when:* a reviewer can run each scenario
today from §5's playbooks with what exists, and can see exactly which gaps §7 closes and how each
is measured. *Not in scope:* implementation; a hosted relay; replacing ADR-0007. *Fan-out cap
used to produce it:* 6 sub-agents, all read-only.

---

## 0. Thesis

The pack has the right **ledger** (ADR-0007) and the right **contention model** (artifact
classes). What it lacks is not a bus. It lacks **three protocol objects** and **one distinction**:

- a **designated leader held in a compare-and-swap cell** (a git ref), recorded in the ledger,
  fenced at the join — never elected, never arbitrated by a union merge (executed spike: two
  competing `leader-claim` lines both survive a union merge with exit 0);
- a **five-part delegation contract** whose fifth part is the termination condition, and whose
  cross-harness form carries a **deadline and a fallback** so a silent peer cannot block progress
  (ai-de measured 28% of 901 seam requests never resolved and improvised "not waiting on Codex");
- a **mechanical Owner review**: typed decision requests answered by numbered, heading-defined
  rulings — the one cross-harness protocol that measurably worked in ai-de;
- and the distinction between a **spawned** relationship (the parent holds the child's process:
  push, liveness and join are free) and a **registered** relationship (peers share only files and
  git: push is best-effort). **S2 is spawned-native. S1 is spawned-remote. S3 is registered.**
  The same objects flow through all three; only the channel differs.

Everything else the two prior proposals add — a loopback HTTP/SSE bus, a cloud relay, phi-accrual
stall detection, automatic reassignment, per-sub-agent worktree mandates, an interactive board —
is either already shipped by a harness, contradicted by a measurement, or has no measured trigger
yet. Each is listed in §6 with the number that would justify building it.

---

## 1. Grounding — what exists, what was measured

### 1.1 The pack today (read, not recalled)

`pack/scripts/coord-core.py` has 21 verbs: `claim / check / release / tail / hook / precommit /
guard / session / collaborate / request / worktree / metrics / install / class / classify /
merge-derived / regen / doctor / allocate / resolve / merge-register / plugin`. Leases are TTL
300 s default, 900 s cap, `--long-edit <reason>` above; expiry is computed, never stored;
verdicts exit 0 / 3 / 4 and fail to NOT CHECKED, never to allow. Session liveness is a
`session-start` with no `session-end` inside an **8-hour staleness window** (`coord-core.py:32`,
`simplify:` marker at `:2209`). `HARNESS_STATUS` is a constant from 2026-08 spikes with entries
for `claude` and `copilot` only. There is **no leader, inbox, board, heartbeat or push**. `.agents/`
resolves to the primary checkout from every worktree, which is the whole mechanism by which two
sessions see each other. The pack's default `.gitignore` **ignores** `.agents/*` except the
registry; ai-de overrides this and **tracks** `log/`, `decisions/` and `sessions/` (206 + 156 +
55 files). Both prior proposals say "git-tracked ledger"; only ai-de's is.

`/prepare-for-coordination` emits a plan (layer state · artifact classes · tracks · serial spine
· seams · struck tracks · order) and `/execute-with-coordination` is already the Coordinator role
("does not author track work itself"; `--agents` or `--brief`; `conductor-join.py` is the only
join; ten-item dispatch). drm-0010 (undecided) proposes COORD-I control currency (p44), COORD-J
join state (p45), COORD-L harness id (p46), COORD-D "no end recorded, never live" (p47), COORD-O
"the push half is the proposal's decision" (p57) and **p58: coordination doctrine has no home —
write `pack/knowledge/agent-coordination.md` (CO1–COn) as an always-loaded document.**

### 1.2 What ai-de measured (main @ 62e3ed29)

| Quantity | Value |
|---|---|
| Ledger events / sessions | 6,557 / 206 |
| Claims never released · sessions never ended | 648 (19%) · 183 (58%) — DC-067 recurrence |
| Enforcement decisions allowed / not_checked / refused | 12,131 / 132 / 59 |
| Seam requests with no recorded resolution | ~253 of 901 (28%) |
| Watcher poll interval · Claude watcher | 15 s · OFF ("do not expect a Claude poll of the ledger") |
| PreToolUse wired in ai-de | **No** — the commit floor (exit 3 / exit 4) is the control |
| Longest stall (background node, `EnterWorktree` refusal) | 8,143 s (DC-206) |
| Conductor active time in joins/gates · in coordination logic | 44.8% · 0.7% |
| Two joins queued behind one lease | ~50 min (DC-163) |
| Harnesses present | Claude Code (Opus 5), Copilot CLI, Codex (`gpt-6-astra`), Grok. **Antigravity absent.** |

What **worked** there, with pain: a single ownership register (`session-contracts.md` §2: "you
edit it, the other session proposes changes to it"); handshake revisions `r2…r7` frozen by blob
hash with `PRODUCER ACK AS WRITTEN` / `CONSUMER ACK AS WRITTEN`; **Rulings 1–139** defined by
headings and enforced by `verify-ruling-citations.py` ("a decision that cannot be read is not a
decision; it is a number with a reputation"); the join as one script with one exit code
(`join.json`); liveness commits that record "not waiting on Codex for listing". What **failed**:
free-text request/resolve produced ACK loops ("your producer-authored quote is not the consumer
evidence … no further generic ACK wait"); nothing ended sessions or released claims by protocol;
the board and standing files were pulls nobody read.

### 1.3 What the research established (headline only; the base carries the citations)

1. A lease is never mutual exclusion; only a fenced resource is (Jepsen: ~18% acknowledged-update
   loss on etcd locks; Kubernetes `client-go`: "does not guarantee … fencing").
2. Git refs are the one CAS cell in the stack (executed: `update-ref` refuses a stale `old`,
   exit 128; `--force-with-lease=<ref>:<expect>` refuses "stale info", exit 1; **`--force` silently
   overrides the lease**); the union-merged ledger is not (executed: both leader claims survive).
3. At 2–10 crash-only sessions with a human present, **designation with a reclamation lease**
   beats election (two nodes cannot self-elect; FLP; incident command and single-threaded
   ownership are appointed).
4. Claude Code (per-session socket, turn injection, `SendMessage`/`notify_when_idle` — observed
   in this session; background sessions via `--bg` and `claude agents`), Codex (`codex queue
   --thread … --message …`; `app-server --listen ws://`) and Antigravity (`--input-format
   stream-json`: one stdin line per turn, spawned print-mode child only) expose a supported push
   into a running session. Grok has print mode but no push found; Copilot CLI is docs-only on
   this machine. Four of five have a headless print mode with JSON output and a schema
   (executed `--help` on 2026-09-19: Claude Code 2.1.278, Codex 0.155.0, Antigravity 1.2.7,
   Grok). Every harness has native fan-out; **none has a cross-harness coordinator**.
5. A `Stop`/`TeammateIdle`-class hook that drains an inbox and exits 2 is the portable push where
   such a hook exists (Verified for Claude Code; Flagged elsewhere).
6. Heartbeats must carry progress (tool calls, files, tokens) — MAST's step repetition (15.7%)
   is invisible to a liveness ping; ratios cluster at renew TTL/3, dead after ≥3 missed beats;
   phi-accrual is over-engineered below ~9 nodes.
7. Contention is predicted by **files changed simultaneously on both branches**; ownership
   concentration predicts fewer defects; parallelism has a finite optimum (USL) and coding
   parallelises worse than research (~15× chat tokens; ~7× for agent teams); write-parallelism
   needs a test oracle.
8. Verification is 21% of measured multi-agent failures and **the harness will not gate plans
   for you** (Claude Code auto-approves a teammate's plan in the lead's session).
9. **An agent message is never consent** — the harness forbids permission laundering by design.
10. "AgentRoom (arXiv:2608.23740)", cited by both prior proposals, could not be found.

---

## 2. Critique of the two prior proposals

### 2.1 "Ledger and bus" (`active-multi-harness-coordination.md`, now on `main` at `28fda01`)

**Keep.** The M5–M9 diagnosis against M1–M4; "leader advises, ledger grants"; dual-write;
inject coordination and never scores (ADR-0019); the four-part delegate; artifacts not prose; a
kick *ladder*; the non-goals list; Copilot honesty; open questions left to the maintainer; demos
in ai-de rather than a toy repo. Its §1.5 is the best written account of why the pull-only board
failed.

| # | Finding | Evidence |
|---|---|---|
| A1 | **One topology.** Every session is a peer reached over a bus. The manager-vs-swarm fork (§3.1) is named and then unused. A Coordinator that *spawned* a worker already holds its stdin/stdout/exit — the strongest push channel there is — and the design never uses it. S1 and S2 are not designed; S3 is designed as the only case. | Claude Code `-p` binds an inbox socket unless `--bare`; Codex `app-server`; every harness's native fan-out (KB §2) |
| A2 | **Three planes ship (D1), including a hosted HTTPS relay with signed cards, before any measurement says the local inbox is insufficient.** "Fail-open, not fail-absent" is asserted as the justification. By the pack's ladder (YAGNI first) and R4 (a trigger is measured), the relay is a trigger-gated follow-on. | Solution-Selection Ladder; IO rules |
| A3 | **Leader by election: "first append wins; the fold is the total order."** Executed: two `leader-claim` lines union-merge with exit 0 and both survive; across machines "first" is per-view until fetch. With N ≤ 5 crash-only sessions and a human present, election adds a split-brain mode with no measured need. | SPK-3; KB findings 1–3 |
| A4 | **Progress-φ per session.** Phi-accrual needs an inter-arrival distribution; a session emits tens of bursty progress events. Its own Q5 concedes automatic kick is off until a baseline exists — so the detector is speculative generality. A deadline in the contract plus a from-the-world liveness signal is what can be measured today. | Akka all-to-all cutoff at 9 nodes; Temporal heartbeat classes |
| A5 | **Push = hook `additionalContext` at the next tool boundary.** That is a pull at the harness edge: it cannot reach a session idle at a prompt, a hung subprocess, or a harness with no hook (ai-de has no PreToolUse wired). It also ignores that Claude Code already delivers cross-session messages natively with delivery notices. | ai-de `.claude/settings.json`; OBS-1 |
| A6 | **Liveness still depends on the agent volunteering a heartbeat** (→ Loomkeeper `UpsertHeartbeat`). ai-de measured 58% of sessions never ending and 19% of claims never releasing; the enlistment gap is structural. DC-024: liveness must be read from the world. | §1.2 |
| A7 | **The Owner seat has no mechanism.** The mandate is prose in the session contract; nothing defines what the Owner reviews, when, in what artifact, or what a ruling is — while ai-de runs a numbered, heading-defined ruling register that works. | `verify-ruling-citations.py` |
| A8 | **"Git-tracked ledger" throughout; the pack's default install gitignores `.agents/log`.** Only ai-de tracks it. Either the default changes or the cross-machine story is wrong. | ai-forward `.gitignore:28-32`; ai-de `.gitignore:552-565` |

### 2.2 "Proactive multi-harness coordination" (`proactive-multi-harness-coordination.md`, untracked)

**Keep.** It names S1/S2/S3 explicitly; the running track (in flight / done / remaining) as an
operator surface; `harness_id` / `model_id` in every event (COORD-L); union merge for per-session
ledgers; a delegation-contract schema carrying budget, deadline and forbidden paths; the A2A-shaped
session card kept as a shape, not a dependency.

| # | Finding | Evidence |
|---|---|---|
| B1 | **Grounding errors on load-bearing rows.** The tier table names "Gemini 2.5/3 Pro, Claude 3.7, Sonnet 3.7, GPT-4o"; the ai-de fleet ran Opus 5 and `gpt-6-astra`, and this harness offers Fable 5.1 / Opus 5 / Sonnet 5 / Haiku 4.5. The tier table is the load-bearing half of the role model and it was asserted from memory (NG1). "8-hour timeouts" conflates the session staleness window with lease TTL (300/900 s). "Antigravity as Leader": agy is not a participant in ai-de, has no `HARNESS_STATUS` entry, and its headless flags are undocumented. | `coord-core.py:27-32`, ai-de trailers, this harness |
| B2 | **Fencing is declared, not built.** "Token_worker ≥ Token_active_lease at commit" is not Kleppmann's rule (the *resource* rejects any token lower than the highest seen). No store keeps "highest seen", no verb issues the token, and the join gate is never named. Same shape as `hotspot` (CTX-H): a name with no mechanism. | KB finding 1; QLE-22 |
| B3 | **Universal WT1 enforcement** ("wire `coord worktree new` unconditionally into all session launch hooks") contradicts three recorded decisions: P5 of `coordination-framework-tightening` (count the WT4 exception; no refusal without a baseline), `INSTALL.md:26` (ONE SESSION must remain a legal answer), and the fact that the 8,143 s stall **was** a worktree-entry refusal (DC-206). Per-sub-agent worktrees inside one session (S2) multiply the join cost that already takes 44.8% of conductor time. | §1.2 |
| B4 | **Invented constants and destructive rungs.** Φ ≥ 1.5 / 2.5, 5 min silence, 90 s ack, then "terminate the process, revoke the lease, clean the worktree, reassign" — automatic destruction on a detector with no baseline, against WT11 (never remove a tree to settle a conflict) and against the measured false-liveness rate. | WT11; DC-067 |
| B5 | **Advertised harness capabilities with no spike:** "writes an immediate trigger into the session's active terminal", "stdin event injector" for Copilot/Codex, "OS signals / named trigger pipes", "`send_message` wakes the agy loop". Phase-3 rule: never advertise a harness mode you have not executed. §13 then lists mid-turn interruption as an open question while Rung 1 depends on it. | KB §2 table |
| B6 | **Leader election by lease + "higher total-order commit wins on epoch collision"** — no mechanism for total order on git before merge; A3 stated more confidently. | SPK-3 |
| B7 | **Scope.** Four phases Oct–Dec (SSE bus, TUI, MCP tools, dashboard, φ detectors, federation, cloud relay) with no "what I am not proposing" section, no ladder pass, no control-that-fails-first per phase, and targets (≤ 60 s, ≤ 200 ms, ≥ 35% tokens) verified by "simulated" tests rather than the profiler that exists (SP-07/15/19). | CI6; IO rules |
| B8 | **Ignores the coordination that measurably worked in ai-de:** frozen handshakes with ACK-as-written, the ruling register, `join.json`, liveness commits, "not waiting on Codex". It also misreads the largest stall class: the 28% unresolved requests and the 8,143 s stall are ACK-discipline and bounded-wait failures, not transport-latency failures. | §1.2 |
| B9 | **Vocabulary collision unaddressed:** "Owner" = a model here; in ai-de "Owner" = the ruling seat (a human or the Claude Owner sub-agent). The prior proposal names this; this one silently overloads it. | ai-de `claude-conductor.md:6` |
| B10 | **"Baseline: cross-harness message delay = ∞ because the board had 0 callers"** conflates a product bug (CTX-H, an uninstalled control) with a protocol property. | CTX-H |

### 2.3 Both

Neither maps the three seats onto what each harness can actually run. Neither gives the operator
a playbook. Neither defines a termination variant for a cross-harness request — the one thing
ai-de had to improvise and the largest measured stall class. Both cite a paper that does not exist.

---

## 3. The model

### 3.1 Seats and the capability floor

| Seat | Model floor | May | Must not |
|---|---|---|---|
| **Owner** | The most capable model available in the harness (in Claude Code today: Fable 5.1; the Coordinator may be as capable) | Answer decision requests with numbered rulings; hold the veto; set and enforce the mandate; escalate to the human when a ruling's reversibility or blast radius exceeds the mandate | Grant or refuse leases; author track work; answer a permission prompt on the human's behalf; clear its own veto when it authored the thing |
| **Coordinator** | Capable enough to decompose and join (Opus/Sonnet-tier); may equal the Owner | Decompose for disjoint authored sets; author shared contracts *before* fan-out; dispatch under five-part contracts; watch progress; join; hold the leader designation in S3 | Author track work; widen fan-out past the declared cap; reassign without a ruling; treat a sub-agent's report as authority |
| **Sub-Agent** | Fit for the task (Sonnet/Haiku-tier for mechanical work; a persona on a stronger model for adversarial review) | Execute one contract in one worktree; return artifact references and proof of done; `nack` a contract outside the mandate | Re-plan; touch another track's authored set; spawn teams; relay a denied action |

Seats are **seats, not processes**: in S2 the Owner and Coordinator are usually one process in
two modes (Peer to coordinate, Adversary to review), and the veto rule is satisfied by a
**separate review sub-agent on the Owner-tier model**, so the author never clears its own veto.

**Vocabulary rule (from ai-de's collision):** *Owner* is the model seat; the person is the
**human operator**; ai-de's AgentPlane conductor keeps its name.

### 3.2 Two control relationships

| | **Spawned** | **Registered** |
|---|---|---|
| Who holds the process | The Coordinator (subprocess, Agent tool, `invoke_subagent`, `/fleet`, `spawn_subagent`) | Nobody — independent sessions the human started |
| Push | Free: stdin, tool results, exit; Claude Code inbox socket; Codex `queue` / app-server; Antigravity stdin `stream-json` turns | Best-effort: native cross-session message (Claude↔Claude), `codex queue` (Codex peers), stop-class hook inbox drain, or inbox file + count injection |
| Liveness | The process | Read from the world: process liveness + worktree/ledger activity |
| Join | The return value + the branch | The branch only, after a request/ack |
| Termination variant | The contract's deadline; `bounded_process.py`; TaskStop | **Mandatory:** deadline + fallback on every request |
| Scenarios | S2 (native), S1 (remote) | S3 |

### 3.3 Invariants (each traceable to a measurement or spike)

1. **Leadership is a CAS cell, recorded in the ledger, fenced at the join.** `refs/coord/leader`
   updated only by `update-ref <ref> <new> <old>`; the ledger line `leader-pin` *records* the
   transition; every leader-authored plan carries the epoch; the join refuses a lower epoch. (SPK-1..3)
2. **Designate, don't elect.** The human pins; an expired designation is reclaimable by a strictly
   higher epoch after a quiet period; a contested claim pages the human. Tie-break, if ever
   automated: lowest session id. (KB finding 3)
3. **Path leases are efficiency locks.** TTL 300/900 unchanged; git's three-way merge plus the
   commit floor is the correctness arbiter; no code path may assume a lease was honoured. (KB finding 1)
4. **Never `--force` with `--force-with-lease`; always the three-part form.** (SPK-2)
5. **Liveness from the world; heartbeats carry progress.** A heartbeat without tool-call / file /
   token deltas is not progress; "no end recorded" is never rendered "live". (p47; SCH-8)
6. **Five-part contract; artifacts not prose.** Objective · artifact path / schema · tools in
   bounds · boundaries (paths, budget, fan-out cap) · **termination condition**. (AC-1; MAST)
7. **Every cross-harness request carries a deadline and a fallback**, and its ACK is pinned to a
   blob hash. (ai-de handshake; 28% unresolved)
8. **Two tracks never author one file or one slice in the same window.** The Coordinator fixes the
   boundary; it never schedules around it. (SCH-17; existing skill rule)
9. **An agent message is never consent.** Owner authority is over work, never permission. (AC-5/6)
10. **Never advertise a harness channel not executed on this machine**; `enforced / observed-only /
    unsupported` per harness, with date and version. (Phase-3 rule; CTX-H)
11. **Empty fleet view is NOT CHECKED**, never "all quiet". (R4)
12. **Fan-out declares all GO7 fields and a main-line budget**; width 3–5 by default. (CTX-M; USL)

---

## 4. Protocol objects (shared by all three scenarios)

All are **ledger lines** (`.agents/log/<session>.jsonl`), each with a stable `id`, an HLC-shaped
stamp `(wall_ms, counter, session)`, `host` (COORD-L vocabulary `claude|copilot|grok|agy|codex`)
and `tree` (`primary|worktree`). Order and dedup are fold-time properties (`merge=union` is
path-scoped to these files only).

| Object | Verb (proposed) | Fields beyond the common ones | Notes |
|---|---|---|---|
| **Session Card** | `coord session start --host … --roles … --model …` (extends the existing verb) | roles claimed, model, worktree, branch, base commit, listen address if any | A2A-shaped; roles are claimed, not granted |
| **Delegation contract** | `coord delegate --to … --wi …` | the five parts; `budget calls/tokens`; `deadline`; `fallback` | Cross-harness form = seam request + contract |
| **Work item / running track** | `coord track` (fold view) | `wi`, owner session, state `todo|in-flight|blocked|done`, blocked-on, deadline, last progress | Derived; text + the existing operator HTML; never a second store |
| **Progress heartbeat** | `coord session heartbeat` (from PostToolUse/Stop hooks where present; worktree mtime otherwise) | calls since last, files touched, tokens if known | Bus-free; sampled into the ledger at most once per TTL/3 |
| **Seam request (typed)** | `coord request add --to … --contract … --deadline … --fallback …`; `ack --blob …`; `resolve`; `expire` | states `sent → received → ack-as-written → resolved`, or `expired-fallback` | Replaces free-text ACK; ai-de's handshake, mechanised |
| **Decision request / Ruling** | `coord decide request …` / `coord decide rule <n> …` | options, evidence, recommendation, reversibility, blast radius / the ruling text under a heading | `verify-ruling-citations` absorbed into the pack |
| **Leader designation** | `coord leader pin|who|renew|release|reclaim` | epoch, ttl, quiet period | `refs/coord/leader` CAS; ledger records |
| **Join state** | existing `conductor-join.py` + `JoinState` (COORD-J) | per-step state, terminal `complete`, epoch checked | The fence |

**Kick ladder (kept from the prior proposal, with automatic destruction removed):**
0 notify (blocked recorded → pushed by the cheapest channel) → 1 kick (deadline passed or 3
missed progress beats; `suggest` is an enum) → 2 **escalate to the Owner with a decision request**
(reassignment happens only under a ruling) → 3 human. Cap two kicks per work item; count them.

---

## 5. The three scenarios

### 5.1 S2 — one harness, native fleet (the base case)

**Topology.** Owner + Coordinator seats in the main session; sub-agents via the harness's fan-out;
Owner review by a separate Owner-tier review agent.

| Harness | Coordinator spawns | Model per sub-agent | Isolation | Owner review | Push to a sub-agent | Status |
|---|---|---|---|---|---|---|
| **Claude Code** | `Agent` tool (background), optionally agent teams for long-lived tracks; `Workflow` for deterministic pipelines | `model: sonnet|haiku|opus|fable` per call | `isolation: worktree` for writers | review sub-agent on `fable`; `TaskCompleted`/`Stop` hook exit 2 as the mechanical gate | `SendMessage` to a teammate; TaskStop | **enforced** (observed 2026-09-18, v2.1.x; teams experimental) |
| **Antigravity** | `invoke_subagent` / `define_subagent` | `model: inherit|flash|pro` in the agent file | `workspace: branch` | reviewer subagent with `model: pro` | peer messaging by conversation id | **observed-only** (docs read; not executed here) |
| **Copilot CLI** | `/fleet` | per-session model (per-subagent choice Flagged) | undocumented | handoff to a review agent after the fleet completes | none documented | **observed-only** |
| **Grok Build** | `spawn_subagent --parallel` (≤ 8) | via subagent type | worktree per child | reviewer subagent type | none documented | **observed-only** |
| **Codex** | manager + workers (caps Flagged) | Flagged | sandbox | reviewer worker | `app-server` | **observed-only** |

**Playbook (Claude Code, today).** In the main session on the strongest model: run
`/prepare-for-coordination` (plan with disjoint authored sets, serial spine first), then
`/execute-with-coordination --agents`. The skill already dispatches with the ten-item contract;
add the termination condition and `--main-budget`. Dispatch writers with `isolation: worktree`
and a `model` override; dispatch the review on `fable` in Adversary mode against the plan
*before* fan-out and against each artifact *after*. **Enter the worktree before the first spawn**
(§8, CTX-Q). Join with `conductor-join.py` only.

**Gaps closed by §7:** five-part contract in the skill; Owner review as a hook where the harness
supports it; heartbeats with progress; `coord track`.

### 5.2 S1 — one harness hosts Owner + Coordinator, sub-agents on other harnesses

**Topology.** S2 with remote spawned sub-agents: the Coordinator's shell tool launches each
external harness **headless, in its own worktree**, under `bounded_process.py`, with an
`--agent-run` audit span carrying the budget.

| Target harness (version probed 2026-09-19) | Dispatch (today) | Structured return | Mid-run steering | Status |
|---|---|---|---|---|
| Claude Code 2.1.278 | `claude -p "<contract>" --output-format json --json-schema <schema> --permission-mode acceptEdits` in the track worktree (not `--bare`, so it binds an inbox socket); or `--bg` for a managed background session | JSON with `total_cost_usd`; the branch | inbox socket via the child's registry entry; `--resume <id>`; `claude agents|attach|logs|stop` for `--bg` sessions | **executed `--help`**; socket path discovery **Flagged** — probe `~/.claude/sessions/<pid>.json` |
| Codex 0.155.0 | `codex exec --json -o <last.json> --output-schema <schema> --worktree -C <dir> --sandbox workspace-write --approve-for-me "<contract>"` | JSONL events + last message; the branch | `codex queue --thread <uuid|name> --message <text>`; `app-server --listen ws://…` + `--remote` | **executed `--help`**; subagent caps still Flagged |
| Antigravity 1.2.7 | `agy -p "<contract>" --output-format json --json-schema <schema> --mode accept-edits --model <m> --effort <e> --print-timeout <s>` | JSON; the branch | `--input-format stream-json` (one NDJSON message per line, one turn each) for a child kept open; `--conversation <id>` to resume | **executed `--help`** |
| Grok Build | `grok -p "<contract>" --output-format json --json-schema <schema> --worktree=<name> --permission-mode <m> --max-turns <n>` | JSON (or ACP `streaming-json`); the branch | none found; `--resume`/`--session-id` for continuation | **executed `--help`** |
| Copilot CLI | `copilot -p "<contract>" --allow-tool …` (narrow allow lists; `--allow-all-tools` grants the user's full access) | stdout; the branch | none documented | **observed-only** — not installed on this machine |

**Playbook (today).** Owner + Coordinator in Claude Code (or any harness with a shell tool). For
each track: `coord worktree new --branch <work>`; write the contract file; launch the target
harness as above with cwd = the worktree; the child's `session-start` hook emits its Session Card
with `--host`; poll the child's exit and its branch (progress from the worktree mtime and commits
until P3 lands); join through `conductor-join.py`. Antigravity works today both as **host** (its
shell tool launches the CLIs) and as a **spoke** (`agy -p`); the earlier "unsupported" row was
wrong and is corrected by execution.

**Gaps closed by §7:** `coord dispatch` wrapper (bounded, audited, per-harness status recorded);
progress liveness from the world; `coord track`.

### 5.3 S3 — several harnesses, each self-contained, one designated leader

**Topology.** Each harness runs S2 internally. The human starts each session with a scope
("Antigravity = backend, Claude Code = tests, Copilot = UI"), tells each to **register**, and
**pins one Coordinator as leader**. Sessions share the primary checkout's `.agents/` (machine-local,
instant) and git (durable, cross-machine).

**Protocol.**
1. Register: `coord session start --host <h> --roles coordinator …` → Session Card.
2. Designate: human runs `coord leader pin <session> --ttl 300` in any harness → CAS on
   `refs/coord/leader`, epoch +1, ledger line.
3. Own: each harness's authored set is in the session contract (one register, `session-contracts.md`
   §2 pattern); classes decide what needs no coordination at all.
4. Coordinate seams: `coord request add --to <session> --contract … --deadline … --fallback …`;
   the consumer `ack --blob <hash>`; producer `resolve`. At the deadline with no ack the requester
   runs the fallback and records `expired-fallback` — *"not waiting on Codex"* as a protocol step.
5. Lead: the leader holds the running track, runs the anti-entropy fold every 15 s (ai-de's
   watcher interval, now a pack verb), notifies waiters on `done`/`release`, kicks on deadline or
   three missed progress beats, escalates to its Owner and then to the human. It **advises**
   assignment; `coord claim` still grants.
6. Renew / lose / reclaim: the leader renews at TTL/3; a lapsed designation is reclaimable by
   another Coordinator only after a 30 s quiet period, with epoch +1, and the takeover
   **re-establishes** the in-flight table (which harness owns which work item, outstanding
   requests, remaining lease time) before acting — Raft's transfer and Garcia-Molina's
   reorganisation phase, by hand.
7. Push by the cheapest verified channel: Claude↔Claude → native cross-session message (turn
   injection, delivery notice, `notify_when_idle`); a harness with a stop-class hook → inbox
   drain + exit 2; otherwise inbox file + a count injected at SessionStart. Each recorded as
   `enforced / observed-only / unsupported` per host.

**Playbook (today, without §7).** Everything above except `leader`, typed `request` states and
`track` exists: `coord session start`, `coord claim/check`, `coord request add/resolve`,
`coord collaborate check`, `session-contracts.md`. The human names the leader in the session
contract; the leader Coordinator runs `coord tail` and `coord collaborate summary` on a 15 s
Monitor; Claude Code peers message each other with `SendMessage`. That is S3 as ai-de runs it
now, with ai-de's failure rates.

**Failure modes and dispositions.**

| Mode | Disposition |
|---|---|
| Leader session dies | Designation lapses; reclaim after quiet period by CAS; in-flight table re-read from the fold; human paged if two reclaim attempts collide |
| Two leaders (laptop sleep, clock jump) | The ref has one value; the join refuses the lower epoch; on wake a leader whose monotonic and wall clocks disagree by more than the skew budget steps down and re-pins |
| Silent peer | Deadline + fallback; `expired-fallback` counted |
| Stall | Kick ladder to the Owner; no automatic reassignment |
| Free-text ACK churn | Typed states; ACK pinned to blob hash |
| Empty fleet view | NOT CHECKED |
| Harness without hooks (ai-de's Copilot today) | Commit floor + inbox file; recorded `observed-only` |

---

## 6. What I am not proposing (the Simplifier's pass)

| Struck | Why | Measured trigger that would reopen it |
|---|---|---|
| Loopback HTTP/SSE bus daemon | Claude Code already ships a per-session socket with turn injection; Codex ships a WebSocket control plane; the measured stall classes are ACK discipline and bounded waits, not transport latency; a daemon adds an availability dependency ADR-0007 removed | median time-to-ack > 60 s **after** P1 + P4 land, measured by `coord metrics` |
| Cloud relay with signed cards | No cross-machine fleet exists in either repo; A2A is implemented by no harness in scope | a second machine appears in a session contract |
| Leader election | SPK-3; FLP; human present; two-node fleets cannot self-elect | leader-loss stalls > 1/week after P2, measured |
| Phi-accrual detectors | Over-engineered below 9 nodes; no baseline; kick false-positive rate unknowable today | false-kick rate measured under P3's deadline + 3-missed-beats rule |
| Automatic reassign / process kill / worktree clean | WT11; DC-067 false liveness; destructive on a false positive | never automatic; the Owner rules |
| Mandatory worktree per sub-agent in S2 | Contention is a property of the artifact; the join is 44.8% of conductor time; the 8,143 s stall was a worktree refusal; INSTALL keeps ONE SESSION legal | WT4 exception rate (already counted) rising while overlap conflicts appear |
| Interactive board / TUI / MCP board tools | `coord track` over the fold plus the existing operator HTML is the projection; a board is a pull nothing read | `track` read-rate measured and still zero after SessionStart injection |
| CRDT for source or state | CodeCRDT −39% worst case; leases must be refused, not merged | none |
| A2A / ANP / mTLS / DID | No harness implements A2A; OS user is the trust boundary on one machine | a third party's agent joins the fleet |
| MCP sampling as the delegation primitive | Deprecated in MCP 2026-07-28 | none |

---

## 7. Build plan — ranked by benefit ÷ cost, each with a control that fails first and a measurement

| # | Item | Pack surface | Control that fails on recurrence | Measurement | Cost |
|---|---|---|---|---|---|
| **P0** | **Doctrine home + hygiene.** `pack/knowledge/agent-coordination.md` (CO1–COn, `load: always`, drm p58) carrying §3.3; register **CTX-Q** (§8); pack default tracks `.agents/log`, `requests.jsonl`, `sessions/` and ignores `decisions/` (ai-de's split), with a `pack-doctor` check; COORD-L `--host` on `session start` and `audit-log append`; COORD-D "no end recorded" never "live" + start/end ratio in `metrics` | knowledge, `.gitignore` template, `pack-doctor.py`, `coord-core.py`, `audit-log.py`, `session-start.py` | `foundation-check` lists the doc as always-loaded; doctor FAILs an install whose ledgers are ignored; a fixture with start-and-no-end must not render live; selfcheck gate counts unrecorded host | start/end ratio; % entries with `host` | ~1 day |
| **P1** | **Typed seam requests with a termination variant.** `request add --deadline --fallback`; `ack --blob`; `expire`; states `sent/received/ack-as-written/resolved/expired-fallback` | `coord-core.py request`; session-contract template | red-first: a request past its deadline with no ack must fold to `expired-fallback`, never `open`; an ack without a blob is refused | unresolved rate (baseline 28%); median time-to-ack | ~1 day |
| **P2** | **Leader designation in a ref.** `coord leader pin/who/renew/release/reclaim` over `refs/coord/leader` via `update-ref` CAS with epoch and quiet period; the join reads the epoch and refuses a lower one; contested reclaim pages | `coord-core.py`, `conductor-join.py` | the three spikes as tests: stale `old` refused; `--force` never emitted; two concurrent pins → exactly one epoch advances; join refuses lower epoch | leader-loss events; reclaim latency; contested pins | ~1 day |
| **P3** | **Progress liveness + running track.** `session heartbeat` from PostToolUse/Stop hooks (Claude Code, Grok, agy) and worktree mtime fallback; `coord track`; kick ladder 0–2 as notify → kick → decision request | `coord-core.py`, hook adapters | fixture: liveness pings with zero progress deltas must render `stalled`, not `live`; empty corpus → NOT CHECKED | stall detection latency (baseline 8,143 s); false-kick rate | ~2 days |
| **P4** | **Push adapters by relationship.** `coord dispatch --harness claude|codex|copilot` (headless CLI in a worktree under `bounded_process.py`, `--agent-run` span with budget, per-harness status recorded); S3 notify adapter (Claude native message when both are Claude Code; inbox + hook drain where a stop-class hook exists; inbox + SessionStart count otherwise) | `coord-core.py`, hook adapters, `HARNESS_STATUS` (per version, dated) | a dispatch without a budget or deadline is refused; a channel not executed on this machine renders `unsupported` | dispatch success/exit codes; kick-ack rate per host | ~3 days |
| **P5** | **Owner review mechanics.** `coord decide request/rule`; `verify-ruling-citations` absorbed as a gate; `TaskCompleted`/`Stop` exit-2 review gate where supported; skills updated: five-part contract, seat mapping table (§5), "enter worktree before first spawn" | `coord-core.py`, gates, both coordination skills, persona cards | a ruling number cited without a heading definition fails the gate; a contract without a termination condition is refused at dispatch | rulings issued; review latency; contracts refused | ~2 days |

Items P0–P2 are one commit each and independent; P3 depends on P0's `host`/`tree` fields; P4 on
P1 (deadline/fallback) and P2 (epoch on dispatch); P5 on P1. Every item lands with its control red
first (CI6) and a `coord metrics` row, and each is exercised in **ai-de**, not a toy repo, because
that is where the baselines are. `/specify` for P0–P2 is the next step after review.

---

## 8. Defect class registered from this turn

**CTX-Q — A parent enters a worktree after delegating, stranding its delegates.** Four research
sub-agents were spawned from the primary checkout; the parent then called `EnterWorktree`; the
worktree guard resolved each sub-agent's cwd to the shared checkout and refused every Bash call
for the rest of their runs (they delivered inline). Control: the always-loaded doctrine (P0)
carries "enter the worktree before the first spawn", and `/execute-with-coordination` dispatch
refuses to spawn when the session's worktree state is `pending`. Registered in
`docs/lessons/defect-classes.md` as `uncontrolled` until P0 lands.

---

## 9. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | One role model, two control relationships; design by relationship, not by harness | Spawned children are push channels for free; registered peers are not (KB finding 5) |
| D2 | Leadership in `refs/coord/leader` by CAS; ledger records; join fences | SPK-1..3; Jepsen; Kleppmann |
| D3 | Designation with reclamation, never election | FLP; two-node arithmetic; ICS/STO; human present |
| D4 | Path leases stay 300/900 and are efficiency locks | Git is the arbiter; DC-163 |
| D5 | Five-part contract; deadline + fallback on every cross-harness request; ACK pinned to blob | MAST termination-unaware 12.4%; ai-de 28% unresolved |
| D6 | Owner review = decision request → numbered ruling, gated by hook exit code where possible; reviewer ≠ author | MAST verification 21%; harness auto-approves plans; persona-audit rule |
| D7 | Liveness from the world; heartbeats carry progress; no phi | DC-024; Temporal; Akka cutoff |
| D8 | Push by the cheapest executed channel; `unsupported` until executed | Phase-3 rule; CTX-H |
| D9 | No bus, relay, election, auto-reassign, board or per-sub-agent worktree mandate in scope; each has a measured reopen trigger | §6 |
| D10 | Pack default tracks the ledgers (ai-de's split) | A8; cross-machine S3 needs it |
| D11 | Vocabulary: Owner (seat) · human operator · AgentPlane conductor | ai-de collision |

## 10. Open questions for the maintainer

1. **Ledger tracking default (D10):** change the pack default, or keep ignoring and require S3
   users to opt in as ai-de did? Recommendation: change the default; `pack-doctor` reports which.
2. **Leader lease constants:** start at 300 s / 150 s / 20 s with a 30 s quiet period (k8s ×20 for
   a sleeping laptop fleet) and tune from `coord metrics`, or start shorter? Recommendation: start
   long; a false takeover costs more than a slow one.
3. **Copilot hooks:** its stop-class hook names are secondary-sourced. Spend the probe before P4,
   or ship Copilot as `inbox + commit floor` and record `observed-only`? Recommendation: probe
   first; it is one doc page.
4. ~~**Antigravity as S1 host:** `agy --help` …~~ **Resolved 2026-09-19 by execution:** agy 1.2.7
   has a full print mode (`-p`, JSON output, schema, stdin `stream-json` turns, `--conversation`
   resume). Both host and spoke roles are open. Remaining probe for agy: whether a hook surface
   exists for the progress heartbeat (P3) — `agy --help` lists none.

---

## References

- Evidence base: `docs/knowledge/multi-agent-coordination/` (index, state-of-the-art, comparables,
  references, data-and-constants, glossary, open-questions, sources).
- Prior proposals: `docs/proposals/active-multi-harness-coordination.md` (on `main` since
  `28fda01`; add a `relates-to` link to `proposal-active-multi-harness-coordination` when this
  branch is rebased), `docs/proposals/proactive-multi-harness-coordination.md`
  (untracked, primary checkout), `docs/proposals/coordination-framework-tightening.html` (P1–P6
  implemented at revision 62).
- Pack: `pack/scripts/coord-core.py`; `docs/design/coord-*-phase1..4.md`;
  `.claude/skills/{prepare-for-coordination,execute-with-coordination}/SKILL.md`;
  `.claude/knowledge/{session-worktree-discipline,execution-graph-optimization}.md`;
  `docs/dreams/drm-0010/dream.json` p44–p58; `docs/profiles/sp-000{1,2,4,5,8}/profile.md`.
- ai-de: `docs/collaboration/session-contracts.md`; `.agents/{log,decisions,requests.jsonl,sessions}`;
  `docs/coordination/join.json`; `docs/notes/d1-r5-producer-ack.md`; `tools/verify-ruling-citations.py`;
  `docs/profiles/addendum-cd.md`; `docs/notes/collaboration-not-happening.md`;
  `docs/knowledge/multi-agent-coordination/index.md`.

## Status

| | |
|---|---|
| **Completed** | Grounding in both repositories; four research tracks captured as a knowledge base; three executed spikes; critique of both prior proposals (18 findings); the model, protocol objects, three scenario playbooks, the struck list with reopen triggers, a five-item build plan with controls and measurements, one defect class. |
| **Remaining** | Maintainer answers to §10; `/specify` for P0–P2; the Copilot probes (install the CLI; hook page). The `agy` probe and the cherry-pick spike are done (2026-09-19): agy has print mode; union merge converges under merge, rebase and cherry-pick. `verify-bundle` ran against this worktree: gate 1 passes after regenerating `docs/portal/portal-data.js` and `web/pack-index.js`; gate 2 (`sync-pack` then `git diff --exit-code`) fails only because the tree is uncommitted — the diff is this branch's own files; gate 3's five failures reproduce on a clean clone of `main` (pre-existing, `master`-branch assumptions and an audit `--since` test), so none are introduced here; the knowledge-graph, audit, coordination and context-budget gates pass. |
| **Best next action** | Decide D10 and D3; then `/specify` P2 (leader designation) against ai-de, whose baseline is a designated human leader today. |
