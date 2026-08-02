---
id: kb-ddm-comparables
title: "Domain & Data Modelling — Comparables"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [comparables, cqrs, event-sourcing, data-vault, anchor-modeling]
links:
  - { to: kb-domain-and-data-modelling, rel: refines }
review-by: "2026-10-31"
summary: >-
  How other approaches frame and solve "a durable model that keeps history and an audit trail
  without a shadow schema" — CQRS, event sourcing, Data Vault, anchor modelling, temporal
  tables, and the two in-repo precedents (Meridian ADR-0022, TheTerrace hub-and-satellite).
---

# Comparables

Each row is a named approach to the same problem: **keep a durable model whose measures can evolve, that carries history and an audit trail, without maintaining a second schema.**

## Industry approaches

### CQRS (Command Query Responsibility Segregation)
**Frames it as:** two models — a normalised write model enforcing invariants (DDD aggregates) and one or more denormalised read models shaped for queries.
**Does well:** each side is optimised for its job; the read model can be dimensional without compromising the write model's invariants; well-understood.
**Does badly:** you now maintain a projection and its lag; the read model is *derived*, so it is not itself the audit trail; and "light CQRS" (read services returning DTOs from the same tables) is what most teams actually build, which gets none of the separation and all of the naming.
**Relation to our stance:** our standard is closer to *collapsing* CQRS — the durable dimensional shape serves both, and where a genuine projection is needed it is an explicitly-labelled, rebuildable cache (finding 9).

### Event sourcing
**Frames it as:** the event log is the truth; current state is a left-fold over events.
**Does well:** the most complete history and audit trail available — you keep *intent*, not just before/after. Temporal queries and replay are native.
**Does badly:** the cost is famously high — event versioning/upcasting, projection rebuilds, snapshotting, eventual consistency leaking into the UI, and a much harder debugging story. Teams routinely regret adopting it for domains that only needed history.
**Relation to our stance:** append-only facts are "event sourcing's history benefit at a fraction of the cost" — you keep the *what changed* rows without committing to fold-everything-from-events as the only read path.

### Data Vault 2.0
**Frames it as:** hubs (business keys), links (relationships), satellites (descriptive attributes, historised by load date).
**Does well:** auditability and source-traceability are first-class; extremely resilient to source change; parallel loading.
**Does badly:** query complexity is high enough that it almost always needs a dimensional presentation layer on top — so you are back to two schemas.
**Relation to our stance:** the *hub-and-satellite* idea is directly useful and is exactly what TheTerrace independently arrived at for cross-provider identity (`Team` + `TeamProviderRef`). Adopt the pattern where identity resolution demands it; do not adopt the whole methodology.

### Anchor modelling / 6NF temporal
**Frames it as:** decompose to the point where every attribute has its own historised table.
**Does well:** schema evolution is purely additive; full temporality.
**Does badly:** an explosion of tables and joins; needs generated views to be usable at all.
**Relation to our stance:** the same additive-evolution benefit is available from append-only facts without the join explosion. Not recommended.

### SQL:2011 system-versioned temporal tables
**Frames it as:** a platform feature — the database keeps history for you.
**Does well:** it cannot be bypassed by application code, which is a genuine correctness advantage over any application-maintained scheme; point-in-time queries are free; no application code at all.
**Does badly:** always a paired history table (so, two schemas); records *when* but not *who* or *why* without extra columns and session context; retention/pruning is manual.
**Relation to our stance:** the honest competitor. Meridian evaluated it, its own knowledge base recommended it, and the owner's requirement (the *facts themselves* should be the audit trail) superseded it. Where the requirement is only "recover an old value", temporal tables are the smaller answer and should win on the Solution-Selection Ladder.

### Bitemporal modelling
**Frames it as:** two independent time axes — when the fact was *true* and when we *recorded* it.
**Does well:** the only correct answer for restatement-heavy domains (finance, insurance, regulatory reporting) where "what did we believe on Tuesday about Monday" is a real question.
**Does badly:** doubles the temporal reasoning burden on every query and every developer.
**Relation to our stance:** adopt only when the domain genuinely restates. Append-only facts extend to bitemporal naturally (add the valid-time interval as fact columns) — which is another argument for the shape.

## In-repo precedents (the strongest evidence, because they are ours)

### Meridian — ADR-0022 "append-only facts, versioned dimensions"
The owner's requirement, verbatim: *"Every transaction or change should be an update in the correct fact table(s) and then I should be able to go back in time on them… the fact tables effectively maintain history AND become the audit trail for the application. The current record in a fact table is the latest record and all prior records become the history."*

The ADR's own analysis is the key comparable finding: *"What the owner described is, precisely, the dimensional model… The owner asked for star-schema reasoning because the requirement is a dimensional requirement. It simply arrives through the audit door rather than the analytics door."*

Also adopted there and worth carrying: grain declared per fact table; semi-additive balances named explicitly; Type-2 for filing status, retirement date, account ownership, contribution rate; **age derived from birth date, never stored** (a derive-don't-store decision taken specifically to prevent a repeat of a two-sources defect); one bounded context; light CQRS with no event sourcing.

### TheTerrace — hub-and-satellite + declared grain per table
Grain is declared per table as a matter of course:

| Table | One row is… | Kind |
|---|---|---|
| `Fixture` | one match in one competition season | fact |
| `ProviderObservation` | one (source, entity, facet) payload at one instant | fact (append-only) |
| `Prediction` | one member's forecast of one match | fact |
| `SquadMembership` | one spell of a player at a club | **Type-2 row** |
| `Team`, `Player`, `Competition`, `Season` | one thing identified by us across sources | dimension |
| `TeamProviderRef`, … | one source's name for one thing | dimension bridge (domain-motivated snowflake) |

Two lessons travel with it. First, `SquadMembership` is modelled as an interval precisely because *"a `Player.TeamId` would not merely go stale, it would silently rewrite history"* — the clearest one-line statement of why Type-2 exists. Second, an open question is left honestly flagged: `Team.CanonicalName` and `Player.CanonicalName` are Type-1 and therefore *do* silently rewrite history on a rename.

### The grain lesson that cost three design drafts
TheTerrace FR-102: three attempts to answer "which season does a fixture belong to" all died on rescheduled matches. The resolution was not a cleverer date rule but a grain declaration — *one match in one competition season* — which puts the season in the key rather than inferring it from a kick-off date. **Ask the authority; do not reconstruct.** This is the canonical worked example for "declare the grain before the columns."

## What the comparison yields

1. Every approach that keeps history in a *second* structure (shadow tables, temporal history tables, Data Vault satellites + a star on top) pays the two-schema tax. Only append-only facts and event sourcing make the history the primary data — and of those two, append-only facts are dramatically cheaper.
2. Every approach that succeeds at auditability declares its grain and separates the *thing* from the *thing's change*. That separation — dimension vs fact — is the durable insight, independent of vendor or platform.
3. The pattern to borrow selectively from Data Vault is **hub-and-satellite for identity resolution across sources**; the methodology as a whole is more than most systems need.
