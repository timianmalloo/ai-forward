---
id: "note-20260712-model-orchestration-policy"
title: "Model-orchestration routing policy for AI-Forward skills"
type: decision-note
status: superseded
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [decision-note, model-orchestration, loa, skills, orchestrator]
links:
  - { to: "architecture", rel: relates-to }
review-by: "2027-01-08"
review-suggested: []
summary: >-
  Historical policy decision for applying LOA tier allocation to skill execution. Superseded
  after forensic review found the proposed control plane unwired, internally contradictory,
  unproven, and missing data-governance boundaries.
---

# Model-orchestration routing policy for AI-Forward skills

> **Superseded 2026-07-12.** The user reverted this capability after the forensic review.
> See `note-20260712-revert-model-orchestration`.

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback
weight. Captures the five policy calls that settle how the pack routes its own work across
models — the input to `model-orchestration.md` and the Orchestrator's expanded charter.*

- **Kind:** decision
- **Confidence:** Verified *(explicit user directives, quoted below)*
- **Made during:** design of the model-orchestration capability (session `3292b997`), before `/extendaibundle`.

## The call

The pack already teaches LOA's Cheapest-Sufficient-Tier (P1), Capability Router (1.1), and
Capability Escalator (6.1) for the **products it builds** but applies none of it to its **own
execution**. This policy dogfoods LOA on the pack: each skill's constituent activities
(decomposed into nine reusable *activity archetypes* — deterministic mechanics, grounding,
research/spikes, broad reasoning, adversarial review, implementation, creative UX/UI,
documentation, verification/eval) route to the **cheapest sufficient model**, orchestrated by
the **Orchestrator** persona and governed by the **AI Systems Engineer**. The five design
questions are resolved as follows.

1. **Dispatch mode — advisory *default* with auto-dispatch, human overrule.** The Orchestrator
   **auto-dispatches** each stage/persona to its recommended tier by default; the human may
   **overrule** any routing decision at any point. Routing is a strong default, never a cage.
   *User:* "advisory and default - auto dispatch but allow me to overrule."

2. **Cost vs. efficiency — a user knob; default `efficiency`; best model to the highest-rigor
   work.** A profile toggle (`efficiency` | `cost`) governs borderline choices. The default is
   **`efficiency` (quality over cost)**: the areas that need the **most rigor** — adversarial
   hard-veto review, architecture, investigation root-cause — get the **best available model**,
   spending is not clipped there. `cost` mode trades down on borderline (T1) work only.
   *User:* "allow me specify optimize for cost vs. efficiency, by default optimize for
   efficiency over cost and maximize the areas that need the most rigor with the best model."

3. **Adversary independence — a hard rule; blocking → human review + overrule.** On any
   hard-veto gate the **reviewer model MUST differ from the author model** (structural
   separation, BoK §II.3; self-consistency). If honoring it is **truly blocking** (e.g. only one
   model is available), the Orchestrator **surfaces it for human review**, and the human may
   overrule. Enforced, not advisory.
   *User:* "Adversay should be hard rules - if truly blocking then allow me to review and i can
   overrule."

4. **Deterministic → script, but skills-centric.** Deterministic mechanics (archetype A) belong
   in **scripts, not models** (LOA P2). Where such work is still inline, move it to a script.
   **But the skill surface always remains** — a skill may exist purely to invoke a script — so
   the user experience stays **skills-centric**. (Most archetype-A work is *already*
   script-backed: `audit-log.py`, `prompt-log.py`, `docs-graph.py`, `new-capability.py`,
   `sync-pack.ps1`, `verify-bundle.ps1`; this policy makes that a rule and adds `model-router.py`
   as the routing lookup.)
   *User:* "Look at the places that you can move to script and then move them to script in the
   repo but allow AI binding in other words let the skills always exist even if the task of the
   skill is to invoke scripts... so that the experience is always skills centric."

5. **Target runtime — GitHub Copilot CLI on Windows and macOS.** The directive optimizes for the
   **GitHub Copilot CLI** (its per-Task `model` + `reasoning_effort` selection and background
   parallel agents) on **Windows and macOS**. All routing scripts are **cross-platform** (Python
   3.8+ stdlib, or `pwsh`), and model choices are expressed as **capability tiers** mapped to the
   environment's current roster (Provider Portability, LOA 6.6) so the policy survives model churn.
   *User:* "optimize for github copilot CLI on windows and mac."

## Alternatives dismissed
- **A fourth tier vocabulary.** Rejected — compose with the existing Rules-of-the-Road effort
  tiers (T0/T1/T2, which already gate spend), LOA capability tiers, and Rigor Protocol stages;
  add only the *execution-model-per-activity* axis.
- **Enforced (non-overridable) routing.** Rejected per Q1 — the human keeps the override.
- **Cost-first default.** Rejected per Q2 — efficiency is the default; rigor areas get the best model.
- **Model everything, including mechanics.** Rejected per Q4 and LOA P2 — deterministic work is a script.
- **Tool-neutral abstraction only.** Deferred — optimize concretely for the Copilot CLI (Q5)
  while keeping capability-tier names for portability.

## Validation condition
Revisit if the Copilot CLI's model-selection surface changes materially, if a single-model
environment makes Q3 routinely blocking, or if audited inference cost shows the `efficiency`
default is mispriced for the team's workloads.
