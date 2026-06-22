---
id: design-project-memory
title: "Design — project memory + Obsidian decision (suggestion 3)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [memory, obsidian, knowledge-graph, continuity]
links:
  - { to: kb-pack-evolution, rel: implements }
review-by: "2026-12-11"
summary: >-
  A project-memory convention — an append-only, graph-linked docs/project-memory.md ledger that
  skills read at grounding and append to at convergence — plus the explicit decision to treat
  Obsidian as an OPTIONAL lens over the existing vault, never a dependency.
---

# Design: project memory + Obsidian decision (suggestion 3)

- **Status:** Accepted
- **Spec / architecture:** `docs/knowledge/pack-evolution/` · `docs/architecture.md`
- **Delivery phase / vertical slice:** Pack-evolution slice 3. Pure-convention + one template + one knowledge doc; no runtime.
- **Author(s) / date:** Documentation Steward + Tech Lead + Simplifier, 2026-06-14

## The Obsidian decision (the question the user asked) — resolved
**Decision: adopt Obsidian as an OPTIONAL lens, NOT a dependency or the system of record.** *(Verified rationale — knowledge base headline #4.)*
- **Why it's nearly free:** `knowledge-visualization.md` §0/V2 already designed the per-file YAML frontmatter so `docs/` is *"a valid Obsidian vault (Properties, Bases tables, and Obsidian's graph view all read this frontmatter natively)."* Opening `docs/` in Obsidian today yields Properties, Dataview queries (`status`, `review-by`), and a graph view over existing memory — **zero schema change**.
- **Why it must not be required:** the Obsidian+git research records real costs — per-contributor setup, plugin fragility across updates, no live co-edit, not WYSIWYG. Requiring it would break the pack's **tool-neutrality** (it must work for someone who never installs Obsidian) and violate the no-gratuitous-dependency rule.
- **What we ship for it:** (a) a short **"Project memory & Obsidian" knowledge doc** documenting the already-true compatibility and how to open the vault; (b) an **optional, git-ignored-by-default `.obsidian/`** convenience the doctor/scrub ignore; (c) canonical memory stays **plain Markdown + `docs-graph.py`** — no Dataview query is ever load-bearing in a canonical doc. *Obsidian is a reader, never the writer of record.*

## Responsibility
Define **project memory** as the durable, git-committed, tool-neutral record of what a project has learned and decided, and fill the one shape the pack lacked: a **rolling, append-only ledger** (`docs/project-memory.md`) that the **grounding** step of every skill reads and the **convergence** step appends to. It complements — never replaces — the per-artifact frontmatter (V2), decision notes (V17), and glossary (V14). Explicitly **not** a per-agent memory (the pack has lenses, not processes — knowledge base #3), **not** a new store, **not** a runtime.

## Contracts
- **Exposed:** `docs/project-memory.md` — a frontmatter'd graph node (`type: doc`), an append-only reverse-chronological list of **memory entries**: `### YYYY-MM-DD — <one-line headline>` + 1–3 sentences (what changed/was decided/learned), a **confidence label**, and typed back-links to the artifacts it touched. A short standing "Project facts" header (durable invariants) sits above the log.
- **Consumed:** the knowledge graph (read at grounding via V15 traversal); the decision-notes flow (V17) for sub-ADR specifics; `docs-graph.py derive` to index it. *(Verified — pack files.)*
- **Convention contract (the load-bearing part):** every skill's **grounding** reads `docs/project-memory.md` if present (added to the skills' first action); every skill's **last action** appends an entry for any material decision/learning (folds into the existing Discoverability Mandate V10/V17 step). A `review-by` makes the existing freshness gate (V13) surface a stale ledger.

## Patterns
- **Append-only ledger / event log** — entries are added, never rewritten (history is the value). Named `# Pattern: Append-only ledger`.
- **Map of Content (V3)** over the graph — the ledger links into artifacts; it is navigation + narrative, not a parallel store.
- **Optional decorator (Obsidian)** — a read-only lens layered over the canonical vault; rejected alternative: making Obsidian/Dataview the query engine (would lock the canonical docs to a plugin — knowledge base failure mode "Obsidian lock-in").

## Data shapes
Memory entry (Markdown, not a serialized type): heading `### <ISO date> — <headline>`; body 1–3 sentences; `*(Verified|Inferred|Flagged)*`; back-links `[[artifact-id]]`/`(to: <id>, rel: relates-to)`. The file carries standard V2 frontmatter (`id: project-memory`, `type: doc`, `owner`, `review-by`, links to `architecture` and the active work).

## Error & concurrency model
Plain Markdown; concurrency = git (merge conflicts resolved like any doc — entries are append-mostly so conflicts are rare and additive). Idempotent reads. No partial-write risk (a text append).

## Failure-mode analysis

