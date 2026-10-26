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
  0. leader fence                     `coord-core.py leader who --json` BEFORE the merge (and
                                      before --continue): refused with exit 11 (EXIT_FENCE - 0
                                      is success) when the epoch this join carries (--epoch,
                                      default: the ref's epoch at the join's start) is lower
                                      than the ref's, or when the ref cannot be read; an absent
                                      ref is "not applicable" (S2 has no leader)
 0b. dirty-primary fence              refuses dirt outside .agents/log/ before merging or
                                      resuming with --continue (exit 12); changes stay in place
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
  7. stage own outputs; commit         merge result, changed derived views, audit entry, session logs;
                                      refuse residual dirt before gates or push (exit 7)
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

Exit 0 on a complete join; the failing step's number otherwise; 11 when the leader fence (step
0) refuses; 12 for dirty-primary refusal (also --continue); 14 when .agents/artifacts.yml is
absent or invalid (before the merge; the join stages only outputs it declares derived, plus the
audit log, the audit hub it creates and session logs); 13 for a merge refusal without unmerged
paths; 1 for a real conflict or an incomplete merge commit (MERGE_HEAD left); 7 for residual
dirt after committing, and for a refusal while staging (a foreign audit change, unrelated staged
paths, an unreadable git path list or audit hash); 2 on a usage error. Stdlib only.

Recovery after exit 7: gates and push have not run. Read the diagnostic and inspect
`git log -2`, `git status`, and the audit diff. A pre-commit refusal leaves no join chore
commit; the merge may already exist locally. Commit or stash foreign work under its own
session before retrying. A post-commit refusal leaves the join chore commit locally too:
keep it local, separate foreign changes under their author's session, and repair any bad
audit diff before proceeding. Once the tree and audit diff are verified, run the configured
step-8 gates, then the intended push/build steps. Do not blindly retry with --continue:
it performs another step-5 append and creates a second audit entry and chore commit.

Derived-output ownership remains a timing boundary: a foreign session writing an eligible
derived path during a join command can still be included. Joins require exclusive execution.
```

## CLI — options

| Option | Help |
|---|---|
| `--artifact` | proof paths for the audit entry |
| `--audit-done-when` | _(no help text — coverage gap)_ |
| `--audit-goal` | _(no help text — coverage gap)_ |
| `--audit-shortname` | the join's audit shortname |
| `--audit-summary` | _(no help text — coverage gap)_ |
| `--continue` | the merge was resolved and committed by hand; fence the tree, then start at step 2 |
| `--docs-only` | skip the recount (no test or product change) |
| `--epoch` | _(no help text — coverage gap)_ |
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

### `join_outputs(j)`

Reuse the artifact registry's validated parser and longest-pattern classification.

Only fingerprints changed by a join command become owned outputs. A file merely dirty
at step 7 is not evidence the join wrote it. Session logs retain their existing exemption.

### `leader_fence(j, given, log)`

Step 0 - the join carries an epoch and the ref decides (spec-leader-designation US-7).

Not a `Join.run` step: `run` knows exit codes only and the fence must read the JSON
(absent is not-applicable; expired/released still carry the epoch). Refuses with
EXIT_FENCE; never proceeds on an unread fence (R4: NOT CHECKED is not "no leader").

### `dirty_fence(j, branch, log)`

Step 0b - a tracked path modified or staged in this checkout, outside .agents/log/, stops
the join before the merge with EXIT_DIRTY and the list of paths. Session logs are exempt
because every session appends to its own file and the join's own chore commit carries them.
The change is never stashed or committed here: whoever wrote it commits it under their name.

### `join(args, root, contract, log=…, _after_fence=…)`

**Coverage gap** — no docstring in the source.

### `self_test()`

Two joins in a throwaway repository, both with --no-push --docs-only and no gates:
(a) a clean branch completes, and the audit entry carries tier T1, fan_out 0 and a
measured duration; (b) a branch that commits a file with a conflict marker - DC-136's
shape, a hand-resolved file - stops at step 3 with NO join commit.

## Coverage

- Public functions: **7** · documented: **5** (**71%**)
- Undocumented (recorded, not invented): `repo_root`, `join`
