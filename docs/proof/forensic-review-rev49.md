---
id: forensic-review-rev49-proof
title: "Proof Pack - Forensic Review, revision 49"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [proof-pack, forensic-review, evidence, ci, worktree]
links:
  - { to: forensic-review-rev49, rel: tested-by }
  - { to: forensic-review-rev49-backlog, rel: relates-to }
  - { to: forensic-review-rev48-proof, rel: supersedes }
review-by: "2026-11-26"
review-suggested: []
summary: >-
  Evidence record for the revision-49 forensic review at commit 33f651d. It records the
  baseline gates and the three proposed findings: a clean-worktree npm dependency restore
  gap, a Windows CRLF dirty-state after sync, and audit-log suggest's append-only
  self-reference.
---

# Proof Pack - Forensic Review, revision 49

## Capture context

| Field | Value |
|---|---|
| Repository | `ai-forward` |
| Target commit | `33f651d1c6c30074c5eaca0d30a356ebac0a4a20` |
| Target branch | `main`, local checkout 4 commits ahead of `origin/main` at capture |
| Review worktree | `C:\Projects\ai-forward-forensicreview-rev49-post-restart`, branch `forensicreview/rev49-post-restart` |
| Dirty state at grounding | Primary tree clean; review tree clean before evidence probes |
| Pack revision | 49 (`bundle_version: 2026.08.26.3`) |

## Claims

| # | Claim | Evidence | Oracle | Red observed | Confidence |
|---|---|---|---|---|---|
| 1 | The target tree is pack revision 49 with the current documented counts. | `pack/adapters/INSTALL.md` has `revision: 49` and counts `{ lenses: 23, skills: 22, knowledge_docs: 38, templates: 27, scripts: 18 }`. | A different revision/count map would falsify the baseline. | n/a | Verified |
| 2 | The docs graph is healthy at baseline. | `docs-graph.py inventory` reports 118 artifacts, 0 defects, 0 suggestions, 0 stale, 0 flagged, 0 orphans, 0 index drift. | Any nonzero defect/suggestion/stale/flag/orphan/index-drift count. | n/a | Verified |
| 3 | The audit and change logs are readable. | `audit-log.py verify` reports 99 audit + 36 change entries, 0 unreadable lines. | Any unreadable line makes `verify` exit nonzero. | n/a | Verified |
| 4 | The full local bundle gate passes after declared npm dependencies are restored. | In the review worktree, `npm ci` adds 3 packages from `package-lock.json`; then `pwsh tools/verify-bundle.ps1` reports `BUNDLE CONSISTENT - all 9 gates passed`. | A failing gate after dependency restore. | Yes - claim 5 captures the red state before restore. | Verified |
| 5 | A clean worktree without `node_modules` cannot run gate 4. | Temporarily renaming `node_modules` away, then running the exact gate-4 `node --test ...browser_benchmark.test.js...` command exits 1 with `Error: Cannot find module 'playwright'`. | If the command passed without `node_modules`, the finding is false. | Yes | Verified |
| 6 | CI restores npm dependencies before its Node gate, while `verify-bundle.ps1` does not. | `.github/workflows/pack-consistency.yml` gate 4 runs `npm ci` then `npm run test:docs-explorer:core`; `tools/verify-bundle.ps1` gate 4 invokes `node --test` directly and contains no `npm ci`. | Matching restore behavior in both files would falsify the mismatch. | n/a | Verified |
| 7 | `sync-pack.ps1` dirties 12 Copilot agent files by working-tree EOL on Windows. | From a clean review tree, `pwsh tools/sync-pack.ps1` leaves 12 `.github/agents/*.agent.md` files modified; `git ls-files --eol` shows `i/lf w/crlf attr/text eol=lf` for the modified files; `git diff --stat` has no content changes. | A clean status after sync, or real content diff rather than EOL-only state. | Yes | Verified |
| 8 | `audit-log.py suggest` self-reports the commit containing the newest change-log closeout. | At `33f651d`, `audit-log.py suggest --n 50` reports `[commit] 33f651d docs(audit): close change-log suggestions`; the latest change entry's `git.after` is `5062aac`, because the entry was appended before `33f651d` existed. | No suggestion after the closeout commit, or a latest change entry that can reference its containing commit without another commit. | Yes | Verified |
| 9 | No unused worktree existed at recovery close. | `coord-core.py worktree cleanup` reported only the primary checkout before this review created its isolated worktree. The review worktree is intentionally held while this artifact exists. | A removable non-primary worktree would falsify the claim. | n/a | Verified |

## Residual risk

This review did not execute remote CI for the local commits because they are not pushed. The prior remote `main` baseline at `6e9b1fb` has green `pack-consistency` and `pages` runs; the local target has stronger local evidence only. The review's findings are limited to tooling and record hygiene; no production/runtime code path exists in this repository.
