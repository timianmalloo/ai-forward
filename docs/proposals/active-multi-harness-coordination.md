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
  The pack's coordination layer is a git-tracked ledger. AI-DE already built the live surfaces
  (Loomkeeper board, standing files, MCP board tools, AgentPlane) and still measured collaboration
  as empty, because every path is a pull the agent may ignore. This proposal ships all three
  planes: git-tracked ledger (required), local loopback-HTTP bus (fail-open), cloud relay
  (fail-open, same client). Scores stay a pull; blocked/kick/delegate are a push. Unix sockets
  are not the local transport — HTTP on 127.0.0.1 is, so Mac and Windows share one
  implementation. GitHub remains defense in depth.
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
| **Grounding** | `spec-agent-coordination`, `architecture-agent-coordination`, ADR-0007 / 0008 / 0009 / 0010 / 0011, Phases 1–4 designs; **and** the live AI-DE experiment (`session-contracts`, Loomkeeper, AgentPlane, `note-20260902-collaboration-not-happening`, Addenda C/D profile) plus the research cited in §15 |
| **Harnesses in scope** | GitHub Copilot (GPT-*), Grok Build, Claude Code, Antigravity — same repo, same worktrees, different runtimes |
| **Two examples** | **ai-forward** is the pack (ledger, hooks, worktrees). **ai-de** is the product that tried to make that live across harnesses, and has the session history. |

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

> **Keep the ledger as the source of truth. Ship a local loopback-HTTP bus and a cloud relay
> on the same message vocabulary. Dual-write every coordination act to the ledger so
> accountability survives either plane going down. Elect a Leader among sessions so someone
> is on the hook for the whole work list. Inside a session, name Owner / Conductor / Worker
> so the most capable model decides and the right-sized model executes.**

If the bus or the relay is down, the existing layer still works — slower, the way it works
today. That is NFR-P2: fail-open at runtime, not fail-absent at delivery. All three planes
ship.

**GitHub is defense in depth, not the live path.** Decouple *liveness* from `git push` /
`git fetch`. Do not decouple *accountability* from git. The cloud relay is the live path
when sessions do not share a machine. Every state-changing message is still dual-written to
the JSONL that gets pushed, so a clone tomorrow, a PR review, and a relay outage all see
the same kicks. That is Napster's transfer path with BitTorrent's "the file survives the
tracker." GitHub Issues, PRs, and Actions stay. The relay is not a second GitHub.

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

### 1.4 The two examples are not two copies of one thing

| | **ai-forward** (the pack) | **ai-de** (the live experiment) |
|---|---|---|
| Job | Ship a repo-droppable coordination *library*: record, fold, hooks, worktrees, session-contract template | Run several harnesses on one product, watch them, score them, and (the unsolved part) make them actually collaborate |
| What exists | Phases 1–4 of coord-core. Claims, refusals, allocator, derived merge, collaboration check. Passive by design (ADR-0007: no daemon) | Loomkeeper Observatory (Sessions, Board, Ledger, Leaderboard). AgentPlane (ACP-spawned `claude-code` lane, Phase 1 scored Partial 15/15). MCP tools `aide_whoami` / `aide_board_read` / `aide_board_post`. Injected coordination contract (`board.json`, `standing/<session>.json`). Two-session contract: **Core = Claude Code**, **Design = Copilot** |
| Session history | Pack dogfood | Addenda C/D: conductor `claude:919ba21f`, **56 h wall**, **52 writing nodes**, **114 persona reviews**, **166 sub-agents**, **40 Copilot `atlas/*` worktrees** beside it, **649 claims**, **31 `COORD-REFUSED`**. Est. list-price **$2,198**. Profiled in `docs/profiles/addendum-cd.md` |

The pack answered *"may I touch this file?"* AI-DE tried to answer *"are we collaborating?"* and
the measured answer, on 2026-09-02, was **no**.

### 1.5 What ai-de measured — the bus was built as a pull, so it never fired

These are not hypotheticals. They are named notes, named defects, and a session profile.

