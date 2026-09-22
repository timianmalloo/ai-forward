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
