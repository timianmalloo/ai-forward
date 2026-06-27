<!-- AI-FORWARD-PACK:BEGIN (managed block — keep this block intact when reconciling; replace it wholesale on pack updates) -->
## AI-Forward Pack + Agent Knowledge Pack

This repository uses the **Agent Knowledge Pack** (the reasoning constitution and Rules of
the Road) and the **AI-Forward Pack** on top of it. Honor them on every non-trivial task.

- **Reasoning spine:** run the Rigor Protocol — `.claude/knowledge/rigor-protocol.md`. Do not
  rush to a plausible answer: map, interrogate, ground in evidence, disconfirm, then converge,
  with a confidence label on every claim.
- **Personas (dual-mode):** author in Peer Mode, review in Adversary Mode; the author never
  clears its own hard veto. Roster + the operating standard (severity, veto-clears-when,
  conflict rule): `.claude/knowledge/persona-cards.md` and `.claude/knowledge/persona-audit.md`.
- **Skills (16):** thirteen reasoning workflows — `/collectknowledge`, `/adddomainexperts`,
  `/specify`, `/define-architecture`, `/design`, `/implement`, `/investigate`, `/document`,
  `/adopt`, `/migrate`, `/updatepack`, `/addpacktorepo`, `/extendaibundle` — plus the `/auditlog`
  lens over the durable audit & change log, and two prompt-log utilities, `/prompts` and
  `/searchprompts`, that browse and search your logged prompts to reuse. They live in
  `.claude/skills/`. Templates: `docs/ai-forward-pack/templates/`.
- **Prompt log (utility):** `/prompts` opens your logged prompts as an arrow-navigable stack
  (newest on top; → expand, ← collapse, Enter reuse) and `/searchprompts` searches them; reuse
  copies the chosen prompt to the clipboard to paste-and-edit. Engine:
  `docs/ai-forward-pack/scripts/prompt-log.py` (stdlib; store `<repo>/.aiforward/prompts.jsonl`,
  git-ignored). When the user gives a **substantive** request, append it with
  `prompt-log.py add "<text>"` so it is recallable (no CLI hook auto-captures prompts; stop when asked).
- **Unfamiliar APIs/SDKs/MCP servers:** run the Spike Protocol (read the source, run a PoC)
  before depending on a contract — `.claude/knowledge/spike-protocol.md`.
- **Specification:** `/specify` produces **one spec with three layers** — Functional (what &
  why), UX (how it works: IA, user flows, structure), UI (how it looks) — written bottom-up,
  UX before UI, each absent layer marked N/A — `.claude/knowledge/specification-standards.md`; the
  UX Researcher/IA holds the UX-specification veto, UX & Accessibility the UI veto.
- **UI:** whenever the work has a user-facing interface (any medium), the UI & Interaction
- **UI archetype:** for a user-facing UI, select the **archetype** (routing/temporal/data) as a
  determinism control before generating — `.claude/knowledge/ui-archetype-grammar.md` (G1–G16) + the
  16-archetype catalog; record the Archetype Signature in the spec, build to its facet rules.
  Design Standard governs excellence — token systems, complete component states, HAX + Shape-of-AI
  patterns for AI UIs, WCAG 2.2 AA — `.claude/knowledge/ui-interaction-design.md`; the UX &
  Accessibility lens holds the veto.
- **Testing:** what to test and what counts as proof is governed by the Testing Strategy —
  `.claude/knowledge/testing-strategy.md`; the Test Architect enforces it.
- **Instrumentation:** code emits structured, trace-correlated telemetry in the OpenTelemetry
  data model, with stable error codes and RFC 9457 error responses —
  `.claude/knowledge/observability-and-instrumentation.md`; the SRE enforces it.
- **Docs Explorer:** every knowledge/content artifact carries its graph metadata in YAML
  frontmatter (id, type, owner, typed links, review-by); the derived index `docs/docs-index.js`
  is regenerated from it and browsable at `docs/index.html` (hierarchy · graph · mind map ·
  health). Skills write frontmatter + sync the index as their last action; material changes flag
  inbound neighbors review-suggested; sub-ADR decisions become linked decision notes in
  docs/notes/; grounding traverses the graph; all graph mechanics run through the script bundle
  docs/ai-forward-pack/scripts/docs-graph.py — never ad-hoc scripts (V2/V10/V13–V18).
- **Audit & change log:** the project keeps a durable, committed history so work compounds across
  sessions — every meaningful prompt/skill/script in `docs/audit/audit-log.jsonl` (the Audit
  Mandate: every skill appends an entry as its last action) and every design decision in
  `docs/audit/change-log.jsonl` (collectknowledge/define-architecture/design/migrate capture the
  prompt, result, and git before/after). Browse the searchable timeline at `docs/audit/index.html`
  or via `/auditlog` (last-N, search, recall-and-redo a prompt, full-history↔changes toggle); all
  writes go through `docs/ai-forward-pack/scripts/audit-log.py`; the standard is
  `.claude/knowledge/audit-and-change-log.md`. A new session reads it to learn what was done and why.
- **Foundation:** the Body of Knowledge (directives, anti-patterns), Rules of the Road (tiers,
  gates, the loop), Persona Catalog, LOA, and Engineering Governance live in `.claude/knowledge/`
  — the constitution all of the above rests on.
<!-- AI-FORWARD-PACK:END -->
