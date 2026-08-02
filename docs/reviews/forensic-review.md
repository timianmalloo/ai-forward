---
id: forensic-review
title: "Forensic Review — AI-Forward repository (revision 18)"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, ci, consistency, supply-chain, documentation]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-backlog, rel: relates-to }
  - { to: forensic-review-20260712, rel: supersedes }
review-by: "2026-11-02"
review-suggested: []
summary: >-
  Comprehensive evidence-based assessment of the AI-Forward repository at commit 53e3afe
  (revision 18). Ten findings, none P0. The two load-bearing results are FR-011 — the
  repository's foundational invariant (pack/ is source, .claude/ and .github/ are generated)
  has no CI gate, proven by drifting a worktree — and FR-020, Copilot receiving 11 of the 23
  personas the deployment map promises.
---

# Forensic Review — AI-Forward repository (revision 18)

## 1. Scope and baseline

- **Repository:** `timianmalloo/ai-forward`
- **Target commit:** `53e3afe59dc3e20a5e1e20a769311980fd194cb4` (`53e3afe`), branch `main`, **0 ahead / 0 behind** `origin/main`
- **Worktree state at review:** **clean** (0 modified files) — no dirty-state caveat applies
- **Scope:** whole repository, comprehensive. 407 tracked files (305 `.md`, 30 `.json`, 30 `.py`, 16 `.html`, 12 `.js`, 4 `.ps1`, 4 `.yml`)
- **Supersedes:** `forensic-review-20260712` (scoped to model orchestration; that capability was reverted in `8801a47`). Its still-open findings **FR-008** and the residual documentation half of **FR-010** are carried forward here rather than duplicated.
- **Constraint honoured:** no production code, dependency, schema, CI behaviour, or runtime configuration was modified. The review archived the superseded review/backlog and wrote this report and its backlog; nothing else changed.

### Baseline commands (run before judging; results are evidence, not review artifacts)

| Command | Result |
|---|---|
| `pwsh tools/verify-bundle.ps1` | **BUNDLE CONSISTENT** — counts, skill/prompt parity, managed-block lists, prose, vendored-foundation drift, 23 eval cases |
| `python -m pytest tests -q` | **107 passed, 1 skipped, 108 subtests** in 38.9 s |
| `node --test tests/docs_explorer/*.test.js` | **31 pass, 1 skipped, 0 fail** (32 tests) |
| `docs-graph.py validate` | **exit 0** — schema-valid, 0 dangling links, 0 orphans |
| `docs-graph.py freshness` | **0 findings** — nothing stale or flagged |
| `pack-doctor.py --strict` | **6 PASS · 0 WARN · 0 FAIL** — reports revision 18 |
| `scrub.py --check docs pack` | **2 findings** (both the same false positive — see FR-017) |
| `npm test` | **fails — "Missing script: test"** (see FR-016) |

**Caveat on the node/npm baseline.** `npm run test:docs-explorer:core` fails locally because npm spawns `cmd.exe`, which does not have `node` on PATH in this environment; invoking `node --test` directly succeeds. This is a **local environment artifact, not a repository defect** — CI runs on `ubuntu-latest` where the npm script works. Recorded so the failure is not mistaken for a finding.

## 2. Recovered system map

The architecture doc (`docs/architecture.md`) was checked against the code and is **substantially accurate**; it describes the pack correctly as a knowledge/tooling package with no inference client, and refers to knowledge docs categorically (`knowledge/*.md`) rather than enumerating them, so revision 18's four new docs do not falsify it. One stale claim was found (a diagram node reading "the 17 skills") and is folded into FR-013.

**What the repository actually is:** a dual-purpose repo — the canonical **source** of the AI-Forward Pack (`pack/`) *and* a live **install** of it (`.claude/`, `.github/{instructions,prompts,agents}`, `docs/`), generated from source by `tools/sync-pack.ps1`.

```
pack/                     SOURCE OF TRUTH (edit only here)
  knowledge/  28 docs     commands/  18 skills     templates/  22
  adapters/   INSTALL.md + managed blocks + per-tool agents/prompts
  evals/ 23 cases   scripts/ 9 deployables   ci/ docs-health.yml (shipped, not self-applied)
        │
        │  tools/sync-pack.ps1   ← the ONLY sanctioned generator
        ▼
.claude/{knowledge,skills,agents}      .github/{instructions,prompts,agents}
docs/{architecture,knowledge,audit,design,security,reviews,backlog,lessons,ai-forward-pack}
tools/  sync-pack · verify-bundle · check-consistency · new-capability · build-web-index · aiforward
tests/  7 pytest modules · 3 node suites · 1 Playwright spec (3 browsers)
.github/workflows/  pack-consistency · docs-context-reference-benchmark · pages
```

