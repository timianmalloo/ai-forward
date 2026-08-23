---
id: kb-agent-autopilot-controls-comparables
title: "Agent autopilot controls — Symmetry map (Copilot CLI ↔ Claude Code)"
type: knowledge
status: accepted
owner: "@timianmalloo"
tags: [symmetry, comparables, copilot-cli, claude-code]
links:
  - { to: kb-agent-autopilot-controls, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  The load-bearing artifact: a concept-by-concept symmetry table mapping GitHub Copilot CLI
  autonomy controls to their Claude Code equivalents, plus the asymmetries that do not map
  cleanly (the step-cap unit, credit caps, sandbox model).
---

# Symmetry map — Copilot CLI ↔ Claude Code

## The common model
Both surfaces expose the same shape of autonomy control, in the same order of increasing latitude:

**plan-first mode → autonomy mode (no per-step approval) → full-permission "YOLO" → step/turn cap → headless one-shot**, with **Shift+Tab** cycling modes on both.

## Concept-by-concept mapping

| Concept | GitHub Copilot CLI | Claude Code | Confidence |
|---|---|---|---|
| **Autonomous, no per-step approval** | **autopilot mode** (`/autopilot`, `--autopilot`, Shift+Tab) | **acceptEdits** / **auto** / **bypassPermissions** permission modes (`--permission-mode`, Shift+Tab) | Verified |
| **Full permission ("YOLO")** | `--allow-all` / `--yolo` (or `/allow-all` · `/yolo`) | `--dangerously-skip-permissions` = `bypassPermissions` | Verified |
| **Hard step/turn cap** | **`--max-autopilot-continues N`** | **`--max-turns N`** | Verified* |
| **Unit the cap counts** | *continues* — model-initiated continuations after "task not done" | *turns* — **every tool call** | Verified |
| **Plan before acting** | plan mode (Shift+Tab) → "Accept plan and build on autopilot" | `plan` permission mode | Verified |
| **Headless / programmatic one-shot** | `-p "PROMPT"` (+ `--autopilot --yolo`) | `-p "PROMPT"` / `--print` (+ `--bare` for CI) | Verified |
| **Suppress clarifying questions only** | `--no-ask-user` (does not continue through steps) | (no exact analog; closest is a permission mode that auto-approves) | Verified / Inferred |
| **Mode stickiness** | `stayInAutopilot` (default true) | permission mode persists for the session; `settings.json` default | Verified |
| **Interrupt a running agent** | Ctrl+C (stop), Esc (interrupt/rewind) | Esc (interrupt); SIGINT ends turn, SIGTERM → exit 143 | Verified |
| **Restrict what tools can touch** | `/sandbox enable` (local), `copilot --cloud` (cloud sandbox) | container/devcontainer + deny rules in `settings.json` (honoured even in bypass) | Verified |
| **Usage / cost visibility** | `/usage`, `/limits` (AI-Credit **soft cap**), `/context` | `--output-format json` → `total_cost_usd` + per-model cost; usage dashboard | Verified |
| **Parallel / background sessions** | `/fleet` | `claude agents`, background sessions (`attach`/`stop`/`respawn`) | Verified |
| **Structured/reproducible run** | (settings via `/settings`, `-p`) | `--bare`, `--output-format json`, `--json-schema` | Verified |

\* `--max-turns` current semantics confirmed via SDK/headless docs + two secondary sources this session; primary flags-table row not directly paged (see open-questions).

## Asymmetries that do NOT map cleanly (watch these)
- **The cap unit** (the big one): a value of `10` means "10 model-initiated continuations" on Copilot but "10 tool calls" on Claude — the same number is a very different amount of work. Any portable guidance must translate the unit, not the number.
- **Credit vs turns as the money guard:** Copilot has an explicit **AI-Credit soft cap** (`/limits`) as a spend guard; Claude Code's spend guard in automation is effectively the **turn cap** plus plan-based usage limits and the client-side `total_cost_usd` estimate — there is no direct per-session credit-cap command equivalent. *(Inferred)*
- **Sandbox model:** Copilot ships a first-class sandbox toggle (`/sandbox`, `--cloud`); Claude Code relies on the surrounding container/VM plus settings deny-rules rather than an in-CLI sandbox switch. *(Verified for Copilot; Inferred for Claude's absence)*
- **The "middle" autonomy setting:** Copilot's `--no-ask-user` (decide-don't-ask, but don't auto-continue) has no exact Claude analog. *(Verified / Inferred)*

## Adjacent products worth noting
- **Copilot cloud agent / `/delegate`** and **Claude Code cloud sessions / self-hosted runners** are the "hand the whole task to the cloud" tier above local autonomy — out of scope here but the same autonomy spectrum extended to a remote environment. *(Verified — both docs)*
