---
id: investigation-surface-limit-flake
title: "Investigation - the HTML surface limit fails open when one file is transiently unreadable"
type: doc
status: draft
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [investigation, flaky-test, docs-graph, fail-open, CTRL-G]
links:
  - { to: defect-classes, rel: relates-to }
review-by: "2027-02-28"
review-suggested: []
summary: >-
  test_html_surface_discovery_fails_closed_above_surface_limit failed once in two full gate runs.
  discover_html_surfaces counts only files whose title it could read, and drops any file that raises
  an OSError without reporting it. One transient read failure among 101 files leaves 100, so the
  fail-closed limit never fires. The mechanism is verified by fault injection; the transient's source
  (likely an on-access scanner) is inferred. Class CTRL-G registered; phased repair proposed, not applied.
---

# Investigation: surface-limit-flake — a fail-closed limit that a transient read error turns off

- **Status:** Mechanism verified; trigger inferred. Fix proposed and awaiting human review. Nothing implemented.
- **Severity / tier:** T1. The flake is a false red. The same mechanism is a product defect:
  `docs-index.js` can silently lose a surface, and the limit can fail open.
- **Reported by / date:** maintainer, 2026-10-22 ("the flaky test").
- **Related spec:** `pack/scripts/docs-graph.py` `discover_html_surfaces`, `SURFACE_LIMIT = 100`;
  the fail-closed scan limits (exit code 4, `*_LIMIT_EXCEEDED`).

## Symptom

`tests/docs_explorer/test_docs_graph.py::DocsGraphTests::test_html_surface_discovery_fails_closed_above_surface_limit`
failed with `AssertionError: DocsGraphError not raised` (`test_docs_graph.py:438`) in the first
full serial gate run on 2026-10-22. It passed in the second full run and in every isolated run.

## Reproduction

