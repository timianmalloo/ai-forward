---
id: design-docs-explorer-grounding-spatial-navigation
title: "Docs Explorer — Grounding and Spatial Navigation Design"
type: design
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [docs-explorer, knowledge-graph, grounding, project-memory, accessibility, 3d]
links:
  - { to: architecture, rel: refines }
  - { to: project-memory, rel: refines }
  - { to: docs-index, rel: documents }
  - { to: design-language-docs-explorer, rel: depends-on }
  - { to: proof-docs-explorer-redesign, rel: tested-by }
review-by: 2027-01-07
review-suggested: []
summary: >-
  Detailed design for making the repository knowledge graph a deterministic grounding
  interface for coding agents and a clearer human exploration surface. It separates
  selected-node neighborhood context from mind-map rooting, adds provenance-bounded context packets,
  adds a derived directory of standalone HTML knowledge surfaces, and makes deterministic
  Spatial 3D a first-class progressive projection over an accessible 2D baseline.
---

# Docs Explorer - Grounding and Spatial Navigation Design

## 1. Decision and scope

**Decision.** Keep each admitted artifact body plus its frontmatter as the canonical
knowledge source set, with frontmatter authoritative for graph metadata, and add two
bounded derived consumers:

1. a deterministic, stdlib-only grounding interface in `docs-graph.py`; and
2. an accessible browse-first knowledge portal whose graph, mind map, deterministic
   Spatial 3D projection, and standalone HTML knowledge surfaces share selection,
   neighborhood context, filters, and browser navigation history.

The design does **not** replace the current graph, introduce embeddings, or make 3D the
primary navigation model. Spatial 3D is a required progressive projection over the same
typed graph model; Browse remains the default and the relationship list remains the
accessible source of interaction parity.

**Core scenario.** A contributor or coding agent selects an artifact, understands its
authoritative upstream context, downstream proofs and impacts, recent decisions, and
exact source passages without losing orientation or receiving stale history as current
fact.

**Delivery phase.** This is a pack-evolution slice. The grounding CLI remains
independently deployable and testable. The human Explorer slice includes Browse, Graph,
Mind map, Spatial 3D, and a derived directory of HTML knowledge surfaces; all consume
the normalized index while grounding remains independent from visual presentation.

### Governing constraints

The design preserves these established contracts:

- `knowledge-visualization.md` V2: frontmatter is the record; indexes are derived.
- V4: hierarchy/browse is the default landing.
- V5-V6: graph and mind map are projections of the same typed graph.
- V12: projections disclose what they hide and do not invent structure.
- V15: grounding traverses typed edges 1-2 hops and cites the traversal path.
- V18: graph mechanics live in `docs-graph.py`, not prompt-time scripts.
- `project-memory-and-obsidian.md` M1/M5: memory is committed and tool-neutral;
  frontmatter and authoritative artifacts outrank narrative history.
- `docs/architecture.md`: `pack/` remains canonical for pack assets; generated surfaces
  remain derived.
- `ui-interaction-design.md` U16/U17: WCAG 2.2 AA and a named performance budget are
  floors, not enhancements.

## 2. Current-state review

Claims below are based on the current canonical files
`pack/templates/docs-explorer.template.html`, `pack/scripts/docs-graph.py`, and the
derived `docs/docs-index.js`.

| ID | Finding | Impact | Confidence |
|---|---|---|---|
| DX-01 | Mermaid extraction uses a greedy multiline expression, so a diagram title can absorb preceding document content. | Corrupts derived metadata and wastes LLM/browser context. | **Verified** |
| DX-02 | Graph initialization uses `Math.random()` and an O(n^2), 260-iteration force pass. | Layout changes between visits and weakens spatial memory; work grows poorly with graph size. | **Verified** |
| DX-03 | Selection updates details but does not center, fit, isolate, or expose relationship paths. | The selected node is informationally selected but not visually focused. | **Verified** |
| DX-04 | Mind-map construction converts typed directed edges to undirected adjacency before BFS. | Relation direction and meaning are lost in the primary tree. | **Verified** |
| DX-05 | Mind-map click both selects and re-roots. | Inspection and navigation are conflated; accidental clicks destroy orientation. | **Verified** |
| DX-06 | The initial view state is `hierarchy`, but no hierarchy stage exists; it falls through to the mind map. | The implementation contradicts V4's browse-default requirement. | **Verified** |
| DX-07 | Search filters mutate topology while typing and can hide the selected node. | Search behaves like destructive filtering rather than find-and-focus. | **Verified** |
| DX-08 | Core SVG groups and clickable containers lack complete keyboard and screen-reader semantics. | The interface does not meet the declared WCAG floor. | **Verified** |
| DX-09 | There is no typed traversal or context-packet command for agents. | V15 is a prose instruction rather than a deterministic machine contract. | **Verified** |
| DX-10 | Context lacks heading-bounded chunks, line ranges, hashes, query scoring, truncation state, and budget metadata. | Agents cannot prove exactly which source text grounded a conclusion. | **Verified** |
| DX-11 | Project-memory history is append-only but retrieval has no authority or correction policy. | Old narrative can outrank newer decisions when a model receives an unbounded history dump. | **Verified** |
| DX-12 | The graph currently scans project docs, while the canonical pack knowledge corpus lives under `pack/knowledge/`. | In this dogfood repo, some methodology source is outside graph traversal. | **Verified** |
| DX-13 | Mermaid and CDN failures can end in an error wall instead of the required local/offline degradation. | Local documentation becomes unavailable when enhancement dependencies fail. | **Verified** |

### Immediate defect boundary

`DX-01`, `DX-06`, and `DX-08` are correctness/accessibility defects in the existing
surface. The remaining findings are capability gaps or scaling risks. This design does
not silently fold the pack-source corpus (`DX-12`) into the docs graph: doing so changes
the pack's canonical artifact model and requires a separate architecture decision.

## 3. Solution-Selection Ladder and patterns

### Ladder result

1. The work must exist: V15 cannot be reliably followed by an agent without a
   machine-facing traversal contract.
2. Reuse the existing frontmatter parser, relation registry, scan, and derived index.
3. Use Python stdlib for traversal, lexical ranking, hashing, and JSON output.
4. Use native SVG and browser APIs for the canonical 2D interaction.
5. Add no dependency for grounding or 2D visualization.
6. Extract only the renderer-independent state/layout functions needed for tests.
7. Implement the minimum native 3D coordinate and perspective projection needed for
   orbit, zoom, and selected-node focus; add no visualization dependency.

### Named patterns

| Pattern | Use | Why it survives the Simplifier |
|---|---|---|
| **Materialized View** | Frontmatter graph metadata plus canonical body hashes -> browser index. | Preserves the canonical source set while making browser reads cheap. |
| **Master-Detail** | Browse tree and visualization beside a persistent detail panel. | Existing UI already uses it; it fits document discovery better than a canvas-first shell. |
| **Progressive Enhancement** | Browse/list first; Graph, Mind map, native Spatial 3D, and Mermaid build on that floor. | Keeps the core usable offline and on constrained hardware while making immersive exploration available. |
| **Graceful Degradation (LOA 6.5)** | Offline/CDN loss, spatial-budget failure, unsupported 3D transforms, and render failure retain Browse/list/source paths. | Every enhancement has a defined lower-cost usable floor. |
| **Derived Directory / Materialized View** | Safe `docs/**/*.html` discovery emits navigation-only surface metadata beside graph artifacts. | Makes the Explorer a one-stop knowledge portal without hand-maintained links or changing semantic graph hashes. |
| **Grounded Context Injector (LOA 4.1), deterministic evidence stage only** | Typed traversal, lexical retrieval, and exact source citations feed a downstream consumer; prompt injection and synthesis are explicitly deferred. | Reuses the established pattern vocabulary without claiming the model-facing stages that do not exist yet. |
| **Pipes and Filters** | Traversal -> chunking -> ranking -> one Grounding Evidence Document. | Makes each pure stage independently testable without adding a service, store, or integration bus. |

Rejected:

- **Embedding/vector retrieval now:** rejected until lexical retrieval fails a committed
  eval set. It adds model/dependency/cost and non-deterministic ranking.
- **Canvas/WebGL or third-party 3D renderer:** rejected at the current graph size because
  deterministic native geometry plus SVG/DOM projection is smaller, offline, testable,
  and preserves focusable node controls.
- **3D-first navigation:** rejected because it weakens scanability, keyboard access,
  text legibility, and offline resilience.
- **Narrative-history grounding in v1:** rejected because chronology is not authority.
  V1 includes only current artifacts, accepted ADRs, and active change entries that
  explicitly reference the selected artifacts.

## 4. Machine-grounding component

### Responsibility

Return a bounded, deterministic, source-citable evidence packet for one graph root and
an optional query. It never generates prose conclusions, injects a prompt, treats an
index summary as evidence, or claims to be a full LOA Grounded Context Injector.
Consumers must preserve chunk IDs, health issues, budget state, paths, and citations when making a
grounded claim. A future model consumer may compose this provider into LOA Archetype D,
but that separate consumer must define typed prompt injection, source-only
instructions, citation behavior, model budget, and evals.

### Exposed CLI contracts

```text
docs-graph.py context
  --id <artifact-id>
  [--query "<terms>"]
  --policy grounding|impact
  --hops 0..2
  --max-bytes <4096..1048576>                    # default 65536
  [--include-changes]
```

Output is JSON only. `--max-bytes` caps the complete UTF-8 serialization, not only
evidence text. Packet assembly serializes the mandatory envelope first, measures it,
then adds chunks only while the final serialization remains within the cap. A budget
outside 4,096..1,048,576 bytes returns `BUDGET_OUT_OF_RANGE`. If the mandatory
envelope itself exceeds 1 MiB, return `ENVELOPE_TOO_LARGE` before comparing it with the
requested cap. Otherwise, if the envelope cannot fit a valid requested cap, return
`BUDGET_TOO_SMALL`. No estimated or
exact model-token count is claimed without a tokenizer contract.

### Traversal policies