**The load-bearing invariant** — stated in `CLAUDE.md`, `AGENTS.md` and `README.md` — is *"when you change anything under `pack/`, re-run `tools/sync-pack.ps1` and commit `pack/`, `.claude/`, `.github/`, and `docs/` together so source and install stay in lockstep."* FR-011 is that this invariant is unenforced.

## 3. Assessment by layer

### 3.1 Architecture — **sound**
Boundaries are clean and the generator is single-sourced. `pack/` has no inbound dependency from the generated trees; the deployment map in `pack/adapters/INSTALL.md` is the stated contract and matches the sync tool's behaviour. Dependency direction is correct (source → generated, never the reverse). No cycles. The dual-purpose design (source + dogfooded install) is unusual but deliberate, documented, and is the reason the pack's own guidance is continuously exercised.

The one architectural weakness is not structural but **operational**: the invariant that makes the dual-purpose design safe is asserted in prose and enforced only by a local PowerShell script a contributor must remember to run (FR-011).

### 3.2 Design — **sound, with one tool defect**
Scripts are stdlib-only Python plus PowerShell, consistent with the stated dependency-averse posture. `docs-graph.py` is the single graph mechanic (V18) and is honoured — no ad-hoc graph scripts were found. The templates and skills are mutually consistent: **all 19 referenced templates and all 4 referenced scripts exist; no template is shipped unreferenced.**

The defect is in `docs-graph.py cmd_rollup`, which computes generated links relative to `--root` rather than to the directory of the document it writes into (FR-012). Because `/design` mandates rollups into `docs/security/{threat-model,privacy-review}.md` — always one directory below the root — **every generated rollup link is broken, in this repo and in every consuming repo.**

### 3.3 Implementation — **healthy**
All three test suites pass. No dangling template/script references. `__pycache__`, `node_modules`, `test-results/` and `*.jsonl.lock` are correctly gitignored, and **zero `.pyc` files are tracked** (a stale `test_model_router.cpython-312.pyc` exists locally from the reverted experiment but is untracked and therefore not a repository defect — ruled out during review). Audit and change logs are integrity-clean: 14/14 and 8/8 entries parse, all ids unique, and the derived `audit-data.js` is in step with the JSONL.

### 3.4 Traceability — **partial**
Spec → architecture → design → code → proof holds for the deliberately-designed subsystems (Docs Explorer, pack-doctor, RAI/scrub, project memory each have a `docs/design/` artifact and proof). The gap is in the **reverse** direction: the consistency checker gates *counts* in six files but not *lists*, and does not scan `docs/index.md` or `docs/architecture.md` at all — so three documents currently claim a skill count they do not enumerate (FR-013). A second traceability break runs from the deployment map to the generator: `INSTALL.md` §1 promises every persona on both tool surfaces and `sync-pack.ps1` delivers only 11 of 23 to Copilot (FR-020).

### 3.5 Testing & CI — **strong suites, incomplete gates**
This is the weakest lens. The repository has genuinely good tests — 107 Python assertions, 32 node contract tests, a 3-browser Playwright spec, deterministic fixtures, canonical-hash parity. **CI runs only a subset:** `pack-consistency.yml` executes four gates and omits pytest entirely, omits the Playwright suite, and omits `docs-graph.py validate/freshness` — the very graph gate the pack *ships to consumers* as `pack/ci/docs-health.yml` (FR-014). Its `paths:` filter also excludes `.claude/**`, `.github/{instructions,prompts,agents}/**` and most of `docs/**`, so a PR touching only the generated trees triggers no workflow at all.

### 3.6 Security & supply chain — **good, one inconsistency**
No secrets found; the two scrub hits are a GitHub noreply bot address in a commented-out CI example (FR-017). Permissions are least-privilege per workflow. `pack-consistency.yml` and `docs-context-reference-benchmark.yml` pin every action by 40-character SHA. **`pages.yml` — the only workflow holding `pages: write` and `id-token: write` — pins none of its four actions**, and the shipped `pack/ci/docs-health.yml` is likewise unpinned, propagating the pattern to every consuming repo (FR-015).

