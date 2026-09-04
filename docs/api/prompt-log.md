---
id: api-prompt-log
title: "API — prompt-log.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  prompt-log.py — the fast prompt-reuse lens over the project's audit log.
---

# `prompt-log.py`

*Generated from `pack/scripts/prompt-log.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
prompt-log.py — the fast prompt-reuse lens over the project's audit log.

A tiny, stdlib-only front-end for browsing, searching, and **reusing** the prompts already
recorded in the committed **audit log** (docs/audit/audit-log.jsonl). Unified with the Audit &
Change Log Standard (audit-and-change-log.md): there is **one store of prompts** — the audit
log — and this is the reuse lens over it (its arrow-navigable stack + clipboard reuse), the
companion to the broader /auditlog timeline/search/change-log/viewer.

  add      log a prompt (writes a kind:prompt entry to the audit log)  -> via audit-log.py
  list     show the stack, newest first (label · time)
  search   freeform search; matches contain ALL terms
  show     print one entry in full (label, time, text)
  get      print one entry's RAW text only (for piping/copying)
  browse   interactive stack: Up/Down move, Right expand, Left collapse, Enter reuse
  pick     like browse, pre-filtered by a search query (powers /searchprompts)

REUSE MODEL (honest about the medium). A script cannot type into the Copilot CLI's input
line, so "reuse" copies the chosen prompt to the clipboard (pbcopy, when present) and prints
it — you paste it into your next prompt (Cmd+V) and edit before sending.

ONE STORE. The default store is the committed audit log (docs/audit/audit-log.jsonl), so every
prompt the audit mandate records — skill runs, scripts, and prompts you `add` — is reusable
here, and there is no second parallel prompt store. `add` writes through audit-log.py (the
single writer of record, AL0.1) as a kind:prompt entry. Override the store with --store or
$AIFORWARD_PROMPT_LOG (e.g. a legacy <repo>/.aiforward/prompts.jsonl); the reader adapts to
either schema. Stdlib only; no third-party import.
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `add` | log a prompt (to the audit log by default) |
| `browse` | interactive stack (↑/↓ move, → expand, ← collapse, Enter reuse) |
| `get` | print one entry's RAW text (for piping/copying) |
| `list` | show the stack, newest first |
| `pick` | interactive stack pre-filtered by a query (powers /searchprompts) |
| `search` | freeform search (matches contain ALL terms) |
| `self-test` | exercise the data layer (no TTY needed) |
| `show` | print one entry in full |

## CLI — options

| Option | Help |
|---|---|
| `--copy` | also copy to the clipboard |
| `--json` | emit JSON |
| `--label` | a short label / shortname (default: derived from the first line) |
| `--limit` | max entries to show (0 = all) |
| `--no-copy` | don't copy the chosen prompt to the clipboard |
| `--quiet` | don't echo the logged line |
| `--session` | the session id to record on the audit entry (default: prompt-log) |
| `--store` | _(no help text — coverage gap)_ |
| `--summary` | the audit summary (default: 'prompt logged for reuse') |
| `--tag` | a tag (repeatable) |
| `--text` | the prompt text |

## Functions

### `resolve_store(explicit=…)`

**Coverage gap** — no docstring in the source.

### `load_entries(store)`

Return entries oldest-first in the stack shape; callers reverse for newest-first views.

Reads the unified audit log (or a legacy store) and adapts each row; rows with no prompt
text are skipped (you cannot reuse an empty prompt).

### `append_entry(store, entry)`

**Coverage gap** — no docstring in the source.

### `newest_first(entries)`

**Coverage gap** — no docstring in the source.

### `filter_entries(entries, query)`

Case-insensitive AND match over label+text; preserves order.

### `resolve_one(entries_newest, ref)`

Resolve a 1-based newest-first index OR an id (full/unique-prefix) to an entry.

### `copy_to_clipboard(text)`

pbcopy (macOS) / xclip / clip.exe when available; returns the tool name or None.

### `cmd_add(args)`

**Coverage gap** — no docstring in the source.

### `cmd_list(args)`

**Coverage gap** — no docstring in the source.

### `cmd_search(args)`

**Coverage gap** — no docstring in the source.

### `cmd_show(args)`

**Coverage gap** — no docstring in the source.

### `cmd_get(args)`

**Coverage gap** — no docstring in the source.

### `cmd_browse(args)`

**Coverage gap** — no docstring in the source.

### `cmd_pick(args)`

**Coverage gap** — no docstring in the source.

### `cmd_selftest(args)`

Exercise the data layer end-to-end in a temp store (no TTY needed).

### `build_parser()`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **16** · documented: **5** (**31%**)
- Undocumented (recorded, not invented): `resolve_store`, `append_entry`, `newest_first`, `cmd_add`, `cmd_list`, `cmd_search`, `cmd_show`, `cmd_get`, `cmd_browse`, `cmd_pick`, `build_parser`

