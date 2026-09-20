---
id: kb-acp-compatibility
title: "ACP compatibility spike — Grok-driven evidence"
type: knowledge
status: active
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, evidence, spike]
links:
  - { to: spec-acp-coordination, rel: documents }
  - { to: kb-multi-agent-coordination, rel: relates-to }
review-by: "2026-12-20"
review-suggested: []
summary: >-
  Sanitized observations from a Grok-driven, bounded local spike of Grok native ACP,
  Claude and Codex ACP adapters, and Agy's native stream. Captures exact version and
  scope limits, project trust, permission discrimination and the reproduction scripts.
---

# Grok-driven ACP compatibility evidence

Read the [full specification and measured matrix](../../specs/acp-coordination.md)
or its [offline HTML rendition](../../specs/acp-coordination.html) first. This is a
2026-09-20 macOS experiment, not a production client or cross-platform certification.

## Evidence inventory

- [observations.json](observations.json): six bounded observations, selected capability
  and mode responses, final replies, timings, named hook events and file-presence oracles.
- [protocol-evidence.jsonl](protocol-evidence.jsonl): minimal actual tool/progress,
  permission request/rejection and cancellation events. Provider/account inventories,
  arbitrary extension payloads and model reasoning are excluded.
- [grok-driver-evidence.json](grok-driver-evidence.json): Grok's two driver results and
  bounded-process metadata. The first driver returned successfully. The follow-up driver
  reached its three-turn cap and exited 1 after producing completed target control files;
  no successful final response is claimed for that wrapper. The control records were
  inspected independently. No direct Codex fallback was used for a target probe. Driver
  cost is driver-only, not the sum of child costs.
- [manifest.json](manifest.json): versions, file hashes, limits and experimental caveats.
- [probe.py](probe.py), [retry.py](retry.py), [run-driver.py](run-driver.py): exact local
  experiment programs; paths describe the machine/run that generated the observation.
- [package.json](package.json) and [package-lock.json](package-lock.json): pinned adapter
  environment, installed only in a temporary directory with lifecycle scripts disabled.
  The [observed installation lock](observed-package-lock.json) retains npm's original
  prefix-relative paths. The portable reproduction lock normalizes only package paths and
  root metadata; dependency versions, registry URLs and integrity values remain intact.
- [capture-evidence.py](capture-evidence.py): allowlist export used to separate public
  operational evidence from local raw diagnostic streams.
- [render-qa.json](render-qa.json): independent browser measurements and final HTML hash;
  desktop and narrow viewport checks include document width and internal anchors.
- [verify-evidence.py](verify-evidence.py): non-vacuous permission/completion verdict
  controls, artifact hashes, privacy exclusions, full HTML criteria/link checks and
  version-bound browser geometry evidence.

## Method and negative oracles

Each target received a new disposable Git repository, one instruction canary and one
read sentinel. The first prompt did not contain the instruction marker. The second
prompt asked for a nonce supplied in the first. The client advertised no filesystem
or terminal service. Permission callbacks selected `reject_once` when offered, otherwise
`cancelled`; there was no approve response. A denied file was checked on disk independently
of model prose. A permission test with **zero callbacks** was explicitly not called a
successful refusal. The original Grok/Codex local writes remain recorded; they are not
hidden by the later Codex external-path negative control.

Grok's same-fixture native control plus `grok inspect` showed untrusted project state,
no local instruction discovery, and no local hooks. That discriminates project setup
from an ACP-specific instruction regression. No trust setting was changed. Whether
existing trusted-repository policy covers new sibling worktrees remains unqualified.

Codex's first file-read prompt forbade shell; it correctly reported no dedicated read
tool. The control permitted a native read/shell tool. An actual `exec_command` read
returned the sentinel at exit zero. An external edit then generated a real ACP request,
which was rejected; the outside-workspace file remained absent. The mode called
`read-only` in adapter 1.12.0 maps to `workspaceWrite`/`on-request` in its source, so a
local edit is compatible with that observed policy.

Claude's adapter fired SessionStart, UserPromptSubmit and Stop canaries and obeyed the
fixture instruction. These observations do not prove the pack's complete PreToolUse
ownership veto or owner-review Stop-block semantics. The adapter uses its SDK runtime,
not the separately inventoried installed Claude CLI. Codex hooks were not configured
in the fixture. Agy's PreInvocation and Stop hooks fired through native stream-json
with `--add-dir`; its denied write reported an existing local review hook deadline,
not a demonstrated universal property of plan mode.

Cancellation was sent 0.25 s after starting an ACP prompt; all three returned `cancelled`.
This is an early in-flight prompt test. Agy was cancelled by owned-process termination;
no ACP or graceful per-turn cancellation capability is claimed. Optional ACP loads
replayed the same process's session; restart/load/continuation and arbitrary existing
terminal attachment were not tested. Pack task handback and integration are release
gates still to execute, separate from these protocol outcomes.

## Reproduction scope

The exact scripts are retained for audit, not installed into the pack. To reproduce on
another machine, make a fresh temporary run directory; adjust the script's fixture,
driver-worktree, pack-script and Codex executable paths; install the pinned lockfile
there using `npm ci --ignore-scripts --no-audit --no-fund`; use normal authenticated
harness installations. Inspect the scripts and current CLI contracts first. Run from
an assigned isolated Grok worktree. Preserve profile/trust differences as observations;
do not disable a permission or trust check to turn a blocked cell green.

The in-memory queue is unbounded and the byte cap applies after consumption; a long
unterminated line is likewise not a hardened boundary. POSIX process-group cleanup is
not a proof of cross-platform descendant containment. No production code should import
these scripts. The production runner must enforce bounds before buffering and reuse its
established process containment. Raw diagnostics stay local and must not be committed;
only this allowlisted export is the durable experiment record.
