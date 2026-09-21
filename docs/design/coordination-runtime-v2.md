---
id: design-coordination-runtime-v2
title: "Coordination runtime control contracts"
type: design
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, runtime, permissions, audit]
links:
  - { to: spec-coordination-runtime-v2, rel: implements }
  - { to: plan-coordination-runtime-v2, rel: relates-to }
review-by: "2026-12-21"
review-suggested: []
summary: "Private append-only controls around the existing bounded ACP/native runtime."
---

# Runtime control contracts

## Decision, model and durable representation

Reuse the existing runner, subprocess boundary and coordination events. Stdlib only.
Pattern: bounded producer/consumer mailbox and explicit permission state machine; no
broker, background service or automatic permission policy. A foreground runner may be
supervised by the initiating terminal/session. An unattended run has no interactive stdin
dependency; all external inputs are explicit immutable control records.

Run aggregate root: immutable prepared manifest; invariant finite qualified execution
under the same live leader epoch. Worker aggregate: one owned checkout/native session;
invariant no automatic replay after a prompt may have dispatched. Control aggregate:
one immutable request ID and at most one decision, tied to run and worker. References
use identities, never duplicated session ownership facts.

One control record is exactly one enqueue, finish, permission request or decision.
Records live under the existing private `.git/coord-runs/<run>/` directory, created
exclusively, bounded in size, never overwritten. IDs/order come from serialized local
allocation; atomic publication prevents partial-read approval. User-input bodies are
private; public coordination events contain IDs, state, counts and digest only. OS local
user/filesystem authority is the trust boundary, as with the existing coordination store;
this is not protection against arbitrary code running as the same OS user.

History is append-only, no backfill. Existing manifests without runtime options retain
finite denial-only behavior. New runtime policy is manifest-hashed: unattended boolean,
mailbox boolean, maximum turns, maximum pre-dispatch retries, permission mode deny/ask,
and optional literal ACP `mode_id`. Explicit unattended enablement must be true. A mode
must be advertised by the fresh native session and selected before its first prompt;
loaded shared sessions cannot have their mode changed by this client.
Facts are immutable; pending and consumed views derive from records/events. Dispatch is
at-most-once within the run. A crash after admission produces an indeterminate state and
never an automatic resume or replay. Durations and byte/turn counts are additive per
attempt; total wall time and current pending counts are non-additive across snapshots.

## API and wire contracts

`run_session` adds optional keyword-only `next_prompt` and `permission_handler` callbacks.
The default remains the current finite prompt list and deny-all callback. Dynamic input
is requested only after a correlated completed turn; finite turn/time/byte bounds still
apply. Each callback is polled briefly so cancellation and leader expiry remain checked.
Native ACP permission response must select an exact offered option for this session and
request. Only `allow_once` can grant in this slice; reject/cancel are always supported.
Callbacks cannot override native runtime denial or trust controls. An allowed request
does not force a permission-denied terminal result; track request/allow/deny counts separately.

Runner CLI additions: enqueue a compiled audit ID for one worker, close its mailbox,
list pending permissions, show one private request and decide its exact option. Owner
identity/live epoch and immutable policy are checked before control writes. The runner
revalidates compiled prompts, leader, config and operational file identity before sending.
No raw mailbox body becomes model input without the existing compilation gate.

Automatic retry is a wrapper around a whole transport attempt only if no prompt was
started, cleanup succeeded and a classified transient startup failure occurred. Each
retry is counted, shares the original wall/byte budget and rechecks clean checkout,
fingerprint and leader. Denials, protocol failures, auth failures and any post-dispatch
failure are terminal. Backoff is bounded and cancellation-aware. No silent requalification.

Live attach uses a measured addressable backend. Codex uses native `queue --remote`
after a bounded Unix WebSocket `thread/read` proves the exact UUID, cwd and direct-input
capability. Grok uses ACP load only against an explicitly supplied live leader socket;
its returned native metadata must prove the exact UUID and cwd before any prompt. This
specific shared-backend contract was measured with two simultaneous clients. Generic
saved-session loading does not establish live attachment. The registered worker's actual
Git common directory, branch and worktree, executable and owned socket identity are
checked before dispatch. The operator explicitly binds the worker and native UUID;
the backend retains its original environment and trust. Queue delivery is not completion
or qualification. Never send session-wide cancellation to a loaded shared backend, even
after this client sent a prompt: another controller may now own the active turn. Stop
only our client and report indeterminate work, which may continue in the backend.

## Surfaces and telemetry

