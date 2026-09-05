---
id: api-pack-apply
title: "API — pack-apply.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  pack-apply.py — apply the AI-Forward deployment map to a repo, mechanically and reversibly.
---

# `pack-apply.py`

*Generated from `pack/scripts/pack-apply.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
pack-apply.py — apply the AI-Forward deployment map to a repo, mechanically and reversibly.

`/updatepack` and `/addpacktorepo` used to hand-apply INSTALL.md's deployment map, so every
step a person could forget - re-pasting a managed block, deleting the wrapped copy of a doc
whose load scope moved, converting CLAUDE.md to the `@AGENTS.md` import, retiring a parity
control that encoded the old invariant - was remembered or it was not. This script IS the
deployment map (INSTALL.md 1), run from the pack source against a target repo:

  pack-apply.py plan  --source <ai-forward clone> --target <repo>     # every action, no writes
  pack-apply.py apply --source <ai-forward clone> --target <repo>     # do it, idempotently

What it does, per artifact family (pack-owned names only - repo-local files are never touched):

  knowledge   -> .claude/knowledge/<name>.md verbatim; .github/instructions/<name>.instructions.md
                 (applyTo-wrapped) for load: always|glob; .github/knowledge/<name>.md for
                 load: skill|reference; the STALE copy in the other Copilot location is removed
                 (CTX-E: a doc re-scoped to on-demand must stop attaching).
  skills      -> .claude/skills/<name>/ (the whole directory: SKILL.md + reference/*.md);
                 .github/prompts/<name>.prompt.md
  agents      -> .claude/agents/ (both sets); .github/agents/<name>.agent.md (renamed, `tools:` stripped)
  bundle      -> docs/ai-forward-pack/{templates,scripts,hooks,README,OVERVIEW,research-synthesis,
                 INSTALL,context-budget.json}; .github/hooks/ai-forward.json; .claude/settings.json
                 (hooks merged, showThinkingSummaries set); .gitignore lines; docs/index.html only if
                 absent; docs/docs-index.js NEVER (V10)
  front doors -> AGENTS.md: the managed block replaced wholesale between markers (appended if absent).
                 CLAUDE.md: converted to `@AGENTS.md` + the addendum block (CTX-B); the old file is
                 backed up under docs/ai-forward-pack/retired/, and every paragraph that is NOT in
                 AGENTS.md (after toolchain-path normalisation) is kept above the addendum.
  controls    -> a repo-local parity test that asserts CLAUDE.md carries the standing-method block
                 (the OLD invariant) is rewritten into a shim asserting the NEW invariant through
                 pack-doctor, its other assertions carried over where they can be read; the original
                 is backed up beside the CLAUDE.md backup.

Repo-local deviations are honoured, not reverted: a destination that differs from the version the
repo received at its installed revision is three-way merged (`git merge-file`) against the pack's
old and new text; a clean merge lands as MERGE, a conflicting one is left untouched with the new
pack text written under docs/ai-forward-pack/conflicts/ and reported as CONFLICT for the skill to
reconcile. The installed revision advances only in `apply`. Re-running is a no-op.

Python 3.8+, stdlib only. Exit 0 = applied/clean, 1 = conflicts or errors reported, 2 = usage.
```

## CLI — options

| Option | Help |
|---|---|
| `--force` | re-apply even when the revisions match |
| `--install` | fresh install: allow a target with no installed pack |
| `--json` | emit the action rows as JSON |
| `--no-baselines` | do not run context-budget --update-baseline after applying |
| `--project` | project name for docs/index.html on a fresh install |
| `--quiet` | only the UNCHANGED rows are hidden |
| `--source` | an ai-forward clone (holds pack/) |
| `--target` | the repo to update (default: cwd) |

## Types

### `Applier`

_(no docstring — coverage gap)_

## Functions

### `read(path)`

**Coverage gap** — no docstring in the source.

### `norm_nl(text)`

**Coverage gap** — no docstring in the source.

### `same(a, b)`

Equal after newline normalisation and a stripped BOM - a CRLF checkout is not a drift.

### `frontmatter(text)`

**Coverage gap** — no docstring in the source.

### `git(args, cwd)`

**Coverage gap** — no docstring in the source.

### `strip_tools(text)`

Drop the frontmatter `tools:` line and its indented continuation (INSTALL 1.2).

### `replace_block(text, block)`

Replace the AI-FORWARD-PACK region wholesale (markers included); append if absent. The
blank line that separated the block from what follows is preserved.

### `normalise(text)`

**Coverage gap** — no docstring in the source.

### `unique_paragraphs(claude, agents)`

Paragraphs of CLAUDE.md (outside the managed block) with no counterpart in AGENTS.md after
toolchain-path normalisation; the title line and the import line are never 'unique'.

### `parity_shim(original, backup_rel)`

A PowerShell shim asserting the import invariant through pack-doctor, carrying over the
original's skill-surface needles and required-phrase checks where they can be read.

### `render_table(rows)`

**Coverage gap** — no docstring in the source.

### `summarize(rows)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **12** · documented: **5** (**42%**)
- Undocumented (recorded, not invented): `read`, `norm_nl`, `frontmatter`, `git`, `normalise`, `render_table`, `summarize`

