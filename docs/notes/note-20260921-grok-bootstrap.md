---
id: note-20260921-grok-bootstrap
title: Bind early ACP updates to the completed session creation
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, grok]
links:
  - { to: design-multi-harness-runner, rel: refines }
  - { to: proof-native-coordination-repair, rel: relates-to }
review-by: "2026-12-21"
summary: Grok 1.0.34 sends a session update before its session/new response. Retain only a bounded candidate identity and count during creation, require the response to confirm that identity, and dispatch no prompt before correlation succeeds.
---

# Grok session bootstrap correlation

Status: approved bounded contract delta. Tier T2. Owner Ruling 6 resolves
`req-01M30NFSZ8ARJA2WHSRNQCPVVN`; independent source review is
`al-01M30NRJSKX84RBVKZM7HDAV7C`. The bootstrap repair and a fresh two-turn Grok
diagnostic pass. The first diagnostic exposed an additional watcher response defect;
Ruling 8 approves the exact version-bound compatibility rule below.

## Evidence and scope

Verified in the private observation `/tmp/native-repair-qualification/requal-grok.json`:
initialize response, authenticate response, six extension notifications, then
`session/update` with `available_commands_update` and a nonempty session ID. The
previous client returns `protocol_error` at that update, before receiving the creation
response or dispatching any prompt. The raw file contains provider payloads and is not
copied into this note or durable transport events.

