# Project Memory & Continuity (with the Obsidian lens)

*How AI-Forward gives a project durable, tool-neutral memory — what a project has learned and decided — so work compounds across sessions and contributors. This is the methodology-pack analogue of an agent runtime's per-agent `history.md`/`decisions.md`, re-expressed as committed Markdown in the knowledge graph. It composes with the Knowledge Visualization Standard (`knowledge-visualization.md`, V1–V18); it does not replace it.*

Normative keywords (**MUST**, **SHOULD**, **MAY**) follow RFC 2119.

---

## 1. What project memory is (and is not)

**Project memory** is the durable, git-committed, **tool-neutral** record of what a project has learned and decided. In AI-Forward it is **not** a runtime store and **not** per-agent (the pack has reasoning *lenses*, not persistent agent processes); it is four things the repo already commits, plus one rolling ledger:

1. **The knowledge graph** — every artifact's V2 frontmatter (the queryable record). *(V2)*
2. **Decision notes** — `docs/notes/` (V17): a sub-ADR decision, discovered assumption, or resolved question, captured before a session closes.
3. **The glossary** — `docs/knowledge/glossary.md` (V14): the project's ubiquitous language.
4. **Freshness SLAs** — `review-by` per artifact (V13): memory that has gone stale is surfaced, not silently trusted.
5. **The project-memory ledger** — `docs/project-memory.md` (this doc's addition): a rolling, append-only narrative the skills read and append to.

> **M1 — Memory lives in the committed graph, not in a tool.** Project memory **MUST** be plain Markdown committed to the repo, readable with no special tool. Anyone who clones the repo inherits the memory. A memory that requires a running service or a specific editor to read is a violation.

## 2. The project-memory ledger (`docs/project-memory.md`)

The ledger fills the one shape the graph lacked: a **rolling, chronological narrative** an agent can read top-to-bottom on grounding to absorb "what has happened here and why." Template: `templates/project-memory.template.md`.

- **M2 — Read at grounding.** Every skill's grounding step (its first action) **SHOULD** read `docs/project-memory.md` if it exists, alongside the V15 graph traversal, so prior decisions inform the work.
- **M3 — Append at convergence.** Every skill's last action (the Discoverability Mandate, V10) **SHOULD** append a ledger entry for any **material** decision or learning — the same threshold as a decision note (V17). An entry is a dated headline + 1–3 sentences + a confidence label + back-links to the artifacts it touched.
- **M4 — Append-only.** Past entries **MUST NOT** be rewritten — history is the value. The "Project facts" header block is the one editable-in-place exception (durable invariants).
- **M5 — Frontmatter wins.** The ledger is *narrative*, not *authority*; where it disagrees with an artifact's frontmatter or the derived index, the **frontmatter wins** (V2). The ledger never becomes a parallel source of truth.
- **M6 — Freshness.** The ledger carries a `review-by` (90-day SLA, V13) so the freshness gate flags a ledger that has stopped being updated — the backstop against rot.
- **M7 — No secrets or PII.** Entries **MUST NOT** contain secrets or personal data; reference `@handles`, not emails. The `scrub.py` first-pass redacts the obvious cases; CI secret-scanning (gitleaks/Presidio) is the real enforcement. (See the Responsible-AI Policy.)

## 3. The Obsidian lens (optional, never required)

`docs/` is **already a valid Obsidian vault**: `knowledge-visualization.md` (§0, V2) designed the per-file YAML frontmatter so that *"Properties, Bases tables, and Obsidian's graph view all read this frontmatter natively."* So Obsidian is **additive at zero cost** — open `docs/` as a vault to get Properties, Dataview queries (`status: draft`, `review-by` past), and an interactive graph over project memory, with **no schema change**.

- **M8 — Obsidian is a reader, never the writer of record.** The pack **MUST NOT** require Obsidian or any plugin to read or maintain canonical memory. A Dataview (or any plugin) query **MUST NOT** be load-bearing inside a canonical document — `docs-graph.py` is the only query engine the pack depends on. This preserves tool-neutrality (the pack works for someone who never installs Obsidian) and avoids plugin-fragility lock-in.
- **M9 — Optional convenience.** A repo **MAY** add an `.obsidian/` workspace for contributors who use it; it **SHOULD** be git-ignored by default so it never becomes a committed dependency. The Docs Explorer (`docs/index.html`) is the tool-neutral graph view that ships with the pack and needs nothing installed.

**Why not make Obsidian the system of record?** It offers the richest memory UX out of the box, but requiring it imposes per-contributor setup, plugin reliability risk across Obsidian updates, no live co-editing, and a non-WYSIWYG learning curve — costs that violate the pack's dependency-free, tool-neutral promise. Adopted as an *optional lens*, it captures the upside with none of the lock-in.

## 4. Self-verification checklist

- [ ] Project memory is plain committed Markdown, readable with no tool (M1).
- [ ] `docs/project-memory.md` exists from the template, is a graph node (frontmatter + a link), and carries a `review-by` (M2, M6).
- [ ] Skills read it at grounding and append at convergence; entries are append-only with confidence labels + back-links (M2–M4).
- [ ] No entry contains a secret or PII; `scrub.py` has been run over it (M7).
- [ ] No canonical doc depends on an Obsidian/Dataview query; Obsidian config (if any) is git-ignored (M8–M9).

## 5. References

- **`knowledge-visualization.md`** (V1–V18) — the graph model project memory composes with; §0/V2 establish the Obsidian-vault compatibility.
- **`templates/project-memory.template.md`** — the ledger template.
- **`responsible-ai-policy.md`** + **`scrub.py`** — the no-PII enforcement for memory.
- **Zettelkasten / PKM practice** (Obsidian community) — atomic, linked notes; Maps of Content — the tradition behind the graph model.
