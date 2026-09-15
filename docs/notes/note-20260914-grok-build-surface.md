---
id: note-20260914-grok-build-surface
title: "Grok Build is a third host: native .grok/ surface, shared knowledge, no rules dump"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [decision-note, grok, adapters, CTX-B]
links:
  - { to: plan-optimize-graph-grok-surface, rel: relates-to }
  - { to: proof-grok-build-surface, rel: tested-by }
review-by: "2027-03-13"
review-suggested: []
summary: >-
  Deploy a native Grok Build surface under .grok/{skills,agents,hooks,rules} rather than
  relying on Claude compatibility. Knowledge stays at .claude/knowledge/. .grok/rules/
  holds only the path map. Pack /implement overrides Grok's bundled implement in a
  pack-installed repo.
---

# Grok Build is a third host: native `.grok/` surface, shared knowledge, no rules dump

*A decision note (`knowledge-visualization.md` V17).*

- **Kind:** decision
- **Confidence:** Verified (Grok user-guide 08-skills, 12-project-rules, 16-subagents, 10-hooks, 05-configuration read 2026-09-14; pack-apply dests proven by test)
- **Made during:** `/implement` of the Grok Build surface (revision 71)

## The call

Grok Build already loads root `AGENTS.md` and, with Claude compatibility on (the default), discovers `.claude/skills/`. That is not a Grok install: `[compat.claude] skills = false` drops skills; personas belong in `.grok/agents/` not `.claude/agents/`; Copilot wraps are not auto-applied; hooks live in Claude/Copilot configs.

So `pack-apply.py` deploys native destinations:

- `.grok/skills/<name>/` — same `SKILL.md` as Claude Code
- `.grok/agents/<name>.md` — `_agent` suffix stripped, `tools:` stripped
- `.grok/hooks/ai-forward.json` — `--host grok`
- `.grok/rules/grok-surface.md` — path map only

Knowledge is **not** copied into `.grok/rules/`. Grok loads every `*.md` in that directory on every turn (user-guide 12-project-rules). Dumping the 38 knowledge docs would be CTX-B. Grok reads `AGENTS.md` natively and the shared `.claude/knowledge/` copies on demand.

Pack `/implement` at `.grok/skills/implement/` **overrides** Grok's bundled implement skill. Intended: a pack-installed repo runs the Rigor Protocol loop.

No Rhai workflows in this revision. Skills *are* the workflows. `.grok/workflows/` remains available.

## Alternatives dismissed

- **Rely on Claude compatibility only.** Fails closed when the user disables `[compat.claude] skills`. Personas still would not be at the documented Grok agent path.
- **Copy always-on knowledge into `.grok/rules/`.** Attaches the full constitution twice (AGENTS.md + the docs). CTX-B.
- **Prefix every skill (`aif-implement`).** Avoids the bundled `/implement` collision but makes `/specify` a different name than Claude/Copilot. One collision, documented, is cheaper than renaming the roster.
- **Author 27 Rhai workflows.** Duplicates SKILL.md. Skills already auto-invoke.

## Validation / revisit if

Grok stops scanning `.grok/skills/` or `.grok/agents/`; Claude compatibility becomes off-by-default and the native surface is missing files; a future Grok release loads `.grok/rules/` with a cap that makes the path map too expensive (then shrink it further).
