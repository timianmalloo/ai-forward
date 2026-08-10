// Derived from artifact frontmatter by scripts/docs-graph.py — DO NOT hand-edit (frontmatter wins; see knowledge-visualization.md V2/V18).
window.DOCS_INDEX = {
  "schemaVersion": "docs-index/v2",
  "project": "AI-Forward",
  "generated": "2026-08-10T13:44:09Z",
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
          "mermaid": "flowchart TB\n  subgraph SRC[\"pack/ — canonical source (edit here)\"]\n    K[\"knowledge/*.md<br/>(reasoning spine + roster + foundation)\"]\n    C[\"commands/&lt;name&gt;/SKILL.md<br/>(the 17 skills)\"]\n    T[\"templates/*<br/>(artifacts each skill emits)\"]\n    A[\"adapters/<br/>(Claude Code + Copilot agents, INSTALL.md)\"]\n    SC[\"scripts/ (9) · evals/ · ci/ · examples/\"]\n    PD[\"README · OVERVIEW · research-synthesis\"]\n  end\n\n  subgraph TOOLS[\"tools/ — build\"]\n    SYNC[\"sync-pack.ps1\"]\n    PKG[\"package-pack.ps1\"]\n  end\n\n  subgraph INSTALL[\".claude/ + docs/ — generated install (do not hand-edit)\"]\n    CK[\".claude/knowledge/*.md\"]\n    CS[\".claude/skills/*\"]\n    CA[\".claude/agents/*.md\"]\n    DP[\"docs/ai-forward-pack/<br/>templates + scripts + pack docs\"]\n    EXP[\"docs/index.html<br/>(Docs Explorer)\"]\n    IDX[\"docs/docs-index.js<br/>(accumulated graph index)\"]\n    ARCH[\"docs/architecture.md · index.md · _meta.json<br/>(this bundle)\"]\n  end\n\n  subgraph CONSUMERS[\"consumers\"]\n    CC[\"Claude Code / Copilot<br/>(read .claude/)\"]\n    WEBE[\"web/ai-forward-pack-explainer.html<br/>(interactive explainer)\"]\n    ZIP[\"dist/ai-forward-pack.zip\"]\n  end\n\n  K --> SYNC\n  C --> SYNC\n  T --> SYNC\n  A --> SYNC\n  SYNC --> CK & CS & CA & DP & EXP\n  C -. \"skills reference\" .-> CK\n  CA -. \"agents reference\" .-> CK\n  DP --> GRAPH[\"docs-graph.py<br/>(in docs/ai-forward-pack/scripts)\"]\n  GRAPH --> IDX\n  ARCH --> GRAPH\n  IDX --> EXP\n  CK --> CC\n  CS --> CC\n  CA --> CC\n  SRC --> PKG --> ZIP\n  CK -. \"derived content\" .-> WEBE"
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
      "sourceSha256": "16a98e62ffcbf07734f0f5821870e14beb670118ed185c7c67d0fe724bc209fc"
    },
    {
      "id": "note-20260712-model-orchestration-policy",
      "path": "docs/notes/note-20260712-model-orchestration-policy.md",
      "title": "Model-orchestration routing policy for AI-Forward skills",
      "type": "decision-note",
      "status": "superseded",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2027-01-08",
      "reviewSuggested": [],
      "summary": "Historical policy decision for applying LOA tier allocation to skill execution. Superseded after forensic review found the proposed control plane unwired, internally contradictory, unproven, and missing data-governance boundaries.",
      "tags": [
        "decision-note",
        "model-orchestration",
        "loa",
        "skills",
        "orchestrator"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "ba53a24fa990b5a6e5b9f1ba1f6ab3057bf8d1ed31606d97b97770b9fcbe45dc"
    },
    {
      "id": "note-20260712-revert-model-orchestration",
      "path": "docs/notes/note-20260712-revert-model-orchestration.md",
      "title": "Revert the model-orchestration capability",
      "type": "decision-note",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2027-01-08",
      "reviewSuggested": [],
      "summary": "Removes the model-orchestration standard, static router, tests, and active wiring after forensic review found the capability unwired and unsafe to claim as automatic enforcement; retains the review and decision history.",
      "tags": [
        "decision-note",
        "model-orchestration",
        "revert"
      ],
      "links": [
        {
          "to": "note-20260712-model-orchestration-policy",
          "rel": "supersedes"
        },
        {
          "to": "forensic-review",
          "rel": "depends-on"
        },
        {
          "to": "architecture",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "a5268718eefb7d1ebe33b490d527fc108fd372a30ee5180d5fa01178c7a43485"
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
      "sourceSha256": "7eec2f1180943293694b96465bb5c026b4651bd42b8d62a5a7fca60c9c7f001a"
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
      "id": "defect-classes",
      "path": "docs/lessons/defect-classes.md",
      "title": "Defect-class register",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "This repository's register of defect classes — the recurring shapes of things that go wrong here, what each one survives, and the control that now fails when the shape recurs. Read at grounding; appended to on every defect, correction or falsified assumption.",
      "tags": [
        "lessons",
        "defect-classes",
        "continuous-improvement"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "relates-to"
        },
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "b1f80b6edc77dcc68433473ab82e1668f44234881817e4bc3eb0cff1103f9c95"
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
      "sourceSha256": "a1e2999d19839b86db84f42619db982b59bbd588ec53a38c7dc432c86dd3295e"
    },
    {
      "id": "forensic-review",
      "path": "docs/reviews/forensic-review.md",
      "title": "Forensic Review — AI-Forward repository (revision 30)",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-08",
      "reviewSuggested": [],
      "summary": "Adoption-readiness assessment at commit 2227632 (revision 30), scoped to inconsistencies and contradictions. Every self-declared gate is green and the repository is still not ready to hand to adopters. Two findings dominate: 183 documented commands invoke `python3`, which on a default Windows install is a broken Store alias, and the Copilot surface receives 11 of the 23 personas the deployment map promises — first raised twelve revisions ago, never closed.",
      "tags": [
        "forensic-review",
        "adoption-readiness",
        "consistency",
        "ci",
        "documentation",
        "portability"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "documents"
        },
        {
          "to": "forensic-review-backlog",
          "rel": "relates-to"
        },
        {
          "to": "forensic-review-20260802",
          "rel": "supersedes"
        }
      ],
      "diagrams": [],
      "sourceSha256": "b23c9cfb53a2a66559bd12c5cf186ea4f6bd4c7b45073eca8575c1634276c35b"
    },
    {
      "id": "forensic-review-20260712",
      "path": "docs/reviews/forensic-review-20260712-model-orchestration.md",
      "title": "Forensic Review — AI-Forward model orchestration",
      "type": "doc",
      "status": "superseded",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-10-10",
      "reviewSuggested": [],
      "summary": "Evidence-based assessment of AI-Forward commit 5d7b952 focused on model orchestration. The user accepted the readiness BLOCK and reverted the capability; the report is retained as historical evidence.",
      "tags": [
        "forensic-review",
        "model-orchestration"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "documents"
        },
        {
          "to": "forensic-review-backlog-20260712",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "9e2abc127f9b4c38c7dc6ed4a7f955ef7ac3a2ef1640c4c86467ad4bb91a7832"
    },
    {
      "id": "forensic-review-20260802",
      "path": "docs/reviews/forensic-review-20260802-rev18.md",
      "title": "Forensic Review — AI-Forward repository (revision 18, archived)",
      "type": "doc",
      "status": "superseded",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-02",
      "reviewSuggested": [],
      "summary": "Comprehensive evidence-based assessment of the AI-Forward repository at commit 53e3afe (revision 18). Ten findings, none P0. The two load-bearing results are FR-011 — the repository's foundational invariant (pack/ is source, .claude/ and .github/ are generated) has no CI gate, proven by drifting a worktree — and FR-020, Copilot receiving 11 of the 23 personas the deployment map promises.",
      "tags": [
        "forensic-review",
        "ci",
        "consistency",
        "supply-chain",
        "documentation"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "documents"
        },
        {
          "to": "forensic-review-20260802-backlog",
          "rel": "relates-to"
        },
        {
          "to": "forensic-review-20260712",
          "rel": "supersedes"
        }
      ],
      "diagrams": [],
      "sourceSha256": "17cc455044845c62f23f5013a78809fe422ead390bc3375d23561d1eb51502cd"
    },
    {
      "id": "forensic-review-20260802-backlog",
      "path": "docs/backlog/forensic-review-20260802-rev18.md",
      "title": "Forensic Review Backlog — AI-Forward repository (revision 18)",
      "type": "doc",
      "status": "proposed",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-02",
      "reviewSuggested": [],
      "summary": "The proposed backlog from the revision-18 forensic review of AI-Forward at commit 53e3afe — ten findings (FR-011..FR-020) ordered into four phases, plus FR-008 carried forward and FR-010 closed into FR-020. All items are status `proposed` and await human triage; none has been implemented.",
      "tags": [
        "backlog",
        "forensic-review",
        "ci",
        "consistency",
        "supply-chain"
      ],
      "links": [
        {
          "to": "forensic-review-20260802",
          "rel": "refines"
        },
        {
          "to": "architecture",
          "rel": "depends-on"
        },
        {
          "to": "forensic-review-backlog-20260712",
          "rel": "supersedes"
        }
      ],
      "diagrams": [],
      "sourceSha256": "e9dff6862d5cce87e6dfb4a40923f941a0f2a5a20fd569c8b7a592a663992fe1"
    },
    {
      "id": "forensic-review-backlog",
      "path": "docs/backlog/forensic-review.md",
      "title": "Forensic Review Backlog — AI-Forward repository (revision 30)",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-08",
      "reviewSuggested": [],
      "summary": "Twelve proposed items (FR-031..FR-042) from the revision-30 review, ordered into four independently deliverable phases. Seven carry forward unchanged from the revision-18 backlog. All items are status `proposed` and await human triage; nothing has been remediated.",
      "tags": [
        "backlog",
        "forensic-review",
        "adoption-readiness",
        "triage"
      ],
      "links": [
        {
          "to": "forensic-review",
          "rel": "refines"
        },
        {
          "to": "forensic-review-20260802-backlog",
          "rel": "supersedes"
        }
      ],
      "diagrams": [],
      "sourceSha256": "6f9f6c3cf3732d5ee307941aa847649c9ce04fe265cf668ca7d59afc88566d39"
    },
    {
      "id": "forensic-review-backlog-20260712",
      "path": "docs/backlog/forensic-review-20260712-model-orchestration.md",
      "title": "Forensic Review Backlog — Model orchestration",
      "type": "doc",
      "status": "proposed",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-10-10",
      "reviewSuggested": [],
      "summary": "Historical remediation backlog from the model-orchestration forensic review. The capability was reverted; orchestration-specific items are closed by removal. FR-008 and residual FR-010 remain independent repository findings.",
      "tags": [
        "backlog",
        "model-orchestration"
      ],
      "links": [
        {
          "to": "forensic-review-20260712",
          "rel": "refines"
        },
        {
          "to": "architecture",
          "rel": "depends-on"
        }
      ],
      "diagrams": [],
      "sourceSha256": "6c4e8d947e823f9469d0f76eabe6cf2059f14662712f1e983faf0319d4fd49aa"
    },
    {
      "id": "lens-code-doc-join",
      "path": "docs/lenses/code-doc-join.md",
      "title": "Lens - code/doc join",
      "type": "doc",
      "status": "accepted",
      "owner": "@maintainers",
      "phase": "",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Derived join between the documentation graph (intent) and the Graphify code graph (reality): documentation referencing code that does not exist, and the most connected code symbols no artifact governs. A prompt, never a gate.",
      "tags": [
        "lens",
        "graphify",
        "code-graph",
        "traceability"
      ],
      "links": [
        {
          "to": "lens-graph-structure",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "1f4ae92b1f268b6dc29d7f28bfd7a4d7ea53e7114e3bec4a06bc00bad88bb947"
    },
    {
      "id": "lens-graph-health",
      "path": "docs/lenses/graph-health.md",
      "title": "Lens - graph health",
      "type": "doc",
      "status": "accepted",
      "owner": "@maintainers",
      "phase": "",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "A read-time Dataview lens over the knowledge graph's health - stale artifacts, missing owners, missing freshness SLAs, and review-suggested flags. Derived, never authoritative.",
      "tags": [
        "lens",
        "obsidian",
        "dataview",
        "graph-health"
      ],
      "links": [
        {
          "to": "lens-graph-structure",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "fa610a3c05e3c4e58a6c6a0eb456ab484d2c85081d59c4a48b665035c8100a99"
    },
    {
      "id": "lens-graph-insight",
      "path": "docs/lenses/graph-insight.md",
      "title": "Lens - graph insight (computed)",
      "type": "doc",
      "status": "accepted",
      "owner": "@maintainers",
      "phase": "",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Computed structural analysis of the knowledge graph - hubs, bridges, components, orphans and structural gaps. Regenerate with obsidian-setup.py --analyze --write. Derived, never authoritative.",
      "tags": [
        "lens",
        "graph-analysis",
        "computed"
      ],
      "links": [
        {
          "to": "lens-graph-structure",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "5d89b28a6d4ba272e5b88ac53c9e08f9c03195ac57e76a51c2b23702f832597b"
    },
    {
      "id": "lens-graph-structure",
      "path": "docs/lenses/graph-structure.md",
      "title": "Lens - graph structure",
      "type": "doc",
      "status": "accepted",
      "owner": "@maintainers",
      "phase": "",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "A read-time lens over the shape of the knowledge graph - artifacts by type and status, and the traceability chains (spec to design to proof). Derived, never authoritative.",
      "tags": [
        "lens",
        "obsidian",
        "dataview",
        "structure"
      ],
      "links": [
        {
          "to": "lens-graph-health",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "5bf8471b858442580beb4f227c56ae44fb370b0ff6185b66ba14d4d0da90ae07"
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
      "id": "ui-capability-guide",
      "path": "docs/ui-guide.md",
      "title": "UI & UX Capability Guide",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-03",
      "reviewSuggested": [],
      "summary": "The how-to layer over this repository's seven UI standards: the layer stack and what each one decides, a job-to-path picker, the /ui-design loop, the command cheat sheet, an archetype picker, the veto table, the anti-pattern tells, and where artifacts land. The browsable surface is ui-guide.html; this node is its place in the graph.",
      "tags": [
        "ui",
        "ux",
        "guide",
        "design",
        "accessibility",
        "docs-explorer"
      ],
      "links": [
        {
          "to": "design-language-docs-explorer",
          "rel": "relates-to"
        },
        {
          "to": "docs-index",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "38c9f5f6595c4765e66b42a121ef6c7fce9708cb988bcfa21388f8e15829db98"
    },
    {
      "id": "ui-review-pack-explainer",
      "path": "docs/reviews/ui-pack-explainer.md",
      "title": "UI review — AI-Forward Pack Explainer",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-05",
      "reviewSuggested": [],
      "summary": "Review of web/ai-forward-pack-explainer.html, triggered by the question \"can Higgsfield beautify this?\". Measurement says no: the public surface renders blank without three un-hashed CDN scripts, has no focus styling, ARIA or reduced-motion, and carries 166 hex colours against 20 tokens. Imagery is not the lever. Inlining the runtime is.",
      "tags": [
        "ui-review",
        "ux",
        "accessibility",
        "supply-chain",
        "explainer"
      ],
      "links": [
        {
          "to": "ui-capability-guide",
          "rel": "relates-to"
        },
        {
          "to": "docs-index",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "0be650029252586167fcea2b6fc15e2a4363c628d410e708a1533f0dbaec9dbe"
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
      "id": "kb-ddm-comparables",
      "path": "docs/knowledge/domain-and-data-modelling/comparables.md",
      "title": "Domain & Data Modelling — Comparables",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "How other approaches frame and solve \"a durable model that keeps history and an audit trail without a shadow schema\" — CQRS, event sourcing, Data Vault, anchor modelling, temporal tables, and the two in-repo precedents (Meridian ADR-0022, TheTerrace hub-and-satellite).",
      "tags": [
        "comparables",
        "cqrs",
        "event-sourcing",
        "data-vault",
        "anchor-modeling"
      ],
      "links": [
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "63d69a0719bfda4a7db15a6286e28d84f1e1840294b47b3760d23c81b11f6647"
    },
    {
      "id": "kb-ddm-data",
      "path": "docs/knowledge/domain-and-data-modelling/data-and-constants.md",
      "title": "Domain & Data Modelling — Data, Shapes & Constants",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "The concrete, reusable shapes: the grain statement form, the additivity classes, the Type-2 dimension column set, the append-only fact column set, the aggregate-design checklist, and the expand-migrate-contract sequence.",
      "tags": [
        "grain",
        "scd",
        "additivity",
        "invariants",
        "shapes"
      ],
      "links": [
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "f0b9a1af0c6c7900727e1817eb6a23470500ea782bbb44049559488b9ab62001"
    },
    {
      "id": "kb-ddm-glossary",
      "path": "docs/knowledge/domain-and-data-modelling/glossary.md",
      "title": "Domain & Data Modelling — Glossary",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "The ubiquitous language of domain and data modelling, each term defined with what it is NOT — the near-miss disambiguation that stops two people using one word for two things.",
      "tags": [
        "glossary",
        "ubiquitous-language"
      ],
      "links": [
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "54586633a22a35c2aa7fa6d85c131c99cc8c7516e67fa908f0d2744e9ba97415"
    },
    {
      "id": "kb-ddm-open-questions",
      "path": "docs/knowledge/domain-and-data-modelling/open-questions.md",
      "title": "Domain & Data Modelling — Open Questions & Failure Modes",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "What the research could not settle (three Flagged claims), the disconfirming case against this standard's central stance, and the known failure modes of domain and data modelling observed in two production repos.",
      "tags": [
        "open-questions",
        "risks",
        "failure-modes"
      ],
      "links": [
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "2bed5032868f981f5633e654e7d92cf7f2b705a1e31117ea6c0e75a25ec08dc3"
    },
    {
      "id": "kb-ddm-references",
      "path": "docs/knowledge/domain-and-data-modelling/references.md",
      "title": "Domain & Data Modelling — References",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "The seminal works, standards and vendor documentation this knowledge base rests on — Evans and Vernon for DDD, Kimball for dimensional modelling, Inmon for the ODS, SQL:2011 for temporal tables, and the current lakehouse layering documentation.",
      "tags": [
        "references",
        "evans",
        "vernon",
        "kimball",
        "inmon",
        "sql2011"
      ],
      "links": [
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "3b69e6287688f12796b780151d06033cb7c9243dad99342f657dc79516bdcd54"
    },
    {
      "id": "kb-ddm-sota",
      "path": "docs/knowledge/domain-and-data-modelling/state-of-the-art.md",
      "title": "Domain & Data Modelling — State of the Art",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "Current best practice across the four literatures this standard crosses: tactical DDD (aggregate design rules), conceptual/logical/physical modelling, Kimball dimensional modelling (grain, facts, SCD), and modern history mechanisms (SQL:2011 temporal tables, event sourcing, medallion/lakehouse layering).",
      "tags": [
        "ddd",
        "kimball",
        "scd",
        "temporal",
        "medallion",
        "event-sourcing"
      ],
      "links": [
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "c84b416adefff05967393cf6dd782980d1f997ce05bd09f8e34eabb3b9d84824"
    },
    {
      "id": "kb-ddm-sources",
      "path": "docs/knowledge/domain-and-data-modelling/sources.md",
      "title": "Domain & Data Modelling — Sources",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "Full source list with access dates and the confidence each source carries, ordered by the source-of-truth hierarchy: primary works and standards, then vendor documentation, then practitioner synthesis, then in-repo evidence.",
      "tags": [
        "sources",
        "provenance"
      ],
      "links": [
        {
          "to": "kb-domain-and-data-modelling",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "bf1de4e4c569cd063edd04f24263b8d6a2f6b8f41897799ea8686201cdb25fe1"
    },
    {
      "id": "kb-domain-and-data-modelling",
      "path": "docs/knowledge/domain-and-data-modelling/index.md",
      "title": "Domain & Data Modelling — DDD, conceptual models, ODS, star schemas (domain knowledge)",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "data-model-primacy",
      "reviewBy": "2026-10-31",
      "reviewSuggested": [],
      "summary": "Sourced evidence base for the pack's data-model-primacy directive: Domain-Driven Design (bounded contexts, aggregates, entities vs value objects), the conceptual/logical/physical model levels, the Operational Data Store, and Kimball dimensional modelling (grain, facts, Type-2 dimensions, snowflaking). Establishes why \"core entities as dimensions, change-over-time as facts\" gives history and audit without a shadow schema — and where that stance costs.",
      "tags": [
        "ddd",
        "aggregate-root",
        "conceptual-model",
        "ods",
        "star-schema",
        "dimension",
        "fact",
        "scd",
        "grain",
        "temporal"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "relates-to"
        },
        {
          "to": "kb-pack-evolution",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "4e7b5d667bf07b6f22c0c714ddec9241d638c98cd9dc0ec91c291a8f991a7b84"
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
      "summary": "Repo-level privacy posture for the pack-evolution tooling: the CLI and doctor touch no personal data; project memory may incidentally record handles/names (no special-category data, mitigated by the scrub); the scrub is itself a privacy control; Docs Explorer navigation state remains local. The reviewed model-orchestration experiment was reverted before an executable provider-routing boundary was added.",
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
          "to": "forensic-review",
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
      "sourceSha256": "1109de89ee851b3fea33548d8c292b525a0c7e6e58e431d5ed1bee65ccb8ab9f"
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
      "title": "ai-forward — Audit & Change Log",
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
      "id": "surface-ui-guide",
      "path": "docs/ui-guide.html",
      "title": "UI & UX Capability Guide",
      "kind": "guide",
      "description": "Read a how-to guide for a capability in this repository.",
      "artifactId": "ui-capability-guide"
    },
    {
      "id": "surface-design-docs-explorer-design-language-preview",
      "path": "docs/design/docs-explorer-design-language-preview.html",
      "title": "Docs Explorer - Design Language Preview",
      "kind": "design-preview",
      "description": "Inspect a rendered design or design-language preview."
    }
  ],
  "graphSha256": "30d2326abbf65d04933fd2a96af3c97dc103682dda7c18081a6bca594eaa2895"
};
