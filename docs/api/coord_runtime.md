---
id: api-coord_runtime
title: "API — coord_runtime.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Private, bounded, append-only runtime controls for an already admitted run.
---

# `coord_runtime.py`

*Generated from `pack/scripts/coord_runtime.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Private, bounded, append-only runtime controls for an already admitted run.

One record is one input or decision fact. Filesystem ownership is the authority
boundary; this does not isolate mutually hostile programs running as the same user.
```

## Types

### `Controls`

Pattern: serialized append-only mailbox; state is derived, never overwritten.

## Functions

### `encoded(value)`

**Coverage gap** — no docstring in the source.

### `digest(value)`

**Coverage gap** — no docstring in the source.

### `require(condition)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **3** · documented: **0** (**0%**)
- Undocumented (recorded, not invented): `encoded`, `digest`, `require`

