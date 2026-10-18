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

### Actuals (2026-10-17/18)

Pytest-step seconds per job, from `gh run view --json jobs` (step start → completion).

| Node | Runs | ubuntu | macOS | Windows | Result |
|---|---|---|---|---|---|
| P0 baseline, serial (`main` `cbf5079`) | 39064545888 | 927 | 1263 | 2590 | **red on all three**: found WT-E2 (security regression) and RUN-B2; fixed in PRs #15, #16 |
| Serial, after the fixes | 39068485991 | 923 | 1288 | 2943 | green on all three, the first fully green run |
| P1 `-n 4` | 39072532730 / 534222 / 535673 | 360 / 402 / 326 | 626 / 550 / 477 | 1358 / 1169 / 1382 | 9/9 green, 0 races; Windows ≤ 1,200 s met 1 of 3 |
| P1 Windows `-n 8` | 39074268339 / 269865 / 271836 | 410 / 405 / 374 | 819 / 795 / 916 | 1272 / 1157 / 1288 | **rejected**: Windows red 3/3 on load-sensitive tests for a 6% gain; ubuntu exposed one `-n 4` race (P1a) |
| Local `verify-bundle.ps1`, Windows dev box | — | — | — | 2,390 s serial → **1,119 s** at `-n 4` | identical results |

**Deviation from the goal state (owner ruling, 2026-10-18).** At `-n 4` the Windows job stays at
~23 min wall-clock, so "a PR's run completes in ≤ 20 min" is not met. The owner chose to require
all three jobs and accept the measured ~23 min; further speed is C4 (slow fixtures), already out of
scope here. `-n 8` was measured and rejected, not assumed.

**P1a serial stage (owner ruling, 2026-10-18).** Each Windows round at `-n 4` failed a
different wall-clock test (deadline, process-kill and concurrent-writer assertions), so the cause
was contention, not the tests. Those tests are marked `wallclock` in one list
(`tests/docs_explorer/conftest.py`) and run serially after the parallel stage, with their real
deadlines (~44 s on Windows). `check-test-counts.py` checks both stages' JUnit reports together.
Local `verify-bundle.ps1`: **all 18 gates pass, 925 s.**

**P1a race fixed:** `test_exit_between_poll_and_signal_rechecks_macos_zombie_error` simulated
macOS's EPERM while the peer could still be alive; it now waits for a real unreaped exit
(`waitid` with `WNOWAIT`). **P5 deviation:** `pack-consistency`'s `pull_request` is restored
**unfiltered**. The pre-`156943d` `paths` filter would stop a required check reporting on a PR
outside it (risk 1 above). P6 pins this in `test_ci_required_checks.py`. **P2 deviation:** the
concurrency group is on `pack-consistency` and `docs` only. `adoption-entrypoints` stays exactly
manual-only, as `test_upstream_adoption_integration` pins by policy; with no PR trigger a group
there would do nothing.