| Failure mode | From which choice | Disposition | How addressed | Detection | Test |
|---|---|---|---|---|---|
| ledger rot (entries stop being added) | append-on-convergence convention | mitigate + detect | the convention is part of skills' last action; a `review-by` makes V13 freshness flag it | `docs-graph.py freshness` WARN | covered by freshness gate (existing) |
| ledger captures PII/secret | free-text entries | mitigate | guidance "no secrets/PII in entries" + the scrub (design 4) runs over it | scrub findings | `scrub_redacts_memory_email` (design 4) |
| Obsidian config committed by accident | optional `.obsidian/` | prevent | `.obsidian/` git-ignored by default in the install guidance | git status | n/a (gitignore) |
| canonical doc depends on a Dataview query | Obsidian lens | prevent | rule: no plugin query is load-bearing in a canonical doc; `docs-graph.py` is the only query engine | review | n/a (convention) |
| ledger and graph disagree | two records | mitigate | frontmatter/graph wins (V2); ledger is narrative, not authority | derive drift | existing index-drift check |

## Adversarial analysis (STRIDE-lite)
No new trust boundary: project memory is committed Markdown read/written by the same humans/agents who write all other docs; no network, no privilege. The one real risk is **Information disclosure** — a memory entry leaking a secret/PII into git history. Disposition: **mitigate** via the no-PII authoring guidance + the design-4 scrub as a pre-commit/periodic control, and **transfer** to CI secret-scanning (gitleaks, named) for real enforcement. Recorded, with the scrub as the in-pack first-pass.

## Privacy analysis (LINDDUN-lite)
**Touches personal data — possibly.** A free-text ledger *could* record a person's name/email in a decision ("decided with @alice"). Findings: **D**isclosure (PII into git history) → **mitigate** (authoring guidance: reference handles not emails; the scrub redacts emails); **N**on-compliance (retention) → **accept** with rationale: project memory is intentionally durable (the value is permanence), retention is "life of the repo", and the rights path is the same as any git history (rewrite via `git-filter-repo` if required). Data categories: at most handles/names that already appear in commits; **no special-category data** belongs in memory (stated as a rule). Residual risk: low, equal to ordinary commit metadata.

## UI & interaction design
**Medium:** Markdown document (read in any editor; optionally Obsidian). **Key view:** `project-memory.md` — standing "Project facts" block at top, then reverse-chronological entries. In Obsidian it additionally renders as graph nodes + Dataview-queryable Properties (the optional lens). **States:** empty (first run — a template with the "Project facts" stub and "no entries yet" line guiding the first append) · populated (the log) · stale (V13 flags it in the Explorer health view). **Copy (real):** template headers — `# Project memory`, `## Project facts (durable)`, `## Log (newest first)`, and the empty-state line `_No entries yet — skills append here at convergence._`. **Accessibility/perf:** plain Markdown, instant; the Explorer/Obsidian graph is the visual lens.

## Telemetry
N/A (a committed document). Its "observability" is the Docs Explorer health view (stale/orphan/flag) which already covers it once it is a graph node.

## Test plan
Triggers: **T7** (a payload/format others consume — the ledger entry shape) → **D6** light: a check that `project-memory.md` parses as a valid graph node (`docs-graph.py validate` passes with it present); **D0** throughout. Eval case `project-memory`: the template instantiates, carries valid frontmatter, links into the graph (no orphan), and `docs-graph.py validate` exits 0. The PII path is tested under design 4 (the scrub redacts an email planted in a memory entry).

## Conformance notes
**Counts impact:** adds `templates/project-memory.template.md` → templates 15→16; adds a knowledge doc `project-memory-and-obsidian.md` → knowledge_docs 18→19 (and a `.github/instructions/` wrap). Honors V2/V13/V14/V17 (memory is graph-native). No third-party dependency (Obsidian optional).

## Flagged risks & residual unknowns
- Ledger freshness (knowledge base Flagged) — mitigated by `review-by` + append-on-convergence; residual: relies on the convention being followed (the freshness gate is the backstop).

## Status & next action
| | |
|---|---|
| **Completed** | project-memory + Obsidian-decision design — **implemented in revision 8** (`templates/project-memory.template.md` + `knowledge/project-memory-and-obsidian.md`; commit 2fa8bce) |
| **Remaining** | none — all four pack-evolution designs delivered in revision 8. Ledger **instantiated** at `docs/project-memory.md` (2026-06-22). |
| **Best next action** | none outstanding — skills read/append the ledger at grounding/convergence |

## Gate record
`GATE design · 2026-06-14 · Documentation Steward + Simplifier + Privacy & Data Governance · criteria met: Obsidian decision resolved (optional lens, evidenced), memory is graph-native not a new store, privacy flow analyzed, counts impact recorded · verdict: PASS · vetoes→resolution: Simplifier confirmed no new store (convention + 1 template + 1 doc); Privacy confirmed the no-special-category rule + scrub mitigation · author did not self-clear`

---
**Handoff:** → `/implement` (via `/extendaibundle`).
