---
id: kb-ddm-data
title: "Domain & Data Modelling — Data, Shapes & Constants"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [grain, scd, additivity, invariants, shapes]
links:
  - { to: kb-domain-and-data-modelling, rel: refines }
review-by: "2026-10-31"
summary: >-
  The concrete, reusable shapes: the grain statement form, the additivity classes, the
  Type-2 dimension column set, the append-only fact column set, the aggregate-design
  checklist, and the expand-migrate-contract sequence.
---

# Data, shapes & constants

Reusable, copyable shapes. These are the *forms* the standard's directives refer to.

## The grain statement (the one sentence that must exist before any column)

```
GRAIN: one row in <table> is exactly one <business event or state-spell>,
       identified by (<the key that makes it unique>),
       recorded when <the moment that produces the row>.
```

Worked examples:

- `one row in FactContribution is exactly one contribution to one account on one date, identified by (AccountKey, ContributionDate, SourceKey).`
- `one row in Fixture is exactly one match in one competition season, identified by (CompetitionSeasonKey, HomeTeamKey, AwayTeamKey, MatchNumber).`
- `one row in SquadMembership is exactly one spell of one player at one club, identified by (PlayerKey, ClubKey, EffectiveFrom).`

**The test of a good grain statement:** two different people, given the statement and a real-world scenario, produce the same number of rows.

## Additivity classes (declare one per measure)

| Class | Sums across | Typical measures | The error it prevents |
|---|---|---|---|
| **Additive** | all dimensions incl. time | amount, quantity, count, duration | — |
| **Semi-additive** | all dimensions **except time** | balance, headcount, inventory level, position value | Summing month-end balances into a nonsense annual figure |
| **Non-additive** | none — recompute from components | ratio, percentage, rate, unit price, average | Averaging averages; summing percentages |

Every measure column in a design carries its class. A measure with no stated class is an unreviewed claim.

## Type-2 dimension — the column set

| Column | Purpose |
|---|---|
| `<Entity>Key` | **surrogate** primary key — one per *version*; this is what facts join to |
| `<Entity>Id` / natural key | the business identity, stable across versions |
| …descriptive attributes… | the attributes whose change produces a new row |
| `EffectiveFrom` | inclusive start of this version's validity |
| `EffectiveTo` | exclusive end (open/`NULL`/`9999-12-31` for the current row — pick one and be consistent) |
| `IsCurrent` | convenience flag for the current version (derived from the interval; index it) |
| `VersionNumber` | optional ordinal, useful for debugging and for "the nth change" queries |
| `ChangedBy` / `ChangeReason` | who and why — the audit dimension that temporal tables do not give you for free |

**Invariants to enforce and test:** intervals for one natural key are contiguous and non-overlapping; exactly one row per natural key has `IsCurrent = true`; `EffectiveFrom < EffectiveTo`; no fact points at a dimension version whose interval does not contain the fact's event time.

## Append-only fact — the column set

| Column | Purpose |
|---|---|
| `<Fact>Key` | surrogate identity of this row |
| dimension foreign keys | the context, joined on **surrogate** keys (so history is point-in-time correct) |
| degenerate dimensions | business identifiers with no dimension table of their own (order number, transaction ref) |
| measures | the numbers, each with a declared additivity class |
| `EventAt` | when the thing happened in the world (application/valid time) |
| `RecordedAt` | when we learned it (system time) — the second axis, free if you add the column now |
| `RecordedBy` | actor/principal — this is what makes the fact table an audit trail |
| `SourceRef` | provenance: which source/message/import produced this row |
| `SupersedesKey` | optional pointer to the row this one corrects — makes "latest wins" explicit rather than implied |

**Invariants to enforce and test:** rows are never `UPDATE`d or `DELETE`d (enforce with permissions or a trigger, and prove with a test that attempts it); the current value for a key is a deterministic function of the rows (define it once — usually max `RecordedAt`, tie-broken by `<Fact>Key`); replaying the rows reproduces the current state exactly (the rebuild test — TheTerrace FR-089 exists because that claim was made four times and never tested).

## Aggregate design checklist (per aggregate)

- [ ] The **invariant** this aggregate exists to protect is written in one sentence.
- [ ] Everything inside the boundary is needed to enforce that invariant *in one transaction*.
- [ ] Nothing inside the boundary is there merely because it is related.
- [ ] Other aggregates are referenced **by identity only**.
- [ ] The aggregate is small enough to load and save without a wide join.
- [ ] Cross-aggregate consistency is achieved by a domain event / compensating action, not a bigger transaction.
- [ ] Value objects are used for everything without its own identity (money, ranges, quantities-with-units, identifiers).

## Expand-migrate-contract (the safe schema-change sequence)

1. **Expand** — add the new shape (nullable/defaulted). Old and new code both work.
2. **Migrate** — dual-write, then backfill. **Backfill never guesses**: rows that cannot be attributed deterministically are surfaced for a human, never inferred.
3. **Move reads** — switch readers to the new shape behind a flag; verify equivalence against the old shape.
4. **Contract** — drop the old shape only after no reader remains, in a separate change.

Each step is independently deployable and independently reversible. A migration is not done when it compiles — it is done when the thing that deploys it also applies it, and when its `Down` path has been exercised.

## Naming conventions that prevent a known defect class

| Convention | Prevents |
|---|---|
| Dimension tables `Dim<Entity>` / entity name; fact tables `Fact<Process>` | Ambiguity about whether a table describes a thing or records an event |
| Surrogate keys `<Entity>Key`; natural keys `<Entity>Id` | Joining a fact to a natural key and silently losing point-in-time correctness |
| One name for one concept, repo-wide, taken from the glossary | Two names for one FK (Meridian found exactly this in its entity model) |
| Derived values named for their derivation, never stored under the same name as their source | "One quantity, two homes" — the highest-frequency observed defect class |
