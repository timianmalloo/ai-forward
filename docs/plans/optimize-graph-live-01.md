---
id: plan-optimize-graph-live-01
title: "optimize-graph live run 01 — commit the rev-40 change set"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [optimize-graph, plan, cost-vs-delivery, measurement, live-run]
links:
  - { to: kb-graph-and-loop-engineering, rel: depends-on }
  - { to: backtest-optimize-graph, rel: relates-to }
  - { to: audit-log, rel: relates-to }
review-by: "2027-02-18"
summary: >-
  First live /optimize-graph run, on the prompt that asked for it. Records the plan, the
  planned-vs-actual ledger (GO18), and the run's headline measurement — parallelising three
  independent verification gates ran 19% SLOWER (0.84x) while completeness, rigor and tokens were all
  unchanged, which under the lexicographic objective is pure loss and a rejected plan. The span was
  83% of the work so the ceiling was only 1.20x, and fan-out overhead exceeded the whole available
  gain. The measurement replaced a modeled constant and produced GO4a.
---

# optimize-graph — live run 01

**Prompt (verbatim):** *"commit pack/ + .claude/ + .github/ + docs/ together, then run /optimize-graph live and record planned-vs-actual (GO18) to replace the modeled constants with measurements"*

**Date:** 2026-08-22 · **Tier:** T2 (a commit that writes always-loaded directives) · **Objective:** the standing lexicographic order — completeness and rigor, then token cost, then speed (GO4a).

---

## Stage 0 — Triage (GO16)

**Plan, do not skip.** More than two nodes, and three rigor gates are triggered (the change set contains always-loaded directives, a client-rendered surface, and graph artifacts). The skip threshold is 1–2 nodes with no loop, no fan-out and no gate.

## Stage 1 — Naive graph (what an unplanned agent does)

| # | Node | Exit condition | Tier |
|---|---|---|---|
| 1 | `git add` the four named paths | staged | T0 |
| 2 | `git commit` | commit object exists | T0 |
| 3 | *discover `CLAUDE.md` / `tools/` / `web/` were missing* | — | **rework** |
| 4 | amend or add a second commit | tree consistent | T0 |
| 5 | run the gates | green | T0 |
| 6 | *discover a gate is red after committing* | — | **rework** |
| 7 | choose a subject for the optimize-graph run | chosen | T3 |
| 8 | write the plan | file exists | T3 |
| 9 | execute it | done | mixed |
| 10 | measure | numbers exist | T0 |
| 11 | write the ledger + audit | appended | T0 |

**Work `T₁` = 11 · span `T∞` = 11** (fully serial). Two of the eleven are rework nodes caused by the plan's own omissions.

## Stage 2 — Floor nodes (GO12, added *before* optimizing)

| Node | Why it is triggered | Immovable |
|---|---|---|
| **F1** consistency gate | the change edits counts in six documents and adds a skill | yes |
| **F2** `docs-graph validate` | the change adds nine graph artifacts | yes |
| **F3** render proof (E11) | the change adds a client-rendered surface (PACK-G / PACK-H) | yes |
| **F4** secret scan | 47 changed files, committed to a public repo (AL4) | yes |
| **F5** audit + change entries | AL5 / CL1 | yes |
| **F6** honest commit message | the tree holds work from two streams (CI11, RIG-E) | yes |

**All six precede the commit.** A gate that fires after the commit costs a second commit; the same gate firing before costs one node (GO4).

## Stage 3 — Edge classification (GO2)

| Edge | Kind | Verdict |
|---|---|---|
| determine true atomic file set → stage | **data** | keep |
| F1, F2, F3 → commit | **decision** (a red gate changes whether we commit at all) | keep |
| F1 ↔ F2 ↔ F3 | **none** — all read-only, no shared exclusive resource | **incidental → deleted** |
| stage → commit | **data** | keep |
| commit → measure | **incidental** — measurement needs neither | **deleted** |
| execute → measure | **data** | keep |

**Finding at plan time.** The naive plan staged the *four named paths*. Classification showed `CLAUDE.md`, `AGENTS.md`, `README.md`, `tools/` and `web/` carry the same change — the managed blocks, the corrected counts, and the PACK-G gate extension. Committing only four paths would have produced exactly the drift the atomicity rule exists to prevent. **This deleted naive nodes 3–4 (the rework pair) before they happened.**

## Stage 4 — Span and the objective (GO4, GO4a)

```
determine-atomic-set
        │
        ├── F1 consistency ┐
        ├── F2 docs-graph  ├── gate set ──► commit ──► measure ──► ledger + audit
        ├── F3 render      ┘
        └── F4 secret scan
```

**Work `T₁` = 9 · span `T∞` = 6.** Ceiling `Tₚ ≥ T∞` ⇒ no better than 11 → 6.

## Stage 5 — Concurrency (GO5–GO7)

**Independence test on F1/F2/F3:** no data edge (none consumes another's output); no decision edge (none changes another's shape); no shared exclusive resource (all read-only). → **may run concurrently.**

