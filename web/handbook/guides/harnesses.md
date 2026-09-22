# Choose the right AI harness for the work

AI-Forward is installed into several agent harnesses. A harness is the application that gives a model instructions, tools, a workspace and interaction controls. The pack tries to present the same workflows across them, but the hosts are not identical. Treat a harness as qualified only for the behavior you have checked on the current machine and repository.

## Common starting point

Most harnesses read the repository's root instructions and then discover pack skills from host-specific paths. The workflow names are the same: `/specify`, `/design-slice`, `/implement`, `/investigate`, and so on. Codex uses `$skill` selection rather than registering these as slash commands.

Scripts are not global commands. When a skill tells you to run a script, use the installed path under `docs/ai-forward-pack/scripts/`. On Linux and macOS, examples often use `python3`. On Windows, use `python` or `py -3` unless your environment has a real `python3.exe`.

## Claude Code

Claude Code reads `CLAUDE.md`, which imports `AGENTS.md` in an installed repo. Skills live under `.claude/skills/<name>/SKILL.md`, and persona definitions live under `.claude/agents/`. Knowledge files are under `.claude/knowledge/`.

Use slash skill names such as:

```text
/specify Add CSV export for every task matching the current HarborTasks filter.
```

If hooks are installed, they can warn about repeated reads and mark session starts. A warning is a prompt to reuse context, not a reason to hide evidence.

## GitHub Copilot CLI

Copilot CLI loads root instruction files and `.github/instructions/`. Skills are available through `/skills` and pack prompts under `.github/prompts/`. The built-in help confirms current CLI commands such as `/skills`, `/model`, `/settings`, `/subagents`, `/worktree`, `/autopilot`, `/tasks`, `/permissions` and `/instructions`.

For ordinary work, invoke the pack skill through the skill picker or by asking for the named workflow:

```text
/specify Add CSV export for every task matching the current HarborTasks filter.
```

For coordinated native Copilot workers, the pack has a stricter qualified profile. The profile uses an explicit native model argument, calls the native model setter before the first prompt, and reads back actual assistant-message and usage model evidence before the worker is considered ready. A requested model ID is not proof of the model that ran. If your run is GPT-only, pin the Owner, workers and native subagents to the exact allowed GPT model and check actual inference evidence. Do not rely on automatic routing.

The current profile also requires an explicitly emitted local plugin bundle for the qualified Windows path. Repository-hook files alone are not treated as proof that Copilot executed the coordination controls. Re-emit and requalify after changing the hook scripts or plugin bundle.

## Codex

Codex reads `AGENTS.md` and discovers skills from `.agents/skills/<name>/SKILL.md`. Use `$collectknowledge`, `$specify`, `$implement`, or the `/skills` selector. If slash notation appears as text, resolve the named pack skill and read its `SKILL.md`.

Example:

```text
$specify Add CSV export for every task matching the current HarborTasks filter.
```

Codex does not automatically inherit Copilot, Claude, Grok or Antigravity hooks. Where no Codex hook is installed, start and close audit or coordination steps explicitly. The optional Codex ownership guard must be emitted and reviewed for the project; do not assume a generic native hook or terminal attachment exists.

Codex queueing can deliver a pointer into an existing thread when available, but an incoming turn is not proof of the transport. Check the local `codex queue --help` before depending on it. If unavailable, paste the same pointer and authorization manually.

## Grok Build

Grok Build reads root `AGENTS.md`. Pack skills live under `.grok/skills/<name>/SKILL.md` and are invoked with the familiar slash names. `.grok/rules/grok-surface.md` is a path map, not a place to paste all knowledge.

Folder trust is required before project hooks run. Some hook behaviors may be observed-only in a given version. Treat “hook configured” and “hook enforced” as different claims.

## Antigravity

Antigravity reads root `AGENTS.md`. Skills live under `.agents/skills/<name>/SKILL.md` and are discoverable through `.agents/skills.json`. Knowledge remains in the shared `.claude/knowledge/` copies. Persona work can be enacted inline or through host subagent mechanisms.

Antigravity hook configuration lives in `.agents/hooks.json`. Launch with `AGENT_SESSION=<id>` when coordination needs session identity. Some events may fire only when the folder is a registered project, so qualify the actual startup path you use.

## How to choose

Choose the harness that is qualified for the behavior the task needs:

- use the harness you already trust for a single coherent implementation;
- use Codex when `$skill` selection and explicit script-driven work fit your environment;
- use Copilot CLI when its repository context, plugins and native model evidence are qualified for the task;
- use Grok or Antigravity when their installed path maps and hook status are verified for the repo;
- fall back to human-brief mode for coordination when a native worker profile is unqualified.

The fallback is not failure. A pasted brief in a known-good session is safer than an unqualified launch that looks automated but cannot prove instructions, permissions, identity or model selection.

## What to check before relying on a harness

Check the installed paths, the skill inventory, the model selection mechanism, the actual model readback when it matters, hook status, workspace trust, permissions and whether the host can run in the assigned worktree. For coordination, check that the worker can receive its brief, write only its assigned files, return evidence, and stop for Owner decisions.

If any of those are missing, narrow the mode. Use a manual brief, a serial session, or a different harness. Do not convert “not checked” into a success-shaped claim.

## Where to go next

Use [coordinate work without losing ownership](#coordination) for multi-session work. Use [start with one small task](#get-started) for first use. Use [the skill reference](#skills) to choose the workflow before choosing the host.