| Policy | Edge behavior | Primary use |
|---|---|---|
| `grounding` | Follow outgoing `implements`, `refines`, `depends-on`, `uses-term`; include outgoing `tested-by`/`documents` as evidence; preserve edge direction. | Load authoritative context for work. |
| `impact` | Follow inbound `implements`, `refines`, `depends-on`, `tested-by`, `uses-term`. | Determine what must be reviewed after a change. |

Stable ordering is: depth, policy relation priority, artifact ID, source line. Cycles are
recorded once and never recurse indefinitely.

The registry of policy -> relations -> direction -> priority is versioned once in
`docs-graph.py` and emitted into the browser index. It defines `grounding`, `impact`,
`proof` (outgoing `tested-by`), and `explore-neighborhood` (registered relations in
both directions with direction labels). The CLI exposes `grounding`/`impact`; the UI
uses all four. The index and each packet include `policyVersion`, `policySha256`, and
the graph snapshot hash. They do not maintain separate traversal semantics.

Canonical hash preimages use UTF-8, LF-normalized source text, JSON keys sorted
lexicographically, compact separators, and arrays in the stable order defined by this
design. `policySha256` covers the policy version and each policy's ordered
relation/direction/priority entries. `graphSha256` covers the index schema/project plus
artifacts ordered by ID with `id`, `path`, `title`, `type`, `status`, `owner`,
`reviewBy`, canonical `reviewSuggested`, sorted tags, sorted typed links, summary, and
canonical source-body SHA-256; it excludes generated timestamps and runtime diagnostics.
Python/JavaScript golden vectors use fixed UTF-8 preimage bytes and expected SHA-256
digests for CRLF normalization, non-ASCII text, key order, and array order. The committed
`canonical-hash-v1.json` fixture stores each exact primitive and complete policy/graph
preimage as base64 plus its literal 64-character digest; the expected values are
generated once with an independent platform hash tool, never by either runtime under
test. Complete vectors prove the specified field projection, including excluded
timestamps/diagnostics; add-one/remove-one field mutations must change or preserve the
digest exactly as the projection contract requires. An unsupported
version or policy/graph/source/chunk hash mismatch returns
`GRAPH_INVALID`; the browser disables path actions and falls back to Browse/list rather
than presenting provenance as valid.

### Grounding packet v1

```json
{
  "schemaVersion": "grounding-packet/v1",
  "policyVersion": "traversal-policy/v1",
  "policySha256": "<canonical-policy-hash>",
  "graphSha256": "<canonical-graph-and-admitted-source-metadata-hash>",
  "rootId": "design-example",
  "request": {
    "policy": "grounding",
    "hops": 2,
    "query": "retry contract",
    "maxBytes": 24000,
    "includeChanges": true
  },
  "healthIssues": [{
    "code": "STALE",
    "artifactId": "architecture"
  }],
  "coverage": {
    "roots": ["docs"],
    "artifactsScanned": 19,
    "relationshipsScanned": 42,
    "admittedSourceBytes": 98304
  },
  "paths": [{
    "from": "design-example",
    "to": "architecture",
    "rel": "refines",
    "direction": "outbound",
    "depth": 1
  }],
  "chunks": [{
    "artifactId": "architecture",
    "path": "docs/architecture.md",
    "heading": "## Composition contract",
    "lineStart": 101,
    "lineEnd": 132,
    "sourceSha256": "<canonical full-source hash>",
    "sourceByteStart": 6280,
    "sourceByteEnd": 8174,
    "sha256": "<content hash>",
    "reason": ["root-neighbor", "query-match"],
    "text": "<exact source text>"
  }],
  "changes": [{
    "id": "cl-0003",
    "datetime": "ISO-8601 UTC",
    "summary": "<decision summary>",
    "artifacts": ["docs/architecture.md"]
  }],
  "budget": {
    "bytesUsed": 19840,
    "chunksIncluded": 9,
    "truncated": true,
    "omittedChunkCount": 4
  }
}
```

`healthIssues` is the single graph-health authority. Stable issue codes are `STALE`,
`REVIEW_SUGGESTED`, and `MISSING_TARGET`; presentation copy is derived. Budget truncation
is represented only by `budget.truncated` and `omittedChunkCount`, never a second issue
field.

Consumers MUST reject unsupported schema/policy versions, verify the policy, graph,
source, and chunk hashes against the canonical rules above, and verify each chunk against
the cited source hash/range before claiming source-grounded status. A consumer without
source access may display the citation but must label it unverified. Preserve
`healthIssues`, budget metadata, and graph paths with every cited chunk. A packet is
evidence input, not a generated answer.

`sourceSha256` is intentionally repeated on each chunk so every bounded chunk remains a
self-contained citation record when streamed or copied independently. Hoisting it would
add a lookup table and coupling for negligible savings inside the 1 MiB packet ceiling.

Error output is also a versioned JSON contract:

```json
{
  "schemaVersion": "docs-graph-error/v1",
  "error": {
    "code": "ROOT_NOT_FOUND",
    "message": "Artifact 'missing-id' was not found.",
    "details": { "artifactId": "missing-id" }
  }
}
```

Stable codes are `ROOT_NOT_FOUND`, `POLICY_UNSUPPORTED`, `HOPS_OUT_OF_RANGE`,
`BUDGET_OUT_OF_RANGE`, `SCAN_LIMIT_EXCEEDED`, `SOURCE_FILE_TOO_LARGE`,
`GRAPH_INVALID`, `BUDGET_TOO_SMALL`, `ENVELOPE_TOO_LARGE`, and `INTERNAL_ERROR`.
Success and error schemas are golden contracts; stdout never mixes the two.
`SCAN_LIMIT_EXCEEDED` MUST include `details.limit` with one of
`artifacts|relationships|admittedSourceBytes|generatedChunks`; boundary tests assert
the discriminator, not only the shared code.
`INTERNAL_ERROR` exposes only the stable code, a generic message, and bounded scalar
diagnostics. It strips stack frames, source text, secrets, absolute paths, usernames,
and environment values before serialization.

After command-line parsing, multi-fault precedence is fixed: requested budget range,
policy, hops, graph validity, artifact limit, relationship limit, root existence,
per-file source size, admitted-source limit, mandatory-envelope size, envelope versus
requested budget, then generated-chunk limit. The first failing stage is the sole error;
later stages do not execute. Within mandatory-envelope sizing, `ENVELOPE_TOO_LARGE`
therefore wins over `BUDGET_TOO_SMALL` and any later chunk outcome.

### Chunking and ranking

- Parse Markdown by ATX headings; a chunk is one heading-bounded section.
- Preserve the heading line and exact line range.
- Hash the exact UTF-8 chunk text with SHA-256.
- Root, health-issue, coverage, budget, and graph-path metadata are mandatory envelope
  fields.
- Lexical score uses deterministic normalized terms, title/heading boosts, body term
  frequency, and graph-depth penalty. Stable artifact/line ordering breaks ties.
- Summaries, tags, and titles may influence navigation score but MUST NOT be emitted as
  evidence unless their source frontmatter is cited as frontmatter.
- Oversized sections split on paragraphs while preserving parent heading and ranges.
- Missing targets, stale nodes, and review flags become structured `healthIssues`; invalid
  frontmatter makes the graph invalid rather than producing partial evidence.

### Project-memory boundary

V1 grounds only:

1. current artifact body/frontmatter;
2. accepted ADRs reached by graph links; and
3. active, non-superseded change-log entries whose `artifacts` explicitly include a
   selected/traversed path, when `--include-changes` is set.

The narrative project-memory ledger and audit prompts are excluded from V1 evidence.
They remain human-readable history, not machine authority. A later memory design may
add correction/conflict reporting, but it is not required to make typed grounding
correct.

### Supported load and resource bounds

| Input | Limit | Failure |
|---|---|---|
| Root | exactly 1 | argument validation / `ROOT_NOT_FOUND` |
| Hops | 0..2 | `HOPS_OUT_OF_RANGE` |
| Scanned artifacts | 2,000 | `SCAN_LIMIT_EXCEEDED` |
| Admitted source bytes | 64 MiB total, checked from file metadata before body reads; verified regular files only, symlinks/reparse points not followed, file identity pinned across each open | `SCAN_LIMIT_EXCEEDED` |
| File size | 1 MiB per Markdown file | `SOURCE_FILE_TOO_LARGE` |
| Relationships | 20,000 total | `SCAN_LIMIT_EXCEEDED` |
| Generated chunks | 1,024 | `SCAN_LIMIT_EXCEEDED` |
| Chunk text | 64 KiB before paragraph split | split deterministically |
| Packet | inclusive 4 KiB..1 MiB | outside range -> `BUDGET_OUT_OF_RANGE`; valid but below envelope -> `BUDGET_TOO_SMALL` |

The CLI is single-process and read-only. It admits source files in deterministic path
order using metadata-only size checks, then reads and hashes the admitted regular-file
snapshots through a bounded worker pool while collecting results in the original order.
Each open revalidates file type and identity before trusting bytes, then rechecks identity,
size, and timestamps after the read so path swaps and parallel mutation fail closed. Source
files are chunked incrementally; the
CLI never retains the full admitted corpus and retains chunk text only for the bounded
mandatory set plus the current top-ranked packet candidates. It must remain below 256
MiB peak RSS and
finish a two-hop traversal of the maximum legal corpus within 2 seconds on the
benchmark environment in section 8.
Callers set a 10-second subprocess timeout to bound slow or stalled filesystem reads;
the process emits no success-shaped fallback after caller cancellation. This timeout is
the supported process-boundary liveness control because Python cannot safely preempt a
blocked synchronous filesystem call in-process; CLI help and every shipped caller state
this requirement.

Pack-owned callers MUST use one stdlib invocation helper rather than raw subprocess
calls. The helper drains stdout/stderr concurrently, enforces the 10-second timeout,
terminates the exact process tree, and discards stdout on timeout or nonzero exit. It
also kills the process if drained stdout exceeds the 1 MiB packet ceiling or stderr
exceeds 64 KiB, so a defective child cannot grow caller memory until timeout. A contract
test enumerates pack-owned invocation sites and rejects bypasses of the helper.
On Windows, a Job Object applies aggregate process-count and memory ceilings before the
requested command starts. On POSIX, stdlib-only containment is intentionally weaker:
the helper uses a new process group for tree termination and `RLIMIT_AS` for the launched
process, but does not claim a tree-wide memory or process-count ceiling. `RLIMIT_NPROC`
is not used because it is enforced per real user ID and can starve unrelated processes.
Every result exposes the containment mode and whether aggregate process and memory limits
were enforced, so POSIX callers do not silently mistake per-process containment for the
stronger Windows contract.

