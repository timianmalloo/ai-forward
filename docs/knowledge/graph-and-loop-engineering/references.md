---
id: kb-graph-and-loop-engineering-references
title: "Graph & loop engineering — Reference information"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [reference, formulae, brent, amdahl, ranking-function, invariants, edge-cases]
links:
  - { to: kb-graph-and-loop-engineering, rel: refines }
review-by: "2026-11-20"
summary: >-
  The formulae, invariants, decision rules and edge cases of the domain — the work/span bounds,
  Amdahl and Brent, the independence and coupling tests, the termination obligation, the granularity
  rules, and the boundary set an execution-graph planner must handle.
---

# Reference information

## Formulae (the load-bearing maths)

| Name | Formula | Reading |
|---|---|---|
| **Work** | `T₁ = Σ cost(nodeᵢ)` | total sequential cost |
| **Span / critical path** | `T∞ = max over paths Σ cost(node)` | the fastest the graph can possibly run |
| **Brent's bound** | `Tₚ ≤ (T₁ − T∞)/p + T∞` | achievable time on `p` workers |
| **Speedup** | `Sₚ = T₁ / Tₚ` | how much faster than serial |
| **Parallelism** | `T₁ / T∞` | average width; more workers than this buys nothing |
| **Amdahl** | `Sₚ = p / (1 + σ(p−1))` → `1/σ` | ceiling given a sequential fraction `σ` |
| **Efficiency** | `Sₚ / p` | how much of the added capacity is actually used |

**The one that governs planning:** `Tₚ ≥ T∞` always. **You cannot parallelize below the critical path.** If the plan is too slow and the span is the reason, the only legal moves are *shorten the chain* (collapse, remove, or overlap steps) — never *add workers*.

## Decision rules

**Independence test (may these run concurrently?)** — all three must hold:
1. **No data edge** — neither consumes the other's output.
2. **No decision edge** — neither's result changes the *shape* of the other (if B's plan depends on A's finding, they are coupled even if B does not read A's output).
3. **No shared exclusive resource** — same file to write, same rate-limited provider beyond its budget, same lock.

If all three hold → concurrent. If any fails → serial, and **the plan must say which one failed**.

**Coupling test (should they, given they may?)** — from the orchestrator-worker boundary condition:
- **Loosely coupled + breadth-first + independently valuable** → parallelize; the token multiplier buys coverage.
- **Tightly coupled / sequential / needs shared evolving context** → keep serial; parallelism costs more *and* is less reliable.

**Collapse test (merge two nodes?)** — collapse when *all* hold: they share the same context, the boundary buys no independent verification, and neither is a rigor gate. **Never collapse across a gate.**

**Promote test (split a node out?)** — promote when *any* holds: it carries independent risk; it needs its own budget or tier; it is a verification gate hiding inside an implementation step; it is the reusable part of several nodes.

## The termination obligation (loop engineering)

Any cyclic node **must** declare four things:

| Field | What it is | Failure if absent |
|---|---|---|
| **Variant** | the quantity that strictly decreases each iteration | no reason it ever ends — "hoped to terminate" |
| **Well-founded floor** | the bottom of the order (e.g. 0 for ℕ) | descent could continue forever |
| **Exit condition** | the state predicate routing to done | the loop stops only by running out |
| **Budget cap** | circuit breaker (iterations / tokens / wall-clock) | a bug becomes a runaway |

**Invariant:** the cap is *not* the termination argument. **If the cap fires, that is a defect signal, not a resource signal** — it means the variant was wrong or the exit condition was never reachable.

**Common agent variants that actually work:**
- *bounded worklist* — items remaining (strictly decreases; floor 0)
- *unresolved-findings count* — must decrease per pass, else stop and escalate
- *residual error / distance to target* — decreases by a stated minimum delta, else stop (a non-decreasing pass is the exit)
- *lexicographic* `(open_gates, unresolved_findings, iterations)` for nested loops

**Anti-shape:** "keep refining until it's good." No variant, no floor, no exit — this is the pack's *Unbounded Reflection Loop* (LOA Appendix C) and it is rejected, not scored.

## Fan-out contract (what a parallel node must specify)

1. **Width cap** — max concurrent branches (never unbounded).
2. **Transient-failure policy** — retry with backoff; which errors are transient (429/529/timeout) vs terminal.
3. **Per-branch exit condition** — how a single branch knows it is done.
4. **Join rule** — all-must-succeed / quorum / best-effort-with-report; and **what the join does with a partial result**.
5. **Failure containment** — does one branch failing fail the whole node? (In the measured C1 case, it did, and should not have.)

## Cost model inputs (for the cost-vs-delivery ledger)

Per node, estimate and later record: **context tokens loaded**, **output tokens**, **tool round-trips**, **wall-clock**, **tier** (T0 deterministic … T3 frontier). The dominant term in agent work is usually *context loaded*, not output generated — so **a removed node saves its own cost plus its output's presence in every downstream context**.

Deterministic (T0) nodes are ~free and fully reproducible: **prefer them wherever they would do** (LOA P1/P2). Promoting a model node to a deterministic node is the single best cost *and* determinism move available.

## Boundary set (what a planner must handle)

Single-step prompt (the graph is one node — say so and stop) · a prompt whose real dependencies are unknown until work starts (exploratory: plan to a checkpoint, then replan) · a prompt with a hidden cycle (A needs B needs A — must be broken with an explicit ordering or an approximation) · a fan-out over an unbounded collection (must be capped or batched) · a fan-out against a rate-limited provider (needs backpressure) · a "do everything" prompt with no exit condition · a node that is a rigor gate (immovable) · a cost budget that is exhausted mid-plan (degrade gracefully, never silently drop a gate) · a plan whose optimized form is *identical* to the naive form (a legitimate and common outcome — report it) · a prompt so small that planning costs more than executing (**do not plan; execute**).

## The floors an optimizer may never lower

These are **inputs**, not variables. Reordering is allowed; removal is not.

- Tier-appropriate persona review and every **hard veto** in scope (`persona-audit.md` §8.4/§8.7).
- The **Testing Strategy** trigger-table union for the code shape touched.
- The **end-to-end surface list** for a data-carrying change (E7) and the reader trace (E8/DM15).
- **Red-first observation** for any claimed control (CI6).
- The **audit + change log** entries (AL5, CL1).
- The **no-guessing** obligations — check, mark, or ask (NG1).

A plan that reaches its cost target by removing one of these is **rejected**, not scored.
