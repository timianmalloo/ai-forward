---
id: plan-harness-config-portability
title: Refresh and complete portable five-harness configuration
type: doc
status: implemented
owner: release-engineer
phase: implementation
tags: [hooks, windows, macos, configuration]
links:
  - { to: plan-cross-platform-readiness, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: 2026-10-26
summary: Reuse the upstream Git launcher, close the remaining Grok and legacy-emitter gaps, and make source sync and downstream settings upgrades safe and repeatable.
---

# Portable five-harness configuration

## Goal

AI-Forward and consuming repositories support Copilot CLI, Claude Code, Codex CLI,
Grok Build and Antigravity on Windows and macOS. Repair configuration, execute the
plan, commit and push. Preserve custom hooks, permissions, explicit ownership opt-ins,
unrelated local changes and host-specific event semantics.

## Grounding correction

The initial checkout was revision 92. A late fetch revealed that origin/main already
contained revision 95, including the exact Copilot/Agy/Codex launcher repair and
Windows/macOS CI. The primary branch had two local-only commits and was 33 commits
behind origin/main. The initial Node-launcher alternative was therefore superseded,
not shipped: reuse the existing `run-hook.sh` Git-alias launcher instead of adding a
dependency. The uncommitted prototype is retained in a named Git stash for recovery.

The original runtime failure remains verified: Copilot 1.0.89-4 ran a Claude-format
Bash command through PowerShell, which failed to parse and denied tools before Python.
The emergency settings rewrite also introduced a UTF-8 BOM. Upstream's launcher
already parses under cmd.exe, PowerShell and sh and retains Codex's caller directory.

Remaining gaps established against revision 95:

- Grok's default commands and native ownership emitter still use inline POSIX syntax.
- The legacy `coord install` settings printer still emits that syntax.
- Source sync does not refresh Claude settings, unlike downstream `pack-apply`.
- The updater removes whole entries based on a path substring, which can erase a
  custom wrapper or additional policy; BOM/nested malformed settings are not handled.
- The doctor checks hook-file presence, not whether old commands remain executable.

## Plan and acceptance

| Phase | Capability | Change | Exit oracle | Depends on |
|---|---|---|---|---|
| 1 | Reasoning | Reconcile with fetched upstream and reject the redundant alternative | Base is origin/main; no new runtime dependency | None |
| 2 | Deterministic mechanics | Use the existing quote-free Git launcher for Grok and the legacy settings printer | Actual command/payload tests; all five emitted host configs remain valid | 1 |
| 3 | Deterministic mechanics | Share narrow settings merge between installer and sync; diagnose old launch syntax | Exact legacy commands replaced; custom wrappers/metadata retained; malformed bytes unchanged; BOM normalized; idempotence | 2 |
| 4 | Independent review | Review upgrade boundary; run full bundle and Windows/macOS CI | Tests fail on prior updater; source/install parity; native shell tests pass | 3 |
| 5 | Deterministic mechanics | Commit and push the repair; preserve unrelated primary state | Remote commit and CI results read back | 4 |

Scope: source templates, `coord-core.py`, `pack-apply.py`, `named_hook_bundles.py`,
`pack-doctor.py`, sync tool, regression tests, this plan, defect register, revision
changelog and generated installations. No skill behavior or native permission policy
changes; Codex hooks remain explicit opt-ins. Git and Python remain prerequisites.

The migration recognizes a finite set of **complete shipped command strings**, scoped
by event. It replaces only command fields, preserving matcher/order/timeout/disabled
state and custom handlers. Wrappers, extra arguments and unknown shapes are not silently
treated as pack ownership. Validate nested settings before writing, and reject symlinks.

The model is unchanged: templates are the configuration source; settings are a merged
deployment, not a second policy store. Existing telemetry remains at the hook boundary.
The doctor reports malformed settings, obsolete shell forms and failed launcher probes
explicitly; it does not declare native event enforcement from adapter execution.

Rollback reverts source and generated copies together. Never restore Bash-only commands
on the affected Windows path. Updates preserve user permissions and do not grant trust.

## Evidence and limits

Upstream baseline: 55 tests and 125 subtests passed, with two explicit sh-dependent
skips on this Windows PATH. Official contracts:
https://docs.github.com/en/copilot/reference/hooks-reference ,
https://code.claude.com/docs/en/hooks ,
https://developers.openai.com/codex/hooks/ ,
https://docs.x.ai/build/features/hooks ,
https://antigravity.google/docs/hooks .

Shell/adapter execution is not proof that every installed model host honored an event
or permission decision. Windows execution is local; macOS execution must come from CI.
The original 90-call estimate did not include reconciling an already-fixed, divergent
upstream: that late fetch is rework, not a justification for a second launcher.

## Proof Pack

| Claim | Evidence and oracle | Red observed | Confidence / residual |
|---|---|---|---|
| Updates preserve custom policy and malformed bytes | `test_hook_settings_upgrade.py`: wrappers, mixed handlers, disabled opt-ins, BOM, nested invalid JSON and invalid UTF-8; both installer and sync | Nine old-merger failures; UTF-8 corruption independently reproduced by reviewer | Verified on Windows |
| All five ownership/default command paths use the existing launcher | Expanded `test_cross_platform_controls.py` exercises actual PowerShell/cmd commands and verifies reached script/argv | Earlier Bash command produced PowerShell ParserError | Windows verified; POSIX execution remains CI's responsibility |
| Source sync matches downstream refresh | Shared pure merger; real CLI byte-equality and repeat-application tests | Old source sync left Claude settings untouched | Verified on Windows |
| Readiness does not hide malformed/old configuration | Doctor rejects BOM/legacy commands and runs fixed benign hook help | Tests fail if it reports readiness for legacy settings | Verified; not native event-enforcement qualification |

Targeted run: **66 tests and 162 subtests passed**, two explicit sh-dependent skips on
this Windows PATH. Independent Test Architect closed the UTF-8/policy-preservation
veto after independently exercising the installer, sync CLI and optional hook paths.
The first full run found stale API reference output, this plan's missing typed links,
and three old tests still requiring inline Bash strings; those are corrected before
the final gate. No production behavior was weakened to satisfy those tests.

GATE upgrade-safety · 2026-09-26 · Test Architect · PASS · exact command migration,
strict decoding, unchanged malformed bytes, preserved opt-ins and metadata demonstrated.
Final bundle and Windows/macOS CI results are recorded by the release audit and CI run.

Full local Python suite: **1,267 passed, 143 platform/feature skips, 547 subtests
passed** (388.46 seconds). All executable checks passed; the remaining generated
documentation drift was repaired with the existing API/site builders. Only generated
documentation and this evidence record changed after that suite. The final no-repeat
bundle pass rechecks the remaining gates with `-SkipTests`; it does not replace the
full-suite evidence above. Windows/macOS workflow results attach to the pushed commit.

The first remote run, **36257413320**, passed the new portability/upgrade tests on
Windows, macOS and Linux. All three jobs failed three pre-existing doctrine tests
because a shallow feature-branch checkout contained neither `origin/main` nor `main`.
The workflow now fetches that one comparison ref before tests on each platform;
the tests retain their fail-closed missing-baseline behavior. This is a CI environment
repair, not a relaxation of the compatibility assertions.
