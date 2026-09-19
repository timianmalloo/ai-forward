---
id: design-agent-coordination-doctrine
title: "Design — the doctrine doc's structure: sections as the aggregate, CO ids as identity, a byte budget per section, and the test that pins completeness under the ceiling"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, doctrine, knowledge-doc, always-on, context-budget, p0, ctx-q, co-lines]
links:
  - { to: spec-agent-coordination-doctrine, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: kb-multi-agent-coordination, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Detailed design for spec-agent-coordination-doctrine. The component is a Markdown document
  and its pinning test: a fixed section order with a byte budget per section that sums under the
  3,000-token ceiling as context-budget.py counts it, CO ids as append-only identity, the two
  seeded sections carried byte-for-byte, every proposal §3.3 invariant as one CO line with its
  citation, and one stdlib test module that derives every check from the sources (the proposal,
  origin/main, est_tokens) rather than from a hand-kept table. No script, no dependency.
---

# Design: the doctrine doc (`pack/knowledge/agent-coordination.md`) and its pinning test

- **Status:** Draft
- **Spec / architecture:** `docs/specs/agent-coordination-doctrine.md` (US-1…US-12, the aggregate invariant *completeness under the ceiling*, the boundary set) · proposal §3, §4, §4b, §5, §6, §7b.2, §8 · the fixed contract in `docs/coordination/coordination-p0-p1.md` "Fixed contracts → P0".
- **Delivery phase / vertical slice:** coordination **P0**, built after the P2/P4/P6/P8 joins (base `902a252`). Real around it: the seeded CO-S0 and CO-L sections, `context-budget.py`, the KB `kb-multi-agent-coordination*`, the three skills citing CO-S2. **Absent until the join (Coordinator-owned):** the managed-block citation, the `always_on_tokens` baseline change, the CTX-Q register row, `sync-pack` deployment to `.claude/knowledge/` and `.github/instructions/`. **Mock-substitutable seam:** none needed — the test reads real files; the only external it touches is `git show origin/main:<path>`, which exists in every clone that can run CI.
- **Author(s) / date:** Python Developer (Peer Mode, Track P0) with Patterns Expert, Simplifier and Domain Researcher enacted inline, 2026-09-19. Gate adversaries enacted inline (fan-out 0): Patterns Expert ⇄ Simplifier, Test Architect (hard veto), SRE (telemetry).

> **Grounding trace (V15):** `design-agent-coordination-doctrine` → `implements` → `spec-agent-coordination-doctrine` (US-1…US-12; the aggregate invariant) → `refines` → `proposal-owner-coordinator-subagent-coordination` (§3.3 bullet shape `N. **lead phrase** … (citation)`, verified by reading lines 244–268; §6 table columns *Struck · Why · Measured trigger*; §7b.2 stage table) → `relates-to` → `kb-multi-agent-coordination` (ids: `-data`, `-glossary`, `-sota`, `-comparables`, `-references`, `-sources`, `-open-questions` — read from each file's `id:`). Internal contracts read: `test_context_budget.py` (imports the script by `importlib.util.spec_from_file_location`; `ROOT = parents of __file__`), `test_coord_leader.py` (`subprocess.run(..., encoding="utf-8")`, `REPO = Path(__file__).resolve().parents[2]`), `conftest.py` (session-scoped git-env normalisation — the test may shell to git). No conflict with the spec found.

## Responsibility
One: carry the always-on half of every coordination control in ≤ 3,000 estimated tokens, so an agent applies the rule from its prefix and opens a cited artifact only for the *why*. The test's one responsibility: fail whenever the doc stops satisfying *completeness under the ceiling*.

## Data model (settled first — DM1–DM18)
- **Aggregate:** the **Doctrine doc**; root = the file; the one invariant = *completeness under the ceiling* (every §3.3 invariant has one CO line · both seeded sections unchanged · `est_tokens(bytes) ≤ 3,000`). Other aggregates are referenced by identity only: the proposal by its id and section numbers, specs by id, the KB by id, constants **never restated as numbers** (CO-L's rule — `LEADER_TTL` etc. are named, D13 is cited).
- **Entities:** the doc (path); a **Directive** identified by its **CO id**. **Value objects:** a section (heading + body, equality by bytes), a citation, a reopen trigger, a scenario pointer.
- **Grain:** one CO line is exactly one directive, identified by its id, recorded when it lands. One struck row is exactly one struck item with one trigger. **Additivity:** counts of CO lines and struck rows are additive; the token count is additive across sections (bytes sum) — which is what makes a per-section byte budget a valid planning instrument; "coverage of §3.3" is a ratio, non-additive.
- **History rule (Type-2 by identity):** a CO id is assigned once and never reused or renumbered — a superseded directive keeps its id with a one-word status (`struck`) rather than vanishing, so a citation in a skill or a register row never dangles. The two seeded ids (`CO-S0`, `CO-L`) are frozen by contract; `CO-S1`/`CO-S2` are landed here and become frozen to the next track the same way. Co-location of `CO1…CO12` with the proposal's §3.3 numbering is a convenience at landing, not a rule.
- **Derive, don't store:** the token count is derived by `est_tokens` at test time, never written into the doc; the invariant list is parsed from the proposal, never a table in the test; the struck-row trigger allowlist is the *only* stored derivation (a short tuple in the test), labelled as such with the reason (a trigger is prose; a regex over prose is the pragmatic floor — `simplify:` ceiling: if §6 gains a row, the tuple gains a phrase, and the test fails first because the row count is compared to the parsed table).
- **Migration:** frontmatter `load: skill` → `load: always`, `skills:` key removed (expand-migrate-contract is not applicable to a single file; the change is one commit and its rollback is `git revert`). Every downstream reader of the frontmatter is `context-budget.py scan()`, which reads only `load`, `applyTo`, `skills` — `skills` on an always-on doc is inert (verified: `always_on()` filters on `load` only).

## Section plan (the durable representation, with its byte budget)
The ceiling is **3,000 × 4.83 = 14,490 bytes** (`est_tokens` rounds; the test uses the function, this table is the plan). The seed is 6,529 bytes, of which the rewritable preamble is ≈ 700.

| # | Section (H2 or block) | Carries | Budget (bytes) |
|---|---|---|---|
| 0 | frontmatter + H1 + preamble | `load: always`; what this doc is; what lives elsewhere (KB by id, the specs by id) | 650 |
| 1 | Vocabulary | Owner seat · human operator · conductor (D11); Coordinator, Sub-Agent, leader, track, contract | 350 |
| 2 | **CO1** seats and the floor | the three seats, each with model floor · may · must not, in one line each; "seats, not processes"; reviewer ≠ author | 900 |
| 3 | **CO2** the two control relationships | spawned vs registered: who holds the process, push, liveness, join, termination variant | 550 |
| 4 | **CO3–CO14** invariants | one line per §3.3 bullet: bold lead phrase verbatim → one clause → citation in parentheses | 2,600 |
| 5 | **CO15** protocol objects | the nine names with their verb, one line each | 900 |
| 6 | **CO16** kick ladder | rungs 0–3, cap two, count them; reassignment only under a ruling | 350 |
| 7 | **CO-S0** (verbatim) | as seeded | 2,632 |
| 8 | **CO-S1** seat stage | `Runs as:`; Coordinator duties; Sub-Agent duties; the last action is `coord mail send --kind done` | 700 |
| 9 | **CO-S2** stop = message | the decision request + board post + inbox entry; halt on the request | 450 |
| 10 | **CO-L** (verbatim) | as seeded | 3,197 |
| 11 | Scenarios | S2, S1, S3 — one sentence each → proposal §5.1/§5.2/§5.3 playbook | 450 |
| 12 | Struck list | ten rows, `item — reopens when <trigger>` | 1,100 |
| 13 | References | KB ids, spec ids, sibling docs, CTX-Q | 300 |
| | **Total** | | **15,129 → over by ≈ 640** |

The plan overshoots by ~640 bytes, so the design fixes the **trim order** now rather than at the keyboard: (a) the struck list compresses to a two-column table (≈ −300); (b) the seats table drops the model-floor column to a trailing sentence (≈ −200); (c) the preamble drops to two sentences (≈ −150). **Never trimmed:** the CO lines' bold phrases and citations, the seeded sections, the frontmatter. If the doc is still over after (a)–(c), the struck list moves whole to `kb-multi-agent-coordination-open-questions` and is cited — the spec's recorded recovery path — and the test's struck-list check follows it there (a design decision recorded in a note, not a silent move).

## Contracts
- **Exposed:** the CO ids (`CO1`…`CO16`, `CO-S0`, `CO-S1`, `CO-S2`, `CO-L`) as citation targets for skills and the register; the frontmatter `load: always`; the section order above; the promise that constants appear by name only.
- **Consumed (each with source + confidence):** `context-budget.py::est_tokens` and `CHARS_PER_TOKEN` (`pack/scripts/context-budget.py:64`, **Verified** by reading) — imported by path in the test; `git show origin/main:pack/knowledge/agent-coordination.md` (**Verified**: the tree is at `902a252` = `origin/main`, md5 of both texts equal); the proposal's §3.3 bullet shape (**Verified**: twelve bullets, each `^\d+\. \*\*(.+?)\*\*`, each ending with a parenthesised citation); §6's three-column table (**Verified**); the KB ids (**Verified** by `grep ^id:`); the three skills' CO-S2 citations (**Verified**).

## Patterns
- **Progressive disclosure by citation** (the pack's CTX-E control, `reference/*.md` beside a SKILL.md): the always-on layer carries the rule; the *why* is one read away by id. Chosen over inlining (breaks the ceiling) and over a `load: skill` doc (the CTX-Q failure: nobody opened it).
- **Golden-master (characterization) test** for the seeded sections: compare against the committed base, not a copied fixture — the base *is* the oracle and cannot drift from itself (Testing Strategy D-characterisation; the same shape as `test_gate_parity`).
- **Derive-from-source test** (no hand-kept expectation list): the invariant phrases are parsed from the proposal at test time. Rejected: a fixture list of twelve strings — it would pass forever after the proposal changed (the memoir shape CI6 names).
- **Append-only identity** for CO ids (DM10 Type-2), the same convention WT/CT/E/GO ids follow in the sibling docs.
- Ladder: rung 3 (stdlib — `re`, `subprocess`, `pathlib`, `importlib.util`, `unittest`); no new dependency; the whole test is one module.

## Data shapes (the test's)
- `Section = str | None` — the text from an H2 line whose heading starts with the id, up to (not including) the next `\n## `; `None` when the heading is absent. Both sides normalised `\r\n → \n` before comparison.
- `Invariant = tuple[str, str]` — `(lead_phrase, citation)` parsed from §3.3; the region is the lines between `### 3.3` and the next `## `; a bullet is `^\s*\d+\.\s+\*\*(.+?)\*\*`; the citation is the last `(...)` group in the bullet's text.
- `StruckRow = tuple[str, str, str]` — the three cells of a §6 table row (header and separator skipped).
- Frontmatter: the block between the first two `---` lines; parsed as `key: value` lines (the same subset `context-budget.read_frontmatter` accepts — the test reuses that function by import rather than re-parsing).

## Error & concurrency model
A Markdown document has no runtime. The test's failures are its error model, each with a message that names the unit: missing phrase → the phrase; over the ceiling → the measured number and the ceiling; drifted seeded section → a unified diff; `git show` non-zero → the ref and stderr (a test **error**, never a pass); empty §3.3 → "parsed 0 invariants" (PACK-P). No concurrency: the test is read-only over the tree.

## Change-surface list (E7 — the document's surfaces)
| Surface | Writer | Reader | Owner |
|---|---|---|---|
| `pack/knowledge/agent-coordination.md` (source) | this track | `context-budget.py`, `sync-pack.ps1`, every skill citing CO-* | P0 |
| `pack/knowledge/session-worktree-discipline.md` (one paragraph after WT12) | this track | readers of WT; `check-consistency` | P0 |
| `tests/docs_explorer/test_agent_coordination_doctrine.py` | this track | pytest, CI | P0 |
| `.claude/knowledge/agent-coordination.md`, `.github/instructions/agent-coordination.instructions.md` (deployed copies) | `sync-pack.ps1` | the harnesses | Coordinator (join) |
| managed block in `AGENTS.md` (the always-on citation line) | Coordinator | every session's prefix | Coordinator |
| `pack/context-budget.json` `always_on_tokens` | `context-budget.py gate --update-baseline` | the gate | Coordinator (acknowledged) |
| `docs/lessons/defect-classes.md` §CTX-Q | Coordinator (text returned by P0) | `/dream`, `session-profile.py` | Coordinator |
| `docs/docs-index.js` | `docs-graph.py derive` | the Explorer | derived |
| `docs/security/threat-model.md`, `docs/security/privacy-review.md` (`documents` links to this design) | Coordinator (P0 must not edit `docs/security/*`) | rollup | Coordinator |

## Failure-mode analysis
| Mode | Disposition |
|---|---|
| Doc over the ceiling after a later edit | **Detect** — the test fails with the number; **mitigate** — the trim order above, then the KB move. The ratchet (`gate`) is a second, coarser detector on the always-on total. |
| A seeded section edited "just to fix a typo" | **Prevent** — the golden-master test against `origin/main`; a legitimate change to CO-S0/CO-L is that track's change with the test's base updated in the same commit (the test reads the ref, so a landed change becomes the new base automatically after merge — no fixture to update). |
| Proposal §3.3 reformatted (bullets → table) | **Detect** — the parser finds 0 → the test fails loudly (PACK-P), never passes vacuously. Accepted cost: one test edit when the proposal's shape changes. |
| A CO line paraphrases the invariant | **Detect** — verbatim bold-phrase match; paraphrase fails. Accepted: the phrases are the proposal's, so the doc reads slightly proposal-shaped in twelve lines. |
| `origin/main` absent (shallow clone, detached CI without the remote) | **Detect** — subprocess non-zero → test error naming the ref; **mitigate** — the test falls back to `main` then errors; it never skips silently. |
| CRLF checkout on Windows | **Prevent** — both sides normalised before comparison; bytes on disk still count toward the ceiling (`est_tokens(getsize)`), so a CRLF checkout of a 14,400-byte doc could read ≈ +260 bytes — **accepted** with the headroom the trim order leaves (target ≤ 14,200 bytes on LF), recorded here as the reason for the margin. |
| `skills:` left in the frontmatter | **Detect** — US-1's test. |
| CO-S2 defined here but P8's `verify-skill-contracts.py` expects a different heading shape | **Detect** at the join — the lint runs in CI; **mitigate** — the heading is `## CO-S2 — …`, the same shape as the seeded `## CO-S0 — …` that the lint already passes against. |
| The struck list moves to the KB (recovery path) and the test still looks in the doc | **Prevent** — the test's struck-list check reads a target path recorded in one constant; the move updates the constant and the decision note in the same commit. |

## Adversarial analysis (STRIDE-lite)
| Boundary | Threat | Disposition |
|---|---|---|
| Knowledge doc → every model prefix | **Tampering / injection**: a repo write that turns a doctrine line into an instruction to the model (the doc *is* instruction text by design) | **Transfer** — repo write access is the trust boundary (branch protection on `main`, `required_conversation_resolution`); the doc carries no external content and cites by id, so no untrusted text is inlined. **Accept** the residual: the pack's own text is trusted by construction (ADR-0011's untrusted-heading rule applies to *messages*, not to committed doctrine). |
| Test → `git show origin/main` | **Spoofing** of the base (a local `origin/main` ref pointing elsewhere) | **Accept** — a local repo owner can already edit the doc; the test guards drift, not malice. In CI the ref is the protected branch. |
| Test → proposal text | **Denial** — an oversized or pathological proposal making the regex slow | **Accept** — the region is bounded to §3.3 (≈ 30 lines) before any regex runs. |

## Privacy analysis (LINDDUN-lite)
The component touches no personal data: the doc is normative text; the test reads repo files and a git ref. Session ids appear only in the audit entries this track writes, under the audit log's existing rules.

## UI & interaction design
N/A — no interface (spec Part C).

## Telemetry
- **Emitting sources on the normal path:** `context-budget.py report` (per-doc and always-on totals, ESTIMATES labelled) and `gate` (delta vs baseline, exit code) — the same numbers the Coordinator acknowledges; the test prints the measured token count in its failure message and as an `INFO`-style assertion message so a CI log carries the number even on pass (`self.assertLessEqual(tokens, 3000, f"measured {tokens}")`).
- **Operator questions:** *how big is the doc* → `report --verbose`; *did the always-on set grow and was it acknowledged* → `gate` and the `context-budget.json` diff; *is CTX-Q recurring* → `session-profile.py` grep for the guard's refusal text (recorded in the class row); *duration of this track* → the three `audit-log.py` entries with `duration_seconds` from the `start` markers.
- **Degradation:** a missing baseline prints `not recorded` (existing behaviour of `gate`), never a plausible number.

## Test plan (Testing Strategy — triggered directives, the union)
- **D0 hygiene** on every test: deterministic (reads committed files and a fixed ref), one focal behaviour each, meaningful assertion, seen red first.
- **Characterisation / golden-master** (seeded sections vs `origin/main`).
- **Contract test at a boundary** (D5): the frontmatter contract (`load: always`, no `skills:`); the ceiling via the *real* counter imported by path (a reimplementation would be a second definition — DM7).
- **Derived-expectation tests**: §3.3 → CO lines (with the PACK-P non-empty guard); §6 → struck rows with triggers.
- **Presence tests**: protocol object names; kick ladder rungs and cap; vocabulary; CO-S1/CO-S2 headings; S1/S2/S3 sentences; KB citation ids resolvable in `docs/docs-index.js`.
- **Neighbour test**: `session-worktree-discipline.md` has exactly one new paragraph between WT12 and `## 4.` mentioning CTX-Q and CO-L and containing neither `update-ref` nor `EnterWorktree`-mechanics beyond the pointer.
- **Red-first order:** all tests written and run before the doc is edited — expected red: US-1, US-2 passes (the seed is small — recorded as *not a red*, its oracle is the 3,001 boundary which is exercised by a temp copy), US-3 passes on the unedited seed (its red is demonstrated by a temp-copy mutation of one byte), US-4…US-11 red.
- **Existing suites that must stay green:** `test_context_budget.py` (the doc gains `load: always`; `test_skill_scoped_docs_name_the_skills_that_load_them` no longer applies to it), `test_check_consistency.py`, `test_skill_contracts`-family (CO-S2 now resolves).

## Conformance notes
- Style: the sibling always-on docs' shape — RFC 2119 keywords, numbered directive ids in bold, a references section; **no tables copied from the proposal** (US-10).
- Python: stdlib only, `pathlib`, `encoding="utf-8"` on every open and subprocess, no machine paths (the three lints), `unittest.TestCase` like the neighbouring modules, pytest-collected.
- `simplify:` markers: the struck-trigger allowlist tuple (ceiling: a §6 row count change; trigger: the row-count assertion fails first).

## Flagged risks & residual unknowns
- **Flagged:** the byte plan overshoots by ≈ 640 before trimming; the trim order is fixed above and US-2 decides. If the KB move fires, the struck list's reader changes (the note records it).
- **Flagged:** whether the harnesses that read always-on docs *on grounding* (Codex, agy) rather than as a prefix still make CTX-Q's rule "always present" — they read the doc at session start, which precedes the first spawn; recorded as **Inferred** in the doc's residual-risk line.
- **Inferred:** `verify-skill-contracts.py` accepts the CO-S2 heading shape used here (same as CO-S0's) — confirmed at the join by CI, not by this track (the lint's source is P8's; P0 reads it only if the lint fails).

## Status & next action
| | |
|---|---|
| **Completed** | the data model (doc as aggregate, CO ids as identity), the section plan with a byte budget and a trim order, the contracts, the test plan, the E7 surface list with owners |
| **Remaining** | `/implement`: the test module red → the doc → the WT pointer → green; the decision note; the CTX-Q text and the measured delta for the Coordinator |
| **Best next action** | `/implement` this design in the P0 tree, red-first |

## Gate record (adversaries enacted inline, fan-out 0)
| Lens | Finding | Resolution |
|---|---|---|
| **Patterns Expert ⇄ Simplifier** | Simplifier: *"a byte-budget table is planning theatre — just write it and measure."* Patterns Expert: *"then the trim happens at the keyboard and drops whatever is nearest."* | Kept the table **and** the trim order — the order is the design decision (what is never trimmed); the table is the estimate that makes the order needed. Net: 14 rows of prose, no mechanism. |
| **Simplifier** | *"Sixteen CO ids for one doc?"* | Accepted as designed: fourteen are the proposal's own list (12 invariants + seats + relationships); ids are what skills cite. Struck: separate ids for the vocabulary, the scenarios and the struck list — they are sections, not directives. |
| **Test Architect** (hard) | *"US-3 on the unedited seed is green at first run — that is not red-first."* | Recorded honestly in the test plan: the verbatim test's oracle is demonstrated by a one-byte mutation of a temp copy inside the test (`test_a_one_byte_change_to_a_seeded_section_is_detected`), so the detector is seen firing; the doc-level test is then a regression guard. |
| **Test Architect** (hard) | *"The allowlist tuple for struck triggers is a hand-kept expectation."* | Conceded and bounded: the row **count** is derived from the proposal's §6 table and compared first, so a new row fails before the tuple can hide it; the tuple carries a `simplify:` marker naming that ceiling. |
| **SRE** | *"Where is the number emitted on the normal path?"* | `context-budget.py report`/`gate` already emit it; the test's assertion message carries the measured count; the track's report prints it. No new emitter needed. |
| **Verdict** | **PASS-WITH-CONDITIONS** — conditions are the red-first order and the one-byte mutation test; the author did not clear the Test Architect's veto, the tests are the clearance. |
