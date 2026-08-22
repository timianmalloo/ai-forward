---
id: forensic-review
title: "Forensic Review — AI-Forward repository (revisions 30 & 33)"
type: doc
status: superseded
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, adoption-readiness, consistency, ci, documentation, portability]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-backlog, rel: relates-to }
  - { to: forensic-review-20260802, rel: supersedes }
review-by: "2026-11-08"
review-suggested: []
summary: >-
  Adoption-readiness assessment at commit 2227632 (revision 30), scoped to inconsistencies
  and contradictions. Every self-declared gate is green and the repository is still not ready
  to hand to adopters. Two findings dominate: 183 documented commands invoke `python3`, which
  on a default Windows install is a broken Store alias, and the Copilot surface receives 11 of
  the 23 personas the deployment map promises — first raised twelve revisions ago, never closed.
---

# Forensic Review — AI-Forward repository (revision 30)

**Target:** commit `2227632`, branch `main`, **clean worktree**. 46 commits, 462 tracked files.
**Scope:** whole repository, weighted by the request toward **inconsistencies, contradictions, and cleanup required before asking others to adopt**.
**Mode:** Peer Mode to reconstruct, Adversary Mode at the gate. No production code, dependency, schema, CI behaviour or runtime configuration was changed.
**Supersedes:** the revision-18 review, archived at `forensic-review-20260802`.

---

## 1. Verdict

> **NOT READY FOR ADOPTION.** Not because the pack is weak — the reasoning corpus is strong and internally coherent — but because **the path a new adopter walks is broken at its first step**, and because a prior review's findings were never triaged.

| | Count |
|---|---|
| P0 | 0 |
| **P1** | **4** |
| P2 | 5 |
| P3 | 3 |

**Highest improvement-to-effort change: FR-031.** Every documented command in the pack is prefixed `python3`. On a default Windows install that resolves to the Microsoft Store alias, which prints *"Python was not found"* and exits `9009`. It is a search-and-replace plus one portability note, and it unblocks essentially every other instruction in the pack.

**The uncomfortable result.** Every gate this repository owns is green: `check-consistency.py` clean, `docs-graph.py validate` reporting zero problems across 42 artifacts, 107 Python tests passing, 26 JS tests passing, `verify-bundle.ps1` printing BUNDLE CONSISTENT. All of that is true, and none of it caught anything below. This is the repository's own **CD13 / E2E-E** lesson landing on itself: *a gate's green result is evidence the gate passed, not that its contents passed.*

---

## 2. Baseline (evidence, not attribution)

| Gate | Result | Note |
|---|---|---|
| `tools/check-consistency.py` | **clean** | 19 skills, 23 lenses, 33 knowledge, 23 templates, 13 scripts, 19 prompts |
| `docs-graph.py validate` | **clean** | 42 artifacts; 0 problems, stale, flagged, orphans, index drift |
| `pytest tests/` | **107 passed**, 1 skipped | not run in CI (FR-034) |
| `node --test` (core) | **26 passed** | the `npm run` wrapper fails on a local PATH quirk only |
| `verify-bundle.ps1` | **BUNDLE CONSISTENT** | not run in CI (FR-033) |

No pre-existing failures. Everything below was found *despite* a fully green baseline.

---

## 3. Findings

Each carries location, evidence, consequence, confidence, and the disconfirming check attempted. Remediation detail is in the backlog.

### P1 — blocks adoption

**FR-031 · issue · Portability · Verified.** **183 documented commands invoke `python3`, which does not work on a default Windows install.**
*Evidence:* `python3 docs/ai-forward-pack/scripts/docs-graph.py validate` → `Python was not found; run without arguments to install from the Microsoft Store`, **exit 9009**. `python3` resolves to `…\WindowsApps\python3.exe`, the Store alias; `python` resolves correctly. 183 instructions across `pack/`, `docs/`, `.claude/` and `.github/` use the `python3` form.
*Consequence:* a Windows adopter following any documented instruction gets an error that looks like a missing Python installation. The pack ships PowerShell tooling and targets Windows-friendly workflows, so this is the mainstream path, not an edge case.
*Notable:* `pack/evals/run-evals.py` already contains `if os.name == "nt" and resolved and resolved[0] == "python3"` — the problem was known and worked around **in exactly one place**, and never fixed in the documentation or the other twelve scripts.
*Disconfirming check:* ran the command verbatim; confirmed `python` succeeds where `python3` fails.

