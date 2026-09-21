---
id: architecture-multi-harness-coordination
title: "AI-Forward - multi-harness coordination evolution"
type: architecture
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, multi-harness, multi-agent, worktrees, launch, runtime, qualification]
links:
  - { to: architecture-agent-coordination, rel: refines }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: documents }
  - { to: spec-agent-coordination, rel: documents }
  - { to: spec-multi-harness-launch-and-monitor, rel: documents }
  - { to: design-multi-harness-runner, rel: documents }
  - { to: proof-coordination-runtime-v2, rel: documents }
  - { to: coordination-end-to-end, rel: documents }
  - { to: note-20260919-coordination-decisions-ratified, rel: relates-to }
review-by: "2027-03-21"
summary: >-
  The deep architecture and history of AI-Forward's multi-agent, multi-harness coordination:
  why shared checkouts and prompt-only relays failed, how worktree isolation and the Owner /
  Coordinator / Sub-Agent doctrine replaced them, what execute-with-coordination grew into,
  what the bounded runtime actually ships, what was deliberately not shipped, and which
  qualifications remain profile-specific.
---

# Multi-harness coordination evolution

This is the deep narrative for the coordination surface the pack now ships. It is not a generic
survey of agent swarms. It is the repo's own history, traced to the proposal/spec/design/proof
stack and to the landed skills and scripts.

**Confidence note**

- **Verified** - proposals, specs, designs, proof packs, API docs, and the git history in this
  repository; every shipped claim below is backed by a committed artifact in this tree.
- **Flagged** - profile-scoped residual limits that the landed proofs still leave open
  (for example full Windows Codex write-hook trust, Copilot arbitrary terminal attach,
  Copilot `additional_roots`, and arbitrary Claude/Agy live-terminal attachment).

## 1. Where it started

The starting point was not "multi-harness orchestration". It was a collection of failure modes
observed in real work:

| Starting shape | Why it failed | Source |
|---|---|---|
| Shared checkout, several sessions | One session's checkout/add/commit could move or sweep another session's work. That is work loss, not a merge conflict. | `spec-agent-coordination.md`, `session-worktree-discipline.md` |
| Prompt-only coordination | A plan described in prose did not fail when ignored. The pack's own doctrine phrases it exactly: a rule that ships only as prose is a memoir. | `spec-agent-coordination.md`, `note-20260919-coordination-decisions-ratified.md` |
| One ledger for everything | A union-merged ledger can record claims and mail, but it cannot elect a leader or fence a join. Two competing leader claims both survive a union merge. | `kb-multi-agent-coordination/index.md`, `architecture-agent-coordination.md` |
| "Done" as a transport event | A worker could finish a turn while still holding an open Owner decision, missing evidence, or using the wrong checkout. Transport completion is not review readiness. | `proof-multi-harness-runner.md`, `proof-coordination-runtime-v2.md` |

That is why the pack's coordination surface did **not** become a broker, a daemon, or a
cloud relay. The work started from repo-local failures and stayed repo-local until a measured
trigger justified anything more.

## 2. The pivots

Four pivots changed the design.

| Pivot | What changed | Why it mattered |
|---|---|---|
| **Worktree isolation** | The pack moved from shared-checkout convention to one-session-per-worktree discipline. | It turns work preservation into a structural property instead of a reminder. |
| **Artifact classes** | `authored`, `derived`, `register`, `hotspot` stopped being one lease problem. | Generated files are regenerated, registers allocate, hotspots batch under an integrator, only authored files lease normally. |
| **Owner / Coordinator / Sub-Agent doctrine** | Authority, decomposition and execution became separate seats. | The reviewer/ruler stopped being conflated with the track doing the work. |
| **Compile -> coordinate -> verify** | The operator's prose is compiled before dispatch, then verified again at handback and join. | A worker no longer receives an improvised paragraph and no longer hands back a success-shaped string. |

## 3. The arc from proposal to runtime