Success serializes the complete packet in memory, writes it to stdout in one operation,
and exits `0`; callers discard any stdout if the process exits nonzero or is killed.
Every failure leaves stdout
empty and writes exactly one error object to stderr. `ROOT_NOT_FOUND`,
`POLICY_UNSUPPORTED`, `HOPS_OUT_OF_RANGE`, and `BUDGET_OUT_OF_RANGE` exit `2`;
`GRAPH_INVALID` and `SOURCE_FILE_TOO_LARGE` exit `3`; `SCAN_LIMIT_EXCEEDED`,
`BUDGET_TOO_SMALL`, and `ENVELOPE_TOO_LARGE` exit `4`; `INTERNAL_ERROR` exits `1`.
The compact classes are intentional for shell/CI callers: `2` means correct the request,
`3` means repair graph/source input, `4` means reduce load or raise a valid packet cap,
and `1` means an unexpected internal failure.
Partial success is represented only by `healthIssues` and budget truncation metadata,
never a success-shaped fallback.

### Pack-source corpus prerequisite

Before the grounding packet schema is frozen or implemented, an ADR MUST choose one of:

1. make canonical `pack/knowledge/*.md` files graph records and update all wrappers; or
2. add an explicit, versioned source-corpus registry whose entries are derived evidence
   resources but not graph nodes.

Option 2 is the design recommendation because canonical pack knowledge currently lacks
artifact frontmatter and the generated tool wrappers should not become a parallel source
of truth. The ADR gates only the grounding slice; independent Browse/accessibility and
2D-layout defect work may proceed.

## 5. Human Explorer component

### UI Archetype Signature

```text
DocsKnowledgeExplorer {
  Type:Portal; Arch:HubAndSpoke; Layout:MasterDetail; Density:Comfortable;
  Nav:TopBar+Sidebar+Breadcrumb; Viewport:FluidResponsive;
  Input:KeyboardFirst+PrecisionPointer+TouchPrimary; Color:DarkAdaptive;
  x-TypeStyle:Utilitarian; Depth:SoftShadow; Sync:Stateless; Persistence:Session;
  Feedback:Instant; Motion:Micro+Fluid; Pacing:Freeform; Transition:Morph;
  A11y:WCAG_2.2_AA+ReducedMotion+HighLegibility+ScreenReaderFirst;
  x-ProjectionSet:"BrowseGraphMindMapSpatial3D";
  x-KnowledgeSurfaces:"DerivedHtmlDirectory";
}
```

The surface uses `docs/DESIGN.md` (`design-language-docs-explorer`) as its token
contract.

### Information architecture

The canonical application has four projections and one derived destination directory:

1. **Browse** (default): type/phase hierarchy and search results.
2. **Graph**: full typed network with semantic zoom.
3. **Mind map**: a context-rooted spanning tree with cross-links retained as ghost edges.
4. **Spatial 3D**: deterministic perspective projection with orbit, zoom, reset, and
   selected-node camera targeting.

A searchable **Knowledge surfaces** directory links to safely discovered standalone HTML
knowledge tools such as the audit timeline, design previews, and generated documentation
sites. The portal does not duplicate those tools' behavior.

The right detail panel remains stable across projections and contains:

- summary and health;
- outgoing relations and backlinks grouped by relation/direction;
- `Explore neighborhood`;
- `Show grounding path`, `Show impact path`, `Show proofs`;
- open-source-file action;
- non-spatial neighborhood list equivalent to the visual view.

### State model

```text
projection: browse | graph | mindmap | spatial3d
route: browse | visualization | details
selectedNodeId: string | null
contextNodeId: string | null
filters: { types, statuses, health, relations }
search: { query, activeMatchId }
pathMode: none | grounding | impact | proof
```

Rules:

- Single click/Enter selects; it does not re-root.
- `Explore neighborhood` sets `contextNodeId`, centers/fits the two-hop neighborhood,
  and deterministically derives the mind-map root from that context.
- Selection persists across projections even when temporarily outside a filter.
- Applying a filter that excludes `contextNodeId` deterministically clears context,
  announces the change, and preserves selection in Details with an "outside filters"
  notice. Browser Back restores the previous filter/context URL.
- Search locates and highlights. Topology changes only after an explicit filter action.
- Context is encoded in the URL fragment and browser History API; browser Back/Forward
  restores the prior projection, selection, and context.
- Projection-local viewport and Spatial 3D camera state are renderer details, not shared
  application state or graph semantics.
- On narrow screens, `route=visualization` requires
  `projection=graph|mindmap|spatial3d`;
  `projection=browse` requires `route=browse`; `route=details` may retain the prior
  projection for Back restoration. Desktop ignores route for layout and normalizes it
  from the visible shell.

Reducer events are explicit: `SELECT_NODE`, `EXPLORE_CONTEXT`, `SET_PROJECTION`,
`SET_ROUTE`, `LEAVE_CONTEXT`, `SET_SEARCH`, `APPLY_FILTERS`, `SET_PATH_MODE`, and
`RESTORE_STATE`. Search matches are derived from graph/filter/query input and never stored
as a second result authority. Invariants:
selection never implies context; context always names a visible graph artifact; when
context exists, the mind-map root equals `contextNodeId`; when context is absent, Mind
map uses the stable project-root artifact from index metadata and never derives its root
from selection.

| Event | Route | Selection | Context | Path | Normalization |
|---|---|---|---|---|---|
| `SELECT_NODE(id)` | unchanged | set `id` | unchanged | unchanged | invalid ID -> notice, no state change |
| `EXPLORE_CONTEXT(id)` | visualization | unchanged | set `id` | unchanged | `id` must be visible and valid |
| `SET_PROJECTION(value)` | narrow: Browse for `browse`, Visualization for `graph|mindmap|spatial3d`; desktop: implied | unchanged | unchanged | unchanged | unsupported value -> Browse; route/projection pair normalized |
| `SET_ROUTE(value)` | set | unchanged | unchanged | unchanged | narrow Visualization + Browse projection -> Graph; narrow Browse -> Browse projection; Details retains prior projection; desktop route is implied |
| `LEAVE_CONTEXT` | unchanged | unchanged | clear | clear if neighborhood-relative | restore default Mind-map root |
| `SET_SEARCH(query)` | unchanged | unchanged | unchanged | unchanged | highlights/result cursor only; topology unchanged |
| `APPLY_FILTERS(filters)` | unchanged | retain | clear if excluded | clear if invalid | announce clear; Back can restore prior URL |
| `SET_PATH_MODE(mode)` | unchanged | unchanged | unchanged | set | reject unsupported mode |
| `RESTORE_STATE(decodedState)` | coherent valid route | valid selected or null | valid visible context or null | valid mode or none | invalid values already removed; route/projection pair normalized; one local notice |

URL state uses the fragment so it works over `file://`:

```text
#route=browse|visualization|details
&view=browse|graph|mindmap|spatial3d
&selected=<encoded-artifact-id>
&context=<encoded-artifact-id>
&path=none|grounding|impact|proof
```

Pure `decodeUrlState(URLSearchParams)` and `encodeUrlState(state)` helpers sit outside the
reducer; browser history effects sit outside both. They use native `URLSearchParams` and
`sort()`. Omitted/default values are removed. Filters use sorted repeated `type`,
`status`, `health`, and `relation` keys. Search text is not persisted by default. Unknown
keys are ignored; invalid enum values are removed with a local notice; missing artifact
IDs recover to Browse as defined in the failure table. Only explicit user actions call
`history.pushState`; the entry MAY carry a bounded `focusReturnId` browser-effect hint
for Back focus restoration, but that hint is not application or URL state. Transient
search and camera moves never create history entries.

Spatial camera state (`yaw`, `pitch`, `zoom`, and `target`) is renderer-local. It is
initialized from deterministic layout plus current selection/context and is never
serialized into URL state, graph hashes, or grounding packets.

### Selected-node context behavior

On **Explore neighborhood**:

1. center the node instantly in Graph/Mind map; in Spatial 3D retarget the camera with
   `{motion.context}` unless reduced motion is requested;
2. fit its 1-hop neighborhood with padding;
3. keep 2-hop nodes visible with the audited reduced-emphasis text/graphical tokens;
4. retain unrelated node shapes and edges with audited dim/ghost graphical tokens,
   hide their labels at Neighborhood zoom, and never use opacity compositing to create
   a contrast-bearing state;
5. show directed upstream/downstream lanes and arrowheads;
6. reveal full selected-node title regardless of zoom;
7. announce the explored artifact and neighbor counts to assistive technology;
8. expose an equivalent ordered relationship list in the details panel.

`Escape` leaves neighborhood context without clearing selection. Browser Back returns
to prior context. No global single-character shortcut is registered. Within a focused
graph widget, Arrow keys move between node controls, Enter selects, and Escape returns
to the projection toolbar. Editable controls suppress graph navigation keys.

In Spatial 3D, node selection becomes the camera target without changing
`contextNodeId`. **Focus selected** is an explicit toolbar action. Reduced-motion mode
snaps to the target; otherwise the one restrained camera transition is interruptible by
manual orbit/zoom.

### Semantic zoom

| Scale | Visible information |
|---|---|
| Overview | Type/phase lane labels, health counts, selected node, no edge labels. |
| Neighborhood | Node titles, selected path, directional arrows, limited labels. |
| Detail | Relation labels, health markers, backlinks, full selected/context title. |

Labels are prioritized by selected path, context neighborhood, health problems, then
screen-space availability. A hard visible-label ceiling avoids the current all-labels
collision.

### Deterministic 2D layout

- Place type or phase lanes deterministically; order artifacts by stable ID inside each
  lane. Lane display rank comes from the one canonical artifact-type registry emitted by
  `docs-graph.py`; phase values sort numeric, then lexical, then unassigned.
