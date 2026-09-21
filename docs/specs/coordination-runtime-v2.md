---
id: spec-coordination-runtime-v2
title: "Bounded unattended coordination and interactive control"
type: spec
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, runtime, permissions, sessions]
links:
  - { to: spec-multi-harness-launch-and-monitor, rel: refines }
  - { to: spec-acp-coordination, rel: refines }
  - { to: plan-coordination-runtime-v2, rel: relates-to }
review-by: "2026-12-21"
review-suggested: []
summary: "Runtime control for qualified workers, explicit permission decisions and native live session attachment."
---

# Bounded unattended coordination

## Functional specification

The operator asks either Claude or Codex to coordinate work without manually relaying
every follow-up. Routine execution continues within the admitted contract. A new tool
permission request pauses for a concrete decision. It does not become approval merely
because execution is unattended. The historical proof stays historical; new runtime
qualification is separate and bound to the actual profile.

The bounded context remains coordination execution. A Run owns one finite resource
budget and qualified Worker attempts. A Prompt admission identifies one completed
compilation; a Permission request identifies one native request and its exact offered
options. Decisions cannot authorize another request. Live attachment addresses a known
native session, without changing its owner, cwd, trust or permissions. Resume of stored
history is a different capability and must be labelled as such.

| ID | Acceptance criterion |
|---|---|
| AC1 | Reconcile all three pushed feature tips without losing fixes already in main; record the resolution and push a linear main equal to origin/main. |
| AC2 | Explicit unattended mode runs qualified workers within finite time, bytes, turns and retry bounds. It retains leader/config checks, request fences and Owner review. |
| AC3 | After the initial brief, an Owner can enqueue a completed compilation while the run is alive. It reaches the same worker session exactly once at a turn boundary; finish closes input. |
| AC4 | For ACP permission requests, the operator sees the exact native action/options in a private local view and can choose one offered `allow_once` or reject. Missing, malformed, stale or mismatched decisions cannot approve. Native policy remains authoritative. |
| AC5 | Transient failures before any model prompt dispatch can retry automatically within the original budget after successful cleanup and unchanged checkout/config/leader. A possibly executed prompt, permission denial, policy drift or cancellation never retries automatically. |
| AC6 | An existing live terminal session is addressable through a verified native session-input mechanism, by exact session identity and explicit compiled prompt. Unsupported harnesses fail with a concrete capability explanation; resume is never reported as live attach. |
| AC7 | A fresh single-branch clone verifies historical evidence without private temporary files, local archive refs, installed model credentials or a network fetch of hidden history. Original Git hashes, parents, ancestry and receipt contents remain checked. Corruption fails. |
| AC8 | Public events distinguish transport completion, blocked permission, retry, input closed, evidence verification and review readiness. Raw prompts and native action bodies stay out of committed telemetry. |

Platform expansion is tied to these runtime capabilities. This slice does not claim
Windows process containment until measured. It does not install a terminal multiplexer,
send arbitrary keystrokes into an unrelated shell, elect a leader, or bypass approval.
Official/native alternatives are researched before adding a custom transport.

## UX specification

CLI, task archetype: serial action/confirmation with a parallel status view. Prepare →
qualify → run unattended; from another terminal use status, enqueue, permissions and
finish. Pending permission output names run/worker/request and a local detail path.
The decision command requires that exact request ID plus an offered option ID. A rejected
or expired request stays visible. An idle mailbox is shown as waiting, not completed.
The user can cancel the process; cancellation stops owned children and preserves work.

Live attach requires an explicit harness, exact native session ID and compiled prompt.
Queue acceptance is reported as queued, never as evidence of work completion. Existing
session ownership and permissions are not inherited from a newly qualified worker.

## UI specification

Terminal JSON/text only; use existing CLI error/remedy conventions and no color-only
meaning, animation or truncation of load-bearing IDs. Empty/loading/error/success states
are `waiting`, `permission_pending`, `blocked`, `queued` and `ready_for_review` with a
reason and next command where relevant. Native action detail is read only on request.
No graphical design tokens apply. HAX correction/control and explicit Governors apply:
cancel, reject, inspect, and distinguish queue acceptance from completed work.

## Confidence and validation

Verified: all four installed runtimes completed dynamic second prompts. Claude produced
a real permission callback and completed an inspected one-time file edit. Disposable
Codex app-server and Grok leader sessions accepted input from a second client while the
original controller remained usable. These observations do not qualify arbitrary open
terminals or transfer a backend's ownership/environment. The linked runtime proof records
exact versions, remaining permission limitations and reproducible offline checks.
Independent reviews challenged and retested hostile/stale control records, interruption,
wrong worktree identity and ambiguous dispatch. No deployment-wide qualification follows
from a successful local transport canary.
