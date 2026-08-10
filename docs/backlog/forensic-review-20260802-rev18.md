---
id: forensic-review-20260802-backlog
title: "Forensic Review Backlog — AI-Forward repository (revision 18)"
type: doc
status: proposed
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [backlog, forensic-review, ci, consistency, supply-chain]
links:
  - { to: forensic-review-20260802, rel: refines }
  - { to: architecture, rel: depends-on }
  - { to: forensic-review-backlog-20260712, rel: supersedes }
review-by: "2026-11-02"
review-suggested: []
summary: >-
  The proposed backlog from the revision-18 forensic review of AI-Forward at commit 53e3afe —
  ten findings (FR-011..FR-020) ordered into four phases, plus FR-008 carried forward and
  FR-010 closed into FR-020. All items are status `proposed` and await human triage; none has
  been implemented.
---

# Forensic Review Backlog — AI-Forward repository (revision 18)

**Source review:** [`forensic-review`](../reviews/forensic-review.md) · **Target commit:** `53e3afe` · **Status:** every item is `proposed`; **nothing here has been implemented.**

> **Triage first.** Per the `/forensicreview` contract this backlog stops at proposal. Use `/investigate` before fixing any item whose cause is not already proven here; FR-011, FR-012, FR-016 and FR-017 carry reproductions and can go straight to `/implement` once approved.

## Phase order

| Phase | Goal | Items |
|---|---|---|
| **1 — Close the enforcement gap** | Make the gates gate what they claim | FR-011, FR-014, FR-008 |
| **2 — Fix the propagating defects** | Stop shipping broken or partial output to consuming repos | FR-020, FR-012, FR-015 |
| **3 — Restore documentation truth** | Make every count and list self-consistent | FR-013, FR-019 |
| **4 — Hygiene** | Low-risk quality-of-life | FR-016, FR-017, FR-018 |

**Highest improvement-to-effort item: FR-011.** The check already exists in `verify-bundle.ps1`; it is a handful of CI lines to run it where it matters.
**Highest user-visible impact: FR-020.** Copilot users are missing 12 of 23 personas, including both vetoes revision 18 introduced.

---

## FR-011 — Gate source↔install drift in CI

- **Kind / priority / status:** issue · **P1** · proposed
- **Evidence:** `docs/reviews/forensic-review.md` §4.1 — a detached worktree with `pack/knowledge/rigor-protocol.md` drifted from `.claude/knowledge/rigor-protocol.md` passed `check-consistency.py`, `foundation-check.py` and the eval gate, all exit 0. `tools/verify-bundle.ps1` step 5 performs the check but is absent from `.github/workflows/pack-consistency.yml`. `check-consistency.py` compares counts, parity, managed-block lists and prose — never generated-tree content.
- **Affected scope:** the repository's foundational invariant; propagates to every consuming repo via `/updatepack`, which copies the *generated* `.claude/` tree.
- **Consequence:** a contributor who edits `pack/` and forgets `sync-pack.ps1` merges a stale install, and the stale file is then distributed outward as the current standard.
- **Recommended remediation:** add a CI step that runs `sync-pack.ps1` and fails if it produces any change (`git diff --exit-code` after sync, ignoring the `web/pack-index.js` `generated` timestamp — see note). Extend the workflow `paths:` filter to include `.claude/**`, `.github/instructions/**`, `.github/prompts/**`, `.github/agents/**` and `docs/**`, so edits to the generated trees are gated too.
- **Acceptance criteria:**
  1. A commit that edits any `pack/**` file without re-syncing **fails** CI with a message naming the drifted path.
  2. A correctly synced commit passes.
  3. A PR touching only `.claude/**` triggers the consistency workflow.
  4. The check is immune to the `web/pack-index.js` regenerated-timestamp-only diff (which is not real drift and must not cause a false failure).
- **Validation:** fault injection — replay the review's worktree reproduction in CI and assert nonzero exit.
- **Dependencies:** none. Supersedes the first bullet of FR-008.
- **Suggested owner:** Release Engineer
- **Next skill:** `/implement`

## FR-012 — `docs-graph.py rollup` emits links relative to the wrong base

