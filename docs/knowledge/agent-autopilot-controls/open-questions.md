---
id: kb-agent-autopilot-controls-open-questions
title: "Agent autopilot controls — Open questions & failure modes"
type: knowledge
status: accepted
owner: "@timianmalloo"
tags: [open-questions, failure-modes, disconfirmation]
links:
  - { to: kb-agent-autopilot-controls, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  What this research could not fully settle, the failure modes of autonomous execution, and the
  disconfirming views deliberately sought.
---

# Open questions & domain failure modes

## Unresolved by research (re-verify on refresh)
1. **Exact current `--max-turns` semantics on the primary page.** Confirmed via the Claude Code SDK/headless docs family and two secondary sources (ClaudeLog, SFEIR) this session; the primary `cli-reference` flags table is alphabetical and was not paged to the `M` row, so the precise wording/version note was not read first-hand. Load-bearing for the symmetry claim → re-read the primary flags row on refresh. *(Flagged)*
2. **Does Copilot CLI expose a `--max-turns`-style cap counted in tool calls, or only in continues?** Only `--max-autopilot-continues` (continuation-counted) was found. If a tool-call-level cap exists it was not surfaced. *(Flagged)*
3. **Claude Code in-CLI sandbox** — no first-class `/sandbox`-equivalent toggle was found; Claude appears to rely on the surrounding container + deny-rules. Confirm whether a sandbox switch exists in a current version. *(Flagged)*
4. **Whether `--no-ask-user` (Copilot) has any Claude analog** beyond choosing a permission mode. *(Flagged)*

## Known failure modes of autonomous execution
- **Runaway with no cap set** — both caps are **opt-in and unset by default**, so an unattended run with a bad prompt can loop until credits/turns are exhausted or a human intervenes. The default is *unbounded*. *(Verified)*
- **Cap-as-crutch** — raising the cap when it fires, instead of fixing the missing goal state (pack GO9 / CT22). The cap firing is the symptom. *(Verified — pack)*
- **Full-permission blast radius** — `--yolo` / `--dangerously-skip-permissions` grant delete/execute authority; combined with autonomy this is the highest-risk configuration. Vendors recommend sandboxes/CI only. *(Verified)*
- **Silent completion misjudgment** — autopilot stops when the *model* judges the task complete; with no written done-state (PACK-O) that judgment is unreliable in both directions (stops early, or keeps initiating steps). *(Inferred — this is the PACK-O mechanism)*

## Disconfirming views deliberately sought
- **"Autopilot runs forever / the harness forces continuation."** *Disconfirmed by the primary source:* Copilot autopilot stops at the model's completion judgment, and `stayInAutopilot` explicitly "does not cause Copilot to keep working after it has decided the task is done." So the PACK-O amplifier is **not** a harness that forces work — it is autonomy *removing the stop-and-ask checkpoint*. This sharpened the pack's diagnosis rather than confirming the initial framing.
- **"The step cap is the real fix for runaways."** *Partially disconfirmed:* the cap bounds the blast radius but does not supply the missing goal state; it is a rung-1 mitigation of the amplifier, not a fix for the defect (consistent with the proposal ranking the toggle/cap below the front matter).
