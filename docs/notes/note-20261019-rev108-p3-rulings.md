---
id: note-20261019-rev108-p3-rulings
title: "Decision — every host answers like Claude, session checks need approval, setup installs a release"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [decision, hooks, permissions, supply-chain, ci, session-checks]
links:
  - { to: forensic-review-rev108-backlog, rel: relates-to }
  - { to: note-20261019-edits-never-ask, rel: refines }
  - { to: adr-0014-meet-the-developer-in-their-harness, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-04-19"
review-suggested: []
summary: >-
  Three owner rulings of 2026-10-19 on the revision-108 P3 findings, executed in revision 117.
  FR-100: every host answers an edit outside the repository as Claude does (no decision), because
  worktrees, memory and scratch folders are outside it. FR-098: a committed session-checks.json runs
  only after a human approves its exact bytes on that machine. FR-093: the documented one-line setup
  installs a release tag, with main as an explicit opt-in. The same revision gives CI one gate list
  (FR-091) and splits the Windows and macOS test suites into three shards (FR-094).
---

# Decision — every host answers like Claude, session checks need approval, setup installs a release

**Date:** 2026-10-19 · **Decided by:** the owner · **Executed:** revision 117

## FR-100: native hosts answer like Claude

**Ruling:** *"all harnesses should allow edit outside the repo because work trees are 'outside the
repo' … all harnesses should work like what we have with claude."*

The edit-ownership hook gave Claude no decision for a path in no checkout of the repository
(WT-E), but answered `deny` on Codex, Grok, Antigravity and Copilot. Those hosts could not write a
sibling worktree, user memory or a scratch folder. Now every host gets the Claude rule:

| Case | Answer on every host |
|---|---|
| A path in no checkout of this repository | no decision: the host's own permission mode decides |
| Any other input the hook cannot judge (no session, no record, no readable target) | no decision |
| A path that is itself suspect: a traversal, or an alias inside the checkout that resolves out | `deny` |
| A target that is present but cannot be read: a malformed patch, a relative Antigravity path | `deny` |
| A checked path: free or owned / held by another session | `allow` / `deny` |

The neutral answer is each host's documented one. Codex and Grok continue on exit 0 with empty
stdout (Codex hooks reference; Grok Build hooks docs), Copilot reads `{}`, Antigravity reads empty
success, and Claude reads `{}`. **Verified** for the hook's output by tests on every host; the
hosts' reading of it is **Inferred** from their published docs, not observed in a live session.

The unreadable-patch refusal is the one place this goes beyond Claude. Claude's edit tools carry a
structured path, so Claude never sends one. Giving it no decision would let the host apply a patch
whose targets this hook could not see, including a leased file.

## FR-098: session checks run only once approved

**Ruling:** option (a), *pin a hash at first approval*.

`.agents/session-checks.json` is committed config that runs commands at session start. A clone
used to run it at once. Now `session-start.py` runs it only if its sha256 matches the one recorded
for that path in `$XDG_CONFIG_HOME/ai-forward/session-checks-approved.json` (default `~/.config`),
outside every repository. Otherwise it reports `NOT RUN` with the approve command;
`session-start.py --approve-checks <path>` prints each argv and records the hash. Any byte change
needs a new approval. An agent can still run the approve command itself: this stops a clone from
running a contributor's commands unseen; it is not a sandbox.

## FR-093: setup installs a release

**Ruling:** *"yes should be pinned to a release tag."*

`bootstrap.py` carries `RELEASE_REF` and defaults `--ref` to it; every documented copy of the
one-line setup fetches the launcher at that tag. `--ref main` installs unreleased work. The first
tag is `v2026.10.19.4`, created on the revision-117 merge commit. `InstallCommandIsPinnedTests`
fails when a documented command fetches anything but the release, or `main` without `--ref main`.
Moving the pin is a deliberate release step: bump `RELEASE_REF`, the README commands, merge, tag.

## FR-091 and FR-094: one gate list, sharded tests

Not rulings, but the same revision. `tools/gates.py` is the only gate list; `verify-bundle.ps1`
and every CI job run it, so CI can no longer drift from the local proof. On Windows and macOS the
test suite (17 and 16 of the job minutes) runs in three shards, split by a crc32 of each test id.
The required checks `consistency-windows` and `consistency-macos` are now small jobs that pass only
when every shard passed, so branch protection is unchanged.

## Re-open triggers

- A host is observed treating the neutral answer as a refusal or as an approval.
- An approved session check is found to have run after its file changed.
- The release tag in the README is found missing on the remote.