- Route typed edges between lanes with arrowheads and bounded label placement.
- Do not run a force simulation in the first slice.
- For roughly <=500 visible nodes and <=1,000 edges, retain SVG.
- Above the visualization ceiling, do not render the spatial projection. Keep Browse
  and the complete relationship list available and explain the supported limit.
- Add clustering, virtualization, force refinement, a Web Worker, Canvas, or WebGL only
  after measured corpus growth and task evidence prove the bounded SVG insufficient.

The 2D SVG and relationship list consume one normalized internal projection model.
Canonical node arrays contain artifact fields plus lane/depth. Canonical edge arrays
contain `source`, `rel`, `target`, direction, and path/ghost flags. Exact duplicate typed
links are invalid graph input because they carry no additional semantics; failing loudly
preserves frontmatter as the authoritative record instead of silently repairing an
authoring defect in a derived view.
Selected/context flags and visible counts are derived from the stored IDs and array
lengths. Nodes sort by lane rank then artifact ID. Edges sort by source, relation, then
target; stable edge IDs use `<source>|<rel>|<target>`.

### Deterministic Spatial 3D layout

- Input is the same normalized artifacts and relationships consumed by Graph.
- Place type lanes on stable X coordinates and nodes inside each lane by artifact-ID
  order on Y.
- Derive Z from a stable depth band plus a bounded deterministic artifact-ID hash jitter;
  shuffled input arrays produce identical world coordinates.
- Return world coordinates from one pure function and apply perspective/camera transforms
  in a separate pure function.
- The canonical camera target is the selected node when present, otherwise the context
  node, otherwise the graph centroid.
- Orbit changes yaw/pitch, zoom changes camera distance, reset restores the canonical
  camera, and Focus selected retargets the selected node. Pointer orbit starts only on
  blank canvas; equivalent labelled keyboard controls adjust yaw and pitch.
- Depth-sort nodes and edges only for presentation. Camera angle, visual distance, Z
  depth, and occlusion never influence typed traversal, paths, graph hashes, context
  packets, or packet ordering.
- If node/edge limits are exceeded or 3D transforms are unavailable, route to Graph while
  preserving selection, context, filters, and path state.

### Native Spatial 3D projection

Spatial 3D is a bounded progressive projection, not a plugin contract. It receives a
read-only snapshot from the normalized graph model and may request only host-owned
selection, explore, path, and projection actions. Renderer-local code owns camera state,
pointer capture, animation frames, and listeners.

The selected node becomes the camera target; its neighborhood brightens and unrelated
nodes retain accessible but reduced emphasis. Unsupported transforms, limit rejection,
initialization failure, or render failure route to Graph with core state unchanged. No
fact, relation, or action exists only in 3D. Reduced-motion users receive the full 3D
projection with instant camera placement rather than being excluded from the mode.

The implementation uses native JavaScript math and SVG/DOM. No 3D dependency is approved
or required. Pointer and wheel input update camera state immediately but coalesce
projection writes through one `requestAnimationFrame`; cached node/edge references avoid
re-querying the DOM on each event. Rerender or lost pointer capture clears drag state.

### Offline asset contract

Core Browse, Graph, Mind map, Spatial 3D, details, and relationship-list assets MUST be pinned and
served from relative repository paths copied from canonical `pack/` sources by
`sync-pack.ps1`. React/htm may remain only if their pinned local copies and licenses are
recorded; replacing them with native DOM is preferred if implementation evidence shows
it is smaller. Network access is optional enhancement only. Mermaid lazy-loads and fails
to source text; Spatial 3D has no external asset. No core task depends on a CDN or service
worker cache.

### Derived knowledge-surface directory

`docs-graph.py derive` safely scans regular files matching `docs/**/*.html` and emits a
deterministically ordered `surfaces` collection beside `artifacts`.

Each surface contains stable `id`, repo-relative `path`, extracted or fallback `title`,
`kind`, concise `description`, and optional linked `artifactId`. The derivation:

- excludes `docs/index.html`, `docs/ai-forward-pack/templates/**`, symlinks/reparse
  points, and paths outside `docs/`;
- extracts the first non-empty `<title>` with a stable path-derived fallback;
- derives known destinations such as `docs/audit/index.html` without hardcoding a portal
  menu;
- sorts by `(kind, title, path)`;
- admits at most 100 surfaces and fails derivation with `SURFACE_LIMIT_EXCEEDED`; the
  browser independently enforces the same ceiling;
- keeps `surfaces` outside the canonical graph hash and grounding packet so navigation
  metadata cannot alter semantic provenance.

## 6. Complete UI states and copy

| Surface | Loading | Empty | Error | Success/ready | Disabled / recovery / overflow |
|---|---|---|---|---|---|
| App shell | Static navigation immediately; "Loading project map..." | "No indexed artifacts yet. Run docs-graph.py derive." | "The project map could not be loaded. Review the error code below." | Browse view with graph-health summary | Navigation remains reachable; secondary metadata collapses first. |
| Browse tree | Skeleton rows with stable headings | "No artifacts in this group." | "This group could not be read. Show all artifacts." | `tree`/`treeitem` hierarchy with selected state | Empty groups disabled; long labels wrap; index over-limit state blocks load. |
| Breadcrumb/context trail | Keep prior valid trail while restoring URL | Project root only | "This context is unavailable. Return to Browse." | Links reflect browser history state | Current item is not a link; overflow collapses to an accessible menu. |
| Filters | Current results remain visible while applying | "No filters are available." | Invalid stored filter is cleared with notice | Explicit Apply/Clear and active-filter count | Unavailable values disabled; filtered selection remains in details with notice. |
| Projection tabs | Current projection remains visible | Browse remains available | Unavailable projection explains why | Selected tab exposes `aria-selected` | Spatial 3D is a core progressive tab; tab list scrolls at narrow width. |
| Search | No blocking state; local incremental match | `No search results for "<query>". The graph remains unchanged.` | Invalid query never crashes; clear action | Match count and next/previous controls | No suggestion list; full results remain in Browse. |
| Graph | Stable lane skeleton | "No nodes satisfy these filters." | "Graph layout failed. Showing the relationship list instead." | Focusable SVG plus equivalent list | Above 500 visible nodes/1,000 edges, use Browse/list instead. |
| Mind map | Keep current root while recomputing | "This artifact has no visible relationships." | "Mind map could not be built. Showing direct relationships." | Root, spanning tree, and ghost cross-links | Bounded complete tree; no hidden expansion state. |
| Spatial 3D | Keep the last valid frame while retargeting | "No nodes satisfy these filters." | "3D is unavailable. Your selection and context were preserved in Graph." | Perspective node field, orbit/zoom/reset/focus controls, equivalent list | Above 500 nodes/1,000 edges or unsupported transforms, route to Graph. |
| Knowledge surfaces | Stable cards render with shell | "No standalone knowledge surfaces were discovered." | Invalid/unsafe entries are omitted; graph navigation remains available | Searchable cards link directly to audit, previews, and generated sites | Long paths wrap; no template-only files. |
| Details | Selected shell with metadata placeholders | "Select an artifact to inspect its context." | "The source body is unavailable; metadata and links remain usable." | Summary, health, links, paths, actions | Scroll regions with headings; no horizontal clipping. |
| Relationship list | Stable group headings | "No visible relationships." | "Relationships are incomplete. Review graph health." | Every visible edge is represented in DOM with the same stable edge ID; node controls retain artifact IDs | Browser index caps guarantee the complete list remains bounded; never silently omit visible edges. |
| Explore action | N/A — context reduction and deterministic layout are synchronous in the same frame; adding a visual-only loading flash would create churn without observable work | No selection: disabled with explanation | "Could not explore this neighborhood. Return to Browse." | URL/context updated and one completion announcement sent | Leave-neighborhood action restores prior URL state. |
| Narrow-screen visualization route | Preserve selected title during route load | Same empty state as projection | Return to Browse with message | Full-screen projection with explicit Back link | At 320px/400% zoom all controls reflow in document order. |
| Offline/CDN loss | Local shell and index remain active | Same as local data | "Enhanced diagrams are offline; source text is still available." | Browse/graph/mind map work without CDN | Mermaid source is shown as text. |

Load-bearing copy:

- Primary context action: **Explore neighborhood**
- Exit action: **Leave neighborhood**
- Path actions: **Trace grounding**, **Trace impact**, **Show proofs**
- Empty graph: **No artifacts match these filters. Clear filters**
- Graph-health notice: **Some context is stale or incomplete. Review graph health before using it**
- 3D fallback: **3D is unavailable. Your selection and context were preserved in Graph**
- Knowledge surfaces empty: **No standalone knowledge surfaces were discovered**

## 7. Accessibility and responsive behavior

- Focus order on desktop is: skip link -> project header -> search -> projection tabs ->
  Browse tree -> projection toolbar -> spatial nodes -> details panel. The details
  panel's internal order is heading/actions -> relationship-list subsection ->
  source/body controls.
  Narrow routes begin with Back -> route heading -> route controls -> content.
- Browse is a `tree` with `treeitem` children. Up/Down move items, Right expands or
  enters a group, Left collapses or returns to the parent, Enter selects.
- Graph, Mind map, and Spatial 3D are named `region` elements. Each SVG node contains a focusable
  HTML `button` through `foreignObject`, with a text equivalent in the relationship
  list. Roving tabindex exposes one node at a time; Arrow keys move to the nearest
  visible node in that direction: filter to the directional half-plane, then minimize
  angular deviation, squared distance, and artifact ID in that order. Enter or Space
  selects; Escape returns to the projection toolbar. The canonical relationship list
  follows the visualization and uses the same canonical node/edge ordering in DOM.
- The Spatial 3D viewport is focusable and describes its pointer, wheel, and keyboard
  controls. Six labelled orbit buttons provide yaw/pitch equivalents; zoom, reset, and
  focus-selected remain native buttons.
- Reduced-emphasis nodes remain focusable where present. Their focus indicator always
  renders with the full mode-specific focus-ring token, width, and offset; node
  de-emphasis never composites or reduces the focus indicator.
