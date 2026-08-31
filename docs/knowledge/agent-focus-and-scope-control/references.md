---
id: kb-agent-focus-and-scope-control-references
title: "Agent Focus & Scope Control — References & Patterns"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [scope-lock, done-predicate, adaptive-anchoring, bounded-self-critique, gpt-5-prompting]
links:
  - { to: kb-agent-focus-and-scope-control, rel: refines }
review-by: "2027-02-28"
summary: >-
  Copy-usable techniques mapped to the pack's existing controls: reasoning-depth controls, the
  GPT-5 structured scope-lock block, enforced done predicates, adaptive anchoring, and bounded
  self-critique - with the enforcement principle (structural beats prose under long context).
---

# References — concrete patterns & techniques

*Copy-usable techniques from the sources, mapped to the pack's existing controls. Confidence in
`state-of-the-art.md`; sources in `sources.md`.*

## Reasoning-depth controls (failure mode 1 — overthinking)
- **`reasoning_effort: minimal|low|medium|high`** — depth of exploration before answering. Low for
  routine/latency-sensitive; high for ambiguous/safety-critical. *Governs depth, not scope.*
- **`output_verbosity` / explicit length caps** — "≤N sentences", "code only, no commentary".
- **Reasoning path-length monitoring** ("overclocking") — cap/prune steps; empirically more concise
  *and* more accurate.
- **Preference for shorter generations** — length can drop sharply with minimal quality loss.

## Scope / task-adherence controls (failure mode 2 — the user's problem)

### Structured scope-lock block (GPT-5/5.1 guides) — *the pattern to consider adopting*
```
Implement EXACTLY what was requested, nothing more.
- Do not add features, edge-case handling, refactors, or comments unless specified.
- If requirements are ambiguous, use the simplest valid solution.
- Surface improvements as OPTIONAL suggestions (text only); never implement without approval.
- Cap tool/API calls at the minimum the request requires.
```
**Pack mapping:** this is CT14–CT18 (capture ideas, don't chase; smallest change; reviewer findings
are advice, not scope) — already present as prose. The delta the evidence suggests is *structure +
enforcement*, not new content.

### Enforced "done" predicate (opening)
State, before acting: **Goal · Done when · Not in scope.** The "Done when" is a *terminal condition*
you can point at. **Pack mapping:** CT19 goal-state front matter — present, but skipped in 78% of
substantive turns (drm-0008). The lever is right; the enforcement is missing.

### Adaptive anchoring (mid-task)
At each checkpoint, restate the *original* goal and check the work has not drifted. **Pack mapping:**
re-ground (BoK §VI.2) + the E18 Completed/Remaining/Next close.

### Bounded self-critique (close)
One pass mapping outputs → the pre-stated acceptance criteria; name gaps; **stop.** Rules that keep
it from becoming ceremony: max one round by default; prioritise correctness/floor failures over
polish; weigh the cost of another pass against expected benefit. **Pack mapping:** the Test
Architect's Proof Pack + the self-verification checklists — but no *session-level* bounded self-check
today.

## The enforcement principle (the load-bearing takeaway)
Across every source: a control that lives only as always-loaded prose degrades under long context.
The interventions that hold are **structural** (a required opening shape), **mechanical** (detecting
the control's absence), or **bounded** (a self-check that self-terminates). The pack's CI6 ladder
says the same thing: *make it impossible > automated control > always-loaded instruction > knowledge
doc*. The goal/stop control currently sits at rung 3; the evidence says move it up.
