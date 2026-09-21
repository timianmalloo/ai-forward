---
id: api-coord_transport
title: "API — coord_transport.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  Bounded POSIX ACP / Agy session IO. Native harness policy remains authoritative.
---

# `coord_transport.py`

*Generated from `pack/scripts/coord_transport.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
Bounded POSIX ACP / Agy session IO. Native harness policy remains authoritative.

This is a lifecycle adapter, not an editor proxy or an approval broker. Only
locally selected operational fields leave this module; wire bodies are discarded.
```

## Functions

### `file_root_identities(paths, missing_path=…)`

Validate explicit file access; content may append without changing identity.

Only preparation may defer its exact future session log until worktree registration.

### `run_session(transport, argv, cwd, env, prompts, deadline_seconds, output_limit, emit, cancelled, before_prompt=…, additional_roots=…)`

Run admitted turns in one owned process group; return metadata, never bodies.

Callbacks are caller-owned, fast/bounded functions. Admission is charged to the
same attempt deadline. The caller must bind native permissions and trust before
launch. No capabilities or instructions are inferred from a successful result.

## Coverage

- Public functions: **2** · documented: **2** (**100%**)

