---
id: kb-agent-focus-and-scope-control-sota
title: "Agent Focus & Scope Control — State of the Art"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [overthinking, goal-drift, scope-creep, stopping-conditions, reasoning-effort]
links:
  - { to: kb-agent-focus-and-scope-control, rel: refines }
review-by: "2027-02-28"
summary: >-
  The two failure modes (overthinking vs goal drift) and the four evidence-backed levers for scope
  and task adherence: enforced done predicates, adaptive anchoring, structured scope locks, and
  bounded self-critique. Why reducing reasoning effort does not reach scope drift.
---

# State of the art — extended-reasoning focus & scope control (2025)

*Confidence-labelled. Sources in `sources.md`.*

## The two failure modes (keep them separate)

### 1. Overthinking (reasoning depth)
Reasoning-tuned models add unnecessary reasoning steps, **especially on simpler problems**, and
paradoxically *underthink* harder ones — they misjudge task difficulty and do not adapt response
length to need. Excessive chain-of-thought can *degrade* accuracy by introducing new errors as the
reasoning path grows. **[Verified — Su et al., "Between Underthinking and Overthinking", arXiv 2505.00127]**

Mitigations are about *depth*: monitoring and capping reasoning path length ("Overclocking LLM
Reasoning", arXiv 2506.07240, uses an internal progress encoding to prune steps → more concise *and*
more accurate); preference-optimising for shorter generations with minimal quality loss;
budget-aware prompting and sketch-of-thought. **[Verified — arXiv 2506.07240; efficient-reasoning survey]**

### 2. Goal drift / scope creep (task boundary)
Distinct from overthinking. The agent deviates from its original objective as context changes or is
polluted; sub-goals mutate and the task expands — **Latent Goal Crystallization (LGC)** — *without
explicit re-prompting*. Over long sessions this compounds via context-window overflow, recursive
prompt editing, and accumulated minor inconsistencies, producing **semantic drift** (interpretations
shift) and **behavioural drift** (unrequested subroutines emerge). **[Verified — arXiv 2505.02709; IJETA V13I3P63; usewire agent-drift]**

Measured impact: "Agent Drift" (arXiv 2601.04170) quantifies degradation in accuracy, coherence and
coordination over long missions for single- and multi-agent systems; IBM catalogues "agentic drift"
as a production risk. Unchecked, drift forces *more* human supervision, undermining autonomy. **[Verified — arXiv 2601.04170; IBM]**

> **Why reducing reasoning level does not fix the user's problem.** `reasoning_effort` governs
> failure mode 1 (depth). The user's symptom — "additional tasks and ceremony" — is failure mode 2
> (scope). Different axis; the dial does not reach it. **[Verified — synthesis of the two source clusters]**

## The four levers that address scope/task adherence

1. **Enforced stopping conditions / "done" predicates.** The lack of a clearly specified stopping
   condition is *the* driver of agents that stall or over-run. Explicitly enforced "done" predicates
   and episodic memory are the proposed remedy — but "not yet universal standards". **[Verified — arXiv 2505.02709, 2601.04170]**

2. **Adaptive anchoring (periodic revalidation).** Re-validate against the *original* goal at
   intervals so accumulated context cannot silently redefine the task. Named explicitly among 2025
   mitigations alongside memory-consolidation and drift-aware behaviours. **[Verified — arXiv 2601.04170; goal-persistence work]**

3. **Structured scope locks (system-prompt level).** The OpenAI GPT-5/5.1 prompting guidance and
   derived cheatsheets recommend *structured constraint blocks*, e.g.:
   - "Implement EXACTLY what the user described, nothing more."
   - "Do not add features, fix edge cases, or suggest improvements unless explicitly requested."
   - "Suggest potential improvements as optional text only; never implement without user approval."
   - "Limit tool/API calls to only those precisely required."
   Structured beats prose because narrative instructions degrade under long context. **[Verified — developers.openai.com GPT-5 / GPT-5.1 prompting guides]**

4. **Bounded self-critique.** Reflexion / Producer-Critic style self-evaluation improves
   definition-of-done adherence *when* bounded by explicit stopping rules (max rounds, score
   thresholds) and told to prioritise major failures over minor imperfections. **Unbounded, it
   becomes "degenerating reasoning" — cyclical, non-terminating self-correction, i.e. more ceremony.**
   **[Verified — arXiv 2405.06682; Reflexion; reflective-agent surveys]**

## The synthesis for an agent framework
The evidence does not say "reason less"; it says "**anchor the goal, enforce the stop, lock the
scope, and bound any self-check.**" A framework that already states these as directives has the
*content* right; the open problem is **enforcement under long context** — directives degrade exactly
where they are most needed. The highest-value intervention is therefore to move the goal/stop
control from prose to *structure* and to *detect its absence*, rather than to author more prose.
