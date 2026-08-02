---
id: kb-ddm-sota
title: "Domain & Data Modelling — State of the Art"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [ddd, kimball, scd, temporal, medallion, event-sourcing]
links:
  - { to: kb-domain-and-data-modelling, rel: refines }
review-by: "2026-10-31"
summary: >-
  Current best practice across the four literatures this standard crosses: tactical DDD
  (aggregate design rules), conceptual/logical/physical modelling, Kimball dimensional
  modelling (grain, facts, SCD), and modern history mechanisms (SQL:2011 temporal tables,
  event sourcing, medallion/lakehouse layering).
---

# State of the art

## 1. Domain-Driven Design (the behavioural model)

**Strategic DDD** — the *bounded context* is the unit within which a term has exactly one meaning. The ubiquitous language is context-scoped; "Account" in billing and "Account" in identity are different concepts and must not share a class. Context maps (shared kernel, customer/supplier, conformist, anticorruption layer) describe how contexts relate. *(Verified — Evans 2003; still the operative framing in 2026.)*

**Tactical DDD** — the current, stable standard for aggregate design is Vernon's four rules:

| # | Rule | Why |
|---|---|---|
| 1 | Model **true invariants** within a consistency boundary | An aggregate is the set of objects that must be consistent *at the end of a transaction*. If two things need not be transactionally consistent, they are not one aggregate. |
| 2 | Design **small** aggregates | Large object graphs produce lock contention, load cost, and slow, brittle tests. |
| 3 | Reference other aggregates **only by identity** | Direct object references couple aggregates and force wide loads; an ID keeps them independently loadable and persistable. |
| 4 | Use **eventual consistency** across aggregates | One aggregate per transaction; coordinate the rest with domain events / compensating actions. |

*(Verified — Vernon, *Effective Aggregate Design* (three-part series) and *Implementing Domain-Driven Design* ch. 10; summarised by archi-lab's Red Book rules page.)*

**Entities vs value objects.** An entity has identity that persists through attribute change; a value object is defined wholly by its attributes, is immutable, and is compared by value. The 2026 practitioner consensus is to *prefer value objects* — they shrink aggregates, carry their own validation, and remove a class of "which one is this?" defects. Money, date ranges, quantities-with-units, and identifiers are the canonical value objects.

**The aggregate root as gatekeeper.** All outside access goes through the root; no external code mutates an aggregate's interior. This is what makes the invariant enforceable in one place — the same property that finding 9 (derive-don't-store) depends on.

## 2. The three model levels

The conceptual/logical/physical separation (ANSI/SPARC lineage, still taught as the data-modelling spine) is:

| Level | Answers | Audience | Contains |
|---|---|---|---|
| **Conceptual** | *What things exist and how do they relate?* | domain experts + engineers | entities, relationships, cardinality, the ubiquitous language — **no keys, no types, no tables** |
| **Logical** | *What is the normalized/structured shape?* | data modellers | attributes, keys, normalization or the deliberate dimensional shape, still platform-agnostic |
| **Physical** | *How is it stored on this engine?* | engineers/DBAs | tables, column types, indexes, partitions, constraints, storage |

The discipline that matters is **traceability downward**: every physical object traces to a logical one, every logical one to a conceptual statement. The absence of the conceptual level is not "moving fast" — it means the conceptual model exists implicitly and unexamined.

## 3. Kimball dimensional modelling (the analytical shape, and our durable shape)

**The four-step method**, unchanged and still canonical:

1. Select the **business process** (the real-world event that produces measurements).
2. **Declare the grain** — "one row is exactly one ______." Do this before any column exists.
3. Identify the **dimensions** (the descriptive context: who, what, where, when, why, how).
4. Identify the **facts** (the numeric measurements consistent with the grain).

**Fact tables** are tall and narrow: foreign keys to dimensions + numeric, aggregatable measures + degenerate dimensions (e.g. an order number). They record events; they do not describe things.

