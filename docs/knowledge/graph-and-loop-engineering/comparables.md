---
id: kb-graph-and-loop-engineering-comparables
title: "Graph & loop engineering — Comparables"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [comparables, langgraph, llmcompiler, airflow, temporal, dspy, in-repo-evidence]
links:
  - { to: kb-graph-and-loop-engineering, rel: refines }
review-by: "2026-11-20"
summary: >-
  How existing systems frame and solve execution-graph planning — workflow engines (Airflow,
  Temporal, Dagster), agent frameworks (LangGraph, LLMCompiler, orchestrator-worker), and compiler
  approaches (DSPy) — plus the in-fleet evidence from TheTerrace, meridian and HealthWatch audit
  logs, including a measured unbounded-fan-out failure and a measured successful parallel run.
---

# Comparables

## External systems

| System | How it frames the problem | Does well | Does badly / limits |
|---|---|---|---|
| **Apache Airflow** | a DAG of operators, statically declared, scheduled | mature dependency semantics, retries, backfill, observability | the DAG is static; ill-suited to dependencies discovered at runtime |
| **Temporal** | durable execution; workflow code *is* the graph, with deterministic replay | crash-safety, exactly-once activities, long-running workflows | requires determinism in workflow code; heavy runtime |
| **Dagster / Prefect** | asset/task graphs with typed data dependencies | data-aware edges; the dependency is the *asset*, not the call | infrastructure weight for a planning problem |
| **LangGraph** | stateful **cyclic** graph of nodes; cycles are the point (agent loops) | supports the think→act→observe loop; checkpointing; `Send` fan-out | termination is a **cap** (`recursion_limit`, default 25), not a proof; easy to build a graph that only stops because it ran out |
| **LLMCompiler** | plan a DAG of function calls, dispatch independent ones in waves | measured 3.7x latency / 6.7x cost / ~9% accuracy vs sequential | needs the task to be decomposable up front; a planner error costs a whole wave |
| **Orchestrator–worker (Anthropic)** | lead agent decomposes; parallel subagents with isolated context | +90.2% on open-ended research; scales breadth | ~15x tokens; explicitly wrong for tightly-coupled/sequential work |
| **DSPy** | *compile* the pipeline: optimize prompts/structure against a metric | treats the pipeline as optimizable with a measured objective | needs a metric and a training set — most real tasks have neither |

**The gap all of them leave for us:** every one is a *runtime* (or a compiler for one). None of them is a **pre-execution planning discipline** that a general coding agent applies to an arbitrary natural-language prompt, in committed Markdown, with the rigor floors treated as immovable nodes. That is the niche `/optimize-graph` occupies — and it means we borrow the *theory* (span, waves, coupling, termination) without importing a runtime, consistent with the pack's dependency-averse identity.

---

## In-fleet evidence (the strongest comparables, because they are ours and they are measured)

Mined from the committed audit logs of `TheTerrace` (372 entries), `meridian-finance-planner` (320) and `HealthWatch` (58) — 750 entries total. **481 of 750 (64%) are multi-step work** (≥2 artifacts), which is the population an execution-graph plan applies to.

### C1 — Unbounded fan-out with no backpressure (a measured runaway)
> **meridian `al-0058`** (2026-07-24, `/investigate`, outcome success)
> *Prompt:* "the AI advisors still are problematic (panel of specialists captured an error report instead of working)"
> *Summary:* "Root cause: **5 parallel Claude calls + no retry tripped 429/529 and failed the whole panel.** Fix: **concurrency cap 2 + transient retry-with-backoff** + broadened catch + accurate failure reason. +2 tests; API deployed"

This is the canonical case for the rule **"bound the fan-out and pair it with backpressure."** Parallelism was correctly identified as the right shape (five independent specialist opinions) and then implemented without a concurrency cap or retry, so the *whole* panel failed. The fix is exactly what a fan-out node's contract should have specified up front: a width cap and a transient-failure policy. **Confidence: Verified** (in-repo, root-caused, tests added).

### C2 — A successful wide parallel research fan-out (the positive control)
> **HealthWatch `al-0003`** (2026-08-16, `/collectknowledge`, outcome success)
> *Summary:* "Built four sourced, confidence-labeled knowledge bases in docs/knowledge/ from **10 parallel research tracks** (4 repo-mining, 6 primary-source web)…"

