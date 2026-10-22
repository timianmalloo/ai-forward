---
id: spec-hermetic-fixtures-and-fail-closed-scans
title: "Spec - hermetic git fixtures (TEST-C) and fail-closed corpus scans (CTRL-G)"
type: spec
status: draft
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [spec, test-hermeticity, fail-closed, docs-graph, bootstrap, TEST-C, CTRL-G]
links:
  - { to: investigation-bootstrap-release-tag-collision, rel: refines }
  - { to: investigation-surface-limit-flake, rel: refines }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-04-20"
review-suggested: []
summary: >-
  The durable fixes for two verified defect classes. TEST-C: a test never uses the developer
  checkout as a git upstream it names refs in. CTRL-G: a scan that renders a verdict over a corpus
  accounts for every item it admitted, and reports every item it could not read instead of skipping
  it silently. Delivered in four slices. Each slice has failing-first tests, and an AST-defined
  control drives the remaining latent sites onto one shared rule.
---

# Spec: hermetic git fixtures and fail-closed corpus scans

This spec states *what* must be true and *why*. The *how* belongs to `/design-slice`: helper
names, signatures, the exit code chosen for a walk fault. Source evidence:
`docs/investigations/bootstrap-release-tag-collision.md` and
`docs/investigations/surface-limit-flake.md`.

## Part A — Functional specification

### Problem

Two kinds of verification in this repo give answers that depend on things outside what they
check.

1. **TEST-C.** Some bootstrap tests use the developer's own checkout (`ROOT`) as their git
   upstream. Either they clone it, or they hand it straight to `run_bootstrap`, whose `--source`
   defaults to `ROOT` (`test_bootstrap.py:40`). They then create or name refs as if the upstream
   had none of its own. Since the 2026-10-19 release tag, one test fails in every developer clone
   and passes in CI, which has no tags. Two more tests carry the same dependence. One of them
   already passes in CI for the wrong reason: on a detached HEAD the branch name is empty
   (`:967`).
2. **CTRL-G.** Several scans render a verdict over a set of files, but silently skip a file they
   cannot read. They do this in four ways:
   - an `except OSError: continue` around the read;
   - an `lstat` failure that is reported as "not a regular file";
   - `os.walk` with no `onerror`, which ignores directory-listing errors by default
     (`os.walk.__doc__`, verified 2026-10-22);
   - a strict UTF-8 decode of a truncated read.

   This turns a fail-closed limit into fail-open (the flaky `SURFACE_LIMIT` test). It drops
   entries from the derived index without a trace. And it lets a lint gate pass a file it never
   read.

Both classes produce a **wrong verdict with no signal**. A false red costs a gate run (~80 min
locally). A false green is worse: a check that reports it examined what it did not.

### Target users & personas

- **Pack maintainer** runs `verify-bundle.ps1` before every push. They need a red to mean a real
  defect.
- **CI** (`pack-consistency`, three OSes) needs the same verdict a maintainer gets locally.
- **Consuming-repo user** runs `docs-graph.py derive` / `validate` and the shipped gate scripts.
  They need the index and the gates to be complete, or to say clearly that they are not.

### Core scenario

A maintainer runs the full gate locally, in a clone that holds every release tag, on a Windows
machine with on-access scanning. Every test that passes in CI passes locally. If a file could not
be read during a scan, the run names that file and the error, and the verdict that depends on it
fails. It never silently passes or silently drops the file.

### In scope / Out of scope (explicit non-goals)

**In scope**
- The TEST-C fixtures in `tests/docs_explorer/test_bootstrap.py`: `clone_source()`,
  `run_bootstrap()`'s default source, the `preview` test (`:717`), and `:966-978`.
- In `pack/scripts/docs-graph.py`: HTML-surface admission, both walks, and surfacing the
  findings in `validate`.
- One shared "read or report" rule for every other CTRL-G site in `pack/scripts`. The sites are
  found and driven by the class control, not hand-listed.
- One class control per class, run in gate 3 (the test suite).

**Out of scope**
- **Retrying** transient I/O. Retry would hide the signal this spec exists to surface.
- Changing **CI's** checkout (tags, depth).
- Any change to `bootstrap.py` or to the release-pin mechanism.
- New *deployed* scripts. The controls are repository tests, so they add no script count.
- A per-site injection test for each latent sibling gate. The shared rule is tested once, and the
  control forces every site onto it. The one exception is the security-relevant secret scan (S5).