- Every visible graph edge has the same stable edge ID in the spatial view and
  relationship list. Node controls retain their artifact IDs in both projections,
  while actions use semantic focus keys. Tests compare the ordered edge IDs; richer
  node/action mirroring is deferred unless user research shows it improves task completion.
- Accessible node names contain title, type, status, and relationship count. Selection
  uses `aria-pressed`; neighborhood context is announced separately and never described
  as keyboard focus.
- No global character-key shortcut is registered. Graph keys work only while the graph
  widget has focus and are suppressed in editable controls.
- Search is a native `<input type="search">` with result count plus explicit
  Previous/Next result buttons. It introduces no suggestion/listbox state.
- Recoverable status changes use a polite `role=status`; failures that block the current
  task use `role=alert`. Repeated layout ticks and result-count changes are not announced.
- Mode-specific focus tokens meet >=3:1 against every adjacent surface. Meaning never
  relies on color alone.
- Edge direction is conveyed by arrows and relation text; health uses icon/text plus
  color.
- Screen-reader announcements are limited to deliberate selection/context changes, not
  layout/render updates: one polite announcement per completed selection/context action,
  and zero for intermediate ticks, derived search counts, or viewport moves.
- Reduced motion uses instant placement or a short opacity change; Spatial 3D camera
  retargeting snaps with no camera flight.
- Operable HTML node controls, toolbar controls, and relationship-list rows are at least
  `{targets.minimum}` square. Non-interactive overview glyphs may be smaller but never
  become the only operable representation.
- Sticky header controls use focus scroll compensation so focus scrolling cannot leave
  the active control hidden beneath the header.
- Knowledge-surface links expose unique accessible names (`Open <title>`); unsafe
  entries are omitted rather than rendered as ambiguous repeated links.
- At `{breakpoints.narrow}` and below, and at 320 CSS pixels/400% zoom, the shell becomes URL-addressable
  Browse -> Visualization -> Details routes. Browser Back returns to the prior route
  and keyboard focus returns to the initiating control. There is no modal bottom sheet
  or fixed three-column squeeze.
- Forward route navigation places focus on the route heading (`tabindex=-1`) after the
  title and selected artifact are updated; Back restores the exact initiating control.

The keyboard contracts follow the WAI-ARIA Authoring Practices Tree View and Tabs
patterns. The no-global-character rule implements WCAG 2.1.4; focus indicators meet
WCAG 2.4.11/2.4.13 geometry and contrast requirements.

## 8. Performance budget

| Measure | Budget |
|---|---|
| Usable 2D shell | <=2.0s p75, cold cache, pinned Chromium, 4x CPU slowdown, `Standard_D4s_v5` reference VM. |
| Selection/search feedback | <=100ms. |
| Initial 2D layout | <=500ms at 500 nodes/1,000 edges on the reference machine. |
| Initial Spatial 3D projection | <=500ms at 500 nodes/1,000 edges on the reference machine. |
| Navigation frame rate | 60fps target; no 1-second window below 30fps. |
| Visible labels | <=150, prioritized by semantic zoom. |
| CLI context | <=2s wall time and <=256 MiB peak RSS at 2,000 artifacts/20,000 edges/64 MiB admitted source. |
| Core offline | Fresh-cache task completion over `file://` and localhost with network blocked. |
| Mermaid | Lazy-load only when a document with diagrams is opened; failure shows source. |
| Spatial 3D | No added runtime dependency; 500-node/1,000-edge ceiling; five-run p75 and active-orbit frame floor reported. |
| Knowledge surfaces | <=100 safe regular HTML destinations; derivation and browser preflight both fail closed. |

Browser thresholds use five cold and five warm runs; report p50/p75/max. Interaction
latency uses Event Timing where available or `performance.measure`. Frame rate samples
the full pan/context transition, not an idle canvas.

Browser preflight rejects a `docs-index.js` payload over 5 MiB, more than 1,000
artifacts, more than 5,000 typed edges, or more than 100 HTML surfaces before layout.
Spatial projections additionally
stop at 500 visible nodes/1,000 visible edges and route to Browse plus the full
relationship list. A source body over 1 MiB is not rendered; a Mermaid block over 64 KiB,
more than 500 lines, or a document with more than 20 diagrams is shown as escaped source
without invoking Mermaid. Index script loading, source fetches, and Mermaid asset loading
have separate 5-second deadlines. Synchronous Mermaid rendering is bounded only by
preflight complexity caps and the pinned performance corpus; the design does not claim a
timer can preempt third-party code while it holds the main thread.
The deterministic layout is synchronous and count-bounded by the 500-node/1,000-edge
spatial preflight. It either commits a complete projection or routes to the existing
Browse/relationship-list recovery shell if layout preparation throws. A timer is not
claimed to preempt synchronous layout work; the 500ms target is proved only by the
reference browser benchmark.

One host-owned `runWithDeadline(operation, milliseconds, scheduler)` seam owns
asynchronous deadlines. `operation` receives an `AbortSignal`, stages output without
mutating visible state, and exposes an idempotent disposer. The host commits only after
the operation settles before the monotonic deadline; settlement at or after the exact
deadline is a timeout. Timeout aborts first, disposes once, and ignores/disposes any late
resolve or reject. The scheduler defaults to native monotonic timers and is injected with
a fake scheduler in tests. Synchronous parsing/render preparation is protected by the byte/line/count limits
above; a timer is not claimed to preempt synchronous code.

Deadline bindings are a closed contract for implemented asynchronous work: index script
load `5,000ms` and source fetch `5,000ms`. The fake/native scheduler suite proves the
shared deadline semantics; source-fetch browser tests prove its bound constant. Mermaid
asset loading is outside the stable P1 surface because deep body rendering is deferred.

The CLI benchmark uses seed `20260710`, CPython 3.11.9 on Windows Server 2022 x64,
and an Azure `Standard_D4s_v5` VM (4 vCPU, 16 GiB; exact CPU model/clock recorded in
the result), with a generated 2,000-node/20,000-edge corpus and 64 MiB of admitted
Markdown distributed across
empty, small, maximum-sized, cyclic, dangling-link, and Unicode fixtures. It runs ten
warm-cache iterations. A committed PowerShell harness owns the 10-second watchdog,
measures wall time with `System.Diagnostics.Stopwatch`, samples
`System.Diagnostics.Process.PeakWorkingSet64`, and terminates the exact process tree on
timeout. It emits p50/p75/max wall time plus maximum per-run peak working set, packet
bytes, visited nodes/edges, and chunk counts. Passing requires p75 wall <=2 seconds and
every run's peak working set <=256 MiB; watchdog tests require empty stdout and no
surviving child process. Results without the committed command, fixture, and pinned
environment do not satisfy the budget.

The PowerShell harness accepts an injected watchdog duration for its own tests. A
committed fixture process writes nothing, spawns one child, and blocks on an unsignaled
wait handle (no sleep); a short test watchdog must terminate the exact tree, leave stdout
empty, and report timeout. Production benchmark runs pin the watchdog to 10 seconds.

The P2 release benchmark uses the same `Standard_D4s_v5` VM and pinned Windows Server 2022
CI image, the committed Playwright/browser revision from the lockfile, Chromium's exact
build number, headless mode, SwiftShader software rendering, declared launch flags,
disabled extensions/background throttling, a fresh browser context per cold run, a
1366x768 viewport at DPR 1, and CDP 4x CPU throttling. It uses seed `20260710`, the
committed 500-node/1,000-edge fixture SHA-256, and both cold-cache and warm-cache runs.
The committed browser benchmark emits `docs-explorer-browser-benchmark/v1` JSON with
OS image, headless/GPU mode, launch flags, CPU rate, cache mode, environment,
fixture/hash, five run samples, p50/p75/max, frame-floor window, heap delta where
available, and threshold verdicts. Results missing any required field do not satisfy the
budget. Firefox/WebKit run functional parity only.

The P2 benchmark samples active fit/reset/context transitions and one second after they
settle. The stable P1 implementation does not adaptively mutate labels or topology based
on local frame timing; it uses the deterministic label ceiling and complete
relationship-list/Browse fallback on every machine.

## 9. Failure-mode analysis

| Failure mode | Disposition | Detection / proof |
|---|---|---|
| Invalid or missing frontmatter | **Prevent/detect:** validation blocks context output; stderr names paths and stable code. | Golden invalid-fixture test; `GRAPH_INVALID`. |
| Dangling/cyclic links | **Detect/mitigate:** record missing target/cycle; traversal remains bounded and deterministic. | Cycle/dangling fixture. |
| Greedy Mermaid extraction | **Prevent:** heading-local, non-greedy fenced-block parsing. | Multi-diagram regression fixture. |
| Context budget exceeded | **Mitigate:** values outside 4 KiB-1 MiB return `BUDGET_OUT_OF_RANGE`; envelope >1 MiB returns `ENVELOPE_TOO_LARGE` first; otherwise a valid budget smaller than the envelope returns `BUDGET_TOO_SMALL`; chunks truncate deterministically and final bytes are `<= maxBytes`. | Requested-cap tests at 4,095, 4,096, envelope-1, envelope, exact-chunk, 1 MiB, and 1 MiB+1; independent envelope-size fixtures at 1 MiB and 1 MiB+1. |
| Lexical ranking misses semantic synonym | **Accept initially:** record eval miss; add aliases/glossary before embeddings. | Retrieval golden set and recall threshold. |
| Superseded change treated as current | **Prevent/detect:** include only active non-superseded change entries explicitly linked by artifact path. | Supersession fixture. |
| Layout is unstable | **Prevent:** deterministic type/phase lanes and artifact-ID ordering. | Snapshot positions across repeated runs. |
| Browser index exceeds preflight or spatial ceiling | **Prevent/mitigate:** reject over-limit index or route spatial views to Browse/list before layout. | N-1/N/N+1 index-byte, node, and edge fixtures. |
| Search hides selection | **Prevent:** search highlights; explicit filters alone change visibility. | Interaction test. |
| URL restores missing node | **Detect/recover:** return to Browse, name missing ID, offer valid root/parent. | Removed-node history fixture. |
| Index, source, Mermaid-asset, or layout operation stalls | **Detect/recover:** enforce the host-owned lifecycle/deadline contract, abort/ignore late completion, dispose partial resources, and retain Browse/source/list fallback. Synchronous Mermaid render relies on preflight and benchmark gates, not a false timeout claim. | T-1/T/T+1 fake/native scheduler tests for each deadline-bound operation; Mermaid complexity/performance fixtures. |
| Source/diagram complexity exceeds browser bound | **Prevent:** preflight body/block/line/diagram counts before renderer invocation. | N-1/N/N+1 source/diagram fixtures. |
| CLI filesystem read stalls | **Bound at process boundary:** only regular non-symlink files are admitted; every shipped caller enforces the documented 10-second subprocess watchdog and discards output on kill. | Blocking parent/child fixture proves exact-tree termination and empty stdout. |
| CDN or Mermaid fails | **Mitigate:** local shell, metadata, and source remain usable. | Network-blocked browser test. |
| Spatial 3D cannot initialize or exceeds limits | **Mitigate:** route to Graph, preserve semantic state, release pointer/listener/animation resources exactly once. | Unsupported-transform, N/N+1 limit, and repeated mount/fail/unmount tests. |
| HTML surface path is unsafe or points at a template | **Prevent:** derive only safe regular files under approved docs roots and exclude template/portal paths. | Symlink/reparse, traversal, exclusion, and deterministic-order tests. |
| HTML surface count exceeds the portal ceiling | **Prevent:** fail derivation with `SURFACE_LIMIT_EXCEEDED`; browser preflight independently rejects oversized metadata. | 100/101 surface fixtures plus browser limit fixture. |
| Dense graph becomes unreadable | **Mitigate:** semantic zoom, label ceiling, relation/path modes, equivalent list. | Dense fixture and visual/a11y assertions. |

