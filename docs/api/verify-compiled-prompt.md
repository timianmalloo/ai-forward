---
id: api-verify-compiled-prompt
title: "API — verify-compiled-prompt.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-compiled-prompt.py - the compile-stage gate: a compiled prompt never adds scope.
---

# `verify-compiled-prompt.py`

*Generated from `pack/scripts/verify-compiled-prompt.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-compiled-prompt.py - the compile-stage gate: a compiled prompt never adds scope.

THE CLASS (spec US-4, design docs/design/compile-stage.md). A model step turns the operator's
prose into a goal state. The measured failure is that it ADDS scope: a *Done when* clause the
operator never asked for, a phrase "quoted" from the prompt that is not in it, or a belief
laundered into a clause through an assumption nobody was asked about. This gate refuses each of
those shapes deterministically, against the raw text the audit log holds, before anything is
logged or rendered.

WHAT IT CHECKS, IN ORDER (each refusal `<code>: <target> - fix: <text>` on stderr, exit 1)
  field missing: <name>          the seven goal_state fields are non-empty ("NOT COMPILED" counts)
  raw mismatch: <raw_id>         sha256(raw text) != raw_sha256
  assumption incomplete: #<n>    belief / confirm / breaks all non-empty
  added scope: <clause>          a done_when / not_in_scope clause with no trace
  invalid trace: <clause>        a phrase trace that is not a verbatim substring of the raw text
                                 (whitespace runs collapsed, line endings normalised, CASE-SENSITIVE),
                                 or an assume trace naming an id that is not in assumptions
  decision request missing: #<n> a clause whose only trace is an assumption needs that assumption
                                 consequential: true AND a decision request referencing it
  pass-through refused: <x>      pass-through mode: the same minus the trace checks
  raw not found: <raw_id>        (CLI) the raw id is not a kind:prompt entry in the audit log
In "not-compiled" mode the trace checks are skipped; field and hash checks still run.

USAGE
  python3 verify-compiled-prompt.py verify <compiled.json> [--audit-root <docs dir>]
  python3 verify-compiled-prompt.py --self-test      the nine directions in a temp dir
  python3 verify-compiled-prompt.py                  the same (run-verify-gates.py's argument-free form)

EXIT  0 pass  ·  1 refused  ·  2 usage.  Stdlib only.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `verify` | gate one compiled prompt JSON |

## CLI — options

| Option | Help |
|---|---|
| `--audit-root` | the docs dir holding audit/audit-log.jsonl (default <repo>/docs) |
| `--self-test` | _(no help text — coverage gap)_ |

## Functions

### `refusal(code, target, fix)`

The one refusal grammar: `<code>: <target> — fix: <text>` on a single line.

### `collapse(text)`

Line endings normalised, every whitespace run one space; case untouched.

### `sha256_text(text)`

**Coverage gap** — no docstring in the source.

### `load_raw(audit_root, raw_id)`

The kind:prompt entry with this id from <audit_root>/audit/audit-log.jsonl, else None.

### `verify_document(doc, raw_text)`

Every refusal for this compiled document against the raw text, in the fixed order.

### `trace_table(doc)`

**Coverage gap** — no docstring in the source.

### `verify_file(path, audit_root)`

**Coverage gap** — no docstring in the source.

### `self_test_refusals()`

Every refusal the nine directions produce (for the grammar assertion).

### `self_test()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **9** · documented: **5** (**56%**)
- Undocumented (recorded, not invented): `sha256_text`, `trace_table`, `verify_file`, `self_test`

