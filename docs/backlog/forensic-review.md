---
id: forensic-review-backlog
title: "Forensic Review Backlog — AI-Forward repository (revisions 30 & 33)"
type: doc
status: superseded
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

---

# Revision-33 review — new findings (FR-044..FR-048)

## FR-044 — The deployment map still promises `.claude/commands/`, which nothing creates — **RESOLVED**
- **RESOLVED at revision 34.** The map row now reads *(none — Claude Code auto-discovers `.claude/skills/*/SKILL.md` by description)* and the worked "sample thin command" block, which invited adopters to hand-author unversioned duplicates of the skills, was deleted. **The control is the real fix:** `check_promised_paths()` in `check-consistency.py` now fails when any pack artifact names a repo path that neither exists, nor is claimed by a SKILL.md as created-at-runtime, nor is allowlisted with a stated reason. It caught this finding and FR-045 the moment it was written — red-first by construction — and would have caught FR-043.
- **Kind:** issue · **Priority:** P1 · **Confidence:** Verified · **Status:** proposed
- **Evidence:** `pack/adapters/INSTALL.md:139` — `| Thin command entry points | `.claude/commands/<name>.md` | ... |` — and `:215` gives a worked *"Sample thin command — `.claude/commands/specify.md`"*. The directory does not exist in this repo, and `tools/sync-pack.ps1` contains no `.claude/commands` branch (grep: no match).
- **Violated contract:** PACK-E — a deployment map promising an artifact the project does not ship. **This is the same class, in the same file, that FR-043 corrected at revision 33.** The fix stopped at `docs/ui-guide.md` and never swept the rest of the map, which is exactly the CI2 failure the register exists to prevent — the second occurrence of "the sweep stopped at the instance" in this project.
- **Consequence:** an adopting agent following the map creates a directory with no source, then authors thin command files from the worked sample — pure invention, unversioned, and drifting from the skills they duplicate.
- **Disconfirming check attempted:** searched `sync-pack.ps1` for both path separators, and checked whether Claude Code requires the directory. Skills in `.claude/skills/` are auto-discovered by description, so the entry points appear to be **unnecessary** rather than missing — which makes the *map* wrong, not the install.
- **Remediation:** either delete the row and the sample, or ship a generator. Prefer deletion (Simplifier) unless a concrete need is named.
- **Acceptance criteria:** every destination named in the deployment map either exists after a fresh install, or is explicitly marked *created by skill X at runtime*. **Validation:** re-run the FR-043 scratch-repo install and diff installed paths against the map. **Owner:** maintainer. **Next skill:** `/implement`.

## FR-045 — A second, contradictory deployment map inside an always-loaded document — **RESOLVED**
- **RESOLVED at revision 34.** All six paths corrected to the real deployment layout across `agent-rules-of-the-road.md`, `agent-body-of-knowledge.md` and `csharp-style-guide.md`. Because these are **vendored** foundation docs, the edit was recorded as a known intentional divergence in `FOUNDATION.md` and re-hashed with `foundation-check.py --update`; that gate is green again and the divergence is now visible rather than silent.
- **Kind:** issue · **Priority:** P1 · **Confidence:** Verified · **Status:** proposed
- **Evidence:** `pack/knowledge/agent-rules-of-the-road.md` §6 *"Deployment map — wiring these documents into the toolchain"* names paths that do not exist anywhere in this repo:

  | It says | Actually deployed as |
  |---|---|
  | `.github/instructions/knowledge.instructions.md` | `agent-body-of-knowledge.instructions.md` |
  | `.github/instructions/csharp.instructions.md` | `csharp-style-guide.instructions.md` |
  | `.github/instructions/loa.instructions.md` | `layered-optimized-architecture.instructions.md` |
  | `.github/instructions/tests.instructions.md` | `testing-strategy.instructions.md` |
  | `.github/knowledge/testing-strategy.md` | **`.github/knowledge/` does not exist at all** |
  | `.github/knowledge/engineering-governance.md` | same — no such directory |

