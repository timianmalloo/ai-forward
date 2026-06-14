// Derived from artifact frontmatter by scripts/docs-graph.py — DO NOT hand-edit (frontmatter wins; see knowledge-visualization.md V2/V18).
window.DOCS_INDEX = {
  "project": "AI-Forward",
  "generated": "2026-06-14T22:31:54Z",
  "generator": "docs-graph.py derive",
  "artifacts": [
    {
      "id": "architecture",
      "path": "docs/architecture.md",
      "title": "AI-Forward — Architecture Overview",
      "type": "architecture",
      "status": "accepted",
      "owner": "@mallalieut",
      "phase": "documentation",
      "reviewBy": "2026-12-14",
      "reviewSuggested": [],
      "summary": "The architecture of record for this repository: a dual-purpose repo that is both the canonical SOURCE of the AI-Forward Pack (pack/) and a live INSTALL of it (.claude/, docs/), kept in lockstep by tools/sync-pack.ps1. Includes the four diagram families and the tool/CLI reference, verified against the repo as of the documented commit.",
      "tags": [
        "pack",
        "knowledge-graph",
        "tooling",
        "source-and-install"
      ],
      "links": [
        {
          "to": "docs-index",
          "rel": "relates-to"
        }
      ],
      "diagrams": [
        {
          "kind": "class",
          "title": "Architecture: AI-Forward (pack source + live dogfood install)\n\n- **Status:** Accepted\n- **Tier:** N/A — this repository is a knowledge/tooling package, not an AI runtime system, so the LOA capability tiers (T0–T4, which allocate *inference* cost) do not apply here. The tier model is part of the pack's *payload*, not this repo's own runtime. `[Verified]` (no inference code in the repo).\n- **Driving context:** `README.md`, `CLAUDE.md`, `pack/OVERVIEW.md`\n- **Documented commit:** see `docs/_meta.json`\n\n## Context & constraints\n\nThis repository is **two things at once** (`README.md` §\"This repo is two things at once\"):\n\n1. **The canonical source** of the AI-Forward Pack — everything you edit to expand the pack lives under `pack/`. `[Verified: README.md, pack/]`\n2. **A live install of the pack** — the pack is installed into this same repo (`.claude/`, `docs/`) so the skills, agents, and knowledge are active in Claude Code *while you work on the pack itself*. Dogfooding: the pack is built using the pack. `[Verified: .claude/, CLAUDE.md]`\n\nThe load-bearing constraint that shapes the whole structure:\n\n> **`.claude/` and `docs/` are GENERATED from `pack/`** by `tools/sync-pack.ps1` and committed so a fresh clone has a working install with no setup. `pack/` is the single source of truth — never edit the generated copies directly; they are overwritten on the next sync. `[Verified: CLAUDE.md, tools/sync-pack.ps1]`\n\nConsequence for documentation (a finding surfaced by this run): the generated knowledge documents under `.claude/knowledge/` and `docs/ai-forward-pack/` carry **no YAML frontmatter** (they are vendored prose, not graph nodes). The Knowledge-Visualization graph model (V1–V18) therefore sees **zero artifacts** until frontmatter'd documentation (like this file) is added under `docs/`. See *Flagged risks* below. `[Verified: docs-graph.py inventory → \"artifacts\": 0]`\n\n## Archetype & rationale\n\nNo LOA system archetype (A–I) applies — those classify AI-integrated *runtime* systems. The applicable shape here is a classic **source → build → install → consumer** pipeline with a **dogfood loopback**: the install layer feeds back into the authoring experience (Claude Code reads `.claude/` while you edit `pack/`). `[Inferred from repo structure]`\n\n## Component map & boundaries\n\nThe major components and the real dependency edges between them (read from `tools/sync-pack.ps1`, `tools/rebuild-overview.ps1`, `tools/package-pack.ps1`, and the directory layout):\n\n```mermaid\nflowchart TB\n  subgraph SRC[\"pack/ — canonical source (edit here)\"]\n    K[\"knowledge/*.md<br/>(reasoning spine + roster + foundation)\"]\n    C[\"commands/&lt;name&gt;/SKILL.md<br/>(the 10 skills)\"]\n    T[\"templates/*<br/>(artifacts each skill emits)\"]\n    A[\"adapters/<br/>(Claude Code + Copilot agents, INSTALL.md)\"]\n    SC[\"scripts/  ·  evals/  ·  ci/  ·  examples/\"]\n    PD[\"README · OVERVIEW · research-synthesis\"]\n  end\n\n  subgraph TOOLS[\"tools/ — build\"]\n    SYNC[\"sync-pack.ps1\"]\n    PKG[\"package-pack.ps1\"]\n    OVR[\"rebuild-overview.ps1\"]\n  end\n\n  subgraph INSTALL[\".claude/ + docs/ — generated install (do not hand-edit)\"]\n    CK[\".claude/knowledge/*.md\"]\n    CS[\".claude/skills/*\"]\n    CA[\".claude/agents/*.md\"]\n    DP[\"docs/ai-forward-pack/<br/>templates + scripts + pack docs\"]\n    EXP[\"docs/index.html<br/>(Docs Explorer)\"]\n    IDX[\"docs/docs-index.js<br/>(accumulated graph index)\"]\n    ARCH[\"docs/architecture.md · index.md · _meta.json<br/>(this bundle)\"]\n  end\n\n  subgraph CONSUMERS[\"consumers\"]\n    CC[\"Claude Code / Copilot<br/>(read .claude/)\"]\n    WEBO[\"web/ai-forward-pack-overview.jsx<br/>(embeds pack .zip for download)\"]\n    WEBE[\"web/ai-forward-pack-explainer.html<br/>(interactive explainer)\"]\n    ZIP[\"dist/ai-forward-pack.zip\"]\n  end\n\n  K --> SYNC\n  C --> SYNC\n  T --> SYNC\n  A --> SYNC\n  SYNC --> CK & CS & CA & DP & EXP\n  C -. \"skills reference\" .-> CK\n  CA -. \"agents reference\" .-> CK\n  DP --> GRAPH[\"docs-graph.py<br/>(in docs/ai-forward-pack/scripts)\"]\n  GRAPH --> IDX\n  ARCH --> GRAPH\n  IDX --> EXP\n  CK --> CC\n  CS --> CC\n  CA --> CC\n  SRC --> PKG --> ZIP\n  SRC --> OVR --> WEBO\n  CK -. \"derived content\" .-> WEBE\n```\n\nBoundaries that matter:\n- **Source ↔ install boundary** — crossed *only* by `tools/sync-pack.ps1`. Editing the install side directly is a contract violation (the next sync overwrites it). `[Verified: CLAUDE.md, sync-pack.ps1]`\n- **`sync-pack.ps1` write scope** — it writes only `.claude/{knowledge,skills,agents}`, `docs/ai-forward-pack/**`, and `docs/index.html`; it **intentionally does not touch** `docs/docs-index.js` (skills accumulate it) or other `docs/` root files. This is why this bundle (`docs/architecture.md`, `docs/index.md`, `docs/_meta.json`) and `web/ai-forward-pack-explainer.html` have a stable home that sync will not clobber. `[Verified: tools/sync-pack.ps1 lines 22, 92–98]`\n\n## Key flow — the sandbox / dogfood loop (sequence)\n\nThe authoring loop from `README.md` §\"Expanding the pack\", with the graph-refresh step `/document` adds:\n\n```mermaid\nsequenceDiagram\n  actor Dev as Author\n  participant Pack as pack/ (source)\n  participant Sync as tools/sync-pack.ps1\n  participant Install as .claude/ + docs/\n  participant CC as Claude Code (this repo)\n  participant Graph as docs-graph.py\n  participant Explorer as docs/index.html\n\n  Dev->>Pack: edit a knowledge doc / SKILL.md / persona / template\n  Dev->>Sync: pwsh tools/sync-pack.ps1\n  Sync->>Install: mirror knowledge, skills, agents, templates, scripts\n  Sync->>Install: regenerate docs/index.html from template\n  Note over Sync,Install: docs-index.js is NOT touched (accumulated separately)\n  Dev->>CC: try the change (regenerated skills/agents are now live)\n  CC-->>Dev: run a skill; dogfood the edit\n  Dev->>Graph: /document → docs-graph.py derive\n  Graph->>Install: write docs/docs-index.js from frontmatter\n  Graph->>Explorer: index loaded; hierarchy · graph · mind map · health render\n  Dev->>Pack: commit pack/ + .claude/ + docs/ together (lockstep)\n```\n\n`[Verified: README.md §\"Expanding the pack (the sandbox loop)\", sync-pack.ps1, docs-graph.py --help]`\n\n## Layered view (source → consumer)\n\nThe repo's own layering (distinct from the LOA *capability* tiers it ships as payload):\n\n```mermaid\nflowchart TB\n  subgraph L4[\"Consumer layer\"]\n    direction LR\n    cc[Claude Code / Copilot]:::c\n    ex[Docs Explorer + web explainer]:::c\n    z[dist/ zip for other repos]:::c\n  end\n  subgraph L3[\"Install layer (generated, committed)\"]\n    direction LR\n    claude[.claude/ knowledge·skills·agents]:::i\n    docs[docs/ pack-docs·scripts·templates·index]:::i\n  end\n  subgraph L2[\"Build layer\"]\n    direction LR\n    sync[sync-pack.ps1]:::b\n    pkg[package-pack.ps1]:::b\n    ovr[rebuild-overview.ps1]:::b\n  end\n  subgraph L1[\"Source layer (single source of truth)\"]\n    pack[pack/ knowledge·commands·templates·adapters·scripts]:::s\n  end\n  L1 --> L2 --> L3 --> L4\n  classDef s fill:#1d2b4d,stroke:#5a7cff,color:#dde6ff\n  classDef b fill:#13324a,stroke:#5ad1c7,color:#dffaf6\n  classDef i fill:#2a2440,stroke:#a98bff,color:#efeaff\n  classDef c fill:#163024,stroke:#56d364,color:#dcffe4\n```\n\nDependency direction points **up only** (source → build → install → consumer); no consumer writes back into source except through the human author editing `pack/`. `[Verified: tools/*.ps1]`\n\n## Domain model (class) — the UI Archetype Grammar\n\nThe most code-like structure in the repo is the **Archetype Grammar** (`ui-archetype-grammar.md` EBNF, G1–G16) and its catalog (`ui-archetype-catalog.md`). Documented here as a class model because it is the conceptual schema the experience and the codegen contract are built on:",
          "mermaid": "classDiagram\n  class Signature {\n    +Name name\n    +FacetList facets\n    +StyleHints? hints\n    +validate() conflicts\n    +roundTrip() bool  %% G10: identify AND generate\n  }\n  class Facet {\n    <<abstract>>\n    +String key\n  }\n  class SingleValuedFacet {\n    +Value value  %% Type, Arch, Layout, Density, Pacing, ...\n  }\n  class MultiValuedFacet {\n    +Value[] values  %% Nav, Input, Feedback, Motion, A11y (joined with +)\n  }\n  class StyleHints {\n    +String[] hints  %% bounded NL decoration, applied last\n  }\n  class Archetype {\n    +String id          %% A1..F2\n    +String name\n    +Exemplar[] exemplars\n    +Signature canonical\n    +String codegenDescriptor\n  }\n  Signature \"1\" o-- \"4..*\" Facet : composes\n  Facet <|-- SingleValuedFacet\n  Facet <|-- MultiValuedFacet\n  Signature \"0..1\" *-- \"1\" StyleHints : decorated by\n  Archetype \"1\" *-- \"1\" Signature : canonical\n  Archetype \"1\" o-- \"1..*\" Exemplar\n  note for Signature \"G4: MUST carry Type, Arch, Layout, Pacing.\\nG1: always composed with a concrete U1–U20 / S1–S18 spec.\""
        }
      ]
    },
    {
      "id": "docs-index",
      "path": "docs/index.md",
      "title": "AI-Forward — Documentation Map of Content",
      "type": "doc",
      "status": "accepted",
      "owner": "@mallalieut",
      "phase": "documentation",
      "reviewBy": "2026-12-14",
      "reviewSuggested": [],
      "summary": "A curated Map of Content (V3) over the AI-Forward repo's documentation — the human entry point linking the architecture overview, the interactive explainer, the downloadable overview, the Docs Explorer, and the pack's own knowledge and skills.",
      "tags": [
        "moc",
        "navigation",
        "knowledge-graph"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "documents"
        }
      ],
      "diagrams": []
    }
  ]
};
