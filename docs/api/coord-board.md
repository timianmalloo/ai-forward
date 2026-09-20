---
id: api-coord-board
title: "API — coord-board.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  coord-board.py — the board: human transparency over agent messages (spec-board, D12).
---

# `coord-board.py`

*Generated from `pack/scripts/coord-board.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
coord-board.py — the board: human transparency over agent messages (spec-board, D12).

A READ MODEL over the message store, never a store. It folds every session inbox
(`.agents/mail/<session>.jsonl`) and every ledger twin (`type: mail` records in
`.agents/log/<session>.jsonl`) into one timeline, one row per mail id:

    ts · from → to · kind · ref · age · acked?

Reading writes nothing (the read-rate is measured from the shell history / the session
profiler, not by the board). An empty corpus prints NOT CHECKED, never "all quiet" (R4).
A human speaks into the same inboxes with `board post`, which goes ONLY through the message
layer's single writer — P4's `append_mail(root, session, entry)` in coord-mail.py, imported by
path — so a post that bypasses the inbox writer is impossible by construction. Until that file
lands, `--writer <path>` names a module with the same signature (the tests ship a fixture).

Subcommands
  board            print the rows (or NOT CHECKED); --json for the same rows as data
    --follow       poll every --interval seconds (5.0) until --max-polls reads (720 = 1 h at
                   5 s) have happened, printing only rows not yet printed; says why it stopped
    --since <id>   rows ordered after that mail id (by ts, then id)
    --session <s>  rows where from == s, to == s, or to == "*"
  board post --to <session|*> "<text>" [--kind note|ruling] [--ref <ref>] [--from <session>]
             [--writer <path>]

Conventions
  --root is the `.agents` directory (default: <repo root>/.agents, the repo root found by
  walking up from cwd to a .git file or directory — the layout coord-core.repo_root reads).
  A root outside the repository is refused (COORD-NOT-CHECKED-ROOT, as coord-core does).
  Python 3.8+, stdlib only. Exit 0 for every read, 2 for a refused argument or post.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `board` | print the board (a read model; reading writes nothing) |
| `post` | write a human note or ruling through the single writer |

## CLI — options

| Option | Help |
|---|---|
| `--follow` | poll until --max-polls reads |
| `--from` | sender (default: $AGENT_SESSION or 'human') |
| `--interval` | seconds between polls |
| `--json` | the rows as JSON |
| `--kind` | note (default) or ruling |
| `--max-polls` | stop after this many reads (default 720 = 1 h at 5 s) |
| `--ref` | the decision request a ruling answers (DR-n), or a path/id |
| `--root` | the .agents directory (default: <repo root>/.agents) |
| `--session` | rows from or to this session (or to '*') |
| `--since` | rows ordered after this mail id |
| `--to` | recipient session, or '*' |
| `--writer` | path to the module exposing append_mail (default: sibling coord-mail.py) |

## Functions

### `repo_root(cwd)`

The PRIMARY checkout, from any worktree - the `.agents` stores are per repository.

Walk up from cwd to the first `.git` entry. A directory is the primary itself. A FILE is a
linked worktree's pointer (`gitdir: <primary>/.git/worktrees/<name>`), so the primary is
that path's third parent. Filesystem only, no subprocess (coord-core's reasoning). Before
this the board resolved the NEAREST checkout and, from a worktree, read the committed ledger
copies and no inbox at all (class WT-A).

### `resolve_root(cwd, raw)`

The .agents root, refused when it resolves outside the repository (coord-core's rule).

### `read_sources(root)`

Return (inbox_lines, twins, errors, files_scanned) — every line of every source, once.

### `fold(inbox, twins, now=…)`

Pure fold: store lines -> rows keyed by mail id. Rendering twice yields equal rows.

### `apply_filters(rows, session=…, since=…, errors=…)`

**Coverage gap** — no docstring in the source.

### `format_row(row)`

One row, plain text, no colour-only meaning: the ack state is a WORD beside its glyph.

### `not_checked_line(root)`

**Coverage gap** — no docstring in the source.

### `read_board(root, session=…, since=…)`

**Coverage gap** — no docstring in the source.

### `cmd_board(args, root)`

**Coverage gap** — no docstring in the source.

### `new_ulid(now=…)`

A 26-char Crockford-base32 ULID: 48-bit ms timestamp + 80 random bits (stdlib only).

### `load_writer(path)`

Import the message layer's writer module BY PATH (the file lands with P4 at the join).

### `build_entry(to, body, kind, ref, sender, now=…)`

**Coverage gap** — no docstring in the source.

### `cmd_post(args, root)`

**Coverage gap** — no docstring in the source.

### `build_parser()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **14** · documented: **7** (**50%**)
- Undocumented (recorded, not invented): `apply_filters`, `not_checked_line`, `read_board`, `cmd_board`, `build_entry`, `cmd_post`, `build_parser`

