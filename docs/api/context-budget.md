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
  prefix      The WHOLE static prefix as the host assembles it - managed blocks (AGENTS.md /
              CLAUDE.md, counted twice where the host loads both), the always-on docs, plus
              stated tool/host allowances - with its own ratchet (CTX-B).
  skills      Per-skill SKILL.md size with a per-skill ratchet and a ceiling: a skill is
              re-injected whole on every invocation, so its size is a per-invocation tax (CTX-E).

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
| `prefix` | the whole static prefix per host, with its ratchet |
| `preflight` | fail before a fan-out that cannot fit |
| `report` | tier table + always-on total |
| `skills` | per-skill SKILL.md size with a per-skill ratchet |

## CLI — options

| Option | Help |
|---|---|
| `--agent` | preflight one agent's lens instead of the main thread |
| `--agents-dir` | override agent definition discovery |
| `--ceiling` | override the derived backstop from context-budget.json |
| `--config` | override context-budget.json discovery |
| `--gate` | fail on unacknowledged prefix growth or a double-loaded CLAUDE.md |
| `--host` | _(no help text — coverage gap)_ |
| `--knowledge-dir` | override knowledge doc discovery |
| `--min-headroom` | working headroom the task itself needs (default 32000) |
| `--overhead` | any further fixed prefix |
| `--root` | override repo-root discovery (AGENTS.md / CLAUDE.md) |
| `--skills-dir` | override skills discovery (pack/commands or .claude/skills) |
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

### `repo_root(explicit=…)`

The repo root the managed blocks live in: the nearest ancestor holding AGENTS.md,
CLAUDE.md or .git.

### `config_path(explicit=…)`

Locate the committed budget config (pack/ in the source repo, docs/ai-forward-pack/ once
installed). Returns None when absent -- the gate then runs ceiling-only and says so.

### `load_config(explicit=…)`

**Coverage gap** — no docstring in the source.

### `write_baseline(path, total, key=…, stamp=…)`

Rewrite only the named baseline + its stamp, preserving comments, key order and formatting.

### `write_json_key(path, key, value)`

Rewrite one JSON object-valued key (the per-skill baseline map). Comments and the other
keys are preserved; the map is re-serialised one entry per line.

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

### `prefix_components(root, kdir, cfg, host)`

Every component of the static prefix this tool can see, per host, with a label each.
'measured' = a file on disk; 'allowance' = a stated figure from config (Inferred).

### `cmd_prefix(args)`

**Coverage gap** — no docstring in the source.

### `skills_dir(explicit=…)`

**Coverage gap** — no docstring in the source.

### `scan_skills(sdir)`

**Coverage gap** — no docstring in the source.

### `cmd_skills(args)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **21** · documented: **12** (**57%**)
- Undocumented (recorded, not invented): `knowledge_dir`, `load_config`, `agents_dirs`, `always_on`, `cmd_report`, `cmd_prefix`, `skills_dir`, `scan_skills`, `cmd_skills`

