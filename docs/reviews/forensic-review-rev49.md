---
id: forensic-review-rev49
title: "Forensic Review - AI-Forward repository (revision 49)"
type: doc
status: superseded
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, ci, worktree, audit, verification, adoption-readiness]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-rev49-backlog, rel: relates-to }
  - { to: forensic-review-rev49-proof, rel: tested-by }
  - { to: forensic-review-rev48, rel: supersedes }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-11-26"
review-suggested: []
summary: >-
  Forensic assessment at commit 33f651d (pack revision 49). The repository's source,
  graph, audit log, and full gates are healthy after dependency restore, but the review
  found three tooling/record-hygiene gaps: verify-bundle is not self-contained in a clean
  worktree because it omits npm dependency restore; sync-pack leaves CRLF-only dirty
  Copilot agent files on Windows; and audit-log suggest can self-report the commit that
  records its own closeout.
---

# Forensic Review - AI-Forward repository, revision 49

**Target:** commit `33f651d1c6c30074c5eaca0d30a356ebac0a4a20`, local `main`, pack revision 49.
**Scope:** whole repository.
**Mode:** Peer Mode to reconstruct and assess, Adversary Mode for evidence quality.
**Worktree:** `C:\Projects\ai-forward-forensicreview-rev49-post-restart`, branch `forensicreview/rev49-post-restart`, created for this review per WT1.
**Supersedes:** `forensic-review-rev48`, whose backlog is resolved.
**Constraint honored:** no production code, dependencies, schemas, CI behavior, or runtime configuration was changed. The only writes in this run are review artifacts, graph projections, and audit records.

## 1. Baseline

| Surface | Result |
|---|---|
| Git | Primary tree was clean at `33f651d` and 4 commits ahead of `origin/main`; review branch has no upstream. |
| Pack counts | 22 skills, 23 lenses, 38 knowledge docs, 27 templates, 18 scripts. |
| Docs graph | 118 artifacts; 0 defects, stale nodes, flagged nodes, orphans, or index drift. |
| Audit log | 99 audit + 36 change entries, 0 unreadable lines. |
| Remote baseline | `origin/main` at `6e9b1fb` has successful `pack-consistency` and `pages`; local `33f651d` is not pushed. |
| Full local gate | `pwsh tools/verify-bundle.ps1` passes all nine gates **after** `npm ci` restores declared Node dependencies. |

## 2. Reconstructed system state

AI-Forward remains a static methodology/tooling repository. `pack/` is the source of truth; `.claude/`, `.github/`, `docs/ai-forward-pack/`, portal data, web index, and graph projections are generated or derived surfaces. The public invocable surface is the PowerShell/Python/JavaScript toolchain: `sync-pack.ps1`, `verify-bundle.ps1`, `package-pack.ps1`, `check-consistency.py`, `docs-graph.py`, `audit-log.py`, and the test/eval gates.

The meaningful recent changes since rev48 are record-hygiene and recovery records, not product behavior. The accepted branch-protection position still holds: required status checks are deliberately absent, while the Pages workflow has its own in-workflow quality gate.

## 3. Findings

### FR-069 - P1 issue - `verify-bundle.ps1` is not self-contained in a clean worktree

**Evidence:** a new worktree has no `node_modules` because it is git-ignored. Gate 4 imports `playwright` through `tests/docs_explorer/browser_benchmark.test.js` and fails with `Cannot find module 'playwright'` when `node_modules` is absent. CI restores dependencies with `npm ci` before its Node gate; `verify-bundle.ps1` does not. Running `npm ci` from the committed lockfile makes the same local verifier pass all nine gates.

**Violated contract:** the front door presents `pwsh tools/verify-bundle.ps1` as the one-command local proof, and WT1 makes new worktrees the default for writing sessions.

**Consequence:** the prescribed workflow fails in the prescribed workspace unless ambient untracked dependencies happen to exist.

**Confidence:** Verified. **Disconfirming check:** after `npm ci`, the same verifier passed, ruling out a broken test as the cause.

### FR-070 - P2 issue - `sync-pack.ps1` leaves CRLF-only dirty generated agent files on Windows

**Evidence:** from a clean Windows worktree, `sync-pack.ps1` leaves 12 `.github/agents/*.agent.md` files modified. `git ls-files --eol` shows `i/lf w/crlf attr/text eol=lf` for those files and `git diff --stat` reports no content changes.

**Violated contract:** WT7/WT12 cleanup and review baselines depend on clean worktree state meaning "no work present." A verifier should not leave a clean tree dirty when no semantic drift exists.

**Consequence:** cleanup is blocked until a human/agent normalizes line endings, and clean-tree claims need caveats after every sync on Windows.

**Confidence:** Verified. **Disconfirming check:** normalizing the files to LF restores a clean status without content changes.

### FR-071 - P3 todo - `audit-log.py suggest` has an append-only self-reference false positive

**Evidence:** after the recovery closeout change-log entry was committed, `audit-log.py suggest --n 50` still reported the commit containing that closeout. The newest change entry's `git.after` necessarily points at the commit that existed before the change entry was committed.

**Violated contract:** `suggest` is a triage lens for unlogged meaningful changes. A closeout commit containing only the closeout entry is not an untriaged product decision.

**Consequence:** the tool cannot reach a durable empty state after a change-log-only closeout, so users must learn to ignore a recurring false positive.

**Confidence:** Verified. **Disconfirming check:** the same command reports exactly the closeout commit, not an unreferenced ADR/note/source change.

## 4. Non-findings

| Candidate | Disposition |
|---|---|
| Required status checks disabled | Not reopened. This is an accepted risk with explicit re-open triggers in `docs/notes/required-status-checks.md`; none was observed here. |
| `audit-log.py suggest` reporting older ADRs/notes | Not current. The previous recovery turn added change-log references for those artifacts; the only remaining suggestion is the closeout self-reference captured as FR-071. |
| Remote CI not run for `33f651d` | Not a repository defect. The commit is local and unpushed; local gates are the available proof. |
| Graphify graph stale from August 2 | Not in the review scope. It is an optional generated code graph and was not used as current-state evidence. |

## 5. Readiness verdict

**READY WITH TOOLING BACKLOG.** The repository content and generated surfaces are consistent after dependency restore, the graph is healthy, audit history is readable, and the current findings are local-tooling/record-hygiene issues. The one P1 item affects the reliability of the prescribed local proof in a clean worktree; it should be triaged before the next pack source change.

## 6. Persona gate record

`GATE forensicreview-rev49 · 2026-08-28 · external Test Architect, with SRE/Documentation/Simplifier self-checks · exit criteria met after correcting the proof-pack wording from "accepted findings" to "proposed findings"; each finding has a repro command, disconfirming check, consequence and acceptance criterion; speculative candidates removed · verdict: PASS-WITH-CONCERNS · vetoes: none`

## 7. Status

| | |
|---|---|
| **Completed** | Reconstructed current repo state at `33f651d`; ran graph/audit/history inventory; ran the full bundle gate red/green around dependency restore; proved three findings; wrote proof pack and proposed backlog. |
| **Remaining** | Human triage of FR-069..FR-071. Nothing was fixed in this review. |
| **Best next action** | Approve or reject FR-069. If approved, implement it first so `verify-bundle.ps1` works as the documented one-command proof in a fresh worktree. |
