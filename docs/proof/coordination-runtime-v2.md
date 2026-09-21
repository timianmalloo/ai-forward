---
id: proof-coordination-runtime-v2
title: "Bounded coordination runtime: proof and operating limits"
type: proof-pack
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, proof, runtime]
links:
  - { to: spec-coordination-runtime-v2, rel: implements }
  - { to: design-coordination-runtime-v2, rel: implements }
  - { to: proof-coordination-fresh-clone, rel: depends-on }
  - { to: kb-coordination-runtime-capabilities, rel: relates-to }
review-by: "2026-12-21"
review-suggested: []
summary: "Reproducible offline proof, native observations and explicit unsupported runtime capabilities."
---

# Coordination runtime proof

The runner now admits explicit bounded unattended execution, compiled follow-up prompts,
pre-dispatch retries and request-specific interactive permission decisions. Both Claude
and Codex can be Owner; no command below designates Claude as the required leader.
Existing qualification, worktree ownership, live-leader and Owner review checks remain
required. Enabling unattended execution does not grant tools or accept completed work.

## Claims & evidence

| Claim / criterion | Evidence and source | Oracle / red observed | Confidence and residual risk |
|---|---|---|---|
| AC2: explicit finite policy | `test_runtime_controls_require_explicit_unattended_enablement`, runner validation and qualified run CLI tests | False opt-in must fail before preparing workers; policy binds immutable manifest | Verified locally; qualification is tied to the current profile |
| AC3: exactly-once compiled input | Runner mailbox tests, `test_completed_worker_refuses_input_while_other_worker_runs`, transport dynamic-turn tests | Independent review reproduced writes into a finished worker; fixed and retested. Consumed admission is durable before dispatch | Verified; crashes after admission remain indeterminate, not replayable |
| AC4: exact once-only decision | Control concurrent/tamper tests and transport permission tests; real Claude callback/write readback | Wrong option/request, expired decisions, reused RPC IDs and persistent grants fail. Initial native zero-callback canaries were rejected as proof | Verified for tested callbacks; native policy can suppress callbacks |
| AC5: no ambiguous replay | Runner pre-dispatch EOF retry, dirty checkout and `test_eof_after_prompt_is_not_retried` | Dispatch counter is incremented before queueing the wire frame; post-dispatch EOF produces one attempt | Verified offline; no automatic auth/policy recovery |
| AC6: native attachment | Runner real socket/process tests; disposable Codex/Grok two-controller native observations | Wrong native cwd and substituted Git repository refuse input; SIGTERM child leak reproduced before fix; shared backend remains alive afterward | Verified addressable native backends; arbitrary existing terminals unsupported |
| AC7: fresh-clone proof | Seven `test_coord_proof_fresh_clone.py` tests and historical verifier | Original verifier failed in an actual single-branch clone. Missing/corrupt pack, wrong ancestry and current receipt tampering fail | Verified; pinned historical fixture is evidence, not a new live run |
| AC8: bounded private controls and truthful events | `test_coord_runtime.py`, runner, native and transport tests | FIFO/held lock reproduced hangs before fix; profile helper deadline, Unicode body serialization, cancellation-final-read and queued-output regressions fixed | Verified locally; same-OS-user malicious access is outside isolation boundary |

Primary source contracts are `pack/scripts/coord_runtime.py`, `coord-runner.py`,
`coord_transport.py`, `coord_native.py` and `bounded_process.py`. Tests use the public
CLI composition root, real temporary repositories, sockets and owned subprocesses.
Mode selection additionally requires one exact advertised fresh ACP mode before any
prompt; omitted, invalid, duplicate, unknown and failed selection cases are covered.

## Native observations

Sanitized measured records are in
[`runtime-native-observations.json`](../knowledge/acp-compatibility/runtime-native-observations.json).
All canaries used disposable sessions; no pre-existing user session was contacted.

| Harness | Dynamic follow-up | Interactive permission evidence | Live attachment |
|---|---|---|---|
| Claude ACP 0.79.0 | Two completed turns, 71.932258s including approval wait | One inspected native `allow_once`; exact file content read back | No qualified shared-terminal endpoint; Remote Control is a separate native workflow |
| Codex ACP 1.12.0 | Two completed turns, 6.563573s | Explicit `read-only` mode: one real request, inspected exact diff, `allow_once`, matching file readback; 62.591083s including review | Native app-server socket/UUID queue, original controller usable afterward |
| Grok 1.0.34 | Two completed turns, 15.426334s | Installed profile auto-approved the canary despite CLI default mode; **ask remains unqualified** | Two ACP clients on the same explicit live leader socket, matching native cwd/UUID |
| Agy, wire version not reported | Two completed turns, 6.096607s | Headless interactive approval unavailable; `ask` rejected before preparation | No qualified native live-input endpoint |

