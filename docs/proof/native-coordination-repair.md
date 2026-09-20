---
id: proof-native-coordination-repair
title: Native coordination repair and profile requalification
type: proof-pack
status: draft
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, qualification]
links:
  - { to: plan-native-coordination-repair, rel: implements }
  - { to: design-multi-harness-runner, rel: implements }
  - { to: proof-local-coordination-profiles, rel: relates-to }
review-by: "2026-12-20"
summary: Recorded-wire regressions repair ACP extension notifications and sticky Agy denials; live readiness is decided separately against unchanged local profiles.
review-suggested: []
---

# Native coordination repair and profile requalification

Goal: perform the recommended transport repairs and repeat actual profile qualification.
No trust or permission setting is changed. No unattended attestation is issued merely
because transport tests pass. The previous report remains historical evidence.

## Contract and implementation proof

Verified contract: [ACP v1 extensibility](https://agentclientprotocol.com/protocol/v1/extensibility)
reserves underscore methods for extensions and says unrecognized notifications should
be ignored. Requests still need a response. The transport now counts valid extension
notifications without retaining names or payloads; malformed envelopes, foreign sessions,
response IDs, permission handling, byte/deadline limits and cancellation stay enforced.

Agy native `denied_actions` is checked before SUCCESS. A native ERROR step terminates
dispatch immediately; the observed TOOL_ERROR permission signature maps to blocked,
other errors to `native_tool_error`. ERROR evidence requires an established matching
conversation. A denial cannot credit a turn, admit a later prompt or promote an existing
file receipt. Only sanitized counters and stable action identifiers reach runner status.

| Oracle | Observed evidence |
|---|---|
| Recorded wire, red first | Original transport fails the new extension/denial regressions: 8 failures and 3 errors. Fixture retains recorded envelope fields with sensitive payloads replaced. |
| Installed composition, red first | Corrected runner regression against original source reaches false `ready_for_review` despite native denial. Initial test argv omitted required Agy flags and failed too early; that fixture was corrected and rerun before accepting red. |
| Mutation check | Removing extension handling, native result denial, or native ERROR handling is killed by the corresponding test. |
| Independent review correction | Reviewer reproduced missing conversation ID before/after init. Both new regressions failed before the fix, then passed; both produce `protocol_error`, zero native denials and no subsequent prompt. |
| Privacy and boundaries | Tests cover malformed/mixed envelopes, extension requests, foreign sessions, notification flood, cancellation, malformed denials, and no raw SECRET payload in persistent runner status. |

Independent implementation review: **PASS**, original audit
`al-01M30GDDCBZV4TDNGCESTZEFA0` (original review identifier).
The reviewer cleared the sole binding finding after rerunning its two-case reproducer.
No new dependency, policy bypass, response transcript store or approval mechanism is added.
The existing design threat/privacy register remains applicable; the changes strengthen its
untrusted parsing, resource bounds, denial and false-completion controls.

## Release verification

All **17 release gates passed**, including 1,146 Python tests, 12 explicit skips and
339 subtests in 122.53 seconds; 34 Node tests; browser rendering/accessibility; source/install
drift and metadata gates. Later documentation-only closure reuses these code results and
repeats affected metadata gates. A draft graph edge used an unregistered relation; the
graph validator rejected it and it was corrected to the existing `implements` relation.

Live qualification is pending at this intermediate source checkpoint. The final evidence
record will name actual profile outcomes and remaining gates.
