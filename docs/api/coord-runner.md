---
id: api-coord-runner
title: "API — coord-runner.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Prepare and run an opt-in, qualified multi-harness coordination contract.
---

# `coord-runner.py`

*Generated from `pack/scripts/coord-runner.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Prepare and run an opt-in, qualified multi-harness coordination contract.

Run `prepare --contract FILE`, qualify the resulting checkout-specific fingerprints,
then `run --run ID --qualification FILE`. `status --run ID` never replays work.
The existing coordinator remains responsible for decisions and semantic review.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `_attach_identity` | _(no help text — coverage gap)_ |
| `_profile` | _(no help text — coverage gap)_ |
| `_prompt` | _(no help text — coverage gap)_ |
| `attach` | _(no help text — coverage gap)_ |
| `prepare` | _(no help text — coverage gap)_ |

## CLI — options

| Option | Help |
|---|---|
| `--clean` | _(no help text — coverage gap)_ |
| `--compilation` | _(no help text — coverage gap)_ |
| `--contract` | _(no help text — coverage gap)_ |
| `--harness` | _(no help text — coverage gap)_ |
| `--option` | _(no help text — coverage gap)_ |
| `--qualification` | _(no help text — coverage gap)_ |
| `--request` | _(no help text — coverage gap)_ |
| `--run` | _(no help text — coverage gap)_ |
| `--worker` | _(no help text — coverage gap)_ |

## Types

### `Refused`

_(no docstring — coverage gap)_

### `Runner`

_(no docstring — coverage gap)_

## Functions

### `load_module(name, filename)`

**Coverage gap** — no docstring in the source.

### `require(condition, code, remedy)`

**Coverage gap** — no docstring in the source.

### `encoded(value)`

**Coverage gap** — no docstring in the source.

### `digest(value)`

**Coverage gap** — no docstring in the source.

### `interruption()`

An owned child gets a cleanup opportunity when the attachment CLI is stopped.

### `read_json(path)`

**Coverage gap** — no docstring in the source.

### `private_write(path, value)`

**Coverage gap** — no docstring in the source.

### `git(cwd, *args)`

**Coverage gap** — no docstring in the source.

### `identity(value)`

**Coverage gap** — no docstring in the source.

### `text(value)`

**Coverage gap** — no docstring in the source.

### `integer(value, minimum, maximum)`

**Coverage gap** — no docstring in the source.

### `relative_path(value)`

**Coverage gap** — no docstring in the source.

### `child_env(worker)`

**Coverage gap** — no docstring in the source.

### `file_hash(path)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **14** · documented: **1** (**7%**)
- Undocumented (recorded, not invented): `load_module`, `require`, `encoded`, `digest`, `read_json`, `private_write`, `git`, `identity`, `text`, `integer`, `relative_path`, `child_env`, `file_hash`