The native attachment checks measured shared context: the second client recalled the
first client's token; the original controller then recalled the second client's token.
They establish live input for those backends. They do not establish arbitrary terminal
attachment, inherit `AGENT_SESSION` into an existing backend, or attest worker ownership.
Ordinary coordination mail is not executed as instructions. The runtime mailbox accepts
only an Owner-admitted completed compilation at a turn boundary.

## Test coverage of the boundary set

Fresh clone/Git history, filesystem privacy and hostile file types, concurrent controls,
native schema/correlation, process tree containment, timeout/cancellation, leader/profile
drift, compiled input admission and public CLI output are covered. The first aggregate
offline run passed 158 tests (five pre-existing platform skips); one later manifest-mode
regression also passed. Full bundle and final clone results belong in the gate record.

## Change reach & instrumentation

Manifest/control writer → schema and append-only records → runner admission/fence →
transport/native wire → status/permission/attach CLI → generated launch guidance → proof
reader. Dispatch/permission/retry counts, duration, bytes and outcome are emitted by the
normal path. Spend/tokens remain **not recorded** when the native runtime provides none.
The fresh-clone helper distinguishes deterministic proof from native qualification.

## Failure modes addressed

No automatic retry after possible dispatch; no replay after a durable admission; no
approval on timeout, wrong request or persistent grant; no child surviving ordinary
owned-client cancellation; no cancellation of a loaded shared backend; no native input
to a mismatched worktree. A crashed backend may keep running and needs operator review.

## Threats addressed (adversarial analysis)

The design records STRIDE-lite controls for spoofed identity, tampered input, local
repudiation, disclosure, resource exhaustion and unintended permission escalation.
Independent reviewers reproduced and retested lock/FIFO hangs, finished-worker input,
oversized serialized Unicode, wrong checkout binding and interruption leaks. Approval
remains an explicit exact-option action. No native hook or global trust setting changed.

## Privacy findings addressed (LINDDUN-lite)

Prompt/action bodies stay in owner-only local controls; events contain IDs and digests.
Private run records persist until the operator removes a completed run directory.
Committed canaries contain no prompt/action bodies or credential material. Execution
identities are intentionally linkable for audit; same-user hostile processes are not isolated.

## UI states & floors proven

Terminal-only serial action/confirmation interface: waiting, pending, refused, queued,
indeterminate and ready-for-review are distinct. Exact IDs/options remain copyable;
meaning does not depend on color. Approval details are explicitly requested, not clipped
into summary output. No graphical layout, animation or contrast surface is introduced.

## Testing Strategy directives applied

D0–D7 relevant filesystem, subprocess, protocol and provider boundaries; A1 deterministic
wrapper, A3 structured responses, A4 bounded workflow, A6 skill guidance. MCP/generated
content quality are not new boundaries. Semantic acceptance remains Owner review.

## Verification commands

From a fresh POSIX clone with Python 3 and Git, without model credentials:

```sh
python3 tools/verify-coordination-runtime.py
```

This checks original Git receipt hashes/ancestry in an isolated object store and runs the
runtime boundary suites. It neither contacts models nor qualifies a local profile.
Native lifecycle checks are opt-in through
`docs/knowledge/acp-compatibility/qualify-runtime-controls.py`; inspect its help and use
the actual installed executable. Permission-capable profiles require a non-vacuous
request, concrete inspection/decision and observed result before admitting `ask`.

## Flagged risks / residual unknowns

Windows containment remains unqualified. Claude/Agy arbitrary live-terminal attachment
is unsupported. Grok's current auto-approval profile cannot be called ask-qualified.
Native permission payloads can omit edit contents; the permission viewer shows the exact
offered request, and a separate native inspection is required before approving when that
payload is insufficient. Terminal.app is the chosen host, with native sockets as the
attachment boundary; the runner does not automate terminal focus or type into shells.
Loaded shared sessions can continue work after this client disconnects; queue acceptance
is not completion. Native versions and profile settings can change and invalidate proof.

## Status & next action

Implementation, independent review and all 17 release gates passed for the declared
supported paths. Use an explicitly enabled manifest and current profile qualification
for the next unattended run. Unsupported native capability rows remain explicit.
The final delivery verifies remote synchronization and executes the fresh-clone command.

## Gate record

Full bundle: all 17 gates PASS; 1,263 Python tests, 508 subtests, 12 explicit skips;
28 Node contracts and rendered accessibility checks PASS. Initial offline helper:
158 tests with five platform skips; the later manifest-mode regression and all 43
liveness tests also passed. The public helper now includes those added boundaries.
Independent final status review confirmed that missing, changed or ambiguous inventory
cannot produce a fabricated retained-worktree path. No hook definitions changed.

Fresh-clone execution on source commit `277d545b7d6bb115018ec6fb99584ab915897712`: **PASS**, 202 tests and five explicit platform skips. The clone used `--no-local --single-branch`, had only its selected branch and no alternates, and all four historical worker commits were absent from its Git object database. Original receipt verification still passed through the isolated pinned fixture. Subsequent integration changes contain audit/lifecycle records and this proof result, with no runtime or test-code changes.
