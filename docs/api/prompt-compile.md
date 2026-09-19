---
id: api-prompt-compile
title: "API — prompt-compile.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  prompt-compile.py - the compile stage: a logged raw prompt -> a gated, harness-rendered prompt.
---

# `prompt-compile.py`

*Generated from `pack/scripts/prompt-compile.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
prompt-compile.py - the compile stage: a logged raw prompt -> a gated, harness-rendered prompt.

THE SHAPE (design docs/design/compile-stage.md): a deterministic SKELETON (references resolved
under the repo root and hashed, pass-through detected by a fixed grammar, the harness template
loaded from the registry) -> the running agent FILLS the model-only fields in the JSON ->
FINISH runs the gate (verify-compiled-prompt.py, imported by path), renders the harness idiom,
appends ONE `kind: compilation` audit entry and copies the text to the clipboard. Nothing is
logged on a refusal; `finish` is the only writer and writes last.

VERBS
  skeleton  --text "<raw>" | --text-file <path> | --from-audit <al-id>  --harness <name> --out <path.json>
            [--no-model] [--audit-root <docs dir>] [--templates-dir <dir>]
  finish    <compiled.json> [--harness <name>] --session <id> [--compiler-model <name>]
            [--compile-tokens <n>] [--no-clipboard] [--audit-root <docs dir>] [--templates-dir <dir>]
  render    <compiled.json> --harness <name> [--templates-dir <dir>]  |  render --self-test
  distance  --compiled <al-id> --received-file <path> [--audit-root <docs dir>]

REFUSALS (stderr, `<code>: <target> - fix: <text>`, exit 1): empty prompt · raw not found ·
template missing · template ambiguous · forbidden construct · and every gate code. Exit 2 is usage
(a malformed compiled JSON names the offending key). Stdlib only; UTF-8 on every seam.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `distance` | _(no help text — coverage gap)_ |
| `finish` | _(no help text — coverage gap)_ |
| `render` | _(no help text — coverage gap)_ |
| `skeleton` | _(no help text — coverage gap)_ |

## CLI — options

| Option | Help |
|---|---|
| `--audit-root` | _(no help text — coverage gap)_ |
| `--compile-tokens` | _(no help text — coverage gap)_ |
| `--compiled` | _(no help text — coverage gap)_ |
| `--compiler-model` | _(no help text — coverage gap)_ |
| `--from-audit` | _(no help text — coverage gap)_ |
| `--harness` | _(no help text — coverage gap)_ |
| `--no-clipboard` | _(no help text — coverage gap)_ |
| `--no-model` | _(no help text — coverage gap)_ |
| `--out` | _(no help text — coverage gap)_ |
| `--received-file` | _(no help text — coverage gap)_ |
| `--self-test` | _(no help text — coverage gap)_ |
| `--session` | _(no help text — coverage gap)_ |
| `--skill` | _(no help text — coverage gap)_ |
| `--templates-dir` | _(no help text — coverage gap)_ |
| `--text-file` | _(no help text — coverage gap)_ |
| `--text` | _(no help text — coverage gap)_ |

## Types

### `Refusal`

_(no docstring — coverage gap)_

## Functions

### `default_templates_dir()`

**Coverage gap** — no docstring in the source.

### `copy_to_clipboard(text)`

prompt-log.py's ladder, reused by import (pbcopy · xclip · wl-copy · clip.exe UTF-16LE).

### `read_entries(audit_root)`

**Coverage gap** — no docstring in the source.

### `find_entry(audit_root, entry_id, kind)`

**Coverage gap** — no docstring in the source.

### `log_raw_prompt(audit_root, text)`

Log the raw text as a kind:prompt entry through prompt-log.py add and return the entry.

prompt-log.py prints the label, not the id, so the id is read back from the log: the newest
kind:prompt entry whose text is this text.

### `append_compilation_entry(audit_root, entry)`

The single write: audit-log.py append --kind compilation --from-json <tmp>. Returns the id.

### `detect_pass_through(raw)`

The fixed grammar: the seven labels line-initial, in order, each once; else None.

### `docs_graph(root, files)`

**Coverage gap** — no docstring in the source.

### `extract_tokens(raw, graph_ids)`

Backticked names, path-like tokens and docs-graph ids, in first-appearance order.

### `resolve_reference(token, root, files, graph)`

Exactly one match -> resolved {path, sha256}; else unresolved with a reason; never a read outside root.

### `read_template(path)`

**Coverage gap** — no docstring in the source.

### `load_template(templates_dir, harness)`

**Coverage gap** — no docstring in the source.

### `build_skeleton(raw_text, raw_id, harness, root, templates_dir, no_model)`

**Coverage gap** — no docstring in the source.

### `check_schema(doc)`

The offending key of a malformed compiled document, else None.

### `render_sections(doc)`

**Coverage gap** — no docstring in the source.

### `render_document(doc, template, session=…, skill=…)`

**Coverage gap** — no docstring in the source.

### `edit_distance(compiled, received)`

**Coverage gap** — no docstring in the source.

### `cmd_skeleton(args)`

**Coverage gap** — no docstring in the source.

### `cmd_finish(args)`

**Coverage gap** — no docstring in the source.

### `render_self_test()`

**Coverage gap** — no docstring in the source.

### `cmd_render(args)`

**Coverage gap** — no docstring in the source.

### `cmd_distance(args)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **22** · documented: **7** (**32%**)
- Undocumented (recorded, not invented): `default_templates_dir`, `read_entries`, `find_entry`, `docs_graph`, `read_template`, `load_template`, `build_skeleton`, `render_sections`, `render_document`, `edit_distance`, `cmd_skeleton`, `cmd_finish`, `render_self_test`, `cmd_render`, `cmd_distance`

