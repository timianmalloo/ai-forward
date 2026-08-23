---
id: kb-agent-autopilot-controls-sota
title: "Agent autopilot controls — State of the Art"
type: knowledge
status: accepted
owner: "@timianmalloo"
tags: [autopilot, permission-modes, state-of-the-art]
links:
  - { to: kb-agent-autopilot-controls, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  How the two surfaces implement autonomous execution today: Copilot CLI's autopilot mode + its
  permission and continuation switches, and Claude Code's permission-mode ladder (default →
  acceptEdits → auto → bypassPermissions) plus its headless -p / --max-turns automation model.
---

# State of the art — agent autopilot controls

## GitHub Copilot CLI

- **Autopilot mode** — Copilot works through a task "without waiting for your input after each step," until the model judges the task complete, a problem blocks it, you press **Ctrl+C**, or the continuation cap is reached. Enter it by pressing **Shift+Tab** to cycle modes, or start with the `--autopilot` flag. *(Verified — GitHub Docs, "Allowing GitHub Copilot CLI to work autonomously")*
- **`--max-autopilot-continues N`** — the safety cap: "limits how many steps it can take before stopping, to avoid infinite loops." Settable at session start (`copilot --allow-all --max-autopilot-continues 10`) or with autopilot programmatically. *(Verified — GitHub Docs autopilot page)*
- **`--allow-all` / `--yolo`** — grant the agent all tools, paths and URLs. With `--allow-all` alone you are *still in the normal interactive flow* (Copilot still stops at decision points); it only removes the per-tool approval. Autopilot is what removes the stop-and-ask between steps. `/allow-all` (alias `/yolo`) does the same mid-session and does **not** toggle back off. *(Verified — GitHub Docs)*
- **`--no-ask-user`** — suppresses the clarifying questions Copilot would otherwise ask, forcing the agent to decide on its own. Unlike autopilot it does **not** let the agent continue through successive model-driven steps, and it does **not** consume extra AI credits without your involvement. A "middle" autonomy setting. *(Verified — GitHub Docs autopilot page)*
- **`stayInAutopilot` (default `true`)** — autopilot is "sticky": after a task completes you remain in autopilot for the next prompt. Set `false` (via `/settings stayInAutopilot false` or `~/.copilot/settings.json`) to drop back to interactive after each task. The docs are explicit that this setting "only controls which mode you are in *after* a task completes. It does not cause Copilot to keep working after it has decided the task is done." *(Verified — GitHub Docs autopilot page)*
- **Sandboxing** — `/sandbox enable` restricts what the agent's commands can touch (local sandbox); `copilot --cloud` runs the whole session in an isolated cloud sandbox. In autopilot + local sandbox, anything achievable inside the sandbox runs uninterrupted; a step that must escape it is denied. *(Verified — GitHub Docs)*
- **Plan → autopilot workflow** — the recommended shape: Shift+Tab into **plan mode**, build a plan interactively, then "Accept plan and build on autopilot." *(Verified — GitHub Docs)*
- **`/limits`** — view/edit session limits; the AI-Credit limit is a **soft cap**. `/usage` shows credits used, session duration, lines edited, and per-model token usage. *(Verified — `copilot` in-product help; GitHub Docs context-management section)*

## Claude Code

- **Permission modes (`--permission-mode`)** — a ladder of increasing autonomy: **default** (prompts before edits/shell), **acceptEdits** (auto-approves reads/edits and common FS commands, still prompts for shell), **plan** (produce a plan, approve before acting), **bypassPermissions** (skip *all* checks). Cycle interactively with **Shift+Tab**; set a default in `~/.claude/settings.json`. *(Verified — Claude Code CLI reference + permission-modes docs)*
- **`auto` mode (auto-mode classifier)** — a newer mode (Claude Code v2.1.208+) that "eliminates prompts" by running a **classifier** that auto-approves ordinary operations and only prompts for genuinely dangerous ones. Inspect it with `claude auto-mode defaults` / `claude auto-mode config`; reset with `claude auto-mode reset`. Configured via an `autoMode` section in settings. *(Verified — Claude Code CLI reference)*
- **`--dangerously-skip-permissions`** (alias behaviour of `bypassPermissions`; `--allow-dangerously-skip-permissions` adds it to the Shift+Tab cycle without starting in it) — the full "YOLO": auto-approve everything including shell. Vendor and community guidance: sandboxes/CI/containers only. Deny rules in `settings.json` are still honoured even here. *(Verified — Claude Code CLI reference)*
- **`--max-turns N`** — caps the number of **agentic turns** (each tool call = one turn) in a headless/non-interactive run, "to avoid runaway processes, infinite loops, and excessive resource usage." The direct analog of Copilot's `--max-autopilot-continues`, differing in the counted unit. *(Verified — Claude Code SDK/headless docs, corroborated by ClaudeLog and SFEIR)*
- **Headless / programmatic (`-p` / `--print`)** — run non-interactively; exits 0 on success, non-zero on failure (scripts branch on exit code). `--bare` skips auto-discovery of hooks/skills/MCP/CLAUDE.md for reproducible CI runs (and is slated to become the `-p` default). `--output-format text|json|stream-json`; `json` carries `total_cost_usd` and per-model cost (client-side estimates). *(Verified — Claude Code headless docs)*
- **Signals & background caps** — SIGINT ends the current turn cleanly; SIGTERM exits 143 leaving the turn unfinished (resumable). Background subagents block `claude -p` exit up to a **10-minute default ceiling** (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, `0` = unbounded). *(Verified — Claude Code headless docs)*

## The frontier / where it is moving
- Both CLIs are fast-moving; Claude Code documents features per-version (e.g. auto-mode v2.1.208+, import v2.1.213+), so any specific flag semantics carry a version caveat. *(Verified — Claude Code CLI reference version notes)*
- Convergence is visible: both now offer plan-first modes, Shift+Tab mode cycling, background/parallel sessions (Copilot `/fleet`; Claude `claude agents`/background sessions), and headless automation — the surfaces are becoming feature-symmetric. *(Inferred from the two docs)*
