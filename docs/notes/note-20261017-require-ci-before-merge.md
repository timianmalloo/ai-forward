---
id: note-20261017-require-ci-before-merge
title: "Decision — require CI to pass before anything reaches main"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [decision, branch-protection, ci, release, required-status-checks]
links:
  - { to: note-required-status-checks, rel: supersedes }
  - { to: proposal-ci-speed-2026-10-17, rel: relates-to }
  - { to: plan-ci-speed-and-required-checks, rel: relates-to }
  - { to: forensic-review-rev108, rel: relates-to }
review-by: "2027-04-17"
review-suggested: []
summary: >-
  The owner decided on 2026-10-17 that CI must pass before a change reaches main, reversing the
  2026-08-26 decision not to require pack-consistency. Re-open trigger 1 of that decision fired
  (a second contributor now lands work on main), and its accepted-risk premise ("CI goes red,
  the next push fixes it") stopped holding when every workflow became manual-only on
  2026-10-04. Not yet executed: it depends on CI running on pull_request first.
---

# Decision — require CI to pass before anything reaches `main`

**Date:** 2026-10-17 · **Decided by:** the owner · **Supersedes:** `note-required-status-checks` (2026-08-26) · **Status of execution:** not started — see `plan-ci-speed-and-required-checks`

## Why the earlier decision no longer holds

- **Re-open trigger 1 fired.** A second contributor now lands work on `main` (commit `f92cf31`, PR #6). Verified from `git log`.
- **The accepted risk's premise is false.** The earlier note accepted that "a red commit on `main` means CI is red and the next push fixes it". Since commit `156943d` (2026-10-04) every workflow is `workflow_dispatch` only, so CI never turns red on its own. Verified from the workflow triggers (forensic review rev108).

## The decision

Make the `pack-consistency` jobs **required status checks** on `main`.

## Consequences, stated before execution

- **Direct pushes to `main` end.** With `enforce_admins: true`, a required check gates pushes as well as merges, with no admin bypass. Every change goes through a pull request. This includes agent work: WT1's "merge back" becomes "open a PR, rebase-merge when green".
- **Ordering is forced.** A required check reports only if the workflow runs on `pull_request`. Restoring the triggers (proposal change C7) must land **before** the requirement is switched on, or no PR can merge.
- **Speed becomes a cost on every change.** A 46.8-minute gate would block each merge for most of an hour. The CI speed changes (C1–C3) are sequenced ahead of the requirement for that reason, not as a precondition of the decision.
- **The check names must be stable.** Required checks are matched by job name; renaming a job in `pack-consistency.yml` silently drops the requirement. The plan pins the names and adds a test.

## Re-open triggers

- The gate's median wall-clock on `main` exceeds 30 minutes for two weeks after the speed work lands.
- A required check blocks an urgent fix and there is no documented break-glass path.

## Implemented (2026-10-18)

Applied after `plan-ci-speed-and-required-checks` P1–P6 landed (PR #17). Protection now requires
`consistency`, `consistency-windows` and `consistency-macos`, each bound to the GitHub Actions app
(id 15368) so no other integration can satisfy them, with `strict: true`; every other setting is
unchanged. Proof, observed:

- **A red PR cannot merge.** PR #18 broke gate 1 on purpose; with two checks red,
  `mergeStateStatus` was `BLOCKED` and `gh pr merge` refused. It was closed unmerged.
- **A green PR can.** The PR carrying this note merged once its three checks passed.

Measured cost: the Windows job sets the pace at ~25 min (pytest ~1,500 s including the serial
`wallclock` stage). The first re-open trigger above stays the guard against that growing.
