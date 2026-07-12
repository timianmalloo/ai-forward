---
id: forensic-review-backlog
title: "Forensic Review Backlog — Model orchestration"
type: doc
status: proposed
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [backlog, model-orchestration]
links:
  - { to: forensic-review, rel: refines }
  - { to: architecture, rel: depends-on }
review-by: 2026-10-10
review-suggested: []
summary: >-
  Historical remediation backlog from the model-orchestration forensic review. The capability
  was reverted; orchestration-specific items are closed by removal. FR-008 and residual FR-010
  remain independent repository findings.
---

# Forensic Review Backlog — Model orchestration

*Historical backlog for `docs/reviews/forensic-review.md`. The user selected revert rather than
remediation. FR-001–FR-007 and FR-009 are **closed by removal**. FR-008 and the pre-existing
deployment-map portion of FR-010 remain proposed repository work.*

## Delivery phases

| Phase | Goal | Items |
|---|---|---|
| Closed by revert | Removed model orchestration and all active claims/wiring | FR-001–FR-007, FR-009 |
| Residual repository work | Improve bundle proof and reconcile pre-existing Copilot peer-agent deployment docs | FR-008, FR-010 |

---

## FR-001 — Wire model orchestration into both host tool surfaces

- **Kind / priority / status:** issue · **P1** · closed-by-revert
- **Evidence:** `model-orchestration.md:M1/M3/M7/M8/M12`; zero skill/agent router
  references; `sync-pack.ps1:119-125`; missing `.github/agents/orchestrator.agent.md`.
- **Affected scope:** all T1/T2 skill execution; Copilot CLI and Claude Code adapters.
- **Consequence:** auto-dispatch is a claim, not a repeatable execution path.
- **Recommended remediation:** run `/design` for one host-binding contract. Define a single
  declarative routing manifest consumed by (a) the Orchestrator agent, (b) all skill surfaces,
  and (c) the deterministic router. Ship a Copilot Orchestrator agent and update the Claude
  Orchestrator. Prefer one common routing hook over 17 hand-maintained copies.
- **Acceptance criteria:**
  1. Invoking any T1+ skill states profile, task tier, stage archetype, resolved host model, and
     effort before authoring starts.
  2. `efficiency` is the default; an explicit user `cost`/model override wins and is shown.
  3. `.claude/agents/orchestrator.md` and `.github/agents/orchestrator.agent.md` both exist and
     implement the same routing contract.
  4. A smoke run of `/forensicreview` dispatches D/E tasks using host-valid model IDs.
- **Validation:** Copilot CLI integration trace + adapter parity test + consistency gate.
- **Dependencies:** none
- **Suggested owner:** Orchestrator + AI Systems Engineer + Release Engineer
- **Next skill:** `/design`

## FR-002 — Enforce hard reviewer-model independence

- **Kind / priority / status:** issue · **P1** · closed-by-revert
- **Evidence:** M5 vs `orchestrator.md:15`; router E record is metadata only.
- **Affected scope:** every hard-veto gate.
- **Consequence:** self-review can be represented as independent.
- **Recommended remediation:** carry `author_model` and `reviewer_model` in the dispatch/gate
  context; reject equality; if no distinct allowed model exists, stop for a recorded human
  overrule/deviation. Remove the same-model inline-turn rule.
- **Acceptance criteria:**
  1. Same author/reviewer model returns BLOCK and cannot close the gate.
  2. Distinct allowed models return PASS-to-review.
  3. One-model environments surface the exact human-overrule prompt and record the deviation.
  4. Gate/audit output records both model identities.
- **Validation:** deterministic independence unit tests + Copilot CLI hard-veto integration test.
- **Dependencies:** FR-001
- **Suggested owner:** AI Systems Engineer + Test Architect + Orchestrator
- **Next skill:** `/design` → `/implement`

## FR-003 — Make cost routing aware of T0/T1/T2 and irreversible surfaces

- **Kind / priority / status:** issue · **P1** · closed-by-revert
- **Evidence:** M4; Rules of the Road §0.2; `migrate --profile cost` returns D=`mid`.
- **Affected scope:** migrate, design/specify for T2 work, forensic review, any dynamically
  high-risk invocation.
- **Consequence:** cost mode can reduce rigor below the governing risk tier.
- **Recommended remediation:** add required task `effort_tier` (`T0|T1|T2`) and triggered
  constraints (`irreversible`, `security`, `data`, `money`) to the routing input. No
  load-bearing stage downgrades at T2.
