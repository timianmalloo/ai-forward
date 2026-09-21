---
id: note-20260921-codex-coordination-file-roots
title: "Explicit Codex coordination file access"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, codex, acp, sandbox]
links:
  - { to: design-multi-harness-runner, rel: refines }
  - { to: design-native-profile-controls, rel: relates-to }
  - { to: coordination-end-to-end, rel: relates-to }
review-by: "2026-12-21"
summary: Native sandbox and ACP creation measurements support explicit access to individual operational ledgers, with identity-bound admission and no directory grant.
---

# Decision and goal

Goal: let an explicitly admitted Codex worker use the existing primary coordination
request, own-log and Owner-inbox writers while preserving bounded native permissions.
Done when measured adapter behavior, red-first regression controls, independent source
review and all release gates pass. T2; fan-out zero. No default permission change, extra
operational scope, new store writer, permission broker or automatic qualification.

The runner aggregate owns the immutable path set and file identity at preparation. One
identity record is one admitted operational file's canonical path/device/inode; it is not
a content snapshot. Existing append-only coordination facts remain the sole durable store.
The source-to-surface path is contract validation → prepared manifest/fingerprint → launch
and per-prompt fences → ACP creation → native per-turn sandbox → actual ledger writers.
The design and launch reference describe the same optional field and refusal behavior.

The approved execution graph is evidence → contract review → red regressions → minimum
implementation → independent source review → sync/release gates → audit/commit. Reasoning
owns the design, root provides independent review, and deterministic scripts perform the
remaining mechanics. Width one avoids competing edits; no repeated native model runs are
needed to establish this adapter contract. A failed oracle causes diagnosis, not a blind
retry. This bounded repair follows the parent coordination plan and its independent gate.

## Observed contract

Verified locally: Codex CLI 0.155.1, `@agentclientprotocol/codex-acp` 1.12.0. The installed
adapter's `readAdditionalDirectories` accepts absolute strings; its per-turn
`addAdditionalDirectoriesToSandboxPolicy` supplies them as `workspaceWrite.writableRoots`.
A config-only writable-roots setting is insufficient because the selected mode constructs
the turn policy. The adapter also passes these roots through skill discovery, so source
inspection alone was insufficient to establish file-root compatibility.

Two bounded native app-server `command/exec` calls used the installed binary's generated
`CommandExecParams` schema, which explicitly defines the same sandbox shape as thread/turn
execution. With no extra root, an existing requested ledger, existing sibling ledger, new
sibling and instruction file all refused writes; cwd workspace writes succeeded. With
one existing ledger as the exact root, only that additional file became writable. Actual
bytes confirmed the one append and unchanged neighbors. The policy disabled network and
excluded implicit temporary-directory grants. No adapter or repository files were edited.
Private evidence: `/tmp/codex-file-root-app-spike.json`; cleanup reported no error.

A separate bounded ACP initialize and `session/new` passed the same exact file through
`additionalDirectories`. Initialize identified the installed adapter and advertised
`sessionCapabilities.additionalDirectories`; creation succeeded, including skill discovery.
No model prompt was sent. Private evidence: `/tmp/codex-file-root-acp-spike.json`; cleanup
reported no error. Earlier CLI sandbox syntax probes failed before executing a canary;
they are diagnosis, not sandbox proof. Both successful probes used byte/time bounds and
owned process cleanup. These observations establish the transport contract, not final
qualification of a real repository worker.

## Admission and limits

Only Codex ACP can opt in. The list is capped at the three exact primary-store files:
requests, this worker's log and this Owner's inbox. Every admitted path is canonical,
absolute, unique and a nonsymlink regular file. Requests/inbox must already exist through
normal store use. The future worker log alone may be absent until normal worktree
registration creates it. No missing directory is created by this option. Preparation then
captures every identity; fingerprinting and each prompt reject replacement. Appending to
a ledger does not invalidate qualification. Supplied internal identity fields refuse.

An omitted option leaves existing profiles unchanged. Explicit malformed false/null values
never become omission. Native permission callbacks remain denied and sticky. This set does
not cover worker-inbox acknowledgements, broadcast mail or arbitrary other coordination
operations. No whole-directory scope is inferred from their possible future use. Boundary
checks do not claim atomic protection against a privileged actor replacing paths during
an active native turn. Final real-profile qualification remains the coordinator's job.

## Failure class and regression proof

Class: a transport omits a required narrow operational access path, then a configuration
setting is mistaken for the effective per-turn policy. Sweep: decision requests append
requests plus own log; targeted mail appends the recipient inbox and sometimes own log.
These writers use append/open, not replacement or hidden sibling lock files. Derive:
bind access identities independently of appendable content. Prevent: recorded adapter
capability admission, exact path allowlist, wire forwarding/default omission, malformed
and replacement refusals, append-stable fingerprint and retained permission-denial tests.
The parent owns the shared defect-class register; this branch does not rewrite it.

Red observed before production edits: 25 failures across seven new test methods and
their subcases, including missing forwarding and invalid access admission. The combined
runner/transport suite then passed 81 tests and 98 subtests in 43.04 seconds. A subsequent
expanded replacement test passed both first-prompt and second-prompt cases. Three isolated
mutants (drop forwarding, remove allowlist, remove identity pin) were all killed. Independent
root review read the source, contracts and native captures and observed another six tests
plus 23 subtests passing. Raw exceptions from caller-owned fences remain sanitized; some
runner replacement failures therefore use `callback_failed`, while the internal transport
check uses `file_roots_changed`. Both refuse further prompts. Final release-gate results
are recorded in the closing audit; final repository-worker qualification is still separate.
