---
id: api-ui-craft-gate
title: "API — ui-craft-gate.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  ui-craft-gate.py - the UI craft gate for AI-Forward.
---

# `ui-craft-gate.py`

*Generated from `pack/scripts/ui-craft-gate.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
ui-craft-gate.py - the UI craft gate for AI-Forward.

Runs the Impeccable deterministic detector (`impeccable detect --json`) over a UI
surface and translates its findings into the pack's own review shape, per
`ui-craft-detection.md` CD11: every finding gains a **dimension** (one of the
DX22 rubric dimensions), a pack **severity** (Nit/Minor/Major/Blocker) with the
CD12 accessibility and token-discipline floors applied, and the owning pack
directive. Stdlib only; lives in the script bundle (deployed to
docs/ai-forward-pack/scripts/).

Why this exists: the detector is the rung-2 automated control under the pack's UI
craft doctrine (`continuous-improvement.md` CI6), but its raw output is not a
review finding. This performs the translation once, in a script, rather than by
hand in every session - and it applies the severity floors that U16 (accessibility
hard veto) and U3/U20 (token discipline) require and a linter's own defaults do not.

Modes
  (default)   report  - print the measurement + the rubric table; exit 0
  --gate      gate    - exit 1 if any Blocker-mapped finding is present
  --a11y-obligation   accessibility findings become Blockers (CD12)
  --markdown          emit a paste-ready markdown section for docs/reviews/ui-<surface>.md
  --json              emit the translated findings as JSON

Exit codes: 0 clean/report, 1 blockers present (with --gate), 2 detector unavailable
or it scanned nothing (CD9 - an empty corpus is a success-shaped failure).

Usage:
  ui-craft-gate.py <file-or-dir-or-url> [...] [--gate] [--a11y-obligation]
                   [--markdown] [--json] [--impeccable <cmd>]
```

## CLI — options

| Option | Help |
|---|---|
| `--a11y-obligation` | the product is under an accessibility obligation; accessibility findings become Blockers (CD12) |
| `--gate` | exit 1 if any Blocker-mapped finding is present |
| `--impeccable` | explicit detector command (default: auto-resolve) |
| `--json` | emit the translated findings as JSON |
| `--markdown` | emit a paste-ready markdown review section |

## Functions

### `resolve_detector(explicit=…)`

Return an argv prefix that runs the detector, or None.

Order: explicit --impeccable > `impeccable` on PATH > local node_modules >
`npx impeccable`. Establishing the tool rather than assuming it is NG1.

### `run_detector(prefix, targets)`

Run `detect --json` and return the parsed finding list.

The detector exits non-zero when it finds anti-patterns, which is a *result*,
not a failure - so the exit code is deliberately not treated as an error
(`end-to-end-integrity.md` E14: read the state, do not read the exit code).

### `translate(findings, a11y_obligation)`

CD11 - give each finding the pack's shape; CD12 - apply the severity floors.

### `measurement(rows)`

DX23 - measure before you diagnose. Counts are the diagnosis.

### `render_markdown(rows, targets)`

**Coverage gap** — no docstring in the source.

### `render_text(rows, targets)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **6** · documented: **4** (**67%**)
- Undocumented (recorded, not invented): `render_markdown`, `render_text`

