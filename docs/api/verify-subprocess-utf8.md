---
id: api-verify-subprocess-utf8
title: "API — verify-subprocess-utf8.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-subprocess-utf8.py - a text-mode subprocess states its encoding; the locale never decides.
---

# `verify-subprocess-utf8.py`

*Generated from `pack/scripts/verify-subprocess-utf8.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-subprocess-utf8.py - a text-mode subprocess states its encoding; the locale never decides.

THE CLASS (PLAT-A; ai-de's DC-211, absorbed). `subprocess.run(..., text=True)` with no `encoding=`
decodes the child's bytes with the interpreter's locale codec - cp1252 on Windows - while every
file this pack writes and every path git prints is UTF-8. A non-ASCII branch name or file path
comes back as mojibake, `_dirty_paths` mis-compares, and a byte-identity oracle reports its own
committed bytes as CHANGED. The pack fixed this once, in `prompt-log.py`, with a comment naming
the defect, and left the same shape in 21 sibling call sites (the audit of 2026-09-19). A lesson
applied where it was learned and never swept is the class; this gate is the sweep that stays.

WHAT IT CHECKS. Every `.py` under pack/scripts, pack/adapters/hooks and tools (the sources;
docs/ai-forward-pack/scripts is a generated copy and is skipped). Each call to
subprocess.run / check_output / check_call / call / Popen that passes `text=True` or
`universal_newlines=True` must also pass `encoding=`. Read with the `ast` module - a call split
over lines or spelled through an alias still counts; prose in comments and docstrings does not.

USAGE
  python3 verify-subprocess-utf8.py               scan this repository
  python3 verify-subprocess-utf8.py --root <repo>  scan that repository
  python3 verify-subprocess-utf8.py --self-test    prove the gate can fail (DC-104)

EXIT  0 clean  ·  1 findings  ·  2 usage
```

## CLI — options

| Option | Help |
|---|---|
| `--root` | _(no help text — coverage gap)_ |
| `--self-test` | _(no help text — coverage gap)_ |

## Functions

### `scan_source(source, rel)`

Findings for one module's source text: (line, head) per undecoded text-mode call.

### `scan(root)`

**Coverage gap** — no docstring in the source.

### `self_test()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **3** · documented: **1** (**33%**)
- Undocumented (recorded, not invented): `scan`, `self_test`

