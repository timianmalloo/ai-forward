---
id: kb-graph-and-loop-engineering-sota
title: "Graph & loop engineering — State of the Art"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [dag, scheduling, critical-path, termination, parallel-function-calling, orchestrator-worker]
links:
  - { to: kb-graph-and-loop-engineering, rel: refines }
review-by: "2026-11-20"
summary: >-
  Current best practice across the three joined literatures — DAG scheduling and the work/span
  bound, agentic parallel planning (LLMCompiler, orchestrator-worker, the five Anthropic workflow
  patterns), loop termination via ranking functions, and the compiler loop-transformation tradition
  — with what each contributes to planning an agent's execution graph.
---

# State of the art

## 1. Graph engineering — the DAG and its bounds

The settled model is a **directed acyclic graph** where nodes are tasks and edges are dependencies. Three quantities govern everything:

| Quantity | Meaning | Why it matters to a plan |
|---|---|---|
| **Work `T₁`** | total cost if run sequentially | the cost you pay if you parallelize nothing |
| **Span `T∞`** | longest dependency chain (critical path) | the floor — **the fastest the graph can possibly go** |
| **`Tₚ`** | cost on `p` workers | bounded by Brent: `Tₚ ≤ (T₁ − T∞)/p + T∞` |

**Parallelism** is `T₁/T∞` — the average width of the graph, and the point past which more workers buy nothing. **Amdahl's law** gives the same message from the other direction: with a sequential fraction `σ`, speedup is capped at `p / (1 + σ(p−1))`, tending to `1/σ`. A plan with a long thin critical path is *not fixable by concurrency*; it is fixable only by making the chain shorter.

**Task granularity** is the classical trade-off: fine-grained exposes parallelism but pays scheduling and communication overhead per task; coarse-grained pays less overhead but under-uses capacity. **DAG scheduling** (list scheduling, HEFT for heterogeneous workers, work-stealing as in Cilk) assigns ready tasks to workers to minimize makespan while honouring dependencies.

*(Verified. Standard parallel-computing material; see `sources.md`.)*

## 2. Agentic graph engineering — the same theory, re-derived

**LLMCompiler** (ICML 2024) is the clearest instance: a **Function Calling Planner** parses the task into a DAG, a **Task Fetching Unit** dispatches tasks whose dependencies are satisfied, and an **Executor** runs each wave in parallel. Measured against sequential ReAct-style execution: **up to 3.7x latency speedup, up to 6.7x cost reduction, up to ~9% accuracy improvement**. A simple 2-way-parallel HotpotQA task shows 1.8x; the speedup scales with the graph's width.

**Anthropic's five workflow patterns** (from *Building Effective Agents*) are the practitioner vocabulary and map one-to-one onto graph shapes:

| Pattern | Graph shape | Cost/latency note |
|---|---|---|
| **Prompt chaining** | a path | latency adds per step; the span *is* the chain |
| **Routing** | a switch node | classify once, then specialize |
| **Parallelization** (sectioning / voting) | a fan-out/fan-in | lower latency, higher concurrent resource use |
| **Orchestrator–workers** | dynamic fan-out | scales to open-ended work; coordination cost |
| **Evaluator–optimizer** | a **cycle** | quality gain per loop, cost and latency per loop |

The published advice is to start with the simplest pattern that works and add complexity only when it earns its place — the same instinct as the pack's Solution-Selection Ladder.

**Orchestrator-worker at production scale:** Anthropic's multi-agent research system runs a lead agent with 3–15 parallel subagents holding isolated context windows, reporting **90.2% improvement over single-agent** on internal research evals at **~15x chat token usage**, with token spend explaining **~80% of performance variance**. The stated boundary condition is decisive: this shape suits **open-ended, breadth-first, loosely-coupled** work, and is the *wrong* choice for tightly-coupled or strictly sequential tasks, where coordination overhead makes a single agent cheaper and more reliable.

*(Verified on mechanism and direction; the specific vendor-reported percentages are Flagged.)*

## 3. Loop engineering — termination is a proof, not a limit

The formal position has been stable since Floyd (1967) and is standard Hoare-logic material:

- **Partial correctness**: if it terminates, the answer is right.
- **Total correctness**: partial correctness **plus** termination. These are *separate obligations*.
- Termination is proved by exhibiting a **variant** / **ranking function** — a map from program state into a **well-founded order** (no infinite descending chain, e.g. ℕ under `<`) whose value **strictly decreases every iteration**. Because the order is well-founded, it cannot descend forever, so the loop must stop.
- Automated tooling synthesises these with SMT solvers — linear ranking functions, **lexicographic** combinations for nested/multi-variable loops, ordinal or multiset ranks for harder cases.

**What agent frameworks actually ship** is the weak substitute: a **step cap**. LangGraph enforces `recursion_limit` (default **25**) and raises `GraphRecursionError`. Its own documentation is explicit that this is a safety net, not a design: always include explicit state-based exit conditions routing to `END`; do not raise the limit without a solid exit condition; and **hitting the cap immediately (at exactly the default) usually means a missing or broken exit condition**, whereas failing only on large inputs means step count scales with input and the work should be batched or fanned out instead.

The practical synthesis for agent work: **a cap answers "how do I stop a runaway?"; a variant answers "why will this ever finish?"** A responsible loop has both, and they play different roles — the variant is the design, the cap is the circuit breaker whose firing is a *defect signal*.

*(Verified.)*

## 4. Graph optimization — transformations worth stealing

From the compiler tradition, the loop transformations that have direct agent analogues:

| Transformation | Compiler meaning | Agent analogue |
|---|---|---|
| **Loop-invariant code motion** | hoist work that does not change per iteration | ground/load context **once** outside the loop, not per iteration |
| **Fusion** | merge two loops over the same range | one pass over the files, not one pass per concern |
| **Fission** | split a loop so parts can vectorize | separate the parallelizable scan from the serial decision |
| **Unrolling** | reduce per-iteration overhead | batch N items per call instead of one call per item |
| **Strength reduction** | replace an expensive op with a cheap one | replace a model call with a deterministic check (LOA P2) |
| **Dead-code elimination** | drop work nothing consumes | drop a step whose output no downstream node reads |
| **Common-subexpression elimination** | compute once, reuse | one authoritative producer per quantity (DM7) |

**Speculative execution** (run cheap and expensive in parallel, commit the cheap result if confident) is already in the pack as LOA Pattern 1.6, with the standing warning that it is only cost-neutral if cancellation actually propagates.

*(Verified on the transformations; Inferred on the agent mappings, which are our synthesis.)*

## 5. Where the frontier is (2026)

- **Planning quality under decomposition is contested.** Practitioner coverage cites a 2026 study in which *every* tested multi-agent topology degraded plan quality by 39–70% versus a single coherent planner — the strongest available counter-argument to reflexive decomposition. *(Flagged — secondary citation.)*
- **Context is the cost centre, not generation.** Per-task agent cost is dominated by context overhead; caching repeat context is the biggest single lever; "context rot" degrades accuracy as well as cost. *(Flagged — practitioner sourcing.)*
- **Failure is structural.** MAST's finding that failures cluster in specification, inter-agent misalignment, and verification — not raw capability — is the strongest argument that *planning the graph* is a correctness intervention, not merely a performance one. *(Verified.)*
