<!-- AI-FORWARD-PACK:BEGIN (managed block — keep this block intact when reconciling; replace it wholesale on pack updates) -->
## AI-Forward Pack + Agent Knowledge Pack

This repository uses the **Agent Knowledge Pack** and the **AI-Forward Pack**. Honor them on
every non-trivial task.

- **No guessing (the standing rule):** when you do not know, there are exactly **three** moves —
  **check it** (the default; open the file, run it, read the signature), **mark it** (an inline
  `assume:` carrying the belief, what would confirm it, and what breaks if it is false), or
  **ask** (only when consequential *and* unresolvable by you). Proceeding on an unmarked belief
  is not a fourth option. **An assumption that was not written down before the work is not an
  assumption — it is a guess**, so "I assumed X" is unavailable afterwards. Watch the tells —
  *should be · presumably · typically · I believe · it follows the pattern* — and any API,
  version, path, count or boundary behaviour asserted without opening it. **Verified means you
  observed it, never that it is likely**, and a citation, a tool output, a sub-agent's report or
  an `INFERRED` edge does not promote a claim. Ask of every load-bearing statement as you write
  it: *"if this is wrong, how would I find out, and when?"* — if the answer is "in production",
  check it now. `.github/instructions/no-guessing-protocol.instructions.md` (NG1–NG11).
- **Reasoning spine:** the Rigor Protocol — see `.github/instructions/rigor-protocol.instructions.md`.
  Map, interrogate, ground in evidence, disconfirm, then converge; label every claim with its
  confidence.
- **The standing method (unconditional):** the absence of the words *"use the Rigor Protocol"*,
  *"convene the personas"* or *"run /design first"* is **not permission to skip them** — an
  interactive prompt carries the same standard as a skill run; only the ceremony scales with the
  tier, never the rigor. Never decide in a silo: ground in the **whole intent, end to end**, name
  what the decision constrains, and write down the **surface list** a change must reach before you
  start (store → model → service → projection/wire → client type → UI → compute reader). Prove the
  **rendered surface** and the **consistency across surfaces**, not just the units; a gate's green
  result is evidence the gate passed, not that its contents passed; an exit code is not a result —
  read the state; and never assert the shape of *our own* code from memory — open the file or label
  the claim Inferred. `.github/instructions/end-to-end-integrity.instructions.md` (E1–E18).
- **The data model is the highest-priority decision.** Before any surface, endpoint or table:
  model the domain in **DDD** terms (bounded context, ubiquitous language, entities vs value
  objects, **aggregates bounded by an invariant**, small, referenced by identity). Then choose the
  **durable representation** — by default core entities as **dimensions** and change-over-time as
  **append-only facts**, so history and the audit trail *are* the data rather than a shadow schema,
  and new measures are new rows/columns rather than rewrites. **Declare the grain before the
  columns** ("one row is exactly one ______"), classify every measure additive / semi-additive /
  non-additive, decide the **history rule per attribute** (Type-2 whenever a change would rewrite
  the meaning of a past record), **derive don't store** (two definitions of one quantity is a defect
  signature), and snowflake only when the domain demands the entity. Migrate expand-migrate-contract;
  a backfill never guesses. `.github/instructions/domain-and-data-modelling.instructions.md`
  (DM1–DM18); evidence in `docs/knowledge/domain-and-data-modelling/`; the **Data & Persistence
  Architect** holds the veto.
- **Continuous improvement (a primary directive):** every bug you create, every mistaken
  assumption, and every correction you receive is captured — as a **class, not an instance** — in
  `docs/lessons/defect-classes.md`, and converted into a **control** that fails when the shape
  recurs. Run **class → sweep → derive → prevent** in writing on every defect fix; a fix that stops
  at the instance is not finished. **A lesson recorded as prose is a memoir** — it only counts once
  it is a test, a gate, a lint rule, or a file that is always loaded. Read the register at
  grounding. `.github/instructions/continuous-improvement.instructions.md` (CI1–CI12).
- **Smallest correct (build discipline):** climb the **Solution-Selection Ladder** before writing —
  YAGNI → reuse-in-codebase → stdlib → native → installed dep → one line → minimum — never cutting
  validation, security, accessibility, or the failure-mode/test floors; mark bounded shortcuts with an
  inline `simplify:` comment (ceiling + upgrade trigger); ceremony scales with the tier (T0 code-first,
  T1/T2 full artifacts). `.github/instructions/solution-selection-ladder.instructions.md`; the
  Simplifier is its adversarial mirror.