[ACP v1 session setup](https://agentclientprotocol.com/protocol/v1/session-setup)
requires the creation response to return the conversation identity. Its session/new
section does not establish a response-before-notification guarantee. This change
supports the measured Grok ordering; it does not assert every ACP provider uses it.
Grounding follows native repair proof → runner design → transport. AC5 session control
and AC6 bounded failure remain the governing requirements.

## Contract and data model

The existing attempt remains the aggregate: one process and one created session.
During the single pending `session/new` RPC, an otherwise valid `session/update` may
precede the result. Retain only one candidate session identifier (existing 256-character
identifier bound) and an integer count. Never retain notification bodies or dispatch
prompts, permissions, or tools on that candidate's authority. This is an ephemeral
correlation value, not a second session record or a durable schema.

The update must have object params, a valid nonempty session ID, and an object update
with a valid nonempty `sessionUpdate` discriminator. Every early update must name the
same candidate. The matching RPC response must return that same valid session ID.
Missing, malformed, changed or foreign identity fails `protocol_error`; no creation
event or prompt may precede confirmation. Early updates during initialize/authenticate
are refused. Once bound, the existing exact-session check still applies.
Permission requests require an already established nonempty session identity; absent,
null or provisional candidate identities fail protocol validation and are not credited
as permission callbacks. This also closes the pre-existing `None == None` identity hole.

After confirmation, fold the count into the existing `progress_updates` counter and
coalesced progress emission, after `session_created`. The counter remains additive per
attempt. No replay loop over saved messages, payload queue, protocol library, new store,
permission policy, retry or native hook change is needed. A normal response with zero
early updates still works. A failed creation response never becomes successful because
notifications arrived.

All bytes still pass the existing shared stdout/stderr cap; each receive still checks
the original attempt deadline and cancellation. A missing creation result ends by EOF,
deadline, cancellation or protocol error, never readiness. No per-update durable event
is added. Unknown usage/cost remains unknown. No HTTP or new UI surface is introduced.

## Failure, security and privacy controls

| Boundary/failure | Disposition and falsifying proof |
|---|---|
| Early update identity → established session | Single candidate must equal returned session ID; mismatch, two candidates and foreign post-bind tests |
| Update before session/new or malformed envelope | Refuse; initialize/auth, missing ID, empty ID, list update and missing discriminator tests |
| Candidate → prompt authority | No prompt before matching response; EOF/error/timeout tests inspect actual peer request log |
| Provider stream → resources | Existing cap/deadline/cancel unchanged; early-update flood and stalled creation tests |
| Provider payload → durable metadata | Count only after binding; SECRET sentinel absent from result/events; no payload queue |

STRIDE: correlation prevents accidental cross-session attribution; process trust and
native permissions remain the existing boundary. A malicious provider that forges both
notifications and its creation response remains outside this local correlation guarantee.
LINDDUN: raw updates may contain personal paths or model text; discard them, retaining only
existing session identity and operational counters. No new retention or external telemetry.

## Execution and review

Change surfaces: source transport + recorded envelope fixture + real subprocess peer/tests
→ parent-generated installed script → runner's existing metadata reader. Parent owns
shared design integration, source/install sync, full release gates, defect register and
the composed four-harness proof. This note owns only the bounded bootstrap delta.

Testing union from the runner design: D0–D4, D6–D7, A1, A3–A4, A6. First replay the recorded
ordering against the current code and observe failure. Add the malformed/foreign/resource
negatives; implement the minimum local state; kill mutations removing response correlation
and phase restriction. Run the complete transport suite. A fresh bounded live Grok run
must then demonstrate creation and two ordered prompts. Any run before integrated source
gates is labelled diagnostic and cannot qualify unattended coordination.

Planned graph: contract review → recorded-order red → local repair → negatives/mutations
→ independent source review → parent sync/gates → fresh live proof. Fan-out 0. The parent
may perform independent native-controls work concurrently; this track does not touch it.
Runtime qualification, full pack hook preservation and complete coordination are not
inferred from bootstrap success. The authored paths are claimed only while editing.

## Verification record

| Claim | Oracle / observed result |
|---|---|
| Original ordering fails | Four new tests first produced seven ordering/resource failures; the missing-ID update incorrectly completed two turns. |
| Unbound permission is invalid | Additional red test produced two failures: missing/null identity incorrectly became one credited denial. |
| Repaired local behavior | All 34 transport tests pass in 7.189 seconds, with ResourceWarning treated as error. Parent independently observed 34 tests and 60 subtests in 7.23 seconds. |
| Guard sensitivity | Three disposable-source mutants killed: remove creation-response equality, remove phase fence, allow missing precreation permission identity. |
| Fresh real bootstrap | Grok 1.0.34 diagnostic created session `01a0c15c-656c-7f42-98df-07e9dae9e81c`; two bootstrap updates correlate and the first prompt is dispatched. |
| Ordered prompt limitation | At 3.261042 seconds the attempt returns `protocol_error`, zero completed turns, 317418 stdout bytes, zero stderr, no cleanup error. An unsolicited response has string id `skills-reload` and result `{result: {reloaded: 1}}`. The existing response-ID guard rejects it. No second prompt is sent. |

The live attempt is **diagnostic before integrated source gates, not profile qualification**.
It used the assigned checkout, unchanged Grok argv (`grok agent --no-leader stdio`),
120-second total deadline and 4 MiB combined output cap. Prompts requested only nonce
memory and response, with no tools, edits, agents, settings or permission changes. The
observer records and returns each message unchanged; it does not synthesize wire traffic.
Source SHA-256: `302948e50cdb7e7d5fb8d35d2d23687877b5424d61269cac917ab22afea00625`.
Private raw observation SHA-256:
`0ebb03d73d6ad7729e7ecef9a9ceb21046b413f10a14af8a0f2be79a8b9c30b9`.
Raw and sanitized operational traces remain at `/tmp/grok-bootstrap-diagnostic-raw.json`
and `/tmp/grok-bootstrap-diagnostic-summary.json`. No raw model/provider payload is
committed. Cost/tokens were not recorded by the transport.

Class → sweep → prevent: absent identities comparing equal can grant pre-creation
authority; both session updates and permission paths are now guarded by valid/established
identity, with missing/null/foreign regression tests. Separately, requiring a notification
to follow a reply without measuring provider ordering can reject valid startup; the
recorded-order fixture controls this temporal assumption. Parent owns the shared defect
register and final integrated qualification. The new `skills-reload` observation does not
authorize weakening response correlation; it is a separately diagnosed next seam.

## Approved exact Grok 1.0.34 watcher compatibility

Verified local provenance: the installed native executable contains the adjacent strings
`failed to inject skills reload into ACP stream`, `Skill directory changed on disk,
reloading skills for all sessions`, and `skills-reload` at byte offset 117154554.
The measured response therefore matches a named native watcher mechanism. No matching
literal exists in the project pack/Grok configuration or searched user Grok script/config
files. The shipped `grok agent stdio --help` exposes debug and leader-socket options;
the shipped configuration reference has no documented skills-watcher disable switch.
The actual filesystem event that triggered this one reload is not recorded. Disabling
project skills/hooks or changing undocumented settings is not an acceptable prevention.

The measured initialize response identifies this native profile with
`result._meta.grokShell=true` and `result._meta.agentVersion="1.0.34"`; agentInfo is absent.
Approved narrow disposition: Ruling 8 resolves `req-01M30P12KWPRP2J9CGCY2PGFVA`:

- Select only that explicit initialize metadata pair. Report its version with a constant
  provenance field; do not infer the profile from executable name or a null version.
- Only while a numeric `session/prompt` RPC is pending and a session is established,
  consume exactly `{jsonrpc: "2.0", id: "skills-reload", result: {result: {reloaded: 1}}}`.
  Require the exact keys at all three object levels and integer 1 (not boolean).
- Increment `compatibility_responses`, an additive attempt counter. Do not return from
  the pending RPC, grant permission, advance a turn, emit per-item events or retain payloads.
- Every other ID, envelope, phase and version retains strict rejection. The shared byte,
  deadline and cancellation limits still apply to every compatibility response.

Tests must fail before this change on the recorded envelope, then prove wrong profile,
wrong phase, extra keys, malformed nesting/value, unrelated IDs, flood and cancellation
remain rejected/bounded. A mutation removing profile selection must be killed. One fresh
diagnosed retry then tests two ordered prompts. This is a documented compatibility
exception for a measured provider version, not a general permission to ignore responses.

## Diagnostic retry and final source proof

The one diagnosed retry uses the same two prompts and native argv, a fresh native session,
and the repaired source SHA-256
`d1cb1f8008d0c1463fe41118df68962f936a2c5fa5854861ce4b9d295f88b65e`.
It completes two turns in **10.467414 seconds**, with 227671 stdout bytes, zero stderr,
zero permission callbacks and no cleanup error. The second turn reports the remembered
nonce. Session identity is `01a0c163-f99d-7321-a04c-66ca64366eb9`; reported version is
1.0.34 from `grok._meta.agentVersion`. These values were read from the actual result,
not inferred from the installed binary version.

The retry has **zero compatibility responses**: the native watcher did not fire again.
Therefore ordered prompts are demonstrated live, while the watcher exception is proven
by the exact recorded envelope and fault tests, not by a second live watcher occurrence.
The private raw retry SHA-256 is
`7ae52b681f688466c9178fdab61931e7a29b18c3dcc25ec1a00b5706c4dd7a0b`;
the corresponding files are `/tmp/grok-bootstrap-diagnostic-retry-raw.json` and
`/tmp/grok-bootstrap-diagnostic-retry-summary.json`. Both live attempts remain explicitly
diagnostic before integrated source gates. Unattended profile readiness is not claimed.

The first watcher regression run failed with one failure and twelve missing-counter
errors. The expanded 37-test transport run passes in 10.030 seconds. A further
acknowledgement-only test requires timeout with zero credited turns. Six disposable-source
mutations are killed: response correlation, creation phase, permission identity, watcher
profile selector, exact watcher envelope and watcher falsely completing the pending RPC.
The full release gate exercises all 38 tests and their negative subcases. Final independent
source review passed at `al-01M30PDVTHJ6WNH3PPAHQHA5HQ`, with 38 tests and 71 subcases
observed in 10.49 seconds, including the exact integer-versus-boolean envelope distinction.

All **17 local release gates pass**. The full Python suite reports 1173 passed, 12 explicit
skips and 388 passed subcases in 132.81 seconds; all 34 Node tests pass with zero skips,
and the explainer render/accessibility proof passes. Source/install drift, graph and ruling
citations are clean. The retained gate log is `/tmp/e2e-grok-verify-bundle-qualified-env.log`.
The initial log `/tmp/e2e-grok-verify-bundle.log` is also retained: 16 gates passed but the
Python gate could not start because the system interpreter lacked pytest. The successful
run selected `/tmp/ai-forward-runner-verify-venv/bin/python` through PATH and installed the
existing locked Node dependencies; it changed no dependency manifest or runtime policy.
Both native diagnostic registrations were ended. No process cleanup failure was observed.

Remaining composition evidence belongs to the coordinator: the integrated cross-track
release gates and a fresh final profile matrix against the integrated reviewed commit.
Parent source review and these tests do not establish native ownership/Stop controls.
