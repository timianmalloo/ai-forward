---
id: design-native-profile-controls
title: Native profile controls and final decision handback
type: design
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, hooks, ownership, acceptance]
links:
  - { to: design-multi-harness-runner, rel: refines }
  - { to: design-native-ownership-enforcement, rel: refines }
  - { to: spec-multi-harness-launch-and-monitor, rel: implements }
  - { to: adr-0010-enforcement-topology, rel: depends-on }
review-by: "2026-12-21"
summary: Reuse the native ownership guard for Grok and Agy, add a separately trusted Codex Stop hook, and enforce a final worker decision-state fence independently of bounded native Stop behavior.
review-suggested: []
---

# Native profile controls and final decision handback

Goal: complete the missing control seams for the four-harness end-to-end qualification.
Done when reviewed source and red-first tests support native guards, observable bounded
Stop behavior and fail-closed runner handback, with a finite Agy write diagnostic.
T2; no nested delegation. No transport edits, shell sandbox, automatic semantic approval,
dynamic prompt loop, global trust writes, blanket permission changes or remote push.
Parent performs installed-source release gates and the final runtime qualification.

## Model, invariants and surfaces

Grounding: launch specification AC3/5/7/10 → runner design → native ownership design →
ADR-0010. The existing Request aggregate owns one request identity and append-only
transition facts in `requests.jsonl`. Session identity remains `AGENT_SESSION`; native
payload identities and cwd are untrusted. Final acceptance is a derived observation,
not a new decision store, ruling or workflow engine. Existing Owner ruling authority
and explicit request-expiration semantics remain unchanged. Expiration is not a ruling
and never substitutes for semantic Owner acceptance in qualification.

Invariants:

1. Every supported native edit is checked against the complete existing lease policy,
   including actual cwd, lexical/physical paths, aliases, exclusions and unreadable state.
2. No worker becomes `ready_for_review` while its sent decision requests remain open,
   or while the final decision state cannot be read and validated.
3. Native Stop feedback is bounded and independently observable. A host's passive event
   is never labeled an enforced refusal. The runner fence remains necessary after the
   native loop guard permits a stop.
4. Hook approval is not inferred from config installation. The previously approved Codex
   apply_patch definition remains unchanged; the separate Stop entry needs native review.

Surface list: native envelope → existing policy → native response + per-path decision
facts → explicit project hook config → actual edit evidence; Request facts → strict
decision-state reader → Stop receipt / runner final outcome → status/manual remedy.
Pack source and deployed copies reach the same commit before final live evidence.

## Contracts and smallest correct changes

Reuse-before-write wins the solution ladder: Adapter additions to `coord-core.py hook`,
one bounded strict projection over the existing request fold, and one final runner check.
No dependency, daemon, new authoritative store, new coordinator role or permission broker.

### Native edit adapters

Claude and approved Codex behavior stay intact. Grok receives camelCase `toolName` and
`toolInput`; its documented deny output is top-level `decision` and `reason`. Agy receives
`toolCall.name` and `toolCall.args`; known file tools are `write_to_file`,
`replace_file_content` and `multi_replace_file_content` with `TargetFile`.
Normalize only named supported shapes; malformed recognized writes deny. Resolve paths
from the real process cwd; do not let payload cwd/workspace fields redirect ownership.
Unknown native state maps to deny for Grok/Agy as it does for Codex. A free Agy path must
not create a blanket permission grant: return no permission override and validate neutral
successful hook output in the finite diagnostic. If the installed CLI cannot compose a
neutral guard with existing permission policy, report that prerequisite instead of
quietly using `decision:allow` to weaken policy.

Install a specific Grok write matcher and Agy named ownership bundle. Grok also discovers
Claude settings, so duplicate discovery must be observed at qualification; repeated checks
may produce repeated facts but cannot grant a denied edit. Source command wrappers use
fixed quoted shell syntax only, runtime cwd and environment identity, and no payload eval.

