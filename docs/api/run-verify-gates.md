---
id: api-run-verify-gates
title: "API — run-verify-gates.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  run-verify-gates.py - every verify-*.py gate, one exit status, no pipe.
---

# `run-verify-gates.py`

*Generated from `pack/scripts/run-verify-gates.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
run-verify-gates.py - every verify-*.py gate, one exit status, no pipe.

The control for defect class DC-113 (a gate made advisory by the SHAPE of the shell line)
in its loop form. Measured in a consuming repo over three days: 168 main-line shell lines
piped a gate run into `tail`/`head`/`grep` with no pipefail, 102 of them also committing,
merging or pushing on the same line; four hid a red. A `for ... done` loop's exit status is
its LAST command's, not its worst one's, so "chain with &&" is defeated by construction -
there is no single status to chain on. This runner IS that status.

What it runs. Every `verify-*.py` in the repository's gate directories - by default
`tools/` (the repo's own gates) and `docs/ai-forward-pack/scripts/` (the pack's) - each in
its argument-free form, which every gate is expected to support as "check the repository".
A gate that needs arguments gets them with `--args NAME=ARG ...`. A gate that is missing,
cannot be started, or runs past its budget counts as a FAILURE, never as a skip; a skip is
printed by name (`--skip`), never silently.

Why not bounded_process.run_bounded: it blanks stdout on a non-zero exit (its callers read
stderr diagnostics only), and the one thing this runner must relay is a failing gate's last
printed line - the finding. The budget is enforced here with a process-tree kill instead.

Usage
  python3 run-verify-gates.py                        run every gate found
  python3 run-verify-gates.py --dir tools            only this directory (repeatable)
  python3 run-verify-gates.py --skip verify-slow.py  skip by basename (printed as skipped)
  python3 run-verify-gates.py --args verify-test-run.py=--no-run
  python3 run-verify-gates.py --budget 300           seconds per gate (default 300)
  python3 run-verify-gates.py --self-test            prove a red gate is reported red

Exit 0 when every gate passed, 1 when any failed, 2 on a usage error (no gate found).
Stdlib only. Use it as the ONLY line before a commit at a join:
  python3 run-verify-gates.py && git commit ...
```

## CLI — options

| Option | Help |
|---|---|
| `--args` | arguments for one gate, e.g. verify-test-run.py=--no-run (repeatable) |
| `--budget` | per-gate wall budget; past it the gate is killed and counted red |
| `--dir` | gate directory relative to the repo root (repeatable; default: tools/ and docs/ai-forward-pack/scripts/) |
| `--root` | repository root (default: git's answer from the cwd) |
| `--self-test` | prove the runner reports a failing gate as a failure |
| `--skip` | gate basenames to skip - each is printed as skipped, never silently |

## Functions

### `repo_root(start=…)`

The repository root: git's answer, else the nearest ancestor carrying `tools/` or
`docs/ai-forward-pack/`, else the cwd. Printed, never assumed silently.

### `gates(root, dirs)`

**Coverage gap** — no docstring in the source.

### `run_one(gate, root, extra_args=…, budget=…)`

(ok, seconds, last_line). A gate past its budget is killed with its children and is
a failure - a hung gate that is waited on forever is the same silence as a skipped one.

### `parse_args_map(specs)`

**Coverage gap** — no docstring in the source.

### `self_test()`

A gate that exits 1 must be red; one that exits 0 green; one that hangs past its
budget red - and the runner's own exit status must carry each verdict (DC-104: a control
that cannot fail is not a control).

## Coverage

- Public functions: **5** · documented: **3** (**60%**)
- Undocumented (recorded, not invented): `gates`, `parse_args_map`

