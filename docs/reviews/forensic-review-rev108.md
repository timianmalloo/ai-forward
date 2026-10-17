---
id: forensic-review-rev108
title: "Forensic review — ai-forward at revision 108"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "assessment"
tags: [forensic-review, assessment, governance, security, rev108]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-rev108-backlog, rel: relates-to }
  - { to: forensic-review-rev59, rel: supersedes }
  - { to: defect-classes, rel: relates-to }
  - { to: note-20261017-require-ci-before-merge, rel: relates-to }
  - { to: note-20261017-session-profiles-published, rel: relates-to }
review-by: "2027-04-17"
summary: >-
  Forensic assessment of ai-forward at 332c297 (pack revision 108). Every gate passes except
  the Python suite, whose 10 failures are environmental and pre-existing on unmodified main.
  No P0 or P1. Four P2 findings: a byte-code cache in a fixed shared temp directory, CI that
  runs only on manual dispatch, a git-identity guard with six verified bypasses, and an
  edit-ownership hook whose `allow` skips the user's permission prompt. Eleven P3 items are
  hygiene, portability and documentation drift. Two were fixed during the review: the hook's
  needless prompts (WT-D, WT-E; PR #12) and bundle changes shipped without a revision bump
  (PACK-W; revision 109).
---

# Forensic review — ai-forward at revision 108

## Scope and baseline

| | |
|---|---|
| Commit | `332c297` on `main` (PR #12 merged; clean tree) |
| Pack revision | 108 (`pack/adapters/INSTALL.md:5`) |
| Supersedes | `forensic-review-rev59` |
| Findings | **FR-086 … FR-102** (ids continue from FR-085) |
| Surface | 30 skills · 23 personas · 40 knowledge docs · 29 templates · 47 scripts (`check-consistency.py`) |

### Baseline commands — run before judging, recorded as evidence

| Command | Result |
|---|---|
| `pwsh tools/verify-bundle.ps1` (tree of PR #12) | **17 of 18 gates pass**; gate 1 failed on stale `docs/api` and `docs/_site`, fixed in PR #12 and re-run green on the final tree |
| Gate 3 — `python -m pytest tests -q` | **1679 passed, 10 failed, 180 skipped** (39 min 29 s) |
| Gate 3 failures, same 10 on unmodified `main` `c267bd4` | 5 symlink tests raise `WinError 1314` instead of skipping (Developer Mode off) · 2 `test_delivery_session_start` tests read `AGENT_SESSION` leaked from `.claude/settings.local.json` · 3 `test_uv_hook_launcher` tests cannot spawn `sh` — see FR-099 |
| `docs-graph.py validate` | pass — 362 artifacts; 2 stale (V13) suggestions, non-failing |
| Workflow `uses:` | 9 distinct actions, **all pinned to a 40-character SHA** |
| Workflow `permissions:` | `contents: read` everywhere; `pages: write` + `id-token: write` on Pages; `attestations: write` on the benchmark |

The ten gate-3 failures are not attributable to this revision: they were reproduced on the
parent commit with no change applied.

## What was checked and found sound

- **Supply chain.** Every action is SHA-pinned; the deployed scripts remain stdlib-only.
- **Workflow privilege.** No workflow holds more than its job needs.
- **Source↔install boundary.** Gate 2 (`sync-pack.ps1` then `git diff --exit-code`) passes; a
  re-sync on the final tree produced no diff.
- **Defect register integrity.** `test_defect_register_counts.py` passes after two new classes
  (WT-D, WT-E).
- **Primary-checkout protection (PRIM-A).** A linked-tree session writing into the primary is
  still refused by name on every host.

## Findings in this revision

**P2 — material governance, security or operability debt**

- **FR-086** — `dispatch.py` sets `sys.pycache_prefix` to a fixed name under the shared temp
  directory. On a multi-user POSIX host, another user can pre-create it and plant byte-code.
- **FR-087** — Every workflow is `workflow_dispatch` only since `156943d`. Combined with
  FR-082 (no required check), nothing runs CI on a push or PR unless someone remembers.
- **FR-088** — `git-identity-guard.py` misses six ways of setting an identity and blocks
  quoted text that merely mentions the pattern (executed probe below).
- **FR-089** — The edit-ownership hook answers `allow` for any free in-repo write. On Claude
  Code a PreToolUse `allow` skips the permission prompt, so the hook grants writes the user's
  permission mode would have asked about.

**P3 — localized hygiene** — FR-090 … FR-100 (stale counts, hand-copied gate lists, link-unsafe
writes, bootstrap from a mutable ref, a 46-minute Windows job, no six-harness ADR, an
unsourced `.codex/hooks.json`, a lock with manual-only recovery, executable session-check
config, test isolation, native-host outside-path refusals).

**Resolved during the review** — FR-101: the hook's needless prompts (WT-D, WT-E), PR #12.
FR-102: those fixes and the Muse re-measure changed deployed files without a revision bump, so
pack-apply saw two versions of revision 108 and the hook fix could not reach a consumer. Fixed
by releasing revision 109; class PACK-W now has a gate-3 control.

### Executed probe — FR-088

`evaluate()` from `pack/adapters/hooks/git-identity-guard.py`, run directly on each command:

| Command | Result | Correct? |
|---|---|---|
| `git config user.name Bot` | BLOCK | yes (control) |
| `git config user.name` | allow | yes (read) |
| `git -C . config user.name Bot` | allow | **no** |
| `git config --file .git/config user.email b@x` | allow | **no** |
| `git config --worktree user.name Bot` | allow | **no** |
| `git config set user.name Bot` | allow | **no** |
| `GIT_AUTHOR_NAME=Bot GIT_AUTHOR_EMAIL=b@x git commit -m x` | allow | **no** |
| `git commit --author="Bot <b@x>" -m x` | allow | **no** |
| `echo 'docs: git config user.name X is forbidden' > notes.md` | BLOCK | **no** (over-match) |

## Assessment by layer

### Architecture — sound, under-recorded

The source → install → consumer direction still holds and is gated. The gap is in the record:
the pack now targets six harnesses (Claude Code, Copilot, Codex, Grok, Antigravity, Muse) and no
ADR records that decision or its cost (FR-095). `architecture.md` still describes revision 53
(FR-090).

### Design — sound, with two trust-boundary gaps

Two hooks overstep their domain. The identity guard is too narrow (FR-088). The ownership hook
is too broad: it speaks for paths it does not own (WT-E, fixed) and grants writes it only
needed not to refuse (FR-089). Both share one shape: **a guard's answer must stay inside the
question it was built to answer.**

### Implementation — sound, platform-sensitive

Correctness is well covered: 1679 tests. The debt is portability. Ten tests depend on the
host's symlink privilege, a leaked environment variable, or a POSIX shell (FR-099). Temp-dir
and link handling assume a single-user machine (FR-086, FR-092).

### Operations — the weakest layer

CI no longer runs by itself (FR-087), nothing requires it (FR-082), and the Windows job
quadrupled to ~47 minutes on the PR #6 branches (FR-094). The accepted CI proposal
(`proposal-ci-speed-2026-10-17`) and its plan (`plan-ci-speed-and-required-checks`) address all
three; the plan is recorded as next steps and **not yet executed**.

## Carried forward from revision 59

| Item | State at rev108 |
|---|---|
| FR-076, FR-077 | resolved 2026-09-22 (unchanged) |
| FR-078 coordination layer not run on its own repo | **partial** — gate 8b proves it is installed; the repo still does not route work through it |
| FR-079 docstring coverage | open — 279 of 599 public functions documented (47%) |
| FR-080 federation de-dup defeated by abstraction | open — now also covers the `apply-learnings` "conflict" branch |
| FR-081 fleet provenance lost on application | open |
| FR-082 no required status check | open — decision accepted (`note-20261017-require-ci-before-merge`), plan not executed |
| FR-083 budget gate on a fitted constant | open |
| FR-084 Node 20 runtime actions | open |
| FR-085 no coverage measurement | open |

## Rejected candidates

Recorded so they are not raised again:

- **"FR-083 came true."** The claim rested on a hypothetical chars-per-token ratio, not a
  measurement. The backstop has not been observed to fail.
- **`INSTALL.md` size.** Large, but it is a reference archive read on demand, not an always-on
  load; gate 8 measures what is always on.
- **Published session profiles (privacy BLOCK).** Overruled by the owner: publishing
  `docs/profiles` is intended (`note-20261017-session-profiles-published`). No backlog item.

## Readiness verdict

**Healthy, with an operations gap.** No P0 or P1. The code is well tested and the supply chain
is clean. The real risk is that CI has stopped being automatic at the same time as nothing
requires it, so a red `main` is caught only by a local `verify-bundle.ps1` run. FR-087 and FR-082
together are the first thing to close.

## Confidence ledger

| Finding | Confidence | Basis |
|---|---|---|
| FR-086 | **Verified** (code) · exploit **Inferred** | `pack/adapters/hooks/dispatch.py:142`; planting not executed |
| FR-087 | **Verified** | `git show 156943d`; every workflow `on:` is `workflow_dispatch` only |
| FR-088 | **Verified** (executed) | probe table above |
| FR-089 | **Verified** (code) · effect **Inferred** | `coord-core.py` `cmd_hook` returns `allow` for free paths; the prompt-skip is Claude Code's documented PreToolUse contract, not observed here |
| FR-090 | **Verified** | `architecture.md:16,47,61,158`; `AGENTS.md:11`; `.github/copilot-instructions.md:21`; `project-memory.md:59` |
| FR-091 | **Verified** | `verify-bundle.ps1:88-239` against `pack-consistency.yml:27-361` |
| FR-092 | **Verified** (code) | `reread-guard.py:53-72`; `pack-apply.py:542-547` |
| FR-093 | **Verified** (code) · download **Inferred** | `README.md:46,50`; `bootstrap.py:527`; no download observed |
| FR-094 | **Verified** on PR #6 branches · `main` **not measured** | runs 38983040683 (46.7 min), 38953998178 (49.6 min) |
| FR-095 | **Verified** | `docs/adr/0001–0013`; no harness-support ADR |
| FR-096 | **Verified** | no `pack/` source; `sync-pack.ps1:391-395` refreshes only if present |
| FR-097 | **Verified** | `delivery.py:1007-1018`; `checkpoints.md:81` |
| FR-098 | **Verified** | `session-start.py:83-89,134-143`; `hooks/README.md:101-105` |
| FR-099 | **Verified** (executed) | same 10 failures on `c267bd4` and `332c297` |
| FR-100 | **Verified** (executed) | `test_native_hosts_still_fail_closed_on_an_outside_path` |
| FR-101 | **Verified** (executed) | red-first tests; PR #12 |
| FR-102 | **Verified** (executed) | `test_bootstrap` CONFLICT reproduced alone; control red on `332c297`, green on revision 109 |

## Residual risk

- **The persona lens outputs were not persisted.** The lenses and adversaries ran in session
  `00bb7bcd`, but only their conclusions survived, in session memory. Every finding here was
  re-checked against the code or by execution in session `4bdeb954`. The per-lens verdict table
  of earlier reviews is therefore absent, not reconstructed.
- **Two effects are inferred, not observed:** byte-code planting (FR-086) and the prompt-skip of
  `allow` (FR-089). Each names its confirming check in the backlog.
- **Self-review.** The same agent authored much of the reviewed revision, including WT-D, whose
  `ask` this review then found was wrong (WT-E). That is the expected failure mode, and the
  reason every claim above was executed rather than recalled.
