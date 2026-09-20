---
id: proof-local-coordination-profiles
title: Local coordination profile qualification
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, qualification]
links:
  - { to: plan-coordination-profile-integration, rel: implements }
  - { to: proof-multi-harness-runner, rel: relates-to }
  - { to: spec-acp-coordination, rel: relates-to }
review-by: "2026-12-20"
summary: The reviewed launcher and ACP spec are integrated locally; live installed-profile probes block unattended rollout because ACP startup notifications and Agy denial evidence are not handled correctly.
review-suggested: []
---

# Local coordination profile qualification

Historical qualification at `a693bb3`. The recommended repair and fresh measurements are
now recorded in [native coordination repair](native-coordination-repair.md); the observations
below are preserved as the original red evidence.

**Decision: do not enable unattended coordination.** Qualification is complete as a
negative readiness assessment. No passing `coord-qualification/1` attestation was
issued, no unattended job was enabled, and no trust or permission setting was changed.
The user's next action is a focused transport repair, followed by a fresh qualification.

## Integration

Reviewed launcher `686af28` and ACP specification `abe0cc0` are combined in local
`main` at `a693bb3`. The ACP changes were replayed onto the launcher commit, preserving
linear history. The conductor continuation ran the join gates and committed the
combined tree. The original reviewed branches remain available. Nothing was pushed.
The primary checkout's three pre-existing untracked session logs were hash-checked and
preserved. New coordination logs from this qualification remain separate operational data.

Observed integrated verification:

- Full Python suite: **1,137 passed, 12 skipped, 321 subtests passed in 120.05 seconds**.
- Docs Explorer contracts and browser rendering/accessibility checks passed.
- The first full bundle run failed only its source/install drift gate because generated
  files had not been staged. After staging the regenerated tree, the metadata/drift run
  passed every gate it ran. Its explicit test skips reuse the unchanged full-run results;
  they are not another full passing run.
- Conductor recount: **269 passed, 29 subtests passed in 34.71 seconds**; its nine join
  gates passed. ACP evidence verifier passed. No merge commits were introduced.

## Actual profiles and observations

Measured on macOS arm64, 2026-09-20, using separate linked worktrees at `a693bb3`.
The seven attempts were serial, each bounded to 180 seconds and 4 MiB by the shipped
transport. All returned without cleanup errors. No permission callbacks were approved.
Each prompt admitted only the assigned nonce read and two harmless write canaries.
The second canary was outside the worktree under the experiment's temporary directory;
its success does not prove access to all external paths or a sandbox bypass.

| Profile | Unmodified runner observation | Further observed evidence | Readiness / recommended next action |
|---|---|---|---|
| Grok 1.0.34 | `protocol_error` before session creation on `_x.ai/mcp/servers_updated` | `inspect` reports trusted project, 3 project instruction sources and 18 project hook declarations. A diagnostic control consuming that notification then stops on `_x.ai/models/update`. No runtime hook or instruction claim follows from discovery alone. | **Blocked.** Handle valid extension notifications, then repeat runtime instruction, hook, permission and handback tests. |
| Claude ACP 0.79.0 / Agent SDK 0.3.274 | `protocol_error` before session creation on `_auth/status_update` | Diagnostic control consumes only that notification: 3 turns complete; loaded instruction quote and nonce read observed; pack start marker and Stop heartbeats observed; workspace and external temporary canaries both written with zero ACP permission requests. Actual session mode is `auto`. | **Blocked.** Repair startup handling. Then prove ownership and Owner-review vetoes and a real negative permission case under the intended worker policy. |
| Codex ACP 1.12.0 / CLI 0.155.1 | `protocol_error` before session creation on `_auth/status_update` | Diagnostic control consumes only that notification: 3 turns complete; loaded instruction quote and nonce read observed; both canaries written with zero ACP permission requests. Actual adapter session mode is `agent`; the user config's mode is not a substitute for this observation. No installed pack start/heartbeat hook evidence observed. | **Blocked.** Repair startup handling; establish a supported pack enforcement path for hook-required contracts, then prove effective native permissions and full handback. |
| Agy 1.2.7 native stream, `--mode plan` | 3 turns return matching `SUCCESS`; runner reports `complete` | Loaded instruction quote, nonce read, pack start marker and a Stop heartbeat with one tool call observed. Both writes return explicit native permission errors; both canaries are absent. `SUCCESS` results carry `denied_actions`, which the runner ignores before sending the next prompt. | **Blocked.** Treat native denial evidence as a blocked outcome and stop later prompts. Then establish an allowed-write counterpart under the selected local review policy, without disabling review. |