| Run | Result |
|---|---|
| Full serial gate run 1 (~80 min, machine under load) | **Failed** |
| Full serial gate run 2 (80 min) | Passed |
| Serial prefix run, every test file up to `test_docs_graph.py` in one process (72 min) | Passed (its one failure was the bootstrap test) |
| Test file alone (56 tests) | Passed |
| The scenario 480 times across 12 parallel processes, with every read error traced | 480/480 raised; 0 files dropped |
| **Fault injection:** one `PermissionError` (Windows sharing violation) on `os.open` of `tool-050.html` | **Not raised, 100 surfaces returned**, deterministically |
| **Fault injection:** one `OSError` on `os.lstat` of one file (`_safe_path_kind`, before the count; the adversarial reviewer's probe) | **Not raised, 100 surfaces returned**, deterministically |

## Timeline

There is no change correlated with the onset. The test and `discover_html_surfaces` are unchanged
on this branch. The one failure happened during the longest, most loaded run. That fits an
environmental transient, not a code change.

## System map

The function walks the directory. For each `.html` file:
1. `_safe_path_kind` (`lstat`). An `OSError` makes it return False, and the file is skipped without a report.
2. The limit check: `len(candidates) >= SURFACE_LIMIT` (`docs-graph.py:668`).
3. `_surface_title`, which opens and reads the file. An `OSError`, `UnicodeError` or
   `_SourceChangedError` makes it return None, and the file is skipped without a report
   (`docs-graph.py:598`, `:676`).
4. Append to `candidates`.

The limit counts **successes**, and failures are skipped silently, so any transient failure takes
an item out of the count. The markdown path, `_markdown_candidates` (`docs-graph.py:501-541`),
counts admitted paths *before* reading, and records every rejected path as a `problem`. The HTML
path is the outlier.

## Hypotheses considered

| # | Hypothesis | Evidence | Verdict |
|---|---|---|---|
| H1 | A transient read failure drops one file, so the limit is never reached | Injection reproduces the exact symptom. Isolated runs show no drops, which fits a rare transient. | **Mechanism Verified; trigger Inferred** |
| H2 | Earlier tests leak in-process state (monkeypatched `os`, `tempfile`, `HTMLParser`) | No test in `tests/docs_explorer` patches `os.open` (grep). Run 2 and the serial prefix run used the same order and passed. | Not supported |
| H3 | Parallel workers race on a shared temp dir | Gate 3 ran serially (no `xdist` installed). The test uses its own `TemporaryDirectory`. | Ruled out |
| H4 | The limit constant or the off-by-one changed | `SURFACE_LIMIT = 100`, check `>=`, 101 files. Deterministic, and passes in isolation. | Ruled out |

## Verified root cause

`discover_html_surfaces` enforces a fail-closed limit over the count of files it *admitted and
read successfully*, and drops a file without reporting it at three fault points:
- `lstat` in `_safe_path_kind`;
- the open or read in `_surface_title`;
- a directory listing that `os.walk` (no `onerror`) skips silently.

**Sufficient:** one injected fault at either of the first two points turns the raise into a
silent return of 100 surfaces. **[Verified]** The third is inferred from `os.walk`'s documented
default (errors ignored).
**Necessary [Inferred]:** without a fault the result is deterministic (480 of 480 raise), but
that does not show that run 1 hit a fault, or which one. The three fault points are competing
triggers with the same symptom (adversarial finding 6). The likely source is an on-access scanner
(Defender or the search indexer) touching freshly written files, but that is unconfirmed: the
drop leaves no record, and that gap is itself part of the defect.

## Causes ruled out

H2 to H4 (above).

## Specific fix(es) for this instance

- **Change:** count every `.html` candidate the walk yields, before `lstat` or reading. Record
  every failure at each of the three fault points as a visible `problem` that names the
  exception class, and pass an `onerror` to `os.walk` that does the same. Then the limit is
  deterministic, and a dropped surface shows up in `docs-graph.py validate` and gate 9c. The same
  `onerror` gap exists in `_markdown_candidates` (`docs-graph.py:505`), so the "model" path needs
  it too.
- **Why it reaches the root:** the verdict no longer depends on I/O luck, and the failure becomes
  measurable. That closes the "drop leaves no record" gap above (instrumentation over inference).
- **Blast radius:** `docs-index.js` surface entries. A surface that cannot be read becomes a
  reported problem instead of a silent omission.
- **Decision for the human:** should an unreadable surface fail `derive` (fail-closed, consistent
  with the markdown path), or warn and carry on? The recommendation is to record it as a `problem`,
  matching the markdown path.
- **Rollback:** revert the one function.
- **Regression tests (fail-first), one per fault point:**
  - inject a fault on `os.open`, `os.lstat`, and the walk's directory listing, each once for one
    of 101 files;
  - in each case, assert `SURFACE_LIMIT_EXCEEDED`, plus a recorded problem in the
    under-the-limit case.

  These run in-process with no environment dependency, so they fail in CI too. The `os.open` and
  `os.lstat` cases were observed failing on the current code (probes in the session scratchpad:
  `surface_inject.py` and `surface_inject_lstat.py`).

## Generalization — the failure class

- **Class (CTRL-G):** a control silently skips an item it could not read, so its verdict is
  computed over less than its input. The skip turns a fail-closed bound into fail-open, makes a
  derived artifact non-deterministic, or lets a lint gate pass a file it never examined.
- **Siblings found (the same shape; latent fail-open, never observed misfiring):**
  `except OSError: continue` around the file read inside a scan loop, in:
  - `marker-lint.py:117`
  - `verify-no-conflict-markers.py:89` (also catches `UnicodeDecodeError`, intentionally, for binaries)
  - `verify-no-machine-paths.py:128`
  - `verify-portable-text-io.py:132`
  - `verify-subprocess-utf8.py:89`
  - `scrub.py:125`
  - `visual-assets-setup.py:213` (the committed-secret scan)

  A file deleted mid-scan is a legitimate skip. A file that exists but cannot be read is not.
  `UnicodeError` is *permanent*, not transient: a non-UTF-8 file is dropped on every run, so it
  is a finding, never a silent skip (adversarial finding 8).
- **Sibling shape 2 (found by the adversarial review, confirmed by grep):** an `os.walk`/`rglob`
  with no `onerror` drops a whole subtree silently when a directory listing fails. There are 19
  sites in 14 scripts:
  - delivery
  - docs-graph (both walks)
  - dream
  - marker-lint
  - pack-apply
  - prompt-compile
  - rayfin-setup (added on this branch; it walks for project discovery, so a failure there means
    a missed project)
  - scrub
  - verify-no-new-console-launches
  - verify-portable-text-io
  - verify-ruling-citations
  - verify-subprocess-utf8
  - visual-assets-setup
  - xaml-token-lint

  Each needs triage: is its walk a verdict over a corpus, or a best-effort discovery?
- **Siblings ruled out:** 32 silent `OSError` swallows in `pack/scripts` were classified with
  `swallow_sweep.py`. The other 24 are single-file probes of optional state (for example
  `pack-doctor._read`, `coord-core.current_blob`, `_is_reparse_point`) whose "absent" result is
  the documented default. None feeds a count or a verdict over a corpus. Within `docs-graph.py`,
  `scan()` and `scan_context()` already record unreadable files as problems.
- **Broader rule:** in a control that enumerates a corpus, every item is counted on admission.
  Each item is either processed or recorded as a problem, and only `FileNotFoundError` (gone
  mid-scan) may be skipped silently. Every walk that feeds a verdict passes an `onerror` that
  records the problem. Class prevention: a lint over `pack/scripts` that flags two shapes, unless
  a `# skip-ok:` reason is present:
  - an `except OSError` → `continue`/`return None` inside a walk;
  - an `os.walk`/`rglob` with no `onerror`.
- **Markers harvested:** `grep -n "assume:\|simplify:" pack/scripts/docs-graph.py` found no
  marker covering the silent-skip choice.

## Phased repair plan

| Phase | Scope (code + tests) | Failure mode eliminated | Validation | Depends on |
|---|---|---|---|---|
| 1 | `docs-graph.py`: count on admission; record `lstat`, read and walk failures as `problem`s; `onerror` on both walks. Add three injection regression tests. | The flake; a fail-open limit; a silent loss of a surface or artifact from the index | Each test fails on current code and passes after; gate 9c is stable | Decision above |
| 2 | The seven scanning gates: unreadable-but-present → a reported finding; `FileNotFoundError` may still be skipped; `UnicodeError` is a finding. One injection test per gate. | A gate passes a file it never read | Each test fails on current code | 1 (same rule) |
| 3 | Triage the 19 walks with no `onerror`: verdict walks get a recording `onerror`; best-effort ones get `# skip-ok:` | A gate or discovery silently drops a subtree | An injection test per verdict walk | 1 |
| 4 | Class control: the lint for both shapes, with `# skip-ok:` | Recurrence of CTRL-G in new scanners | The lint fails on the pre-phase-2 tree | 2, 3 |

## Residual risk & follow-ups

- The run-1 trigger stays **Inferred** until phase 1 makes drops visible. The first recorded
  `problem` will name the exception class.
- **What would change the diagnosis:** a recurrence after phase 1 with no recorded problem. That
  would mean a path outside the read, such as the walk itself.

## Gate record

- Diagnosis by the investigator (Peer Mode).
- **Adversarial review (Test Architect, 2026-10-22): PASS-WITH-CHANGES.** The mechanism and the
  seven sibling lines were upheld. The findings are folded in above:
  - the `lstat` and walk fault points the first fix missed (verified with the reviewer's probe);
  - "necessary" relabelled Inferred;
  - the `os.walk`-without-`onerror` sibling shape (19 sites, verified by grep);
  - `UnicodeError` is permanent, not transient.
- **Test Architect hard veto: not cleared.** It clears when the phase-1 injection tests exist and
  are observed failing on the unfixed code. That is implementation work, after approval.
- **Stop:** this report ends at human review. No phase is implemented without explicit approval.
