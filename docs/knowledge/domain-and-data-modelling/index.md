---
id: kb-domain-and-data-modelling
title: "Domain & Data Modelling — DDD, conceptual models, ODS, star schemas (domain knowledge)"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [ddd, aggregate-root, conceptual-model, ods, star-schema, dimension, fact, scd, grain, temporal]
links:
  - { to: architecture, rel: relates-to }
  - { to: kb-pack-evolution, rel: relates-to }
review-by: "2026-10-31"
summary: >-
  Sourced evidence base for the pack's data-model-primacy directive: Domain-Driven Design
  (bounded contexts, aggregates, entities vs value objects), the conceptual/logical/physical
  model levels, the Operational Data Store, and Kimball dimensional modelling (grain, facts,
  Type-2 dimensions, snowflaking). Establishes why "core entities as dimensions, change-over-time
  as facts" gives history and audit without a shadow schema — and where that stance costs.
---

# Domain & Data Modelling — domain knowledge

**Domain & problem:** Two AI-Forward repos in active development (Meridian, TheTerrace) independently produced the same finding: *most of their production defects were data-model defects presenting as application defects*. Both then wrote a local "data model is the highest-priority decision" directive because the pack had none. This knowledge base establishes the evidence for a pack-level standard: how to derive the **conceptual domain model** (Domain-Driven Design), how to choose the **durable representation** so that measures can evolve and history is free (dimensional modelling), and where the naive version of that stance is wrong.

**Canonical framing:** the field splits this into two literatures that are usually kept apart — **DDD** (Evans 2003, Vernon 2013) governs the *behavioural/transactional* model; **dimensional modelling** (Kimball) governs the *analytical* model, downstream of an **ODS** (Inmon). Our framing deliberately crosses them: we want the *dimensional shape* (dimensions + facts) as the **durable representation of the operational domain**, not only as a downstream analytical star. That crossing is defensible and is what buys history and audit trails for free — but it is a **deviation from the canon and must be made knowingly** (see finding 6 and `open-questions.md`).

**Compiled:** 2026-08-02 · **Lead:** Domain Researcher · **Status:** fresh

## Headline findings

