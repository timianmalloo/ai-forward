---
id: api-graphify-setup
title: "API — graphify-setup.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  graphify-setup.py - stand up the CODE knowledge graph and join it to the docs graph.
---

# `graphify-setup.py`

*Generated from `pack/scripts/graphify-setup.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
graphify-setup.py - stand up the CODE knowledge graph and join it to the docs graph.

WHAT THIS IS
  Graphify (graphify.com, Apache 2.0, PyPI `graphifyy`) builds an on-device knowledge graph
  of a codebase that an AI assistant queries instead of grepping, with file:line citations and
  a provenance tag on every edge. This script wires it into an AI-Forward repo and - the part
  that does not exist anywhere else - JOINS it to the pack's documentation graph.

  A repository has two knowledge graphs and the expensive defects live in the gap between them:
    * the DOCS graph (docs-index.js, from V2 frontmatter) holds INTENT
    * the CODE graph (graphify-out/graph.json)          holds REALITY
  Nothing normally traverses both, which is exactly why documentation drifts from code. --join
  computes the two gaps that matter: documentation with no implementation, and risk with no
  governance.

DESIGN RULES THIS HONORS  (knowledge/code-knowledge-graph.md, GK1-GK16)
  * The docs graph stays the record; the code graph is a derived build output (GK2-GK3).
  * Graph the SOURCE, never its generated projections (GK4) - .graphifyignore does this.
  * Provenance is carried through: EXTRACTED -> Verified, INFERRED -> Inferred,
    AMBIGUOUS -> Flagged (GK6). A citation is not a promotion.
  * The join is a LENS: derived, never authoritative, and a prompt rather than a gate (GK11).

USAGE
  graphify-setup.py --check                # is graphify installed, built, ignored, joined?
  graphify-setup.py --install              # uv tool install graphifyy + register the skill
  graphify-setup.py --init                 # write .graphifyignore + .gitignore rules
  graphify-setup.py --build                # full, ignore-respecting re-extraction
  graphify-setup.py --join                 # write docs/lenses/code-doc-join.md
  ... --root <repo> --platform claude,copilot --dry-run --json

Stdlib only. Python 3.8+. Exit 0 on success, 1 on error, 2 on --check findings.
```

## CLI — options

| Option | Help |
|---|---|
| `--build` | full ignore-respecting re-extraction |
| `--check` | report state, write nothing (default) |
| `--dry-run` | _(no help text — coverage gap)_ |
| `--init` | write .graphifyignore and the .gitignore rule |
| `--install` | install graphifyy and register the skill |
| `--join` | write docs/lenses/code-doc-join.md |
| `--json` | machine-readable join output |
| `--platform` | assistants to register (default: claude,copilot) |
| `--root` | repository root (default: .) |
| `--top` | ungoverned symbols to report (default 15) |

## Functions

### `detect_repo_kind(root)`

Return (kind, canonical, rules). Detect - never assume - which copy is authoritative.

### `ignore_template(root, tool=…)`

**Coverage gap** — no docstring in the source.

### `out(msg=…)`

**Coverage gap** — no docstring in the source.

### `write_text(path, text, dry)`

**Coverage gap** — no docstring in the source.

### `graphify_exe()`

Resolve the CLI, including uv's tool dir which is often not on PATH in a fresh shell.

### `run(cmd, cwd, dry, label)`

**Coverage gap** — no docstring in the source.

### `load_code_graph(root)`

**Coverage gap** — no docstring in the source.

### `load_docs_graph(root)`

**Coverage gap** — no docstring in the source.

### `resolve_reference(root, artifact_path, ref)`

Resolve a referenced path the way a reader would: relative to the artifact first
(so `../web/index.html` inside docs/index.md works), then relative to the repo root.
Returns (normalised_repo_relative_path, exists).

### `join_graphs(root, code, docs, top_n=…)`

Compute the two gaps between intent and reality (GK11).

### `render_join(j)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **11** · documented: **4** (**36%**)
- Undocumented (recorded, not invented): `ignore_template`, `out`, `write_text`, `run`, `load_code_graph`, `load_docs_graph`, `render_join`

