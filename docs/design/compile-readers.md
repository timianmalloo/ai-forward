---
id: design-compile-readers
title: "Design — compile readers (session-profile.py compile measurements · dream.py CO-S0 miner · verify-skill-contracts.py · runs_as and the shared-stage citations)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, compile, readers, session-profiler, dream, lint, skills, runs-as, co-s0, p8]
links:
  - { to: spec-compile-readers, rel: implements }
  - { to: design-compile-stage, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: audit-log, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  Detailed design for spec-compile-readers: one pure reader over the audit log inside
  session-profile.py (per-session and per-template-version compile measurements, SP-27/SP-28,
  F-26/F-27, two compare-table columns), one deterministic miner beside PACK-O in dream.py, a new
  stdlib lint verify-skill-contracts.py with four rules and a self-test, and the smallest edit to
  each SKILL.md: a runs_as frontmatter line, the fixed CO-S0 sentence, the CO-S2 one-liner and
  optimize-graph's dispatchable stop — all under the per-skill 2% budget.
---

# Design: compile readers

- **Status:** Draft
- **Spec / architecture:** `docs/specs/compile-readers.md` (US-1…US-9, boundary set) · `docs/architecture-agent-coordination.md` (the layer) · `design-compile-stage` (the writer side: entry shapes, refusal codes) · proposal §7b.2–7b.5, D15
- **Delivery phase / vertical slice:** coordination **P8**, reading what P7 writes. Real around it: the audit log with its compile fields (P7 landed), the profiler and dream, `context-budget.py skills --gate`, the three portability lints. **Mocked / absent:** P2's `runs_as: Coordinator` and the dispatchable-stop sentence on the two coordination skills (the lint reads them and reports); the doctrine's CO-S1/CO-S2 sections (P0 — cited by id only); the gate-runner registration of the lint (Coordinator). Mock-substitutable seams: the **audit log path** (the readers take a root; tests write a temp log) and the **skills root** (`--root`; the self-test writes its own fixtures).
- **Author(s) / date:** Python Developer (lead) + Patterns Expert + The Simplifier + Data & Persistence Architect (peers, inline — fan-out 0), 2026-09-19. Adversaries inline: Test Architect (hard veto), SRE, Patterns Expert ⇄ Simplifier, Security (advisory — no trust boundary beyond files the repo commits).

> **Grounding trace (V15):** `design-compile-readers` → `implements` → `spec-compile-readers` → `refines` → `spec-compile-stage` (US-6: *compiler quality is measured by what the human changed*; US-8: *one stop criterion per consuming skill*) → `relates-to` → `design-compile-stage` (Telemetry: the fields; Data model: *workflow entries gain `compiled_from` + `edit_distance` (non-additive) or `compiled: false`*). Read for conventions, by opening the files: `session-profile.py` (`FIXES`/`FINDINGS` ordered catalogs; `detect()`'s `add()` shape; `family_comparison()` rows; `render_markdown()` tables; `_audit()` resolves the audit script under `docs/ai-forward-pack/scripts` then `pack/scripts`), `dream.py` (`load_corpus` reads the log with `read_jsonl`; the PACK-O miner is section 5 of `build_proposals`, keyed by `sig`; the score formula and the evidence-or-drop gate), `verify-portable-text-io.py` (module docstring as the class statement; stdio guard; `--root`; `--self-test` that writes fixtures to a temp dir and returns 1 on the first direction that does not fail; `EXIT 0 clean · 1 findings · 2 usage`), `context-budget.py cmd_skills` (`tokens > int(base * 1.02)` fails; `reference/*.md` is not counted), `tests/docs_explorer/test_dream_pack_o.py` and `test_session_profile.py` (module-load-by-path; `_profile_all(found, args)` with an `Args` shim; `render_markdown` on a dict). **No drift** between the spec and the writer's design; one **clarification** recorded: the spec's "hard-stop shape" regex is fixed here (Data shapes) so the lint and the test share one definition.

---

## Responsibility
Three read-only consumers of committed text, plus the smallest text edits that make the doctrine citable and lintable. (1) `session-profile.py` gains **one pure function** over `docs/audit/audit-log.jsonl` returning the compile measurements and their findings; rendering adds one section and two columns. (2) `dream.py` gains **one miner** (section 7 of `build_proposals`) that proposes and never scores above the formula. (3) `verify-skill-contracts.py` is a **new stdlib lint** over `pack/commands/*/SKILL.md` (+ `reference/*.md`) with four rules, a self-test and the refusal grammar. (4) Each owned SKILL.md gains a `runs_as:` line; the prose-input skills gain the CO-S0 sentence (inline or by pointer); the four hard-stop skills gain a CO-S2 one-liner; `optimize-graph` gains the dispatchable-stop sentence. **Not responsible for:** writing any audit entry itself (the profiler's existing `_audit` is unchanged), promoting a dream, editing P2's two skills, the baselines, gate registration, the audit viewer.

## Spec clarification (recorded, not drift)
The spec says the hard-stop detector matches "`**STOP` in capitals, `stop for human`, or `never merges`" — the exact regex is `(\*\*STOP\b|(?i:stop for human)|(?i:never merges))`, applied to SKILL.md text with the frontmatter stripped. Verified against the tree at grounding: it matches exactly `investigate`, `forensicreview`, `code-hygiene`, `apply-learnings` (design-slice/implement's lower-case *"stop and surface the drift"* and execute-with-coordination's *"stop and run"* do not match).

## Data model (settled first — DM1–DM6)
- **Aggregates (from the spec).** *Measurement* (root: one read of the log; invariant: every cell derives from ≥ 1 entry or reads `not recorded`). *Skill contract* (root: SKILL.md + `reference/*.md`; invariant: one seat from the closed set, and the citations its shape requires). *Dream proposal* (evidence-bearing or dropped).
- **Durable representation.** Nothing new is persisted by this design. The **facts** are the audit entries P7 already appends (append-only; grain *one row is exactly one gate-passing compilation* or *one skill run*). The readers compute **derivations** at run time — **derive, don't store** (DM7): the per-session and per-template rows are written into `profile.json` as a labelled snapshot of a derivation (`compile.source` names the log it was derived from), rebuildable by re-running the profiler on the same log; the equality test is `test_compile_measurements_rebuild_equal` (two reads of one log are equal).
- **Grain of each derived row.** *by_session*: one row is exactly one audit `session` value in the window. *by_template*: one row is exactly one `(harness, template_version)` pair, labelled `<harness> v<n>`, plus the row `unknown` for runs whose `compiled_from` is not in the log or window.
- **Additivity.** `compilations`, `substantive_recorded`, `compiled_false`, `unrecorded`, `refusals`, `retries`, `samples` — **additive** across sessions/templates. `compiled_false_share`, `decision_requests_per_compilation` — **non-additive** ratios (recomputed from the additive parts, never summed). `edit_distance_median/p90`, `engine_seconds_median` — **non-additive** (a median of medians is a category error; the compare-table column recomputes from the pooled samples of the group's sessions).
- **History rule.** N/A — nothing persisted beyond the profile snapshot, which is itself an append-only artifact (`docs/profiles/sp-NNNN/`, never rewritten).
- **Writer / compute reader per field (DM15).** `compiled`, `compiled_from`, `edit_distance` — writer `audit-log.py append` (P7); readers: this profiler, this miner. `compiled.provenance.*`, `decision_requests[]`, `template_version`, `harness`, `dispatchable`, `raw_id` — writer `prompt-compile.py finish` (P7); readers: the same. `runs_as` — writer: the skill author; reader: the lint (and, later, `coord`).

## Contracts

### Exposed
**`session-profile.py`** (additions; every existing verb, flag, id and shape unchanged)
- `compile_measurements(root, days) -> dict` — pure; reads `<root>/docs/audit/audit-log.jsonl` once. Returns `{"source": <path>|NOT_RECORDED, "window_days": days, "by_session": {sid: row}, "by_template": {label: row}, "runs": n, "compilations": n}`. Missing/empty log or no compile-bearing entries → `source: NOT_RECORDED`, empty maps.
- `compile_findings(measure) -> [finding]` — `SP-27` (Inferred; per session; only `compiled: false` runs whose `tier` ≠ `T0`) and `SP-28` (Verified; per template with `edit_distance_median > 0.20`, `samples` in the metric and the evidence). Finding dicts use `detect()`'s shape (`id · title · severity · confidence · session · harness="audit" · evidence · metric · fixes`).
- `FINDINGS` gains `SP-27` (Major, `["F-26"]`), `SP-28` (Major, `["F-27"]`); `FIXES` gains `F-26`, `F-27`. Existing ids untouched (`test_session_profile.py` asserts the catalogs).
- `family_comparison(sessions, compile=None)` — optional second argument; rows gain `compiled_pct` and `edit_dist_p50` (or `None`, rendered `not recorded`); the markdown table gains the two trailing columns `compiled` and `edit dist p50`. `_profile_all` passes the measurement; `cmd_profile` stores it under `profile["compile"]`; `render_markdown` renders `## Compile stage (audit log)` after the tuning view (two tables, or one line naming `not recorded`).

**`dream.py`** (addition)
- Section 7 of `build_proposals`, keyed `sig` ∈ {`CO-S0 compiled:false presence`, `CO-S0 unanswered decision requests`, `CO-S0 gate refusals`}; each `kind: "Control upgrade"`, `confidence: "v"`, `source: "deterministic"`, `control.loc: "knowledge/agent-coordination.md#CO-S0"`; scored by `score()` like PACK-O (`_has_control: True`, `_freq` = count). Evidence ≤ 8 per proposal; a note carries the entry id, shortname/`DR-n`/refusal code and a number — never prompt text.

**`verify-skill-contracts.py`** (new)
- `python3 verify-skill-contracts.py` — argument-free: `--root` defaults to the repo root found by walking up from the script (or cwd) to a directory holding `pack/commands` or `.claude/skills`; the first existing of those two is the skills root. `--root <repo>` overrides. `--self-test` writes fixtures to a temp dir and proves every direction fails (DC-104). Exit `0` clean · `1` refusals · `2` usage (no skills root).
- Refusal grammar on stdout, one per line: `<code>: <skill> — fix: <text>`; codes (stable, O7): `seat missing` · `seat invalid` · `fan-out without compile` · `fan-out without contract` · `hard stop without message` · `dispatch before compile` · `skills root missing` (exit 2).
- Rules per skill (`SKILL.md` required; a directory without one prints `skip: <dir> — no SKILL.md` and is not a refusal):
  1. **Seat.** Frontmatter (the first `---` fence) has a line `runs_as: <v>` with `v ∈ {Coordinator, Sub-Agent, either}`.
  2. **Fan-out.** If `SKILL.md ∪ reference/*.md` matches `fan-out cap(?: of|:|\s*(?:≤|<=|<))?\s*([1-9]\d*)` (case-insensitive) → the union must contain `CO-S0`, and both `five-part contract` and `termination`.
  3. **Hard stop.** If the body matches the hard-stop regex (above) → the union must contain `CO-S2`.
  4. **Dispatch order.** If SKILL.md body matches `(?m)^#+ .*\bDispatch\b|\*\*Stage \d+ — Dispatch|coord dispatch|(?:^|[.:;]\s+)[Ss]pawn\b` (an *instruction* to dispatch; the first cut `(?i)\bspawn` refused `prepare-for-coordination` on its intro sentence "which spawns one sub-agent per track" — prose, not an instruction — so the detector was narrowed at implement time) → SKILL.md's first `CO-S0` must occur before the first such match (absent = refusal).

**SKILL.md text (verbatim, fixed by the P8 contract)**
- Frontmatter line `runs_as: <seat>` immediately after `description:` (YAML-safe — no `: ` inside the value).
- The CO-S0 sentence: *Consume the compiled prompt when one is in hand (CO-S0, `knowledge/agent-coordination.md`; `/compile`): its goal state is the turn's goal state and its Not-in-scope is the interdiction — derive nothing from raw prose that a compiled prompt already fixed.* — first sentence of the Grounding paragraph (or Stage 0 where the skill has no Grounding paragraph) **or**, where the budget cannot hold it, in `reference/co-s0.md` with the SKILL.md Grounding paragraph opening *"CO-S0 applies first — the sentence is `reference/co-s0.md`."*
- The CO-S2 one-liner on the four hard stops, appended to the stop sentence: *(the stop is a message — CO-S2, `knowledge/agent-coordination.md`)*.
- The dispatchable-stop sentence on `optimize-graph` Stage 7 (plan emission): *Before dispatch, refuse a compiled prompt whose `dispatchable` is false or whose text still carries an unanswered `DR-n` line — stop with `decision request unanswered: DR-n` (CO-S0).*

### Consumed (each with source and confidence)
| Contract | Source | Confidence |
|---|---|---|
| Audit entry shapes: `kind: compilation` with `compiled.{harness, template_version, dispatchable, raw_id, decision_requests[{id, answer}], provenance{refusals[], retries, engine_seconds, compile_tokens}}` and `prompt` = rendered text (lines `- DR-n … · answer: unanswered`); `kind: skill` with `compiled: false` or `compiled_from` + `edit_distance` (float, 4 dp) | opened in `docs/audit/audit-log.jsonl` at grounding (4 entries); `design-compile-stage` Data shapes | Verified |
| `prompt-compile.py distance` semantics (0 = identical, 1 = nothing shared) | `design-compile-stage` Contracts › Exposed | Verified |
| `dream.read_jsonl` skips malformed lines; `load_corpus` windows by `datetime` | `dream.py` lines 52–66, 160–186 | Verified |
| `context-budget.py skills --gate`: fail iff `tokens > int(baseline * 1.02)`; tokens = chars / 4.83 of SKILL.md only | `context-budget.py` 689–716; `pack/context-budget.json` | Verified |
| `check-consistency.py check_frontmatter_yaml` refuses an unquoted `: ` in a frontmatter value | `tools/check-consistency.py` 431–456 | Verified |
| The stdio guard idiom and `newline="\n"` on writes (PLAT-A) | `verify-portable-text-io.py` | Verified |
| Skill directories in a consuming repo live at `.claude/skills/<name>/` | `CLAUDE.md` addendum; `INSTALL.md` (not opened — the addendum states it) | Inferred — the lint tries `pack/commands` first, which is Verified for this repo |

## Patterns (named, justified, ladder-climbed)
- **Pure reader over an append-only log** (the profiler's existing shape for harness stores; `dream.load_corpus`) — one pass, no state, testable on a temp file. Ladder: reuse-in-codebase (`read_jsonl` idiom re-implemented in the profiler because the two scripts do not import each other — a 10-line local, not a new module; `simplify:` ceiling: if a third reader appears, lift it into a shared `audit_read.py`).
- **Ordered catalogs with stable ids** (`FIXES`, `FINDINGS`) — extended, never renumbered.
- **Miner section keyed by `sig`** (PACK-O's shape) — the dream review and the tests select proposals by `sig` prefix.
- **Lint with self-test and refusal grammar** (`verify-portable-text-io.py`, `verify-compiled-prompt.py`) — the pack's established control shape; DC-104 (a gate that cannot fail is not a gate).
- **Progressive disclosure** (`reference/*.md`, class CTX-E) — the budget fallback for the sentence.
- Rejected: a YAML parser (stdlib has none; the frontmatter subset is `key: value` lines — a 6-line scanner, as `check-consistency.py` does); a shared "audit reader" module (rung 2 vs rung 6 — one function each is smaller than a module two scripts must locate at runtime); an AST-level parse of SKILL.md prose (regex over three fixed shapes is the smallest correct idiom; the self-test pins each).

## Data shapes
**Profiler rows** (`profile.json › compile`):
```
by_session[sid]  = {substantive_recorded: int, compiled_false: int, compiled_false_share: float|NOT_RECORDED,
                    unrecorded: int, compilations: int, edit_distances: [float]}
by_template[lbl] = {compilations: int, samples: int, samples_unrecorded: int,
                    edit_distance_median: float|NOT_RECORDED, edit_distance_p90: float|NOT_RECORDED,
                    decision_requests_per_compilation: float|NOT_RECORDED,
                    refusals: int, retries: int, engine_seconds_median: float|NOT_RECORDED}
```
`lbl = "{harness} v{template_version}"`; a run whose `compiled_from` resolves to no compilation → `unknown`. Percentiles via the existing `pct()`; medians via `statistics.median`.

**Seat per skill** (`runs_as`, with the reason the lint cannot check):
| Skill(s) | Seat | Why |
|---|---|---|
| specify · define-architecture · design-slice · implement · investigate · ui-design · collectknowledge · forensicreview · migrate · document · code-hygiene · adopt · visualize · adddomainexperts | `either` | Prose-input workflows (§7b.3 group B): run in the main line by a human, or dispatched as a Sub-Agent under a compiled contract |
| optimize-graph | `Coordinator` | Emits the dispatchable plan and the fan-out contracts; the seat that plans is the seat that dispatches (§7b.3 group A) |
| addpacktorepo · updatepack · extendaibundle | `Coordinator` | Pack lifecycle: write the installed surface, run sync/verify, offer to commit — main-line only (group D) |
| session-profiler · dream · apply-learnings | `Coordinator` | Cross-session measurement, consolidation and cross-repo planning that write `docs/profiles`, `docs/dreams` or a plan per repo; apply-learnings ends in a human stop (CO-S2) |
| compile · also · auditlog · prompts · searchprompts | `either` | Utilities a human may paste into any session, including a sub-session; none dispatches |
| execute-with-coordination · prepare-for-coordination | `Coordinator` (P2 writes it) | Reported by the lint here; not edited |

**Budget arithmetic** (4.83 chars/token; sentence 261 chars ≈ 54 tokens; `runs_as: either\n` ≈ 3 tokens): inline fits where headroom ≥ 58 — `specify` (72), `investigate` (73), `document` (70), `code-hygiene` (85), `visualize` (63), `adddomainexperts` (71). Pointer route (`reference/co-s0.md`) where it does not — `define-architecture` (57), `forensicreview` (53), `collectknowledge` (46), `ui-design` (45), `design-slice` (40), `implement` (40), `migrate` (39), `adopt` (32). **Measured at implement time** (`context-budget.py skills --gate` after the inline pass): seven skills grew past baseline × 1.02 — `forensicreview` (+71), `collectknowledge` (+56), `ui-design` (+56), `design-slice` (+57), `implement` (+56), `migrate` (+57), `adopt` (+57); `define-architecture` fit (2,905 vs an allowance of 2,905). Those seven took the pointer route (`reference/co-s0.md`); **each is reported to the Coordinator for a ~60-token baseline raise**, after which one edit moves the sentence inline.

## Error & concurrency model
Read-only over committed files; no concurrency. A malformed JSONL line is skipped and counted in `measure["skipped_lines"]`. A compilation whose `compiled` object lacks `provenance` counts 0 refusals / 0 retries and contributes no engine-seconds sample. The lint never writes outside its self-test temp dir. Exit codes as above; the profiler's exit codes are unchanged (the reader cannot raise past `cmd_profile` — it catches `OSError`/`ValueError` and degrades to `not recorded`, printing one stderr line naming the cause).

## Change-surface list (E7)
store (audit log — unchanged) → model (`compile_measurements` rows; dream proposals; lint refusals) → service (`_profile_all`, `build_proposals`, `main`) → projection/wire (`profile.json › compile`; `profile.md` section + two columns; dream `evidence`/`control`; lint stdout) → client type (n/a) → UI (Markdown tables; the dream HTML view reads the same proposal dict unchanged) → compute reader (dream section 6 reads `profile.json` findings — SP-27/SP-28 flow into it with no change). Skill surfaces: `pack/commands/<skill>/SKILL.md` (+ `reference/co-s0.md`) → the Claude/Copilot/Codex/Grok/agy installs via `tools/sync-pack.ps1` (**not run by P8** — the Coordinator syncs at the join) → `context-budget.py skills --gate`.

## Failure-mode analysis
| Failure mode | From which choice | Disposition | How it's addressed | Detection | Test |
|---|---|---|---|---|---|
| Log missing or empty | reading a file that may not exist in a consuming repo | degrade | `source: not recorded`, empty maps; no finding | the `source` cell | `test_empty_log_reads_not_recorded` |
| Malformed JSONL line | hand-merged log | mitigate | skipped, counted | `skipped_lines` in the profile | `test_malformed_line_skipped` |
| `edit_distance` null or non-numeric | P7's `not recorded` path | mitigate | excluded; `samples_unrecorded` | the column | `test_non_numeric_distance_excluded` |
| `compiled_from` not resolvable | window cut or foreign log | mitigate | template `unknown` | the `unknown` row | `test_unresolved_compiled_from_is_unknown_template` |
| One-sample median read as a trend | a median over n=1 | detect | `samples` in metric and evidence | SP-28 evidence | `test_sp28_evidence_names_samples` |
| SP-27 on a T0 turn | firing on every `compiled: false` | prevent | tier filter; label Inferred | — | `test_sp27_skips_t0` |
| Pre-P7 entries counted as gaps | absence read as `false` | prevent | `unrecorded` bucket | the column | `test_unrecorded_not_in_denominator` |
| A regex matches prose *about* a stop/spawn | rule 3/4 over prose | accept | errs toward requiring a citation; the self-test pins each shape; residual: a false refusal is a one-line fix, never silence | the refusal names the skill | self-test directions |
| Sentence duplicated (inline + reference) | the pointer route | detect | citation test counts across the skill | test | `test_sentence_exactly_once_per_skill` |
| A skill tips over baseline × 1.02 | adding lines | detect | `context-budget.py skills --gate` (existing) | gate exit 1 | `test_context_budget.py` (existing) + the exit-evidence run |
| Frontmatter value with `: ` | `runs_as` line | prevent | the value is a bare word | `check-consistency.py` | existing gate |
| Two compilations of one raw, later answered | DR mining | prevent | latest compilation per `raw_id` decides | — | `test_dr_answered_later_not_proposed` |

## Adversarial analysis (STRIDE-lite)
| Trust boundary | STRIDE threat | Disposition | Control / rationale | Negative test |
|---|---|---|---|---|
| Committed audit log → profile/dream text | I: prompt text (possibly a pasted secret) copied into a finding | mitigate | evidence carries ids, shortnames, codes and numbers only; dream notes pass the existing `scrub()` and a tainted note is excluded | `test_evidence_carries_no_prompt_text` (a fixture prompt containing `sk-…` never appears in evidence) |
| Committed SKILL.md → lint verdict | T: a skill cites `CO-S0` in a comment to pass | accept | the lint checks presence, not meaning; the citation test checks the fixed sentence for the prose-input set; residual: a bad-faith author — reviewed at the PR | `test_self_test_directions` |
| `--root` argument | D: a huge or non-repo path | accept | reads ≤ 28 small files under one directory; no recursion beyond `*/SKILL.md` and `*/reference/*.md` | n/a |

## Privacy analysis (LINDDUN-lite)
This component touches no personal data beyond what the audit log already commits (session ids and the git handle in the `owner` field): verified by listing every field the readers copy into output — entry ids, shortnames, `DR-n` ids, refusal codes, counts, ratios, template labels. No prompt text, no model names beyond what the log's `provenance.compiler_model` already holds (not copied). Retention: the profile snapshot follows `docs/profiles/`.

## UI & interaction design
CLI and Markdown only (medium: terminal + committed report). Copy is in the pack's voice: refusals `<code>: <skill> — fix: <text>`; `clean - N skill(s) checked`; profile cells `not recorded`. The two tables sit after the tuning view (spec Part B). No visual UI (U19 N/A beyond this paragraph).

## Telemetry
- The **profile is the instrument** (IO): `compile.source`, `runs`, `compilations`, `skipped_lines`, and every row cell; `not recorded` is the degraded value (IO8).
- The lint's refusal codes are stable (O7); a new code is a design change. Counts only, no free text in metric-like fields (O13).
- The profiler's own audit entry (`_audit`) is unchanged; the skill runs' closing entries carry `--tier T2 --fan-out 0 --main-budget` as today.

## Test plan (Testing Strategy triggers → directives)
Triggers: pure functions over data (D0 hygiene, D1 unit with exact oracles), a CLI gate (D3 contract: exit codes and the grammar; DC-104 self-test), file I/O (D4 boundary: missing/empty/malformed), a text-edit surface with a budget gate (A2 conformance: the existing `context-budget` test and the exit-evidence run), portability (the three lints; `newline="\n"`; stdio guard).
- `tests/docs_explorer/test_readers_compile_fields.py` — profiler: `test_measurements_from_fixture_log` (US-1 numbers), `test_provenance_and_dr_rows`, `test_empty_log_reads_not_recorded`, `test_missing_log_reads_not_recorded`, `test_unrecorded_not_in_denominator`, `test_non_numeric_distance_excluded`, `test_unresolved_compiled_from_is_unknown_template`, `test_sp27_fires_inferred_and_skips_t0`, `test_sp28_fires_verified_above_0_2_not_at_0_2`, `test_sp28_evidence_names_samples`, `test_catalogs_gain_sp27_sp28_f26_f27_without_renumbering`, `test_compare_rows_carry_compiled_and_edit_dist`, `test_render_has_compile_section`, `test_compile_measurements_rebuild_equal`, `test_malformed_line_skipped`, `test_evidence_carries_no_prompt_text`; dream: `test_compiled_false_presence_proposal`, `test_unanswered_dr_proposal`, `test_dr_answered_later_not_proposed`, `test_refusals_proposal`, `test_no_compile_fields_no_co_s0_proposal`; lint: `test_self_test_exits_zero`, `test_seat_missing_refused`, `test_seat_invalid_refused`, `test_fan_out_without_co_s0_refused`, `test_fan_out_with_zero_cap_exempt`, `test_hard_stop_without_co_s2_refused`, `test_dispatch_before_compile_refused`, `test_good_skill_accepted`, `test_exit_2_when_no_skills_root`.
- `tests/docs_explorer/test_skill_co_s0_citation.py` — `test_every_prose_input_skill_carries_the_sentence_exactly_once` (across SKILL.md ∪ reference), `test_pointer_route_skill_cites_co_s0_in_skill_md`, `test_optimize_graph_and_prepare_carry_it_once_not_twice`, `test_optimize_graph_carries_the_dispatchable_stop_once`, `test_every_owned_skill_declares_runs_as_from_the_closed_set`, `test_hard_stop_skills_cite_co_s2`, `test_no_machine_path_in_new_files`.
- Existing suites stay green: `test_session_profile*.py`, `test_dream_pack_o.py`, `test_context_budget.py`, `test_portable_text_io_gates.py`.
- **Red first:** the lint's argument-free run on the base tree (`seat missing` × 25 expected), the citation test, and the reader tests were all observed failing before the code existed (recorded in the implement Proof Pack).

## Conformance notes
LOA C-criteria N/A (no model step). Pack conventions: stdlib only, 3.8+, LF writes, stdio guard, refusal grammar, `--self-test`, module docstring naming the class — all conformed; no deviation recorded.

## Flagged risks & residual unknowns
| Risk | Cheapest next probe |
|---|---|
| SP-28's 0.20 threshold (Flagged) | ten compiles per template, then read the distribution |
| Eight skills carry the sentence by pointer, not inline (the always-injected surface says only "CO-S0 applies first") | the Coordinator raises eight baselines by ~55 tokens; one edit moves the sentence inline |
| P2's two skills fail the lint in this tree | green at the join once P2's `runs_as: Coordinator` and CO-S0 line land |
| `.claude/skills` as the consuming-repo skills root (Inferred) | `pack-doctor` in a consuming repo after the next `updatepack` |
| The Copilot prompt mirrors do not carry the sentence (they carry no Grounding text) | none needed — the mirror is a pointer/summary; recorded so nobody looks for it |

## Status & next action
| | |
|---|---|
| **Completed** | This design; the spec it implements |
| **Remaining** | `/implement` (tests red → readers, miner, lint, SKILL.md lines → gates); the `documents` links from `docs/security/threat-model.md` and `privacy-review.md` to this design (P8 may not edit `docs/security/*` — reported to the Coordinator for the join) |
| **Best next action** | `/implement docs/design/compile-readers.md` in this tree |

## Gate record
`GATE design · 2026-09-19 · Test Architect (hard) · SRE · Patterns Expert ⇄ Simplifier · Security (advisory) · Data & Persistence Architect — inline, fan-out 0 · verdict: PASS-WITH-CONDITIONS`

| # | Finding (severity) | Resolution |
|---|---|---|
| 1 | Test Architect — "`family_comparison(sessions)` is sliced by source text in an existing test (line 524); a signature change could break it" (Major) | optional kwarg with default `None`; the existing test is run before and after; recorded as a check in the implement plan |
| 2 | SRE — "the reader raising inside `cmd_profile` would take the harness tables down with it" (Major) | wrapped: `OSError`/`ValueError` → `not recorded` + one stderr line (error model) |
| 3 | Simplifier ⇄ Patterns Expert — "a shared audit reader module vs a local 10-line function" | local function with a `simplify:` ceiling (third reader → lift) |
| 4 | Data & Persistence Architect — "median of medians in the compare table" (Major) | pooled samples per group; medians never summed (Additivity) |
| 5 | Security — "prompt text into evidence" (Minor) | ids/shortnames/codes/numbers only; negative test |
| 6 | Test Architect — "the pointer route makes 'exactly once' ambiguous" (Major) | defined: exactly once across SKILL.md ∪ reference; SKILL.md must cite `CO-S0` exactly once in either route |

Authors did not clear their own veto: #1 and #6 were raised by the Test Architect and resolved by the Python Developer's rewrite, re-read by the Test Architect.

---
**Handoff:** → `/implement`.
