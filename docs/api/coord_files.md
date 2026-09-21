---
id: api-coord_files
title: "API — coord_files.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Bounded regular-file reads with pinned, non-reparse Windows ancestors.
---

# `coord_files.py`

*Generated from `pack/scripts/coord_files.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Bounded regular-file reads with pinned, non-reparse Windows ancestors.

The Windows handles deny delete sharing until the read ends. This protects the
path-to-handle transition; it is not isolation from hostile code as the same user.
```

## Functions

### `protect_private_directory(path)`

Apply an inheritable current-user/SYSTEM DACL, not POSIX chmod emulation.

### `pinned_directory(path)`

Hold every Windows ancestor without following a reparse point.

### `open_regular(path, writable=…, create=…)`

Open a non-reparse regular file; a writable shared handle supports locking.

### `read_regular(path, limit)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **4** · documented: **3** (**75%**)
- Undocumented (recorded, not invented): `read_regular`

