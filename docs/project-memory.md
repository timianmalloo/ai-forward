---
id: project-memory
title: "Project Memory"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [memory, continuity]
links:
  - { to: architecture, rel: relates-to }
  - { to: design-project-memory, rel: implements }
review-by: "2026-09-20"
summary: >-
  The durable, append-only record of what this project has learned and decided — read at every
  skill's grounding and appended to at every skill's convergence. Frontmatter/graph is authority;
  this ledger is narrative.
---

<!--
Project memory ledger — the rolling, graph-linked record of decisions & learnings.
Design: docs/design/project-memory.md. Knowledge: .github/instructions/project-memory-and-obsidian.instructions.md.

HOW IT WORKS (the convention that makes it load-bearing):
- READ at grounding: every skill, as its first action, reads this file if present, so prior
  decisions/learnings inform the work (alongside the V15 graph traversal).
- APPEND at convergence: every skill, as part of its last action (the Discoverability Mandate
  V10 / decision-note step V17), adds an entry for any material decision or learning.
- Entries are APPEND-ONLY (history is the value); never rewrite a past entry.
- Frontmatter/graph WINS over the ledger (V2) — this is narrative, not authority.
- NO secrets / PII in entries (reference @handles, not emails). Run `scrub.py` over this file;
  use gitleaks/Presidio in CI for real enforcement.
- OBSIDIAN (optional lens): docs/ is already a valid Obsidian vault — open it to get Properties,
  Dataview queries, and a graph view over this ledger. Obsidian is a reader, never required.
-->

# Project memory

## Project facts (durable)
*Standing invariants a contributor or agent should know before touching this project. Edit in place as facts change; this block is the exception to append-only.*

- **Source of truth is `pack/`.** `.claude/`, `.github/{instructions,prompts,agents}/`, and the generated parts of `docs/` (`docs/ai-forward-pack/`, `docs/index.html`) are produced by `tools/sync-pack.ps1` — never hand-edit them. After any `pack/` edit, re-run the sync and commit `pack/` + both installs together.
- **Dogfood artifacts under `docs/` are hand-authored, not generated:** `docs/architecture.md`, `docs/design/`, `docs/knowledge/`, `docs/notes/`, this ledger, and the accumulated `docs/docs-index.js`. `sync-pack.ps1` does not touch them.
- **All scripts are stdlib-only Python** (no third-party import); the developer CLI is `tools/aiforward.py` (a Façade over the scripts).
- **The drift gate is `tools/check-consistency.py`** (must print `clean`, CI-enforced); the full proof is `tools/verify-bundle.ps1` (must print `BUNDLE CONSISTENT`). Graph health is `docs/ai-forward-pack/scripts/docs-graph.py {validate,freshness,derive}` (V18 — all graph mechanics go through this bundle).
- **Pack updates** bump `revision` in `pack/adapters/INSTALL.md` frontmatter and replace its `changes` list with the new delta (prior deltas roll into the Prior-revisions log).

## Log (newest first)
*Append an entry at each skill's convergence. Format: `### <ISO date> — <headline>` + 1–3 sentences + a confidence label + back-links to touched artifacts.*

### 2026-06-22 — Added the prompt-log capability (revision 11): engine + /prompts + /searchprompts
New stdlib engine `pack/scripts/prompt-log.py` (a project-local labelled+timestamped prompt log: add/list/search/show/get + a curses stack with ↑/↓ move, → expand, ← collapse, Enter reuse-via-clipboard; store `<repo>/.aiforward/prompts.jsonl`, git-ignored) plus two utility skills `/prompts` and `/searchprompts`. Honest limits recorded in the skills: no CLI hook auto-captures every prompt (logging is explicit `add` + a default-on managed-block convention), and reuse is clipboard-paste, not input-injection. Skills 13→15, scripts 4→5; INSTALL revision 10→11; both tool surfaces synced; `BUNDLE CONSISTENT`. *(Verified — self-test, both eval cases PASS, consistency clean, verify-bundle green; the interactive curses rendering itself is Inferred — not exercisable headlessly.)*
Touches: prompt-log.py, /prompts, /searchprompts, INSTALL.md, managed blocks

### 2026-06-22 — Outstanding-work audit; design-doc status tables refreshed; this ledger instantiated
A full repo audit found all gates green (clean working tree; 0 open issues/PRs; `check-consistency.py` clean; graph 0 stale/orphan/flagged/drift) and all four pack-evolution capabilities (CLI, doctor, memory, RAI+scrub) already shipped in **revision 8**. The only real loose end was **Doc Drift**: the four `docs/design/*.md` status tables still advertised completed work as "Remaining / best next action" — now corrected to reflect rev-8 completion. This ledger was created (closing the project-memory adoption gap), and the optional "knowledge-docs-in-graph" item was resolved as a recorded won't-do (see architecture.md Flagged risks). *(Verified — gates re-run green after the changes.)*
Touches: [[architecture]], [[design-aiforward-cli]], [[design-pack-doctor]], [[design-project-memory]], [[design-rai-and-scrub]]
