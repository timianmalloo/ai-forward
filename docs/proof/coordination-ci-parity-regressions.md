---
id: proof-coordination-ci-parity-regressions
title: "Proof Pack - coordination CI parity regressions"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: "coordination CI parity regression repair"
tags: [coordination, ci, regression, proof]
links:
  - { to: api-coord_runtime, rel: documents }
review-by: "2026-12-22"
summary: >-
  Proof for the CI-only regressions caused by the approved P1-P6 coordination implementation.
  It covers bounded-process termination seams, explicit ACP model-setting authority, and
  Windows runtime-control lock contention.
---

# Proof Pack: coordination CI parity regressions

- **Change:** `fix/coordination-ci-parity`
- **Spec / design:** user-approved P1-P6 implementation; CI run 35670195939 failure log
- **Tier:** T1
- **Author / date:** Copilot CLI, 2026-09-22

## Root-cause / class / sweep / prevent

| Item | Summary |
|---|---|
| **Root cause** | Three tests/contracts did not match the platform reality after P1-P6: the bounded-process test patched the old termination seam, POSIX transport assertions still treated startup metadata as proof despite the newer `session/set_model` authority, and Windows `msvcrt.locking` retryable contention was collapsed into `invalid_runtime_control`. |
| **Class** | Existing platform/CI parity classes: CI-ENV (control proven on one environment only) and PLAT-style cross-platform semantics. The runtime-control case is also a retryable-busy-vs-corrupt classification defect. |
| **Sweep** | Searched owned coordination regression surfaces for `session/set_model`, `selected_model_set`, `model_set_error`, `invalid_runtime_control`, `busy`, and `Controls(`. The only caused production-code change required was `coord_runtime.py`; bounded-process and transport were stale test-oracle repairs. |
| **Prevent** | Added/updated regression oracles: injected terminate callback is asserted, missing/mismatched startup metadata proceeds only after successful `session/set_model`, failed setter sends no prompt and leaves `selected_model_set=false`, concurrent writers still publish eight unique ordered records, and held-lock busy returns explicitly without publishing a record. |

## Claims & evidence

### Claim 1: Bounded-process second wait timeout uses the injected termination seam
- **Evidence:** `test_second_wait_timeout_returns_bounded_failure` passes and asserts the injected `terminate` callback was called once.
- **Oracle:** The test fails if `wait_after_termination` falls back to real process-group killing for the mock process, which was the CI failure on Linux/macOS.
- **Red observed before green:** yes, CI 35670195939 failed with `TypeError: 'Mock' object cannot be interpreted as an integer`.
- **Confidence:** Verified on Windows targeted suite; POSIX red evidence is from CI log and will be re-proven by CI.
- **Residual risk:** Local run did not execute on Linux/macOS.

### Claim 2: ACP expected-model authority is `session/set_model`, not startup metadata
- **Evidence:** `test_expected_model_match_mismatch_and_missing_gate_fresh_session` now asserts `model_missing` and `model_mismatch` complete two prompts only after `session/set_model`, while `model_set_error` returns `remote_error`, starts zero prompts, and leaves `selected_model_set=false`.
- **Oracle:** The request trace must show `initialize`, `session/new`, `session/set_model` before any `session/prompt`; the failed-setter branch must contain no prompt request.
- **Red observed before green:** yes, CI 35670195939 showed stale assertions expecting `remote_error` for missing/mismatched metadata and `selected_model_set=true` for setter failure.
- **Confidence:** Verified by Windows targeted suite; POSIX class is structurally the same fixture and will be re-proven by CI.
- **Residual risk:** No live model/harness launch was run by request.

### Claim 3: Runtime-control contention is explicit bounded busy, not corrupt control data
- **Evidence:** `test_concurrent_writers_have_unique_ordered_records` preserves eight unique ordered prompt records; `test_another_process_holding_lock_cannot_suspend_deadline_forever` raises `runtime_control_busy` within the bounded caller budget; `test_enqueue_while_another_process_holds_lock_fails_busy_without_writing` proves no partial JSON is published while busy.
- **Oracle:** The concurrent test fails on lost/duplicate/out-of-order records. The held-lock tests fail if busy is success-shaped empty, collapses to `invalid_runtime_control`, waits beyond the operation budget, or publishes a partial record.
- **Red observed before green:** yes, CI 35670195939 failed on Windows Python 3.14 with `PermissionError` becoming `invalid_runtime_control`; the new held-lock write oracle is a fault-injection regression.
- **Confidence:** Verified on Windows locally.
- **Residual risk:** Windows CI has slower runner timing than local Windows; the operation remains finite and CI is the final environment proof.

