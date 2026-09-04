---
id: forensic-review-rev59-backlog
title: "Forensic review backlog — ai-forward revision 59 (FR-076 … FR-085)"
type: doc
status: proposed
owner: "@timianmalloo"
phase: "assessment"
tags: [forensic-review, backlog, rev59, governance]
links:
  - { to: forensic-review-rev59, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2027-03-04"
summary: >-
  Ten proposed backlog items from the revision-59 forensic review, FR-076 to FR-085, each with
  evidence, falsifiable acceptance criteria and a recommended next skill. No P0 or P1; the work
  is governance and documentation debt. Status proposed — nothing here is implemented, and the
  review stopped for human triage.
---

# Forensic review backlog — revision 59

**Status: `proposed`.** Nothing below is implemented. Every item awaits triage.

Priorities: **P0** exploitable / data-loss / irreversible · **P1** high-likelihood correctness,
security or migration risk · **P2** material maintainability, operability or governance debt ·
**P3** localized hygiene.

**There is no P0 and no P1.** The repo is healthy; this is debt, ordered by how much each item
erodes trust in an instrument the pack asks people to rely on.

---

## Phase 1 — Restore trust in the instruments (P2)

These two are first not because they are the biggest, but because each currently teaches a
reader to distrust a control. A control nobody believes is worse than no control.

### FR-076 · issue · P2 — The defect-class register's stated counts are wrong by an order of magnitude
- **Location:** `docs/lessons/defect-classes.md:32` (the `**Status counts:**` line)
- **Evidence:** the line states `controlled 12 · partially-controlled 9 · uncontrolled 22` — a
  total of **43**. The file contains **24** real classes (25 `###` headings less the schema
  example), whose actual `**Status:**` values are **14 controlled, 8 partially-controlled,
  2 uncontrolled**. The stated "uncontrolled" figure is **eleven times** the real one.
- **Violated contract:** `continuous-improvement.md` CI4 — the register is the governance record;
  and the pack's own rule that a number in a committed artifact is either measured or labelled.
- **Consequence:** the single number a reader uses to judge whether the discipline is working is
  wrong, and wrong in the alarming direction. Any trend drawn from it is fiction.
- **Root cause:** the counts are hand-maintained and hand-incremented. Nothing derives or checks
  them. Three increments during the revision-58/59 work propagated an error already present.
- **Disconfirming check attempted:** parsed every `**Status:**` value in the file and compared
  against the stated line; also confirmed no class is missing a `**Status:**` field (0 missing),
  so the discrepancy is not an artefact of unparsed entries.
- **Recommended remediation:** derive the counts, or check them. A test that parses the file and
  asserts the stated line equals the tally is ~15 lines and closes it permanently.
- **Acceptance criteria:** (a) the stated counts equal the parsed tally; (b) a test fails when
  they diverge, **observed failing on the current file before the fix**; (c) the test runs in
  `verify-bundle.ps1` gate 3.
- **Validation:** run the new test against the pre-fix file — it must fail — then against the
  corrected file.
- **Dependencies:** none. **Owner:** Documentation Steward. **Next skill:** `/implement`.

### FR-077 · issue · P2 — The marker linter's entire output is noise from its own test fixtures
- **Location:** `pack/scripts/marker-lint.py`; findings all in `tests/docs_explorer/test_marker_lint.py`
- **Evidence:** `python pack/scripts/marker-lint.py` reports **"10 finding(s) across 14
  marker(s)"**. All ten are inside the linter's own test file, which contains deliberately
  malformed markers as fixtures. Genuine findings across the entire pack: **zero**.
- **Violated contract:** `instrumentation-over-inference.md` IO12 — instrument deliberately;
  telemetry that is ignored is worse than none.
- **Consequence:** a real marker violation would appear as the eleventh line in a list of ten
  known-false ones. The tool runs in warn mode, so nothing fails and nobody re-reads the list.
  This is signal destroyed by its own noise floor.
- **Disconfirming check attempted:** filtered the output for findings outside the test file —
  the result is empty, confirming 100% false-positive rate rather than a mixed signal.
- **Recommended remediation:** exclude the linter's own fixtures (or `tests/` generally) from
  the scan. Once the output is genuinely empty, promote it from warn to `--gate` in CI, which is
  only safe *because* it is empty.
- **Acceptance criteria:** (a) a clean tree produces **zero** findings; (b) a deliberately
  malformed marker in `pack/` produces exactly one, **observed**; (c) the linter runs gating in
  `pack-consistency.yml`.
- **Dependencies:** none. **Owner:** Test Architect. **Next skill:** `/implement`.

---

## Phase 2 — Close the federation loop (P2)

The pack can now find and promote a learning. It still cannot prove one arrived.

### FR-080 · issue · P2 — Abstraction defeats the federation deduplicator (defect class FED-A)
- **Location:** `pack/scripts/apply-learnings.py`, the reconciliation step
- **Evidence:** COORD-C and COORD-D were abstracted **from** ai-de's own DC-088 and DC-067, then
  filed back into ai-de as `add`. Measured signature overlap: **0.17** and **0.14** against a
  0.6 merge threshold. Both fleet classes name the target class in their own `evidence`
  (`ai-de:DC-088`), which the reconciler never reads.
- **Violated contract:** ADR-0004 — one quantity, one home; the merge path exists to prevent
  exactly this duplicate.
- **Consequence:** applying such a plan literally puts one class in two homes in the target.
  Caught here only because the source repo happened to be known.
- **Recommended remediation:** reconcile on **provenance before prose** — a fleet class whose
  `evidence` names a class id in the target is a `merge` against that id regardless of lexical
  score. This is an exact recorded identity, not the fuzzy index the Simplifier rejected, so
  that objection does not apply.
- **Acceptance criteria:** (a) pushing COORD-C to ai-de yields `merge → DC-088`, not `add`;
  (b) a fleet class with no provenance in the target still yields `add`; (c) both observed.
- **Dependencies:** none. **Owner:** Release Engineer. **Next skill:** `/design-slice`, then `/implement`.

### FR-081 · issue · P2 — Fleet provenance does not survive application, so arrival is unverifiable
- **Location:** the `learnings/plans/*.plan.md` → target-register boundary
- **Evidence:** plans emit `- **Source:** fleet (drm-NNNN/pN)` in each entry, but **zero**
  `Source:** fleet` markers exist in the committed register of any target (TheTerrace, ai-de,
  HealthWatch all 0). ai-de *did* once apply fleet dream results by hand (`71747f4`), reworded,
  so the provenance was lost in transit.
- **Consequence:** no target can answer "which of my classes came from the fleet, and from which
  dream?". The federation loop cannot be audited end to end, and a duplicate cannot be detected
  after the fact (compounding FR-080).
- **Disconfirming check attempted:** searched for the marker at each target's committed `HEAD`
  rather than the working tree, so an uncommitted application would not produce a false negative.
  Also checked commit subjects, which is what surfaced the ai-de hand-application.
- **Recommended remediation:** make the marker load-bearing — `/apply-learnings` verifies it
  after application, and `check-consistency` (in the target) can then report inherited-class
  count. A hand-applied entry that drops the marker should be detectable.
- **Acceptance criteria:** (a) an applied plan leaves a machine-readable provenance marker;
  (b) a report can list a target's inherited classes with their source dream; (c) five currently
  uncommitted target applications either carry it or are recorded as not carrying it.
- **Dependencies:** FR-080 (same code path). **Owner:** Release Engineer. **Next skill:** `/design-slice`.

---

## Phase 3 — Dogfooding and documentation debt (P2)

### FR-078 · issue · P2 — The repo ships and documents a coordination layer it does not run
- **Location:** this repository; `pack/scripts/coord-core.py`
- **Evidence:** `coord-core.py doctor` here reports `registry NOT PRESENT (advisory)`,
  `merge driver none declared (748 tracked files scanned)`, and no pre-commit hook is installed.
  Meanwhile `docs/portal` publishes a full **Agent Coordination** section describing the layer,
  and `CLAUDE.md` mandates worktree discipline (WT1–WT12).
- **Violated contract:** the repo's own dogfooding premise — it is "the development home of the
  pack *and* a live install of it".
- **Consequence:** the capability most exposed to multi-agent risk is the one least exercised
  here. Defects in it will be found by consuming repos rather than by this one. AI-DE, which
  *does* run it, is where all eight COORD classes were discovered — that asymmetry is the
  evidence.
- **Recommended remediation:** run `coord install` in this clone and add `.agents/artifacts.yml`.
  Note the honest counter-argument for triage: this repo is largely single-session, so the layer
  may genuinely not be needed — in which case the finding is that the **documentation should say
  so**, rather than that the layer should be installed.
- **Acceptance criteria:** either (a) `coord doctor` reports an effective registry and driver
  here, or (b) the architecture records why this repo deliberately does not run it.
- **Dependencies:** none. **Owner:** Release Engineer. **Next skill:** `/investigate` (decide which arm).

### FR-079 · todo · P2 — 60% of the deployed script bundle's public functions have no docstring
- **Location:** `pack/scripts/*.py` (19 modules); per-module gaps listed in `docs/api/*.md`
- **Evidence:** `tools/build-api-docs.py` — **267 public functions, 108 documented (40%)**.
  The remaining 159 are individually named as coverage gaps rather than fabricated.
- **Consequence:** this is the surface deployed to every consuming repo. A consumer reading the
  generated reference finds a signature and no contract for three functions in five.
- **Recommended remediation:** raise coverage by module, highest-traffic first
  (`coord-core.py` 57, `docs-graph.py` 38, `audit-log.py` 36). Consider a ratchet rather than a
  target — the same instrument FR-083's budget uses, for the same reason.
- **Acceptance criteria:** (a) a coverage ratchet exists and fails on a decrease; (b) coverage
  rises against the recorded baseline of 40%.
- **Dependencies:** none. **Owner:** Documentation Steward. **Next skill:** `/document` per module.

### FR-082 · risk · P2 — `main` has no required status check, so nothing blocks a red push
- **Location:** branch protection on `main`
- **Evidence:** `gh api repos/timianmalloo/ai-forward/branches/main/protection` —
  `required_status_checks` **absent**; `enforce_admins: true`, `required_linear_history: true`,
  `allow_force_pushes: false`.
- **Consequence:** `verify-bundle.ps1` before pushing is the only thing between an author and a
  red `main`. On 2026-08-26 a commit published to the public site while its consistency gate was
  red — the `pages.yml` in-workflow gate was added in response, but the underlying exposure is
  unchanged for every other workflow.
- **Status:** this is a **recorded, deliberate decision** (`docs/notes/required-status-checks.md`),
  restated here because a forensic review should not silently inherit an accepted risk. The item
  is to **re-test the decision**, not to reverse it.
- **Acceptance criteria:** the decision note's re-open triggers are reviewed and either still
  hold (record the date) or have fired (add the required check).
- **Dependencies:** none. **Owner:** SRE. **Next skill:** `/investigate`.

---

## Phase 4 — Hygiene (P3)

### FR-083 · risk · P3 — The context-budget gate rests on a fitted constant
- **Evidence:** `CHARS_PER_TOKEN = 4.83` in `context-budget.py`, calibrated by fitting to one
  measured system prompt. Recomputing the always-on set (211,367 chars) across the plausible
  range: **4.0 → 52,841 · 4.4 → 48,037 · 4.83 → 43,761 · 5.2 → 40,647**, against a 60,000
  backstop. The backstop **holds at every ratio**, but at 4.0 the set sits at **88%** of it,
  where the headline figure implies 72%.
- **Consequence:** the ratchet is immune — it compares like with like. The *backstop* is an
  absolute comparison against a real model window and inherits the estimate's error.
- **Recommended remediation:** measure the ratio once against a real tokenizer and either
  confirm 4.83 or record the measured value; alternatively widen the backstop's headroom to
  cover the range. Cheap either way.
- **Acceptance criteria:** the ratio is stated as measured-or-fitted with its provenance, and
  the backstop's derivation notes the sensitivity.
- **Owner:** AI Systems Engineer. **Next skill:** `/investigate`.

### FR-084 · todo · P3 — Pinned actions target the deprecated Node 20 runtime
- **Evidence:** every recent workflow run carries the annotation that `actions/checkout`,
  `actions/setup-node` and `actions/setup-python` target Node 20 and are being forced onto
  Node 24.
- **Consequence:** none today; the runner compensates. The exposure is that the forcing is a
  transitional courtesy, not a contract.
- **Recommended remediation:** bump each action to its current major and re-pin to the new
  40-char SHA. Note the existing deliberate split: `pages.yml` already pins a newer `checkout`
  than `pack-consistency.yml`; unify while here.
- **Acceptance criteria:** no Node-20 deprecation annotation on a green run; every action still
  SHA-pinned; the pinning check still passes.
- **Owner:** Release Engineer. **Next skill:** `/implement`.

### FR-085 · todo · P3 — No line or branch coverage is measured for the deployed script bundle
- **Evidence:** no coverage tooling in any workflow, in `verify-bundle.ps1`, or in
  `package.json`. Gate 1's "proof coverage" is skill/prompt parity, not code coverage.
- **Consequence:** 440 tests pass, but which of the 267 public functions they reach is unknown.
  Untested code is indistinguishable from tested code from here.
- **Recommended remediation:** add `coverage.py` to the pytest run and record a baseline. Prefer
  a ratchet over a target for the same reason as FR-079.
- **Acceptance criteria:** a coverage number exists, is recorded as a baseline, and a decrease
  fails the build.
- **Owner:** Test Architect. **Next skill:** `/implement`.

---

## Summary

| | Completed | Remaining | Best next action |
|---|---|---|---|
| **This review** | Baseline captured · architecture and bundle verified true to code · 10 findings evidenced · adversarial gate passed | Human triage of FR-076 … FR-085 | Take **FR-076** and **FR-077** together — both are small, both restore trust in an instrument, and neither has a dependency |

Ten findings, no P0, no P1. The repository is healthy; the debt is in the instruments that
measure it.
