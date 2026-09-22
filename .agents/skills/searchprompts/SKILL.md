---
name: searchprompts
description: Search your logged prompts by freeform text and reuse a match — the same arrow-navigable expand/collapse stack as /prompts, pre-filtered to prompts whose label or text contains all your terms. A utility skill backed by the stdlib prompt-log engine.
---

# Codex host mapping

Codex reads the shared root `AGENTS.md`. Knowledge remains at `.claude/knowledge/`;
resolve a pack `knowledge/<name>.md` reference there. Do not load `CLAUDE.md` as a
second constitution. Skills are `.agents/skills/<name>/SKILL.md`, including their
reference directories. Invoke a skill with `$name` or select it using `/skills`.

Personas are generated at `.codex/agents/<name>.toml`. Ask Codex to delegate to the
named persona. Use the actual exposed spawning tool's signature: host APIs differ.
If it has no named-persona selector, read that persona's `developer_instructions`
and include those instructions in the separate agent's task. Never pass Claude's
`subagent_type` or Grok's `spawn_subagent` arguments to a tool without those fields.
Keep author and hard-veto reviewer in separate agent contexts. Inherit the user's
model and permission choices; the pack does not override them.

Claude tool names in shared workflow prose describe operations: `Read` means read
the named file with the available file/shell tool; `Grep` means a targeted `rg`
search; `Glob` means file discovery; `Edit`/`Write` means the available patch or
file-writing tool; `Bash` means the available shell tool; `Task` means delegation
through the available subagent tool. Inspect tool signatures before use. Do not
invoke `EnterWorktree` or `ExitWorktree`; the root agent uses the documented
`coord-core.py worktree` lifecycle, and child agents use absolute paths.

Native hooks are merged into `.codex/hooks.json`. Project trust and review of each
hook through `/hooks` are required; a changed hook needs review again. Existing
`.codex/config.toml` settings, including disabled hooks, are preserved. The pack
does not grant trust, change approvals, or add a permission bypass.

# Skill: /searchprompts

A **utility skill** (not a Rigor-Protocol workflow): find a past prompt by **freeform text**, then reuse it. It is **/prompts pre-filtered** — you give search terms, and the same interactive **stack (newest on top)** opens over just the prompts whose label or body contains **all** your terms (case-insensitive). Navigate with **↑/↓**, **→** to expand a match and read it in full, **←** to collapse, **Enter** to reuse (copies it to your clipboard to paste-and-edit).

Companion skill: **/prompts** (the full stack, unfiltered). Both are reuse lenses over the same unified **audit log** (`docs/audit/audit-log.jsonl`); the broader timeline/search/change-log/viewer is **/auditlog**.

## Engine
All behavior is in the stdlib script **`docs/ai-forward-pack/scripts/prompt-log.py`** (in this source repo: `pack/scripts/prompt-log.py`). **Unified store:** prompts come from the committed **audit log** `docs/audit/audit-log.jsonl` (the same store `/auditlog` reads); `add` writes a `kind:prompt` entry through `audit-log.py`. Override with `--store` (e.g. a legacy `<repo>/.aiforward/prompts.jsonl`) or `$AIFORWARD_PROMPT_LOG`; the reader adapts to either schema.

## What this skill does
1. **Run the filtered interactive browser** with the user's terms:
   `python3 docs/ai-forward-pack/scripts/prompt-log.py pick <terms...>`
   - matches contain **all** terms; the stack is newest-first.
   - ↑/↓ move · → expand · ← collapse · `/` refine the filter · **Enter** reuse · `q` quit.
2. **If there is no interactive terminal**, the script prints the matching stack as a numbered list (newest first). Render it, let the user pick a number, then `prompt-log.py show <n>` to expand and `prompt-log.py get <n> --copy` to put it on the clipboard.
   - You may also run the non-interactive search directly: `prompt-log.py search <terms...>` (add `--json` for structured output).
3. **Reuse:** the user pastes the copied prompt into their next CLI prompt and edits before executing.

## In both list and interactive views
The list shows **label + timestamp**; when you are *on* a prompt, **→ expands** it to the full text and **← collapses** it back to the label — so you can scan labels fast and open only the ones you want.

## Definition of done
- [ ] The matches (label · time) for the user's terms were shown newest-first.
- [ ] The user could expand/collapse and pick one; the chosen prompt is on the clipboard (or printed) for paste-and-edit — never executed for them.
- [ ] If nothing matched, that was stated plainly (no fabricated results).

**Handoff:** none — utility skill. Companion: **/prompts**.
