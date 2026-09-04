---
id: api-docs-graph
title: "API — docs-graph.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  docs-graph.py — the AI-Forward Pack docs script bundle (knowledge-visualization.md V18).
---

# `docs-graph.py`

*Generated from `pack/scripts/docs-graph.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
docs-graph.py — the AI-Forward Pack docs script bundle (knowledge-visualization.md V18).

Deterministic mechanics for the knowledge graph, so skills invoke ONE tool instead of
generating ad-hoc scripts at prompt time. Python 3.8+, stdlib only (a built-in parser
covers the V2 frontmatter subset; no PyYAML needed).

Subcommands
  inventory   Scan the graph: artifacts, missing/invalid frontmatter, bad links,
              unregistered rels, orphans, stale (V13), flagged (V16), index drift. JSON out.
  derive      Full derivation sweep: frontmatter -> docs/docs-index.js (V2/V10).
  validate    inventory + nonzero exit on DEFECTS (CI-able). `--gate fail` also fails on
              suggestions (V16 flags, V13 staleness), which only warn by default.
  freshness   The freshness gate's time-based half: stale + flagged + orphans; exit code.
  flag        V16 propagation: --changed <id> --reason "..." flags inbound neighbors.
  clear-flag  Clear a review-suggested flag (--id <artifact> --by <changed-id>) and
              optionally --bump-review <days>.
  stub        Scaffold a new artifact file with schema-correct frontmatter.
  snapshot    Append a graph-health record to docs/health-history.jsonl (governance trend).
  rollup      Aggregate per-artifact markdown tables under a heading (e.g. the designs'
              STRIDE / privacy tables) into one register, each row prefixed with its
              source artifact — paste-ready for the threat-model / privacy-review docs.
  context     Build one deterministic, bounded, provenance-rich grounding packet.

Conventions
  --root defaults to docs/. Excluded from the graph: docs/ai-forward-pack/**, docs/_site/**,
  docs/index.html, docs/docs-index.js, non-.md files. Frontmatter is the record; this tool
  never invents metadata — files without frontmatter are reported, not silently indexed.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `clear-flag` | _(no help text — coverage gap)_ |
| `context` | _(no help text — coverage gap)_ |
| `derive` | _(no help text — coverage gap)_ |
| `flag` | _(no help text — coverage gap)_ |
| `freshness` | _(no help text — coverage gap)_ |
| `inventory` | _(no help text — coverage gap)_ |
| `rollup` | _(no help text — coverage gap)_ |
| `snapshot` | _(no help text — coverage gap)_ |
| `stub` | _(no help text — coverage gap)_ |
| `validate` | _(no help text — coverage gap)_ |

## CLI — options

| Option | Help |
|---|---|
| `--bump-review` | _(no help text — coverage gap)_ |
| `--by` | _(no help text — coverage gap)_ |
| `--changed` | _(no help text — coverage gap)_ |
| `--file` | _(no help text — coverage gap)_ |
| `--force` | _(no help text — coverage gap)_ |
| `--gate` | fail = treat review-suggested/stale as errors too (default: warn) |
| `--generator` | _(no help text — coverage gap)_ |
| `--heading` | _(no help text — coverage gap)_ |
| `--hops` | _(no help text — coverage gap)_ |
| `--id` | _(no help text — coverage gap)_ |
| `--include-changes` | _(no help text — coverage gap)_ |
| `--link` | to:rel (repeatable), e.g. --link spec-checkout:implements |
| `--max-bytes` | _(no help text — coverage gap)_ |
| `--out` | _(no help text — coverage gap)_ |
| `--owner` | _(no help text — coverage gap)_ |
| `--phase` | _(no help text — coverage gap)_ |
| `--policy` | _(no help text — coverage gap)_ |
| `--project` | _(no help text — coverage gap)_ |
| `--query` | _(no help text — coverage gap)_ |
| `--reason` | _(no help text — coverage gap)_ |
| `--review-by` | _(no help text — coverage gap)_ |
| `--root` | docs root (default: docs) |
| `--summary` | _(no help text — coverage gap)_ |
| `--tag` | _(no help text — coverage gap)_ |
| `--timings` | emit phase timings as structured JSON on stderr after a successful packet |
| `--title` | _(no help text — coverage gap)_ |
| `--type` | _(no help text — coverage gap)_ |

## Types

### `DocsGraphError`

_(no docstring — coverage gap)_

## Functions

### `canonical_json(value)`

**Coverage gap** — no docstring in the source.

### `sha256_text(text)`

**Coverage gap** — no docstring in the source.

### `normalized_source(text)`

**Coverage gap** — no docstring in the source.

### `parse_scalar(v)`

**Coverage gap** — no docstring in the source.

### `split_flow(s)`

**Coverage gap** — no docstring in the source.

### `parse_flow_map(v)`

**Coverage gap** — no docstring in the source.

### `parse_frontmatter(text)`

Returns (dict, error). Supports: scalars, '>-' folded blocks, '- item' lists,
'- { k: v }' lists, flow lists/maps. That is the whole V2 schema.

### `extract_mermaid_blocks(text)`

**Coverage gap** — no docstring in the source.

### `discover_html_surfaces(root, artifacts)`

**Coverage gap** — no docstring in the source.

### `scan(root, metadata_only=…, artifact_limit=…)`

**Coverage gap** — no docstring in the source.

### `scan_context(root)`

**Coverage gap** — no docstring in the source.

### `read_context_source(artifact, expected_hash)`

**Coverage gap** — no docstring in the source.

### `sniff_kind(code)`

**Coverage gap** — no docstring in the source.

### `analyze(arts, problems)`

**Coverage gap** — no docstring in the source.

### `cmd_inventory(args, exit_on_findings=…)`

**Coverage gap** — no docstring in the source.

### `count_by(arts, key)`

**Coverage gap** — no docstring in the source.

### `index_drift(args, arts)`

Compare derived-from-frontmatter against the existing docs-index.js (ids + shallow fields).

### `policy_hash()`

**Coverage gap** — no docstring in the source.

### `graph_hash(entries, project)`

**Coverage gap** — no docstring in the source.

### `project_identity(root, explicit=…)`

**Coverage gap** — no docstring in the source.

### `project_root_id(entries)`

**Coverage gap** — no docstring in the source.

### `cmd_derive(args)`

**Coverage gap** — no docstring in the source.

### `cmd_freshness(args)`

**Coverage gap** — no docstring in the source.

### `edit_frontmatter_flags(path, mutate)`

**Coverage gap** — no docstring in the source.

### `cmd_flag(args)`

**Coverage gap** — no docstring in the source.

### `cmd_clear_flag(args)`

**Coverage gap** — no docstring in the source.

### `cmd_rollup(args)`

Extract the markdown table under --heading from every matching artifact and merge.

### `cmd_snapshot(args)`

**Coverage gap** — no docstring in the source.

### `cmd_stub(args)`

**Coverage gap** — no docstring in the source.

### `context_graph(arts, problems)`

**Coverage gap** — no docstring in the source.

### `traverse_context(by_id, root_id, policy_name, hops)`

**Coverage gap** — no docstring in the source.

### `markdown_chunks(artifact, source, depth, relation_priority, query_terms)`

**Coverage gap** — no docstring in the source.

### `context_health(arts)`

**Coverage gap** — no docstring in the source.

### `active_changes(root, paths)`

**Coverage gap** — no docstring in the source.

### `packet_bytes(packet)`

**Coverage gap** — no docstring in the source.

### `cmd_context(args, timings=…)`

**Coverage gap** — no docstring in the source.

### `write_context_error(error)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **37** · documented: **3** (**8%**)
- Undocumented (recorded, not invented): `canonical_json`, `sha256_text`, `normalized_source`, `parse_scalar`, `split_flow`, `parse_flow_map`, `extract_mermaid_blocks`, `discover_html_surfaces`, `scan`, `scan_context`, `read_context_source`, `sniff_kind`, `analyze`, `cmd_inventory`, `count_by`, `policy_hash`, `graph_hash`, `project_identity`, `project_root_id`, `cmd_derive`, `cmd_freshness`, `edit_frontmatter_flags`, `cmd_flag`, `cmd_clear_flag`, `cmd_snapshot`, `cmd_stub`, `context_graph`, `traverse_context`, `markdown_chunks`, `context_health`, `active_changes`, `packet_bytes`, `cmd_context`, `write_context_error`

