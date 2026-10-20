---
id: design-agent-focus-controls
title: "Design — Agent focus & scope controls"
type: design
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [design, agent-focus, selfcheck, goal-state, convene-trigger]
links:
  - { to: spec-agent-focus-controls, rel: implements }
  - { to: kb-agent-focus-and-scope-control, rel: relates-to }
review-by: "2027-02-28"
review-suggested: []
summary: >-
  Design for the three agent-focus controls. FC-1: a stdlib `audit-log.py selfcheck --session`
  subcommand (bounded, deterministic, reuses read_log + the PACKO_SUBSTANTIVE set) plus a CT25
  closing-self-assessment directive. FC-2: sharpen CT19 to a fixed three-field goal-state block
  mapped to the audit goal/done_when fields. FC-3: extend the persona convene table for a scope-diff
  trigger. One new command + one test; three directive edits. No new store, no new persona.
---

# Design — Agent focus & scope controls

Implements `spec-agent-focus-controls`. Ceremony matched to **T1** (pack governance + a stdlib CLI
control; no security/PII/money surface). Smallest-correct throughout (Solution-Selection Ladder):
reuse the existing audit reader; add exactly one subcommand and three directive edits.

## FC-1 — Bounded session self-assessment

### Mechanical control: `audit-log.py selfcheck`
- **Interface:** `python audit-log.py --session <id> selfcheck [--json]` (top-level `--session`, as
  the other commands take it; also accept a `selfcheck --session` fallback is *not* added — keep to
  the existing top-level pattern).
