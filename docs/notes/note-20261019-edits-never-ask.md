---
id: note-20261019-edits-never-ask
title: "Decision — an edit never asks for permission"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [decision, hooks, permissions, coordination, edit-ownership]
links:
  - { to: forensic-review-rev108-backlog, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-04-19"
review-suggested: []
summary: >-
  The owner ruled on 2026-10-19 that the pack's edit hooks never make the user approve an edit.
  The edit-ownership hook answers allow for a path it checked and found free or owned, deny for
  a held lease or a suspect path, and no decision otherwise, so the session's own permission
  mode decides. It never answers ask, which Claude Code turns into a prompt even in bypass mode.
  Closes FR-089 (the allow is the intent) and defines class EDIT-ASK. Executed in revision 114.
---

# Decision — an edit never asks for permission

**Date:** 2026-10-19 · **Decided by:** the owner · **Executed:** revision 114 (`coord-core.py`)

## The ruling

The owner, in session: *"I should not have to give permission for edits … when I run in bypass
permissions or some form of YOLO the asking for permissions gets in the way … so ensure that on
edits I DON'T have to provide permission."*

## What the hook answers on the Claude host

| Condition | Answer | Effect |
|---|---|---|
| Checked, and the path is free or under your own lease | `allow` | No prompt in any mode |
| Checked, and another session holds the lease | `deny` | Refused with the holder named |
| A traversal (`../…`), or an alias inside the checkout whose target is outside it | `deny` | Refused; the path itself is suspect |
| A write into the primary checkout from a linked worktree (PRIM-A) | `deny` | Unchanged |
| A path outside every checkout of the repository (WT-E) | `{}` | The session's mode decides |
| Not checked: no `AGENT_SESSION`, no coordination record, an unreadable record or payload | `{}` | The session's mode decides |

`ask` is not among the answers. Claude Code prompts on a PreToolUse `ask` even in bypass mode, so
before this ruling every "not checked" condition prompted on every edit. That covers any consuming
repo with no coordination record. Codex, Grok, Antigravity and Copilot keep their recorded
fail-closed `deny` (FR-100 tracks the cost).

## Why `{}` and not `allow` for "not checked"

`allow` would be a grant the hook did not earn: with no record or no identity it cannot know whether
the path is leased. `{}` adds nothing. In bypass mode there is no prompt; in default mode Claude
Code prompts as it would with no pack installed. That is the user's own choice of mode, not the
hook's.

## Controls

- `tests/docs_explorer/test_coord_enforcement.py::EditsNeverPromptTests`. It pins each row above on
  the default and `--host claude` paths. It also fails on any `"ask"` literal in `hook_response`,
  `_not_checked`, `cmd_hook` or `main`.
- Register: class **EDIT-ASK** in `docs/lessons/defect-classes.md`.

## Re-open triggers

- A coordinated multi-agent run loses work because an unverified edit (`{}` in bypass mode) went
  through over a lease the hook could not read.
- Claude Code adds a hook answer that defers to the mode but still shows the agent a reason.
  The "not checked" text could then travel with `{}`.