- **Personas (dual-mode):** author in Peer Mode, review in Adversary Mode; the author never
  clears its own hard veto. Agents in `.github/agents/`; the operating standard in the
  `persona-audit` / `persona-cards` instructions.
- **Workflows (19):** the prompts in `.github/prompts/` — sixteen reasoning workflows
  (`collectknowledge`, `adddomainexperts`, `specify`, `define-architecture`, `design`, `ui-design`,
  `visualize`, `implement`, `investigate`, `document`, `adopt`, `forensicreview`, `migrate`,
  `updatepack`, `addpacktorepo`, `extendaibundle`),
  the `auditlog` lens over the audit & change log, plus two prompt-log utilities, `prompts` and
  `searchprompts`. Templates: `docs/ai-forward-pack/templates/`.
- **Prompt reuse (utility):** `/prompts` opens the audit log's prompts as an arrow-navigable stack
  (newest on top; → expand, ← collapse, Enter reuse) and `/searchprompts` searches them; reuse
  copies the chosen prompt to the clipboard to paste-and-edit. Engine:
  `docs/ai-forward-pack/scripts/prompt-log.py` (stdlib) — a **reuse lens over the *same* committed
  audit log** (`docs/audit/audit-log.jsonl`), not a second store. When the user gives a
  **substantive** request, log it with `prompt-log.py add "<text>"` (it writes a `kind:prompt`
  audit entry via `audit-log.py`) so it is recallable (no CLI hook auto-captures prompts; stop when asked).
- **Unfamiliar APIs/SDKs/MCP servers:** run the Spike Protocol before depending on a contract.
- **Specification:** `/specify` produces **one spec with three layers** — Functional (what &
  why), UX (how it works: IA, user flows, structure), UI (how it looks) — written bottom-up,
  UX before UI, each absent layer marked N/A — `.github/instructions/specification-standards.instructions.md`; the
  UX Researcher/IA holds the UX-specification veto, UX & Accessibility the UI veto.
- **UI:** whenever the work has a user-facing interface (any medium), the **UI & Interaction
  Design Standard** governs excellence — token systems, complete component states (incl.
  empty/loading/error), HAX + Shape-of-AI patterns for AI UIs, WCAG 2.2 AA, performance budget —
  `.github/instructions/ui-interaction-design.instructions.md` (U1–U20); the UX & Accessibility
  lens holds the veto.
- **UI archetype:** for a user-facing UI, select the **archetype** (routing/temporal/data) as a
  determinism control before generating — `.github/instructions/ui-archetype-grammar.instructions.md` (G1–G16) + the
  archetype catalog; record the Archetype Signature in the spec, build to its facet rules, and
  verify it against the *shape of the task* even on an existing screen (reading is parallel;
  entering is serial).
- **UI craft (`ui-design`):** to create, review or elevate a surface, run the `ui-design` prompt —
  direction in words before pixels, the design system before the screens, a **self-contained
  dependency-free mockup** that renders the hard states with a **review harness** (persona ·
  viewport · state · theme · reduced motion), and a **rubric critique** (location · dimension ·
  severity · evidence · fix · confidence) run structure-before-surface, ending in a ranked plan.
  Measure before you diagnose, and self-check against the generic-AI-look tells.
  `.github/instructions/ui-design-craft.instructions.md` (DX1–DX25).
- **UI craft detection (the control):** the craft floor is not only prose — the **deterministic,
  LLM-free 59-rule detector** (`ui-craft-gate.py`, wrapping Impeccable) reads your `DESIGN.md`
  natively and enforces *outward* against the built source what `design-lint.py` only checks
  inward: every off-token colour, font, size and radius, plus the mechanized generic-AI-look
  tells, hierarchy, motion, copy and overflow rules. Run it at `ui-design` Stage 3 (it **is**
  the measurement), fold its findings into the rubric with the accessibility and token severity
  floors, and gate CI on it — **a lesson recorded as prose is a memoir** (CI6). A clean run is a
  **floor, never a verdict**: it cannot see archetype fit, IA, whether the hard states exist at
  all, or whether the copy is true.
  `.github/instructions/ui-craft-detection.instructions.md` (CD1–CD20).
