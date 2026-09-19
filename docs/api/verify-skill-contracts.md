---
id: api-verify-skill-contracts
title: "API — verify-skill-contracts.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-skill-contracts.py - every skill declares its seat and cites the shared stage its shape needs.
---

# `verify-skill-contracts.py`

*Generated from `pack/scripts/verify-skill-contracts.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-skill-contracts.py - every skill declares its seat and cites the shared stage its shape needs.

THE CLASS (coordination proposal §7b.5, D15; spec-compile-readers US-4..US-8). The pack has a
doctrine of delegation - three shared stages in knowledge/agent-coordination.md (CO-S0 compile,
CO-S1 seat, CO-S2 stop = message) - and, measured on 2026-09-19, 25 of 28 skills declared no
seat, 11 of 14 prose-input skills did not cite CO-S0, and none of the four hard stops cited
CO-S2. Doctrine no skill cites is prose, and prose is a memoir (CI6). This lint is the control.

WHAT IT CHECKS. Every `<skills-root>/<name>/SKILL.md` (plus that skill's `reference/*.md`):
  1. seat            frontmatter carries `runs_as: Coordinator|Sub-Agent|either` (CO-S1)
  2. fan-out         a skill naming a fan-out cap above zero (`fan-out cap 2`, `: 3`, `of 4`,
                     `<= 4`) cites CO-S0 and the five-part contract with a termination condition
  3. hard stop       a hard-stop stage (`**STOP`, `stop for human`, `never merges`) cites CO-S2
  4. dispatch order  a dispatcher (a Dispatch heading or stage label, `coord dispatch`, or a
                     sentence-initial `spawn`) cites CO-S0 in SKILL.md before that instruction

Refusals, one per line on stdout, in the pack's grammar:  <code>: <skill> — fix: <text>
Codes are stable (O7): seat missing · seat invalid · fan-out without compile · fan-out without
contract · hard stop without message · dispatch before compile · skills root missing.

USAGE
  python3 verify-skill-contracts.py                 check pack/commands (or .claude/skills)
  python3 verify-skill-contracts.py --root <repo>   check that repository's skills
  python3 verify-skill-contracts.py --self-test     prove every direction can fail (DC-104)

EXIT  0 clean  ·  1 refusals  ·  2 usage (no skills root)
```

## CLI — options

| Option | Help |
|---|---|
| `--root` | repository root (default: found by walking up from this script or the cwd) |
| `--self-test` | prove the gate can fail |

## Functions

### `check_skill(name, skill_md, reference_texts)`

Returns the refusal lines for one skill. Pure over the texts (the self-test and the tests
call it through the CLI; the CLI is the only place that touches the filesystem).

### `find_skills_root(root)`

**Coverage gap** — no docstring in the source.

### `default_root()`

**Coverage gap** — no docstring in the source.

### `scan(skills_root)`

**Coverage gap** — no docstring in the source.

### `self_test()`

Every direction must FAIL on its fixture and the good skill must pass (DC-104).

## Coverage

- Public functions: **5** · documented: **2** (**40%**)
- Undocumented (recorded, not invented): `find_skills_root`, `default_root`, `scan`

