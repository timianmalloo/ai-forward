---
id: design-hermetic-fixtures-and-fail-closed-scans
title: "Design - hermetic git fixtures (TEST-C) and fail-closed corpus scans (CTRL-G)"
type: design
status: draft
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [design, test-hermeticity, fail-closed, docs-graph, bootstrap, TEST-C, CTRL-G]
links:
  - { to: spec-hermetic-fixtures-and-fail-closed-scans, rel: implements }
  - { to: investigation-surface-limit-flake, rel: relates-to }
  - { to: investigation-bootstrap-release-tag-collision, rel: relates-to }
review-by: "2027-04-20"
review-suggested: []
summary: >-
  How the three spec slices are built. Slice 1 makes the bootstrap fixtures clone with --no-tags
  and run against origins the tests own, guarded by an AST control over tests/. Slice 2 makes
  docs-graph count surfaces on admission, give both walks an onerror, decode the title read
  incrementally, and run surface discovery in validate. Slice 3 applies one read-or-report rule
  inline at every corpus-scan site in pack/scripts, guarded by an AST control. It adds no new
  module.
---

# Design: hermetic git fixtures and fail-closed corpus scans

Implements `docs/specs/hermetic-fixtures-and-fail-closed-scans.md`.

**Spec statements this design must satisfy:**
- "every ref a test names, the test created";
- `admitted = judged + findings + legitimate skips`;
- "only `FileNotFoundError` may be skipped silently";
- the S1–S6 criteria.

## Responsibility

- **Slice 1:** the bootstrap tests are independent of the developer checkout's refs.
- **Slice 2:** `docs-graph.py` surface discovery and markdown discovery account for every item
  and directory.
- **Slice 3:** every corpus-scan site in `pack/scripts` either reports an unreadable item or
  declares itself best-effort.

## Contracts

**Exposed (changed):**

| Contract | Before | After |
|---|---|---|
| `discover_html_surfaces(root, artifacts, problems=None)` | Returns surfaces. Drops unreadable files silently. The limit counts titled files. | Returns surfaces and appends findings to `problems` when given. The limit counts admitted files. |
| `docs-graph.py derive` | Problems go to stderr; exit 0. | Same, plus surface and walk findings. |
| `docs-graph.py validate` / `inventory` | Markdown scan only. | Also runs surface discovery. Its findings count as defects, so `validate` exits 1. |
| Seven scanning gates and three rglob lints | An unreadable file is skipped silently. | A finding (or crash) and a non-zero exit. A missing file is still skipped. |
| `test_bootstrap.py` `clone_source(origin=ROOT)` | Clones with tags. | `--no-tags`, origin parameterised. |

**Consumed (established, cited):**
- `os.walk(top, onerror=f)`: by default `scandir` errors are ignored; `onerror` receives the
  `OSError`. **[Verified]** `os.walk.__doc__`, Python 3.12.10.
- `git clone --no-tags`: clones no tags, and later fetches do not follow them. **[Verified]**
  `git clone -h`.
- `bootstrap.py:530-543` resolves `--ref` in its own tagged clone of `--source`, and falls back
  to `refs/remotes/origin/<branch>`. So `refs/heads/preview` resolves to the branch even when a
  `preview` tag exists. **[Verified]** by reading the code; proven again by the S2 demo.
- `codecs.getincrementaldecoder("utf-8")().decode(b, final=False)` keeps an incomplete trailing
  sequence buffered instead of raising. **[Verified]** in the 2026-10-22 probe re-run under
  the implementation.
- The minimum Python is 3.8 (INSTALL.md:471). `Path.walk` (3.12+) is therefore not used.

## Patterns

- **Fail-closed enumeration (count on admission, "Collecting Parameter" for findings).**
  `_markdown_candidates` already does this. The surface path is brought into line with it.
  This is the reuse rung of the ladder (L1-2), not a new pattern.
- **Inline read-or-report, not a shared module (deviation from the spec's "shared rule"
  wording).** The rule is three lines per site:

  ```python
  except FileNotFoundError:
      continue
  except OSError as exc:
      findings.append(...)
  ```

  A shared `scan_io.py` would be a new *deployed* script: the script count goes 47→48, the
  revision counts change, and every gate gains a cross-script import that a partial upgrade
  could break. The AST control enforces the shape at every site, so the single-sourcing a module
  would give is already held by the control. The spec's S5 "tested once" becomes a parametrised
  test over the gates. The spec is amended to match (see Conformance).
- **Fail-loud walk (`onerror=_raise`)** where the walk feeds an install or a delivery check
  (`pack-apply` source walks, `delivery` snapshots). There a silent gap is worse than a stopped
  run, and those callers already turn an exception into a failure.