| Phase | What the repo adopted | What it rejected or demoted | Evidence |
|---|---|---|---|
| **Manual era** | Session contracts, rulings, a join script, human-owned seams. | Shared checkout safety, free-text ACK loops, "read the standing file" as a push channel. | `docs/proposals/owner-coordinator-subagent-coordination.md` critique, ai-de readings cited there |
| **Coordination substrate** | Append-only per-session ledger, artifact classes, worktree lifecycle, claim/check/release, derived-file regeneration. | A daemon, a database, "just scan the branch list" allocation. | `adr-0007`, `adr-0008`, `adr-0009`, `0dcff48`, `architecture-agent-coordination.md` |
| **Doctrine and seams** | Owner / Coordinator / Sub-Agent roles, typed seam requests, compile stage, human rulings, board/message layer plan. | Election, auto-reassignment, phi-accrual, unbounded loops, free-text dispatch. | `1705ad3`, `4a4c0b3`, `coordination-p0-p1.md`, `coordination-p2-p8.md`, `coordination-p3-p5-p8.md` |
| **execute-with-coordination** | The coordinator skill became the front door: `--agents`, `--brief`, then opt-in `--launch`. | Writing track code from the coordinator seat; "launch" as a silent replacement for the existing modes. | `pack/commands/execute-with-coordination/SKILL.md`, `reference/launch.md` |
| **Bounded runtime** | Qualified prepare/fingerprint/run/status, explicit permission decisions, dynamic compiled mailbox input, live attach where proved. | A broker, post-dispatch replay, arbitrary terminal typing, implied cross-platform parity. | `686af28`, `proof-multi-harness-runner.md`, `proof-coordination-runtime-v2.md` |

The key architectural lesson is that **the pack evolved by replacing guessed generality with
measured seams**. Every time the design was tempted toward a larger system, a smaller local control
proved sufficient or a proof pack showed which part was still not qualified.

## 4. Current architecture in one picture

```mermaid
flowchart TB
  Human["Human operator / repo owner"]
  Owner["Owner seat<br/>reviews requests and evidence"]
  Coord["Coordinator seat<br/>decomposes, dispatches, joins"]
  Compile["compile stage<br/>finished, dispatchable prompt"]
  Plan["prepare-for-coordination<br/>plan + owned paths + seams"]
  Skill["execute-with-coordination<br/>--agents | --brief | --launch"]

  subgraph Core["Repo-local coordination core"]
    Leader["leader ref + epoch fence"]
    Ledger["append-only ledgers<br/>claims, events, decisions"]
    Mail["mailboxes + doorbells"]
    Track["heartbeat / track / kick"]
    Requests["typed seam and decision requests"]
    Trees["worktree lifecycle"]
  end

  subgraph Runtime["Opt-in bounded runtime"]
    Runner["coord-runner.py"]
    Transport["coord_transport.py"]
    Native["qualified native/ACP adapters"]
  end

  subgraph Workers["Per-track worker sessions"]
    A["same-harness worker"]
    B["cross-harness worker"]
    C["live-attached worker"]
  end

  Proof["proof packs + receipts + API docs"]
  Join["conductor-join.py + verify gates"]

  Human --> Owner
  Owner --> Compile --> Plan --> Skill
  Skill --> Trees
  Skill --> Requests
  Skill --> Leader
  Skill --> Runner
  Trees --> A
  Runner --> Transport --> Native --> B
  Runner --> Native --> C
  Mail --> Owner
  Track --> Owner
  A --> Ledger
  B --> Ledger
  C --> Ledger
  A --> Proof
  B --> Proof
  C --> Proof
  Proof --> Owner --> Join
  Ledger --> Join
  Leader --> Join
```

**What this means in practice**

- The **core** is deterministic and repo-local.
- The **runtime** is optional and bounded.
- The **join** is where authority is re-checked.
- The **human/Owner** still decides meaning; the runtime only moves bounded work.

## 5. The four diagram families traced to code

### 5.1 Sequence - the operator workflow today

```mermaid
sequenceDiagram
  actor Human as Human
  participant Owner as Owner / Coordinator
  participant Compile as prompt-compile.py
  participant Plan as /prepare-for-coordination
  participant Exec as /execute-with-coordination
  participant Runner as coord-runner.py
  participant Worker as Worker session
  participant Decide as coord-decide.py
  participant Join as conductor-join.py

  Human->>Owner: request multi-track or multi-harness work
  Owner->>Compile: compile raw prose into a dispatchable contract
  Compile-->>Owner: finished compilation ids
  Owner->>Plan: allocate tracks, owned paths, seams, exit evidence
  Plan-->>Owner: canonical plan
  Owner->>Exec: run plan in --agents, --brief or --launch mode
  alt --agents
    Exec->>Worker: same-harness delegated track
  else --brief
    Exec-->>Human: one brief per track for a separately started session
  else --launch
    Exec->>Runner: prepare / fingerprint / run
    Runner->>Worker: bounded transport session with exact identity
  end
  Worker-->>Owner: seam request or decision request when needed
  Owner->>Decide: rule by numbered ruling / exact request id
  Decide-->>Worker: ruling and resolved request
  Worker-->>Owner: receipt + declared evidence
  Owner->>Join: verify evidence, epoch, gates, then integrate
```

