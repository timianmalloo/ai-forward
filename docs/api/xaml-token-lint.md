---
id: api-xaml-token-lint
title: "API — xaml-token-lint.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  xaml-token-lint.py — first-slice token linter for XAML/native UI markup.
---

# `xaml-token-lint.py`

*Generated from `pack/scripts/xaml-token-lint.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
xaml-token-lint.py — first-slice token linter for XAML/native UI markup.

Checks the deterministic subset of the native-client UI design:
- raw colors in visual properties,
- inline SolidColorBrush colors,
- raw dimensions in common layout/type properties.

It is intentionally not a XAML compiler. It uses bounded text scanning, never fetches
external resources, and refuses paths outside the declared root.
```

## CLI — options

| Option | Help |
|---|---|
| `--format` | _(no help text — coverage gap)_ |
| `--root` | repo root; scanned paths must stay inside it |

## Functions

### `is_resource(value)`

**Coverage gap** — no docstring in the source.

### `is_allowed_dimension(value)`

**Coverage gap** — no docstring in the source.

### `finding(path, line, rule, severity, message, attribute)`

**Coverage gap** — no docstring in the source.

### `lint_text(path, text)`

**Coverage gap** — no docstring in the source.

### `resolve_under_root(root, path)`

**Coverage gap** — no docstring in the source.

### `is_under_root(root_resolved, candidate)`

**Coverage gap** — no docstring in the source.

### `expand_paths(root, inputs)`

**Coverage gap** — no docstring in the source.

### `lint_file(path)`

**Coverage gap** — no docstring in the source.

### `print_text(findings)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **9** · documented: **0** (**0%**)
- Undocumented (recorded, not invented): `is_resource`, `is_allowed_dimension`, `finding`, `lint_text`, `resolve_under_root`, `is_under_root`, `expand_paths`, `lint_file`, `print_text`