- **Declared best-effort (`# skip-ok: <reason>`)** for advisory miners and probes, where a missed
  file lowers recall but renders no verdict.
- **Rejected:** retry (the spec excludes it); `Path.walk(on_error=)` (needs 3.12); a
  text-matching control (it produces 59 hits, about 30 of them boilerplate, measured).

## Data shapes

No persisted data and no schema. The data-model DoD items are N/A: no store, no facts, no
migration. The only new shapes are findings:

| Where | Shape |
|---|---|
| `docs-graph` problems | `{"file": "<public-relative path>", "problem": "unreadable surface: PermissionError"}`. Variants: `"unreadable directory: <Exc>"`, `"surface is not UTF-8: UnicodeDecodeError"`, `"surface changed during read"`. |
| Gate string findings | `"<rel>: unreadable: <ExcName>"`, in each gate's existing findings list. |
| marker-lint | `{"code": "UNREADABLE", "marker": "", "src": "<rel>", "text": "<ExcName>"}` |
| Secret scan | `(<rel>, "unreadable: <ExcName>")`, which takes the existing exit-2 path. |

## Error & concurrency model

**Errors:**
- `FileNotFoundError` on an item is a legitimate skip, raised when an item vanishes mid-scan.
- Any other `OSError`, a `_SourceChangedError`, or a `UnicodeDecodeError` on a complete read is
  a finding.
- `os.walk` directory errors go to `onerror`, as a finding or (fail-loud sites) a re-raise.
- `SURFACE_LIMIT_EXCEEDED` (exit 4) fires on admission 101. It is unchanged.

**Concurrency:** none added. A scan is single-threaded per site (`scan_context`'s thread pool is
untouched).

**Admission order in `discover_html_surfaces`:**
1. Walk.
2. Name filter.
3. `lstat` (an error is a finding, and the item is counted).
4. Link/reparse/non-regular check (excluded, not counted).
5. `admitted += 1`, and raise if it passes the limit.
6. Title read.

The `lstat` error counts toward the limit, so a fault can never lower the count.

## Change-surface list (E7)

| Slice | Surfaces |
|---|---|
| 1 | `tests/docs_explorer/test_bootstrap.py`, `test_bootstrap_preservation.py`, `test_session_start_hook.py`, `test_install_revision_bump.py`, plus the new `tests/docs_explorer/test_hermetic_git_fixtures.py` (the TEST-C control) |
| 2 | `pack/scripts/docs-graph.py` → synced `docs/ai-forward-pack/scripts/docs-graph.py`; `tests/docs_explorer/test_docs_graph.py`; INSTALL revision and `changes` |
| 3 | The ten gates and the other flagged scripts in `pack/scripts` → synced copies; `tests/docs_explorer/test_fail_closed_scans.py` (the parametrised exit test and the CTRL-G control); INSTALL revision and `changes` |
| Docs | Register statuses (`docs/lessons/defect-classes.md`); spec amendment; this design |

There is no UI, wire or store surface.

## Failure-mode analysis

| Mode | Disposition |
|---|---|
| A transient `PermissionError` on one surface read | **Detect.** A finding is recorded, the limit still counts the file, and `validate` exits 1. Test S3. |
| An `lstat` error on a surface | **Detect.** As above. Test S3. |
| A directory listing fails | **Detect.** `onerror` records a finding. Test S3/S4. |
| A valid surface over 256 KiB with a multi-byte character across the cap | **Prevent.** Incremental decode. Test S3. |
| A non-UTF-8 surface | **Detect.** A finding on every run. Test S3. |
| A file deleted mid-scan | **Accept** (legitimate skip; the spec allows it). Characterization test. |
| `validate` now fails in a consuming repo that has an unreadable HTML file | **Accept.** It is intended, and the INSTALL `changes` entry says so. |
| A `pack-apply` source walk fails | **Prevent.** A fail-loud re-raise means no partial install is reported as success. Test: an injected walk error stops the run. |
| A gate migrated to the rule but discarding its findings | **Detect.** The parametrised exit-code test. |
| The control misses a new shape (an unforeseen helper) | **Accept the residual.** The control covers loops in scanner modules. The register records the rule for review. |
| The fixture clone gets slower | **Accept.** `--no-tags` makes the clone smaller, not slower. |

## Adversarial analysis (STRIDE-lite)

