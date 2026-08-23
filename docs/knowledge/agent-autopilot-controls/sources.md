---
id: kb-agent-autopilot-controls-sources
title: "Agent autopilot controls — Sources"
type: knowledge
status: accepted
owner: "@timianmalloo"
tags: [sources]
links:
  - { to: kb-agent-autopilot-controls, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  Full source list with access dates and the claims each supports. Primary vendor docs first.
---

# Sources

| # | Title / source | Type | URL | Accessed | Used for |
|---|---|---|---|---|---|
| 1 | GitHub Docs — "Allowing GitHub Copilot CLI to work autonomously" (autopilot) | primary | https://docs.github.com/en/copilot/concepts/agents/copilot-cli/autopilot | 2026-08-23 | `--max-autopilot-continues`, `stayInAutopilot`, stopping conditions, `--allow-all`/`--yolo`, `--no-ask-user`, plan→autopilot, sandbox interplay, programmatic usage |
| 2 | GitHub Docs — "Using GitHub Copilot CLI" | primary | https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli | 2026-08-23 | tool-approval flow, `--allow-all`/`--yolo`, `/sandbox`, `--cloud`, `/settings`, `/usage`/`/context`/`/compact`, custom agents, `-p` |
| 3 | GitHub Copilot CLI in-product help (`copilot help` / `?`) | primary (self-doc) | (local CLI v1.0.80) | 2026-08-23 | `/autopilot`, `/limits` (AI-Credit soft cap), `/fleet`, `/permissions`, `/allow-all`, Shift+Tab modes, Ctrl+C/Esc |
| 4 | Claude Code Docs — "CLI reference" | primary | https://code.claude.com/docs/en/cli-reference | 2026-08-23 | commands (`claude`, `-p`, `-c`, `-r`), `auto-mode`, `--dangerously-skip-permissions`/`--allow-dangerously-skip-permissions`, `--allowedTools`, background sessions, permission-mode references |
| 5 | Claude Code Docs — "Run Claude Code programmatically" (headless) | primary | https://code.claude.com/docs/en/headless | 2026-08-23 | `-p`/`--print`, `--bare`, `--output-format`/`--json-schema`, SIGTERM/SIGINT (exit 143), background wait ceiling (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`), stdin 10 MB cap |
| 6 | Claude Code Docs — "Configure permissions" / permission modes | primary | https://code.claude.com/docs/en/permission-modes | 2026-08-23 | `default`/`acceptEdits`/`plan`/`bypassPermissions`/`auto`, deny rules honoured under bypass |
| 7 | ClaudeLog FAQ — "What is --max-turns in Claude Code" | secondary | https://claudelog.com/faqs/what-is-max-turns-in-claude-code/ | 2026-08-23 | `--max-turns` semantics (each tool call = a turn), turn-budgeting heuristic |
| 8 | SFEIR Institute — Claude Code Headless Mode & CI/CD command reference | secondary | https://institute.sfeir.com/en/claude-code/claude-code-headless-mode-and-ci-cd/command-reference/ | 2026-08-23 | `--max-turns` corroboration, headless/CI patterns |

**Sourcing note:** claims labelled *Verified* rest on the primary vendor docs (#1–#6). `--max-turns` (#7–#8) is corroborated by two secondary sources plus the SDK/headless doc family and is treated as Verified, with the primary flags-table row flagged for direct re-read on refresh (open question 1). Both CLIs move fast — re-verify version-sensitive flags when refreshing.