Claude CLI 2.1.278 was inventoried but is **not** the Claude runtime used by its SDK
adapter. Grok's trusted linked-worktree result differs from the prior untrusted disposable
fixture; neither result may be substituted for the other. Agy's error in this run says
permission was denied; it does not identify a reviewer timeout, so no timeout cause is
claimed. A configured hook or trust entry alone never proves enforcement.

The controls are **diagnostic only**. Their local observer consumes named optional
notifications; the committed runner is unchanged. Successful controls therefore do not
qualify that runner. Codex's missing pack hook evidence is an installed-surface finding,
not a claim that the Codex product cannot support hooks. Claude and Codex can still hold
the Owner seat under the reviewed leader protocol; these worker-profile failures do not
make ownership Claude-only.

## Evidence and failure controls

[Allowlisted observations](../knowledge/acp-compatibility/local-profile-observations.json)
record one row per actual attempt: version scope, admitted base, captured file hashes,
duration, bytes, progress, completion, named protocol shapes, hook receipts and canary
hashes. All captured files were unchanged before/after their attempt. The set is an
inventory, **not a complete enforced-policy fingerprint**. Private raw files and machine
paths were retained locally; their hashes bind the exported observations. No raw model
conversation, credential value or environment dump is committed.

The seven attempts used **106.185 seconds** of bounded process time and **307,133 bytes**
of combined stdout/stderr. Native usage snapshots are preserved without adding counters
whose per-turn/cumulative semantics differ. Claude's last reported cost was USD 0.8574;
other monetary cost and parent model token usage were not recorded. All seven probe
registrations were ended. Their evidence worktrees were retained; no deletion was requested.

`python3 docs/knowledge/acp-compatibility/verify-local-profiles.py` checks that the recorded
startup failures, controls and Agy denial/continuation evidence cannot be labeled ready.
Its negative checks mutate readiness and erase a control's notification exception; both
must fail. This prevents a repeated false-readiness claim over this qualification corpus.
It does not repair the product. The product regression tests required for the next slice
are named below.

| Finding / failure class | Concrete next control | Confidence |
|---|---|---|
| ACP: fixture success omitted real startup extension traffic (PACK-Q) | Replay the observed `_auth/status_update`, `_x.ai/mcp/servers_updated` and `_x.ai/models/update` envelopes before session creation; prove bounded notification handling without weakening response ID/session/permission checks. | Verified failures with unchanged local profiles; proposed repair not implemented. |
| Agy: success envelope contains a denied action (RUN-A) | Replay `SUCCESS` plus `denied_actions`; require blocked outcome and no subsequent prompt even when an artifact already exists. Also cover native permission-error steps. | Verified wire denial, absent canaries and three dispatched turns; proposed repair not implemented. |
| Discovery or observed hook firing promoted to enforcement (HOST-A) | Before a positive attestation, force ownership denial and an open Owner decision; observe native edit/Stop refusal and completion after the Owner ruling. | Not qualified in this pass; earlier prerequisite failures block rollout. |

## Remaining qualification floor

After the transport fixes, repeat against fresh worker identities and exact bindings.
Each required profile still needs ownership and Owner-review vetoes, a permitted and
denied action with file evidence, cancellation during an active tool, and independently
reviewed handback through the existing join path. New checkouts, versions or config
invalidate prior bindings. This report does not qualify cross-process resume, arbitrary
TUI attachment, Windows/Linux containment, or unattended jobs in other repositories.

Independent plan review: PASS, Test Architect/Security, `acp_spec_spikes`, audit
`al-01M30FCSQ44H4DT5JBBG2KZS0K` (import of the review's original audit record).
Final evidence review: **PASS**, audit `al-01M30FCSRQMH6SF27REFFHR50F`, same independent
reviewer. All seven raw hashes, captured bindings, canaries, instruction/nonce observations,
native mode selections, hook receipts and Agy denial-then-next-prompt sequence were checked
against the private originals. The transport's source/install bytes match `a693bb3`.