**FR-032 · issue · Deployment contract · Verified.** **Copilot receives 11 of the 23 personas the deployment map promises.**
*Evidence:* `pack/adapters/claude-code/agents` = 12 files, `pack/adapters/copilot/agents` = 11. Sync deploys 12+11 = **23 to `.claude/agents/`** and **11 to `.github/agents/`**. `INSTALL.md`'s deployment map promises both *"Peer agents (orchestrator, product-strategist, domain-researcher)"* and *"Adversary agents"* to `.github/agents/<name>.agent.md`.
*Consequence:* Copilot users are missing 12 personas, including hard-veto lenses. The pack's adversarial-review discipline — its core claim — is materially weaker on one of its two supported tools.
*Why every gate misses it:* `check-consistency.py` computes `lenses = len(cc) + len(cop)` from the **pack source**. It never counts the **deployed** `.github/agents/`. The "23 lenses" claim is true of the source and false of the Copilot install, and the checker is structurally incapable of seeing the difference.
*Status:* **first raised at revision 18 as FR-020. Twelve revisions later, unchanged.**

**FR-033 · issue · CI enforcement · Verified.** **The repository's foundational invariant is still not gated in CI.**
*Evidence:* `.github/workflows/pack-consistency.yml` runs `check-consistency.py`, `foundation-check.py`, the JS core tests and eval validation. It does **not** run `sync-pack.ps1` and check for drift — the check that proves `pack/` is source and `.claude/`/`.github/` are generated. `verify-bundle.ps1` performs that check and is never invoked by CI.
*Consequence:* source↔install drift, the single failure mode the whole architecture exists to prevent, can merge.
*Status:* first raised at revision 18 as **FR-011**, described then as *"a handful of CI lines."* Unchanged.

**FR-034 · issue · CI enforcement · Verified.** **The 107-test Python suite and the graph gate never run in CI.**
*Evidence:* the workflow runs `npm run test:docs-explorer:core` but not `pytest tests/` (107 tests, including `test_docs_graph.py`, `test_audit_log.py`, `test_check_consistency.py`) and not `docs-graph.py validate`.
*Consequence:* the largest test suite in the repository is advisory. A regression in `docs-graph.py` or `audit-log.py` merges green.
*Status:* raised at revision 18 as **FR-014**; the JS half was added, the Python half was left.

### P2 — material debt

**FR-035 · issue · Documentation truth · Verified.** **`S1–S18` is cited in ~30 files; `specification-standards.md` defines only S1–S10.** Likewise **`G1–G18` in 8 files against a standard defining G1–G16.**
*Evidence:* enumerated every `**S<n>` and `**G<n>` definition in the source standards and cross-scanned all range citations. The `S1–S18` figure traces to the revision-1 changelog (*"Specification Standards S1-S18"*); the standard was later consolidated to S10 and no citation followed.
*Consequence:* every skill's Authority line over-claims the extent of a governing standard. An agent told to satisfy `S1–S18` is pointed at eight directives that do not exist.
*Why no gate catches it:* `check-consistency.py` verifies *file counts*, never *directive-range integrity*. This is mechanically checkable and unchecked.

**FR-036 · issue · Documentation truth · Verified.** **The generated documentation bundle is twelve revisions stale.** `docs/_site/` newest file is dated **2026-07-12**; the repository is at **revision 30** (2026-08-10). It predates revisions 19–30 entirely — the Obsidian lens, Graphify, the No-Guessing Protocol, the UI detection and visual-assets layer, and `/visualize`. *Status:* raised at revision 18 as **FR-019**; unchanged.

