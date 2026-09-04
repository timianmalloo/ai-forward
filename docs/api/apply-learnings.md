---
id: api-apply-learnings
title: "API — apply-learnings.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  apply-learnings.py - the AI-Forward federation / push mechanism.
---

# `apply-learnings.py`

*Generated from `pack/scripts/apply-learnings.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
apply-learnings.py - the AI-Forward federation / push mechanism.

Distributes approved, generalised fleet learnings (from learnings/fleet-classes.jsonl in the
ai-forward repo) into one or more target repos, RECONCILING each against that repo's existing
defect-class register so nothing is duplicated or silently contradicted. It produces a REVIEWABLE
plan + a diff/patch per target repo - it NEVER merges and NEVER executes anything in a target
(spec-dreaming US-5, ADR-0002/0005). The second, pull-based federation path is /updatepack, which
inherits general classes shipped into the pack itself.

Reconciliation (ADR-0004, slug-exact + human-flagged; no fuzzy index):
  * add     - the class has no equivalent in the target -> append to the target's register.
  * merge   - the target already has the class (slug/id or signature match) -> append the instance
              / upgrade the control note, never a duplicate entry.
  * conflict- the incoming class contradicts an existing directive -> SURFACE in the plan for the
              human to resolve; never overridden.

Python 3.8+, stdlib only. Safety: strip+scrub runs again before anything is written to a plan
(defence in depth); a target without the pack is skipped with a note.

Targeting/record layer (ADR-0006, the Dream Manifest):
  * manifest-init --repos a,b,c [--dream id]  -> scaffold learnings/manifests/<id>.json (every fleet
    class assigned to every repo, scope=all, status=pending) + a self-contained compose HTML matrix.
  * push --manifest <file>  -> reconcile PER ASSIGNMENT (a learning only into its `targets`), write a
    reviewable plan per repo, record the outcome back into the manifest's status map, re-render the
    rollout HTML. Manifests name repos -> LOCAL-ONLY (excluded from the published bundle).
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `manifest-init` | scaffold a learnings×repos manifest + compose HTML from the fleet store |
| `push` | reconcile fleet learnings into target repos -> plans |

## CLI — options

| Option | Help |
|---|---|
| `--dream` | optional dream id this manifest derives from |
| `--id` | manifest id (default: manifest-<timestamp>) |
| `--manifest` | a learnings×repos manifest (learnings/manifests/<id>.json) — targets per assignment, records status back |
| `--repos` | comma-separated repo paths, or 'all' (sibling repos with the pack) |
| `--root` | the ai-forward repo root (holds learnings/) |
| `--session` | session id for the audit trail |

## Functions

### `now_iso()`

**Coverage gap** — no docstring in the source.

### `find_root(start)`

**Coverage gap** — no docstring in the source.

### `read_jsonl(path)`

**Coverage gap** — no docstring in the source.

### `scrub(text)`

**Coverage gap** — no docstring in the source.

### `slug(sig)`

**Coverage gap** — no docstring in the source.

### `target_has_pack(repo)`

**Coverage gap** — no docstring in the source.

### `target_register(repo)`

Return {token-set, ids, raw} of the target's existing defect-class register for reconciliation.

### `reconcile(learning, reg)`

Classify one incoming learning against a target register: add | merge | conflict.

### `load_fleet(root)`

Deduped list of promoted fleet learnings (latest wins by slug).

### `control_text(record)`

The control on a learning may be a {rung, text} object (what a dream writes) or a bare
string (a hand-edited store, or an older record — this JSONL is a plain committed file
anyone can edit). Chaining `.get("control", {}).get("text")` crashed with an unhandled
AttributeError on the string form, in the script that writes into other people's
repositories, AFTER it may already have written plans for earlier targets. Neither shape
is malformed enough to justify that; a genuinely absent control still returns "" and is
skipped by the caller. Swept as a class: the identical line existed in dream.py.

### `plan_repo(repo, learnings)`

Reconcile a set of learnings into one target repo -> a plan list (add|merge|conflict|skip).
Shared by `push --repos` and `push --manifest`; never merges, only plans (ADR-0005).

### `find_template(root, name)`

Resolve a pack template whether running from the ai-forward repo or an installed target.

### `render_manifest_html(root, manifest, learnings, mode)`

Render the self-contained learnings×repos matrix (compose|rollout) with the data inlined.

### `render_patch(repo, plan)`

A human-readable reconciliation plan + the exact register additions (never auto-applied).

### `cmd_push(args)`

**Coverage gap** — no docstring in the source.

### `cmd_manifest_init(args)`

Scaffold a learnings×repos manifest from the fleet store + render the compose HTML.

## Coverage

- Public functions: **16** · documented: **9** (**56%**)
- Undocumented (recorded, not invented): `now_iso`, `find_root`, `read_jsonl`, `scrub`, `slug`, `target_has_pack`, `cmd_push`

