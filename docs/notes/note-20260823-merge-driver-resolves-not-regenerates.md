---
id: "note-20260823-merge-driver-resolves-not-regenerates"
title: "A merge driver cannot regenerate a derived artifact — git runs drivers before the sources are merged"
type: decision-note
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, merge-driver, git, design-amendment]
links:
  - { to: design-coord-federation-phase3, rel: relates-to }
  - { to: adr-0009-artifact-class-and-derived-merge, rel: relates-to }
review-by: "2027-02-23"
review-suggested: []
summary: >-
  The Phase-3 design had the .gitattributes merge driver regenerating a derived artifact during
  the merge. Git runs merge drivers per file in arbitrary order, so the artifact's own sources may
  still be unmerged when its driver runs. The corrected contract is resolve-then-regenerate: the
  driver takes ours and records a debt, and `coord regen` clears it once the tree is whole.
---

# A merge driver cannot regenerate a derived artifact

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback weight.*

- **Kind:** discovered-assumption / design amendment
- **Confidence:** Verified *(established while implementing `cmd_merge_derived`; the ordering property is git's documented per-file driver invocation, and spike S11 observed two separate driver invocations within one rebase)*
- **Made during:** `/implement` of `design-coord-federation-phase3` (session 6c74f4f4)

## What the design said, and why it is wrong

`design-coord-federation-phase3` specified `coord merge-derived` as a driver that **regenerates**
the derived artifact, falling back to conflict markers if regeneration failed. Two things make that
unimplementable as written:

1. **Ordering.** Git invokes a merge driver **once per conflicting file, in arbitrary order**. A
   derived artifact's own *sources* may still be unmerged — or not yet reached — when its driver
   runs. Regenerating at that moment produces output from a half-merged tree, which is worse than
   a conflict: it is a plausible-looking artifact that matches neither side.
2. **Blast radius.** Real generators write the working tree (`docs-graph.py derive` writes
   `docs/docs-index.js`). Running one from inside a driver makes the driver write files it was not
   given — the exact hazard test `Q8` and STRIDE row `B8` exist to prevent. The driver is handed
   `%A`, a temp file; `%P` is identity, not a write target.

There was also a plain gap: the registry format is `pattern: class`, with **nowhere to put a
regenerate command**. That absence was the first sign the responsibility was in the wrong place.

## The call

**Resolve during the merge; regenerate after it.**

- The driver classifies `%P`. If it is `derived`, it resolves to **ours** (byte for byte, touching
  only `%A`) and records the path in `.agents/regen-owed.txt`. If it is anything else — including
  a path the registry cannot classify — it writes conventional conflict markers and exits 0.
- `coord regen` runs each owed generator once the tree is whole, and clears only what succeeded.
- **A failed regeneration stays owed and reports non-zero.** A stale derived artifact *looks
  finished*, which is more dangerous than a conflict, so it must be loud.
- The registry gains an optional trailing command: `pattern: derived <command...>`. A `derived`
  entry without one is a registry error — it could resolve every merge and leave the artifact
  permanently stale while claiming to be handled.

This is the shape the prior art already had. `sync-generated.ps1` in TheTerrace rebases *and then*
regenerates; the design reinvented the ordering and got it backwards.

## Alternatives dismissed

- *Regenerate in the driver and accept half-merged input.* Rejected: silently wrong output is the
  worst available outcome, and it is invisible.
- *Have the driver conflict every derived file and regenerate by hand.* Rejected — that is today's
  behaviour, and removing it is the point of the phase.
- *A `post-merge`/`post-rewrite` git hook instead of an explicit `coord regen`.* Attractive, and
  deferred rather than dismissed: `post-rewrite` does not fire on every rebase path, and a hook
  that silently regenerates during a conflicted rebase reintroduces the ordering problem. An
  explicit command the delivery loop calls is smaller and observable. Revisit if the manual step
  is measurably forgotten.

## Known wrinkle, recorded rather than fixed

`coord regen` runs the registry command with `shell=True`, which on Windows is **cmd.exe** — not
the Git Bash shell a developer typed the command in. A registry entry of `python regen.py` resolved
in Git Bash and failed in the driver's shell during the Phase-3 demo. The failure was loud and the
debt stayed owed (the designed behaviour), but the trap is real: **registry commands must be
resolvable by the platform shell**, and an absolute interpreter path is the safe form.

## Validation condition

Holds while git invokes merge drivers per file with no ordering guarantee relative to a file's
sources. If a future git offers a whole-tree resolution hook that runs after all files are merged,
revisit — that would allow regeneration inside the merge and remove the deferred debt entirely.

## Promotion rule

If a second derived-artifact mechanism appears, or if the deferred-regeneration debt turns out to
be routinely forgotten, promote to an ADR amending ADR-0009 and set this note `status: superseded`.
