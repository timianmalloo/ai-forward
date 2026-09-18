---
id: proposal-active-multi-harness-coordination
title: "Proposal: ledger and bus — active multi-harness coordination"
type: doc
status: in-review
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, p2p, multi-harness, leader-election, leases, messaging, rfc]
links:
  - { to: spec-agent-coordination, rel: refines }
  - { to: architecture-agent-coordination, rel: refines }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
  - { to: adr-0005-harness-runner-boundary, rel: depends-on }
  - { to: design-coord-collaboration-phase4, rel: refines }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-12-18"
review-suggested: []
summary: >-
  The coordination layer is a git-tracked ledger with leases, hooks, and a fold. That is the
  right substrate for accountability and it is the wrong substrate for liveness. This proposal
  adds an optional, local-first message bus on top of that ledger: session advertisements,
  heartbeats, blocked-on push, lease-based leader election, and a kick ladder so work continues
  instead of waiting for the next fetch. In-session hierarchy is Owner / Conductor / Worker.
  Between sessions one Conductor is elected Leader. The bus is never the source of truth; if it
  is down the existing layer still works.
---

# Proposal: ledger and bus — active multi-harness coordination

*Research + architecture proposal. **Nothing here is implemented.** Rendered companion:
[`active-multi-harness-coordination.html`](./active-multi-harness-coordination.html) — same content,
formatted for reading. This Markdown is the record (M1: readable with no special tool).*

**Status:** `in-review` — awaiting the maintainer's decision on the open questions in §14.

| | |
|---|---|
| **Date** | 2026-09-18 |
| **Tier** | T2 — sits on the edit path of every harness, federated by the pack |
| **Grounding** | `spec-agent-coordination`, `architecture-agent-coordination`, ADR-0007 / 0008 / 0009 / 0010 / 0011, Phases 1–4 designs, plus the research cited in §15 |
| **Harnesses in scope** | GitHub Copilot (GPT-*), Grok Build, Claude Code, Antigravity — same repo, same worktrees, different runtimes |

---

## 0. Thesis

The pack already built the right **ledger**. It has not built a **bus**.

Git, githooks, PreToolUse, pre-commit, and an append-only JSONL fold give concurrent agents
leases, collision-proof ids, derived-file regeneration, and an audit trail. That layer answers
*"may I touch this file?"* and *"what was decided?"* It does not answer *"the other session is
stuck, tell it, and if it does not move, take the work."*

GitHub and githooks are **eventual**. A claim is visible after a push and a fetch, or after the
next edit-boundary check. A blocked-on edge is a fold, not a message. A stalled session expires
a TTL and is discovered by whoever happens to claim next. Nobody is responsible for chasing
progress. That is the passivity.

The proposal is not "add a daemon and throw ADR-0007 away." It is:

> **Keep the ledger as the source of truth. Add an optional, local-first message bus for
> liveness. Dual-write every coordination act to the ledger so accountability survives the bus
> going down. Elect a Leader among sessions so someone is on the hook for the whole work list.
> Inside a session, name Owner / Conductor / Worker so the most capable model decides and the
> right-sized model executes.**

If the bus is down, the existing layer still works — slower, the way it works today. That is
the NFR-P2 constraint, kept.

---

## 1. Diagnosis — the ledger is correct and too quiet

### 1.1 What the current layer already solves

Measured, designed, and (for Phases 1–4) built:

| Mode | Mechanism | Where |
|---|---|---|
| **M1** Structural conflict on derived files | Artifact class + merge driver that resolves, then `coord regen` | ADR-0009, Phase 3 |
| **M2** Allocation collision | Non-coordinating ids (clock + 80 random bits) | ADR-0008, Phase 3 |
| **M3** Silent divergence | Decision register returned with the grant | Phase 4 |
| **M4** Work loss in a shared tree | One session per worktree; stage-by-name; unique-commit guard | Phase 2, WT1–WT12 |

The substrate decision still holds: **append-only JSONL, one file per session, folded on demand,
no daemon, no database** (ADR-0007). Spike S2 priced a 10,000-event fold at 47 ms p95 against a
100 ms budget. The Simplifier's veto on a required service was upheld by a benchmark, not by
taste.

Enforcement lives at the harness edge (PreToolUse) and at the universal commit floor. Identity
is asserted, not authenticated (ADR-0011). The core is a pure library; each vendor surface is a
thin host (ADR-0005). That composition is why Claude Code, Copilot, Grok, and Antigravity can
share one record.

### 1.2 What it does not solve

Five modes the spec did not name, because the evidence in 2026-08 was merge conflict and lost
work, not stall:

| Mode | What happens today | Why git/hooks cannot fix it |
|---|---|---|
| **M5 Stall** | A session is alive, holds leases, and is not making progress. TTL expiry is the only recovery, and it is silent. | A hook fires on *edit*, not on *absence of edit*. |
| **M6 Passivity** | Session B records `blocked-on: A`. A does not find out until it folds, fetches, or happens to `coord tail`. | Git is pull. There is no push to a running model. |
| **M7 No hierarchy** | Every session is a peer. Decisions that should be made by the strongest model wait for a human, or get made twice. | The session contract has roles as prose. Nothing elects, nothing delegates as a protocol. |
| **M8 No kick** | Nobody is accountable for the *fleet's* work list. A blocked waiter waits. A looping worker loops until a human notices. | The operator view is a query. It is not a supervisor. |
| **M9 Cross-harness liveness** | Copilot, Grok, Claude Code, and Antigravity share a git remote and a JSONL directory. They do not share a live channel. | Each harness's hook surface is an *edit interceptor*, not a mailbox. |

