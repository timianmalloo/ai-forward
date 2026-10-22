---
id: investigation-bootstrap-release-tag-collision
title: "Investigation - test_bootstrap fails with 'tag v2026.10.19.4 already exists' in a developer clone"
type: doc
status: draft
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [investigation, test-hermeticity, bootstrap, git-refs, TEST-C, CI-ENV]
links:
  - { to: defect-classes, rel: relates-to }
review-by: "2027-02-28"
review-suggested: []
summary: >-
  test_no_source_overrides_use_upstream_main_defaults clones the developer's checkout, tags and all,
  then creates the release tag v2026.10.19.4 on the assumption that the clone has none. Since the
  2026-10-19 release the tag exists in every developer clone, so the fixture fails; CI never sees it
  because it checks out without tags. Verified necessary and sufficient. Class TEST-C (a fixture
  inherits ambient refs from the checkout it clones) registered; phased repair proposed, not applied.
---

# Investigation: bootstrap-release-tag-collision — the bootstrap test fails only where the release tag exists

- **Status:** Root cause verified. Fix proposed and awaiting human review. Nothing implemented.
- **Severity / tier:** T1. Test-only defect: a false red on the gate. The product is unaffected.
- **Reported by / date:** maintainer, 2026-10-22, against `main` at 30b184b. Reproduced on
  `feat/installrayfin` (based on 30b184b; the test, the fixture and `bootstrap.py` are unchanged
  there) and in a clean no-tags clone of 30b184b.
- **Related spec:** `bootstrap.py` release pin (`RELEASE_REF`); `pwsh tools/verify-bundle.ps1` gate 3.

## Symptom

`tests/docs_explorer/test_bootstrap.py::BootstrapTests::test_no_source_overrides_use_upstream_main_defaults`
fails locally with `fatal: tag 'v2026.10.19.4' already exists`. It failed in both full local gate
runs on 2026-10-22 (1 failed, 1,778 passed). CI `pack-consistency` is green on the same commit.

## Reproduction

- **Fails:** any clone that carries the tag. In the primary checkout, local tag and `origin` tag
  are both annotated `3d65bf6` → commit `30b184b` (`git for-each-ref refs/tags/v2026.10.19.4`).
- **Passes:** a `git clone --no-tags` of the same commit. The test passed in 50 s. **[Verified]**
- **Fails again:** in that same no-tags clone, after `git tag v2026.10.19.4`, the test fails with
  the reported message. **[Verified]**

## Timeline

1. `bootstrap.py:531`: with no `--source`, the default ref is `RELEASE_REF = "v2026.10.19.4"`.
2. The test (`test_bootstrap.py:60-107`) builds its upstream with `clone_source()`, which runs
   `git clone --no-hardlinks ROOT source`. A plain clone copies every tag reachable from `ROOT`.
3. At line 79 the test runs `git tag v2026.10.19.4` in that clone. It assumes the tag is new.
4. 2026-10-19: the revision-117 release pushed the tag. From then on, every fetch with tags brings
   it into developer clones, and the fixture's assumption is false.
5. CI checks out with `fetch-depth: 50` and no tags. The assumption stays true there, so the
   test is green.

## System map

The input is the ref set of the developer's checkout. The fixture copies it into the test
upstream; the test adds refs and assumes none of its names are taken. The test's verdict depends
on state outside the test. No feedback loop is involved, but there is a delay: the defect stayed
latent until a release created the name.

## Hypotheses considered

| # | Hypothesis | Evidence | Verdict |
|---|---|---|---|
| H1 | The local tag is stale or points at the wrong commit | `for-each-ref` shows local = remote (`3d65bf6` → `30b184b`). An earlier reading said otherwise, but PowerShell had mangled `^{commit}`, so that reading is retracted. | Ruled out |
| H2 | `bootstrap.py` regressed | The test passes on the same code in a no-tags clone | Ruled out |
| H3 | The fixture inherits the tag from the developer clone | Necessary and sufficient, shown below | **Verified** |

## Verified root cause

`clone_source()` is not hermetic. It inherits the refs of the checkout it runs in, and the test
then creates a ref whose name the repository's own release process also publishes.
**Necessary:** without the inherited tag, the test passes. **Sufficient:** adding the tag back
makes it fail. **[Verified, both directions, 2026-10-22]**

## Causes ruled out

H1 and H2 (above). A product defect in the release pin is ruled out too: the failing command is
the fixture's `git tag`, which runs before `bootstrap.py` is called.

## Specific fix(es) for this instance

- **Change:** `clone_source()` clones with `--no-tags` (`git clone --no-tags --no-hardlinks ROOT
  source`). The test then owns every tag in its upstream. The alternative, `git tag -f`, is
  rejected: it would hide the collision instead of making the fixture independent of it.
- **Why it reaches the root:** it removes the dependence on ambient refs. It does not just make
  this one tag name safe.
- **Blast radius:** the other `clone_source()` callers use `--source`, so their default ref is
  `HEAD` and they read no tags. The swept sibling at line 717 is covered by phase 2.
