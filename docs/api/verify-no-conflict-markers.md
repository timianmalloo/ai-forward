---
id: api-verify-no-conflict-markers
title: "API — verify-no-conflict-markers.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-no-conflict-markers.py - a conflict marker must never reach a commit.
---

# `verify-no-conflict-markers.py`

*Generated from `pack/scripts/verify-no-conflict-markers.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-no-conflict-markers.py - a conflict marker must never reach a commit.

The control for defect class DC-136 (a merge resolved as "regenerate, then stage
everything" leaves markers in a file that is patched in place, not regenerated), measured
in a consuming repo: two PUBLISHED pages carried `<<<<<<< HEAD` / `=======` / `>>>>>>>`
on main. Every existing gate passed - a figure check verified four copies of a right
answer, and a derived-views check did not own the file because it was only PARTIALLY
derived. A content check cannot see structural damage by construction. Then a join
resolved a register conflict, piped this gate's output through `| tail -1`, read the
remedy text as a pass, and sealed a merge carrying markers (DC-113's fourth recurrence).

That is why this gate is FIRST in a join's step list and runs on its own line: a marker is
syntactically legal in almost every text format we commit, survives a skimmed diff of a
large generated file, and is unambiguous evidence that a file which should have been
regenerated was resolved by hand instead. There is no legitimate reason for one in a
tracked file, which makes this the rare check with no judgement in it.

What is checked. Every tracked text file, for `<<<<<<<`, `>>>>>>>` and `|||||||` at the
start of a line. `=======` alone is deliberately NOT flagged: it is a Markdown setext
heading underline and a reStructuredText rule, and a gate that fires on valid prose is a
gate someone switches off.

Usage
  python3 verify-no-conflict-markers.py               scan every tracked file
  python3 verify-no-conflict-markers.py --root <repo>  scan that repository
  python3 verify-no-conflict-markers.py --self-test    prove all three directions

Exit 0 when clean, 1 on any finding (or when nothing could be read - a verdict over an
empty corpus is not a verdict, PACK-P). Stdlib only.
```

## CLI — options

| Option | Help |
|---|---|
| `--root` | repository to scan (default: git's answer from the cwd) |
| `--self-test` | prove the gate fires, does not fire on valid Markdown, and refuses an empty corpus |

## Functions

### `repo_root(start=…)`

**Coverage gap** — no docstring in the source.

### `tracked_files(root)`

**Coverage gap** — no docstring in the source.

### `scan(root, files)`

Returns (findings, files actually read). This file describes the markers it hunts,
so it necessarily contains them in prose and is skipped by identity, not by name.

### `self_test()`

All three directions: it fires; it does NOT fire on valid prose; an empty corpus is
refused rather than reported clean.

## Coverage

- Public functions: **4** · documented: **2** (**50%**)
- Undocumented (recorded, not invented): `repo_root`, `tracked_files`

