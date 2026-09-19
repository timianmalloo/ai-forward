---
id: spec-agent-coordination-doctrine
title: "Spec — the doctrine home: pack/knowledge/agent-coordination.md as the always-loaded Owner / Coordinator / Sub-Agent doctrine under a 3,000-token ceiling"
type: spec
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, doctrine, knowledge-doc, always-on, context-budget, p0, ctx-q, co-lines]
links:
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: spec-agent-coordination, rel: relates-to }
  - { to: note-20260919-coordination-decisions-ratified, rel: relates-to }
  - { to: kb-multi-agent-coordination, rel: relates-to }
  - { to: spec-compile-stage, rel: relates-to }
  - { to: spec-leader-designation, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Specifies P0 of the coordination proposal: pack/knowledge/agent-coordination.md becomes the
  always-loaded doctrine for the Owner / Coordinator / Sub-Agent model — one CO<n> line per §3.3
  invariant naming its measurement or spike, the §4 protocol objects by name, the kick ladder, the
  vocabulary, the three shared stages and the struck list with reopen triggers — while keeping the
  seeded CO-S0 and CO-L sections byte-for-byte and the whole document under 3,000 estimated tokens
  as context-budget.py counts them. Stage detail beyond the ceiling lives in the knowledge base
  and is cited by id.
---

# Spec: the doctrine home (`pack/knowledge/agent-coordination.md`, `load: always`)

- **Status:** Draft
- **Tier (cost-of-error):** **T2** — the document is attached to *every* request of every session that uses the pack (Tier A of the context budget), so a wrong rule is executed by every agent and a bloated one is paid on every call (class PACK-R). The rules it carries govern who may rule, who may merge and who may spawn; a misstatement of the leader fence or the consent rule reaches the human as a wrong action, not a wrong sentence.
- **Author(s) / date:** Python Developer (Peer Mode, Track P0 of `coordination-p0-p1`) with Product Strategist, Domain Researcher and Data & Persistence Architect enacted inline, 2026-09-19. Adversaries at the gate, **enacted inline (fan-out 0 by the track contract)**: The Simplifier (soft veto), Test Architect (hard veto), Data & Persistence Architect (model veto). Inline enactment is recorded, not hidden — each veto condition below is a falsifiable criterion proven by a named test at `/implement`; the author did not clear a veto silently.
- **Supersedes / related:** refines `docs/proposals/owner-coordinator-subagent-coordination.md` §3 (the model), §4 and §4b (protocol objects, message layer, kick ladder), §5 (playbooks), §6 (struck list), §7 row **P0**, §7b.2 (the three shared stages), §8 (CTX-Q), D1–D15. Describes — never contradicts — the landed contracts `spec-leader-designation` (CO-L), `spec-message-layer`, `spec-board`, `spec-compile-stage` (CO-S0). Sibling of `spec-agent-coordination` (the `coord` layer's own spec: leases, ledger, join). The fixed contract is `docs/coordination/coordination-p0-p1.md` "Fixed contracts → P0".

> **Grounding trace (V15):** `spec-agent-coordination-doctrine` → `refines` → `proposal-owner-coordinator-subagent-coordination` (§3.1 seats table + vocabulary rule; §3.2 two relationships; §3.3 twelve numbered invariants each ending in a citation `(SPK-1..3)`, `(KB finding 3)`, `(p47; SCH-8)` …; §4 eight protocol objects; §4b store/doorbell/board + the kick ladder paragraph; §5.1–5.3 playbooks; §6 ten struck rows each with a *measured trigger that would reopen it*; §7b.2 CO-S0/CO-S1/CO-S2; §8 CTX-Q) → `relates-to` → `note-20260919-coordination-decisions-ratified` (D9 revised, D12–D15 added; "skills cite three shared stages written once in the doctrine doc") → `relates-to` → `spec-compile-stage` / `spec-leader-designation` (the two landed sections the doc already carries verbatim) → `relates-to` → `kb-multi-agent-coordination` (`data-and-constants.md` holds SPK-1..3 and the hook-surface table; `glossary.md` the terms). Read in the tree: the seeded doc (`load: skill`, `skills: [...]`, CO-S0 + CO-L, 6,529 bytes ≈ 1,352 est. tokens); `session-worktree-discipline.md` (a `load: always` sibling: frontmatter is the single line `load: always`; WT12 is the last directive, §4 the checklist, §5 references); `context-budget.py` (`est_tokens(os.path.getsize(path))` at 4.83 chars/token — **bytes, not characters**; `always_on()` filters on `load == "always"` only, so a `skills:` key on an always-on doc is inert); `docs/lessons/defect-classes.md` §CTX-Q (registered `uncontrolled`, control "proposed, not yet built (P0)"). **Citations already in the tree that this spec must not orphan:** `code-hygiene`, `forensicreview`, `investigate` SKILL.md cite **CO-S2** ("the stop is a message"); `execute-with-coordination` and `session-worktree-discipline.md` WT-§3 cite **CO-L**; `specify`/`implement` cite **CO-S0**. CO-S2 is cited today and defined nowhere — a dangling citation this spec closes (US-7). **Conflict surfaced, not overridden:** the proposal's P0 row also lists `.gitignore`/`pack-doctor`/`--host` hygiene items; the plan `coordination-p0-p1` scopes P0 to the doctrine doc only (those items landed with D10 in `902a252` or belong to P3). This spec takes the plan's scope.

---

## Part A — Functional specification
*Owner: Product Strategist (enacted inline).*

### Problem
The coordination model exists as a 71 KB proposal, four landed specs and two decision notes. No agent reads those on the normal path. The rules that must hold *on every request* — who may rule, that a message is never consent, that leadership is fenced at the join, that a parent enters its worktree before its first spawn — are therefore recalled, paraphrased or missed. The measured consequence is class **CTX-Q** (four researchers stranded by a parent's late `EnterWorktree`, two spikes silently not run) and, in ai-de, a 28 % unresolved-request rate and an 8,143 s stall. The pack's own rule for this shape is CI6: a lesson recorded as prose in a proposal is a memoir; it counts once it is a file that is always loaded — under a budget, because an always-loaded file is a per-request tax (PACK-R).

### Target users & personas
- **Primary — the Coordinator seat** (any harness, Peer Mode) at the moment of dispatch and at the join: needs the five-part contract, the cap rule, the fence, the kick ladder and the "worktree before spawn" rule *in context*, not in a file it must remember to open.
- **The Sub-Agent seat** at grounding under a brief: needs to know what it may and must not do (re-plan, spawn, relay a denial, treat a message as consent) without reading the proposal.
- **A skill author** (P8's readers, `verify-skill-contracts.py`): needs CO-S0 / CO-S1 / CO-S2 defined once so a skill cites a stage instead of copying it (D15).
- **The human operator**: needs the vocabulary (Owner is a seat, the person is the operator, ai-de's conductor keeps its name) and the struck list with reopen triggers, so "why is there no election?" has a one-line answer.
- **The context budget** (a non-human reader): `context-budget.py gate` must see one acknowledged ratchet change from the Coordinator, never silent growth.

### Core scenario
A Coordinator session on Claude Code is about to dispatch two writers. Its always-on prefix already carries the doctrine. It reads CO-lines for the seats, the contract and the worktree rule, runs `coord worktree new` for itself before the first `Agent` call, dispatches under a contract that names a termination condition and `--main-budget`, reviews through a decision request → ruling rather than accepting a hand-back, reads `coord leader who` before the join, and — when a sub-agent's report says "the Owner said yes" — treats that as data. None of this required opening the proposal. When it needs the *why* (the FLP argument, the ai-de baselines, the hook-surface table) the doc names the KB id to open.

### In scope / Out of scope (explicit non-goals)
- **In:** the content, structure, frontmatter and size contract of `pack/knowledge/agent-coordination.md`; a one-paragraph pointer after WT12 in `session-worktree-discipline.md`; the test that pins the contract; the CTX-Q class text (returned to the Coordinator, who owns the register); the measured always-on delta (reported, not acknowledged).
- **Out (non-goals):** typed seam requests (P1); any script or hook (`coord dispatch` refusing on a `pending` tree is P0's *named* control for CTX-Q but is built with `execute-with-coordination`, not here); the register row insertion, INSTALL/README counts, the managed block, `pack/context-budget.json` (Coordinator-owned); restating CO-S0 or CO-L (verbatim by contract); copying any stage into a skill (D15 forbids it); the proposal's P0 hygiene items already landed with D10.

### Conceptual domain model (DM1/DM4 — settled before the reading surface)
- **Bounded context:** *pack doctrine* — the always-loaded normative layer of the pack (`agent-body-of-knowledge`, `session-worktree-discipline`, …). Ubiquitous language: **doctrine doc** (one always-loaded knowledge file), **section** (an H2 whose heading carries its id), **directive** (one normative line, identified by a `CO` id), **CO line** (a directive that names the measurement or spike it traces to), **seeded section** (a section landed by an earlier track and frozen byte-for-byte), **ceiling** (an absolute limit in estimated tokens as `context-budget.py` counts them), **ratchet** (the always-on baseline the Coordinator acknowledges), **citation** (a `kb-*` or spec id, never inlined text).
- **Entities:** the **Doctrine doc** (identity: its path; the aggregate root); a **Directive** (identity: its `CO` id — `CO1`…`COn` for invariants and model rules, `CO-S0`/`CO-S1`/`CO-S2` for the shared stages, `CO-L` for leadership; an id is never reused or renumbered, so a citation from a skill stays valid — append-only identity, the same history rule WT and CT ids follow).
- **Value objects:** a **section** (heading + body; equality by text — which is exactly what the verbatim test compares), a **citation**, a **reopen trigger** (one line: the measured condition that would reopen a struck item), a **scenario pointer** (one sentence naming the proposal's playbook).
- **Aggregate and its invariant:** the Doctrine doc is one aggregate whose invariant is **completeness under the ceiling**: *every* §3.3 invariant of the proposal has exactly one CO line, *every* seeded section is unchanged, and the whole is ≤ 3,000 estimated tokens. The three parts are one invariant because satisfying any two by breaking the third is the failure mode this spec exists to prevent (restate an invariant → break the ceiling; trim the ceiling → drop an invariant or edit a seeded section).
- **Derive, don't store:** the token count is derived by the same function the gate uses (`est_tokens`), never written into the doc; the CO ↔ §3.3 mapping is derived by parsing the proposal's bold lead phrases, never a hand-kept table.

### User stories & acceptance criteria (testable — Gherkin)
Each maps to a test in `tests/docs_explorer/test_agent_coordination_doctrine.py`, red-first.

- **US-1 Always loaded.** *Given* the doc's frontmatter, *then* it is `load: always` and carries no `skills:` key (inert on an always-on doc; its presence would misdescribe the load scope to a reader). **Error path:** a doc with `load: skill` fails the test; a doc with both keys fails.
- **US-2 The ceiling.** *Given* the file on disk, *when* `context-budget.py`'s `est_tokens(os.path.getsize(path))` is applied (imported by path, not reimplemented), *then* the result is ≤ 3,000. **Error path:** the test prints the number on failure so the fix is a measurement, not a guess.
- **US-3 Seeded sections verbatim.** *Given* `git show origin/main:pack/knowledge/agent-coordination.md` (subprocess, `encoding="utf-8"`), *when* the `## CO-S0` and `## CO-L` sections (heading to next H2) are extracted from base and tree, *then* they are byte-identical. **Error path:** one changed character in either section fails with a unified diff.
- **US-4 Every invariant has a CO line.** *Given* the proposal's §3.3 (lines between `### 3.3` and the next `## `), *when* each numbered bullet's bold lead phrase is parsed, *then* every phrase appears verbatim in the doc on a line that begins with a `CO<n>` id, and that line names a measurement or spike (a parenthesised citation such as `SPK-2`, `KB finding 1`, `p47`, `MAST`, `R4`, `CTX-M`). **Error path:** a missing phrase fails naming the phrase; a CO line with no citation fails naming the id.
- **US-5 The protocol objects by name.** *Then* the doc names each of: session card · delegation contract · seam request · decision request · ruling · leader designation · join state · mail · board.
- **US-6 The kick ladder and the vocabulary.** *Then* rungs 0–3 (notify → kick → escalate to the Owner with a decision request → human) and the cap (two kicks per work item) are present; *and* the three vocabulary terms **Owner seat · human operator · conductor** are present.
- **US-7 The three shared stages.** *Then* `## CO-S1` and `## CO-S2` exist beside the verbatim `## CO-S0` (D15; `code-hygiene`, `forensicreview`, `investigate` cite CO-S2 today — a citation to an undefined stage is the dangling-reference defect `check-consistency` exists to catch).
- **US-8 The struck list.** *Given* the proposal's §6 table, *then* every struck item is listed in one line each, and each line carries its reopen trigger (the test checks a trigger phrase per row: `time-to-ack`, `second machine`, `leader-loss`, `false-kick`, `never automatic`, `WT4 exception`, `cannot be built on files`, `CRDT`/`none`, `third party`, `MCP`/`deprecated`).
- **US-9 The scenarios.** *Then* S1, S2 and S3 each get one sentence pointing at the proposal's playbook (§5.2, §5.1, §5.3), no more — the playbooks are stage detail and stay in the proposal.
- **US-10 Stage detail is cited, never inlined.** *Then* the doc cites `kb-multi-agent-coordination` ids for the *why* (spikes, baselines, hook surfaces) and contains no table copied from §4b or §5.
- **US-11 The worktree pointer.** *Given* `session-worktree-discipline.md`, *then* exactly one new paragraph follows WT12 and precedes `## 4.`, mentions **CTX-Q** and **CO-L**, and restates neither (it contains no `EnterWorktree` mechanics beyond the pointer and no epoch rule).
- **US-12 Measured, reported, not acknowledged.** *When* `context-budget.py gate` runs in the track's tree, *then* it reports the growth against the recorded baseline; the track reports the number and does **not** run `--update-baseline` (Coordinator-owned; one acknowledged ratchet change at the join).

### Non-functional requirements (ISO/IEC 25010)
- **Functional suitability:** completeness under the ceiling (the aggregate invariant) — measured by US-2/3/4.
- **Performance efficiency:** ≤ 3,000 est. tokens per request; the delta to the always-on total is reported (expected ≈ +1,600 over the seeded 1,352, i.e. the doc's whole count moves from Tier C to Tier A).
- **Compatibility:** the doc is a plain Markdown file with a one-line frontmatter, deployed by `sync-pack.ps1` to `.github/instructions/*.instructions.md` and `.claude/knowledge/*.md` unchanged in body — no new syntax the wrapper does not already handle (PACK-T).
- **Usability:** every directive is findable by id; a reader cites `CO<n>`, never a page.
- **Reliability:** the verbatim test guards the two landed contracts against drift on every CI run.
- **Maintainability:** append-only ids; a new invariant is a new `CO<n>`, never a renumbering; growth beyond the ceiling forces a citation, not a raise (the ceiling is absolute by contract, unlike the ratchet).
- **Portability:** the test reads with `encoding="utf-8"`, uses `pathlib` relative to the repo root, and carries no machine path (the three lints: `verify-no-machine-paths`, `verify-subprocess-utf8`, `verify-portable-text-io`).
- **Security:** none new — the doc is data; the consent rule (invariant 9) is carried, not weakened.

### Boundary set
Empty proposal §3.3 (the parser finds zero bullets → the test **fails**, never passes vacuously — PACK-P); a CO line whose citation is empty parentheses; the base text unreadable (`git show` non-zero → test error naming the ref, never a silent pass); the doc exactly at 3,000 tokens (pass) and at 3,001 (fail); a seeded section moved but unchanged (pass — position is not identity); a seeded section with a trailing-whitespace change (fail); CRLF line endings in the tree (the extraction normalises `\r\n` → `\n` on both sides before comparing, so a checkout setting cannot fake a drift).

### Comparables & evidence (sourced)
- **Verified** — the pack's own always-on siblings (`session-worktree-discipline.md`: single-line frontmatter, numbered directives, checklist, references) set the shape; `context-budget.py` counts bytes / 4.83 (`est_tokens`, line 64 `CHARS_PER_TOKEN`).
- **Verified** — the current always-on total is 47,642 est. tokens against a baseline of 47,642 with 2 % tolerance (48,594) and a 60,000 backstop (`context-budget.py gate`, run 2026-09-19 in the track tree). A +1,600-token doc exceeds the tolerance → the gate will report unacknowledged growth, which is the designed signal for the Coordinator's acknowledgement.
- **Verified** — CTX-Q instance: `docs/lessons/defect-classes.md` §CTX-Q (2026-09-18, session `2eb8c619`, six sub-agents, two spikes not run).
- **Verified** — CO-S2 is cited by three skills and defined nowhere (grep over `pack/commands/*/SKILL.md`, 2026-09-19).
- **Inferred** — Claude Code's own `CLAUDE.md` guidance and Copilot's `applyTo: "**"` instructions are the industry shape for "always-loaded doctrine"; both are known to bloat without a budget (PACK-R's FR-072: 184 K-token prefix). The ceiling-plus-citation pattern is this pack's answer, not an external standard.
- **Flagged** — whether 3,000 tokens is *enough* for every reader's need is a hypothesis; the reopen trigger is a `/session-profiler` finding that agents open the proposal on the normal path after P0 lands.

### Applicable governance lenses
Quality attributes (walked above) · release/rollback (a knowledge doc; rollback is `git revert`; the ratchet change is the only coupled edit and is the Coordinator's) · observability (`context-budget.py report` is the emitting source; the test prints the count) · threat model / privacy / accessibility — **N/A**: no runtime surface, no data, no UI.

---

## Part B — UX specification (the *reading surface*)
*Owner: UX Researcher / IA (enacted inline). The doc has no interface; its user-facing surface is the reading experience of an agent whose prefix carries it.*

- **Who reads it, when:** every agent, on every request, implicitly (Tier A); *actively* at four moments — dispatch (Coordinator), grounding under a brief (Sub-Agent), a hard stop or veto (any skill citing CO-S2), and the join (Coordinator). A human reads it when `coord board` shows a term they do not know.
- **What it must let them do in ≤ 3,000 tokens:** (1) name the seat they are in and its *must not* list; (2) dispatch or accept a contract that has all five parts and a termination condition; (3) act on a message correctly (data, never consent; ack pinned to a blob); (4) run the join fence; (5) climb the kick ladder without inventing a rung; (6) answer "why not X?" for each struck item with its reopen trigger; (7) find the *why* by id in the KB.
- **Information architecture (section order = lookup order):** preamble (what this doc is; what is elsewhere) → vocabulary → seats and the floor → the two control relationships → the invariants (CO lines, numbered in §3.3 order so the proposal's `1.`–`12.` and the doc's ids co-locate) → protocol objects → kick ladder → **CO-S0** (verbatim) → CO-S1 → CO-S2 → **CO-L** (verbatim) → the three scenarios → the struck list → references (KB ids, the sibling docs). Directive ids are the labels; headings are short.
- **User flows:** *lookup by id* (a skill says "CO-S2" → the reader finds the H2 by id — happy path); *lookup by concept* ("may a sub-agent spawn?" → the seats table → one row — alternate); *the answer is not here* (the reader hits a citation → opens the KB or the spec by id — recovery; the doc never says "see the proposal" without a section number); *error* — the reader is a sub-agent whose brief contradicts a CO line: CO-S1 tells it to `nack` a contract outside the mandate, not to re-plan.
- **UX acceptance criteria:** every citation is an id resolvable in `docs/docs-index.js` (US-10); every struck row answers its own "why not" in one line (US-8); no directive requires reading another document to be *applied* (only to be *justified*).

## Part C — UI specification
**N/A — the artifact is a Markdown knowledge document with no visual surface; it is rendered by the harness as prefix text.**

---

## Gate record (Stage 4 — adversaries enacted inline, bottom-up)
| Lens | Finding | Resolution |
|---|---|---|
| **Simplifier** (soft) | *"Do you need CO-S1 and CO-S2 at all? The brief said CO1–COn."* | Kept, narrowly: three skills already cite CO-S2 and D15 says the stages are written once *here*; omitting them leaves dangling citations that `check-consistency` would flag at the join. Each stage is ≤ 4 sentences. **Struck** from this spec: any restatement of the §4b doorbell table, the §5 harness tables and the §7 build plan — all cited by id. |
| **Simplifier** (soft) | *"A test that parses the proposal couples the doc to prose formatting."* | Accepted as designed: the coupling is the point (CI6 — the control fails when the invariant list and the doctrine diverge). The parser keys on the proposal's stable `### 3.3` heading and the `N. **…**` bullet shape; a reformat of the proposal is a visible test failure, not a silent drift. |
| **Test Architect** (hard) | *"US-4 'names a measurement or spike' — what input fails it?"* | A CO line with the phrase but no parenthesised citation fails; the test asserts a `(` … `)` group on the line containing a token from the allowlist derived from the proposal's own citations. Empty §3.3 fails (PACK-P). |
| **Test Architect** (hard) | *"US-3 could pass on a doc that deleted both sections."* | The extractor returns `None` for a missing heading and the test asserts both sections exist in the tree *and* match — absence is a failure, not an equality of `None`. |
| **Data & Persistence Architect** | *"Is the CO id really an identity if the invariants are numbered in §3.3 order and §3.3 might be reordered?"* | Yes: the id is assigned once at landing and is append-only; the *co-location* with §3.3 order is a convenience today, not a rule. A later reorder of the proposal does not renumber the doc (recorded in the design's history rule). |
| **Verdict** | **PASS-WITH-CONDITIONS** — the conditions are US-1…US-12 as named tests, red first. The author did not clear the Test Architect's veto; the tests are the clearance and are reviewed at `/implement` Stage 4. |

## Confidence ledger & residual risk
- **Verified:** the counting function, the current baseline and tolerance, the seeded sections' bytes, the dangling CO-S2 citations, the CTX-Q register text.
- **Inferred:** that 3,000 tokens holds all twelve invariants with citations plus the stages and the struck list (≈ 14,490 bytes; the seed is 6,529) — proven or refuted by US-2 at implement time; if refuted, the struck list moves to the KB and is cited (the spec's own recovery path), never the invariants.
- **Residual risk:** the doc states the join fence and the consent rule; nothing here *enforces* them (CO-L's exit 11 does, CTX-Q's dispatch refusal does not yet exist) — the doctrine is the always-loaded half of each control, and the register says so. `Flagged`: harness deployment of always-on docs on Codex/agy is read-on-grounding, not prefix-attached (`codex.md`), so "every request" is Claude Code and Copilot today.
