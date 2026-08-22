---
id: kb-graph-and-loop-engineering
title: "Graph engineering, loop engineering & graph optimization (domain knowledge)"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "execution-optimization"
tags: [graph-engineering, loop-engineering, graph-optimization, dag, parallelism, critical-path, termination, agent-orchestration, cost-vs-delivery]
links:
  - { to: architecture, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
  - { to: kb-continuous-improvement-and-dreaming, rel: relates-to }
review-by: "2026-11-20"
summary: >-
  Sourced evidence base for planning an agent's work as an explicit dependency graph before
  executing it: the classical work/span and critical-path theory that bounds any possible speedup,
  the termination theory (ranking functions over a well-founded order) that is the only real
  guarantee against runaway loops, the measured agentic results (LLMCompiler 3.7x latency / 6.7x
  cost; Anthropic's orchestrator-worker 90.2% uplift at 15x tokens), and the MAST failure taxonomy
  showing that most multi-agent failure is specification and verification, not model capability.
  Concludes that graph optimization must be a completeness-and-rigor amplifier, never a trade.
---

# Graph engineering, loop engineering & graph optimization — domain knowledge

**Domain & problem:** before an agent executes a prompt, it commits — usually implicitly and usually badly — to an **execution shape**: what runs first, what could have run at the same time, where it loops, when it stops, and how much it is willing to spend. We want to make that shape **explicit, optimized, and bounded** — planned as a dependency graph, scheduled for parallelism where the dependencies allow, collapsed or promoted where the granularity is wrong, guaranteed to terminate, and measured afterwards so the next plan is better. The hard constraint, stated up front because it inverts the usual optimization framing: **this must never trade completeness or rigor for speed.** It exists to *buy* completeness and rigor by spending the same budget better.

**Canonical framing:** the field splits this into three literatures that have never been properly joined for agent work.

1. **Graph engineering / scheduling** — model work as a **DAG** of tasks and dependencies; this is 1950s operations research (Critical Path Method) and 1990s parallel computing (work/span, Brent's theorem), now re-derived for agents by LLMCompiler and every orchestration framework.
2. **Loop engineering / termination** — the formal question "does this halt?", answered since Floyd (1967) by a **ranking function that strictly decreases over a well-founded order**. Agent frameworks have mostly re-invented the *weak* form of this (a step counter) and skipped the strong form.
3. **Graph optimization** — scheduling and transformation to minimize makespan and cost, plus the compiler tradition of loop transformation (fusion, fission, unrolling, invariant hoisting).

Our framing is deliberately narrower than any of them: this is a **planning-discipline problem inside a methodology pack**, not a runtime scheduler. We are not building an orchestration engine. We are making the *plan* — which the agent already forms implicitly — legible, checkable, bounded, and reviewable, in the same committed-Markdown shape as everything else the pack ships.

**Compiled:** 2026-08-22 · **Lead:** Domain Researcher · **Status:** fresh

---

## Headline findings

1. **The DAG is the right model, and the maximum possible speedup is fixed by the graph before any execution begins.** Model work as a directed acyclic graph of tasks; **work** `T₁` is the total sequential cost, **span** `T∞` is the longest dependency chain (the *critical path*), and Brent's theorem bounds execution on `p` workers: `Tₚ ≤ (T₁ − T∞)/p + T∞`. The consequence that matters for planning: **no amount of parallelism can beat the span.** If the critical path is six sequential steps, adding a seventh worker buys nothing — the only remaining lever is *shortening the chain* (collapsing or removing steps), not widening it. Speedup is `T₁/Tₚ`, capped by Amdahl's law at `p / (1 + σ(p−1))` for a sequential fraction `σ`. — *(Verified — work/span and Brent's bound; Amdahl 1967)*

2. **Parallelizing an agent's independent calls is worth ~2–4x latency and can be worth more in cost — and this is measured, not theoretical.** LLMCompiler (ICML 2024, arXiv:2312.04511) plans a DAG of function calls and dispatches independent ones in waves: **up to 3.7x latency speedup, up to 6.7x cost reduction, and up to ~9% accuracy improvement** over sequential ReAct-style execution on HotpotQA / Movie Recommendation / ParallelQA. The accuracy gain is the important part for us — it did **not** trade correctness for speed; better orchestration of dependencies *improved* the answer. — *(Verified — LLMCompiler, ICML 2024)*

3. **Parallelism is a cost multiplier, not a cost saving, when the branches are genuinely separate explorations.** Anthropic's production multi-agent research system uses an orchestrator-worker shape (lead agent + 3–15 parallel subagents with isolated context windows) and reports **90.2% improvement over single-agent** on internal research evals — while burning **~15x the tokens of a chat**, with token usage alone explaining **~80% of performance variance**. The published guidance is explicit that this is only justified for **open-ended, breadth-first, loosely-coupled** work; for tightly-coupled or sequential tasks the coordination overhead makes single-agent both cheaper *and* more reliable. **So "can it run in parallel?" and "should it?" are two different questions, and the second is about coupling, not capacity.** — *(Verified on direction — Anthropic multi-agent engineering writeup; Flagged on the exact 15x / 90.2% / 80% figures, which are vendor-reported internal evaluation, not independently replicated)*

4. **A step counter is not a termination guarantee. A ranking function is.** The formal result (Floyd; Hoare-logic total correctness) is that a loop terminates iff you can exhibit a **variant** — a function of the state that **strictly decreases on every iteration** over a **well-founded order** (one with no infinite descending chain). Total correctness = partial correctness + termination; they are separate proofs. Every agent framework ships the weak substitute: LangGraph's `recursion_limit` (default **25**), raising `GraphRecursionError` when exceeded. The frameworks' own documentation says exactly what the theory says — **never rely on the limit for termination; the limit is a circuit breaker for a bug, and the loop must carry its own explicit state-based exit condition.** Hitting the limit at exactly the default is the diagnostic signature of a *missing or broken exit condition*, not of a task that needed more steps. — *(Verified — Floyd/Hoare termination; LangGraph docs)*

5. **Most multi-agent failure is specification and verification, not model capability — so an optimizer that touches structure is operating on the actual failure surface.** MAST (Berkeley Sky Computing, arXiv:2503.13657) hand-analysed 200+ execution traces across 7 frameworks and derived **14 failure modes in 3 categories**: **specification issues** (ambiguous roles, ill-defined task requirements, *ill-defined stopping conditions*), **inter-agent misalignment** (ignored input, withheld information, unresolved disagreement, derailed handoff — "resources wasted"), and **task verification** (premature declaration of completion, inadequate checking, no secondary validation). Observed failure rates of **41–86.7%** depending on system and benchmark. Two of the three categories are exactly what a pre-execution graph plan addresses: stopping conditions and completion verification. — *(Verified — MAST, arXiv:2503.13657)*

6. **Cost in agentic work is dominated by context, not by generation — which changes what "optimize" means.** 2026 practitioner accounting puts a coding-agent task at roughly **$0.03–$2.60**, consuming **~33k–188k tokens**, with the bulk attributable to *context overhead* (history, tool schemas, retrieved documents) rather than the generated output. Multi-agent topologies carry a reported **5–30x token multiplier**. Two consequences: **(a)** prompt/context caching is the highest-leverage single lever (repeat-context cost reduced up to ~90%); **(b)** "context rot" — accumulation of low-signal tokens — degrades both cost *and* accuracy, because attention is not uniform across a long window. **Cutting a redundant step therefore saves more than its own tokens; it also removes its output from every downstream context.** — *(Flagged — 2026 practitioner/vendor figures of variable authority that move fast; the direction is well-corroborated, the specific ranges are not primary-sourced)*

7. **Granularity is a real optimum with cost on both sides, so "collapse" and "promote" are both legitimate moves.** Classical parallel computing: **fine-grained** tasks expose more parallelism but pay more scheduling/communication overhead; **coarse-grained** tasks pay less overhead but under-use capacity and hurt load balance. In agent terms the overhead per task is a full context load, a tool round-trip, and a re-grounding cost — which is *large*, pushing the optimum coarser than intuition suggests. This is the theoretical warrant for **collapsing** several trivially-related steps into one, and equally for **promoting** an overloaded step into its own properly-budgeted subtask when it carries independent risk. — *(Verified — task granularity trade-off; Inferred — the "agent overhead is large, so prefer coarser" mapping is our synthesis)*

8. **Profile before optimizing; the bottleneck is reliably not the suspect.** This is the pack's own measured finding (`ci-and-test-efficiency.md` CE1–CE3) and it generalizes cleanly: a suite everyone "knew" was slow because of a migration chain turned out to be **73% app-boot time**, and a unit measured at 3s in isolation cost 36s under parallel load because of contention. The lesson transfers directly: **a plan that parallelizes the step you *assumed* was expensive, without measuring, is the Hunch Optimization anti-pattern with a bigger blast radius** — and parallelism layered on top of contention makes things *slower* while costing more. — *(Verified — in-repo, measured; BoK Part VII.8 / Part VIII)*

---

## Confidence summary

- **Verified: 5 · Inferred (in part): 2 · Flagged: 1.**
- **Load-bearing Flagged claim:** finding #6 (cost/context accounting) rests on 2026 practitioner and vendor material of variable authority, and pricing/ratios move monthly. Use the *shape* of the finding (context dominates; caching is the big lever; a redundant step costs downstream too) and **re-establish any specific number before it becomes load-bearing** (NG3). The same caution applies to the exact figures in finding #3.
- **Load-bearing Inferred claims:** the mapping in #7 — that *agent* per-task overhead is large enough to push the granularity optimum coarser — is our synthesis from the classical trade-off plus the context-cost evidence; neither source asserts it. Finding #1's application of Brent's bound to *agent* tasks assumes tasks are independently schedulable and roughly uniform, which real agent steps are not; treat the bound as an **upper limit on what is achievable**, never as a prediction.
- **Disconfirming evidence actively sought and found** (the important half — see `open-questions.md` for the full treatment):
  - Against "parallelize by default": Anthropic's own guidance says multi-agent parallelism is *wrong* for tightly-coupled or sequential work, where it is both costlier and less reliable; practitioner coverage cites a 2026 study reporting **every tested multi-agent topology degrading plan quality by 39–70%** versus a single coherent planner. *(Flagged — secondary citation, primary not read.)*
  - Against "decompose finely": MAST's inter-agent-misalignment category is *created* by decomposition — more boundaries mean more places to lose information. Decomposition has a real, measured downside.
  - Against "the graph is knowable up front": genuinely exploratory work has dependencies that are only discovered by doing the work, so a rigid up-front DAG is wrong for it. Hence the plan must be **revisable at checkpoints**, which is the same conclusion LOA Archetype H reaches (plan → execute → observe → *replan*).

---

## Design implications (what `/optimize-graph` and the pack should do with this)

1. **Plan the graph explicitly, before executing, as a first-class artifact.** Nodes = tasks with a stated goal and exit condition; edges = *real* data/decision dependencies. Making it explicit is what enables everything else — and it directly attacks MAST's largest failure category (specification).
2. **Compute the critical path, and optimize the span before the width.** The first question is never "what can run in parallel?" — it is **"what is the longest chain, and can it be shorter?"** Parallelism cannot beat the span (#1). Report `T₁`, `T∞`, and the resulting ceiling so the plan states what it can and cannot buy.
3. **Parallelize on independence, gate on coupling.** Two tasks may run concurrently iff neither consumes the other's output *and* neither's decision changes the other's shape. Where coupled, keep them serial and say why (#3). Bound the fan-out and pair it with backpressure/retry — unbounded fan-out against a rate-limited provider is a real observed failure in this fleet, not a hypothetical (see `comparables.md`, the 429/529 case).
4. **Give every loop a ranking function, not just a cap.** Each iterative node declares: the **variant** (what strictly decreases), the **well-founded floor** (where it bottoms out), the **exit condition**, and a **budget cap as a circuit breaker only**. A loop with a cap but no variant is flagged: it is *hoped* to terminate. Hitting the cap is a defect signal, not a resource signal (#4).
5. **Treat granularity as a two-way optimization.** *Collapse* steps whose separation buys no independent verification and costs a full context load. *Promote* a step that hides independent risk, needs its own budget, or is a verification gate in disguise (#7).
6. **Rigor floors are inputs to the optimizer, never outputs.** The plan carries the mandatory gates (tier-appropriate personas and veto-holders, the Testing Strategy union, the end-to-end surface list) as **fixed nodes the optimizer may reorder but may not remove**. Optimization reshapes *how* the floor is met; it never lowers the floor. A plan that drops a gate is rejected, not scored.
7. **Determinism is an optimization target, not a side effect.** Prefer the deterministic node over the model node wherever both would do (LOA P2); fixed ordering over incidental ordering; one authoritative producer per quantity (DM7). A more deterministic plan is a *better* plan at equal cost, because it is reproducible and reviewable.
8. **Measure cost vs delivery afterwards, and feed it back.** Record planned vs actual (steps, wall-clock, tokens where available, rework passes) and whether the completeness/rigor floors were met. This is the pack's existing oracle shape — a mitigation record with red→green or human validation (ADR-0003) — and it makes the optimizer improvable rather than merely opinionated. **Profile before optimizing (#8): a plan that reshapes an unmeasured bottleneck is a hunch.**
9. **Keep the plan revisable.** Adopt plan → execute → observe → replan at checkpoints (LOA 1.3 + Archetype H) rather than a frozen DAG, because exploratory dependencies are discovered, not known. Re-planning is cheap; executing the wrong graph is not.

## How to use this base

- **`/optimize-graph`** cites this base for its theory (span, granularity, termination, coupling) and its numbers.
- **`/define-architecture`** and **`/design`** should cite finding #3 when choosing between a single coherent worker and an orchestrator-worker split.
- **`/implement`** should cite finding #4 whenever it writes any retry, poll, or reflection loop.
- Anyone tempted to add parallelism should read the **disconfirming evidence** above first.
