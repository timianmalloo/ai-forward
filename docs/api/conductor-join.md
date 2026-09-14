---
id: api-conductor-join
title: "API — conductor-join.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  conductor-join.py - the join, as a script: every step gated by its exit code, none by a
---

# `conductor-join.py`

*Generated from `pack/scripts/conductor-join.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
conductor-join.py - the join, as a script: every step gated by its exit code, none by a
shell line.

The control for defect class DC-113's fourth recurrence (measured 2026-09-13, a consuming
repo's join): the conductor resolved a register conflict, piped the conflict-marker gate
through `| tail -1`, read the gate's remedy text as a pass, and committed a merge carrying
`<<<<<<<` (DC-136's shape) - caught only because the gate runner was re-run bare before the
push. Three earlier recurrences had the same cause: a hand-typed line at the join whose
status was the formatter's, not the gate's. This script IS the join line. It has no pipes;
each step is a subprocess whose return code decides whether the next runs. The
`execute-with-coordination` skill names it as the only join line.

Steps, in order, stop on the first red (the exit status is the failing step's number):
  1. git merge --no-ff <branch>       a conflict stops here with the file list; resolve by hand,
                                      `git add`, `git commit --no-edit`, re-run with --continue
  2. audit marker                     `audit-log.py start --session <s> --skill execute-with-coordination`
                                      so the join's own duration is MEASURED (a resumed or
                                      hand-typed join set none: 14 of 14 join entries carried
                                      no duration, no tier, no fan-out)
  3. verify-no-conflict-markers       ALWAYS, before anything else reads the tree
  4. checks, then the recount         from join.json (`checks`, `recount`); the recount is timed
                                      as recount_seconds - the largest cost centre of a measured
                                      programme (44.8% of the conductor's active main line) and
                                      the one no entry recorded. --docs-only skips the recount.
  5. audit-log append                 tier T1, fan-out 0, the marker's duration, recount_seconds
  6. regenerate                       `regenerate` from join.json, default `coord-core.py regen`
  7. git add -A && git commit         the join commit (the pre-commit boundary runs)
  8. gates                            `gates` from join.json, default `run-verify-gates.py`
  9. git push <remote> <branch>       only if 8 passed; --no-push skips
 10. build                            `build` from join.json, optional; --no-build skips

join.json (default docs/coordination/join.json; --join <path> overrides; absent = defaults):
  { "checks":     [["python3", "tools/verify-register.py", "--fix-counts"]],
    "recount":    [["python3", "tools/verify-test-run.py", "--update"]],
    "regenerate": [["python3", "docs/ai-forward-pack/scripts/coord-core.py", "regen"]],
    "gates":      [["python3", "docs/ai-forward-pack/scripts/run-verify-gates.py"]],
    "build":      [["dotnet", "build", "src/App/App.csproj", "-c", "Release"]],
    "push_remote": "origin",
    "trailer_file": "docs/coordination/commit-trailer.txt" }
  A command whose first word is `python3` or `python` runs under THIS interpreter.

Usage (from the checkout the join lands on):
  python3 conductor-join.py <branch> --title "<merge title>" --audit-shortname <name>
      --audit-summary "<text>" --audit-goal "<text>" --audit-done-when "<text>"
      [--artifact <path> ...] [--docs-only] [--no-push] [--no-build] [--continue]
      [--join <join.json>] [--session <id>] [--self-test]

Exit 0 on a complete join; the failing step's number otherwise; 2 on a usage error.
Stdlib only.
```

## CLI — options

| Option | Help |
|---|---|
| `--artifact` | proof paths for the audit entry |
| `--audit-done-when` | _(no help text — coverage gap)_ |
| `--audit-goal` | _(no help text — coverage gap)_ |
| `--audit-shortname` | the join's audit shortname |
| `--audit-summary` | _(no help text — coverage gap)_ |
| `--continue` | the merge was resolved by hand; start at step 2 |
| `--docs-only` | skip the recount (no test or product change) |
| `--join` | the join contract (default docs/coordination/join.json) |
| `--no-build` | _(no help text — coverage gap)_ |
| `--no-push` | _(no help text — coverage gap)_ |
| `--self-test` | prove a red step stops the join |
| `--session` | audit session id (default $AGENT_SESSION, then join.json, then 'conductor') |
| `--title` | the merge commit's title (the trailer is appended) |
| `--trailer-file` | text appended to every commit message |

## Types

### `Join`

_(no docstring — coverage gap)_

## Functions

### `repo_root(start=…)`

**Coverage gap** — no docstring in the source.

### `load_join(root, path)`

The join contract for this repository, or the defaults. A malformed file is a usage
error, never a silent fallback to defaults (a join that skipped the recount because its
config had a typo would report as complete).

### `join(args, root, contract, log=…)`

**Coverage gap** — no docstring in the source.

### `self_test()`

Two joins in a throwaway repository, both with --no-push --docs-only and no gates:
(a) a clean branch completes, and the audit entry carries tier T1, fan_out 0 and a
measured duration; (b) a branch that commits a file with a conflict marker - DC-136's
shape, a hand-resolved file - stops at step 3 with NO join commit.

## Coverage

- Public functions: **4** · documented: **2** (**50%**)
- Undocumented (recorded, not invented): `repo_root`, `join`

