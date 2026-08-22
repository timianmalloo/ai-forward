---
id: "note-20260820-spike-corpus-assertion"
title: "A verification script reported COLLISION-FREE over zero identifiers, because it only compared set size to list size"
type: decision-note
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, controls, spike, empty-corpus, continuous-improvement]
links:
  - { to: architecture-agent-coordination, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-02-20"
review-suggested: []
summary: >-
  While spiking the allocator for ADR-0008, the verification harness printed "COLLISION-FREE WITHOUT
  COORDINATION" over an empty result set — the worker processes had died on a syntax error and the
  check only asserted len(set(x)) == len(x), which is trivially true of nothing. Recorded as an
  architectural rule (R4) rather than a code fix, because the defect was in the shape of the assertion.
---

# A verification script reported COLLISION-FREE over zero identifiers

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback weight.*

- **Kind:** discovered-assumption
- **Confidence:** Verified *(observed directly during spike S1b for `/define-architecture` on the agent-coordination layer; the run printed `issued=0 unique=0 collisions=0` followed by `VERDICT: COLLISION-FREE WITHOUT COORDINATION`)*
- **Made during:** `/define-architecture` — agent coordination (session 6c74f4f4)

## What happened

Spike S1b exists to test the one condition that defeated the previous allocator: two sessions minting an
identifier **before either has pushed**. Eight worker processes were spawned, each pinned to the same
millisecond, each issuing 500 ids, and the parent asserted uniqueness with

```python
"COLLISION-FREE" if len(set(flat)) == len(flat) else "COLLIDED"
```

On the first run every worker died on a syntax error introduced by heredoc escaping, `flat` was empty,
and the assertion passed — because `len(set([])) == len([])` is true. The harness announced the exact
verdict the architecture wanted to hear, over no evidence at all.

It was caught only because `issued=0` was printed on the line above and someone read it.

## The call

**This is `GATE-CORPUS-A` — a control that scanned nothing and reported clean** — and the honest response
is not to patch this script. It is to make the shape a standing rule, because the same assertion shape
recurs everywhere: any check written as *"no bad items were found"* passes vacuously when *no items were
found*, and the two outcomes render identically.

Recorded as **architecture rule R4** in `architecture-agent-coordination.md` §9 and made a condition of
the council gate: **every control asserts its corpus was the size it assumed before it is allowed to
report a pass.** The spike now asserts `len(flat) == 4000` and prints `INCONCLUSIVE` otherwise.

The circumstance is worth keeping: this happened **while building a control**, in an architecture whose
own gate condition requires controls to be proven red first, authored by someone who had just written
that condition. That is the same shape as the recorded instances of `DUP-A` and `ONE-A`, where the class
was committed by the person citing the rule against it — which is evidence that these classes are
structural rather than about care.

## Alternatives dismissed

- *Fix the script and move on.* Rejected: a fix that stops at the instance is not finished (CI2), and the
  assertion shape is repo-wide rather than local to this spike.
- *Raise it as a full defect-class entry now.* Deferred rather than dismissed. `GATE-CORPUS-A` already
  exists in HealthWatch's register; the useful work is a **sweep** — find the checks in this repo that
  pass vacuously on an empty corpus — and that is its own task, not a side effect of an architecture run.

## Validation condition

Holds while controls in this repo are written as "no bad items found". If a shared assertion helper is
introduced that makes the corpus-size check structural (so a vacuous pass cannot be expressed), this note
retires and the rule moves into that helper's contract.

## Promotion rule

If the sweep finds instances beyond this one, promote to a defect-class entry in
`docs/lessons/defect-classes.md` with a control that fails on the shape, link it `supersedes` this note,
and set this note `status: superseded`.