### Conceptual domain model (DM1/DM4)

**Bounded context:** *verification of the pack* (tests and gates).

**Ubiquitous language**

| Term | Meaning |
|---|---|
| **Corpus** | The set of items a scan is asked to judge: what its enumeration yields (a walk, a glob, or `git ls-files`) after the documented exclusions. |
| **Admission** | The point where the scan counts an item into the corpus. It happens **before** any read. |
| **Documented exclusion** | An item left out by rule before admission: a template directory, `index.html`, or a symlink/reparse *surface*. It is neither counted nor reported. |
| **Finding (unreadable)** | The record that an admitted item, or a directory, could not be judged. It names the path and the error class. |
| **Legitimate skip** | An admitted item that vanished mid-scan (`FileNotFoundError`). It is the only silent skip allowed. |
| **Skip-ok reason** | A `# skip-ok: <reason>` marker that declares an enumeration best-effort (discovery, not a verdict). |
| **Ambient ref** | A tag, branch or HEAD state a test got from the developer checkout instead of creating it. |

**Aggregate — scan run** (root; one execution). **Invariant:**
`admitted = judged + findings + legitimate skips`. A verdict is rendered only once every admitted
item is in exactly one of those buckets. Findings and counts are value objects.

**TEST-C rule:** every ref a test names, the test created.

### User stories & acceptance criteria (testable)

Each criterion is either **fail-first**, meaning it was observed failing on the unfixed code
before the fix, or **characterization**, meaning it is green first and pins behaviour the fix must
keep.

**S1 — A release tag cannot break a bootstrap test (TEST-C). Fail-first.**
```gherkin
Scenario: the upstream already carries the release tag
  Given clone_source takes its origin as a parameter
  And the test builds a temporary origin (clone --no-tags of ROOT) and plants tag RELEASE_REF in it
  When the no-source-overrides scenario builds its upstream from that origin
  Then the scenario passes
  And the same body fails with "already exists" when clone_source does not pass --no-tags
      # red shown on any checkout, CI included: the test plants the tag itself
```

**S2 — The latent siblings are hermetic. Fail-first.**
In each case below, the test runs against a temporary origin it built, never against `ROOT`.
Red is shown by running the pre-fix test body with `ROOT` swapped for a temporary clone in which
the test planted the ambient ref.
```gherkin
Scenario: a planted tag shares the branch's name
  Given the origin carries branch "preview" and a tag "preview" on a different commit
  When the preview test bootstraps with --ref preview
  Then the receipt records the branch commit
  And the fix names the branch unambiguously (refs/heads/preview)

Scenario: the origin's HEAD is detached
  Given the test's origin is on a detached HEAD
  When the refspec-fallback test builds its refspec
  Then the refspec names a branch the test created (never "refs/heads/:...")

Scenario: the unknown-ref test owns its origin
  Given a fresh origin built by the test, with no ref named "does-not-exist"
  When the unknown-ref test bootstraps with --ref does-not-exist
  Then the bootstrap fails, and the target is unchanged
  # red demo: the pre-fix body, run against a clone of ROOT with "does-not-exist" planted, succeeds
```

**S3 — HTML-surface admission is deterministic (CTRL-G instance). Fail-first unless marked.**
```gherkin
Scenario Outline: one read fault among SURFACE_LIMIT + 1 admitted surfaces
  Given 101 HTML surfaces under the docs root
  And one <fault> on one surface
  When discover_html_surfaces runs
  Then it raises SURFACE_LIMIT_EXCEEDED
  Examples: | fault                                   |
            | os.open PermissionError                 |
            | os.lstat OSError                        |
            | _is_reparse_point OSError               |
            | _SourceChangedError during read         |
  # os.open and os.lstat observed red on 2026-10-22; the reparse and source-changed rows are
  # fail-first, to be observed red before the fix

Scenario: an unreadable surface under the limit
  Given 5 surfaces and one raises PermissionError on read
  When derive runs
  Then the index holds the 4 readable surfaces
  And stderr carries one finding naming the file and "PermissionError"

Scenario: a directory that cannot be listed
  Given a subdirectory whose listing raises OSError
  When discover_html_surfaces runs
  Then a finding names that directory   # its files were never admitted, so the limit cannot count them

Scenario: a valid UTF-8 surface larger than the title read cap
  Given a valid UTF-8 surface whose multi-byte character straddles SURFACE_TITLE_BYTES
  When derive runs
  Then the surface is indexed with its title   # observed red 2026-10-22: _surface_title returns None

Scenario: a surface that is not UTF-8
  Given a surface whose bytes are not valid UTF-8
  When derive runs
  Then a finding names the file and the decode error, on every run

Scenario: a symlinked surface (characterization)
  Given a surface that is a symlink or reparse point
  When derive runs
  Then it is excluded, with no finding and no count   # documented exclusion, as today
```