Ten genuinely independent tracks (four repo-mining, six web) fanned out and joined into four knowledge bases. This is the shape LLMCompiler and orchestrator-worker predict works: breadth-first, loosely coupled, high-value. **Confidence: Verified.**

### C3 — Serial phase chain where the phases were partly independent
> **meridian `al-0124`** (2026-07-29, `/implement`, outcome **partial**)
> *Summary:* "**Ran specify then design then implement** for FR-127 and FR-128, both found by the owner in use… **Caught a vacuous test:** the first accumulation oracle stayed green with contributions zeroed because a 5 percent return makes the median rise on its own — now differential. FR-088's gate caught LifecycleModel.cs missing from architecture.md…"

Two features (FR-127, FR-128) each taken through a three-phase chain. The critical path is genuinely long *per feature* — but the two features are largely independent, so the span could have been shortened by treating them as parallel branches sharing one design pass. Note also the **vacuous test** found late: a verification node that passed while proving nothing (the pack's Coverage-Theater / Mock-Fiction shape) — evidence that verification nodes need their own *oracle* declared, which is a graph-planning obligation. **Confidence: Verified.**

### C4 — Three independent defects discovered serially inside one investigation
> **HealthWatch `al-0022`** (2026-08-17, `/investigate`, outcome success)
> *Summary:* "**Three defects:** FormOptions 128MB multipart default rejected the 348MB zip (WIRE-LIMIT-A); 4GB expansion cap under the real 6.7GB export.xml; per-row SampleWriter would take **12+h** for 8.6M drafts (SCALE-SHAPE-A). Fixed: FormOptions=500MB + honest 413, cap 16GB, OPENJSON set-based writer… Proof: real 6.7GB archive parsed+landed locally in **3m07s**; 196/196 suite green"

Three defects on **three different layers** (wire limit, expansion cap, write path), each blocking the next discovery. Because they were found one at a time, the investigation is a chain of length three; because they are on independent layers, a planned graph would have probed all three layers concurrently against the one real 6.7GB fixture. **This is the clearest "serialization that the dependencies did not require" case in the fleet.** **Confidence: Verified.**

### C5 — Large fan-out delivered partially
> **meridian `al-0310`** (2026-08-15, `/implement`, outcome **partial**, 22 artifacts)
> *Prompt:* "re-ground yourself in the repo then do all the next items enumerated above From FR-291 all the way to FR-289"
> *Summary:* "Implemented the verified slices from FR-287/288 and FR-291-FR-300… **FR-289, FR-295, FR-298, FR-299 remain open by design; FR-291/294/296/297 are partial** as recorded in the backlog addendum."

A wide fan-out over ~14 FRs with no declared per-item exit condition, producing a mixed result that needed a backlog addendum to reconcile. The graph lesson is not "don't fan out" — it is that **a fan-out node needs a per-branch completion contract**, or the join cannot tell done from partial. Maps directly onto MAST's *task verification* failure category. **Confidence: Verified.**

### C6 — Gated architecture pass (an unbounded scope, stopped by review)
> **TheTerrace `al-0012`** (2026-07-22, `/define-architecture`, outcome **partial**)
> *Summary:* "Defined the complete .NET 10/Azure modular-monolith architecture, six proposed ADRs, contract-spike ledger… **Architecture remains in review behind explicit cloud/provider/privacy/test gates.**"

The prompt asked for "a detailed strategy for autonomously building **every slice**" — an unbounded goal. The work stopped at review gates rather than at a declared exit condition. A planned graph would have made the gates explicit nodes with named clearing conditions, converting "remains in review" into "blocked on gate G3: privacy basis." **Confidence: Verified.**

---

## What the in-fleet evidence changes about the design

1. The failure mode we actually hit is **unbounded fan-out without backpressure** (C1) — so a fan-out node's contract must include width and a transient-failure policy, not just "these are independent."
2. The waste we actually pay is **serial discovery of independent problems** (C3, C4) — so the highest-value single question is "are these dependencies real, or incidental?"
3. The completeness risk is **joins that cannot distinguish done from partial** (C5) — so every fan-out needs a per-branch exit condition and the join needs a completeness check.
4. Verification nodes can **pass while proving nothing** (C3's vacuous test) — so a verification node must declare its oracle, exactly as the Test Architect requires.
