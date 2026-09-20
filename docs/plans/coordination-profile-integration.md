---
id: plan-coordination-profile-integration
title: Integrate coordination and qualify local profiles
type: doc
status: accepted
summary: Integrate the reviewed coordination branches, then qualify exact installed harness profiles before unattended use.
owner: "@timianmalloo"
tags: [coordination, qualification, acp]
links:
  - { to: spec-acp-coordination, rel: relates-to }
  - { to: proof-multi-harness-runner, rel: relates-to }
  - { to: kb-graph-and-loop-engineering, rel: depends-on }
review-by: "2026-12-20"
review-suggested: []
---

# Integrate coordination and qualify local profiles

Goal: integrate reviewed commits `686af28` and `abe0cc0` locally, then measure the
actual installed profiles before admitting unattended coordination. Done when the
integrated gates pass and each harness has an evidence-backed readiness decision
and next action. Tier T2; fan-out cap one (review or live probe, never both).
No remote push, global policy/trust changes, unattended work beyond qualification,
or fixes to newly discovered product gaps are part of this task.

## Execution graph

| Node | Capability | Inputs | Exit condition / oracle | Tier | Dependency |
|---|---|---|---|---|---|
| A: combine reviewed branches | Deterministic mechanics | Both commits, clean own checkout | Changes preserved; no conflict markers or merge commit | T1 | None |
| B: integrated release gates | Deterministic mechanics | A and regenerated artifacts | Bundle gates, ACP evidence verifier and join gates pass | T2 | A: data |
| C: local main integration | Deterministic mechanics | B, unchanged main base | Fast-forward main; preserve unrelated untracked files | T1 | B: decision |
| D: actual profile inventory | Deterministic mechanics | Installed binaries/configuration | Versions, hashes, resolved policy/trust and omissions recorded without secrets | T2 | C: data |
| E: serial live qualification | Reasoning | D, isolated linked worktrees | Instructions, tools, hooks, permissions and completion observed or explicitly blocked | T2 | D: decision |
| F: review and readiness record | Independent review | E evidence, explicit claim boundaries | No unsupported capability promoted; qualification only for exact measured profile | T2 | E: data |
| G: record and report | Deterministic mechanics | F | Discoverable proof, committed audit, local main updated and status table | T1 | F: decision |

```mermaid
flowchart LR
 A --> B --> C --> D --> E --> F --> G
```

The review floor also checks the plan before E. The prior implementation/specification
reviews remain valid for unchanged source. No new feature or production boundary is
being implemented. Surface list: reviewed source/install/docs → integrated checkout →
actual local executable/configuration → native session/tools/hooks → observed receipts →
readiness report. File/receipt hashes bind observations; they do not prove policy.

## Bounds and decisions

Each live target is serial, at most 180 seconds and 4 MiB of output, using the shipped
bounded transport. Each uses a new assigned session and checkout. One diagnosed control
probe is allowed per target; no automatic retry. Permission requests are denied; no
approval/trust setting is weakened. Allowed and denied canaries use explicitly owned
paths; permission probes never access credentials. Already configured hooks may write
their normal audit/coordination state. Observe those effects rather than injecting
replacement hooks. Missing native hooks (including the installed Codex surface) remain
unsupported for a hook-required contract. A blocking local prerequisite is a completed
negative qualification result, not a successful readiness result.

Variant: unmeasured cells in the finite four-harness matrix decrease. Deadline failure
triggers diagnosis and the bounded control, or a recorded blocker; it never becomes
qualification. Fallback is retained manual/serial operation. No passing qualification
file is issued for unknown required capabilities. No daemon or unattended job is enabled
before its required row passes. A future worktree/version/configuration change invalidates
the corresponding observation and requires a fresh binding.

Integration follows the repository's explicit linear-history constraint: replay the ACP
commit without committing, regenerate derived artifacts, verify the combined tree, then
use `conductor-join.py --continue --no-push` for gated completion. The continuation skips
only its `merge --no-ff` step. No tests/gates are removed. Fast-forward main after checks.
The primary checkout's unrelated untracked ledgers are preserved byte-for-byte.

## Cost and rigor

Naive and selected graph both have seven logical nodes; selected width one eliminates
shared-profile interference. Independent read-only inventories can be batched. All gate,
audit and independent review floors retained. Work and span are equal at width one;
wall time cannot be predicted from existing fixture measurements (actual native hooks
are the measurement gap). Inferred budget: 45 minutes, 120 parent tool calls, eight live
attempts maximum; tokens/spend not recorded unless provided by the native result. A cap
firing requires a documented re-estimate, never a skipped gate. Re-plan checkpoints:
integration conflict, failed release gate, native trust refusal, missing hook mechanism.

## Planned versus actual

Completed seven logical nodes. Integration landed linearly in local main at `a693bb3`;
no push. Seven serial live attempts measured four baseline profiles and three diagnosed
controls. All four readiness rows are blocked; no positive attestation or unattended job
was enabled. Actual native attempt durations and byte counts are in
`docs/knowledge/acp-compatibility/local-profile-observations.json`; total turn duration
is measured in the closing audit. Parent model tokens/spend and exact tool-call count
were not recorded, so the 120-call estimate is not scored as a measured success.

One integration rework pass corrected missing plan metadata and staged regenerated
artifacts for the drift gate. The unchanged full test results were retained; only the
affected metadata gates were repeated. These are existing metadata/drift failure shapes,
detected by their existing gates. The qualification controls were planned diagnosis,
not retries that qualified the unmodified runner. Independent Test Architect/Security
plan review passed before live probes. Findings and final evidence review are recorded
in `docs/proof/local-coordination-profiles.md`. No live target overlapped another target
or an independent reviewer. Full workflow/hook enforcement remains a release prerequisite,
not a passed floor: the task's exit was a measured readiness decision, not forced readiness.
