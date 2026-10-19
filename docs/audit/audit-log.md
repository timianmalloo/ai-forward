---
id: audit-log
title: "Audit & Change Log"
type: doc
status: accepted
owner: "@timianmalloo"
phase: ""
tags: [audit, history, change-log, project-memory, knowledge-graph]
links:
  - { to: architecture, rel: relates-to }
  - { to: docs-index, rel: relates-to }
review-by: "2027-04-19"
review-suggested: []
summary: >-
  The project's durable, committed activity & decision history — an append-only audit
  log of every meaningful prompt/skill/script and a curated change log of design
  decisions — the committed counterpart to a session's ephemeral store, so work
  compounds across sessions. This node represents the bundle in the knowledge graph.
---

# Audit & Change Log

This is the knowledge-graph hub node for the project's **audit & change log** — the durable,
committed record of what was prompted, done, and decided in this repo, so a human or a fresh
Copilot/Claude Code session can read the project's own history instead of starting blind. The
standard governing it is `audit-and-change-log.md` (`.github/instructions/` / `.claude/knowledge/`).

## What's here

| File | What it is |
|---|---|
| [`audit-log.jsonl`](audit-log.jsonl) | **Audit log** — append-only, one JSON object per line: every meaningful prompt / skill run / script. Every entry carries `id` · `shortname` · `datetime` · `session` · `actor` · `prompt` · `summary` · `kind` · `skill` · `tool` · `artifacts` · `tags` · `outcome`; newer entries add the goal state (`goal`, `done_when`, `tier`, `fan_out`, AL5b) and the measured `duration_seconds` / `started_at` (AL4a). |
| [`change-log.jsonl`](change-log.jsonl) | **Change log** — the curated subset: meaningful design decisions, each with its prompt, summary, rationale, linked artifacts, and the **git context before and after**. |
| [`index.html`](index.html) | the **interactive viewer** — a searchable (session / date / keyword) timeline, expandable rows, copy-prompt, and a Full-history ↔ Changes toggle. |
| `audit-data.js` | the derived `window.AUDIT_DATA` the viewer loads (regenerated from the JSONL; never hand-edited). |

## How it's written and read

- **Written** only through `docs/ai-forward-pack/scripts/audit-log.py` (`append` / `change` / `import`; `start` marks a run's start so its entry measures its duration), never by hand-appending JSON. `prompt-log.py add` writes its `kind: prompt` entries through the same script. Every skill appends an audit entry as its last action (the **Audit Mandate**). `/collectknowledge`, `/define-architecture`, `/design-slice` and `/migrate` must also append a change entry (the **Change Mandate**); `/specify`, `/implement`, `/investigate`, `/forensicreview`, `/ui-design` and `/extendaibundle` add one when a run makes a decision of the same weight.
- **Checked** by `audit-log.py verify` (every line parses; 460 audit and 72 change entries on 2026-10-19).
- **Read** via the `/auditlog` skill (last-N, search, recall-and-redo a prompt, open the viewer), the viewer above (built from [`audit-explorer.template.html`](../ai-forward-pack/templates/audit-explorer.template.html)), or `/prompts` and `/searchprompts` for the logged prompts. A skill's grounding step glances at the recent history for the artifacts in scope, so prior decisions inform new work.

## Why it exists

A coding session's reasoning is the most valuable thing it produces and the first thing lost when
the session ends — the session store is ephemeral and private. This bundle is the **committed,
shared** projection of that activity, keyed by session, so the history compounds: every new session
inherits what prior sessions prompted, did, and decided. The audit log answers *"what has happened
here?"*; the change log answers *"what was decided, and why?"*.