The architecture already recorded the delay that makes this worse: **the gate delay exceeds the
merge interval**, and **the push delay is the window a branch scanner cannot see into**. The
allocator was designed for that window. The lease was designed for the gate delay. Nothing was
designed for "the other agent is in another process, on another harness, and needs to be told
*now*."

### 1.3 The user's diagnosis, restated in the pack's language

> Coordination through GitHub and githooks is too passive. Work should continue actively instead
> of blocking. Inside a session: Owner (most capable) decides, Conductor coordinates and
> delegates, Workers execute. Between sessions: one Leader tracks the total work list and kicks
> sessions that stall.

That is M5–M9. It does not retract M1–M4. A bus that forgets leases, artifact class, or the
fold would re-introduce the four modes we already paid to close.

---

## 2. What we keep — and why a daemon is still not the source of truth

ADR-0007 cut the daemon because:

1. The fold met the latency budget with headroom.
2. A required service makes "the agent cannot work until the service is up" a new failure mode
   (NFR-P2).
3. For a control whose recorded ancestors failed by *reporting success*, a loud non-blocking
   failure is worth more than 20 ms.

Those three reasons still hold for **grants and refusals**. The lease check must not depend on
a live process. The bus proposed here is a **transport**, not a store:

- Every message that changes coordination state is **dual-written** to the session's JSONL.
- The fold remains the only source of leases, work-item status, blocked-on edges, and leader
  identity.
- If the bus is down, unreadable, or unused, the layer says so and degrades to today's
  pull-based behaviour. It does not refuse work because a socket is missing.

The Enterprise Architect's existing ruling is kept verbatim: *if a planner is added later it
may advise, never grant or refuse.* The Leader and the Conductor **advise, delegate, and kick**.
The ledger still grants and refuses.

---

## 3. Research — what to steal, and what not to

### 3.1 Lab multi-agent systems: hierarchy is real, sync is the bottleneck

**Anthropic, "How we built our multi-agent research system" (2025-06-13).**
Orchestrator-worker. Opus 4 lead + Sonnet 4 subagents beat single-agent Opus 4 by **90.2%** on
their internal research eval. Token usage alone explained **80%** of BrowseComp variance.
Multi-agent runs use about **15×** the tokens of a chat — the pack already encoded this as GO6.
They also recorded the production failure that matches M5/M6 exactly:

> The lead agent executes subagents *synchronously*. It cannot steer them, they cannot
> coordinate, and the system can be blocked waiting for one subagent. Asynchronous execution
> would enable extra parallelism, at the cost of result coordination, state consistency, and
> error propagation.

They also shipped two tactics we should copy, not rediscover:

- **Teach the orchestrator to delegate with an objective, an output format, tools, and
  boundaries.** Vague instructions made three subagents duplicate the same search.
- **Subagent output to the filesystem**, passing a reference back, to avoid the game of
  telephone. Our worktrees and the coordination record *are* that filesystem.

