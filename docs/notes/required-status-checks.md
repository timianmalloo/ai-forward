---
id: note-required-status-checks
title: "Decision — do not make pack-consistency a required status check on main"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [decision, branch-protection, ci, release, accepted-risk]
links:
  - { to: forensic-review-rev48-backlog, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2027-02-26"
review-suggested: []
summary: >-
  Decision not to enable required status checks on main, taken while closing FR-062. The
  control would have prevented the original incident outright, but with enforce_admins already
  true it also blocks direct pushes and forces a PR workflow on a solo-maintainer repo that
  pushes directly by design. FR-062 already closed the actual harm. Recorded as an accepted
  risk with explicit re-open triggers rather than left unstated.
---

# Decision — do not make `pack-consistency` a required status check on `main`

**Date:** 2026-08-26 · **Context:** FR-062, revision-48 forensic review · **Confidence:** Verified (the protection state and the GitHub semantics were both read, not recalled)

## The question

The revision-48 review found that commit `c27f83d` reached `main` with its quality gate red, and the public site published from it. FR-062's backlog entry named two remediations and called the second stronger:

1. make publication conditional on the gate *(shipped — `pages.yml` now has a `gate` job that `deploy` depends on)*;
2. make `pack-consistency` a **required status check** on `main`.

Option 2 was explicitly delegated to the maintainer, then delegated back with *"you decide"*.

## What was established

- `gh api repos/timianmalloo/ai-forward/branches/main/protection` returns **no `required_status_checks` block at all**. Also present: `enforce_admins: true`, `required_linear_history: true`, `allow_force_pushes: false`, `allow_deletions: false`, `required_conversation_resolution: true`.
- GitHub's protected-branches reference states branch protection rules *"set requirements for any pushes to the branch, such as passing status checks"* — so required checks gate **pushes**, not merges alone. With `enforce_admins: true` there is no admin bypass.
- Therefore enabling it would **block direct pushes to `main`** and force every change through a pull request.

## The decision

**Do not enable it.** Record the residual risk instead.

## Why

- **The expensive half of the harm is already closed.** FR-062 makes publication conditional on the gate, proven red-first on real CI (run `33015196508`: gate failure → deploy **skipped**, nothing published). The public site can no longer be published from a red tree, which was the damaging part of the incident.
- **What remains is cheap and self-correcting.** A red commit on `main` means CI is red and the next push fixes it. In the observed incident the whole cycle — detect, diagnose, fix, verify, push — took under an hour.
- **The cost is disproportionate and permanent.** This is a solo-maintainer repository whose working style is direct pushes to `main`; four such pushes happened in the session that produced this decision. Forcing a PR round-trip on every change is a standing tax, paid on every commit, to close a gap that is already mitigated.
- **The `enforce_admins` toggle is all-or-nothing.** The obvious middle path — required checks with an admin bypass — would mean setting `enforce_admins: false`, which also removes admin enforcement of linear history and the force-push/deletion bans. That trade is strictly worse than the status quo.
- **The discoverability fix addresses the actual cause.** The commit reached `main` red because the agent never ran the aggregate verifier, not because the branch was unguarded (defect class **CTRL-D**). FR-061 fixed that at the source and is enforced by `check_front_door_names_verifier()`.

## Accepted risk

A commit whose quality gate is red **can still land on `main`**. Consequences bounded to: CI shows red until the next push; a contributor who pulls mid-window gets a tree with a failing gate; the published site is unaffected (FR-062).

## Re-open triggers — any one of these overturns this decision

1. **A second regular contributor** joins the repository. The economics change the moment more than one person pushes.
2. **A red commit reaches `main` again** after FR-061 shipped. That would falsify the premise that the discoverability fix is sufficient.
3. **A red commit on `main` causes downstream damage** — a consuming repo pulling a broken pack revision, or a bad `/updatepack`.
4. **GitHub offers required checks with a per-actor bypass** that does not require disabling `enforce_admins` wholesale.

## Alternatives considered

| Option | Rejected because |
|---|---|
| Required checks + `enforce_admins: true` | Blocks direct pushes; forces PRs on a solo repo. The chosen non-action. |
| Required checks + `enforce_admins: false` | The toggle is global — would also drop admin enforcement of linear history and force-push bans. Net weaker. |
| A `pre-push` git hook running `verify-bundle.ps1` | Genuinely attractive, but hooks are per-clone and not committed, so it is a rung-3 control masquerading as rung-2 — it protects only the machine that installed it. Worth revisiting as an *opt-in convenience*, never as the guarantee. |
