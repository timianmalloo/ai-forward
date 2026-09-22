---
id: proof-codex-adapter
title: "Codex adapter verification"
type: doc
status: active
owner: "@timianmalloo"
tags: [proof, codex, adapters]
links:
  - { to: plan-optimize-graph-codex-adapter, rel: relates-to }
review-by: "2027-03-14"
summary: "Consumer installation, native discovery, preservation and drift evidence for revision 72."
---

# Codex adapter verification

## Scope and result

Revision 72 keeps `pack/` canonical and generates Codex surfaces through the existing installer and source-sync paths. Work is isolated on `feature/codex-adapter`, based on `21dbfeeec3de`. Commit, push and merge remain deferred as requested.

| Requirement | Observed evidence |
|---|---|
| Native skills, including references | Consumer integration checks every source file; installed Codex 0.154.0 `skills/list` discovered all 27 repository skills enabled. |
| Shared constitution | Generated `AGENTS.md` links the Codex surface guide; knowledge stays in the shared `.claude/knowledge` tree. Consumer test asserts the installed mapping. |
| Tools and personas | Guide maps operations to actual exposed tools and provides a separate-agent fallback. All 23 generated TOML personas parse and preserve the complete canonical body; no model or permissions override is introduced. Named-persona execution was not exercised. |
| Hook wiring | Native `hooks/list` discovers all four exact generated definitions in a fresh trusted temporary Git project with no project config.toml. Windows command selection, event names and matcher were observed. Separate fixtures execute the configured commands through cmd and PowerShell from nested paths with spaces and assert actual parent/subagent audit markers. |
| Safe installation and refresh | Tests cover repeated install, unrelated config and hook preservation, modified pack-hook conflicts, historical-guidance refresh and retained local edits. |
| Consistency | Missing, changed and extra projected files fail checks. Source sync, consumer doctor, local bundle verification and CI drift paths include Codex output. |

## Validation

- Red-first: initial consumer checks failed for absent skills/hooks; hook fixtures failed before payload and Windows command adaptation.
- Focused adapter suite: 12 passed.
- Full bundle: all 11 gates passed; Python 720 passed, 1 skipped, 208 subtests passed; Node 28 passed; 36 eval cases passed; graph, rendering/accessibility, audit, coordination, foundation and context checks passed.
- Browser benchmark after installing pinned dependencies: 5 passed, 1 skipped. Both Python and browser skips require directory symlink privileges unavailable on this Windows account. Targeted confirmation: 66 passed, 1 skipped, 73 subtests passed; Python reports WinError 1314.
- Independent adversarial review cleared the implementation after correcting historical merge-base guidance and malformed doctor-input handling. Those defects have regression coverage under HOST-A.

## Native probe boundary

On 2026-09-15 UTC, installed CLI 0.154.0 app-server initialization and `hooks/list` returned four project hooks with no errors or warnings: preToolUse, sessionStart, userPromptSubmit and subagentStart. It selected each `commandWindows` value. All definitions reported `enabled: true`, `trustStatus: untrusted`, as expected before individual hook review. No model turn or trusted native hook execution was performed. Fixture execution proves handler behavior, not an end-to-end host event dispatch.

The existing linked worktree returned zero hooks even though skill discovery succeeded. Its project configuration layer returned an empty object; that does not prove whether the layer was active. A clean consumer with an isolated temporary profile and explicit project trust loaded the exact generated hook file, without a project config.toml. The specific existing-profile/worktree exclusion remains undiagnosed and is not represented as an adapter failure or successful activation. Persistent user configuration and approval settings were not changed by the adapter.

Official contracts: [skills](https://learn.chatgpt.com/docs/build-skills), [custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [hooks](https://learn.chatgpt.com/docs/hooks), [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## Cost and remaining integration

Audit duration is measured from the skill marker and includes interruptions and runtime investigation; it is not active compute time. Agent timing intervals and dollar cost were not recorded, so no speedup or spend estimate is claimed. Retain this worktree for later commit, push and merge. Native trust is a consuming-host setting, separate from generated-file correctness.
