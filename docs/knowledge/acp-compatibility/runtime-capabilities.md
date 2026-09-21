---
id: kb-coordination-runtime-capabilities
title: "Installed runtime control capabilities"
type: knowledge
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, permissions, sessions]
links:
  - { to: spec-coordination-runtime-v2, rel: relates-to }
  - { to: design-coordination-runtime-v2, rel: relates-to }
  - { to: spec-acp-coordination, rel: relates-to }
review-by: "2026-12-21"
summary: "Measured local session creation/loading and a native permission callback, plus installed live-input interfaces and their remaining qualification boundaries."
---

# Installed runtime control capabilities

Measured on 2026-09-21 for the runtime expansion. This research distinguishes a
new process loading conversation history from a second client addressing an existing
live session. None of these probes contacted, prompted, attached to, or terminated an
existing user session. All native model probes used disposable temporary workspaces;
initial permission probes rejected requests. The final Codex probe inspected an exact
native edit diff and selected one offered allow_once; it verified and removed its
owned canary. No permission bypass was added.

## Capability matrix

| Harness / measured version | Session load | Interactive permission response | Follow-up and live-input boundary |
|---|---|---|---|
| Claude ACP 0.79.0 | Advertised; creating and loading the same disposable empty session succeeded. Source loads history and replays it. | A fresh manual-mode session emitted one real callback. Selecting the offered `reject_once` completed the turn without creating the target. | ACP advertises prompt queueing and steering. The normal transport can send sequential prompts. Native Remote Control is a separate authenticated terminal/browser service; ACP load does not establish live-terminal attachment. |
| Codex ACP 1.12.0 | Advertised; an empty new thread loaded through this probe returned `-32603`. Do not promote capability advertisement to a qualified resume profile. | Shipping transport explicitly selected advertised `read-only` mode. A native edit outside the temporary workspace emitted one callback; the reviewed `allow_once` produced exact canary contents. Earlier temporary-target evidence remains vacuous. | Native `queue --remote unix://<socket> --thread <UUID> --message <text>` delivered to a disposable live app-server thread. The original client stayed connected and completed a subsequent turn with the queued turn's context. |
| Grok 1.0.34 | Isolated `agent --no-leader stdio` advertised load and loaded its own empty session successfully. | Unqualified. A later exact-shipping probe wrote its external canary with zero callbacks; the selected invocation did not establish ask policy over the local always-approve configuration. | Two clients on one disposable `agent leader` exchanged prompts on the same session. Both received updates; the original client remained usable with shared context after the second client's prompt. |
| Agy native stream | CLI documents `--conversation` and `--continue`, which start new processes; not live attach. | Headless mode has no interactive permission prompt. A callback must be refused as unsupported on this adapter. | Installed `--input-format stream-json` accepts one user message per turn in a persistent process. Remote-control daemon commands are a different interface; no general live-input API was established here. |

The package versions above came from installed adapter metadata and fresh initialization
responses. The Grok version came from its native `_meta.agentVersion`. CLI help and source
inspection prove the advertised interfaces, not their unattended delivery or permission
behavior. No terminal application or multiplexer was assumed; no `tmux` executable was
found during this probe.

## Native contract evidence