**Microsoft Magentic-One (2024-11) and Magentic-UI (2025).**
A lead Orchestrator runs two loops. The **outer loop** owns a Task Ledger (facts, guesses,
plan). The **inner loop** owns a Progress Ledger (current assignment, "is progress being
made?"). If the stall count exceeds two, the outer loop replans. That is kick-and-replan as a
control loop, not as a hope. Magentic-UI then put a human on the team as `UserProxy` and added
co-planning, co-tasking, and action guards — the Owner in this proposal is that seat, occupied
by the strongest model *until* it must escalate.

**The 2026 protocol stack has split into layers, and we should not smash them together.**

| Layer | Protocol | Job | Our mapping |
|---|---|---|---|
| Agent ↔ tools | MCP (Anthropic → Linux Foundation Agentic AI Foundation, Dec 2025) | Call tools | Existing: `coord` CLI / future MCP host over the same core |
| Agent ↔ editor | ACP (Zed, Aug 2025; JetBrains co-maintains; v2 draft Jul 2026) | Drive a coding session inside an editor | Out of scope. We do not become an IDE. |
| Agent ↔ agent | A2A (Google, Apr 2025; Linux Foundation; v1.0 Mar 2026; 150+ orgs) | Discover, delegate, converse across vendors | **The bus's public shape, later.** Session Cards should be able to become A2A Agent Cards. |
| Internet of agents | AGNTCY (Cisco → LF, Jul 2025), ANP (W3C CG, still draft as of 2026-06) | DNS-like discovery, signed identity, SLIM messaging | Overkill for one laptop. Design so a later remote hop can speak them. |

IBM's Agent Communication Protocol merged into A2A (archived Aug 2025). Do not mint a fourth
wire format. Local v1 can be JSON lines over a Unix socket; the *schema* of a Session Card
should be A2A-shaped so the adapter is a rename, not a redesign.

Anthropic's own caution, which the pack already believes: **most coding tasks have fewer truly
parallelizable pieces than research, and models are not yet great at coordinating in real
time.** Parallelism is a cost multiplier (GO6). The bus exists so the parallel work we *do*
choose is not left to rot when one participant blocks.

### 3.2 Agent-native repositories: do not replace GitHub; steal the live thread

**Zed Delta (private beta Aug 2026, public beta 2026-09-16).**
The sharpest "replace GitHub" attempt in this window. They disabled pull requests on Delta's
own repo and landed 570 changes to main from 33 people. The unit of work is a **thread**
(conversation + edits + worktrees + review), not a PR. DeltaDB extends Git with incremental
deltas between commits so the *reasoning* is not thrown away at `git commit`. Collaboration
does not wait for a push. They still keep Git as the checkpoint you build from, and they still
use GitHub for `zed-industries/zed` community contributions.

What to steal: **the thread as the live unit, conversation glued to the worktree, review as a
subthread with an isolated copy.** What not to steal: replacing PRs, replacing Git, standing up
a CRDT database as the source of truth. Our ledger already is the conversation-about-intent;
Git already is the checkpoint. The missing piece is the live thread *between harnesses that are
not Zed*.

**Agent Client Protocol (ACP).** Zed's "LSP for agents." Editor spawns agent over JSON-RPC.
Grok Build, Claude Code (via adapter), Copilot, Gemini CLI, Goose, OpenHands sit in that
ecosystem. ACP is **agent ↔ client**, not agent ↔ agent. We compose with it; we do not compete
with it.

**CodeCRDT (Pugachev, arXiv:2510.18893, Oct 2025).**
Observation-driven coordination: agents watch a CRDT, claim TODO placeholders, no explicit
mailbox. 600 trials. **Zero merge failures.** Up to **21.1% faster** on parallelizable tasks,
up to **39.4% slower** on coupled ones. Semantic conflicts remain **5–10%** — the CRDT cannot
see them. Median update latency 50 ms. This is independent confirmation of two pack doctrines:
(1) tightly-coupled work is cheaper serial (GO5); (2) structural merge is the wrong problem
(ADR-0009 already moved derived files out of the lease). Do **not** put source files on a CRDT.
A CRDT of *presence and work-item state* is a plausible read-model for the bus. The ledger
stays the write-model.

**AgentRoom (Lee, 2026-08, arXiv:2608.23740)** makes the same split we want: CRDT for the
filesystem *plus* explicit file-level claims as MCP tools. Their contrast with CodeCRDT is
ours: observation alone under-detects semantic conflict; explicit claims (which we already
have) suppress it.

**GitButler vcbench (2026-07) and Jujutsu.**
GitButler ran ~60% faster than git with ~80% fewer commands when Claude Opus and GPT-5.5 did
commit-split-squash work. Jujutsu's always-committed working copy, undo, and conflict-as-commit
are a better *agent VCS UX* on top of a Git backend. Both are complementary. They do not
coordinate two harnesses. They make each harness less likely to lose work inside one tree —
which we already address with WT1 and the unique-commit guard. Mentioned so we do not "solve"
VCS UX in this proposal.

### 3.3 Classic P2P and distributed systems: the lessons that still bite

The user's instinct to look at JXTA, Napster, and friends is the right one. Multi-harness
coordination on one repo is a small peer network with extreme churn (sessions die mid-turn)
and a requirement that *work not stop when the directory is down*.

| System | Shape | Lesson we take | Lesson we refuse |
|---|---|---|---|
| **Napster (1999–2001)** | Central directory, P2P transfer | A directory is fast to search and easy to reason about. Use one as *bootstrap* (the Leader). | The directory as the only path. Napster died at the centre. If the Leader is down, peers must still find each other from the ledger. |
| **Gnutella 0.4/0.6** | Flood, then ultrapeers | Membership must be hierarchical or the cheap nodes drown. 50% of early traffic was pings. | Flooding heartbeats across all sessions. Five to twenty local sessions do not need a DHT; they *do* need to not ping-flood. |
| **JXTA (Sun, 2001)** | Peer advertisements, peer groups, rendezvous, pipes, resolver | **This is the vocabulary.** A session publishes an advertisement (who I am, what I can do, how to reach me). Peers self-organise into a group (the repo / workstream). An optional rendezvous caches advertisements. Pipes carry messages. The resolver answers "who holds this lease / who is Leader." | Implementing JXTA. It was a platform in search of an application, and the early discovery implementation did not scale. Steal the *concepts*, ship JSON. |
| **BitTorrent** | Tracker + swarm, rare-first, tit-for-tat, optimistic unchoke | Work items are pieces. The Leader is the tracker (who has which piece). Rare-first = the serial spine goes first. Tit-for-tat = finish-and-release to get the next assignment. Optimistic unchoke = give a stalled session a small piece to restart it. | Treating source files as pieces of a blob. The artifact-class registry already says which contention is real. |
| **Kademlia / libp2p** | Structured DHT | Right for thousands of untrusted peers. | Wrong for ≤20 trusted-enough sessions on one machine. |
| **Chubby / etcd** | Lease + sequencer | **Leader is a lease, not a personality.** A sequencer/token lets anyone verify the order of leadership. Heartbeat renewal. If the leader fails to renew, someone else takes the lease. | Building a Raft cluster for five local processes. |
| **Phi-accrual (Hayashibara 2004; Cassandra, Akka)** | Continuous suspicion, not binary dead/alive | Stall ≠ dead. A session can heartbeat and still make no progress. Two detectors: liveness-φ (heartbeats) and progress-φ (work-item events). Kick on progress-φ; re-elect on leader liveness-φ. | A single TTL for both "process died" and "model is looping." |
| **SWIM** | Indirect probe + gossip | False positives drop if you ask K peers to ping on your behalf before declaring death. Cheap even at small N. | Gossip as the *work* channel. Work messages are directed. |
| **CRDTs / Automerge / Yjs** | Strong eventual consistency | Fine for presence sets and the operator view. | Not for authored source (semantic conflicts, CodeCRDT 5–10%). Not a replacement for the fold. |

**The hybrid that actually survived in P2P history is Napster's transfer path plus BitTorrent's
tracker-as-bootstrap plus JXTA's advertisements.** Centralised enough to be fast, decentralised
enough to survive the centre dying, with a published card so strangers (here: other harnesses)
can find you without a prior handshake.

---

## 4. Proposed architecture

### 4.1 Two planes

```text
┌─────────────────────────────────────────────────────────────────┐
│  Owner (strongest model in the session)                         │
│    decides, reduces human interaction, holds the veto           │
└───────────────┬─────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────┐
│  Conductor (highly capable model)                               │
│    decomposes, delegates, joins, watches stalls                 │
│    if elected: Leader of the fleet                              │
└───────┬───────────────────────────────┬─────────────────────────┘
        │ in-session                    │ between-session
        ▼                               ▼
┌───────────────┐              ┌────────────────────┐
│ Workers       │              │ Other sessions'    │
│ (right-sized) │              │ Conductors         │
└───────────────┘              └────────────────────┘
        │                               │
        ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  BUS  (optional, local-first)                                   │
│  advertisements · heartbeats · blocked-on · kick · delegate     │
│  never the source of truth · fail open to the ledger            │
└───────────────────────────────┬─────────────────────────────────┘
                                │ dual-write
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEDGER  (existing, required)                                   │
│  .agents/log/<session>.jsonl  fold → leases, work items,        │
│  decisions, blocked-on, leader lease, kick history              │
│  enforced at PreToolUse + pre-commit                            │
└─────────────────────────────────────────────────────────────────┘
```

**Stocks** the bus adds: live Session Cards; a leader lease; a progress-φ per work item; an
in-flight message window.

**Flows:** intent still goes to the ledger first (or atomically with the bus write). The bus
carries a *copy* to whoever needs to act now. Kick, delegate, and unblock are the new flows.

**Feedback loops.** Deliberate: a kick raises progress-φ visibility → the session either moves
or loses the lease → waiters unblock. Vicious, to prevent: kick storms (a flapping detector
kicks a slow-but-working session, which then churns). Caps: max kicks per work item, backoff,
and "progress-φ uses the session's own inter-event history," not a global 30-second timeout.

### 4.2 JXTA vocabulary, grounded in this repo

| JXTA | Here | Stored in |
|---|---|---|
| Peer Advertisement | **Session Card** — harness, model, role, capabilities, worktree, current leases, listen address | Ledger event `session-card` + bus hello |
| Peer Group | The repository, or a named workstream inside it | Session contract (already exists) |
| Rendezvous | Optional `coord bus` process, bound to a Unix socket under `.agents/bus/` | Not git-tracked (runtime); its *membership view* is a fold |
| Pipe | Directed message: kick, delegate, progress, blocked, unblocked | Dual-write: socket + ledger event |
| Resolver | `coord who --path` / `coord leader` | Fold of the ledger; bus is a cache |
| Peer Information Protocol | Heartbeat + progress events | Bus; folded for the operator view |

### 4.3 Session Card (the advertisement)

Issued at `SessionStart` (the hook already runs on Claude Code, Grok, and Antigravity; Copilot's
session-start event is still unverified — that residual stays named). Shape, A2A-compatible:

```json
{
  "kind": "session-card",
  "session": "ses_01…",
  "agent": "grok",
  "harness": "grok-build",
  "model": "grok-4.6",
  "roles": ["conductor"],
  "capabilities": ["edit", "test", "review"],
  "worktree": "/Users/…/ai-forward-active-coord",
  "branch": "proposal/active-coordination-bus",
  "listen": "unix:.agents/bus/ses_01.sock",
  "card_version": 1
}
```

`roles` is claimed, not granted. The Leader lease (below) is the only role that is exclusive.
Owner and Conductor may be the same process; they are distinct *seats* so a session can later
split them without a protocol change.

### 4.4 Trust boundary

The architecture already named the dangerous one: **text authored by one model, injected into
another** (ADR-0011 / architecture §7-E). The bus makes that channel hotter, not new.

Rules, carried forward and tightened:

1. Bus payloads are **data, never instruction.** Fixed schema, length-capped, scrubbed with the
   existing `scrub.py` (not a second implementation).
2. A kick/delegate message is rendered into the receiving model under an explicit untrusted
   heading, the same way the Phase-4 projection is.
3. v1 is **loopback only.** Unix sockets under the repo's `.agents/bus/`. No TCP, no LAN, no
   cloud. Remote / A2A is P8 and wants signed Agent Cards.
4. Identity remains asserted (ADR-0011). A session that sets `AGENT_SESSION` to another's can
   already release leases; the bus does not make that worse, and the record still shows who
   wrote what.

---

## 5. In-session hierarchy — Owner, Conductor, Worker

This is Magentic-One's Orchestrator plus Anthropic's lead/subagent split, named in the session
contract so it is a mechanism, not a prompt.

| Seat | Who sits in it | What it may do | What it must not do |
|---|---|---|---|
| **Owner** | The most capable model available to that session (Opus-class, Grok 4.6, GPT-5.x as configured) | Decide architecture, scope, and "is this done." Reduce human interaction by taking decisions the human would otherwise be paged for, *within a written mandate.* Escalate when the mandate does not cover it. | Grant or refuse leases. Edit paths it does not own. Quietly expand the goal. |
| **Conductor** | A highly capable model; may be the same process as Owner | Decompose, assign, join, watch progress-φ, send delegate/kick *inside the session*, and stand for Leader *between* sessions. | Do the Workers' jobs by default (GO6). Spawn unbounded subagents (Anthropic's "50 subagents for a simple query"). |
| **Worker** | Right-sized model for the task (faster/cheaper for impl, a reviewer persona for attack, etc.) | Execute one assignment against owned paths. Write artifacts to the worktree and return a reference, not a novel. | Re-plan the session. Touch another Worker's owned paths. |

