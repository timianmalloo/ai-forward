---
id: api-pack-doctor
title: "API — pack-doctor.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  pack-doctor.py — AI-Forward install-health check (deployable; runs in a TARGET repo).
---

# `pack-doctor.py`

*Generated from `pack/scripts/pack-doctor.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
pack-doctor.py — AI-Forward install-health check (deployable; runs in a TARGET repo).

Reports whether THIS repo has the pack installed and healthy: the installed revision, both
tool surfaces present, the managed blocks intact, and the knowledge graph valid + fresh.
One PASS/WARN/FAIL line per check with a suggested fix; exit 1 if any FAIL, or if any WARN
is present under --strict.

Distinct from tools/check-consistency.py (which validates the pack SOURCE — pack/ == docs).
A target repo has no pack/, so this checks INSTALL health, not source consistency.
Design: docs/design/pack-doctor.md. Stdlib only; composes docs-graph.py for the graph half.

Usage
  pack-doctor.py [--root <repo>] [--json] [--strict]
Exit: 0 all PASS/WARN (or all PASS under --strict) · 1 any FAIL/strict WARN.
```

## CLI — options

| Option | Help |
|---|---|
| `--json` | _(no help text — coverage gap)_ |
| `--root` | _(no help text — coverage gap)_ |
| `--strict` | treat warnings and inconclusive checks as release-blocking failures |

## Functions

### `check_installed(root)`

**Coverage gap** — no docstring in the source.

### `check_surface(root, label, subdirs)`

**Coverage gap** — no docstring in the source.

### `check_block(root, fname)`

**Coverage gap** — no docstring in the source.

### `check_graph(root)`

**Coverage gap** — no docstring in the source.

### `check_node_runner()`

Report whether `npm run …` can actually resolve node on THIS machine.

FR-055 / registered class PACK-C — *a documented command assumed portable*. The pack and
its contributor docs say `npm run test:docs-explorer:core`. On a real Windows host that
command printed `'node' is not recognized` while `node --version` succeeded and the
identical test invocation run directly passed 31/31. A contributor sees a failure that
is not a failure and may "fix" a healthy suite; CI is Linux-only so it never surfaces
there — precisely the blind spot PACK-C describes.

The probe is the diagnosis: node resolving *for you* proves nothing, because npm runs
scripts through a **child shell** (cmd.exe on Windows, sh elsewhere) whose PATH can
differ from your own. So this spawns that same shell and asks it for node — which is the
only thing that predicts whether the documented command will work.

Mirrors check_interpreter()'s stance for `python3`: name the working invocation for this
machine once, here, instead of discovering it one command at a time (CI6).

### `check_interpreter()`

Report the invocation form that actually runs Python 3 on THIS machine.

The pack documents `python3 …` because that is the POSIX-correct name and matches every
script's shebang. It is not universally available: python.org's Windows installer ships
`python.exe` and `py.exe` but **no `python3.exe`**, and Windows additionally provides a
`python3` App-Execution-Alias that is not Python at all - it prints "Python was not
found" and exits 9009. So a Windows reader copy-pasting a documented command sees what
looks like a missing Python installation when Python is installed and working.

This check exists so that failure is reported once, here, with the right answer, instead
of being discovered one command at a time (continuous-improvement.md CI6 - convert the
lesson into a control that fires at the moment of the mistake).

### `run(root)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **7** · documented: **2** (**29%**)
- Undocumented (recorded, not invented): `check_installed`, `check_surface`, `check_block`, `check_graph`, `run`

