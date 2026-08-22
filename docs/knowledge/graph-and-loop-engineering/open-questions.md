---
id: kb-graph-and-loop-engineering-open-questions
title: "Graph & loop engineering — Open questions & failure modes"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [open-questions, risks, failure-modes, disconfirming-evidence]
links:
  - { to: kb-graph-and-loop-engineering, rel: refines }
review-by: "2026-11-20"
summary: >-
  What the research could not settle, the disconfirming evidence against graph optimization, and the
  domain's known failure modes — including the ones that argue against decomposition and parallelism
  and the ones that would make an optimizer actively harmful if ignored.
---

# Open questions & failure modes

## Disconfirming evidence (sought deliberately — Stage 4)

The strongest arguments **against** what this base recommends. They are recorded here because a base that only gathered confirming sources would be worthless.

1. **Decomposition may degrade plan quality outright.** Practitioner coverage cites a 2026 study in which **every tested multi-agent topology degraded plan quality by 39–70%** versus a single coherent planner. If that result holds generally, aggressive decomposition is *harmful*, and the correct default is one coherent worker with an explicit plan rather than many workers. **We could not read the primary source. Flagged.** *Mitigation adopted:* `/optimize-graph` plans the graph but does **not** mandate multi-agent execution — a single agent executing a well-ordered plan gets the span and determinism benefits with none of the decomposition risk.

2. **Decomposition creates the second-largest failure category.** MAST's **inter-agent misalignment** (ignored input, withheld information, derailed handoff) exists *only because* work was split. Every boundary is a place to lose information. **Verified.** *Mitigation:* the collapse test is as first-class as the promote test, and boundaries must be justified.

3. **The orchestrator-worker uplift is vendor-reported and expensive.** +90.2% at ~15x tokens comes from Anthropic's own internal evaluation on their own product, not an independent benchmark. **Flagged.** *Mitigation:* treat the direction as sound and the magnitude as unproven; require the coupling test before paying the multiplier.

4. **The graph is often not knowable up front.** Genuinely exploratory work discovers its dependencies by doing the work; a fixed up-front DAG is wrong for it and can lock in a bad decomposition. **Verified by construction.** *Mitigation:* plan to the next checkpoint and re-plan, per LOA Archetype H — never a frozen DAG.

5. **Planning has its own cost.** For a small prompt, the plan can cost more than the work. **Verified by inspection** — 36% of this fleet's 750 audit entries are single-step. *Mitigation:* an explicit skip threshold (1–2 nodes, no loop, no gate → execute, do not plan).

## Open questions (unsettled)

| # | Question | Why it is open | How we would settle it |
|---|---|---|---|
| Q1 | What is the *real* per-node overhead for an agent task in this fleet? | We have no per-node token or wall-clock instrumentation; session timings are human-paced and unusable as duration (see `data-and-constants.md`) | Instrument `/optimize-graph` runs: record planned vs actual nodes, tokens where the runner exposes them, and rework passes; after ~20 runs the granularity optimum is measurable rather than assumed |
| Q2 | Does the plan itself improve outcomes, independent of parallelism? | MAST says specification failures dominate, which predicts yes — but we have not isolated it | Run matched pairs: same prompt class with and without a declared graph; compare rework passes and partial outcomes |
| Q3 | What is the right fan-out width for *this* fleet's providers? | C1 failed at 5 unbounded; the safe width depends on provider limits we have not measured | Record 429/529 incidence against observed width; the default of 4 is a guess with a rationale, not a measurement |
| Q4 | Can "completeness" be measured rather than asserted? | Our proxies (outcome field, open/partial items, rework passes) are indirect | Define completeness as *declared exit conditions met at the join*; then it is countable per plan |
| Q5 | Does collapsing nodes reduce or increase defects? | Fewer boundaries means less handoff loss (MAST) but also fewer verification points | Track defects found per boundary against boundaries removed |
| Q6 | How stable are the 2026 cost ratios? | Vendor pricing and multipliers move monthly | Re-establish at each review-by; never let a specific number become load-bearing (NG3) |

## Known failure modes of the domain

*The things that go wrong when you optimize an execution graph. Several are already registered pack defect classes; the fleet reference is the instance we actually hit.*

| Failure mode | Shape | Fleet ref | Guard |
|---|---|---|---|
| **Unbounded fan-out** | N concurrent calls with no width cap or retry; one transient error fails the whole node | **C1** (meridian `al-0058`, 429/529) | width cap + transient-retry policy + failure containment |
| **Parallelism on top of contention** | widening a graph whose nodes contend on one resource — slower *and* costlier | `ci-and-test-efficiency.md` CE3/CE16 | measure isolation vs load before widening |
| **Hunch optimization** | reshaping the step you *assumed* was expensive | CE1, BoK Part VIII | profile first; a plan without a measured bottleneck is a hunch |
| **Runaway loop** | a cap but no variant; stops only by exhaustion | LOA *Unbounded Reflection Loop* | declare the variant; a firing cap is a defect signal |
| **Join that cannot see partial** | fan-out completes "successfully" with branches open | **C5** (meridian `al-0310`) | per-branch exit condition + completeness check at the join |
| **Vacuous verification** | a gate that passes while proving nothing | **C3** (meridian `al-0124`, vacuous test) | every verification node declares its oracle (what would fail it) |
| **Gate dropped for speed** | the optimizer hits its budget by removing a rigor node | — | floors are inputs; such a plan is rejected, not scored |
| **Serial discovery of independent problems** | three independent layers probed one at a time | **C4** (HealthWatch `al-0022`) | test the edges: is this a real dependency or incidental ordering? |
| **Unbounded goal** | "build every slice" — no exit condition, ends in review | **C6** (Terrace `al-0012`) | gates as explicit nodes with named clearing conditions |
| **Over-decomposition** | boundaries that lose more than they buy | MAST inter-agent misalignment | the collapse test, applied as seriously as promote |
| **Plan-cost inversion** | planning a task smaller than the plan | 36% of fleet entries are single-step | skip threshold |
| **False determinism** | a plan claimed reproducible whose nodes are order-dependent | `PACK-I` (unsorted directory walk) | fixed ordering; deterministic tier where possible |

## What would change the recommendations

- A **primary-source** replication of the 39–70% plan-quality degradation finding would materially weaken the case for any decomposition and strengthen "one coherent worker, explicit plan."
- Per-node instrumentation showing agent overhead is *small* would move the granularity optimum finer and make collapse less valuable.
- Evidence that declared exit conditions do **not** reduce partial outcomes would undercut design implication #6 (the completeness join).
