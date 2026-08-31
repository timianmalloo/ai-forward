---
id: kb-agent-focus-and-scope-control
title: "Agent Focus & Scope Control — keeping extended-reasoning models on task"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [knowledge, agent-focus, scope-drift, overthinking, reasoning-effort, stopping-conditions, PACK-O]
links:
  - { to: defect-classes, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2027-02-28"
review-suggested: []
summary: >-
  Sourced evidence base on why extended-reasoning models (GPT-5.x family and peers) keep adding
  unrequested tasks and ceremony even when reasoning level is reduced. Headline: reasoning_effort
  and scope-adherence are DIFFERENT levers - overthinking (reasoning depth) is what reasoning_effort
  controls, while Latent Goal Crystallization / goal drift (task scope expanding without
  re-prompting) is a task-adherence and stopping-condition problem that reasoning level does not
  touch. The evidence-backed fixes are enforced "done" predicates, adaptive anchoring, structured
  scope locks, and BOUNDED self-critique - most of which the pack already has as directives but,
  per the drm-0008 dream, skips in 78% of substantive turns. The gap is enforcement, not directives.
---

# Agent Focus & Scope Control

*Domain knowledge base. Built by `/collectknowledge` to ground the proposal on tightening
extended-reasoning models to the task. Every load-bearing claim is confidence-labelled and sourced
(`sources.md`). The problem framing is the user's: models with extended reasoning "continue to go
off the reservation with additional tasks and ceremony despite the directives to focus on the goal
and the completion stop" — even when reasoning level is reduced.*

## The headline finding (Verified)

**The user is pulling the wrong lever, because two distinct failure modes are being conflated.**

| | **Overthinking** | **Goal drift / scope creep** |
|---|---|---|
| What it is | Excessive reasoning *depth* — unnecessary reasoning steps, especially on easy tasks | The *task boundary itself* expands — new sub-tasks and ceremony appear that were never requested |
| Where it happens | Inside the chain-of-thought, before the answer | At the planning/action level, across turns |
| Controlled by | `reasoning_effort` (minimal/low/med/high), verbosity caps, path-length control | **NOT** `reasoning_effort` — needs task-adherence + stopping-condition controls |
| The user's symptom | (secondary) | **This one** — "additional tasks and ceremony" |

Reducing `reasoning_effort` addresses overthinking (how deeply the model explores *before*
answering). It does **not** address whether the model *expands the task*. The literature names the
scope-expansion mechanism **Latent Goal Crystallization (LGC)**: operative sub-goals mutate and the
task boundary grows *without explicit re-prompting* (Evaluating Goal Drift, arXiv 2505.02709; IJETA
V13I3P63). That is why turning the reasoning dial down does not stop the drift — the dial is on a
different axis. **[Verified — arXiv 2505.02709; 2601.04170; IBM agentic-drift]**

## What the evidence says actually works (Verified)

The 2025 literature converges on four levers for scope/task adherence — none of which is
"reason less":

1. **Enforced "done" predicates / acceptance criteria.** Agents that carry an explicit,
   pre-stated completion condition adhere better and stop cleanly; the absence of a clear stopping
   condition is *the* driver of both stalling and over-running. **[Verified — arXiv 2505.02709; 2506.07240; Reflexion]**
2. **Adaptive anchoring.** Periodic *re-validation against the original goal* mid-task counteracts
   drift as context accumulates and dilutes the instruction. **[Verified — arXiv 2601.04170; goal-persistence work]**
3. **Structured scope locks in the system prompt** (not prose). The GPT-5/5.1 prompting guides
   recommend explicit blocks: *implement exactly what is requested; do not add features/error
   handling/comments unless specified; suggest improvements as optional text only, never implement
   without approval; cap tool calls.* Structured constraint beats narrative directive because
   narrative degrades under long context (instruction-following degradation). **[Verified — OpenAI GPT-5/5.1 prompting guides]**
4. **Self-critique WITH explicit stopping rules.** Targeted self-reflection (Reflexion,
   Producer-Critic) improves definition-of-done adherence — but only when bounded by max rounds /
   score thresholds and told to prioritise major failures over minor imperfections. **Unbounded
   self-critique becomes "degenerating reasoning": non-terminating self-correction — i.e. MORE
   ceremony.** A self-assessment that is not itself bounded makes the problem worse. **[Verified — arXiv 2405.06682; Reflexion]**

## Why this matters for the pack (the enforcement gap)

The pack already *has* directives for every one of the four levers:
- enforced done predicate → **CT19 goal-state front matter** (`communication-and-task-discipline.md`);
- adaptive anchoring → the **re-ground** discipline (BoK §VI.2) and the **E18** close;
- stopping condition → **GO16** Stage-0 triage / termination variant (`execution-graph-optimization.md`);
- the whole class is registered as **PACK-O**.

But the `drm-0008` dream (this repo's own corpus) measured, **Verified**, that
**61 of 78 substantive turns (78%) recorded no goal-state (`done_when`)**. The control exists at
rung-3 (always-loaded prose) and is *skipped in the large majority of turns*. This is the pack's own
CI6 lesson pointed at itself: **a directive that lives only as always-loaded prose is a memoir** —
present, correct, and ignored. The literature predicts exactly this (instruction-following
degradation under long context). **[Verified — drm-0008/dream.json p12]**

## Design implications (what the next phase should weigh)

These feed the proposal (`docs/proposals/agent-focus-tightening.html`). The evidence supports a
clear priority ordering:

1. **Highest leverage — make the goal-state opening *structural and enforced*, not more prose.**
   The lever that works (enforced done predicate) already exists but is skipped 78% of the time.
   Converting it from "please write a goal state" into a lightweight, mechanically-checkable opening
   (and detecting its absence, which the audit `done_when` field + PACK-O miner already do) is the
   single highest-value move. **Adding more prose directives is low leverage** — the problem is not a
   missing directive.
2. **Medium leverage — a BOUNDED session self-assessment.** The evidence supports a self-check that
   maps outputs to the pre-stated acceptance criteria *and is itself bounded* (one pass, name the
   gap, stop). It must never become an open reflection loop — that is the degenerating-reasoning trap
   and would *manufacture* the ceremony the user is complaining about.
3. **Lower leverage — persona extension.** Scope discipline is already owned by the Simplifier
   (soft veto on unjustified complexity) and the Tech Lead (smallest correct change). Personas are
   convened at *gates*, not *per turn*, so they cannot catch per-turn scope creep as it happens; a
   "scope sentinel" persona would duplicate existing lenses and fire too late. Extending personas is
   the lowest-leverage of the three options — though a sharpened Simplifier/Tech-Lead *convene
   trigger* on autopilot turns is a cheap increment.

**The meta-warning the evidence makes explicit:** any fix must be *bounded*. The failure mode is
"too much unrequested work"; a fix that adds an unbounded self-review, a new heavyweight ceremony,
or a persona that always convenes would *increase* the very thing it targets. Scope control must be
cheap, structural, and self-terminating.

## Confidence summary

- **Verified:** the two-lever distinction; LGC/goal-drift as the scope mechanism; the four working
  levers; unbounded self-critique degenerates; the pack's 78% goal-state-skip rate.
- **Inferred:** the exact leverage ordering of the three proposal options (reasoned from the
  evidence + the measured skip rate, not from a controlled study of *this* pack).
- **Flagged:** the field is young and unsettled — "no solution is yet fully satisfactory" (arXiv
  2601.04170); benchmarks are still moving from short-turn to longitudinal. Treat any single
  technique as directional, not proven-optimal.

## How to use this base
- The **proposal** (`docs/proposals/agent-focus-tightening.html`) answers the user's three questions
  (personas? directives? self-assessment?) grounded in this evidence.
- `state-of-the-art.md` — the failure modes and the four levers, in depth.
- `references.md` — the concrete, copy-usable patterns (scope-lock blocks, stopping rules, anchoring).
- `glossary.md`, `open-questions.md`, `sources.md`.
