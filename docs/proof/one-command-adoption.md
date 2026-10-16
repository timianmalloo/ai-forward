---
id: proof-one-command-adoption
title: "Proof Pack — one-command adoption"
type: proof-pack
status: in-review
owner: "@ahutanu"
phase: "pack-adoption"
tags: [adoption, delivery, installation, portability]
links:
  - { to: spec-one-command-adoption, rel: implements }
  - { to: design-one-command-adoption, rel: implements }
review-by: "2027-01-01"
summary: >-
  Executed evidence for conditional outcome delivery and portable source-driven setup,
  including old-code failures, preservation probes, native skill use and finite limits.
---

# Proof Pack: one-command adoption

- **Change:** `feat/one-command-adoption`
- **Spec / design:** `docs/specs/one-command-adoption.md` · `docs/design/one-command-adoption.md`
- **Tier:** T2 (load-bearing workflow boundaries, local state and cross-platform installation)
- **Author / date:** @ahutanu · 2026-10-02

## Revision 102 checkpoint boundary correction

A read-only review reproduced three additional boundary gaps in revision101:
verification could adopt changed product files after independent review, executable
permission changes kept the same content fingerprint, and inherited Git variables
could select another project despite an explicit target. A verification permission
pause could also replace the snapshot, so a completion-only check was insufficient.

Each repair followed an observed red regression before the source change:

- Verification completion and every verification-stage pause now require the
  unchanged workspace. Fresh proof and closure files belong in the existing local
  or external evidence area; a nonignored in-project proof file is not a drift
  waiver. Product corrections use the affected authored stage and independent
  re-review. Normal authoring-stage capture and unchanged closure remain valid.
- Regular workspace entries record content hashes and POSIX executable bits.
  Resume and scoped repairs reject mode-only behavior changes, including unrelated
  executable files. Authorized mode corrections remain possible. Windows uses a
  neutral field, not a claim of equivalent POSIX permissions; timestamps and other
  permission metadata are not a new fingerprint boundary.
- All delivery Git queries isolate inherited repository-local selectors for the
  worktree, index, common directory, object store and local configuration. The
  explicit project remains the checkpoint identity; credentials and global Git
  configuration are not disabled.

The focused real compiler/helper suite passed **80 tests and 147 subtests** after
these repairs, including Git/plain T1/T2 closure and pause counterexamples, actual
POSIX execution failure, scoped mode correction/refusal and inherited root/index
controls. Receipts in these tests are synthetic structural fixtures, not authentic
human consent or live model qualification. Earlier content-only checkpoint hashes
cannot prove the stronger workspace boundary: preserve refused records and their
original evidence, and reconcile rather than recomputing an integrity hash.

The three-platform adoption workflow includes the new regression file; POSIX-only
mode tests explicitly skip Windows. Independent review, the complete local bundle,
source/install/API/package parity and published-head native receipts are separate
qualification gates, not implied by these focused results. The product presentation,
upstream-default onboarding and full prior refresh history are unchanged.

## Revision 101 presentation preservation

The earlier onboarding rewrite replaced original product and reference prose rather
than merely moving it. This correction restores the complete upstream root README,
pack README/overview and stage-by-stage handbook guidance from committed raw Git
source, with portable setup and `deliver` sections added alongside it. The original
Rigor Protocol, dual-mode personas, roster, detailed standards, workflow examples,
repository layout, maintenance loop and portal explanation remain.

Whole-file reversal of the explicit additions and feature-only adjustments matches
upstream `ccc5160603448981d6c879a8735b79129500eb64` exactly on all five source guides.
The adjustments are limited to directly affected skill counts, new installer support,
source/installed Codex-path clarification, prerequisites and optional source-clone
alternatives. Controls check full original explanation blocks, not just headings;
the prior published rewrite and a retained-heading/replaced-paragraph mutation both
fail. The canonical upstream one-liner, host-specific entry points, human gates,
failure guidance and same-project resume remain. Runtime files are unchanged.

Independent preservation review passed the full raw-source comparison and narrow
feature adjustments, including restored applier/host mechanics and first-class
individual workflows. Focused documentation, history, installation-default and
reader checks passed **88 tests and 61 subtests**. Browser checks passed **264 tests
with 12 deliberate skips**; they retain the original specification exercise and
compile-after-planning assertions alongside the new delivery path. Executable,
existing skill and knowledge bytes are unchanged; managed-block changes restore
workflow presentation only. Final aggregate and published-head native qualification
must be checked separately, not inferred from the historical receipts below.

