---
id: kb-agent-autopilot-controls-glossary
title: "Agent autopilot controls — Glossary"
type: knowledge
status: accepted
owner: "@timianmalloo"
tags: [glossary]
links:
  - { to: kb-agent-autopilot-controls, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  The ubiquitous language of agent autonomy across both surfaces, defined so the two vocabularies
  can be discussed without conflation.
---

# Glossary — ubiquitous language

- **Autopilot mode (Copilot CLI)** — the mode in which Copilot continues through a task's steps without waiting for input after each one, until the task is done, blocked, interrupted, or the continuation cap is hit. *(Verified)*
- **Continue / continuation (Copilot)** — one model-initiated step taken after Copilot judges the task "not yet done." The unit counted by `--max-autopilot-continues`. *(Verified)*
- **Turn (Claude Code)** — one agentic cycle, i.e. **one tool call** (read, edit, shell). The unit counted by `--max-turns`. *Not* the same as a Copilot "continue." *(Verified)*
- **Permission mode (Claude Code)** — the named level of autonomy: `default`, `acceptEdits`, `plan`, `bypassPermissions`, `auto`. *(Verified)*
- **auto mode (Claude Code)** — a classifier-driven mode that auto-approves ordinary operations and prompts only for dangerous ones. *(Verified)*
- **YOLO / full permissions** — grant all tools/paths/URLs: Copilot `--allow-all`/`--yolo`; Claude `--dangerously-skip-permissions`/`bypassPermissions`. *(Verified)*
- **Headless / print mode** — non-interactive one-shot run: `copilot -p` / `claude -p` (`--print`). Exits after producing the result; scriptable via exit code. *(Verified)*
- **Bare mode (Claude Code)** — `--bare`: skip auto-discovery of hooks/skills/MCP/CLAUDE.md for reproducible CI runs. *(Verified)*
- **Sticky autopilot (`stayInAutopilot`)** — whether Copilot remains in autopilot for the *next* prompt after a task completes (default true). *(Verified)*
- **Plan mode** — produce and approve a plan before any action: Copilot plan mode (Shift+Tab) / Claude `plan` permission mode. *(Verified)*
- **Soft cap (AI Credit, Copilot)** — a usage limit that warns/limits but is not a hard stop; viewed/edited via `/limits`. *(Verified)*
- **Cap firing (pack term)** — a step/turn/credit limit being reached; per pack GO9 a **defect signal** about a missing termination argument, not a normal way to end. *(Verified — pack)*
