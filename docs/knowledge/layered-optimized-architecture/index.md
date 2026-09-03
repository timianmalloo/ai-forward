---
id: kb-loa
title: "Layered Optimized Architecture — evidence & reference material"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "architecture"
tags: [loa, architecture, patterns, reference, context-budget]
links:
  - { to: architecture, rel: relates-to }
  - { to: kb-loa-pattern-catalog, rel: refines }
review-by: "2026-12-31"
summary: >-
  The reference half of the Layered Optimized Architecture. The directive half — principles,
  archetypes, conformance criteria and the decision framework — stays in the knowledge doc an
  agent reads; the bulky lookup material lives here so consulting it is a deliberate act
  rather than a cost paid on every load.
---

# Layered Optimized Architecture — evidence & reference

The LOA directive doc (`.claude/knowledge/layered-optimized-architecture.md`) is read
**linearly**: the frame, the principles, the archetypes, the conformance criteria, the decision
framework. Part IV was different in kind — a **lookup catalog**, consulted one row at a time
once you already have a candidate pattern in hand.

At 63,831 characters it was **45% of the document** and, before the load-scope tiering, 19% of
the pack's entire always-on instruction payload. Splitting it separates *reading* from *looking
up*: the principles load without the catalog, and the catalog is fetched when a pattern choice
actually has to be defended.

| File | What it holds | When to read it |
|---|---|---|
| [`pattern-catalog.md`](pattern-catalog.md) | Part IV verbatim — every pattern with intent, structure, applicability, trade-offs, cost impact | You are choosing or justifying a specific pattern |
| `.claude/knowledge/layered-optimized-architecture.md` | Principles, archetypes, conformance, decision framework, Appendices A–K | You are making an architecture decision at all |

**Appendix A (Pattern Quick Reference)** and **Appendix B (Archetype-to-Pattern Mapping)**
deliberately stayed in the directive doc: naming a candidate is cheap and frequent, and should
not require a second load. The catalog is where you go to *defend* the candidate, not to find it.

## Why this is not the pattern for every large doc

The same split was considered for `ui-archetype-catalog.md` and **rejected**. That document is
irreducibly a catalog — sections A–H *are* the rows — so extracting them leaves a stub that
always needs its other half, turning one load into two. It is scoped instead (`load: glob`, UI
file patterns), which costs nothing on non-UI work and keeps the rows with their selector.

Splitting earns its keep only where a document mixes a **linear read** with a **lookup surface**.
Where the whole document is the lookup, scope it; do not shard it.
