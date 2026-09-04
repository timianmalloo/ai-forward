---
id: api-dream
title: "API — dream.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  dream.py - the AI-Forward dreaming / continuous-improvement consolidation harness.
---

# `dream.py`

*Generated from `pack/scripts/dream.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
dream.py - the AI-Forward dreaming / continuous-improvement consolidation harness.

Offline, reviewable consolidation over the committed corpus (audit-log.jsonl, change-log.jsonl,
the defect-class register, captured mitigations, and triggered simplify:/assume: markers). It runs
light -> (REM) -> deep and emits a *dream*: a set of reviewable proposals + an HTML review view + a
Dream Diary entry. It writes NO durable store on `run` - only `apply-decisions` (after a human
approves in the HTML view) touches a durable store, and it re-validates + re-scrubs first.

Design authority: docs/architecture-dreaming.md + ADR-0002..0005 + spec-dreaming.
- Deterministic at the floor (LOA P2): staging, taint gate, scrub, dedup, scoring, thresholds,
  rendering, promotion and reconciliation are all stdlib. The one model step (REM abstraction) is an
  INJECTED boundary (ADR-0005): `run` produces deterministic proposals; a runner may enrich them.
- Human gate, no auto-merge (BoK D3): `run` proposes; `apply-decisions` writes only approved items.
- Append-only inputs, new-artifact output: the source logs are never mutated.

Python 3.8+, stdlib only. Subcommands:
  run                 Consolidate the corpus -> a dream (dream.json + dream-data.js + review HTML + diary).
  capture-mitigation  Append a MitigationRecord (the promotion oracle) - red-green or human-validated.
  apply-decisions     Validate a decisions file from the review view, then promote approved learnings.
  list                Show recent dreams / mitigations.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `apply-decisions` | promote approved learnings from a decisions file |
| `capture-mitigation` | append a MitigationRecord (the promotion oracle) |
| `list` | show recent dreams and mitigations |
| `run` | consolidate the corpus into a dream |

## CLI — options

| Option | Help |
|---|---|
| `--boundary` | where the class applies / does not |
| `--class` | the defect-class id/signature this addressed |
| `--control` | the control the fix leaves behind |
| `--days` | corpus window in days (default 30) |
| `--oracle` | _(no help text — coverage gap)_ |
| `--root` | repo root (default: discover from cwd) |
| `--session` | session id for the audit trail |
| `--summary` | what was mitigated |
| `--test` | a verifying test id (repeatable; required for red-green) |

## Functions

### `find_root(start)`

**Coverage gap** — no docstring in the source.

### `now_iso()`

**Coverage gap** — no docstring in the source.

### `read_jsonl(path)`

**Coverage gap** — no docstring in the source.

### `append_jsonl(path, obj)`

**Coverage gap** — no docstring in the source.

### `scrub(text)`

**Coverage gap** — no docstring in the source.

### `control_text(record)`

The control on a learning may be a {rung, text} object (what a dream writes) or a bare
string (a hand-edited store, or an older record — this JSONL is a plain committed file
anyone can edit). Chaining `.get("control", {}).get("text")` crashed with an unhandled
AttributeError on the string form. A genuinely absent control still returns "" and is
rejected by the caller, so the CI6 guard is unchanged; only the crash is gone.

### `is_tainted(sig)`

**Coverage gap** — no docstring in the source.

### `parse_defect_classes(path)`

Very small parser for docs/lessons/defect-classes.md: one entry per '### <ID> - <shape>'.

### `grep_markers(root)`

Harvest simplify:/assume: markers (bounded; skip generated/vendored trees).

### `load_corpus(root, days)`

**Coverage gap** — no docstring in the source.

### `score(freq, distinct_days, has_control, recency=…)`

**Coverage gap** — no docstring in the source.

### `build_proposals(corpus)`

**Coverage gap** — no docstring in the source.

### `dream_id(root)`

**Coverage gap** — no docstring in the source.

### `render_data_js(dream)`

**Coverage gap** — no docstring in the source.

### `render_html(root, out_dir)`

**Coverage gap** — no docstring in the source.

### `append_diary(root, dream)`

**Coverage gap** — no docstring in the source.

### `cmd_run(args)`

**Coverage gap** — no docstring in the source.

### `cmd_capture_mitigation(args)`

**Coverage gap** — no docstring in the source.

### `cmd_apply_decisions(args)`

**Coverage gap** — no docstring in the source.

### `cmd_list(args)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **20** · documented: **3** (**15%**)
- Undocumented (recorded, not invented): `find_root`, `now_iso`, `read_jsonl`, `append_jsonl`, `scrub`, `is_tainted`, `load_corpus`, `score`, `build_proposals`, `dream_id`, `render_data_js`, `render_html`, `append_diary`, `cmd_run`, `cmd_capture_mitigation`, `cmd_apply_decisions`, `cmd_list`

