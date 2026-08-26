---
id: forensic-review-rev48
title: "Forensic Review — AI-Forward repository (revision 48)"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, ci, derived-artifacts, supply-chain, verification, adoption-readiness]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-rev48-backlog, rel: relates-to }
  - { to: forensic-review-rev48-proof, rel: tested-by }
  - { to: forensic-review-rev42, rel: supersedes }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-11-24"
review-suggested: []
summary: >-
  Forensic assessment at commit c27f83d (revision 48), clean tree. The headline is not a
  latent risk but a present one: main is red. Two of the nine gates the repository runs on
  itself fail on the pushed commit — the counts/parity gate with five findings and the
  source-install drift gate on two stale derived artifacts — and the public site published
  from that same commit because the Pages workflow does not depend on the quality gate.
  The three defects are unrelated in symptom and identical in cause: the always-loaded front
  door (CLAUDE.md, AGENTS.md) names the generator, sync-pack.ps1, and never names the
  verifier, verify-bundle.ps1, so an agent that follows the documented workflow to the letter
  pushes a red branch and is told nothing. That is seed defect class CTRL-D, live here,
  unregistered in this repository's own register and carrying no control. Ten findings,
  FR-058 to FR-067. An external Test Architect pass BLOCKED the first submission and its six
  clearing conditions are recorded in §5a; it also caught FR-065, a 14-off documented count
  that gate 1 is structurally blind to and that has survived at least two prior reviews.
---

# Forensic Review — AI-Forward repository, revision 48

**Target:** commit `c27f83d5f4db8a296ced04345e46a543ef1490d4` (`c27f83d`), branch `main`, **clean worktree** at review time.
**Scope:** whole repository (654 tracked files; 449 `.md`, 62 `.py`, 59 `.json`, 36 `.html`, 24 `.js`).
**Mode:** Peer Mode to reconstruct and assess, Adversary Mode at the gate. Reviewed from an isolated worktree (`forensicreview/pack-audit`) per WT1.
**Supersedes:** the revision-42 review (`forensic-review-rev42`), whose nine findings were all triaged and dispositioned at revision 43.
**Constraint honoured:** no production code, dependency, schema, runtime configuration or CI behaviour was changed. Every gate below was *run*, not inferred. Two derived artifacts were deliberately **not** regenerated so that FR-060 stays reproducible on this branch — see §8.

> **Naming deviation (recorded).** The `/forensicreview` contract names its outputs `docs/reviews/forensic-review.md` and `docs/backlog/forensic-review.md`. This repository's live convention is rev-numbered files with the generic name held by an older, superseded artifact (`forensic-review.md` is status `superseded`; the newest is `forensic-review-rev42.md`). Conforming to the local convention outranks the generic name (BoK Part V.1), so this review is `forensic-review-rev48`. The generic-name drift is itself recorded as **FR-064**.

---

## 1. Baseline — the repository's own gates, executed

The repository defines its gate set twice: in CI (`.github/workflows/pack-consistency.yml`, nine steps) and locally in `tools/verify-bundle.ps1`, which is written to mirror it. Both were run against the target commit.

