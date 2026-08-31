---
id: kb-agent-focus-and-scope-control-open-questions
title: "Agent Focus & Scope Control — Open Questions"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [open-questions, unsettled, enforcement-vs-autonomy, model-family-variance]
links:
  - { to: kb-agent-focus-and-scope-control, rel: refines }
review-by: "2027-02-28"
summary: >-
  What the research could not settle: no fully satisfactory long-horizon solution yet; the
  enforcement-vs-autonomy tension; whether a session self-assessment helps or adds ceremony here;
  how mechanical a structural opening can be; and model-family variance in drift rate.
---

# Open questions & risks

- **No fully satisfactory solution exists yet (2025–26).** The field explicitly states long-horizon
  drift is "unsolved or brittle in most deployed systems"; architecture/training choices in 2026 will
  decide whether it is structurally fixed or patched at deployment. Treat every technique as
  directional. **[Flagged — arXiv 2601.04170; lyntx benchmark survey]**
- **Enforcement vs. autonomy tension.** Structural scope locks and required openings reduce drift but
  can feel heavy; too much enforcement reproduces the "ask permission per step" cost that autopilot
  exists to remove. The right level is an open calibration question for this pack specifically.
- **Does a session self-assessment help or add ceremony *here*?** The evidence says "helps if bounded,
  hurts if unbounded" — but the exact bound (one pass? a fixed checklist? a mechanical presence check
  only?) that maximises adherence without manufacturing ceremony has not been measured for this pack.
  A/B-able via the audit `done_when` + PACK-O miner already in place.
- **Structural opening — how mechanical can it be?** The audit `done_when` field already detects a
  *missing* goal-state; whether goal-state *quality* (a real terminal condition vs a vague aspiration)
  can be checked mechanically, or needs human/LLM judgement, is unsettled.
- **Model-family variance.** The user reports the GPT-5.6 family drifting even at reduced reasoning.
  Whether the drift rate differs materially across families (and whether a control should be
  family-tuned) is not established here — would need per-family audit data.
- **Reasoning-depth vs scope interaction.** Whether lowering `reasoning_effort` *worsens* scope
  adherence (less deliberation about "should I do this?") or is neutral is not settled; the two
  clusters were studied largely separately.