This is the important change from the early approach: the worker does **not** hand back a free-form
"done". It hands back a bounded receipt plus evidence, and the Owner seat still holds the decision.

### 5.2 Class - the protocol objects that survived

```mermaid
classDiagram
  class Compilation {
    +auditId
    +dispatchable
    +render_sections()
  }
  class CoordinationPlan {
    +tracks[]
    +ownedPaths[]
    +exitEvidence[]
  }
  class LaunchContract {
    +run_id
    +owner
    +workers[]
    +parallelism
  }
  class WorkerAttempt {
    +session
    +branch
    +harness
    +transport
  }
  class Qualification {
    +fingerprint
    +effective_policy
    +capabilities
  }
  class DecisionRequest {
    +request_id
    +deadline
    +fallback
  }
  class Ruling {
    +number
    +request_id
    +text
  }
  class Receipt {
    +artifact hashes
    +checkout proof
    +review state
  }
  class LeaderDesignation {
    +session
    +epoch
    +expires_at
  }

  CoordinationPlan --> Compilation : consumes
  LaunchContract *-- WorkerAttempt
  WorkerAttempt --> Qualification : requires
  WorkerAttempt --> DecisionRequest : may raise
  DecisionRequest --> Ruling : resolved by
  WorkerAttempt --> Receipt : returns
  LaunchContract --> LeaderDesignation : fenced by
```

The design is intentionally small. These are the objects the code and proofs kept. Broker
registries, cloud relays, elections and CRDTs never made it past the design gate.

### 5.3 Layered architecture - what is deterministic vs profile-specific

```mermaid
flowchart TB
  subgraph L4["Human and review layer"]
    H["Human operator"] --> O["Owner rulings and receipt review"]
  end
  subgraph L3["Harness/runtime layer"]
    CC["Claude ACP / native hooks"]
    CX["Codex ACP / app-server"]
    GK["Grok ACP / leader socket"]
    AG["Agy native stream"]
    CP["Copilot hooks / native CLI"]
  end
  subgraph L2["Coordination protocol layer"]
    C1["compile stage"]
    C2["plans, seams, decisions"]
    C3["mail, doorbells, liveness"]
    C4["leader ref + join fence"]
  end
  subgraph L1["Deterministic core layer"]
    D1["coord-core.py"]
    D2["coord-runner.py"]
    D3["coord_transport.py"]
    D4["bounded_process.py"]
    D5["proof packs and tests"]
  end
  L1 --> L2 --> L3 --> L4
```

The boundary to remember is that **models live inside harnesses, and harnesses live above the
deterministic core**. Changing the model does not change the hook/transport boundary. Changing the
harness does.

### 5.4 Component - what execute-with-coordination grew into

```mermaid
flowchart LR
  EWC["/execute-with-coordination"]
  Agents["--agents<br/>same-harness sub-agents"]
  Brief["--brief<br/>manual cross-harness briefs"]
  Launch["--launch<br/>bounded multi-harness runtime"]
  Compile["compiled prompts only"]
  Review["Owner review + rulings"]
  Join["conductor-join.py"]

  EWC --> Agents
  EWC --> Brief
  EWC --> Launch
  Launch --> Compile
  Agents --> Review
  Brief --> Review
  Launch --> Review
  Review --> Join
```

The coordinator role stayed the same while the execution modes widened:

| Mode | What it buys | What it does **not** buy |
|---|---|---|
| `--agents` | Lowest friction inside one harness; native spawned-worker behavior. | Cross-harness proof, independent runtime diversity, or a different hook surface. |
| `--brief` | The smallest correct fallback. It carries the exact contract across harnesses when automation is unsupported or unqualified, without pretending the other side enforced anything. | Automation, liveness, or trust that the other harness enforced anything. |
| `--launch` | Opt-in bounded prepare/fingerprint/run/status over a qualified runtime. | Semantic acceptance, universal portability, or permission bypass. |

## 6. Models and harnesses are separate axes

This distinction is load-bearing and easy to lose:

