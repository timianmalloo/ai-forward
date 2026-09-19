---
id: api-coord-decide
title: "API — coord-decide.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  coord-decide.py - the Owner seat's mechanism: decision request -> numbered ruling (D6).
---

# `coord-decide.py`

*Generated from `pack/scripts/coord-decide.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
coord-decide.py - the Owner seat's mechanism: decision request -> numbered ruling (D6).

THE CLASS (proposal §2.1 A7, §4, §7 P5; spec-owner-review). The doctrine says the Owner reviews by
decision request -> numbered ruling (CO1) and the kick ladder escalates with a decision request
(CO17). Until now nothing implemented it: the number was typed by hand and enforced by reputation.
ai-de measured where that ends (tools/verify-ruling-citations.py, 2026-09-11): eight numbers cited
as binding defined nothing, and one number was allocated twice BECAUSE nothing recorded the first.

WHAT THIS IS NOT. Not a store and not an allocator (class ID-A):
  - a decision request IS P1's typed seam request. `request` runs `coord-core.py request add`
    with `--reason decision-request` and the five decision fields as a JSON object in
    `--contract`; `rule` runs `coord-core.py request resolve`. This file never opens the
    request store.
  - the two mails (`decision-request`, `ruling`) go through P4's single writer, `append_mail`
    in coord-mail.py, imported by path (the coord-board.py idiom).
  - the ruling number is read from the register's own headings: `### Ruling NN — <title>` in
    docs/notes/rulings.md, the only file this script writes and the only definition site
    (verify-ruling-citations.py is the gate).

VERBS
  request  --to <owner-session> --options T --evidence T --recommendation T --reversibility T
           --blast-radius T --deadline <seconds|default> --fallback T [--ref <mail-id>] "<question>"
           refused (exit 2, nothing written) without every one of them; writes the P1 row, then
           the decision-request mail (ref = the request id); prints one JSON line.
  rule     <n|next> --title T --text T --request <req-id>
           n must be the next number (max defined + 1); a defined number, a gap, a self-rule
           (requester == ruler, D6) are refused before anything is written. Appends the heading,
           resolves the request with "Ruling n", mails the requester.
  list     [--json]   open decision requests + the register's rulings; an absent store or
           register renders NOT CHECKED (never quiet).

EXIT  0 ok · 2 refused · 3 request terminal · 4 not checked (store unreadable, request unknown,
      siblings not installed) · otherwise the child's code (coord-core.py's stderr passes through)
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `list` | open decision requests and the register's rulings |
| `request` | raise a decision request (P1 request + decision-request mail) |
| `rule` | answer a decision request with the next numbered ruling |

## CLI — options

| Option | Help |
|---|---|
| `--deadline` | seconds until terminal, or `default` |
| `--fallback` | what the requester does at the deadline |
| `--json` | _(no help text — coverage gap)_ |
| `--ref` | the kick mail id this request escalates (CO17 rung 2) |
| `--register` | the ruling register (default: <repo>/docs/notes/rulings.md; inside the repo) |
| `--request` | _(no help text — coverage gap)_ |
| `--root` | the .agents directory (default: $COORD_ROOT or <repo>/.agents) |
| `--scripts` | directory holding coord-core.py and coord-mail.py (default: beside this script) |
| `--text` | _(no help text — coverage gap)_ |
| `--title` | _(no help text — coverage gap)_ |
| `--to` | the Owner (or coordinator) session that rules |

## Functions

### `refuse(code, what, because, remedy, exit_code=…)`

**Coverage gap** — no docstring in the source.

### `load_siblings(scripts)`

coord-core.py (the request reader + resolve_root) and coord-mail.py (append_mail).

### `iso_utc(now)`

**Coverage gap** — no docstring in the source.

### `parse_register(path)`

[{number, title, request}] in file order; an absent file is an empty register.

### `next_number(rulings)`

**Coverage gap** — no docstring in the source.

### `append_ruling(path, number, title, text, request, session, now)`

**Coverage gap** — no docstring in the source.

### `decision_body(question, contract)`

**Coverage gap** — no docstring in the source.

### `cmd_request(args, core, mail, core_path, root, session)`

**Coverage gap** — no docstring in the source.

### `cmd_rule(args, core, mail, core_path, root, repo, session)`

**Coverage gap** — no docstring in the source.

### `cmd_list(args, core, root, repo)`

**Coverage gap** — no docstring in the source.

### `build_parser()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **11** · documented: **2** (**18%**)
- Undocumented (recorded, not invented): `refuse`, `iso_utc`, `next_number`, `append_ruling`, `decision_body`, `cmd_request`, `cmd_rule`, `cmd_list`, `build_parser`

