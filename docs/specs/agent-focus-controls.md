---
id: spec-agent-focus-controls
title: "Spec — Agent focus & scope controls (goal-state structure, bounded self-assessment, convene trigger)"
type: spec
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [spec, agent-focus, scope-drift, PACK-O, self-assessment, goal-state]
links:
  - { to: kb-agent-focus-and-scope-control, rel: implements }
  - { to: defect-classes, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2027-02-28"
review-suggested: []
summary: >-
  Specifies the three approved controls from the agent-focus proposal for tightening
  extended-reasoning models to the task: (FC-2) promote the goal-state turn opening from prose to a
  structured, mechanically-detectable block; (FC-1) a bounded, inline, self-applied session
  self-assessment that reads the audit goal-state/summary data; and (FC-3) a sharpened
  Simplifier/Tech-Lead convene trigger on scope inflation. Part A functional only; no user-facing UI.
---

# Spec — Agent focus & scope controls

## Grounding / provenance
Implements the recommendations in `docs/proposals/agent-focus-tightening.html`, grounded in
`docs/knowledge/agent-focus-and-scope-control/` (the `implements` edge above). The corpus evidence
(`docs/dreams/drm-0008` p12): **61/78 substantive turns (78%) recorded no goal-state** — the control
exists at rung-3 prose (CT19) and is skipped. The research finding: reasoning-effort does not reach
scope drift; the working levers are an *enforced done predicate*, *adaptive anchoring*, and *bounded
self-critique* — all of which the pack states as prose but does not enforce.

## Part A — Functional specification

### Problem (solution-independent)
Extended-reasoning agents expand the task boundary — adding unrequested work and ceremony — because
the standing controls that would stop this (goal state, stop condition, scope check) live only as
always-loaded prose that degrades under long context, and are demonstrably skipped 78% of the time.
The problem is **enforcement of the controls we already have**, not a shortage of directives.

### Personas / jobs-to-be-done
- **The agent (any model, esp. GPT-5.x family)** — needs the goal/stop to be a *structural* opening
  it cannot skip silently, and a *bounded* closing check it can self-apply to catch its own drift.
- **The maintainer (@timianmalloo)** — needs the drift to be *mechanically visible* (present in the
  audit log, checkable by a script) rather than only detectable by reading a transcript.

### Core scenario
An agent opens a substantive turn by recording the structured goal-state (Goal / Done-when /
Not-in-scope), does the work, then runs the bounded self-assessment at close: it reads its own
session's audit entries, confirms each substantive turn recorded a goal-state, and flags any turn
whose summary reaches beyond its Done-when — in **one deterministic pass**, then stops.

### Explicit non-goals
- **Not** an LLM-scored or judgemental self-critique — the mechanical check is deterministic; scope
  judgement is *surfaced for review*, never auto-decided.
- **Not** an unbounded reflection loop — the self-assessment is one pass and self-terminates (the
  research's "degenerating reasoning" trap; adding an open loop would *increase* ceremony).
- **Not** a new persona (proposal Q1 — lowest leverage; scope discipline is already owned).
- **Not** more prose directives beyond the minimum needed to define the structure and the check.
- **Not** a new datastore — reuses the existing audit `goal`/`done_when` fields (AL5b).

### Conceptual model (ubiquitous language — no persistence beyond existing audit fields)
- **Goal-state** — the structured opening: `Goal` (the requested outcome) · `Done-when` (a terminal,
  checkable condition) · `Not-in-scope` (what the turn will not touch). Maps 1:1 to the audit fields
  `goal` and `done_when` (AL5b) — no new fields.
- **Substantive turn** — an audit entry whose `kind ∈ {skill, manual, prompt, command}` (the
  `PACKO_SUBSTANTIVE` set already used by the dream miner). Trivial/conversational turns are exempt.
- **Scope diff** — the comparison of a turn's realised summary against its Done-when / Not-in-scope.
- **Bounded self-assessment** — a single deterministic pass over the current session's substantive
  turns producing (a) presence gaps and (b) drift-review pairs; no second pass, no re-plan.

### Acceptance criteria (falsifiable)

**FC-1 — Bounded session self-assessment (a mechanical control + a directive)**
- **AC-1.1** Given a session id, a `selfcheck` command reads that session's audit entries and reports
  every substantive turn that recorded **no** `done_when` (presence gap). *Fails if:* a substantive
  turn without `done_when` is not reported, or a trivial turn is reported.
- **AC-1.2** For substantive turns that **have** a `done_when`, it emits the `done_when → summary`
  pair for review — it **does not** auto-judge drift. *Fails if:* it prints a pass/fail verdict on
  scope rather than surfacing the pair.
- **AC-1.3** It is **one deterministic pass** — no network, no model, no second iteration; same input
  → same output; exits 0 with a clean "all substantive turns recorded a goal-state" when there are no
  gaps. *Fails if:* output varies across runs on identical input, or it loops.
- **AC-1.4** A directive (in `communication-and-task-discipline.md`) defines the bounded closing
  self-assessment as the standing behaviour, explicitly one-pass and self-terminating, composing with
  the E18 close. *Fails if:* the directive permits a second reflection pass or re-planning.

**FC-2 — Structural goal-state opening (promote prose → structure)**
- **AC-2.1** The CT19 opening is specified as a **fixed three-field block** (Goal / Done-when /
  Not-in-scope) that maps 1:1 to the audit `goal`/`done_when` fields, so its presence is
  **mechanically detectable** by FC-1's `selfcheck` (and the existing dream PACK-O miner). *Fails if:*
  the opening remains free-form prose with no field mapping a script can read.
- **AC-2.2** "Done-when" is defined as a **terminal, checkable condition** (not an aspiration), and a
  gap found en route remains a *finding*, not a new goal (CT19 unchanged in intent, sharpened in form).
  *Fails if:* the directive allows a vague aspiration to satisfy Done-when.

**FC-3 — Sharpened Simplifier / Tech-Lead convene trigger**
- **AC-3.1** The persona convene table (`persona-audit.md` §8.7) is extended so the **Simplifier**
  (and **Tech-Lead**) convene when a turn — especially an autopilot turn — **touched anything in its
  declared Not-in-scope, or its realised work exceeded its stated Goal**. *Fails if:* the trigger
  still fires only on "adds an abstraction/dependency" and not on scope inflation.

### ISO 25010 NFR checklist (applicable lenses)
- **Functional suitability** — the `selfcheck` correctly classifies substantive turns and detects
  presence gaps (AC-1.1). **[applies — tested]**
- **Maintainability** — reuses the existing audit reader and the `PACKO_SUBSTANTIVE` set; stdlib only.
  **[applies]**
- **Reliability** — deterministic, degrades to "not recorded" when a field is absent (never a wrong
  number). **[applies — AC-1.3]**
- **Security / Privacy** — reads only the committed audit log (no secrets/PII per AL4); no new data.
  **[applies — no new surface]**
- **Performance** — a single pass over one session's entries; trivially within budget. **[applies]**
- Portability, Compatibility, Usability (as a UI) — **N/A** (a developer CLI, no visual surface).

## Part B — UX specification
**N/A — no user-facing surface.** The deliverables are (1) agent-behaviour directives in the pack's
knowledge docs and (2) a developer-facing CLI subcommand. There is no end-user flow, IA, or
navigation to design. The CLI's output is plain diagnostic text, specified functionally in Part A
(FC-1), not a designed UX.

## Part C — UI specification
**N/A — no visual UI.** No screen, component, or visual state exists. The CLI output format is a
functional concern (Part A), not a UI-token/state-machine surface.

## Comparables (sourced, from the knowledge base)
- **OpenAI GPT-5/5.1 prompting guides** — structured scope-lock blocks beat prose directives; the
  structural goal-state (FC-2) applies this. **[Verified — knowledge base sources.md]**
- **Reflexion / Producer-Critic + arXiv 2405.06682** — self-critique helps *bounded*, harms
  unbounded; FC-1's one-pass rule is the direct application. **[Verified]**
- **arXiv 2601.04170 (adaptive anchoring)** — periodic revalidation against the original goal; FC-1's
  self-assessment is the per-session instance. **[Verified]**

## Governance lenses
- Threat model / privacy: **no new surface** — reads the committed audit log only.
- Observability: the control *is* an observability feature (it surfaces the presence/drift signal).
- Release/rollback: pure-additive (a new CLI subcommand + directive text); trivially reversible.

## Residual risk & flagged unknowns
- **Flagged (from the knowledge base):** whether an inline self-assessment materially reduces drift
  *for this pack* is not yet measured — the field is young and no technique is proven-optimal. FC-1
  makes the signal *visible and self-applied*; whether agents *act* on it is the open question the
  audit `done_when` trend will answer over time.
- **Inferred:** the exact "Done-when reaches beyond summary" drift heuristic (AC-1.2) is surfaced for
  human/agent judgement precisely because a mechanical drift *verdict* would be a false-precision
  wrong number (IO8) — deliberately kept to "surface the pair", not "decide".

## Gate record (Stage 4 — Adversary Mode)
- **Simplifier (soft veto): PASS** — scope is minimal: one CLI subcommand reusing the existing reader,
  three directive edits; explicitly no new persona, no new store, no unbounded loop.
- **Test Architect (hard veto): PASS** — every FC-* acceptance criterion is falsifiable and names its
  failing input; FC-1 is the testable core.
- **Security & Identity: N/A** — no trust boundary, secret, identity, or PII touched.
- Authors did not self-clear.
