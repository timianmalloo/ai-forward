// Derived from artifact frontmatter by scripts/docs-graph.py — DO NOT hand-edit (frontmatter wins; see knowledge-visualization.md V2/V18).
window.DOCS_INDEX = {
  "schemaVersion": "docs-index/v2",
  "project": "AI-Forward",
  "generated": "2026-07-12T00:37:11Z",
  "generator": "docs-graph.py derive",
  "rootId": "architecture",
  "artifactTypes": [
    "knowledge",
    "glossary",
    "spec",
    "architecture",
    "adr",
    "design",
    "design-language",
    "investigation",
    "proof-pack",
    "decision-note",
    "threat-model",
    "privacy-review",
    "api",
    "source",
    "doc",
    "index"
  ],
  "relationRegistry": [
    "implements",
    "refines",
    "depends-on",
    "supersedes",
    "tested-by",
    "documents",
    "uses-term",
    "relates-to"
  ],
  "policyVersion": "traversal-policy/v1",
  "policySha256": "968b035a9618e6f997592e4f7ae91fd412b1c059c0ee89d6d8ff3025c26279fd",
  "traversalPolicies": {
    "grounding": [
      {
        "rel": "implements",
        "direction": "outbound",
        "priority": 0
      },
      {
        "rel": "refines",
        "direction": "outbound",
        "priority": 1
      },
      {
        "rel": "depends-on",
        "direction": "outbound",
        "priority": 2
      },
      {
        "rel": "uses-term",
        "direction": "outbound",
        "priority": 3
      },
      {
        "rel": "tested-by",
        "direction": "outbound",
        "priority": 4
      },
      {
        "rel": "documents",
        "direction": "outbound",
        "priority": 5
      }
    ],
    "impact": [
      {
        "rel": "implements",
        "direction": "inbound",
        "priority": 0
      },
      {
        "rel": "refines",
        "direction": "inbound",
        "priority": 1
      },
      {
        "rel": "depends-on",
        "direction": "inbound",
        "priority": 2
      },
      {
        "rel": "tested-by",
        "direction": "inbound",
        "priority": 3
      },
      {
        "rel": "uses-term",
        "direction": "inbound",
        "priority": 4
      }
    ],
    "proof": [
      {
        "rel": "tested-by",
        "direction": "outbound",
        "priority": 0
      }
    ],
    "explore-neighborhood": [
      {
        "rel": "depends-on",
        "direction": "outbound",
        "priority": 0
      },
      {
        "rel": "depends-on",
        "direction": "inbound",
        "priority": 0
      },
      {
        "rel": "documents",
        "direction": "outbound",
        "priority": 1
      },
      {
        "rel": "documents",
        "direction": "inbound",
        "priority": 1
      },
      {
        "rel": "implements",
        "direction": "outbound",
        "priority": 2
      },
      {
        "rel": "implements",
        "direction": "inbound",
        "priority": 2
      },
      {
        "rel": "refines",
        "direction": "outbound",
        "priority": 3
      },
      {
        "rel": "refines",
        "direction": "inbound",
        "priority": 3
      },
      {
        "rel": "relates-to",
        "direction": "outbound",
        "priority": 4
      },
      {
        "rel": "relates-to",
        "direction": "inbound",
        "priority": 4
      },
      {
        "rel": "supersedes",
        "direction": "outbound",
        "priority": 5
      },
      {
        "rel": "supersedes",
        "direction": "inbound",
        "priority": 5
      },
      {
        "rel": "tested-by",
        "direction": "outbound",
        "priority": 6
      },
      {
        "rel": "tested-by",
        "direction": "inbound",
        "priority": 6
      },
      {
        "rel": "uses-term",
        "direction": "outbound",
        "priority": 7
      },
      {
        "rel": "uses-term",
        "direction": "inbound",
        "priority": 7
      }
    ]
  },
  "limits": {
    "indexBytes": 5242880,
    "artifacts": 1000,
    "relationships": 5000,
    "spatialNodes": 500,
    "spatialEdges": 1000,
    "visibleLabels": 150,
    "surfaces": 100
  },
  "artifacts": [
    {
      "id": "adr-0001-grounding-source-corpus-registry",
      "path": "docs/adr/0001-grounding-source-corpus-registry.md",
      "title": "ADR-0001: Use a versioned supplemental source-corpus registry",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Keeps frontmatter-bearing docs as the authoritative project graph while admitting canonical pack knowledge through a separate, versioned supplemental source-corpus registry. Generated Claude and Copilot wrappers remain projections, never parallel graph authorities.",
      "tags": [
        "docs-explorer",
        "grounding",
        "source-corpus",
        "knowledge-graph"
      ],
      "links": [
        {
          "to": "design-docs-explorer-grounding-spatial-navigation",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "eb87d82543bc3da18f2bb7880670dd33396f24ecc6f7cc94dba3b09c3f69dd12"
    },
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
          "kind": "flowchart",
          "title": "Component map & boundaries",
          "mermaid": "flowchart TB\n  subgraph SRC[\"pack/ — canonical source (edit here)\"]\n    K[\"knowledge/*.md<br/>(reasoning spine + roster + foundation)\"]\n    C[\"commands/&lt;name&gt;/SKILL.md<br/>(the 10 skills)\"]\n    T[\"templates/*<br/>(artifacts each skill emits)\"]\n    A[\"adapters/<br/>(Claude Code + Copilot agents, INSTALL.md)\"]\n    SC[\"scripts/  ·  evals/  ·  ci/  ·  examples/\"]\n    PD[\"README · OVERVIEW · research-synthesis\"]\n  end\n\n  subgraph TOOLS[\"tools/ — build\"]\n    SYNC[\"sync-pack.ps1\"]\n    PKG[\"package-pack.ps1\"]\n  end\n\n  subgraph INSTALL[\".claude/ + docs/ — generated install (do not hand-edit)\"]\n    CK[\".claude/knowledge/*.md\"]\n    CS[\".claude/skills/*\"]\n    CA[\".claude/agents/*.md\"]\n    DP[\"docs/ai-forward-pack/<br/>templates + scripts + pack docs\"]\n    EXP[\"docs/index.html<br/>(Docs Explorer)\"]\n    IDX[\"docs/docs-index.js<br/>(accumulated graph index)\"]\n    ARCH[\"docs/architecture.md · index.md · _meta.json<br/>(this bundle)\"]\n  end\n\n  subgraph CONSUMERS[\"consumers\"]\n    CC[\"Claude Code / Copilot<br/>(read .claude/)\"]\n    WEBE[\"web/ai-forward-pack-explainer.html<br/>(interactive explainer)\"]\n    ZIP[\"dist/ai-forward-pack.zip\"]\n  end\n\n  K --> SYNC\n  C --> SYNC\n  T --> SYNC\n  A --> SYNC\n  SYNC --> CK & CS & CA & DP & EXP\n  C -. \"skills reference\" .-> CK\n  CA -. \"agents reference\" .-> CK\n  DP --> GRAPH[\"docs-graph.py<br/>(in docs/ai-forward-pack/scripts)\"]\n  GRAPH --> IDX\n  ARCH --> GRAPH\n  IDX --> EXP\n  CK --> CC\n  CS --> CC\n  CA --> CC\n  SRC --> PKG --> ZIP\n  CK -. \"derived content\" .-> WEBE"
        },
        {
          "kind": "sequence",
          "title": "Key flow — the sandbox / dogfood loop (sequence)",
          "mermaid": "sequenceDiagram\n  actor Dev as Author\n  participant Pack as pack/ (source)\n  participant Sync as tools/sync-pack.ps1\n  participant Install as .claude/ + docs/\n  participant CC as Claude Code (this repo)\n  participant Graph as docs-graph.py\n  participant Explorer as docs/index.html\n\n  Dev->>Pack: edit a knowledge doc / SKILL.md / persona / template\n  Dev->>Sync: pwsh tools/sync-pack.ps1\n  Sync->>Install: mirror knowledge, skills, agents, templates, scripts\n  Sync->>Install: regenerate docs/index.html from template\n  Note over Sync,Install: docs-index.js is NOT touched (accumulated separately)\n  Dev->>CC: try the change (regenerated skills/agents are now live)\n  CC-->>Dev: run a skill; dogfood the edit\n  Dev->>Graph: /document → docs-graph.py derive\n  Graph->>Install: write docs/docs-index.js from frontmatter\n  Graph->>Explorer: index loaded; hierarchy · graph · mind map · health render\n  Dev->>Pack: commit pack/ + .claude/ + docs/ together (lockstep)"
        },
        {
          "kind": "flowchart",
          "title": "Layered view (source → consumer)",
          "mermaid": "flowchart TB\n  subgraph L4[\"Consumer layer\"]\n    direction LR\n    cc[Claude Code / Copilot]:::c\n    ex[Docs Explorer + web explainer]:::c\n    z[dist/ zip for other repos]:::c\n  end\n  subgraph L3[\"Install layer (generated, committed)\"]\n    direction LR\n    claude[.claude/ knowledge·skills·agents]:::i\n    docs[docs/ pack-docs·scripts·templates·index]:::i\n  end\n  subgraph L2[\"Build layer\"]\n    direction LR\n    sync[sync-pack.ps1]:::b\n    pkg[package-pack.ps1]:::b\n  end\n  subgraph L1[\"Source layer (single source of truth)\"]\n    pack[pack/ knowledge·commands·templates·adapters·scripts]:::s\n  end\n  L1 --> L2 --> L3 --> L4\n  classDef s fill:#1d2b4d,stroke:#5a7cff,color:#dde6ff\n  classDef b fill:#13324a,stroke:#5ad1c7,color:#dffaf6\n  classDef i fill:#2a2440,stroke:#a98bff,color:#efeaff\n  classDef c fill:#163024,stroke:#56d364,color:#dcffe4"
        },
        {
          "kind": "class",
          "title": "Domain model (class) — the UI Archetype Grammar",
          "mermaid": "classDiagram\n  class Signature {\n    +Name name\n    +FacetList facets\n    +StyleHints? hints\n    +validate() conflicts\n    +roundTrip() bool  %% G10: identify AND generate\n  }\n  class Facet {\n    <<abstract>>\n    +String key\n  }\n  class SingleValuedFacet {\n    +Value value  %% Type, Arch, Layout, Density, Pacing, ...\n  }\n  class MultiValuedFacet {\n    +Value[] values  %% Nav, Input, Feedback, Motion, A11y (joined with +)\n  }\n  class StyleHints {\n    +String[] hints  %% bounded NL decoration, applied last\n  }\n  class Archetype {\n    +String id          %% A1..F2\n    +String name\n    +Exemplar[] exemplars\n    +Signature canonical\n    +String codegenDescriptor\n  }\n  Signature \"1\" o-- \"4..*\" Facet : composes\n  Facet <|-- SingleValuedFacet\n  Facet <|-- MultiValuedFacet\n  Signature \"0..1\" *-- \"1\" StyleHints : decorated by\n  Archetype \"1\" *-- \"1\" Signature : canonical\n  Archetype \"1\" o-- \"1..*\" Exemplar\n  note for Signature \"G4: MUST carry Type, Arch, Layout, Pacing.\\nG1: always composed with a concrete U1–U20 / S1–S18 spec.\""
        }
      ],
      "sourceSha256": "1df89886606bad84cca852988c36324028b8bebba95a48ba1ed26ce9b2fb50c3"
    },
    {
      "id": "design-aiforward-cli",
      "path": "docs/design/aiforward-cli.md",
      "title": "Design — aiforward CLI (suggestion 1)",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-12-11",
      "reviewSuggested": [],
      "summary": "A single stdlib-only Python developer CLI (tools/aiforward.py) that is a thin Façade dispatcher over the pack's existing scripts (sync, verify, check, new, doctor, graph, scrub) — one memorable entry point with --help, no new runtime dependency.",
      "tags": [
        "cli",
        "tooling",
        "dx"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "implements"
        }
      ],
      "diagrams": [],
      "sourceSha256": "4c52b72da4a80dc78ea30213c6eefc577fb8af212764b95e8d85b603b7354fde"
    },
    {
      "id": "design-docs-explorer-grounding-spatial-navigation",
      "path": "docs/design/docs-explorer-grounding-and-spatial-navigation.md",
      "title": "Docs Explorer — Grounding and Spatial Navigation Design",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2027-01-07",
      "reviewSuggested": [],
      "summary": "Detailed design for making the repository knowledge graph a deterministic grounding interface for coding agents and a clearer human exploration surface. It separates selected-node neighborhood context from mind-map rooting, adds provenance-bounded context packets, adds a derived directory of standalone HTML knowledge surfaces, and makes deterministic Spatial 3D a first-class progressive projection over an accessible 2D baseline.",
      "tags": [
        "docs-explorer",
        "knowledge-graph",
        "grounding",
        "project-memory",
        "accessibility",
        "3d"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "refines"
        },
        {
          "to": "project-memory",
          "rel": "refines"
        },
        {
          "to": "docs-index",
          "rel": "documents"
        },
        {
          "to": "design-language-docs-explorer",
          "rel": "depends-on"
        },
        {
          "to": "proof-docs-explorer-redesign",
          "rel": "tested-by"
        }
      ],
      "diagrams": [],
      "sourceSha256": "38a09a51a44004a2939929a9c81f95d19b2c074492484fa31a1f097578b76f1f"
    },
    {
      "id": "design-pack-doctor",
      "path": "docs/design/pack-doctor.md",
      "title": "Design — installed-repo doctor (suggestion 2)",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-12-11",
      "reviewSuggested": [],
      "summary": "A deployable, stdlib-only pack-doctor.py that reports the INSTALL health of a target repo (revision, both tool surfaces, managed-block integrity, graph health) as PASS/WARN/FAIL with fixes and a nonzero exit — distinct from the source-only consistency gate.",
      "tags": [
        "doctor",
        "health",
        "install",
        "tooling"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "implements"
        }
      ],
      "diagrams": [],
      "sourceSha256": "25cacb5d72b8027a8bfd8e4c23cf4dae7f6dd939806c5f13eaa063e4526b1762"
    },
    {
      "id": "design-project-memory",
      "path": "docs/design/project-memory.md",
      "title": "Design — project memory + Obsidian decision (suggestion 3)",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-12-11",
      "reviewSuggested": [],
      "summary": "A project-memory convention — an append-only, graph-linked docs/project-memory.md ledger that skills read at grounding and append to at convergence — plus the explicit decision to treat Obsidian as an OPTIONAL lens over the existing vault, never a dependency.",
      "tags": [
        "memory",
        "obsidian",
        "knowledge-graph",
        "continuity"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "implements"
        }
      ],
      "diagrams": [],
      "sourceSha256": "46cf23771d42d00bdfe2796ab0b3daaba35e0350dda1ae49598cc92951c5de92"
    },
    {
      "id": "design-rai-and-scrub",
      "path": "docs/design/rai-and-scrub.md",
      "title": "Design — RAI policy + PII/secret scrub (suggestion 4)",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-12-11",
      "reviewSuggested": [],
      "summary": "A committed Responsible-AI policy knowledge doc mapping Microsoft RAI principles + NIST AI RMF functions to the pack's EXISTING personas/templates, plus a stdlib regex scrub.py first-pass that redacts obvious PII/secrets from Markdown — explicitly labeled not-a-substitute for gitleaks/Presidio.",
      "tags": [
        "responsible-ai",
        "privacy",
        "pii",
        "secrets",
        "governance"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "implements"
        }
      ],
      "diagrams": [],
      "sourceSha256": "56b1c7e87d28bcfdac3906cb30b403c4a586fe6901d74c5b86960805a5bdc698"
    },
    {
      "id": "design-language-docs-explorer",
      "path": "docs/DESIGN.md",
      "title": "Docs Explorer — Design Language",
      "type": "design-language",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2027-01-07",
      "reviewSuggested": [],
      "summary": "Token and interaction language for the Docs Explorer knowledge portal: browse, graph, mind-map, deterministic Spatial 3D, and derived HTML knowledge surfaces. It defines a high-legibility dark/light system, selected-node focus behavior, complete visualization states, and the performance/accessibility floors that implementation must satisfy.",
      "tags": [
        "design-language",
        "docs-explorer",
        "ui",
        "tokens",
        "accessibility"
      ],
      "links": [
        {
          "to": "design-docs-explorer-grounding-spatial-navigation",
          "rel": "refines"
        },
        {
          "to": "docs-index",
          "rel": "documents"
        }
      ],
      "diagrams": [],
      "sourceSha256": "5894c47b0acd2f11f55f2a0c222143c1a1a7dda6b3418c7052756fb524a6de8b"
    },
    {
      "id": "audit-log",
      "path": "docs/audit/audit-log.md",
      "title": "Audit & Change Log",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "",
      "reviewBy": "2026-09-25",
      "reviewSuggested": [],
      "summary": "The project's durable, committed activity & decision history — an append-only audit log of every meaningful prompt/skill/script and a curated change log of design decisions — the committed counterpart to a session's ephemeral store, so work compounds across sessions. This node represents the bundle in the knowledge graph.",
      "tags": [
        "audit",
        "history",
        "change-log",
        "project-memory",
        "knowledge-graph"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "relates-to"
        },
        {
          "to": "docs-index",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "f7da2d40e289e43fb0beb300b45e28b63305ffc1534b7dfe79c114f0006e5cc9"
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
      "diagrams": [],
      "sourceSha256": "e17d4f5accd582cb4b2baf375a949ed12fc8d7ff39f70f833dbaee5b048366fa"
    },
    {
      "id": "project-memory",
      "path": "docs/project-memory.md",
      "title": "Project Memory",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-20",
      "reviewSuggested": [],
      "summary": "The durable, append-only record of what this project has learned and decided — read at every skill's grounding and appended to at every skill's convergence. Frontmatter/graph is authority; this ledger is narrative.",
      "tags": [
        "memory",
        "continuity"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "relates-to"
        },
        {
          "to": "design-project-memory",
          "rel": "implements"
        }
      ],
      "diagrams": [],
      "sourceSha256": "ef39aa2634caaccd815ed64e487a2987ff5ef19fd5b3851362cda4f764114c40"
    },
    {
      "id": "kb-pack-evolution-glossary",
      "path": "docs/knowledge/pack-evolution/glossary.md",
      "title": "Pack Evolution — Glossary",
      "type": "glossary",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-12",
      "reviewSuggested": [],
      "summary": "The ubiquitous language for the pack-evolution work: pack-lifecycle skill, source consistency vs install health, doctor, project memory / ledger, Obsidian vault, RAI policy, scrub, stdlib-only, zero-drift.",
      "tags": [
        "glossary",
        "cli",
        "doctor",
        "memory",
        "responsible-ai"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "a0c670c403ddf6e56e037ac25043bd7a6c2d16bb5f138a6794e412e896814925"
    },
    {
      "id": "kb-pack-evolution",
      "path": "docs/knowledge/pack-evolution/index.md",
      "title": "Pack Evolution — CLI, Doctor, Project Memory, RAI (domain knowledge)",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-12",
      "reviewSuggested": [],
      "summary": "Sourced evidence base for four capabilities AI-Forward is considering adopting from agent-orchestration products (notably bradygaster/squad): a unified CLI, an installed-repo doctor, persistent project memory (and whether to introduce Obsidian), and a committed Responsible-AI policy plus a PII/secret scrub. Every load-bearing claim is confidence-labeled.",
      "tags": [
        "cli",
        "doctor",
        "memory",
        "obsidian",
        "responsible-ai",
        "pii",
        "squad"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "d4973f47e05c295dbc4ceefd4de2adc9f4abcde61954bcf830c636a01279c2f1"
    },
    {
      "id": "kb-pack-evolution-comparables",
      "path": "docs/knowledge/pack-evolution/comparables.md",
      "title": "Pack Evolution — Comparables",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-12",
      "reviewSuggested": [],
      "summary": "Squad-vs-AI-Forward capability comparison for the four suggestions, what to borrow (intent) and what to reject (runtime form), plus adjacent doctor/changesets/Dataview patterns worth borrowing.",
      "tags": [
        "squad",
        "comparables",
        "cli",
        "doctor",
        "memory",
        "responsible-ai"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "711863d64f4e49cfa268e819be41d1ec5018b8931d40ea1794049c735ddf18e1"
    },
    {
      "id": "kb-pack-evolution-open-questions",
      "path": "docs/knowledge/pack-evolution/open-questions.md",
      "title": "Pack Evolution — Open Questions & Failure Modes",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-12",
      "reviewSuggested": [],
      "summary": "Flagged unknowns (regex-scrub recall, ledger freshness, CLI cross-shell), the domain's failure modes (runtime creep, drift, RAI theater, Obsidian lock-in, doctor false confidence), and disconfirming views sought.",
      "tags": [
        "risks",
        "pii",
        "memory",
        "responsible-ai",
        "disconfirmation"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "c58e35c06ab17a2f55ee41b18653a1bd35fa9519b79269b9007c5038d6d5eb67"
    },
    {
      "id": "kb-pack-evolution-references",
      "path": "docs/knowledge/pack-evolution/references.md",
      "title": "Pack Evolution — References",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-12",
      "reviewSuggested": [],
      "summary": "Standards (MS RAI Standard, NIST AI RMF, EU AI Act/GDPR), the pack's own contracts the capabilities conform to (knowledge-visualization V1–V18, INSTALL deployment map, engineering-governance), and tooling references.",
      "tags": [
        "responsible-ai",
        "nist",
        "standards",
        "tooling"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "2256a95932e51eead9e8d49c73f0e2480919eccbfed065cab14e64125a0df60d"
    },
    {
      "id": "kb-pack-evolution-sota",
      "path": "docs/knowledge/pack-evolution/state-of-the-art.md",
      "title": "Pack Evolution — State of the Art",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-12",
      "reviewSuggested": [],
      "summary": "Current best practice for the four capabilities: CLI distribution (repo-local stdlib Python wins), the doctor pattern, persistent project/agent memory, Obsidian as an optional lens, and RAI policy + PII scrubbing.",
      "tags": [
        "cli",
        "doctor",
        "memory",
        "obsidian",
        "responsible-ai"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "7963340d55793856d967c6b7559bd663abf5eadf7e98c4a9e84ce2b97f70f62f"
    },
    {
      "id": "kb-pack-evolution-sources",
      "path": "docs/knowledge/pack-evolution/sources.md",
      "title": "Pack Evolution — Sources",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-09-12",
      "reviewSuggested": [],
      "summary": "The full source list with access dates for the pack-evolution knowledge base — Squad, the pack's own files, the MS RAI and NIST RMF standards, the scrub tooling, and the web research rows.",
      "tags": [
        "sources",
        "citations"
      ],
      "links": [
        {
          "to": "kb-pack-evolution",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "21bfb1d3ca4bd03f9dcae01e0887e3c46dc60fc650d4a17337f353a042fc85da"
    },
    {
      "id": "privacy-review",
      "path": "docs/security/privacy-review.md",
      "title": "Privacy Review",
      "type": "privacy-review",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2027-01-07",
      "reviewSuggested": [],
      "summary": "Repo-level privacy posture for the pack-evolution tooling: the CLI and doctor touch no personal data; project memory may incidentally record handles/names (no special-category data, mitigated by the scrub); the scrub is itself a privacy control; Docs Explorer navigation state remains local and introduces no analytics or new personal-data flow.",
      "tags": [
        "privacy",
        "linddun",
        "data-governance"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "documents"
        },
        {
          "to": "design-aiforward-cli",
          "rel": "documents"
        },
        {
          "to": "design-pack-doctor",
          "rel": "documents"
        },
        {
          "to": "design-project-memory",
          "rel": "documents"
        },
        {
          "to": "design-rai-and-scrub",
          "rel": "documents"
        },
        {
          "to": "design-docs-explorer-grounding-spatial-navigation",
          "rel": "documents"
        }
      ],
      "diagrams": [],
      "sourceSha256": "7d21b9e93708f5a5a8a2aff8fca3586e5b0a52354fa7b5366520c47dfea2113f"
    },
    {
      "id": "proof-docs-explorer-redesign",
      "path": "docs/proof/docs-explorer-redesign.md",
      "title": "Docs Explorer Redesign - Proof Pack",
      "type": "proof-pack",
      "status": "accepted",
      "owner": "@maintainers",
      "phase": "implementation",
      "reviewBy": "2027-01-07",
      "reviewSuggested": [],
      "summary": "Accepted implementation evidence for the deterministic, local-first Docs Explorer, native Spatial 3D knowledge portal, and bounded grounding packet implementation. The P0/P1 contract is covered by Python, Node, and three-engine browser suites; phase-attributed benchmark evidence separates graph work from process/host overhead. Revision 17 remains intentionally unreleased pending pinned-reference performance proof or a human-approved deviation.",
      "tags": [
        "docs-explorer",
        "grounding",
        "accessibility",
        "performance",
        "verification"
      ],
      "links": [
        {
          "to": "design-docs-explorer-grounding-spatial-navigation",
          "rel": "relates-to"
        },
        {
          "to": "adr-0001-grounding-source-corpus-registry",
          "rel": "depends-on"
        },
        {
          "to": "design-language-docs-explorer",
          "rel": "depends-on"
        },
        {
          "to": "threat-model",
          "rel": "relates-to"
        },
        {
          "to": "privacy-review",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "8596cd2175507a7b8da9f922cf7db6bee84be7eec6622235bc51964b5f370675"
    },
    {
      "id": "threat-model",
      "path": "docs/security/threat-model.md",
      "title": "Threat Model",
      "type": "threat-model",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2027-01-07",
      "reviewSuggested": [],
      "summary": "Repo-level security posture for the pack-evolution tooling. The scrub handles potentially sensitive file content, while the Docs Explorer crosses committed-Markdown, filesystem, browser-rendering, and optional dependency boundaries; the remaining tools are local and read-mostly.",
      "tags": [
        "security",
        "threat-model"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "documents"
        },
        {
          "to": "design-aiforward-cli",
          "rel": "documents"
        },
        {
          "to": "design-pack-doctor",
          "rel": "documents"
        },
        {
          "to": "design-project-memory",
          "rel": "documents"
        },
        {
          "to": "design-rai-and-scrub",
          "rel": "documents"
        },
        {
          "to": "design-docs-explorer-grounding-spatial-navigation",
          "rel": "documents"
        }
      ],
      "diagrams": [],
      "sourceSha256": "a6ec4562f4bb1ef81abcb7645c817dae374d64ebff211fcef95165cbe8f09e26"
    }
  ],
  "surfaces": [
    {
      "id": "surface-audit-index",
      "path": "docs/audit/index.html",
      "title": "AI-Forward — Audit & Change Log",
      "kind": "audit",
      "description": "Browse the committed audit and change timeline.",
      "artifactId": "audit-log"
    },
    {
      "id": "surface-site-index",
      "path": "docs/_site/index.html",
      "title": "AI-Forward Documentation",
      "kind": "documentation",
      "description": "Open the generated documentation bundle."
    },
    {
      "id": "surface-design-docs-explorer-design-language-preview",
      "path": "docs/design/docs-explorer-design-language-preview.html",
      "title": "Docs Explorer - Design Language Preview",
      "kind": "design-preview",
      "description": "Inspect a rendered design or design-language preview."
    }
  ],
  "graphSha256": "a4a1010b23bb1f4e605cb6e1f6e20d7c41faaf27078d6266c0b91f880353f23e"
};
