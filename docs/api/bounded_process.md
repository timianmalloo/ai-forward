---
id: api-bounded_process
title: "API — bounded_process.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Bounded subprocess execution for pack-owned tool invocations.
---

# `bounded_process.py`

*Generated from `pack/scripts/bounded_process.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Bounded subprocess execution for pack-owned tool invocations.
```

## Types

### `ProcessResult`

_(no docstring — coverage gap)_

## Functions

### `run_bounded(command, cwd=…, env=…, timeout_seconds=…, stdout_limit=…, stderr_limit=…, memory_limit=…, process_limit=…)`

Run one process with concurrent draining, hard output caps, and tree cleanup.

On Windows the timeout includes the contained gate wrapper's process-start cost.
Callers running substantive commands should set an explicit workload budget.

## Coverage

- Public functions: **1** · documented: **1** (**100%**)

