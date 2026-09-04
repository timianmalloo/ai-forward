---
id: api-visual-assets-setup
title: "API — visual-assets-setup.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  visual-assets-setup.py - wire up a generation backend for UI visual assets (AI-Forward).
---

# `visual-assets-setup.py`

*Generated from `pack/scripts/visual-assets-setup.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
visual-assets-setup.py - wire up a generation backend for UI visual assets (AI-Forward).

`ui-visual-assets.md` (VA1-VA18) governs *whether and how* imagery, personas and motion
may be generated for a UI. This script is the *mechanism*: it reports which generation
backends a repo can actually reach, scaffolds the asset directory and manifest, and keeps
the credential and hygiene rules that VA9/VA11 depend on. Stdlib only; lives in the script
bundle (deployed to docs/ai-forward-pack/scripts/).

It deliberately does NOT generate anything and NEVER writes a credential. Generation runs
through the `/visualize` skill against whichever backend is configured; secrets live in the
environment or the agent host's own MCP configuration, never in the repository.

Modes
  --check      what is configured, what is missing, and exactly how to fix it
  --init       scaffold docs/assets/, the DESIGN.md assets manifest, and .gitignore hygiene
  --init-mcp   write a GIT-IGNORED project-level .mcp.json for an MCP backend, plus a
               committed .mcp.json.example. Credentials come from the environment, or are
               reused from an agent-host config that already has them. Never committed.
  --backends   print the backend capability matrix and exit
  --dry-run    with --init/--init-mcp: print what would change, write nothing
  --json       machine-readable output for --check

Exit codes: 0 fine, 1 nothing usable is configured (with --check), 2 a hygiene problem was
found that needs a human (a credential appears to be committed).

Usage:
  visual-assets-setup.py --check [--json]
  visual-assets-setup.py --init [--dry-run]
  visual-assets-setup.py --backends
```

## CLI — options

| Option | Help |
|---|---|
| `--backends` | print the capability matrix |
| `--check` | report what is configured |
| `--dry-run` | with --init/--init-mcp, write nothing |
| `--init-mcp` | write a git-ignored project .mcp.json (+ committed .example) for an MCP backend (default: higgsfield) |
| `--init` | scaffold assets dir, manifest and hygiene |
| `--json` | machine-readable --check |
| `--root` | repository root (default: .) |

## Functions

### `repo_paths(root)`

**Coverage gap** — no docstring in the source.

### `find_design_md(root)`

VA12's manifest lives in the design language. Resolve it the way the craft
detector does (repo root, then docs/) so both tools agree on one file (CD4).

### `backend_status(name, spec)`

**Coverage gap** — no docstring in the source.

### `scan_for_committed_secrets(root)`

A generation credential in the tree is a hygiene failure, not a style issue.
Deliberately shallow and cheap: a first-pass tripwire, not a scanner (see the
Responsible-AI policy - real enforcement belongs in CI secret scanning).

### `resolve_mcp_entry(spec)`

Find the installed server entry point. Established by looking, not assumed:
the global npm root differs per platform and per install method.

### `read_user_mcp_credentials(spec)`

Reuse credentials already configured in the agent host, so `--init-mcp` works for
someone who set the server up interactively and never exported the variables.
Returns (creds, source) and NEVER logs a value.

### `cmd_init_mcp(root, backend, dry_run)`

Write a GIT-IGNORED project-level .mcp.json plus a committed .example.

Copilot CLI reads project config from `.mcp.json` (cwd up to the repo root) and
`.github/mcp.json`, and project definitions take precedence over the user config.
Verified from the official docs. What is NOT established is `${VAR}` expansion inside
the `env` block - the docs say environment variables "must be configured here" and the
changelog only documents auto-inclusion for vars referenced in command/args/cwd. So a
committed config cannot carry the credentials, and this writes a git-ignored one
instead of relying on expansion that was never verified (NG1/NG6).

### `cmd_backends()`

**Coverage gap** — no docstring in the source.

### `cmd_check(root, as_json)`

**Coverage gap** — no docstring in the source.

### `ensure_gitignore(root, dry_run)`

**Coverage gap** — no docstring in the source.

### `ensure_manifest(root, dry_run)`

**Coverage gap** — no docstring in the source.

### `cmd_init(root, dry_run)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **12** · documented: **5** (**42%**)
- Undocumented (recorded, not invented): `repo_paths`, `backend_status`, `cmd_backends`, `cmd_check`, `ensure_gitignore`, `ensure_manifest`, `cmd_init`

