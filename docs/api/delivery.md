---
id: api-delivery
title: "API — delivery.py"
type: api
status: accepted
owner: "@ahutanu"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Conditional delivery routing and local checkpoint integrity, not a workflow runner.
---

# `delivery.py`

*Generated from `pack/scripts/delivery.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Conditional delivery routing and local checkpoint integrity, not a workflow runner.
```

## CLI — options

| Option | Help |
|---|---|
| `--actor` | _(no help text — coverage gap)_ |
| `--audit-root` | _(no help text — coverage gap)_ |
| `--authority` | _(no help text — coverage gap)_ |
| `--authorization` | _(no help text — coverage gap)_ |
| `--closure` | _(no help text — coverage gap)_ |
| `--compiled-id` | _(no help text — coverage gap)_ |
| `--evidence` | _(no help text — coverage gap)_ |
| `--facts` | _(no help text — coverage gap)_ |
| `--input` | _(no help text — coverage gap)_ |
| `--kind` | _(no help text — coverage gap)_ |
| `--path` | _(no help text — coverage gap)_ |
| `--question` | _(no help text — coverage gap)_ |
| `--receipt` | _(no help text — coverage gap)_ |
| `--repo` | _(no help text — coverage gap)_ |
| `--review` | _(no help text — coverage gap)_ |
| `--stage` | _(no help text — coverage gap)_ |
| `--state-root` | _(no help text — coverage gap)_ |
| `--task` | _(no help text — coverage gap)_ |

## Functions

### `route(facts)`

**Coverage gap** — no docstring in the source.

### `read_json(path)`

**Coverage gap** — no docstring in the source.

### `digest(value)`

**Coverage gap** — no docstring in the source.

### `git(repo, *args, optional=…)`

**Coverage gap** — no docstring in the source.

### `identity(repo)`

**Coverage gap** — no docstring in the source.

### `snapshot(repo, local_area=…, details=…, _depth=…)`

**Coverage gap** — no docstring in the source.

### `file_record(path)`

**Coverage gap** — no docstring in the source.

### `validate_scoped_product_path(path, root)`

Refuse aliases and special files; a missing leaf remains a valid create/delete scope.

### `check_records(records, label)`

**Coverage gap** — no docstring in the source.

### `compiler()`

**Coverage gap** — no docstring in the source.

### `contract(audit_root, compiled_id)`

**Coverage gap** — no docstring in the source.

### `local_area(repo, state_root=…)`

**Coverage gap** — no docstring in the source.

### `state_path(repo, task, state_root=…)`

**Coverage gap** — no docstring in the source.

### `save(path, state)`

**Coverage gap** — no docstring in the source.

### `view(state)`

**Coverage gap** — no docstring in the source.

### `load(repo, task, check_tree=…, state_root=…)`

**Coverage gap** — no docstring in the source.

### `new_gate(state, kind, authority, question)`

**Coverage gap** — no docstring in the source.

### `resume(state, receipt_path)`

**Coverage gap** — no docstring in the source.

### `begin_repair(state, args)`

**Coverage gap** — no docstring in the source.

### `recheck_repair(state, args)`

**Coverage gap** — no docstring in the source.

### `close_outcome(state, path)`

**Coverage gap** — no docstring in the source.

### `execute(args)`

**Coverage gap** — no docstring in the source.

### `locked_execute(args)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **23** · documented: **1** (**4%**)
- Undocumented (recorded, not invented): `route`, `read_json`, `digest`, `git`, `identity`, `snapshot`, `file_record`, `check_records`, `compiler`, `contract`, `local_area`, `state_path`, `save`, `view`, `load`, `new_gate`, `resume`, `begin_repair`, `recheck_repair`, `close_outcome`, `execute`, `locked_execute`