- **Acceptance criteria:**
  1. `route --skill migrate --profile cost --tier T2` keeps D/E frontier.
  2. Any T2 invocation produces the same rigor tiers under cost and efficiency.
  3. T1 `specify --profile cost` may downgrade D only when no hard trigger is present.
  4. Unknown/missing task tier fails closed for irreversible skills.
- **Validation:** red-first table/property tests against every skill/profile/tier combination.
- **Dependencies:** FR-005 single routing manifest recommended
- **Suggested owner:** AI Systems Engineer + Test Architect
- **Next skill:** `/implement`

## FR-004 — Add behavioral orchestration evals and a Proof Pack

- **Kind / priority / status:** issue · **P1** · closed-by-revert
- **Evidence:** Testing Strategy A6; no orchestration eval case; deterministic lookup tests only;
  no Proof Pack/red-run attestation.
- **Affected scope:** global model-orchestration instruction and all skill behavior.
- **Consequence:** inert or regressed orchestration can merge green.
- **Recommended remediation:** add golden cases for representative skills (`specify`,
  `define-architecture`, `implement`, `forensicreview`, `migrate`) with deterministic trace
  assertions and a distinct judge where semantic judgment is needed. Capture a Proof Pack.
- **Acceptance criteria:**
  1. Golden traces assert stage classification, profile, task tier, host-valid model, effort,
     distinct reviewer, override behavior, and audit fields.
  2. A deliberately same-model reviewer case fails.
  3. A deliberately T2 cost-downgrade case fails.
  4. Tests are observed red before enforcement and linked in a Proof Pack.
- **Validation:** `run-evals.py` + integration tests + mutation survey.
- **Dependencies:** FR-001, FR-002, FR-003
- **Suggested owner:** Test Architect + AI Systems Engineer
- **Next skill:** `/implement`

## FR-005 — Replace duplicated placeholders with one host-resolvable routing contract

- **Kind / priority / status:** issue · **P2** · closed-by-revert
- **Evidence:** standard §2/§4 duplicated in `model-router.py`; placeholders such as
  `strongest reasoning`; no stage/roster/author/available-model inputs.
- **Affected scope:** model-router, standard, skills, adapters, future roster updates.
- **Consequence:** policy drift and output that cannot be dispatched.
- **Recommended remediation:** choose explicitly:
  - **tier-only advisory:** delete model/effort placeholders and state that the host resolves;
    or
  - **real resolver:** use a versioned roster/config sourced from Copilot CLI `/model` /
    `/subagents` capabilities and return valid model IDs plus one exact effort.
  Keep archetype/skill mapping in one machine-readable source and derive docs/tests.
- **Acceptance criteria:**
  1. No hand-duplicated skill-profile table.
  2. Resolver output is either honestly tier-only or accepted directly by the host API.
  3. Unknown/stale/unavailable models fail explicitly.
  4. Stage-level routing is representable.
- **Validation:** schema/parity tests + current-CLI contract spike on Windows and macOS.
- **Dependencies:** architecture choice from FR-001
- **Suggested owner:** AI Systems Engineer + Patterns Expert + Simplifier
- **Next skill:** `/design`

## FR-006 — Extend the audit contract for routing evidence

- **Kind / priority / status:** issue · **P2** · closed-by-revert
- **Evidence:** M11; fixed audit schema; `al-0010` has no routing data.
- **Affected scope:** `audit-log.py`, audit standard/viewer, every T1/T2 skill last action.
- **Consequence:** no evidence for model choice, independence, cost, or governance.
- **Recommended remediation:** add a structured routing object containing profile, task tier,
  stage, activity archetype, model, effort, author/reviewer identities, provider/region/data
  class where applicable, override/deviation, and usage/cost when exposed by the host.
- **Acceptance criteria:**
  1. `audit-log.py append` accepts and preserves validated routing JSON.
  2. Viewer/search exposes profile/model/override without leaking prompt content.
  3. T1/T2 skill audits fail validation when load-bearing D/E routing is absent.
  4. Regression test proves round trip.
- **Validation:** audit-log unit tests + schema fixture + viewer test.
- **Dependencies:** FR-001, FR-009
- **Suggested owner:** AI Systems Engineer + SRE + Privacy/Data Governance
- **Next skill:** `/design` → `/implement`

## FR-007 — Extract install/update mechanics into deterministic scripts

- **Kind / priority / status:** issue · **P2** · closed-by-revert
- **Evidence:** M6; procedural copy/reconcile logic remains in `addpacktorepo` and `updatepack`
  skill prose.