**FR-037 · issue · Documentation truth · Verified.** **`docs/` still documents a reverted capability.** Model-orchestration was reverted in `8801a47`; `pack/knowledge/model-orchestration.md` and `pack/scripts/model-router.py` do not exist. Ten `docs/` files still reference them, including **`docs/architecture.md`**, `docs/index.md`, `docs/security/privacy-review.md` and the derived `docs/lenses/code-doc-join.md`. The revert is honestly recorded in `docs/notes/note-20260712-revert-model-orchestration.md`, so this is stale propagation rather than concealment — but an adopter reading the architecture doc is told about a script that was deleted.

**FR-038 · issue · Adoption · Verified.** **`.mcp.json.example` is committed containing a machine-specific absolute path** — `C:\\Users\\malla\\AppData\\Roaming\\npm\\node_modules\\higgsfield-mcp\\src\\server.js`. Anyone adopting gets a path that cannot resolve. Introduced three commits ago by `visual-assets-setup.py --init-mcp`, which writes the resolved local path into the *example* as well as the real config.

**FR-039 · risk · Security / UX · Verified.** **The public explainer's blockers are open and untriaged.** `web/ai-forward-pack-explainer.html` still loads three unpkg CDN scripts with **0** integrity hashes, and has **0** `:focus-visible` rules, **0** `aria-*` attributes and **0** `prefers-reduced-motion` against 2 animation declarations. The page renders blank without the CDN (216 of 68,522 body bytes survive a `<script>` strip). Documented at revision 28 in `docs/reviews/ui-pack-explainer.md`; nothing has changed since.

### P3 — hygiene

**FR-040 · todo · Ownership · Verified.** No `CODEOWNERS`, and three distinct owner handles across `docs/`: `@timianmalloo` (35), `@maintainers` (5), `@mallalieut` (2). Template placeholders are correctly confined to templates. *Status:* revision-18 **FR-018**; unchanged.

**FR-041 · todo · Tooling · Verified.** `package.json` defines no `test` script — only `test:docs-explorer:*`, so `npm test` fails. *Status:* revision-18 **FR-016**; unchanged.

**FR-042 · todo · Tooling · Verified.** `pack/scripts/scrub.py` does not allowlist `*@users.noreply.github.com`, so the repository's own commit trailers read as PII. *Status:* revision-18 **FR-017**; unchanged.

---

## 4. The meta-finding

**Seven of the twelve findings in the revision-18 backlog are still open, unchanged, twelve revisions later** — FR-011, FR-014 (partially), FR-016, FR-017, FR-018, FR-019, FR-020. Every one is still `status: proposed`. In the same period the pack gained twelve revisions of new capability.

That is the pattern worth naming before adoption: **this repository is far better at adding capability than at closing its own backlog.** The prior review correctly stopped for human triage, as its contract requires; triage then did not happen, and nothing in the system noticed. A backlog with no review cadence and no gate is a memoir in exactly the sense `continuous-improvement.md` CI6 warns about.

Registered as defect class **PACK-B**.

---

## 5. Persona verdicts

| Lens | Verdict | Basis |
|---|---|---|
| Enterprise Architect | **BLOCK** | The source↔install invariant that defines the architecture is ungated in CI (FR-033) |
| Documentation Steward | **BLOCK** | Range citations over-claim (FR-035); the bundle is twelve revisions stale (FR-036); reverted work is still documented (FR-037) |
| Security & Identity | **CONCERNS** | Un-hashed CDN scripts on the public surface (FR-039). No secret is committed — verified: `git log -S` on the live key returns nothing |
| Test Architect | **BLOCK** | The largest suite in the repo gates nothing (FR-034) |
| UX & Accessibility | **BLOCK** | The public explainer meets none of the keyboard, ARIA or reduced-motion floors (FR-039) |
| SRE | **CONCERNS** | CI does not exercise the checks that already exist |
| The Simplifier | **PASS** | Four candidate findings removed as preference-not-defect; no speculative items retained |
| Data & Persistence | **N/A** | No schema, migration or persistent store in this repository |
| Distributed Systems | **N/A** | No messaging, async delivery or consistency boundary |
| AI Systems | **PASS** | `/visualize` and the detector ship with evals; no model capability without a verification path |
| Privacy | **PASS** | `.mcp.json` verified git-ignored and absent from history |

