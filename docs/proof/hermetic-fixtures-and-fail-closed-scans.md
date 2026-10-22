---
id: proof-hermetic-fixtures-and-fail-closed-scans
title: "Proof Pack — hermetic git fixtures and fail-closed corpus scans"
type: proof-pack
status: in-review
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [proof, test-hermeticity, fail-closed, docs-graph, bootstrap, TEST-C, CTRL-G]
links:
  - { to: spec-hermetic-fixtures-and-fail-closed-scans, rel: implements }
  - { to: design-hermetic-fixtures-and-fail-closed-scans, rel: implements }
  - { to: investigation-surface-limit-flake, rel: relates-to }
  - { to: investigation-bootstrap-release-tag-collision, rel: relates-to }
review-by: "2027-04-20"
summary: >-
  Executed evidence for the three slices. Bootstrap fixtures no longer inherit tags from the
  developer checkout, docs-graph counts every surface before reading it, and every corpus scan
  in pack/scripts reports what it could not read. Each control and fail-first test was seen red
  on the pre-fix code.
---

# Proof Pack: hermetic git fixtures and fail-closed corpus scans

- **Change:** `fix/hermetic-fixtures-fail-closed-scans` (INSTALL revision 118)
- **Spec / design:** `docs/specs/hermetic-fixtures-and-fail-closed-scans.md` ·
  `docs/design/hermetic-fixtures-and-fail-closed-scans.md`
- **Investigations:** `docs/investigations/bootstrap-release-tag-collision.md` ·
  `docs/investigations/surface-limit-flake.md`
- **Tier:** T1 (test fixtures and gate behaviour; no runtime data, identity or contract change)
- **Author / date:** Claude Code (Opus 5.5) for @timianmalloo, 2026-10-22

## Claims & evidence

Red is the named pre-fix code; green is this branch. All observed on Windows, Python 3.12.10.

| # | Claim | Oracle | Red (observed) | Green (observed) |
|---|---|---|---|---|
| 1 | A fixture clone of the repo carries no tags from the developer checkout | `test_clone_source_inherits_no_refs_from_its_origin` | `git tag --list` returned `preview\nv2026.10.19.4` | empty |
| 2 | The bootstrap tests pass with an ambient `preview` tag present | scratchpad demo: pre-fix vs fixed body, `preview` tag planted on the fixture upstream | pre-fix body FAILED (`MERGE` not found) | fixed body PASSED |
| 3 | No test reads a named ref from the developer checkout (TEST-C) | `test_hermetic_git_fixtures.py` AST control | 7 sites on `origin/main`, plus `test_bootstrap.py:968` once ref reads were added | 0 |
| 4 | A read fault cannot lower the surface count below `SURFACE_LIMIT` | `SurfaceAdmissionTests` (open, lstat, source-change faults) | 11 of 11 fail-first tests red after only the parameter was added | 70 of 70 in `test_docs_graph.py` |
| 5 | An unreadable surface, an unlistable directory and a non-UTF-8 surface are findings, and `validate` fails on them | `SurfaceAdmissionTests` validate/derive tests | red (as row 4) | green |
| 6 | `validate` stops above the surface limit | `test_validate_fails_closed_above_the_surface_limit` | `origin/main` script: 1 failed | passed |
| 7 | A file of exactly the 256 KiB cap is decoded in full | `test_a_file_of_exactly_the_cap_is_decoded_in_full` | pre-round-3 script: failed (cut byte swallowed) | passed |
| 8 | No corpus scan in `pack/scripts` skips an item silently (CTRL-G) | `test_fail_closed_scans.py` AST control | 42 sites on `origin/main`; 12 more once extended to `glob`, `Path.walk` and empty assignments | 0 |
| 9 | Each gate fails on an unreadable file and still skips a gone one | `GatesFailClosedTests` (`FAIL_CLOSED_SCRIPTS=<pre-fix tree>`) | 12 of 12 failed on `HEAD` copies; 3 of 3 new listing tests failed | 18 of 18 pass |
| 10 | The listing rewrites list the same files as before | xaml and documented-commands parity tests | pass on both (characterization, not fail-first) | pass |