- **Affected scope:** pack installation and update lifecycle.
- **Consequence:** non-deterministic file operations, harder idempotency and recovery testing,
  unnecessary frontier-model use.
- **Recommended remediation:** implement one cross-platform stdlib lifecycle script with
  `install`, `update`, and `--dry-run`; skills remain the human-facing wrappers that perform
  recon/approval, invoke the script, and explain results.
- **Acceptance criteria:**
  1. Fresh install and update are idempotent and resumable after interruption.
  2. Managed blocks, Copilot wrapping, protected files, and `.gitignore` directives are tests.
  3. Dry-run has zero writes and matches apply output.
  4. Skills contain no manual copy loop.
- **Validation:** temp-repo integration tests on Windows/macOS.
- **Dependencies:** none
- **Suggested owner:** Release Engineer + Test Architect
- **Next skill:** `/design` → `/implement`

## FR-008 — Make bundle/CI consistency a real oracle

- **Kind / priority / status:** issue · **P2** · proposed
- **Evidence:** `verify-bundle.ps1:59-76` does not fail on dirty sync; stale web index
  reproduction; CI omits Python tests and runs only Ubuntu; consistency ignores router/peer
  parity.
- **Affected scope:** pack release gate.
- **Consequence:** drift or an untested router can ship under BUNDLE CONSISTENT.
- **Recommended remediation:** compare the tree before/after sync and fail on **new** generated
  drift (or sync twice and prove the second run is a no-op); run full Python tests; validate
  router keys against filesystem and agent deployment-map parity; add Windows/macOS matrix
  coverage for orchestration/lifecycle scripts.
- **Acceptance criteria:**
  1. The reproduced stale `web/pack-index.js` condition exits nonzero.
  2. Missing/extra routing skill or promised Copilot peer agent fails consistency.
  3. `test_model_router.py` runs in CI.
  4. Windows + macOS router/lifecycle smoke jobs pass.
- **Validation:** CI mutation fixtures + local `verify-bundle` fault injection.
- **Dependencies:** FR-005 manifests simplify parity
- **Suggested owner:** Release Engineer + Test Architect
- **Next skill:** `/implement`

## FR-009 — Add provider/data governance before automatic dispatch

- **Kind / priority / status:** risk · **P1** · closed-by-revert
- **Evidence:** M3/M5/M7 route context across models; no data class/provider allowlist/
  residency/DPA/no-training boundary; privacy review forensic LINDDUN.
- **Affected scope:** every downstream repo using automatic model selection.
- **Consequence:** work/personal/regulated data may cross an unapproved provider or region.
- **Recommended remediation:** add a governance axis before model resolution:
  `data_class`, allowed providers/models/regions, required commercial-tier/no-training posture,
  and cross-provider approval. Prefer a distinct model inside an approved provider; require
  human opt-in to cross provider/residency boundaries.
- **Acceptance criteria:**
  1. Confidential/regulated payload cannot route without an explicit allowlist rule.
  2. Cross-provider/residency change stops for human approval.
  3. Policy decision is recorded in audit without sensitive payload.
  4. Public-repo payload follows the cheap automatic path.
- **Validation:** policy matrix negative tests + Privacy persona re-review.
- **Dependencies:** FR-005 resolver, FR-006 audit
- **Suggested owner:** Privacy/Data Governance + Security/Identity + AI Systems Engineer
- **Next skill:** `/design`

## FR-010 — Reconcile remaining public documentation

- **Kind / priority / status:** todo · **P3** · proposed
- **Evidence:** missing OVERVIEW bullet; wrong Claude router path; INSTALL promises/deployment
  and single-agent prose contradict current repo/CLI; decision-note blast radius overstates.
- **Affected scope:** pack docs and managed blocks.
- **Consequence:** users believe incomplete behavior is wired.
- **Recommended remediation:** update source docs only after FR-001/FR-005 architecture is
  approved; promote the model-orchestration decision note to an ADR because it changes every
  skill's execution.
- **Acceptance criteria:**
  1. Every path resolves.
  2. Copilot/Claude deployment map matches generated agent files.
  3. OVERVIEW, standard, ADR, decision note, and actual runtime use identical terms.
  4. `check-consistency.py` covers the new parity.
- **Validation:** link/path/parity tests + Documentation Steward PASS.
- **Dependencies:** FR-001, FR-005
- **Suggested owner:** Documentation Steward + Enterprise Architect
- **Next skill:** `/document`

---

## Human triage

No model-orchestration implementation is approved. Triage only FR-008 and the residual
deployment-map/doc mismatch in FR-010 if they are worth addressing independently.