- **Kind / priority / status:** issue · **P2** · proposed
- **Evidence:** `docs/ai-forward-pack/scripts/docs-graph.py:1135-1136` (`cmd_rollup`) builds each link with `os.path.relpath(a["_fs_path"], os.path.abspath(args.root))` — relative to the **root**, not to the directory of the document being written. Computed proof: for target `docs/design/rai-and-scrub.md` written into `docs/security/threat-model.md`, the emitted `design/rai-and-scrub.md` does **not** resolve; the correct `../design/rai-and-scrub.md` does. Three broken links exist today inside the `<!-- BEGIN GENERATED -->` blocks of `docs/security/threat-model.md` and `docs/security/privacy-review.md`.
- **Affected scope:** every repository that installs the pack. `/design` mandates refreshing these rollups, and the output always lives one directory below the root.
- **Consequence:** every generated link in every threat model and privacy review is broken. Test coverage does not catch it: the only rollup test (`test_docs_graph.py:34`) asserts UTF-8 encoding behaviour on Windows, never link resolution.
- **Recommended remediation:** compute the link relative to `os.path.dirname(output_file)`. Add a regression test that writes a rollup into a subdirectory and asserts every emitted link resolves from the output file's location. Regenerate the two affected rollups afterwards.
- **Acceptance criteria:**
  1. A rollup written into `docs/security/` emits `../design/x.md` and the path resolves.
  2. A rollup written into the root still emits `design/x.md` and resolves.
  3. A test fails on the pre-fix code (red observed) and passes after.
  4. `docs/security/threat-model.md` and `privacy-review.md` contain zero broken relative links.
- **Validation:** the new unit test, plus a repo-wide relative-link scan returning zero broken links.
- **Dependencies:** none
- **Suggested owner:** Documentation Steward + the Python developer lens
- **Next skill:** `/implement`

## FR-013 — Gate skill *lists*, not just counts

- **Kind / priority / status:** issue · **P2** · proposed
- **Evidence:** `check-consistency.py` has `check_managed_blocks` (which *does* verify every skill appears in the managed-block lists) and `check_prose` (which verifies only *totals*). Consequence, measured at `53e3afe`: `README.md` — count says 18, `/ui-design` mentions = **0**; `.github/copilot-instructions.md` — heading reads "### The 18 skills and their natural order", `/ui-design` mentions = **0**; `docs/index.md` — still reads "**The 17 skills:** fourteen reasoning workflows", `/ui-design` mentions = **0**. `docs/architecture.md:61` still renders "(the 17 skills)". Neither `docs/index.md` nor `docs/architecture.md` is scanned by the checker at all.
- **Affected scope:** the repository's own documentation, including `.github/copilot-instructions.md`, which is Copilot's always-on repo instruction.
- **Consequence:** a document that states a count it does not enumerate passed the gate. Because the omitted file is an always-on instruction, an agent working in this repo is not told `/ui-design` exists — the capability is invisible at exactly the surface designed to advertise it.
- **Recommended remediation:** extend `check_prose` (or add `check_skill_lists`) to assert that any file stating a skill total also names every skill; add `docs/index.md` and `docs/architecture.md` to the scanned set. Then correct the four documents.
- **Acceptance criteria:**
  1. Removing any single skill name from `README.md`, `docs/index.md`, or `.github/copilot-instructions.md` fails `check-consistency.py`.
  2. All four documents name all 18 skills, including `/ui-design`.
  3. `docs/architecture.md` no longer states a hard-coded skill count, or states the correct one.
  4. The new check is exercised by `test_check_consistency.py`.
- **Validation:** mutation fixture (delete one skill name → expect nonzero exit).
- **Dependencies:** none
- **Suggested owner:** Documentation Steward + Test Architect
- **Next skill:** `/implement`

## FR-014 — Run the tests and the graph gate that already exist