**S4 — `validate` fails on surface and walk findings. Fail-first. This adds new wiring.**
Today `validate` (`cmd_inventory`, `docs-graph.py:900`) scans markdown only. Surface discovery
runs only in `derive` (`:1103`). That is why this behaviour is new.
```gherkin
Scenario: a surface finding reaches the gate
  Given one surface raises PermissionError on read
  When docs-graph.py validate runs
  Then it exits non-zero, and the finding is counted under "problems"

Scenario: a markdown directory that cannot be listed
  Given a docs subdirectory whose listing raises OSError
  When validate runs
  Then it exits non-zero with a finding naming the directory

Scenario: derive stays non-blocking (characterization)
  Given any finding
  When derive runs
  Then it writes the index, reports the finding on stderr, and exits 0 as today
```

**S5 — One shared read-or-report rule for the other CTRL-G sites.**
```gherkin
Scenario: the shared rule (fail-first, tested once)
  Given an in-scope file that exists but raises PermissionError on open
  When it is read through the shared rule
  Then a finding is produced, and the caller's verdict fails

Scenario: a file gone mid-scan (characterization)
  Given an in-scope file that raises FileNotFoundError on open
  Then it is skipped without a finding

Scenario: every gate that uses the rule turns its findings into a failing exit (fail-first)
  Given each scanning gate migrated onto the shared rule
  And one in-scope file that raises PermissionError
  When the gate runs
  Then its exit code is non-zero
  # one parametrised test over the gates, so a gate that calls the rule and discards its findings is caught

Scenario: the secret scan fails closed (fail-first; the security-relevant site)
  Given a file in the visual-assets-setup committed-secret scan that raises PermissionError
  When the scan runs
  Then it reports the file instead of passing

Scenario: binary files in verify-no-conflict-markers (characterization)
  Given an in-scope binary file
  Then it is skipped as today
  And the decode skip and the OSError path are separate handlers
  And its --self-test (which asserts "an unreadable corpus counts as nothing read") is updated to the new rule
```

**S6 — The classes cannot quietly return (controls). Fail-first: each control is observed red on
the tree before its fix.**
```gherkin
Scenario: TEST-C control
  Given a test in tests/ that
    - runs git clone with ROOT as the source and no --no-tags, or
    - calls a helper whose git source defaults to ROOT
  When gate 3 runs
  Then the control test fails and names the file and line
  # read-only clones get --no-tags too; no allowlist unless the first run proves one is needed

Scenario: CTRL-G control (matched by AST, not by text)
  Given a for-loop over the result of os.walk, Path.walk, Path.rglob, Path.glob, glob.glob or a git ls-files call
  And inside it an except clause catching OSError, any OSError subclass, Exception, or a bare except
      (alone or in a tuple)
  And that clause's body is only continue, pass, return None or return False
  And there is no "# skip-ok: <reason>" on the except line
  Then the control test fails and names the file and line
  Or: an os.walk with no onerror, or a Path.walk with no on_error, and no "# skip-ok:" fails the control
  Or: any Path.rglob / Path.glob used for a verdict with no "# skip-ok:" fails it
      # Python 3.12's rglob has no error hook: move to Path.walk(on_error=) or declare it best-effort
  # TEST-C "helper whose git source defaults to ROOT" means a function parameter default of ROOT,
  # or a `<param> or ROOT` expression feeding a git source. Each is pinned by a fixture.

Scenario: control fixtures
  Given positive and negative fixture snippets for each rule
  Then the control flags every positive and none of the negatives
```

### Non-functional requirements (ISO/IEC 25010 checklist)