**Collaboration surfaces rendered; nothing wrote them.**
`note-20260902-collaboration-not-happening`: three live agents (Copilot, Claude Code, a pwsh
terminal) all launched in **the same worktree** (`TheTerrace/docs/fix-broken-design-links`). The
user asked Copilot to *"send a message to the loomkeeper board to let the other agents know you
are here."* Copilot grepped, found `coord-core.py`, found no board command. The Board pane said
*"No board posts yet."* The Ledger was empty. Harness identity and Verified trust had landed;
collaboration had not.

The code comment that followed is the diagnosis in one paragraph
(`IngestHost.PostToBoard`):

> `MessageBoardService` had **no callers anywhere in the product**. It was implemented, tested
> and rendered as a pane, and nothing could write to it — a read surface over an empty store.

That is CTX-H in the product: a control that ships uninstalled. The MCP slice
(`design-mcp-enlightened-path`) then added `aide_board_read` / `aide_board_post` as a
*translation* of the JSONL contract, not a second API. Two registered, trust-Verified agents
were asked whether they knew Loomkeeper. **Both said no.** One had grepped `.claude/`,
`.github/`, `docs/` first — *"no tool, no config, no endpoint."*

**Standing — the kick — was also built as a pull, on purpose.**
`StandingPublisher` writes `$AIDE_CONTRACT_LOG/standing/<session>.json`. The remarks are load-bearing:

> It is still a pull. Nothing is injected into the agent's context — the file sits there and
> the agent chooses to read it. That distinction is what ADR-0019's anti-Goodhart section
> turns on.

A C1 standing *tool* was added to `McpToolGateway` — correct, tested, **unreachable**: the
gateway had no caller and no transport (ADR-0004: the MCP transport was spiked and never
built). Adding a tool nothing can call does not deliver a story about receiving.

`plan-daydream-and-collaboration-slices` measured the same shape on 2026-09-02: Message Board
*writer added today, unverified in a running build*; `StandingComposer` — **zero production
callers**; FleetAggregator — **zero production callers**.

**Sessions register, they do not enlist.**
`note-20260902-session-enlistment-telemetry-gap`: live Claude Code and Copilot rows read
`Not Recorded · trust Asserted · 0 span(s) · Ended/Stale`. The App identity wiring was
correct. Heartbeats, model identity, spans, and Asserted→Verified evidence were not arriving.
Liveness is `UpsertHeartbeat`. No heartbeat, no Alive.

**The stall the kick ladder exists for, timed.**
Addenda C/D profile (`docs/profiles/addendum-cd.md`), conductor `claude:919ba21f`:

| Event | Number | Mode |
|---|---|---|
| `EnterWorktree` refused (cwd was the repo root) on SH-4.1 | **8,143 s = 2 h 15 min** blocked | M5 |
| S2 `/specify` answered 18 h later, 20 s of work | store span 65,516 s vs audit 4,992 s | M5 |
| Joins + gates as share of the conductor's *active* time | **44.8%** (13,451 s of 8.3 h) | serial spine, not protocol |
| Time spent in the coordination layer itself | **0.7%** (217 s) | the ledger was on; the bus was not |
| Claims in the window | 649; 31 `COORD-REFUSED` | M1/M2 layer *was* used |
| Peer Copilot fleet | 40 `atlas/*` worktrees beside the conductor | M9: they were *there* |
| Mean live width vs cap of 3 | **1.9** (width 4 for 0.8% of live time) | GO6 held in practice |
| Two Owner ids for one conductor | `claude-conductor-addendum-c` (20) and `conductor-addendum-c` (8) | identity asserted, not unified |

The 2 h 15 min `EnterWorktree` wait is the kick ladder's rung 0–2, unbuilt. Nothing told the
conductor the node was stuck on a worktree rule it already owns. The node sat. The operator
was the detector.

**The session contract worked as a document, and failed as a channel.**
`docs/collaboration/session-contracts.md` is the richest in-session hierarchy this fleet has:
Core (Claude Code) owns extractors/store/view-models; Design (Copilot) owns pixels. The seam
is one sentence. Open requests are a table in the markdown. Four rebases, four conflicts,
**always the same two files** (`docs/audit/*.jsonl` and derived views) — ADR-0009's exact
prediction. Both sessions once edited `IpcServer.cs` / `CanvasGraphViewModel.cs` in the same
window and converged; the lesson written down was "a claim + a glance at §4." That is
announce-before-act, still pull.