### 3.7 Lenses explicitly N/A
- **Data & persistence / migrations:** N/A — the repo has no database, schema, or migration. The only persisted state is append-only JSONL, reviewed above.
- **Distributed systems / concurrency:** N/A — no services, queues, or concurrent writers beyond `docs-graph.py`'s sibling lock files, which are covered by `test_bounded_process.py` and `test_docs_graph.py`.
- **AI systems / inference cost:** N/A — as `docs/architecture.md` states, this package has no inference client.
- **Accessibility / UX:** partially in scope and **passing** — the Docs Explorer, Audit Explorer and design-language preview are dependency-free local HTML with accessibility contracts under test (`knowledge_surfaces.test.js`, the Playwright accessibility route). The revision-18 mockup harness was render-tested across 7 states, 3 themes, 4 viewports and reduced motion with 0 contrast failures.
- **Privacy:** in scope, no findings — no personal data is collected or stored; `docs/security/privacy-review.md` exists and is graph-linked.

## 4. Findings

Ten findings. **No P0.** One P1, five P2, four P3. One prior finding carried forward; the other resolved into FR-020.

| id | kind | pri | title | confidence |
|---|---|---|---|---|
| **FR-011** | issue | **P1** | Source↔install drift has no CI gate — proven undetectable | **Verified** |
| **FR-012** | issue | **P2** | `docs-graph.py rollup` emits links relative to the wrong base — every rollup link is broken | **Verified** |
| **FR-013** | issue | **P2** | Skill *lists* are ungated: three docs claim a count they do not enumerate | **Verified** |
| **FR-014** | issue | **P2** | pytest, Playwright, and the graph gate never run in CI | **Verified** |
| **FR-015** | risk | **P2** | The only privileged workflow uses floating action tags; the shipped CI template does too | **Verified** |
| **FR-020** | issue | **P2** | Copilot receives 11 of 23 personas — the deployment map promises all of them | **Verified** |
| **FR-016** | issue | **P3** | `npm test` is undefined — the conventional entry point errors | **Verified** |
| **FR-017** | issue | **P3** | `scrub.py` flags GitHub noreply bot addresses (permanent false positive) | **Verified** |
| **FR-018** | todo | **P3** | Ownership hygiene: three owner handles, no CODEOWNERS | **Verified** |
| **FR-019** | todo | **P3** | The `/document` bundle (`docs/_site/`) is stale relative to revision 18 | **Verified** |
| FR-008 | issue | P2 | *(carried forward)* Make bundle/CI consistency a real oracle | Verified |
| FR-010 | — | — | *(closed)* Resolved into FR-020 — the residual was verified and re-scoped | — |

Full remediation detail, acceptance criteria and validation for every item are in **`docs/backlog/forensic-review.md`**.

### 4.1 FR-011 — the load-bearing finding, with its proof

The repository's foundational invariant is that `pack/` is source and `.claude/`/`.github/` are generated. **Nothing enforces it.** `verify-bundle.ps1` checks it locally as step 5 (git-clean-after-sync) but is not run in CI, and `check-consistency.py` — which *is* run in CI — compares counts, skill/prompt parity, managed-block lists and prose totals, never the *content* of the generated trees against source.

**Disconfirming test performed** (in a detached `git worktree` under `%TEMP%`, so the real tree was never touched):

1. Confirmed `pack/knowledge/rigor-protocol.md` and `.claude/knowledge/rigor-protocol.md` were byte-identical (`54ED3586…`).
2. Appended one line to the `pack/` copy only — deliberately skipping `sync-pack.ps1`, exactly as a hurried contributor would.
3. Ran every gate `pack-consistency.yml` runs:

| CI gate | Result on the drifted tree |
|---|---|
| `check-consistency.py` | `clean` — **exit 0** |
| `foundation-check.py` | `clean` — **exit 0** |
| eval well-formedness | `eval cases ok` — **exit 0** |
| node core contracts | not re-run (tests the Explorer core, unrelated to knowledge-doc sync) — *Inferred pass* |