| Boundary | Threat | Disposition |
|---|---|---|
| Untrusted repository content read by the gates | **Tampering / DoS:** a file made unreadable (permissions or a lock) to slip a secret or marker past a gate | **Mitigate.** The gate now fails on an unreadable file. Negative test: S5 secret scan with an injected `PermissionError`. |
| The same boundary | **DoS:** many unreadable files flood the findings | **Accept.** Findings are bounded by corpus size, and existing limits apply (`SURFACE_LIMIT`). |
| The same boundary | **Information disclosure** through the finding text | **Mitigate.** A finding names only the repo-relative path and the exception class, never file content. |

No new trust boundary, identity or secret handling.

## Privacy analysis (LINDDUN-lite)

The component touches no personal data. Findings carry repo-relative paths and exception class
names only.

## UI & interaction design

N/A — no interface. The only operator-visible output is the one-line finding.

## Telemetry

The repo's telemetry for CLI gates is their stdout/stderr and exit code (O-series as applied to
local tools). Every finding is emitted on the normal path, with no flag:
- `derive` writes `finding: <file>: <problem>` to stderr;
- `validate` adds the finding to the JSON `problems` list and counts it in `defects`;
- gates print their existing finding lines.

The stable codes are the problem strings above, plus `UNREADABLE` (marker-lint). There are no
spans or metrics: these are short-lived local processes.

Load-bearing telemetry is tested: S3 asserts the stderr line, and S4 asserts the `validate` JSON
and exit code.

## Test plan

| Directive | Tests |
|---|---|
| **D0 hygiene** | Every new test asserts outside `subTest`, or has an explicit sentinel (TEST-B). There is no dead code, and scratch probes stay outside the repo. |
| **Slice 1 (fail-first)** | `test_clone_source_inherits_no_refs_from_its_origin`: a tiny origin repo with tag `RELEASE_REF` and tag `preview` → `clone_source(origin)` → `git tag -l` is empty. Red on the pre-fix `clone_source` (tags copied). This is a cheaper equivalent of S1's full-scenario red, and it proves the same invariant; the full scenario then passes in a tagged clone (observed). |
| | S2 tests rewritten to run against `clone_source()` with a branch the test creates (`refs/heads/preview`; a created branch for the refspec test; `source=` for the unknown-ref test). Red demonstrations are recorded in the Proof Pack. |
| | **TEST-C control** `test_hermetic_git_fixtures.py`, an AST scan of `tests/**/*.py`, which flags: a `git` `clone` arg list that contains the repo-root expression (`ROOT`/`REPO`, `str(...)`, `.as_uri()`) without `--no-tags`; and an `--ref <literal other than HEAD>` in a call whose source is the repo root (explicit `--source str(ROOT)`, or `run_bootstrap` without `source=`). Positive and negative fixtures are included. It was red on the pre-fix tree (5 clones; the 972/978 calls). |
| **Slice 2 (fail-first)** | Four fault-injection cases (`os.open`, `os.lstat`, `_is_reparse_point` via an `lstat`-less call, `_SourceChangedError`): each raises the limit at 101. Under the limit, one unreadable surface → 4 surfaces plus one finding. A directory-listing fault → a finding. A cap-straddle surface keeps its title. A non-UTF-8 surface → a finding. `validate` exits 1 on a surface finding and on a markdown-walk finding. |
| | **Characterization:** symlink surface excluded; `derive` exit 0 with findings; boundaries at 100 and 0. **NFR:** one `_open_verified_binary` call per admitted surface. |
| **Slice 3 (fail-first)** | A parametrised test over the ten gates: one in-scope file whose open raises `PermissionError` gives a non-zero exit or a finding. The same test asserts at most one open of that file. Secret-scan-specific: an unreadable file appears in `committed_secret_suspects`. `pack-apply` source walk fault → raises. |
| | **Characterization:** `FileNotFoundError` is skipped silently (per gate, in the same parametrised test); the conflict-marker gate skips binaries; the existing `--self-test`s stay green. |
| | **CTRL-G control**, an AST scan of `pack/scripts/*.py`, with positive and negative fixtures. In *scanner modules* (those calling `os.walk`, `glob`/`rglob`/`iglob`, `scandir`, `listdir`, `iterdir`, or passing `ls-files`), it flags a `for`-loop over a non-literal iterable containing a handler that is silent (`continue`/`pass`/`return None`/`return False`) and that catches `OSError`, an `OSError` subclass other than `FileNotFoundError` alone, `Exception`, or a bare `except`, without `# skip-ok:` on the handler line. In any module, it flags `os.walk(...)` without `onerror` and `.rglob(`/`.glob(` on a non-literal receiver, without `# skip-ok:`; `ast.walk` is never flagged. It was red on the pre-fix tree (the probe found 18 handlers and 17 filesystem walks/globs). |

