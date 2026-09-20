---
id: design-multi-harness-runner
title: "Design: bounded multi-harness runner"
type: design
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, execution]
links:
  - { to: spec-multi-harness-launch-and-monitor, rel: implements }
  - { to: design-message-layer, rel: refines }
  - { to: spec-leader-designation, rel: depends-on }
review-by: "2027-03-20"
review-suggested: []
summary: >-
  An opt-in foreground runner prepares worktrees and runs admitted compiled prompts
  through a shared bounded ACP client or an explicit Agy stream adapter. Existing
  coordination leadership and event writers remain authoritative; qualification and
  artifact evidence are reported separately from transport completion.
---

# Bounded multi-harness runner

Status: design gate passed. Tier T2. This is a local composition of the existing
coordination layer, not a replacement broker or a new authority boundary.

## Responsibility and scope

The specification requires isolated identities/checkouts (AC2–3), lease renewal (AC4),
finite execution (AC6), and independent evidence inspection (AC7). The runner implements
those deterministic mechanics. The Owner still writes contracts, qualifies capabilities,
rules on requests, reviews semantic work, and invokes the existing join gate.

Grounding traversal: launch spec → message-layer design → coordination core; launch spec
→ leader designation. Protocol evidence is the separate ACP spike, commit `abe0cc0`:
Grok native ACP, Claude ACP and Codex ACP passed creation/repeated prompts/progress/early
cancellation; Agy passed native stream turns. These observations do not qualify installed
pack hooks. The experimental probe is not reused as a production stream implementation.

**Selected scope:** opt-in pilot, foreground, POSIX process groups, at most four workers.
Windows refuses before model launch until an interactive Job Object implementation is
qualified. One attempt admits a finite list of compiled prompts in advance; later prompts
use the same transport session. Dynamic mailbox-driven prompting, arbitrary TUI attach,
cross-process session resume, interactive permission approval and automatic join are out.
An Owner ruling that needs an additional prompt requires an explicit new attempt or the
existing manual brief workflow. No existing default mode changes.

## Domain and durable representation

Run is the aggregate. Its identity is exclusive for its lifetime, including after a crash.
Worker identities and branches are unique within it and differ from the Owner. Preparation
binds the invoking commit, exact compiled prompts and worker contracts. A run is never
silently retried. A new attempt needs a new run id, new worker ids and new branches.

| Record | Grain and invariant | Representation / history |
|---|---|---|
| Prepared run | One immutable admitted contract with actual worktree paths | Private manifest in git common directory `coord-runs/<run-id>/`; exclusive directory creation; partial preparation facts retain created paths |
| Worker identity reservation | One session assigned to exactly one attempt | Exclusive private file in common-git `coord-run-sessions/`; retained after failure, alongside existing session-history check |
| Started marker | One exclusive attempt start including admitted holder and epoch | Exclusive file creation; never removed to make a retry appear new |
| Qualification | One Owner-supplied observation bound to prepared worker fingerprint | Input file; digest recorded in start event; no automatic promotion from spike |
| Lifecycle event | One observed transition per run/worker | Existing `coord-core.append_event` writer in `.agents/log/<owner>.jsonl` |
| Artifact receipt | One explicit file or commit verification result | Terminal lifecycle event; derived by reading assigned checkout |

Local manifests contain prompts; they live beneath `.git`, not the committed audit.
Tracked events contain identifiers, hashes, measured counters and stable codes, no model
text, environment values, prompts, tool arguments or permission descriptions. Status folds
the existing event ledger and reports missing terminal evidence as `interrupted_or_running`,
never success. No second event ledger is introduced. Counters are additive per attempt;
duration is per-attempt elapsed time; ratios and status are derived; usage/cost are explicitly
`not recorded`. Versions are labelled qualification metadata unless reported by the adapter.

## Change-surface list (E7)

`pack/scripts/coord-runner.py` (input, worktrees, leadership, receipts, CLI) +
`pack/scripts/coord_transport.py` (bounded wire lifecycle) → common-git manifest and existing
event writer → JSONL progress / status JSON → `execute-with-coordination --launch` instructions
→ generated Claude/Codex/Grok/Copilot skill surfaces and deployed scripts → deterministic
tests invoking the deployed composition root. No board schema change, public HTTP endpoint,
graphical interface, new persistent authority store, or credential storage.

## Exposed contracts

`coord-runner.py prepare --contract FILE` validates all workers before creating any tree,
then calls `coord worktree new`, reads actual git inventory and stores the manifest.
`run --run ID --qualification FILE` checks all bindings and a live Owner designation, creates
the exclusive start marker, then launches. `status --run ID` reads facts. Exit 0 means the
requested command completed; `run` exits nonzero unless every worker is ready for review.
JSON output always names the per-worker transport and evidence outcomes.

