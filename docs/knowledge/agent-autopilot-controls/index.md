---
id: kb-agent-autopilot-controls
title: "Agent autopilot & autonomous-continuation controls (Copilot CLI ↔ Claude Code)"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [autopilot, autonomy, permission-modes, max-turns, max-autopilot-continues, copilot-cli, claude-code, termination, GO9, PACK-O, CT22]
links:
  - { to: defect-classes, rel: relates-to }
  - { to: kb-graph-and-loop-engineering, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  Sourced comparison of the autonomous-execution controls in GitHub Copilot CLI and Claude Code —
  the autonomy modes, the full-permission "YOLO" switches, and (the load-bearing finding) the
  step/turn caps that bound a runaway agent: Copilot's --max-autopilot-continues and Claude Code's
  --max-turns. Both vendors frame the cap exactly as the pack's GO9 does ("avoid infinite loops"),
  independently validating CT22, and both expose a rung-1 environment control that complements the
  in-context front matter (CT19–CT24). The answer to open question 3 (PACK-O mitigation): yes, a
  symmetric step cap exists on both surfaces.
---

# Agent autopilot & autonomous-continuation controls — domain knowledge

**Domain & problem:** the project runs on two coding-agent surfaces — **GitHub Copilot CLI** and **Claude Code** — and needs to know, symmetrically, what controls each exposes for *autonomous continuation*: the modes that let the agent act without per-step approval, the switches that grant full permissions, and above all the **caps that stop a runaway turn**. This directly serves the pack's PACK-O defect class (a turn begun with no exit condition) and clause CT22 (completion pressure is a cap firing, not a termination argument).
**Canonical framing:** both vendors frame autonomy as a **spectrum of permission/continuation modes** plus an explicit **safety cap**, and both describe the cap in the same words the pack uses — *"avoid infinite loops / runaway processes."* Our framing (the cap's firing is a *defect signal*, GO9) is the same one both vendors imply.
**Compiled:** 2026-08-23 · **Lead:** Domain Researcher · **Status:** fresh

## Headline findings
1. **Both surfaces expose a hard step/turn cap** — Copilot CLI's **`--max-autopilot-continues N`** and Claude Code's **`--max-turns N`** — explicitly to "avoid infinite loops" / bound runaway autonomous execution. *(Verified — GitHub Docs autopilot page; Claude Code headless/SDK docs corroborated by two secondary sources)*
2. **The units differ (a real asymmetry).** Copilot counts *continues* — model-initiated continuations after it judges the task "not done"; Claude counts *turns* — **every tool call is a turn**. A recommended cap value is not portable between the two without translating the unit. *(Verified — GitHub Docs; ClaudeLog / SFEIR)*
3. **Autopilot does not force work past completion.** Copilot's `stayInAutopilot` (default `true`) only keeps you *in* autopilot mode for the next prompt; the docs state explicitly it "does not cause Copilot to keep working after it has decided the task is done." Autopilot stops on: task complete (model's judgment), a blocking problem, Ctrl+C, or the continuation cap. *(Verified — GitHub Docs autopilot page)*
4. **The autonomy modes map onto a common model** across both surfaces: plan-first → autonomy mode → full-permission "YOLO" → step/turn cap → headless `-p`, with **Shift+Tab** cycling modes on both. *(Verified — both primary docs)*
5. **Two independent vendors validate the pack's GO9/CT22 stance.** Each frames the cap as a safety limit against runaway loops, i.e. its firing means the task was not bounded — exactly the pack's "a cap firing is a defect signal, not a termination argument." *(Inferred from the two vendors' framing)*

## Confidence summary
- **Verified: 9 · Inferred: 2 · Flagged: 1.** The one Flagged load-bearing item: the *exact current semantics* of Claude Code `--max-turns` were confirmed via two secondary sources and the SDK docs family this session, not read directly off the primary `cli-reference` flags table (which is alphabetical and was not paged to the `M` row) — re-verify on refresh (open question 1).

## Design implications (what the pack should do with this)
- **Answer to open question 3 (PACK-O mitigation): yes.** A rung-1 environment cap exists on *both* surfaces. The pack can recommend running autonomous/CI sessions with an explicit cap — `copilot --autopilot --yolo --max-autopilot-continues N` and `claude -p … --max-turns N` — as the belt-and-suspenders complement to the in-context front matter (CT19–CT24) and CT22. This is a **partial** mitigation (it bounds the amplifier; it does not supply the missing goal state), consistent with the proposal's own ranking.
- **Keep the caps' *unit* explicit** in any pack guidance (continues vs turns) — a "cap at 10" means different amounts of work on each surface.
- **Symmetry is achievable and cheap.** Because CT19–CT24 are surface-agnostic (goal state + `/optimize-graph` + stop discipline), the pack does not need per-surface directives; it needs one directive plus a per-surface *cap-flag* footnote. See `comparables.md` for the mapping table.
- **Sharpen the PACK-O diagnosis** with finding 3: the amplifier is not "the harness forces continuation" — autopilot *removes the natural stop-and-ask checkpoint*, so an agent that has not correctly judged completion (because no done-state was written) keeps initiating steps. The countermeasure is precisely the written goal state (CT19) plus the cap.

## How to use this base
Personas and the design skills cite these files as evidence (BoK §III.1). The `comparables.md` symmetry table is the load-bearing artifact for any pack guidance on autonomous usage. Refresh when either CLI moves (both are fast-moving; Claude Code versions its features per-release) and bump the date.