Authors did not self-clear. Findings the Test Architect rejected for lacking an oracle are not present.

---

## 6. Confidence ledger and residual risk

Every finding above is **Verified** by execution or direct file inspection. No finding rests on inference.

**Residual risk — what this review did not cover.** The Playwright browser suite was not run (it needs a browser install, and adding one would have changed the environment being assessed). The three CI workflows were read but never executed, so their behaviour is inferred from their definitions rather than observed. `/addpacktorepo` was not run end to end against a scratch repository, so the adoption path is assessed from the deployment map and the artifacts rather than from a real installation — **that end-to-end install is the single most valuable next verification**, and FR-031 and FR-038 are exactly the defects it would catch. Non-Windows portability was not tested.

---

## 7. Status

| | |
|---|---|
| **Completed** | Baseline captured; all five gates run; contradiction, reference-integrity, deployment-map, graph-health and adoption-path sweeps done; 12 findings evidenced and deduplicated; prior review archived |
| **Remaining** | Human triage of the backlog. Nothing has been remediated — by contract this review stops at proposal |
| **Best next action** | Triage **FR-031** (the `python3` fix), then run `/addpacktorepo` against a scratch repository to verify the adoption path end to end |


---

# Revision-33 forensic review

**Target:** `a587952` on `main`, revision 33. **Worktree at start:** dirty in one path (`web/pack-index.js`, a timestamp-only re-sync artifact — see FR-048); otherwise clean. **Scope:** comprehensive, with deliberate emphasis on what the previous two reviews could not see.

## Baseline (recorded before any judgment; nothing here is attributed to this review)

| Gate | Result |
|---|---|
| `check-consistency.py` | exit 0 |
| `docs-graph.py validate` | exit 0 — 48 artifacts, 0 problems, 0 stale, 0 orphans, 0 index drift |
| `pytest tests -q` | 119 passed, 1 skipped, 108 subtests |
| Docs Explorer core (node) | 31 passed, exit 0 |
| `verify-bundle.ps1` | `BUNDLE CONSISTENT` |
| `foundation-check.py` | clean |

**Every gate is green, and the repository is not ready.** That sentence is the finding, not a paradox — it is the third consecutive review in which the defects that matter were invisible to every automated check, because each one lives in a place nothing looks.

## Method note — where the findings came from

The revision-30 review missed the broken adoption path (later FR-043) because it reasoned over the repository rather than *executing* it. This review therefore weighted three probes that gates structurally cannot perform:

1. **Sweep a class the project has already fixed once.** FR-043 registered PACK-E (*a deployment map promises an artifact the project does not ship*) and fixed one instance. Sweeping every backticked repo path promised across `pack/**` found **15 promised-but-missing paths**, of which two are genuine defects (FR-044, FR-045) and the rest are correctly created-at-runtime by skills.
2. **Run the things nothing runs.** Smoke-invoking all 12 deployed scripts surfaced FR-047 in the one script no test or gate touches.
3. **Attack a control I added myself.** The FR-033 drift gate was simulated exactly as CI runs it. The hypothesis that it always fails was **disconfirmed** (exit 0) — but the simulation surfaced FR-048.

## Findings

| id | kind | pri | title | confidence |
|---|---|---|---|---|
| FR-044 | issue | P1 | Deployment map still promises `.claude/commands/`, which nothing creates | Verified |
| FR-045 | issue | P1 | A second, contradictory deployment map inside an always-loaded document | Verified |
| FR-046 | risk | P1 | Seven deployed scripts have no tests and no gate — including the PII control | Verified |
| FR-047 | issue | P2 | `prompt-log.py --help` crashes on Windows; the encoding fix was never swept | Verified |
| FR-048 | risk | P2 | A generated artifact excluded from the only gate that checks generated artifacts | Verified |

