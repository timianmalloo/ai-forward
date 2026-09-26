---
id: plan-harness-config-portability
title: Portable five-harness pack configuration
type: doc
status: in-progress
owner: release-engineer
phase: implementation
tags: [hooks, windows, macos, configuration]
relates-to: [plan-cross-platform-readiness]
review-by: 2026-10-26
summary: Repair shell-dependent hook launch commands for all five supported harnesses, including downstream upgrades, without changing permissions or hook decisions.
---

# Portable five-harness pack configuration

## Goal and acceptance

The source repo and repositories receiving the pack support Copilot CLI, Claude Code,
Codex CLI, Grok Build and Antigravity (agy) on Windows and macOS. This change repairs
configuration portability; it does not promise that every host offers identical events,
native permission enforcement, or runtime attachment.

Done when:

1. Pack-owned hook commands run through PowerShell and POSIX shells, from a repository
   root or subdirectory, including paths with spaces. Python discovery rejects unusable
   interpreters and preserves stdin, stdout, stderr and the actual hook exit status.
2. Source sync, fresh installation and upgrade deploy the same launcher and definitions.
   Updates replace stale pack-owned handlers, preserve unrelated settings/custom hooks
   and explicit ownership opt-ins, and produce BOM-free UTF-8. Invalid settings fail
   without overwrite. A second update is idempotent.
3. All five harness skill/configuration surfaces remain available. Codex retains its
   existing opt-in native hook policy; no new trust, permission or ownership grants occur.
4. Tests execute the real launch commands and installation path on Windows and macOS.
   Pack verification passes, the change is committed and pushed, and CI results are read.
   Native model sessions are a separate qualification: shell/adapter proof must not be
   described as proof that a particular host version honored an authorization decision.

Not in scope: personal credentials/settings, unrelated dirty files, new agent behavior,
or changes to lease, decision, permission and native hook payload semantics.

## Evidence and design

Verified on Windows, Copilot 1.0.89-4: a Claude-format hook command beginning
`py=$(python3 ...); [ -x "$py" ]` ran through PowerShell, failed to parse and denied
every tool before its implementation ran. Clearing PreToolUse restored tool access,
but left the same commands on other events. The local emergency rewrite introduced
a UTF-8 BOM rejected by the pack doctor. Existing portability tests only ran the
command under `sh`, so they could not detect this cross-loader failure.

Primary contracts consulted:

- https://docs.github.com/en/copilot/reference/hooks-reference
- https://code.claude.com/docs/en/hooks
- https://developers.openai.com/codex/hooks/
- https://developers.openai.com/codex/windows/
- https://docs.x.ai/build/features/hooks
- https://antigravity.google/docs/hooks

Current docs describe direct argv execution in some hosts, not all installed
cross-loaders. Do not require those newer optional fields. Retain each host's current
JSON schema and use a shell-neutral `node -e` bootstrap containing no shell expansions.
The bootstrap asks Git for the current checkout root and requires one pack-owned CJS
launcher. Node passes a fixed script name and arguments to Python without a shell.
The launcher permits only the shipped hook entry points and coordination hook command.
It anchors execution to its own installed checkout, never a machine-specific path.

Node.js, Python 3 and Git become explicit prerequisites for pack hooks on both platforms.
This is preferable to requiring Git Bash on every Windows host or installing a private
Python alias. Missing prerequisites fail loudly. The launcher does not change the
Python hooks' allow/deny, duplicate-event, identity or stop behavior.

### Security review dispositions

- Migration uses a finite map of **complete previously shipped command strings**, not
  path/host substring matching. Wrappers and added arguments are never rewritten.
  Validate all hook arrays/objects/command fields before writing. Replace only a
  recognized handler's command; keep its matcher, position, timeout and enabled state.
- Python discovery has a cumulative one-second deadline, probes receive no stdin,
  capture at most 4 KiB and are killed with SIGKILL on timeout. The hook runs once, with a two-second
  child deadline, below the smallest existing five-second host deadline. A missing
  executable, timeout, signal or null status is non-success, never an allowed decision.
  Preserve real child exit codes including 2. Copilot's native PowerShell arm explicitly
  exits with LASTEXITCODE; generic host command wrappers remain subject to the host's
  documented execution/error semantics. No fallback after child execution begins.
- Runtime/PATH and approved checkout integrity belong to the operator and the host's
  workspace approval. This launcher is not a sandbox for malicious approved code.
  Git discovery drops GIT_DIR, GIT_WORK_TREE and GIT_COMMON_DIR in the child environment.
  A nested repository resolves to itself and fails if it has no pack: never fall back
  to a parent's install. Symlinked script targets escaping the installed checkout fail.
  Only fixed built-in Node module names are loaded; invocation validation permits
  known scripts, known hosts/events, and `coord-core.py hook`, never other subcommands.
- Missing Node/Git can fail before Python protocol handling. Copilot's observed
  preToolUse behavior denies launcher errors; other hosts' error/timeout handling is
  host/version-specific. Do not promote native enforcement from launcher success.
  This repair preserves the separate commit/runner floors and never changes trust.

The data model is unchanged: native hook configurations remain the host-facing
representation, pack templates remain their source, and the launcher has no durable
state. Existing telemetry remains at the Python hooks. Launcher failures identify the
bootstrap, missing interpreter or child failure on stderr without logging request bodies.

## Execution plan

| Phase | Capability | Work and surfaces | Exit oracle | Dependencies |
|---|---|---|---|---|
| 1 | Reasoning | Establish host contracts; review this design for trust and migration safety | No implicit grants; launch paths and upgrade identity rules specified | None |
| 2 | Deterministic mechanics | Red-first command/upgrade tests; launcher; four hook templates; all five native ownership emitters | Old commands fail PowerShell tests; repaired commands preserve payload/output/status | 1 |
| 3 | Deterministic mechanics | Installer, sync and doctor; BOM repair and managed-handler replacement | Fresh/old/BOM/custom/malformed fixtures; second run unchanged; all five skill surfaces present | 2 |
| 4 | Independent review | Test Architect review; full bundle gate; Windows/macOS CI | Real-shell and real-install assertions, not substring-only conformance | 3 |
| 5 | Deterministic mechanics | Revision/changelog, docs and defect-class evidence; commit/push; reconcile primary checkout | Remote commit and CI state read back; unrelated changes preserved | 4 |

The implementation is one context-sharing track; independent contract/security/test
reviews are bounded to four agents total (the security hard gate required a second,
narrow ruling because synchronous agents cannot receive follow-up messages). No parallel writers. Main-line estimate:
90 tool calls; at the estimate, report remaining work rather than silently expanding it.
No latency estimate is claimed: the prior measurement covers the failure, not this repair.
The correction loop reduces the finite set of failing assertions; two non-improving
passes trigger a diagnostic stop rather than a weakened test.

## Rollout and rollback

The deployment revision names the launcher, templates, installer and doctor together.
Never distribute only the new JSON without the executable it references. Existing local
ownership hooks are migrated only when recognized as pack commands; arbitrary custom
commands and permission settings remain untouched. Fresh installs do not enable ownership.
Rollback reverts the source and generated surfaces together. Do not restore a known
Bash-only command into a Windows Copilot checkout as an emergency rollback; retain the
last working portable revision instead.

## Proof and review record

Pending implementation and execution. Full live-host qualification on both operating
systems is not inferred from adapter tests; record platform/host limits explicitly here.

GATE design-security · 2026-09-26 · Security & Identity Architect · PASS after
exact-command migration, bounded failure handling and explicit checkout/runtime trust
requirements replaced three underspecified design clauses. Implementation proof pending.
