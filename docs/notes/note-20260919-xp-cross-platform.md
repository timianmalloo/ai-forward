---
id: note-20260919-xp-cross-platform
title: "XP cross-platform residue: documented commands made shell-neutral, the default-branch tests made honest, the session-id sanitiser cut as a seam patch"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, cross-platform, plat-a, plat-b, xp-track, coordination-p3-p5-p8]
links:
  - { to: plan-cross-platform-readiness, rel: implements }
  - { to: investigation-cross-platform-readiness, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Track XP of coordination-p3-p5-p8 (T1, fan-out 0). Every documented command under pack/
  is now a single line, unchained and `python3`; a gate (`verify-documented-commands.py`) and
  its test pin the shape and were red-first at 26 findings on 24 lines; the three
  `test_coord_derived.py` tests read the default branch the machine chose and are green under
  both `init.defaultBranch=main` and `=master`; T-2 and T-3 were found already fixed at a01ed77
  and re-proven by execution; the AGENT_SESSION sanitiser travels as
  docs/coordination/seam-xp-to-p3.patch because P3 owns coord-core.py.
---

# XP — cross-platform residue (decisions below ADR weight)

Base `a01ed77`, branch `fix/xp-cross-platform`, plan row **XP** of `coordination-p3-p5-p8`.
Grounding: `docs/plans/cross-platform-readiness.md` P4/P5; `docs/investigations/cross-platform-readiness.md`
XS-01..25, T-1/T-2/T-3, DC-207, PLAT-A/PLAT-B.

## Re-count (investigation vs observed at a01ed77)

| Class | Investigation | Observed (gate, fenced command blocks) | Observed inline (prose backticks, outside the gate's contract) |
|---|---|---|---|
| backslash continuation | 8 commands | **10 commands / 16 lines** — the 8 cited + `templates/threat-model.template.md:27`, `templates/privacy-review.template.md:27` | 0 |
| ` && ` chain | 4 | **2** (`code-knowledge-graph.md:129`, `obsidian-lens.md:128`, both also continuations) | **4** — `extendaibundle/SKILL.md:71`, `addpacktorepo/SKILL.md:155`, `adapters/copilot/prompts/addpacktorepo.prompt.md:7`, `templates/documentation-bundle.template.md:120` |
| bare `python` | 16 (10 unintended) | **8** — `apply-learnings/SKILL.md:34,36,43,49`, `INSTALL.md:298-300`, plus `INSTALL.md:215` (the labelled Windows twin, allowlisted) | **6** — `dream/SKILL.md:22,30`, `ui-design/reference/flow.md:28`, `extendaibundle/SKILL.md:23,61,64` |

Red-first gate output: `26 finding(s) on 24 line(s) - 2 and-chain, 8 bare-python, 16 continuation`.
The inline sites are outside the gate's contract (it scans fenced command blocks) and were
rewritten by hand; the residual risk that a new inline `&&` slips past the gate is recorded below.

## Decisions

1. **Gate, not only a test.** `pack/scripts/verify-documented-commands.py` holds the scanner and
   the scan contract; `tests/docs_explorer/test_documented_commands_portable.py` loads it, asserts a
   clean scan, runs its self-test (DC-104) and pins the contract constants. `run-verify-gates.py`
   discovers `verify-*.py` under `docs/ai-forward-pack/scripts/` — the synced copy — so the gate
   is live once `sync-pack.ps1` runs (coordinator, at the landing); `verify-bundle.ps1` needs an
   explicit line (its gates 1b–1e are each named). Both are handed to the coordinator.
2. **Shebang blocks are files.** A fenced block whose first line is `#!…` is a program (DC-207:
   a file, then a run), not a typed command; `[ -n "$a" ] && [ -z "$b" ]` inside one is legitimate
   `sh` and is skipped whole rather than allowlisted line by line.
3. **`portable-ok: <reason>`** is the allowlist marker, one line, reason mandatory (a marker with
   no reason is its own finding). Single use today: `INSTALL.md:215`, the labelled Windows form
   beside its `python3` twin.
4. **Single lines over separate lines** for the long `audit-log.py` and `conductor-join.py`
   commands: the argument sets are one invocation, and splitting them would invite an agent to
   run half. The two `derive && validate` pairs became two lines — two commands.
5. **Inline `&&` chains** became "run in order: `a`, `b`, `c`" — three commands, no separator,
   because `;` runs `push` after a failed `commit` and `&&` does not parse in PowerShell 5.1.
6. **T-1 fix reads the branch back** (`git symbolic-ref --short HEAD` after `git init`) rather
   than forcing `-b main`: the test then agrees with whatever the machine's `init.defaultBranch`
   is, and the proof runs the suite under both values via `GIT_CONFIG_PARAMETERS`.
7. **T-2 / T-3 were already fixed** at a01ed77 (`test_run_evals.py:187-191` resolves both sides;
   `audit-log.py:411-424` `ids_at_ref` realpaths both sides with the T-3 comment). Nothing to
   change; both re-proven green by execution on this Mac (`/var` → `/private/var`).
8. **Sanitiser as a seam.** `session_id_error()` — `[A-Za-z0-9._-]+`, not `.`/`..`, `fullmatch` so
   a trailing newline is refused — plus its gate in `main()` after `_identity()` (before `hook`, so
   no writer is reachable with a bad id) and on `worktree --session`. Delivered as
   `docs/coordination/seam-xp-to-p3.patch` (32 + 87 lines, `git apply --check` clean against this
   tree); this branch's `coord-core.py` equals base. An empty `AGENT_SESSION` still falls to the
   identity gate (`COORD-NOT-CHECKED-IDENTITY`, exit 4), unchanged.
9. **CT27 remedy** appended in the same sentence: PowerShell has no `pipefail` — the gate on its
   own line, then `if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }`.
10. **Scaffold sentence** added to `tools/new-capability.py`'s SKILL template "Documentation &
    discoverability (last action)" block (there is no "Audit (last action)" block in the scaffold —
    the plan's name for it was inexact): the Windows interpreter word and `pack-doctor`'s check.

## Not done (out of row, handed over)

- DC-207 promotion to the `execute-with-coordination` dispatch rule — a semantic skill edit (P8).
- `coord-mail.py` / `coord-board.py` read `AGENT_SESSION` themselves; the sanitiser covers only
  `coord-core.py`'s paths. Finding for P3/P5.
- The two whole-suite failures (`test_codex_surface`, `test_pack_apply::test_source_repo_is_already_current`)
  are the source-vs-installed drift that `sync-pack.ps1` closes; not run here by contract.
- Pre-existing `ruff` findings (`test_coord_derived.py` E702 ×17, `new-capability.py` F541 ×11,
  `coord-core.py` ×7) are unchanged from base; no new finding was added.

## Residual risk

An inline (backtick) `&&` chain or bare `python` in prose is outside the gate's contract; the
gate scans fenced command blocks only, by design (prose mentions `a && b` legitimately). If the
class recurs inline, extend the contract to backtick spans that start with a known command word.