**Vocabulary collision, named so the rest of this document cannot smuggle it.**

| Word | In this proposal | In AI-DE today |
|---|---|---|
| **Owner** | The most capable *model* in a session; reduces human paging within a written mandate | The *human* who signs execution graphs (Owner sign-off, 2026-09-09, five binding conditions) |
| **Conductor** | A highly capable *model* that decomposes, delegates, joins, and may be elected Leader | **AgentPlane**: a product that *spawns* an ACP-speaking engine into a provisioned worktree, holds the protocol session, enforces spend/lease, and closes an episode into Loomkeeper. Phase 1 is one governed `claude-code` run. Phase 2 (plan/review/dispatch *multiple* lanes) is explicitly not claimed |
| **Leader** | Elected among sessions, holds the work list, kicks | Not a role. The Observatory is a *view* |
| **Board** | The bus's public pipe | Loomkeeper Message Board (US-4). Built. Empty when agents don't pull |
| **Standing** | Kick / next-turn feedback | US-16 file. Built as pull, to avoid Goodhart |

The proposal does **not** rename AI-DE's Conductor. AgentPlane stays the spawn/govern path for
engines the workbench itself launched. Independently launched harness sessions (the Copilot
atlas fleet, a Grok Build session, a Claude Code the operator started in a terminal) still
need the bus, because AgentPlane never spawned them. The two compose: AgentPlane *is* a
session that can hold the Leader lease; the bus is how everyone else hears it.

### 1.6 The load-bearing split: inject coordination, never inject scores

AI-DE chose pull for standing *for a real reason* (ADR-0019 anti-Goodhart: an agent shown its
rank every turn is a different system). That reason does not apply to `blocked`, `kick`, or
`delegate`. Those are facts about *other agents' work*, not a score of this one.

| Payload | Channel | Why |
|---|---|---|
| Rank, trend, qualitative standing | **Pull** (standing file / `aide_standing`). Agent asks. | Goodhart. US-16 stays a pull. |
| `blocked` / `kick` / `delegate` / `unblocked` | **Push** into the next tool boundary (`additionalContext`) *and* the mailbox/board | If the agent does not ask, work stops. That is the 8,143 s wait. |
| Board posts (`question`, `decision`, `breadcrumb`) | Dual: MCP write (already designed) + hook inject of *"N new board posts"* count, not the prose | Agents treat every board message as untrusted data (`AgentProtocolDocument`). Inject the *existence*, not the instruction-shaped body. |
| Heartbeat / liveness | Bus + Loomkeeper `UpsertHeartbeat` | Sessions that do not heartbeat read Ended. That is the enlistment gap. |

P5 in this proposal is therefore **not a new product**. It is: (1) per-session worktree on
launch (the app still does not call `coord worktree new`); (2) a push of coordination
messages onto the next tool boundary; (3) dual-write into the Loomkeeper store the panes
already read, so the Board stops lying about emptiness; (4) keep standing as a pull.

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
wire format. Local v1 is the §7 JSON over loopback HTTP; the *schema* of a Session Card
should be A2A-shaped so the adapter is a rename, not a redesign.

Anthropic's own caution, which the pack already believes: **most coding tasks have fewer truly
parallelizable pieces than research, and models are not yet great at coordinating in real
time.** Parallelism is a cost multiplier (GO6). The bus exists so the parallel work we *do*
choose is not left to rot when one participant blocks. The same post records that **subagent
waves still run synchronously** — the lead waits for each set. Asynchronous subagents are
named as future work, not a shipped control plane. That is M5/M6 at the lab that invented
the pattern.

**Two topologies, not one, and we already picked.** AutoGen AgentChat ships three:
SelectorGroupChat (central next-speaker), Swarm (`HandoffMessage`, no central orchestrator —
the specialist *becomes* the active agent), and MagenticOneGroupChat (the stall-counter
Orchestrator). OpenAI's Agents SDK makes the same fork first-class: manager retains control
and calls specialists as tools, or a handoff makes the specialist the active agent. AI-DE's
AgentPlane is the manager-retains-control shape (it *spawns* a lane and holds the protocol
session). Independently launched Copilot/Grok/Claude sessions are the Swarm shape — nobody
spawned them, so they can only *handoff* and *notify*. The elected Leader is how a Swarm
grows a Magentic-One inner loop without requiring every participant to have been spawned by
AgentPlane.

