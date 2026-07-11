---
id: adr-0001-grounding-source-corpus-registry
title: "ADR-0001: Use a versioned supplemental source-corpus registry"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [docs-explorer, grounding, source-corpus, knowledge-graph]
links:
  - { to: design-docs-explorer-grounding-spatial-navigation, rel: implements }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  Keeps frontmatter-bearing docs as the authoritative project graph while admitting
  canonical pack knowledge through a separate, versioned supplemental source-corpus
  registry. Generated Claude and Copilot wrappers remain projections, never parallel
  graph authorities.
---

# ADR-0001: Use a versioned supplemental source-corpus registry

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** @timianmalloo
- **Context spec/architecture:** `docs/design/docs-explorer-grounding-and-spatial-navigation.md`

## Context

The grounding packet needs exact, source-citable evidence from canonical
`pack/knowledge/*.md`, but those files intentionally lack the project-artifact
frontmatter used by `docs-graph.py`. Adding graph records to every canonical knowledge
file would also require reconciling generated Claude and Copilot wrappers and would risk
creating multiple apparent authorities for the same content.

## Decision

We will keep frontmatter-bearing project documents as the authoritative typed graph and
use a separate, versioned source-corpus registry for canonical pack knowledge. Registry
resources are supplemental evidence resources, not graph nodes; they cannot create graph
edges, satisfy artifact identity, or override graph metadata.

Grounding packet v1 remains valid when no registry is configured. Registry admission is
an additive follow-up under its own schema version and must preserve exact source hashes,
approved roots, and the packet byte budget.

## Alternatives considered

- **Make every `pack/knowledge/*.md` file a graph record:** rejected because the generated
  wrappers would look like parallel authorities and every vendored foundation refresh
  would require graph-frontmatter reconciliation.
- **Ground generated `.claude/` or `.github/instructions/` wrappers:** rejected because
  generated projections are not canonical sources and may contain tool-specific wrapping.
- **Exclude pack knowledge permanently:** rejected because it would leave the pack's
  methodology unavailable to deterministic repository grounding.

## Consequences

- **Positive:** graph identity stays unambiguous; pack knowledge can be added without
  changing generated wrappers; target repositories can opt into their own registries.
- **Negative / accepted trade-offs:** registry resources do not participate in graph
  traversal and need an explicit admission/ranking contract.
- **Follow-ups / new risks:** define `source-corpus/v1`, approved-root checks, and
  graph-to-resource applicability before enabling registry evidence in packets.

## Evidence

- **Verified:** `pack/knowledge/*.md` is canonical and generated into multiple tool-facing
  projections by `tools/sync-pack.ps1`.
- **Verified:** `docs-graph.py` currently scans only frontmatter-bearing Markdown under
  `docs/`, excluding generated pack documentation.
- **Inferred:** a registry is the smallest design that preserves one graph authority while
  allowing canonical non-graph evidence.
