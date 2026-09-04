---
id: api-obsidian-setup
title: "API — obsidian-setup.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  obsidian-setup.py - stand up (and analyze) the Obsidian lens over an AI-Forward docs graph.
---

# `obsidian-setup.py`

*Generated from `pack/scripts/obsidian-setup.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
obsidian-setup.py - stand up (and analyze) the Obsidian lens over an AI-Forward docs graph.

WHAT THIS IS
  The pack's knowledge graph lives in per-artifact YAML frontmatter under docs/ (V2), which
  makes docs/ *already* a valid Obsidian vault. This script makes that lens real and shared:
  it writes a committed .obsidian/ configuration (graph colour groups keyed to the pack's own
  artifact types, the enabled plugin list, sensible defaults), seeds non-canonical dashboard
  "lenses", and keeps per-user workspace/cache files out of git.

  It ALSO ships a dependency-free graph analyzer (--analyze) that computes the same class of
  structural insight the Obsidian graph-analysis plugins provide - degree, betweenness
  centrality (Brandes), components, orphans, structural gaps - directly from docs-index.js.
  That matters: the insight must not be locked behind a GUI plugin, because the pack promises
  tool-neutrality (project-memory-and-obsidian.md M8: Obsidian is a reader, never the writer
  of record).

DESIGN RULES THIS HONORS
  * Frontmatter stays the record; docs-graph.py stays the only writer of the graph. This
    script never edits an artifact's frontmatter and never writes docs-index.js.
  * Obsidian is never required. Every mode works, and --analyze is useful, with Obsidian
    absent.
  * Third-party plugin CODE is not downloaded by default. `--init` writes only the *enabled
    list*, so Obsidian's own UI performs the install with the user's consent. `--fetch-plugins`
    is an explicit, pinned opt-in.

USAGE
  obsidian-setup.py --check                  # report state, write nothing (default)
  obsidian-setup.py --init                   # write .obsidian/ config + lenses + .gitignore
  obsidian-setup.py --analyze                # structural insight report to stdout
  obsidian-setup.py --analyze --write        # ...and save it to docs/lenses/graph-insight.md
  obsidian-setup.py --fetch-plugins          # opt-in: download pinned plugin releases
  obsidian-setup.py --install-app            # print the OS install command (--yes to run it)
  ... --root <repo> --vault docs --dry-run --json

Stdlib only. Python 3.8+. Exit 0 on success, 1 on error, 2 on --check findings.
```

## CLI — options

| Option | Help |
|---|---|
| `--all-plugins` | include the optional-tier plugins |
| `--analyze` | structural insight from docs-index.js |
| `--check` | report state, write nothing (default) |
| `--dry-run` | print the plan, write nothing |
| `--fetch-plugins` | opt-in: download plugin code from GitHub releases |
| `--init` | write .obsidian/ config, lenses, .gitignore |
| `--install-app` | install the Obsidian desktop app |
| `--json` | machine-readable output (with --analyze) |
| `--root` | repository root (default: .) |
| `--vault` | vault directory relative to root (default: docs) |
| `--write` | with --analyze: save to <vault>/lenses/graph-insight.md |
| `--yes` | with --install-app: actually run it |

## Functions

### `out(msg=…)`

Print without dying on a legacy Windows console codepage.

### `write_json(path, obj, dry)`

**Coverage gap** — no docstring in the source.

### `write_text(path, text, dry)`

**Coverage gap** — no docstring in the source.

### `load_index(root)`

Parse docs/docs-index.js (a JS assignment wrapping a JSON object).

### `build_graph(index)`

Return (nodes, undirected adjacency, directed out/in) keyed by artifact id.

### `betweenness(nodes, adj)`

Brandes' betweenness centrality, unweighted, on the undirected projection.

O(V*E). Exact - no sampling - which is affordable at documentation scale and
means the ranking is reproducible rather than approximate.

### `components(nodes, adj)`

**Coverage gap** — no docstring in the source.

### `analyze(index, root)`

**Coverage gap** — no docstring in the source.

### `render_report(a)`

**Coverage gap** — no docstring in the source.

### `type_colors()`

Graph colour groups keyed to the PACK's artifact types.

This is the whole point of a committed graph.json: Obsidian's default graph is an
undifferentiated hairball, and the pack's types are exactly the differentiation that
makes it readable. Queries use Obsidian's search syntax over frontmatter.

### `init_vault(root, vault, dry, enable_optional)`

**Coverage gap** — no docstring in the source.

### `lens_notes(project)`

Non-canonical dashboards. Each carries V2 frontmatter so it is a first-class
graph node rather than an un-indexed finding, and each states plainly that it is a
LENS - a projection - never a source of truth (M5/M8).

### `update_gitignore(root, vault, dry)`

**Coverage gap** — no docstring in the source.

### `fetch_registry()`

**Coverage gap** — no docstring in the source.

### `fetch_plugins(root, vault, dry, enable_optional)`

Explicit opt-in: download plugin code from each plugin's GitHub release.

This executes third-party JavaScript inside Obsidian, so it is NOT the default.
The safer path - and the one --init sets up - is to let Obsidian's own plugin
browser install them with the user's consent.

### `app_install_command()`

**Coverage gap** — no docstring in the source.

### `app_installed()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **17** · documented: **7** (**41%**)
- Undocumented (recorded, not invented): `write_json`, `write_text`, `components`, `analyze`, `render_report`, `init_vault`, `update_gitignore`, `fetch_registry`, `app_install_command`, `app_installed`

