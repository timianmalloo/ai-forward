---
id: proof-coord-collaboration-phase4
title: "Proof Pack - coord collaboration mode, Phase 4"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, collaboration, proof]
links:
  - { to: design-coord-collaboration-phase4, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
review-by: "2027-02-28"
summary: >-
  Proof pack for coord collaboration mode: active-session projection, collaboration health checks,
  owner-aware claim warnings, seam-request workflow, collaboration summary, and the session-contract
  template. Records the red-first evidence, test oracles, commands, and residual risks for the
  shippable cross-session collaboration slice.
---

# Proof Pack: coord collaboration mode - Phase 4

- **Change:** cross-session collaboration first slice
- **Spec / design:** `docs/specs/agent-coordination.md` · `docs/design/coord-collaboration-phase4.md`
- **Tier:** T1/T2 coordination infrastructure
- **Author / date:** Copilot CLI, 2026-08-29

## Claims & evidence

### Claim 1: `coord session list` exposes active sessions and live claims
- **Evidence:** `python -m unittest tests.docs_explorer.test_coord_core.CollaborationTests -v` -> 14 tests OK.
- **Oracle:** `test_session_list_reports_active_sessions_and_claims` fails if `active_sessions()` drops worktree, agent, or claim paths; `test_cli_session_list_json_reports_active_sessions` fails if the public JSON omits claim `wi` or path.
- **Red observed before green:** yes. Initial run failed with `AttributeError: module 'coord_core' has no attribute 'active_sessions'`.
- **Confidence:** Verified.
- **Residual risk:** The projection only reports sessions that registered. Absence of a session is not proof nobody is using a worktree; cleanup still owns filesystem liveness.

### Claim 2: ended and stale sessions are excluded from active-session projections
- **Evidence:** `test_session_end_removes_the_active_session` and `test_stale_session_is_not_active` pass.
- **Oracle:** The tests fail if the `session-end` branch is removed or if the stale-session filter is removed.
- **Red observed before green:** fault-injection equivalent added after the first Test Architect review; these tests cover branches the earlier green suite did not.
- **Confidence:** Verified.
- **Residual risk:** The staleness duration is still a bounded policy. A dead session can hold the worktree until the window elapses.

### Claim 3: `coord collaborate check` requires a session contract for multi-session work
- **Evidence:** `test_collaboration_check_requires_contract_for_multiple_live_sessions` and `test_cli_collaborate_check_fails_when_contract_is_missing` pass.
- **Oracle:** The tests create two live sessions and no `docs/collaboration/session-contracts.md`; they fail unless the helper and CLI emit `COORD-COLLAB-NO-CONTRACT` and the CLI exits non-zero.
- **Red observed before green:** yes. Initial run failed with `AttributeError: module 'coord_core' has no attribute 'collaboration_findings'`.
- **Confidence:** Verified.
- **Residual risk:** Contract quality is human-reviewed; this check only proves the contract exists, not that it is good.

### Claim 4: `coord collaborate check` passes when the contract and active claims exist
- **Evidence:** `test_cli_collaborate_check_passes_when_contract_and_claims_exist` passes.
- **Oracle:** The test fails unless public CLI JSON reports `contract_exists: true`, no findings, and exit code 0 for two registered, claimed sessions.
- **Red observed before green:** yes by Test Architect disconfirmation. The first implementation returned non-zero for warning-level findings; the test forced exit semantics to distinguish blockers from warnings.
- **Confidence:** Verified.
- **Residual risk:** Owner-aware claims are deferred; a claim can still target a path another role "owns" until the next slice introduces a machine-readable ownership model.

### Claim 5: the reusable session-contract template is shipped with the pack
- **Evidence:** `pack/templates/session-contract.template.md` exists and `sync-pack.ps1` copies it to `docs/ai-forward-pack/templates/session-contract.template.md`.
- **Oracle:** Bundle count gate detects the template count; source/install drift gate detects a missing copied template after commit.
- **Red observed before green:** counts gate failed after the template was added but stale count literals remained; fixed by updating INSTALL/OVERVIEW counts.
- **Confidence:** Verified after commit/clean verify; currently Verified for source presence and sync output, pending final clean bundle gate after commit.
- **Residual risk:** The template is a starting contract, not enforcement. `coord collaborate check` enforces presence only.

### Claim 6: an empty coordination corpus is not reported as a successful collaboration check
- **Evidence:** `test_cli_collaborate_check_fails_when_coordination_corpus_is_empty` passes.
- **Oracle:** The test fails unless `coord collaborate check --json` emits `COORD-COLLAB-NOT-CHECKED-EMPTY`, marks it `blocker`, reports `files_scanned: 0`, exits non-zero, and does not create a fake corpus.
- **Red observed before green:** yes by Test Architect adversarial review. The first implementation emitted the not-checked finding as a warning and exited 0.
- **Confidence:** Verified.
- **Residual risk:** The check still cannot prove that an unregistered but externally active worktree is idle; worktree cleanup owns that liveness evidence.

### Claim 7: contract ownership tables produce cross-owned-claim warnings
- **Evidence:** `test_collaboration_check_warns_on_claim_outside_contract_owner` passes.
- **Oracle:** The test fails unless a Design-labelled session claiming a Core-owned path from `docs/collaboration/session-contracts.md` produces `COORD-COLLAB-CROSS-OWNED-CLAIM`.
- **Red observed before green:** yes. The red run produced no owner-aware finding.
- **Confidence:** Verified.
- **Residual risk:** Role inference is advisory and label-based. `test_owner_role_inference_requires_token_boundary` prevents substring false grants, but a later slice should add explicit role metadata.

### Claim 8: seam requests are append-only and fold to current state
- **Evidence:** `test_request_workflow_add_list_resolve_is_append_only` passes.
- **Oracle:** The test fails unless `coord request add` emits an id, `request list --json` shows it open, `request resolve` appends a resolution, open-list becomes empty, and all-list shows the same request as resolved.
- **Red observed before green:** yes. The red run failed because `request` was not a valid command.
- **Confidence:** Verified.
- **Residual risk:** Request IDs are opaque; no UI yet groups them by contract or target role beyond the JSON/text listing.

### Claim 9: collaboration summary is a view over sessions, findings, and open requests
- **Evidence:** `test_collaboration_summary_includes_sessions_findings_and_requests` passes.
- **Oracle:** The test fails unless `coord collaborate summary --json` returns active sessions, findings, and open seam requests while excluding resolved requests and exiting 0 as a view.
- **Red observed before green:** yes. The red run failed because `summary` was not a valid action; an intermediate run also forced the exit semantics to differ from `check`.
- **Confidence:** Verified.
- **Residual risk:** Summary does not yet include git branch divergence or derived/register merge obligations.

### Claim 10: P12 is promoted as a general fleet learning
- **Evidence:** `dream.py apply-decisions` for `p12` reported `applied: 1 general, 0 repo-local; skipped 0; rejected 0`; audit verification passed. Store rows exist in `learnings/fleet-classes.jsonl` and `learnings/promoted.jsonl` for `dream=drm-0007`, `proposal=p12`.
- **Oracle:** The promotion is idempotent: `learnings/promoted.jsonl` is the skip ledger, and `apply-decisions` rejects tainted/no-control items. The row would be absent if the decision was not applied.
- **Red observed before green:** n/a - this is a promotion operation over an approved human decision.
- **Confidence:** Verified.
- **Residual risk:** Fleet learning text remains the p12 proposal's first-slice control; downstream repos still need `/apply-learnings` or `/updatepack` to receive it.

## Test coverage of the boundary set

| Boundary | Test |
|---|---|
| Empty/missing collaboration state | `test_cli_collaborate_check_fails_when_coordination_corpus_is_empty` |
| Multiple live sessions, no contract | `test_collaboration_check_requires_contract_for_multiple_live_sessions`; `test_cli_collaborate_check_fails_when_contract_is_missing` |
| Multiple live sessions, contract present | `test_collaboration_check_passes_with_contract_for_multiple_live_sessions` |
| Multiple live sessions, contract + claims present | `test_cli_collaborate_check_passes_when_contract_and_claims_exist` |
| Ended session | `test_session_end_removes_the_active_session` |
| Stale session | `test_stale_session_is_not_active` |
| CLI JSON surface | `test_cli_session_list_json_reports_active_sessions`; `test_cli_collaborate_check_fails_when_contract_is_missing`; `test_cli_collaborate_check_passes_when_contract_and_claims_exist` |
| Cross-owned claims | `test_collaboration_check_warns_on_claim_outside_contract_owner` |
| Role substring false grant | `test_owner_role_inference_requires_token_boundary` |
| Seam requests | `test_request_workflow_add_list_resolve_is_append_only` |
| Summary view | `test_collaboration_summary_includes_sessions_findings_and_requests` |
| P12 promotion | `dream.py apply-decisions` output + fleet/promoted JSONL rows |

## Failure modes addressed

| Failure mode | Handled in code by | Proven by |
|---|---|---|
| Multi-session work has no readable contract | `collaboration_findings()` emits `COORD-COLLAB-NO-CONTRACT` | `test_collaboration_check_requires_contract_for_multiple_live_sessions` |
| Warning-level no-claims finding blocks collaboration | `cmd_collaborate()` returns non-zero only for blocker severity | `test_cli_collaborate_check_passes_when_contract_and_claims_exist` |
| Session-end ignored | `active_sessions()` removes ended sessions | `test_session_end_removes_the_active_session` |
| Stale session treated as active forever | stale filter on `last_at` | `test_stale_session_is_not_active` |
| Cross-owned claim hidden | `contract_ownership()` + `owner_rows_for_path()` emit advisory finding | `test_collaboration_check_warns_on_claim_outside_contract_owner` |
| Role inferred from substring | role inference uses normalized word tokens, not substring containment | `test_owner_role_inference_requires_token_boundary` |
| Seam request rewritten in place | `request-add` / `request-resolve` append-only events | `test_request_workflow_add_list_resolve_is_append_only` |
| Summary behaves like a gate | `cmd_collaborate(summary)` returns 0 while reporting findings | `test_collaboration_summary_includes_sessions_findings_and_requests` |

## Threats addressed (STRIDE-lite)

| Boundary / threat | Disposition | Enforcing code | Negative security test | Result |
|---|---|---|---|---|
| Coordination record -> projection / malformed record hides sessions | mitigate | `active_sessions()` returns errors; `cmd_session_list()` exits 4 | existing malformed-record tests in coord suite | pass |
| Template -> repo policy / template mistaken as lock | mitigate | template states claims are advisory unless enforced | n/a documentation contract | accepted residual |

## Privacy findings addressed

No new personal-data flow. Session ids, agent names, worktree keys, and repo-relative paths remain local operational metadata.

## Testing Strategy directives applied

- **D0:** deterministic isolated tests; no network.
- **D1:** pure fold behavior in `active_sessions()` and `collaboration_findings()`.
- **D4:** existing coord worktree tests keep real git semantics covered.
- **D6:** JSONL and public CLI JSON behavior checked.

## Verification commands

```powershell
python -m unittest tests.docs_explorer.test_coord_core.CollaborationTests -v
python -m unittest tests.docs_explorer.test_coord_core -v
python docs\ai-forward-pack\scripts\docs-graph.py validate
python docs\ai-forward-pack\scripts\audit-log.py verify
pwsh tools\sync-pack.ps1
pwsh tools\verify-bundle.ps1
```

## Flagged risks / residual unknowns

- `coord collaborate check` requires a contract but does not parse whether the contract's ownership table is complete.
- A live but unregistered worktree remains a cleanup/liveness problem, not solved by this slice.
- The full bundle verifier's drift gate (`git diff --exit-code`) can only pass after source and generated surfaces are committed together.

## Status & next action

| | |
|---|---|
| **Completed** | Active-session projection, collaboration health check, owner-aware warnings, seam-request workflow, collaboration summary, P12 promotion, session-contract template, and tests. |
| **Remaining** | Hard owner enforcement, branch-divergence/merge-obligation summary, and the `/collaborate` skill wrapper. |
| **Best next action** | Decide whether to implement `/collaborate` from `docs/specs/collaborate-skill.md`, then add owner-role metadata so warnings can become enforceable checks. |

## Gate record

`GATE implement · 2026-08-29 · Python Developer, Test Architect · criteria met: focused coord suite green, docs/audit valid, proof pack attached · verdict: PASS-WITH-CONDITIONS · vetoes: Test Architect blocks resolved by adding CLI positive path, claims in JSON, session-end and stale-session tests, empty-corpus CLI failure, owner-aware warning, token-boundary role inference, seam-request append-only proof, summary view, P12 proof, and this Proof Pack.`