Contract schema `coord-run/1`:

```
run_id, owner, parallelism (1..4), workers (1..8)
worker: session, branch, harness (claude|codex|grok|agy), transport (acp|agy),
        argv (nonempty string array; installed executable, no shell),
        prompts (1..8 compilation audit IDs), deadline_seconds (1..3600),
        output_limit (1024..16777216 total bytes), fallback (nonempty text),
        required_capabilities ({name: enforced|observed-only}),
        binding_files (absolute or checkout-relative paths),
        evidence ([{kind: file, path, max_bytes} | {kind: commit}])
```

Only Agy can select its native transport. `argv` may contain a literal `{worktree}` argument
substitution; no other expansion or shell interpretation occurs. The Owner selects documented
effective policy via native argv and inherited harness configuration. The runner never adds
unrestricted permission flags. Child environment overrides `AGENT_SESSION`, `AGENT_HOST`,
`AGENT_WI`; clears inherited `CLAUDECODE` for nested adapter launch. Prompts come from verified,
dispatchable compilation audit records, not worker output. Each compilation is rechecked
against its raw prompt using the existing compiler gate. The transport prompt is normalized
from verified `render_sections` output with the assigned worker's audit-start/cwd envelope;
the separately rendered audit `prompt` is never dispatched (Codex's native template contains
an outer CLI wrapper). Resulting exact bytes are bound in the prepared manifest. Outstanding
decision requests refuse. Aggregate admitted worker/brief data is capped at 512 KiB before
any worktree is created, leaving headroom below the 2 MiB manifest reader bound.

Preparation refuses an unresolved parent index, invalid git branch, duplicate worker/branch,
existing branch/tree, missing compilation or malformed evidence path. It uses the invoking
checkout's resolved HEAD, not the primary checkout HEAD. Created trees are never deleted on
partial failure. Repeating prepare reports the existing run; it does not complete a partial
prepare by guessing. The manifest retains the exact admitted prompt bytes for manual fallback.

`fingerprint --run ID` prints current per-worker fingerprints for **recording an observation**.
It is not a qualification command and never marks a capability verified. The fingerprint
binds run contract/prompt hashes, actual cwd/base, argv, resolved executable content hash,
selected instruction/hook/trust configuration file hashes (missing is explicit), and the
effective inherited environment digest (values never printed). The Owner must list all
load-bearing configuration and adapter lockfiles in `binding_files`. Hashing detects drift;
it cannot prove that the listed files are complete or that a hook ran.

Qualification schema `coord-qualification/1`: `workers` maps session to `{fingerprint,
version, evidence, effective_policy, trust, capabilities}`. Policy and trust describe the
measured effective settings; an adapter mode name alone is insufficient. Evidence is a nonempty explanation/reference to measured
observations; each capability has the required classification or stronger. Unknown, missing,
changed fingerprint or unsupported blocks. Classification is an Owner attestation, clearly
labelled; the runner does not claim to enforce native harness boundaries. Requirements cannot
be weakened implicitly. A manual brief and remediation remain available on a blocked run.

## Transport contract and protocol

`coord_transport.run_session(transport, argv, cwd, env, prompts, deadline_seconds,
output_limit, emit, cancelled, before_prompt) -> dict` is the only process seam. `emit` receives sanitized
metadata only; `cancelled()` is checked at least every 100 ms during IO. Each transport
implements creation, finite ordered prompts, progress, terminal reason and cleanup. Return
contains `outcome`, `code`, `session_id`, `turns_completed`, `stdout_bytes`, `stderr_bytes`,
`duration_seconds`, `permission_requests`, `cleanup_error`, `reported_version`,
`extension_notifications`, `native_denials`. The two new counters are one attempt's
observed messages/denial entries, additive within that attempt; no capability is inferred.
`before_prompt(remaining_seconds)` returns whether the live exact holder/epoch still admits
dispatch; its execution is included in the attempt deadline. Only ACP `end_turn` and Agy
`SUCCESS` qualify as complete. A max-token/max-turn stop, cancellation, protocol error or
permission refusal is not complete, even if its response parses successfully.

ACP JSON-RPC 2.0 over newline-delimited UTF-8: initialize protocolVersion 1 with empty
clientCapabilities; session/new with cwd and empty mcpServers; session/prompt with text
blocks; session/update notifications; session/cancel notification for bounded cancellation.
Grok authentication selects advertised `cached_token` only; unsupported authentication is a
named failure requiring native login. No editor filesystem/terminal capabilities are exposed.
All unsolicited server requests receive method-not-found except `session/request_permission`:
it receives a reject_once option if present, otherwise cancelled. Permission denial produces
an action id and `permission_denied`, never ready for review, even if a later stop says done.
Denial is sticky and stops the remaining prompt list. This first version waits zero seconds
for permission approval and retains the stated fallback.
No raw server error/message/tool fields are copied into the durable event stream.