| Change | What changes | What does **not** change |
|---|---|---|
| **Same harness, different model** | Reasoning profile, cost, and sometimes context window. | Hooks, transport, trust, or file sandbox. |
| **Different harness, same model family** | Adapter, queue/socket path, hook surface, and qualification burden. | Semantic diversity by itself. |
| **Different harness, different model** | Both the reasoning profile and the control surface. | Owner review, receipts, or the join fence. |

That is why the documentation and proof surface now distinguish **model qualification** from
**harness qualification**. A Copilot run that reports a GPT label but actually uses a Claude
backend is not "close enough". It is an invalid proof and must be thrown away. The same rule
already appears in the landed docs for permissions: zero callbacks is not permission evidence.

## 7. What shipped, and what deliberately did not

| Attractive idea | Why it was attractive | What actually shipped |
|---|---|---|
| HTTP/SSE bus or cloud relay | A single transport for all harnesses. | Repo-local files, git, native queues/sockets where they exist, and manual briefs where they do not. |
| Leader election | Looks automatic. | Human designation in a git ref with CAS, epoch, and reclaim. |
| One big "agent swarm" abstraction | One story for every scenario. | Spawned relationships, registered relationships, and a different push path for each. |
| Post-dispatch replay | Recover work after a crash. | At-most-once admission; after dispatch the state is indeterminate, never replayed automatically. |
| "Transport complete" as success | Easy status display. | Receipt verification, zero open Owner decisions, live leader check, then `ready_for_review`. |

The best summary is simple: **no implied distributed service if the code does not ship one**.

## 8. Actual scenarios and qualification limits

### 8.1 Runtime by harness, as currently documented in this branch

| Harness | Dynamic follow-up | Permission qualification | Live attach | Current limit |
|---|---|---|---|---|
| **Claude ACP 0.79.0** | Verified | Real inspected `allow_once` on a file edit | No qualified shared-terminal attach in this branch | Owner and worker runtime proven, but profile-specific qualification still required |
| **Copilot ACP / Windows** | Verified | Exact one-time approval observed; separate explicit denial produced no file; a held lease refusal left bytes unchanged | Arbitrary terminal attach remains unsupported | Qualified profile requires native `--model`, an emitted local plugin bundle, the exact-ID model policy and actual post-run model evidence. The first eight GPT-labelled runs were withdrawn as invalid because the backend was really Claude. |
| **Codex ACP 1.12.0 / Windows Job path** | Verified | Read-only GPT-5.5 handoff returned the matching JSON acknowledgement; the bounded Windows Job path survived the closed-pipe stdin fix | Verified via app-server socket/UUID | Not full Windows write-hook/trust qualification; explicit file-root scope remains narrow and identity-bound |
| **Grok 1.0.34** | Verified | Current installed profile auto-approved the canary; `ask` remains unqualified | Verified against an explicit leader socket | Live input exists; permission qualification remains profile-specific |
| **Agy 1.2.7** | Verified | `ask` rejected; denied native actions treated as blocked | No qualified live attach path | Headless stream is real; interactive approval is not |

### 8.2 Negative proofs that changed the design

| Negative proof | Why it matters |
|---|---|
| Two leader claims survive a union merge | The ledger can record leadership changes; it cannot arbitrate them. |
| `--force` overrides `--force-with-lease` | A join fence must be explicit, and the push path must never smuggle in `--force`. |
| A native hook/trust entry can exist without proving it fired | Discovery is not enforcement. Qualification must observe the actual refusal. |
| A worker can complete transport while still holding an open Owner decision | Final handback must read decision state after receipt verification. |
| A profile can auto-approve a canary with zero callbacks | Silence is not a permission model. It is a missing proof. |

These negative proofs are why the coordination docs are heavy on **reviewed limits**. The point of
the runtime proof is not to flatter the runtime. It is to keep unsupported behavior out of the
operator's mental model.

## 9. API coverage and current documentation gaps

The coordination architecture is better documented at the **design/proof** level than at the
docstring level. That is visible in the generated API reference:

| Script | Public functions | Source-docstring coverage | Implication |
|---|---:|---:|---|
| `coord-runner.py` | 14 | 7% | The runtime contract is currently carried by `spec-multi-harness-launch-and-monitor`, `design-multi-harness-runner` and the proof packs more than by inline API docstrings. |
| `coord-mail.py` | 22 | 23% | The message layer is behaviorally specified and tested, but its script-level API comments remain thin. |
| `coord-board.py` | 14 | 50% | Better internal coverage, still not complete. |
| `coord-decide.py` | 11 | 18% | The Owner-review path is documented mostly through specs/designs and rulings discipline. |
| `coord_transport.py` | 2 | 100% | The transport seam is small and fully described. |