**A2A is not a P2P control plane.** v1.0 is client–server: Agent Card at
`/.well-known/agent-card.json`, server-owned Tasks, client may block, poll `GetTask`,
subscribe via SSE, or register a webhook. Push is **optional, capability-gated,
server-initiated, and one-way.** ANP is the closer cousin to what this proposal wants:
federated DID-addressed JSON-RPC, and Profile P3 *requires* the peer-initiated notification
`direct.incoming` after ingress accepts `direct.send` — success of send is acceptance, not
completion. AGNTCY's invocation ACP (OpenAPI 0.2.3) was **archived 2026-04-11**; SLIM is a
separate overlay with named nodes, not direct agent-to-agent sockets. Session Cards stay
A2A-shaped for later; the v1 *behaviour* (mandatory notify on blocked/kick) is the ANP
lesson, not the A2A one.

**The distributed-systems theorem behind Q7.** Raft's leader *pushes* empty AppendEntries as
heartbeats; a follower starts an election only after a timeout with no such RPC — it does
not poll the leader for status. Chubby's client API was built around event notification and
KeepAlive-piggybacked invalidations *specifically so clients need not poll files*. SWIM
replaces all-to-all heartbeats with randomized ping plus indirect probes. Gossipsub replaced
floodsub because unbounded flooding does not scale. CRDTs (Automerge) are not an active
coordination protocol: they converge only after the same updates have eventually synced.
The 8,143 s wait is what you get when the control plane is a file the agent may choose not
to read. Push is not a taste. It is how every lease service that survived was built.

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
│  RELAY  (ships; fail-open; HTTPS)                               │
│  presence · board · kick/delegate fan-out · SSE/webhook push    │
│  never grants leases · never the only copy                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  BUS  (ships; fail-open)                                        │
│  HTTP 127.0.0.1 + token · inbox file · Loomkeeper when AI-DE    │
│  same §7 kinds as the relay                                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ dual-write (always)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEDGER  (required)  +  GitHub (defense in depth)               │
│  .agents/log/<session>.jsonl  fold → leases, work items,        │
│  decisions, blocked-on, leader lease, kick history              │
│  cloneable, reviewable, survives the relay                      │
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
| Rendezvous | Local: `coord bus serve` on `127.0.0.1`. Remote: the cloud relay. Same §7 kinds. | Runtime; membership is a fold of the ledger. The relay is a cache of that fold, not a second membership. |
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
  "listen": "http://127.0.0.1:<port>/",
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
3. P5–P7 are **loopback HTTP** on `127.0.0.1`, token-gated. Not Unix sockets (see §8.1).
4. The **relay (P8)** is the same vocabulary on HTTPS. It requires signed Session Cards (A2A v1.0). Unsigned
   loopback identity (ADR-0011, asserted) must not be accepted on the wire. A GitHub token
   may authenticate the *operator* to the relay; it is not the session's identity.
5. Identity remains asserted on loopback (ADR-0011). A session that sets `AGENT_SESSION` to
   another's can already release leases; the local bus does not make that worse, and the
   record still shows who wrote what. The relay is the first place impersonation is worth
   preventing rather than detecting.

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
   **This is the push.** Reserved for `blocked` / `kick` / `delegate` / `unblocked` and for a
   *count* of new board posts — never for standing, rank, or board prose (see §1.6).
2. **Mailbox file** `.agents/bus/inbox/<session>.jsonl`, and when AI-DE is the host, the
   Loomkeeper board + `$AIDE_CONTRACT_LOG/standing/<session>.json` that already exist. Works
   even when hooks cannot inject. Runtime, gitignored, rebuilt from the ledger on demand.
3. **Operator page.** For the human at rung 4. In AI-DE this is the Observatory Board/Ledger
   that already renders honestly when data exists.

None of these is a daemon the agent must start. (1) piggy-backs on the edit path. (2) is a
file AI-DE already writes. (3) is the existing operator view with a badge.