**But see the measurement below — they should not.** Independence was necessary and not sufficient (GO4a).

**Fan-out contract (as specified before measuring):** width cap 3 · transient policy n/a (local, deterministic) · per-branch exit = process exit code · join = **all-must-succeed** · containment = **any red blocks the commit**.

## Stage 7 — Loops (GO8–GO10)

The gate → fix → gate loop is the only cycle.

- **Variant:** number of open gate findings.
- **Well-founded floor:** 0.
- **Exit condition:** 0 findings across all three gates.
- **Cap:** 3 iterations (circuit breaker; firing = defect signal).
- **Observed:** 1 iteration. Across the preceding session the variant ran 15 → 1 → 0 (count drift → stale portal → clean).

---

## Planned vs actual (GO18)

| Metric | Naive | Planned | **Actual** | Kind |
|---|---|---|---|---|
| Nodes (work) | 11 | 9 | **9** | Verified |
| Span | 11 | 6 | **6** | Verified |
| Rework passes | 2 | 0 | **0** | Verified |
| Gates present before commit | 0 | 6 | **6** | Verified |
| Loop iterations | unbounded | ≤3 | **1** | Verified |
| Commit atomicity | 4 paths (drift) | full set | **61 files, one commit** (`dc5ffc7`) | Verified |
| Working tree after | — | clean | **clean (0 files)** | Verified |
| Post-commit gate state | — | green | **green** | Verified |

**Span reduction 11 → 6 = −45%**, structural, and it matched the plan exactly. Completeness and rigor both rose (six floor gates present instead of none; two rework passes eliminated). Tokens fell (two rework nodes never ran). Speed improved. **All four axes moved the right way, so the plan is accepted without needing the GO4a trade rule.**

---

## ★ The headline measurement — the naive optimization was wrong

The three-gate wave was the one node where a *modeled* constant could be replaced with a *measured* one. Each gate was timed individually (best of three), then all three were run as genuinely concurrent processes (best of three).

| Quantity | Value | Kind |
|---|---|---|
| `check-consistency.py` | **0.49 s** | **Verified — measured** |
| `docs-graph validate` | **0.06 s** | **Verified — measured** |
| render proof | **0.04 s** | **Verified — measured** |
| **Work `T₁`** (serial total) | **0.59 s** | Verified |
| **Span `T∞`** (longest gate) | **0.49 s** | Verified |
| Theoretical ceiling `T₁/T∞` | **1.20×** | derived |
| Brent bound at p=3 | **0.52 s** | derived |
| **Parallel, actual** | **0.70 s** | **Verified — measured** |
| **Actual speedup** | **0.84× — 19% slower** | **Verified** |

**Parallelising three genuinely independent nodes made the work slower.** Two causes, both predicted by the standard and both invisible without measuring:

1. **The span dominated.** One gate is **83% of the work**, so the ceiling was never 3× — it was **1.20×**. The entire available prize was **0.10 s**.
2. **Fan-out overhead exceeded the prize.** Process spawn cost ≈ 0.2 s — twice the maximum possible gain.

### Reading it against the objective (GO4a)

| Axis | Rank | Effect of parallelising |
|---|---|---|
| Completeness | 1 | **unchanged** |
| Rigor | 1 | **unchanged** |
| Token cost | 2 | **unchanged** (same three processes, same work) |
| Speed | 3 | **worse — 19% slower** |

Under the lexicographic objective this is not a neutral trade and not a marginal call. A slower plan is acceptable **only when completeness ↑ and rigor ↑ and tokens ↓, all three together**. Here **none** improved. **The parallel plan is therefore pure loss and is rejected** — and the serial gate set is what actually shipped.

This is the strongest available validation of **GO3** (profile before reshaping) and **GO4** (compute the ceiling before widening): an optimizer that parallelised on the independence test *alone* would have made this node worse on the only axis it moved.

### What the measurement changed

- **Standard:** added **GO4a** — the lexicographic objective, the conjunction rule for accepting a slower plan, and the requirement to **compare the ceiling `T₁ − T∞` against the fan-out overhead before widening**. Prime directive 1 now states the ordering explicitly.
- **Evidence base:** `data-and-constants.md` carries the measured block, replacing the modeled uniform-node-cost assumption for this class of node.
- **Back-test:** its uniform-cost model is now qualified — it holds where node costs are comparable and **overstates** the gain where one node dominates. The back-test's *structural* results (span, completeness, rigor) are unaffected; its modeled *time* index is an upper bound, not an expectation.

---

## Residual risk

- These are **sub-second local gates**. Fan-out overhead is a roughly fixed cost, so it dominates *small* nodes and is negligible for nodes measured in minutes (a research track, a build, a test suite). **Do not generalise "parallelism is slower"** — generalise **"compute the ceiling and compare it to the overhead."**
- Node-cost uniformity remains the back-test's weakest assumption (open question Q1). One measurement is not a distribution.
- Wall-clock on a shared developer machine is noisy; best-of-three mitigates but does not eliminate it.