## Revision 100 upstream onboarding correction (historical qualification)

Primary onboarding now documents the upstream repository and `main`, which are
already the bootstrap defaults. The normal command has no `--repo` or `--ref`.
Source/ref overrides remain optional for unmerged review and reproducible version
selection; historical fork qualification below is not the upstream customer path.

The documentation regression was observed red for the four primary guides before
the correction. A real no-override bootstrap control exercises dry-run, install
and byte-identical repeat against a disposable committed post-merge source mirror.
It verifies the upstream repository and `main` in the receipt without changing
global Git settings. This is fixture execution, not a claim that the unmerged
launcher has already appeared on upstream `main`. Runtime installer and delivery
code are unchanged. A refresh-history control rejects abbreviated records on both
canonical and installed surfaces; the complete prior delta block was compared
byte-for-byte with the committed baseline, not reconstructed from display excerpts.
Documentation guards distinguish that explicit historical data from current
instructions; controls retain forbidden current advice outside the archive, in
other collapsed sections and in incomplete history containers.
Local revision-100 verification passed: **1,543 Python tests, 44 expected skips,
875 subtests and all 18 bundle gates**; the focused documentation/defaults and
current-guidance controls passed **64 tests and 18 subtests**. Browser checks
passed **264 tests with 12 deliberate skips** across Chromium, Firefox and WebKit.
Source, installed and packaged byte comparisons passed. Independent closure
replayed **33 guard invocations over 11 cases**, including the prior malformed
container and mixed-record failures, without changing the original guard rules.
These are finite local controls, not universal model or human-consent proof.
The existing native qualification below covers the unchanged runtime; the new
published documentation head must receive its own CI readback before handoff.

## Revision 99 quality follow-up (historical qualification)

An outcome and customer-journey review
reproduced five boundary gaps in the earlier revision: an existing instruction archive
could be replaced, inherited Git attributes could change, review repairs could strand
a saved task, nested submodule edits could escape drift checks, and an older native
Python could be selected. The earlier positive tests did not cover those conditions.

Revision 99 repairs those gaps. The follow-up adversarial review also found and closed
hardlink/FIFO repair-scope aliases, stale or incompatible `UV_PYTHON` selectors and
generated API drift. Exact-hash closure probes found no remaining P0–P2 issue in those
repairs. A cold-reader review checked twenty onboarding, recovery, proof and tone gaps;
all local gaps passed, and post-push branch plus exact-commit installs closed the three
publication checks. This revision is accepted on the evidence below.

## Claims and evidence

### Claim 1: one named skill selects an applicable route without silently changing the finish line
- **Evidence:** focused delivery, evaluator and adoption controls exercise T0/T1/T2, six
  explicit risk floors, load-bearing architecture, coordination, defect review,
  characterization-before-coordinated-migration, plain-project state, fresh-process
  resume, drift refusal, bound receipts and exact criteria closure.
- **Oracle:** real CLI subprocesses against disposable Git/plain projects and the
  protected golden-case oracle. The controls fail when stages are reordered, evidence
  changes, the contract changes, an author clears an applicable veto, the verifier is
  changed, or product behavior exits before all boundary checks finish.
- **Red observed before green:** yes; routing, proportional review, active-author and
  oracle counterexamples were executed against the pre-fix source.
- **Confidence:** [Verified] for deterministic routing/checkpoint mechanics.
- **Residual risk:** actor/source labels and hashes are cooperative structural controls,
  not proof of semantic correctness or authentic human consent. Model compliance is a
  separate native-host observation.

### Claim 2: setup is one cross-shell command and preserves product work
- **Evidence:** current committed-source fixtures install into both plain and Git
  projects, preserve dirty product bytes and an existing product graph, deploy the exact
  canonical `deliver` skill/helper, create no audit log, and produce byte-identical
  repeat installs. Focused controls cover worktrees, exact refs and hidden commits,
  malformed policy, nonregular paths, rollback, installed-state readback and failures.
- **Oracle:** source-map-derived plans, a disposable staging target, pre-promotion drift
  checks and exact installed-byte readback. Tests explicitly fail if the bootstrap scans
  dependency trees, initializes Git, leaks URL credentials, executes project module
  shadows, overwrites existing named hooks, removes unverified instructions, changes an
  existing Git policy, or rewrites active product checks.
- **Red observed before green:** yes; each listed preservation/privacy failure was
  reproduced against the earlier wrapper/source behavior before its regression turned green.
