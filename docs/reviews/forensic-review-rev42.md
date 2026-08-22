---
id: forensic-review-rev42
title: "Forensic Review — AI-Forward repository (revision 42)"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, adoption-readiness, testing, verification, documentation, ci]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-rev42-backlog, rel: relates-to }
  - { to: forensic-review, rel: supersedes }
review-by: "2026-11-20"
review-suggested: []
summary: >-
  Forensic assessment at commit e4eae82 (revision 42), clean tree, all seven CI gates green and
  verified green on a runner. Four findings carried from revision 33 are now verified RESOLVED and
  the largest standing residual risk — "CI has never executed on a runner" — is closed by evidence.
  Eight findings remain or are new. The dominant one is convergent, not incidental: the three newest
  capabilities (/dream, /apply-learnings, /optimize-graph) have neither unit tests nor eval cases,
  while writing durable cross-repo stores. That is RIG-C — sweep stopped at the instance — on its
  fourth confirmed occurrence, and this time the un-swept sibling is the federation path. A second
  finding (FR-056) was discovered by obeying V16: correct change-propagation turns the CI graph gate
  red, so the incentive runs against the discipline.
---

# Forensic Review — AI-Forward repository, revision 42

## 1. Scope and baseline

| | |
|---|---|
| **Target commit** | `e4eae82fab8840d6296a0a7435f0233d05ad85a3` (`e4eae82`) |
| **Branch** | `main`, in sync with `origin/main` |
| **Worktree** | **clean** — 0 modified files at start and at end |
| **Revision** | 42 (`pack/adapters/INSTALL.md`) |
| **Scope** | whole repository, comprehensive |
| **Constraint honoured** | no production code, dependency, schema, CI behaviour or runtime config was modified |

**Repository shape.** 590 tracked files: 416 Markdown, 50 Python, 49 JSON, 34 HTML, 19 JS, 7 JSONL, 5 PowerShell, 4 YAML. This is a **methodology pack, not a running service** — the documentation *is* the product, and the "code" is a stdlib script bundle plus repo-local build tooling.

### Baseline — the repository's own seven CI gates, run locally

| Gate | Command | Result |
|---|---|---|
| G1 counts & parity | `tools/check-consistency.py` | **PASS** |
| G2 source↔install drift | `sync-pack.ps1` + `git diff --exit-code` | **PASS** — no drift, tree clean after sync |
| G3 Python suite | `pytest tests -q` | **PASS** — 183 passed, 1 skipped, 122 subtests, 49s |
| G4 Docs Explorer core | `node --test …` | **PASS** — 31 passed, 1 skipped, 0 failed |
| G5 knowledge graph | `docs-graph.py validate` | **PASS** — 0 problems / orphans / stale / flagged / index-drift, 87 artifacts |
| G6 vendored foundation | `pack/scripts/foundation-check.py` | **PASS** — clean |
| G7 eval cases | inline JSON+regex check | **PASS** — 26 cases |

**Baseline caveat (recorded, not attributed to this review):** `npm run test:docs-explorer:core` fails on this Windows host because the shell npm spawns does not resolve `node`, although `node` is on PATH and the identical command run directly passes 31/31. **The tests are green; only the documented launcher is not portable here.** This is a sibling of the registered class **PACK-C** (a documented command assumed portable) and is filed as FR-055 at P3.

## 2. Recovered system map

The architecture is documented and was checked against the tree rather than taken on trust.

- **`pack/` is the single source of truth.** `.claude/`, `.github/{instructions,prompts,agents}/` and `docs/ai-forward-pack/` are **generated** by `tools/sync-pack.ps1`. Verified: a re-sync on a clean tree produced **zero diff**, which is the invariant's own oracle.
- **Two consumer surfaces** — Claude Code (`.claude/`) and GitHub Copilot (`.github/`) — receive 37 knowledge docs, 22 skills, 23 personas, 26 templates, 16 scripts. Counts verified against the filesystem by G1.
- **Deliverables:** committed Markdown + a stdlib-only Python script bundle. **No runtime service, no database, no message transport, no credential surface** — which is why several standard review lenses are legitimately N/A (§5).
- **Knowledge graph:** 87 artifacts (30 knowledge, 20 doc, 12 ADR, 9 design, 3 architecture, 3 spec, 4 decision-note, plus glossary/proof-pack/threat-model/privacy-review/investigation/design-language). Zero orphans, zero stale, zero dangling links.
- **CI:** three workflows — `pack-consistency` (the seven gates), `pages` (publish), `docs-context-reference-benchmark`.

No architecture reconstruction was necessary: `docs/architecture.md` exists, and the source→install invariant it asserts was **verified by execution**, not read.

## 3. What changed since revision 33 — four findings verified closed

Each was tested against current code, not against the prior document.