**Do not grow a second board.** Loomkeeper's Message Board is the bus's public pipe when the
watcher is present; `coord-core` is the ledger everywhere. AI-DE already ruled this:
pack sessions coordinate through `coord-core`; non-pack sessions get the injected contract;
one ledger, projected, not duplicated (`architecture-loomkeeper` §6). A bus that wrote a
third store would be DM6.

---

## 8. Transport — all three planes, one vocabulary

**All three planes ship.** Ledger, local bus, cloud relay. Fail-open at runtime (a down bus or
a down relay never refuses an edit). Not fail-absent at delivery: P5 builds the local bus, P8
builds the relay, both are in the programme, neither is "maybe later."

The message kinds in §7 are the protocol. The plane is just where a copy travels.

### 8.1 Local bus — not Unix sockets

Unix domain sockets are the wrong default for a bus that has to work on a Mac *and* a PC.

| Candidate | macOS | Windows | One stdlib implementation? | Same client as the relay? |
|---|---|---|---|---|
| **Unix domain sockets** | Native, first-class | `AF_UNIX` exists since Windows 10 1803, pathname-only, leftover socket files, historically buggy in runtimes. A second implementation, not a port. | No | No |
| **Named pipes** | POSIX FIFOs are *not* Windows named pipes (no multiplex, different blocking, no ACL-equivalent) | Native `\\.\pipe\…` | No | No |
| **.NET `NamedPipeServerStream`** | Implemented *with* UDS on Unix | Native | Pack core is Python, not .NET. AI-DE can host; harnesses still have to speak it. | No |
| **HTTP on `127.0.0.1`** | Identical | Identical | Yes — Python `http.client` / `http.server`; .NET `HttpListener` / `HttpClient` | **Yes.** Same §7 JSON, `http://127.0.0.1` vs `https://relay`. |

**Chosen: loopback HTTP + SSE, bound to `127.0.0.1` only.**

- Bind **`127.0.0.1`, not `0.0.0.0`, not `localhost`.** `localhost` can resolve to `::1` first
  and miss; `0.0.0.0` trips the Windows firewall and is reachable off-box.
- Port **0** (OS assigns), then write `.agents/bus/listen.json` `{host, port, pid, token_path}`.
  No hashed-port scheme; collisions are not a coordination problem we need.
- A per-repo **token file** (mode `0600` on POSIX; the equivalent user ACL on Windows). Any
  local account can hit `127.0.0.1`; the token is the filesystem permission UDS would have
  given us. First request without it is 401, not a hang.
- SSE (or a long-poll) for push onto the next tool boundary. POST for `hello` / `progress` /
  `blocked` / `kick` / `delegate`. This is A2A's webhook/SSE shape, used locally, so P8 is
  a URL change plus signatures, not a second client.
- If nothing is listening, senders write the ledger and the inbox file only. NFR-P2 kept.

MCP, A2A, and Copilot's cloud path already speak HTTP. A UDS-only bus would be a fourth
wire that only POSIX harnesses could use, which is how Copilot becomes `unsupported` by
accident.

Unix sockets remain a permitted *optimisation* behind the same HTTP vocabulary (a reverse
proxy onto a UDS on macOS) if a spike ever shows loopback HTTP is the latency problem.
They are not the contract.

Solution-Selection Ladder:

| Rung | Decision |
|---|---|
| 1 YAGNI | All three planes earn their place. A Raft cluster does not. A second local protocol (UDS + named pipes) does not. |
| 2 Reuse | SessionStart hook, `coord-core` fold, the allocator, `scrub.py`, the §7 JSON. The relay reuses the local bus's client. |
| 3 stdlib | `http.client` / `http.server`, `json`, `os`, `secrets`. No Redis, NATS, libp2p, MQTT. |
| 4 native | Loopback TCP, which both kernels already are. |
| 5+ | Not reached. |

**Discovery, Napster-as-bootstrap:**

1. On SessionStart, write the Session Card to the ledger and to `.agents/bus/peers/<session>.json`.
2. If `.agents/bus/listen.json` exists and the pid is alive, POST `hello` to that port with the
   token. If it does not, the first session that wants to be Leader may start
   `coord bus serve` (binds `127.0.0.1:0`, writes `listen.json`). If nobody does, senders
   write the ledger and the inbox file only.
