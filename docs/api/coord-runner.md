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

### `LeaderCheckSlow`

A bounded leader-check subprocess did not finish inside its timeout. Carries the

### `Runner`

_(no docstring — coverage gap)_

## Functions

### `housekeeping_check(check, lease, epoch)`

One bounded leader check for a caller with no operation deadline (RUN-B).

True while authority stands. A definitive refusal or a changed epoch ends it at once. A
check that only ran slow (LeaderCheckSlow) is not lost authority while the last observed
lease expiry is more than one check window away; the caller checks again on its next
tick, so the dispatch loop never blocks for longer than one check. `check(window)` returns
a leader row, or None for a renewal, which carries no row.

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

### `dispatch_base(cwd, contract)`

The commit every worker tree starts from: the contract's `base` (a branch, tag or
commit) when it names one, else the invoking checkout's HEAD.

BASE-A (x-harness-x-model-bench, 2026-10-04): with HEAD as the only base, a dirty primary
froze every dispatch, because the integration head was a branch the primary could not
fast-forward to. The base is resolved once, here, and pinned in the manifest as a sha.

### `identity(value)`

**Coverage gap** — no docstring in the source.

### `text(value)`

**Coverage gap** — no docstring in the source.

### `integer(value, minimum, maximum)`

**Coverage gap** — no docstring in the source.

### `copilot_model(argv)`

**Coverage gap** — no docstring in the source.

### `expected_model(worker)`

The model the transport must select and confirm before any prompt, or None.

SERVE-A (x-harness-x-model-bench run w2-g3-e1e4): a Grok argv pin (-m / --model) was never
sent as session/set_model, so Grok's ACP default answered instead. An unpinned Grok worker
keeps the earlier behaviour; an ambiguous pin is refused.

### `copilot_model_evidence(session_id, env, expected)`

Check actual native inference events, never the advertised ACP model list.

### `copilot_policy(cwd, model)`

Require the native exact-ID policy before preparation and fingerprinting.

### `relative_path(value)`

**Coverage gap** — no docstring in the source.

### `child_env(worker)`

**Coverage gap** — no docstring in the source.

### `file_hash(path)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **20** · documented: **6** (**30%**)
- Undocumented (recorded, not invented): `load_module`, `require`, `encoded`, `digest`, `read_json`, `private_write`, `git`, `identity`, `text`, `integer`, `copilot_model`, `relative_path`, `child_env`, `file_hash`