| Prior finding | Claim | Verification performed | Verdict |
|---|---|---|---|
| **FR-044 / FR-045** (P1) | deployment maps promise paths nothing creates | `check_promised_paths()` exists in `tools/check-consistency.py:639` with a documented `PROMISED_PATH_ALLOWLIST`; G1 passes | **RESOLVED — with a control** |
| **FR-047** (P2) | `prompt-log.py --help` crashes on Windows | smoke-invoked **all 16 deployed scripts** with `--help`; every one exited 0 | **RESOLVED — and swept** |
| **FR-048** (P2 risk) | a generated artifact excluded from the drift gate | `web` is now inside the G2 diff path list; G2 passes | **RESOLVED** |
| **"CI has never executed on a runner"** — the largest standing residual risk since revision 32 | correctness of CI only Inferred | `gh run list`: **12 recent runs**; `pack-consistency` **success on `e4eae82`** (the target commit) at 18:17, plus one instructive failure at `54d32fb9` that caught a real cross-platform defect | **CLOSED — Verified** |

That last row matters most. The repository's most-repeated caveat across three prior reviews is now retired by evidence, and the one CI failure in the window is itself a positive signal: the gate caught a defect (`PACK-I`, OS-dependent ordering) that every local gate had passed.

## 4. Findings

Eight findings. Full evidence, disconfirming checks and acceptance criteria in `docs/backlog/forensic-review-rev42.md`.

| id | kind | pri | title | confidence |
|---|---|---|---|---|
| **FR-049** | risk | **P1** | The three newest capabilities have neither unit tests nor eval cases, and they write durable cross-repo stores | Verified |
| FR-050 | issue | P2 | `docs/_site` documentation bundle is 12 revisions stale (carried FR-036) | Verified |
| FR-051 | risk | P2 | Public explainer: three CDN dependencies, zero ARIA, no skip link (carried FR-039) | Verified |
| FR-052 | issue | P2 | The system-of-record audit log silently discards a malformed line; a marker-store write failure is swallowed | Verified |
| FR-056 | issue | P2 | A correct V16 propagation turns the CI graph gate red until every flag is hand-cleared | Verified |
| FR-053 | issue | P3 | Four file handles opened without a context manager in `audit-log.py` | Verified |
| FR-054 | todo | P3 | `docs-graph.py` is 1,599 lines with three functions over 90 | Verified |
| FR-055 | issue | P3 | `npm run test:docs-explorer:core` is not portable to Windows (PACK-C sibling) | Verified |

**FR-056 was found by obeying the pack's own mandate, not by reading code.** Marking the prior review `superseded` and running the V16-mandated `docs-graph.py flag` propagated `review-suggested` to four inbound neighbours — and `validate`, which is CI gate G5, exits non-zero on *any* flag. So propagating a change correctly turns `main` red until every flagged owner responds, while *skipping* the propagation leaves CI green and is undetectable. The incentive runs against the discipline. V16 calls the flag "a suggestion with provenance"; the gate calls it a build failure. The pack's own `freshness` command already solves this with `--gate warn|fail`; `validate` has no equivalent.

### FR-049 is the finding of this review, and it is convergent

Three separate observations resolve to **one root cause**:

- **5 of 15 deployed scripts have no test at all:** `dream.py`, `apply-learnings.py`, `graphify-setup.py`, `obsidian-setup.py`, `visual-assets-setup.py`.
- **3 of 22 skills have no eval case:** `dream`, `apply-learnings`, `optimize-graph`.
- The intersection is exact: **the continuous-improvement / federation / planning cluster** — the newest capabilities in the repository.

This is not a coverage statistic. `dream.py` writes the **fleet learnings store** and the **defect-class register**; `apply-learnings.py` generates **plans that mutate other repositories**. They are the two scripts whose defects would propagate *across* the fleet, and they are the two with no automated proof. `optimize-graph` — which I added at revision 40 — shipped with no eval case while 26 exist for its siblings.

**Prior finding FR-046 raised exactly this class at revision 33** ("seven deployed scripts have no tests — including the PII control"). The named instance was fixed: `scrub.py` is now tested. **The class was not swept.** That is **RIG-C — "sweep stopped at the instance"** — on its **fourth** confirmed occurrence, and the register already carries it as `uncontrolled`.

The honest reading, unchanged from revision 33 and now with one more data point: **the pack teaches the sweep discipline better than it practises it, and nothing in the toolchain enforces it.** The fix for FR-049 is therefore not "write five test files" — it is a control that fails when a deployed script or a skill ships without proof.

## 5. Lenses

**Reviewed:** architecture (source→install invariant verified by execution, deployment-map conformance, dependency direction), documentation truth (graph validate + bundle staleness), traceability (spec→design→ADR→code→test), testing and proof strength, CI/operations (now runner-verified), portability, supply chain (CI actions pinned to SHAs — spot-verified in `pack-consistency.yml`), accessibility (explainer), and release/publish (Pages workflow green).