**Testing Strategy union:** D0, regression (fail-first per handled mode), characterization
(preserved behaviour), negative-security (secret scan), and a static control (AST). No
concurrency or performance directive is triggered beyond the one-open assertion.

## Conformance notes

- **Spec amendment (recorded, not silent):**
  - S5's "shared rule … tested once" becomes the inline rule plus the parametrised per-gate
    test and the AST control;
  - S6's TEST-C "helper whose git source defaults to ROOT" is narrowed to "a named non-HEAD
    `--ref` resolved against ROOT". A HEAD-only call names no ref, so it carries no TEST-C risk,
    and flagging the dozens of `run_bootstrap()` callers would cost a full repo clone each for
    no failure prevented.
- `pack/` slices bump the INSTALL revision (PACK-W). Slices 2 and 3 land in one PR and share
  one revision.

## Flagged risks & residual unknowns

- **Revision collision** with `feat/installrayfin` (also 118). Resolved at whichever merge comes
  second.
- **Surface findings in this repo's own `docs/`.** If any existing surface is unreadable, or is
  over 256 KiB without a `<title>` in reach, `validate` turns red after slice 2. This is checked
  by running gate 9 before the PR.
- **What triggered run 1 is still unknown.** After slice 2 the next occurrence names its fault.

## Status & next action

| | |
|---|---|
| **Completed** | Design and implementation of slices 1–3 |
| **Remaining** | None in scope. Follow-up: limit errors outside `context` exit with a traceback |
| **Best next action** | Merge; the Proof Pack is `docs/proof/hermetic-fixtures-and-fail-closed-scans.md` |

## Gate record

**Round 1 (2026-10-22):**

- **Patterns Expert + Simplifier — PASS-WITH-CONDITIONS, soft veto cleared.**
  - Applied: `pack-apply.py:1049` walks the *target* repository, so it is `# skip-ok`, not
    fail-loud; the `pack-apply` source walks (684/750) and the `delivery` snapshots stop on
    purpose, because a snapshot that drops a directory compares equal across a change.
  - Applied: the "clone gets slower" row is dropped.
  - Declined: the simpler TEST-C rule ("every clone in `tests/` has `--no-tags`"). It would force
    `--no-tags` on clones of temporary repos the tests build themselves, while the root-expression
    rule targets exactly the ambient-ref source.
- **Test Architect — BLOCK.** Every finding was resolved:
  1. **Directory `lstat` faults pruned a subtree silently.** Now a finding, through the new
     `_path_kind`; test `test_a_directory_whose_lstat_fails_is_a_finding`.
  2. **CTRL-G could not see helpers.** The rule now covers same-module functions that a corpus
     loop calls, and treats empty-value returns as silent. It flags `_surface_title` and
     `_safe_path_kind` on the pre-fix tree.
  3. **The `_is_reparse_point` row was unreachable.** Dropped.
  4. **TEST-C missed ref reads in ROOT and `--repo`.** Both are added, with fixtures, and the rule
     flags `test_bootstrap.py:968` on the pre-fix tree.
  5. **"Literal" was undefined.** It now means a tuple/list/set display, with the stdio
     boilerplate as a negative fixture.
  6. **Slice-1 red sequencing.** `origin` was made a parameter first, red was observed, then
     `--no-tags` was added.
  7. **"Exactly one open" was wrong for explicit titles.** It is now "at most one".
- **Round 2: implementation evidence.** Every fail-first test was observed red on the pre-fix code,
  then green. The evidence is in the Proof Pack.

**Round 3: pre-merge review (2026-10-22):**

- **Python Developer — PASS-WITH-CONDITIONS.** All applied: the title read takes one byte past
  the cap, so a file of exactly the cap is decoded in full; the walks in ruling-citations and
  console-launches prune their skip directories; console-launches reports a relative path;
  `pack-apply main` turns an unreadable file into a message and exit 1; `scrub` names an unknown
  directory when the error carries no filename.
- **Test Architect — PASS-WITH-CONDITIONS, hard veto cleared on finding 1.**
  1. **The control missed `glob` and `Path.walk`.** Both added. On the pre-round-3 scripts it
     flagged 12 sites, now 0. Ten moved to `iterdir` (which raises); session-profile's two are
     `# skip-ok`.
  2. **A handler that assigns an empty value was not seen as silent.** Added. `audit-log` and
     `coord-core` were annotated (the value is recorded, not dropped).
  3. **`problems` is now required** in `discover_html_surfaces`.
  4. **delivery main traceback.** No change: `delivery.main` already catches `OSError`.
  5–7. Added tests for xaml and documented-commands listing parity, an exact `tests/sub`
     assertion, and the exact-cap decode.
