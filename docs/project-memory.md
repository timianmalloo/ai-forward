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
- **Pack scripts have no runtime third-party dependency:** the Python tools are stdlib-only, and the Docs Explorer core is dependency-free JavaScript. The developer CLI is `tools/aiforward.py` (a Façade over the scripts).
- **The drift gate is `tools/check-consistency.py`** (must print `clean`, CI-enforced); the full proof is `tools/verify-bundle.ps1` (must print `BUNDLE CONSISTENT`). Graph health is `docs/ai-forward-pack/scripts/docs-graph.py {validate,freshness,derive}` (V18 — all graph mechanics go through this bundle).
- **Pack updates** bump `revision` in `pack/adapters/INSTALL.md` frontmatter and replace its `changes` list with the new delta (prior deltas roll into the Prior-revisions log).

## Log (newest first)
*Append an entry at each skill's convergence. Format: `### <ISO date> — <headline>` + 1–3 sentences + a confidence label + back-links to touched artifacts.*

### 2026-07-11 — Cleared the final Docs Explorer implementation vetoes
The timing contract now proves byte-identical packet stdout, and release validation independently rejects contradictory benchmark proofs whose measured p75 or RSS exceeds the pinned limits. The reference workflow is constrained to protected `main`, immutable action SHAs, exact-SHA credential-free checkout, a protected approval environment, and a dedicated ephemeral-runner marker; the live repository now enforces required PR review and the benchmark environment review. The final suite contains 90 Python tests, 19 Node tests, and 155 passing browser tests. Revision 17 remains intentionally unreleased because pinned-reference performance evidence is still absent. *(Verified — Test Architect and Security & Identity independently cleared their implementation hard vetoes.)*
Touches: [[proof-docs-explorer-redesign]], [[threat-model]], [[design-docs-explorer-grounding-spatial-navigation]]

### 2026-07-11 — Finalized Docs Explorer implementation proof while preserving the release gate
The final P0/P1 implementation now has 89 Python tests, 19 Node tests, and 155 passing three-engine browser checks. Grounding benchmark diagnostics attribute warm internal p75 to 801.140 ms (scan 636.701 ms) while wall-clock p75 remains 2,049.978 ms on a non-reference host; Playwright provenance is pinned to public-registry SHA-512 entries with Apache-2.0 metadata and zero audited vulnerabilities. Revision 17 intentionally remains unreleased pending pinned-reference proof or human-approved deviation. *(Verified — independent implementation reviews completed; full automated gates rerun after repairs.)*
Touches: [[proof-docs-explorer-redesign]], [[threat-model]], [[design-docs-explorer-grounding-spatial-navigation]], [[adr-0001-grounding-source-corpus-registry]]

### 2026-07-10 — Implemented the deterministic Docs Explorer redesign
The Explorer now lands in Browse, separates selection from neighborhood context, restores URL/Back state and focus, uses deterministic Graph/Mind-map layouts with relationship-list parity, and fails closed on malformed/oversized graph input while preserving local/offline navigation. `docs-graph.py context` emits bounded provenance packets and the real index derives cleanly after invalid artifacts are reported but excluded. *(Verified — Python/Node suites green; 40 cross-browser checks passed with the two non-Chromium timing cases intentionally skipped.)*
Touches: [[design-docs-explorer-grounding-spatial-navigation]], [[adr-0001-grounding-source-corpus-registry]], [[proof-docs-explorer-redesign]], [[threat-model]], [[privacy-review]]

### 2026-07-10 — Accepted the Docs Explorer grounding and spatial-navigation design
The Explorer design now defines deterministic, provenance-bounded grounding packets; a Browse-first accessible 2D experience with separate selection and neighborhood context; deterministic Graph/Mind-map navigation; and 3D only as a disposable P3 experiment. Five adversarial lenses passed the design gate; implementation and its Proof Pack remain intentionally deferred. *(Verified — Patterns, Simplifier, Test Architect, UX & Accessibility, and SRE verdicts PASS.)*
Touches: [[design-docs-explorer-grounding-spatial-navigation]], [[design-language-docs-explorer]], [[threat-model]], [[privacy-review]]

### 2026-06-22 — Added the prompt-log capability (revision 11): engine + /prompts + /searchprompts
New stdlib engine `pack/scripts/prompt-log.py` (a project-local labelled+timestamped prompt log: add/list/search/show/get + a curses stack with ↑/↓ move, → expand, ← collapse, Enter reuse-via-clipboard; store `<repo>/.aiforward/prompts.jsonl`, git-ignored) plus two utility skills `/prompts` and `/searchprompts`. Honest limits recorded in the skills: no CLI hook auto-captures every prompt (logging is explicit `add` + a default-on managed-block convention), and reuse is clipboard-paste, not input-injection. Skills 13→15, scripts 4→5; INSTALL revision 10→11; both tool surfaces synced; `BUNDLE CONSISTENT`. *(Verified — self-test, both eval cases PASS, consistency clean, verify-bundle green; the interactive curses rendering itself is Inferred — not exercisable headlessly.)*
Touches: prompt-log.py, /prompts, /searchprompts, INSTALL.md, managed blocks

### 2026-06-22 — Outstanding-work audit; design-doc status tables refreshed; this ledger instantiated
A full repo audit found all gates green (clean working tree; 0 open issues/PRs; `check-consistency.py` clean; graph 0 stale/orphan/flagged/drift) and all four pack-evolution capabilities (CLI, doctor, memory, RAI+scrub) already shipped in **revision 8**. The only real loose end was **Doc Drift**: the four `docs/design/*.md` status tables still advertised completed work as "Remaining / best next action" — now corrected to reflect rev-8 completion. This ledger was created (closing the project-memory adoption gap), and the optional "knowledge-docs-in-graph" item was resolved as a recorded won't-do (see architecture.md Flagged risks). *(Verified — gates re-run green after the changes.)*
Touches: [[architecture]], [[design-aiforward-cli]], [[design-pack-doctor]], [[design-project-memory]], [[design-rai-and-scrub]]