### Decision projection and final fence

Deployment preservation is a named-bundle merge, shared by `sync-pack.ps1` and
`pack-apply.py`: source-owned names refresh, names absent from source survive, malformed
existing JSON refuses without overwrite. Fresh consumers receive no ownership guard.
This repository's Agy `ownership-guard` is its explicit opt-in. Grok uses a separate
repo-owned `.grok/hooks/coord-ownership.json`, discovered by its documented `*.json`
convention and untouched by the managed `ai-forward.json` replacement. This is approved
scope expansion to deployment preservation, not a new policy store or universal guard.

Add `decision_request_state(root, session)` returning `open_ids` and `checked` plus a
stable failure code. Validate a bounded regular JSONL ledger before calling the existing
fold: reject malformed JSON, non-object rows, unsupported transition shapes and missing
identities; I/O, decoding and size errors are unchecked. An absent ledger is empty only
inside an initialized coordination root with its existing log directory. Never interpret
an unreadable ledger as empty. Unknown transitions and duplicate identities are unchecked.
The bound is 8 MiB; no blocking special file or symlink is opened as a ledger. Exceeding
the limit gives a repairable blocked result, not silently truncated state. No bodies,
prompts, local exception strings or arbitrary ledger fields enter status telemetry.

After transport completion and independent receipt verification, the runner reads this
projection for the exact assigned worker, rechecks cancellation/leadership, and emits
`blocked` with `RUN-DECISION-OPEN` or `RUN-DECISION-NOT-CHECKED` when necessary. A finite
list of at most 32 validated IDs is included with total and truncation fields. Only an
empty checked state and final exact holder/epoch fence permit `ready_for_review`.
The stopped worker cannot create more requests after the check; independent external
edits after the observation remain outside an atomic transaction guarantee. The final
state is an observation at this seam, not semantic acceptance or automatic integration.
Preserve receipts when blocked and retain the manual brief. Existing immutable-attempt
behavior applies after a real Owner ruling; no resume feature is introduced.

### Native Stop and receipts

Claude keeps its existing one-continuation loop guard. Agy retains at most two refusals
per native stop sequence. Codex uses documented `decision:block`/reason JSON and checks
`stop_hook_active`; successful nonblocking responses use valid JSON. The new entry is
separate from unchanged apply_patch and is inert until its exact native trust approval.
Grok's official page calls Stop passive, but the measured installed 1.0.34 initialize
metadata advertises `stop`/`subagent_stop` as blocking events. Retain its existing exit-2
requested refusal; actual host enforcement remains unqualified until the native probe.
Copilot is outside this four-harness qualification; preserve its existing behavior.

Use the existing `append_event` writer for one `owner-review-stop` fact per evaluated
invocation: environment session, actual cwd, host, event, checked flag, bounded open IDs,
result (`refused`, `allowed`, `loop_guard`, `not_checked`) and timestamp. `refused` is the
script's requested decision; it is never alone proof that the host enforced that decision.
No raw messages/tool arguments. Event counts are additive; state/IDs are nonadditive
observations, not current-state columns. Missing identity/root cannot be attributed and
therefore emits no invented receipt. Telemetry failure never fabricates success and does
not change the pre-existing bounded native Stop behavior; final runner state fails closed.

## Finite Agy diagnostic

Verified local help accepts `--mode plan|accept-edits`. Official documentation says plan
adds read-only planning instructions, while headless workspace writes normally autoallow.
Existing user config has an enabled `agy-auto-approve` PreToolUse hook. Preserve and hash
all relevant settings/hook definitions; do not invoke its update/config-edit actions.

First try a fresh isolated cwd/session with `--add-dir <cwd>` and stream JSON, omitting
the current plan override. One prompt requests one harmless native file write; bound the
attempt to 180 seconds and 4 MiB. Inspect native tool evidence and actual bytes, not prose.
At most one targeted retry follows a diagnosed cause. No broad write grant, skip-permission
flag or global change is permitted. If a narrow resource grant is genuinely required,
prepare the exact file/profile/definition for the Owner to review rather than applying it.
This is diagnostic, not final qualification; parent re-runs on the integrated source base.

