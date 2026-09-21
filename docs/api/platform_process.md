---
id: api-platform_process
title: "API — platform_process.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Cross-platform owned-process helpers for bounded local subprocesses.
---

# `platform_process.py`

*Generated from `pack/scripts/platform_process.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Cross-platform owned-process helpers for bounded local subprocesses.
```

## Types

### `WindowsJob`

_(no docstring — coverage gap)_

## Functions

### `spawn_windows_gate(command, cwd=…, env=…, stdout=…, stderr=…, closed_stdin=…)`

**Coverage gap** — no docstring in the source.

### `release_windows_gate(process, close_after=…)`

**Coverage gap** — no docstring in the source.

### `terminate_owned_process(process, windows_job=…)`

**Coverage gap** — no docstring in the source.

### `wait_after_termination(process, windows_job=…, terminate=…, timeout=…)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **4** · documented: **0** (**0%**)
- Undocumented (recorded, not invented): `spawn_windows_gate`, `release_windows_gate`, `terminate_owned_process`, `wait_after_termination`

