---
id: coordination-p0-p1
title: "Coordination plan - P0 doctrine home and P1 typed seam requests, two full loops after the P2/P4/P6/P8 joins"
type: plan
status: proposed
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, worktrees, parallelism, doctrine, seam-requests, p0, p1]
links:
  - { to: proposal-owner-coordinator-subagent-coordination, rel: implements }
  - { to: coordination-p2-p8, rel: refines }
review-by: "2026-12-18"
review-suggested: []
summary: >-
  Two Sub-Agent tracks dispatched after the four P2/P4/P6/P8 joins land, because both touch files
  those tracks own: P0 turns agent-coordination.md into the always-loaded doctrine home (CO1–COn
  from the proposal's §3, with the seeded CO-S0 and CO-L sections kept) and registers CTX-Q; P1
  gives seam requests a deadline, a fallback, an ack pinned to a blob, five states and a
  termination variant in coord-core.py. Disjoint authored paths; the coordinator owns the shared
  surfaces, the always-on budget baseline and the join.
---

# Coordination plan — P0 doctrine home · P1 typed seam requests

- **Scope:** build-plan items P0 and P1 of `proposal-owner-coordinator-subagent-coordination`, each a full loop (spec → design → implementation, red-first) in its own tree, **dispatched only after** `coordination-p2-p8`'s four joins are on the integration branch (P0 edits `agent-coordination.md`, which P2 extends today; P1 edits `coord-core.py`, which P2 owns today).
- **Coordinator:** this session. **Sub-Agents:** one per track, `python-developer`, own worktree each, invoking `/specify`, `/design-slice`, `/implement` themselves.
- **Multiplier:** measured ≈ 1.3× tokens (`sp-0009`); paid for independence (a knowledge doc vs a script) and context hygiene.
- **Tier:** T2 · **Fan-out cap:** 2 (coordinator); 0 per track.

## Layer state
| check | result | meaning |
|---|---|---|
| registry · merge driver | ok; effective (measured 2026-09-19T16:58Z) | unchanged |
| regeneration | owed until the join | coordinator regenerates once — every generator in the registry plus the two `tools/build-*` views |
| harness · claude | enforcing boundary; Agent-tool delegation observed on six tracks today | as before |
| base | `origin/main` **after** the P2/P4/P6/P8 landing commit | the trees are created off that commit, never earlier |

## Artifact classes
| path / pattern | class | mechanism | coordination needed |
|---|---|---|---|
| derived views; `docs/audit/*.jsonl`; sync-pack outputs; `docs/security/*` | as in `coordination-p2-p8` | same rules | none / coordinator |
| `pack/knowledge/agent-coordination.md` (becomes `load: always`), `pack/knowledge/session-worktree-discipline.md` (a CTX-Q pointer), `docs/lessons/defect-classes.md` **CTX-Q row only** (coordinator inserts the row text P0 returns — the register is coordinator-owned), `docs/specs/agent-coordination-doctrine.md`, `docs/design/agent-coordination-doctrine.md`, `docs/notes/note-*doctrine*.md`, `tests/docs_explorer/test_agent_coordination_doctrine.py` | authored | lease | **Track P0 only** |
| `pack/scripts/coord-core.py` (`cmd_request`: `add --deadline --fallback`, `ack --blob`, `resolve`, `expire`; five states), `pack/scripts/pack-doctor.py` (expired-request check), `tests/docs_explorer/test_coord_requests_typed.py`, `docs/specs/typed-seam-requests.md`, `docs/design/typed-seam-requests.md`, `docs/notes/note-*seam*.md` | authored | lease | **Track P1 only** |
| INSTALL.md (rev 78), counts, managed blocks (the doctrine doc becomes always-on: the block cites it), `pack/context-budget.json` (`always_on_tokens` and `prefix_tokens` baselines — the ratchet must be acknowledged, not raised silently), `docs/coordination/**`, `docs/security/**`, `docs/lessons/defect-classes.md` | authored | lease | **Coordinator only** |

### Fixed contracts
**P0 — the doctrine doc:** keeps the seeded `CO-S0` and `CO-L` sections verbatim; adds `CO1–COn` from proposal §3 (seats and the capability floor, the two control relationships, the invariants I1–In each traceable to a measurement or spike), §4 protocol objects by name, the kick ladder, and the vocabulary (Owner seat · human operator · conductor); `load: always` with a **token ceiling of 3,000** for the whole doc (the always-on ratchet is the guard: `context-budget.py gate` must pass with an acknowledged baseline change the coordinator makes, never a silent one); stage detail beyond the ceiling goes to `docs/knowledge/multi-agent-coordination/` and is cited. **CTX-Q** (parent enters the worktree after delegating) is returned as a class row with its control (`coord worktree new` + the brief's "no EnterWorktree" line + a profiler finding) for the coordinator to insert.
**P1 — typed seam requests:** `coord request add --to <session> --deadline <s> --fallback <text> [--blob <sha>]` (refuses without deadline or fallback, exit 2); states `sent → received → acked → resolved | expired`; `ack --blob <sha>` pins the acknowledgement to the artifact blob it read (a later change to that blob renders the ack `stale` on read); `resolve`, `expire` (deadline passed ⇒ the fallback is recorded as the outcome, never silence); `coord metrics` gains unresolved-by-deadline and fallback-taken counts; `coord doctor` FAILs when an expired request has no recorded outcome; the ledger records every transition. Constants: default deadline 900 s (the long lease), retry 20 s (D13). Mail integration (P4's `decision-request`/`done` kinds) is by `--ref <mail id>`, no new store.

## Tracks
| track | owns | depends on | tier | fan-out cap | budget | exit evidence | harness |
|---|---|---|---|---|---|---|---|
| **P0 — doctrine home** | the P0 row | proposal §3–§4, the landed CO-S0/CO-L sections, `context-budget.py`, class CTX-Q's investigation note (`docs/investigations/cross-platform-readiness.md` records the original CTX-Q instance) | T2 | 0 | 120 calls · 120 min · ceiling 400k | spec + design with gate records; the doc at `load: always` under 3,000 tokens (`context-budget.py` reports the number); `test_agent_coordination_doctrine.py` (red first: every invariant in proposal §3.3 has a CO-line; CO-S0/CO-L unchanged; ceiling); lints exit 0; the CTX-Q row text | claude |
| **P1 — typed seam requests** | the P1 row | proposal §4 "Seam request (typed)", D5, MAST termination-unaware 12.4%, ai-de's 28% unresolved (KB), `cmd_request` as it is | T2 | 0 | 160 calls · 150 min · ceiling 400k | spec + design with gate records; the verbs and states above; `test_coord_requests_typed.py` (red first: add without deadline refused; expire records the fallback; stale ack detected; doctor FAILs an expired request without outcome; metrics counts); existing coord tests green; lints exit 0 | claude |

## Serial spine
| item | why | who |
|---|---|---|
| Dispatch after the P2/P4/P6/P8 landing | shared files with today's tracks | coordinator |
| The always-on budget baseline | one acknowledged ratchet change, once | coordinator |
| CTX-Q row insertion, rollup links, counts, INSTALL rev 78, sync, all generators, verify-bundle, linear landing | shared surfaces | coordinator |

## Seams
| from -> to | the request | resolved by |
|---|---|---|
| P0 -> coordinator | the CTX-Q row; the always-on token number; the managed-block citation line | coordinator at the join |
| P1 -> coordinator | the `documents` links; INSTALL changelog text | coordinator at the join |
| P1 -> P4 (landed) | none expected: `--ref <mail id>` is read-only against the mail store | — |

## Struck tracks
| track | why |
|---|---|
| P0 and P1 as one track | a knowledge doc and a script have nothing in common but the proposal; one context would carry both loops |
| P3 alongside | heartbeats need P4's hook adapters as landed and P1's deadlines; sequence, not width |

## Order of operations
| # | action | cost | why now |
|---|---|---|---|
| 1 | after the four joins land on `main`: `coord worktree new --branch impl/p0-doctrine --base origin/main --session p0-doctrine`; same for `impl/p1-requests` / `p1-requests`; `coord doctor` in each | 2 min | fresh base |
| 2 | dispatch both with the five-part contract (width 2) | — | independent |
| 3 | verify returns in-tree; commit each on its branch; join P0 then P1 by `conductor-join.py` | 10 min each | E16 |
| 4 | coordinator: CTX-Q row, rollups, counts, INSTALL rev 78, `context-budget.py gate --update-baseline` (acknowledged in the commit message), sync, every generator, full pytest, `verify-bundle.ps1`; linear landing; CI; cleanup; planned vs actual | 30 min | shared surfaces |

## Status
| | |
|---|---|
| **Completed** | plan |
| **Remaining** | waits for the P2/P4/P6/P8 landing |
| **Best next action** | step 1 once `main` carries the four joins |