## Failure, security and test union

## Adversarial analysis (STRIDE-lite)

| Boundary | Threat | Disposition |
|---|---|---|
| Native arguments → target | T/E: generic aliases hide actual native target | Mitigate: Agy uses absolute TargetFile only; Grok checks all recognized target spellings. Nested-cwd and misleading-field tests. |
| Decision facts → final readiness | T/E: malformed or self-resolved terminal hides open decision | Mitigate: strict bounded projection validates terminal shape and rejects decision requester self-resolution; historical untyped remains open. |
| Config source → installed named hooks | T/E: regeneration removes local guard | Mitigate: shared named-bundle merge and actual sync/installer regression. Malformed input leaves target unchanged. |
| Native Stop → host control | E: emitted refusal mistaken for enforcement | Detect through native runtime control. Script receipt proves emission only; runner independently blocks final readiness. |

## Privacy analysis (LINDDUN-lite)

| Data flow | Finding | Disposition |
|---|---|---|
| Stop and decision projection → local facts/status | Linkability of session/cwd/request IDs | Existing local ledger retention; validated IDs capped32 plus count; no question/body/prompt/config contents. Tests assert sentinel absence. |

## Test union and residual scope

STRIDE: payload identity/cwd spoofing is denied by environment identity and real cwd;
lease alias/tampering protection is reused; malformed/fifo/oversized request state blocks
handback; native trust remains explicit. Shared same-user ledger tampering and shell
bypass remain ADR-0010 limitations, not newly promised containment. LINDDUN: logs reveal
local session/path/request identifiers only; no user content, credentials or raw tool data.
No new graphical UI or visual design; existing JSON/status/manual brief is the user surface.

Red-first contract cases:

- Native Grok/Agy free/mine/held edits, unknown state, malformed args, outside cwd and
  payload spoofing; existing alias/move suite continues to guard common normalization.
- Codex separate Stop refusal, valid nonblocking JSON, loop guard; unchanged apply_patch
  definition; Grok requested refusal separate from host-enforcement evidence.
- Stop receipts for refusal, ruled closure, bounded loop, unreadable store and no identity;
  verify bodies are absent and events use the existing writer.
- Deployed runner + real git/worktrees + protocol fixture: open decision blocks despite
  valid receipt; another worker's request does not; real Owner ruling permits a new
  attempt; malformed/non-object/unreadable/oversized ledger fails closed; no transport edit.
- Native output/schema negative cases, exact project config parse, sanitized telemetry,
  existing runner leader/cancel/privacy tests and native path alias regression suite.

Parent is independent Security/Test/Simplifier reviewer. No source implementation starts
until this design clears. Release claims distinguish unit/composition proof, configured
hooks, trusted hooks and actual native runtime observations per harness.

## Contract sources and observation limits

- [Codex hooks](https://learn.chatgpt.com/docs/hooks): Stop continues the turn; exact hook
  definitions require review. The installed version remains separately measured.
- [Grok hooks](https://docs.x.ai/build/features/hooks): camelCase input, top-level deny,
  PreToolUse-only blocking, passive Stop and per-project trust.
- [Agy hooks](https://antigravity.google/docs/hooks),
  [execution modes](https://antigravity.google/docs/cli/modes/) and
  [headless mode](https://antigravity.google/docs/cli/headless/): native shapes and policy
  prerequisites. Neutral successful hook composition remains a diagnostic question.

Review status: parent Security/Test/Simplifier PASS, formal Owner Ruling 7 on request
`req-01M30NZ4Z1VQHG9SBMNZRKK2DK`. Runtime cells remain unqualified until the parent observes
the complete required matrix on installed reviewed source.
