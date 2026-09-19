---
id: spec-skill-evolution
title: "Skill evolution — the ten remaining skills cite CO-S0, the §7b.3 rows land as text the lint can refuse, and the owner-review sentences reach the two coordination skills"
type: spec
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, skills, co-s0, co-s2, runs-as, lint, context-budget, owner-review, p8]
links:
  - { to: spec-compile-readers, rel: refines }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: implements }
  - { to: coordination-p3-p5-p8, rel: relates-to }
  - { to: spec-owner-review, rel: relates-to }
  - { to: note-20260919-readers-seat-and-citation-placement, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Specifies the P8 skill sweep: the ten skills that still cite no CO-S0 carry the citation (a
  Grounding sentence, or the fixed sentence behind a reference/co-s0.md pointer where the 2%
  budget cannot hold it); the proposal §7b.3 rows for groups C and D land as skill text that names
  only landed engine verbs; P5's owner-review contract sentences are inserted verbatim into the
  two coordination skills; verify-skill-contracts.py gains three red-first rules (compile missing,
  pointer without reference, dispatch without deadline) so the sweep is a control, not a memoir.
---

# Spec: Skill evolution (P8 skill sweep)

- **Status:** Draft
- **Tier (cost-of-error):** **T2** (fixed by the coordination plan row). A skill is the always-injected contract a session runs from; a wrong sentence here is loaded on every invocation in every consuming repo, and the lint it feeds becomes a bundle gate.
- **Author(s) / date:** Python Developer (lead, Peer Mode; the persona the plan names for P8) with the Test Architect, the Simplifier and the AI Systems Engineer enacted inline — **fan-out 0**, the track's cap. 2026-09-19.
- **Compiled from:** the P8 dispatch brief (Sub-Agent seat, CO-S1): its goal state is this spec's goal state and its *Not in scope* is the interdiction (CO-S0).
- **Supersedes / related:** refines `spec-compile-readers` (US-4..US-8 landed the seat key, the fixed sentence on the fourteen prose-input skills and the four-rule lint); implements proposal §7b.2 (the three stages), §7b.3 groups A (verification only), C and D, §7b.5 (controls); lands seam (b) of `docs/coordination/seam-p5-to-coordinator.md`.

## Part A — Functional specification

### Problem
Measured on this tree at `9ea0e00` (`grep -c CO-S0 pack/commands/*/SKILL.md`): **10 of 28** skills cite no CO-S0 — `addpacktorepo`, `also`, `apply-learnings`, `auditlog`, `dream`, `extendaibundle`, `prompts`, `searchprompts`, `session-profiler`, `updatepack`. `verify-skill-contracts.py` is **clean** on that tree because none of its four rules asks for the citation unless a skill fans out or dispatches — so the doctrine's "every skill" is prose the gate cannot see. The §7b.3 rows for groups C and D are unapplied, and three landed rows do not hold: `prepare-for-coordination`'s track row lacks *deadline · fallback · termination condition · target harness · doorbell status*, `optimize-graph`'s fan-out contract names no deadline or fallback, and `execute-with-coordination` says "fallback" once and "deadline" nowhere. P5's owner-review sentences are delivered as text and sit in a seam file no skill reads.

### Core scenario
A maintainer runs any of the 28 skills in any harness. The skill's first paragraph says what it does with a compiled prompt (CO-S0), its frontmatter says which seat it runs in (CO-S1), and where it dispatches or stops it says so in the layer's verbs (`coord decide request`, `coord board post`) with a deadline and a fallback (CO-S2). `verify-skill-contracts.py` refuses any skill that drops any of it, at authoring time, before the bundle syncs.

### User stories and acceptance criteria

| # | Story | Acceptance (falsifiable) |
|---|---|---|
| US-1 | Every skill cites CO-S0 | `grep -L CO-S0 pack/commands/*/SKILL.md` prints nothing; new lint rule `compile missing` refuses a seat-ful skill without it (self-test fixture + unit test); red-first count on the tree is **10** |
| US-2 | The citation form follows the budget | A skill whose recorded baseline + 2% holds the fixed sentence carries it inline; otherwise `reference/co-s0.md` carries it and Grounding opens with the pointer line *"CO-S0 applies first — the sentence is `reference/co-s0.md`."* — `context-budget.py skills --gate` exits 0 |
| US-3 | A utility skill cites CO-S0 by naming its own touch-point | `also`, `prompts`, `searchprompts`, `auditlog` cite CO-S0 in one sentence that names what they do with a compiled prompt (recompile on a cap raise; `⟲ compiled from <raw id>`; `--raw <id>`; the `kind:compilation` twin). The fixed sentence is not duplicated into them (the existing test's "exactly once" holds for the fourteen) |
| US-4 | A pointer is never dangling | New rule `pointer without reference`: a SKILL.md that names `reference/co-s0.md` whose reference texts do not contain `CO-S0` is refused |
| US-5 | A dispatcher names a deadline and a fallback | New rule `dispatch without deadline`: a skill with a dispatch instruction or a fan-out cap above zero whose union lacks both words is refused; red-first on the tree is **1** (`execute-with-coordination`) |
| US-6 | Seam (b) sentences land verbatim | The three sentences of `seam-p5-to-coordinator.md` (b) are byte-present at the named insertion points; a test pins them |
| US-7 | §7b.3 rows C/D are text that names landed verbs only | `also` recompiles on a cap raise (compiled id on the `pending` row); `prompts`/`searchprompts` name `⟲ compiled from <raw id>` and `--raw <id>` (both verified in `prompt-log.py`); `auditlog` names the Messages view (verified in `docs/audit/index.html`); `dream` names the compile-field miner (`dream.py` section 7); `session-profiler` names SP-27/SP-28 and the `compile` subcommand and reads the unbuilt indicators as `not recorded`; `apply-learnings` offers each plan as `coord decide request --to <target human seat>` with the five fields, `--deadline default` and a fallback; `addpacktorepo`/`updatepack` name the five hook adapters, `!.agents/log/` (D10), `.agents/mail/`, `pack-doctor`'s `doorbells` line and `coord log portable`; `extendaibundle`'s "both tools" invariant becomes every harness surface plus `runs_as`, CO-S0 and the lint |
| US-8 | Landed rows still hold | `prepare-for-coordination` track row gains the five missing fields; `optimize-graph`'s fan-out contract names deadline and fallback; verified rows are cited file:line in the exit evidence |
| US-9 | The lint stays a gate | `--self-test` exits 0 with the new directions; `tests/docs_explorer/test_verify_skill_contracts.py` red-first then green; `clean - 28 skill(s)` on the tree |

### Non-goals
Engine code (`pack-apply.py`, `prompt-log.py`, `session-profile.py`, `dream.py`, `new-capability.py`, hooks); knowledge docs; INSTALL frontmatter; persona cards (§7b.3 names no persona change for these rows); the Copilot mirrors beyond a twin sentence (the coordinator syncs generated surfaces); raising any `skills_baseline` (coordinator-owned).

### Constraints
- Per-skill budget: recorded baseline × 1.02 (`pack/context-budget.json`). Headroom measured before editing (chars): `searchprompts` 93 · `prompts` 128 · `auditlog` 155 · `also` 201 · `apply-learnings` 202 · `dream` 223 · `updatepack` 331 · `session-profiler` 339 · `extendaibundle` 372 · `execute-with-coordination` 406 · `prepare-for-coordination` 408 · `addpacktorepo` 505 · `optimize-graph` 519. The seam (b) text is ≈1,230 chars for `execute-with-coordination`: **it cannot land verbatim under the ratchet without compressing other prose in that skill** — the design names each compression and the rule (no checklist item, citation, command or class id is dropped).
- Command shape (XP): single line, `python3`; `verify-documented-commands.py --root .` stays green.
- No heredocs; a gate never behind a pipe.

## Part B — UX specification
N/A — no user-facing surface changes; the skills are read by an agent.

## Part C — UI specification
N/A.

## Flagged risks & residual unknowns
| Risk | Cheapest next probe |
|---|---|
| Six more `reference/co-s0.md` files (pointer route) keep the CO-S0 sentence off the always-injected surface | the coordinator raises those six baselines by ~60 tokens; one edit moves each inline |
| `pack-apply.py` places only three of the five hook scripts (`reread-guard.py`, `session-start.py`, `mail-doorbell.py`; `pack-apply.py:527`) while the Claude hook JSON it merges names `heartbeat.py` and `owner-review-gate.py` — a consuming repo's settings would point at files never copied | engine seam to the coordinator (exact requirement in the design); the skill text names the five and tells the operator to confirm they landed |
| The §7b.3 indicators for `session-profiler` (messages sent/read/acked, doorbell latency, board read-rate, contracts refused) and `dream`'s refused-dispatch / boundary-correction miners are not in the readers | the skill text reads them as `not recorded`; finding to the coordinator, not engine work here |
| `tools/new-capability.py` writes no `runs_as` or CO-S0 line into a scaffolded skill, so every new skill is red on the lint until edited by hand | seam: the scaffold writes `runs_as: either` and the pointer line + `reference/co-s0.md` |
| `runs_as: Coordinator` on skills that dispatch nothing (`session-profiler`, `dream`, `addpacktorepo`, `updatepack`, `extendaibundle`) asserts a seat they do not use | Inferred; left as landed (the readers' test pins the closed set, not these values); reported |

## Gate record
`GATE spec · 2026-09-19 · Test Architect (hard) · Simplifier (soft) · AI Systems Engineer (contract) — enacted inline, fan-out 0 · verdict: PASS-WITH-CONDITIONS`

| # | Adversary finding (severity) | Resolution |
|---|---|---|
| 1 | Test Architect — "'the ten skills carry CO-S0' is a grep, not a control; nothing refuses the eleventh" (Blocker) | US-1: rule `compile missing` over every skill, red-first on the ten |
| 2 | Simplifier — "a pointer file for a utility skill whose only prose input is a flag is ceremony" (Major, soft) | US-3: utility skills cite CO-S0 with the sentence that names their touch-point; the pointer is used only where a skill takes prose or a plan (six skills) |
| 3 | AI Systems Engineer — "a skill that says 'raw and compiled side by side' before the engine does it leaks an unverified behaviour into the contract" (Major) | US-7: every named verb was read in `--help` or source (`prompt-log.py:104-122, 601, 607`); unbuilt indicators read `not recorded` |
| 4 | Test Architect — "'dispatch without deadline' can be green by accident if no skill matches the dispatcher detector" (Major) | US-5 requires the red-first count on the tree (1) plus a self-test fixture |
| 5 | Simplifier — "compressing P2's coordination skill to fit verbatim P5 text risks dropping an obligation to save a token" (Major, soft) | the design lists each compression with the retained obligation; the test suite that pins skill text (`test_coord_worktree_config.py`, `test_pack_apply.py`) runs before and after |

Authors did not clear their own veto: #1 and #4 were raised by the Test Architect and resolved by the Python Developer's rewrite of US-1/US-5, re-read by the Test Architect.

---
**Handoff:** → `/design-slice` (`docs/design/skill-evolution.md`).
