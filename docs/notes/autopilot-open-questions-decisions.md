---
id: note-autopilot-open-questions-decisions
title: "Decisions on PACK-O open questions (logging, class granularity, autopilot caps)"
type: decision-note
status: accepted
owner: "@timianmalloo"
tags: [PACK-O, front-matter, decisions, autopilot]
links:
  - { to: defect-classes, rel: relates-to }
  - { to: kb-agent-autopilot-controls, rel: relates-to }
review-by: "2027-02-21"
summary: >-
  The user's answers to the three open questions from the task-discipline / front-matter proposal
  (revision 3), which gate the next change: making PACK-O controllable.
---

# Decisions — PACK-O open questions

Recorded from the user (2026-08-23), gating the next change (moving PACK-O from rung-3 instruction toward a rung-2 control). Confidence: **Verified** (direct user instruction).

1. **Log interactive turns?** → **Yes — log FULL substantive interactive prompts, plus timings (start and end).** This unblocks P2 (the rung-2 control): with the full prompt and duration in the audit corpus, `/dream` can mine turns where the summary exceeded the goal (scope drift) and where duration signals a runaway. Chosen over the metadata-only option. *Implication:* needs a capture mechanism (no CLI hook auto-captures interactive prompts today) and a per-prompt no-PII pass (AL4); start/end timing aligns with the AL4a duration marker already added.

2. **One PACK-O class or split it?** → **Keep one PACK-O.** Honours CI2 (capture the class, not the instance): the root cause is singular (no goal state). Detectors for the two symptoms (ceremony vs under-validation) can be built separately without splitting the class. *(No change needed — already registered as one.)*

3. **Investigate a Copilot autopilot / completion-nudge toggle?** → **Yes**, and executed as `/collectknowledge` → `docs/knowledge/agent-autopilot-controls/`. Finding: a rung-1 cap exists on **both** surfaces — Copilot `--max-autopilot-continues N` and Claude Code `--max-turns N` — with symmetry required (and achieved) between GitHub Copilot and Claude Code. The cap complements CT22 (it bounds the amplifier; it does not supply the missing goal state).

## Next steps (not done in this turn)
- Implement P2 per decision 1: capture full substantive interactive prompts + start/end timings into the audit log (mechanism TBD), then wire the `/dream` mining that makes PACK-O a rung-2 control.
- Optionally update PACK-O's control cell in `docs/lessons/defect-classes.md` to cite the environment caps (`--max-autopilot-continues` / `--max-turns`) as the rung-1 belt-and-suspenders, per `kb-agent-autopilot-controls`.
