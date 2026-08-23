---
id: kb-agent-autopilot-controls-references
title: "Agent autopilot controls — Reference (flags, settings, commands)"
type: knowledge
status: accepted
owner: "@timianmalloo"
tags: [reference, flags, settings, commands]
links:
  - { to: kb-agent-autopilot-controls, rel: relates-to }
review-by: "2026-11-21"
summary: >-
  The authoritative flag/setting/command surface for autonomous execution on each CLI, with the
  primary-source page for each.
---

# Reference — flags, settings, commands

## GitHub Copilot CLI (primary: GitHub Docs)
Command-line options:
- **`--autopilot`** — start in autopilot mode. *(Verified)*
- **`--max-autopilot-continues N`** — cap autonomous continuations before stopping. *(Verified)*
- **`--allow-all`** / **`--yolo`** — allow all tools, paths, URLs. *(Verified)*
- **`--no-ask-user`** — suppress clarifying questions (decide, don't ask). *(Verified)*
- **`--cloud`** — run the session in a cloud sandbox. *(Verified)*
- **`-p "PROMPT"`** — programmatic/one-shot prompt (scriptable). *(Verified)*
- **`--agent=NAME`**, **`--continue`**, **`--resume`**. *(Verified)*

Slash commands / settings:
- **`/autopilot`** — toggle autopilot. *(Verified — in-product help)*
- **`/allow-all`** (`/yolo`) — grant full permissions mid-session (not a toggle-off). *(Verified)*
- **`/permissions`**, **`/allow-all`**, **`/add-dir`**, **`/reset-allowed-tools`** — permission surface. *(Verified)*
- **`/sandbox enable`** — local sandbox. *(Verified)*
- **`/limits`** — session limits; AI-Credit limit is a **soft cap**. *(Verified)*
- **`/usage`**, **`/context`**, **`/compact`** — usage/context management. *(Verified)*
- **`/settings KEY VALUE`** / `~/.copilot/settings.json` — e.g. **`stayInAutopilot`** (bool, default true). Full list: Copilot CLI configuration reference. *(Verified)*
- **Shift+Tab** — cycle interactive / plan / autopilot modes. *(Verified)*

## Claude Code (primary: code.claude.com/docs)
CLI commands:
- **`claude`** / **`claude "query"`** — interactive. **`claude -p "query"`** — headless one-shot (SDK), exit 0/non-0. **`claude -c`** — continue; **`claude -r "<session>"`** — resume. *(Verified)*
- **`claude auto-mode defaults|config|reset`** — inspect/reset the auto-mode classifier. *(Verified)*
- **`claude agents` / `attach` / `stop` / `respawn`** — background/parallel sessions. *(Verified)*

CLI flags:
- **`--permission-mode <default|acceptEdits|plan|bypassPermissions|auto>`** — autonomy ladder. *(Verified for default/acceptEdits/plan/bypassPermissions; auto Verified via auto-mode)*
- **`--dangerously-skip-permissions`** / **`--allow-dangerously-skip-permissions`** — full bypass / add bypass to the Shift+Tab cycle. *(Verified)*
- **`--max-turns N`** — cap agentic turns (tool calls) in headless runs. *(Verified — SDK/headless docs + secondary corroboration)*
- **`--allowedTools` / `--allowed-tools`**, **`--tools`**, **`--add-dir`** — tool/dir allow surface. *(Verified)*
- **`--bare`** — skip auto-discovery for reproducible CI runs. *(Verified)*
- **`--output-format text|json|stream-json`**, **`--json-schema`**, **`--verbose`**, **`--include-partial-messages`**. *(Verified)*

Settings / env:
- **`~/.claude/settings.json`** — default permission mode, `autoMode` section, `permissions.deny` (honoured even under bypass). *(Verified)*
- **`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`** — background-subagent wait cap for `-p` (default 10 min; `0` = unbounded). *(Verified)*

## Authoritative pages
- Copilot autopilot: `https://docs.github.com/en/copilot/concepts/agents/copilot-cli/autopilot`
- Copilot CLI usage: `https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli`
- Copilot CLI config/command reference: `https://docs.github.com/en/copilot/reference/copilot-cli-reference/`
- Claude Code CLI reference: `https://code.claude.com/docs/en/cli-reference`
- Claude Code headless: `https://code.claude.com/docs/en/headless`
- Claude Code permission modes: `https://code.claude.com/docs/en/permission-modes`
