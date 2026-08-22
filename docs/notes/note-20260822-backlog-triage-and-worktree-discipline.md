---
id: note-20260822-backlog-triage-and-worktree-discipline
title: "Decision note — revision-42 backlog triage, and worktree-per-session"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, triage, worktree, coordination, continuous-improvement]
links:
  - { to: forensic-review-rev42-backlog, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2027-02-22"
review-suggested: []
summary: >-
  Four sub-ADR decisions taken while clearing the revision-42 backlog and adding
  worktree-per-session: withdrawing FR-050 rather than acting on it, closing FR-054 as won't-do
  with a falsifiable trigger, bounding the bare-handle sweep at write sites, and extending
  coord-core.py rather than adding a parallel worktree tool.
---

# Decision note — revision-42 backlog triage, and worktree-per-session

Four decisions below ADR weight that shaped the work, recorded before the session closes (V17).

## 1. FR-050 was withdrawn, not actioned — *Verified*

**Decided:** close FR-050 as **not a defect** and register the reasoning error as a class, rather
than delete or regenerate `docs/_site/`.

**Why.** The finding's evidence was a **file mtime** and a revision distance. Checking the content
instead: it is a hand-maintained hub (`check_static_page_links` says so in its own docstring), all
8 card links resolve, it holds zero hard-coded counts that could drift, and two tests plus a CI
gate assert its shape. **The recommended remedy — deletion — would have broken the build.** The old
mtime meant *nothing needed changing*, which is the correct state for an unchanged file whose every
claim is still true.

**Alternatives dismissed.** *Regenerate it anyway* — there is nothing to regenerate from; it is not
generated. *Delete it and fix the tests* — that is destroying a working surface to satisfy a finding
whose premise is false. *Leave it open* — carrying an item whose premise has been falsified is how a
backlog stops being believed.

**What this cost, and why it is recorded.** The disconfirming check in the original finding asked
only "is it referenced from the portal?" and never "is anything it says wrong?". That is a proxy
standing in for the property actually cared about — the substitution
`instrumentation-over-inference.md` exists to forbid — committed in the same session that wrote
that document. Registered as class **PACK-N**.

## 2. FR-054 closed won't-do, with a trigger — *Verified*

**Decided:** do not split `docs-graph.py` (1,599 lines). Re-open **when a defect is attributed to
its size**.

**Why.** No failure is attributed to it; the backlog itself retained it as `todo`, not `issue`,
after the Simplifier's challenge. It is the most-invoked script in the pack, so a
characterization-first split is a `/migrate` job with real blast radius. Doing it alongside nine
findings and a new capability would produce a large change that is red in the middle — one you
cannot bisect when it breaks (BoK V.2).

**The honest risk of this decision:** carrying an item forward repeatedly is the **PACK-B** pattern
this repository registered about itself. That is why the closure is explicit and the re-open
condition is falsifiable, rather than the item quietly appearing in a fifth review.

## 3. The bare-handle sweep was bounded at write sites — *Verified*

**Decided:** fix all 7 handles in `audit-log.py` (FR-053's scope, which named 4), fix the **write**
sites in three other scripts, and **register** the ~30 remaining read sites rather than converting
them blind.

**Why.** The class sweep (CI2) found the shape in six scripts. Write sites carry the real hazard —
a truncated file on the exception path — and are single-line, mechanical fixes. The read sites
include `for ln in open(...)` forms that need body re-indentation, in scripts whose test coverage
was thin until this same session. **My own scripted conversion introduced an `IndentationError`,
caught within seconds by the suite** — which is the direct evidence for bounding the sweep rather
than the argument against sweeping at all.

**Alternatives dismissed.** *Convert all 36* — a broad diff with a demonstrated failure rate, in
the middle of a session doing ten other things. *Fix only the 4 named* — that is the RIG-C failure
(fix the instance, leave the class live) which FR-049 exists to punish. CI3 explicitly permits
registering a discovered sibling with an owner when fixing it in the same change is not safe.

## 4. Worktree lifecycle extends `coord-core.py` — *Verified*

**Decided:** add `worktree new|list|cleanup` to `coord-core.py` rather than create a new script.

**Why.** `coord-core.py` **already** owns worktree identity (`_worktree_key`), one-session-per-tree
occupancy (`COORD-WORKTREE-OCCUPIED`, whose own message already advises *"use a separate
worktree"*), and the primary-checkout resolution that makes one event log visible from every tree.
A separate tool would have re-implemented all three and then had to agree with them. One concern,
one owner.

**The design point worth keeping:** creation was the easy half. The half that rots is cleanup, so
it is **fail-safe by construction** — a tree is removable only when it is not primary, not the cwd,
clean *including untracked*, carries no commit absent from every other ref, and is unheld. Every
refusal is printed with its reason, because a silent skip is indistinguishable from finding
nothing. Deletion is opt-in. Proven end to end on a real repository: create → live-session HELD →
untracked-file HELD → unmerged-commit HELD **even with `--remove`** → clean/merged SAFE → reaped →
metadata pruned to zero.

**Assumption carried forward.** `assume:` the 8-hour staleness window inherited from `cmd_session`
is the right horizon for "this session is gone". It is inherited, not derived. **Confirm:** the
first time a human is blocked by a tree held by a dead session, or the first time a genuinely live
long session is declared stale. **If false:** cleanup either refuses forever (annoying, safe) or
reaps a live session's tree (dangerous) — the latter is bounded by the dirty/unmerged hard stops,
which is why the window is acceptable as an inherited default rather than a researched one.
