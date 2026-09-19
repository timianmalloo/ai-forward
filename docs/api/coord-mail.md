---
id: api-coord-mail
title: "API — coord-mail.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  coord-mail.py - the local message layer: per-session inbox files, ledger twins, bounded dispatch.
---

# `coord-mail.py`

*Generated from `pack/scripts/coord-mail.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
coord-mail.py - the local message layer: per-session inbox files, ledger twins, bounded dispatch.

THE FILE IS THE STORE; THE DOORBELL IS THE PUSH (proposal section 4b, D9 revised). One inbox per
session at `.agents/mail/<session>.jsonl` (a message to `*` lands in `_broadcast.jsonl`),
append-only, one JSON object per line. State-changing kinds are dual-written, without their
body, to the sender's coord ledger `.agents/log/<session>.jsonl` so git carries them across
machines. An acknowledgement is a NEW line in the same file as the message it refers to.

This module is the SINGLE WRITER: the board (coord-board.py) imports `append_mail` by path.

Verbs
  send      --to <session|*> --kind <k> (--body <text> | --body-file <path>) [--ref <x>] [--from <s>]
  read      [--since <id>] [--ack] [--json]          own inbox + broadcasts, unread first
  ack       <id>                                     idempotent; a nack is `send --kind nack --ref <id>`
  dispatch  --harness claude-code|codex|copilot|grok|agy --brief <file> --deadline <s> --fallback <t>
            [--worktree <dir>] [--budget-calls <n>]  runs the harness headless under bounded_process

Exit codes (coord-core's meanings): 0 ok - 2 refused by contract - 3 inbox full - 4 NOT CHECKED.
Design: docs/design/message-layer.md - Spec: docs/specs/message-layer.md
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `ack` | acknowledge one message (a new line; idempotent) |
| `dispatch` | run another harness headless under a deadline |
| `read` | print my unread mail and the broadcasts under an untrusted heading |
| `send` | append a message to a session's inbox (or * for everyone) |

## CLI — options

| Option | Help |
|---|---|
| `--ack` | acknowledge everything shown |
| `--body-file` | a file inside the repository |
| `--body` | _(no help text — coverage gap)_ |
| `--brief` | the compiled prompt file, inside the repository |
| `--budget-calls` | recorded in the audit span |
| `--deadline` | seconds; the child's budget |
| `--fallback` | what the caller does if the run is not verified |
| `--from` | default: $AGENT_SESSION |
| `--harness` | _(no help text — coverage gap)_ |
| `--json` | _(no help text — coverage gap)_ |
| `--kind` | _(no help text — coverage gap)_ |
| `--ref` | a path, an audit id, or the message an ack answers |
| `--session` | default: $AGENT_SESSION |
| `--since` | only ids sorting after this id |
| `--to` | recipient session id, or * (derived for ack/nack) |
| `--worktree` | _(no help text — coverage gap)_ |

## Types

### `MailError`

_(no docstring — coverage gap)_

## Functions

### `mail_dir(root)`

**Coverage gap** — no docstring in the source.

### `inbox_path(root, to)`

**Coverage gap** — no docstring in the source.

### `ledger_path(root, session)`

**Coverage gap** — no docstring in the source.

### `iso_utc(now=…)`

**Coverage gap** — no docstring in the source.

### `parse_ts(text)`

**Coverage gap** — no docstring in the source.

### `read_file(path)`

**Coverage gap** — no docstring in the source.

### `read_inbox(root, session)`

Own inbox plus the broadcast file, sorted by id (time-ordered).

### `acks_in(entries)`

**Coverage gap** — no docstring in the source.

### `is_acked(entry, entries, by=…)`

**Coverage gap** — no docstring in the source.

### `order_key(entry)`

Time order: the timestamp first, the id as the tie-break (ids minted in one millisecond
order by their random bits, so id alone is not deterministic within that millisecond).

### `unread(entries, me, since=…)`

**Coverage gap** — no docstring in the source.

### `queued(root, to)`

Messages in one inbox file not yet acknowledged by anyone.

### `doorbell_state(root, session, now=…)`

(count of unacked messages newer than DOORBELL_EXPIRY_S, newest such id). Never a body.

### `validate_entry(session, entry)`

**Coverage gap** — no docstring in the source.

### `append_mail(root, session, entry, now=…)`

Append one message from `session` to the recipient's inbox; twin it when state-changing.

`root` is the `.agents/` directory. Returns the id. Raises MailError with no partial write.
An ack/nack is written to the file that holds the message it references and is idempotent
by (ref, from) - the existing ack's id is returned then.

### `append_ack(root, session, ref, kind=…, now=…)`

**Coverage gap** — no docstring in the source.

### `cmd_send(args)`

**Coverage gap** — no docstring in the source.

### `cmd_read(args)`

**Coverage gap** — no docstring in the source.

### `cmd_ack(args)`

**Coverage gap** — no docstring in the source.

### `write_harness_status(root, harness, record)`

**Coverage gap** — no docstring in the source.

### `cmd_dispatch(args)`

**Coverage gap** — no docstring in the source.

### `build_parser()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **22** · documented: **5** (**23%**)
- Undocumented (recorded, not invented): `mail_dir`, `inbox_path`, `ledger_path`, `iso_utc`, `parse_ts`, `read_file`, `acks_in`, `is_acked`, `unread`, `validate_entry`, `append_ack`, `cmd_send`, `cmd_read`, `cmd_ack`, `write_harness_status`, `cmd_dispatch`, `build_parser`