Full evidence, disconfirming checks and acceptance criteria: `docs/backlog/forensic-review.md`.

## The pattern across all five

Four of the five are **the same shape**: *a fix was applied to the instance and never swept to the class.*

- FR-044 is PACK-E, in the very file FR-043 corrected, one revision later.
- FR-045 is a second deployment map that nobody reconciled when the first was authored.
- FR-047 is a console-encoding guard applied to exactly one of seven scripts.
- FR-046 is the general case: controls exist, but only some are themselves controlled.

`continuous-improvement.md` CI2 mandates **class → sweep → derive → prevent**, and CI3 says a discovered sibling must be fixed or explicitly registered. The register already carries **RIG-C — "sweep stopped at the instance"** as `uncontrolled`. This review is its third confirmed occurrence, which promotes it from an observed class to the project's **dominant defect signature**. The honest reading is that the pack teaches the sweep discipline better than it practises it, and that nothing in the toolchain enforces it.

## Lenses

**Reviewed:** architecture (source→install invariant, deployment map conformance), documentation truth, traceability, testing/proof coverage, supply chain (pinned action SHAs verified), operations/CI, portability, and the adoption path.
**N/A with rationale:** runtime concurrency, data migration, and distributed consistency — the pack ships no runtime service, no database and no message transport. Security/identity is **partially** reviewed: no credential surface changed since revision 30, and the `.mcp.json` ignore rule verified at revision 30 was re-confirmed by `git check-ignore`.
**Not reviewable here:** the CI workflow has still **never executed on a runner**. Its correctness is Inferred from YAML parse plus faithful local simulation. This is unchanged from revision 32 and remains the largest single unverified claim in the repository.

## Adversarial gate

- **Test Architect — PASS with a condition.** Every finding carries an executed oracle. FR-046 and FR-048 were reclassified from *issue* to *risk* on challenge, because neither has an observed failure — only an absent proof. **Condition:** FR-046 is not cleared by adding tests that merely import the module.
- **Simplifier — PASS.** Three candidate findings were removed as preference rather than defect: the `docs/_site` structural question (already recorded and deliberately left for the maintainer), the CRLF warnings on sync (cosmetic; `.gitattributes` normalises), and `scrub.py`'s Windows mojibake (folded into FR-047 rather than filed separately).
- **Documentation Steward — BLOCK, resolved into FR-045.** An always-loaded document instructing agents to load six non-existent files is a documentation defect of the first order.
- **Enterprise Architect — PASS with concern.** The source→install invariant holds and is now gated, but FR-048 shows the gate's boundary was drawn by convenience rather than by the invariant.
- **Security & Identity — PASS.** No new credential surface; the ignore rule holds.

No author cleared their own veto: the findings were authored in Peer Mode and attacked in Adversary Mode, and the two that survived reclassification did so by losing severity, not by being defended.

## Readiness verdict

**Adoptable, with two caveats to fix first.** This is an upgrade from revision 30's *NOT READY*: the adoption path now demonstrably works end-to-end (FR-043, verified on a scratch repo), all 23 personas reach both surfaces, and CI gates drift, tests and graph health.

The two caveats are **FR-044 and FR-045** — both are *instructions that send an adopting agent to files that do not exist*, and both are cheap to fix. FR-046 is the one that should not be deferred twice: shipping an unverified PII control is a governance position the project would not accept from a consumer.

## Residual risk

- The CI workflow has never run on a runner (unchanged since revision 32).
- `/updatepack`, `/visualize` and the judgment stages of `/addpacktorepo` (language detection, tier assessment, adapting to a repo that already has `CLAUDE.md`) remain unexercised. FR-043 established that an unexercised path is where this project's most serious defects live.
- FR-039 (the public explainer's CDN dependency and absent accessibility floor) is unchanged and remains the largest open item.