### Claim 4: Runtime-control retries cannot approve an expired request or hide non-contention lock errors
- **Evidence:** `test_decide_and_answer_use_time_after_retry_and_record_read` advances mocked wall time across the real lock/record-read boundary and proves no decision is published and no answer is granted after expiry. `test_windows_lock_noncontention_error_is_not_retried_as_busy` proves Windows `EBADF` propagates immediately instead of being retried as contention.
- **Oracle:** The expiry test fails if `decide()` or `answer()` captures default wall time before retry/record-read. The Windows error test fails if all `OSError` values are treated as retryable busy.
- **Red observed before green:** review finding identified the stale-time path; the tests were added with the fix as deterministic fault-injection controls.
- **Confidence:** Expiry behavior verified on Windows locally; non-contention Windows errno test is Windows-only and skipped off Windows.
- **Residual risk:** POSIX has no `msvcrt` path; Linux/macOS remain covered by CI for the rest of the runtime suite.

## Test coverage of the boundary set

| Boundary | Covered by |
|---|---|
| Retryable Windows lock contention | `test_concurrent_writers_have_unique_ordered_records`, `test_another_process_holding_lock_cannot_suspend_deadline_forever`, `test_enqueue_while_another_process_holds_lock_fails_busy_without_writing` |
| Failed ACP model setter | `test_expected_model_match_mismatch_and_missing_gate_fresh_session` |
| Missing/mismatched ACP startup metadata | `test_expected_model_match_mismatch_and_missing_gate_fresh_session` |
| Final process wait timeout | `test_second_wait_timeout_returns_bounded_failure` |
| Expiry while contending for runtime-control lock | `test_decide_and_answer_use_time_after_retry_and_record_read` |
| Non-contention Windows lock error | `test_windows_lock_noncontention_error_is_not_retried_as_busy` |

## Testing Strategy directives applied

| Trigger | Directive | Evidence |
|---|---|---|
| T1 deterministic logic | D0/D1 | Focused unit/regression assertions for each changed contract. |
| T4 filesystem persistence/locking | D4 | Real temp directories and real lock files; no filesystem mocks. |
| T8 boundary substitute | D7 | Bounded-process mock now targets the explicit injected seam rather than patching production process-kill behavior. |
| T12 tool/workflow trace | A4 | ACP test asserts request ordering and no prompt after failed setter. |

## Verification commands

```powershell
$env:AGENT_SESSION='coord-ci-parity-20260922'
Set-Location -LiteralPath 'C:\Projects\ai-forward-fix-coordination-ci-parity'
python -m pytest tests\docs_explorer\test_coord_runtime.py tests\docs_explorer\test_bounded_process.py tests\docs_explorer\test_coord_transport.py -q
python tools\build-api-docs.py
pwsh tools\sync-pack.ps1
python tools\build-doc-site.py
git add pack\scripts\coord_runtime.py pack\adapters\INSTALL.md tests\docs_explorer\test_coord_runtime.py tests\docs_explorer\test_coord_transport.py tests\docs_explorer\test_bounded_process.py docs\ai-forward-pack\scripts\coord_runtime.py docs\ai-forward-pack\INSTALL.md web\pack-index.js
pwsh tools\verify-bundle.ps1
```

## Results

- Targeted regression suite: `36 passed, 70 skipped, 9 subtests passed in 35.10s`; follow-up runtime suite: `9 passed, 3 skipped, 4 subtests passed in 1.07s`.
- Full bundle verification: `BUNDLE CONSISTENT - all 17 gates passed`.

## Status & next action

| | |
|---|---|
| **Completed** | Fixed the three caused CI regressions and synced generated install/runtime surfaces. |
| **Remaining** | Linux/macOS CI must re-run to verify the POSIX-only jobs in their native runners. |
| **Best next action** | Parent reviews this commit and pushes/re-runs CI. |

## Gate record

`GATE implement · 2026-09-22 · python-developer/test-architect self-check; full verify-bundle gate · criteria met: targeted regressions pass, generated source/install drift gate passes, full suite passes locally · verdict: PASS-WITH-CONDITIONS · vetoes→resolution: POSIX runner proof remains pending CI rerun.`
