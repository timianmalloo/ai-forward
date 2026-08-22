---
id: kb-graph-and-loop-engineering-glossary
title: "Graph & loop engineering — Glossary"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [glossary, ubiquitous-language, dag, span, variant, fan-out]
links:
  - { to: kb-graph-and-loop-engineering, rel: refines }
review-by: "2026-11-20"
summary: >-
  The ubiquitous language for execution-graph planning — work, span, critical path, node, edge,
  wave, fan-out/join, collapse/promote, variant, well-founded order, circuit breaker, gate node,
  cost-vs-delivery ledger — for use in the skill, the plans it produces, and any code.
---

# Glossary — ubiquitous language

Use these exact terms in plans, skills, and code. One concept, one name (DM17).

**Execution graph** — the DAG of tasks a prompt requires. Nodes are tasks; edges are real dependencies. The artifact `/optimize-graph` produces.

**Node** — one unit of work with a stated **goal**, **inputs**, **exit condition**, and **tier**. Not "a step I might take" — a thing that can be declared done.

**Edge (dependency)** — a *real* constraint that one node must precede another. Two kinds: a **data edge** (B reads A's output) and a **decision edge** (A's result changes B's *shape*). An edge that is neither is **incidental ordering** and is the main thing optimization removes.

**Incidental ordering** — two nodes written in sequence purely because they were thought of in that order. The most common and cheapest win.

**Work (`T₁`)** — total cost of every node if run one at a time.

**Span (`T∞`) / critical path** — the longest chain of dependent nodes. **The floor on execution time.** Optimize this *before* thinking about width.

**Parallelism (`T₁/T∞`)** — the graph's average width; the point past which more workers buy nothing.

**Wave** — a set of nodes whose dependencies are all satisfied, dispatched together (LLMCompiler's scheduling unit).

**Fan-out** — one node spawning N concurrent branches. Must declare **width cap**, **transient-failure policy**, **per-branch exit condition**, **join rule**, and **failure containment**.

**Join** — where branches recombine. Must state what it does with a **partial** result; a join that cannot tell done from partial is a completeness defect (fleet ref C5).

**Collapse** — merging nodes whose separation buys no independent verification and costs a context load. Never across a gate.

**Promote** — splitting a node out because it carries independent risk, needs its own budget/tier, or is a hidden verification gate.

**Gate node** — a mandatory rigor checkpoint (a persona review, a veto-holder, a required test class, the surface-list check). **Immovable**: the optimizer may reorder it, never remove it.

**Rigor floor** — the set of gate nodes and obligations a plan must contain for its tier. An *input* to optimization, never an output.

**Variant (ranking function)** — the quantity a loop makes **strictly decrease** every iteration, over a well-founded order. **The termination argument.** Without one, a loop is *hoped* to terminate.

**Well-founded order** — an order with no infinite descending chain (e.g. ℕ under `<`). What makes a decreasing variant a *proof*.

**Exit condition** — the state predicate under which a node or loop is done. Distinct from the cap.

**Circuit breaker (cap)** — a hard iteration/token/wall-clock limit. **Not** a termination argument. **A firing cap is a defect signal, not a resource signal.**

**Runaway** — a loop or fan-out that consumes budget without approaching its exit condition. Prevented by the variant; detected by the cap.

**Coupling** — whether two nodes need each other's evolving context. *May* they run in parallel is the **independence** test; *should* they is the **coupling** test.

**Tier (T0–T3)** — the capability tier a node runs at (LOA): T0 deterministic … T3 frontier model. **Prefer the lowest tier that is sufficient.**

**Determinism score** — how reproducible a plan is: the share of nodes that are T0/deterministic, plus the absence of incidental ordering and unbounded loops. A first-class optimization target, not a side effect.

**Cost-vs-delivery ledger** — the record of *planned* vs *actual* (nodes, wall-clock, tokens, rework passes) with whether the completeness and rigor floors were met. What makes the optimizer improvable rather than opinionated.

**Rework pass** — a repetition caused by something the plan should have caught (a late defect, a missing dependency, a vacuous verification). The primary waste signal.

**Vacuous verification** — a check that passes while proving nothing (fleet ref C3). A verification node must declare its **oracle**: what input would make it fail.

**Re-plan checkpoint** — a point where the plan is revised because a result changed the shape of remaining work. Cheap; executing the wrong graph is not.
