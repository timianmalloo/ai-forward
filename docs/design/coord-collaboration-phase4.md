---
id: design-coord-collaboration-phase4
title: "Design - coord collaboration mode, Phase 4"
type: design
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, collaboration, worktrees, contracts, claims]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
  - { to: design-coord-core-phase1, rel: refines }
  - { to: design-coord-enforcement-phase2, rel: refines }
  - { to: design-coord-federation-phase3, rel: refines }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-02-28"
summary: >-
  Phase-4 collaboration mode for coord: a live session list, a collaboration health check, and a
  reusable session-contract template so multi-agent work records roles, seams, ownership, claims,
  and merge policy before concurrent implementation begins.
---

# Design: coord collaboration mode - Phase 4

- **Status:** Accepted
- **Spec / architecture:** `docs/specs/agent-coordination.md` (US-1, US-5, US-6, US-9, NFR-R2) and the existing Phase-1 to Phase-3 coordination designs.
- **Delivery phase / vertical slice:** Phase 4 operator/collaboration slice. Real: session listing, collaboration check, reusable contract template. Deferred: live TUI/HTML operator surface, seam-request workflow, owner-aware claim enforcement.
- **Author(s) / date:** Orchestrator + Patterns Expert + Simplifier + Python Developer + Test Architect, 2026-08-29.

> **Grounding trace (V15):** `design-coord-collaboration-phase4` -> `refines` -> `design-coord-core-phase1` (append-only record + fold) -> `refines` -> `design-coord-enforcement-phase2` (one-session-per-worktree, commit floor) -> `refines` -> `design-coord-federation-phase3` (shared allocator and register merge) -> `implements` -> `spec-agent-coordination`. AI-DE evidence: `docs/collaboration/session-contracts.md` and defect classes DC-013/DC-024.

## Responsibility

**One:** make cross-session collaboration visible and checkable before two agents start changing one repository at the same time.

It does not enforce all ownership rules yet. It reports collaboration preconditions from the existing coordination record and gives sessions a shared contract template. Enforcement remains the existing hook/pre-commit/merge-driver floor.

## Data model

**Bounded context:** Agent Coordination.

**Aggregate touched:** Session record. Root `SessionId`. **Invariant:** a live session is derived from append-only `session-start` and `session-end` facts; the current active set is a fold, never a stored list.

**New value objects:**
- `CollaborationSession` - one active session projection: `session`, `agent`, `worktree`, `started_at`, `last_at`, `claims[]`.
- `CollaborationFinding` - one health finding: `code`, `severity`, `reason`.

**Grain:** one row in `.agents/log/<session>.jsonl` remains exactly one event emitted by one session at one instant. This slice adds no new fact store.

**Derive, don't store:** active sessions and collaboration findings are computed from existing session/claim facts plus the presence of `docs/collaboration/session-contracts.md`.

## Change surfaces (E7)

store (`.agents/log/*.jsonl`, `docs/collaboration/session-contracts.md`) -> model (`CollaborationSession`, `CollaborationFinding`) -> service (`active_sessions`, `collaboration_findings`) -> projection/wire (`coord session list --json`, `coord collaborate check --json`) -> client (CLI) -> UI (terminal/operator output) -> compute reader (human/agent decides whether collaboration is safe to continue).

## Contracts

**Exposed CLI:**

```text
coord session list [--json]          # 0 active sessions listed; 4 unreadable record
coord collaborate check [--json]     # 0 ok; 3 collaboration findings
```

**Contract template:** `templates/session-contract.template.md`, deployed with the pack. It defines session roles, seam, file ownership, contracts, seam-change protocol, merge policy, open requests, and each session's response.

## Solution-Selection Ladder

| Rung | Decision |
|---|---|
| 1 YAGNI | Needed: AI-DE showed the contract, registration, claims, and merge policy were the difference between safe collaboration and ID/worktree failures. |
| 2 Reuse | Reuse existing `coord-core.py` record, `fold`, worktree model, merge drivers, and tests. No new store. |
| 3 stdlib | `json`, `pathlib`, existing git helpers only. |
| 4 native | Git worktree inventory stays the native source for worktrees. |
| 5 dependency | Not reached. |
| 6-7 minimum | Two projections and one template; defer owner-aware claim enforcement to a later slice. |

## Patterns