- **Kind / priority / status:** issue · **P2** · proposed
- **Evidence:** full read of `.github/workflows/pack-consistency.yml` — it runs `check-consistency.py`, `npm run test:docs-explorer:core`, `foundation-check.py`, and an inline eval-well-formedness script. It does **not** run: `pytest` (7 modules, 107 assertions, covering `audit-log.py`, `docs-graph.py`, `pack-doctor.py`, `bounded_process.py`, `check-consistency.py`, `run-evals.py`, the benchmark harness); the Playwright suite (`tests/docs_explorer/docs_explorer.spec.js`, 3 browser projects); or `docs-graph.py validate` / `freshness`. The pack **ships** `pack/ci/docs-health.yml` — a graph-health workflow — to consuming repos but does not apply it to itself. All gates run only on `ubuntu-latest`, so `sync-pack.ps1` and `verify-bundle.ps1` are never exercised in CI on any platform.
- **Affected scope:** the release gate.
- **Consequence:** a regression in any of the nine deployable scripts, in the Explorer's browser behaviour, or in graph health merges green. The pack asks consumers to run a gate it does not run on itself.
- **Recommended remediation:** add `pytest`, `docs-graph.py validate`, and `docs-graph.py freshness --gate warn` to `pack-consistency.yml`; add the Playwright suite (or a documented, deliberate exclusion with rationale if browser-download cost is the reason); add a Windows job covering the PowerShell tooling.
- **Acceptance criteria:**
  1. `pytest tests -q` runs in CI and a deliberately broken assertion fails the build.
  2. `docs-graph.py validate` runs in CI and a dangling link fails the build.
  3. Either the Playwright suite runs in CI, or `pack-consistency.yml` carries a comment stating why it does not and where it does run.
  4. `sync-pack.ps1` + `verify-bundle.ps1` execute on a Windows runner.
- **Validation:** fault injection per criterion.
- **Dependencies:** shares a workflow file with FR-011 — land together.
- **Suggested owner:** Release Engineer + Test Architect
- **Next skill:** `/implement`

## FR-015 — Pin actions in the privileged workflow and in the shipped CI template

