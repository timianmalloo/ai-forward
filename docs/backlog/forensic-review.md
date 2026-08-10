---
id: forensic-review-backlog
title: "Forensic Review Backlog — AI-Forward repository (revision 30)"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [backlog, forensic-review, adoption-readiness, triage]
links:
  - { to: forensic-review, rel: refines }
  - { to: forensic-review-20260802-backlog, rel: supersedes }
review-by: "2026-11-08"
review-suggested: []
summary: >-
  Twelve items (FR-031..FR-042) from the revision-30 review, ordered into four
  independently deliverable phases. Nine are RESOLVED at revisions 31-32 (FR-031..FR-035,
  FR-037, FR-038, FR-040..FR-042); three remain open (FR-036, FR-039, and the unverified
  end-to-end adoption path). Two proposals were overturned at triage by establishing the
  contract rather than trusting the finding.
---

# Forensic Review Backlog — revision 30

> **Triage first.** Per the `/forensicreview` contract this backlog stops at proposal. Use `/investigate` before fixing any item whose cause is not already established here, and `/implement` only once the governing acceptance criteria are approved.

**Carried forward from revision 18 (still open, unchanged):** FR-011→FR-033, FR-014→FR-034, FR-016→FR-041, FR-017→FR-042, FR-018→FR-040, FR-019→FR-036, FR-020→FR-032.

## Phases

| Phase | Goal | Items |
|---|---|---|
| **1 — Unblock adoption** | A newcomer can follow the instructions and get the promised install | ~~FR-031~~ ~~FR-032~~ ~~FR-038~~ — **complete** |
| **2 — Make the gates gate** | The checks that exist actually run where they matter | ~~FR-033~~ ~~FR-034~~ ~~FR-035~~ — **complete** |
| **3 — Restore documentation truth** | Nothing published contradicts the code | ~~FR-037~~ · **open: FR-036, FR-039** |
| **4 — Hygiene** | Low-risk quality of life | ~~FR-040~~ ~~FR-041~~ ~~FR-042~~ — **complete** |

