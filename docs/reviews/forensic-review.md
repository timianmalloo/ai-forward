---
id: forensic-review
title: "Forensic Review — AI-Forward model orchestration"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, model-orchestration]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-backlog, rel: relates-to }
review-by: 2026-10-10
review-suggested: []
summary: >-
  Evidence-based assessment of AI-Forward commit 5d7b952 focused on model orchestration. The
  user accepted the readiness BLOCK and reverted the capability; the report is retained as
  historical evidence.
---

# Forensic Review — AI-Forward model orchestration

## 1. Scope and baseline

> **Post-review disposition (2026-07-12): reverted.** The user chose to remove the
> model-orchestration standard, router, tests, and active wiring rather than implement the
> proposed backlog. Findings remain below as evidence. FR-001–FR-007 and FR-009 are closed by
> removal; FR-008 and the pre-existing agent-deployment portion of FR-010 remain independent
> repository findings.

- **Repository:** `timianmalloo/ai-forward`
- **Target commit:** `5d7b95235e664b7779c7a653c000f6a199403070`
  (`feat: add Model-Orchestration Standard to the AI-Forward pack (rev 17)`)
- **Branch:** `main` tracking `origin/main`
- **Initial worktree:** clean
- **Review scope:** whole-repository architecture/documentation baseline, with primary focus on
  the model-orchestration standard, router, tests, adapters, skills, audit path, and release
  proof introduced by `5d7b952`.
- **Constraint:** review/docs only. No pack source, production behavior, dependency, schema,
  runtime configuration, or CI behavior was changed.

### Existing proof baseline

| Check | Result | Interpretation |
|---|---|---|
| `python -m unittest discover -s tests/docs_explorer -p "test_*.py"` | **117 passed, 1 skipped** | Existing Python regression baseline green |
| `python tools/check-consistency.py` | **clean** | Counts and skill/prompt parity green; scope does not include orchestration/agent parity |
| `python pack/scripts/pack-doctor.py --strict` | **0 FAIL / 0 WARN / 6 PASS** | Install and graph health green |
| `docs-graph.py inventory` | **22 artifacts; no problems/stale/flagged/orphans/drift** | Documentation graph healthy before this report |
| `pwsh tools/verify-bundle.ps1` | exits 0, prints **BUNDLE CONSISTENT** | Finding FR-008: the same run changed `web/pack-index.js` but did not fail |
| Router probes | valid output; unknown skill exits 2 | Static lookup works for its implemented contract |

The `verify-bundle`-generated `web/pack-index.js` change was inspected, recorded as evidence,
then reverted because this review does not alter generated pack surfaces.

## 2. Recovered system map

### Intended control plane

`model-orchestration.md` defines nine activity archetypes (A–I), an efficiency/cost profile,
hard reviewer-model independence, deterministic-to-script routing, and an Orchestrator-owned
Capability Router. `model-router.py` is presented as the deterministic lookup; Copilot CLI /
Claude Code are the execution hosts.

### Actual control plane

1. The standard is globally deployed through `.claude/knowledge/` and a Copilot instruction.
2. `model-router.py` is a pure static lookup from **skill + profile** to abstract tiers and
   placeholder model labels.
3. No skill, Orchestrator agent, AI Systems agent, audit writer, or dispatch adapter invokes
   that lookup.
4. The Copilot install has 11 adversary agents and no Orchestrator peer agent, despite the
   deployment map promising one.
5. Hard reviewer independence is metadata (`distinct_from_author: true`), not an enforcement
   boundary.

The current capability is therefore **useful policy guidance plus an inert deterministic
lookup**, not the automatic task/model orchestration claimed by M1/M3/M5/M7/M11/M12.

## 3. Architecture, design, and implementation assessment

| Lens | Assessment |
|---|---|
| Architecture | Source→build→install layering remains coherent. The new host-level orchestration edge is declared but not implemented. |
| Design | Missing executable contracts for task risk tier, model roster resolution, author/reviewer identity, human override, provider/data policy, and audit capture. |
| Implementation | `model-router.py` is small, deterministic, stdlib-only, and side-effect free. It duplicates policy and cannot dispatch or resolve a current host model. |
| Traceability | User decisions → standard/router exist; standard/router → skills/personas/audit/evals is broken. |
| Testing | Router unit baseline is green, but behavioral orchestration, policy parity, cost-transition, CLI JSON, model independence, and classification are not proven. |
| Security | No active code side effect or credential handling added. |
| Privacy | The global instruction can cause task context to reach selected/distinct models; no data-class/provider/residency/DPA boundary is defined. |
| Data/migrations | N/A for current inert lookup. The cost router nevertheless mishandles `/migrate`'s T2 risk tier. |
| Distributed systems | N/A — no network/runtime service in the repository. |
| Reliability/operations | Routing decisions and actual cost are not observable in the audit log. |
| Performance/cost | `cost` is a heuristic downgrade profile, not measured optimization; no usage/cost feedback loop. |
| Accessibility/UX | N/A — no user-facing UI change. |
| Supply chain | Positive: no new dependency; Python 3.8+ stdlib only. |
| Release | Bundle gate is incomplete: it reports post-sync dirtiness but still succeeds; orchestration Python tests are not in CI. |

