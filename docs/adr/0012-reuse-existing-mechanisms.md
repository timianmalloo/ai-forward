---
id: adr-0012-reuse-existing-mechanisms
title: "ADR-0012: Compose the mechanisms that already exist — the harness ships two of them, and the fleet ships three more"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, reuse, dup-a, one-a, worktree, reachability, git]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
  - { to: defect-classes, rel: relates-to }
review-by: ""
review-suggested: []
summary: >-
  The F8 reconciliation the spec made a condition of pass. Two of the four failure modes are already
  partly addressed by mechanisms shipped in the harness itself, and three more by scripts in
  TheTerrace; each is adopted, superseded, or retired explicitly. Also records the exact git
  expression for unique work, and why the obvious one silently reports SAFE.
---

# ADR-0012: Compose what exists, and name what is retired

- **Status:** Accepted · **Date:** 2026-08-20 · **Deciders:** Tech Lead, Enterprise Architect, the Simplifier, Domain Researcher
- **Context spec/architecture:** `docs/specs/agent-coordination.md` (F8, condition 2), `docs/architecture-agent-coordination.md` §8

## Context

The spec made this a **condition of pass**: two of the four failure modes are already partly solved by repo-local scripts, and federating a second mechanism would produce `ONE-A` — *a shared rule with no gate accretes private copies* — one of the classes the spec itself cites. Meridian's `DUP-A` adds the sharper form: *deciding to build and looking for prior art are two different acts*, and an unevidenced search is indistinguishable from no search. Both classes were authored by someone who had just cited the rule requiring the search.

So the search is run here and recorded where a reviewer can see it.

## Decision

We will **compose or supersede every existing mechanism explicitly**, and record the disposition of each.

| Existing mechanism | Disposition |
|---|---|
| `guard-worktree.ps1` (TheTerrace) | **Becomes the implementation** of the reachability check, with the corrected expression below and its two recorded bugs as red-first tests |
| `worktree-status.ps1` (TheTerrace) | **Becomes the implementation** of the operator status view |
| `sync-generated.ps1` (TheTerrace) | **Superseded in part** by ADR-0009's merge driver, which acts earlier and cannot be forgotten. Its `CTRL-E`/`CTRL-G` hardening is **carried forward as requirements** |
| `test-no-wildcard-staging.ps1` (TheTerrace) | **Adopted as-is** as the control on this layer's own surface |
| `new-finding.ps1` branch scanner (TheTerrace) | **Retired** by ADR-0008 |
| `worktree.bgIsolation` (**the harness**) | **Do not rebuild.** It already blocks Edit/Write in the main checkout for background sessions |
| `WorktreeCreate` / `WorktreeRemove` / `SessionStart` / `SessionEnd` hooks (**the harness**) | **Reused** for session registration and worktree lifecycle |
| `audit-log.py`, `docs-graph.py`, `scrub.py` (this pack) | **Composed, never duplicated** |

**And the expression, because getting it wrong is the recorded defect.** Unique work is:

```
peers = git for-each-ref --format='%(refname)' refs/heads refs/remotes  minus the current branch
unique = git rev-list HEAD --not $peers
```

`--all` is **forbidden** in this expression.

## Alternatives considered

- **Write the layer from the spec alone.** Rejected once the search was run — it would have rebuilt two mechanisms the harness already ships, which is `DUP-A` performed while implementing a spec that cites `DUP-A`.
- **Keep the existing scripts alongside the layer.** Rejected: two answers to one question is the defect signature. Each script is adopted, superseded, or retired — never left running beside its replacement.
- **`git rev-list HEAD --not --all` for unique work** (the intuitive form, and the one that shipped). **Rejected on a reproduction.** *Spike S4:* in a scratch repo where the branch genuinely held one commit reachable from no other ref, it returned **0** — reporting SAFE for exactly the case the guard exists to catch. The mechanism, now established rather than guessed: **`--all` implicitly includes `HEAD`**, so the expression reduces to `HEAD --not HEAD`. `--exclude=<branch> --all` fails identically, because excluding the branch does not exclude `HEAD`.

## Consequences

- **+** The most valuable finding in the architecture: **`worktree.bgIsolation` already exists**, so the layer composes with it and covers what it does not — foreground sessions, non-Claude harnesses, and cross-worktree leases. A version written from the spec alone would have rebuilt it.
- **+** Session and worktree lifecycle come from harness events rather than from a daemon or from polling, which is what lets ADR-0007 stay serviceless.
- **+** The corrected git expression is recorded with its failure mechanism, so the next person to write it has the reason and not just the incantation.
- **−** Adoption is not free: two PowerShell scripts must be ported to the layer's language and platform floor (`NFR-P2`: Windows, Linux and macOS, no runtime the pack does not already require). Porting is where a behavioural difference can be introduced silently, so each ported control must be **proven red on the un-fixed shape** before it is trusted — including `rev-list HEAD --not --all` returning SAFE, and the single-at-risk-commit case where the original lost its count.
- **−** Composing with harness features couples the layer to a surface the pack does not own. Mitigated by the composition contract: harness events are an adapter over the core (the ADR-0005 precedent), so a change there is a change to one thin host.
- **−** This reconciliation is a snapshot. New mechanisms will appear in both the harness and the fleet, so the search has to be re-run at each phase rather than treated as done.