**Current branch limit:** the separate 2026-09-21 implementation branch adds `coord_files.py`
and `platform_process.py`, but those modules are not present in this branch's generated API
reference and are therefore **not** described here as part of the landed surface.

## 10. 2026-09-21 landed qualification scope

The 2026-09-21 rebase onto `04db4f07015277b811e82bed51f9230162b7a134` moved the Copilot and
Windows runtime work out of the "pending" category and into committed source. The operator-facing
contract is now split between the general runtime proof, the Copilot profile reference, and the
public sanitized fixture at `pack/evals/fixtures/copilot-windows-qualification.json`.

| Landed evidence | What is now established | What is still explicitly limited |
|---|---|---|
| **Copilot GPT-5.4 worker qualification** | The qualified Windows path prepares and runs an isolated Copilot worker, inspects one exact native permission request, approves it once through the immutable queue, verifies actual GPT usage/assistant-model evidence, reaches `ready_for_review` with zero open decisions, and reviews / fast-forward joins fixture commit `31879118`. | The qualified path is the explicit GPT-only worker profile documented in `reference/copilot.md`; it is not a blanket Copilot profile and not an arbitrary saved-terminal attach path. |
| **Copilot negative controls** | Separate proofs now exist for an explicit denial with no file written, a true lease refusal with a specific holder and unchanged bytes, instruction-marker read/write, and active cancellation after a concrete marker write with `cleanup_error: null`. | Cancellation can omit usage, so cancellation is never readiness evidence. The historical `sourcecontrolscanary` field-misroute from the first eight runs remains invalid proof, not a tolerated edge case. |
| **Codex GPT-5.5 cross-harness handoff** | The committed runtime now proves a matching read-only JSON acknowledgement and the bounded Windows Job path after the closed-pipe stdin fix; actual `turn_context` shows `gpt-5.5` / `provider=openai`. | This is not full Windows Codex write-hook trust qualification. The file-root grant remains narrow and identity-bound. |
| **Open Owner-decision fence** | A seeded open Owner decision causes native Stop refusal; the model's attempted out-of-scope fabricated local-ledger expiry is not approved; the bounded attempt expires and never becomes ready. | That expiry is not mislabeled `RUN-DECISION-OPEN`. The completed-transport decision fence is proved separately by the real-Git offline integration path. |

Two documentation rules follow from this landed scope:

1. **Invalid proof stays invalid.** The first eight Copilot attempts supplied `--model gpt-5.4`
   but actually ran Claude in the backend. They are retained as negative evidence and excluded
   from qualification.
2. **Requested configuration is not effective configuration.** Copilot's landed profile binds the
   explicit native model setter, the required exact-ID policy (`fallback: gpt-5.4` then
   `gpt-5.4`), the emitted plugin bundle, and the post-run actual-model check. The profile is
   therefore proved by the effective model and usage evidence, not by argv alone.

<a id="from-prompt-to-coordinated-execution"></a>

## 11. From prompt to coordinated execution

The missing visible bridge was the workflow between the skills and the lower-level coordination
machinery. The pack now makes that bridge explicit.

| Stage | Operator-visible skill or seat | What it takes in | What it outputs | Underlying machinery | Human decision point |
|---|---|---|---|---|---|
| 1 | **Raw prompt** | ordinary prose | unstructured ask | none yet | the operator states the job |
| 2 | **[`/compile`](../pack/commands/compile/SKILL.md)** | raw prompt text or a prior prompt audit id | one compiled prompt, one compilation audit id, traced goal state, assumptions, `DR-n` requests, `dispatchable` flag | `prompt-compile.py` + `verify-compiled-prompt.py` | the operator may edit the compiled prompt; compile grants no permission, no worktree and no lease |
| 3 | **[`/prepare-for-coordination`](../pack/commands/prepare-for-coordination/SKILL.md)** | either raw intent or a compiled prompt already in hand | `docs/coordination/<plan-id>.md` + `.html` with tracks, owned paths, dependencies, budgets, exit evidence | `coord-core.py classify/install/doctor`, docs graph grounding | the coordinator decides boundaries, ownership and harness targets |
| 4 | **[`/execute-with-coordination`](../pack/commands/execute-with-coordination/SKILL.md)** | a parsed plan | worktrees (`--agents`), human briefs (`--brief`) or launched runtime sessions (`--launch`), plus receipts, rulings and a join | `coord-core.py`, `coord-mail.py`, `coord-runner.py`, `conductor-join.py` | the Owner rules on decisions, reviews receipts and approves integration |
| 5 | **[`/document`](../pack/commands/document/SKILL.md)** | landed code + proof + doc deltas | regenerated docs bundle, portal/front door, graph index, API docs, Pages bundle | `docs-graph.py`, `build-doc-site.py`, `build-docs-portal.py`, `build-web-index.py`, `build-pages-bundle.py` | the documentation steward decides whether the docs match the shipped code |