Accepted simplifications:

- `simplify:` lexical ranking is sufficient for the first corpus; add embeddings only
  when the golden retrieval set misses its agreed recall threshold.
- `simplify:` SVG is sufficient through 500 visible nodes/1,000 edges; above that,
  retain Browse/list and add spatial scaling machinery only when real corpus/task
  evidence justifies it.

## Adversarial analysis (STRIDE-lite)

Trust boundaries: committed Markdown/frontmatter/HTML metadata -> parser/index; local
index/Markdown -> browser renderer; Spatial 3D pointer input -> browser camera; protected
workflow dispatch/environment approval -> self-hosted runner/OIDC attestation; CLI input
-> filesystem reads.

| Boundary | STRIDE | Disposition | Control | Negative test |
|---|---|---|---|---|
| Markdown -> browser | **T** tampered frontmatter injects HTML/script-shaped data | mitigate | Validate schema and render metadata, source Markdown, and Mermaid code as literal escaped text. The P1 contract has no Markdown/Mermaid execution step. | Script/HTML fixture renders inert. |
| CLI -> filesystem | **T/E** path traversal through artifact path or CLI ID | mitigate | Resolve only scanned canonical paths under approved roots. | `../` and absolute-path misuse tests. |
| Filesystem path -> opened source | **T/E** a scanned source is replaced by a symlink, reparse point, or different same-size file before/during read | mitigate | Reject links/reparse points, pin regular-file identity across `lstat`/open/`fstat`, use no-follow opens where available, and recheck identity/size/timestamps after the read. Windows has no `O_NOFOLLOW`; its effective control is the identity/reparse pin before and after open. | Symlink, reparse, concurrent mutation, and same-size path-swap fixtures fail closed. |
| Scanner directory -> traversal | **T/E** an intermediate directory is replaced by a symlink or junction after admission but before `os.walk` descends | accept | Exploitation requires concurrent write access to the repository checkout; leaf reads remain identity-pinned and the race does not cross a privilege boundary. Revisit with descriptor-relative traversal if the scanner accepts less-trusted roots. | Accepted local same-user residual risk; no success-shaped fallback. |
| Graph -> grounding packet | **R** context provenance cannot be reconstructed | mitigate | Include line ranges, source/chunk SHA-256, paths, traversal paths, and schema version. | Recompute source/chunk hashes and compare. |
| Scanner -> packet | **I** unintended files enter grounding context | mitigate | Explicit roots/exclusions; no arbitrary path input; packet lists coverage. | Secret-shaped file outside roots never appears. |
| Index -> layout/parser | **D** dense or malformed graph exhausts resources | mitigate | Preflight/index/spatial limits, bounded traversal/layout, and fallback list. | Large/cyclic/over-limit synthetic fixtures. |
| Eval case file -> subprocess | **T/E** a case-controlled `cmd-exit` argv executes with the CI identity | accept | Eval cases are trusted, reviewed repository content; bounded execution limits time, memory, output, and process descendants. CI must not execute `--exec` or `cmd-exit` from unreviewed fork/PR-supplied cases. | Hostile IDs/workspaces fail containment; bounded-process fixtures terminate the full process tree. |
| Spatial 3D -> browser | **T/D/E** pointer/camera path exhausts rendering or exposes hidden actions | mitigate | Native bounded geometry, host-owned actions, explicit limits, pointer release/disposal, Graph fallback. | Exceed limits, force transform/init failure, interrupt pointer capture, repeatedly mount/unmount. |
| HTML surfaces -> browser | **T/E** crafted title/path becomes executable or escapes docs root | prevent | Safe regular-file discovery, escaped text, repo-relative links, template exclusions. | Script-shaped title, traversal path, symlink/reparse, and external-path fixtures. |
| Protected workflow -> self-hosted benchmark runner/OIDC attestation | **S/T/E** a dispatcher, approver, or runner administrator executes unreviewed code or attests forged evidence | mitigate | Canonical protected `main` only, required PR review, exact-SHA credential-free checkout, immutable action pins, protected environment, dedicated one-job ephemeral runner, and attested evidence. | Fork/branch dispatch is skipped; a non-ephemeral runner fails with a stable error code; release validation rejects mismatched evidence. Residual: environment/repository administrators retain bypass or self-approval authority. |

No authentication, authorization, secrets, money, or irreversible actions are added.

## Privacy analysis (LINDDUN-lite)

| Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|
| Committed project docs + local search/selection/context state | **L/D** stable artifact IDs and selected context are visible in the same-device URL/history; no new personal-data category is introduced | mitigate | Same-origin local operation only; no analytics, model egress, cross-user store, or remote state. Existing no-secrets/no-PII rules for committed docs still apply. | Navigation state lasts only in browser history/session and is cleared by leaving the page or removing the hash; document retention follows Git governance. |

## 12. Telemetry and diagnostics

This is a local, single-process documentation tool. Production behavior sends no
analytics over the network, and a custom trace/ring-buffer substrate would add state
without improving correlation.

### CLI

- The `context` command emits only its packet or its one bounded error object.
- Stable result codes and bounded scalar error details are the operational contract; no
  second diagnostics stream or compatibility schema is added.
- The committed benchmark harness emits its own bounded benchmark result artifact; it is
  test evidence, not runtime telemetry.

### Browser

- Use `performance.mark/measure` for index load, layout, context, document fetch/render,
  and Mermaid load/render; clear each mark/measure after its value is consumed.
- Failures show the stable code and recovery action in the local UI. There is no
  downloadable snapshot, persistent diagnostics panel, trace tree, or ring buffer.
- No prompts, document/search text, personal data, or full filesystem paths enter UI
  notices.

**Recorded deviation - Observability O2/O4:** no span/trace context is created because
there is one local process, no service boundary, and no request fan-out. The consequence
is no distributed-trace pivot; the compensating evidence is stable bounded errors,
external benchmark results, and native duration measurements. Add OTel spans only if the
Explorer gains a service boundary or concurrent runtime where correlation is otherwise
lost.

### Browser failure-code registry

| Code | Trigger | Disposition |
|---|---|---|
| `DOC.INDEX.UNAVAILABLE` | index missing, load failed, or timed out | stop waiting; Browse shell + setup/retry guidance |
| `DOC.INDEX.INVALID` | schema, link, policy, or hash invalid | Browse/list; disable affected path actions |
| `DOC.INDEX.LIMIT_EXCEEDED` | browser preflight exceeded | Browse/list only |
| `DOC.URL.INVALID_STATE` | malformed/missing fragment values | normalize to valid/default state + notice |
| `DOC.NAVIGATION.TARGET_MISSING` | selected/context artifact removed | clear invalid target; restore Browse/project-root focus |
| `DOC.SEARCH.INVALID` | decoded search/filter state malformed | clear invalid values; retain valid projection state |
| `DOC.LAYOUT.UNAVAILABLE` | lane or mind-map construction fails or times out | relationship list + Browse |
| `DOC.SPATIAL3D.UNAVAILABLE` | browser lacks required local pointer/transform capability | preserve semantic state in Graph |
| `DOC.SPATIAL3D.LIMIT_EXCEEDED` | 3D node/edge ceiling exceeded | preserve semantic state in Graph |
| `DOC.SPATIAL3D.RENDER_FAILED` | deterministic 3D construction or projection throws | preserve semantic state in Graph |
| `DOC.DOCUMENT.UNAVAILABLE` | body missing, over limit, fetch/render failure, or timeout | metadata/escaped-source/open-file fallback |
| `DOC.DIAGRAM.UNAVAILABLE` | asset/source over limit, asset-load timeout, or render failure | escaped source + local guidance |

## 13. Test and eval plan

### Trigger mapping

- **D0** applies to every test.
- **D1** deterministic logic: traversal, chunking, ranking, budgets, layouts, state
  transitions.
- **D2** wide input domains: graph cycles, malformed frontmatter, Unicode headings,
  large graphs, exact budget boundaries.
- **D3** architecture: admitted artifact body/frontmatter and admitted decision records
  remain canonical; CLI and UI use the same versioned traversal-policy registry;
  optional experiments cannot mutate core state.
- **D4** real-infra integration: real temporary filesystem, local `file://`/HTTP browser
  runs, and blocked-network asset tests.
- **D5-provider** provider verification for the published packet, error, policy-registry,
  URL, and benchmark-result contracts.
- **D6** schema/golden payload: grounding packet v1, policy registry, graph index,
  normalized projection-model fixtures, malformed Mermaid, URL state, and benchmark
  result fixtures.
