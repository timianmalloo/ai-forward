---
id: design-compile-stage
title: "Design — the compile stage (prompt-compile.py · verify-compiled-prompt.py · harness templates · /compile · audit fields)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, compile, prompt, audit-log, prompt-log, templates, skill, p7]
links:
  - { to: spec-compile-stage, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: design-coord-federation-phase3, rel: relates-to }
  - { to: audit-log, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  Detailed design for spec-compile-stage. One stdlib engine (prompt-compile.py: skeleton · finish ·
  render · distance) and one gate (verify-compiled-prompt.py, nine self-test directions) around a
  compiled-prompt JSON whose invariant is no added scope; versioned harness templates as data files
  (v1 claude-code, codex); the compilation recorded as a new audit-log kind that the existing
  /prompts lens reads unchanged; a thin /compile skill and a seeded agent-coordination.md carrying
  the CO-S0 stage. Divided into two disjoint tracks for /prepare-for-coordination.
---

# Design: the compile stage

- **Status:** Draft
- **Spec / architecture:** `docs/specs/compile-stage.md` (US-1…US-8, NFRs, boundary set) · `docs/architecture-agent-coordination.md` (the coordination layer this stage feeds) · proposal §7b.4, P7, D14, D15
- **Delivery phase / vertical slice:** coordination **P7**, the first of the proposal's build-plan items to be built after P0–P2 were specified. Real around it at this phase: the audit log (`audit-log.py`, `prompt-log.py`), the docs graph, the two coordination skills. **Mocked / absent:** P4 dispatch (`coord dispatch`), P5 rulings, the doorbells — so the *contract slot* is carried empty and a decision request is answered by the operator editing the compiled prompt, not by a ruling entry. Mock-substitutable seams: the **model fill** (a JSON the running agent edits; a fixture fills it in tests) and the **template** (a data file; tests ship their own).
- **Author(s) / date:** Patterns Expert + The Simplifier + Python Developer + Data & Persistence Architect + Security & Identity Architect (peers), 2026-09-19. Adversaries: Test Architect (hard veto), Security (hard veto), SRE, Patterns Expert ⇄ Simplifier.

> **Grounding trace (V15):** `design-compile-stage` → `implements` → `spec-compile-stage` (US-1…US-8; the Compilation and Template-set aggregates) → `refines` → `proposal-owner-coordinator-subagent-coordination` (§7b.4, P7) → `relates-to` → `design-coord-federation-phase3` (the local conventions for a pack script with a `--self-test`, a registry-as-data-file, and spikes recorded in the design) → `relates-to` → `audit-log` (the single store; `AUDIT_KINDS`, `_adapt()` in `prompt-log.py`). Read for conventions: `pack/scripts/audit-log.py` `cmd_append` (goal fields, `main_budget`, `agent_run`, `consume_start`), `pack/scripts/prompt-log.py` `_adapt`/`load_entries`/`cmd_add`, `tests/docs_explorer/test_context_budget.py` (module-load-by-path test idiom), `tools/check-consistency.py` (counts and prose totals), commit `abe76c4` (the last new skill: the full surface a skill touches). No drift found between the spec and the architecture; one **spec clarification** recorded below (the compilation's audit `kind`).

---

## Responsibility

**One:** turn a logged raw prompt into a gated, logged, harness-rendered compiled prompt without adding scope — and make the compile measurable. Not responsible for: executing or dispatching the prompt, choosing the harness, optimising for accuracy, answering assumptions, or editing the raw prompt.

## Spec clarification (recorded, not drift)

The spec says the compilation is "one audit entry naming the raw prompt id". `audit-log.py` validates `--kind` against `AUDIT_KINDS = ["skill","command","script","prompt","commit","manual","session-import"]`. A compilation is none of these; forcing it into `prompt` would make `/prompts` show compiled text as if the operator typed it. **Decision:** add `compilation` to `AUDIT_KINDS`. The entry's `prompt` field carries the **rendered compiled text**, so the unchanged `prompt-log.py` `_adapt()` already lists it for reuse; the structured record lives in a `compiled` object beside it. Recorded as decision note `note-20260919-compilation-is-an-audit-kind`.

## Data model (settled first — DM1–DM6)

**Bounded context:** Prompt compilation (spec). **Aggregates:** Compilation (root: the compiled prompt; invariant: no added scope) and Template set (root: harness template; invariant: one current version per harness). Referenced by identity only: the raw prompt (audit id), the template (harness + version), the docs-graph nodes (ids).

**Durable representation.** Append-only facts in the existing audit log; no new store, no directory of compiled files.

| Fact / projection | Grain ("one row is exactly one …") | Additive measures | History rule | Derive-don't-store |
|---|---|---|---|---|
| `kind: compilation` audit entry | one **gate-passing compile attempt** of one raw prompt for one harness | `assumptions`, `consequential`, `decision_requests` (counts), `engine_seconds`, `compile_tokens` (or `not recorded`) — all additive across entries | append-only; a re-compile is a new entry naming the same `raw_id`; **never** updated in place (a stale-marker duration is `not recorded`) | `dispatchable` is stored as the **snapshot at compile time** (derived from `decision_requests` being non-empty) and labelled so; the consuming skill recomputes from the text it receives (an unanswered `DR-n` line) |
| `compiled_from` + `edit_distance` on a workflow's closing entry | one workflow run started from one compiled prompt | `edit_distance` is **non-additive** (a ratio; aggregate by distribution, never by sum) | append-only | `compiled: false` is written when a `kind: skill` entry has no `--compiled-from` — a stored flag so the PACK-O miner reads presence without a join |
| Harness template file | one **version** of one harness's idiom | — | a new version is a new file; `current: true` moves; old files stay (Type-2 by file) | the renderer never caches; `template ambiguous` is computed at every render |
| `/prompts` twin view | projection over `kind: prompt` and `kind: compilation` rows | — | derived, rebuildable | never a store (`prompt-log.py` reads the JSONL each run) |

**Enforced invariants and their tests:** no added scope → `verify-compiled-prompt.py` directions 1–3, 8, 9; one current template → `prompt-compile.py render --self-test`; append-only → the existing audit-log tests plus `test_compile_audit_fields.py::test_recompile_is_a_new_entry`; determinism of the skeleton → golden test (same raw, same tree, same template ⇒ byte-identical skeleton).

## Contracts

### Exposed

**`pack/scripts/prompt-compile.py`** (stdlib; exit 0 ok · 1 refused · 2 usage; every refusal `<code>: <target> — fix: <text>` on stderr)

| Verb | Arguments | Effect |
|---|---|---|
| `skeleton` | `--text "<raw>"` \| `--text-file <path>` \| `--from-audit <al-id>`; `--harness <name>`; `--out <path.json>`; `--no-model` | Refuses `empty prompt` (before any logging). Logs a `kind:prompt` entry via `prompt-log.py add` when the input is text (the id becomes `raw_id`); `--from-audit` refuses `raw not found` unless the id exists and is `kind: prompt`. Detects pass-through by the fixed grammar. Resolves references by the reference grammar; computes `raw_sha256`; collects docs-graph neighbour ids; loads the current template (refuses `template missing` / `template ambiguous`); writes the **skeleton JSON** with model-filled fields set to `null` (or literally `"NOT COMPILED"` with `--no-model`); prints the path and `engine_seconds`. |
| `finish` | `<compiled.json>`; `--harness <name>` (defaults to the skeleton's); `--session <id>`; `--compiler-model <name>`; `--compile-tokens <n>`; `--no-clipboard` | Runs the gate (`verify-compiled-prompt.py` imported by path); on refusal prints the refusals and exits 1 **without logging**; on pass renders the idiom, appends the `kind: compilation` entry (via `audit-log.py append --kind compilation --from-json`), prints the rendered text, copies it to the clipboard when one is available (else prints `clipboard: skipped`). |
| `render` | `<compiled.json> --harness <name>` \| `--self-test` | Renders only (no gate, no log). `--self-test`: two current templates for one harness ⇒ `template ambiguous`; one ⇒ rendered; none ⇒ `template missing`. |
| `distance` | `--compiled <al-id>` `--received-file <path>` | Prints `1 − difflib.SequenceMatcher(None, compiled, received).ratio()` over line-ending-normalised text, 4 decimals. |

**`pack/scripts/verify-compiled-prompt.py`** (stdlib; exit 0 pass · 1 refused · 2 usage)

`verify <compiled.json> [--audit-root docs/audit]` reads the raw text by `raw_id` from the JSONL and applies, in order: `field missing` (seven goal-state fields non-empty, unless `NOT COMPILED` mode) → `raw mismatch` (sha256 of the raw text ≠ `raw_sha256`) → `assumption incomplete` (belief/confirm/breaks) → per clause in *Done when* and *Not in scope*: `added scope` (no trace) · `invalid trace` (phrase not a verbatim substring after whitespace-collapse, case-sensitive; or assumption id absent) → `decision request missing` (a clause whose only trace is an assumption without `consequential: true` and a `DR-n` in `decision_requests`) → `pass-through refused` (in pass-through mode the same checks minus trace checks, reported under this code). Prints the clause → trace table on pass. `--self-test` runs the **nine directions** in a temp dir and exits 0 only if all nine behave.

**`pack/commands/compile/SKILL.md`** — `/compile [text | --from-audit <id>] [--harness <name>] [--edit]`: the operator-facing wrapper (below). **`pack/adapters/copilot/prompts/compile.prompt.md`** — the Copilot mirror. **`pack/evals/cases/compile-01.json`** — the eval case (T14 → A6).

**`audit-log.py` additions:** `compilation` in `AUDIT_KINDS`; `append --compiled-from <al-id> --edit-distance <float>`; when `kind == skill` and no `--compiled-from`, write `compiled: false`; a `compilation` entry never consumes a start marker (like `prompt`). **`prompt-log.py` additions:** `list`/stack shows `kind: compilation` rows with a `⟲ compiled from <raw_id>` label suffix and `--raw <id>` filter; `search` already matches the `prompt` field of both.

**`pack/knowledge/agent-coordination.md`** (`load: skill`) — seeded with **CO-S0 Compile** only, and a header stating CO1–COn land with P0. **`optimize-graph`** and **`prepare-for-coordination`** Stage 0 gain one sentence citing CO-S0 (the other twelve prose-input skills are P8).

### Consumed (each with source and confidence)

| Contract | Source | Confidence |
|---|---|---|
| `audit-log.py append` flags and `--from-json` merge semantics | `pack/scripts/audit-log.py` `cmd_append` L703–L800, read this session | Verified |
| `prompt-log.py add` writes `kind:prompt` via `audit-log.py`, `--prompt-file -` over a UTF-8 pipe | `prompt-log.py` `cmd_add` L221–L260 | Verified |
| `_adapt()` lists any entry with a non-empty `prompt` field | `prompt-log.py` L96–L120 | Verified |
| Frontmatter `id:` on every docs artifact; `docs/docs-index.js` derived | `docs-graph.py` (V2); this repo | Verified |
| Skill surface: SKILL.md + Copilot prompt + eval case + counts in INSTALL/README/OVERVIEW/managed blocks + `check-consistency.py` + `context-budget.json` `skills_baseline` | commit `abe76c4`; `tools/check-consistency.py` L4–L16; `pack/context-budget.json` | Verified |
| Clipboard ladder (pbcopy · clip.exe UTF-16LE · xclip · skip) | `prompt-log.py` (P2 work, this repo) — **reused by import**, not copied | Verified |
| `difflib.SequenceMatcher.ratio()` semantics | Python stdlib docs | Verified (stdlib) |
| Codex brief shape: `codex exec --json -o <file> --output-schema <file> --worktree -C <dir>` | KB `data-and-constants.md` "Harness CLI contracts", executed 2026-09-18 | Verified |
| Claude Code brief shape: `start` line first, absolute paths, no `EnterWorktree`, CT27 line shapes | `execute-with-coordination/SKILL.md` Stage 3 | Verified |
| A running Claude Code agent can edit a JSON file and re-run a script (the model-fill seam) | this session, every day | Verified |

No unfamiliar contract; **no spike needed**. The one open contract — how well a Codex-rendered brief performs — is a measurement the spec already flags.

## Patterns (named, justified, ladder-climbed)

| Pattern | Where | Why it survives both lenses |
|---|---|---|
| **Compiler front-end split: deterministic skeleton + bounded fill + verifier** (TSCG's shape; LOA "deterministic wrapper around a model step") | `skeleton` → agent edits JSON → `finish` | The Simplifier's alternative — "let the agent write the goal state as today" — is the measured 38% problem; the Patterns Expert's alternative — a pipeline DSL — is DSPy, struck as a non-goal. The JSON-in-the-middle is the smallest seam that lets a test substitute the model. |
| **Registry as data files with one `current`** (already used for `.agents/artifacts.yml` and the hook adapters) | `pack/adapters/prompt-templates/<harness>.v<n>.md` | Reuse-in-codebase rung; a Python dict of templates would hide versions from `git log`. |
| **Gate as a separate script with `--self-test`** (the pack's own idiom: `verify-no-conflict-markers.py`, `verify-subprocess-utf8.py`) | `verify-compiled-prompt.py` | Conformance to the local convention; the engine imports it by path rather than duplicating rules. |
| **Single store, new kind** | `kind: compilation` | Ladder rung "reuse what already lives here"; a `compiled/` directory was the rejected alternative (second store, drift). |
| **Placeholder substitution, not a template engine** | `{{goal_state}}`, `{{trace}}`, `{{references}}`, `{{assumptions}}`, `{{decision_requests}}`, `{{contract_slot}}`, `{{provenance}}` via `str.replace` | stdlib rung; `simplify:` marker — ceiling: seven named placeholders, no conditionals; upgrade trigger: a template needs a loop or a conditional. |

Rejected: Jinja2 (new dependency for seven substitutions); a `.py` template module per harness (code where data suffices); a hash-only trace (the review showed substring validity must be checked against the raw **text**).

## Data shapes

```jsonc
// compiled prompt (the skeleton after fill) — pack/scripts/prompt-compile.py writes and reads this
{
  "schema": "compiled-prompt/1",
  "raw_id": "al-…", "raw_sha256": "…", "raw_text_normalised": false,
  "harness": "claude-code", "template": "claude-code", "template_version": 1,
  "mode": "compiled" | "pass-through" | "not-compiled",
  "goal_state": { "goal": "…", "done_when": ["…"], "not_in_scope": ["…"], "tier": "T1",
                  "fan_out_cap": 2, "context_ceiling": 400000, "main_line_budget": 60 },
  "clauses": [ { "section": "done_when" | "not_in_scope", "text": "…",
                 "trace": { "kind": "phrase" | "assume", "ref": "<verbatim phrase>" | "#1" } } ],
  "references": [ { "token": "conductor-join.py", "status": "resolved" | "unresolved",
                    "path": "pack/scripts/conductor-join.py", "sha256": "…", "reason": null | "outside repo" | "ambiguous: 2 matches" | "not found" } ],
  "graph_neighbours": [ "spec-compile-stage", "…" ],
  "assumptions": [ { "id": "#1", "belief": "…", "confirm": "…", "breaks": "…", "consequential": true } ],
  "decision_requests": [ { "id": "DR-1", "assumption": "#1", "question": "…", "default": "…", "answer": null } ],
  "contract_slot": { "width_cap": null, "transient_retry": null, "per_branch_exit": null, "join_rule": null,
                     "containment": null, "termination": null, "deadline": null, "fallback": null },
  "dispatchable": false,
  "provenance": { "engine_seconds": 0.41, "compiler_model": "claude-fable-5-1" | null,
                  "compile_tokens": null, "refusals": [], "retries": 0 }
}
```

The audit entry: `{ kind: "compilation", shortname: "compile-<raw shortname>", prompt: "<rendered text>", summary: "compiled <raw_id> for <harness> v<n>: <k> clauses, <a> assumptions, <d> decision requests", artifacts: [], compiled: { …the object above minus raw_text… }, compiled_from: null, dispatchable, mode }`. A workflow's entry: `{ …, compiled_from: "al-…", edit_distance: 0.0731 }` or `{ …, compiled: false }`.

Template file (`pack/adapters/prompt-templates/claude-code.v1.md`):

```
---
harness: claude-code
version: 1
current: true
forbids: ["EnterWorktree", "ExitWorktree", "cd "]
---
python3 docs/ai-forward-pack/scripts/audit-log.py start --session {{session}} --skill {{skill}}
{{goal_state}}
{{trace}}
{{references}}
{{assumptions}}
{{decision_requests}}
{{contract_slot}}
Rules: absolute paths only; a multi-line program is a file, then a run; a gate's exit status is never behind a pipe.
{{provenance}}
```

`forbids` is checked by `render`: a rendered brief containing a forbidden token refuses `forbidden construct: <token>` (a template author's error, caught at render).

## Error & concurrency model

- **Errors are refusals with stable codes** (O7): `empty prompt` · `raw not found` · `template missing` · `template ambiguous` · `forbidden construct` · `field missing` · `raw mismatch` · `assumption incomplete` · `added scope` · `invalid trace` · `decision request missing` · `pass-through refused` · `outside repo` (a reference reason, not an exit). Exit 1 for any refusal, 2 for usage. Nothing is logged on a refusal; `finish` is the only writer and writes last.
- **Idempotency:** `skeleton --from-audit` is pure; `skeleton --text` logs one `kind:prompt` per call by design (a second call is a second raw prompt — the operator asked twice). `finish` on the same JSON twice appends two compilation entries naming the same `raw_id` (append-only; the second is a recompile).
- **Concurrency:** no shared mutable state beyond the JSONL, whose append discipline the audit log already owns (one line per `append`, `newline="\n"`, UTF-8). Two sessions compiling at once produce two entries.
- **Retry loop** (the skill's, not the engine's): at most two re-fills on a refusal, then hand the refusal to the operator. Termination variant: attempts remaining.
- **Cancellation:** killing `finish` before its append leaves no entry; the start marker, if any, is marked stale by the next entry.

## Change-surface list (E7)

store (audit JSONL: new kind, new fields) → model (`compiled-prompt/1` JSON; template frontmatter) → service (`prompt-compile.py`, `verify-compiled-prompt.py`, `audit-log.py`, `prompt-log.py`) → projection/wire (`audit-log.py render` → `audit-data.js`; `/prompts` stack labels) → client type (`docs/audit/index.html` shows a `compiled` badge and the `compiled_from` link — a badge on an existing row, no new screen) → UI (`/compile` SKILL.md, Copilot prompt; CO-S0 in `agent-coordination.md`; one sentence in two skills) → compute reader (`/session-profiler` and `/dream` read `compiled`, `edit_distance`, `compiled: false` — **deferred to P8** and recorded as remaining) → install surface (INSTALL.md rev 76 counts `skills: 28, knowledge_docs: 39, scripts: 32`; README/OVERVIEW/managed blocks "Workflows (28)"; `check-consistency.py`; `context-budget.json` `skills_baseline`; `sync-pack.ps1` regenerates `.claude/`, `.github/`, `.grok/`, `.agents/`, `docs/ai-forward-pack/`).

## Failure-mode analysis

| Failure mode | From which choice | Disposition | How it's addressed | Detection | Test |
|---|---|---|---|---|---|
| Empty / whitespace input | `--text` | prevent | refuse before logging | `empty prompt` refusal | `test_empty_text_logs_nothing` |
| Input already a goal-state block | fixed grammar | mitigate | pass-through keeps state, self-traces, still gated | `mode: pass-through` | `test_pass_through_passes_gate`, `test_prose_goal_colon_is_not_pass_through` |
| Raw id missing / wrong kind | `--from-audit` | prevent | `raw not found` | refusal | `test_from_audit_wrong_kind_refused` |
| Reference not found / ambiguous / outside repo | reference grammar | mitigate | unresolved + consequential assumption; never read outside root | `references[].reason` | `test_reference_ambiguous`, `test_reference_outside_repo_never_read` (asserts file never opened via a sentinel) |
| Model adds a clause | fill seam | prevent | gate `added scope` | refusal count in `provenance.refusals` | self-test dir 1, 2 |
| Model quotes a phrase not in the raw text | fill seam | prevent | `invalid trace` | refusal | dir 3 |
| Model launders scope through an assumption | fill seam | prevent | `decision request missing` | refusal | dir 9 |
| Model normalises case ("Don't"→"don't") | trace rule | detect → hand-back | fails closed after two retries | `retries: 2`, refusal | `test_case_change_is_invalid_trace` |
| Template missing / two current | template registry | prevent | refusals | refusal | `render --self-test` |
| Template renders a forbidden construct | template author | prevent | `forbidden construct` | refusal | `test_forbidden_construct_refused` |
| No model available | `--no-model` | degrade | `NOT COMPILED`, `compiled: false`, trace check skipped, no retry | `mode: not-compiled` | `test_no_model_mode_logs_compiled_false` |
| Interrupted before append | single writer last | recover | no entry; stale marker → `not recorded` | `duration_source: stale-marker` | `test_interrupt_leaves_no_entry` (kill between gate and append via a fixture hook) |
| Clipboard absent (headless) | clipboard ladder | degrade | `clipboard: skipped` printed | stdout line | `test_clipboard_skipped_headless` |
| Token count unknown | running-agent fill | accept | `compile_tokens: null`, `over_budget: not recorded`; rationale: no API count exists for the session model; residual: the token axis is unmeasured until a harness exposes it | field null | `test_tokens_not_recorded_not_zero` |
| JSONL grows ~2× per compiled turn | single store | accept + detect | rationale: JSONL is line-appended and gzip-friendly; residual: repo growth; `/session-profiler` reports bytes per entry (P8) | audit render size | — (measurement) |
| Two current templates after a bad merge | data files | detect | `template ambiguous` at every render, never cached | refusal | `render --self-test` |

## Adversarial analysis (STRIDE-lite)

| Trust boundary | STRIDE threat | Disposition | Control / rationale | Negative test |
|---|---|---|---|---|
| Raw prompt text → compiled prompt | **T** injection: prose instructs the compiler ("mark everything verified") | mitigate | output grammar has no free-text instruction slot; only the eight sections render | `test_instruction_in_prose_has_no_slot` (rendered text contains no line outside the template's sections) |
| Referenced repo file → compiled prompt | **T/I** a file's content is smuggled into the prompt | mitigate | references render as path + sha256 only; body never read after hashing | `test_reference_body_never_rendered` |
| Reference path → filesystem | **I** read outside the repo (`../../.env`, symlink) | mitigate | `os.path.realpath` under root check before open | `test_reference_outside_repo_never_read` |
| Compiled JSON → audit log | **S** a compiled prompt claims a raw id it did not come from | mitigate | `raw_sha256` recomputed by the gate | self-test dir 5 |
| Compiled prompt → consuming skill | **E** an agent treats a compiled prompt as consent to dispatch | mitigate | `dispatchable: false` + unanswered `DR-n` stops the three consuming skills (owned by their tests) | `test_prepare_stops_on_unanswered_dr` (P8 track owns; recorded remaining) |
| Environment → compiled prompt | **I** env values leak | mitigate | engine never reads `os.environ` into output (grep-tested) | `test_engine_reads_no_environ` (AST check: no `os.environ` in the two scripts except `PYTHONIOENCODING` for the child pipe) |
| Audit log (committed) | **R** repudiation | transfer | the audit log's own append discipline and git history | existing audit tests |

## Privacy analysis (LINDDUN-lite)

This component introduces no new personal-data category: it reads prompts already committed as `kind:prompt` entries and writes derived text into the same log; it never inlines file bodies or environment values. Verified by reading `cmd_add` (prompts are committed today) and by the two negative tests above. Retention and rights paths are those of the audit log (`audit-and-change-log.md`). No LINDDUN finding beyond the existing log's.

## UI & interaction design

**Medium:** CLI (terminal text). No visual UI of this component's own (spec Part C N/A). The compiled prompt renders in the **eight-section order** of the spec's IA with fixed English labels; refusals in the fixed grammar; `clipboard: skipped` when headless; plain text, no colour-only meaning. The audit timeline gains a `compiled` badge and a `from <raw_id>` link on existing rows (inherits the page's tokens and states; no new component).

## Telemetry

- The **compilation entry is the telemetry** (IO): `engine_seconds`, `compile_tokens` (or null → rendered as `not recorded`), `assumptions`, `consequential`, `decision_requests`, `refusals[]`, `retries`, `mode`, `template_version`, `dispatchable`.
- The **workflow entry** adds `compiled_from`, `edit_distance`; `compiled: false` otherwise.
- **Stable error codes** (O7): the refusal codes above, unchanged across versions; a new code is a design change.
- **Cardinality** (O13): no free-text in metric-like fields; counts and enums only. No HTTP surface (O8 N/A). Load-bearing telemetry is tested: `test_compilation_entry_fields`, `test_edit_distance_recorded`, `test_compiled_false_on_plain_skill_entry`.

## Test plan (Testing Strategy triggers → directives)

| Trigger | Directive | Tests (all `tests/docs_explorer/`, module-load-by-path idiom) |
|---|---|---|
| T1 pure logic (trace validity, sha256, distance) | D1 | `test_verify_compiled_prompt.py`: nine self-test directions run as unit tests + `test_selftest_exits_zero`; `test_prompt_compile.py::test_distance_known_pairs` (three fixed pairs) |
| T2 parsers/validators (reference grammar, pass-through grammar, template frontmatter) | D2 | boundary rows as parametrised cases: empty, "my goal:" mid-sentence, non-English prose with English labels, long prompt, ambiguous basename, outside-repo path |
| T4 filesystem/persistence (JSONL append, template files) | D4 | `test_compile_audit_fields.py`: `compilation` kind accepted; `--compiled-from`/`--edit-distance` written; `compiled: false` on a plain skill entry; recompile is a new entry; interrupted finish leaves no entry; `render --self-test` |
| T8 a substitute at a boundary (the fill fixture) | D7 | the fixture that fills the skeleton is exercised against the real gate, so a drift between fixture and gate fails |
| T9 deterministic wrapper around a model step | A1 | skeleton determinism golden test; `finish` with a fixture fill end-to-end (skeleton → fill → gate → render → entry) |
| T11 model output consumed as typed data | A3 | schema check of `compiled-prompt/1` (required keys, enums) before the gate; malformed JSON ⇒ `usage` exit 2 with the offending key |
| T14 a skill/prompt markdown is added | A6 | `pack/evals/cases/compile-01.json`; `context-budget.py skills --gate` (new skill under 5,000 tokens) |
| Determinism (NFR) | D1 | golden skeleton test; `engine_seconds` median-of-five ≤ 5 s |
| Portability (PLAT-A gates 1b–1d) | existing gates | the two scripts pass `verify-no-machine-paths`, `verify-subprocess-utf8`, `verify-portable-text-io` |
| Measurement, not acceptance (spec US-3) | — | `tests/docs_explorer/fixtures/compile-eval/` with 20 planted-belief and 10 planted-instruction prompts; a script records catch rates per template version into the eval case notes; **no assertion on the rate** (v1 sets the floor) |

Red first: the nine self-test directions and `test_compile_audit_fields.py` are written and observed failing before the engine and the audit-log change land.

## Tracks for `/prepare-for-coordination` (authored paths, disjoint)

| Track | Owns (authored) | Depends on | Exit evidence |
|---|---|---|---|
| **A — engine, gate, templates** | `pack/scripts/prompt-compile.py`, `pack/scripts/verify-compiled-prompt.py`, `pack/adapters/prompt-templates/claude-code.v1.md`, `pack/adapters/prompt-templates/codex.v1.md`, `tests/docs_explorer/test_prompt_compile.py`, `tests/docs_explorer/test_verify_compiled_prompt.py`, `tests/docs_explorer/fixtures/compile-eval/**` | the CLI contract above (fixed); B's `AUDIT_KINDS` change only at `finish` (A's tests stub the append until B lands; the join runs the end-to-end test) | both scripts' `--self-test` exit 0; the two test files green; gates 1b–1d green on the new files |
| **B — audit fields, skill, knowledge** | `pack/scripts/audit-log.py`, `pack/scripts/prompt-log.py`, `tests/docs_explorer/test_compile_audit_fields.py`, `pack/commands/compile/SKILL.md`, `pack/adapters/copilot/prompts/compile.prompt.md`, `pack/evals/cases/compile-01.json`, `pack/knowledge/agent-coordination.md`, one Stage-0 sentence in `pack/commands/optimize-graph/SKILL.md` and `pack/commands/prepare-for-coordination/SKILL.md` | the CLI contract above (the skill's commands); A's script names | `test_compile_audit_fields.py` green; existing `test_audit_log.py` green; the skill under the 5,000-token skill ceiling |
| **Coordinator (join)** | `pack/adapters/INSTALL.md` (rev 76, counts, changelog), `README.md`, `pack/README.md`, `pack/OVERVIEW.md`, `pack/adapters/managed-blocks/*.block.md` (28), `tools/check-consistency.py`, `pack/context-budget.json`, `docs/notes/note-20260919-compilation-is-an-audit-kind.md`, derived surfaces via `sync-pack.ps1` | A and B joined | `verify-bundle.ps1` green except the three pre-existing gate-3 tests; end-to-end `finish` on a real prompt in this repo |

`derived` and `register` paths (everything under `docs/ai-forward-pack/`, `.claude/`, `.github/`, `.grok/`, `.agents/`, `docs/docs-index.js`, `web/`, `docs/portal/`) need no claim: the coordinator regenerates them once at the join.

## Conformance notes

LOA C1 (tier annotation): the engine and gate are T0 deterministic; the fill runs at the session model's tier — recorded in `provenance.compiler_model`. C3 (receipt): the compilation entry is the receipt. C4 (typed boundary): `compiled-prompt/1` JSON with a schema check. C5 (side-effect protection): the only side effect is the audit append, behind the gate. C9: no anti-pattern signature — no silent fallback, no plausible default.

## Flagged risks & residual unknowns

| Risk | Cheapest next probe |
|---|---|
| Template quality per harness (Inferred) | ship v1; read `edit_distance` after ten compiles each |
| The consuming skills' `dispatchable` stop is P8's | record as remaining; until then the operator's edit is the control |
| `/session-profiler` and `/dream` do not yet read the new fields | P8 |
| `kind: compilation` may need the audit viewer's kind filter extended | check `docs/audit/index.html` filter list at the join; add the kind if the list is enumerated |

## Status & next action

| | |
|---|---|
| **Completed** | design of the compile stage: data model, CLI contract, data shapes, templates, refusal codes, failure/STRIDE/LINDDUN analyses, telemetry, test plan, two disjoint tracks and the coordinator's join list |
| **Remaining** | P8 readers (`session-profiler`, `dream`, the twelve other prose-input skills' CO-S0 citation, the consuming skills' `dispatchable` stop); templates for Copilot, Grok, Antigravity (after P4 executes their doorbells) |
| **Best next action** | `/prepare-for-coordination` on this design's track table, then `/execute-with-coordination --agents` |

## Gate record

`GATE design · 2026-09-19 · peers: Patterns Expert, Simplifier, Python Developer, Data & Persistence Architect, Security · adversaries: Test Architect (hard), Security (hard), SRE, Patterns Expert ⇄ Simplifier · criteria met: data model first (grain, additivity, history, derive-don't-store per row); E7 list; every consumed contract Verified from this repo, no spike needed; patterns named and ladder-climbed with one simplify: marker; failure modes dispositioned with tests; STRIDE per boundary with negative tests; LINDDUN no-new-data line; telemetry = the entry; every triggered directive (T1, T2, T4, T8, T9, T11, T14) in the plan · verdict: PASS at authoring; the hard vetoes are re-checked by the Test Architect at the implement join (the author does not clear them) · vetoes→resolution: Simplifier "three artifacts for one feature" → one engine, gate as the pack's own idiom, skill as a thin wrapper (maintainer's need); Simplifier "a new knowledge doc for one paragraph" → accepted as the seeded P0 home at load: skill (no always-on budget hit); Security "the fill step reads referenced files" → the engine hashes and closes; the model step sees paths and hashes only; Data architect "dispatchable is a stored derivation" → labelled as a compile-time snapshot with the consumer recomputing from text.`

---
**Handoff:** → `/prepare-for-coordination` → `/execute-with-coordination --agents` → `/implement` per track.
