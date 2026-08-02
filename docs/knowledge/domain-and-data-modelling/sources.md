---
id: kb-ddm-sources
title: "Domain & Data Modelling — Sources"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "data-model-primacy"
tags: [sources, provenance]
links:
  - { to: kb-domain-and-data-modelling, rel: refines }
review-by: "2026-10-31"
summary: >-
  Full source list with access dates and the confidence each source carries, ordered by the
  source-of-truth hierarchy: primary works and standards, then vendor documentation, then
  practitioner synthesis, then in-repo evidence.
---

# Sources

All web sources accessed **2026-08-02**. Confidence follows the source-of-truth hierarchy (BoK §III.1): primary works and standards outrank vendor docs, which outrank practitioner synthesis.

## Tier 1 — primary works and standards

| Source | Used for | Confidence |
|---|---|---|
| Eric Evans, *Domain-Driven Design* (2003) | Bounded context, ubiquitous language, entity/value object/aggregate/repository | Verified (book, cited via secondary summaries — not re-read for this compilation) |
| Vaughn Vernon, *Effective Aggregate Design* (kalele.io) & *Implementing DDD* ch. 10 | The four aggregate rules | Verified |
| Ralph Kimball & Margy Ross, *The Data Warehouse Toolkit* / Kimball Group technique index | Four-step method, grain, fact/dimension design, SCD types, denormalised-dimension guidance | Verified |
| Bill Inmon — ODS and CIF definitions | ODS as subject-oriented, integrated, current-valued, volatile, detailed | Verified |
| **SQL:2011** period tables (system time / application time) | Temporal-table semantics and the paired-history-table requirement | Verified |

## Tier 2 — vendor / platform documentation

| Source | Used for | Confidence |
|---|---|---|
| Microsoft Learn — *Temporal Tables (SQL Server)* | Concrete temporal implementation, `AS OF`, history-table retention | Verified |
| Databricks — *What is the medallion lakehouse architecture?* | Bronze/silver/gold layer definitions and audiences | Verified |
| Microsoft Learn — *Implement medallion lakehouse architecture in Fabric* | The same layering in Fabric/OneLake | Verified |
| Kimball Group — *Dimensional Modeling Techniques* | The maintained canonical technique index | Verified |

## Tier 3 — practitioner synthesis (leads, verified against Tier 1)

| Source | Used for | Confidence |
|---|---|---|
| archi-lab.io — *Aggregate Design Rules according to Vaughn Vernon's Red Book* | Compact statement of the four rules | Verified (agrees with Tier 1) |
| Dimensional-modelling practitioner guides (2026) | Grain-declaration emphasis; per-attribute SCD choice; surrogate-key joins | Verified (agrees with Tier 1) |
| Temporal-table practitioner articles (2024–2026) | The trade-off list: storage/write overhead, manual pruning, no `who` without extension | Verified (agrees with Tier 1 + vendor docs) |
| Medallion-architecture guides (2025–2026) | Cross-vendor confirmation that dimensional models live in gold | Inferred (broad agreement, no single authority) |

## Tier 4 — in-repo evidence (strongest for *our* context, weakest for generality)

| Source | Used for | Confidence |
|---|---|---|
| Meridian `docs/adr/0022-append-only-facts-versioned-dimensions.md` | The durable-representation decision and its rationale; the "arrives through the audit door" framing | Verified (a real, committed decision record) |
| Meridian `.claude/knowledge/data-model-primacy.md` (DM1–DM7) | Grain/additivity/history discipline; the three-schema-levels rule | Verified |
| Meridian `docs/knowledge/data-modeling/index.md` | "Age is derived, never stored"; "backfill never guesses"; the aggregate-too-large self-correction | Verified |
| Meridian `.claude/knowledge/end-to-end-discipline.md` | Failure modes 1–3 (two homes; five surfaces not four; no compute reader) | Verified |
| TheTerrace `docs/knowledge/domain-and-data-modelling/` | The ODS-vs-star correction; the grain table; hub-and-satellite; the Type-1 open question | Verified |
| TheTerrace standing-method block + forensic-review backlog (FR-061, FR-088, FR-089, FR-102, FR-110) | Failure modes 2, 6, 9, 10 | Verified |

## What was *not* established

- No source recommends a star schema as the operational transactional store. Finding 6 of the index is therefore a **synthesis (Inferred)**, corroborated only by an in-repo ADR. It is labelled as such and its disconfirming case is written out in `open-questions.md`.
- Performance thresholds for "latest row per key" at scale (F1) were not found in any authority and must be measured per project.
- The Evans and Kimball books were used via their canonical technique summaries and secondary sources rather than re-read end-to-end for this compilation; the claims drawn from them are the widely-attested ones, but a reader needing an exact quotation should go to the book.