3. Git remains the discovery path across machines and after a reboot: fetch, fold, see cards.
   The relay (below) is the live path across machines *without* waiting for that fetch.

### 8.2 The cloud relay — the third plane, same vocabulary

The local bus does not reach a Copilot cloud agent, a session on another laptop, or a worker
the workbench spawned into a VM. GitHub fetch reaches them, and it is too slow — that is M6.
That is why the relay is a plane, not a future spike.

The relay is **rendezvous + message board + push**, hosted. Same §7 kinds as the local bus.
It is not a lease server, not a merge queue, and not a replacement for Issues/PRs/Actions.

| It does | It does not |
|---|---|
| Accept a signed Session Card and keep presence | Grant or refuse a path lease (the ledger still does) |
| Fan out `blocked` / `kick` / `delegate` / `unblocked` (SSE or webhook — A2A's optional push, made mandatory for these kinds, ANP P3's lesson) | Be the only copy of any of those messages |
| Hold a short window of board posts for sessions that missed them | Persist the work list as a second source of truth |
| Authenticate the operator (GitHub as one IdP is fine) | Treat a GitHub token as a session identity |

**Defense in depth, the rule that makes this not Napster:**

1. Every state-changing message is written to the session JSONL **before or atomically with**
   the relay POST. If the relay ACK is lost, the ledger still has it.
2. A clone with no relay config is a complete, slower system. `coord doctor` reports
   `relay: off`.
3. If the relay and the fold disagree, **the fold wins.** The relay is a cache. A repair is
   "replay the fold to the relay," never the other way.
4. GitHub remains the remote the JSONL is pushed to. A PR still shows who kicked whom. A
   relay outage is an inconvenience; a GitHub-shaped history is the recovery.

That is why we do not put the work list only in the cloud, and why we do not stop pushing.
Zed can turn off PRs on Delta's own repo. We keep GitHub as the depth layer even if every
live notify goes through the relay.

**Sequencing, not optionality.** P5 proves the vocabulary on one machine (loopback HTTP +
inbox + Loomkeeper). P8 is the same client pointed at `https://`, plus signed cards. Both
are in the programme. A repo may run with the relay off (`coord doctor` reports `relay: off`);
that is fail-open, not "we did not build it."

**Shape.** Small HTTPS service: POST event, GET/SSE board, webhook register. The local bus
is the same three verbs on `127.0.0.1`. Stdlib client. Signed Session Cards on the wire.
Hosting (Azure, Fly, a box) is an operations choice, not an architecture one. Do not take
NATS/libp2p as a
build dependency; the relay *is* the rendezvous.

---

## 9. Cross-harness reality

The pack already installs four surfaces. The bus must not grow a fifth core.

| Harness | Edit enforcement today | SessionStart today | Bus adapter |
|---|---|---|---|
| Claude Code | PreToolUse deny (executed) | `session-start.py --host claude` | Inject via `additionalContext`; HTTP client to `listen.json` |
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
| B12 | Relay unreachable | **Degrade.** Local bus + ledger + git push. Same as B1. Never refuse an edit. |
| B13 | Relay is the only copy of a kick | **Prevent.** Dual-write is the invariant. A relay POST without a ledger append is a defect, tested red-first. |
| B14 | Unsigned card accepted on the relay | **Prevent.** Loopback identity is asserted; the wire requires a signature. Unsigned → 401, and the event is not fanned out. |

---

## 11. Explicit non-goals

Each with the reason, so this proposal cannot be read as a licence to build them.

- **Replacing GitHub Issues, PRs, or Actions.** Zed is doing that experiment, and even they
  keep GitHub for the public `zed` repo. Our backlog and merge queue stay. The bus is
  in-flight. GitHub remains the durable remote for the ledger even if live notify moves to
  the relay. The spec already said this.
- **Replacing git with DeltaDB, Pijul, or a source CRDT.** Complementary. Out of this change.
- **A *required* daemon or hosted broker.** Retracts ADR-0007 and NFR-P2. An *optional* cloud
  relay is in scope at P8, fail-open, never the only copy. A repo that never configures it
  is a complete system.
- **Implementing A2A, AGNTCY, ANP, or libp2p in v1 (P5–P7).** Speak their *shape* (Session
  Card ≈ Agent Card). The relay at P8 may speak A2A webhooks / SSE; it still must not become
  a second grantor of leases.
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

