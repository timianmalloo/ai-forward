---
id: api-repo_identity
title: "API — repo_identity.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  repo_identity.py - the canonical project name, in ONE place (class PACK-P).
---

# `repo_identity.py`

*Generated from `pack/scripts/repo_identity.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
repo_identity.py - the canonical project name, in ONE place (class PACK-P).

WHY THIS EXISTS. The pack's own worktree discipline (WT1) requires every writing session to
work in its own linked worktree, and `coord worktree new` names that directory
`<repo>-<branch-slug>`. Any generator that names the project `basename(cwd)` therefore stamps
the WORKTREE folder into a committed artifact the moment the discipline is followed:
`docs/audit/audit-data.js` ("project"), `docs/audit/index.html` (<title>), the Docs Explorer
surface titles. Following one rule guaranteed corrupting the other -- a tool that infers
identity from the filesystem, inside a system whose own discipline moves work around the
filesystem. Observed in this repo (a commit stamped `ai-forward-feature-audit-signals-writer`)
and repeatedly in a consuming repo, always caught by eye or by a bundle gate, never by a test.

RESOLUTION ORDER, and why each rung is where it is:
  1. an explicit name the caller was given (`--project`)  -- configuration beats inference,
     always, and this is the rung that makes the others a fallback rather than a guess;
  2. `remote.origin.url` -- explicit git configuration, shared by every worktree of the repo,
     and the only rung that is stable across a clone whose directory was renamed;
  3. the PRIMARY checkout's directory name, via `git rev-parse --git-common-dir` -- one call
     that resolves to the primary repo's `.git` even from a linked worktree;
  4. the directory name -- last resort, for a tree that is not a git repository at all.

VERIFIED, not assumed (Windows, git 2.x, 2026-09-10):
  * from a linked worktree, `--git-common-dir` -> `C:/Projects/ai-forward/.git` (absolute);
  * from the PRIMARY checkout it returns the RELATIVE string `.git`, whose dirname is ''.
    So rung 3 MUST resolve it against the repo path before taking a basename; a naive
    `dirname(common_dir)` yields an empty name in the most common case of all.
  * outside a git repository, `git rev-parse` exits 128 with empty stdout, and
    `git config --get remote.origin.url` exits 1 -- so both rungs must tolerate failure
    rather than raise.

Stdlib only, Python 3.8+. The underscore in the filename is deliberate: a hyphen is not
importable, which is why `coord_ids.py` and `bounded_process.py` are named the way they are.
```

## Functions

### `canonical_project(root, explicit=…)`

The project's canonical name -- never the worktree folder it happened to run in.

`root` is any path inside the repository (a worktree root, or a directory under it).
`explicit` is a caller-supplied override (`--project`) and always wins when non-empty.
Returns a non-empty string; falls back to "repo" only when there is no name to be had.

## Coverage

- Public functions: **1** · documented: **1** (**100%**)