- **D7** boundary substitutes pair with browser/contract tests against real DOM, History
  API, file loading, native timers, and process-watchdog behavior.
- **A6** contract gate: revision 17 protects the current graph/index, packet/error,
  traversal-policy, URL-state, registry, and benchmark contracts with fixed canonical
  fixtures. Its intentional `docs-index/v2` compatibility break is recorded in the
  INSTALL revision changelog. A complete parameterized previous/current compatibility
  corpus across every listed surface is P2 release-hardening rather than a P0/P1 claim;
  future unrecorded drift remains forbidden.
- UI directives U9/U16/U17 require state, keyboard, contrast, reduced-motion, and
  performance threshold tests.

### Deterministic graph-tool tests

Exhaustive process contract:

| Input/result | Code | Exit | stdout | stderr |
|---|---|---:|---|---|
| Valid complete packet | none | 0 | one packet | empty |
| Valid truncated/health-issue packet | structured metadata only | 0 | one packet | empty |
| Unknown root | `ROOT_NOT_FOUND` | 2 | empty | one error |
| Unknown policy | `POLICY_UNSUPPORTED` | 2 | empty | one error |
| hops <0 or >2 | `HOPS_OUT_OF_RANGE` | 2 | empty | one error |
| maxBytes <4 KiB or >1 MiB | `BUDGET_OUT_OF_RANGE` | 2 | empty | one error |
| invalid graph/schema/hash | `GRAPH_INVALID` | 3 | empty | one error |
| source file >1 MiB | `SOURCE_FILE_TOO_LARGE` | 3 | empty | one error |
| corpus/node/edge/chunk/admitted-byte limit exceeded | `SCAN_LIMIT_EXCEEDED` | 4 | empty | one error |
| mandatory envelope >1 MiB (checked first) | `ENVELOPE_TOO_LARGE` | 4 | empty | one error |
| envelope <=1 MiB and valid maxBytes < envelope | `BUDGET_TOO_SMALL` | 4 | empty | one error |
| unexpected defect | `INTERNAL_ERROR` | 1 | empty | one redacted error |

1. Typed traversal preserves relation and direction.
2. Policy-specific edges and stable ordering match golden JSON.
3. Cycles terminate; dangling targets emit health issues; exact duplicate typed links fail validation.
4. Heading chunk ranges and SHA-256 match source.
5. Mandatory envelope is measured before chunks; packet never exceeds `maxBytes`;
   `BUDGET_OUT_OF_RANGE`, `BUDGET_TOO_SMALL`, and `ENVELOPE_TOO_LARGE` are disjoint
   at requested-cap 4,095, 4,096, envelope-1, envelope, 1 MiB, and 1 MiB+1,
   plus envelope-size 1 MiB and 1 MiB+1.
6. Query ranking is deterministic under ties and Unicode input.
7. Superseded change entries are excluded; unrelated history never enters evidence.
8. Root/file/node/edge/chunk limits fail with stable codes and bounded memory.
9. Mermaid extraction handles multiple diagrams without title bleed.
10. Grounding packet and traversal-policy schemas remain backward compatible.
11. Targeted negative and fault-injection tests reject reversed-edge,
    removed-health-issue, cycle-guard, and off-by-one-budget defects.
12. Every load-bearing error and timeout emits its registered code and satisfies the
    exit/stdout/stderr matrix.
13. A parameterized precedence ladder supplies one dual-fault fixture for every adjacent
    stage in the declared order; each asserts the earlier stage is the sole code/exit/
    stream result and that the later stage was not executed. Envelope size 1 MiB+1 with
    a small valid cap and excess chunks specifically yields `ENVELOPE_TOO_LARGE`.
14. Each `SCAN_LIMIT_EXCEEDED` fixture asserts the exact `details.limit` discriminator.
15. Fixed UTF-8 preimage/digest vectors cover CRLF, non-ASCII, key-order, array-order,
    complete `policySha256`, and complete `graphSha256` preimages independently in Python
    and JavaScript; field add/remove negative fixtures prove the composite projection.

For D2, a seeded stdlib property harness generates valid and malformed graphs with
Unicode headings, cycles, dangling targets, exact duplicate typed links, distinct
parallel relations, exact byte boundaries,
and shuffled input order. Invariants: traversal terminates within the declared bounds;
ordered output is invariant under input ordering; every path starts at `rootId` and
uses registered directed edges; every emitted hash matches exact text; serialized
success/error output validates its schema; packet bytes never exceed the inclusive
budget. `simplify:` a narrow deterministic reducer removes graph elements and shortens
text/budget values only because Testing Strategy D2 requires a shrunk counterexample;
it is not a general property-testing framework. Adopt a property library only if new
generators require shrink strategies beyond graph lists, text, and integer budgets.
Every reduced counterexample becomes a named permanent fixture.

Common policy fixtures run through Python and the browser traversal module. Tests
compare ordered tuples `(from,to,rel,direction,depth)` for grounding, impact, proof, and
explore-neighborhood at hops 0/1/2, with cycles and missing targets. A shared registry
without this cross-runtime parity proof is insufficient.
The seeded property harness also exports every generated graph/query/policy case to both
runtimes and compares the same ordered tuples, so parity is not limited to hand-authored
goldens.

### Retrieval evals

Commit 20 golden query/root cases with a pinned expected-chunk denominator. Each case
records:

- root artifact/query;
- required source chunk IDs;
- forbidden stale/superseded chunks;
- maximum byte budget;
- expected health issues and truncation state.

First-slice thresholds:

- 100% required provenance fields;
- 100% budget compliance;
- 100% stale/flagged health-issue recall;
- >=90% micro-averaged required-chunk recall across the pinned expected-chunk
  denominator (and at least 18/20 cases with all must-have chunks).

Falling below retrieval recall opens the next-rung decision (aliases/glossary, then
possibly embeddings); it does not silently change ranking.

### Browser tests

Use a plain Node `assert` suite for renderer-independent graph/state/layout functions.
Implementation first adds a pinned Playwright harness and CI command; no UI correctness
claim may pass before that harness has observed the relevant test red. Playwright
browser automation is the mandatory implementation gate for:

- Browse is the real default projection.
- Selection does not change context; `Explore neighborhood` does.
- Context centers/fits and is restored through URL/browser Back.
- Search highlights without topology change.
- Tree, graph, mind-map, toolbar, Escape, and focus-restoration keyboard flows.
- Spatial 3D pointer orbit plus labelled keyboard yaw/pitch controls.
- Spatial and relationship-list node/edge/path/action ID sets are equal.
- Reduced motion suppresses camera/layout animation.
- 320px and 400% zoom route/back/focus lifecycle.
- CDN-blocked and source-fetch failure degradation.
- WCAG checks: labels/roles/focus order/contrast/no color-only meaning.
- Sticky-header focus visibility, unique knowledge-surface names, actionable empty-state
  controls, and Spatial 3D/portal target-size, contrast, and forced-colors coverage.
- Reproducible cold/warm layout and interaction thresholds against synthetic 50, 500,
  and 1,000-node fixtures in pinned Chromium. Firefox/WebKit run functional,
  keyboard/a11y, limit, and fallback parity without asserting Chromium's timing budget.

The implemented revision-17 A6 gate uses committed canonical fixtures for graph/index
input, grounding packet success/error, traversal policy, URL state, browser failure
registry, and benchmark result. The `docs-index/v2` incompatibility is explicit in the
revision changelog rather than silently accepted. A complete parameterized
previous/current matrix for CLI help/exit/stream behavior and every changed-contract
surface remains P2; aggregate pass rates must not hide a regressed case when that matrix
lands.

Promise-to-test matrix:

