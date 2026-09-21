---
id: proof-native-profile-controls
title: Native profile control source and Agy diagnostic evidence
type: proof-pack
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, hooks, proof, agy]
links:
  - { to: design-native-profile-controls, rel: implements }
  - { to: design-multi-harness-runner, rel: implements }
review-by: "2026-12-21"
summary: Red-first source evidence for native ownership adapters, observable bounded Stop and final Owner-decision handback, plus two finite Agy profile diagnostics. Final integrated four-harness qualification remains separate.
---

# Native profile controls

The source adds a final worker Owner-decision fence independently of native Stop limits.
It also supplies explicit Grok/Agy native write adapters and a separate Codex Stop entry.
The existing Codex apply_patch definition is unchanged. New Stop trust is pending native
user review; no trust database, global permission file or model default was changed.

## Claims and red-first controls

| Claim | Evidence and oracle | Red observed | Confidence / limit |
|---|---|---|---|
| Complete transport plus file receipt cannot clear an open worker decision | `RunnerTests.test_open_owner_decision_blocks_ready_even_with_verified_receipt`: installed runner, actual git/worktree/ref, real protocol peer; receipt exists but result blocked | Original runner returned ready, exit0 | Verified deterministic composition; semantic Owner acceptance remains separate |
| Unreadable or malformed state cannot appear empty | strict projection tests: bad JSON, nonobject, unknown transition, missing resolution, self-resolution, depth/size/symlink/FIFO | Original projection accepted malformed/self-resolved terminals; original runner accepted malformed ledger | Verified bounded negative controls; same-user ledger sabotage is not sandbox containment |
| Native path policy uses the host's actual target | Native Grok/Agy held/free/mine/escape tests, Agy misleading generic field and nested cwd | Missing native hosts; generic file_path masked held TargetFile | Verified subprocess controls; live Grok native argument contract still qualified separately |
| Stop emission is observable without model prose | Codex refusal, allowed ruling closure, loop guard, malformed state and identity tests assert existing ledger receipts | No Codex adapter or Stop receipts | Script output observed; host honoring it requires runtime evidence |
| Local hook opt-ins survive source refresh | Actual PowerShell sync and pack installer tests preserve custom name, update managed names, repeat idempotently, reject malformed JSON without overwrite | Real sync deleted custom entry; installer retained stale managed section / missed conflict | Verified deployment composition; fresh installs omit ownership opt-in |
| Standalone installer still diagnoses a stale copy | Existing stale-applier/first-hop suite | New eager helper import broke standalone bootstrap | Shared pure merge moved into standalone installer; CLI helper calls it without duplicating policy |

Initial focused native/runner suite: 63 tests passed in40.504s. Deployment suite:4 tests
passed in12.473s. Bootstrap plus actual sync:11 tests passed in12.959s. Broader affected
suite exposed the standalone import regression and an expected unsynchronized install;
both were addressed before full release gates. Final bundle/reviewer result is recorded
below after completion. No gate exit is used as evidence of native host enforcement.

## Agy finite diagnostic

Two serial attempts used a fresh assigned diagnostic worktree based on6711dba872e1,
the existing deployed transport, explicitly hashed uncommitted guard source, unchanged
user settings/hooks and existing credentials. They are diagnostic, not final installed
qualification. Each was bounded to180s and4MiB; no retry followed the targeted second
attempt. Raw files remain private; the committed [sanitized evidence](../knowledge/acp-compatibility/agy-native-controls-diagnostic.json)
contains their SHA-256 hashes and measured fields.

| Attempt | Selected mode | Native reported permission_mode | Result | File oracle |
|---|---|---|---|---|
| Normal | no mode override | request-review | blocked / permission_denied,14.396644s | Ordinary receipt absent; ownership hook allowed target |
| Targeted edit profile | per-process accept-edits | request-review | ordinary turn complete, then native_tool_error on held replacement,25.071701s | Exact ordinary bytes present; leased canary unchanged; allowed/refused native rows |

The second native error explicitly reports `tool call denied by pre-tool hook: REFUSED`
with the current holder. The transport at this diagnostic base labels it generic
`native_tool_error`, so native_denials remains0. That counter is not the oracle for this
new hook error shape. The native error, matching refusal row, live lease and unchanged
bytes establish the refusal. No later prompt was sent. The transport owner receives this
new envelope for its separate bounded classification review.

Both records show unchanged captured settings/executable hashes. The actual hook process
cwd is `<assigned-worktree>/.agents`, with matching environment session and host; the
native TargetFile is absolute. Do not claim cwd equals the worker root. Both native init
messages report request-review even though the second command selects accept-edits;
report exact argv and observed behavior without inventing an effective-mode field.

Existing user hook dependencies to bind: `~/.gemini/config/hooks.json`,
`~/.gemini/config/config.json`, `~/.gemini/antigravity-cli/settings.json` and the configured
`~/.cargo/bin/agy-auto-approve` executable. The prior user reviewer itself returned allow
for a denied write; the native write policy is a distinct layer. No hook was disabled,
no force/skip permission flag was used, and no persistent mode changed.

Recommendation: use the measured per-invocation file-edit profile for the final Agy
qualification, preserving native ownership denial and existing shell permission rules.
Require actual loaded-hook evidence and canary outcomes on the reviewed integrated
commit. Grok Stop metadata versus documentation, Codex new Stop trust, cancellation,
Owner ruling/closure and final composed handback remain in the parent's full matrix.

## Release and independent review

Parent independent Security/Test/Simplifier source review passed after terminal-row,
standalone-bootstrap, documentation and event-identity corrections. The full release run
passed the installed-source Python gate:1181 tests,12 skips,375 subtests in147.53s, plus
Node core contracts and offline render/accessibility checks. Its only remaining gate
finding was the proof-coverage registry's missing direct reference to the new merge CLI.
A meaningful direct CLI preservation/idempotence/malformed/symlink test was added and
passed; the consistency gate is now clean. Final metadata gates run after audit/proof
regeneration; source code is unchanged after that full test pass.

Three disposable mutants were killed by the relevant controls: removing the open-decision
fence, accepting decision-requester self-resolution, and omitting managed hook refresh.
The real shared historical request corpus also returned checked with no open requests
for this author, preserving the ruled request history. The final metadata-gate log and
source commit are reported in the handback rather than guessed in advance.

Parent performs integration and final runtime qualification; this proof does not attest
unattended readiness. Retain the dirty diagnostic worktree and private raw records for
review; no automatic deletion or remote push occurred.