- **Confidence:** [Verified] on actual GitHub-hosted Linux, macOS and Windows, including
  real Python 3.9/3.11 selector controls and the literal Windows `cmd.exe` one-liner.
- **Residual risk:** selected source is trusted executable code; cooperative drift
  detection is not a concurrent-writer lock or a power-loss transaction. Unsafe legacy
  transformations deliberately stop for reconciliation rather than guess ownership.

### Claim 3: the installed entry point can complete a real small task and resume interruptions
- **Evidence:** an installed `/deliver` skill in GitHub Copilot CLI grounded a README-only
  T0 correction, stopped when a required command permission was unavailable, resumed the
  same task after permission was supplied, survived one transient model connection timeout,
  changed the exact requested bytes, and passed the unchanged verifier. No owned audit log
  or product graph was created.
- **Oracle:** a pre-existing verifier was observed red before the task and its original
  SHA-256 was read back after completion; exact README bytes were asserted separately.
- **Red observed before green:** yes.
- **Confidence:** [Verified] for this one installed native scenario.
- **Residual risk:** this is not proof for every host/model/backend. The host's ignored
  session-start timing marker is inherited runtime plumbing, not an authored audit entry.

## Boundary coverage

| Boundary | Evidence |
|---|---|
| Empty request / review-only request | skill contract and reference tests |
| T0 proportional path / T1-T2 reviewed paths | route + checkpoint CLI tests |
| Defect, migration, UI, architecture, coordination | route matrix and ordered transition tests |
| Human decision, permission, veto, release | bound positive/negative receipt controls |
| Plain project, Git root, linked worktree, subdirectory | bootstrap/checkpoint integration tests |
| Dirty/untracked work, local policy, generated product data | preservation and conflict-refusal probes |
| Symlink, hardlink, FIFO, directory conflict, Windows reparse | path-safety fixtures; native junction remains matrix evidence |
| Initial/repeat/preview/unknown ref/hidden commit/I/O failure | bootstrap CLI tests and committed-source fixtures |
| UTF-8/legacy console/cross-shell command shape | portability gates and native shell workflow |
| Evaluator tampering / early exit / final-state mutation | trusted pre/behavior/post oracle assertions |

## Failure modes addressed

- Conditional routing does not become a blind all-skills conveyor belt.
- Checkpoint transport, model completion or matching JSON structure are not acceptance.
- Unanswered/denied/stale/wrong-author decisions do not become consent.
- A remote wrapper cannot silently substitute `main` for an unresolved requested ref.
- Product policy and safety checks are not treated as disposable because their filenames
  once belonged to the pack.
- Project modules cannot shadow stdlib imports during a no-write bootstrap preview.
- Worker-writable verifiers cannot approve an unimplemented or prematurely exiting product.

## Revision 99 acceptance readback (historical qualification)

- The complete local bundle finished with **1,535 passed, 44 skipped and 872
  subtests passed**; all **18/18** consistency, portability, source-sync,
  Python, Node, graph, doctor, eval-shape and budget gates passed.
- The complete local Playwright result on the final artifact set is **264 passed,
  12 deliberately skipped** across Chromium, Firefox and WebKit.

- **Original qualified implementation:** `049d234b5e64cd8fd04d354c071c6ec99aaffab3`.
- **Revision 99 quality qualification:** `888942d656343643117999fe7c4e1b7da951a36b`,
  authored as `Alex Hutanu <alex@hutanu.net>`.
- **Native matrix:** [GitHub Actions run 37077090769](https://github.com/ahutanu/ai-forward/actions/runs/37077090769)
  completed successfully for Ubuntu, macOS and Windows on the revision 99 quality SHA.
- Every platform passed routing/resume/preservation/deployment tests and an actual
  HTTPS exact-SHA one-line install plus repeat install in a plain project. Windows
  additionally passed the exact `cmd.exe` one-liner and native junction fixture.
- Public branch and exact-SHA smoke runs both installed revision 99 from
  `888942d656343643117999fe7c4e1b7da951a36b`, initialized no Git repository,
  delivered byte-matching customer pages and repeated byte-identically.
- Independent code closure rejected hardlink/FIFO aliases, preserved regular
  create/modify/delete behavior, exercised stale/old/compatible uv selectors with
  stdin/arguments/exit status intact, and found no remaining bounded P0–P2 issue.
- Independent reader closure verified the live preview command, installed guidance,
  host-specific next steps, missing-checkpoint recovery, proof limits and qualified
  cross-host claims. File installation remains bounded mechanical evidence, not
  universal model compliance or authenticated consent.
