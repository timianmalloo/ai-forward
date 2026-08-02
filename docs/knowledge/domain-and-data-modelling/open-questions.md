---
id: kb-ddm-open-questions
title: "Domain & Data Modelling — Open Questions & Failure Modes"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [open-questions, risks, failure-modes]
links:
  - { to: kb-domain-and-data-modelling, rel: refines }
review-by: "2026-10-31"
summary: >-
  What the research could not settle (three Flagged claims), the disconfirming case against
  this standard's central stance, and the known failure modes of domain and data modelling
  observed in two production repos.
---

# Open questions & failure modes

## Flagged — the research could not settle these

**F1 — The read-path cost of "latest row per key" at scale.** Append-only facts make current-state reads a window/`MAX` query rather than a point lookup. Every source agrees this is indexable and materialisable; none gives a threshold at which it becomes the dominant cost for a given workload. *Resolution path:* measure it per project against a stated performance budget (Engineering Governance §6), and treat a materialised current-state view as an explicitly-labelled, rebuildable cache with an equality test — not as a second source of truth.

**F2 — Whether Type-1 overwrite is ever acceptable for a name-like attribute.** TheTerrace flags `Team.CanonicalName` and `Player.CanonicalName` as Type-1, and notes honestly that a rename therefore rewrites history. The argument for Type-1 is that a display name is a *label*, not a fact anyone reasons over; the argument against is that "which name did the report use last season" is a real question in exactly the domains that care. *Resolution path:* decide per attribute, and record the decision — a Type-1 attribute is a *decision to discard history*, and must be written down as one.

**F3 — Whether "one bounded context" survives the next subdomain.** Both repos deliberately chose a single bounded context. That is almost certainly correct at their current size (Evans warns against premature context splitting more often than against a single context). It is unknown whether the boundary holds when a genuinely different language arrives. *Resolution path:* the trigger to revisit is *linguistic*, not structural — the moment one word means two things to two stakeholders, the context is splitting whether or not the code has noticed.

## The disconfirming case against this standard's central stance

Stated as strongly as it can be, because the standard should survive it:

> *"You are using an analytical modelling technique as an operational schema. Kimball never proposed that. The transactional model's job is to enforce invariants at write time, and a fact table enforces nothing — it accepts every row. You will find yourself reconstructing current state on every read, indexing your way out of it, and eventually building the normalised model you avoided, next to the facts. Use a normalised write model with temporal tables; you get the same history with the database enforcing it, and you keep your invariants."*

**Why the standard survives it, and what it concedes:**
- It **concedes** that a fact table enforces nothing. That is exactly why the standard keeps the **DDD aggregate as the behavioural model**: invariants are enforced in the domain layer, at write time, by the aggregate root — the dimensional shape is the *durable representation*, not the validator. A design that drops the aggregate and keeps only tables has lost the argument.
- It **concedes** the read-path cost (F1) and requires it to be measured, not hand-waved.
- It **holds** on the requirement: when the audit trail *is* the requirement, temporal tables give you a second schema, no `who`, no `why`, and DBA-managed pruning. Append-only facts give you one schema whose rows carry actor, reason, source and both time axes.
- It **holds** on evolvability: a new measure is a new row or column, not a rewrite of history. That is the property the user named first — "measures can evolve over time" — and it is the property normalised-plus-temporal does *not* have cheaply.

**When the disconfirming case wins:** when the requirement is only "recover a previous value" (not "explain every change"), and the domain has no analytical dimension to it. Then temporal tables are the smaller correct answer and the Solution-Selection Ladder says take them.

## Known failure modes (observed, not theorised)

Each was seen in a production repo; each is why a directive in the standard exists.

| # | Failure mode | What it looked like | Directive it produced |
|---|---|---|---|
| 1 | **One quantity, two homes** | A new call site wired to a different source than its neighbours; a Monte Carlo collapsed to a one-year simulation reporting 100% success | Derive-don't-store; single source of truth per quantity |
| 2 | **Stored fact that nothing writes** | A stored `HasProductionSource` boolean beside a `HasProductionSource()` function; the stored copy was maintained by nothing, so the product could never leave demo mode | Every persisted field has a writer *and* a reader, both traced |
| 3 | **Persisted field with no compute reader** | A value stored, entered on a real screen, round-tripped through the API and round-trip-tested — and read by nothing that computes anything | The reader trace: classify every reference as write / CRUD / schema / **compute** |
| 4 | **Entity that accreted** | A profile entity nobody decided on, discovered later during refactor | The conceptual model is a required artifact; a physical object with no conceptual statement is a finding |
| 5 | **Aggregate too large** | An initial design put fifteen financial tables under one root — a fifteen-table load on every save | Vernon rule 2; caught in review, kept visible in the doc rather than edited away |
| 6 | **Grain inferred instead of declared** | Three design drafts for "which season does this fixture belong to" all died on rescheduled matches | Declare the grain; put the season in the key; ask the authority, don't reconstruct |
| 7 | **Semi-additive measure summed** | Balances summed across months | Additivity is declared per measure |
| 8 | **Type-1 where Type-2 was needed** | A mutable `TeamId` on a player would not go stale — it would silently rewrite which club a past match was played for | History rule decided per attribute before the attribute ships |
| 9 | **Declared-but-never-written facet** | Facets `Score` and `Status` declared in the design, never written, so a score change re-recorded everything | A declared shape with no write path is an unimplemented design, not a design |
| 10 | **Rebuildability claimed, never tested** | "The projection is rebuildable from the corpus" — asserted four times, never implemented, never replayed | The rebuild test is mandatory when the claim is made |
| 11 | **Migration that compiles but is never applied** | A migration that built fine and was never run by the deploy | A migration is done when the deployer applies it and the `Down` path has been exercised |
| 12 | **Backfill that guessed** | — (prevented) | Backfill never guesses; unattributable rows go to a human |