| Characteristic | Requirement |
|---|---|
| Functional suitability | Every fail-first criterion is observed red on unfixed code. Every characterization criterion is green before and after (Test Architect veto). |
| Reliability | Scan verdicts depend only on the corpus. A fault yields a named finding, never a different verdict without a signal. The TEST-C tests give the same result in any clone, with or without tags, and on attached or detached HEAD. |
| Performance efficiency | **At most one open per admitted file**, asserted by one test that counts calls at the shared rule's own open seam. `discover_html_surfaces` reaches the same seam through `_open_verified_binary`. `os.open` is not the counter, because `Path.read_text`/`io.open` never call it. No retry. |
| Maintainability | One rule per class, held in the register and enforced by one AST-defined control. `# skip-ok:` reasons sit at the call site. |
| Portability | Same behaviour on Windows, Linux and macOS. Fault injection is in-process. |
| Security | The committed-secret scan stops failing open (S5). |
| Usability (operator) | A finding is one line: the repo-relative path and the exception class. |
| Compatibility | `docs-index.js` gains no fields. `validate` gains new *defects*; the INSTALL `changes` entry says so. |

### Boundary set

- `SURFACE_LIMIT` = 100: 100 admitted surfaces pass, and 101 raise, whether or not they are
  readable.
- 0 surfaces: no finding, no raise.
- A symlink/reparse *surface* is a documented exclusion. A symlink in the *markdown* walk stays a
  problem, as today (`docs-graph.py:528`). `_safe_path_kind` must distinguish "is a link" from
  "lstat failed": today both return False (`:247-253`).
- `FileNotFoundError` mid-scan is a legitimate skip. Every other `OSError`, a
  `UnicodeDecodeError` on a complete read, and a `_SourceChangedError` are all findings.
- A directory-listing fault cannot raise the limit, because its files were never admitted. It
  produces a finding and fails `validate`.

### Comparables & user evidence (sourced)

- **[Verified]** `os.walk` ignores `scandir` errors unless `onerror` is passed (Python 3.12.10
  `os.walk.__doc__`, 2026-10-22).
- **[Verified]** `git clone --[no-]tags` (`git clone -h`, 2026-10-22).
- **[Verified]** In-repo comparable: `_markdown_candidates` (`docs-graph.py:501-541`) counts on
  admission and records rejected paths as problems.
- **[Verified]** `derive` reports problems on stderr without blocking (`:1055,1168`). `validate`
  fails on problems (FR-056, `:904-940`), but it runs only the markdown scan (`:901`).
- **[Verified]** `_surface_title` reads `SURFACE_TITLE_BYTES` (256 KiB) and decodes strictly
  (`:594`). A probe on a valid file with `é` across the cap returned `None` (2026-10-22).
- **[Verified]** User evidence:
  - the bootstrap test failed in 3 of 3 local runs on 2026-10-22;
  - the surface test failed in 1 of 3;
  - CI was green on the same commit.
- **[Inferred]** Hermetic fixtures are standard practice (pytest `tmp_path`, Bazel hermeticity).
  No external citation was fetched, and nothing depends on it.

### Applicable governance lenses

| Lens | Applies | Answer |
|---|---|---|
| Quality attributes | Yes | NFR table |
| Threat model | Partly | Secret scan fails closed (S5). No new trust boundary. |
| Privacy | No | — |
| Accessibility | No | No UI |
| Performance | Yes | One open per admitted file, asserted |
| Release / rollback | Yes | Each slice reverts on its own. `pack/` slices carry an INSTALL revision bump (PACK-W, `test_install_revision_bump.py`). Tests-only slices do not. |
| Observability | Yes | Every finding is emitted on the normal path, with no flag. This makes the next occurrence of the run-1 trigger diagnosable. |

### AI-integrated allocation

N/A — no model-backed capability.

### Delivery slices (each independently shippable)

| Slice | Covers | Touches `pack/` (revision bump) | Depends on |
|---|---|---|---|
| 1 | S1, S2, S6 TEST-C control | No | — |
| 2 | S3, S4 (`docs-graph.py`) | Yes | — |
| 3 | S5 shared rule; S6 CTRL-G control, which drives every remaining site onto the rule or `# skip-ok:` | Yes | 2 |

Slices 1 and 2 are independent. Slices 2 and 3 may share one revision bump in one PR.

### Amendments from design (2026-10-22, recorded, not silent)

- **S5 "shared rule … tested once" becomes an inline rule per site.**
  - Why not a module: a shared module would be a new deployed script (script count, INSTALL
    counts, and a cross-script import a partial upgrade can break).
  - What holds the rule instead: the AST control (S6) holds it at every site, and a fault-injection
    test per gate proves each verdict fails.
