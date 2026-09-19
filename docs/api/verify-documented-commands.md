---
id: api-verify-documented-commands
title: "API — verify-documented-commands.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-documented-commands.py - every documented command under pack/ runs in any shell.
---

# `verify-documented-commands.py`

*Generated from `pack/scripts/verify-documented-commands.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-documented-commands.py - every documented command under pack/ runs in any shell.

THE CLASS (PLAT-A, the shell half; cross-platform readiness P4, XS-01..25, 2026-09-19).
The pack targets bash, zsh, PowerShell 5.1/7 and cmd, and an agent types a documented
command as written. Three shapes were written once for bash and left in their siblings:

  1. A trailing ` \` continuation - bash/zsh only. cmd runs the next line as a SEPARATE
     command; PowerShell continues with a backtick. 10 multi-line commands (16 lines)
     carried it at a01ed77, among them the AL5 audit step, the WT1 worktree step and the
     only join line.
  2. ` && ` between two commands - not a statement separator in Windows PowerShell 5.1
     (it parses as a token error, so `git add -A && git commit ... && git push` runs
     nothing). 2 fenced and 4 inline documented commands carried it.
  3. A line-initial bare `python` - stock macOS and Linux ship `python3` only; the pack's
     own convention is `python3` (the Windows substitution is `pack-doctor`'s job to name).
     7 fenced skill/INSTALL commands and 6 inline ones carried it; INSTALL's labelled
     Windows twin is the one allowlisted line.

SCAN CONTRACT (GO14a - root, recursion, token set, allowlist).
  root       <repo>/pack (absent in a consuming repo: nothing to scan, exit 0 and say so)
  recursion  commands/**/*.md, knowledge/*.md, adapters/INSTALL.md, templates/*.md
  blocks     fenced code blocks (``` or ~~~) whose info string is empty or one of
             bash, sh, shell, zsh. A block whose FIRST line starts with `#!` is a file
             (DC-207: a multi-line program is a file, then a run), not a typed command,
             and is skipped whole. Blank lines and `#` comment lines are skipped.
  tokens     continuation  - the line ends in whitespace + `\`
             and-chain     - the line contains ` && `
             bare-python   - the first token is `python` (optionally after a `$ ` prompt)
  allowlist  the inline marker `portable-ok: <reason>` anywhere on the line, like
             `machine-path-ok` in verify-no-machine-paths.py. A marker with no reason is
             a finding of its own (`marker-without-reason`).

USAGE
  python3 verify-documented-commands.py               scan this repository
  python3 verify-documented-commands.py --root <repo>  scan that repository
  python3 verify-documented-commands.py --self-test    prove the gate can fail (DC-104)

EXIT  0 clean  ·  1 findings  ·  2 usage
```

## CLI — options

| Option | Help |
|---|---|
| `--root` | repository root (default: this repo) |
| `--self-test` | prove the gate can fail |

## Types

### `Finding`

_(no docstring — coverage gap)_

## Functions

### `documented_files(pack)`

The files the contract names, in a stable order.

### `command_lines(text)`

Yield (lineno, line) for every command line inside a command fence.

A fence opens on ``` or ~~~ with a command info string and closes on the same
marker; a block whose first line is a shebang is a file and is skipped whole.

### `tokens_in(line)`

The portability tokens one command line carries (empty when allowlisted).

### `scan(root)`

**Coverage gap** — no docstring in the source.

### `report(findings, root, pack_present)`

**Coverage gap** — no docstring in the source.

### `self_test()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **6** · documented: **3** (**50%**)
- Undocumented (recorded, not invented): `scan`, `report`, `self_test`

