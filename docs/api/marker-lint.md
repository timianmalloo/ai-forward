---
id: api-marker-lint
title: "API — marker-lint.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  marker-lint.py - completeness check for the pack's inline decision markers.
---

# `marker-lint.py`

*Generated from `pack/scripts/marker-lint.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
marker-lint.py - completeness check for the pack's inline decision markers.

Tier-1 of the prose->structure review (docs/proposals/prose-to-structure-review.html).
The `simplify:` (L5) and `assume:` (NG4) markers each carry required fields that were,
until now, specified only in prose and therefore unenforced:

  simplify: <shortcut> ... <TRIGGER>                 (the "revisit when" condition; L5/L6)
  assume:   <belief> ... <CONSEQUENCE> ... <CONFIRM>  (what breaks + how to verify; NG4)

This lints for the *semantic components* the directives already require, using the existing
free-prose marker style (a trigger keyword / an em-dash clause / a "Confirm:" cue) rather than
mandating a new label syntax - so every existing marker and the dream.py harvest regex keep
working. It is the first-class harvest command L6 names as the natural follow-up.

Posture (V16a / the docs-graph.py --gate pattern): default reports and exits 0 (warn,
grandfathers legacy free-form); --gate exits 1 on any finding. --json for machine use. A clean
scan of a non-empty corpus says so, so an empty run is distinguishable from a clean one (E14).

Stdlib only; Python 3.8+.
```

## CLI — options

| Option | Help |
|---|---|
| `--gate` | exit nonzero on any finding (default: warn) |
| `--include-md` | also scan .md files |
| `--json` | emit JSON |
| `--root` | directory to scan (default: cwd) |

## Functions

### `scan(root, include_md)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **1** · documented: **0** (**0%**)
- Undocumented (recorded, not invented): `scan`