This is the close of the loop AI-DE already half-built. Not a new product.

- Session Card at SessionStart, written to the ledger and to `peers/`.
- Inbox file + `coord mailbox`. When AI-DE is the host: the same line
  `aide_board_post` already appends, so the Observatory Board pane stops reading empty.
- `hello` / `progress` / `blocked` as ledger events, with loopback HTTP if `listen.json`
  is live.
- **Push** of `blocked` onto the next tool boundary. Standing stays a pull.
- Per-session worktree on "New <agent> session" (`coord worktree new`) — the gap
  `collaboration-not-happening` named, still open at launch.
- Heartbeat → Loomkeeper `UpsertHeartbeat` so a live agent reads Alive.
- `coord doctor` grows `bus: off | advisory | live` and **asserts the corpus size** (R4).
- **Demo, in ai-de, not a toy repo:** two harnesses (Claude Code + Copilot). A posts to the
  board; B sees it on the next tool call *without* being asked to grep. A second demo: launch
  two agent sessions; they land in distinct worktrees.
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

### P8 — The relay, same client, signed cards

- Session Card schema frozen as a subset of A2A Agent Card, **signed**.
- Cloud relay: presence, board window, fan-out of `blocked`/`kick`/`delegate`. Same three
  verbs as P5, on `https://`. Dual-write invariant tested red-first (B13). Fold wins.
- Copilot session-start spike, or an honest `unsupported` forever.
- **Not a promise to implement the full A2A stack.** A promise that the card and the
  notify kinds will not have to be redesigned, and that GitHub still has every kick.

A repo may run with `coord bus` down and the relay unconfigured — fail-open, inbox-only.
That is a runtime degradation, not a delivery skip. All three planes are in the programme.

---

The local HTTP bus is P5's walking skeleton. The relay is P8 on the same client. GitHub
is the depth layer from day one (the JSONL is already pushed).

---

## 13. Key decisions

| # | Decision | Why |
|---|---|---|
| D1 | All three planes ship. Ledger required at runtime; local bus and relay fail-open | NFR-P2 is fail-open, not fail-absent. The relay is rendezvous for hosts that do not share a filesystem, not a second grantor. |
| D2 | Dual-write every state-changing message | Accountability is the ledger's job. A bus that is the only copy of a kick is Napster's directory. |
| D3 | Leader is a lease with a sequencer, not a designated process | Chubby. Sessions die. The fold outlives them. |
| D4 | Kick ladder, not immediate reassign | Magentic-One stall-count; phi-accrual; optimistic unchoke. False eviction is worse than a slow session. |
| D5 | Owner / Conductor / Worker as seats in the session contract | Anthropic + Magentic-One, made a mechanism. Capability is configured, not inferred from a model string at runtime. |
| D6 | Delegate with four required fields; artifacts not prose | Anthropic's duplication failure and telephone failure, both measured. |
| D7 | Loopback HTTP on `127.0.0.1` + token file + inbox; not Unix sockets | One stdlib implementation on Mac and Windows. Same client as the HTTPS relay. UDS is a POSIX-only second code path, which is how Copilot becomes `unsupported` by accident. |
| D8 | Session Card shaped like an A2A Agent Card | Do not invent a fourth agent identity format. Do not take the A2A dependency in v1. |
| D9 | Do not CRDT the source tree | CodeCRDT: coupled tasks get slower; semantic conflicts remain. We already have artifact class. |
| D10 | Do not replace GitHub; use it as defense in depth | Decouple liveness from fetch/push. Never decouple accountability from the git-tracked JSONL. A clone without the relay is complete, slower. |
| D11 | Never advertise an unexecuted harness mode | Phase-3 conformance, applied to Copilot live-inject. |
| D12 | Leader advises; ledger grants | Existing council ruling, kept. |
| D13 | Inject coordination messages; never inject scores | AI-DE chose pull for standing (ADR-0019 anti-Goodhart) and was right. That reason does not apply to `blocked` / `kick` / `delegate`. The 8,143 s wait is what pull-only costs. |
| D14 | Do not grow a third *source of truth* | Loomkeeper Board and the cloud relay are projections of the ledger. `coord-core` remains the grantor. One ledger, two caches. |

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