- **Generated visual assets:** imagery, personas and motion a UI *contains* may be generated;
  the **interface itself may not** (image models render illegible text and invented controls).
  Direction in words first, then optionally a **visual world** that makes the brief concrete —
  mood **never** structure, supplementing **never** replacing real named references. Generate
  once, **download, optimize and commit** (provider results expire and a re-rolling asset is
  non-determinism in a deterministic artifact); every asset carries a manifest entry with its
  verbatim prompt, preset, cost, **alt text** and disclosure; never upload a real person's
  likeness or customer data.
  `.github/instructions/ui-visual-assets.instructions.md` (VA1–VA22).
- **Where to start on any UI job:** `docs/ui-guide.html` (also listed under **Knowledge
  surfaces** in the Docs Explorer) is the how-to layer over all of the above — the layer stack,
  a job-to-path picker, the `ui-design` stages, the command sheet, an archetype picker, the veto
  table, the tells, and where artifacts land. It is **derived** from the standards and never
  authoritative over them.
- **Running the pack's scripts:** commands are written `python3 <script>` (the POSIX name, and
  the shebang on every script). **On Windows that fails — use `python` or `py -3`**: python.org
  ships no `python3.exe`, and the `python3` present there is a Microsoft Store alias that is not
  Python (it prints *"Python was not found"* and exits `9009`). This is a substitution, not a
  missing install. `pack-doctor.py`'s `python interpreter` check names the working form for the
  current machine.
- **Testing:** the Testing Strategy governs what to test and what counts as proof —
  `.github/instructions/testing-strategy.instructions.md`; the Test Architect enforces it.
- **Instrumentation:** structured, trace-correlated telemetry in the OpenTelemetry data model,
  stable error codes, RFC 9457 error responses —
  `.github/instructions/observability-and-instrumentation.instructions.md`; the SRE enforces it.
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
  or via the `auditlog` prompt (last-N, search, recall-and-redo, full-history↔changes toggle); all
  writes go through `docs/ai-forward-pack/scripts/audit-log.py`; the standard is
  `.github/instructions/audit-and-change-log.instructions.md`. A new session reads it to learn what was done and why.
- **Obsidian lens (optional):** `docs/` is already a valid Obsidian vault — the same V2
  frontmatter drives Properties, Dataview and the graph view. Stand it up with
  `docs/ai-forward-pack/scripts/obsidian-setup.py` (`--check` · `--install-app` · `--init` ·
  `--analyze`): it commits the vault **config** (colour groups keyed to artifact `type`) and
  git-ignores the per-user **state** and plugin code. Obsidian stays a **reader** — frontmatter
  is the record, `docs-graph.py` the only writer, and no query is load-bearing in a canonical
  artifact (queries live only in `docs/lenses/`). `--analyze` computes hubs, exact betweenness
  bridges, components, orphans and structural gaps **dependency-free**, so the insight is never
  locked behind a plugin. `.github/instructions/obsidian-lens.instructions.md` (OB1–OB14).
- **Code knowledge graph (optional, composes with the above):** **Graphify** (graphify.com,
  Apache 2.0, PyPI `graphifyy`) builds an **on-device** graph of the *code* — symbols, calls,
  imports, schemas — that an assistant queries instead of grepping, answering with `file:line`
  citations. It is the natural partner to the docs graph: **docs hold intent, code holds
  reality, and the expensive defects live in the gap.** Every edge is tagged `EXTRACTED` /
  `INFERRED` / `AMBIGUOUS`, which maps onto this pack's **Verified / Inferred / Flagged** — so a
  cited traversal is how you satisfy *"never assert the shape of our own code from memory"*
  cheaply, while remembering that **a citation is not a promotion**. Stand it up with
  `docs/ai-forward-pack/scripts/graphify-setup.py` (`--install` · `--init` · `--build` ·
  `--join`); `--init` writes a **repo-kind-aware** `.graphifyignore` (in a consuming repo
  `.claude/` and `docs/ai-forward-pack/` are the *only* copy and are kept). `--join` writes the
  code↔docs lens: documentation with no implementation, and risk with no governance.
  `.github/instructions/code-knowledge-graph.instructions.md` (GK1–GK16).
- **Foundation:** the Body of Knowledge, Rules of the Road, Persona Catalog, LOA, and Engineering
  Governance are in `.github/instructions/` (always applied) — the constitution all of this rests on.
<!-- AI-FORWARD-PACK:END -->
