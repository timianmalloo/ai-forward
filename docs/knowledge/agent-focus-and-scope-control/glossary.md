---
id: kb-agent-focus-and-scope-control-glossary
title: "Agent Focus & Scope Control — Glossary"
type: glossary
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [glossary, overthinking, latent-goal-crystallization, adaptive-anchoring]
links:
  - { to: kb-agent-focus-and-scope-control, rel: refines }
review-by: "2027-02-28"
summary: >-
  The ubiquitous language of agent focus and scope control - overthinking, goal drift, Latent Goal
  Crystallization, instruction-following degradation, stopping conditions, adaptive anchoring,
  degenerating reasoning, and the pack's PACK-O / two-step front matter.
---

# Glossary — agent focus & scope control

- **Overthinking** — a reasoning model adds unnecessary reasoning *depth*, especially on easy tasks;
  can degrade accuracy. Controlled by `reasoning_effort`. *Not* the user's primary problem.
- **Underthinking** — the mirror: failing to extend reasoning when a hard task needs it. Same root
  (misjudging difficulty).
- **Goal drift** — an agent's behaviour deviates from its original objective as context accumulates
  or is polluted. Semantic drift (interpretation shifts) + behavioural drift (unrequested subroutines).
- **Latent Goal Crystallization (LGC)** — operative sub-goals mutate and the task boundary expands
  *without explicit re-prompting*. The precise mechanism behind "additional tasks and ceremony".
- **Scope creep** — the observable result of LGC/goal drift: unrequested work added to the task.
- **Instruction-following degradation** — the weakening of adherence to standing instructions over a
  long session (context overflow, recursive prompt editing, accumulated inconsistency). Why prose
  directives fail exactly where needed.
- **Stopping condition / "done" predicate** — an explicit, checkable statement of when the task is
  complete. Its absence is the main cause of stall-or-overrun.
- **Adaptive anchoring** — periodic revalidation of the current work against the *original* goal to
  counteract drift.
- **Degenerating reasoning** — non-terminating self-correction: a self-critique loop with weak/absent
  stopping rules that keeps "improving" and *adds* ceremony. The trap a session self-assessment must
  avoid.
- **reasoning_effort** — the depth-of-exploration control (minimal/low/medium/high). Governs
  overthinking, **not** scope.
- **Reflexion / Producer-Critic** — self-critique agent patterns; effective for definition-of-done
  adherence *when bounded*.
- **PACK-O** (this repo) — the registered defect class: "a turn begun with no stated goal state or
  exit condition." The pack's name for the scope/stopping failure.
- **Two-step front matter** (this repo, CT19–CT24) — the pack's opening control: write the goal
  state (Goal/Done-when/Not-in-scope), then plan the turn once with `/optimize-graph`.