**Q7. Push vs pull — does §1.6 hold?** AI-DE's `StandingPublisher` deliberately does not inject,
because of ADR-0019 anti-Goodhart. This proposal injects *coordination* messages and keeps
standing as a pull. If the maintainer wants *no* injection of any kind, P5 degrades to "make
the pull unmissable" (SessionStart + Stop hooks force a mailbox/board read; a session that
never reads is `NOT CHECKED` for collaboration, not "all quiet"). That still would not have
unblocked the 8,143 s `EnterWorktree` wait — only a push, or a conductor that watches
progress-φ, would. Recommendation: **keep the split.**

**Q8. Hosting for the relay?** Architecture is HTTPS + signed cards + dual-write. Hosting
(Azure vs Fly vs a box) is operations. Recommendation: pick later; do not let the host choose
the protocol. The local bus is HTTP on `127.0.0.1` so the client does not care.

**Q9. (closed) Unix sockets vs loopback HTTP.** Closed: HTTP on `127.0.0.1`. See §8.1 and D7.

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
  https://a2a-protocol.org/latest/specification/
- Microsoft AutoGen v0.4 Core / AgentChat (SelectorGroupChat, Swarm, MagenticOneGroupChat).
  https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html
- OpenAI Agents SDK — orchestration and handoffs.
  https://openai.github.io/openai-agents-python/agents/
- Zed Industries, Agent Client Protocol. https://agentclientprotocol.com
- Cisco Outshift / Linux Foundation, AGNTCY ("Internet of Agents"), donated Jul 2025.
  ACP invocation spec archived 2026-04-11; SLIM remains a transport overlay.
- ANP 1.1 — did:wba, ADSP, Profile P3 `direct.incoming` (mandatory peer-initiated notify).
  https://github.com/agent-network-protocol/AgentNetworkProtocol
- G. Chang et al., "Agent Network Protocol Technical White Paper," arXiv:2508.00007, 2025-07.
- D. Ongaro, J. Ousterhout, "In Search of an Understandable Consensus Algorithm (Raft)."

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

The live experiment, **ai-de** (read, not recalled):

- `docs/collaboration/session-contracts.md` — Core (Claude Code) / Design (Copilot) seam
- `docs/notes/collaboration-not-happening.md` — three agents, one worktree, empty board
- `docs/notes/session-enlistment-telemetry-gap.md` — register ≠ enlist
- `docs/architecture/loomkeeper.md`, `docs/architecture/agent-plane.md`
- `docs/specs/agentic-watcher-substrate.md` US-4 / US-8 / US-16
- `docs/design/mcp-enlightened-path.md` — MCP as translation of the JSONL contract
- `docs/plans/daydream-and-collaboration-slices.md` — StandingComposer zero callers
- `docs/plans/conductor-programme.md` — Phase 1 width 1; Phase 2 multi-lane not claimed
- `docs/profiles/addendum-cd.md` — 8,143 s EnterWorktree stall; 44.8% joins/gates; 0.7% coord
- `src/AiDe.Core/Watcher/IngestHost.cs` (`PostToBoard` remarks), `StandingPublisher.cs`,
  `AgentProtocolDocument.cs`
- `docs/knowledge/multi-agent-coordination/` — Kleppmann fencing, Cognition, MAST, METR

---

## Status

| | |
|---|---|
| **Completed** | Research across lab multi-agent systems, agent-native repos, and classic P2P; diagnosis of M5–M9 against the pack's M1–M4 layer **and** against AI-DE's measured empty board, enlistment gap, and 8,143 s stall; a two-plane architecture that keeps ADR-0007; inject-coordination / pull-scores split; roles, leader lease, kick ladder, message vocabulary, transport, phasing, twelve key decisions, Q7. |
| **Remaining** | Maintainer answers on Q1–Q7. Then `/specify` (acceptance criteria for P5) against *ai-de*, not a toy repo. |
| **Best next action** | Decide Q7 (push vs pull) and Q1 (peer-group grain). P5's first demo is: Copilot posts, Claude sees it on the next tool call over loopback HTTP, two launches get two worktrees. P8 is the same demo pointed at the relay. |
