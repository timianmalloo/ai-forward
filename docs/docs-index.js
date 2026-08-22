// Derived from artifact frontmatter by scripts/docs-graph.py — DO NOT hand-edit (frontmatter wins; see knowledge-visualization.md V2/V18).
window.DOCS_INDEX = {
  "schemaVersion": "docs-index/v2",
  "project": "AI-Forward",
  "generated": "2026-08-22T20:59:48Z",
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
      "id": "adr-0002-fleet-learnings-store",
      "path": "docs/adr/0002-fleet-learnings-store.md",
      "title": "ADR-0002: Fleet learnings store in ai-forward; append-only facts + slug-keyed learnings; two federation paths",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "The fleet learnings store lives in the ai-forward repo; corpus/oracle records are append-only facts and a Learning is a slug-keyed dimension whose instances are append-only; general classes federate two ways — a push skill (/apply-learnings) and a pull path (/updatepack).",
      "tags": [
        "dreaming",
        "federation",
        "data-model",
        "fleet-store"
      ],
      "links": [
        {
          "to": "architecture-dreaming",
          "rel": "implements"
        },
        {
          "to": "spec-dreaming",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "16dbd4f89c26f9d69b17c99cec63caae55d37522991bdeb4475fa7a3f97b757c"
    },
    {
      "id": "adr-0003-promotion-oracle",
      "path": "docs/adr/0003-promotion-oracle.md",
      "title": "ADR-0003: The promotion oracle is captured successful mitigations (red→green test or human validation)",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "The oracle for 'the fix worked' is a captured MitigationRecord whose verification is either a red-observed→green test pair or an explicit human validation; a fix with neither is 'unverified' and is never mined as a successful mitigation.",
      "tags": [
        "dreaming",
        "promotion-oracle",
        "mitigations",
        "reflexion",
        "testing"
      ],
      "links": [
        {
          "to": "architecture-dreaming",
          "rel": "implements"
        },
        {
          "to": "spec-dreaming",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "0bbcd43185920644d77c385d47b6136d4499fe3d7270ddfcd967c100b3c397f3"
    },
    {
      "id": "adr-0004-instance-to-class-abstraction",
      "path": "docs/adr/0004-instance-to-class-abstraction.md",
      "title": "ADR-0004: Safe instance→class abstraction — deterministic strip, model name, generalisation guards, human gate",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Defines the safe instance→class abstraction: deterministically strip specifics + PII, model-name the shape, enforce five generalisation guards (evidence threshold, falsifiable control, boundary statement, retained provenance, no PII across the boundary), and never promote without the human gate.",
      "tags": [
        "dreaming",
        "abstraction",
        "federation",
        "privacy",
        "over-generalisation"
      ],
      "links": [
        {
          "to": "architecture-dreaming",
          "rel": "implements"
        },
        {
          "to": "spec-dreaming",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "3136333b0464909987a084d89b193ca1019a4b1ea7d4d8aae216fdb3fa170503"
    },
    {
      "id": "adr-0005-harness-runner-boundary",
      "path": "docs/adr/0005-harness-runner-boundary.md",
      "title": "ADR-0005: Ship a stdlib deterministic harness; the model call is an injected boundary owned by the runner; human-gate, no auto-merge",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "The pack ships a stdlib-only deterministic harness (dream.py) + prompts; the one model call per phase is an injected boundary the runner (claude-cowork / OpenClaw / Claude Dreams / a skill session) owns; every durable write and every cross-repo change passes a human gate — never an auto-merge.",
      "tags": [
        "dreaming",
        "pack-identity",
        "model-boundary",
        "human-gate",
        "runner"
      ],
      "links": [
        {
          "to": "architecture-dreaming",
          "rel": "implements"
        },
        {
          "to": "spec-dreaming",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "c19375435db43149cd158dfc6ae6e8abd87566abf49caf4db9455d7f5e19869a"
    },
    {
      "id": "adr-0006-dream-manifest",
      "path": "docs/adr/0006-dream-manifest.md",
      "title": "ADR-0006: The Dream Manifest — a learnings×repos targeting/record layer for federation, composed in a UI, consumed by apply-learnings --manifest, local-only by default",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Federation had a distribution mechanism (apply-learnings push -> per-repo plans) but no targeting/record layer: which learnings go to which repos, and what happened when they did. The Dream Manifest is that layer — a learnings×repos assignment matrix (learnings/manifests/<id>.json) composed in a self-contained HTML, consumed by `apply-learnings.py push --manifest`, which reconciles per assignment and writes status back. Manifests carry repo identifiers so they are LOCAL-ONLY by default (excluded from the published Pages bundle), consistent with the publish boundary.",
      "tags": [
        "dreaming",
        "federation",
        "manifest",
        "targeting",
        "publish-boundary"
      ],
      "links": [
        {
          "to": "architecture-dreaming",
          "rel": "implements"
        },
        {
          "to": "spec-dreaming",
          "rel": "implements"
        },
        {
          "to": "adr-0002-fleet-learnings-store",
          "rel": "depends-on"
        },
        {
          "to": "adr-0005-harness-runner-boundary",
          "rel": "depends-on"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "9f580ef9588475df5621e901b78dff2399aa057e52a760bc6147b3735dd1814b"
    },
    {
      "id": "adr-0007-coordination-substrate",
      "path": "docs/adr/0007-coordination-substrate.md",
      "title": "ADR-0007: A git-tracked append-only record folded on demand — no daemon, no database",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Coordination state lives in an append-only JSONL record, one file per session, git-tracked, and every piece of state is a fold over it. The daemon and the SQLite read model the draft proposed are both cut, because a measured full fold of a 10,000-event record costs 47 ms p95 against a 100 ms budget — and because a service introduces an availability dependency into an offline local tool.",
      "tags": [
        "coordination",
        "substrate",
        "event-sourcing",
        "fold",
        "latency",
        "spike"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "51bb0711fd975bd9af8b22acbcfa6cb265954651ab6e2ac478ae43f406d22b12"
    },
    {
      "id": "adr-0008-non-coordinating-allocation",
      "path": "docs/adr/0008-non-coordinating-allocation.md",
      "title": "ADR-0008: Identifiers come from a non-coordinating stdlib scheme — not uuid7, and not branch scanning",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Shared-register identifiers are issued from a stdlib-only, time-ordered, non-coordinating scheme — 48 bits of millisecond timestamp plus 80 bits from os.urandom, Crockford base32. uuid.uuid7 is rejected because it is absent on the installed 3.12 interpreter and present on the \"3.x\" CI runner; branch scanning is rejected because a working 22-branch scanner still collided within the hour.",
      "tags": [
        "coordination",
        "allocation",
        "ulid",
        "kg-b",
        "spike",
        "stdlib"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "e7ec73873881766858cdc652486d9873493bdd594262020b7b28758976e910dd"
    },
    {
      "id": "adr-0009-artifact-class-and-derived-merge",
      "path": "docs/adr/0009-artifact-class-and-derived-merge.md",
      "title": "ADR-0009: Artifact class decides the mechanism — derived artifacts are regenerated by a merge driver, never leased",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Every path pattern is classified authored / derived / register / hotspot, and the class decides the coordination mechanism entirely. Derived artifacts — which are the six busiest files in the measured repository — are resolved by a .gitattributes merge driver that regenerates them, proven in a spike to resolve cleanly while an authored file on the same merge still conflicts normally.",
      "tags": [
        "coordination",
        "artifact-class",
        "merge-driver",
        "gitattributes",
        "ci-b",
        "spike"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "9d588654dd25b8ab3fe7e16e37011248c77be3e9ff18bf9fb80078093519e01f"
    },
    {
      "id": "adr-0010-enforcement-topology",
      "path": "docs/adr/0010-enforcement-topology.md",
      "title": "ADR-0010: Enforce at the harness edit boundary where it exists, at the commit boundary always — and fail to ask, never to allow",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "A PreToolUse hook returning permissionDecision deny refuses an unleased edit before it happens; the pre-commit boundary is the universal floor no settings key can remove. Every indeterminate path returns ask with a reason beginning NOT CHECKED. The hook runs in exec-form with no shell, which closes the SHELL-A class structurally rather than by care.",
      "tags": [
        "coordination",
        "enforcement",
        "hooks",
        "pretooluse",
        "fail-safe",
        "spike",
        "shell-a"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "bb38f77a5c7edb03695afe41bbb36d63a0fe0b068a6bc0a0e7fd2d49f0df71d2"
    },
    {
      "id": "adr-0011-projection-trust-boundary",
      "path": "docs/adr/0011-projection-trust-boundary.md",
      "title": "ADR-0011: Cross-agent content is untrusted data — the projection ships only after its rendering rules exist",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "The projection renders text authored by one agent's model into another agent's context, which the hook schema confirms is a live injection channel. Cross-agent content is therefore treated as data with no instruction authority, and the delivery order is inverted so no projection ships before its rendering rules and adversarial corpus exist.",
      "tags": [
        "coordination",
        "security",
        "prompt-injection",
        "trust-boundary",
        "stride",
        "projection"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "b8dc9c410ff5ad98b53c2849588f1ea2c3e33b6017048d9cef743d630671ce46"
    },
    {
      "id": "adr-0012-reuse-existing-mechanisms",
      "path": "docs/adr/0012-reuse-existing-mechanisms.md",
      "title": "ADR-0012: Compose the mechanisms that already exist — the harness ships two of them, and the fleet ships three more",
      "type": "adr",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "The F8 reconciliation the spec made a condition of pass. Two of the four failure modes are already partly addressed by mechanisms shipped in the harness itself, and three more by scripts in TheTerrace; each is adopted, superseded, or retired explicitly. Also records the exact git expression for unique work, and why the obvious one silently reports SAFE.",
      "tags": [
        "coordination",
        "reuse",
        "dup-a",
        "one-a",
        "worktree",
        "reachability",
        "git"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "1228eaa30ff8da634812cea2bf2745b008dfbf267c93034aafdc807509851e27"
    },
    {
      "id": "architecture",
      "path": "docs/architecture.md",
      "title": "AI-Forward — Architecture Overview",
      "type": "architecture",
      "status": "accepted",
      "owner": "@timianmalloo",
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
          "mermaid": "classDiagram\n  class Signature {\n    +Name name\n    +FacetList facets\n    +StyleHints? hints\n    +validate() conflicts\n    +roundTrip() bool  %% G10: identify AND generate\n  }\n  class Facet {\n    <<abstract>>\n    +String key\n  }\n  class SingleValuedFacet {\n    +Value value  %% Type, Arch, Layout, Density, Pacing, ...\n  }\n  class MultiValuedFacet {\n    +Value[] values  %% Nav, Input, Feedback, Motion, A11y (joined with +)\n  }\n  class StyleHints {\n    +String[] hints  %% bounded NL decoration, applied last\n  }\n  class Archetype {\n    +String id          %% A1..F2\n    +String name\n    +Exemplar[] exemplars\n    +Signature canonical\n    +String codegenDescriptor\n  }\n  Signature \"1\" o-- \"4..*\" Facet : composes\n  Facet <|-- SingleValuedFacet\n  Facet <|-- MultiValuedFacet\n  Signature \"0..1\" *-- \"1\" StyleHints : decorated by\n  Archetype \"1\" *-- \"1\" Signature : canonical\n  Archetype \"1\" o-- \"1..*\" Exemplar\n  note for Signature \"G4: MUST carry Type, Arch, Layout, Pacing.\\nG1: always composed with a concrete U1–U20 / S1–S10 spec.\""
        }
      ],
      "sourceSha256": "278a15e60eeb168b89ffb59cb751f1835ba038a6c68f684407d57c3ee96bb40c"
    },
    {
      "id": "architecture-agent-coordination",
      "path": "docs/architecture-agent-coordination.md",
      "title": "Agent coordination — architecture",
      "type": "architecture",
      "status": "draft",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "2027-02-20",
      "reviewSuggested": [],
      "summary": "The architecture for the agent-coordination layer: a git-tracked append-only record of intent, folded on demand with no daemon and no database, enforced at each harness's edit boundary and at the universal commit boundary, with a non-coordinating identifier allocator and a merge driver that regenerates derived artifacts rather than merging them. Every load-bearing choice here was settled by an executed spike, several of which overturned the obvious answer.",
      "tags": [
        "coordination",
        "worktrees",
        "multi-agent",
        "leases",
        "allocation",
        "hooks",
        "merge-driver",
        "spikes"
      ],
      "links": [
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        },
        {
          "to": "audit-log",
          "rel": "relates-to"
        }
      ],
      "diagrams": [
        {
          "kind": "flowchart",
          "title": "3. Components and boundaries",
          "mermaid": "flowchart TB\n  subgraph H[\"Harness edge — per agent, per worktree\"]\n    HK[\"PreToolUse hook<br/>exec-form args, no shell\"]\n    PC[\"pre-commit hook<br/>THE UNIVERSAL FLOOR\"]\n  end\n  subgraph CORE[\"coord core — stdlib, no deps, no daemon\"]\n    REC[\"Record<br/>append-only JSONL<br/>one file per session\"]\n    FOLD[\"Fold<br/>leases · work items · decisions<br/>pure function, replay-idempotent\"]\n    ALLOC[\"Allocator<br/>non-coordinating id\"]\n    CLASS[\"Artifact-class registry<br/>authored · derived · register · hotspot\"]\n  end\n  subgraph GIT[\"git — where structure beats policy\"]\n    MD[\".gitattributes merge driver<br/>derived → regenerate\"]\n    RL[\"reachability<br/>peers = for-each-ref minus HEAD's branch\"]\n  end\n  subgraph OUT[\"Surfaces\"]\n    PROJ[\"Projection ≤ 2k tokens<br/>UNTRUSTED DATA\"]\n    STAT[\"Operator status<br/>unique-work first\"]\n    STREAM[\"Stream\"]\n  end\n  HK -->|check| FOLD\n  PC -->|check + stage-by-name| FOLD\n  HK & PC -->|append| REC\n  REC --> FOLD\n  CLASS --> FOLD\n  ALLOC --> REC\n  ALLOC -.serves.-> EXT[\"EXISTING registers<br/>audit-log · change-log · findings\"]\n  FOLD --> PROJ & STAT & STREAM\n  CLASS --> MD\n  RL --> STAT\n  PROJ -.->|\"trust boundary<br/>additionalContext\"| H"
        }
      ],
      "sourceSha256": "af4c58efedd6655ac22bfcdd816c5a34cec5364c8f1d2bb97f4631fa2aba1807"
    },
    {
      "id": "architecture-dreaming",
      "path": "docs/architecture-dreaming.md",
      "title": "Dreaming subsystem — architecture",
      "type": "architecture",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "2027-02-11",
      "reviewSuggested": [],
      "summary": "Subsystem architecture for AI-Forward's dreaming capability — the offline consolidation pipeline (light/REM/deep) over the committed corpus, the HTML review/approval surface, the promotion oracle, the safe instance→class abstraction, the fleet learnings store, and the /apply-learnings federation path — as an LOA Continuous Sentinel with determinism at the floor and a human gate before any durable write. Refines the pack's top-level architecture; it is a subsystem, not a new system.",
      "tags": [
        "dreaming",
        "architecture",
        "consolidation",
        "federation",
        "oracle",
        "loa-continuous-sentinel"
      ],
      "links": [
        {
          "to": "spec-dreaming",
          "rel": "implements"
        },
        {
          "to": "architecture",
          "rel": "refines"
        },
        {
          "to": "adr-0002-fleet-learnings-store",
          "rel": "depends-on"
        },
        {
          "to": "adr-0003-promotion-oracle",
          "rel": "depends-on"
        },
        {
          "to": "adr-0004-instance-to-class-abstraction",
          "rel": "depends-on"
        },
        {
          "to": "adr-0005-harness-runner-boundary",
          "rel": "depends-on"
        }
      ],
      "diagrams": [
        {
          "kind": "flowchart",
          "title": "3. Components & boundaries",
          "mermaid": "flowchart LR\n  subgraph Consolidation [Consolidation context - T0 + one T3 step]\n    C1[corpus reader\\naudit/change/register/mitigations/markers] --> C2[light: stage + dedup + taint gate + scrub]\n    C2 --> C3[REM: reflect -> candidate classes\\n(model boundary - injected)]\n    C3 --> C4[deep: score + threshold gate -> proposals]\n    C4 --> C5[render: dream.json + dream-data.js + review HTML + Dream Diary]\n  end\n  subgraph Governance [Governance context - human gate]\n    C5 --> G1[[Dream Review HTML\\napprove/edit/reject/defer]]\n    G1 --> G2[decisions.json]\n    G2 --> G3[apply-decisions: validate + taint re-check]\n  end\n  subgraph Federation [Federation context]\n    G3 -->|approved general| F1[abstract instance->class\\n+ scrub + boundary]\n    F1 --> F2[(fleet learnings store\\nin ai-forward)]\n    G3 -->|approved repo-local| F3[(repo defect-classes.md)]\n    F2 -->|/apply-learnings push| F4[reconcile vs target repo\\n-> reviewable diff/branch]\n    F2 -->|/updatepack pull| F5[deployment map -> repo]\n  end\n  ORACLE[(mitigations.jsonl)]:::o --> C1\n  IMPL[/implement, /investigate,\\nhuman validation/] --> ORACLE\n  classDef o fill:#2c2a29,stroke:#888684;"
        }
      ],
      "sourceSha256": "a3975ab26cb8083b799bfb77026c6bf0ddaf8da812fe0cbbd5a5bc492d1c8987"
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
      "id": "note-20260818-dream-rerun-unchanged-corpus",
      "path": "docs/notes/note-20260818-dream-rerun-unchanged-corpus.md",
      "title": "Re-running /dream over an unchanged corpus re-surfaces already-promoted classes under new proposal ids",
      "type": "decision-note",
      "status": "draft",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "2027-02-14",
      "reviewSuggested": [],
      "summary": "Observed in drm-0004: a dream over a corpus unchanged since the prior dream re-emits the same control-upgrade/marker/mitigation proposals under fresh (dream, proposal) ids, and apply-decisions' per-(dream,proposal) idempotency does not treat them as duplicates — so approving them re-appends the same class to the fleet store. Push-stage slug dedup (\"latest wins per class slug\") absorbs the downstream harm, so the correct operating response is Defer/Reject at the review gate, not a code change.",
      "tags": [
        "decision-note",
        "dreaming",
        "continuous-improvement",
        "idempotency"
      ],
      "links": [
        {
          "to": "architecture-dreaming",
          "rel": "relates-to"
        },
        {
          "to": "spec-dreaming",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "e034436a95ed2a8bec9d0db465dfd0c28d31fe2911944d00c003e5be9c58e622"
    },
    {
      "id": "note-20260820-spike-corpus-assertion",
      "path": "docs/notes/note-20260820-spike-corpus-assertion.md",
      "title": "A verification script reported COLLISION-FREE over zero identifiers, because it only compared set size to list size",
      "type": "decision-note",
      "status": "draft",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "2027-02-20",
      "reviewSuggested": [],
      "summary": "While spiking the allocator for ADR-0008, the verification harness printed \"COLLISION-FREE WITHOUT COORDINATION\" over an empty result set — the worker processes had died on a syntax error and the check only asserted len(set(x)) == len(x), which is trivially true of nothing. Recorded as an architectural rule (R4) rather than a code fix, because the defect was in the shape of the assertion.",
      "tags": [
        "decision-note",
        "controls",
        "spike",
        "empty-corpus",
        "continuous-improvement"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "relates-to"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "bc92c7e129284b9993f97548093f6989d1a2f73057a9f190898dbc64af6dea87"
    },
    {
      "id": "note-20260822-backlog-triage-and-worktree-discipline",
      "path": "docs/notes/note-20260822-backlog-triage-and-worktree-discipline.md",
      "title": "Decision note — revision-42 backlog triage, and worktree-per-session",
      "type": "decision-note",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2027-02-22",
      "reviewSuggested": [],
      "summary": "Four sub-ADR decisions taken while clearing the revision-42 backlog and adding worktree-per-session: withdrawing FR-050 rather than acting on it, closing FR-054 as won't-do with a falsifiable trigger, bounding the bare-handle sweep at write sites, and extending coord-core.py rather than adding a parallel worktree tool.",
      "tags": [
        "forensic-review",
        "triage",
        "worktree",
        "coordination",
        "continuous-improvement"
      ],
      "links": [
        {
          "to": "forensic-review-rev42-backlog",
          "rel": "relates-to"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        },
        {
          "to": "architecture",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "e2331adf193cdda5220425ea89ae8c999cdcc6b80f86c5d2fa5df8a77d2fc869"
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
      "id": "design-coord-core-phase1",
      "path": "docs/design/coord-core-phase1.md",
      "title": "Design — coord core, Phase 1 walking skeleton (record · fold · claim/check/release/tail)",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "2027-02-20",
      "reviewSuggested": [],
      "summary": "The Phase-1 walking skeleton: an append-only per-session record, a pure fold over it, and four verbs (claim, check, release, tail) that let two sessions in two worktrees see each other's leases. Stdlib only, no daemon, no dependency. The LOG-A seam — an append onto a file that does not end in a newline fuses two records and loses both — is the record writer's first test, not a hardening.",
      "tags": [
        "coordination",
        "walking-skeleton",
        "append-only",
        "fold",
        "leases",
        "log-a",
        "stdlib"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "spec-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "adr-0007-coordination-substrate",
          "rel": "implements"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "64784accd18757a616f565035e8c539171a00124817cf70dc05a5e1284ec5031"
    },
    {
      "id": "design-coord-enforcement-phase2",
      "path": "docs/design/coord-enforcement-phase2.md",
      "title": "Design — coord enforcement, Phase 2 (PreToolUse hook · pre-commit floor · work-preservation guard)",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "2027-02-22",
      "reviewSuggested": [],
      "summary": "Phase 2 makes the Phase-1 lease actually hold: a PreToolUse hook that refuses an unleased edit, a pre-commit floor no settings key can switch off, and a guard that refuses to move HEAD over work reachable from exactly one ref. Splits the store in two — intent stays folded, enforcement decisions never are — because Phase 1's measurement put the fold at its compaction trigger at 10k events.",
      "tags": [
        "coordination",
        "enforcement",
        "pretooluse",
        "pre-commit",
        "reachability",
        "work-loss",
        "ctrl-g",
        "stdlib"
      ],
      "links": [
        {
          "to": "architecture-agent-coordination",
          "rel": "implements"
        },
        {
          "to": "adr-0010-enforcement-topology",
          "rel": "implements"
        },
        {
          "to": "design-coord-core-phase1",
          "rel": "refines"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "223442bf4c429ba48ed47b7c7f67a0a3dd9f4d8ed7ac9b2c36fc078df4a4c604"
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
      "id": "mockup-documentation-portal",
      "path": "docs/mockups/documentation-portal.md",
      "title": "Documentation Portal — mockup",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "documentation-portal",
      "reviewBy": "2027-02-11",
      "reviewSuggested": [],
      "summary": "Self-contained, dependency-free high-fidelity mockup of the Documentation Portal — the DocsPortal (Content Portal / HolyGrail reading layout) front door: persistent sidebar nav over six sections (Getting Started · Capabilities · The 21 Skills · UI Capabilities · Systems · Reference), search, and reading-optimised content. Renders the hard states (loading/empty/error) via a review harness (theme · viewport · state · motion) and reuses docs/DESIGN.md's AA-audited knowledge-surface tokens.",
      "tags": [
        "documentation",
        "portal",
        "mockup",
        "content-portal",
        "ui"
      ],
      "links": [
        {
          "to": "spec-documentation-portal",
          "rel": "implements"
        },
        {
          "to": "design-language-docs-explorer",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "ead16153a64b0f7b7be20781c0f518b40cb453c8351bb919b90a81d8c2dff1dc"
    },
    {
      "id": "mockup-dream-review",
      "path": "docs/mockups/dream-review.md",
      "title": "Dream Review — mockup",
      "type": "design",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "2027-02-11",
      "reviewSuggested": [],
      "summary": "Self-contained, dependency-free high-fidelity mockup of the Dream Review view — the Master-Detail approval queue the maintainer uses to review a dream's proposals (evidence, provenance, confidence, proposed control, federation scope) and Approve/Edit/Reject/Defer each, then export decisions. Renders the hard states (empty/loading/error/overflow) via a review harness (theme · viewport · state · motion) and reuses docs/DESIGN.md's AA-audited knowledge-surface tokens.",
      "tags": [
        "dreaming",
        "mockup",
        "review-view",
        "master-detail",
        "ui"
      ],
      "links": [
        {
          "to": "spec-dreaming",
          "rel": "implements"
        },
        {
          "to": "design-language-docs-explorer",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "47760a4a638e2b08e5acf59575b589ef336fa6651e8aa331b60e388d5b25d654"
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
      "id": "backtest-optimize-graph",
      "path": "docs/backtest/optimize-graph/backtest.md",
      "title": "optimize-graph back-test — twelve real prompts replanned",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2027-02-18",
      "reviewSuggested": [],
      "summary": "Back-test of the /optimize-graph skill against twelve real prompts drawn from 750 committed audit entries across TheTerrace, meridian-finance-planner and HealthWatch. Reports modeled time and token indices alongside rubric-scored completeness and rigor, with an explicit measured-vs-modeled integrity split — session timings in those logs span days of human-paced work and are therefore not execution times. Headline: completeness +14.8 pts, rigor +9.4 pts, and no case lost either.",
      "tags": [
        "optimize-graph",
        "back-test",
        "evaluation",
        "execution-graph",
        "cost-vs-delivery"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "depends-on"
        },
        {
          "to": "audit-log",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "3d52521a4ce7b4f2a93a790acc21f627aff351d577051bf8df8a4cc90c083cb8"
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
      "sourceSha256": "fb1bbce65fe50af62c0997874fa057e346312eb28973c3d20df82028689a851d"
    },
    {
      "id": "docs-index",
      "path": "docs/index.md",
      "title": "AI-Forward — Documentation Map of Content",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
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
      "sourceSha256": "12bb237176e77568df0d5e1b3c00eaeace976e20055bc5dbee1686b6f3dd6b98"
    },
    {
      "id": "dream-diary",
      "path": "docs/dreams/DREAMS.md",
      "title": "Dream Diary",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "Human-readable narrative of each dream pass (what it added/merged/superseded). NOT a promotion source - excluded from re-ingestion (no self-poisoning). Generated by dream.py.",
      "tags": [
        "dreaming",
        "dream-diary",
        "continuous-improvement"
      ],
      "links": [
        {
          "to": "spec-dreaming",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "1d3a3d212d0338e9500f1df53f5f6b1b4f2dbf99c27754fa17eddb9cfe5cfa1c"
    },
    {
      "id": "forensic-review",
      "path": "docs/reviews/forensic-review.md",
      "title": "Forensic Review — AI-Forward repository (revisions 30 & 33)",
      "type": "doc",
      "status": "superseded",
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
      "sourceSha256": "3ad50771ca4b95400a6af418f366f314636bfb1893d3908343fb9fd45304dac1"
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
      "title": "Forensic Review Backlog — AI-Forward repository (revisions 30 & 33)",
      "type": "doc",
      "status": "superseded",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-08",
      "reviewSuggested": [],
      "summary": "Twelve items (FR-031..FR-042) from the revision-30 review, ordered into four independently deliverable phases. Nine are RESOLVED at revisions 31-32 (FR-031..FR-035, FR-037, FR-038, FR-040..FR-042); three remain open (FR-036, FR-039, and the unverified end-to-end adoption path). Two proposals were overturned at triage by establishing the contract rather than trusting the finding.",
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
      "sourceSha256": "c4411d9595b1c3b09a77b6929db90fc253c5ae9de95e0ca0205bbf7fbc0e9d20"
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
      "id": "forensic-review-rev42",
      "path": "docs/reviews/forensic-review-rev42.md",
      "title": "Forensic Review — AI-Forward repository (revision 42)",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "Forensic assessment at commit e4eae82 (revision 42), clean tree, all seven CI gates green and verified green on a runner. Four findings carried from revision 33 are now verified RESOLVED and the largest standing residual risk — \"CI has never executed on a runner\" — is closed by evidence. Nine findings remain or are new. The dominant one is convergent, not incidental: the three newest capabilities (/dream, /apply-learnings, /optimize-graph) have neither unit tests nor eval cases, while writing durable cross-repo stores. That is RIG-C — sweep stopped at the instance — on its fourth confirmed occurrence, and this time the un-swept sibling is the federation path. A second finding (FR-056) was discovered by obeying V16: correct change-propagation turns the CI graph gate red, so the incentive runs against the discipline.",
      "tags": [
        "forensic-review",
        "adoption-readiness",
        "testing",
        "verification",
        "documentation",
        "ci"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "documents"
        },
        {
          "to": "forensic-review-rev42-backlog",
          "rel": "relates-to"
        },
        {
          "to": "forensic-review",
          "rel": "supersedes"
        }
      ],
      "diagrams": [],
      "sourceSha256": "eb4ee397f9d5c03173fe87d5d96820e078bcc99b154627311033db26810e1e7c"
    },
    {
      "id": "forensic-review-rev42-backlog",
      "path": "docs/backlog/forensic-review-rev42.md",
      "title": "Forensic Review Backlog — revision 42",
      "type": "doc",
      "status": "resolved",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "Backlog from the revision-42 forensic review at commit e4eae82, ALL NINE ITEMS TRIAGED AND DISPOSITIONED at revision 43. Seven resolved with a control observed failing first, FR-050 closed as not-a-defect (its premise - staleness inferred from an mtime - did not survive checking, and its recommended deletion would have broken the build), FR-054 closed won't-do with a falsifiable re-open trigger. Three of the most useful findings emerged from doing the work: a crash in the script that writes into other repositories, found by the first assertion ever written against it; a false staleness premise; and a coverage gate that was wrong in both directions until its own verdicts were disconfirmed.",
      "tags": [
        "forensic-review",
        "backlog",
        "testing",
        "verification",
        "documentation",
        "accessibility"
      ],
      "links": [
        {
          "to": "forensic-review-rev42",
          "rel": "relates-to"
        },
        {
          "to": "architecture",
          "rel": "relates-to"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "e509f32db3c5fd2e4daeb66ed2bc9db4eec6d1710923b0570a4845aaee00e745"
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
      "sourceSha256": "75e75721568488011950601e2ef7862557c3bc52dd9907a3a6f7b209caf1f580"
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
      "id": "plan-optimize-graph-live-01",
      "path": "docs/plans/optimize-graph-live-01.md",
      "title": "optimize-graph live run 01 — commit the rev-40 change set",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2027-02-18",
      "reviewSuggested": [],
      "summary": "First live /optimize-graph run, on the prompt that asked for it. Records the plan, the planned-vs-actual ledger (GO18), and the run's headline measurement — parallelising three independent verification gates ran 19% SLOWER (0.84x) while completeness, rigor and tokens were all unchanged, which under the lexicographic objective is pure loss and a rejected plan. The span was 83% of the work so the ceiling was only 1.20x, and fan-out overhead exceeded the whole available gain. The measurement replaced a modeled constant and produced GO4a.",
      "tags": [
        "optimize-graph",
        "plan",
        "cost-vs-delivery",
        "measurement",
        "live-run"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "depends-on"
        },
        {
          "to": "backtest-optimize-graph",
          "rel": "relates-to"
        },
        {
          "to": "audit-log",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "fb30d636f0c68014b333a7182f767e54d66af70659c3c027f266805d9a4539bb"
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
      "id": "proposal-hosting-and-dream-manifest",
      "path": "docs/notes/hosting-and-dream-manifest.md",
      "title": "Proposal / dialog: GitHub Pages hosting + the Dream Manifest",
      "type": "doc",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "An RFC/dialog opener on (1) whether to host the Documentation Portal and surfaces on GitHub Pages, (2) how that impacts dream output and privacy, and (3) a proposed Dream Manifest - a first-class, reviewable, hostable artifact recording which approved learnings from a dream session target which repos (the missing 'targeting' layer between apply-decisions and /apply-learnings). Ends with the open decisions for the maintainer.",
      "tags": [
        "hosting",
        "github-pages",
        "dreaming",
        "federation",
        "manifest",
        "dialog",
        "rfc"
      ],
      "links": [
        {
          "to": "spec-documentation-portal",
          "rel": "relates-to"
        },
        {
          "to": "architecture-dreaming",
          "rel": "relates-to"
        },
        {
          "to": "adr-0002-fleet-learnings-store",
          "rel": "relates-to"
        },
        {
          "to": "adr-0006-dream-manifest",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "69a9739b5ab387e841ebdf338c644cff7a93a61b48d89658622637b720687c5c"
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
      "id": "investigation-blank-explainer-live",
      "path": "docs/investigations/blank-explainer-live.md",
      "title": "Investigation: the hosted explainer renders blank even after the 'fix'",
      "type": "investigation",
      "status": "resolved",
      "owner": "@timianmalloo",
      "phase": "hosting",
      "reviewBy": "",
      "reviewSuggested": [],
      "summary": "The hosted explainer stayed blank after a fix was declared, because the fix lived only in the working tree — it was never deployed, so the live URL still served the old syntax-broken file. A compounding cause: the earlier fix was proven with `node --check` (syntax) but never with a render check (the mounted surface). Both verified here: the live file is the old corrupted version; a jsdom load-and-run proves the fixed file MOUNTS while the old one stays BLANK. Root cause = not-deployed + verified-at-the-wrong-level. Registered as class PACK-H.",
      "tags": [
        "ui",
        "hosting",
        "github-pages",
        "explainer",
        "deploy",
        "render-verification"
      ],
      "links": [
        {
          "to": "adr-0006-dream-manifest",
          "rel": "relates-to"
        },
        {
          "to": "proposal-hosting-and-dream-manifest",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "f16679f8cf89726bce68ed00a6d3e8d29fed442dae57701e709204121043d2af"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/index.md",
      "title": "Continuous Improvement & Dreaming — harvesting learnings across repos (domain knowledge)",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "Sourced evidence base for continuously harvesting learnings, mistakes, patterns and anti-patterns across a fleet of local repositories and sharing them so every repo benefits. Synthesises the \"dreaming\" wave (Claude Dreams, OpenClaw, Karpathy's LLM-wiki), its academic roots (Reflexion, Generative Agents reflection, A-MEM, sleep-time compute), the self-improving AGENTS.md trend, and SRE/NASA lessons-learned practice — then maps them onto what AI-Forward already ships (audit/change logs, the defect-class register, the knowledge graph) and states the gap: the pack has built the *awake* half (capture) and lacks the *asleep* half (scheduled offline consolidation + cross-repo federation).",
      "tags": [
        "continuous-improvement",
        "dreaming",
        "agent-memory",
        "self-improvement",
        "audit-log",
        "defect-classes",
        "cross-repo",
        "federation"
      ],
      "links": [
        {
          "to": "defect-classes",
          "rel": "relates-to"
        },
        {
          "to": "audit-log",
          "rel": "relates-to"
        },
        {
          "to": "architecture",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "ca59c1f18a31d75efe01b13b72c3066f239f04cbf7ca02ea48d7db2f1d243472"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming-comparables",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/comparables.md",
      "title": "Continuous Improvement & Dreaming — Comparables",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "How Claude Dreams, OpenClaw, Reflexion, Generative Agents, A-MEM, the LLM-wiki, self-improving AGENTS.md, and SRE/NASA lessons-learned frame and solve the problem — and what AI-Forward should borrow or reject; plus the five-part architecture everyone independently builds.",
      "tags": [
        "dreaming",
        "comparables",
        "claude-dreams",
        "openclaw",
        "postmortem",
        "agents-md"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "b73485876844dabcbd46db5a9000c3dc2f1961690f753bed45344a381788c59e"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming-data",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/data-and-constants.md",
      "title": "Continuous Improvement & Dreaming — Data, Constants & Invariants",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "The concrete parameters (Claude Dreams 1-100 sessions; OpenClaw's six weighted deep-ranking signals and threshold gates; nightly cron), the AI-Forward corpus a dream pass reads, the eight testable invariants (guardrails), and an order-of-magnitude cost/cadence model.",
      "tags": [
        "dreaming",
        "constants",
        "invariants",
        "guardrails",
        "scoring",
        "corpus"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "b51bd3d2499fd2de488db29041e050e4cca00be8356d9cc0aaacd3244933c5b3"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming-glossary",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/glossary.md",
      "title": "Continuous Improvement & Dreaming — Glossary",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "The ubiquitous language for the dreaming/consolidation capability — dream pass, light/REM/deep phases, candidate, promotion, provenance taint gate, Dream Diary, outcome signal, defect class, control ladder, federation, fleet learnings store — for use in the spec, design, and code.",
      "tags": [
        "dreaming",
        "glossary",
        "ubiquitous-language"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "3bed1089c00c0bdb194f4dcae879b034629f799f2cb013fb1d915a14dc6f3bf7"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming-open-questions",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/open-questions.md",
      "title": "Continuous Improvement & Dreaming — Open Questions & Failure Modes",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "The unresolved forks to carry into /specify (fleet store location, the promotion oracle, safe instance-to-class abstraction, cadence, runner), the known failure modes to design against (prose memoir, auto-merge, in-place mutation, memory poisoning, over-generalisation, PII leakage), and the disconfirming views deliberately sought.",
      "tags": [
        "dreaming",
        "open-questions",
        "failure-modes",
        "disconfirming",
        "federation"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "f4d7e4339569fde71420f34a2746e64c557dbd0c260ac4359601d88175584096"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming-references",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/references.md",
      "title": "Continuous Improvement & Dreaming — References",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "Primary product/platform sources, seminal papers (Reflexion, Generative Agents, A-MEM, sleep-time compute), SRE/NASA practice, and the in-repo standards this capability composes with (continuous-improvement, audit-and-change-log, defect-classes, knowledge-visualization) plus runners.",
      "tags": [
        "dreaming",
        "references",
        "standards",
        "papers",
        "in-repo-standards"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "397766d1b8e558028c3ca34cb528aef9cd411cf60eb3237a9a02d71e408c2406"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming-sota",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/state-of-the-art.md",
      "title": "Continuous Improvement & Dreaming — State of the Art",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "Current best practice for continuous self-improvement: the awake/asleep loop; Claude Dreams and OpenClaw's phased local dreaming; Reflexion and Generative Agents as the academic root; A-MEM and Karpathy's LLM-wiki as the durable-store shape; sleep-time compute as the scheduling warrant.",
      "tags": [
        "dreaming",
        "agent-memory",
        "self-improvement",
        "reflexion",
        "sleep-time-compute"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "0ef079786afc923b5edb436a794704433acd3727d918d3a554f76c1410303989"
    },
    {
      "id": "kb-continuous-improvement-and-dreaming-sources",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/sources.md",
      "title": "Continuous Improvement & Dreaming — Sources",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "continuous-improvement",
      "reviewBy": "2026-11-13",
      "reviewSuggested": [],
      "summary": "Full source list with access dates and confidence labels — primary product/platform docs (Claude Dreams, OpenClaw), seminal papers, SRE/NASA practice, and the in-repo standards — with a currency note on which sources are research-preview or secondary framing.",
      "tags": [
        "dreaming",
        "sources",
        "citations"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "bb27d016b82e07af7bd4a1dd442aef75611c794638d7b7c2b1da04bf4009d26a"
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
      "id": "kb-graph-and-loop-engineering",
      "path": "docs/knowledge/graph-and-loop-engineering/index.md",
      "title": "Graph engineering, loop engineering & graph optimization (domain knowledge)",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "Sourced evidence base for planning an agent's work as an explicit dependency graph before executing it: the classical work/span and critical-path theory that bounds any possible speedup, the termination theory (ranking functions over a well-founded order) that is the only real guarantee against runaway loops, the measured agentic results (LLMCompiler 3.7x latency / 6.7x cost; Anthropic's orchestrator-worker 90.2% uplift at 15x tokens), and the MAST failure taxonomy showing that most multi-agent failure is specification and verification, not model capability. Concludes that graph optimization must be a completeness-and-rigor amplifier, never a trade.",
      "tags": [
        "graph-engineering",
        "loop-engineering",
        "graph-optimization",
        "dag",
        "parallelism",
        "critical-path",
        "termination",
        "agent-orchestration",
        "cost-vs-delivery"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "relates-to"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        },
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "relates-to"
        }
      ],
      "diagrams": [],
      "sourceSha256": "9a87e3ca3d848547da3a4bde0eaeeec35139947001b3460bf743cee59efd8eb9"
    },
    {
      "id": "kb-graph-and-loop-engineering-comparables",
      "path": "docs/knowledge/graph-and-loop-engineering/comparables.md",
      "title": "Graph & loop engineering — Comparables",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "How existing systems frame and solve execution-graph planning — workflow engines (Airflow, Temporal, Dagster), agent frameworks (LangGraph, LLMCompiler, orchestrator-worker), and compiler approaches (DSPy) — plus the in-fleet evidence from TheTerrace, meridian and HealthWatch audit logs, including a measured unbounded-fan-out failure and a measured successful parallel run.",
      "tags": [
        "comparables",
        "langgraph",
        "llmcompiler",
        "airflow",
        "temporal",
        "dspy",
        "in-repo-evidence"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "d2d735a3a8c75cbe1e3380ea651e7130569c42dd8f0b7cc535aaeecfbc74f15d"
    },
    {
      "id": "kb-graph-and-loop-engineering-data",
      "path": "docs/knowledge/graph-and-loop-engineering/data-and-constants.md",
      "title": "Graph & loop engineering — Data & constants",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "The numbers — published benchmark results (LLMCompiler, orchestrator-worker, MAST failure rates), framework defaults (LangGraph recursion_limit 25), 2026 cost ranges, and the measurements taken from this fleet's own 750 committed audit entries — each with its confidence label and a currency warning on the fast-moving ones.",
      "tags": [
        "data",
        "constants",
        "benchmarks",
        "token-cost",
        "defaults",
        "fleet-measurements"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "244fc6f0ec27f438d5d0e0d0d1000430b5363ad5aea2658479c1010660d433a4"
    },
    {
      "id": "kb-graph-and-loop-engineering-glossary",
      "path": "docs/knowledge/graph-and-loop-engineering/glossary.md",
      "title": "Graph & loop engineering — Glossary",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "The ubiquitous language for execution-graph planning — work, span, critical path, node, edge, wave, fan-out/join, collapse/promote, variant, well-founded order, circuit breaker, gate node, cost-vs-delivery ledger — for use in the skill, the plans it produces, and any code.",
      "tags": [
        "glossary",
        "ubiquitous-language",
        "dag",
        "span",
        "variant",
        "fan-out"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "735f23639faaa7799ac69027b7b2740589e710dc9a4bee67552937962e04e842"
    },
    {
      "id": "kb-graph-and-loop-engineering-open-questions",
      "path": "docs/knowledge/graph-and-loop-engineering/open-questions.md",
      "title": "Graph & loop engineering — Open questions & failure modes",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "What the research could not settle, the disconfirming evidence against graph optimization, and the domain's known failure modes — including the ones that argue against decomposition and parallelism and the ones that would make an optimizer actively harmful if ignored.",
      "tags": [
        "open-questions",
        "risks",
        "failure-modes",
        "disconfirming-evidence"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "32e2442274dfd6ac938150fa698bf26449196ab55f8ed2ac58c6746a9c85e458"
    },
    {
      "id": "kb-graph-and-loop-engineering-references",
      "path": "docs/knowledge/graph-and-loop-engineering/references.md",
      "title": "Graph & loop engineering — Reference information",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "The formulae, invariants, decision rules and edge cases of the domain — the work/span bounds, Amdahl and Brent, the independence and coupling tests, the termination obligation, the granularity rules, and the boundary set an execution-graph planner must handle.",
      "tags": [
        "reference",
        "formulae",
        "brent",
        "amdahl",
        "ranking-function",
        "invariants",
        "edge-cases"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "976eaa808cc1a6209ff0385bea37037753edb6d287890faff0ced7b9c6d3f6a0"
    },
    {
      "id": "kb-graph-and-loop-engineering-sota",
      "path": "docs/knowledge/graph-and-loop-engineering/state-of-the-art.md",
      "title": "Graph & loop engineering — State of the Art",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "Current best practice across the three joined literatures — DAG scheduling and the work/span bound, agentic parallel planning (LLMCompiler, orchestrator-worker, the five Anthropic workflow patterns), loop termination via ranking functions, and the compiler loop-transformation tradition — with what each contributes to planning an agent's execution graph.",
      "tags": [
        "dag",
        "scheduling",
        "critical-path",
        "termination",
        "parallel-function-calling",
        "orchestrator-worker"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "d9a54c86c0ddeb9ed22b4f44947289ad43e0c59261e0ca68123b1e9390be07b2"
    },
    {
      "id": "kb-graph-and-loop-engineering-sources",
      "path": "docs/knowledge/graph-and-loop-engineering/sources.md",
      "title": "Graph & loop engineering — Sources",
      "type": "knowledge",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "execution-optimization",
      "reviewBy": "2026-11-20",
      "reviewSuggested": [],
      "summary": "Full source list with access dates and confidence labels — primary papers (LLMCompiler, MAST), framework documentation (LangGraph), vendor engineering writeups (Anthropic), classical parallel-computing and termination theory, this fleet's own committed audit logs, and the in-pack standards this base composes with — plus the currency warning on the fast-moving material.",
      "tags": [
        "sources",
        "citations",
        "currency"
      ],
      "links": [
        {
          "to": "kb-graph-and-loop-engineering",
          "rel": "refines"
        }
      ],
      "diagrams": [],
      "sourceSha256": "6bd3d8db6ff31d5f4e4590b25368a077b0f2f357c00c709e893a6bef405f02d3"
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
          "to": "design-coord-core-phase1",
          "rel": "documents"
        },
        {
          "to": "design-coord-enforcement-phase2",
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
      "sourceSha256": "07a53576dc1e7d9a2a94a18354777885feabcf414c71edf7bfa93835376372f0"
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
      "id": "spec-agent-coordination",
      "path": "docs/specs/agent-coordination.md",
      "title": "Agent coordination — shared context and explicit coordination across worktrees and agents",
      "type": "spec",
      "status": "draft",
      "owner": "@timianmalloo",
      "phase": "coordination",
      "reviewBy": "2027-02-20",
      "reviewSuggested": [],
      "summary": "Specification for a repo-local, model-agnostic coordination layer that lets several agents and worktrees work one repository at once without losing work or time. Grounded in measured evidence from TheTerrace, HealthWatch and Meridian, it targets four distinct failure modes — structural conflict on derived artifacts, allocation collision on client-minted ids, silent semantic divergence, and outright work loss in a shared tree — and requires each rule to ship as a mechanism that fails rather than a paragraph that is read.",
      "tags": [
        "coordination",
        "worktrees",
        "multi-agent",
        "merge-conflicts",
        "leases",
        "allocation",
        "continuous-improvement"
      ],
      "links": [
        {
          "to": "defect-classes",
          "rel": "relates-to"
        },
        {
          "to": "audit-log",
          "rel": "relates-to"
        },
        {
          "to": "architecture",
          "rel": "relates-to"
        },
        {
          "to": "spec-dreaming",
          "rel": "relates-to"
        }
      ],
      "diagrams": [
        {
          "kind": "flowchart",
          "title": "User flows",
          "mermaid": "flowchart TD\n  A([Session begins work item]) --> B[Announce intent + prior-art search]\n  B --> C{Announcement complete?}\n  C -->|no search recorded| C1[Reported incomplete: state what you searched for] --> B\n  C -->|yes| D[Claim artifacts]\n  D --> E{Any overlapping unexpired lease?}\n  E -->|no| F[Granted + decisions in force returned with the grant]\n  E -->|yes, another session| G[REFUSED: holder, work item, expiry, remedy]\n  E -->|undecidable overlap| G2[REFUSED as a precaution, and says so]\n  E -->|hotspot| H[REFUSED: owned by integrator] --> H1[Record request against integrator] --> I\n  G --> I{Can I do other work in this item?}\n  G2 --> I\n  I -->|yes| J[Proceed on the unblocked part]\n  I -->|no| K[Record block, naming what is needed] --> K1([Visible to the holder now, not at merge])\n  F --> L[Edit - permitted, lease held]\n  L --> M{Liveness maintained?}\n  M -->|no, TTL elapsed| N[Leases expire - recorded as an event, not an absence] --> D\n  M -->|yes| O[Release / done]\n  O --> P([Leases dropped, work item closed])"
        },
        {
          "kind": "flowchart",
          "title": "User flows",
          "mermaid": "flowchart TD\n  A([Harness about to write a file]) --> B{Lease state determinable?}\n  B -->|no record / no git / unreadable registry| C[NOT CHECKED - stated explicitly, never a silent pass] --> L\n  B -->|yes| E{Artifact class?}\n  E -->|derived| F[Allow - derived artifacts are regenerated, never leased]\n  E -->|hotspot| G[REFUSE - owned by integrator]\n  E -->|authored / register| H{Lease held by me?}\n  H -->|yes| I[Allow]\n  H -->|no, free| J[REFUSE: claim it first - one command, given verbatim]\n  H -->|no, held by other| K[REFUSE: holder + work item + expiry + remedy]\n  F --> L{Commit boundary}\n  I --> L\n  L --> M{Any staged artifact never claimed?}\n  M -->|yes| N[REFUSE the commit - the universal floor, present in every harness]\n  M -->|no| O([Commit proceeds])"
        },
        {
          "kind": "flowchart",
          "title": "User flows",
          "mermaid": "flowchart TD\n  A([PR opened]) --> B{Mergeable?}\n  B -->|conflicting| C[State it plainly: CONFLICTED - no gate will run]\n  C --> C1[Distinguished from 'gate has not reported yet' - today these are the same silence]\n  C1 --> D[Resolve: rebase, then REGENERATE derived artifacts]\n  D --> E{Conflict outside the declared derived set?}\n  E -->|yes| F[FAIL CLOSED - change nothing, name the paths] --> G([Human resolves])\n  E -->|no| H[Stage only the paths written, BY NAME]\n  H --> I[Name every file deliberately left alone]\n  I --> J{Commits in == commits out?}\n  J -->|no| K[REFUSE the push - a commit was dropped] --> G\n  J -->|yes| L[Push with an explicit refspec]\n  L --> M{Remote ref matches local?}\n  M -->|no| N[FAIL by name - an exit code is not a result] --> G\n  M -->|yes| B\n  B -->|clean| O([Gate runs])"
        },
        {
          "kind": "flowchart",
          "title": "User flows",
          "mermaid": "flowchart TD\n  A([Session needs an id for a shared register]) --> B[Request from the allocator]\n  B --> C{Requires seeing other sessions?}\n  C -->|yes - scanning| C1[REJECTED DESIGN: two sessions minting before either pushes still collide]\n  C -->|no - non-coordinating scheme| D[Id issued]\n  D --> E[Entry written to the register]\n  E --> F[Merge with another branch]\n  F --> G{Both entries present after merge?}\n  G -->|count fell| H[FAIL CLOSED - a resolution that loses an entry is refused] --> I([Human resolves, both entries kept])\n  G -->|both present| J([Merged])"
        },
        {
          "kind": "flowchart",
          "title": "User flows",
          "mermaid": "flowchart TD\n  A([About to move HEAD: checkout / reset / rebase / branch -D]) --> B[Count commits reachable from HEAD and from no other ref]\n  B --> C{Count > 0?}\n  C -->|cannot determine| D[REFUSE and say it could not determine - never a silent SAFE]\n  C -->|yes, including exactly 1| E[REFUSE - list the commits, offer push as the remedy]\n  C -->|no| F([Safe to move])\n  E --> G[Push] --> B"
        }
      ],
      "sourceSha256": "6d92efaafdbf157502c92422c2cab588ba17c1630d806b480cb7e21fa12742dd"
    },
    {
      "id": "spec-documentation-portal",
      "path": "docs/specs/documentation-portal.md",
      "title": "Documentation Portal — a derived, self-maintaining interactive front door",
      "type": "spec",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "documentation-portal",
      "reviewBy": "2027-02-11",
      "reviewSuggested": [],
      "summary": "Specification for a single, polished, interactive HTML documentation portal that is the front door to the AI-Forward repo — a capabilities overview, concrete reference for all 21 skills, an in-depth UI-capabilities section, and an explicit getting-started guide. The portal is a DERIVED artifact (a pure function of committed pack sources), regenerated on every sync and drift-gated in CI, so it cannot rot as the repo evolves; editorial sections live in committed source, structured content (skills, counts, UI standards) is pulled from the pack.",
      "tags": [
        "documentation",
        "portal",
        "onboarding",
        "derived-artifact",
        "getting-started",
        "discoverability"
      ],
      "links": [
        {
          "to": "architecture",
          "rel": "refines"
        },
        {
          "to": "design-language-docs-explorer",
          "rel": "depends-on"
        },
        {
          "to": "docs-index",
          "rel": "relates-to"
        }
      ],
      "diagrams": [
        {
          "kind": "flowchart",
          "title": "User flows (happy + alternate + error + recovery)",
          "mermaid": "flowchart TD\n  open([Open docs/portal/index.html over file://]) --> load{portal-data.js present & valid?}\n  load -->|no/malformed| err[Error state: 'Portal data missing - regenerate with build-docs-portal.py'] --> done1([Close])\n  load -->|yes| land[Land on Getting Started - the guided descent]\n  land --> nav{What does the reader want?}\n  nav -->|orient| cap[Capabilities overview + live counts]\n  nav -->|start| gs[Getting Started steps -> run first skill]\n  nav -->|look up a skill| skills[Skills reference, grouped by the loop]\n  nav -->|UI depth| ui[UI Capabilities deep-dive]\n  nav -->|systems| sys[Dreaming / graph / audit / personas]\n  nav -->|specialised surface| ref[Reference -> link out]\n  skills --> pick[Select a skill card]\n  pick --> detail[what it does / when / produces / handoff / source link]\n  ref --> out{target exists?}\n  out -->|yes| surface([Open Docs Explorer / UI guide / audit / dreams])\n  out -->|no| miss[Link shown as 'not generated yet' - never a broken link]\n  search([Search/filter]) --> skills"
        }
      ],
      "sourceSha256": "a8753bab54f21bb987df9032becd79016980c60af68168e9e160bdb38aa407eb"
    },
    {
      "id": "spec-dreaming",
      "path": "docs/specs/dreaming-continuous-improvement.md",
      "title": "Dreaming — continuous-improvement consolidation, review, and cross-repo federation",
      "type": "spec",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "dreaming",
      "reviewBy": "2027-02-11",
      "reviewSuggested": [],
      "summary": "Specification for AI-Forward's dreaming capability: a /dream consolidation skill that mines the committed corpus (audit/change logs, defect-class register, captured mitigations, triggered markers) and emits an HTML review view of proposed learnings; a schedulable dream job; a promotion oracle that captures successful mitigations (error→red test→green, or human validation); a safe instance→class abstraction procedure; a fleet learnings store in the ai-forward repo; and an /apply-learnings push skill that reconciles approved learnings into target repos.",
      "tags": [
        "dreaming",
        "continuous-improvement",
        "consolidation",
        "federation",
        "promotion-oracle",
        "review-view"
      ],
      "links": [
        {
          "to": "kb-continuous-improvement-and-dreaming",
          "rel": "implements"
        },
        {
          "to": "defect-classes",
          "rel": "relates-to"
        },
        {
          "to": "audit-log",
          "rel": "relates-to"
        }
      ],
      "diagrams": [
        {
          "kind": "flowchart",
          "title": "User flows (happy + alternate + error + recovery)",
          "mermaid": "flowchart TD\n  open([Open dream view over file://]) --> load{dream-data.js present & valid?}\n  load -->|no/empty| empty[Empty state: 'No proposals in this dream' or 'Data missing — regenerate with /dream'] --> done1([Close])\n  load -->|yes| queue[Review queue, grouped by kind, highest-leverage first]\n  queue --> pick[Select a proposal]\n  pick --> inspect[Inspect evidence, provenance, control, boundary, scope]\n  inspect --> decide{Decision}\n  decide -->|Approve| mark[Mark approved]\n  decide -->|Edit| edit[Adjust control/boundary inline, then approve]\n  decide -->|Reject| rej[Mark rejected + optional reason]\n  decide -->|Defer| def[Mark deferred]\n  mark --> more{More proposals?}\n  edit --> more\n  rej --> more\n  def --> more\n  more -->|yes| pick\n  more -->|no| export[Export decisions]\n  export --> emit[[View emits decisions JSON + apply command]]\n  emit --> apply[Run dream.py apply-decisions file]\n  apply --> promote{Any approved & general?}\n  promote -->|yes| store[Promote to fleet learnings store in ai-forward]\n  promote -->|no| localonly[Repo-local learnings updated only]\n  store --> push([Later: /apply-learnings --repos ... reconciles into targets])\n  apply -->|malformed decisions file| aerr[Validation error: reject file, nothing written] --> export"
        }
      ],
      "sourceSha256": "3a1b4242dc83c313fbc9b3e14877e875e9e44eb3b5eeb59025efd5abd1b0a13d"
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
          "to": "design-coord-core-phase1",
          "rel": "documents"
        },
        {
          "to": "design-coord-enforcement-phase2",
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
      "sourceSha256": "5f9763bd812cd9ce960f788835c92cf73dc06fb0d0cbce93243618c9cc16dd42"
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
    },
    {
      "id": "surface-architecture-agent-coordination",
      "path": "docs/architecture-agent-coordination.html",
      "title": "Agent coordination — architecture",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact.",
      "artifactId": "architecture-agent-coordination"
    },
    {
      "id": "surface-specs-agent-coordination",
      "path": "docs/specs/agent-coordination.html",
      "title": "Agent coordination — specification",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact.",
      "artifactId": "spec-agent-coordination"
    },
    {
      "id": "surface-portal-index",
      "path": "docs/portal/index.html",
      "title": "AI-Forward — Documentation",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact."
    },
    {
      "id": "surface-mockups-documentation-portal",
      "path": "docs/mockups/documentation-portal.html",
      "title": "AI-Forward — Documentation Portal (mockup)",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact.",
      "artifactId": "mockup-documentation-portal"
    },
    {
      "id": "surface-knowledge-continuous-improvement-and-dreaming-overview",
      "path": "docs/knowledge/continuous-improvement-and-dreaming/overview.html",
      "title": "Continuous Improvement & Dreaming — techniques overview",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact."
    },
    {
      "id": "surface-dreams-drm-0002-index",
      "path": "docs/dreams/drm-0002/index.html",
      "title": "Dream Review",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact."
    },
    {
      "id": "surface-dreams-drm-0003-index",
      "path": "docs/dreams/drm-0003/index.html",
      "title": "Dream Review",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact."
    },
    {
      "id": "surface-dreams-drm-0004-index",
      "path": "docs/dreams/drm-0004/index.html",
      "title": "Dream Review",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact."
    },
    {
      "id": "surface-dreams-drm-0005-index",
      "path": "docs/dreams/drm-0005/index.html",
      "title": "Dream Review",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact."
    },
    {
      "id": "surface-mockups-dream-review",
      "path": "docs/mockups/dream-review.html",
      "title": "Dream Review — mockup",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact.",
      "artifactId": "mockup-dream-review"
    },
    {
      "id": "surface-backtest-optimize-graph-index",
      "path": "docs/backtest/optimize-graph/index.html",
      "title": "optimize-graph back-test — AI-Forward",
      "kind": "knowledge-tool",
      "description": "Open an interactive knowledge artifact.",
      "artifactId": "backtest-optimize-graph"
    }
  ],
  "graphSha256": "b1b756766ec775e42e678c5cd2dad2ed034836f9236e225cff3056ef6fa94a51"
};
