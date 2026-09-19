---
id: note-20260919-readers-seat-and-citation-placement
title: "The seat key is runs_as, the CO-S0 sentence moves to reference/ where the 2% budget cannot hold it, and a dispatch instruction is a heading, a verb or a sentence-initial spawn"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, compile, readers, skills, runs-as, co-s0, context-budget, p8]
links:
  - { to: design-compile-readers, rel: relates-to }
  - { to: spec-compile-readers, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Three decisions taken while building P8, below ADR weight: the seat is declared as the YAML
  key `runs_as` (the proposal wrote `Runs as:`); seven prose-input skills carry the CO-S0
  sentence in reference/co-s0.md behind a one-line pointer because their recorded baseline + 2%
  cannot hold 54 tokens; and the lint's dispatch-order rule reads an instruction to dispatch, not
  prose about spawning. The implement Proof Pack is recorded here because docs/proofs/ is not a
  P8-owned path.
---

# Readers, seats and citation placement (P8, 2026-09-19)

## Decision 1 — `runs_as:` is the frontmatter key
The proposal (§7b.2) and the coordination plan write the seat as `Runs as:`. The P8 contract fixes `runs_as:` — a bare YAML key with a bare-word value, so `check-consistency.py check_frontmatter_yaml` cannot trip on it and a Copilot/Codex adapter can read it as data. Values: `Coordinator` · `Sub-Agent` · `either`. **Assumption marked:** `assume:` P2 writes the same key on its two skills (belief: the plan's row 76 names the P8 lint as the control, so P2 conforms to the lint's key; confirm: the join's lint run; breaks: two spellings in one tree, the lint refuses P2's two skills on `seat missing` until one is renamed).

## Decision 2 — the CO-S0 sentence by pointer where the budget cannot hold it
Every SKILL.md sits exactly at its recorded baseline (`pack/context-budget.json`, 2026-09-14), so the per-skill headroom is 2% and the fixed sentence is ~54 tokens. Measured after the inline pass: seven skills over (`forensicreview`, `collectknowledge`, `ui-design`, `design-slice`, `implement`, `migrate`, `adopt`); `define-architecture` fit by one token. The contract's fallback applies: the sentence lives in `reference/co-s0.md` and the Grounding paragraph opens *"CO-S0 applies first — the sentence is `reference/co-s0.md`."* The test counts the sentence exactly once across `SKILL.md ∪ reference/*.md` and requires `CO-S0` exactly once in SKILL.md in either route. **Reported to the Coordinator:** raising those seven baselines by ~60 tokens each lets one edit move the sentence inline (the always-injected surface would then carry the whole rule, not its pointer).

## Decision 3 — a dispatch *instruction*, not prose about spawning
The first cut of rule 4 (`(?i)\bspawn`) refused `prepare-for-coordination` on its intro sentence *"which spawns one sub-agent per track"* — a description of another skill, before its Stage 0 where CO-S0 is cited. The detector was narrowed to a Dispatch heading or bold stage label, the `coord dispatch` verb, or a sentence-initial `spawn`; the self-test carries both shapes. The residual (a false refusal on an unusual phrasing) errs toward requiring the citation earlier, never toward silence.

## Observed, not estimated
- Red-first on base `2b3a815`: **34 refusals across 28 skills** — 28 × `seat missing` (the plan estimated 25; no skill carried any seat key), 4 × `hard stop without message`, 2 × `dispatch before compile`. Tests: 35 failed / 3 passed before the code existed.
- After: `verify-skill-contracts.py` refuses only P2's two skills (`seat missing` on both; `dispatch before compile` on `execute-with-coordination`, which cites CO-S0 nowhere yet).
- The Copilot prompt mirrors carry no Grounding/Stage-0 text for the prose-input skills (only `dream` and `optimize-graph` mirrors carry a one-line "Stage 0"), so no mirror was edited.

## Proof Pack (implement, T2 — recorded here because `docs/proofs/` is not P8-owned)
| Claim | Evidence | Source | Oracle (why it can fail) | Red-observed | Confidence | Residual |
|---|---|---|---|---|---|---|
| Per-template edit-distance median/p90 and per-session `compiled: false` share are read from the log | `test_measurements_from_fixture_log` (0.18 median; 0.33 share) | `session-profile.py compile_measurements` | wrong denominator, wrong join on `compiled_from` | yes (35 red) | Verified | window filter relies on `parse_ts` (None → in window) |
| Empty/missing log → `not recorded`, no finding | `test_empty_log_reads_not_recorded`, `test_missing_log_reads_not_recorded` | same | a `0` where absence should read | yes | Verified | — |
| Pre-P7 entries are `unrecorded`, not gaps | `test_unrecorded_not_in_denominator` | same | absence read as `false` | yes | Verified | — |
| SP-27 Inferred, skips T0; SP-28 Verified, strictly > 0.2, names samples | `test_sp27_fires_inferred_and_skips_t0`, `test_sp28_fires_verified_above_0_2_not_at_0_2`, `test_sp28_evidence_names_samples` | `compile_findings` | threshold `>=`, tier filter dropped | yes | Verified | 0.2 is Flagged |
| Catalog ids unchanged; F-26/F-27 added | `test_catalogs_gain_sp27_sp28_f26_f27_without_renumbering` + existing suites (112 → 118 green) | `FINDINGS`/`FIXES` | renumbering | yes | Verified | — |
| Compare table gains `compiled` / `edit dist p50`, pooled not median-of-medians; old call shape works | `test_compare_rows_carry_compiled_and_edit_dist` | `family_comparison(sessions, compile=None)` | median of medians; signature break | yes | Verified | — |
| Rendered surface: section present, `not recorded` when empty; `compile` subcommand through `main()` | `test_render_has_compile_section`, `test_compile_subcommand_prints_the_rendered_section` | `render_compile_section`, `cmd_compile` | section missing / a number in an empty cell | yes | Verified | E11: the `profile` verb's full path exercised by the exit-evidence run |
| No prompt text in evidence | `test_evidence_carries_no_prompt_text` | both readers | a note copying `prompt` | yes | Verified | — |
| Dream proposes presence gaps, unanswered DRs (newest compilation decides), refusals; nothing without the fields | the five `DreamCompileMinerTests` | `dream.py` section 7 | later answer ignored; proposal on a plain corpus | yes (3 negative tests were green by construction) | Verified | — |
| Lint: every direction fails, good skills pass, exit 0/1/2, grammar | `--self-test` exit 0; the nine `LintTests` | `verify-skill-contracts.py` | a direction that cannot fail (DC-104) | yes | Verified | regexes over prose (accepted) |
| Every owned skill declares a seat; prose-input skills carry the sentence exactly once; hard stops cite CO-S2; optimize-graph carries the dispatchable stop once | `test_skill_co_s0_citation.py` (7 tests) | `pack/commands/*/SKILL.md` | duplicate sentence; missing seat | yes | Verified | P2's two skills |
| Budget held | `context-budget.py skills --gate` exit 0, `clean - no unacknowledged skill growth` | gate output | any skill > baseline × 1.02 | yes (7 GREW before the pointer route) | Verified | seven baselines to raise |
