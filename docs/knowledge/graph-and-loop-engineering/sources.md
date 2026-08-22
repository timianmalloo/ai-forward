---
id: kb-graph-and-loop-engineering-sources
title: "Graph & loop engineering — Sources"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [sources, citations, currency]
links:
  - { to: kb-graph-and-loop-engineering, rel: refines }
review-by: "2026-11-20"
summary: >-
  Full source list with access dates and confidence labels — primary papers (LLMCompiler, MAST),
  framework documentation (LangGraph), vendor engineering writeups (Anthropic), classical
  parallel-computing and termination theory, this fleet's own committed audit logs, and the in-pack
  standards this base composes with — plus the currency warning on the fast-moving material.
---

# Sources

**All web sources accessed 2026-08-22** unless noted. Ordered by the source-of-truth hierarchy (BoK §III.1): primary/peer-reviewed → official docs → vendor engineering → practitioner secondary.

## Primary / peer-reviewed

| Source | Used for | Confidence |
|---|---|---|
| **An LLM Compiler for Parallel Function Calling** — Kim et al., ICML 2024, arXiv:2312.04511 · `proceedings.mlr.press/v235/kim24y.html` · code `github.com/SqueezeAILab/LLMCompiler` | the DAG planner / task-fetching / executor architecture; 3.7x latency, 6.7x cost, ~9% accuracy, 1.8x on a 2-way task | **Verified** |
| **Why Do Multi-Agent LLM Systems Fail?** (MAST) — UC Berkeley Sky Computing, arXiv:2503.13657 · `sites.google.com/berkeley.edu/mast` | 14 failure modes in 3 categories; 200+ traces / 7 frameworks; 41–86.7% failure rates | **Verified** |
| **Floyd–Hoare termination theory** — loop variant / ranking function over a well-founded order; total vs partial correctness. Stanford termination-analysis notes (`theory.stanford.edu/~arbrad/slides/termination.pdf`); NYU decision-procedures notes; `en.wikipedia.org/wiki/Loop_variant` | the termination obligation; lexicographic and linear ranking functions | **Verified** |
| **Classical parallel computing** — work/span model, Brent's theorem, critical path, Amdahl's law, task granularity (`downey.io` work-span notes; `theartofhpc.com/istc/parallel.html`) | `Tₚ ≤ (T₁−T∞)/p + T∞`; parallelism `T₁/T∞`; the granularity trade-off | **Verified** |

## Official framework documentation

| Source | Used for | Confidence |
|---|---|---|
| **LangGraph — `GRAPH_RECURSION_LIMIT` / `GraphRecursionError`** · `docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT` · `reference.langchain.com/python/langgraph/errors/GraphRecursionError` | default limit **25**; the cap-is-not-termination guidance; the "hit at exactly the default = broken exit condition" diagnostic; `Send` fan-out for input-scaled step counts | **Verified** |

## Vendor engineering writeups

| Source | Used for | Confidence |
|---|---|---|
| **Anthropic — Building Effective Agents** + Claude Cookbooks agent patterns (`github.com/anthropics/claude-cookbooks/tree/main/patterns/agents`) | the five workflow patterns (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer) and the start-simple guidance | **Verified** (patterns are stable and widely replicated) |
| **Anthropic — How we built our multi-agent research system** (`anthropic.com/research/how-we-built-our-multi-agent-research-system`) | orchestrator-worker at production scale; 3–15 subagents; +90.2%; ~15x tokens; ~80% variance explained; the loosely-coupled boundary condition | **Flagged on figures** (vendor-reported internal eval, not independently replicated); Verified on architecture and boundary condition |

## Practitioner / secondary — used for framing only

| Source | Used for | Confidence |
|---|---|---|
| 2026 agent cost-accounting material (`agentmarketcap.ai`, `kunalganglani.com`, `explainx.ai`, `niteagent.com`, `cipherbuilds.ai`, `academy.kspl.tech`) | per-task $0.03–$2.60; 33k–188k tokens; 5–30x multi-agent multiplier; ~90% caching saving; context rot | **Flagged** — variable authority, fast-moving; re-establish before load-bearing use |
| DAG-orchestration practitioner coverage (`particula.tech`) | fan-out/fan-in cutting wall-clock 36–50% in production; the 39–70% plan-quality degradation citation | **Flagged** — secondary; the 39–70% primary was **not** read |

## In-fleet primary evidence (our own committed logs)

| Source | Used for | Confidence |
|---|---|---|
| `TheTerrace/docs/audit/audit-log.jsonl` (372 entries) · `meridian-finance-planner/docs/audit/audit-log.jsonl` (320) · `HealthWatch/docs/audit/audit-log.jsonl` (58) — read 2026-08-22 | 750 entries; 481 multi-step (64%); 53 multi-entry sessions; the six named instances C1–C6 | **Verified** (primary, committed, quoted verbatim in `comparables.md`) |

> **Integrity caveat carried forward:** session elapsed times in these logs (mean ~55 h, median ~21 h) span human-paced work across days and **are not** prompt execution times. Structural facts from the logs are measurements; any duration is a modeled estimate.

## In-pack standards this base composes with

`layered-optimized-architecture.md` (Archetypes A/B/E/H; Patterns 1.1–1.7, 2.4, 3.5, 3.6, 5.3, 6.1, 6.5; the *Unbounded Loop* and *Unbounded Reflection Loop* anti-patterns) · `ci-and-test-efficiency.md` (CE1–CE3 profile-first, CE16 contention, CE22 no coverage-for-speed trade) · `solution-selection-ladder.md` (smallest correct; the `simplify:` marker) · `rigor-protocol.md` (the five stages the plan must still traverse) · `end-to-end-integrity.md` (E7 surface list, E11 prove the surface, E13 gate contents) · `continuous-improvement.md` (CI2 class→sweep→derive→prevent; CI6 the control ladder) · `agent-rules-of-the-road.md` §0.2 (tiers) · `persona-audit.md` §8.4/§8.7 (veto predicates and convene triggers) · `testing-strategy.md` (the trigger-table union) · `domain-and-data-modelling.md` (DM7 derive-don't-store, DM17 name things once).

## Currency

- **Fast-moving (re-check at review-by):** all 2026 cost figures; the Anthropic multi-agent numbers; LangGraph defaults; the plan-quality-degradation claim.
- **Stable:** work/span and Brent's bound, Amdahl, Floyd–Hoare termination, the granularity trade-off, the compiler loop transformations, MAST's taxonomy.
- **Ours and re-derivable:** the fleet measurements — re-run the same audit-log analysis to refresh.