| # | Gate | Command | Result |
|---|---|---|---|
| 1 | Counts, skill/prompt parity, proof coverage | `tools/check-consistency.py` | **FAIL — 5 findings** |
| 2 | Source↔install drift | `sync-pack.ps1` + `git diff --exit-code` | **FAIL — 2 files** |
| 3 | Python test suite | CI: `python3 -m pytest tests -q` · local: `python -m unittest discover -s tests\docs_explorer` | PASS — 341 tests, 1 skipped, 97.8 s (adversary re-ran CI's form: 340 passed, 1 skipped) |
| 4 | Docs Explorer core contracts | `node --test` (3 files) | PASS — 32 tests, 31 pass, 1 skipped |
| 4b | Explainer render + a11y proof | `tools/verify-explainer-render.js` | PASS — all assertions |
| 5 | Knowledge-graph validation | `docs-graph.py validate` | PASS — 114 artifacts, 0 defects, 0 suggestions |
| 6 | Vendored-foundation drift | `pack/scripts/foundation-check.py` | PASS — clean, 7 docs |
| 6b | Audit log fully readable | `pack/scripts/audit-log.py verify` | PASS — 90 audit + 33 change entries, 0 unreadable |
| 7 | Eval cases well-formed | inline JSON/regex check | PASS — 31 cases |

**Aggregate:** `pwsh tools/verify-bundle.ps1` → `BUNDLE INCONSISTENT - 2 of 9 gate(s) failed.` (exit 1).

**The remote agrees.** GitHub Actions run **`32987223699`** (`pack-consistency`, `main`, push, 2026-08-26T16:13:04Z) **failed**, and `--log-failed` returns the same five findings in the same order as the local run. The immediately preceding commit `e1ec9d0` was **green** (run `32732534879`). Re-running gate 1 against `e1ec9d0` in a detached probe worktree returned `clean - all documented counts and skill/prompt parity match the filesystem` (exit 0). Attribution is therefore not inferred: the target commit introduced every failure.

**Not attributable to this review.** One environment artefact was observed and rejected as a finding: `npm run test:docs-explorer:core` reported `'node' is not recognized` on this host while `node --version` (v24.18.0) and a direct `node --test` invocation both succeeded. This is the npm-shim PATH divergence that `verify-bundle.ps1` already documents in its own header comment and works around by invoking node directly. No defect.

---

## 2. Recovered system map

The repository is **two things at once**, and that duality is the source of most of its risk surface.

1. **Canonical source of the AI-Forward Pack.** Everything authored lives under `pack/` — 22 skills (`commands/<name>/SKILL.md`), 39 knowledge markdown files (38 + the `FOUNDATION.md` provenance manifest), 27 templates, 18 stdlib-only Python scripts, 23 persona lenses, adapters, and a 31-case eval suite.
2. **A live install of that pack.** `.claude/`, `.github/{instructions,prompts,agents}/`, `docs/ai-forward-pack/`, `web/`, `CLAUDE.md` and `AGENTS.md` are **generated** from `pack/` by `tools/sync-pack.ps1`. The repo dogfoods: the pack is built using the pack.

**The load-bearing invariant** is therefore *`pack/` is the only source of truth, everything else is derived*. The architecture defends it with two mechanisms: `sync-pack.ps1` regenerates, and CI gate 2 re-runs sync and fails on any diff. Both are sound. The gap is not in the mechanism — it is in **who is told to run it** (§4, FR-061).

**Derived-artifact dependency order** (recovered from `tools/sync-pack.ps1` and the skill contracts, Verified by execution):

```
pack/**  ──sync-pack.ps1──▶  .claude/ .github/ docs/ai-forward-pack/ CLAUDE.md AGENTS.md
                              │
                              ├──build-web-index.py───▶ web/pack-index.js      ─┐ both read
                              └──build-docs-portal.py─▶ docs/portal/portal-data.js ┘ docs/docs-index.js
                                                                    ▲
docs/**/*.md frontmatter ──docs-graph.py derive──▶ docs/docs-index.js
                                                   (skills run this as their LAST action)
```

That diagram is the whole of FR-060: `sync-pack.ps1` consumes `docs/docs-index.js`, but every skill regenerates `docs/docs-index.js` *after* sync, as its documented last action. Any skill run that adds an artifact therefore leaves the portal and the web index stale, and nothing local says so.

**Trust boundaries.** Three, all in CI: (a) `pack-consistency` — `contents: read`, all actions SHA-pinned; (b) `pages` — `pages: write` + `id-token: write`, actions pinned only to mutable tags (FR-063); (c) `docs-context-reference-benchmark` — `attestations: write` + `id-token: write`, SHA-pinned. The publish boundary itself is enforced in code by `tools/build-pages-bundle.py`, which fails non-zero if a local-only tree (raw dreams, audit log, federation manifests) leaks into the bundle — a genuinely good control, and out of scope of the findings below.

---

## 3. Findings

Ten findings, deduplicated by root cause. Confidence follows the pack's ledger: **Verified** = observed by execution; **Inferred** = reasoned, not run; **Flagged** = suspected.

### FR-058 — `INSTALL counts.knowledge_docs` incremented to 39 when no knowledge doc was added
- **Kind:** issue · **Priority:** P1 · **Confidence:** Verified
- **Location:** `pack/adapters/INSTALL.md:6`
- **Evidence:** the frontmatter reads `counts: { lenses: 23, skills: 22, knowledge_docs: 39, templates: 27, scripts: 18 }`. `tools/check-consistency.py:57` defines `knowledge_docs = [f for f in knowledge if f != "FOUNDATION.md"]`; the filesystem holds 39 `.md` files in `pack/knowledge/`, of which 38 are knowledge docs. Gate 1 reports `INSTALL counts.knowledge_docs = 39, filesystem has 38`. At `e1ec9d0` the same line read `knowledge_docs: 38` and the gate was clean.
- **Contract violated:** the INSTALL frontmatter counts are the downstream consumer's refresh contract; `check-consistency` exists to hold them to the filesystem.
- **Consequence:** CI red on `main`. Downstream: an adopter reading `counts` to verify a completed install would look for a 39th knowledge doc that does not exist.
- **Disconfirming check attempted:** counted `pack/knowledge/*.md` directly (39 incl. `FOUNDATION.md`); read the exclusion rule in the checker rather than assuming it; confirmed `pack/OVERVIEW.md:59` independently states `38 docs (+FOUNDATION manifest)` — so the repository contradicts *itself*, and 38 is the value two of three sources agree on.
- **Root cause:** the native-UI change extended three existing knowledge docs (`ui-design-craft`, `ui-visual-assets`, `ui-archetype-catalog`) and added none; the count was incremented as though a doc had been added, alongside the two increments that were correct (`templates` 26→27, `scripts` 17→18).

### FR-059 — three prose count strings still say 26 templates
- **Kind:** issue · **Priority:** P1 · **Confidence:** Verified
- **Location:** `pack/OVERVIEW.md:52`, `pack/OVERVIEW.md:61`, `.github/copilot-instructions.md:50`
- **Evidence:** gate 1 emits three findings of the form `'26 templates' implies templates=26, filesystem has 27`. `pack/templates/` holds 27 files; `pack/adapters/INSTALL.md` correctly declares `templates: 27` and its own changelog entry says `templates 26->27`. The prose was not updated with it.
- **Contract violated:** documented counts must match the filesystem (the whole purpose of gate 1).
- **Consequence:** CI red; the overview a new adopter reads under-counts the artifact set.
- **Disconfirming check attempted:** counted `pack/templates` (27) and compared against `e1ec9d0` (26) — the increment is real and the prose is the stale side, not the count.
- **Note:** `.github/copilot-instructions.md` is *not* generated by `sync-pack.ps1`; it is hand-maintained, which is why sync did not carry the change into it.

### FR-060 — two derived artifacts committed stale; the regeneration order is a standing hazard
- **Kind:** issue · **Priority:** P1 · **Confidence:** Verified
- **Location:** `docs/portal/portal-data.js`, `web/pack-index.js`; ordering defined by `tools/sync-pack.ps1:204-210` vs. the skills' last-action contract
- **Evidence:** `python tools/build-docs-portal.py --check` → `DRIFT: docs/portal/portal-data.js is stale` (exit 1). Running `sync-pack.ps1` on the clean target commit and then `git diff --quiet -- .claude .github/... docs web CLAUDE.md AGENTS.md` returns **exit 1**, naming exactly `docs/portal/portal-data.js` and `web/pack-index.js`. The portal diff is +16 lines and its content is precisely the `spec-design-slice-rename` node and its two `relates-to` edges — an artifact added by `docs-graph.py derive` *after* the last `sync-pack.ps1` of that session.
- **Determinism ruled out as the cause:** two consecutive `build-docs-portal.py` runs produced byte-identical output (`4D9C01E5…` both times), so this is not PACK-I (unsorted-iteration non-determinism). The generator is correct; the committed artifact is simply stale.
- **Contract violated:** CI gate 2 — *"a re-sync that produces a diff IS the drift"*.
- **Consequence:** the portal half of this defect is **gate 1 finding #5** — `check-consistency.py` regenerates the portal and asserts byte-identical output (`README.md:109`: *"a stale portal is a failing build, not a matter of discipline"*) — **and** both files fail **gate 2**. Only `web/pack-index.js` is genuinely latent behind gate 1. **Correction:** an earlier draft claimed the whole of FR-060 was latent behind gate 1. That was wrong and it matters: fixing FR-058 and FR-059 alone does **not** turn gate 1 green, because finding #5 survives them.
- **Recurrence:** this class already fired. Run `32650207743` (2026-08-23) failed with `validate: 1 defect(s) - … 1 index-drift item(s)` — the same family (a derived artifact committed out of step), different symptom.
- **Disconfirming check attempted:** tested generator determinism (ruled out); inspected the diff content to confirm it is a *missing new node* rather than a formatting or platform difference; restored the tree afterwards so the review reports the committed truth.

### FR-061 — the always-loaded front door names the generator and never the verifier (root cause; CTRL-D)
- **Kind:** issue · **Priority:** P1 · **Confidence:** Verified
- **Location:** `CLAUDE.md`, `AGENTS.md`, `pack/adapters/managed-blocks/CLAUDE.block.md`
- **Evidence:** a literal search for `verify-bundle|check-consistency` returns **NOT MENTIONED** in `CLAUDE.md`, `AGENTS.md`, and `CLAUDE.block.md`; the same files mention `sync-pack` twice each. `.github/copilot-instructions.md` mentions `verify-bundle.ps1` **exactly once repo-wide** (line 106) — inside the `/extendaibundle` skill description, not in its "Build / maintenance commands" section, which lists only `sync-pack.ps1` and `package-pack.ps1`. **Correction:** an earlier draft added *"`README.md:109` mentions it"*. That was false — `README.md` contains **zero** occurrences of `verify-bundle`; line 109 mentions `check-consistency.py`, and the reviewer collapsed a `verify-bundle|check-consistency` alternation onto the wrong term. Striking it *strengthens* the finding: the verifier is named in exactly one place in the entire repository, in a hand-maintained file, inside an unrelated paragraph.
- **Contract violated:** `ci-and-test-efficiency.md` **CE21** — *"the gate invokes the aggregate control/test runner; an agent running 'the scripts I know about' reports 'controls green' and the gate then fails on a control that was never in their list."* Seed defect class **CTRL-D**.
- **Consequence:** this is the *mechanism* by which FR-058, FR-059 and FR-060 reached a protected branch. The control that would have caught all three already exists and reports `BUNDLE INCONSISTENT - 2 of 9 gate(s) failed` on this very commit — it was simply never named where an agent would read it. **Caveat (Inferred, not Verified):** `verify-bundle.ps1` is *written to* mirror CI, but nothing asserts it. Two divergences are already visible on inspection — CI runs `pip install pytest` before gate 3 and the local script does not (so on a pytest-less host gate 3 goes red for the wrong reason), and CI invokes `python3` where the local script invokes `python`. Pointing the front door at a proxy for CI that nothing holds *to* CI is a Mock-Fiction risk in the remedy itself; the backlog therefore pairs FR-061 with a set-equality check (FR-067).
- **Register gap:** the repository's own `docs/lessons/defect-classes.md` holds 17 live classes (`SHELL-A`, `PACK-A`…`PACK-Q`). **CTRL-D is not among them** — it exists only in the pack's *seed* register in `continuous-improvement.md` §6, where its status for a fresh repo is `uncontrolled`. This repository has now instantiated it and still has no control.
- **Disconfirming check attempted:** verified the control is not merely missing but *present and correct* (ran it; it fails correctly and names both gates), so the finding is genuinely about discoverability rather than absent tooling. Also checked whether the front door might reference it indirectly via the managed block — it does not.

### FR-062 — the public site publishes from commits whose quality gate is red
- **Kind:** risk · **Priority:** P2 · **Confidence:** Verified
- **Location:** `.github/workflows/pages.yml`
- **Evidence:** for commit `c27f83d`, run `32987223694` (`pages`) **succeeded** at 2026-08-26T16:13:04Z while run `32987223699` (`pack-consistency`) **failed** at the same timestamp. `pages.yml` triggers independently on `push: branches: [main]` and declares no dependency on the consistency workflow.
- **Contract violated:** `end-to-end-integrity.md` E13 — a green result from one gate is evidence about that gate, not about the tree. Nothing makes publication conditional on the tree being consistent.
- **Consequence:** `timianmalloo.github.io/ai-forward/` currently serves a bundle built from a commit with mismatched documented counts and two stale derived artifacts. Impact is reputational and adopter-facing rather than a data or security exposure — the publish boundary in `build-pages-bundle.py` still correctly withholds local-only trees.
- **Disconfirming check attempted:** confirmed the two runs share a commit and timestamp rather than being different pushes; confirmed `pages.yml` has no `workflow_run` dependency and no gating condition.

### FR-063 — the highest-privilege workflow is the least-pinned
- **Kind:** risk · **Priority:** P2 · **Confidence:** Verified
- **Location:** `.github/workflows/pages.yml` — the five `uses:` at lines 37, 38, 46, 47 and 51
- **Evidence:** `pages.yml` holds `pages: write` **and** `id-token: write` and uses five actions pinned only to mutable tags — `actions/checkout@v4`, `actions/setup-python@v5`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`. By contrast `pack-consistency.yml`, which holds only `contents: read`, pins every action to a full commit SHA (`actions/checkout@34e1148…`, `actions/setup-python@a26af69…`, `actions/setup-node@49933ea…`), and the benchmark workflow does the same (`actions/attest-build-provenance@e8998f9…`, `actions/upload-artifact@ea165f8…`).
- **Contract violated:** `engineering-governance.md` §9 (supply chain — pinned, deterministic builds; new external tooling is part of the trust boundary) and the Security & Identity lens's least-privilege/provenance scope.
- **Consequence:** a mutable tag is a supply-chain write primitive. A compromised or force-moved `v4`/`v5` tag executes in the one workflow that can mint an OIDC token and write to Pages. The repository has already decided SHA-pinning is its standard; the posture is inverted exactly where it matters most.
- **Disconfirming check attempted:** enumerated `uses:` across all three workflows to confirm the inconsistency is real and not a partial migration in one direction only — `pages.yml` is the sole unpinned workflow, and it is the sole high-privilege one.

### FR-064 — the canonical review filename no longer points at the newest review
- **Kind:** todo · **Priority:** P3 · **Confidence:** Verified
- **Location:** `docs/reviews/forensic-review.md`, `docs/backlog/forensic-review.md`
- **Evidence:** `docs/reviews/forensic-review.md` carries `id: forensic-review` with `status: superseded` and covers revisions 30 & 33; the newest prior review is `forensic-review-rev42.md`. The `/forensicreview` skill contract names `docs/reviews/forensic-review.md` as its output, so the contract and the convention now disagree, and a reader who opens the contractually-named file gets a two-revision-old superseded document.
- **Consequence:** low, but it is a truth-of-the-record issue in the artifact class whose entire purpose is truth of the record. It also forced a recorded deviation in this review's own naming.
- **Disconfirming check attempted:** confirmed both files are indexed and linked (so this is naming drift, not an orphan), and confirmed the `supersedes` chain is otherwise intact (`rev42` → `forensic-review` → `forensic-review-20260802`).

### FR-065 — a 14-off count defect of exactly the reviewed class, in a file this review read, and gate 1 is blind to it
- **Kind:** issue · **Priority:** P1 · **Confidence:** Verified
- **Location:** `.github/copilot-instructions.md:48`; blind spot at `tools/check-consistency.py:474-477`
- **Evidence:** line 48 reads `knowledge/    ← 24 knowledge docs (reasoning spine + vendored foundation)`. The filesystem holds **38** knowledge docs excluding `FOUNDATION.md`. That is off by **14** — an order of magnitude worse than FR-058's off-by-one. It is present at `e1ec9d0` as well, so it has survived every prior forensic review. `check-consistency.py`'s prose-rule family matches `(skills|workflows)`, `(lenses|personas)`, `(?:artifact )?templates`, and the single form `(\d+)\s+docs\s*\(\+FOUNDATION` — there is **no rule for `N knowledge docs`**, and none for `N scripts`, so the gate cannot see either.
- **Contract violated:** documented counts must match the filesystem — the same contract as FR-058/FR-059.
- **Consequence:** the file Copilot loads as repo instructions understates the knowledge base by 37%. More importantly it falsifies an implicit premise of this review: **gate 1 is not a sufficient oracle for documented counts**, so "gate 1 green" must not be read as "counts are correct".
- **Found by:** the adversarial gate, not the author — this review cited **line 50 and line 106 of this exact file** and walked past line 48. Recorded as such rather than absorbed silently.
- **Disconfirming check attempted:** counted the directory directly (38); confirmed the miss exists at `e1ec9d0` too, so it is not a regression introduced by the target commit; read the regex table rather than assuming coverage.

### FR-066 — the linear-history branch protection is undocumented and collides with the documented flow
- **Kind:** todo · **Priority:** P3 · **Confidence:** **Flagged** (deliberately, see below)
- **Location:** `CLAUDE.md`, `AGENTS.md`, `README.md`; the `main` branch-protection rule
- **Evidence and its limit:** observed directly as `remote: error: GH006 … Found 1 violation: f935964…` when a fast-forward of an integration branch was pushed. This is a **transient console message from a push that no longer exists** — a triager cannot re-run it, which is why confidence is Flagged rather than Verified *despite* being first-hand. Obtaining a durable oracle (`gh api repos/:owner/:repo/branches/main/protection`) is FR-066's first task, not an assumption to build on.
- **Consequence:** the documented worktree-per-session flow (WT1) produces exactly what the protection forbids at its integration step, so the collision is near-certain on a contributor's first integration, and the recovery is undocumented.
- **Disconfirming check attempted:** confirmed the rule is named in none of the three front-door files.

### FR-067 — nothing asserts that `verify-bundle.ps1` still mirrors CI
- **Kind:** risk · **Priority:** P2 · **Confidence:** Verified (the *absence* of the check is verified; any drift magnitude is Inferred)
- **Location:** `tools/verify-bundle.ps1` vs `.github/workflows/pack-consistency.yml`
- **Evidence:** no test, gate or script compares the local gate list to the CI step list. Two divergences are visible on inspection today: CI runs `python3 -m pip install … pytest` before gate 3 and the local script does not (so on a pytest-less host that gate goes red for the wrong reason); CI invokes `python3` where the local script invokes `python`.
- **Consequence:** FR-061 will make this script the officially recommended proxy for CI in every agent session. If it silently stops mirroring CI, the front door teaches agents to trust a control that no longer holds — Mock Fiction at the level of the remedy, and a fresh instance of the class this whole review is about.
- **Disconfirming check attempted:** searched the test suite and CI config for any assertion relating the two files; none exists. Raised by the adversarial gate, not the author.

---

A forensic review that reports only defects is not fair (Paul–Elder). Verified strengths at this commit:

- **The graph is clean.** 114 artifacts, **0 defects, 0 suggestions**, no orphans, no dangling links, no index drift. The V16 warn-vs-fail split introduced at revision 43 (FR-056) is holding: propagation no longer punishes compliance.
- **The test suite is real and green.** 341 Python tests plus 32 Node contract tests, and `test_deployed_scripts.py` enforces pack↔deployed parity — verified independently here: `pack/scripts` and `docs/ai-forward-pack/scripts` are 18/18 with **zero content hash mismatches**, and templates are 27/27 identical.
- **The rev42 class sweep held.** Revision 42's dominant finding was new capabilities shipping without tests or evals. The two capabilities added since (native-client UI, the `design-slice` rename) both shipped **with** unit tests (`test_native_ui_extension.py`, `test_design_slice_rename.py`) *and* eval cases (`ui-design-native-01`, `visualize-native-01`, `design-slice-01/02`). RIG-C did not recur.
- **The audit log is intact.** 90 audit + 33 change entries, 0 unreadable lines — the FR-052 control is working on a corpus that has since grown.
- **The publish boundary is enforced in code**, not in prose: `build-pages-bundle.py` fails the deploy if a local-only tree leaks.
- **`verify-bundle.ps1` is a well-built control** — it runs the same nine-gate shape as CI, invokes node directly to dodge the npm PATH divergence, and prints `SKIPPED` loudly rather than counting a skip as a pass. Two defects, both in the backlog: nobody is told to run it (FR-061), and nothing asserts it still matches CI (FR-067).

---

## 5. Persona verdicts (Adversary Mode)

Authors did not self-clear. A hard-veto BLOCK describes the reviewed repository's readiness; it does not suppress this report.

| Lens | Verdict | Basis |
|---|---|---|
| **Enterprise Architect** | **BLOCK** | The source-of-truth invariant is the architecture's central claim and two derived artifacts contradict it at HEAD (FR-060). Clears when gates 1–2 are green on `main`. |
| **Test Architect** (hard veto) | **BLOCK → cleared on re-review** | Run as an **external adversarial pass**, not by the author. First verdict: **BLOCK**, with four Blockers — a contaminated worktree contradicting the review's own tree claims, two acceptance criteria that could not fail (FR-061, FR-062), and a missing Proof Pack recorded alongside a self-cleared PASS. All six clearing conditions were then addressed (§5a). The adversary independently re-derived the attribution on pristine probe worktrees and it held on all three axes. |
| **Security & Identity** (hard veto) | **CONCERNS** | FR-063 is a real inversion of the repo's own pinning standard in the only OIDC-bearing workflow. Not a BLOCK: no exposure is observed, the publish boundary holds, and the fix is mechanical. Clears when `pages.yml` is SHA-pinned. |
| **Release / Deployment Engineer** (soft veto) | **BLOCK** | Publication is not gated on the quality gate (FR-062), and the protected-branch rule is undocumented (see §6). Clears when `pages` depends on `pack-consistency` or the branch is gated. |
| **SRE & Diagnostician** | **PASS with concern** | The gates are observable and CI reproduces local results exactly. Concern: `web/pack-index.js`'s failure is latent behind gate 1, so the repository under-reports its own breakage by one gate. |
| **Documentation Steward** | **CONCERNS** | The repository contradicts itself on a documented count (FR-058 vs `OVERVIEW.md:59`), and the canonically-named review file is two revisions stale (FR-064). |
| **The Simplifier** (soft veto) | **PASS** | Seven findings from a whole-repo sweep, deduplicated to four root causes; one candidate finding (the npm PATH artefact) was removed as environmental rather than kept as filler. |
| **Data & Persistence** | **N/A** | No schema, store, or migration in scope; the audit JSONL append-only contract is verified intact. |
| **Distributed Systems** | **N/A** | No messaging, async delivery, or consistency boundary in this repository. |
| **AI Systems Engineer** | **PASS** | Prompt/skill surfaces are contract-gated by 31 eval cases and the A6 regression rule; the `design-slice` rename shipped with renamed eval cases proven to seed correctly. |
| **Privacy & Data Governance** | **PASS** | No personal data in scope; the publish boundary withholds the audit log and federation data from the published bundle. |

**Unresolved hard veto:** none *after* the re-review below. The Security lens's CONCERNS and the two BLOCKs are readiness statements against the target commit, recorded rather than cleared, and each maps to a backlog item.

### 5a. Adversarial gate record — Test Architect hard veto

`GATE test-architect · 2026-08-26 · external adversarial pass (author did not self-clear) · verdict: BLOCK → cleared`

The first submission was **blocked**. Recording what it caught, because a review that hides its own gate is the failure it exists to detect:

| # | Clearing condition | Disposition |
|---|---|---|
| 1 | FR-061's AC must be mechanical and able to fail today | **Done** — rewritten as a `check-consistency` rule that fails on the current tree; the `controlled`/`partially-controlled` disjunction replaced with one asserted value |
| 2 | FR-062's AC must be exercisable where `pages` can actually trigger | **Done** — the old AC passed vacuously (`pages.yml` only triggers on `main`, so "push to a branch ⇒ no deploy" is true unfixed); re-specified against the `main` path with red observed first |
| 3 | Restore `portal-data.js` / `web/pack-index.js`, or correct the tree claims | **Done** — both restored to HEAD; FR-060 re-verified reproducible (`build-docs-portal.py --check` exit 1). The contamination came from the adversary's own `sync-pack.ps1` run in the shared worktree — a live **WT3** violation the author caused by pointing a subagent at this tree |
| 4 | Attach a Proof Pack; replace the self-cleared PASS | **Done** — `docs/proof/forensic-review-rev48.md`; §5's Test Architect row now records the external verdict |
| 5 | Correct the three miscited evidence items and the "latent" claim | **Done** — gate-3 command, the false `README.md:109` citation, `pages.yml` line numbers, and FR-060's consequence all corrected in place with the correction shown, not silently overwritten |
| 6 | Demote "mirrors CI exactly" or back it with a check | **Done** — demoted to Inferred with the two known divergences named, and FR-067 added to make it Verified |

It also found a defect the author missed entirely — **FR-065**, a 14-off count in a file this review had already cited twice. That is the single strongest argument in this document for the discipline it is recommending.

---

## 6. Lens coverage

| Lens | Status | Note |
|---|---|---|
| Architecture | Reviewed | Source-of-truth invariant recovered and tested; FR-060 |
| Design | Reviewed | Gate design is sound; discoverability is the defect (FR-061) |
| Implementation | Reviewed | 341+32 tests green; script/template parity verified byte-identical |
| Traceability | Reviewed | Skills → tests → evals intact for both new capabilities |
| Testing | Reviewed | No gap found; rev42's class did not recur |
| Security | Reviewed | FR-063 |
| Privacy | Reviewed | N/A — no personal data; publish boundary enforced |
| Data / migration | N/A | No schema or store |
| Operations / observability | Reviewed | FR-062; gate-2 latency behind gate-1 noted |
| Release | Reviewed | FR-062 + the undocumented no-merge-commit protection, below |
| Performance / cost | Reviewed | Suite 97.8 s; CI ~50 s. Within budget; no finding |
| Accessibility | Reviewed | Explainer a11y proof passes all assertions |
| Supply chain | Reviewed | FR-063 |
| Maintainability | Reviewed | FR-058, FR-059, FR-064 |

**Release-process observation — raised separately as FR-066 (Flagged).** `main` is protected with **"This branch must not contain merge commits"**, observed directly as `remote: error: GH006 … Found 1 violation: f935964…` when a fast-forward of an integration branch was pushed. The repository's documented flow is worktree-per-session (WT1), whose natural integration step *produces* a merge commit, and neither `CLAUDE.md`, `AGENTS.md` nor `README.md` mentions the linear-history requirement. **Confidence is Flagged, not Verified:** the evidence is a transient console message from a push that no longer exists, so a triager cannot re-run it. FR-066's first task is to obtain a reproducible oracle (`gh api repos/:owner/:repo/branches/main/protection`). It is a *documentation* defect, not a publication-gating one, which is why an earlier draft's decision to fold it into FR-062 was wrong.

---

## 7. Confidence ledger

| Claim | Evidence | Confidence |
|---|---|---|
| `main` fails its own gate 1 at `c27f83d` | local run + CI run `32987223699` `--log-failed`, five identical findings | **Verified** |
| `e1ec9d0` was green | CI run `32732534879` + gate 1 re-run in a detached probe worktree (exit 0) | **Verified** |
| Gate 2 also fails at `c27f83d` | `sync-pack.ps1` then `git diff --quiet …` → exit 1, two named files | **Verified** |
| The portal generator is deterministic | two consecutive builds, identical SHA-256 | **Verified** |
| Portal staleness = the post-sync `derive` node | diff content is exactly `spec-design-slice-rename` + 2 edges | **Verified** |
| `verify-bundle.ps1` would have caught both | executed: `BUNDLE INCONSISTENT - 2 of 9` | **Verified** |
| The front door never names the verifier | literal search across `CLAUDE.md`, `AGENTS.md`, `CLAUDE.block.md` | **Verified** |
| CTRL-D is unregistered locally | enumerated all 17 ids in `docs/lessons/defect-classes.md` | **Verified** |
| Pages published from a red commit | run `32987223694` success vs `32987223699` failure, same commit | **Verified** |
| `pages.yml` is the only unpinned workflow | enumerated `uses:` across all three workflows | **Verified** |
| Portal drift is gate 1 finding #5, not latent | `check-consistency.py` emits it directly; `README.md:109` states the portal is drift-gated there | **Verified** |
| Only `web/pack-index.js` is latent behind gate 1 | gate 2 names both files; gate 1 names only the portal | **Verified** |
| `.github/copilot-instructions.md:48` says 24 vs 38 actual | direct count + regex-table read; present at `e1ec9d0` too | **Verified** |
| `verify-bundle.ps1` still mirrors CI | written to, and shaped like, CI's nine steps — but nothing asserts it, and two divergences are visible (`pip install pytest`, `python3` vs `python`) | **Inferred** |
| No third CI gate is latent behind gate 2 | gates 3–7 all pass locally, but no CI run at `c27f83d` has executed past step 1 | **Inferred** |

---

## 8. Residual risk

- **Two gates are proven red; gates 3–7 are only inferred green in CI order.** They pass locally and passed remotely on `e1ec9d0`, but no run at `c27f83d` has executed past step 1. Only a green CI run on the fix commit closes this.
- **Gate 1 is not a sufficient oracle for documented counts.** Its prose-rule family has no rule for `N knowledge docs` or `N scripts`, which is how FR-065's 14-off count survived at least two prior reviews. "Gate 1 green" must not be read as "counts are correct" until FR-065's class half lands.
- **Nothing holds `verify-bundle.ps1` to `pack-consistency.yml`.** FR-061 is about to point every agent at that script as CI's proxy; if the two drift, the front door will teach agents to trust a control that no longer mirrors the gate. FR-067 exists for exactly this.
- **`.github/copilot-instructions.md` is hand-maintained and outside `sync-pack.ps1`.** FR-059's third instance and FR-065 both live there; nothing regenerates it, so it will drift again independently of the pack.
- **"Clean tree" is unreliable by inspection on this repo.** `sync-pack.ps1` rewrites twelve `.github/agents/*.agent.md` with CRLF on every Windows run, marking them dirty in `git status` while `git diff` normalizes them clean. This review fell into that trap once (§5a item 3) and now states tree claims from a restored, re-verified state.
- **CTRL-D is registered by this review but not yet controlled.** Until FR-061 lands, the next agent session repeats the failure — the class's defining property is that everything the agent ran was green.
- **This review's own artifacts add graph nodes**, which is exactly the FR-060 trigger. `docs-graph.py derive` was run (116 artifacts, 0 defects), but `docs/portal/portal-data.js` and `web/pack-index.js` were **deliberately left un-regenerated**. Regenerating them would turn gate 2 green on this branch and destroy the very evidence a triager needs to reproduce FR-060. This branch therefore inherits `main`'s red state on purpose; Phase 1 of the backlog is what turns it green, and the reader can confirm the finding by running the gate here.
- **`docs/_site/` and other historically-flagged surfaces were not re-examined**; FR-050 established that mtime-based staleness claims do not survive checking, and no content-based staleness signal was available within this review's scope.

---

## 9. Readiness verdict

> **NOT READY at `c27f83d`.** The repository is in good structural health — clean graph, green tests, verified parity, an intact audit corpus, and a control set that is well designed. But its own aggregate verifier reports `BUNDLE INCONSISTENT — 2 of 9 gates failed` on the current tip of a protected branch, and the public site has already published from that tip.
>
> The defects are individually trivial: one wrong integer, three stale strings, two regenerable files. What makes them a P1 cluster is that **none of them is the actual problem**. The actual problem is that a correct, complete, CI-mirroring verifier exists in this repository and the two files every agent loads on every session do not mention it. Fix the three symptoms and `main` goes green; fix FR-061 and it stays green.

---

## 10. Status

| | |
|---|---|
| **Completed** | Nine gates executed at `c27f83d`; two reproduced red locally and confirmed against remote CI run `32987223699`; attribution proven against `e1ec9d0` by probe worktree and independently re-derived by the adversary; system map and derived-artifact dependency order recovered; **ten** findings evidenced with disconfirming checks; **external** Test Architect gate run — BLOCK, six clearing conditions addressed (§5a); Proof Pack at `docs/proof/forensic-review-rev48.md`; backlog at `docs/backlog/forensic-review-rev48.md` |
| **Remaining** | All ten findings are **proposals awaiting human triage**. Nothing was fixed: counts, prose strings, workflows, front-door docs and the register are untouched, per the `/forensicreview` no-implementation contract. `docs/portal/portal-data.js` and `web/pack-index.js` are deliberately left at HEAD so FR-060 stays reproducible |
| **Best next action** | Triage **Phase 1** (FR-058, FR-059, FR-060, FR-065) — note it is **four** items, not three: FR-060's portal half and FR-065 are both gate-1 findings, so the earlier "three edits turn main green" was wrong |
