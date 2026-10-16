---
id: spec-one-command-adoption
title: "One-command setup and outcome delivery"
type: spec
status: in-review
owner: "@ahutanu"
phase: "pack-adoption"
tags: [adoption, usability, delivery, installation, cross-platform]
links:
  - { to: architecture, rel: refines }
review-by: 2027-01-01
review-suggested: []
summary: >-
  Reduce first-run command selection without weakening outcome ownership. A portable
  bootstrap installs the existing pack deployment map; deliver selects applicable
  workflows, preserves human gates, and resumes one task from validated checkpoints.
---

# One-command setup and outcome delivery

## Problem and scope

A newcomer currently needs a source clone and knowledge of the pack's individual
skills and handoffs. The new first-run path is one setup command in the project,
then `/deliver <desired outcome>` (`$deliver` in Codex). Expert skills remain available.

The goal is lower interaction and discovery cost, not evidence of a measured increase
in population adoption. Installing files is not proof a coding application loaded them.
A workflow checkpoint is not proof of human consent or semantic correctness.

## Part A — Functional requirements

### Setup

- **S1:** One invocation deploys and verifies the current source deployment map into
  the invoking project. Git worktree/subdirectory and plain project behavior is explicit.
- **S2:** Use the existing `pack-apply.py` program. Resolve an exact Git commit and
  installed pack revision. Support explicit source/ref selection and local committed
  source for offline verification; never install uncommitted source silently.
- **S3:** Preserve product code, dirty/untracked work, accumulated documentation,
  project-owned policy, custom hooks, permissions and trust. Managed additions are
  intentional; conflicting local deviations are refused rather than force-overwritten.
- **S4:** Preview writes nothing to the project. Repeating a successful install is
  idempotent. A failed or incomplete installation is never reported as successful.
- **S5:** No Git initialization, invented identity, commit/push, global configuration,
  release, registry publication, ownership opt-in or optional CI injection.
- **S6:** Give a concise result and exact next action, plus a machine-independent
  receipt with source commit and pack revision. Distinguish warnings from failures.
- **S7:** One identical launcher syntax works in Linux/macOS/Windows shells. State
  `uv` and Git prerequisites; the launcher manages Python without installing the
  target project's dependencies or creating a project environment/lockfile.

### Deliver

- **D1:** With a task, select applicable existing workflows from grounded repository
  evidence, the requested outcome and unresolved questions. With no task, ask simply
  what outcome the user wants. Do not present the whole skill catalog as homework.
- **D2:** Preserve the original request, completion conditions and exclusions through
  each handoff. Compare any compiled contract with original human intent; quote/hash
  provenance alone is not semantic equivalence.
- **D3:** Routine features use only necessary research/specification/architecture/design
  stages. Small T0 changes take a short path. Risk triggers and migration cannot reduce
  the required tier or verification floors.
- **D4:** A defect uses investigation and its human repair-review stop, except where
  the human explicitly preauthorized continuing. Migration characterizes old behavior
  before changing it. UI design precedes building a visual surface.
- **D5:** Coordinate only justified independent work. Prepare the division and contracts
  before dispatch; coordination replaces single-session execution, not extra default
  agents. Preserve the task-specific investigation/characterization obligations.
- **D6:** Continue automatically between applicable approved stages. Required decisions,
  permissions, hard-veto resolution and release authorization remain real pauses.
- **D7:** Resume the same task in a fresh session using a small durable checkpoint.
  Validate project identity, contract, inputs and evidence; reject corrupt/stale/wrong
  context rather than assume completion. Do not repeat valid completed work.
- **D8:** Stop only on demonstrated completion, a concrete human gate/blocker or user
  redirection. Return original criteria versus observed evidence, changed artifacts,
  actual checks/skips, residual limits and the decision still needed.
- **D9:** No default adoption, domain-expert generation, dreaming, profiling, deployment
  or unrelated cleanup. Respect explicit question/review-only requests and the pack's
  current audit/graph opt-in behavior.

### Acceptance scenarios

- A known small correction needs no new architecture/specification ceremony; its real
  regression check and original completion condition still apply.
- A data/identity/migration task cannot route as T0/T1 merely because the diff is small.
- An investigation finishes with a repair proposal and waits for the actual human
  response; a fresh session resumes that task, not a newly invented replacement.
- A migration cannot lose characterization by selecting coordinated execution.
- A checkpoint whose evidence changes, whose contract changes or whose project differs
  refuses reuse. A handback with a missing success criterion remains incomplete.
- Installing into a project with existing instructions, custom hooks and a graph keeps
  those decisions. A managed conflict or unsupported source fails before promotion.
- Running the installer twice does not duplicate blocks or overwrite local deviations.
- A plain project remains non-Git after installation; an unrelated large tree is not
  copied merely to deploy the pack. Shell/path/Unicode handling is tested on actual OSes.

## Part B — UX specification

The primary interface is two familiar entry points, not a workflow designer. Expert
commands remain discoverable as progressive detail. Show the chosen path and reasons
briefly; the user should not choose every stage manually.

States: no task → ask for outcome; running → concise useful progress; decision →
question/recommendation/consequence; paused → durable task identity and next action;
resumed → confirm valid checkpoint and continue; error → specific obstacle and safe
recovery; complete → result, evidence and remaining limits.

A pause does not abandon the task or claim it was delivered. A successful installation
explains that restarting/refreshing the coding application's discovery may be needed.
Do not resolve a warning by granting broad permissions.

## Part C — UI specification

N/A for graphical tokens, animation and screen layout: the added surfaces are native
coding-agent commands and plain terminal output. Accessible text carries every state;
color is not required to understand success/error or a next action. Existing handbook
styling is preserved. CLI examples are single-line and shell-independent where claimed.

## Non-goals and evidence limits

No universal slash-command process runner, new coordination broker, semantic proof
from structural receipts, authenticated same-user authority, or automatic human consent.
No alteration of unrelated compiler/eval defects from a previous audit. Deterministic,
fixture, native-harness and actual cross-platform evidence are labeled separately.
