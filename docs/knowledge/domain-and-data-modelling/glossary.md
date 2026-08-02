---
id: kb-ddm-glossary
title: "Domain & Data Modelling — Glossary"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [glossary, ubiquitous-language]
links:
  - { to: kb-domain-and-data-modelling, rel: refines }
review-by: "2026-10-31"
summary: >-
  The ubiquitous language of domain and data modelling, each term defined with what it is
  NOT — the near-miss disambiguation that stops two people using one word for two things.
---

# Glossary

*Each entry gives the definition in this pack's voice and, where it matters, the **near miss** it must not be confused with.*

**Aggregate** — a cluster of entities and value objects treated as one unit for data change, bounded by an invariant that must hold at the end of every transaction. *Not:* "everything related to this entity." Relatedness does not create an aggregate; a shared invariant does.

**Aggregate root** — the single entity through which all outside access to an aggregate passes. *Not:* the biggest or most important table. It is the gatekeeper that makes the invariant enforceable in one place.

**Additivity** — whether a measure can be summed, and across which dimensions: additive (all), semi-additive (all but time), non-additive (none). *Not:* a data type.

**Bounded context** — the boundary within which a term of the ubiquitous language has exactly one meaning. *Not:* a module, a service, or a schema — though it often maps onto one.

**Conceptual model** — the entities, relationships and rules of the domain in the domain's own words, with no keys, types, or tables. *Not:* an ER diagram of your database. The direction of travel is conceptual → logical → physical, never the reverse.

**Conformed dimension** — a dimension used identically by more than one fact table, so measures from both can be compared along it. *Not:* a copied dimension; the point is that it is *the same* one.

**Degenerate dimension** — a business identifier that lives on the fact row with no dimension table of its own (an order number, a transaction reference). *Not:* a missing dimension.

**Derive-don't-store** — the rule that a quantity computable from other data is computed, not persisted; anything persisted for performance is a labelled, rebuildable cache with a test proving it equals its derivation. *Not:* a prohibition on caching — a prohibition on *two definitions of one fact*.

**Dimension** — a table describing a *thing* and its attributes, providing the context by which facts are filtered and grouped. *Not:* a lookup table; a dimension carries the history rule for its attributes.

**Entity** — a domain object with an identity that persists through attribute change. *Not:* "a database table" and *not:* a value object.

**Fact** — a row recording that something *happened*, or that a measure *had a value*, at a grain. In this standard facts are **append-only**, so the fact table is simultaneously the current state, the history, and the audit trail. *Not:* a row that gets updated.

**Grain** — the precise meaning of one row: "one row is exactly one ______." Declared before any column exists. *Not:* the primary key (the key *implements* the grain), and *not:* the level of aggregation you happen to query at.

**Invariant** — a rule that must be true at the end of every transaction. It is what draws an aggregate boundary. *Not:* a validation rule on an input field (that is a constraint on a command, which may be broader).

**Logical model** — the platform-agnostic structural model: attributes, keys, and the chosen shape (normalised or dimensional). *Not:* the physical schema, and *not:* the conceptual model.

**Medallion (bronze/silver/gold)** — the lakehouse layering: raw as-ingested → cleaned, conformed, current-valued detail → curated business models (where star schemas live). *Not:* three copies of the same thing for no reason; each layer has a distinct job and a distinct audience.

**ODS (Operational Data Store)** — a subject-oriented, integrated, **current-valued, volatile, detailed** store for operational reporting and immediate lookups. *Not:* a data warehouse (which is historised and non-volatile) and *not:* a star schema (which is the analytical shape). Conflating ODS with star schema is a specific, common error this glossary exists to prevent.

**Physical model** — tables, types, indexes, partitions, constraints, on a named engine. *Not:* the truth about the domain; it is one realisation of the logical model.

**SCD (slowly changing dimension)** — the policy for what happens to history when a dimension attribute changes. Chosen **per attribute**: Type 0 never changes; Type 1 overwrites; Type 2 adds a new row with an effective interval; Type 3 keeps a previous-value column; Type 4/6 are hybrids. *Not:* a table-level setting.

**Snowflake** — a dimension normalised into its hierarchy. Kimball advises against it for analytical shape; this standard permits it **only when the domain model requires the hierarchy as its own entity** (identity, invariants, lifecycle). *Not:* "normalising because it feels tidier."

**Star schema** — one fact table surrounded by denormalised dimensions. *Not:* an analytics-only construct in this standard — we adopt the shape as the durable operational representation, as a recorded deviation from the canon.

**Surrogate key** — a meaningless, system-generated key identifying one *version* of a dimension row; the key facts join on. *Not:* the natural/business key, which identifies the *thing* across versions. Joining a fact to the natural key silently destroys point-in-time correctness.

**Temporal table (system-versioned)** — a SQL:2011 table whose prior row versions the database moves automatically into a paired history table. *Not:* the same as append-only facts: temporal tables give you two schemas and record *when*; append-only facts give you one schema and record *when, who, why, and from where*.

**Type-2 history rule** — the decision that a given attribute's change must not retroactively alter the meaning of past facts, and therefore produces a new dimension version rather than an overwrite. *Not:* an optimisation; it is a correctness rule, and getting it wrong rewrites history silently.

**Ubiquitous language** — the shared, context-scoped vocabulary used identically in conversation, specification, model, and code. *Not:* a naming convention; a naming convention describes *how* to write a name, the ubiquitous language decides *which* name is right.

**Value object** — a domain object defined wholly by its attributes, immutable, compared by value (money, a date range, a quantity with units). *Not:* a DTO, and *not:* an entity — it has no identity of its own.
