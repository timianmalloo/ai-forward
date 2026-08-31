---
id: forensic-review-rev49-backlog
title: "Forensic Review Backlog - revision 49"
type: doc
status: superseded
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [backlog, forensic-review, ci, worktree, audit, windows]
links:
  - { to: forensic-review-rev49, rel: refines }
  - { to: forensic-review-rev49-proof, rel: tested-by }
  - { to: forensic-review-rev48-backlog, rel: supersedes }
  - { to: defect-classes, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2026-11-26"
review-suggested: []
summary: >-
  Three proposed items from the revision-49 forensic review at commit 33f651d: make the
  local bundle verifier restore declared npm dependencies in clean worktrees; stop sync-pack
  from leaving CRLF-only dirty Copilot agent files on Windows; and make audit-log suggest
  distinguish its unavoidable append-only self-reference from untriaged meaningful changes.
---

# Forensic Review Backlog - revision 49

**Source review:** `docs/reviews/forensic-review-rev49.md` - commit `33f651d`, branch `main`, isolated worktree `forensicreview/rev49-post-restart`.
**Carried forward:** no open rev48 findings. The accepted required-status-check risk remains governed by `docs/notes/required-status-checks.md`.

## Phases

| Phase | Goal | Items |
|---|---|---|
| 1 - Restore verifier portability | Make the front-door local proof work in a clean worktree | FR-069, FR-070 |
| 2 - Tighten audit suggestion semantics | Remove a recurring false positive from the decision-ledger triage tool | FR-071 |

## Phase 1 - Restore verifier portability

### FR-069 - issue - P1 - `verify-bundle.ps1` fails in a clean worktree because it does not restore npm dependencies
- **Affected scope:** `tools/verify-bundle.ps1`, `package.json`, `package-lock.json`, `.github/workflows/pack-consistency.yml`
- **Evidence:** `package.json` declares `@playwright/test`; `package-lock.json` pins `playwright` 1.61.1. In an isolated clean worktree with no `node_modules`, gate 4's direct `node --test tests/docs_explorer/docs_explorer_core.test.js tests/docs_explorer/browser_benchmark.test.js tests/docs_explorer/knowledge_surfaces.test.js` exits 1 with `Cannot find module 'playwright'`. CI's equivalent step runs `npm ci` first; `verify-bundle.ps1` does not. After `npm ci`, the same `verify-bundle.ps1` run passes all nine gates.
- **Consequence:** the documented front-door instruction says to run `pwsh tools/verify-bundle.ps1`, and WT1 says writing sessions start in new worktrees. A new worktree has no ignored `node_modules`, so the one-command proof is not actually one command there. The primary checkout can pass because it has ambient untracked dependencies, which is the CI-ENV class in local form.
- **Recommended remediation:** make `verify-bundle.ps1` restore declared npm dependencies before gate 4, matching CI. Prefer `npm ci --ignore-scripts` unless Playwright's package lifecycle is required; if lifecycle scripts are required, name the supply-chain reason and keep the command identical to CI.
- **Acceptance criteria:** in a new worktree with no `node_modules`, `pwsh tools/verify-bundle.ps1` exits 0 through gate 4 without manual `npm ci`; deliberately moving `package-lock.json` aside or corrupting the npm restore makes the script fail with a specific dependency-restore message before the Node tests.
- **Validation:** create a scratch worktree, confirm `Test-Path node_modules` is false, run `pwsh tools/verify-bundle.ps1`; then corrupt the lockfile/restore path and confirm the dependency-restore step fails.
- **Dependencies:** none
- **Owner:** @timianmalloo
- **Next skill:** `/implement`
- **Status:** proposed

### FR-070 - issue - P2 - `sync-pack.ps1` leaves CRLF-only dirty `.github/agents` files on Windows
- **Affected scope:** `tools/sync-pack.ps1`, `.github/agents/*.agent.md`, `.gitattributes`/line-ending policy
- **Evidence:** from a clean Windows worktree, `pwsh tools/sync-pack.ps1` leaves 12 `.github/agents/*.agent.md` files modified. `git ls-files --eol -- .github/agents/*.agent.md` shows the modified files as `i/lf w/crlf attr/text eol=lf`; `git diff --stat` reports no content diff. Normalizing those files back to LF restores a clean tree.
- **Consequence:** the verifier can pass while the worktree is dirty. That blocks fail-safe worktree cleanup, makes clean-tree claims noisy, and teaches agents to normalize generated files by hand after every run.
- **Recommended remediation:** make the sync writer emit LF for all generated text files, or run a deterministic LF normalization pass over the sync output before returning. Add a regression check for working-tree cleanliness after sync on Windows-sensitive generated surfaces.
- **Acceptance criteria:** on Windows with `core.autocrlf=true`, a clean checkout stays clean after `pwsh tools/sync-pack.ps1`; `git ls-files --eol -- .github/agents/*.agent.md` reports `w/lf` for generated agent files; a test or gate fails if sync writes CRLF into a path whose attributes require LF.
- **Validation:** run `pwsh tools/sync-pack.ps1` from a clean worktree, then `git status --short` and `git ls-files --eol -- .github/agents/*.agent.md`.
- **Dependencies:** none
- **Owner:** @timianmalloo
- **Next skill:** `/implement`
- **Status:** proposed

## Phase 2 - Tighten audit suggestion semantics

### FR-071 - todo - P3 - `audit-log.py suggest` self-reports the commit that records its own closeout
- **Affected scope:** `docs/ai-forward-pack/scripts/audit-log.py`, `pack/scripts/audit-log.py`, `docs/audit/change-log.jsonl`
- **Evidence:** after closing the recovery change-log suggestions, `audit-log.py suggest --n 50` still reports `[commit] 33f651d docs(audit): close change-log suggestions`. The latest change entry was appended before that commit existed, so its `git.after` is `5062aac`; the commit containing the entry necessarily appears after `git.after`.
- **Consequence:** the suggestion list cannot reach a durable empty state after a change-log-only closeout. Operators learn to ignore one recurring false positive, which weakens the purpose of `suggest` as a triage lens.
- **Recommended remediation:** teach `suggest` to recognize and suppress commits whose only tracked changes are the change log and its derived viewer projection when the newest change entry is a closeout/triage entry. Alternatively, add explicit `--since-after-current-change-commit` semantics or a recorded ignore marker for self-referential closeout commits.
- **Acceptance criteria:** after a change-log closeout commit that only updates `docs/audit/change-log.jsonl` and `docs/audit/audit-data.js`, `audit-log.py suggest` prints `no unlogged meaningful changes detected`; a normal decision-signalling commit that changes a design/ADR/source file is still suggested.
- **Validation:** create a scratch change-log-only commit and run `suggest`; then create a scratch ADR/design-signalling commit and verify it is still suggested.
- **Dependencies:** none
- **Owner:** @timianmalloo
- **Next skill:** `/design-slice` if semantics are changed, then `/implement`
- **Status:** proposed

## Status

| | |
|---|---|
| **Completed** | Three evidenced findings converted into proposed backlog items with acceptance criteria and validation methods. |
| **Remaining** | Human triage. Nothing has been fixed in this `/forensicreview` run. |
| **Best next action** | Approve or reject Phase 1. If approved, implement FR-069 first because it restores the reliability of the local proof in the worktree workflow. |

