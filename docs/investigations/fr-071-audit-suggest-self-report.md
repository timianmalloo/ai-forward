---
id: investigation-fr-071
title: "Investigation - FR-071: audit-log suggest self-reports its own closeout"
type: doc
status: resolved
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [investigation, audit-log, suggest, false-positive, FR-071]
links:
  - { to: forensic-review-rev53-backlog, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
  - { to: audit-log, rel: documents }
review-by: "2027-02-28"
review-suggested: []
summary: >-
  audit-log.py `suggest` lists every commit since the last change-log entry with no filter,
  so it surfaces bookkeeping/closeout commits (including the very commit that recorded a change
  entry) and floods with routine commits - contrary to its spec (audit-and-change-log.md CL3),
  which specifies surfacing only commits whose message signals a decision. Verified root cause:
  a missing message filter and a missing exclusion of logging commits. Fix: filter to CL3 decision
  signals and exclude commits that wrote an audit .jsonl. Class SELF-REPORT registered.
---

# Investigation - FR-071: `audit-log.py suggest` self-reports its own closeout

## Symptom
The rev49 forensic review found that `audit-log.py suggest` "self-reports the commit that records
its own closeout" - it recommends change-logging a commit that was itself the act of logging.

## Reproduction (Verified)
Ran `python pack/scripts/audit-log.py suggest` at HEAD `2af47ce`. The last change-log entry is
`cc1f4ec` ("Coord collaboration mode second slice"), so `suggest` listed **all 13 commits since**,
including pure documentation/bookkeeping commits (`docs(backlog): record ...`, `chore(...)`,
`fix(...)`, `test(...)`) that are not decisions and, in the closeout case, commits that recorded a
change entry. The tool floods and self-reports.

## Timeline / mechanism
1. A change-shaping skill runs `audit-log.py change` -> records `git.after = X` (HEAD *at the moment
   `change` runs*, i.e. **before** the closeout commit that will contain the entry). `cmd_change:454`.
2. The skill commits; closeout commit `Y` (a child of `X`) contains the new change-log line and
   touches `docs/audit/change-log.jsonl`.
3. Later, `suggest` computes candidates as `commits_between(last_after=X, HEAD)` =
   `git log X..HEAD` - which is **inclusive of `Y`** (`commits_between:275`).
4. `cmd_suggest:604-605` appends **every** commit in that range with **no filter**, so `Y` (the
   logging closeout) is reported as an "unlogged meaningful change" -> self-report. Every routine
   commit in the range is reported too -> flood.

## System map
`suggest` computes `pending = commits since last change entry`. It de-dupes the *ADR/notes* branch
against existing change entries (`cmd_suggest:611-617`) but applies **no filter at all** to the
*commit* branch - neither the spec's decision-signal filter nor an exclusion of the logging commits
that are the act it is reminding you to perform.

## Verified root cause (necessary + sufficient, grounded in the spec)
**`cmd_suggest` lists every commit in `last_change.git.after..HEAD` unfiltered, contrary to
`audit-and-change-log.md` CL3**, which specifies the commit heuristic as "a commit ... whose message
signals a decision (`feat`, `BREAKING`, `migrate`, `arch`, `decision`, `adr`)", and never excludes
commits that are themselves logging closeouts.
- **Sufficient:** with no filter, bookkeeping commits ARE listed - reproduced (`docs(backlog): ...`,
  `docs(review): ...` surfaced by the real `suggest` run).
- **Necessary:** applying the CL3 decision-signal filter AND excluding commits that wrote an audit
  `.jsonl` removes the bookkeeping/self-report commits while retaining genuine unlogged decisions -
  proven by the failing-first regression test (`test_audit_suggest.py`): on the unfixed code the
  logging-closeout and routine commits surface (test red); after the fix only the `feat` decision
  surfaces (test green).

## Competing causes ruled out
- *"`git.after` off-by-one boundary alone"* - the range's inclusivity of `Y` contributes, but a
  perfect boundary would still self-report a **bundled** decision+change commit, and would not stop
  the flood. The missing filter is the systemic cause; the boundary is a secondary contributor the
  logging-commit exclusion also covers. (Ruled out as *the* cause; retained as contributor.)
- *"`read_log` selects the wrong last entry"* - no; `last_after` is correctly the last change
  entry's `git.after` (`cmd_suggest:597-600`).

## Specific fix (systemic, spec-conformant)
In `cmd_suggest`, filter the commit candidates (both the `last_after..HEAD` branch and the
`elif head` last-N branch):
1. **CL3 decision-signal filter** - keep only commits whose subject matches
   `\b(feat|BREAKING|migrate|arch|decision|adr)\b` (case-insensitive). Removes the routine-commit flood.
2. **Logging-closeout exclusion** - drop any commit that modified an audit `.jsonl`
   (`docs/audit/*.jsonl`); such a commit *is* the logging action, never an unlogged change. Removes
   the self-report even for decision-worded logging commits.

Extracted as pure-ish helpers `_suggests_decision(subject)` and `_is_logging_commit(sha, root)` for
testability. Blast radius: one advisory command; no writes, no other caller. Rollback: `git revert`.
Regression test seen failing on the unfixed code first.

## Generalization
- **Failure class - SELF-REPORT:** *a discern/reminder tool whose candidate set includes its own
  bookkeeping* - it computes "pending = items since the last log mark" but neither filters to the
  spec's signal nor excludes the commits that ARE the logging action, so it re-surfaces already-logged
  or non-meaningful work (including the commit that recorded the last entry).
- **Siblings swept (Verified):** the `commits_between` / `last_after` "since the last log entry" shape
  is **unique to `cmd_suggest`** - no other pack script has it. `dream.py`'s register miner already
  de-dupes (`seen` set, `dream.py:184/247`), so it does not self-report. `docs-graph.py`'s
  `review-suggested`/freshness is frontmatter-cleared, a different mechanism. **No siblings found.**
- **Broader solution (reusable rule):** a discern tool's candidate set must **subtract the actions
  that satisfy the item** - here, exclude logging commits and filter to the specified signal. Encoded
  as the control below.
- **Markers harvested (CI9):** `audit-log.py` carries **no** `simplify:`/`assume:` markers - nothing
  predicted this in writing.

## Phased repair plan
| Phase | Scope (code + tests) | Failure mode eliminated | Validation | Dependencies |
|---|---|---|---|---|
| 1 | `cmd_suggest` filter (`_suggests_decision` + `_is_logging_commit`) in `pack/scripts/audit-log.py` + regression test `tests/docs_explorer/test_audit_suggest.py` | Self-report of logging closeouts; routine-commit flood | Test red on unfixed code, green after; real `suggest` no longer lists bookkeeping commits | none |
| 2 | Register defect class **SELF-REPORT** in `docs/lessons/defect-classes.md` with the phase-1 test as its control | The class recurring undetected | Test observed failing on unfixed code | Phase 1 |

## Residual risk
The decision-signal filter matches on the commit **subject** (where conventional-commit type lives),
not the full body; a `BREAKING CHANGE:` trailer in the body without a subject signal would not
surface. Accepted: `suggest` is advisory, and the subject is the documented signal locus (CL3).
**What would change the diagnosis:** if a self-report were observed for a commit that did *not* touch
an audit `.jsonl` and whose subject *did* signal a decision - none exists (the logging closeout always
touches change-log.jsonl).

## Gate record
- Test Architect (hard veto): **PASS** - regression test observed failing on unfixed code, green after.
- SRE / Distributed Systems: **PASS** - root cause explains the flood and the self-report; advisory-only, no runtime effect.
- Security: **N/A** - no trust boundary, secret, or identity scope touched.
