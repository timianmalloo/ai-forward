---
id: coordination-p3-xp
title: "Coordination plan - P3 liveness, the cross-platform residue, and the stale knowledge review (after P0/P1)"
type: plan
status: superseded
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, worktrees, parallelism, liveness, cross-platform, docs-freshness, p3]
links:
  - { to: proposal-owner-coordinator-subagent-coordination, rel: implements }
  - { to: coordination-p0-p1, rel: refines }
  - { to: plan-cross-platform-readiness, rel: relates-to }
review-by: "2026-12-18"
review-suggested: []
summary: >-
  Three tracks after the P0/P1 landing: P3 progress liveness and the running track with the kick
  ladder (coord-core.py, hook adapters — so it waits for P1's coord-core changes); the
  cross-platform residue (documented commands that run in any shell, the three master-branch
  tests); and a review of the seven pack-evolution knowledge docs whose review dates passed on
  2026-09-12 and have kept the docs workflow red since. Disjoint paths; coordinator owns the
  shared surfaces and the join.
---

# Coordination plan — P3 liveness · cross-platform residue · stale knowledge review

- **Scope:** build-plan item P3 of the proposal; items P4 and P5 of `docs/plans/cross-platform-readiness.md`; the V13 review of `docs/knowledge/pack-evolution/` (7 docs, `review-by: 2026-09-12`).
- **Dispatch condition:** after `coordination-p0-p1` lands, because P3 edits `coord-core.py` (P1's file until then).
- **Coordinator:** this session or its successor (WT1a: a new session at this task boundary is the honest choice). **Sub-Agents:** `python-developer` for P3 and the cross-platform track; `documentation-steward` for the knowledge review.
- **Multiplier:** measured ≈ 1.3× tokens, wall dominated by the coordinator's spine (`sp-0009`, the four-track landing). **Tier:** T2 · **Fan-out cap:** 3.

## Layer state
| check | result | meaning |
|---|---|---|
| registry · merge driver · leader | ok; effective; `none designated` (measured 2026-09-19T18:56Z in two fresh trees) | unchanged |
| base | `origin/main` after the P0/P1 landing | trees created off that commit |

## Artifact classes
| path / pattern | class | coordination needed |
|---|---|---|
| derived views; `docs/audit/*.jsonl`; sync-pack outputs; `docs/security/*`; the register | as before | none / coordinator |
| `pack/scripts/coord-core.py` (`session heartbeat`, `coord track`, the kick ladder 0–2), `pack/adapters/hooks/*.json` + `pack/adapters/hooks/heartbeat.py` (new; PostToolUse/Stop for Claude Code, Grok, agy; worktree-mtime fallback), `pack/scripts/pack-doctor.py` (heartbeat status), `tests/docs_explorer/test_coord_liveness.py`, `docs/specs/liveness-and-track.md`, `docs/design/liveness-and-track.md`, `docs/notes/note-*liveness*.md` | authored | **Track P3 only** |
| the 8 backslash-continued and 4 `&&`-chained documented commands (in `pack/commands/**/SKILL.md`, `pack/knowledge/*.md`, `pack/adapters/INSTALL.md` — the exact list is `docs/investigations/cross-platform-readiness.md` XC-*), the 10 bare `python` skill commands, the skill template's Audit block sentence, CT27's `$LASTEXITCODE` remedy, the `AGENT_SESSION` file-name sanitiser (`coord-core.py` — **a seam to P3**, who owns the file: the cross-platform track hands P3 the one-function patch), `tests/docs_explorer/test_coord_derived.py` (default branch from `git symbolic-ref` or `git init -b main`), `tests/docs_explorer/test_documented_commands_portable.py` (new lint-shaped test) | authored | **Track XP only** |
| `docs/knowledge/pack-evolution/*.md` (7), their `review-by` and `review-suggested` fields, one decision note recording what was re-verified and what was flagged | authored | **Track KB only** — reviewing, not rewriting: a claim that no longer holds is flagged `review-suggested` with the reason, never silently edited; a date moves only where the content was re-verified |
| INSTALL rev 79, counts, `docs/coordination/**`, `docs/security/**`, `docs/lessons/defect-classes.md`, `pack/context-budget.json` | authored | coordinator |

## Tracks
| track | owns | depends on | tier | fan-out cap | budget | exit evidence | harness |
|---|---|---|---|---|---|---|---|
| **P3 — liveness + track** | the P3 row | proposal §4 (progress heartbeat, running track, kick ladder), §7 P3, D7 (heartbeats carry progress; no phi); KB hook-surface table; P4's doorbell adapters as landed (same hook files — add entries, do not restructure); P1's typed requests as landed (the ladder's rung 2 is a decision request with a deadline) | T2 | 0 | 160 calls · 150 min | spec + design; `session heartbeat` with progress deltas (calls, files, tokens since last) from hooks and worktree mtime fallback; `coord track` renders per work item: owner, state (`live` / `stalled` / `blocked` / `done`), blocked-on, deadline, last progress; the fixture from the proposal: pings with zero progress deltas render `stalled`, never `live`; empty corpus → NOT CHECKED; kick ladder 0–2 as notify (mail `note`) → kick (mail `kick`, capped at two per work item) → decision request (`coord request add` with deadline); tests red-first; existing coord tests green; lints 0 | claude |
| **XP — cross-platform residue** | the XP row | `docs/plans/cross-platform-readiness.md` P4/P5, `docs/investigations/cross-platform-readiness.md` (the counted sites), classes PLAT-A/PLAT-B/CTX-Q | T1 | 0 | 100 calls · 90 min | the counted commands rewritten and a lint-shaped test that fails on a backslash continuation or `&&` chain inside a documented command block; `test_coord_derived.py` green on a machine whose `init.defaultBranch` is not `master` (prove by running with `-c init.defaultBranch=main` and `=master`); the sanitiser patch delivered to P3 as a seam; lints 0 | claude |
| **KB — stale knowledge review** | the KB row | V13 (review-by SLA), the docs workflow's freshness gate (`docs-graph.py freshness --gate fail`), `docs/knowledge/pack-evolution/sources.md` (re-fetch each source; a dead link is a finding) | T1 | 0 | 80 calls · 60 min | each of the 7 docs re-verified or flagged with a reason; `docs-graph.py freshness --gate fail` exit 0 on the tree; a decision note listing per doc: verified claims, changed claims, dead sources; no content rewritten silently | claude (`documentation-steward`) |

## Serial spine
| item | why | who |
|---|---|---|
| Dispatch after the P0/P1 landing | `coord-core.py` | coordinator |
| The `AGENT_SESSION` sanitiser | one function in P3's file, written by XP | seam XP → P3 |
| INSTALL rev 79, counts, sync, every generator, verify-bundle, linear landing | shared surfaces | coordinator |

## Seams
| from -> to | the request | resolved by |
|---|---|---|
| XP -> P3 | the sanitiser function + its test, as a patch file XP places in its own tree under `docs/coordination/seam-xp-to-p3.patch`; P3 applies it | P3 before its implement stage closes |
| P3 -> coordinator | new hook file for INSTALL; the doctor line | coordinator |
| KB -> coordinator | the decision note id for the register (no class expected) | coordinator |

## Struck tracks
| track | why |
|---|---|
| P5 owner review mechanics alongside | it needs P3's decision-request rung and P6's board post for rulings to be observable; sequence after P3 |
| Merging XP into P3 | different intent and different reviewers; XP is T1 |

## Order of operations
| # | action |
|---|---|
| 1 | after the P0/P1 landing: `coord worktree new` × 3 off `origin/main`; `coord doctor` in each |
| 2 | dispatch the three with the five-part contract (width 3) |
| 3 | verify returns in-tree; commit each; join KB (docs-only, `--docs-only`), then XP, then P3 |
| 4 | coordinator: register any class; rollups; INSTALL rev 79; sync; every generator; full pytest; `verify-bundle.ps1`; linear landing; CI (both workflows now expected green); cleanup; planned vs actual |

## Status
| | |
|---|---|
| **Completed** | plan |
| **Remaining** | waits for the P0/P1 landing |
| **Best next action** | step 1 once `main` carries P0/P1 |