- **S6 TEST-C is narrowed from "a helper whose source defaults to ROOT" to the ref-naming shapes:**
  - a named non-HEAD `--ref` resolved against the root;
  - a ref read run in the root;
  - a root clone without `--no-tags`.

  A HEAD-only `run_bootstrap()` names no ref, and flagging its many callers would cost a full repo
  clone each for no failure prevented.
- **"The path does not exist" includes `NotADirectoryError`** (a parent is a file), alongside
  `FileNotFoundError`.
- **CTRL-G's control is scoped to the zones that can drop an item:** corpus loops in scanner
  modules, plus the same-module functions those loops call. A module-wide rule flagged 59 handlers,
  most of them optional single-file probes.
- **The `_is_reparse_point` fault row is dropped from S3.** On the real path it always receives
  metadata, so it cannot raise; a test there would pass vacuously.

## Part B — UX specification

N/A — no user-facing interface. The only operator-visible output is a one-line finding (NFR,
Usability).

## Part C — UI specification

N/A — no visual UI.

## Flagged risks & residual unknowns

- **Revision collision.** `feat/installrayfin` (uncommitted) takes INSTALL revision 118. Slices 2
  and 3 take the next revision after whichever PR merges first.
- **What triggered run 1 is still unknown.** After slice 2 the next occurrence names its fault. A
  recurrence with *no* finding would mean the diagnosis was wrong.
- **Breadth of the CTRL-G control.** `pack/scripts` holds about 105 `except OSError` sites, per
  the reviewer's count. The AST rule flags only those inside an enumeration loop, but the
  first run may still surface more sites than the 7 + 19 named so far. Each is moved onto the
  shared rule or given a `# skip-ok:` reason; review checks the reasons.
- **New findings in consuming repos.** After slices 2 and 3, an unreadable file that used to pass
  silently becomes a visible `validate` defect. This is intended, and the INSTALL `changes`
  entry says so.

## Gate record

**Round 1 (2026-10-22), on the first draft:**
- **Test Architect — BLOCK.** Three findings were blockers:
  - the S1 and S2 Givens could not be set up, because they required mutating `ROOT`, and
    `clone_source` hard-coded `ROOT`;
  - the directory-fault case could not raise the limit.

  The majors were:
  - `validate` needs new wiring (it was claimed as reuse);
  - the symlink rule conflicted with the markdown path and with `_safe_path_kind`;
  - the controls were too loose: text matching, and they missed `ls-files` loops;
  - the binary skip shares a tuple with `OSError`, and its `--self-test` must change;
  - the ±3% performance budget was not measurable;
  - preservation criteria were mislabelled as fail-first.

  Every one is resolved in this revision. The S1 and S2 Givens now use origins the test builds;
  S3 has a separate directory finding; S4 states the new wiring; the boundary set is rewritten;
  the controls are AST-defined; S5 has its binary scenario; the performance criterion is "one
  open per file"; and criteria are labelled fail-first or characterization.
- **The Simplifier — soft veto.** The main finding: S5 and S6 restated one rule three times
  with per-site tests. Resolved by merging them into one shared rule, one test, and one control
  that drives the sites. Only the secret scan keeps its own test. The second fixture aggregate and
  the ±3% NFR were cut. The TEST-C allowlist was dropped: read-only clones get `--no-tags` too.
  The non-UTF-8 scenario was kept, because `_surface_title` decodes strictly (`:594`), so the
  drop is real.
- **Found while resolving:** the 256 KiB truncation drops a valid UTF-8 surface (probe returned
  `None`). Added to S3.
- **Round 2 (2026-10-22):**
  - **The Simplifier — PASS, soft veto cleared.** It judged the Test Architect's additions
    justified. Nit applied: the two unobserved S3 fault rows are labelled "to be observed".
  - **Test Architect — PASS-WITH-CONDITIONS, hard veto cleared for the spec gate.** Four
    non-blocking findings were applied: the open counter moved to the shared rule's seam; a
    parametrised exit-code test per gate; the self-contradictory S2 scenario rewritten; and the
    AST rule extended to OSError subclasses, `Exception`, bare `except`, `Path.walk`, the rglob
    hook gap, and the `source or ROOT` default.
- **The implementation gate still needs a Proof Pack.** Every fail-first criterion must be shown
  red and then green.