Store → manifest/runtime/control value validation → runner service → ACP/native wire →
CLI commands/status → execute-with-coordination launch guidance → proof verifier/readers.
Source scripts in `pack/scripts`, generated installs via sync-pack; tests cover both
normal and refused public behavior. Existing public events gain permission pending/decided,
prompt admitted, waiting, retry started/exhausted and input closed, carrying run/worker/
request IDs and timestamps. Body text is private. Latency, attempts, bytes and failures
are measured; tokens/spend explicitly remain not recorded where unavailable. No HTTP
surface, so RFC9457 is N/A. CLI uses stable RUN-/transport codes and remedies.

## Adversarial analysis (STRIDE-lite)

| Boundary/failure or threat | Disposition and negative proof |
|---|---|
| Malformed/oversized/duplicate/out-of-order control | Prevent with schema, size, exclusive immutable publication, sequence and exact identity checks; mutate every field in tests. |
| Concurrent enqueue/finish/decision | Serialize allocation/publication, one decision per request; concurrent-process test checks no lost writes or double approval. |
| Partial publication/crash after dispatch | Atomic files; consumed admission is never replayed; crash tests require indeterminate/blocked outcome. |
| Stale leader, manifest/profile drift, replaced root | Detect/fence before every prompt/retry/decision; existing drift tests extended. |
| Prompt or permission spoofing/tampering | Owner/epoch and compilation checks; native session correlation; exact offered allow_once only; forged IDs/options and altered pending requests rejected. |
| Repudiation | Immutable local controls plus body digests and public decision/dispatch events. Same-OS-user malicious rewriting remains outside boundary and is stated, not called authenticated. |
| Disclosure | Native details/prompts only private files, mode0600; sanitized events/errors; sentinel-secret tests. |
| Flood/hang/denial of service | Run time/byte/turn/control-count bounds; expiry/cancellation while waiting; no unbounded background children. |
| Escalation by unattended mode | Mode grants no permissions. Timeout/default deny. Persistent allow options rejected. Native trust and policy retained. |
| Retry after mutation/ambiguous response | Prevent automatic replay once prompt_started is observed; test EOF before vs after dispatch and dirty checkout between attempts. |
| Native live attach unavailable | Fail with capability-specific remedy; never simulate success with saved-session load or terminal typing. |
| Fixture missing/corrupt/wrong history | Pinned original Git object pack, isolated object store, unchanged parent/ancestry/content checks; fresh-clone and corrupt-fixture tests. |

## Privacy analysis (LINDDUN-lite)

| Threat | Data and disposition | Verification |
|---|---|---|
| Linkability and identifiability | Run/worker IDs intentionally link execution; raw prompts and native action details remain private local files. | Sentinel-secret output tests; sanitized native observation records. |
| Disclosure | Permission details and compiled bodies are owner-only mode0600 records in mode0700 directories. | Permissions, symlink, tamper and size negatives. |
| Detectability and unawareness | Pending approval is explicit; no background approval or hidden mailbox input. | Pending/decision events and exact-option CLI tests. |
| Retention | Operator retains completed private run directories until explicitly removed. No new analytics recipient. | Public launch guide documents the local deletion boundary. |

Prompts/action descriptions may contain user paths or task data. Minimize public
linkability to run/worker IDs; no raw text in telemetry. Private records remain until
operator removes the completed run directory; documentation states retention and local
deletion path. No additional external recipient or analytics. These controls cover
LINDDUN disclosure, identifiability, detectability and awareness; execution accountability
is intentional, with private local retention under the operator's control.

## Test plan and review

Triggered union: D0 hygiene, D1 branch/mutation resistance, D2 bounded schema invariants,
D3 module/CLI contracts, D4 real filesystem/process integration, D5-provider CLI/callback
contracts, D6 message schema, D7 recorded/native fidelity; A1 deterministic AI wrapper,
A3 typed wire responses, A4 workflow termination/cancel/retry, A6 skill guidance contract.
A2 MCP and A5 generated semantic content are not introduced; Owner semantic review stays
separate. Each handled failure above has a negative test. Native smoke tests use disposable
sessions, original trust/policy, harmless evidence and explicit denial/approval controls.
Fresh-clone proof has no model dependency. Full bundle gates follow source/install sync.

Independent review must challenge option binding, at-most-once dispatch, cancellation
during waiting, retry ambiguity and false live-attachment claims. Residual risk: adapters
change, OS processes can outlive a crash, and a local same-user attacker is not isolated.
No deployment-wide unattended capability claim follows from a single-machine observation.