- **Kind / priority / status:** risk · **P2** · proposed
- **Evidence:** `.github/workflows/pages.yml` uses `actions/checkout@v4`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4` — four floating tags — while holding `permissions: pages: write, id-token: write`. The other two workflows pin every action by 40-character SHA. `pack/ci/docs-health.yml`, shipped to every consuming repo, also uses `actions/checkout@v4` and `actions/setup-python@v5` unpinned.
- **Affected scope:** the Pages deployment (this repo) and the CI of every repo that installs the pack.
- **Consequence:** a retagged or compromised action would execute in the repository's only workflow able to mint an OIDC token and publish to Pages. Likelihood is low — all four are first-party `actions/*` — but the repo's own Security lens requires provenance pinning, and the inconsistency means the standard is stated and not self-applied.
- **Recommended remediation:** pin all four `pages.yml` actions by SHA with a `# vN` comment, matching the convention already used in the other two workflows; do the same in `pack/ci/docs-health.yml` and note the pinning expectation in `INSTALL.md` so consumers inherit it.
- **Acceptance criteria:**
  1. Every `uses:` in every workflow in `.github/workflows/` matches `@[0-9a-f]{40}`.
  2. Every `uses:` in `pack/ci/*.yml` matches the same pattern.
  3. Pages still deploys successfully after pinning.
- **Validation:** a repo-wide grep asserting no floating `uses:` tags; one successful Pages deploy post-change.
- **Dependencies:** none
- **Suggested owner:** Security & Identity Architect + Release Engineer
- **Next skill:** `/implement`

## FR-016 — Define `npm test`

- **Kind / priority / status:** issue · **P3** · proposed
- **Evidence:** `npm test` at `53e3afe` returns `npm error Missing script: "test"`. `package.json` defines `test:docs-explorer:core`, `test:docs-explorer:browser`, `test:docs-explorer`, and `benchmark:docs-explorer:browser`.
- **Affected scope:** contributor onboarding; any tooling that assumes the npm convention.
- **Consequence:** the universal entry point errors. A newcomer reasonably concludes the repo has no tests.
- **Recommended remediation:** add `"test": "npm run test:docs-explorer"` (or point it at the core suite if browser downloads should stay opt-in) and mention the Python suite in `README.md` beside it.
- **Acceptance criteria:** 1. `npm test` exits 0 on a clean tree. 2. `README.md` states how to run both the node and the Python suites.
- **Validation:** run `npm test`.
- **Dependencies:** none
- **Suggested owner:** the JavaScript/tooling maintainer
- **Next skill:** `/implement`

## FR-017 — Allowlist `*@users.noreply.github.com` in `scrub.py`

- **Kind / priority / status:** issue · **P3** · proposed
- **Evidence:** `scrub.py --check docs pack` exits **1** with 2 findings, both the string `docs-bot@users.noreply.github.com` at `documentation-bundle.template.md:141` (source and deployed copy) — inside a **commented-out** CI example, and the canonical GitHub Actions bot identity rather than personal data.
- **Affected scope:** `scrub.py` and any CI that adopts it.
- **Consequence:** the tool is permanently red on the pack's own content, so `scrub.py --check` cannot be wired into CI as the Responsible-AI policy envisages — and a permanently-red check trains people to ignore it.
- **Recommended remediation:** allowlist the `users.noreply.github.com` domain (and, optionally, addresses inside fenced/commented blocks); add a fixture asserting the bot address is not flagged while a real address still is.
- **Acceptance criteria:** 1. `scrub.py --check docs pack` exits 0 at a clean commit. 2. A genuine address in the same file **is** still flagged (the check must not be weakened into uselessness).
- **Validation:** the new fixture, red-observed before the change.
- **Dependencies:** none
- **Suggested owner:** Privacy & Data Governance lens
- **Next skill:** `/implement`

## FR-018 — Ownership hygiene: one handle, plus CODEOWNERS

- **Kind / priority / status:** todo · **P3** · proposed
- **Evidence:** across 34 graph artifacts the `owner:` field holds three values — `@timianmalloo` (31), `@mallalieut` (`docs/architecture.md`, `docs/index.md`), `@maintainers` (`docs/proof/docs-explorer-redesign.md`). No `.github/CODEOWNERS` exists, though `knowledge-visualization.md` V13 states ownership should "pair with a `docs/**` section in CODEOWNERS so doc changes route to them".
- **Affected scope:** documentation governance.
- **Consequence:** ownership does not route. V13's freshness/ownership model assumes a resolvable owner; two of the three handles will not resolve to a reviewer.
- **Recommended remediation:** normalise to one handle (or confirm `@mallalieut` is a real distinct account and keep it deliberately); add `.github/CODEOWNERS` with a `docs/**` rule.
- **Acceptance criteria:** 1. Every `owner:` resolves to a real GitHub account or team. 2. `CODEOWNERS` exists and routes `docs/**`. 3. `docs-graph.py inventory` reports no unowned artifact.
- **Validation:** manual account check + a CODEOWNERS syntax validation on PR.
- **Dependencies:** none
- **Suggested owner:** Documentation Steward
- **Next skill:** `/document`

## FR-019 — Regenerate the stale `/document` bundle

- **Kind / priority / status:** todo · **P3** · proposed
- **Evidence:** `docs/_site/index.html` last modified **2026-07-12**, predating revisions 17 and 18 (four new knowledge docs, one new skill, three new templates).
- **Affected scope:** the generated documentation bundle.
- **Consequence:** the browsable bundle understates the pack. Low impact — `pages.yml` publishes `web/`, not `docs/_site/`, so the public explainer is current; only the local bundle is stale.
- **Recommended remediation:** run `/document` to regenerate the bundle; consider a freshness check so the bundle's age relative to `HEAD` is visible.
- **Acceptance criteria:** 1. The bundle lists all 18 skills and all 28 knowledge docs. 2. A staleness signal exists (a `documented_sha` baseline as the bundle template already describes).
- **Validation:** regenerate and diff; confirm counts.
- **Dependencies:** best done after FR-013 so the corrected counts flow through.
- **Suggested owner:** Documentation Steward
- **Next skill:** `/document`

## FR-020 — Deploy all 23 personas to the Copilot surface

- **Kind / priority / status:** issue · **P2** · proposed
- **Evidence:** `docs/reviews/forensic-review.md` §4.2. `.claude/agents/` holds **23** files; `.github/agents/` holds **11**. Missing from Copilot: `ai-systems-engineer`, `data-persistence-architect`, `documentation-steward`, `domain-researcher`, `mobile-app-developer`, `native-desktop-developer`, `orchestrator`, `privacy-data-governance`, `product-strategist`, `release-engineer`, `ux-accessibility`, `ux-researcher-ia`. `pack/adapters/INSTALL.md` L91–L92 maps **both** peer and adversary agents to `.github/agents/<name>.agent.md`, and §1.2 specifies the transform ("strip the `tools:` line"); `tools/sync-pack.ps1` populates `.claude/agents/` from both adapter directories but `.github/agents/` from `adapters/copilot/agents/` only, so the transform is documented and never executed. `AGENTS.md` tells Copilot users "Agents in `.github/agents/`".
- **Affected scope:** the Copilot tool surface, in this repo and in every repo that installs the pack.
- **Consequence:** Copilot users get 11 of the 23 advertised lenses and cannot `@`-mention the rest — including the **Data & Persistence Architect** (owner of the data-modelling standard and its migration hard veto) and **UX & Accessibility** (lead of `/ui-design`, holder of the accessibility hard veto). Revision 18's wiring is therefore only half-live on one of the two supported tools. `INSTALL.md` also contradicts itself: L108 says the three peer agents are "described in `knowledge/collaborative-personas.md`" instead, which conflicts with L91 and does not account for the other nine.
- **Recommended remediation:** decide the intended contract first, then make code and docs agree — do **not** silently pick one.
  - *Option A (recommended — matches the map and §1.3 "fit for both"):* extend `sync-pack.ps1` to copy `adapters/claude-code/agents/*.md` into `.github/agents/<name>.agent.md`, applying the §1.2 transform (strip `tools:`). Remove the contradictory L108 sentence.
  - *Option B:* if the 12 are deliberately Claude-only, correct L91–L92 to say so, state the rationale for each, and change `AGENTS.md` so it does not imply the full roster is `@`-mentionable under Copilot.
- **Acceptance criteria:**
  1. `.claude/agents/` and `.github/agents/` either hold the same persona set, **or** `INSTALL.md` states the exact intended difference and the reason for each exclusion.
  2. `check-consistency.py` fails when the two surfaces diverge from the documented contract (this is the agent-parity check the prior FR-010 asked for).
  3. No `.github/agents/*.md` carries a `tools:` line (currently true — must stay true after any copy is added).
  4. `INSTALL.md` contains no self-contradiction about where peer agents are deployed.
- **Validation:** extend `test_check_consistency.py` with a fixture that removes one agent from one surface and asserts nonzero exit.
- **Dependencies:** shares the checker with FR-013 — land together.
- **Suggested owner:** Enterprise Architect + Documentation Steward
- **Next skill:** `/design` (the contract decision is Option A vs B) → then `/implement`

---

## Carried forward from the 2026-07-12 review

## FR-008 — Make bundle/CI consistency a real oracle *(carried forward)*

- **Kind / priority / status:** issue · **P2** · proposed
- **Update at this review:** **partially superseded.** The orchestration-specific criteria (router-key parity, `test_model_router.py`) are void — that capability was reverted in `8801a47` and the test no longer exists. The durable half is now proven and split out: the dirty-sync gap is **FR-011**, the missing Python/cross-platform coverage is **FR-014**.
- **Residual scope:** the *principle* — `verify-bundle.ps1` should fail loudly rather than print advisory text, so "BUNDLE CONSISTENT" means every check actually gated. Retain as the umbrella item; close it when FR-011 and FR-014 land.
- **Suggested owner:** Release Engineer + Test Architect
- **Next skill:** `/implement`

## FR-010 — Reconcile remaining public documentation *(CLOSED — resolved into FR-020)*

- **Status:** **closed at this review.** The model-orchestration portions were voided by the revert in `8801a47`. The residual concern — Copilot peer-agent deployment-map parity — was carried at *Inferred* confidence by the prior review; it has now been **verified by measurement** (11 of 23 personas on the Copilot surface) and re-scoped as **FR-020**, which carries the evidence, the contract decision, and the acceptance criteria.
- **No action required on FR-010 itself.** Triage FR-020 instead.