The ACP session-load capability is optional and must be negotiated. Loading restores a
conversation; it does not confer repository ownership or establish that another controlling
client stopped. Native permission requests carry a session, request ID, tool description and
offered option IDs. A response selects an offered option or cancels the request. The runner
must bind its own decision to that concrete request. Sources:
[ACP session setup](https://agentclientprotocol.com/protocol/v1/session-setup) and
[ACP tool calls](https://agentclientprotocol.com/protocol/v1/tool-calls).

Claude's installed adapter implements `loadSession` using `readResumedSession`,
`getOrCreateSession` and history replay. Its initialization advertises `loadSession`,
session resume/list/close/fork, prompt queueing and steering. Native Claude Remote Control
can be enabled inside an existing interactive session and preserves simultaneous terminal
and browser interaction. It requires its own authentication/confirmation and is not an ACP
attachment API. Source: [Claude Remote Control](https://code.claude.com/docs/en/remote-control).

Codex's installed adapter implements load/resume through app-server `threadResume`,
refreshing skills and supplying cwd/config. Its live-input CLI and generated protocol schema
were inspected independently. `thread/queue/add` requires `threadId`, `clientUserMessageId`
and input; `thread/queue/start` is separate. The similarly named `thread/attachment/add`
stores an attachment on a thread and must not be misreported as terminal attachment.

Agy's official headless documentation says approval-required actions are handled by policy,
with no interactive prompt. Stream input is a user-message interface, not a documented
permission-response interface. It also distinguishes process-per-resume from a persistent
stdin conversation. Native permission policy and exact version remain relevant even when
a run returns success. Source:
[Agy headless mode](https://www.antigravity.google/docs/cli/headless/).

## Bounded probes and retained evidence

The no-model probe gave each new ACP process a 20-second / 4-MiB budget and cleaned up
only its owned process group. Claude, Codex and Grok all created new sessions. Claude and
Grok loaded their own empty sessions. Codex's empty-load failure is retained. Cleanup
reported no error for all three. These probes did not send a model prompt.

The permission probe used one prompt per fresh disposable session, a 90-second / 4-MiB
budget, and selected no allow option. Claude emitted `allow-once`, `allow-with-updates`
and `reject`; the client chose `reject`. The absent target and completed turn were observed
in 8.550085 seconds. Codex's 11.836889-second result had no permission request and a created
temporary target; it cannot prove approval handling. Grok stopped after 5.002227 seconds
on a diagnostic parser error, before a permission verdict. All three cleanup results were
null. Failed or vacuous tests remain unqualified.

Private artifacts are intentionally not a portable qualification corpus:

| Artifact | SHA-256 / role |
|---|---|
| `coord-runtime-empty-session-results.json` | `6f2557c129feb6f17e741923d81f52f44d16c80798c2d79685775479c73b21eb` |
| `coord-runtime-permission-results.json` | `7b7648290278c08443068deb7e97ab0c187002988f336ab8c84e37f4f22f066a` |
| `coord-runtime-empty-session-spike.py` | Bounded disposable-session reproduction; permission mode is an explicit separate invocation. |
| `coord-runtime-*-help.txt` | Saved local CLI help, including Codex queue and Grok leader modes. |
| `coord-runtime-codex-schema` | Generated installed app-server schema; no model or existing session was accessed. |
| `coord-runtime-live-grok.json` | `4727c59bd2c2fc41680aa264c96bbcf60577d00dd2bf2aa00239e641dac151de` |
| `coord-runtime-live-codex-ws.json` | `ab99a05289496ddfe10dbff8851fb725d6f23bbf9c4718ec5441476365237641` |
| `coord-runtime-live-codex.json` | `ce39cf971605a4418aba95f6f7c8cce76b532fe009f8735d7d9ceffc921f5b09`; failed diagnostic framing attempt, before session creation. |
| `coord-runtime-live-codex_proxy.json` | `e4b1a1b7cccf0c270559fe6969807a5a52aac5752853ca805f4f3b3077788e57`; native byte proxy did not answer JSONL within 20 seconds. |
| `coord-runtime-live-codex_proxy-ws.json` | `45498c4acffb62ede4c0bce2b835fbc429fc2376a4a93bdfc0af8bf688694536`; despite the retained filename, this is a successful direct second WebSocket metadata client. |

## Disposable live-input measurements

The Grok leader used an explicit fresh socket and `--relay-on-demand --no-auto-update
--no-exit-on-disconnect`. Both stdio clients used `--leader --leader-socket <same socket>`
with native default permission mode. Client A created a session and remembered a unique
token. Client B loaded that session, recalled A's token and remembered a second token.
Original client A then recalled B's token. All three results were `end_turn`, both clients
received streamed updates, and both clients plus the leader were still alive before owned
cleanup. The attempt took 16.6188 seconds and read 335,178 bytes. The load response carries
identity in `_meta.sessionId` and cwd in `_meta["x.ai/sessionDetail"]`; its top-level
`sessionId` is absent. This qualifies shared-leader addressing, not attachment to a
standalone Grok process started without that leader.

The Codex probe created an explicit fresh Unix-socket app-server and a controlling
WebSocket client. The thread used `read-only` sandbox and `on-request` approval. After the
first turn remembered a token, a separate native `codex queue` command addressed that
thread through the same endpoint. It exited zero, the queued turn automatically started,
and it recalled the first token while storing a second. The original controlling client
then started a third turn and recalled the second token. All three turn statuses were
`completed`; no explicit `thread/queue/start` was needed. This attempt took 14.4881 seconds
and read 19,351 bytes. The original connection remained usable throughout.

The first Codex diagnostic assumed newline framing for a Unix socket and reached its
180-second deadline without creating a session. The corrected observer uses the documented
HTTP Upgrade and WebSocket frames. This is an observer defect, retained separately from
the successful native queue result. Transport names must not be used to infer framing;
the recorded handshake and three completed turns are the control. OpenAI documents the
Unix-socket WebSocket contract and marks app-server/WebSocket experimental:
[Codex App Server](https://learn.chatgpt.com/docs/app-server).

A separate no-model metadata probe measured a second WebSocket connection to the same
fresh Codex app-server. After initialization, `thread/read` with the exact thread ID and
`includeTurns: false` returned `result.thread.id`, `sessionId`, `cwd`,
`canAcceptDirectInput: true` and idle status. The original client then read the same thread.
This took 0.2869 seconds and read 7,015 bytes; the returned CLI version was 0.155.1.
Attachment can check exact ID, cwd and direct-input eligibility on that endpoint before
queueing. A preceding `codex app-server proxy --sock <socket>` experiment did not answer
JSONL initialization within 20 seconds. Its help advertises byte forwarding, not framing
conversion; do not depend on it as a JSONL adapter without further evidence.

Both live attempts had a 180-second / 4-MiB bound and terminated only their own process
groups. These probes establish supported endpoint/session combinations. They do not locate
or attach every already-open terminal, prove concurrent conflicting writers safe, or
authorize a new coordinator to take ownership of another session.

## Smallest transport extension

Reuse the existing bounded wire and sequential turn loop. Add keyword-only
`next_prompt(remaining_seconds)` returning text, `None` to wait or `False` to close;
`permission_handler(request, remaining_seconds)` returning an offered option ID or `None`
to wait; and `max_turns` capped at eight, including the initial prompts. Defaults preserve
the finite prompt list and immediate permission denial. Closing must be explicit when the
last available turn finishes; waiting or another prompt at that limit is blocked.

An optional keyword `session_id` requests ACP `session/load` instead of `session/new`.
The agent must explicitly advertise `loadSession: true`; Agy and additional file-root
grants are refused for this path before spawning. Replay updates must match the requested
identity, present response identities must agree, and no permission handler runs before
the load succeeds. A reported Grok session-detail cwd must match the requested cwd.
Live attachment passes `require_loaded_cwd=True`, which requires both exact session ID
and cwd in native session-detail metadata before any prompt. The default generic load
retains optional metadata; the result exposes only `loaded_cwd_verified`, not the raw cwd.
Failure cleanup never sends cancellation to any loaded existing session: ACP cancellation
is session-wide, and this client cannot prove it owns the shared backend's current turn.
Only the owned client process is terminated; backend work may continue. Loading emits
`session_loaded`. Endpoint validation and live-leader
authority remain caller responsibilities; the transport does not claim generic attachment.

The private request object contains `sessionId`, `requestId`, `requestSequence`, `toolCall`
and `options`. The sequence increments per request, not per poll: a native agent may reuse
an RPC ID, and a previous once-only approval must not authorize the later request. Polls
receive equivalent isolated data so callback mutation cannot create an offered option.
Only `allow_once` grants; persistent allow options are rejected. The runner checks current
authority immediately before returning a selection. It also fences every dynamic prompt.

Callbacks are trusted, cheap polls. Their elapsed time is charged to the run; arbitrary
blocking Python code cannot be preempted. Between polls the wire still drains bounded
output and checks cancellation/deadlines. Bodies stay private, while public events contain
state, counts and local action IDs. Agy rejects an interactive handler before spawning.

Record `prompts_started` before a prompt observer or queue action can fail. This is a
conservative retry floor, not proof that bytes were delivered. Any possibly dispatched
prompt prohibits automatic retry. Startup retries belong to the runner and must share
the original resource budget and recheck leader/profile/checkout state.

Independent source review caught a shutdown hazard: flushing arbitrary queued data could
send a prompt or approval after cancellation. Real subprocess regressions reproduced both
cases. Cleanup may flush only a tagged cancelled permission response queued while output
was empty, followed by session cancellation; it never flushes a queued prompt or approval.

The callback slice passed 55 real-process tests and killed four targeted mutations. The
load extension then passed 60 tests after recorded red failures for missing loading,
premature permission handling, cwd mismatch and cancellation of an existing session.
The final strict-cwd flag passed all six focused load tests after six red missing-API
errors. Integration and generated-surface gates belong to the coordinating Owner.

The fresh-session `mode_id` option selects exactly one literal advertised native mode
before the first prompt, using `session/set_mode`. It is incompatible with loading an
existing session or the Agy adapter. Omission preserves the native default. Missing,
unknown, duplicate or malformed mode advertisement and a failed mode response prohibit
prompt dispatch. The mode slice passed 65 transport tests after three red tests with
ten missing-API errors.

## Remaining qualification

The Owner should retain exact endpoint and session identity checks around the measured
Codex queue and Grok shared-leader paths. Claude Remote Control and Agy's interactive UI need
separate native integration contracts; neither should be simulated by terminal keystrokes
or relabelled resume. Grok still needs a non-vacuous native approval profile. Codex's explicit
mode/callback observation does not replace per-checkout policy and hook qualification.
No general unattended authorization follows from this research note.

## Native approval-policy follow-up

Codex ACP 1.12.0 defaults to its `agent` mode, which routes approvals to automatic review.
Its advertised `read-only` mode instead sets approval policy `on-request`, reviewer `user`
and a workspace-write sandbox that still permits temporary-directory writes. This explains
why the earlier temporary target produced no callback. A new diagnostic targeting a unique
canary under the research worktree emitted a real edit permission with the exact path.
It was intentionally interrupted without approval while explicit native mode selection
was added to the public transport API; no canary remained. Its retained result hash is
`0ecde7afaddf86a4d3a2e1a001946bd3ee38cb58e37234b18ee965b319d822cc`.

The final Codex attempt used the shipping transport public API with `mode_id="read-only"`,
without the diagnostic mode-injection wrapper. The adapter advertised that mode and
accepted `session/set_mode` before the prompt. A native edit update exposed the exact
single canary path, `oldText: null` and `newText` containing `COORD_ONCE_CODEX_20260921`
followed by one newline.
The callback referenced the same tool-call ID and path. After inspection, the reviewer
selected only the offered `allow_once`; the persistent-allow option was not used.
The transport completed with one request, one allowance, zero denials and null cleanup
error. The probe independently read the exact expected bytes and removed its canary.
Total duration was 62.591083 seconds including the manual review interval; stdout was
37,255 bytes, stderr zero. This is a non-vacuous native callback/once-approval observation.
It proves this explicit policy and finite operation, not unrestricted unattended safety.

Retained private evidence: `coord-runtime-once-codex-shipping-result.json`, SHA-256
`012211895b6b5d15426099a433eaf8116d58ba65549865a17dc123dc6bd0fabf`;
the passive wire transcript SHA-256 is
`ec77aa9fdc5cfddedd85080111509a4e60fb328af7d5716adda53d26d427ede5`.
The measured transport source SHA-256 is
`add1f4e2b923638063b0f0a817e15e4e5873f474bd1d2dc4b31d3fbd265f35e4`.
The runner's optional mode validation and pass-through were independently reviewed:
the entire runtime policy remains in the admitted worker/manifest fingerprint, omitted
mode does not select a default, and unsupported modes block before prompt dispatch.

Grok's shipping transport used native `--permission-mode default` and a unique canary
outside its temporary runtime workspace. It wrote the exact requested content, completed
in 22.127213 seconds, and emitted zero permission callbacks. The file was read back and
removed. This is another **unqualified approval profile**, not an allow-once success.
The local Grok user configuration sets `ui.permission_mode` to `always-approve`; this
attempt demonstrates that the selected agent-stdio invocation did not establish ask mode.
Its result hash is `2d95b97ca90b250034a660c57b49d63b7aafe1578e7e8851ff9128fc826dce36`.

Installed native documentation explicitly excludes permission settings from the soft
`GROK_CONFIG` overlay. A no-model `grok inspect --json` test confirmed that a proposed
`ui.permission_mode` overlay was ignored. `GROK_DEFAULT_SELECTED_PERMISSION` selects the
initial approval cursor, not enforcement mode. Neither can be promoted to a tested ask
profile. The ignored-overlay evidence hash is
`d72f83dd62837f08531d16ab1ff09e9f92e155d213684b8e58cbb673f389adfd`.
No global configuration or alternate home/profile was changed. Grok interactive approval
remains gated pending a separately established native permission-profile contract.

On 2026-09-21, a fresh disposable probe placed `--permission-mode default` before the
`agent --no-leader stdio` subcommand, which is the CLI's documented option position. The
transport completed one turn in 7.786403 seconds, reported Grok 1.0.34, emitted zero
permission callbacks and zero native denials, and wrote the requested `PROBE` canary.
The canary was read back and removed. This rules out an argument-order mistake for the
current installed profile; it still does not qualify interactive approval.