## 4. Findings

### FR-001 — Declared auto-dispatch has no executable integration

- **Category / kind / priority:** architecture · issue · **P1**
- **Location:** `pack/knowledge/model-orchestration.md:42,75,111`;
  `pack/adapters/claude-code/agents/orchestrator.md:11-21`;
  `tools/sync-pack.ps1:119-125`; `pack/adapters/INSTALL.md:93,204,214-215`
- **Observed evidence:** repo-wide search finds no `model-orchestration` or `model-router`
  reference in any `pack/commands/*/SKILL.md` or persona agent. The Copilot install contains
  only the 11 adversaries; there is no Orchestrator agent. The static script performs no
  dispatch.
- **Violated contract:** M1, M3, M7, M8, M12; INSTALL deployment-map claims.
- **Consequence:** users are told task/model routing is automatic while execution remains
  dependent on an unstructured model interpretation of a global instruction.
- **Disconfirming check:** the global instruction does make the policy visible to a compliant
  host model, and Copilot CLI `1.0.70` help exposes `/model`, `/subagents`, `/fleet`, and
  `/tasks`; this reduces the finding from "host incapable" to **repository binding absent**.
- **Confidence:** **Verified**

### FR-002 — Hard adversary-model independence is contradicted and unenforced

- **Category / kind / priority:** correctness/governance · issue · **P1**
- **Location:** `pack/knowledge/model-orchestration.md:79`;
  `pack/adapters/claude-code/agents/orchestrator.md:15`;
  `pack/scripts/model-router.py:74-105`; `pack/adapters/INSTALL.md:214-215`
- **Observed evidence:** M5 says same-model hard-veto review is not cleared. The Orchestrator
  still prescribes a same-model inline Copilot turn. The router sets a boolean but accepts no
  author/reviewer model identities and cannot block a match or request human override.
- **Violated contract:** M5; BoK D3 / Rules of the Road §3.2.
- **Consequence:** a hard veto can be represented as independent while still being produced by
  the author model.
- **Disconfirming check:** this forensic review successfully used distinct models, proving the
  host can support the target behavior; the repository simply does not enforce it.
- **Confidence:** **Verified**

### FR-003 — Cost routing can downgrade work that the standard defines as T2

- **Category / kind / priority:** correctness · issue · **P1**
- **Location:** `pack/scripts/model-router.py:70-92`;
  `pack/knowledge/model-orchestration.md:77`;
  `pack/knowledge/agent-rules-of-the-road.md:52`
- **Observed evidence:** the router accepts only skill/profile. `migrate --profile cost`
  downgrades broad reasoning from frontier to mid, although data migration is always a T2
  trigger and M4 forbids clipping T2/irreversible work.
- **Violated contract:** M4 and Rules-of-the-Road effort tiers.
- **Consequence:** the cost knob can weaken the exact high-cost-of-error reasoning it promises
  to protect.
- **Disconfirming check:** E remains frontier and `define-architecture` / `investigate` are
  protected; the defect is the missing task-risk input and incomplete protection set.
- **Confidence:** **Verified**

### FR-004 — No behavioral eval or sufficient proof for the global instruction

- **Category / kind / priority:** testing/AI · issue · **P1**
- **Location:** `pack/knowledge/testing-strategy.md:26,171-174`;
  `tests/docs_explorer/test_model_router.py:27-85`; `pack/evals/cases/`
- **Observed evidence:** no orchestration eval case exists. Unit tests assert the static lookup,
  not a skill classifying stages, invoking host-valid models, honoring an override, enforcing
  distinct review, or writing audit evidence. No model-orchestration Proof Pack/red-run
  attestation exists.
- **Violated contract:** Testing Strategy A6; Test Architect veto-clears-when.
- **Consequence:** a globally applied behavior-shaping instruction can regress or remain inert
  while all gates pass.
- **Disconfirming check:** 9 targeted router tests and the full 117-test suite pass; they prove
  deterministic lookup behavior only.
- **Confidence:** **Verified**

### FR-005 — Router duplicates policy and cannot resolve a host-valid model or stage

