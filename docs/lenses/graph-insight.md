---
id: lens-graph-insight
title: "Lens - graph insight (computed)"
type: doc
status: accepted
owner: "@maintainers"
tags: [lens, graph-analysis, computed]
links:
  - { to: lens-graph-structure, rel: relates-to }
review-by: ""
summary: >-
  Computed structural analysis of the knowledge graph - hubs, bridges,
  components, orphans and structural gaps. Regenerate with
  obsidian-setup.py --analyze --write. Derived, never authoritative.
---

# Graph insight - AI-Forward

*Computed from `docs/docs-index.js` (generated 2026-08-02T23:28:45Z) by `obsidian-setup.py --analyze`. Dependency-free: no Obsidian or plugin required.*

## Shape

- **38 artifacts**, **71 typed links**, density 0.0939
- **1 connected component(s)**; largest holds 38 artifact(s)

| type | n |
|---|---|
| knowledge | 14 |
| doc | 10 |
| design | 5 |
| decision-note | 2 |
| adr | 1 |
| architecture | 1 |
| design-language | 1 |
| glossary | 1 |
| privacy-review | 1 |
| proof-pack | 1 |
| threat-model | 1 |

| relation | n |
|---|---|
| `refines` | 19 |
| `relates-to` | 18 |
| `documents` | 18 |
| `implements` | 6 |
| `depends-on` | 6 |
| `supersedes` | 3 |
| `tested-by` | 1 |

## Hubs - the most connected artifacts

*A hub carries the most context. If one is wrong or stale, the error propagates widest.*

| artifact | degree |
|---|---|
| `architecture` | 16 |
| `kb-pack-evolution` | 12 |
| `kb-domain-and-data-modelling` | 10 |
| `design-docs-explorer-grounding-spatial-navigation` | 8 |
| `privacy-review` | 8 |
| `threat-model` | 7 |
| `docs-index` | 5 |
| `forensic-review` | 5 |

## Bridges - highest betweenness

*A bridge is the only path between regions. Losing it fragments the graph; these are the artifacts most worth keeping accurate.*

| artifact | betweenness |
|---|---|
| `architecture` | 370.51 |
| `kb-pack-evolution` | 248.27 |
| `kb-domain-and-data-modelling` | 235.45 |
| `docs-index` | 83.08 |
| `privacy-review` | 39.87 |
| `design-docs-explorer-grounding-spatial-navigation` | 37.92 |
| `lens-graph-health` | 36.0 |
| `threat-model` | 30.42 |

## Attention


**Orphans (no links either way)** - 0 *(an orphan is a finding, not a result (V10))*
- none

**Fragments (disconnected from the main graph)** - 0 *(reachable only in isolation)*
- none

**Leaves (single link)** - 14 *(weakly integrated - often correct, sometimes forgotten)*
- `kb-ddm-comparables`
- `kb-ddm-data`
- `kb-ddm-glossary`
- `kb-ddm-open-questions`
- `kb-ddm-references`
- `kb-ddm-sota`
- `kb-ddm-sources`
- `kb-pack-evolution-comparables`
- `kb-pack-evolution-glossary`
- `kb-pack-evolution-open-questions`
- `kb-pack-evolution-references`
- `kb-pack-evolution-sota`
- `kb-pack-evolution-sources`
- `lens-graph-structure`

**Unowned** - 0 *(V13 requires an accountable owner)*
- none

**Missing review-by** - 3 *(no freshness SLA)*
- `adr-0001-grounding-source-corpus-registry`
- `lens-graph-health`
- `lens-graph-structure`

**Flagged review-suggested** - 0 *(an upstream change wants a look)*
- none

## Structural gaps

*Expected relations that are absent. A prompt, not a failure - close the link or record why it does not apply.*

| artifact | type | gap |
|---|---|---|
| `design-aiforward-cli` | design | no proof-pack proves this design's claims |
| `design-pack-doctor` | design | no proof-pack proves this design's claims |
| `design-project-memory` | design | no proof-pack proves this design's claims |
| `design-rai-and-scrub` | design | no proof-pack proves this design's claims |

## Ownership

| owner | artifacts |
|---|---|
| @timianmalloo | 33 |
| @maintainers | 3 |
| @timianmalloo | 2 |