- **Violated contract:** single source of truth. `INSTALL.md` is the authoritative deployment map; this is a **second map that disagrees with it**, and it sits in a document the managed block loads on **every session**, on both surfaces.
- **Consequence:** an agent grounding itself is told, authoritatively, to look for six files that do not exist. Worst case it concludes the install is broken and "repairs" it toward the wrong layout.
- **Disconfirming check attempted:** verified each path with `Test-Path` and by listing `.github/instructions/`; confirmed `.github/knowledge/` is absent. Also confirmed the §6 **persona row is correct** (`.github/agents/<persona>.agent.md`) — it in fact corroborates the naming FR-043 corrected, so the section is not uniformly stale.
- **Note on editability:** these are vendored foundation docs, but `FOUNDATION.md` maintains a **known-divergence list** and `foundation-check.py --update` re-hashes after an intentional edit. A precedent divergence is already recorded. So this is correctable, not frozen.
- **Acceptance criteria:** §6 either matches the real deployment map or is replaced by a pointer to `INSTALL.md`; `foundation-check.py` clean with the divergence recorded. **Validation:** assert every path named in §6 resolves. **Owner:** maintainer. **Next skill:** `/implement`.

## FR-046 — Seven deployed scripts have no tests and no gate, including the PII control — **RESOLVED**
- **RESOLVED at revision 34** for the two load-bearing controls. `tests/docs_explorer/test_deployed_scripts.py` asserts `scrub.py` on a **true positive** (a real address is reported), a **true negative** (the GitHub noreply identity is not), and clean text; and `design-lint.py` on a resolvable vs unresolvable `{token}`. The design-lint fixture initially failed because it **guessed** the DESIGN.md contract; reading `design-lint.py` showed it also requires a `typography:` block. Suite 119 → 126. The three setup scripts (`graphify`, `obsidian`, `visual-assets`) remain untested — they are interactive installers, and are left as a smaller, recorded residual rather than being given theatre tests.
- **Kind:** risk · **Priority:** P1 · **Confidence:** Verified · **Status:** proposed
- **Evidence:** of the 12 scripts deployed to every adopting repo, gate/test coverage is:

  | Script | Gated by | Tests |
  |---|---|---|
  | `docs-graph.py` · `audit-log.py` · `pack-doctor.py` · `bounded_process.py` · `foundation-check.py` | yes | yes (except foundation-check) |
  | **`scrub.py`** · **`design-lint.py`** · **`ui-craft-gate.py`** · **`prompt-log.py`** · `graphify-setup.py` · `obsidian-setup.py` · `visual-assets-setup.py` | **none** | **none** |

- **Violated contract:** the pack's own doctrine — CI6 (a lesson only counts once it is a test or a gate) and the Test Architect's hard veto (a correctness claim with no verification path). **`scrub.py` is named in `responsible-ai-policy.md` §4 as the PII/secret first-pass control, and `design-lint.py` is the U3a token control.** The pack ships controls that are themselves unverified.
- **Consequence:** a regression in the redaction regexes or the token resolver ships silently to every adopting repo, and the first evidence is a leaked address or a drifted design system.
- **Disconfirming check attempted:** smoke-ran all seven; six exit 0 on `--help`, so they are not obviously broken — the gap is *proof*, not an observed defect. That is why this is filed as **risk**, not **issue**. (The seventh is FR-047.)
- **Acceptance criteria:** each of the four load-bearing scripts (`scrub`, `design-lint`, `ui-craft-gate`, `prompt-log`) has a test asserting both a true positive and a true negative, and runs in `pack-consistency.yml`. **Validation:** delete a regex and confirm a test fails. **Owner:** maintainer. **Next skill:** `/implement`.