- **Category / kind / priority:** design/maintainability · issue · **P2**
- **Location:** `pack/knowledge/model-orchestration.md:48-67,87-99,137`;
  `pack/scripts/model-router.py:25-68,108-119,170-185`
- **Observed evidence:** archetypes, skill profiles, and tiers are hand-duplicated. The standard
  says the script resolves the current Copilot roster, but it returns placeholders such as
  `strongest reasoning` and `high/xhigh/max`. It accepts no stage, task tier, author model,
  available-model roster, provider policy, or override.
- **Violated contract:** M1, M3, M5, M8; Solution-Selection Ladder / single source of truth.
- **Consequence:** roster or skill changes can drift; output cannot be passed directly to a
  host task call; "dispatch" is misleading.
- **Disconfirming check:** current script/doc skill sets match and CLI JSON is syntactically
  valid; the defect is contract scope and duplicated authority.
- **Confidence:** **Verified**

### FR-006 — Routing audit evidence cannot be recorded

- **Category / kind / priority:** observability/governance · issue · **P2**
- **Location:** `pack/knowledge/model-orchestration.md:109`;
  `pack/scripts/audit-log.py` append schema; `docs/audit/audit-log.jsonl:10`
- **Observed evidence:** the audit writer has no routing/profile/tier/model/effort fields.
  `al-0010`, the run that introduced M11, records none.
- **Violated contract:** M11; audit/show-your-work contract.
- **Consequence:** efficiency-versus-cost quality, model independence, model drift, and spend
  cannot be audited or tuned.
- **Disconfirming check:** free-text summary can mention routing, but it is not structured,
  complete, or mechanically enforceable.
- **Confidence:** **Verified**

### FR-007 — Deterministic lifecycle mechanics remain model-interpreted prose

- **Category / kind / priority:** design/reliability · issue · **P2**
- **Location:** `pack/knowledge/model-orchestration.md:81`;
  `pack/commands/addpacktorepo/SKILL.md:57-100`;
  `pack/commands/updatepack/SKILL.md:41-88`
- **Observed evidence:** both skills are classified A/B, but installation/update copy,
  wrapping, marker replacement, idempotency, and verification remain long prose procedures;
  no install/update script exists.
- **Violated contract:** M6 and LOA P2.
- **Consequence:** repeated file mechanics remain non-deterministic and expensive despite the
  explicit user decision to move them to scripts while preserving the skill surface.
- **Disconfirming check:** audit/prompt/graph/sync/extension mechanics are already correctly
  script-backed; the gap is localized to remaining lifecycle workflows.
- **Confidence:** **Verified**

### FR-008 — Bundle and CI gates do not prove the claimed consistency

- **Category / kind / priority:** release/testing · issue · **P2**
- **Location:** `tools/verify-bundle.ps1:59-76`;
  `.github/workflows/pack-consistency.yml:27-68`;
  `tools/check-consistency.py`
- **Observed evidence:** from a clean commit, `verify-bundle` regenerated a stale
  `web/pack-index.js`, reported the dirty path, exited 0, and printed BUNDLE CONSISTENT.
  Python router tests are absent from CI; CI is Ubuntu-only; consistency checks do not compare
  router keys to real skills or promised peer agents to deployed Copilot agents.
- **Violated contract:** `/extendaibundle` clean-after-sync proof; M7 Windows/macOS claim;
  release consistency gate.
- **Consequence:** the release oracle can certify drift and omit the capability's tests.
- **Disconfirming check:** counts, foundation drift, eval JSON shape, and Node core tests are
  genuinely enforced.
- **Confidence:** **Verified**

### FR-009 — Automatic model routing lacks a provider/data-governance boundary

- **Category / kind / priority:** privacy/data governance · **risk** · **P1**
- **Location:** `pack/knowledge/model-orchestration.md:75,79,83,99,109`;
  `pack/knowledge/ai-commercial-models.md:78-82`
- **Observed evidence:** routing keys on capability/cost, not payload sensitivity. No provider
  allowlist, data class, commercial-vs-consumer tier, DPA/no-training, residency, or
  cross-provider approval field exists. M5 may send the full artifact to a distinct provider.
- **Violated contract:** Privacy persona purpose/minimization/egress basis; AC6–AC7.
- **Consequence:** downstream work or personal data could be routed to a model/provider that
  the repository or tenant has not approved.
- **Disconfirming check:** `model-router.py` itself is inert and makes no network call; the risk
  begins at the globally applied host-agent dispatch instruction.
- **Confidence:** **Verified missing control; adverse outcome Inferred**

### FR-010 — Public documentation still overstates and mislinks the capability