- **Rollback:** revert one line.
- **Regression test (fail-first):** `clone_source(origin=ROOT)` takes the origin as a parameter.
  The test builds its *own* tagged origin (`git clone --no-tags ROOT origin`, then `git tag
  v2026.10.19.4` there) and runs the scenario against it. It must not depend on ROOT's tags.
  Otherwise it passes vacuously in CI, where ROOT has no tags (adversarial finding 1). The
  failure is observed through the reproduction above (no-tags clone + `git tag`). The committed
  test lands with phase 1.

## Generalization — the failure class

- **Class (TEST-C):** a test fixture clones or copies the developer's checkout and inherits its
  ambient state (tags, branches, remotes, config). It then assumes that state is empty.
- **Relation to CI-ENV:** this is the same root as CI-ENV ("verification depends on the
  checkout's ref set") with the polarity inverted. CI-ENV breaks when a ref is *missing* in CI.
  TEST-C breaks when a ref is *present* locally. The CI-ENV control fetches the missing ref, so it
  cannot catch this direction.
- **Siblings found:**
  - `test_bootstrap.py:717-745` creates branch `preview` and passes `--ref preview`. **Latent:**
    if a `preview` tag were ever inherited, the name would be ambiguous and git resolves a tag
    before a branch. There is no such tag today (`git for-each-ref` checked), so it passes now.
  - `test_bootstrap.py:966-978` (`test_fetch_fallback_...`, `test_unknown_ref_...`). These read
    ROOT's live state: line 967 runs `branch --show-current` on ROOT, and `run_bootstrap`
    (line 38) defaults `--source` to ROOT itself, so every named `--ref` resolves against the
    developer's refs. **Latent, both polarities:** on a detached CI checkout the branch is
    empty, which gives the refspec `refs/heads/:refs/heads/redirected`. The test still asserts
    a non-zero exit, so it passes, but for a different reason than intended (the CI-ENV
    direction). And an ambient ref named `does-not-exist` would flip line 976 (the TEST-C
    direction). Corrected from "ruled out" by the adversarial review (finding 2). **[Verified]**
    by reading the lines.
- **Siblings ruled out (with evidence):**
  - `test_bootstrap_preservation`: pins `--ref` to a commit SHA.
  - The other `clone_source()` users in `test_bootstrap.py`: use `--source`, so the ref is `HEAD`.
  - `test_session_start_hook`: bare clone; creates no named refs.
  - `test_install_revision_bump`: depth-1 clone; reads, creates nothing.
  - `test_coord_runner`, `test_coord_proof_fresh_clone`: create worktree branches with unique
    generated names.
- **Broader rule:** a fixture that clones the working repository is hermetic by construction.
  It clones with `--no-tags`, and creates or fully qualifies (`refs/heads/<n>`) every ref it
  later names. A test never passes the developer checkout itself as an upstream that it resolves
  named refs against. Class prevention is a test-suite check. It flags two things:
  - a `git clone` of `ROOT` without `--no-tags`;
  - `--source ROOT` combined with a named `--ref`.

  Read-only clones are allowlisted, each with a reason: `test_bootstrap_preservation.py:109,225`,
  `test_session_start_hook.py:292` and `test_install_revision_bump.py:70` (adversarial finding 3).
- **Markers harvested:** `grep -n "assume:\|simplify:" tests/docs_explorer/test_bootstrap.py bootstrap.py`
  found no marker on the fixture's ref assumption. The belief was unmarked, which is the NG9 shape.

## Phased repair plan

| Phase | Scope (code + tests) | Failure mode eliminated | Validation | Depends on |
|---|---|---|---|---|
| 1 | `clone_source(origin=ROOT)` uses `--no-tags`. Add a regression test against a self-built tagged origin. | False red in every developer clone after a release | The new test fails on current code in CI as well as locally, and passes after; the original test passes in a tagged clone | — |
| 2 | Line 717 uses `refs/heads/preview`. Lines 966-978 run against a hermetic clone with a known branch, not against ROOT. | Latent ambiguity from ambient refs; a detached-HEAD refspec that tests a different case | One test per site with a colliding ref added to the origin | 1 |
| 3 | Class control: a suite check for clones of ROOT without `--no-tags` and for `--source ROOT` with a named `--ref`, with a reasoned allowlist | Recurrence of TEST-C in new fixtures | The control fails against today's tree, then passes | 1, 2 |

## Residual risk & follow-ups

- **[Inferred]** The manual `adoption-entrypoints.yml` workflow checks out with `fetch-depth: 0`
  (tags included) and runs `test_bootstrap.py`, so it would fail the same way. It has not been
  run since the tag existed. Phase 1 resolves it.
- **What would change the diagnosis:** the test failing in a tag-free clone.

## Gate record

- Diagnosis by the investigator (Peer Mode).
- **Adversarial review (Test Architect, 2026-10-22): PASS-WITH-CHANGES.** The root cause was
  upheld and independently verified (the tag was created 2026-10-19 at 18:13:19; CI fetches with
  `--no-tags` at `pack-consistency.yml:41`). The four findings are folded in above: the vacuous-CI
  regression test, the misclassified 966-978 sibling, the control's scope, and the branch named in
  the header.
- **Test Architect hard veto: not cleared.** It clears when the phase-1 regression test exists and
  is observed failing in a tag-free checkout. That is implementation work, after approval.
- **Stop:** this report ends at human review. No phase is implemented without explicit approval.