**Additivity classes** (part of the fact's contract):

| Class | Meaning | Example |
|---|---|---|
| **Additive** | Sums correctly across *every* dimension | sale amount, quantity |
| **Semi-additive** | Sums across every dimension **except time** | account balance, inventory level, headcount |
| **Non-additive** | Does not sum at all; must be recomputed from components | ratios, percentages, unit price, rates |

**Dimensions** are wide and denormalised by default, keyed by a **surrogate key** (not the natural/business key), with the natural key retained as an attribute. Facts join dimensions on the surrogate key — this is precisely what makes point-in-time history work.

**Slowly changing dimensions**, chosen **per attribute**:

| Type | Behaviour | Use when |
|---|---|---|
| **0** | Never changes | true constants (birth date, original signup date) |
| **1** | Overwrite in place | corrections of a mistake; the old value was never *true* |
| **2** | New row per change, with effective/end interval + is-current flag | **the default whenever a past fact's meaning depends on the attribute** |
| **3** | Add a "previous value" column | a single, bounded "before/after" comparison is genuinely all that's needed |
| **4 / 6** | Mini-dimension / hybrid | rapidly-changing attributes; combined current+historical access |

*(Verified — Kimball Group "Dimensional Modeling Techniques"; corroborated by 2026 practitioner guides.)*

**Snowflaking** — normalising a dimension into its hierarchy. Kimball's standing advice for analytical models is **don't**: it adds joins and complicates queries for little storage gain. The recognised exceptions are large sparse dimensions, hierarchies with independent lifecycles, and outriggers/bridges that are genuinely their own entity (which is the domain-driven exception this standard adopts).

## 4. History mechanisms — the current options and their trade-offs

| Mechanism | How history is kept | Strengths | Costs |
|---|---|---|---|
| **SQL:2011 system-versioned temporal tables** (SQL Server, DB2, MariaDB, Postgres via extension) | DB automatically moves prior versions to a paired **history table**; `FOR SYSTEM_TIME AS OF` queries | Automatic, cannot be bypassed by application code, standardised, point-in-time queries free | Always a second physical table; captures *when* but not *who/why* without extension; history pruning is a manual DBA job; write amplification |
| **Bitemporal** (system time + valid/application time) | Both timelines modelled | Correct for "what did we *believe* on date X about period Y" — insurance, finance, regulatory restatement | Highest complexity; still requires the history table; few teams need both axes |
| **Append-only facts + Type-2 dimensions** (this standard's default) | History *is* the data: latest row = current value, prior rows = history = audit trail | One schema, not two; the audit trail is the model; new measures are new rows/columns, so measures evolve without rewriting history; naturally carries *who/why* because they are just more fact columns | Current-state reads become "latest row per key" (index/materialise); the never-update discipline must be enforced by design and test, not assumed |
| **Event sourcing** | The event log is the source of truth; state is a fold | Complete intent-level history; temporal queries; replay | Heavy: projections, versioning of events, snapshotting, eventual consistency everywhere. Usually more than the problem needs |
| **Hand-rolled shadow/audit tables + triggers** | Duplicate schema maintained by triggers | Familiar | The failure mode this standard exists to avoid: a second schema that drifts, and audit gaps when a trigger is disabled or a path bypasses it |

The load-bearing observation: **temporal tables and shadow tables both give you two schemas; append-only facts give you one.** That is the substantive argument for the dimensional stance in an operational system, and it is why "history for free, without inventing another shadow schema" is an accurate description rather than a slogan.

## 5. Where this lives in a modern data platform

The lakehouse **medallion** layering (Databricks, Microsoft Fabric, Snowflake practice as of 2025–2026) is the current expression of the classic layering:

| Layer | Classic analogue | Shape |
|---|---|---|
| **Bronze** | staging / landing | raw as-ingested, no cleansing — reprocessable |
| **Silver** | ODS / integrated detail | cleaned, conformed, deduplicated, **current-valued and detailed** |
| **Gold** | data marts | curated business models — **this is where star schemas live** |

Two things follow. First, the ODS's job (integrated, current-valued, detailed, operational) is *silver's* job — it is not the dimensional layer. Second, keeping the raw layer means business-logic changes can be reprocessed rather than migrated, which is the same evolvability argument as append-only facts, one level up.

## 6. What "state of the art" does *not* say

No mainstream authority prescribes a star schema as the **operational transactional store**. The canon separates them: DDD/3NF for the write model, dimensional for the read/analytical model, with CQRS as the recognised bridge. Our standard's crossing is therefore a **deliberate, recorded deviation**, justified by the audit/history requirement rather than by an analytics requirement — and the honest form of it keeps the DDD aggregate as the *behavioural* model while making the *durable* representation dimensional. See `open-questions.md`.