- **Category / kind / priority:** documentation · todo · **P3**
- **Location:** `pack/OVERVIEW.md` §2;
  `pack/adapters/managed-blocks/CLAUDE.block.md:19-20`;
  `pack/adapters/INSTALL.md:93,204,214-215`;
  `docs/notes/note-20260712-model-orchestration-policy.md:13-17`
- **Observed evidence:** OVERVIEW has no standard bullet; the Claude block points to nonexistent
  top-level `scripts/model-router.py`; INSTALL promises peer Copilot agents that are not
  deployed and describes obsolete single-agent behavior; the decision note says persona hints
  and per-skill dispatch were shaped although they were not implemented.
- **Violated contract:** Documentation Steward truth-to-code mandate.
- **Consequence:** readers infer a completed, executable integration.
- **Disconfirming check:** source/install copies are otherwise byte-consistent and counts are
  correct.
- **Confidence:** **Verified**

## 5. Documentation corrections completed by this review

Review-only corrections (no pack/runtime source changes):

- updated `docs/architecture.md` with current counts, tool surface, and the actual
  model-orchestration control plane;
- updated `docs/index.md` to 17 skills and linked this review/backlog;
- refreshed `docs/_meta.json` to target commit `5d7b952`;
- extended `docs/security/privacy-review.md` with the model-routing LINDDUN boundary.

## 6. Persona gate record

| Persona | Verdict | Veto / condition | Residual focus |
|---|---|---|---|
| Enterprise Architect (distinct Claude model) | **BLOCK** (advisory) | Standard is normative but unwired; Copilot runtime binding missing | Host binding / ADR |
| AI Systems Engineer (distinct Claude model) | **PASS-WITH-CONDITIONS** | Narrow veto clears for inert lookup; Major integration/eval/audit gaps remain | Classification, roster, audit, Mac proof |
| Test Architect (distinct Claude model) | **BLOCK** | No behavioral eval/Proof Pack; mutation-surviving tests | CI gate withheld |
| Documentation Steward (distinct Claude model) | **BLOCK** (advisory) | Public surface contradicts source/runtime | Orchestrator/skills/overview |
| Simplifier (distinct GPT model) | **BLOCK** (soft) | Router duplicates policy and is pseudo-dispatch until wired | Net ~260 lines removable if left advisory |
| Privacy & Data Governance (distinct Claude model) | **BLOCK** (hard) | No data-class/provider/residency/egress basis | Add governance boundary before real dispatch |

`GATE forensic-review · 2026-07-12 · distinct-model Enterprise + AI Systems + Test
Architect + Documentation Steward + Simplifier + Privacy · findings evidence-linked and
disconfirmed · verdict: BLOCK for model-orchestration readiness · unresolved vetoes:
Test Architect (behavioral proof), Privacy (egress basis) · author did not self-clear`

## 7. Readiness verdict

**Repository baseline:** **healthy** — existing deterministic tests, install health, graph
health, and source/install count parity pass.

**Model-orchestration capability:** **REVERTED after BLOCK.** The pack makes no automatic
model-per-task routing claim.

## 8. Confidence ledger

| Claim | Evidence / disconfirmation | Label |
|---|---|---|
| Router lookup is deterministic and safe | stdlib-only source; compile + unit suite; no I/O/network | **Verified** |
| Auto-dispatch is implemented | global instruction exists, but no skill/persona/adapter invocation and no Copilot Orchestrator | **Verified false** |
| Cost mode protects T2 | `migrate --profile cost` downgrades D; E remains protected | **Verified false** |
| Hard reviewer independence is enforced | boolean only; contradictory inline-turn instruction | **Verified false** |
| Existing pack remains operational | 117 tests; consistency; doctor; graph inventory | **Verified** |
| Windows/macOS parity | Windows execution passes; no macOS CI | **Flagged** |
| Cross-provider routing is governance-safe | no active network in script; no dispatch policy fields | **Flagged risk** |

## 9. Residual risk and what would change the verdict

The blocked capability was removed, so no proof is now required. Any future reintroduction
must begin as a new spec/ADR and satisfy the original FR-001–FR-009 constraints before landing.

## 10. Status

| | |
|---|---|
| **Completed** | Baseline, architecture reconstruction, all engineering lenses, distinct-model adversarial gate, 10 deduplicated findings, docs corrections, proposed backlog |
| **Remaining** | FR-008 (bundle dirty-tree oracle) and the pre-existing Copilot peer-agent deployment-map mismatch recorded under residual FR-010 |
| **Best next action** | None for model orchestration. Treat any future proposal as new work, not continuation of this backlog. |