- **Reuse (ladder rung 2):** `read_log(root, "audit")` (existing reader); the substantive set is the
  same `{"skill","manual","prompt","command"}` the dream miner uses — **extract it to a module-level
  constant `PACKO_SUBSTANTIVE`** in audit-log.py so the inline check and the offline dream share one
  definition (derive-don't-store: one source for "what is a substantive turn").
- **Algorithm (one deterministic pass):**
  1. entries ← `read_log`; if `--session`, filter to that session; else use all (with a note).
  2. `subst` ← entries with `kind ∈ PACKO_SUBSTANTIVE`.
  3. `gaps` ← `subst` without a truthy `done_when`; `have` ← `subst` with `done_when`.
  4. Print: the count and %, each **gap** (shortname — "no goal-state recorded"), then each **have**
     as a `done_when → summary` **review pair** (never a verdict).
  5. Exit **0** always (advisory, like `suggest`); print the clean line
     "all N substantive turns recorded a goal-state" when `gaps` is empty.
- **Boundedness (AC-1.3):** no network, no model, no loop, no second pass; deterministic on identical
  input. Degrades to "not recorded" for absent fields (never invents a value — IO8).
- **`--json`:** emit `{session, substantive, gaps:[...], review:[{done_when,summary,shortname}], ...}`.

### Directive: CT25 (the closing self-assessment)
Add **CT25** to `communication-and-task-discipline.md` §5 (the front-matter section, which already
holds CT19–CT24), defining the **bounded closing self-assessment** as standing behaviour:
- one pass at close: re-read the goal state (CT19); confirm each substantive turn recorded a
  goal-state (or that gap *is* the finding); map the realised work to Done-when; diff against
  Not-in-scope; **stop** — no re-plan, no "improve", end with the E18 Completed/Remaining/Next close;
- explicitly: **one pass, self-terminating** — a second reflection pass is the degenerating-reasoning
  trap and is forbidden; the mechanical `selfcheck` is the rung-2 aid, this directive the rung-3 habit.

## FC-2 — Structural goal-state opening (sharpen CT19)
Edit **CT19** in `communication-and-task-discipline.md` to specify the opening as a **fixed
three-field block** rather than free-form prose:
```
Goal:         <the requested outcome, one line>
Done when:    <a terminal, checkable condition>
Not in scope: <what this turn will not touch>
```
and state that these map **1:1 to the audit `goal` and `done_when` fields** (AL5b), so presence is
**mechanically detectable** by `selfcheck` and the dream PACK-O miner. No behavioural change to
CT19's intent (a gap en route is still a finding, not a new goal) — the change is *form*: prose →
structure, which is the whole point (proposal Q2). Managed-block CLAUDE/AGENTS summaries of CT19–CT24
are re-pasted by sync; the source edit is in the knowledge doc.

## FC-3 — Sharpened convene trigger (persona-audit §8.7)
Edit the **convene-when** table row for the **Simplifier** (and note it for the **Tech Lead**) in
`persona-audit.md` §8.7 to add the scope-diff trigger:
> Simplifier — convene when the change adds an abstraction, layer, config option, dependency,
> pattern, or speculative generality — **or when a turn (especially an autopilot turn) touched
> anything in its declared Not-in-scope, or its realised work exceeded its stated Goal (scope
> inflation)**.

This is a directive/trigger edit only (personas convene at gates — the proposal's Q1 note that this
is lower-leverage than FC-1/FC-2 is recorded; it is the cheap increment, not a new persona).

## Test plan (red-first)
`tests/docs_explorer/test_audit_selfcheck.py` (subprocess the **generated** copy, temp `--root`, matching
`test_audit_log.py` conventions):
- **T1 (AC-1.1):** a session with a substantive turn missing `done_when` → that turn is reported as a
  gap; a `kind:"read"`/trivial turn is **not** reported. *Red on unfixed:* command does not exist → fail.
- **T2 (AC-1.2):** a substantive turn *with* `done_when` → its `done_when → summary` pair is surfaced;
  output contains **no** "PASS/FAIL"/verdict token on scope.
- **T3 (AC-1.3):** identical input run twice → identical output (deterministic); empty gaps → the
  clean "all N substantive turns recorded a goal-state" line and exit 0.
- Directive edits (FC-2, FC-3) are prose; their "test" is the consistency gate (sync + verify-bundle)
  and the self-verification checklists in the docs — no unit test (they are not executable logic).

## Failure-mode analysis (FC-1 control)
| Mode | Disposition |
|---|---|
| Empty/absent audit log | `read_log` returns [] → "no substantive turns" clean exit 0 (guard). |
| Entry missing `done_when` | that is the *signal* — reported as a gap, not an error. |
| Entry missing `summary` | review pair shows `summary=''` (degrade to empty, never invent — IO8). |
| Unknown `--session` | zero substantive turns → clean "no substantive turns for session X" exit 0. |
| Corrupt log line | `read_log` already tolerates/So it is handled upstream (FR-052); selfcheck inherits it. |

## Adversarial analysis (STRIDE-lite)
Trust boundary: the audit log (`docs/audit/audit-log.jsonl`, or the `.agents/log` fallback from `resolve_default_root`), which any agent or human with write access can append to → `audit-log.py selfcheck` → stdout, read by a model, a human or a CI step. FC-2 and FC-3 are directive text only and cross no runtime boundary; repo write access governs them like any other pack text. `selfcheck` writes nothing: `cmd_selfcheck` has no append call (`pack/scripts/audit-log.py:1242-1327`, Verified). Its only subprocess is read-only `git` under `--since`. It makes no network or model call.

| Boundary | Threat | Disposition | Control, evidence and test |
|---|---|---|---|
| Audit log → `selfcheck` | **T**: a malformed or hand-broken line drops a substantive turn, so `--gate` passes without it | mitigate (partial) | `read_log` skips the line, warns on stderr and records it in `LOG_READ_SKIPS` (`audit-log.py:524-543`). `cmd_selfcheck` never reads `LOG_READ_SKIPS`, so the gate can pass while lines are skipped (Verified by reading `:1242-1327`). `audit-log.py verify` is the check that fails on it (`:1131-1151`). No selfcheck test covers a corrupt line. |
| Audit entry fields → `--gate` | **S/T**: an agent writes its own `done_when`, `tier` and `fan_out`; filler text satisfies the gate | accept | The gate checks presence only (`:1250-1254`); the design states it is "never a verdict". Transferred to repo write access and PR review on `main`. No test, by design. |
| `--since <ref>` → `git show` | **T/E**: the ref is passed to git with no `--end-of-options`, so a value that starts with `-` is read as a git option | accept (Inferred) | `ids_at_ref` passes `"<ref>:<path>"` as one argv item, no shell (`:481-499`), so there is no command injection. A probe with `--since=--output=<tmp>/planted` on Windows wrote no file (Verified 2026-10-19; the appended `:<path>` makes the name invalid there). On POSIX git may write diff output to that path (Inferred, not run). The value comes from the operator's own command line, never from log content. No test. |
| Unreadable `--since` base → `--gate` | **T**: a missing ref or a shallow clone weakens the ratchet | mitigate | `ids_at_ref` returns `None` and `cmd_selfcheck` then filters nothing (`:1255-1260`), so the gate reports more, not less. Test: `test_gate_since_grandfathers_historical_but_catches_new` (`tests/docs_explorer/test_audit_selfcheck.py:119`). |
| stdout → model reader | **T** (prompt injection): `done_when` and `summary` text from earlier turns re-enters a model's context | accept | Text mode truncates to 60 and 80 characters (`:1321-1324`); `--json` prints the full strings, JSON-escaped (`:1267-1280`). No control-character strip, unlike `coord-core.py` `_safe`. The text is committed repo content, the same trust as any file the model reads. No test. |
| Audit log size → run time | **D**: the whole log is loaded into memory on every run | accept | `read_log` has no cap (`:524-543`). Growing the log needs repo write; the log is append-only by design. |

**Design vs code:** the design says `selfcheck` "exits 0 always". The code now has `--gate`, which exits 1 on a gap, a tier gap or an over-cap fan-out (`:1261`, `:1280`, `:1327`; INSTALL.md revision entry "GOAL-STATE GATE"). The tables above analyse the code.

## Privacy analysis (LINDDUN-lite)
| Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|
| Audit log → `selfcheck` (read) | D: the log holds each substantive turn's verbatim prompt and its session id; `selfcheck` reads every entry | mitigate | Output carries only `shortname`, `id`, `done_when`, `summary`, budget counts and fan-out numbers (`cmd_selfcheck`, `audit-log.py:1263-1324`). The `prompt` field is never printed (Verified by reading). | No new store; `selfcheck` writes nothing. The log keeps its own Git retention. |
| `done_when` / `summary` → stdout or CI log | I: free text written by an agent may quote a path, a name or a pasted value | accept | Truncated to 60 / 80 characters in text mode; full in `--json`. No scrub. The same text is already committed in the log. | Terminal only, or the CI host's log retention where a repo wires `--gate` into CI. |
| `--session <id>` filter | L: links one session's turns together | accept | By design. Session ids are pseudonymous work identifiers already in the log. | As the log. |
| FC-2 goal-state block → audit `goal` / `done_when` fields | U/I: every substantive turn now records its goal text in a committed store | accept | Work description, not a personal-data category. The verbatim prompt is already recorded (AL5b), so FC-2 adds structure, not a new data class. | Git retention of `docs/audit/audit-log.jsonl`; the only rights path is a history rewrite. |

No personal-data category is introduced. No egress: `selfcheck` imports no network module and calls no model. Non-compliance: nothing beyond the audit log's existing posture.

**Security and privacy review (2026-10-19):** both sections were written from the code as it is now, not from the plan, to close the gap rows in `docs/security/threat-model.md` §4 and `docs/security/privacy-review.md` §5.

## Blast radius & rollback
Pure-additive: one new subcommand (no change to existing commands), one extracted constant, three
directive edits, one test. Rollback = `git revert`. No store, schema, CI-behaviour, or runtime config
changed. Generated copies (`docs/ai-forward-pack/scripts/audit-log.py`) regenerate via sync.

## Change-surface list (E7)
source `pack/scripts/audit-log.py` (add `PACKO_SUBSTANTIVE`, `cmd_selfcheck`, subparser, dispatch) →
generated copy (sync) → test `tests/docs_explorer/test_audit_selfcheck.py` → directives
(`communication-and-task-discipline.md` CT19+CT25, `persona-audit.md` §8.7) → managed blocks (sync).
No wire/DTO/UI surface (CLI only).
