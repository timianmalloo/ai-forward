---
id: kb-agent-autopilot-controls-data
title: "Agent autopilot controls — Data, defaults & invariants"
type: knowledge
status: accepted
owner: "@timianmalloo"
tags: [defaults, constants, invariants]
links:
  - { to: kb-agent-autopilot-controls, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  The concrete defaults, stopping conditions, and invariants of autonomous execution on each
  surface — the numbers and rules a recommendation must respect.
---

# Data, defaults & invariants

## Stopping conditions
- **Copilot autopilot stops** on exactly one of: (a) the model judges the task complete; (b) a problem blocks progress; (c) **Ctrl+C**; (d) the **`--max-autopilot-continues`** limit is reached (if set). *(Verified — GitHub Docs autopilot page)*
- **Claude headless `-p` ends** when the run completes (exit 0), fails (non-0), hits **`--max-turns`**, or receives a signal (SIGINT = clean turn end; SIGTERM = exit 143, turn left unfinished/resumable). *(Verified — Claude Code headless docs)*

## Defaults & invariants
- **`--max-autopilot-continues` is unset by default** — autopilot has *no* continuation cap unless you pass one. The cap is opt-in. *(Verified — the doc says "if set")*
- **`--max-turns` is unset by default** — no turn cap unless supplied; recommended for all CI/unattended runs. *(Verified — headless guidance)*
- **`stayInAutopilot` default = `true`** — autopilot is sticky across tasks; it does **not** extend a single task past the model's completion judgment. *(Verified)*
- **`--allow-all` alone ≠ autopilot** — full permissions still leaves Copilot in interactive flow, stopping at decision points. Continuation requires autopilot. *(Verified)*
- **Deny rules always win** — Claude Code `permissions.deny` in `settings.json` is honoured even under `bypassPermissions`/`--dangerously-skip-permissions`. *(Verified)*
- **Claude background wait ceiling = 10 minutes** by default for `-p` (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, `0` = unbounded). *(Verified)*
- **Piped stdin cap (Claude `-p`) = 10 MB.** *(Verified — headless docs)*

## Turn/continue budgeting (secondary guidance, treat as heuristic)
Claude `--max-turns` community sizing — *(Flagged — secondary: ClaudeLog / SFEIR)*:
- simple edit: 2–4 · multi-file: 6–10 · debugging: 10–20 · complex sub-agent workflows: 40–200+.

## The invariant that matters for the pack
A firing cap (`--max-autopilot-continues` or `--max-turns`) is a **defect signal, not a resource signal** (pack GO9): when it fires, investigate the missing termination argument (the un-written goal state, PACK-O), do not simply raise the cap. Both vendors describe the cap as an anti-runaway safety net, which is consistent with — not contradictory to — this reading. *(Inferred from vendor framing + pack GO9)*