**Mandate.** The Owner's autonomy is the session contract's "Accountable for" column plus a
short written mandate at session start (goal, done-when, not-in-scope, decision rights). This
is CT19 applied to the *fleet*, not just the turn. A decision the mandate does not cover is
escalated — to the Leader if it is in-flight coordination, to the human if it is product
intent.

**Delegation contract**, stolen from Anthropic's "teach the orchestrator to delegate":

Every `delegate` message contains all four, or it is incomplete:

1. Objective (one sentence).
2. Output format / artifact path.
3. Tools and sources in bounds.
4. Boundaries (paths, what not to do, fan-out cap, budget).

The Worker writes the artifact to the worktree (or the record) and returns a **reference**.
The Conductor does not relay the Worker's prose. That is the filesystem-not-telephone rule.

**Join.** The Conductor is the only seat that calls `conductor-join.py`. Workers do not join
their own work. This is already pack doctrine (CT27); the bus just makes the join *requested*
rather than polled.

---

## 6. Between-session Leader — election, work list, kick

### 6.1 Leader is a lease

One Leader per **peer group** (the repo, or a named workstream). The Leader is a Conductor
that holds an unexpired `leader-claim` in the ledger.

```text
coord leader claim --group <repo|workstream> --ttl 30
coord leader renew
coord leader who
coord leader pin <session>     # human override; optional
```

