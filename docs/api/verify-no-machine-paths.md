---
id: api-verify-no-machine-paths
title: "API — verify-no-machine-paths.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-no-machine-paths.py - a tracked, machine-readable file never carries one machine's paths.
---

# `verify-no-machine-paths.py`

*Generated from `pack/scripts/verify-no-machine-paths.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-no-machine-paths.py - a tracked, machine-readable file never carries one machine's paths.

WHY THIS EXISTS (PLAT-B, docs/lessons/defect-classes.md). `coord classify init` wrote
`sys.executable` - `C:\Users\<user>\...\python.exe` - into the TRACKED registry
`.agents/artifacts.yml`. The file was correct on the machine that wrote it and the tool
reported success; `coord regen` then failed on macOS days later with "command not found",
while `pack-doctor` passed because it checked that the registry parsed, never that its
commands resolve here. A home directory, a drive letter or an interpreter path inside a file
git carries is state about ONE machine masquerading as configuration for all of them.

WHAT IT SCANS. Tracked files (`git ls-files`) under the machine-readable surfaces: pack/,
tools/, tests/, web/, .claude/, .github/, .grok/, .agents/ and the repo-root dotfiles and
manifests. Prose under docs/ is out of scope on purpose - investigations and defect classes
cite offending paths as evidence, and a lint that forbids naming the defect is a lint that
forbids fixing it.

WHAT IT REFUSES. Any line matching a machine-path shape (each line below carries the
opt-out marker because it names the shapes; the marker is `machine-path-ok`):
  <drive>:\Users\   <drive>:/Users/   /Users/<name>   /home/<name>   /opt/homebrew/   machine-path-ok
  \.pyenv/           AppData\Local     AppData/Local                                machine-path-ok
A line may opt out with the marker `machine-path-ok` when the path is a fixture and the
test says why (the exemption is visible in the diff; the pattern is not silently widened).

USAGE
  python3 verify-no-machine-paths.py               scan the tracked surfaces of this repo
  python3 verify-no-machine-paths.py --root <repo>  scan that repository
  python3 verify-no-machine-paths.py --self-test    prove the gate can fail (DC-104)

EXIT  0 clean  ·  1 a machine path was found  ·  2 usage / git unavailable
```

## CLI — options

| Option | Help |
|---|---|
| `--root` | _(no help text — coverage gap)_ |
| `--self-test` | _(no help text — coverage gap)_ |

## Functions

### `tracked_files(root)`

**Coverage gap** — no docstring in the source.

### `in_scope(rel)`

**Coverage gap** — no docstring in the source.

### `scan(root)`

**Coverage gap** — no docstring in the source.

### `self_test()`

The gate must be able to fail: a fixture with a Windows home path is refused, a clean
fixture is accepted, and an opted-out line is skipped. Exit 0 only if all three hold.

## Coverage

- Public functions: **4** · documented: **1** (**25%**)
- Undocumented (recorded, not invented): `tracked_files`, `in_scope`, `scan`

