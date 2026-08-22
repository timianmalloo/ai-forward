---
id: kb-graph-and-loop-engineering-data
title: "Graph & loop engineering — Data & constants"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [data, constants, benchmarks, token-cost, defaults, fleet-measurements]
links:
  - { to: kb-graph-and-loop-engineering, rel: refines }
review-by: "2026-11-20"
summary: >-
  The numbers — published benchmark results (LLMCompiler, orchestrator-worker, MAST failure rates),
  framework defaults (LangGraph recursion_limit 25), 2026 cost ranges, and the measurements taken
  from this fleet's own 750 committed audit entries — each with its confidence label and a currency
  warning on the fast-moving ones.
---

# Data & constants

## Published benchmark results

| Measure | Value | Source | Confidence |
|---|---|---|---|
| LLMCompiler latency speedup vs sequential | **up to 3.7x** | ICML 2024, arXiv:2312.04511 | Verified |
| LLMCompiler cost reduction | **up to 6.7x** | same | Verified |
| LLMCompiler accuracy improvement | **up to ~9%** | same | Verified |
| LLMCompiler, 2-way-parallel HotpotQA task | **1.8x** | same | Verified |
| Orchestrator-worker uplift vs single agent | **+90.2%** (internal research eval) | Anthropic multi-agent writeup | Flagged (vendor-reported) |
| Orchestrator-worker token multiplier | **~15x** a chat | same | Flagged (vendor-reported) |
| Share of performance variance explained by token spend | **~80%** | same | Flagged (vendor-reported) |
| Typical subagent fan-out | **3–15** | same | Flagged |
| MAST failure modes / categories | **14 modes, 3 categories** | arXiv:2503.13657 | Verified |
| MAST traces analysed | **200+ across 7 frameworks** | same | Verified |
| MAST observed failure rates | **41–86.7%** (system/benchmark dependent) | same | Verified |
| Multi-agent topologies degrading plan quality | **39–70%** | 2026 study via practitioner coverage | **Flagged — secondary, primary not read** |

## Framework defaults

| Constant | Value | Note |
|---|---|---|
| LangGraph `recursion_limit` | **25** | raises `GraphRecursionError`; a *circuit breaker*, not a termination proof |
| Hitting the cap at exactly the default | diagnostic | signature of a **missing/broken exit condition**, not of needing more steps |
| Failing only at large input | diagnostic | step count scales with input → batch or fan out instead of raising the cap |

## 2026 cost ranges — **Flagged, re-establish before relying on them**

| Quantity | Reported range |
|---|---|
| Agentic coding task, per task | **$0.03 – $2.60** (commonly $0.03–$0.13) |
| Tokens per agentic coding task | **~33,000 – 188,000** |
| Multi-agent token multiplier | **5 – 30x** single-agent |
| Repeat-context cost reduction from prompt caching | **up to ~90%** |
| Dominant cost component | **context overhead**, not generated output |

*These are practitioner/vendor figures from 2026 blog material of variable authority; model pricing and ratios move monthly. Treat the **shape** as sound and any **specific number** as needing re-verification at time of use (NG3).*

## Measurements from this fleet (Verified — our own committed logs)

Source: `docs/audit/audit-log.jsonl` in `TheTerrace`, `meridian-finance-planner`, `HealthWatch`, read 2026-08-22.

| Measure | Value |
|---|---|
| Total audit entries analysed | **750** (372 Terrace + 320 meridian + 58 HealthWatch) |
| Entries that are multi-step work (≥2 artifacts) | **481 / 750 = 64%** |
| Entries that are single-step | **269 / 750 = 36%** |
| Multi-entry sessions | **53** |
| Mean session elapsed | **3,299 min (~55 h)** |
| Median session elapsed | **1,253 min (~21 h)** |

> **Integrity note — do not misuse the session timings.** A `session` id persists across hours or days of human-paced work, so **session elapsed time is not the execution time of a prompt.** It includes the human being away. Any per-prompt duration in this knowledge base or in a back-test is therefore a **modeled estimate from graph structure**, never a measurement. The *structural* facts (step counts, artifact counts, outcomes, dependency shape) **are** measurements. Conflating the two would be exactly the RIG-E "it works, therefore it conforms" error.

### Named fleet instances (the evidence behind the rules)

| Ref | Repo / id | Fact | Rule it justifies |
|---|---|---|---|
| C1 | meridian `al-0058` | 5 parallel Claude calls, no retry → 429/529 failed the **whole** panel; fixed with **concurrency cap 2 + backoff** | fan-out needs a width cap + transient-failure policy |
| C2 | HealthWatch `al-0003` | **10 parallel research tracks** → 4 knowledge bases, success | wide fan-out works when branches are genuinely independent |
| C3 | meridian `al-0124` | specify→design→implement chain for 2 independent FRs; **vacuous test** caught late | independent features are branches; verification nodes need an oracle |
| C4 | HealthWatch `al-0022` | **three defects on three layers** found serially; per-row writer would have taken **12+h**, fixed path ran in **3m07s** | probe independent layers concurrently against one fixture |
| C5 | meridian `al-0310` | ~14 FRs fanned out; 4 open, 4 partial, needed a backlog addendum | fan-out needs per-branch exit conditions + a completeness join |
| C6 | Terrace `al-0012` | "build **every slice**" → outcome partial, "remains in review behind gates" | unbounded goals need explicit gate nodes with clearing conditions |

## Working defaults this pack adopts (Inferred — our synthesis, tune with evidence)

| Default | Value | Basis |
|---|---|---|
| Max fan-out width without explicit justification | **4** | C1 failed at 5 unbounded; keep headroom under provider limits |
| Fan-out transient-retry policy | retry 429/529/timeout, exponential backoff, ≥2 attempts | C1's own fix |
| Default loop iteration cap (circuit breaker) | **5** for refinement loops; **3** for verification retries | far below LangGraph's 25; a firing cap is a defect signal |
| Planning threshold | skip planning when the graph is **1–2 nodes** with no loop and no gate | planning must not cost more than the work |
| Re-plan checkpoint | after any node whose result **changes the shape** of remaining work | LOA Archetype H |