## Test coverage of the boundary set

| Boundary | Covered by |
|---|---|
| File absent (`FileNotFoundError`, `NotADirectoryError`) — skipped silently, as before | every `GatesFailClosedTests` case runs the gone-file path |
| File present but unreadable (`PermissionError`) | per-gate fault injection; surface open/lstat faults |
| Directory present but unlistable | `_unlistable` (patches `os.scandir` and `os.listdir`); docs-graph walk tests |
| Source changed during read | `test_a_source_change_during_read_cannot_lower_the_surface_count` |
| Count N = limit, N = limit + 1 with one fault | surface limit tests |
| Title cap: cut inside a character (valid) vs exactly the cap (complete) | the two cap tests |
| At most one open per surface (no retry) | `test_at_most_one_open_per_admitted_surface`; `opens <= 1` per gate |

## Failure modes addressed

| Mode | Disposition | Proof |
|---|---|---|
| Fixture inherits a release tag, so `git tag` collides | `--no-tags --no-hardlinks` clone | rows 1–3 |
| Transient read fault lets 101 surfaces pass as 100 | count on admission | row 4 |
| Gate passes a file it never read | finding and exit 1 | row 9 |
| `rglob`/`glob` read an unlistable directory as empty | `os.walk(onerror=)` or `iterdir` | rows 8–9 |
| `pack-apply` reads an unreadable file as absent and overwrites it | `read` raises; `main` stops with a message | row 9; review round 3 |

## Threats addressed (adversarial analysis)

| Boundary | STRIDE | Disposition |
|---|---|---|
| A file a gate cannot read (permissions, a lock) | Tampering / Repudiation: content escapes the gate | reported, not skipped |
| Developer refs leaking into tests | Tampering of test inputs | hermetic origins |

## Privacy findings addressed (LINDDUN-lite)

N/A — no personal data is read or written.

## UI states & floors proven (if the component has an interface)

N/A — no user-facing interface.

## Testing Strategy directives applied

- Regression test fails on the bug first: rows 1, 2, 4, 6, 7, 9.
- Fault injection at the I/O boundary: rows 4, 5, 9.
- Static control for the class: rows 3, 8.
- Characterization before a rewrite: row 10.

## Verification commands

```
python -m pytest tests/docs_explorer/test_bootstrap.py tests/docs_explorer/test_hermetic_git_fixtures.py
python -m pytest tests/docs_explorer/test_docs_graph.py tests/docs_explorer/test_fail_closed_scans.py
pwsh tools/verify-bundle.ps1
```

## Flagged risks / residual unknowns

- **Behaviour change for consumers.** A file that exists but cannot be read now fails
  `validate` and the scanning gates. The INSTALL revision-118 deploy note says so.
- **Limit errors outside `context` exit with a traceback** (non-zero, fail-closed). This was
  already true of `derive` and of `SCAN_LIMIT_EXCEEDED`; `validate` now joins them. Follow-up,
  not fixed here.
- **What triggered the original surface fault is still unknown.** The next occurrence names the
  file and the error.
- **Revision 118 is also used by `feat/installrayfin`.** Whichever merges second renumbers.

## Status & next action

| | |
|---|---|
| **Completed** | Slices 1–3; pre-merge review rounds applied |
| **Remaining** | None in scope |
| **Best next action** | Merge |

## Gate record

- **Design gate:** Patterns Expert + Simplifier PASS; Test Architect BLOCK, all 7 resolved.
- **Pre-merge:** Python Developer PASS-WITH-CONDITIONS, all applied; Test Architect
  PASS-WITH-CONDITIONS, hard veto cleared once the control covered `glob` and `Path.walk`
  (row 8). Details in the design's gate record.
