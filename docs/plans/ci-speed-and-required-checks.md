---
id: plan-ci-speed-and-required-checks
title: "Plan — fast CI, automatic triggers, then required checks on main"
type: plan
status: proposed
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [plan, ci, performance, branch-protection, next-steps]
links:
  - { to: proposal-ci-speed-2026-10-17, rel: depends-on }
  - { to: note-20261017-require-ci-before-merge, rel: depends-on }
  - { to: forensic-review-rev108-backlog, rel: relates-to }
review-by: "2026-12-17"
review-suggested: []
summary: >-
  Execution plan for the three accepted CI changes (parallel pytest, drop the duplicate
  adoption-entrypoints test list, branch-scoped cancel-in-progress) and the owner's decision to
  require CI before merge. Recorded as next steps on 2026-10-17; nothing in it is executed yet.
  The order is forced: measure, make the gate fast, restore pull_request triggers, then switch
  on the required check, because a required check that never reports blocks every merge.
---

# Plan — fast CI, automatic triggers, then required checks

**Status: `proposed` — next steps, not executed.** Accepted by the owner on 2026-10-17:
changes C1, C2 and C3 of `proposal-ci-speed-2026-10-17`, and the decision
`note-20261017-require-ci-before-merge`. C4–C7 from the proposal appear here only where the
accepted work depends on them.

## Goal state

- **Goal:** every change reaches `main` only through a green, required, reasonably fast CI run.
- **Done when:**
  - `main` protection lists the `pack-consistency` jobs under `required_status_checks`;
  - a PR's run completes in ≤ 20 min wall-clock (median of 5);
  - the collected and passed test counts are equal in every job.
- **Not in scope:** C4 (fixing slow test fixtures) and C5 (folding docs/pages gates). Both are later backlog items.

## Execution graph

Each node lists its dependencies. Only real data dependencies are shown.

| # | Node | Depends on | Change | Proof (observed, not inferred) |
|---|---|---|---|---|
| P0 | **Baseline on `main`** | — | Dispatch `pack-consistency` on `main` once | A `main` run exists; per-job pytest seconds recorded in this plan |
| P1 | **xdist spike (C1)** | P0 | Throwaway branch: add `pytest-xdist`, run `pytest -n 4` in all three jobs; dispatch 3× | Windows pytest ≤ 1,200 s; 0 new failures in 3 runs; passed == collected each job |
| P1a | **Fix races found by P1** | P1 | Any shared-state test found racing is fixed (tmp paths, env, chdir), never answered with `-n 1` | The racing test passes 3× under `-n 4` |
| P2 | **Land C1 + C3** | P1, P1a | PR: `-n 4` + a step asserting passed == collected; `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: ${{ github.ref != 'refs/heads/main' }} }` on pack-consistency, docs, adoption-entrypoints | The PR's own run is green, and two quick pushes to the branch show the older run cancelled |
| P3 | **C2 prerequisite** | P2 | Add the `uv` install and `AIF_TEST_OLD_PYTHON` to the pack-consistency jobs | `pytest -rs` skip count for the 28 adoption files is ≤ the P0 count |
| P4 | **C2** | P3 | Delete the duplicated 28-file step from `adoption-entrypoints.yml`; keep the unique remote / repeat / `cmd` one-liner steps | One adoption-entrypoints dispatch **completes** (it never has; record why if it still queues) |
| P5 | **Restore triggers (C7)** | P2 | `push: [main]` and `pull_request` on pack-consistency (plus docs, pages as before `156943d`) | A PR opened against `main` starts the run automatically |
| P6 | **Pin check names** | P5 | A test asserting the job names in `pack-consistency.yml` match the list recorded here | The test fails when a job is renamed |
| P7 | **Require the check** | P5, P6, and P2's speed result | `gh api -X PUT repos/timianmalloo/ai-forward/branches/main/protection` adding `required_status_checks: { strict: true, contexts: [<P6 names>] }`, keeping every existing setting | Protection read back shows the block; a deliberately red PR cannot merge; a green PR can |
| P8 | **Update the docs that describe the workflow** | P7 | `AGENTS.md` push section (direct pushes end; PR + rebase-merge), WT1c delivery wording, `docs/notes/required-status-checks.md` status | Gate 1 / consistency check green; the AGENTS.md text matches the protection read-back |
| P9 | **Duration budget (C6)** | P5 | `if: always()` job writing per-job durations to the summary; fails on > 50% growth against the trailing median | Two weeks of `main` runs with ≥ 10 recorded points |

**Critical path:** P0 → P1 → (P1a) → P2 → P5 → P6 → P7 → P8. P3 → P4 and P9 run off the critical path once P2 and P5 land.

## Risks and how each is contained

- **The required check blocks all merges** if the trigger or the names are wrong. Containment: P7 depends on P5 and P6, and its proof includes a green PR merging.
- **xdist exposes races.** Expected. Each race is a defect (class PARALLEL-BLIND) and is fixed in P1a.
- **Direct-push habits break.** Agents and the owner push to `main` today. P8 rewrites the documented workflow in the same change window as P7, not after it.
- **No break-glass path.** With `enforce_admins: true` an urgent fix also waits for CI. If that proves unacceptable, the decision note's re-open trigger applies; the plan does not weaken `enforce_admins`.

## Measurement

Record planned vs actual per node in this file as it executes: wall-clock per job, and test counts collected/passed/skipped per job.