Two sequencing rules matter and are easy to overstate:

1. **`/compile` is the explicit utility.** Its source says it is the operator-facing CO-S0 stage
   and that the operator hands the compiled prompt on to `/optimize-graph`,
   `/prepare-for-coordination`, or another prose-input skill.
2. **The coordination skills consume a compiled prompt when one is already in hand.**
   `prepare-for-coordination` opens with *"Consume the compiled prompt when one is in hand"*;
   `execute-with-coordination` refuses dispatch when the compiled prompt is not dispatchable or
   still carries an unanswered `DR-n`. That is narrower than "every request auto-compiles", and
   the docs now say the narrower thing.

### Worked example

**Input (operator prose)**

> Add a deadline and a fallback to seam requests. The join should refuse an expired one. Do not
> touch the lease rules.

**After `/compile`**

- a `kind: prompt` audit entry for the raw text
- a `kind: compilation` audit entry with:
  - Goal / Done when / Not in scope / Tier / Fan-out cap / Context ceiling / Main-line budget
  - traced clauses
  - marked assumptions
  - any unresolved `DR-n` request
  - `dispatchable: true|false`

**After `/prepare-for-coordination`**

- `docs/coordination/<plan-id>.md`
- `docs/coordination/<plan-id>.html`
- declared track ownership
- dependency order
- budgets and exit evidence

**After `/execute-with-coordination`**

- one worktree per track or one external brief per track or one bounded runtime session per track
- seam requests and Owner decision requests where needed
- receipts and review evidence
- one `conductor-join.py` integration path

**After `/document`**

- updated source docs
- regenerated portal/front door and close-up bundle
- regenerated Docs Explorer index
- publishable `_site` bundle for Pages

### Skills vs machinery

The skills are the guided workflow; the Python scripts are the mechanisms that make the workflow
true:

| Workflow surface | Lower-level mechanism |
|---|---|
| `/compile` | `prompt-compile.py`, `verify-compiled-prompt.py`, audit-log append |
| `/prepare-for-coordination` | `coord-core.py classify/install/doctor`, artifact classes, plan emission |
| `/execute-with-coordination` | `coord-core.py`, `coord-mail.py`, `coord-runner.py`, `owner-review-gate.py`, `conductor-join.py` |
| `/document` | `docs-graph.py`, `build-doc-site.py`, `build-docs-portal.py`, `build-web-index.py`, `build-pages-bundle.py` |

That distinction matters operationally: **a skill can explain and sequence, but the proof lives in
the lower-level mechanism and its tests.**

## 12. Operator workflow end to end

1. **Compile the request.** The raw human ask becomes a finished, dispatchable compilation.
2. **Plan the tracks.** `/prepare-for-coordination` assigns owned paths, seams, and exit evidence.
3. **Choose the execution mode.**
   - `--agents` when one harness can hold the whole run.
   - `--brief` when the runtime is unsupported or unqualified.
   - `--launch` when a qualified runtime is available and the bounded contract matters.
4. **Designate or verify the Owner.** Leadership is a ref + epoch, not a chat convention.
5. **Run bounded work.** Every worker gets an explicit identity, checkout, compilation, budget, and
   fallback.
6. **Handle seams and decisions.** Requests become rulings; they do not become ambient memory.
7. **Verify evidence, then join.** Receipts, decision state, leader state, and the integrated gate
   set all have to pass before the work is accepted.

That is the endpoint of the arc: from informal prompt passing to a bounded, reviewable,
multi-harness workflow whose smallest correct fallback is always still a manual brief.