ACP v1 extension handling follows the [extensibility contract](https://agentclientprotocol.com/protocol/v1/extensibility):
underscore-prefixed notifications without an id are ignored and counted. JSON-RPC version,
method type, absence of response-only fields, and params object/array shape remain checked.
Unknown requests still receive -32601. Standard notifications remain explicitly supported
or refused; session updates retain identity validation. Every receive retains the original
attempt-wide byte/deadline/cancellation checks, and no per-extension durable event is emitted.

Agy: caller supplies documented argv including `--add-dir {worktree}` and stream-json input
and output. Send `{"event":"user","message":{"content":text}}`; observe init `conversation_id`,
step_update progress and per-turn `result.conversation_id` / `result.status`.
SUCCESS is transport completion only. Agy has no
observed per-turn correlation id: only one prompt is in flight, prompt bytes are flushed
before reading its result, and buffered unsolicited results are refused at the next turn
boundary. This sequencing control does not claim protection against a malicious provider
fabricating a later result. Agy has no
qualified external permission callback; native policy/hook qualification is a prerequisite,
not something the runner infers from the absence of a callback. Cancellation terminates the
owned process group; no graceful per-turn cancel or undo is claimed.

Native refusal is checked before SUCCESS: a nonempty `denied_actions` list with valid action
identifiers emits sanitized `native_permission_denied` with a stable action id, increments
`native_denials`, and blocks. Malformed lists/items fail closed. Error steps also stop the
attempt immediately after requiring an established, matching conversation identity. A tool step with
`state=ERROR`, `tool_info.error.type=TOOL_ERROR` and the recorded Agy 1.2.7 message prefix
`permission check failed for ` is a native denial; all other ERROR steps fail with
`native_tool_error`. Arbitrary assistant/response prose is never permission evidence. No
raw denial action or error text is retained. The original refusal remains terminal through
cleanup, and existing receipts cannot promote it to ready. Product regressions are derived
from the recorded local-profile envelopes, not only simplified peers.

## Concurrency and resource bounds

Stdlib selectors/nonblocking pipes bound stdin writes as well as both output streams;
unterminated lines and a stopped reader cannot allocate or block without limit. Total bytes
across stdout/stderr have one hard bound per attempt, individual JSON frames are bounded by
that same budget. No unbounded queue or transcript capture. Deadline covers initialize,
authentication, session creation and every prompt together, not a fresh budget per turn.
ACP cancellation has at most one second grace within cleanup; then kill the owned POSIX
group and reap within four seconds. Cleanup runs even after successful prompt completion
because ACP agents remain alive. Process groups contain cooperative descendants; they are
not a sandbox against an executable deliberately escaping its group. Memory/process-count
OS enforcement beyond the finite reader buffers is not claimed.

Main monitor thread owns lease checks, at least once per second, and renews through existing
leader CAS at its published interval (or earlier for a short lease). It checks the exact
holder and epoch, never elects or pins a leader, and passes cancellation to all active
workers on loss. Existing `leader who` and an admitted-epoch renewal helper run through `run_bounded` with an
outer two-second deadline (shorter when the attempt or cached lease has less time); a blocked Git call cannot
inherit the core's longer bound. Cached lease expiry independently cancels workers while
that check is pending. The cleanup clock is anchored to the attempt/lease deadline, not to
callback return. Fresh checks also gate each prompt. Events serialize under a lock; no competing
writer changes leader state. Thread pool width is explicit; queued workers do not start
after cancellation. A single worker failure is contained to its worker; leader loss cancels
the run. SIGINT/SIGTERM cancel owned workers; later status shows the recorded result.

## Evidence verification

After transport completion and cleanup, recheck worker git branch/worktree identity.
File verifier accepts only a regular, nonempty file within the assigned checkout, with no
symlink component, below the declared byte cap; returns byte count and SHA-256. Commit
verifier requires HEAD to be a descendant of the admitted base and different from it;
returns commit id. The verifier never executes worker-supplied commands. Dirty-file
verification is an observation at inspection time; commit verification binds immutable git
objects. Neither verifies semantic acceptance. Missing/escaped/substituted evidence reports
`evidence_incomplete`. Owner review and existing conductor join remain mandatory.

## Patterns and selection ladder

Reuse core worktree/leader/event APIs and compiler gate; stdlib selector and bounded executor.
Two transport strategies normalize only the session lifecycle. No provider inventory, editor
proxy, custom RPC framework, broker, database or daemon. Exclusive create is the at-most-once
attempt fence, not an automatic distributed retry mechanism. Append-only events follow the
existing coordination model. The separate prepare step is required because cwd-specific trust
cannot be qualified before the tree exists. It is not a second approval dialog.

## Failure-mode analysis

| Failure | Disposition / proof |
|---|---|
| Invalid contract/compilation, unresolved index | Refuse before model spawn; malformed, duplicate, unresolved DR tests |
| Partial worktree creation | Preserve trees, record failure, no implicit retry; real git failure fixture |
| Stale or absent qualification | Block before model spawn; cwd/config mutation tests |
| Lease changed/expired/CAS failure | Stop further prompts and owned workers; real git leader-ref mutation |
| Duplicate prepare/run or interrupted attempt | Exclusive fence; report existing facts; concurrent launch test |
| Malformed/flooded output, stalled input, process exit | Stable protocol/output/deadline code; bounded subprocess fault fixtures |
| Permission request | Reject, action id, no success promotion; callback negative fixture |
| False done / missing or escaped artifact / wrong HEAD | Separate receipt failure; real checkout/path tests |
| Buffered Agy completion credited to a prompt not sent | Refuse unsolicited buffered result; flush admitted input before response interpretation; duplicate-result subprocess fixture |

## Adversarial analysis (STRIDE-lite)

| Boundary | Threat | Disposition |
|---|---|---|
| Contract → process | Injection, elevation | Owner-supplied argv array; no shell or automatic installs; no worker-output commands |
| Parent → worker | Identity spoofing | Explicit identity override; inherited leader-env test |
| Lease → dispatch | Stale authority | Exact epoch+holder check with CAS renew; competing leader test |
| Model text → ledger | Disclosure | Whitelisted operational fields only; secret sentinel absent from events |
| Worker checkout → verifier | Substitution | Reject symlinks/traversal, verify actual branch and ancestry |
| Same-user local files | Tampering | Accepted existing coordination trust boundary; hashes detect drift, not malicious same-user forgery |
| Process → host | Escaped descendants | Accepted cooperative-process limitation; not a malicious-harness sandbox |

## Privacy analysis (LINDDUN-lite)

| Data flow | Finding | Disposition |
|---|---|---|
| Contract and repository work → selected harness | Disclosure follows the selected harness/provider's existing policy | Explicit Owner-selected installed transport; no automatic provider routing or credential copying; bind effective policy |
| Prompt bytes → run metadata | Local retention may contain repository work data | Private common-git directory; no raw prompt/conversation in tracked operational facts |
| Worker metadata → ledger | Session linkability | Accepted for durable audit; only bounded operational fields, hashes and explicit unknown cost |

Pseudonymous session ids are linkable by design in the existing audit. Prompt bytes stay in
private common-git run files with restricted permissions; metadata events contain no raw
model output, permission argument, secret or environment value. Unknown cost remains unknown.
Retention follows repository-local run metadata; deleting a manifest is not a safe replay
mechanism. Tracked event history remains the durable evidence. No external telemetry endpoint.

## Telemetry and testing

Events name run/worker/Owner, state/code, time, elapsed duration, bytes, completed turns,
permission count, qualification digest, cleanup disposition and declared fallback reference.
Trace identity is run id, child span identity worker session; no invented tokens/spend.
JSON is the CLI UX; errors have stable code and remedy. This is not HTTP: RFC9457 is N/A.

Testing union D0–D4, D6–D7, A1, A3–A4, A6: red-first real temporary git repositories and
subprocess protocol peers through the installed entry point, property/boundary cases for
identities/paths/budgets, representative ACP/Agy wire fixtures derived from observed traces,
faults for stalled IO/flood/early EOF/permission/leader loss/cancellation, and negative
artifact tests. Live spike observations validate provider contracts, not production wrapper
qualification. All generated skill surfaces and deployed script bytes are checked by sync
and bundle gates. No online provider is required by CI.

## Gate and residual risks

Independent Patterns/Simplifier, Test Architect, Security/Distributed Systems and SRE review
PASS (ACP reviewer, 2026-09-20). Conditions resolved: bounded fresh leader fences and admission
epoch; positive per-turn completion with sticky denial; explicit observed policy/trust fields.
The renewal helper reads the admitted epoch, uses the existing `leader_decide` and
`leader_write` CAS, and emits the existing leader event. This closes the check-then-renew
race without modifying the designation protocol. Worktree checks also verify registration
and git common directory. Executable resolution uses the child cwd/PATH and freezes its
absolute target; a queued worker is rechecked immediately before spawn. Status accepts only
Owner runner facts with matching start admission; partial preparation remains reportable.
Production qualification remains separate from the implementation gate. Initial
release is an opt-in POSIX pilot; unqualified adapters/configuration stay blocked with manual
brief fallback. No claim of full pack hook enforcement or arbitrary open-session attachment.