**The drift merges undetected.** The consequence is not local: `/updatepack` copies the *generated* `.claude/` tree into consuming repositories, so a stale generated file propagates outward to every installed repo as though it were the current standard. This is the strongest possible form of the class the prior review named in FR-008; that finding is now backed by a reproduction.

### 4.2 FR-020 — Copilot receives half the persona roster

The pack advertises **23 lenses**, and `AGENTS.md` — the always-on Copilot instruction — tells Copilot users *"Agents in `.github/agents/`"*. The deployment map in `pack/adapters/INSTALL.md` §1 maps **both** categories to both surfaces:

> L91 · `| Peer agents (orchestrator, product-strategist, domain-researcher) | .claude/agents/<name>.md | .github/agents/<name>.agent.md |`
> L92 · `| Adversary agents (the existing 11) | .claude/agents/<name>.md | .github/agents/<name>.agent.md |`

and §1.2 supplies the exact transform for doing so (*"Strip the `tools:` line"*).

**Measured at `53e3afe`:** `.claude/agents/` holds **23**; `.github/agents/` holds **11**. Twelve personas never reach the Copilot surface:

`ai-systems-engineer` · `data-persistence-architect` · `documentation-steward` · `domain-researcher` · `mobile-app-developer` · `native-desktop-developer` · `orchestrator` · `privacy-data-governance` · `product-strategist` · `release-engineer` · `ux-accessibility` · `ux-researcher-ia`

The cause is in the generator: `tools/sync-pack.ps1` populates `.claude/agents/` from **both** `adapters/claude-code/agents/` and `adapters/copilot/agents/`, but populates `.github/agents/` from `adapters/copilot/agents/` **only** — the §1.2 transform is documented and never executed.

Two things make this material rather than cosmetic:

1. **It removes vetoes on one tool.** Every persona revision 18 depends on is in the missing set — the **Data & Persistence Architect** (owner of the new data-modelling standard and its migration hard veto) and **UX & Accessibility** (lead of `/ui-design`, holder of the accessibility hard veto). A Copilot user following `AGENTS.md` cannot `@`-mention either.
2. **INSTALL.md contradicts itself.** L108 states the three peer agents are instead *"described in `knowledge/collaborative-personas.md`"* — a partial rationale that directly conflicts with L91, and that does not account for the other nine missing personas at all.

**Why it survived every gate.** `check-consistency.py` derives the roster from the **source adapters** — `verify-bundle` reports it as *"23 lenses (12 claude-code + 11 copilot)"* — so the count is correct at source and the deployment shortfall is structurally invisible to the only check that counts lenses. Nothing compares the roster against what each surface actually receives. This is the same shape as FR-011 and FR-013: the checker validates source, never the generated result.

The prior review's FR-010 residual named this concern but left it unverified; it is now Verified and re-scoped as FR-020. Note the pack's own rule **is** honoured where it applies: **no** `.github/agents/*.md` carries a `tools:` line, so nothing that *did* ship violates §1.2.

## 5. Persona verdicts (Adversary Mode)

| Persona | Verdict | Note |
|---|---|---|
| **Enterprise Architect** | **PASS** | Boundaries and generator single-sourcing are sound; the weakness is operational enforcement, not structure. |
| **Test Architect** | **PASS-WITH-CONDITIONS** | Every finding carries an oracle: FR-011 and FR-012 are reproductions, FR-016/017 are executions, the rest are file reads. Condition: the node-gate row of the FR-011 table is labelled *Inferred*, not claimed as run. **Rejected** during review: a proposed finding that `docs/lessons/defect-classes.md` is mostly `uncontrolled` — that is its designed initial state, not a defect. |
| **Documentation Steward** | **BLOCK → recorded** | FR-013, FR-019 and FR-020's INSTALL.md self-contradiction are documentation-truth failures; a file that states "18 skills" and lists 17, and a deployment map that promises 23 agents on a surface holding 11, are self-contradicting. Blocks documentation readiness only; does not suppress this report. |
| **Enterprise Architect (2nd pass)** | **BLOCK → recorded** | FR-020: the generator does not implement the documented deployment map. Tool-parity is a stated architectural property of this pack (INSTALL §1.3, "fit for both"); it is currently false on the Copilot surface. |
| **Security & Identity** | **PASS-WITH-CONDITIONS** | No secrets, least-privilege permissions. Condition: FR-015 — the highest-privilege workflow is the only unpinned one, and the pattern is shipped to consumers. Not P1: all four actions are first-party `actions/*` and no compromise is evidenced. |
| **Release Engineer** | **BLOCK → recorded** | FR-011 + FR-014 mean the release gate does not gate what it claims to. |
| **SRE** | **PASS** | Deterministic, bounded tooling; `bounded_process.py` is exercised by tests. |
| **The Simplifier** | **PASS** | Removed three candidate findings as preference-not-defect: the overloaded `skill` field on four knowledge/script eval cases (by design), the untracked stale `.pyc` (gitignored), and the archived review's historical "17 skills" prose (accurate as history). |
| **Data & Persistence · Distributed Systems · AI Systems · Privacy** | **N/A** | Scoped out with rationale in §3.7. |

