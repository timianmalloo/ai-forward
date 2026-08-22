---
id: adr-0010-enforcement-topology
title: "ADR-0010: Enforce at the harness edit boundary where it exists, at the commit boundary always — and fail to ask, never to allow"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, enforcement, hooks, pretooluse, fail-safe, spike, shell-a]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
  - { to: defect-classes, rel: relates-to }
review-by: ""
review-suggested: []
summary: >-
  A PreToolUse hook returning permissionDecision deny refuses an unleased edit before it happens; the
  pre-commit boundary is the universal floor no settings key can remove. Every indeterminate path
  returns ask with a reason beginning NOT CHECKED. The hook runs in exec-form with no shell, which
  closes the SHELL-A class structurally rather than by care.
---

# ADR-0010: Enforcement topology, and its honest limit

- **Status:** Accepted · **Date:** 2026-08-20 · **Deciders:** Security & Identity Architect, Tech Lead, SRE, Domain Researcher
- **Context spec/architecture:** `docs/specs/agent-coordination.md` (US-2, `NFR-R2`, `NFR-S2`, F1), `docs/architecture-agent-coordination.md` §4.2

## Context

`CI6` with a worked example: `CLAUDE.md` warned against `git add -A` in prose, in the file every session reads at grounding, and **the delivery script did it anyway** — because prose does not fail. A coordination rule that ships only as an instruction changes nothing. The spec therefore puts every invariant behind a mechanism, and the question this ADR answers is *which boundary*.

The spec left **F1 open**: each harness's edit-time hook surface was to be established *by execution, not by documentation*.

## Decision

We will enforce at **two** boundaries.

1. **The edit boundary, where a harness provides one.** For Claude Code, a `PreToolUse` hook matched on `Write|Edit` returning `hookSpecificOutput.permissionDecision` of `allow` / `deny` / `ask` with a `permissionDecisionReason` carrying the four-line refusal.
2. **The commit boundary, always.** A pre-commit check refusing any staged artifact the session never claimed. **This is the floor, not the fallback** — every harness has a commit boundary, and no settings key removes it.

**Every indeterminate path returns `ask`** with a reason beginning `NOT CHECKED` — never `allow`, and never a silent pass.

The hook is configured in **exec-form** (`args`), not as a shell string.

## Alternatives considered

- **Advisory warnings only.** Rejected: the corpus is a list of correct, prominent, always-loaded warnings that changed nothing.
- **Commit boundary only.** Rejected as the *primary*: by then the edit exists, and the agent has spent the work. Kept as the floor.
- **A shell-string hook command.** Rejected once the schema was read: with `args` present the command is spawned directly with no shell, and path placeholders are substituted per element as plain strings, *so paths with quotes, `$`, or backticks never reach a shell parser*. That closes Meridian's **`SHELL-A`** class — source containing bytes nobody typed, introduced by writing content through a shell construct that performs substitution on it — **structurally rather than by care**. It is not the default, so it must be chosen deliberately.
- **Failing open when the lease state cannot be determined.** Rejected on the recorded evidence: a guard that failed open reported SAFE for exactly the case it existed to catch, and a control that borrowed ambient state accused its own branch on CI. *A control that cannot see is not licensed to accuse, and it is certainly not licensed to imply it looked.*

## Consequences

- **+** **The program side is executed, not asserted.** *Spike S5:* the hook was run against the real payload shape across five cases — held-by-another (`deny` with holder, reason, expiry, remedy), free artifact (`allow`), own lease (`allow`), **identity unset (`ask`, NOT CHECKED)**, and **malformed payload (`ask`, NOT CHECKED, no crash)**. All five correct, including both fail-safe paths.
- **+** The `if` pre-filter (permission-rule syntax) decides whether the hook process is **spawned at all**. Since ~14 ms of every call is bare interpreter startup, this is the largest available latency lever and it costs nothing.
- **+** The commit floor means a harness with no hook surface is still enforced somewhere real.
- **−** **F1 is only half closed.** The contract for Claude Code is established and the program executed. **Copilot and any third harness remain unspiked**, and until each surface is executed those agents are advisory at the edit boundary and enforced at commit. The layer says which mode it is in rather than implying enforcement it is not performing.
- **−** **Enforcement is an integrity control, not a security control.** `disableAllHooks`, `allowManagedHooksOnly` and `strictPluginOnlyCustomization` can each switch hook enforcement off from a settings source this layer does not control, and an agent with shell access bypasses the tool boundary entirely. Stated plainly (`NFR-S2`), because a control trusted past its limit is worse than no control.
- **−** `ask` is a real interruption. Chosen over `allow` deliberately: an interruption is recoverable, a silent pass is not.
- **The number that decides whether this works** is `% of edits made under a held lease`. If it does not reach a high fraction, enforcement has failed regardless of implementation quality, and the answer is a different boundary rather than a better hook.
