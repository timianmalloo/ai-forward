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
  - { to: proposal-active-multi-harness-coordination, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
  - { to: note-20260919-coordination-decisions-ratified, rel: relates-to }
  - { to: note-20260919-leadership-in-a-ref-not-the-ledger, rel: relates-to }
review-by: "2026-12-18"
review-suggested: []
summary: >-
  Replaces the two prior coordination proposals with a smaller design grounded in what the
  harnesses ship, what ai-de measured, and three executed git spikes. One role model (Owner /
  Coordinator / Sub-Agent) and two control relationships (spawned, registered) cover the three
  scenarios. Leadership is human-designated and held in a git ref by compare-and-swap, never
  elected and never in the union-merged ledger. Path leases are demoted to efficiency locks; the
  join is the fence. Push uses the cheapest channel each harness actually has, and every
  cross-harness request carries a deadline and a fallback. A formal local message layer (file
  inbox as the store, each harness's own doorbell as the push, git as the fallback) and a board
  for humans (ratified 2026-09-19); a compile stage before planning; three shared stages the 27
  skills cite. No broker, no relay, no election in scope; each is a measured trigger, not a phase.
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
classes). What it lacks is not a bus daemon. It lacks **three protocol objects**, **one distinction** and, as ratified on 2026-09-19, **a message layer whose store is a file and whose push is the harness's own doorbell** (§4b):

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

### 4b. The message layer (D9 revised, D12)

The prior proposals were right that agents must be able to *tell* each other things and wrong
about where the message lives. Claude Code's own shipped design is the template: **the file is
the store; the doorbell is the push.** Its sessions register in files on disk, each binds a
per-session socket, and a delivered message is read between tool calls or starts a new turn when
the session is idle. Nothing in that is a daemon.

| Part | Mechanism | Notes |
|---|---|---|
| **Store** | `.agents/mail/<session>.jsonl` — one append-only inbox per session, machine-local beside the ledgers; every line has `id`, HLC stamp, `from`, `to`, `kind`, `body`, `ref` | State-changing kinds (`delegate`, `blocked`, `unblocked`, `kick`, `decision-request`, `ruling`, `done`, `ack`/`nack`) are **dual-written to the sender's ledger**, so git carries them across machines and a clone tomorrow sees every kick. Chatter (`note`, `progress`) stays inbox-only |
| **Send** | `coord mail send --to <session|*> --kind <k> --body … [--ref <artifact@commit>]` | Appends to the recipient's inbox, dual-writes when state-changing, then rings the recipient's doorbell. Idempotent by `id`; per-recipient queue cap; identical-repeat drop within a window; expiry — the constants Claude Code ships (50 queued, 100 held, 5-minute held expiry) are the starting values |
| **Read** | `coord mail read [--since <id>] [--ack]` | Folds the inbox; the harness adapter calls this at its seam and renders the result under an **untrusted heading** — messages are data, never instructions (ADR-0011) |
| **Doorbell — Claude Code** | the cross-session socket: registry `~/.claude/sessions/<pid>.json`, per-session token, one auth line then the message; delivered between tool calls or as a new turn | **Verified** (docs + observed in this session). The doorbell carries a one-line pointer ("coord mail: 2 new for you; run `coord mail read`"), never the body |
| **Doorbell — Codex** | `codex queue --thread <uuid|name> --message "<pointer>"` | **Verified** (`codex queue --help`, 0.155.0) |
| **Doorbell — Antigravity** | the pack's `.agents/hooks.json` gains a `PreInvocation` hook that runs `coord mail read` and returns the result as `injectSteps`; `PostInvocation` returns `terminationBehavior: force_continue` while the inbox is non-empty | **Verified from docs** (antigravity.google/docs/hooks, 2026-09-19); execution pending |
| **Doorbell — Grok Build** | the deployed Claude-format `PreToolUse` / `UserPromptSubmit` hooks drain the inbox into `additionalContext` at the next tool boundary | pull-at-the-edge; **observed-only**; no external push found |
| **Doorbell — Copilot CLI** | `preToolUse` returns `additionalContext` with the drained inbox at the next tool boundary; `agentStop` / `subagentStop` return `decision: "block"` with `reason` = the pointer, which Copilot injects as the next turn's prompt (runaway guard: 8 consecutive blocks, `stop_hook_active` on the payload); `bash`/`powershell` arms | **Verified from docs** (docs.github.com hooks reference, 2026-09-19): a real stop-class doorbell. `observed-only` until a live session shows a drain firing; inbox + commit floor is the accepted default meanwhile |
| **Fallback** | none of the above reachable → the message is still in the inbox and (if state-changing) in the ledger; `coord board` shows it; the request's deadline and fallback (D5) govern | git is the durable path and the cross-machine path; nothing is lost when a doorbell is missing |
| **Board (D12)** | `coord board [--follow]` folds every inbox plus the ledger's message kinds into one timeline (terminal), and the operator HTML gains a Board view over the same fold; `coord board post --to <session|*> "…"` lets the human speak into the same inboxes | A **read model**, never a store. Rendered empty it says `NOT CHECKED (no inboxes)`, never "all quiet" (R4) |

Rules carried forward: a doorbell rings with a **count and a pointer**, never the message body
(the harness renders untrusted data under a heading, and the pack never injects an
instruction-shaped string); scores and rankings are **never** pushed (ADR-0019 anti-Goodhart);
an agent message is never consent (AC-5/6). Measured origin of the design: ai-de's board had zero
writers and its standing files were pulls nobody opened (COORD-O); the fix is a store every
send writes to and a doorbell every harness we can reach rings, not a prettier pull.

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
| A daemon or broker as the message **store** | The store is per-session inbox files plus the ledger (D9); a process that must be up for a message to exist re-adds the availability dependency ADR-0007 removed. The board (D12) reads the store; it does not hold it | a doorbell adapter that cannot be built on files — none known |
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
| **P4** | **Message layer + dispatch (D9 revised).** `coord mail send/read/ack` over per-session inbox files (`.agents/mail/<session>.jsonl`, machine-local; state-changing kinds dual-written to the ledger); `coord dispatch --harness claude|codex|copilot|agy` (headless CLI in a worktree under `bounded_process.py`, `--agent-run` span with budget, per-harness status recorded); one **doorbell adapter per harness** — Claude Code cross-session message, `codex queue`, Antigravity `PreInvocation → injectSteps`, Grok/Copilot tool-boundary hooks, Copilot `agentStop` block-with-reason — each adapter a count + pointer, never a body; inbox + ledger + deadline/fallback is the floor when no doorbell exists | `coord-core.py`, hook adapters (five), `HARNESS_STATUS` (per version, dated) | a dispatch without a budget or deadline is refused; a doorbell that carries a body is refused; a channel not executed on this machine renders `unsupported`; a `delegate`/`ruling` in an inbox with no ledger twin fails `coord doctor` | dispatch exit codes; mail sent/read/acked per session; doorbell latency (send → first read) per harness; kick-ack rate | ~3 days |
| **P5** | **Owner review mechanics.** `coord decide request/rule`; `verify-ruling-citations` absorbed as a gate; `TaskCompleted`/`Stop` exit-2 review gate where supported; the two coordination skills carry the contract (the wider skill sweep is P8) | `coord-core.py`, gates, both coordination skills, persona cards | a ruling number cited without a heading definition fails the gate; a contract without a termination condition is refused at dispatch | rulings issued; review latency; contracts refused | ~2 days |

| **P6** | **Board (D12).** `coord board [--follow]` renders the inboxes and the ledger's message events as one timeline (who → whom, kind, ref, age, acked?), terminal and the operator HTML; `coord board post --to <session|*> "…"` writes a human message into the same inboxes. A read model, never a store; an empty corpus renders `NOT CHECKED` | `coord-core.py`, `docs/audit/index.html` (a *Messages* view beside the audit timeline) | a board row with no inbox or ledger line behind it fails the fixture; a post that bypasses the inbox is impossible by construction (one writer) | board reads per session; human posts; time-to-first-human-read of a `blocked` | ~1 day |
| **P7** | **Compile stage (§7b).** `prompt-compile.py` turns the operator's prose into the harness- and model-specific starting prompt: the goal state (Goal · Done when · Not in scope · Tier · Fan-out cap), resolved references (every path opened), `assume:` markers for every unresolved belief, and the target harness's idiom (Claude brief; `codex exec`; `copilot -p`; agy `injectSteps`). The compiled prompt is the five-part contract before it has an assignee; consequential unresolved assumptions become decision requests before dispatch. Raw and compiled are logged together (`kind:prompt`, `prompt_compiled`, `target_harness`, `compiler_model`) | `pack/scripts/prompt-compile.py`, `pack/adapters/prompt-templates/<harness>.md`, `audit-log.py`, `prompt-log.py` | `verify-compiled-prompt.py`: a compiled prompt whose *done-when* clause traces to no raw phrase and no `assume:` is refused (the compiler may not add scope, CT19); a compiled prompt missing any of the five fields is refused | compile duration and tokens; assumptions surfaced per prompt; edit distance between compiled and what the human actually ran (compiler quality); downstream: boundary corrections and refused decisions per track in `coord metrics` | ~2 days |
| **P8** | **Skill evolution (§7b).** The 27 skills re-cut for seats, the five-part contract, `coord mail`, the board, leader designation, deadlines/fallbacks and hook-gated Owner review, per the §7b matrix; the shared stages ship once as `pack/knowledge/agent-coordination.md` §CO-skills and are cited, not copied | every `pack/commands/*/SKILL.md` that dispatches or is dispatched; persona cards; `INSTALL.md` counts | `verify-skill-contracts.py`: a skill that names a fan-out cap but no termination condition, or spawns before the compile stage, or dispatches without the five parts, fails; `context-budget` for the added lines | delegations refused at dispatch; per-skill fan-out actual vs cap (`/session-profiler`) | ~3 days |
Items P0–P2 are one commit each and independent; P3 depends on P0's `host`/`tree` fields; P4 on
P1 (deadline/fallback) and P2 (epoch on dispatch); P5 on P1; P6 on P4; P7 on P0 only (it is the cheapest item after P0 and the maintainer's stated priority); P8 on P4, P5 and P7. Every item lands with its control red
first (CI6) and a `coord metrics` row, and each is exercised in **ai-de**, not a toy repo, because
that is where the baselines are. `/specify` for P0–P2 and P7 is the next step after review.

---

## 7b. How the skills evolve, and the compile stage (P7, P8)

*Added 2026-09-19 at the maintainer's request. The survey was a grep over all 27 `pack/commands/*/SKILL.md`
files plus the knowledge docs they cite, run in this worktree; every count below was observed, not
recalled.*

### 7b.1 What the skills do today (measured)

| Finding | Evidence |
|---|---|
| **Only two of 27 skills dispatch anything.** `prepare-for-coordination` and `execute-with-coordination` open worktrees, brief delegates and join. In the other 25, every *Cast* — "Peers", "Adversaries", "the full architect council" — is a **rhetorical council**: personas the running agent enacts in one context. No skill says *spawn*, names a delegate brief, or reads a delegate's return. | grep across the 25 for `spawn`, `Agent tool`, `sub-agent`, `--brief`: zero as an instruction to itself |
| **No skill outside those two touches the coordination layer.** Two read-only hits in 25 files: `session-profiler` runs `coord-core.py worktree list` (SP-15); `updatepack` warns against `git add -A` beside other worktrees. Nothing calls `claim`, `request`, `decision`, `session`, `doctor` or `metrics`. | grep `coord-core|claim|request|decision|doctor|metrics` |
| **The coordination vocabulary is absent.** `coord mail`, board, inbox, doorbell, heartbeat, deadline, leader, Coordinator, resume: **zero** occurrences in the 25. "Owner" is only the frontmatter `owner:` field in the Discoverability boilerplate. | grep, the whole word list |
| **Harnesses appear only as install destinations** — in `addpacktorepo`, `updatepack`, `extendaibundle` (which surfaces to write) and `session-profiler` (which telemetry store to read). Never as a place to send work. | those four files |
| **Four pieces already exist and are reusable.** (1) The CT19 goal-state block (Tier · Fan-out cap · Context ceiling · Main-line budget), which `/also` re-sizes and `/session-profiler` measures against; (2) GO7's five-part fan-out contract, which `/optimize-graph` **emits and no skill consumes**; (3) the `**Handoff:**` last line in 24 of 25 skills — skill → skill today, never agent → agent; (4) four **hard human stops** (`investigate` Stage 7, `forensicreview` triage, `code-hygiene fix` Stage 7, `apply-learnings`), which already say where autonomy yields. | `also/SKILL.md`, `optimize-graph/SKILL.md` Stage 6–7, `execution-graph-optimization.md` GO7, the four STOP stages |

The consequence for this spec: **the pack has a doctrine of delegation and no plumbing for it.** The
contract exists as prose in the graph skill; the seat, the message, the deadline and the review are
defined nowhere a skill can cite. So the evolution is not "rewrite 27 skills" — it is *write the
shared stages once, then make each skill cite the stage it needs*. That is the ladder (reuse-in-codebase
before new text) and the context-budget rule (a paragraph copied into 27 files is paid 27 times).

### 7b.2 The three shared stages (written once, in `pack/knowledge/agent-coordination.md`)

| Stage | What it adds to a skill that cites it | Who runs it |
|---|---|---|
| **CO-S0 Compile** | The operator's prose becomes the harness- and model-specific starting prompt (§7b.4). Idempotent: a prompt already carrying the goal-state block passes through. Unresolved consequential `assume:` markers become **decision requests before any work starts**. | every skill whose input is prose (the fourteen "prose-input" skills below), *before* `/optimize-graph` |
| **CO-S1 Seat** | The skill declares which seat it runs in — `Runs as: Coordinator · Sub-Agent · either` — in frontmatter. As **Coordinator** it dispatches only through the five-part contract with a termination condition, a deadline and a fallback, reads `coord leader who` before any join, and reviews through decision request → ruling, never by accepting a claim. As **Sub-Agent** its goal state *is* the compiled contract it received, it never spawns beyond its cap, and its last action is `coord mail send --to <coordinator> --kind done` carrying the exit evidence, **not** a skill → skill handoff. | every skill |
| **CO-S2 Stop = message** | A hard human stop or a hard veto is no longer only prose. It is `coord decide request` to the seat that can rule (Owner, or the human at rung 3), *plus* a board post, *plus* the inbox entry the doorbell points at. The skill halts on the request, not on the paragraph. | the four stop skills and every skill with a hard veto |

### 7b.3 Per-skill changes (27, grouped by role)

Each row names the smallest change; the control is P8's `verify-skill-contracts.py` unless stated.

**Group A — dispatchers (take the Coordinator seat)**

| Skill | Change |
|---|---|
| `prepare-for-coordination` | Stage 0 runs CO-S0 on the scope; every track row gains **deadline · fallback · termination condition · target harness · doorbell status** (from `HARNESS_STATUS`); the plan names the leader (`coord leader pin`) for S3 and records the compiled prompt id per track |
| `execute-with-coordination` | Stage 3 dispatches the *compiled* contract (`coord dispatch` for cross-harness, native spawn otherwise); Stage 5 reads `coord mail read` and the board rather than polling returns; the kick ladder replaces the two-pass "not converging" rule; Stage 6 runs `coord leader who` before `conductor-join.py`; exit evidence arrives as a `done` message pinned to a blob, verified as today (E16) |
| `optimize-graph` | Stage 0 triage consumes the compiled prompt (it no longer derives the goal state from raw prose); every fan-out node it emits carries the five parts **plus termination condition, deadline and fallback**, so the plan is directly dispatchable; the cost ledger it records gains the mail and doorbell counts |

**Group B — prose-input workflow skills (rhetorical councils today; run as either seat)**

| Skill | Change |
|---|---|
| `specify` · `define-architecture` · `design-slice` · `implement` · `investigate` · `ui-design` · `collectknowledge` · `forensicreview` · `migrate` · `document` · `code-hygiene` · `adopt` · `visualize` · `adddomainexperts` | Cite CO-S0 before grounding and CO-S1 in frontmatter. The Cast stays rhetorical at T0; at T1/T2 with a fan-out cap above zero, an adversary persona **may be spawned as a Sub-Agent under the contract** and its hard veto becomes a **decision request → numbered ruling** (D6) instead of "authors do not self-clear" prose. The `Handoff:` line stays for the Coordinator seat and becomes the `done` message for the Sub-Agent seat |
| `investigate` · `forensicreview` · `code-hygiene` (fix) | The Stage-7 **STOP** is CO-S2: a decision request to the human seat, posted to the board, with the report as the referenced blob. "Do not proceed even on autopilot" is now enforced by the absent ruling, not by the paragraph |
| `implement` | Its Proof Pack is the canonical **exit evidence** shape for a `done` message; the pre-merge adversarial review is the hook-gated Owner review (`TaskCompleted` / `Stop` exit 2 where the harness has it) |
| `design-slice` · `implement` · `ui-design` | Their CTX-E rule ("do not re-invoke to re-read") extends to the compiled prompt: a Sub-Agent receives the contract once, in the brief, never by re-invoking the skill |

**Group C — measurement and utilities (read the new plumbing; dispatch nothing)**

| Skill | Change |
|---|---|
| `session-profiler` | New indicators: messages sent/read/acked per session, doorbell latency per harness, board read-rate, contracts refused at dispatch, compiled-vs-run edit distance; SP-15 also reconciles `coord session list` against mail senders |
| `dream` | Mines refused dispatches, boundary corrections and compile assumptions as candidate classes; PACK-O's presence signal now includes the compiled prompt id |
| `apply-learnings` | Unchanged mechanics; its plan-per-repo becomes a `decision-request` to each repo's human seat when the target runs the layer |
| `also` | Re-sizing the fan-out cap now **recompiles** (CO-S0) so the addendum carries a compiled prompt; the `pending` row references it |
| `auditlog` | Gains the *Messages* view (P6): the board over `docs/audit/index.html` beside the timeline |
| `prompts` · `searchprompts` | Show raw and compiled prompts side by side; reuse copies either; search matches both |

**Group D — pack lifecycle (install the plumbing per harness)**

| Skill | Change |
|---|---|
| `addpacktorepo` · `updatepack` | Install the five doorbell adapters (hook files per harness), create `.agents/mail/` (ignored) and stop ignoring `.agents/log/` (D10), ship `pack/adapters/prompt-templates/<harness>.md`, and report each harness's doorbell status from `pack-doctor` (`verified · observed-only · unsupported`) |
| `extendaibundle` | "Both tool surfaces" becomes **every harness surface plus a seat declaration**: a new skill without `Runs as:` and, when it dispatches, without the five-part contract fails `verify-skill-contracts.py` at authoring time |

### 7b.4 The compile stage (P7) — from the operator's words to the starting prompt

**What it is.** A `compile` step that turns the human's text into the **harness- and model-specific
prompt a workflow starts from**, before `/optimize-graph` or `/prepare-for-coordination` plan anything.
Today the goal state (CT19) is written by the running agent from raw prose on every turn, in every
harness, with no record of what it inferred. Compilation makes that a first-class artifact with a
control on it.

**What it emits** — one document, in the target harness's idiom:

| Part | Content | Where it comes from |
|---|---|---|
| Goal state | Goal · Done when · Not in scope · Tier · Fan-out cap · Context ceiling · Main-line budget (CT19) | the prose, and only the prose; every clause traces to a phrase |
| Resolved references | every path, id, spec and ADR the prose names, **opened and confirmed to exist**; the docs-graph neighbours a grounding would traverse | `docs-graph.py`, the filesystem |
| Assumptions | one `assume:` per belief the prose leaves open — the belief, what confirms it, what breaks if false (NG); **consequential ones become decision requests before dispatch** | the compiler's own gaps |
| Harness idiom | the shape the target actually accepts: a Claude Code brief (absolute paths, no `EnterWorktree`, the `start` line first); `codex exec` with `--output-schema`; `copilot -p`; agy `injectSteps`; Grok `-p` | `pack/adapters/prompt-templates/<harness>.md` |
| Contract slot | the five parts and the termination condition, empty until a Coordinator assigns the work — **a compiled prompt is a contract before it has an assignee** | GO7, D5 |

**How it runs.** Ladder-first: `prompt-compile.py` (stdlib) builds the deterministic skeleton —
resolved references, graph neighbours, the harness template, the audit ids — and the running model
fills the five goal-state fields and the assumptions. Harness-specific shape is **Verified** (the
dispatch forms were probed in §5). Model-specific phrasing is a template per harness and is
**Inferred until measured**: the measurement is the edit distance between the compiled prompt and what
the human actually ran, which is why raw and compiled are logged together (`kind:prompt`,
`prompt_compiled`, `target_harness`, `compiler_model`) and why `/prompts` shows both.

**Where it sits.** A utility skill, `/compile` (skill count 27 → 28), whose engine the fourteen
prose-input skills call at CO-S0 when no compiled prompt is in hand. The human can run it alone, edit
the result, and then start the workflow from it — the "better starting point" the maintainer asked
for. `/also` recompiles when it re-sizes a turn.

**What it must never do.** Add scope. *Autonomy is latitude in the how, never the what* (CT19): a
*done-when* clause that traces to no raw phrase and no marked assumption is the compiler authoring a
goal, and `verify-compiled-prompt.py` refuses it. It also never resolves an assumption by guessing —
the three moves remain check, mark, ask — and a compiled prompt with any of the five fields missing is
refused, so a skill cannot start on a half-compiled prompt.

**What it measures** (IO): compile duration and tokens; assumptions surfaced per prompt and how many
became decision requests; edit distance compiled → run; and downstream, boundary corrections and
refused decisions per track in `coord metrics`, which is the number that says whether compiling paid.

### 7b.5 Controls and measurements for the skill work (P8)

- `verify-skill-contracts.py` (a lint over `pack/commands/*/SKILL.md`, `--self-test`): every skill
  carries `Runs as:`; a skill that names a fan-out cap above zero cites CO-S0 and the five-part
  contract with a termination condition; a hard-stop stage cites CO-S2; a dispatcher never spawns
  before the compile stage. Red first against today's tree (25 of 27 fail on `Runs as:` alone).
- `context-budget` for the added lines — the shared stages are cited, never copied.
- `/session-profiler` reports per-skill fan-out actual vs cap, contracts refused at dispatch, and
  compiled-vs-run edit distance; a skill whose delegations are refused repeatedly is a class, not an
  incident (CI).

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
| D9 | **Revised 2026-09-19 (maintainer):** a **formal local message layer** ships — per-session inbox files as the store, the harnesses' native doorbells as the push (Claude Code cross-session socket, `codex queue`, Antigravity `PreInvocation injectSteps` / `PostInvocation force_continue`, Copilot and Grok hooks at the tool boundary), dual-written to the ledger so **git stays the durable fallback and the cross-machine path**. What stays struck: a daemon or broker as the message *store*, a cloud relay, election, phi detectors, automatic reassignment, per-sub-agent worktree mandates. See §4b. | Claude Code's own effectiveness comes from inter-agent messaging, and its shipped shape is exactly "file registry + doorbell"; the measured ai-de failure was a *pull* nobody read, not messaging itself |
| D10 | Pack default tracks the ledgers (ai-de's split) — **ratified 2026-09-19** | A8; cross-machine S3 needs it |
| D11 | Vocabulary: Owner (seat) · human operator · AgentPlane conductor | ai-de collision |
| D12 | **A board for human transparency** — `coord board` is a read model over the inboxes and the ledger's message events (terminal `--follow` and the operator HTML), and humans post into the same inboxes with `coord board post`. It is never a second store. | The maintainer wants to see messages without reading git; the prior proposals' board failed because nothing *wrote* to it, not because a board is wrong |
| D13 | Leader lease constants: TTL **300 s**, renew every **100 s** (TTL/3), retry **20 s**, quiet period **30 s** after invalidation — **ratified 2026-09-19**; tuned from `coord metrics` | k8s ×20 for a sleeping laptop fleet; Consul lock-delay ×2 |
| D14 | **Compile stage** (§7b.4): the operator's prose is compiled into the harness- and model-specific starting prompt before any planning skill runs; the compiler may **check, mark or ask, never add scope**; raw and compiled are logged together — **added 2026-09-19 (maintainer)** | CT19 (autonomy is the how); NG1–NG11; the goal state was rewritten from raw prose on every turn with no record of what was inferred |
| D15 | **Skills cite three shared stages** (CO-S0 compile · CO-S1 seat · CO-S2 stop = message) written once in the doctrine doc; every skill declares `Runs as:`; the Cast stays rhetorical at T0 and becomes a contracted Sub-Agent only above it — **added 2026-09-19 (maintainer)** | §7b.1: 25 of 27 skills have no delegation plumbing; context-budget forbids copying a stage into 27 files |

## 10. Open questions for the maintainer

*All four answered by the maintainer on 2026-09-19; recorded here and in
`docs/notes/note-20260919-coordination-decisions-ratified.md`.*

1. **Ledger tracking default (D10):** **change the default.** The pack's `.gitignore` fragment will
   track `.agents/log/`, `.agents/requests.jsonl` and `.agents/sessions/` and keep ignoring
   `.agents/decisions/` (ai-de's split); `pack-doctor` reports which state a repo is in.
2. **Leader lease constants:** **TTL 300 s with a 30 s quiet period**; renew at TTL/3 (100 s),
   retry 20 s; tuned from `coord metrics` (D13).
3. **Copilot:** **probe first; inbox + commit floor is the accepted default.** Probed 2026-09-19
   against docs.github.com: Copilot CLI hooks are `sessionStart`, `sessionEnd`, `preToolUse`,
   `postToolUse`, `userPromptSubmitted`, `agentStop`, `subagentStop` and `errorOccurred`, configured
   per platform with `bash`/`powershell` keys — so the inbox can be drained at `preToolUse`
   (next tool boundary) and at `agentStop`. Whether `agentStop` can keep the agent working is
   recorded in §4b from the reference page; until a live session shows a drain firing, Copilot is
   `observed-only`.
4. **Antigravity hook surface:** **probed 2026-09-19 (antigravity.google/docs/hooks).** Antigravity
   fires `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation` and `Stop`; every payload
   carries `conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath` and
   `modelName`. `PreInvocation`/`PostInvocation` accept **`injectSteps`** (context inserted into the
   trajectory) and `PostInvocation` accepts **`terminationBehavior: "force_continue"`**. That is a
   native doorbell *and* a stop-class hook: the progress heartbeat and the inbox drain both have a
   documented seam on agy.

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
| **Completed** | Grounding in both repositories; four research tracks captured as a knowledge base; three executed spikes; critique of both prior proposals (18 findings); the model, protocol objects, three scenario playbooks, the struck list with reopen triggers, a five-item build plan with controls and measurements, one defect class. **2026-09-19 (this revision):** maintainer rulings applied — D9 revised (formal local message layer, git the fallback), D10 and D13 ratified, D12 board, D14 compile stage, D15 skill stages; §4b message layer; §7b skills evolution from a measured survey of all 27 skills; P4 rewritten, P6–P8 added; Copilot and Antigravity hook surfaces verified from their docs and folded into the KB; decision note `note-20260919-coordination-decisions-ratified`. |
| **Landed (2026-09-19, revisions 76–79)** | **All nine build-plan items are landed** through four coordinated multi-track sessions, each with red-first tests and a `conductor-join.py` join: P7 compile stage (rev 76, `coordination-compile-stage`); P2 leader designation, P4 message layer + dispatch, P6 board, P8 readers + skill contracts (rev 77, `coordination-p2-p8`); P0 doctrine, P1 typed seam requests (rev 78, `coordination-p0-p1`); P3 progress liveness + kick ladder, P5 owner-review mechanics, the cross-platform residue and the P8 skill sweep (rev 79, `coordination-p3-p5-p8`). The struck list's reopen triggers are unchanged; D13's TTL lapse under an interactive coordinator is closed by F-1 (the leader's heartbeat renews the designation) rather than by a constant change. |
| **Remaining** | **The cross-harness smoke test** — `note-20260919-cross-harness-smoke-test-readiness` lists every channel still `observed-only` (heartbeat and the owner-review stop gate on every host; the Copilot, Grok and Antigravity doorbells) and the probe order that promotes each; it needs the operator's harness logins, so it is not a coordinator's task. The `prompt-templates/<harness>.v1.md` texts stay Inferred until compiled-vs-run edit distances accumulate in the audit log. Carried-forward findings live in `coordination-p3-p5-p8` "Carried forward". |
| **Best next action** | Probe 1 of the readiness note in a fresh Claude Code session on this repo (three tool calls → `coord track`; a `decide request` → a refused stop), then `coord dispatch --harness claude-code` to create `harness-status.json`. |