## FR-047 — `prompt-log.py --help` crashes on Windows; the console-encoding fix was never swept — **RESOLVED**
- **RESOLVED at revision 34.** The stdout/stderr guard is applied to **all seven** scripts that print non-ASCII, not just the one that crashed — the sweep the finding was about. `test_help_exits_zero_under_cp1252` asserts every deployed script survives `PYTHONIOENCODING=cp1252`, and was **proved red-first**: removing the guard from `prompt-log.py` fails it, restoring it passes. (The first red-first attempt appeared to pass; the strip regex had silently failed and the guard was still present — so the proof was redone rather than trusted.)
- **Kind:** issue · **Priority:** P2 · **Confidence:** Verified · **Status:** **RESOLVED at revision 34**
- **Evidence:** `python pack/scripts/prompt-log.py --help` exits 1 with `UnicodeEncodeError: 'charmap' codec can't encode character '\u2191'` — the help text contains `↑ ↓ → ← ▸ ▾`, none of which exist in cp1252, the default Windows console encoding.
- **Scope, established by sweeping rather than assuming:** seven pack scripts contain non-ASCII and **not one of them guarded stdout**. *(Correction, made while remediating: this first read "`pack-doctor.py` alone guards stdout". That came from a loose heuristic — the file merely mentions `PYTHONIOENCODING` — rather than from opening it. Reading it showed no guard at all, which makes the finding **stronger**: the invariant was entirely unenforced.)* They survive only because their glyphs (`—`, `·`, `…`, `•`) happen to exist in cp1252 — so this is not a near-miss, it is an **unenforced invariant**. `scrub.py` additionally renders its masked output as mojibake on a Windows console, degrading the control's legibility.
- **Violated contract:** PACK-C (documented command assumed portable), now in code rather than prose — and CI2 — though the corrected reading is that **nobody had fixed it anywhere**; the class was simply never noticed, because six of seven scripts fail silently only on glyphs they do not happen to use.
- **Consequence bounded honestly:** `list`, `search`, `add` and `browse` all work (verified, exit 0). Only `--help` dies — but `--help` is the first thing a new adopter runs, and the two skills it backs are the pack's prompt-reuse surface.
- **Disconfirming check attempted:** ran every documented subcommand, not just the failing one, specifically to avoid inflating the severity.
- **Acceptance criteria:** every deployed script guards stdout; `prompt-log.py --help` exits 0 on Windows; a test asserts it. **Validation:** run each script's `--help` under `PYTHONIOENCODING=cp1252`. **Owner:** maintainer. **Next skill:** `/implement`.

## FR-048 — A generated artifact excluded from the only gate that checks generated artifacts — **RESOLVED**
- **RESOLVED at revision 34.** `build-web-index.py` no longer stamps wall-clock time. It uses `SOURCE_DATE_EPOCH` when set (honouring reproducible-builds), otherwise the newest mtime across `pack/` — so the stamp moves when the **content** does, not merely because time passed. **Verified:** two consecutive syncs two seconds apart now produce a byte-identical file. With determinism established, `web/` was added to the drift-gate scope at both call sites, so the generated public index is finally covered by the gate that exists to prove generated surfaces match their source. The latent trap noted in the finding — that adding `docs-graph.py derive` to sync would break the gate on a timestamp-only diff — is unchanged and remains a documented hazard rather than a defect.
- **Kind:** risk · **Priority:** P2 · **Confidence:** Verified · **Status:** proposed
- **Evidence:** `web/pack-index.js` is generated (`// Generated by tools/build-web-index.py — do not hand-edit`) and is rebuilt by `sync-pack.ps1`. The FR-033 drift gate diffs `.claude .github/instructions .github/prompts .github/agents docs CLAUDE.md AGENTS.md` — **`web/` is not in scope.** It cannot simply be added: the file embeds `"generated": "<ISO timestamp>"`, so a re-sync always produces a one-line diff (verified: `1 file changed, 1 insertion(+), 1 deletion(-)`, the timestamp alone).
- **Violated contract:** the repository's foundational invariant — `pack/` is source, generated surfaces are derived — is gated everywhere except here.
- **Consequence:** a `pack/` change committed without a sync leaves the public explainer's index silently stale, and nothing catches it. Latent trap: three further timestamped artifacts (`docs/docs-index.js`, `docs/audit/audit-data.js`, `docs/_meta.json`) sit *inside* the gate scope and are safe **only because `sync-pack.ps1` does not regenerate them** — adding `docs-graph.py derive` to sync, a natural change, would break the drift gate permanently with a timestamp-only diff.
- **Disconfirming check attempted:** simulated the CI gate faithfully (`sync` then `git diff --exit-code` over the exact scope) — **exit 0**, so the gate is sound today. This is filed as *risk*, not *issue*; the initial hypothesis that the gate always fails was **disconfirmed**.
- **Remediation:** make the generator's timestamp deterministic (content hash, or omit), then add `web/` to the gate scope. Add a comment at the `docs-graph derive` call site recording why sync must not regenerate the index.
- **Acceptance criteria:** `web/` is in the drift-gate scope and a no-op sync produces no diff. **Validation:** sync twice, diff. **Owner:** maintainer. **Next skill:** `/implement`.