Election:

1. If a valid claim exists, it is the Leader. Others renew nothing.
2. If the claim is expired (Leader failed to renew), any Conductor may claim. First append
   wins; the fold is the total order. Same "advisory-until-checked" honesty as intersecting
   path claims (architecture §10). The loser backs off.
3. Tie-break is not "highest model IQ." Capability is advertised on the Session Card so a
   human can `pin`. Automatic ranking of models is a policy file if we ever want it; it is
   not the protocol. A wrong automatic ranking would elect a fast, shallow Leader — the
   failure mode Magentic-One avoided by putting the strong model on the Orchestrator.
4. A sequencer (Chubby's word) is the `leader-claim` event id. Any session can verify "this
   kick came from the current Leader" by checking the id against the fold.

Renewal is a heartbeat to the bus **and** a ledger event, rate-limited so we do not turn the
JSONL into a ping log (Gnutella's 50% warning). Suggested: renew every ~ttl/3, compact
heartbeats out of the live fold at the existing 10k-event trigger.

### 6.2 What the Leader is for

The Leader is not a second Owner of every session. It is the **fleet supervisor**:

- Holds the **work list**: every open work item, its owner session, its blocked-on edges, its
  progress-φ.
- Ensures the coordination layer is actually running (`coord doctor` as a periodic self-check,
  not a human ritual).
- **Kicks** when progress-φ crosses the threshold.
- **Reassigns** after kick-without-ack, or after liveness-φ says the holder is gone.
- Unblocks waiters the moment a dependency's `done` (or `release`) hits the bus.

It may **advise** assignment. It may not grant a path lease — `coord claim` still does that,
and the hook still enforces it. A Leader that wants session B to take a file sends `delegate`;
B claims; the ledger grants or refuses.

### 6.3 The kick ladder

Copied from Magentic-One's stall-count, named as a ladder so it cannot jump to "steal the
work" on the first blip.

| Rung | Trigger | Act | Dual-write |
|---|---|---|---|
| **0 Notify** | `blocked-on` recorded | Bus delivers `blocked` to the holder immediately. Holder's model sees it on the next turn, or via hook `additionalContext` if we can do that without violating the projection rules. | `blocked` event |
| **1 Kick** | progress-φ ≥ kick threshold, or notify unanswered across one TTL | Leader sends `kick` with reason, suggested action, deadline. | `kick` event |
| **2 Reassign** | Kick unanswered, or liveness-φ says dead | Leader marks the lease expired *as an event* (today expiry is computed, not written — write it, so it is visible) and `delegate`s the work item to a capable idle session. The new session still has to `claim`. | `reassign` + `delegate` |
| **3 Owner** | Reassign failed, or the work item is a decision not a task | Escalate to the holding session's Owner, or to the Leader's Owner if the holder is gone. | `escalate` |
| **4 Human** | Mandate does not cover it, or two Owner decisions conflict | Stop. The operator view already exists for this; the bus just pages it instead of waiting to be asked. | `escalate-human` |

Caps: at most **two kicks** per work item per hour before rung 2. Progress-φ is computed from
*that session's* inter-progress intervals (phi-accrual), not from a global "30 s of silence
means dead." A research session that heartbeats every turn and writes every five minutes is
healthy. A coding session that claimed `src/**` and has not appended a progress event in the
time it usually takes that session to edit is not.

### 6.4 BitTorrent scheduling, used lightly

Work items already exist in the spec. Treat them as pieces only for **ordering**, not for
file transfer:

- **Rare-first.** The serial spine (the spec already requires it be named) is scheduled before
  the parallel tracks. A Leader that hands out leaf tasks while the interface is still unset
  is repeating the GO5 failure.
- **Tit-for-tat.** A session that completes and releases is next in line for the next
  independent piece. A session that sits on a lease does not.
- **Optimistic unchoke.** After a kick, give the same session a *smaller* piece once, to see
  if it restarts, before reassigning. Cheap, and it avoids the "one timeout and you are
  evicted" failure that made early lease designs hostile.

Do not swarm the contents of a file. Artifact class still decides that.

---

## 7. Message vocabulary

All messages are JSON objects with `kind`, `id` (allocator), `from`, `to` (`*` for group
broadcast, used only for `hello` and `leader-heartbeat`), `at`, and a typed body. Broadcast
is membership-gossip only. Work messages are directed. (Gnutella: do not flood queries.)

| `kind` | Direction | Body (minimum) | Ledger? |
|---|---|---|---|
| `hello` | session → group | Session Card | yes, once per card version |
| `heartbeat` | session → Leader | `liveness: 1` | no (or sampled) |
| `progress` | worker/conductor → Conductor/Leader | `wi`, `status`, `last_act`, `ref` | yes |
| `blocked` | waiter → holder, copy to Leader | `wi`, `on`, `need` | yes |
| `unblocked` | holder/Leader → waiter | `wi`, `reason` | yes |
| `delegate` | Conductor/Leader → Worker/session | the four-part contract in §5 | yes |
| `kick` | Leader → session | `wi`, `reason`, `suggest`, `deadline` | yes |
| `ack` / `nack` | receiver → sender | `ref`, `why` | yes for kick/delegate |
| `leader-claim` | Conductor → group | `group`, `ttl`, `sequencer` | yes |
| `reassign` | Leader → group | `wi`, `from`, `to`, `why` | yes |
| `escalate` | any → Owner / human | `wi`, `why`, `mandate_gap` | yes |

Idempotent by `id`. A retried hook or a duplicated socket write is a no-op. Same rule as
Phase-1 claims.

**Projection into a model.** The receiving harness still has to *show* the message to the
model. Three adapters, in preference order:

1. **Hook `additionalContext` / `systemMessage`** on the next tool boundary (already used by
   `reread-guard.py`). Best effort; the model only sees it when it next touches a tool.
2. **Mailbox file** `.agents/bus/inbox/<session>.jsonl` that a session-start and a periodic
   "read your mail" prompt in AGENTS.md tell the model to fold. Works even when hooks cannot
   inject. The file is runtime, gitignored, rebuilt from the ledger on demand.
3. **Operator page.** For the human at rung 4.

None of these is a daemon the agent must start. (1) piggy-backs on the edit path. (2) is a
file. (3) is the existing operator view with a badge.

---

## 8. Transport — local-first, optional rendezvous, stdlib

Solution-Selection Ladder, applied:

| Rung | Decision |
|---|---|
| 1 YAGNI | The five missing modes are real. A bus earns its place. A Raft cluster does not. |
| 2 Reuse | SessionStart hook, `coord-core` fold, Unix sockets, the allocator, `scrub.py`. |
| 3 stdlib | `socket`, `selectors`, `json`, `os`. No Redis, NATS, libp2p, MQTT, sqlite. |
| 4 native | Unix domain sockets under `.agents/bus/`. Optional `launchd` user agent later, never required. |
| 5+ | Not reached in v1. |

**Discovery, Napster-as-bootstrap:**

1. On SessionStart, write the Session Card to the ledger and to `.agents/bus/peers/<session>.json`.
2. Try to connect to `.agents/bus/rendezvous.sock`. If it exists, register. If it does not,
   **do not start it automatically.** The first session that wants to be Leader may start
   `coord bus serve` in-process as a thread, or the operator starts it once. If nobody does,
   peers still read `peers/*.json` and connect **directly** (full mesh is fine at N≤20).
3. Git remains the discovery path across machines and after a reboot: fetch, fold, see cards.

That is JXTA rendezvous as an optimisation, not as a requirement. It is also NFR-P2: an agent
can work the moment it has the repo.

**Direct pipes.** `unix:.agents/bus/<session>.sock` owned by that session. The session process
accepts, or a tiny per-session helper started by the same hook that already cannot fail closed
(`session-start.py` exits 0 on every path). If the socket is absent, senders write the ledger
and the inbox file only.

**Windows.** Named pipes, same path contract, or fall back to inbox-file-only on platforms
where UDS is painful. The ledger path is the portable one; the socket is a fast path.

---

## 9. Cross-harness reality

The pack already installs four surfaces. The bus must not grow a fifth core.

| Harness | Edit enforcement today | SessionStart today | Bus adapter |
|---|---|---|---|
| Claude Code | PreToolUse deny (executed) | `session-start.py --host claude` | Inject via `additionalContext`; UDS in the session process or a helper |
| Copilot CLI | PreToolUse invoked; **deny not verified**; timeout **fails open** at 30 s | **Not wired** | Inbox file is the floor until session-start is verified. Do not advertise "live kick into Copilot" until it is. |
| Grok Build | PreToolUse (project hooks need trust) | `--host grok` | Same as Claude; Grok already aliases the Claude payload shape |
| Antigravity | `view_file` / `PreInvocation` | `--host agy` | Same helper; `conversationId` is the session key |

The conformance rule from Phase 3 stands: **never advertise a harness mode you have not
executed.** Copilot's live injection is `unsupported` until a deny *and* a session-start have
been seen on this machine. Until then Copilot is ledger + inbox file: better than today
(the inbox is local and does not wait for a push), not as live as a socket.

---

## 10. Failure modes

| # | Mode | Disposition |
|---|---|---|
| B1 | Bus down / socket missing | **Degrade.** Ledger + inbox file. `coord doctor` reports `bus: advisory`. Never refuse an edit because the bus is down. |
| B2 | Leader dies holding the work list | **Recover.** Leader lease TTL; next Conductor claims. Work list is a fold, so nothing was only in the Leader's head. |
| B3 | Two Leaders (partition, or two claims in one ms) | **Detect.** Fold picks one by total order; the other sees `leader-claim` refused on its next check and backs off. Same honesty as intersecting path claims. |
| B4 | Kick storm | **Prevent.** Two-kick cap; phi-accrual not a global timeout; optimistic unchoke before reassign. |
| B5 | Leader is a weak model | **Mitigate.** Human `pin`. Default: only sessions that advertised `roles: ["conductor"]` may claim. Do not auto-rank model strings. |
| B6 | Kick as prompt injection | **Mitigate.** Schema + scrub + untrusted heading. No free-text instruction field. `suggest` is an enum (`continue`, `release`, `report-blocked`, `compact-and-resume`), not a paragraph. |
| B7 | Heartbeats bloat the ledger | **Prevent.** Heartbeats are bus-only; sampled into the ledger at most once per TTL. Compaction trigger unchanged. |
| B8 | Session impersonates Leader | **Accept, documented** (ADR-0011) on loopback. P8 (remote) requires signed cards. The sequencer is in the record, so impersonation is visible after the fact. |
| B9 | Conductor telephones Worker output | **Prevent.** Delegate contract requires an artifact path; join reads the artifact. A `progress` with a 4 kB `body` is rejected. |
| B10 | Owner expands the goal | **Detect.** Mandate is in the session contract; a `delegate` whose objective is not a child of the mandate is `nack`'d by the Worker if the Worker was given the mandate, and by the Leader's check otherwise. This is GO1/CT19 at fleet scale. |
| B11 | Empty bus reported as "no stalls" | **Prevent.** Same R4 as the rest of the layer: a status view over zero Session Cards is `NOT CHECKED`, not "all quiet." |

---

## 11. Explicit non-goals

Each with the reason, so this proposal cannot be read as a licence to build them.

- **Replacing GitHub Issues, PRs, or Actions.** Zed is doing that experiment, and even they
  keep GitHub for the public `zed` repo. Our backlog and merge queue stay. The bus is
  in-flight. The spec already said this.
- **Replacing git with DeltaDB, Pijul, or a source CRDT.** Complementary. Out of this change.
- **A required daemon or hosted broker.** Retracts ADR-0007 and NFR-P2. The rendezvous is
  optional. The inbox file is enough for a degraded mode.
- **Implementing A2A, AGNTCY, ANP, or libp2p in v1.** Speak their *shape* (Session Card ≈
  Agent Card). Do not take a wire-format dependency until P8 has a real second machine.
- **A planner that assigns work to minimise overlap.** Still the spec's non-goal. The Leader
  schedules the *already divided* work list (`/prepare-for-coordination` still divides). It
  does not invent tracks.
- **Semantic merge.** Regeneration and refusal stay in; understanding stays out.
- **Enforcing reasoning.** The bus can kick a session. It cannot make the model think. A kick
  that is ignored is a metric (`kick_ack_rate`), not a solved problem.

---

## 12. Phasing

Each phase is a thin vertical slice, demonstrable with two terminals, substitutable at the
seams. Numbered as **P5–P8** so they sit after the existing four, not instead of them.

### P5 — Presence (walking skeleton of the bus)

- Session Card at SessionStart, written to the ledger and to `peers/`.
- Inbox file + `coord mailbox`.
- `hello` / `progress` / `blocked` as ledger events, with an optional UDS fast path if the
  socket exists.
- `coord doctor` grows `bus: off | advisory | live` and **asserts the corpus size** (R4).
- **Demo:** two worktrees. A records `blocked-on: B`. B's mailbox shows it without a fetch.
- **Not yet:** Leader, kick, roles.

### P6 — Leader and the kick ladder

- `leader-claim` / renew / who / pin.
- progress-φ and liveness-φ (stdlib; port the well-known algorithm, do not invent one).
- Kick ladder rungs 0–2. Rungs 3–4 as events the operator view already renders.
- **Demo:** A holds a lease and stops progressing. Leader kicks. A acks or the work is
  offered to C. The record shows the kick.

### P7 — In-session roles

- Session contract template gains Owner / Conductor / Worker seats and a mandate block.
- `delegate` four-part contract, filesystem-not-telephone.
- Conductor may stand for Leader (P6).
- **Demo:** one Grok session as Owner+Conductor, a Claude Code sub-agent as Worker, a Copilot
  session as a second-session Worker. Delegate, join, mailbox.

### P8 — Cards that travel

- Session Card schema frozen as a subset of A2A Agent Card.
- Signed cards (A2A v1.0) only if/when we leave loopback.
- Copilot session-start spike, or an honest `unsupported` forever.
- **Not a promise to implement A2A.** A promise that we will not have to redesign the card.

No phase makes the bus required. A repo that never runs `coord bus` keeps today's behaviour
plus an inbox that fills from the ledger on `coord mailbox` — still a win for M6, still
passive for M8.

---

## 13. Key decisions

| # | Decision | Why |
|---|---|---|
| D1 | Two planes: ledger required, bus optional | ADR-0007 and NFR-P2 still hold for grants. Liveness is a different job. |
| D2 | Dual-write every state-changing message | Accountability is the ledger's job. A bus that is the only copy of a kick is Napster's directory. |
| D3 | Leader is a lease with a sequencer, not a designated process | Chubby. Sessions die. The fold outlives them. |
| D4 | Kick ladder, not immediate reassign | Magentic-One stall-count; phi-accrual; optimistic unchoke. False eviction is worse than a slow session. |
| D5 | Owner / Conductor / Worker as seats in the session contract | Anthropic + Magentic-One, made a mechanism. Capability is configured, not inferred from a model string at runtime. |
| D6 | Delegate with four required fields; artifacts not prose | Anthropic's duplication failure and telephone failure, both measured. |
| D7 | Loopback Unix sockets + inbox file; no required rendezvous | JXTA rendezvous as optimisation. Gnutella ping-flood avoided. Stdlib. |
| D8 | Session Card shaped like an A2A Agent Card | Do not invent a fourth agent identity format. Do not take the A2A dependency in v1. |
| D9 | Do not CRDT the source tree | CodeCRDT: coupled tasks get slower; semantic conflicts remain. We already have artifact class. |
| D10 | Do not replace GitHub | Zed is running that experiment. We need a bus *across harnesses that still push to GitHub.* |
| D11 | Never advertise an unexecuted harness mode | Phase-3 conformance, applied to Copilot live-inject. |
| D12 | Leader advises; ledger grants | Existing council ruling, kept. |

---

## 14. Open questions

For the maintainer. The writer should not silently resolve these.

**Q1. Peer group grain.** One Leader per repo (simple, matches "one work list"), or one per
workstream/session-contract (better isolation when two unrelated efforts share a clone)?
Recommendation: **per session-contract when one exists, else per repo.** A repo with no
contract has at most one Leader.

**Q2. May the Owner and the Conductor be the same process?** Recommendation: **yes, and that
is the default.** Splitting them is for when the Owner is a slow, expensive model that should
not see every progress event. The protocol treats them as seats, not processes.

**Q3. Copilot.** Wait for a verified session-start + deny before calling P5 done for that
harness, or ship inbox-file-only and mark Copilot `observed-only`? Recommendation: **ship
inbox-file-only, name it, do not wait.** Waiting recreates "F1 stays open" indefinitely.

**Q4. Should `coord bus serve` auto-start from SessionStart?** Recommendation: **no.** Auto-start
reintroduces "a helper I did not ask for is holding a port / a process." The first Leader
claim may start it in-process; otherwise the operator does. Measure how often P5's direct-mesh
is enough before adding a supervisor.

**Q5. Progress-φ default threshold.** Start from Magentic-One's "stall count > 2" translated
to phi, or start with a human-visible `coord stall` and no automatic kick until we have a
baseline? Recommendation: **P5 is notify-only. P6's automatic kick is off until
`kick_ack_rate` has a denominator** (R4). The ladder exists; the trigger is measured.

**Q6. Does a kick inject into the *current* turn, or only the next tool boundary?** Injecting
mid-turn is the only way to stop a runaway Worker, and it is also how you scramble a
half-finished edit. Recommendation: **next tool boundary + mailbox. Mid-turn abort is Owner
only, and it is a harness capability we do not have uniformly.** Name it as residual.

---

## 15. References

Lab and protocol:

- J. Hadfield, B. Zhang, K. Lien, F. Scholz, J. Fox, D. Ford, "How we built our multi-agent
  research system," Anthropic Engineering, 2025-06-13.
  https://www.anthropic.com/engineering/built-multi-agent-research-system
- A. Fourney et al., "Magentic-One: A Generalist Multi-Agent System for Solving Complex
  Tasks," Microsoft Research, 2024-11.
  https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/
- Magentic-UI: Towards Human-in-the-loop Agentic Systems, arXiv:2507.22358, 2025-07.
- Google / Linux Foundation, Agent2Agent protocol v1.0 (stable 2026-03); donated Jun 2025.
  https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-the-a2a.html
- Zed Industries, Agent Client Protocol. https://agentclientprotocol.com
- Cisco Outshift / Linux Foundation, AGNTCY ("Internet of Agents"), donated Jul 2025.
- G. Chang et al., "Agent Network Protocol Technical White Paper," arXiv:2508.00007, 2025-07.

Agent-native repos and coordination:

- N. Sobo, "Replace PRs with Delta – Now in Public Beta," Zed Blog, 2026-09-16.
  https://zed.dev/blog/delta-public-beta
- S. Pugachev, "CodeCRDT: Observation-Driven Coordination for Multi-Agent LLM Code
  Generation," arXiv:2510.18893, 2025-10.
- D. Lee, "AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared Workspace,"
  arXiv:2608.23740, 2026-08.
- S. Chacon, "Agentic Version Control Benchmarks," GitButler, 2026-07. https://vcbench.dev
- Jujutsu (jj) v0.45.1, 2026-09. https://jj-vcs.github.io/jj/

P2P and distributed systems:

- Sun Microsystems, JXTA protocols: Peer Discovery, Resolver, Pipe Binding, Rendezvous,
  Peer Information, Endpoint. 2001.
- Napster (central directory + P2P transfer); Gnutella 0.4 flood / 0.6 ultrapeers;
  BitTorrent (tracker, rare-first, tit-for-tat, optimistic unchoke).
- M. Burrows, "The Chubby lock service for loosely-coupled distributed systems," Google, 2006.
- N. Hayashibara et al., "The φ Accrual Failure Detector," 2004.
- Das, Gupta, Motivala, "SWIM: Scalable Weakly-consistent Infection-style Process Group
  Membership Protocol," 2002.

This repo (read, not recalled):

- `docs/specs/agent-coordination.md` (M1–M4, non-goals, ubiquitous language)
- `docs/architecture-agent-coordination.md` (ADR-0007 shape, delays, council gate)
- `docs/adr/0007-coordination-substrate.md`, `0005`, `0008`, `0009`, `0010`, `0011`
- `docs/design/coord-core-phase1.md`, `coord-enforcement-phase2.md`,
  `coord-federation-phase3.md`, `coord-collaboration-phase4.md`
- `pack/templates/session-contract.template.md`
- `pack/adapters/hooks/session-start.py`, `reread-guard.py`

---

## Status

| | |
|---|---|
| **Completed** | Research across lab multi-agent systems, agent-native repos, and classic P2P; diagnosis of M5–M9 against the existing M1–M4 layer; a two-plane architecture that keeps ADR-0007; roles, leader lease, kick ladder, message vocabulary, transport, phasing, and twelve key decisions. |
| **Remaining** | Maintainer answers on Q1–Q6. Then `/specify` (acceptance criteria for P5) and `/design-slice` for P5 only — not a redesign of coord core. |
| **Best next action** | Decide Q1 (peer-group grain), Q3 (Copilot floor), and Q5 (automatic kick off until measured). P5 can start without Q2/Q4/Q6. |
