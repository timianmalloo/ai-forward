---
id: api-verify-no-new-console-launches
title: "API — verify-no-new-console-launches.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-no-new-console-launches.py - no code launches a child with CREATE_NEW_CONSOLE.
---

# `verify-no-new-console-launches.py`

*Generated from `pack/scripts/verify-no-new-console-launches.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-no-new-console-launches.py - no code launches a child with CREATE_NEW_CONSOLE.

The control for defect class DC-170, measured in a consuming repo (2026-09-12): on a
machine whose default terminal application is Windows Terminal, a child started with
`CREATE_NEW_CONSOLE` is handed to Windows Terminal as a TAB, and Windows Terminal's agent
host attaches an agent session (an assistant child and its MCP servers, one node.exe each)
to that tab and keeps it for Windows Terminal's lifetime after the tab closes. Nine test
classes launched a helper that way: two tests, two node.exe born; 25 during one whole-suite
run; 257 accumulated over two days. The launcher now uses `CREATE_NO_WINDOW` (a headless
console, never a tab): the same tests, zero born. The mechanism is the platform's, not the
project's, so the gate ships with the pack.

What it reads. Every source file under the scan roots (default `src/` and `tests/`,
excluding `bin/` and `obj/`), in the languages where the flag is spelled by name (C#, C,
C++, Rust, Go, Python, PowerShell, JavaScript/TypeScript); the token `CREATE_NEW_CONSOLE`
on a line that is CODE - one whose first non-blank characters are not a comment leader
(`//`, `///`, `#`, `*`, `--`), because a doc comment may name the flag while explaining why
it is not used. Allowlist: none. A `const` declaration counts: it exists to be used.

Usage
  python3 verify-no-new-console-launches.py                 scan src/ and tests/
  python3 verify-no-new-console-launches.py --root-dir app   scan these roots (repeatable)
  python3 verify-no-new-console-launches.py --self-test      prove the gate can fail (DC-104)

Exit 0 when clean, 1 on a finding, 2 on a usage error. Stdlib only.
```

## CLI — options

| Option | Help |
|---|---|
| `--root-dir` | a directory to scan, relative to the root (repeatable; default: src, tests) |
| `--root` | repository root (default: git's answer from the cwd) |
| `--self-test` | _(no help text — coverage gap)_ |

## Functions

### `repo_root(start=…)`

**Coverage gap** — no docstring in the source.

### `findings(root, roots=…)`

(findings, files read). Reads code lines only; a comment naming the flag is prose.

### `self_test()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **3** · documented: **1** (**33%**)
- Undocumented (recorded, not invented): `repo_root`, `self_test`

