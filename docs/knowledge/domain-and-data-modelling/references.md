---
id: kb-ddm-references
title: "Domain & Data Modelling — References"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [references, evans, vernon, kimball, inmon, sql2011]
links:
  - { to: kb-domain-and-data-modelling, rel: refines }
review-by: "2026-10-31"
summary: >-
  The seminal works, standards and vendor documentation this knowledge base rests on —
  Evans and Vernon for DDD, Kimball for dimensional modelling, Inmon for the ODS,
  SQL:2011 for temporal tables, and the current lakehouse layering documentation.
---

# References

## Seminal works

| Work | Author / year | What it is authoritative for |
|---|---|---|
| *Domain-Driven Design: Tackling Complexity in the Heart of Software* | Eric Evans, 2003 | Bounded context, ubiquitous language, entities/value objects/aggregates/repositories, context maps. The origin text. |
| *Implementing Domain-Driven Design* ("the Red Book") — esp. ch. 10 Aggregates | Vaughn Vernon, 2013 | The operative **aggregate design rules**; how DDD is actually applied. |
| *Effective Aggregate Design* (three-part series) | Vaughn Vernon | The four rules in their most-cited form: true invariants in a consistency boundary; small aggregates; reference by identity; eventual consistency across aggregates. |
| *The Data Warehouse Toolkit* (3rd ed.) | Ralph Kimball & Margy Ross | The dimensional canon: the four-step method, grain, fact/dimension tables, SCD types, conformed dimensions, the bus matrix. |
| *Building the Data Warehouse* | Bill Inmon | The ODS and the subject-oriented/integrated/time-variant/non-volatile warehouse definition; the layered (CIF) architecture. |
| *Patterns of Enterprise Application Architecture* | Martin Fowler, 2002 | Data-mapping patterns; the vocabulary (Repository, Unit of Work, Identity Map) that DDD persistence assumes. |
| *Refactoring Databases: Evolutionary Database Design* | Ambler & Sadalage | Safe schema evolution; the intellectual origin of expand-migrate-contract. |

## Standards & specifications

| Standard | Relevance |
|---|---|
| **SQL:2011** — application-time and system-time period tables | The standardised temporal-table mechanism: `PERIOD FOR SYSTEM_TIME`, `GENERATED ALWAYS AS ROW START/END`, `FOR SYSTEM_TIME AS OF`. Implemented (with variations) by SQL Server, DB2, MariaDB, Oracle, and Postgres via extension. |
| **ANSI/SPARC three-schema architecture** | The conceptual / logical (external) / physical (internal) separation this standard's model levels descend from. |
| **ISO/IEC 11179** — metadata registries | Where naming and definition discipline for data elements is formalised; useful when a glossary must be machine-readable. |

## Vendor / platform documentation (verify on use — these move)

| Source | Relevance |
|---|---|
| Kimball Group — *Dimensional Modeling Techniques* | The canonical technique list, maintained as the reference index for the method. |
| Microsoft Learn — *Temporal tables* (SQL Server) | The concrete SQL Server implementation: history table, `AS OF` queries, retention. |
| Databricks — *What is the medallion lakehouse architecture?* | Bronze/silver/gold definitions; where dimensional models sit (gold). |
| Microsoft Learn — *Implement medallion lakehouse architecture in Fabric* | The same layering in the Fabric/OneLake idiom. |

## In-pack authorities this composes with

| Doc | Relationship |
|---|---|
| `domain-and-data-modelling.md` (pack knowledge) | The **normative standard** this evidence base backs. |
| `layered-optimized-architecture.md` | Tier allocation and the AI-integrated patterns the data model serves; **P7 State Lives at the Edges** is the DDD/persistence-boundary rule in LOA terms. |
| `agent-body-of-knowledge.md` Part V.3 | Stateful changes: migrations forward- and backward-compatible; data correctness is part of "done"; reversible or with a tested recovery path. |
| `testing-strategy.md` D4/D6 | Real-infra integration and schema/golden-payload testing — how a data model's claims are proven. |
| `engineering-governance.md` §7 | Release, rollback and data migration as a governance lens. |
| Persona: **Data & Persistence Architect** | Holds the hard veto on an irreversible migration with no backward-compatible path and tested rollback. |

## In-repo precedents (project artifacts, not literature)

| Artifact | Why it is a reference |
|---|---|
| Meridian `docs/adr/0022-append-only-facts-versioned-dimensions.md` | The decision record for the durable representation this standard defaults to, including why it superseded temporal tables. |
| Meridian `docs/design/conceptual-model.md` | A worked conceptual model with owner decisions D1–D6 and a Mermaid ER diagram. |
| TheTerrace `docs/knowledge/domain-and-data-modelling/` | An independently-derived knowledge base reaching the same conclusions; the source of the ODS-vs-star correction. |
