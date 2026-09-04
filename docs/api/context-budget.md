---
id: api-context-budget
title: "API — context-budget.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  context-budget.py — the always-on context budget, measured (AI-Forward Pack).
---

# `context-budget.py`

*Generated from `pack/scripts/context-budget.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
context-budget.py — the always-on context budget, measured (AI-Forward Pack).

An instruction set that is attached to every request IS the static prefix of every call.
It is re-read on every turn, it is billed on every turn (cached or not), and it subtracts
from the window before the user has said anything. Left undeclared, it grows silently:
each new knowledge doc looks free at the moment it is written, because nothing reports
what it costs.

This makes that cost a NUMBER, emitted on the normal path (instrumentation-over-inference
IO2/IO4: a feature is not done until its behaviour is measurable by default), and gates it
so the set cannot re-grow UNNOTICED (continuous-improvement CI6: a lesson recorded as
prose is a memoir). The control is a ratchet, not a ceiling: growing the set is fine,
growing it without recording that you did is what fails.

Every knowledge doc declares its own load scope in frontmatter:

    load: always                # attached to every request  -> Tier A, counts against the budget
    load: glob                  # attached to matching files -> Tier B, costs nothing elsewhere
    applyTo: "**/*.cs,**/*.csx"
    load: skill                 # read on demand by a skill  -> Tier C
    skills: [specify, implement]
    load: reference             # consulted, never attached  -> Tier D

FOUNDATION.md is the vendored provenance manifest: always-loaded by definition, kept
verbatim, and carries no frontmatter of its own.

Subcommands
  report      Tier table + the always-on total.
  gate        Fail on unacknowledged growth past the recorded baseline (ratchet),
              and on a derived backstop. CI-able. See pack/context-budget.json.
  agents      Per-agent declared knowledge prefix (the sub-agent lens, P3).
  preflight   Fail when an assembled prefix would not fit a model's window (P5).

Token figures are ESTIMATES (chars / 4.83) and are labelled as such everywhere. The ratio
is calibrated against a measured system prompt of 184,364 tokens over 890,204 characters of
this doc set. It is accurate enough to gate on and is never presented as a measurement:
where an exact count matters, count with the target model's tokenizer.

Python 3.8+, stdlib only.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `agents` | per-agent declared knowledge prefix |
| `gate` | fail on unacknowledged always-on growth (CI-able) |
| `preflight` | fail before a fan-out that cannot fit |
| `report` | tier table + always-on total |

## CLI — options

| Option | Help |
|---|---|
| `--agent` | preflight one agent's lens instead of the main thread |
| `--agents-dir` | override agent definition discovery |
| `--ceiling` | override the derived backstop from context-budget.json |
| `--config` | override context-budget.json discovery |
| `--knowledge-dir` | override knowledge doc discovery |
| `--min-headroom` | working headroom the task itself needs (default 32000) |
| `--overhead` | any further fixed prefix |
| `--tools` | tool-definition tokens (default 24070, the profiled figure) |
| `--update-baseline` | record the current total as the new baseline; commit the diff alongside the change that caused the growth |
| `--window` | target model context window |
| `-v`, `--verbose` | list every doc |

## Types

### `EmptyCorpus`

The scanned directory held no knowledge docs.

## Functions

### `est_tokens(chars)`

Estimated tokens for a character count. Always reported as an estimate.

### `find_dir(*candidates, predicate=…)`

Resolve a pack directory from either the pack layout or an installed repo.

`predicate` guards against a same-named directory that is not the one meant: walking up
from docs/ai-forward-pack/scripts, a bare "knowledge" candidate matches docs/knowledge/
(the evidence dirs), which contains no knowledge docs at all. Matching it produced an
empty scan that the gate then reported as clean -- defect class PACK-P.

### `knowledge_dir(explicit=…)`

**Coverage gap** — no docstring in the source.

### `config_path(explicit=…)`

Locate the committed budget config (pack/ in the source repo, docs/ai-forward-pack/ once
installed). Returns None when absent -- the gate then runs ceiling-only and says so.

### `load_config(explicit=…)`

**Coverage gap** — no docstring in the source.

### `write_baseline(path, total)`

Rewrite only always_on_tokens + the stamp, preserving comments, key order and formatting.

### `agents_dirs(explicit=…)`

**Coverage gap** — no docstring in the source.

### `read_frontmatter(path)`

Return (meta_dict, body). meta values are raw strings; lists are parsed for [a, b].

### `scan(kdir)`

Every knowledge doc with its declared scope and estimated size. Sorted, deterministic.

### `always_on(docs)`

**Coverage gap** — no docstring in the source.

### `cmd_report(args)`

**Coverage gap** — no docstring in the source.

### `cmd_gate(args)`

Fail on UNACKNOWLEDGED GROWTH first, and on the derived backstop second.

The ratchet is the real control. PACK-R is silent accumulation, so the question that
matters is "did this change grow the always-on set without saying so?", not "is the
number above X". An absolute ceiling answers the second question, stays quiet through
the whole accumulation, and then red-lights an ordinary paragraph -- which trains people
to raise the ceiling reflexively, the exact habit the gate exists to break.

### `cmd_agents(args)`

Per-agent declared knowledge prefix (P3). An agent inherits its LENS, not the world.

### `cmd_preflight(args)`

Fail BEFORE a fan-out when the assembled prefix cannot fit the target window (P5).

One failure at the context ceiling predicts every sibling in the wave: the prefix is
the same for all of them. Probing it once costs a subsecond; discovering it per-run
cost 27 of 39 delegated runs in the profiled session.

## Coverage

- Public functions: **14** · documented: **9** (**64%**)
- Undocumented (recorded, not invented): `knowledge_dir`, `load_config`, `agents_dirs`, `always_on`, `cmd_report`

