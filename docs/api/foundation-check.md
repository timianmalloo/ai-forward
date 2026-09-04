---
id: api-foundation-check
title: "API — foundation-check.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  foundation-check.py — vendored-foundation drift detection (AI-Forward Pack).
---

# `foundation-check.py`

*Generated from `pack/scripts/foundation-check.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
foundation-check.py — vendored-foundation drift detection (AI-Forward Pack).

The pack vendors foundation docs from the base Agent Knowledge Pack into knowledge/.
They WILL diverge over time; this makes divergence visible instead of surprising.
Hashes are computed over NORMALIZED content (CRLF->LF, trailing-space strip) so line
endings never masquerade as drift. Stdlib only.

Usage
  foundation-check.py                 # verify knowledge/ matches FOUNDATION.md manifest
  foundation-check.py --base <dir>    # additionally diff vendored vs base-pack copies
  foundation-check.py --update        # rewrite manifest hashes from current knowledge/
Exit: 0 clean, 1 drift/missing.
```

## CLI — options

| Option | Help |
|---|---|
| `--base` | path to the base Agent Knowledge Pack |
| `--update` | rewrite manifest hashes from current files |

## Functions

### `nhash(path)`

**Coverage gap** — no docstring in the source.

### `read_manifest()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **2** · documented: **0** (**0%**)
- Undocumented (recorded, not invented): `nhash`, `read_manifest`

