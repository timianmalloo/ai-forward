---
id: forensic-review-rev48-backlog
title: "Forensic Review Backlog — revision 48"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [backlog, forensic-review, triage, ci, derived-artifacts, supply-chain]
links:
  - { to: forensic-review-rev48, rel: refines }
  - { to: forensic-review-rev48-proof, rel: tested-by }
  - { to: architecture, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
  - { to: forensic-review-rev42-backlog, rel: supersedes }
review-by: "2026-11-24"
review-suggested: []
summary: >-
  Ten proposed items (FR-058..FR-067) from the revision-48 forensic review at commit
  c27f83d, ordered into four phases. PHASE 1 IS SHIPPED at 7bc0cf2 — FR-058, FR-059 and
  FR-065 resolved, FR-060's instance half resolved, and verify-bundle.ps1 now reports
  BUNDLE CONSISTENT, all 9 gates passing, up from 2 of 9 failing. FR-065's control was
  observed red before green and caught a 14-off count no gate could previously see.
  Six items remain open, led by FR-060's class half (the ordering hazard is still live)
  and FR-061, the root-cause control. An external Test Architect pass blocked the first
  draft because two acceptance criteria could not fail; those were rewritten, and two of
  its findings became FR-065 and FR-067.
---

# Forensic Review Backlog — revision 48

> **Triage first.** Per the `/forensicreview` contract this backlog stops at **proposal**. Use `/investigate` before fixing any item whose cause is not already established here, and `/implement` only once the governing acceptance criteria are approved. Every item below already carries a Verified root cause, so `/investigate` is *not* required for FR-058..FR-063; it is required for anything the fix uncovers.

**Source review:** `docs/reviews/forensic-review-rev48.md` — commit `c27f83d`, branch `main`, clean tree.
**Carried forward:** nothing. All nine revision-42 items were triaged and dispositioned at revision 43.
**State at time of writing:** `pwsh tools/verify-bundle.ps1` → `BUNDLE INCONSISTENT - 2 of 9 gate(s) failed`. CI run `32987223699` failed on `main`.

> ## Phases 1 & 2 — SHIPPED (2026-08-26)
>
> **Phase 1 at `7bc0cf2`:** FR-058, FR-059, FR-065 (both halves) and FR-060's instance half RESOLVED. Gate 1 green.
>
> **Phase 2:** FR-061 and FR-067 RESOLVED; FR-060's class half shipped as **detection** (both derived artifacts now drift-gated at gate 1, previously only the portal). Every control was **observed red before green** — FR-065's rules took findings 5→6; FR-061's control failed on both front-door files; FR-067 failed on a renamed local gate *and* on a removed CI step; FR-060's detection named both dependents after a derive-only run.
>
> **One change was reverted rather than shipped.** FR-060's *source-removal* half — having `sync-pack.ps1` derive before building the dependents — put `docs/docs-index.js` inside gate 2's diff scope, where its wall-clock `generated` field made CI **permanently red**. That is the PACK-I / FR-048 timestamp class, already solved in the sibling generator. Reverted and raised as **FR-068**; the trap is mitigated by detection, not closed at source.
>
> **Still open:** FR-062, FR-063 (Phase 3), FR-064, FR-066 (Phase 4), FR-068.

## Phases

| Phase | Goal | Items | Ships as |
|---|---|---|---|
| **1 — Contain** | Turn gate 1 green | FR-058, FR-059, FR-060 (instance half), FR-065 | one commit |
| **2 — Prevent** | Stop the class recurring | FR-060 (class half), FR-061, FR-067 | one commit each |
| **3 — Close the release & supply-chain gaps** | Publication and provenance | FR-062, FR-063 | one commit each |
| **4 — Record hygiene** | Truth of the record | FR-064, FR-066 | one commit |

> **Corrected after the adversarial gate.** An earlier draft said "Phase 1 is three edits that turn a red protected branch green". That was **wrong** on both counts. `check-consistency.py` emits the portal-staleness itself as gate-1 finding #5, so FR-060's instance half is required for gate 1 — and FR-065 is a fourth gate-1-class count defect the first draft missed entirely. Phase 1 is **four** items, and it turns *gate 1* green; gate 2 needs FR-060's instance half too, and only a CI run on the fix commit proves gates 3–7.

---

## Phase 1 — Contain

### FR-058 · issue · P1 — Correct `INSTALL counts.knowledge_docs` to 38
- **Affected scope:** `pack/adapters/INSTALL.md:6` (and its synced copy `docs/ai-forward-pack/INSTALL.md`)
- **Evidence:** review §3 FR-058. Gate 1: `INSTALL counts.knowledge_docs = 39, filesystem has 38`. `check-consistency.py:57` excludes `FOUNDATION.md`; `pack/OVERVIEW.md:59` independently states `38 docs (+FOUNDATION manifest)`.
- **Consequence:** CI red on `main`; the adopter refresh contract claims a knowledge doc that does not exist.
- **Recommended remediation:** set `knowledge_docs: 38`. Do **not** add a knowledge doc to justify 39 — the native-UI change extended three existing docs and correctly added none. Leave `templates: 27` and `scripts: 18`; both are right.
- **Acceptance criteria (falsifiable):** `python tools/check-consistency.py` emits no finding containing `INSTALL counts.knowledge_docs`; the value equals `len([f for f in pack/knowledge/*.md if f != "FOUNDATION.md"])`.
- **Validation:** `python tools/check-consistency.py`
- **Dependencies:** none · **Owner:** @timianmalloo · **Next skill:** `/implement` · **Status:** **RESOLVED at `7bc0cf2`** — set to 38; gate 1 emits no `INSTALL counts.knowledge_docs` finding

### FR-059 · issue · P1 — Update the three `26 templates` strings to 27
- **Affected scope:** `pack/OVERVIEW.md:52`, `pack/OVERVIEW.md:61`, `.github/copilot-instructions.md:50`
- **Evidence:** review §3 FR-059. Three gate-1 findings of the form `'26 templates' implies templates=26, filesystem has 27`.
- **Consequence:** CI red; the overview a new adopter reads under-counts the artifact set.
- **Recommended remediation:** change `26` → `27` at all three sites. **Note the asymmetry:** the two `pack/OVERVIEW.md` sites are pack source and propagate via `sync-pack.ps1`; `.github/copilot-instructions.md` is hand-maintained and outside sync, so it must be edited directly and will drift again independently.
- **Acceptance criteria:** `python tools/check-consistency.py` emits no `implies templates=` finding; and `Select-String -Path pack/**,.github/copilot-instructions.md -Pattern '(?<![\w-])26\s+(artifact\s+)?templates'` returns **zero** hits. The grep is scoped to `pack/**` and `.github/copilot-instructions.md` explicitly — an earlier draft said "zero hits outside archived review history" without defining the exclusion set, which made it satisfiable by relabelling a file, and which the review artifacts themselves violate by quoting the string.
- **Validation:** `python tools/check-consistency.py`
- **Dependencies:** none · **Owner:** @timianmalloo · **Next skill:** `/implement` · **Status:** **RESOLVED at `7bc0cf2`** — all three sites now read 27; gate 1 emits no `implies templates=` finding

### FR-060 · issue · P1 — Regenerate the two stale derived artifacts and fix the regeneration order
- **Affected scope:** `docs/portal/portal-data.js`, `web/pack-index.js`; ordering in `tools/sync-pack.ps1` and the skills' last-action contract
- **Evidence:** review §3 FR-060. `sync-pack.ps1` + `git diff --quiet` → exit 1 naming both files. Portal diff = exactly the `spec-design-slice-rename` node + 2 edges. Generator proven deterministic (identical SHA-256 across two runs), so this is staleness, not non-determinism.
- **Consequence:** the portal half is **gate 1 finding #5** (`check-consistency.py` regenerates the portal and asserts byte-identical output — `README.md:109`), **and** both files fail gate 2. Only `web/pack-index.js` is latent behind gate 1. **Corrected after the adversarial gate:** the first draft called the whole item "latent", which made Phase 1 look like three edits that turn the branch green. It is not — without this item's instance half, gate 1 stays red.
- **Acceptance criteria:** on a clean tree, `pwsh tools/sync-pack.ps1` **then** `git diff --quiet -- .claude .github/instructions .github/prompts .github/agents docs web CLAUDE.md AGENTS.md` exits **0**; and `python tools/build-docs-portal.py --check` exits **0**. For the class half, **red-first**: add a throwaway `docs/<tmp>.md` with valid frontmatter, run **only** `docs-graph.py derive` (the last action mandated by V10 and by every skill's "Documentation & discoverability" section), and confirm the dependents-stale check **fails** before the ordering fix and **passes** after.
- **Validation (PowerShell 5.1-safe — no `&&`):** `pwsh tools/sync-pack.ps1; git diff --quiet -- .claude .github/instructions .github/prompts .github/agents docs web CLAUDE.md AGENTS.md; echo $LASTEXITCODE` (expect `0`), then `python tools/build-docs-portal.py --check; echo $LASTEXITCODE` (expect `0`)
- **Recommended remediation, two parts:**
  1. *Instance:* run `python docs/ai-forward-pack/scripts/docs-graph.py derive`, **then** `python tools/build-docs-portal.py` and `python tools/build-web-index.py`, and commit the result. Order matters — both readers consume `docs/docs-index.js`.
  2. *Class:* remove the ordering hazard rather than re-running it by hand. Preferred option — have `docs-graph.py derive` refresh the two dependent artifacts (or emit a non-zero "dependents stale" signal) so the skills' documented last action cannot leave them behind. Alternative — make `sync-pack.ps1` run `derive` **before** it builds the portal and the web index. Choose one; do not do both silently.
- **Dependencies:** none, but the **instance half must ship with FR-058/FR-059/FR-065** or gate 1 stays red
- **Owner:** @timianmalloo · **Next skill:** `/design-slice` for the class fix (it changes a contract between three tools), then `/implement` · **Status:** **FULLY RESOLVED.** Instance at `7bc0cf2`; **detection** at `48e0601` (both derived artifacts drift-gated at gate 1, previously only the portal); **source fix at `<fr068>`** — `sync-pack.ps1` derives before building the dependents, which became safe once FR-068 made `docs-index.js` byte-stable. Gate 2 exits 0 on two consecutive syncs. Both halves now hold: the trap is closed at source *and* a hand-run that skips sync is still caught by detection.

### FR-068 · issue · P2 — `docs/docs-index.js` carries a wall-clock timestamp, so it can never be drift-gated
- **Affected scope:** `docs/ai-forward-pack/scripts/docs-graph.py` (deployed), `docs/docs-index.js`
- **Evidence:** attempting FR-060's source-removal fix — having `sync-pack.ps1` run `derive` before building the two dependents — put `docs-index.js` inside gate 2's diff scope, where it failed immediately on a **one-line** diff: `"generated": "2026-08-26T20:44:14Z"` → `"...T20:46:23Z"`. Every `derive` rewrites that field, so the file can never be byte-stable across two runs on two machines. Discovered by **running the gate after the change**, not by reading it.
- **Consequence:** the ordering trap that produced FR-060 cannot be closed at source until the index is stable, because closing it makes **CI permanently red** — strictly worse than the hazard. Detection is therefore the shipped mitigation, and the trap itself is still live.
- **Prior art — this exact class is already solved next door:** `build-web-index.py` carries a comment explaining it **removed** its build timestamp for precisely this reason (*"a wall-clock/mtime stamp made this file differ between the author's machine and a CI checkout … it could never pass the source-install drift gate cross-platform"*) — PACK-I / the FR-048 timestamp class. The sibling generator learned this; `docs-graph.py` did not.
- **Recommended remediation:** remove `generated` from the payload, or make it content-derived (rewrite it only when the rest of the document changes). **Not a drive-by:** `docs-graph.py` is a **deployed** script and `docs-index.js` is an *accumulated* artifact (V10 — never seed or overwrite by hand), so changing its payload shape affects every consuming repo and needs a design pass.
- **Acceptance criteria:** two consecutive `derive` runs minutes apart produce **byte-identical** `docs-index.js` (red-first: today they differ by exactly the timestamp line); and with that true, `sync-pack.ps1` can run `derive` before the dependents with gate 2 still exiting 0.
- **Validation:** `python docs/ai-forward-pack/scripts/docs-graph.py derive`, wait >1s, run again, compare hashes
- **Dependencies:** blocks FR-060's source-removal half · **Owner:** @timianmalloo · **Next skill:** `/design-slice` (deployed-script contract change) · **Status:** **RESOLVED at `<fr068>`.** The `generated` field was **removed** rather than made content-derived, because it was read by **nothing** — verified across `docs/index.html`, `docs-explorer-core.js`, `docs/portal`, `build-docs-portal.py` and the test suite — and because the sibling generator `build-web-index.py` had already made and documented exactly this call for the same reason. Removal is the smallest correct fix (L1: does the field need to exist at all?), so the recommended `/design-slice` pass was not needed once the consumer question was settled by reading rather than assuming.
  **Red observed:** two derives 3 s apart produced different hashes (`0CEE80DE…` vs `B3129494…`). **Green:** two derives 4 s apart now produce identical bytes (`0CFA69ED…` twice).
  **It unblocked FR-060 as designed:** `sync-pack.ps1` derives first again, and gate 2 exits **0** on two consecutive syncs — the exact scenario that forced the Phase 2 revert. Pack revision **48 → 49**.
- **Provenance:** found by this Phase 2 implementation attempting the ordering fix and running the gate afterwards — the change was reverted rather than shipped red.

### FR-065 · issue · P1 — Correct the 24→38 knowledge-doc count and close the regex blind spot
- **Affected scope:** `.github/copilot-instructions.md:48` (instance); `tools/check-consistency.py:474-477` (class)
- **Evidence:** review §3 FR-065. Line 48 reads `24 knowledge docs`; the filesystem has **38** excluding `FOUNDATION.md`. Present at `e1ec9d0` too, so it has survived at least two prior forensic reviews. The checker's prose-rule family has no rule for `N knowledge docs` or `N scripts`.
- **Consequence:** the file Copilot loads as repo instructions understates the knowledge base by 37% — and, more importantly, "gate 1 green" cannot be read as "documented counts are correct" until the class half lands.
- **Recommended remediation:** (1) *instance* — change `24` → `38`; (2) *class* — extend `_prose_rules` with `(\d+)\s+knowledge\s+docs` → `knowledge_docs` and `(\d+)\s+scripts` → `scripts`, then fix whatever the widened net catches.
- **Acceptance criteria:** the new rules, run on the **un-fixed** `copilot-instructions.md`, report a finding (red observed); after the fix `python tools/check-consistency.py` is clean; and a deliberate edit of any `N knowledge docs` or `N scripts` string to a wrong number makes it red again.
- **Validation:** `python tools/check-consistency.py` before and after each half
- **Dependencies:** none · **Owner:** @timianmalloo · **Next skill:** `/implement` · **Status:** **RESOLVED at `7bc0cf2`** — both halves. Class rules added **first** and observed red (5 findings → 6, catching line 48); instance then corrected to 38; gate 1 clean. The `N scripts` rule caught nothing, which is the correct result.
- **Provenance:** raised by the **adversarial gate**, not by the author — this review cited two other lines of this same file and walked past line 48.

---

## Phase 2 — Prevent

> Ship **FR-061 first** (it is the root-cause control), then **FR-067** in the same or the next commit — FR-061 points every agent at `verify-bundle.ps1`, and FR-067 is what keeps that pointer honest. FR-060's *class* half also belongs to this phase.

### FR-067 · risk · P2 — Assert that `verify-bundle.ps1` still mirrors CI
- **Affected scope:** `tools/verify-bundle.ps1`, `.github/workflows/pack-consistency.yml`, `tests/docs_explorer/`
- **Evidence:** review §3 FR-067. Nothing compares the local gate list to the CI step list. Two divergences visible today: CI runs `pip install pytest` before gate 3, the local script does not; CI uses `python3`, local uses `python`.
- **Consequence:** FR-061 makes this script the recommended proxy for CI in every agent session. An unasserted proxy that drifts teaches agents to trust a control that no longer holds — Mock Fiction in the remedy itself, and a fresh instance of the class this review is about.
- **Recommended remediation:** add a test asserting **set equality** between the gates `verify-bundle.ps1` runs and the steps `pack-consistency.yml` runs (by a shared, declared gate-id list rather than by string-scraping two files, which would just move the drift).
- **Acceptance criteria:** deleting or renaming a gate in either file makes the test **fail** — observed red before it is made green; the test runs in CI and reports its own status.
- **Validation:** the red-first deletion above; then `python -m pytest tests -q`
- **Dependencies:** should ship **with or immediately after** FR-061 · **Owner:** @timianmalloo · **Next skill:** `/implement` · **Status:** **RESOLVED at `<phase2>`** — `tests/docs_explorer/test_gate_parity.py` declares the canonical nine gates and checks both files against that declaration. **Observed red in both directions:** renaming a local gate in `verify-bundle.ps1` failed the test, and removing a step name from `pack-consistency.yml` failed it. Runs in CI via the existing pytest gate, so it reports its own status.
- **Provenance:** raised by the adversarial gate.

---

### FR-061 · issue · P1 — Name the verifier in the files agents actually load; register CTRL-D
- **Affected scope:** `pack/adapters/managed-blocks/CLAUDE.block.md`, `pack/adapters/managed-blocks/AGENTS.block.md` (→ regenerated `CLAUDE.md`, `AGENTS.md`), `.github/copilot-instructions.md`, `docs/lessons/defect-classes.md`
- **Evidence:** review §3 FR-061. `verify-bundle|check-consistency` → **NOT MENTIONED** in `CLAUDE.md`, `AGENTS.md`, `CLAUDE.block.md`; `sync-pack` mentioned twice in each. The verifier exists, mirrors CI, and correctly reports `BUNDLE INCONSISTENT - 2 of 9` on this commit.
- **Consequence:** this is the mechanism by which FR-058/059/060 reached a protected branch, and the reason the next session repeats it. Live instance of seed class **CTRL-D** (`ci-and-test-efficiency.md` CE21), absent from this repository's 17-class register.
- **Recommended remediation:**
  1. Add one line to both managed blocks pairing the generator with the verifier — *"after editing `pack/`, run `pwsh tools/sync-pack.ps1`, then **`pwsh tools/verify-bundle.ps1`** before committing; it runs the same nine gates CI does."*
  2. Add `verify-bundle.ps1` to the **Build / maintenance commands** section of `.github/copilot-instructions.md` (it is currently mentioned only inside the `/extendaibundle` description at line 106).
  3. Register **CTRL-D** in `docs/lessons/defect-classes.md` with signature, why-it-survives (*everything the agent ran was green; the gate it never ran was the one that fails*), this instance, and the control.
- **Acceptance criteria (rewritten after the adversarial gate — the first version could not fail):**
  1. A **mechanical check exists and fails on today's tree**: a new rule in `tools/check-consistency.py` (or an equivalent CI step) that reports a finding when `CLAUDE.md` or `AGENTS.md` does not name `verify-bundle.ps1` **in the sentence that describes the commit workflow** — not merely anywhere in the file. Observed **red before the fix** and green after.
  2. `docs/lessons/defect-classes.md` contains a `CTRL-D` entry whose **Status** is exactly **`controlled`**, justified by the check in (1). *(The first draft allowed `controlled` **or** `partially-controlled` — a disjunction no tree can fail.)*
  3. The check in (1) is wired into `pack-consistency.yml`, so it reports its own status rather than being advisory (CE21/E13).
- **Explicitly NOT sufficient:** a bare `Select-String CLAUDE.md -Pattern 'verify-bundle'`. It is satisfied by the literal string appearing anywhere — in a code fence, in a changelog line, or in a sentence saying *not* to run it. That is Coverage Theater, and it would be a particularly poor way to close the item the review calls the one that matters.
- **Validation:** run the new check on `c27f83d` (expect a finding), apply the front-door edit, re-run (expect clean); `pwsh tools/sync-pack.ps1` + drift check to confirm the managed-block change propagated
- **Status:** **RESOLVED at `<phase2>`.** Control `check-consistency.py :: check_front_door_names_verifier()` **observed red on both `CLAUDE.md` and `AGENTS.md`** before the fix, then green. `CLAUDE.md` and `AGENTS.md` now name `verify-bundle.ps1` in the same paragraph as `sync-pack.ps1`; `.github/copilot-instructions.md` names it in **Build / maintenance commands**. **CTRL-D registered as `controlled`** in `docs/lessons/defect-classes.md`. **Design note:** the sentence went in the repo **preamble**, not the managed block — `verify-bundle.ps1` is repo-only tooling and would not exist in a consuming repo, so shipping it in the block would have deployed a broken instruction to every install.
- **Rung note (CI6):** this lands at **rung 3** (always-loaded instruction). A rung-2 belt worth considering separately: a `pre-push` hook, or a CI step that fails when the front-door files stop naming the verifier — because a rung-3 control degrades silently the moment someone rewrites the block.
- **Dependencies:** none · **Owner:** @timianmalloo · **Next skill:** `/implement` · **Status:** proposed

---

## Phase 3 — Close the release and supply-chain gaps

### FR-062 · risk · P2 — Gate publication on the consistency workflow
- **Affected scope:** `.github/workflows/pages.yml`
- **Evidence:** review §3 FR-062. Runs `32987223694` (`pages`, success) and `32987223699` (`pack-consistency`, failure) share commit `c27f83d` and timestamp.
- **Consequence:** the public site serves a bundle built from a tree with mismatched counts and stale derived artifacts. Adopter-facing, not a data or security exposure — the `build-pages-bundle.py` publish boundary still holds.
- **Recommended remediation:** make publication conditional. Either convert `pages.yml` to `on: workflow_run: {workflows: [pack-consistency], types: [completed]}` with an `if: github.event.workflow_run.conclusion == 'success'` guard, or make `pack-consistency` a required status check on `main` so a red tree cannot reach the branch that triggers publication. The second is stronger and also fixes the class.
- **Acceptance criteria (rewritten after the adversarial gate — the first version passed vacuously):** with `pack-consistency` a **required check on `main`**, a deliberately count-broken commit **targeting `main`** (via PR, so protection applies) is **blocked from merging**, and no `pages` run exists for that SHA with `conclusion == success` **while** `pack-consistency` for the same SHA is red; a clean commit then merges and deploys normally. *(The first draft said "pushed to **a branch** … produces no Pages deployment". `pages.yml` triggers only on `push: branches: [main]` and `workflow_dispatch`, so that is already true on the unfixed repo — the criterion could not fail.)*
- **Validation:** `gh run list --branch main` and `gh pr checks <pr>` for the broken SHA — red required check, no successful `pages` run; then the same for the clean SHA — green and deployed. Red observed **before** the fix.
- **Status:** **RESOLVED at `<fr062>`** — by the *first* option (an in-workflow gate), not the required-check option; see the split below.
  **Shipped:** `pages.yml` gains a `gate` job running `check-consistency.py` on the commit about to be published, and `deploy` declares `needs: gate`. Chosen over `on: workflow_run` deliberately — `workflow_run` sets `GITHUB_SHA` to the default-branch head rather than the triggering commit (confirmed in GitHub's events reference) and discards the `paths:` filter; `needs:` is race-free by construction.
  **Red observed end-to-end, on real CI:** a throwaway branch with a deliberately broken count produced `pages` run `33015196508` → **gate: failure, deploy: SKIPPED**, and the latest deployment remained the previous main commit — *nothing was published*. Safe to run because the `github-pages` environment has a branch policy admitting only `main`, so a non-main deploy is blocked by the environment regardless of the wiring.
- **NOT done — deliberately left to the human (BoK §VI.3):** making `pack-consistency` a **required status check** on `main`. `gh api .../branches/main/protection` shows **no `required_status_checks` block at all**, which is precisely how `c27f83d` reached `main` red. Enabling it is a one-line API call, but with `enforce_admins: true` it would **block direct pushes to `main`** and force a PR workflow — a change to how the owner works, not a defect fix. Recommended, not imposed.
- **Also fold in:** nothing. *(An earlier draft folded the "must not contain merge commits" branch-protection gap in here. The adversary was right that it does not belong: it is a documentation defect, not a publication-gating one, and its evidence is a transient console message. It is now **FR-066**, at Flagged confidence, with obtaining a durable oracle as its first task.)*
- **Dependencies:** cleanest after Phase 1, so the first gated run is green · **Owner:** @timianmalloo · **Next skill:** `/implement` · **Status:** proposed

### FR-063 · risk · P2 — SHA-pin the actions in the highest-privilege workflow
- **Affected scope:** `.github/workflows/pages.yml` — the five `uses:` at lines **37, 38, 46, 47, 51** (`deploy-pages` sits outside the range an earlier draft cited)
- **Evidence:** review §3 FR-063. `pages.yml` holds `pages: write` + `id-token: write` and uses five mutable tags (`actions/checkout@v4`, `actions/setup-python@v5`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`); `pack-consistency.yml` (`contents: read`) and the benchmark workflow pin every action by full SHA.
- **Consequence:** a mutable tag is a supply-chain write primitive in the one workflow that can mint an OIDC token and write to Pages. The repository has already chosen SHA-pinning as its standard; the posture is inverted precisely where privilege is highest.
- **Recommended remediation:** pin all five to full commit SHAs with a trailing `# vN` comment, matching the existing house style. Resolve each SHA from the upstream release **at pin time** — do not copy a SHA from memory or from another repo (NG1). **Then add the CI assertion below in the same change**, so the standard becomes a control rather than a convention.
- **Acceptance criteria:** every `uses:` line in `.github/workflows/*.yml` **positively matches** `uses:\s*[\w.-]+/[\w.-]+(/[\w.-]+)*@[0-9a-f]{40}\b`; and a CI step asserting that predicate **fails** when a bare tag is reintroduced — observed red on the current `pages.yml` before the fix. *(An earlier draft asserted the absence of a negative, `uses:.*@(?![0-9a-f]{40})`, which false-positives on trailing-comment `@` and silently passes `uses: ./local-action` and `docker://` forms that have no `@` at all. Assert the positive.)*
- **Validation:** run the new CI step on `c27f83d` (expect red), pin, re-run (expect green); confirm the next `pages` run succeeds on the pinned SHAs
- **Note:** the CI assertion is **part of this item**, not optional hardening. Filing it as "worth considering" — as an earlier draft did — would reproduce CTRL-D one section after the review names CTRL-D as its headline.
- **Status:** **RESOLVED at `<fr063>`.** All five actions in `pages.yml` pinned to full commit SHAs, each **resolved from its tag ref at pin time and verified to be a real commit** via the GitHub API — none copied from memory or from another file. Control `check-consistency.py :: check_workflow_action_pinning()` asserts the **positive** form and was **observed red on all five bare tags first** (lines 37, 38, 46, 47, 51), then green; re-proven red by reintroducing a single bare tag. All **13** `uses:` across all three workflows are now SHA-pinned.
- **Recorded divergence (deliberate, not an oversight):** `actions/checkout` is pinned in `pages.yml` to the **current** v4 (`11d5960`, 2026-07, carries backported fixes) while `pack-consistency.yml` retains the older `34e1148` (2025-11). Both are valid immutable pins. Unifying them is a **version bump on the required gate** — different work, different risk — and was kept out of a security fix. Worth a follow-up if one-SHA-per-action is wanted as a standard.
- **Dependencies:** none · **Owner:** @timianmalloo · **Next skill:** `/implement` · **Status:** proposed

---

## Phase 4 — Record hygiene

### FR-064 · todo · P3 — Reconcile the canonical review filename with the newest review
- **Affected scope:** `docs/reviews/forensic-review.md`, `docs/backlog/forensic-review.md`, and the `/forensicreview` skill contract in `pack/commands/forensicreview/SKILL.md`
- **Evidence:** review §3 FR-064. `docs/reviews/forensic-review.md` is `status: superseded` and covers revisions 30 & 33, two reviews behind. The skill contract names that path as its output, so a reader following the contract gets a stale document.
- **Consequence:** low impact, but it is a truth-of-the-record defect in the artifact class whose purpose is truth of the record — and it forced a recorded naming deviation in the revision-48 review.
- **Recommended remediation:** pick one convention and make the contract and the tree agree. Either (a) keep rev-numbered files and update the skill contract to say "`docs/reviews/forensic-review-rev<N>.md`, superseding the previous", or (b) keep `forensic-review.md` as a always-newest pointer and archive prior reviews on write. Option (a) matches what the repository actually does and preserves the intact `supersedes` chain.
- **Acceptance criteria:** the path named in `pack/commands/forensicreview/SKILL.md` resolves to the review with the **highest `rev<N>`** present under `docs/reviews/`; every other forensic review carries `status: superseded`; `docs-graph.py validate` stays at 0 defects. *("Newest" is defined mechanically as highest `rev<N>` so a script can fail it — an earlier draft said "the newest review" with no oracle for newness.)*
- **Validation:** `python docs/ai-forward-pack/scripts/docs-graph.py validate`; open the contract-named path and confirm it is the newest
- **Dependencies:** none · **Owner:** @timianmalloo · **Next skill:** `/document` · **Status:** proposed

### FR-066 · todo · P3 — Document the linear-history branch protection, after getting a durable oracle
- **Affected scope:** `pack/adapters/managed-blocks/CLAUDE.block.md` + `AGENTS.block.md` (→ `CLAUDE.md`, `AGENTS.md`), `README.md`
- **Evidence and its limit:** review §3 FR-066. Observed as `remote: error: GH006 … Found 1 violation: f935964…`, but that push no longer exists, so the evidence is **not re-runnable** — confidence was **Flagged**, not Verified.
- **ORACLE NOW OBTAINED (2026-08-26, during FR-062):** `gh api repos/timianmalloo/ai-forward/branches/main/protection` returns `"required_linear_history": {"enabled": true}`, alongside `enforce_admins: true`, `allow_force_pushes: false`, `allow_deletions: false`, `required_conversation_resolution: true`, and — notably — **no `required_status_checks` block**. FR-066's first task is therefore **done**; confidence rises from Flagged to **Verified**, and only the documentation half remains.
- **Consequence:** the documented worktree-per-session flow (WT1) produces a merge commit at its integration step, which is exactly what the protection forbids; the collision is near-certain on a contributor's first integration and the recovery is undocumented.
- **Recommended remediation, in order:** (1) obtain the durable oracle — `gh api repos/:owner/:repo/branches/main/protection` — and record the actual rule set; **only then** (2) document it beside the worktree flow, with the recovery step (rebuild the change as a linear commit off `origin/main`).
- **Acceptance criteria:** the protection API response is quoted in the docs (so the claim has a re-runnable source); and `CLAUDE.md`/`AGENTS.md` state the linear-history requirement in the same section as the worktree-per-session flow.
- **Validation:** `gh api repos/:owner/:repo/branches/main/protection`; grep the two front-door files
- **Dependencies:** none · **Owner:** @timianmalloo · **Next skill:** `/document` · **Status:** proposed
- **Provenance:** split out of FR-062 at the adversarial gate's insistence — it is a documentation defect, not a publication-gating one, and its confidence is lower than FR-062's.

---

## Deliberately not proposed

Recording what was rejected is part of an honest backlog (the Simplifier's pass).

| Candidate | Disposition |
|---|---|
| `npm run test:docs-explorer:core` fails with `'node' is not recognized` | **Rejected — environmental.** `node --version` and a direct `node --test` both succeed (31/32 pass). This is the npm-shim PATH divergence `verify-bundle.ps1` already documents and works around. Not a repo defect. |
| Portal generator non-determinism (class PACK-I) | **Rejected — disproven.** Two consecutive builds produced identical SHA-256. The generator is correct; only the committed artifact was stale. |
| Missing tests/evals on recent capabilities (rev42's dominant finding) | **Rejected — did not recur.** Both capabilities added since shipped with unit tests *and* eval cases. Recorded as a strength instead. |
| `docs/_site/` staleness | **Not raised.** FR-050 established that mtime-derived staleness claims do not survive checking, and no content-based signal was available in scope. Raising it again without a content oracle would repeat a withdrawn finding. |
| Broad "add more tests" / "improve docs" items | **Rejected — speculative.** No named failure they would prevent (CT15). |

---

## Status

| | |
|---|---|
| **Completed** | **Phases 1–3 shipped, plus FR-068.** FR-058, FR-059, FR-060 (all halves), FR-061, FR-062, FR-063, FR-065, FR-067, FR-068 RESOLVED. Every control observed **red before green**; FR-062's proven end-to-end on real CI. CTRL-D registered `controlled`. Pack revision 48 → 49 |
| **Remaining** | **Two open, both P3 record hygiene:** FR-064 (canonical review filename) and FR-066 (document the linear-history rule — oracle obtained). The required-status-check question is **decided and recorded** as an accepted risk in `docs/notes/required-status-checks.md` |
| **Best next action** | **FR-064 + FR-066 together** — one small commit; FR-066 now has its oracle, so both are pure documentation |