**No persona cleared its own authored work.** Findings were authored in Peer Mode and attacked in Adversary Mode before entering the backlog.

## 6. Readiness verdict

> **PASS-WITH-CONDITIONS.** The repository is healthy: every test suite is green, the knowledge graph is valid and fresh, pack-doctor is clean, no secrets, and no P0. It is *shippable today*.
>
> It is **not adequately gated**, and it is **not at parity across its two tools**. The single most important invariant in the repository — that the generated trees match their source — can be violated silently and shipped outward to every consuming repo (FR-011). Separately, Copilot users receive half the persona roster the pack advertises, including both vetoes revision 18 introduced (FR-020).
>
> **FR-011 is the highest-leverage action** and the cheapest: the check already exists in `verify-bundle.ps1`; it simply is not run where it matters. **FR-020 is the highest-impact on users**, and its fix is a handful of lines in `sync-pack.ps1` implementing a transform INSTALL.md already specifies.

## 7. Confidence ledger

| Claim | Evidence | Confidence |
|---|---|---|
| Drifted `pack/` passes all CI gates | Worktree reproduction, 3 gates executed, exits recorded | **Verified** |
| The node gate would also pass on that drift | Reasoned from what the suite asserts; not re-executed | **Inferred** |
| Rollup links are broken wherever output is not at root | `os.path.relpath` computation: emitted `design/…` does not resolve, `../design/…` does | **Verified** |
| README, copilot-instructions and docs/index omit `/ui-design` | Pattern count = 0 in each; count strings say 17/18 | **Verified** |
| pytest/Playwright/graph gates absent from CI | Full read of all three workflow files | **Verified** |
| `pages.yml` is the only unpinned workflow | Enumerated `uses:` across all workflows against a 40-hex-SHA test | **Verified** |
| No secrets in committed content | `scrub.py --check` over `docs` + `pack`, 2 hits, both inspected in context | **Verified** (tool is a first-pass, not CI-grade — its own stated limit) |
| Architecture doc is substantially truth-to-code | Read against the tree; knowledge docs referenced categorically | **Verified** |
| No dangling template/script references | Enumerated all `templates/…` and `scripts/…` mentions in skills against the filesystem | **Verified** |
| Copilot surface holds 11 of 23 personas | Directory enumeration on both surfaces; set difference listed; `sync-pack.ps1` copy rules read | **Verified** |
| No `.github/agents/*.md` violates the strip-`tools:` rule | Pattern scan for `^tools:` across the Copilot agent surface — 0 hits | **Verified** |

## 8. Residual risk — what this review did not cover

- **Deep semantic review of all 305 markdown files.** Standards were reviewed structurally (references resolve, counts, links, frontmatter) and the revision-18 additions were read in full; the older knowledge docs were **not** re-read line-by-line for internal contradiction.
- **Runtime behaviour of the skills themselves.** The eval cases were checked for well-formedness, not *executed* — running them requires a live agent session per case. The evals therefore prove the harness, not the skills' outputs.
- **The self-hosted benchmark workflow** (`docs-context-reference-benchmark.yml`) could not be exercised; it requires a dedicated ephemeral runner.
- **`scrub.py` recall.** A regex first-pass cannot prove the absence of secrets. The RAI policy already transfers real enforcement to gitleaks/Presidio in CI; neither is currently wired (a known, documented position, not a new finding).
- **Cross-platform CI.** All gates run on `ubuntu-latest`; the PowerShell tooling (`sync-pack.ps1`, `verify-bundle.ps1`) is never exercised in CI on any platform. Folded into FR-014's remediation.
