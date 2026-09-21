---
id: api-coord_native
title: "API — coord_native.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Read-only Codex thread metadata over its measured local WebSocket endpoint.
---

# `coord_native.py`

*Generated from `pack/scripts/coord_native.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Read-only Codex thread metadata over its measured local WebSocket endpoint.

This deliberately small client handles unfragmented native JSON frames and ping.
Unknown framing fails closed. It never resumes, prompts, approves or cancels a thread.
```

## Functions

### `thread_metadata(path, thread_id, timeout=…, cancelled=…)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **1** · documented: **0** (**0%**)
- Undocumented (recorded, not invented): `thread_metadata`