1. **The conceptual model is a distinct, mandatory level — and skipping it is how models rot.** The three-schema discipline (conceptual → logical → physical, ANSI/SPARC lineage) exists because a physical model that cannot be traced back to a conceptual statement is unexplainable, and an unexplainable model is one nobody can safely change. Where the conceptual level is skipped, the logical model is authored implicitly by whoever writes the first migration, and the real conceptual model is discovered years later during a painful refactor. — *(Verified — three-schema/conceptual-modelling literature; corroborated in-repo by Meridian's `HouseholdProfile`, an entity that "accreted, because there was no conceptual statement for it to contradict")*

2. **Aggregate boundaries are drawn by *invariants*, not by relationships.** Vernon's four rules are the operative standard and are stable as of 2026: (i) model true invariants within a consistency boundary; (ii) design **small** aggregates; (iii) reference other aggregates **only by identity**; (iv) use **eventual consistency** across aggregate boundaries — one aggregate modified per transaction. The failure mode the rules exist to prevent is the "everything-related-is-one-aggregate" graph, which produces contention, load cost and painful tests. — *(Verified — Vernon, *Effective Aggregate Design* / *Implementing DDD* ch. 10; archi-lab summary of the Red Book rules)*

3. **Declaring the fact grain is the single highest-leverage modelling act, and it precedes columns.** Kimball's four-step method is choose the business process → **declare the grain** ("one row is exactly one ______") → identify dimensions → identify facts. Ambiguous grain is what produces silently wrong aggregations, because a join at the wrong granularity inflates measures without erroring. Every dimension key and every measure must conform to the declared grain. — *(Verified — Kimball Group, Dimensional Modeling Techniques; practitioner guides 2026)*

4. **Facts must be classified additive / semi-additive / non-additive, and the classification is part of the contract.** Summing a balance across time periods is the standing category error in any financial or inventory system: balances are *semi-additive* (they sum across every dimension except time). A measure whose additivity is unstated will eventually be summed by someone. — *(Verified — Kimball dimensional-modelling canon; corroborated in-repo: Meridian names semi-additive balances "the standing category error in a financial system")*

5. **Type-2 slowly-changing dimensions are the mechanism that stops history being silently rewritten.** A mutable attribute on a current-state row (`Player.TeamId`, `Account.Owner`, `Person.FilingStatus`) does not merely go stale — it **retroactively changes the meaning of every past fact that joined to it**. Type-2 (surrogate key + natural key + effective/end interval + is-current flag) preserves the version that was true when the fact occurred; facts join on the **surrogate** key, which is what makes point-in-time correctness automatic rather than a query-time reconstruction. SCD type is chosen **per attribute**, not per table. — *(Verified — Kimball SCD canon; practitioner star-schema references 2026)*

6. **"Core entities as dimensions + change-over-time as append-only facts" *is* the dimensional model, arriving through the audit door rather than the analytics door — and it genuinely removes the shadow schema.** The mainstream alternative for history is SQL:2011 **system-versioned temporal tables**, which are excellent but *always* materialise a paired history table, capture *when* but not *who/why* without extension, and put pruning on the DBA. Modelling change as **appended fact rows** instead makes the history the primary data rather than a side-effect: the latest row is the current value, all prior rows are the history, and the same rows are the audit trail — one schema, not two. The cost is real and must be accepted knowingly: current-state reads become "latest row per key" queries (needing indexing/materialisation), and the discipline of never updating a fact must be enforced, not assumed. — *(Inferred — synthesis of the Kimball fact-table canon with the SQL:2011 temporal-table trade-off literature; corroborated in-repo by Meridian ADR-0022, which chose exactly this and superseded its own knowledge base's temporal-table recommendation)*

7. **ODS and star schema are two different layers doing two different jobs, and conflating them is a real error.** An **ODS** (Inmon) is subject-oriented, integrated, **current-valued, volatile and detailed** — built for operational reporting and immediate lookups. A **star schema** is the analytical shape: denormalised dimensions around a fact table, historised, non-volatile. In modern lakehouse terms the medallion layering (bronze/silver/gold) plays the same roles, with dimensional models living in **gold**. Saying "persist in ODS terms so we get fact tables and dimensions" collapses the two; the honest statement is *"one integrated operational store whose durable shape is dimensional."* — *(Verified — Inmon ODS definition; Databricks/Microsoft Fabric medallion documentation 2025–2026; corroborated in-repo: TheTerrace's own knowledge base corrects the same phrasing)*

8. **Snowflaking is what Kimball explicitly advises against for the *analytical* shape — but is the right answer when the *domain* requires the hierarchy.** Kimball's default is flat, denormalised, wide dimensions for query simplicity and performance. Normalising a dimension into its hierarchy (snowflake) is warranted when the hierarchy is itself a domain concept with its own identity, invariants and lifecycle (a provider-reference bridge, an org hierarchy that is versioned independently, a very large sparse dimension). The rule that survives both camps: **snowflake because the domain model demands the entity, never because normalisation feels tidier.** — *(Verified — Kimball Group technique on denormalised dimensions; corroborated in-repo by TheTerrace's hub-and-satellite `Team`/`TeamProviderRef` bridge, which is a domain-motivated snowflake)*

9. **Derive, don't store: two definitions of one fact is a defect signature, not a design choice.** Both repos independently converged on this after production defects (Meridian FR-129/FR-174/FR-192; TheTerrace FR-061/FR-088). A quantity that is both stored and computed will drift, and the stored copy is usually the one that is maintained by nothing. The dimensional stance sharpens the rule: **facts are stored; aggregates, roll-ups, current-state pointers and derived classifications are computed** — and anything stored for performance is an explicitly-labelled, rebuildable cache with a test proving it equals its derivation. — *(Verified — in-repo defect records across two independent codebases; consistent with the DDD rule that invariants live in one place)*

10. **Schema change is the irreversible half of the system, so the durable representation must be chosen for evolvability, not just for correctness today.** Code is refactorable; a schema that has taken data is not. Expand-migrate-contract (add the new shape → dual-write/backfill → move reads → drop the old) is the standard safe path, and backfill **never guesses** — rows that cannot be attributed deterministically are surfaced for a human. The dimensional stance helps here specifically: a *new measure* is a new fact (or a new column on a fact) rather than a mutation of existing rows, so measures can evolve without rewriting history. — *(Verified — expand-migrate-contract is the pack's existing Data & Persistence standard; the "backfill never guesses" rule is quoted from Meridian's data-modelling knowledge base)*

## Confidence summary

- **Verified: 9 · Inferred: 1 (finding 6) · Flagged: 3** (recorded in `open-questions.md`).
- The load-bearing **Inferred** claim is finding 6 — the *crossing* of the transactional and dimensional literatures. No authority tells you to use a star schema as your operational durable representation; the finding is a synthesis, and it is the one a reader should attack first. It is corroborated by a real ADR in a production repo, not by a textbook.
- Load-bearing **Flagged** claims: (a) the read-path cost of "latest row per key" at scale; (b) whether Type-1 overwrite is ever acceptable for a name-like attribute; (c) whether the "one bounded context" simplification both repos chose survives their next subdomain.

## Design implications (what the next phase should do with this)

1. **Make the conceptual model a required, named output of `/specify` and `/design`** — bounded context, ubiquitous language, entities vs value objects, aggregate roots and the invariant each one is bounded by. It comes *before* the UI layer, the endpoints and the tables.
2. **Make grain declaration a gate.** No table, no measure, no projection without "one row is exactly one ______", the additivity classification, and the history rule for every attribute that can change under a past result.
3. **Adopt dimensions + append-only facts as the default durable representation**, stated as a deliberate, recorded deviation from the "star = analytics only" canon, with the read-path cost accepted explicitly (finding 6).
4. **Encode derive-don't-store as a checkable rule**, since it is the highest-frequency defect class observed across both repos.
5. **Keep the ODS/star distinction honest in the wording of the standard** (finding 7) so the directive does not teach a conflation.
6. **Permit snowflaking only with a domain justification** (finding 8), recorded like any other pattern choice.

## Files

| File | Contents |
|---|---|
| `state-of-the-art.md` | Current best practice in DDD, dimensional modelling, temporal/history, and lakehouse layering |
| `comparables.md` | How other products/literatures frame and solve "durable model with history" |
| `references.md` | Standards, seminal works, vendor documentation |
| `data-and-constants.md` | The concrete rules, shapes and invariants (SCD columns, grain statement form, additivity classes) |
| `glossary.md` | The ubiquitous language of this domain |
| `open-questions.md` | What the research could not settle; the known failure modes |
| `sources.md` | Full source list with access dates |