**N/A with rationale:** runtime concurrency, data migration, distributed consistency, performance budgets under load — the pack ships **no runtime service, no database, no message transport**. Security/identity is **partially** reviewed: no credential surface exists in the repo; `.mcp.json` is git-ignored (re-verified by `git check-ignore` in this session); a secret scan over changed files returned 0 hits.

**Explicitly not reviewable here:** the *judgment* stages of the skills. A skill is a Markdown instruction to a model; eval cases are the only available proxy, which is precisely why FR-049 matters.

## 6. Adversarial gate

Authors did not self-clear.

- **Test Architect — PASS with a condition.** Every finding carries an executed oracle. **FR-049 was reclassified from *issue* to *risk*** on challenge: there is no observed failure, only absent proof — the same reclassification FR-046 received. **Condition: FR-049 is not cleared by tests that merely import the module** (the identical condition placed on FR-046, which the intervening revisions did not honour for the un-swept siblings).
- **Simplifier — PASS, one strike.** Challenged **FR-054** (file size) as preference rather than defect. Retained at **P3 `todo`**, explicitly not an issue, because `docs-graph.py` is the single most-invoked script in the pack and three >90-line command functions are a real change-risk surface — but the challenge is recorded and the item must not be treated as a defect.
- **Documentation Steward — PASS with a correction.** The prior review's frontmatter reads *"(revision 30)"* while the document body also covers revision 33. Recorded as part of FR-050's scope rather than as a separate finding (deduplicated by root cause: documentation that trails the code).
- **Enterprise Architect — PASS.** The source→install invariant holds and is gated; the generated surfaces are byte-identical after a re-sync. No dependency-direction violation found.
- **Security & Identity — PASS.** No credential surface; ignore rules verified by reading state back; CI actions pinned to SHAs.
- **SRE — PASS with concern.** CI is now runner-verified, which closes the long-standing risk. Concern: **FR-052** — the audit log is the system of record for this project's memory, and it discards a malformed line without a signal.

**Sub-agent evidence was verified, not cited.** A delegated implementation scan reported *"silent-failure and gate integrity: none found"*. That was **materially wrong** — direct inspection found six exception swallows in `audit-log.py` alone, two of them bare `pass`, one of which is code added in this session. FR-052 exists because the delegated claim was checked (E16). Its file-handle and size findings were confirmed by reading the cited lines.

## 7. Readiness verdict

**ADOPTABLE.** This is an upgrade from revision 33's *adoptable with two caveats*: both caveats (FR-044, FR-045) are resolved with controls, the adoption path is verified end-to-end, all seven gates pass, and CI is now proven to execute on a runner rather than inferred to.

**The single condition on that verdict is FR-049.** Shipping a cross-repo federation path with no automated proof is the same governance position the project explicitly refused to accept for the PII control at revision 33. It should not be deferred a second time.

## 8. Confidence ledger

| Claim | Evidence | Confidence |
|---|---|---|
| All seven CI gates pass at `e4eae82` | executed locally, outputs recorded §1 | **Verified** |
| CI executes on a runner and is green on the target commit | `gh run list` — 12 runs, success on `e4eae82` | **Verified** |
| No source→install drift | `sync-pack.ps1` then `git diff --exit-code` → clean | **Verified** |
| FR-044/045/047/048 resolved | code inspected + all 16 scripts smoke-invoked | **Verified** |
| 5 deployed scripts untested, 3 skills un-evaled | filesystem cross-reference of tests and eval cases | **Verified** |
| `docs/_site` is stale | single file, mtime 2026-08-10, 12 revisions behind | **Verified** |
| Explainer CDN + a11y gaps | 3 CDN URLs, 0 `aria-`, 0 skip links | **Verified** |
| Skill *judgment* quality | not testable without evals | **Flagged** |
| The npm launcher failure is environmental, not a repo defect | same tests pass invoked directly | **Verified** |

## 9. Residual risk

- **Skill judgment remains unproven** wherever eval cases are absent (FR-049). Eval cases are a proxy, not a guarantee, even where they exist.
- **`/updatepack`, `/visualize`, and the judgment stages of `/addpacktorepo`** remain unexercised. Revision 33's lesson stands: *an unexercised path is where this project's most serious defects live.*
- **The back-test in `docs/backtest/optimize-graph/`** reports modeled time and token figures. They are labelled Inferred throughout, but a reader who skims the charts and not the integrity panel could mistake a model for a measurement.
- **RIG-C is now at four occurrences and still `uncontrolled`.** Until a control exists, the next review should expect a fifth.

---

**Status:** stopped for human triage. No production code, dependency, schema, CI behaviour or runtime configuration was modified. No remote issues were created.

| | |
|---|---|
| **Completed** | Baseline (7 gates), system map verified, 4 prior findings verified closed, 7 findings raised with oracles, adversarial gate, backlog |
| **Remaining** | Human triage of `docs/backlog/forensic-review-rev42.md` |
| **Best next action** | Triage **FR-049** first — it is the only P1 and it gates the readiness verdict |
