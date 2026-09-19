---
id: api-verify-portable-text-io
title: "API — verify-portable-text-io.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-portable-text-io.py - text the pack writes is LF and UTF-8 on every OS, and every CLI survives a legacy console.
---

# `verify-portable-text-io.py`

*Generated from `pack/scripts/verify-portable-text-io.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-portable-text-io.py - text the pack writes is LF and UTF-8 on every OS, and every CLI survives a legacy console.

THE CLASS (PLAT-A, the newline and console halves; cross-platform readiness P2/P3, 2026-09-19).
Three shapes, each fixed once somewhere in the pack and left in its siblings:

  1. A text-mode WRITE without `newline="\n"` emits CRLF on Windows. `audit-log.py` writes its
     JSONL with `newline="\n"`; 26 sibling writers used the platform default, so a ledger line
     appended on Windows and its LF twin from macOS are two distinct strings that a union merge
     conserves both of.
  2. A script with a `__main__` entry that prints has no stdio guard: `--help` raises
     UnicodeEncodeError on a cp1252 console the moment a help string carries an em-dash.
     `pack-doctor.py` carries the guard (reconfigure stdout/stderr to utf-8, errors=replace);
     nine siblings did not.
  3. `tempfile.mkstemp(..., text=True)` opens the descriptor with `_O_TEXT` on Windows - a flag
     that says CRLF while the wrapper says LF. Measured harmless on windows-latest, kept out of
     the source so the file says one thing.

WHAT IT CHECKS. Every `.py` under pack/scripts, pack/adapters/hooks and tools (sources only).
With the `ast` module: (1) `open(..., mode)` where the mode contains w, a or + and no `newline`
keyword, and `Path.write_text(...)` with no `newline` keyword, in TEXT mode (a `b` in the mode
exempts the call); (2) a module containing `if __name__ == "__main__"` and a `print(` must
contain `.reconfigure(` on a stream (the guard) - modules that never print are exempt;
(3) `mkstemp(... text=True)`.

USAGE
  python3 verify-portable-text-io.py               scan this repository
  python3 verify-portable-text-io.py --root <repo>  scan that repository
  python3 verify-portable-text-io.py --self-test    prove the gate can fail (DC-104)

EXIT  0 clean  ·  1 findings  ·  2 usage
```

## CLI — options

| Option | Help |
|---|---|
| `--root` | _(no help text — coverage gap)_ |
| `--self-test` | _(no help text — coverage gap)_ |

## Functions

### `scan_source(source)`

**Coverage gap** — no docstring in the source.

### `scan(root)`

**Coverage gap** — no docstring in the source.

### `self_test()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **3** · documented: **0** (**0%**)
- Undocumented (recorded, not invented): `scan_source`, `scan`, `self_test`