**Nine of twelve are resolved** at revisions 31-32. **Two proposals were overturned at triage** — FR-031 (no portable token exists, so the proposed search-and-replace was never available) and FR-037 (the references were already correctly past-tense; the real defect was one present-tense phrase plus a status row that FR-032's own fix invalidated). Both corrections came from establishing the contract instead of trusting the finding, which is the review's own standard applied to itself.

**FR-043 (the adoption path) was raised and resolved at revision 33 — see below; it was the most serious finding of the review and had no id.** **Open: FR-036** (regenerate the stale `docs/_site` bundle) and **FR-039** (the public explainer's CDN dependency and accessibility floor — the largest remaining item). **Also still unverified: `/addpacktorepo` has never been run end-to-end against a scratch repo** — the single highest-value outstanding check of the adoption path, and it is not represented by any FR id.

**Every resolution below carries the control that stops the class from recurring** (CI6), not only the instance fix.

---

## FR-031 — Make the documented commands run on Windows — **RESOLVED**
- **Kind:** issue · **Priority:** P1 · **Status:** **resolved at revision 31** (triaged 2026-08-10)
- **The proposal was wrong, and establishing the contract corrected it.** This item was written as *"a search-and-replace"*. It is not. Verified at triage: python.org's Windows installer ships `python.exe` and `py.exe` and **no `python3.exe`** — so `python3` cannot work on a correctly-installed Windows Python, and the Store alias is a second, separate problem rather than the only one. Equally, a blind `python3`→`python` swap would **break macOS**, where stock systems ship no `python`. **There is no single bare token that is correct on both platforms**, so the fix could not be a substitution at all.
- **What was done instead:**
  1. **Kept `python3` as the canonical documented form** — it is the POSIX name and matches the shebang on all 13 scripts. Churning 183 sites would have traded a Windows failure for a macOS one.
  2. **Stated the convention once, where adopters land:** `INSTALL.md` §0 (new), `README.md`, and both managed blocks — `python3` means *your Python 3 interpreter*; on Windows use `python` or `py -3`; the alias is not Python.
  3. **Converted it into a control (CI6 rung 2):** `pack-doctor.py` gained a `python interpreter` check that probes `python3` / `python` / `py -3` and **names the working substitution for the machine it runs on**. An adopter learns this once, from the health check, instead of one failing command at a time.
  4. **Locked it with 5 regression tests** in `test_pack_doctor.py`, including one asserting that a bad call raises rather than being swallowed into a plausible-looking FAIL — the bug this very check shipped with.
- **Acceptance criteria met:** the doctor reports `WARN · python interpreter · use \`python\` instead` on this Windows machine and `PASS` where `python3` works; tests cover PASS / WARN / FAIL / launch-failure / programming-error.
- **Residual:** the 183 instructions still read `python3`. That is now a *documented convention* rather than a defect, but a reader who skips §0 still hits it once. If that proves too sharp in practice, the follow-up is a deployed cross-platform launcher — deliberately **not** built now (Simplifier: a stated convention plus a detection control is the smaller correct thing).
- **Validation:** `pack-doctor.py` on Windows and on a POSIX host; `pytest tests/docs_explorer/test_pack_doctor.py`. **Owner:** maintainer. **Next skill:** none.

## FR-032 — Deploy all 23 personas to the Copilot surface — **RESOLVED**
- **Resolved at revision 32.** `sync-pack.ps1` now deploys the 12 `claude-code/agents` to `.github/agents` as well, stripping the `tools:` line at the boundary per the INSTALL convention; both deployed surfaces are 23. **The control is the real fix:** `check-consistency.py` gained `check_deployed_agent_parity()`, which counts the *deployed* directories rather than the sources — the exact blind spot that let this survive twelve revisions. **Proved red-first twice:** deleting an agent fails the check, and leaking a `tools:` line into the Copilot copy fails it. Verified no BOM and valid frontmatter on all 23.
- **Kind:** issue · **Priority:** P1 · **Scope:** `pack/adapters/`, `tools/sync-pack.ps1`, `tools/check-consistency.py`
- **Evidence:** `.claude/agents` = 23, `.github/agents` = 11; the deployment map promises peers *and* adversaries to `.github/agents/<name>.agent.md`.
- **Remediation:** deploy the 12 `claude-code/agents` to the Copilot surface too, stripping the `tools:` line at the boundary as the INSTALL convention already requires. Then extend `check-consistency.py` to count the **deployed** surfaces, not only the source.
- **Acceptance criteria:** `.github/agents` contains 23 files; `check-consistency.py` fails when the two deployed surfaces diverge from the documented contract.
- **Validation:** count both deployed directories after `sync-pack.ps1`; deliberately delete one agent and confirm the checker fails. **Owner:** maintainer. **Next skill:** `/implement`. **Depends on:** none. **Status:** proposed. **Carried from FR-020.**

## FR-038 — Stop writing a machine-specific path into the committed example — **RESOLVED**
- **Resolved at revision 32.** `visual-assets-setup.py` now writes a portable placeholder into the committed `.mcp.json.example` while the git-ignored `.mcp.json` keeps the machine-resolved path.
- **Kind:** issue · **Priority:** P1 · **Scope:** `pack/scripts/visual-assets-setup.py`, `.mcp.json.example`
- **Evidence:** the committed example contains `C:\\Users\\malla\\AppData\\Roaming\\npm\\node_modules\\higgsfield-mcp\\src\\server.js`.
- **Remediation:** the example should carry a portable placeholder (`<path to higgsfield-mcp/src/server.js>`) or use `npx higgsfield-mcp`; only the git-ignored `.mcp.json` gets the resolved local path.
- **Acceptance criteria:** no committed file contains a user-specific absolute path; a check asserts it.
- **Validation:** grep the tracked tree for `Users\\` and `/home/`. **Owner:** maintainer. **Next skill:** `/implement`. **Depends on:** none. **Status:** proposed.

## FR-033 — Gate source↔install drift in CI — **RESOLVED**
- **Resolved at revision 32.** `pack-consistency.yml` now runs a source-vs-install drift gate (`sync-pack.ps1` then `git diff --exit-code`), so a commit that edits `pack/` without syncing fails CI. `.gitattributes` normalises to LF, so the gate is line-ending-safe on `ubuntu-latest`.
- **Kind:** issue · **Priority:** P1 · **Scope:** `.github/workflows/pack-consistency.yml`
- **Evidence:** the workflow never runs `sync-pack.ps1` or `verify-bundle.ps1`; the drift check exists only locally.
- **Remediation:** add a job that runs `verify-bundle.ps1` (or `sync-pack.ps1` followed by a `git diff --exit-code`) on PRs touching `pack/`.
- **Acceptance criteria:** a PR that edits `pack/` without re-syncing fails CI.
- **Validation:** push a branch with a `pack/` edit and no sync; confirm red. **Owner:** maintainer. **Next skill:** `/implement`. **Depends on:** none; land with FR-034. **Status:** proposed. **Carried from FR-011.**

## FR-034 — Run the Python suite and the graph gate in CI — **RESOLVED**
- **Resolved at revision 32.** `pack-consistency.yml` now runs `pytest tests -q` and `docs-graph.py validate`, and its path filters were broadened so edits to `tools/`, `tests/`, and `docs/` trigger it. Previously the suite existed but no workflow ran it.
- **Kind:** issue · **Priority:** P1 · **Scope:** `.github/workflows/pack-consistency.yml`
- **Evidence:** 107 Python tests and `docs-graph.py validate` pass locally and are absent from CI.
- **Remediation:** add `pytest tests/` and `docs-graph.py validate` steps.
- **Acceptance criteria:** both run on every PR; a deliberately broken `docs-graph.py` fails CI.
- **Validation:** break a test on a branch and confirm red. **Owner:** maintainer. **Next skill:** `/implement`. **Depends on:** shares the workflow with FR-033 — land together. **Status:** proposed. **Carried from FR-014.**

## FR-035 — Gate directive-range citations — **RESOLVED**
- **Resolved at revision 32.** Corrected `S1–S18`→`S1–S10` and `G1–G18`→`G1–G16` across 17 source files. **The control:** `check-consistency.py` gained `check_directive_ranges()`, which parses the highest directive actually defined in each standard and fails on any citation that outruns it. **Proved red-first.** A *shorter* sub-range is legitimate and is deliberately not flagged.
- **Kind:** issue · **Priority:** P2 · **Scope:** ~38 files citing `S1–S18` and `G1–G18`; `tools/check-consistency.py`
- **Evidence:** `specification-standards.md` defines S1–S10; `ui-archetype-grammar.md` defines G1–G16.
- **Remediation:** correct every citation to the real extent, then add a checker rule: for each standard, the highest directive defined must match every `X1–Xn` whole-range citation of that prefix.
- **Acceptance criteria:** no citation names a directive that does not exist; the checker fails when a standard gains or loses a directive without its citations following.
- **Validation:** add a directive to a standard without updating citations; confirm the checker fails. **Owner:** Documentation Steward. **Next skill:** `/implement`. **Depends on:** none. **Status:** proposed.

## FR-036 — Regenerate the documentation bundle — **PARTIALLY RESOLVED**
- **Partially resolved at revision 32 — and measuring it changed the item.** The proposal said "regenerate the stale bundle via `/document`". Establishing the evidence showed regeneration is not the fix, because the artifact is not a *stale render* — it is **fully static and hand-maintained**: 3,284 body bytes, unchanged by stripping `<script>`, reading no index at all. So it does not go stale between regenerations; it drifts continuously and silently.
- **Measured drift:** 10 hard-coded links against **48 graph artifacts (21% coverage)**, and **one link (`../skills.md`) pointing at a file that has never existed in this repo**. Nothing caught it because a static HTML page is not a graph node, so `docs-graph.py validate` never sees it.
- **Done:** the broken link now points at the real skill catalog, and `check-consistency.py` gained `check_static_page_links()`, which resolves every relative `href` on the page and fails on any that does not exist. **Proved red-first.**
- **Still open — and it is a design decision, not a defect fix, so it stops here for triage:** a hand-curated landing page duplicating `docs/index.html` (which is *derived* from the graph and therefore always current) is the exact anti-pattern V2 exists to prevent. The options are to **derive** `_site` from `docs-index.js`, or to **retire** it and redirect to the Explorer — the latter would change a deliverable `pack/OVERVIEW.md` currently promises, which is not a call to make unilaterally inside a review.

- **Kind:** issue · **Priority:** P2 · **Scope:** `docs/_site/`
- **Evidence:** newest file 2026-07-12; repository at revision 30 (2026-08-10), so the bundle omits revisions 19–30.
- **Remediation:** run `/document`; then add a freshness check so the bundle cannot silently lag.
- **Acceptance criteria:** the bundle covers the current revision; a gate flags a bundle older than the current `INSTALL.md` revision.
- **Validation:** compare bundle contents against the current skill and knowledge lists. **Owner:** Documentation Steward. **Next skill:** `/document`. **Depends on:** best after FR-035 so corrected ranges flow through. **Status:** proposed. **Carried from FR-019.**

## FR-037 — Purge the reverted capability from documentation — **RESOLVED**
- **Resolved at revision 32 — and the proposal was overstated.** Establishing the evidence showed the references in `architecture.md` and `privacy-review.md` were *already* explicitly historical (`was reverted`, `(historical)`, `No active model-orchestration work`), and `code-doc-join.md` is a **derived lens** whose rows are correct output, not a defect. The genuine scope was two lines: one present-tense claim in `docs/index.md` (*'the recovered model-orchestration control plane'*), and a status row in `architecture.md` still asserting the very deployment-map mismatch that FR-032 had just fixed. Both corrected; a stale `22 artifacts` count was re-verified to 42 in the same change (E17).
- **Kind:** issue · **Priority:** P2 · **Scope:** `docs/architecture.md`, `docs/index.md`, `docs/security/privacy-review.md`, `docs/lenses/code-doc-join.md`, and the 20260712 review/backlog/notes
- **Evidence:** ten `docs/` files reference `model-orchestration.md` / `model-router.py`, neither of which exists since `8801a47`.
- **Remediation:** remove or explicitly past-tense every live reference; keep `note-20260712-revert-model-orchestration.md` and the dated review as history, clearly marked as describing reverted work; regenerate `code-doc-join.md`.
- **Acceptance criteria:** no artifact describing current state references a deleted file; historical artifacts say so in their summary.
- **Validation:** grep `docs/` for both names and confirm every hit is explicitly historical. **Owner:** Documentation Steward. **Next skill:** `/document`. **Depends on:** none. **Status:** proposed.

## FR-043 — The adoption path had never been executed — **RESOLVED**
- **Kind:** issue · **Priority:** P0 in effect · **Raised and resolved at revision 33.** The revision-30 review flagged that `/addpacktorepo` *"has never been run end-to-end against a scratch repo"* but gave it no id, so it sat outside the backlog. Running it produced the most serious finding of the whole review.
- **Evidence (executed, not inferred):** a fresh install **fails `docs-graph.py validate` on the adopter's first command**, and fails whichever way the installing agent resolves it. The deployment map promised `docs/ui-guide.md` with **no source in the pack**, so an installing agent copies the source repo's version — whose `links` point at `design-language-docs-explorer` and `docs-index`, artifacts a fresh install does not have → **dangling link, exit 1**. Emptying the links does not help: the node is then an **orphan → also exit 1**. Separately, `docs/audit/audit-log.md` — the graph hub node **AL7 has always mandated** — was created by nothing; a fresh install produced `audit-data.js`, `audit-log.jsonl` and `index.html` but no `.md`, leaving the audit bundle invisible to the graph.
- **Why every gate stayed green:** all of it passes in *this* repo, because this repo has both files, hand-authored. The defect is only observable in a target repo. That is the class, now registered as **PACK-E**.
- **Fix:** ship `templates/ui-guide-hub.template.md` with portable frontmatter and one `relates-to` edge to the audit hub; bootstrap the AL7 hub in `audit-log.py`'s `render()` alongside the viewer (AL11 — same trigger). Links on the audit hub are deliberately empty: an **inbound** link clears the orphan check, established by execution rather than assumed.
- **Verified:** a clean install from the committed state now returns `validate` exit 0 with **2 artifacts, 0 problems, 0 orphans**, and `pack-doctor` reports **0 FAIL / 1 WARN / 6 PASS** (the WARN is the Windows interpreter note, working as designed).
- **Residual:** the install was executed mechanically against the deployment map. The *judgment* stages of `/addpacktorepo` — language detection, tier assessment, adapting to a repo that already has `CLAUDE.md` — remain unexercised. **Owner:** maintainer. **Next skill:** none.


## FR-039 — Triage the public explainer's blockers
- **Kind:** risk · **Priority:** P2 · **Scope:** `web/ai-forward-pack-explainer.html`
- **Evidence:** 3 unpkg scripts, 0 integrity hashes, 0 `:focus-visible`, 0 `aria-*`, 0 `prefers-reduced-motion`; blank without the CDN.
- **Remediation:** as ranked in `docs/reviews/ui-pack-explainer.md` — inline the runtime first (which also closes the supply-chain exposure), then the accessibility floor.
- **Acceptance criteria:** the page renders with JavaScript unavailable from the CDN; `ui-craft-gate.py --gate --a11y-obligation` passes.
- **Validation:** load with the CDN blocked; run the gate. **Owner:** UX & Accessibility. **Next skill:** `/ui-design` (elevate) then `/implement`. **Depends on:** none. **Status:** proposed.

## FR-040 — Ownership hygiene — **RESOLVED**
- **Resolved at revision 32.** The stray `@mallalieut` handle was corrected to `@timianmalloo` in the three live artifacts, and `.github/CODEOWNERS` now exists so `docs/**` ownership routes as V13 requires.
- **Kind:** todo · **Priority:** P3 · **Evidence:** no `CODEOWNERS`; three handles (`@timianmalloo` 35, `@maintainers` 5, `@mallalieut` 2).
- **Remediation:** settle on one canonical handle, normalise `owner:` frontmatter, add `CODEOWNERS` with a `docs/**` section (V13).
- **Acceptance criteria:** one handle across `docs/`; `CODEOWNERS` present. **Owner:** maintainer. **Next skill:** `/implement`. **Status:** proposed. **Carried from FR-018.**

## FR-041 — Define `npm test` — **RESOLVED**
- **Resolved at revision 32.** `package.json` now defines `test`, so `npm test` runs the Docs Explorer core suite instead of erroring.
- **Kind:** todo · **Priority:** P3 · **Evidence:** no `test` script; `npm test` fails.
- **Remediation:** alias `test` to the core suite. **Acceptance criteria:** `npm test` runs the JS core tests and exits 0. **Owner:** maintainer. **Next skill:** `/implement`. **Status:** proposed. **Carried from FR-016.**

## FR-042 — Allowlist noreply addresses in `scrub.py` — **RESOLVED**
- **Resolved at revision 32.** `scrub.py` now allowlists `@users.noreply.github.com` via a negative lookahead, so the GitHub noreply commit identity is no longer reported as a PII finding. **Verified it still flags a real address** in the same probe — the allowlist narrows, it does not disable.
- **Kind:** todo · **Priority:** P3 · **Evidence:** `*@users.noreply.github.com` is not allowlisted, so the repo's own commit trailers read as PII.
- **Remediation:** allowlist the pattern. **Acceptance criteria:** `scrub.py` over the repo reports no finding for a noreply trailer; a test covers it. **Owner:** maintainer. **Next skill:** `/implement`. **Status:** proposed. **Carried from FR-017.**

---

## Not raised (and why)

The Simplifier removed these as preference-not-defect: the `__pycache__` entry for the reverted `test_model_router` (untracked build noise); the `npm run` PATH failure (a local machine issue, not a repo defect — the tests pass when node is invoked directly); mixed dash conventions across knowledge docs (stylistic); and the absence of a LICENSE header in individual script files (the repository LICENSE covers it).
