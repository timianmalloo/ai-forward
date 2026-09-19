---
id: design-skill-evolution
title: "Design: skill evolution — per-skill edits under the 2% budget, three lint rules red-first, the seam (b) insertions"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, skills, co-s0, lint, context-budget, owner-review, p8, design]
links:
  - { to: spec-skill-evolution, rel: implements }
  - { to: design-compile-readers, rel: refines }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
  - { to: coordination-p3-p5-p8, rel: relates-to }
  - { to: note-20260919-readers-seat-and-citation-placement, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Detailed design for spec-skill-evolution: the exact sentence each of the ten skills gains and
  where; which six take the reference/co-s0.md pointer; the three new verify-skill-contracts.py
  rules (compile missing, pointer without reference, dispatch without deadline) with their
  self-test fixtures and red-first counts; the seam (b) insertions and the compressions that make
  them fit execute-with-coordination's budget; the tests; the engine seams reported, not built.
---

# Design: skill evolution

- **Status:** Draft
- **Implements:** `spec-skill-evolution` (US-1..US-9)
- **Author / date:** Python Developer (Peer Mode) · adversaries inline (Test Architect hard, Simplifier soft, AI Systems Engineer) · fan-out 0 · 2026-09-19

## Responsibility
Skill text (28 `SKILL.md`, their `reference/co-s0.md`, three Copilot mirror sentences) and one lint with its test. Nothing else changes.

## Data model
None. The skill frontmatter key `runs_as` (closed set) and the citation tokens `CO-S0` / `CO-S2` are the only machine-read fields; both are already defined (`design-compile-readers`).

## Contracts

### C1 — The CO-S0 citation, by skill kind
| Kind | Skills | Form | Where |
|---|---|---|---|
| prose-input (14) | unchanged | the fixed sentence (inline or pointer) | landed by compile-readers |
| plan/prose consumers that dispatch or run a workflow | `apply-learnings`, `dream`, `session-profiler`, `addpacktorepo`, `updatepack`, `extendaibundle` | pointer: `CO-S0 applies first — the sentence is `reference/co-s0.md`.` + the fixed sentence in `reference/co-s0.md` (same file shape as `execute-with-coordination/reference/co-s0.md`) | first sentence of Grounding |
| turn/log utilities | `also`, `prompts`, `searchprompts`, `auditlog` | one sentence naming the skill's own touch-point with a compiled prompt, containing `CO-S0` | Grounding (`also`, `auditlog`) or the engine/quick-reference paragraph (`prompts`, `searchprompts` — they have no Grounding section) |

Rationale for the third row (Simplifier #2): a compiled prompt is *data these skills show or re-make*, not an input they consume, so the fixed sentence would be false in them; the doctrine token is what the lint reads.

### C2 — Lint rules 5–7 (`verify-skill-contracts.py`)
| # | Code | Fires when | Fix text |
|---|---|---|---|
| 5 | `compile missing` | `CO-S0` absent from the SKILL.md body | cite CO-S0 in SKILL.md — inline in Grounding, or the one-line pointer to `reference/co-s0.md` |
| 6 | `pointer without reference` | the body names `reference/co-s0.md` and no reference text contains `CO-S0` | add `reference/co-s0.md` carrying the CO-S0 sentence beside SKILL.md |
| 7 | `dispatch without deadline` | the dispatcher detector matches, or a fan-out cap above zero is named, and the union lacks `deadline` or `fallback` (case-insensitive) | name a deadline and a fallback for every dispatch (CO8, CO9) |

Rules 1–4 unchanged. Codes stable (O7). Each new direction has a self-test fixture that must fail and the good skills must still pass; the "reference route" good case gains a pointer-with-reference fixture. Red-first counts expected on the tree before the skill edits: rule 5 → 10 skills; rule 6 → 0; rule 7 → 1 (`execute-with-coordination`: "deadline" absent, `pack/commands/execute-with-coordination/SKILL.md` measured `grep -c -i deadline` = 0). Observed counts are recorded in the exit evidence.

### C3 — Seam (b) insertions (verbatim from `docs/coordination/seam-p5-to-coordinator.md`)
1. `execute-with-coordination` Stage 5: the owner-review bullet appended as item 5 of the numbered list (the seam says "last bullet of that stage's list"; the list is numbered, so it is item 5).
2. `execute-with-coordination` Stage 6: the `verify-ruling-citations.py` sentence directly after the join code block, before "It fences first".
3. `prepare-for-coordination` Stage 7: the "who rules" sentence directly after the `dispatchable` sentence.

### C4 — Compressions in `execute-with-coordination` (to hold ≈1,230 chars of C3 in 406 chars of headroom)
Rule: a compression may shorten rationale; it may not drop a checklist item, a command, a class or defect id, a knowledge citation, or a MUST/never. Each is listed with what it keeps:
| Site | Before → after | Keeps |
|---|---|---|
| Stage 2 "Never install from inside a worktree" | the three-sentence rationale collapses to one sentence with the same claims | `coord install` refuses; shares `.git/config` *and* `.git/hooks`; overwrites the repository's registration; primary checkout once per clone; `coord doctor` confirms; `COORD-DRIVER-PATH-FOREIGN` |
| Stage 6 join paragraph | the measurement parentheticals shorten ("44.8% of a conductor's active main line and no entry recorded it" → "44.8% of a conductor's main line, unrecorded") ; "(a hand-resolved file carrying `<<<<<<<` sealed a merge once, DC-136; …)" → "(DC-136; …)" | every step, `recount_seconds`, T1 / fan-out 0, `coord regen` stays owed, `run-verify-gates.py`, `--continue`, `join.json`, E13, DC-142 |
| Intro | "A coordinator that starts writing code in track A stops watching track B, and the first evidence is a merge conflict in a file nobody agreed to share." → "A coordinator that authors track A stops watching track B; the first evidence is a merge conflict nobody agreed to." | the claim |
If the gate is still red after these, the residue is a coordinator seam (`context-budget.py skills --update-baseline`, one line in `pack/context-budget.json`), reported with the measured delta — never a fourth compression that thins an obligation.

### C5 — Per-skill edits (the ten, plus the three verified-not-holding rows)
| Skill | Edit (smallest) | Verb/surface verified |
|---|---|---|
| `also` | Grounding: "A compiled prompt in flight (CO-S0) is the goal state to inherit." Step 5: a raise **recompiles** — `/compile --from-audit <raw id>`; the addendum carries the compiled id and the `pending` row references it. Fix the duplicated "6." numbering | `compile/SKILL.md:28` (a recompile is a new entry naming the same raw id) |
| `apply-learnings` | pointer; broadcast step 4 offers each plan as `coord decide request --to <target human-seat session>` with the five fields, `--deadline default`, `--fallback` "the plan stays unapplied"; never automatic | `coord-decide.py request --help` |
| `auditlog` | Grounding: a `kind:compilation` entry is a prompt's CO-S0 twin (`/prompts --raw <id>`); viewer bullet gains **Messages** (the board) | `docs/audit/index.html:27-32`, `prompt-log.py:601` |
| `prompts` | Engine paragraph: a compiled prompt is its own row, labelled `⟲ compiled from <raw id>` (CO-S0); `list --raw <id>` shows one raw prompt beside its compilations; reuse copies either, search matches both | `prompt-log.py:112-122, 601, 607` |
| `searchprompts` | same fact in the list/interactive paragraph, one sentence | same |
| `dream` | pointer; Light step: mines the compile fields (`compiled: false` above T0, unanswered `DR-n`, gate refusals by code); PACK-O's presence signal carries the compiled prompt id | `dream.py:371-375` |
| `session-profiler` | pointer; "SP-01 … SP-16" → "SP-01 … SP-28"; `session-profile.py compile` (SP-27/SP-28, edit distance p50/p90, `compiled: false` share); message/doorbell/refused-dispatch counts `not recorded` until a reader exists; DoD SP-15 also against `coord session list` | `session-profile.py:1554-1575` |
| `addpacktorepo` | pointer; step 13 names `.agents/*` + `!.agents/artifacts.yml` + `!.agents/log/` (D10) + `.agents/mail/`; a verification bullet names the five hook adapters, the merged host entries, `pack-doctor`'s `doorbells` line, `coord log portable`; mirror step (13) twin edited | `pack-apply.py:79-83, 527-546`, `pack-doctor.py:351-421`, `coord log --help` |
| `updatepack` | pointer; Stage 3 step 1 and Stage 4 pack-doctor bullet gain the same names | same |
| `extendaibundle` | pointer; invariant "Both tools, always" → every harness surface plus a seat (`runs_as`, CO-S0; a dispatcher names the five-part contract with termination, deadline, fallback; `python3 pack/scripts/verify-skill-contracts.py` refuses otherwise); DoD line; mirror IMPLEMENT step twin | the lint |
| `prepare-for-coordination` | Stage 7 row gains *deadline · fallback · termination condition · target harness · doorbell status*; seam (b) sentence | §7b.3 group A row; `pack-doctor` doorbells |
| `optimize-graph` | the five-part contract sentence gains "a deadline and a fallback" | §7b.3 group A row |
| `execute-with-coordination` | C3 + C4 | — |

## Patterns
Progressive disclosure (CTX-E) for the pointer route; a lint as the control (CI6); the ratchet, not a ceiling (PACK-R).

## Error model
The lint prints one refusal per line in the pack grammar, exit 1; exit 2 with no skills root; exit 0 clean. A reference directory that is unreadable is an `OSError` surfaced as-is (the CLI is the only filesystem touch).

## Change-surface list (E7)
`pack/commands/<10>/SKILL.md` · six new `reference/co-s0.md` · `pack/commands/{execute-with-coordination,prepare-for-coordination,optimize-graph}/SKILL.md` · `pack/adapters/copilot/prompts/{addpacktorepo,extendaibundle,apply-learnings}.prompt.md` (twin sentences) · `pack/scripts/verify-skill-contracts.py` · `tests/docs_explorer/test_verify_skill_contracts.py` · this spec/design · one decision note · `docs/docs-index.js` (derived). Generated surfaces (`.claude/`, `.github/`, `docs/ai-forward-pack/`) are the coordinator's sync.

## Failure-mode analysis
| Failure | Signal | Control |
|---|---|---|
| a skill edit pushes past baseline × 1.02 | `context-budget.py skills --gate` FAIL | run before commit; pointer route or C4 |
| a compression drops a pinned sentence | `test_coord_worktree_config.py`, `test_pack_apply.py`, `test_ctx_controls.py` | run the docs_explorer suite |
| the fixed sentence appears twice in a pointer skill | `test_skill_co_s0_citation.py` (exactly once) | new pointer skills are outside its list; the new test counts once across the union for the six |
| a documented command gains a chain or backslash | `verify-documented-commands.py --root .` | run before commit |

## Telemetry
The lint's refusal counts are the measurement; red-first counts recorded in the exit evidence; `audit-log.py` entries carry duration via the start markers.

## Test plan
`tests/docs_explorer/test_verify_skill_contracts.py` (new): self-test exit 0; each new code fires on its fixture; good pointer-with-reference passes; the tree is clean; every skill cites CO-S0; the six pointer skills carry the fixed sentence exactly once across SKILL.md ∪ reference and the pointer line in SKILL.md; the three seam (b) sentences are byte-present; `prepare-for-coordination` names the five track-row fields; no machine path in new files. Red-first observed before the lint and skills are edited.

## Engine seams (reported, not built — exact requirements)
1. `pack-apply.py:527`: the hooks tuple `("reread-guard.py", "session-start.py", "mail-doorbell.py", "README.md")` must include `"heartbeat.py"` and `"owner-review-gate.py"`; the Claude hook JSON it merges (`claude-code.settings.hooks.json`) already names both, so today a fresh install points `PostToolUse`/`Stop` at files it never copied. Add `os.makedirs(<target>/.agents/mail, exist_ok=True)` beside `_gitignore()` so the ignored inbox directory exists (the contract's "create `.agents/mail/`").
2. `tools/new-capability.py`: a scaffolded `SKILL.md` writes `runs_as: either` and the Grounding pointer line, plus `reference/co-s0.md` with the fixed sentence — otherwise every new skill is red on rules 1 and 5 until edited by hand.
3. `prompt-log.py`: already shows `⟲ compiled from <raw id>` and takes `--raw` on `list`/`search` (verified) — no seam. `pick`/`browse` inherit the rows; whether Enter on a compilation copies the compiled text was not executed here (Inferred from the shared row model).
4. `session-profile.py` / `dream.py`: the §7b.3 indicators not yet read (messages sent/read/acked, doorbell latency, board read-rate, contracts refused at dispatch; refused dispatches and boundary corrections as candidate classes) — the skills read them `not recorded`.
5. `pack/context-budget.json`: if the gate is red after C4, the delta for `execute-with-coordination` (and any other) as `--update-baseline` lines.

## Status & next action
| | |
|---|---|
| **Completed** | this design; the spec |
| **Remaining** | `/implement` (tests red → lint → skills → gates → commit) |
| **Best next action** | `/implement docs/design/skill-evolution.md` in this tree |

## Gate record
`GATE design · 2026-09-19 · Test Architect (hard) · Simplifier (soft) · AI Systems Engineer · Patterns Expert — inline, fan-out 0 · verdict: PASS-WITH-CONDITIONS`

| # | Finding (severity) | Resolution |
|---|---|---|
| 1 | Test Architect — "rule 7 keyed on the dispatcher detector alone would be green on `optimize-graph`, whose row also demands deadline/fallback" (Major) | accepted as a limit of the detector: `optimize-graph` names no fan-out number and no dispatch instruction; its row is applied as text and pinned by a test, not by the lint; recorded as residual |
| 2 | Simplifier — "three compressions in P2's skill to make room for P5's text is P8 editing two other tracks' prose" (Major, soft) | the plan assigns all 28 skills to P8 this run; C4's rule and table make each compression reviewable; the pinned-sentence tests run before and after |
| 3 | AI Systems Engineer — "'`--deadline default`' in `apply-learnings` asserts a CLI form" (Minor) | verified in `coord-decide.py request --help`: `--deadline SECONDS  seconds until terminal, or `default`` |
| 4 | Patterns Expert — "six more one-sentence reference files" (Minor) | the established CTX-E shape; the cheaper fix (raise six baselines) is the coordinator's and is named in the spec's risks |

Authors did not clear their own veto: #1 was raised by the Test Architect and resolved by the Python Developer's residual-risk entry, re-read by the Test Architect.

---
**Handoff:** → `/implement`.
