// Derived from artifact frontmatter by scripts/docs-graph.py — DO NOT hand-edit (frontmatter wins; see knowledge-visualization.md V2/V18).
window.DOCS_INDEX = {
  "project": "AI-Forward",
  "generated": "2026-06-27T15:10:56Z",
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
          "title": "Architecture: AI-Forward (pack source + live dogfood install)\n\n- **Status:** Accepted\n- **Tier:** N/A — this repository is a knowledge/tooling package, not an AI runtime system, so the LOA capability tiers (T0–T4, which allocate *inference* cost) do not apply here. The tier model is part of the pack's *payload*, not this repo's own runtime. `[Verified]` (no inference code in the repo).\n- **Driving context:** `README.md`, `CLAUDE.md`, `pack/OVERVIEW.md`\n- **Documented commit:** see `docs/_meta.json`\n\n## Context & constraints\n\nThis repository is **two things at once** (`README.md` §\"This repo is two things at once\"):\n\n1. **The canonical source** of the AI-Forward Pack — everything you edit to expand the pack lives under `pack/`. `[Verified: README.md, pack/]`\n2. **A live install of the pack** — the pack is installed into this same repo (`.claude/`, `docs/`) so the skills, agents, and knowledge are active in Claude Code *while you work on the pack itself*. Dogfooding: the pack is built using the pack. `[Verified: .claude/, CLAUDE.md]`\n\nThe load-bearing constraint that shapes the whole structure:\n\n> **`.claude/` and `docs/` are GENERATED from `pack/`** by `tools/sync-pack.ps1` and committed so a fresh clone has a working install with no setup. `pack/` is the single source of truth — never edit the generated copies directly; they are overwritten on the next sync. `[Verified: CLAUDE.md, tools/sync-pack.ps1]`\n\nConsequence for documentation (a finding surfaced by this run): the generated knowledge documents under `.claude/knowledge/` and `docs/ai-forward-pack/` carry **no YAML frontmatter** (they are vendored prose, not graph nodes). The Knowledge-Visualization graph model (V1–V18) therefore sees **zero artifacts** until frontmatter'd documentation (like this file) is added under `docs/`. See *Flagged risks* below. `[Verified: docs-graph.py inventory → \"artifacts\": 0]`\n\n## Archetype & rationale\n\nNo LOA system archetype (A–I) applies — those classify AI-integrated *runtime* systems. The applicable shape here is a classic **source → build → install → consumer** pipeline with a **dogfood loopback**: the install layer feeds back into the authoring experience (Claude Code reads `.claude/` while you edit `pack/`). `[Inferred from repo structure]`\n\n## Component map & boundaries\n\nThe major components and the real dependency edges between them (read from `tools/sync-pack.ps1`, `tools/package-pack.ps1`, and the directory layout):\n\n```mermaid\nflowchart TB\n  subgraph SRC[\"pack/ — canonical source (edit here)\"]\n    K[\"knowledge/*.md<br/>(reasoning spine + roster + foundation)\"]\n    C[\"commands/&lt;name&gt;/SKILL.md<br/>(the 10 skills)\"]\n    T[\"templates/*<br/>(artifacts each skill emits)\"]\n    A[\"adapters/<br/>(Claude Code + Copilot agents, INSTALL.md)\"]\n    SC[\"scripts/  ·  evals/  ·  ci/  ·  examples/\"]\n    PD[\"README · OVERVIEW · research-synthesis\"]\n  end\n\n  subgraph TOOLS[\"tools/ — build\"]\n    SYNC[\"sync-pack.ps1\"]\n    PKG[\"package-pack.ps1\"]\n  end\n\n  subgraph INSTALL[\".claude/ + docs/ — generated install (do not hand-edit)\"]\n    CK[\".claude/knowledge/*.md\"]\n    CS[\".claude/skills/*\"]\n    CA[\".claude/agents/*.md\"]\n    DP[\"docs/ai-forward-pack/<br/>templates + scripts + pack docs\"]\n    EXP[\"docs/index.html<br/>(Docs Explorer)\"]\n    IDX[\"docs/docs-index.js<br/>(accumulated graph index)\"]\n    ARCH[\"docs/architecture.md · index.md · _meta.json<br/>(this bundle)\"]\n  end\n\n  subgraph CONSUMERS[\"consumers\"]\n    CC[\"Claude Code / Copilot<br/>(read .claude/)\"]\n    WEBE[\"web/ai-forward-pack-explainer.html<br/>(interactive explainer)\"]\n    ZIP[\"dist/ai-forward-pack.zip\"]\n  end\n\n  K --> SYNC\n  C --> SYNC\n  T --> SYNC\n  A --> SYNC\n  SYNC --> CK & CS & CA & DP & EXP\n  C -. \"skills reference\" .-> CK\n  CA -. \"agents reference\" .-> CK\n  DP --> GRAPH[\"docs-graph.py<br/>(in docs/ai-forward-pack/scripts)\"]\n  GRAPH --> IDX\n  ARCH --> GRAPH\n  IDX --> EXP\n  CK --> CC\n  CS --> CC\n  CA --> CC\n  SRC --> PKG --> ZIP\n  CK -. \"derived content\" .-> WEBE\n```\n\nBoundaries that matter:\n- **Source ↔ install boundary** — crossed *only* by `tools/sync-pack.ps1`. Editing the install side directly is a contract violation (the next sync overwrites it). `[Verified: CLAUDE.md, sync-pack.ps1]`\n- **`sync-pack.ps1` write scope** — it writes only `.claude/{knowledge,skills,agents}`, `docs/ai-forward-pack/**`, and `docs/index.html`; it **intentionally does not touch** `docs/docs-index.js` (skills accumulate it) or other `docs/` root files. This is why this bundle (`docs/architecture.md`, `docs/index.md`, `docs/_meta.json`) and `web/ai-forward-pack-explainer.html` have a stable home that sync will not clobber. `[Verified: tools/sync-pack.ps1 lines 22, 92–98]`\n\n## Key flow — the sandbox / dogfood loop (sequence)\n\nThe authoring loop from `README.md` §\"Expanding the pack\", with the graph-refresh step `/document` adds:\n\n```mermaid\nsequenceDiagram\n  actor Dev as Author\n  participant Pack as pack/ (source)\n  participant Sync as tools/sync-pack.ps1\n  participant Install as .claude/ + docs/\n  participant CC as Claude Code (this repo)\n  participant Graph as docs-graph.py\n  participant Explorer as docs/index.html\n\n  Dev->>Pack: edit a knowledge doc / SKILL.md / persona / template\n  Dev->>Sync: pwsh tools/sync-pack.ps1\n  Sync->>Install: mirror knowledge, skills, agents, templates, scripts\n  Sync->>Install: regenerate docs/index.html from template\n  Note over Sync,Install: docs-index.js is NOT touched (accumulated separately)\n  Dev->>CC: try the change (regenerated skills/agents are now live)\n  CC-->>Dev: run a skill; dogfood the edit\n  Dev->>Graph: /document → docs-graph.py derive\n  Graph->>Install: write docs/docs-index.js from frontmatter\n  Graph->>Explorer: index loaded; hierarchy · graph · mind map · health render\n  Dev->>Pack: commit pack/ + .claude/ + docs/ together (lockstep)\n```\n\n`[Verified: README.md §\"Expanding the pack (the sandbox loop)\", sync-pack.ps1, docs-graph.py --help]`\n\n## Layered view (source → consumer)\n\nThe repo's own layering (distinct from the LOA *capability* tiers it ships as payload):\n\n```mermaid\nflowchart TB\n  subgraph L4[\"Consumer layer\"]\n    direction LR\n    cc[Claude Code / Copilot]:::c\n    ex[Docs Explorer + web explainer]:::c\n    z[dist/ zip for other repos]:::c\n  end\n  subgraph L3[\"Install layer (generated, committed)\"]\n    direction LR\n    claude[.claude/ knowledge·skills·agents]:::i\n    docs[docs/ pack-docs·scripts·templates·index]:::i\n  end\n  subgraph L2[\"Build layer\"]\n    direction LR\n    sync[sync-pack.ps1]:::b\n    pkg[package-pack.ps1]:::b\n  end\n  subgraph L1[\"Source layer (single source of truth)\"]\n    pack[pack/ knowledge·commands·templates·adapters·scripts]:::s\n  end\n  L1 --> L2 --> L3 --> L4\n  classDef s fill:#1d2b4d,stroke:#5a7cff,color:#dde6ff\n  classDef b fill:#13324a,stroke:#5ad1c7,color:#dffaf6\n  classDef i fill:#2a2440,stroke:#a98bff,color:#efeaff\n  classDef c fill:#163024,stroke:#56d364,color:#dcffe4\n```\n\nDependency direction points **up only** (source → build → install → consumer); no consumer writes back into source except through the human author editing `pack/`. `[Verified: tools/*.ps1]`\n\n## Domain model (class) — the UI Archetype Grammar\n\nThe most code-like structure in the repo is the **Archetype Grammar** (`ui-archetype-grammar.md` EBNF, G1–G16) and its catalog (`ui-archetype-catalog.md`). Documented here as a class model because it is the conceptual schema the experience and the codegen contract are built on:",
          "mermaid": "classDiagram\n  class Signature {\n    +Name name\n    +FacetList facets\n    +StyleHints? hints\n    +validate() conflicts\n    +roundTrip() bool  %% G10: identify AND generate\n  }\n  class Facet {\n    <<abstract>>\n    +String key\n  }\n  class SingleValuedFacet {\n    +Value value  %% Type, Arch, Layout, Density, Pacing, ...\n  }\n  class MultiValuedFacet {\n    +Value[] values  %% Nav, Input, Feedback, Motion, A11y (joined with +)\n  }\n  class StyleHints {\n    +String[] hints  %% bounded NL decoration, applied last\n  }\n  class Archetype {\n    +String id          %% A1..F2\n    +String name\n    +Exemplar[] exemplars\n    +Signature canonical\n    +String codegenDescriptor\n  }\n  Signature \"1\" o-- \"4..*\" Facet : composes\n  Facet <|-- SingleValuedFacet\n  Facet <|-- MultiValuedFacet\n  Signature \"0..1\" *-- \"1\" StyleHints : decorated by\n  Archetype \"1\" *-- \"1\" Signature : canonical\n  Archetype \"1\" o-- \"1..*\" Exemplar\n  note for Signature \"G4: MUST carry Type, Arch, Layout, Pacing.\\nG1: always composed with a concrete U1–U20 / S1–S18 spec.\""
        }
      ]
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
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
      "diagrams": []
    },
    {
      "id": "privacy-review",
      "path": "docs/security/privacy-review.md",
      "title": "Privacy Review",
      "type": "privacy-review",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-12-11",
      "reviewSuggested": [],
      "summary": "Repo-level privacy posture for the pack-evolution tooling: the CLI and doctor touch no personal data; project memory may incidentally record handles/names (no special-category data, mitigated by the scrub); the scrub is itself a privacy control.",
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
        }
      ],
      "diagrams": []
    },
    {
      "id": "threat-model",
      "path": "docs/security/threat-model.md",
      "title": "Threat Model",
      "type": "threat-model",
      "status": "accepted",
      "owner": "@timianmalloo",
      "phase": "pack-evolution",
      "reviewBy": "2026-12-11",
      "reviewSuggested": [],
      "summary": "Repo-level security posture for the pack-evolution tooling: the only real trust boundary is the scrub reading files that may contain secrets/PII; the CLI, doctor, and memory ledger are local, read-mostly, no-network components with no privilege boundary.",
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
        }
      ],
      "diagrams": []
    }
  ]
};