- **Projection over append-only facts** - active sessions and findings are folds over the record.
- **Health Check** - `coord collaborate check` summarizes unsafe collaboration preconditions.
- **Template Method (artifact, not code)** - `session-contract.template.md` gives every repo the same collaboration skeleton while keeping content repo-specific.
- **Rejected:** a daemon or dashboard. The CLI and template cover the current need without a runtime.

## Failure-mode analysis

| Mode | Disposition |
|---|---|
| Multiple sessions are active but no contract exists | **Detect.** `COORD-COLLAB-NO-CONTRACT`, exit 3. Test: two live sessions without contract fail. |
| A session is active but has no claims | **Detect.** `COORD-COLLAB-NO-CLAIMS`, warning. It is not a hard failure because a newly registered session may be reading before editing. |
| Record is unreadable | **Detect + fail safe.** `COORD-COLLAB-NOT-CHECKED-RECORD`, exit 3/4 depending surface; no OK result is emitted. |
| Empty record is treated as "no collaboration" | **Prevent.** Empty coordination corpus reports `COORD-COLLAB-NOT-CHECKED-EMPTY`; it is not an OK collaboration check. |
| Dormant worktrees are mistaken for live sessions | **Accept, bounded.** This slice reports registered live sessions only. Worktree cleanup still owns filesystem liveness (WT/DC-024). |

## Adversarial analysis (STRIDE-lite)

| Boundary | Threat | Disposition |
|---|---|---|
| Coordination record -> collaboration projection | Tampering: malformed event hides a session | Reuse `read_events` errors; finding emitted, no OK. |
| Environment identity -> session actions | Spoofing: false `AGENT_SESSION` | Existing ADR-0011 accepted identity model. This slice does not increase authority. |
| Template -> repo policy | Elevation: a template is mistaken for enforcement | Template states claims are advisory unless hook/pre-commit/merge drivers enforce. |
| Terminal output -> model reader | Prompt injection via event fields | Output is structured fields; no free-text intent in this slice. |

## Privacy analysis

No personal data is introduced. Session IDs, agent names, worktree paths, and repo-relative claim paths are local operational metadata already present in the coordination record.

## Telemetry

CLI surface only. Stable codes: `COORD-COLLAB-NO-CONTRACT`, `COORD-COLLAB-NO-CLAIMS`, `COORD-COLLAB-NOT-CHECKED-RECORD`, `COORD-COLLAB-NOT-CHECKED-EMPTY`. JSON output includes corpus size (`files_scanned`), active session count, contract presence, findings, and claims.

## Test plan

**Triggered:** D0 (all tests), D1 (pure folds), D4 (real git/worktree semantics already covered by existing worktree tests), D6 (JSONL and CLI error paths), D7 (no mocks at git boundary for existing worktree tests).

| Test | Proves |
|---|---|
| `test_session_list_reports_active_sessions_and_claims` | Active sessions are derived from the existing record and include live claims. |
| `test_collaboration_check_requires_contract_for_multiple_live_sessions` | Two sessions without a contract produce a finding. |
| `test_collaboration_check_passes_with_contract_for_multiple_live_sessions` | The missing-contract finding clears when the contract exists. |
| `test_cli_session_list_json_reports_active_sessions` | The public CLI emits the active session projection. |
| `test_cli_collaborate_check_fails_when_contract_is_missing` | The public CLI exits non-zero and emits the expected finding. |

## Gate record

`GATE design · 2026-08-29 · Patterns Expert, Simplifier, Test Architect, SRE, Security · verdict: PASS`

- **Patterns Expert:** PASS - projection and health check reuse the existing event-sourcing shape.
- **Simplifier:** PASS - no daemon, no new dependency, no new store; owner-aware enforcement deferred.
- **Test Architect:** PASS - red observed for missing APIs; nine tests now cover helper and CLI behavior, including empty-corpus failure, ended/stale sessions, and positive CLI semantics.
- **Security:** PASS - no new trust boundary with authority; advisory output only.
- **SRE:** PASS - operator questions are measurable from JSON output; no service telemetry required.

## Residual risk

The tool still cannot prove an unregistered but idle-looking worktree has no human using it; cleanup remains responsible for filesystem liveness. Owner-aware claim enforcement is not implemented in this slice; it needs a machine-readable ownership model or a parser for the contract table.