| Promise | Named test | Oracle / falsifying mutation |
|---|---|---|
| Packet/error process contract | `Context_InputClass_UsesExpectedExitAndStreams` | fail if any input maps to the wrong code/exit/stream count |
| Versioned schema regression gate | current canonical hash, traversal, packet/error, URL, registry, and benchmark fixture suites | fail for current-contract drift; `docs-index/v2` is the recorded revision-17 decision, while the complete previous/current matrix is P2 |
| Canonical hashes and mismatch handling | `CanonicalHash_PrimitiveAndCompositeFixedPreimages_MatchIndependentDigests` | fail after CRLF, non-ASCII, key-order, array-order, graph/policy field add-remove, or hash-mismatch mutation in either runtime |
| Projection-model order | `ProjectionModel_Fixture_ProducesCanonicalOrderAndEdgeIds` | fail after lane/order or edge-ID mutation; exact duplicate typed links must be rejected |
| Retrieval quality and exclusions | `Grounding_GoldenQueries_MeetRecallAndExclusionThresholds` | fail if required recall/health-issue coverage falls below threshold or forbidden history appears |
| Resource ceilings | `Context_NMinusOneNPlusOne_ReportsExactLimitDiscriminator` | fail if illegal input is admitted, legal boundary rejected, or wrong `details.limit` emitted |
| Multi-fault error precedence | `Context_OversizeEnvelopeWithSmallCapAndExcessChunks_ReturnsEnvelopeTooLargeFirst` | after request/graph/source validation succeeds, fail unless `ENVELOPE_TOO_LARGE` wins over `BUDGET_TOO_SMALL` and chunk-admission/truncation outcomes |
| Python/browser traversal parity | `Traversal_SamePolicyFixture_ProducesSameOrderedPaths` | fail on any ordered path tuple difference or if either runtime processes zero seeded generated cases |
| CLI/browser benchmark reproducibility | `Benchmark_MissingEnvironmentOrHash_RejectsThresholdClaim` | fail if a threshold verdict lacks pinned environment/hash fields |
| CLI wall/RSS budget | `Context_MaximumCorpus_OnReferenceEnvironment_MeetsBudget` | fail when p75 wall time or peak RSS exceeds threshold |
| Browser shell/layout/interaction budgets (P2 release gate) | `Explorer_ReferenceEnvironment_MeetsPerformanceBudgets` | fail when any p75/frame-floor threshold is missed; no P1 completion claim until the harness exists |
| Full error-precedence ladder | `Context_EachAdjacentDualFault_EmitsOnlyEarlierFailure` | fail if any adjacent-stage swap survives or the later stage executes |
| Exact async deadlines | `Deadline_OperationAtTMinusOneTAndTPlusOneDisposesLateResult` | fail if T-1 does not commit, T/T+1 do not abort, late settle mutates state, or disposal count !=1; browser source tests assert the implemented 5,000ms binding |
| Scheduler fidelity | `Deadline_NativeScheduler_MatchesFakeSchedulerContract` | fail if native timers violate the fake-scheduler settlement/abort contract |
| CLI watchdog lifecycle | `BenchmarkWatchdog_StalledFixture_TerminatesExactProcessTree` | injected short watchdog must kill the blocking parent/child fixture, emit no stdout, and leave no surviving process |
| Pack-owned caller enforcement | `ContextCallers_AllUseTimeoutHelperAndDrainMaximumPacket` | fail if any owned invocation bypasses the helper, omits the 10s timeout, waits before draining, accepts killed/nonzero stdout, cannot deliver a 1 MiB success packet, or fails to kill on stdout >1 MiB / stderr >64 KiB |
| Browser failure registry | `BrowserFailure_RegisteredTrigger_ShowsCodeAndFallback` | fail if any registered code has no trigger/fallback test |
| Reducer transition closure | `Reducer_EveryEvent_PreservesDeclaredInvariants` | fail if any event is unhandled or mutates a field outside its transition row |
| Reducer invalid-input normalization | `Reducer_EachEvent_InvalidInput_UsesDeclaredRecovery` | fail if unsupported projection/path/route, invalid artifact, invisible context, or incoherent restored pair bypasses its named notice/no-change/normalization branch |
| Browse is canonical default | `Explorer_InitialRoute_ShowsBrowse` | fail if first rendered projection is Graph/Mind map |
| Selection never changes context/root | `Reducer_SelectNode_PreservesContextAndMindMapRoot` | fail if `SELECT_NODE` mutates context or Mind-map root |
| Filter cannot silently invalidate context | `Reducer_FilterExcludesContext_ClearsWithNoticeAndHistory` | fail if excluded context remains active or clears without notice/Back recovery |
| URL/back/focus round-trip | `History_BackNavigation_RestoresStateAndInitiator` | fail if selected/context/path or active element differs |
| Graph/list parity | `Projection_SameNormalizedModel_ExposesEqualOrderedSpatialAndListIds` | fail after deleting, reordering, or reversing any visible edge/action |
| Complete control states | `Controls_DeclaredStates_RenderSpecifiedBehavior` | fail when any named control lacks disabled/loading/empty/error/success behavior where applicable |
| Keyboard/ARIA | `Explorer_KeyboardFlows_ExposeNamedSemantics` | fail if Space/Enter, tree keys, search controls, status/alert, or accessible name is removed |
| Full accessibility interaction contract | `Explorer_AllBrowsers_MeetFocusOrderKeysAnnouncementsAndTargetSizes` | fail on spatial/list DOM order mismatch, wrong directional half-plane/angular-distance target, editable/global-key interception, duplicate/missing live-region announcement, a reduced-emphasis focused node losing the full focus-ring contract, or an operable control below resolved `{targets.minimum}` in either axis |
| Light/dark/high-contrast/forced-colors | `Theme_AllModes_MeetContrastAndBoundaryFloors` | fail if any audited full-strength or reduced-emphasis text/graphical pairing misses its threshold, if opacity compositing weakens a contrast-bearing state, or if boundaries disappear |
| 320px/400% routes | `Responsive_NarrowOrZoomedViewport_ReflowsWithoutTaskScroll` | fail on horizontal task-content clipping or lost route focus |
| Offline/timeouts | `Offline_CleanContextBlocksNetworkBeforeNavigationAndCoreTasksRemainUsable` | fail if `file://` or localhost needs a request after pre-navigation block |
| No remote telemetry | `Explorer_NetworkEnabled_EmitsNoNonLoopbackRequests` | fail on any non-loopback request |
| Index/spatial limits | `Browser_OverLimitIndexOrProjection_PreventsLayout` | N-1/N/N+1 fixtures fail if over-limit data reaches layout |
| Document/diagram limits | `Browser_SourceAndDiagram_NMinusOneNPlusOne_PreflightBeforeRender` | for body 1 MiB, block 64 KiB, 500 lines, and 20 diagrams, N is the last legal value and N+1 the first rejection; fail if any rejected input reaches renderer |
| HTML/script sanitization | `Renderer_HostileMarkdown_RendersInertContent` | fail if script/event-handler fixture executes |
| Filesystem boundary | `Context_PathEscapesApprovedRoots_RejectsInput` | fail if relative traversal or absolute path is read |
| Corpus exclusion | `Context_SecretShapedFileOutsideRoots_NeverEntersPacket` | fail if excluded file path/text appears |
| Internal-error redaction | `Context_InternalError_RedactsStackSecretsPathsAndUsernames` | force an internal exception containing seeded stack/path/user/secret values; fail unless stderr contains only the stable code, generic message, and bounded scalars with none of the seeds |
| Source tampering / path origin | `Explorer_HashOrApprovedOriginMismatch_RejectsBeforeRender` | fail if altered source content or a path outside the same-origin `docs/` root is rendered; signed index authenticity is a deployment-layer concern outside this local static viewer |

The Proof Pack maps every design promise and handled failure mode to its test, oracle,
red-observed evidence, and residual risk. Browser evidence is required for all UI
correctness claims.

## 14. Implementation backlog

| Priority | Class | Item | Exit condition |
|---|---|---|---|
| P0 | issue | Fix Mermaid fenced-block extraction and add regression fixtures. | No title bleed across multiple headings/diagrams. |
| P0 | decision | Resolve how canonical `pack/knowledge/` enters repository grounding before packet v1 freezes. | ADR selects graph records or the recommended versioned source registry. |
| P0 | risk | Implement `context` packet/error v1 with provenance, policy/graph hashes, shared traversal policy, hard limits, property tests, exact full-packet byte budget, and the one timeout/draining helper for all pack-owned callers. | Grounding golden/property/parity/resource-limit/caller-lifecycle suites meet thresholds. |
| P0 | issue | Make Browse the actual default and add a non-spatial relationship list. | V4 and keyboard baseline pass. |
| P0 | risk | Replace clickable non-semantic containers with keyboard/screen-reader controls. | WCAG smoke and full keyboard path pass. |
| P0 | todo | Add the pinned Playwright harness and browser CI command before UI behavior changes. | Promise-to-test matrix is executable in Chromium, Firefox, and WebKit. |
| P1 | todo | Separate selection from neighborhood context; encode context in URL/browser history. | Cross-projection and Back/focus-restoration tests pass. |
| P1 | todo | Add deterministic type/phase lane layout, semantic zoom, arrows, path modes, Fit/Reset/Explore, and spatial-limit fallback. | Repeated layout snapshots stable; N-1/N/N+1 limits and performance budget pass. |
| P1 | risk | Include only active, artifact-linked change entries in v1 context. | Unrelated/superseded history exclusion tests pass. |
| P1 | issue | Make search highlight-only; make filters explicit and selection-preserving. | Search/filter interaction tests pass. |
| P1 | todo | Add responsive URL routes and deterministic Back/focus behavior. | Keyboard/touch tests pass at 320px and 400% zoom. |
| P1 | risk | Make offline/CDN failure degrade to local navigation and source. | Network-blocked test passes. |
| P2 | todo | Add native performance marks, stable recovery-surface codes, host-owned operation deadlines, and committed benchmark harnesses. | Error/timeout/limit and reproducible benchmark tests pass without remote telemetry or browser diagnostic persistence. |
| P3 | completed decision | Reject `3d-force-graph`; ship native bounded Spatial 3D over the normalized model with no plugin contract or runtime dependency. | Deterministic coordinates, Graph fallback, accessibility, and browser lifecycle tests pass. |

## 15. Adversarial gate record

Current verdict: **PASS — design accepted; implementation proof remains gated**.

`GATE design-adversarial-review · 2026-07-10 · Patterns Expert, Simplifier, Test
Architect, UX & Accessibility, SRE & Systems Diagnostician · exit criteria met:
deterministic/cross-runtime grounding contract; smallest-correct scope; executable
proof paths; WCAG 2.2 AA surface contract; bounded process/browser lifecycle · verdict:
PASS · vetoes: none`

- Patterns Expert: PASS. Generated property cases and fixed fixtures use both Python
  and browser traversal implementations and compare canonical ordered path tuples.
- Simplifier: PASS — "Lean already. Ship." Narrative memory is excluded from evidence
  v1; 3D remains a disposable experiment with no stable plugin contract.
- Test Architect: PASS at the design gate. Exact contracts, current canonical fixtures,
  mutation/fault oracles, internal-error redaction, and caller-lifecycle tests are named;
  the complete A6 previous/current matrix is explicitly P2. Red-observed evidence and the
  populated Proof Pack remain implementation obligations.
- UX & Accessibility: PASS at the design gate. Browse-first IA, selection/context
  separation, graph/list equivalence, deterministic keyboard behavior, responsive
  routes, audited reduced-emphasis tokens, full-strength focus, and 2D parity satisfy
  the WCAG 2.2 AA specification floor.
- SRE: PASS at the design gate. Hard limits, one bounded concurrent-drain invocation
  helper, exact process-tree timeout behavior, reproducible benchmark contracts, active
  frame sampling, and Browse/list degradation close the operational conditions.

Residual risk:

- No user-study evidence yet proves that 3D improves task completion or comprehension.
- Exact provider token counts are unavailable without a tokenizer contract; byte
  budgets are the exact portable boundary.
- Canonical pack knowledge remains outside the docs graph until the P0 architecture
  decision is made.

## 16. Status

| | |
|---|---|
| **Completed** | Deterministic grounding, Browse/Graph/Mind-map, native bounded Spatial 3D, project-memory boundaries, safe HTML knowledge surfaces, accessibility states, and the implementation Proof Pack. |
| **Remaining** | Pinned-reference latency evidence (or a human-approved deviation) before revision 17 may be released. |
| **Best next action** | Keep revision 17 unreleased until the qualified reference benchmark gate passes. |
