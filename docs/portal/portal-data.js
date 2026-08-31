window.PORTAL_DATA = {
  "meta": {
    "counts": {
      "skills": 24,
      "personas": 23,
      "knowledge": 38,
      "templates": 28,
      "scripts": 18
    },
    "whatIs": "AI-Forward is a committed Markdown methodology pack that installs into a repo so Claude Code and GitHub Copilot direct work with a shared reasoning spine, adversarial persona review, and a library of workflow skills - nothing runs as a service; everything is versioned files and stdlib scripts.",
    "skillCount": 24,
    "precisionNote": "This portal is the high-level, user-facing front door. It is a LENS over the repo's core knowledge, not a copy of it: the Foundations, UI, and Architecture sections list and link the structured artifacts (knowledge docs, ADRs, specs, designs) with derived summaries, while the artifacts themselves stay exactly where they are - as structured, individually-owned Markdown. Nothing here is hand-typed content that must be kept in sync; it is generated from those sources, so it cannot drift."
  },
  "sections": [
    {
      "id": "start",
      "n": "1",
      "title": "Getting Started"
    },
    {
      "id": "caps",
      "n": "2",
      "title": "Capabilities"
    },
    {
      "id": "skills",
      "n": "3",
      "title": "The 24 Skills"
    },
    {
      "id": "foundations",
      "n": "4",
      "title": "Foundations"
    },
    {
      "id": "ui",
      "n": "5",
      "title": "UI & Design"
    },
    {
      "id": "architecture",
      "n": "6",
      "title": "Architecture"
    },
    {
      "id": "systems",
      "n": "7",
      "title": "Systems"
    },
    {
      "id": "graph",
      "n": "8",
      "title": "Graph"
    },
    {
      "id": "ref",
      "n": "9",
      "title": "Reference"
    }
  ],
  "gettingStarted": [
    {
      "h": "Understand what it is",
      "p": "A methodology pack, not a runtime. It ships knowledge docs (the reasoning constitution), persona lenses (adversarial review), and skills (workflows), plus stdlib scripts for the knowledge graph, audit log, and dreaming. Everything is committed files you can read.",
      "cmd": null
    },
    {
      "h": "Install it into a repo",
      "p": "Add the pack to a new or existing local repo. From an ai-forward clone, run the installer skill; a brownfield repo also runs /adopt to bootstrap its knowledge graph.",
      "cmd": "/addpacktorepo   (or /adopt for an existing repo)"
    },
    {
      "h": "Know how skills are invoked",
      "p": "In Claude Code, skills apply by description (.claude/skills/). In GitHub Copilot, they are prompts (.github/prompts/). Both surfaces read the same knowledge docs and personas.",
      "cmd": null
    },
    {
      "h": "Run your first skill",
      "p": "Start where the loop starts: collect the domain knowledge your work rests on, then specify. The pack grounds every skill in what the repo already knows.",
      "cmd": "/collectknowledge   then   /specify"
    },
    {
      "h": "Keep the repo learning",
      "p": "As you work, the audit log captures every run; run /dream to consolidate learnings into reviewable improvements, and /apply-learnings to share them across your repos.",
      "cmd": "/dream"
    }
  ],
  "capabilities": [
    {
      "h": "Reason with rigor",
      "p": "A Rigor Protocol (map -> interrogate -> ground -> disconfirm -> converge) and a No-Guessing rule under every non-trivial task."
    },
    {
      "h": "Bound and optimize every turn",
      "p": "Each turn opens with a written goal-state and stop point (the two-step front matter, CT19-CT24), then plans its work as an execution graph - critical path first, every loop given a termination variant, cost recorded against delivery."
    },
    {
      "h": "Review adversarially",
      "p": "Persona lenses author in Peer Mode and attack in Adversary Mode; the author never clears its own hard veto."
    },
    {
      "h": "Specify before building",
      "p": "One spec, three layers - Functional, UX, UI - with a conceptual data model taken first."
    },
    {
      "h": "Design interfaces to a floor",
      "p": "Seven UI standards, an archetype grammar, a deterministic craft detector, and a visual-assets pipeline."
    },
    {
      "h": "Build under TDD",
      "p": "Red->green->refactor paired with the Test Architect; a triggered test directive is applied, not chosen."
    },
    {
      "h": "Remember across sessions",
      "p": "A committed knowledge graph, an append-only audit & change log, and dreaming - offline consolidation of learnings."
    }
  ],
  "skills": [
    {
      "group": "Collect & frame",
      "items": [
        {
          "cmd": "/adddomainexperts",
          "desc": "Identify this project's domain and add domain-expert personas (peer + adversary) tailored to it, wiring in existing Claude domain skills and updating every roster artifact locally.",
          "when": "The domain needs subject-matter lenses beyond the general engineering ones.",
          "produces": "docs/domain-experts.md",
          "handoff": "/specify"
        },
        {
          "cmd": "/collectknowledge",
          "desc": "Before design, run deep sourced research on the project's domain and problem and save it as a confidence-labeled markdown knowledge base in docs/knowledge/, bootstrapping domain expertise.",
          "when": "Starting in an unfamiliar or high-stakes domain.",
          "produces": "docs/knowledge/<topic>/",
          "handoff": "/adddomainexperts -> /specify"
        },
        {
          "cmd": "/specify",
          "desc": "Turn a prompt or idea into a crisp, testable product specification with acceptance criteria.",
          "when": "Any non-trivial feature, before architecture.",
          "produces": "docs/specs/<feature>.md",
          "handoff": "/define-architecture or /design-slice"
        }
      ]
    },
    {
      "group": "Architect & design",
      "items": [
        {
          "cmd": "/define-architecture",
          "desc": "Turn a spec into a top-level architecture with ADRs, grounded in established contracts.",
          "when": "New systems or load-bearing architecture.",
          "produces": "docs/architecture.md + ADRs",
          "handoff": "/design-slice"
        },
        {
          "cmd": "/design-slice",
          "desc": "Turn a spec/component into a detailed component design with a test plan.",
          "when": "A feature within an existing architecture.",
          "produces": "docs/design/<component>.md",
          "handoff": "/implement"
        },
        {
          "cmd": "/ui-design",
          "desc": "Create, review or elevate a user interface to a professional standard — direction brief, design language, reviewable mockup, rubric critique.",
          "when": "Any user-facing surface to create, review, or elevate.",
          "produces": "docs/mockups/ + DESIGN.md",
          "handoff": "/design-slice or /implement"
        }
      ]
    },
    {
      "group": "Build & verify",
      "items": [
        {
          "cmd": "/document",
          "desc": "Generate/maintain the documentation bundle — JavaDoc-style API reference plus sequence, class, layered-architecture, and component diagrams, in committed markdown and a self-contained browsable HTML view; keep it fresh after commit.",
          "when": "After a feature lands, before a release.",
          "produces": "docs bundle + diagrams",
          "handoff": "-"
        },
        {
          "cmd": "/implement",
          "desc": "Turn a design into tested code with a Proof Pack, via TDD pairing.",
          "when": "Building the thing.",
          "produces": "code + tests + Proof Pack",
          "handoff": "ship or /investigate"
        },
        {
          "cmd": "/investigate",
          "desc": "Turn a defect into a verified root cause and a systemic go-forward fix.",
          "when": "Something is broken or behaving wrong.",
          "produces": "investigation report + repair plan",
          "handoff": "/implement"
        }
      ]
    },
    {
      "group": "Continuous improvement",
      "items": [
        {
          "cmd": "/apply-learnings",
          "desc": "Push approved, generalised fleet learnings (promoted from /dream into the ai-forward learnings/ store) into one or more target repos, reconciling each against that repo's existing register so nothing is duplicated or contradicted. Produces a reviewable plan per repo — never merges, never executes.",
          "when": "Sharing a learning across the fleet.",
          "produces": "learnings/plans/",
          "handoff": "review + apply"
        },
        {
          "cmd": "/code-hygiene",
          "desc": "Find and quantify violations of the coding guidelines (dead code, commented-out code, anti-patterns) as a measured backlog with lines-of-code and percent-of-codebase per class; `review` yields the analysis, `fix` builds a TDD-guarded, git-labelled remediation strategy that introduces no regressions.",
          "when": "Holding a codebase to the coding guidelines - finding and removing dead code, commented-out code, and anti-patterns.",
          "produces": "docs/hygiene/backlog.md (+ remediation-plan.md on fix)",
          "handoff": "/implement"
        },
        {
          "cmd": "/dream",
          "desc": "Run an offline, reviewable consolidation pass over this repo's committed corpus (audit & change logs, defect-class register, captured mitigations, triggered simplify/assume markers) and produce a dream — proposed learnings with controls, rendered as an HTML review view you approve/edit/reject/defer, then promote. The \"asleep half\" of continuous improvement.",
          "when": "Periodically, to compound learnings across sessions.",
          "produces": "docs/dreams/ + HTML review",
          "handoff": "/apply-learnings"
        }
      ]
    },
    {
      "group": "Lifecycle & pack",
      "items": [
        {
          "cmd": "/addpacktorepo",
          "desc": "Add the AI-Forward Pack to a local repository at a given path — read the target repo before writing anything, apply the full deployment map from INSTALL.md, produce a table of every artifact installed and what it does, point to the pack explainer, and offer to commit and push.",
          "when": "Adding the pack to a new repo.",
          "produces": "installed pack + summary",
          "handoff": "/adopt"
        },
        {
          "cmd": "/adopt",
          "desc": "Bootstrap the knowledge graph in an existing (brownfield) repository — recover, record, and plan; never fabricate.",
          "when": "Once per legacy repo, right after dropping in the pack.",
          "produces": "initial graph + adoption plan",
          "handoff": "/document"
        },
        {
          "cmd": "/extendaibundle",
          "desc": "Extend the AI-Forward pack itself from a prose prompt — add a skill, knowledge doc, template, or script via collect → specify → design → implement, scaffolded by tools/new-capability.py and proven by tools/verify-bundle.ps1, with zero drift and fit for both tools.",
          "when": "Adding a skill, knowledge doc, template, or script to the pack.",
          "produces": "new pack capability",
          "handoff": "-"
        },
        {
          "cmd": "/forensicreview",
          "desc": "Perform a deep evidence-based architecture, design, implementation, and documentation review of an existing repository, then produce a prioritized risk and remediation backlog.",
          "when": "Assessing an unfamiliar or drifting repo.",
          "produces": "risk & remediation backlog",
          "handoff": "/investigate"
        },
        {
          "cmd": "/migrate",
          "desc": "Characterization-first migrations and large refactors — pin behavior, compute blast radius from the graph, migrate in vertical increments, prove equivalence.",
          "when": "SDK bumps, library swaps, platform moves.",
          "produces": "migrated code + equivalence proof",
          "handoff": "-"
        },
        {
          "cmd": "/updatepack",
          "desc": "Update an installed AI-Forward Pack to the latest revision from a local ai-forward clone — diff revisions in INSTALL.md, apply only the changed artifacts per the changelog, and summarise every action in a table before offering to commit and push.",
          "when": "Pulling pack updates (the federation pull path).",
          "produces": "updated install",
          "handoff": "-"
        }
      ]
    },
    {
      "group": "Utilities & lenses",
      "items": [
        {
          "cmd": "/also",
          "desc": "Append a late addition to the prior prompt without derailing the work in flight; captured now, considered after the current reasoning and work complete, as refined context or an appended task.",
          "when": "Adding a late addition to the prior prompt without derailing work in flight.",
          "produces": "-",
          "handoff": "-"
        },
        {
          "cmd": "/auditlog",
          "desc": "The CLI lens over the project's durable audit & change log — list the last N actions, search by session/date/keyword, copy or re-run a past prompt, toggle to the meaningful-change timeline, or open the interactive viewer.",
          "when": "Recalling what was done or decided across sessions.",
          "produces": "-",
          "handoff": "-"
        },
        {
          "cmd": "/prompts",
          "desc": "Browse your logged prompts as a stack (newest on top) and reuse one — ↑/↓ move, → expand, ← collapse, Enter copies it for paste-and-edit. Utility skill over the stdlib prompt-log engine.",
          "when": "Reusing a prior prompt.",
          "produces": "-",
          "handoff": "-"
        },
        {
          "cmd": "/searchprompts",
          "desc": "Search your logged prompts by freeform text and reuse a match — the same arrow-navigable expand/collapse stack as /prompts, pre-filtered to prompts containing all your terms. Utility skill over the stdlib prompt-log engine.",
          "when": "Finding a specific prior prompt.",
          "produces": "-",
          "handoff": "-"
        },
        {
          "cmd": "/visualize",
          "desc": "Generate, curate and commit the visual assets a site shows — imagery, personas and cinematic motion — from a configured backend, under the ui-visual-assets guardrails.",
          "when": "Making a surface look produced, not templated.",
          "produces": "docs/assets/ + manifest",
          "handoff": "/ui-design"
        }
      ]
    },
    {
      "group": "Delivery",
      "items": [
        {
          "cmd": "/optimize-graph",
          "desc": "Analyse a prompt BEFORE executing it and produce an optimized execution graph — dependencies made explicit, incidental ordering removed, the critical path shortened, independent work parallelised under a bounded fan-out contract, nodes collapsed or promoted to the right granularity, every loop given a termination variant, and cost recorded against delivery. It may only increase completeness, rigor and determinism, never trade them.",
          "when": "Before executing any prompt beyond two steps, or one with a loop, a fan-out, or a triggered gate.",
          "produces": "docs/plans/ + a cost-vs-delivery ledger",
          "handoff": "the workflow skill it wraps, then /dream"
        }
      ]
    }
  ],
  "foundations": {
    "intro": "The reasoning constitution and engineering guidance every skill answers to. These are the always-loaded knowledge docs - the 'why' beneath the 'what'. They stay structured as individual directives; this is the map. Each links to its source.",
    "groups": [
      {
        "group": "Reasoning constitution",
        "items": [
          {
            "name": "agent-body-of-knowledge",
            "title": "Agent Body of Knowledge",
            "summary": "This document is the constitution for coding agents working in this codebase. It governs how the agent thinks, researches, and decides — not how the code is formatted (see the C# Coding Style Guide), how tests are selected and judged (see the Testing...",
            "path": "../../pack/knowledge/agent-body-of-knowledge.md"
          },
          {
            "name": "agent-rules-of-the-road",
            "title": "Agent Rules of the Road",
            "summary": "This is the executable layer. The Body of Knowledge (BoK) sets the philosophy; the Persona Catalog supplies the reviewers; this document is what the agent does, in order, every session. It is written to be deployed verbatim as AGENTS.md (or...",
            "path": "../../pack/knowledge/agent-rules-of-the-road.md"
          },
          {
            "name": "end-to-end-integrity",
            "title": "End-to-End Integrity — the standing method",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/end-to-end-integrity.md"
          },
          {
            "name": "no-guessing-protocol",
            "title": "The No-Guessing Protocol",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/no-guessing-protocol.md"
          },
          {
            "name": "rigor-protocol",
            "title": "The Rigor Protocol",
            "summary": "This document exists to defeat one failure mode above all others: the rush to a plausible answer. A language model is built to emit the most probable next token, and the most probable answer is often the most plausible-sounding one — which is not the same as...",
            "path": "../../pack/knowledge/rigor-protocol.md"
          },
          {
            "name": "spike-protocol",
            "title": "The Spike Protocol",
            "summary": "A spike is a small, time-boxed, throwaway investigation whose only purpose is to convert an unfamiliar contract from a guess into established knowledge before any design or implementation depends on it. It is the direct antidote to the two most expensive AI...",
            "path": "../../pack/knowledge/spike-protocol.md"
          }
        ]
      },
      {
        "group": "Discipline & optimization",
        "items": [
          {
            "name": "communication-and-task-discipline",
            "title": "Communication & Task Discipline",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/communication-and-task-discipline.md"
          },
          {
            "name": "execution-graph-optimization",
            "title": "Execution-Graph Optimization",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/execution-graph-optimization.md"
          },
          {
            "name": "instrumentation-over-inference",
            "title": "Instrumentation over Inference",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/instrumentation-over-inference.md"
          },
          {
            "name": "session-worktree-discipline",
            "title": "Session Worktree Discipline",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/session-worktree-discipline.md"
          }
        ]
      },
      {
        "group": "Specification & domain",
        "items": [
          {
            "name": "domain-and-data-modelling",
            "title": "Domain & Data Modelling Standard",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/domain-and-data-modelling.md"
          },
          {
            "name": "specification-standards",
            "title": "Specification Standards — functional, UX, and UI",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/specification-standards.md"
          }
        ]
      },
      {
        "group": "Personas & review",
        "items": [
          {
            "name": "agent-persona-catalog",
            "title": "Agent Persona Catalog",
            "summary": "These personas exist to do one thing: find the flaw in a design before it becomes code. They are the operational form of Body of Knowledge §II.3 (adversarial validation precedes commitment) and LOA principle P6. Each persona is a world-class expert in their...",
            "path": "../../pack/knowledge/agent-persona-catalog.md"
          },
          {
            "name": "collaborative-personas",
            "title": "Collaborating Peers & the Dual-Mode Operating Model",
            "summary": "The Agent Persona Catalog is, by its own statement, a set of design-time adversaries: eleven world-class lenses whose job is \"to find the flaw in a design before it becomes code.\" That is exactly half of a swarm. A flaw-finding council can review a proposal,...",
            "path": "../../pack/knowledge/collaborative-personas.md"
          },
          {
            "name": "persona-audit",
            "title": "Persona Audit & Operating Standard",
            "summary": "The roster under audit is fourteen lenses: the eleven adversaries of the Agent Persona Catalog (Enterprise Architect, Test Architect, Security & Identity Architect, Tech Lead, SRE & Systems Diagnostician, Distributed Systems Architect, the C#/Rust/Python...",
            "path": "../../pack/knowledge/persona-audit.md"
          },
          {
            "name": "persona-cards",
            "title": "Persona Cards — the roster in one schema",
            "summary": "This is the retrofit that makes the whole catalog uniform. The Agent Persona Catalog gives each adversary a Lens, an Interrogation set, its Catches, and a Veto; this document keeps those (the full interrogation sets stay in the Catalog — cards point to them...",
            "path": "../../pack/knowledge/persona-cards.md"
          }
        ]
      },
      {
        "group": "Architecture & engineering",
        "items": [
          {
            "name": "ai-commercial-models",
            "title": "AI Commercial, Cost & Billing Models",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/ai-commercial-models.md"
          },
          {
            "name": "ci-and-test-efficiency",
            "title": "CI & Test Execution Efficiency — best coverage at minimum time and cost",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/ci-and-test-efficiency.md"
          },
          {
            "name": "engineering-governance",
            "title": "Engineering Governance — the SDLC lenses the craft docs don't cover",
            "summary": "The Body of Knowledge governs reasoning, the Style Guide governs C#, and LOA governs AI-integrated architecture. This document governs the software-development lifecycle concerns that sit around the code: the non-functional requirements, governance, and...",
            "path": "../../pack/knowledge/engineering-governance.md"
          },
          {
            "name": "layered-optimized-architecture",
            "title": "Layered Optimized Architecture for AI-Integrated Systems",
            "summary": "---",
            "path": "../../pack/knowledge/layered-optimized-architecture.md"
          },
          {
            "name": "observability-and-instrumentation",
            "title": "Observability & Instrumentation Standard",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/observability-and-instrumentation.md"
          },
          {
            "name": "solution-selection-ladder",
            "title": "The Solution-Selection Ladder",
            "summary": "The pack already has the value — The Simplifier persona (\"the simplest thing that is still correct\"), and the Gratuitous Dependency and Cargo-Cult Pattern anti-patterns (BoK Part VIII). What it lacked was the procedure: an ordered algorithm the author climbs...",
            "path": "../../pack/knowledge/solution-selection-ladder.md"
          },
          {
            "name": "testing-strategy",
            "title": "Testing Strategy for AI Coding Agents",
            "summary": "This file governs any agent that writes or modifies code in this repository. It is the testing companion to the Body of Knowledge: the BoK says correctness must be demonstrated; this file defines the test selection and quality bar used to demonstrate it.",
            "path": "../../pack/knowledge/testing-strategy.md"
          }
        ]
      },
      {
        "group": "Coding style",
        "items": [
          {
            "name": "csharp-style-guide",
            "title": "C# Coding Style Guide",
            "summary": "A specification for writing C# that is legible, intentional, and durable. The guide is opinionated; defaults exist so reviewers can spend energy on design, not formatting.",
            "path": "../../pack/knowledge/csharp-style-guide.md"
          }
        ]
      },
      {
        "group": "Continuous improvement & memory",
        "items": [
          {
            "name": "audit-and-change-log",
            "title": "Audit & Change Log Standard",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/audit-and-change-log.md"
          },
          {
            "name": "code-knowledge-graph",
            "title": "The Code Knowledge Graph — composing Graphify with the pack",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/code-knowledge-graph.md"
          },
          {
            "name": "continuous-improvement",
            "title": "Continuous Improvement — the defect-class discipline",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/continuous-improvement.md"
          },
          {
            "name": "knowledge-visualization",
            "title": "Knowledge Visualization & Docs Explorer Standard",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/knowledge-visualization.md"
          },
          {
            "name": "obsidian-lens",
            "title": "The Obsidian Lens — graph insight over the knowledge base",
            "summary": "Normative keywords (MUST, SHOULD, MAY, MUST NOT) follow RFC 2119.",
            "path": "../../pack/knowledge/obsidian-lens.md"
          },
          {
            "name": "project-memory-and-obsidian",
            "title": "Project Memory & Continuity (with the Obsidian lens)",
            "summary": "Normative keywords (MUST, SHOULD, MAY) follow RFC 2119.",
            "path": "../../pack/knowledge/project-memory-and-obsidian.md"
          },
          {
            "name": "responsible-ai-policy",
            "title": "Responsible AI Policy",
            "summary": "---",
            "path": "../../pack/knowledge/responsible-ai-policy.md"
          }
        ]
      }
    ]
  },
  "ui": {
    "intro": "The pack treats UI as a first-class engineering surface with a floor, not an afterthought. Seven composable standards, an archetype grammar that makes generated UI deterministic in kind, a deterministic craft detector, and a governed generated-asset pipeline.",
    "standards": [
      {
        "n": "ui-interaction-design (U1-U20)",
        "d": "The floor: design tokens, complete component states (incl. empty/loading/error), motion, real copy, WCAG 2.2 AA, performance budget, and HAX + Shape-of-AI patterns for AI UIs."
      },
      {
        "n": "ui-design-craft (DX1-DX25)",
        "d": "The craft: direction before pixels, the generic-AI-look tells, the fidelity ladder, the review harness, and the critique rubric."
      },
      {
        "n": "ui-archetype-grammar + catalog",
        "d": "Selects the UI's kind (routing/temporal/data archetype) as a determinism control, then composes down into tokens and states."
      },
      {
        "n": "technical-ui-design (TQ1-TQ12)",
        "d": "Expert/quantitative surfaces: numeric legibility, perceptually-uniform colormaps (never jet), uncertainty-first output, provenance, reactive recompute."
      },
      {
        "n": "ui-craft-detection (CD1-CD20)",
        "d": "The deterministic 59-rule detector that enforces token discipline outward against the built source - the control beneath the craft."
      },
      {
        "n": "ui-visual-assets (VA1-VA22)",
        "d": "The generated-imagery pipeline: never generate the interface itself; generate once, download, optimize, commit; mood never structure."
      },
      {
        "n": "specification-standards (S1-S10)",
        "d": "The three spec layers (Functional/UX/UI) and their bottom-up dependency - the UX layer gates the Surface."
      }
    ],
    "stages": "The /ui-design workflow runs: direction brief (words before pixels) -> build the design language (DESIGN.md) -> produce a self-contained reviewable mockup that renders the hard states -> rubric critique (structure before surface) -> a ranked plan. Where each artifact lands: DESIGN.md at the repo root, mockups under docs/mockups/, reviews under docs/reviews/.",
    "guideLink": "../ui-guide.html",
    "examplesIntro": "Beyond the standards, the pack ships concrete UX/UI examples: self-contained reviewable mockups that render the hard states, the project design language (DESIGN.md), and design-language exemplars adapted from real products. Learn the craft from the artifacts, not just the rules.",
    "examples": [
      {
        "title": "Documentation Portal — mockup",
        "summary": "Self-contained, dependency-free high-fidelity mockup of the Documentation Portal — the DocsPortal (Content Portal / HolyGrail reading layout) front door: persistent sidebar nav over six sections (Getting Started · Capabilities · The 21 Skills · UI...",
        "path": "../mockups/documentation-portal.html"
      },
      {
        "title": "Dream Review — mockup",
        "summary": "Self-contained, dependency-free high-fidelity mockup of the Dream Review view — the Master-Detail approval queue the maintainer uses to review a dream's proposals (evidence, provenance, confidence, proposed control, federation scope) and...",
        "path": "../mockups/dream-review.html"
      }
    ]
  },
  "architecture": {
    "intro": "How the repo is shaped and why. The architecture of record, the decisions (ADRs) with their rationale and rejected options, the specifications that govern each feature, and the component designs. All carry frontmatter and live in the knowledge graph; this section is the reading order. Architecture *guidance* (the Layered-Optimized-Architecture for AI-integrated systems) is a foundation - see Foundations.",
    "groups": [
      {
        "group": "Architecture of record",
        "items": [
          {
            "title": "Dreaming subsystem — architecture",
            "summary": "Subsystem architecture for AI-Forward's dreaming capability — the offline consolidation pipeline (light/REM/deep) over the committed corpus, the HTML review/approval surface, the promotion oracle, the safe instance→class abstraction, the fleet learnings...",
            "path": "../../docs/architecture-dreaming.md"
          },
          {
            "title": "AI-Forward — Architecture Overview",
            "summary": "The architecture of record for this repository: a dual-purpose repo that is both the canonical SOURCE of the AI-Forward Pack (pack/) and a live INSTALL of it (.claude/, docs/), kept in lockstep by tools/sync-pack.ps1. Includes the four diagram families and...",
            "path": "../../docs/architecture.md"
          }
        ]
      },
      {
        "group": "Decisions (ADRs)",
        "items": [
          {
            "title": "ADR-0001: Use a versioned supplemental source-corpus registry",
            "summary": "Keeps frontmatter-bearing docs as the authoritative project graph while admitting canonical pack knowledge through a separate, versioned supplemental source-corpus registry. Generated Claude and Copilot wrappers remain projections, never parallel graph...",
            "path": "../../docs/adr/0001-grounding-source-corpus-registry.md"
          },
          {
            "title": "ADR-0002: Fleet learnings store in ai-forward; append-only facts + slug-keyed learnings; two federation paths",
            "summary": "The fleet learnings store lives in the ai-forward repo; corpus/oracle records are append-only facts and a Learning is a slug-keyed dimension whose instances are append-only; general classes federate two ways — a push skill (/apply-learnings) and a pull path...",
            "path": "../../docs/adr/0002-fleet-learnings-store.md"
          },
          {
            "title": "ADR-0003: The promotion oracle is captured successful mitigations (red→green test or human validation)",
            "summary": "The oracle for 'the fix worked' is a captured MitigationRecord whose verification is either a red-observed→green test pair or an explicit human validation; a fix with neither is 'unverified' and is never mined as a successful mitigation.",
            "path": "../../docs/adr/0003-promotion-oracle.md"
          },
          {
            "title": "ADR-0004: Safe instance→class abstraction — deterministic strip, model name, generalisation guards, human gate",
            "summary": "Defines the safe instance→class abstraction: deterministically strip specifics + PII, model-name the shape, enforce five generalisation guards (evidence threshold, falsifiable control, boundary statement, retained provenance, no PII across the boundary), and...",
            "path": "../../docs/adr/0004-instance-to-class-abstraction.md"
          },
          {
            "title": "ADR-0005: Ship a stdlib deterministic harness; the model call is an injected boundary owned by the runner; human-gate, no auto-merge",
            "summary": "The pack ships a stdlib-only deterministic harness (dream.py) + prompts; the one model call per phase is an injected boundary the runner (claude-cowork / OpenClaw / Claude Dreams / a skill session) owns; every durable write and every cross-repo change passes...",
            "path": "../../docs/adr/0005-harness-runner-boundary.md"
          },
          {
            "title": "ADR-0006: The Dream Manifest — a learnings×repos targeting/record layer for federation, composed in a UI, consumed by apply-learnings --manifest, local-only by default",
            "summary": "Federation had a distribution mechanism (apply-learnings push -> per-repo plans) but no targeting/record layer: which learnings go to which repos, and what happened when they did. The Dream Manifest is that layer — a learnings×repos assignment matrix...",
            "path": "../../docs/adr/0006-dream-manifest.md"
          },
          {
            "title": "ADR-0007: A git-tracked append-only record folded on demand — no daemon, no database",
            "summary": "Coordination state lives in an append-only JSONL record, one file per session, git-tracked, and every piece of state is a fold over it. The daemon and the SQLite read model the draft proposed are both cut, because a measured full fold of a 10,000-event record...",
            "path": "../../docs/adr/0007-coordination-substrate.md"
          },
          {
            "title": "ADR-0008: Identifiers come from a non-coordinating stdlib scheme — not uuid7, and not branch scanning",
            "summary": "Shared-register identifiers are issued from a stdlib-only, time-ordered, non-coordinating scheme — 48 bits of millisecond timestamp plus 80 bits from os.urandom, Crockford base32. uuid.uuid7 is rejected because it is absent on the installed 3.12 interpreter...",
            "path": "../../docs/adr/0008-non-coordinating-allocation.md"
          },
          {
            "title": "ADR-0009: Artifact class decides the mechanism — derived artifacts are regenerated by a merge driver, never leased",
            "summary": "Every path pattern is classified authored / derived / register / hotspot, and the class decides the coordination mechanism entirely. Derived artifacts — which are the six busiest files in the measured repository — are resolved by a .gitattributes merge driver...",
            "path": "../../docs/adr/0009-artifact-class-and-derived-merge.md"
          },
          {
            "title": "ADR-0010: Enforce at the harness edit boundary where it exists, at the commit boundary always — and fail to ask, never to allow",
            "summary": "A PreToolUse hook returning permissionDecision deny refuses an unleased edit before it happens; the pre-commit boundary is the universal floor no settings key can remove. Every indeterminate path returns ask with a reason beginning NOT CHECKED. The hook runs...",
            "path": "../../docs/adr/0010-enforcement-topology.md"
          },
          {
            "title": "ADR-0011: Cross-agent content is untrusted data — the projection ships only after its rendering rules exist",
            "summary": "The projection renders text authored by one agent's model into another agent's context, which the hook schema confirms is a live injection channel. Cross-agent content is therefore treated as data with no instruction authority, and the delivery order is...",
            "path": "../../docs/adr/0011-projection-trust-boundary.md"
          },
          {
            "title": "ADR-0012: Compose the mechanisms that already exist — the harness ships two of them, and the fleet ships three more",
            "summary": "The F8 reconciliation the spec made a condition of pass. Two of the four failure modes are already partly addressed by mechanisms shipped in the harness itself, and three more by scripts in TheTerrace; each is adopted, superseded, or retired explicitly. Also...",
            "path": "../../docs/adr/0012-reuse-existing-mechanisms.md"
          }
        ]
      },
      {
        "group": "Specifications",
        "items": [
          {
            "title": "Agent coordination — shared context and explicit coordination across worktrees and agents",
            "summary": "Specification for a repo-local, model-agnostic coordination layer that lets several agents and worktrees work one repository at once without losing work or time. Grounded in measured evidence from TheTerrace, HealthWatch and Meridian, it targets four distinct...",
            "path": "../../docs/specs/agent-coordination.md"
          },
          {
            "title": "Spec - /collaborate skill proposal",
            "summary": "Proposal for a future /collaborate skill that starts a cross-agent collaboration session by creating or entering a worktree, registering the session, scaffolding or updating the session contract, claiming the first files, and printing the collaboration checks...",
            "path": "../../docs/specs/collaborate-skill.md"
          },
          {
            "title": "Rename /design to /design-slice — Specification",
            "summary": "Specification for renaming AI-Forward's detailed component-design workflow from /design to /design-slice. The rename avoids a generic skill-name collision while preserving the workflow's meaning and updating generated Claude/Copilot pack surfaces.",
            "path": "../../docs/specs/design-slice-rename.md"
          },
          {
            "title": "Documentation Portal — a derived, self-maintaining interactive front door",
            "summary": "Specification for a single, polished, interactive HTML documentation portal that is the front door to the AI-Forward repo — a capabilities overview, concrete reference for all 21 skills, an in-depth UI-capabilities section, and an explicit getting-started...",
            "path": "../../docs/specs/documentation-portal.md"
          },
          {
            "title": "Dreaming — continuous-improvement consolidation, review, and cross-repo federation",
            "summary": "Specification for AI-Forward's dreaming capability: a /dream consolidation skill that mines the committed corpus (audit/change logs, defect-class register, captured mitigations, triggered markers) and emits an HTML review view of proposed learnings; a...",
            "path": "../../docs/specs/dreaming-continuous-improvement.md"
          },
          {
            "title": "Native app UI skill extension — Specification",
            "summary": "Specification for extending the AI-Forward UI skills so WPF, WinUI, Avalonia and other native client applications receive the same rigorous UX/UI reasoning as web surfaces. The spec defines the required native medium declaration, native proof pack,...",
            "path": "../../docs/specs/native-app-ui-skill-extension.md"
          }
        ]
      },
      {
        "group": "Component designs",
        "items": [
          {
            "title": "Design — aiforward CLI (suggestion 1)",
            "summary": "A single stdlib-only Python developer CLI (tools/aiforward.py) that is a thin Façade dispatcher over the pack's existing scripts (sync, verify, check, new, doctor, graph, scrub) — one memorable entry point with --help, no new runtime dependency.",
            "path": "../../docs/design/aiforward-cli.md"
          },
          {
            "title": "Design - coord collaboration mode, Phase 4",
            "summary": "Phase-4 collaboration mode for coord: live session listing, collaboration health checks, owner-aware claim warnings, seam-request workflow, collaboration summaries, and a reusable session-contract template so multi-agent work records roles, seams, ownership,...",
            "path": "../../docs/design/coord-collaboration-phase4.md"
          },
          {
            "title": "Design — coord core, Phase 1 walking skeleton (record · fold · claim/check/release/tail)",
            "summary": "The Phase-1 walking skeleton: an append-only per-session record, a pure fold over it, and four verbs (claim, check, release, tail) that let two sessions in two worktrees see each other's leases. Stdlib only, no daemon, no dependency. The LOG-A seam — an...",
            "path": "../../docs/design/coord-core-phase1.md"
          },
          {
            "title": "Design — coord enforcement, Phase 2 (PreToolUse hook · pre-commit floor · work-preservation guard)",
            "summary": "Phase 2 makes the Phase-1 lease actually hold: a PreToolUse hook that refuses an unleased edit, a pre-commit floor no settings key can switch off, and a guard that refuses to move HEAD over work reachable from exactly one ref. Splits the store in two — intent...",
            "path": "../../docs/design/coord-enforcement-phase2.md"
          },
          {
            "title": "Design — coord Phase 3 (collision-proof allocator · artifact-class registry & derived merge driver · harness adapters)",
            "summary": "Phase 3 closes the two structural failure modes — allocation collision and derived-artifact conflict — and turns the harness adapter from an assumption into a contract. Six spikes ran; one closed the F1 condition open since the architecture (Copilot CLI does...",
            "path": "../../docs/design/coord-federation-phase3.md"
          },
          {
            "title": "Docs Explorer — Grounding and Spatial Navigation Design",
            "summary": "Detailed design for making the repository knowledge graph a deterministic grounding interface for coding agents and a clearer human exploration surface. It separates selected-node neighborhood context from mind-map rooting, adds provenance-bounded context...",
            "path": "../../docs/design/docs-explorer-grounding-and-spatial-navigation.md"
          },
          {
            "title": "Native app UI skill extension — Design",
            "summary": "Detailed design for making native client applications first-class in the AI-Forward UI skills. The design updates /ui-design and /visualize, adds a reusable native UI proof-pack template, adds native desktop archetype rows, and introduces a deterministic XAML...",
            "path": "../../docs/design/native-app-ui-skill-extension.md"
          },
          {
            "title": "Design — installed-repo doctor (suggestion 2)",
            "summary": "A deployable, stdlib-only pack-doctor.py that reports the INSTALL health of a target repo (revision, both tool surfaces, managed-block integrity, graph health) as PASS/WARN/FAIL with fixes and a nonzero exit — distinct from the source-only consistency gate.",
            "path": "../../docs/design/pack-doctor.md"
          },
          {
            "title": "Design — project memory + Obsidian decision (suggestion 3)",
            "summary": "A project-memory convention — an append-only, graph-linked docs/project-memory.md ledger that skills read at grounding and append to at convergence — plus the explicit decision to treat Obsidian as an OPTIONAL lens over the existing vault, never a dependency.",
            "path": "../../docs/design/project-memory.md"
          },
          {
            "title": "Design — RAI policy + PII/secret scrub (suggestion 4)",
            "summary": "A committed Responsible-AI policy knowledge doc mapping Microsoft RAI principles + NIST AI RMF functions to the pack's EXISTING personas/templates, plus a stdlib regex scrub.py first-pass that redacts obvious PII/secrets from Markdown — explicitly labeled...",
            "path": "../../docs/design/rai-and-scrub.md"
          }
        ]
      }
    ]
  },
  "systems": [
    {
      "h": "Knowledge graph & Docs Explorer",
      "p": "Every artifact carries YAML frontmatter (id, type, owner, typed links, review-by). docs/docs-index.js is derived from it and browsable at docs/index.html - hierarchy, graph, mind-map, and a health view. Grounding traverses the graph; material changes flag inbound neighbours for review.",
      "link": {
        "name": "Docs Explorer",
        "path": "../index.html"
      }
    },
    {
      "h": "Dreaming - continuous improvement",
      "p": "The 'asleep half': /dream consolidates the audit log, defect-class register, captured mitigations, and triggered markers into reviewable proposed learnings with controls; a promotion oracle captures successful mitigations (red->green tests or human validation); /apply-learnings federates approved learnings across repos.",
      "link": {
        "name": "Dream review",
        "path": "../dreams/"
      }
    },
    {
      "h": "Audit & change log",
      "p": "A durable, committed, append-only history: every skill records its run (audit-log.jsonl) and every design decision its rationale + git context (change-log.jsonl). A new session reads it to learn what was done and why, instead of starting blind.",
      "link": {
        "name": "Audit viewer",
        "path": "../audit/index.html"
      }
    },
    {
      "h": "Personas - the review swarm",
      "p": "Persona lenses (architects, security, data, test, SRE, the Simplifier, platform developers, UX) that convene by the cost-of-error of a change, author in Peer Mode and attack in Adversary Mode, each with a severity, a falsifiable veto-clears-when, and the anti-pattern it owns.",
      "link": null
    }
  ],
  "graph": {
    "nodes": [
      {
        "id": "adr-0001-grounding-source-corpus-registry",
        "type": "adr",
        "title": "ADR-0001: Use a versioned supplemental source-corpus registry",
        "summary": "Keeps frontmatter-bearing docs as the authoritative project graph while admitting canonical pack knowledge through a separate, versioned supplemental..."
      },
      {
        "id": "adr-0002-fleet-learnings-store",
        "type": "adr",
        "title": "ADR-0002: Fleet learnings store in ai-forward; append-only facts + slug-keyed learnings; two federation paths",
        "summary": "The fleet learnings store lives in the ai-forward repo; corpus/oracle records are append-only facts and a Learning is a slug-keyed dimension whose instances..."
      },
      {
        "id": "adr-0003-promotion-oracle",
        "type": "adr",
        "title": "ADR-0003: The promotion oracle is captured successful mitigations (red→green test or human validation)",
        "summary": "The oracle for 'the fix worked' is a captured MitigationRecord whose verification is either a red-observed→green test pair or an explicit human validation; a..."
      },
      {
        "id": "adr-0004-instance-to-class-abstraction",
        "type": "adr",
        "title": "ADR-0004: Safe instance→class abstraction — deterministic strip, model name, generalisation guards, human gate",
        "summary": "Defines the safe instance→class abstraction: deterministically strip specifics + PII, model-name the shape, enforce five generalisation guards (evidence..."
      },
      {
        "id": "adr-0005-harness-runner-boundary",
        "type": "adr",
        "title": "ADR-0005: Ship a stdlib deterministic harness; the model call is an injected boundary owned by the runner; human-gate, no auto-merge",
        "summary": "The pack ships a stdlib-only deterministic harness (dream.py) + prompts; the one model call per phase is an injected boundary the runner (claude-cowork /..."
      },
      {
        "id": "adr-0006-dream-manifest",
        "type": "adr",
        "title": "ADR-0006: The Dream Manifest — a learnings×repos targeting/record layer for federation, composed in a UI, consumed by apply-learnings --manifest, local-only by default",
        "summary": "Federation had a distribution mechanism (apply-learnings push -> per-repo plans) but no targeting/record layer: which learnings go to which repos, and what..."
      },
      {
        "id": "adr-0007-coordination-substrate",
        "type": "adr",
        "title": "ADR-0007: A git-tracked append-only record folded on demand — no daemon, no database",
        "summary": "Coordination state lives in an append-only JSONL record, one file per session, git-tracked, and every piece of state is a fold over it. The daemon and the..."
      },
      {
        "id": "adr-0008-non-coordinating-allocation",
        "type": "adr",
        "title": "ADR-0008: Identifiers come from a non-coordinating stdlib scheme — not uuid7, and not branch scanning",
        "summary": "Shared-register identifiers are issued from a stdlib-only, time-ordered, non-coordinating scheme — 48 bits of millisecond timestamp plus 80 bits from..."
      },
      {
        "id": "adr-0009-artifact-class-and-derived-merge",
        "type": "adr",
        "title": "ADR-0009: Artifact class decides the mechanism — derived artifacts are regenerated by a merge driver, never leased",
        "summary": "Every path pattern is classified authored / derived / register / hotspot, and the class decides the coordination mechanism entirely. Derived artifacts — which..."
      },
      {
        "id": "adr-0010-enforcement-topology",
        "type": "adr",
        "title": "ADR-0010: Enforce at the harness edit boundary where it exists, at the commit boundary always — and fail to ask, never to allow",
        "summary": "A PreToolUse hook returning permissionDecision deny refuses an unleased edit before it happens; the pre-commit boundary is the universal floor no settings key..."
      },
      {
        "id": "adr-0011-projection-trust-boundary",
        "type": "adr",
        "title": "ADR-0011: Cross-agent content is untrusted data — the projection ships only after its rendering rules exist",
        "summary": "The projection renders text authored by one agent's model into another agent's context, which the hook schema confirms is a live injection channel. Cross-agent..."
      },
      {
        "id": "adr-0012-reuse-existing-mechanisms",
        "type": "adr",
        "title": "ADR-0012: Compose the mechanisms that already exist — the harness ships two of them, and the fleet ships three more",
        "summary": "The F8 reconciliation the spec made a condition of pass. Two of the four failure modes are already partly addressed by mechanisms shipped in the harness..."
      },
      {
        "id": "architecture",
        "type": "architecture",
        "title": "AI-Forward — Architecture Overview",
        "summary": "The architecture of record for this repository: a dual-purpose repo that is both the canonical SOURCE of the AI-Forward Pack (pack/) and a live INSTALL of it..."
      },
      {
        "id": "architecture-agent-coordination",
        "type": "architecture",
        "title": "Agent coordination — architecture",
        "summary": "The architecture for the agent-coordination layer: a git-tracked append-only record of intent, folded on demand with no daemon and no database, enforced at..."
      },
      {
        "id": "architecture-dreaming",
        "type": "architecture",
        "title": "Dreaming subsystem — architecture",
        "summary": "Subsystem architecture for AI-Forward's dreaming capability — the offline consolidation pipeline (light/REM/deep) over the committed corpus, the HTML..."
      },
      {
        "id": "audit-log",
        "type": "doc",
        "title": "Audit & Change Log",
        "summary": "The project's durable, committed activity & decision history — an append-only audit log of every meaningful prompt/skill/script and a curated change log of..."
      },
      {
        "id": "backtest-optimize-graph",
        "type": "doc",
        "title": "optimize-graph back-test — twelve real prompts replanned",
        "summary": "Back-test of the /optimize-graph skill against twelve real prompts drawn from 750 committed audit entries across TheTerrace, meridian-finance-planner and..."
      },
      {
        "id": "defect-classes",
        "type": "doc",
        "title": "Defect-class register",
        "summary": "This repository's register of defect classes — the recurring shapes of things that go wrong here, what each one survives, and the control that now fails when..."
      },
      {
        "id": "design-aiforward-cli",
        "type": "design",
        "title": "Design — aiforward CLI (suggestion 1)",
        "summary": "A single stdlib-only Python developer CLI (tools/aiforward.py) that is a thin Façade dispatcher over the pack's existing scripts (sync, verify, check, new,..."
      },
      {
        "id": "design-coord-collaboration-phase4",
        "type": "design",
        "title": "Design - coord collaboration mode, Phase 4",
        "summary": "Phase-4 collaboration mode for coord: live session listing, collaboration health checks, owner-aware claim warnings, seam-request workflow, collaboration..."
      },
      {
        "id": "design-coord-core-phase1",
        "type": "design",
        "title": "Design — coord core, Phase 1 walking skeleton (record · fold · claim/check/release/tail)",
        "summary": "The Phase-1 walking skeleton: an append-only per-session record, a pure fold over it, and four verbs (claim, check, release, tail) that let two sessions in two..."
      },
      {
        "id": "design-coord-enforcement-phase2",
        "type": "design",
        "title": "Design — coord enforcement, Phase 2 (PreToolUse hook · pre-commit floor · work-preservation guard)",
        "summary": "Phase 2 makes the Phase-1 lease actually hold: a PreToolUse hook that refuses an unleased edit, a pre-commit floor no settings key can switch off, and a guard..."
      },
      {
        "id": "design-coord-federation-phase3",
        "type": "design",
        "title": "Design — coord Phase 3 (collision-proof allocator · artifact-class registry & derived merge driver · harness adapters)",
        "summary": "Phase 3 closes the two structural failure modes — allocation collision and derived-artifact conflict — and turns the harness adapter from an assumption into a..."
      },
      {
        "id": "design-docs-explorer-grounding-spatial-navigation",
        "type": "design",
        "title": "Docs Explorer — Grounding and Spatial Navigation Design",
        "summary": "Detailed design for making the repository knowledge graph a deterministic grounding interface for coding agents and a clearer human exploration surface. It..."
      },
      {
        "id": "design-language-docs-explorer",
        "type": "design-language",
        "title": "Docs Explorer — Design Language",
        "summary": "Token and interaction language for the Docs Explorer knowledge portal: browse, graph, mind-map, deterministic Spatial 3D, and derived HTML knowledge surfaces...."
      },
      {
        "id": "design-native-app-ui-skill-extension",
        "type": "design",
        "title": "Native app UI skill extension — Design",
        "summary": "Detailed design for making native client applications first-class in the AI-Forward UI skills. The design updates /ui-design and /visualize, adds a reusable..."
      },
      {
        "id": "design-pack-doctor",
        "type": "design",
        "title": "Design — installed-repo doctor (suggestion 2)",
        "summary": "A deployable, stdlib-only pack-doctor.py that reports the INSTALL health of a target repo (revision, both tool surfaces, managed-block integrity, graph health)..."
      },
      {
        "id": "design-project-memory",
        "type": "design",
        "title": "Design — project memory + Obsidian decision (suggestion 3)",
        "summary": "A project-memory convention — an append-only, graph-linked docs/project-memory.md ledger that skills read at grounding and append to at convergence — plus the..."
      },
      {
        "id": "design-rai-and-scrub",
        "type": "design",
        "title": "Design — RAI policy + PII/secret scrub (suggestion 4)",
        "summary": "A committed Responsible-AI policy knowledge doc mapping Microsoft RAI principles + NIST AI RMF functions to the pack's EXISTING personas/templates, plus a..."
      },
      {
        "id": "docs-index",
        "type": "doc",
        "title": "AI-Forward — Documentation Map of Content",
        "summary": "A curated Map of Content (V3) over the AI-Forward repo's documentation — the human entry point linking the architecture overview, the interactive explainer,..."
      },
      {
        "id": "dream-diary",
        "type": "doc",
        "title": "Dream Diary",
        "summary": "Human-readable narrative of each dream pass (what it added/merged/superseded). NOT a promotion source - excluded from re-ingestion (no self-poisoning)...."
      },
      {
        "id": "forensic-review",
        "type": "doc",
        "title": "Forensic Review — AI-Forward repository (revisions 30 & 33)",
        "summary": "Adoption-readiness assessment at commit 2227632 (revision 30), scoped to inconsistencies and contradictions. Every self-declared gate is green and the..."
      },
      {
        "id": "forensic-review-20260712",
        "type": "doc",
        "title": "Forensic Review — AI-Forward model orchestration",
        "summary": "Evidence-based assessment of AI-Forward commit 5d7b952 focused on model orchestration. The user accepted the readiness BLOCK and reverted the capability; the..."
      },
      {
        "id": "forensic-review-20260802",
        "type": "doc",
        "title": "Forensic Review — AI-Forward repository (revision 18, archived)",
        "summary": "Comprehensive evidence-based assessment of the AI-Forward repository at commit 53e3afe (revision 18). Ten findings, none P0. The two load-bearing results are..."
      },
      {
        "id": "forensic-review-20260802-backlog",
        "type": "doc",
        "title": "Forensic Review Backlog — AI-Forward repository (revision 18)",
        "summary": "The proposed backlog from the revision-18 forensic review of AI-Forward at commit 53e3afe — ten findings (FR-011..FR-020) ordered into four phases, plus FR-008..."
      },
      {
        "id": "forensic-review-backlog",
        "type": "doc",
        "title": "Forensic Review Backlog — AI-Forward repository (revisions 30 & 33)",
        "summary": "Twelve items (FR-031..FR-042) from the revision-30 review, ordered into four independently deliverable phases. Nine are RESOLVED at revisions 31-32..."
      },
      {
        "id": "forensic-review-backlog-20260712",
        "type": "doc",
        "title": "Forensic Review Backlog — Model orchestration",
        "summary": "Historical remediation backlog from the model-orchestration forensic review. The capability was reverted; orchestration-specific items are closed by removal...."
      },
      {
        "id": "forensic-review-rev42",
        "type": "doc",
        "title": "Forensic Review — AI-Forward repository (revision 42)",
        "summary": "Forensic assessment at commit e4eae82 (revision 42), clean tree, all seven CI gates green and verified green on a runner. Four findings carried from revision..."
      },
      {
        "id": "forensic-review-rev42-backlog",
        "type": "doc",
        "title": "Forensic Review Backlog — revision 42",
        "summary": "Backlog from the revision-42 forensic review at commit e4eae82, ALL NINE ITEMS TRIAGED AND DISPOSITIONED at revision 43. Seven resolved with a control observed..."
      },
      {
        "id": "forensic-review-rev48",
        "type": "doc",
        "title": "Forensic Review — AI-Forward repository (revision 48)",
        "summary": "Forensic assessment at commit c27f83d (revision 48), clean tree. The headline is not a latent risk but a present one: main is red. Two of the nine gates the..."
      },
      {
        "id": "forensic-review-rev48-backlog",
        "type": "doc",
        "title": "Forensic Review Backlog — revision 48",
        "summary": "Resolved record of eleven items (FR-058..FR-068) from the revision-48 forensic review at commit c27f83d, ordered into four phases. All phases shipped through..."
      },
      {
        "id": "forensic-review-rev48-proof",
        "type": "proof-pack",
        "title": "Proof Pack — Forensic Review, revision 48",
        "summary": "Evidence record for the revision-48 forensic review. One row per correctness claim, each with the exact command, its observed exit code, the oracle that..."
      },
      {
        "id": "forensic-review-rev49",
        "type": "doc",
        "title": "Forensic Review - AI-Forward repository (revision 49)",
        "summary": "Forensic assessment at commit 33f651d (pack revision 49). The repository's source, graph, audit log, and full gates are healthy after dependency restore, but..."
      },
      {
        "id": "forensic-review-rev49-backlog",
        "type": "doc",
        "title": "Forensic Review Backlog - revision 49",
        "summary": "Three proposed items from the revision-49 forensic review at commit 33f651d: make the local bundle verifier restore declared npm dependencies in clean..."
      },
      {
        "id": "forensic-review-rev49-proof",
        "type": "proof-pack",
        "title": "Proof Pack - Forensic Review, revision 49",
        "summary": "Evidence record for the revision-49 forensic review at commit 33f651d. It records the baseline gates and the three proposed findings: a clean-worktree npm..."
      },
      {
        "id": "forensic-review-rev53",
        "type": "doc",
        "title": "Forensic Review - AI-Forward repository (revision 53)",
        "summary": "Forensic assessment at commit 43bd9f6 (pack revision 53). The repository is healthy and adoption-ready: source is clean after the SIM115 remediation, all 9..."
      },
      {
        "id": "forensic-review-rev53-backlog",
        "type": "doc",
        "title": "Forensic Review Backlog - AI-Forward revision 53",
        "summary": "Proposed, prioritized backlog from the revision-53 forensic review. One carry-forward P2 (FR-069, re-verified open), one carry-forward P3 (FR-071), and four..."
      },
      {
        "id": "hygiene-backlog",
        "type": "doc",
        "title": "Code-hygiene backlog",
        "summary": "Measured code-hygiene review of this repository's hand-authored source (Python, JS, PowerShell). Detects dead/commented-out code (HYG-A) and anti-pattern..."
      },
      {
        "id": "hygiene-remediation-plan",
        "type": "doc",
        "title": "Code-hygiene remediation plan — SIM115 (resource lifecycle)",
        "summary": "TDD-guarded, git-labelled remediation of the 26 SIM115 (open()-without-context-manager) findings from the hygiene backlog. 25 are behaviour-preserving `with..."
      },
      {
        "id": "investigation-blank-explainer-live",
        "type": "investigation",
        "title": "Investigation: the hosted explainer renders blank even after the 'fix'",
        "summary": "The hosted explainer stayed blank after a fix was declared, because the fix lived only in the working tree — it was never deployed, so the live URL still..."
      },
      {
        "id": "investigation-fr-071",
        "type": "doc",
        "title": "Investigation - FR-071: audit-log suggest self-reports its own closeout",
        "summary": "audit-log.py `suggest` lists every commit since the last change-log entry with no filter, so it surfaces bookkeeping/closeout commits (including the very..."
      },
      {
        "id": "kb-agent-autopilot-controls",
        "type": "knowledge",
        "title": "Agent autopilot & autonomous-continuation controls (Copilot CLI ↔ Claude Code)",
        "summary": "Sourced comparison of the autonomous-execution controls in GitHub Copilot CLI and Claude Code — the autonomy modes, the full-permission \"YOLO\" switches, and..."
      },
      {
        "id": "kb-agent-autopilot-controls-comparables",
        "type": "knowledge",
        "title": "Agent autopilot controls — Symmetry map (Copilot CLI ↔ Claude Code)",
        "summary": "The load-bearing artifact: a concept-by-concept symmetry table mapping GitHub Copilot CLI autonomy controls to their Claude Code equivalents, plus the..."
      },
      {
        "id": "kb-agent-autopilot-controls-data",
        "type": "knowledge",
        "title": "Agent autopilot controls — Data, defaults & invariants",
        "summary": "The concrete defaults, stopping conditions, and invariants of autonomous execution on each surface — the numbers and rules a recommendation must respect."
      },
      {
        "id": "kb-agent-autopilot-controls-glossary",
        "type": "knowledge",
        "title": "Agent autopilot controls — Glossary",
        "summary": "The ubiquitous language of agent autonomy across both surfaces, defined so the two vocabularies can be discussed without conflation."
      },
      {
        "id": "kb-agent-autopilot-controls-open-questions",
        "type": "knowledge",
        "title": "Agent autopilot controls — Open questions & failure modes",
        "summary": "What this research could not fully settle, the failure modes of autonomous execution, and the disconfirming views deliberately sought."
      },
      {
        "id": "kb-agent-autopilot-controls-references",
        "type": "knowledge",
        "title": "Agent autopilot controls — Reference (flags, settings, commands)",
        "summary": "The authoritative flag/setting/command surface for autonomous execution on each CLI, with the primary-source page for each."
      },
      {
        "id": "kb-agent-autopilot-controls-sota",
        "type": "knowledge",
        "title": "Agent autopilot controls — State of the Art",
        "summary": "How the two surfaces implement autonomous execution today: Copilot CLI's autopilot mode + its permission and continuation switches, and Claude Code's..."
      },
      {
        "id": "kb-agent-autopilot-controls-sources",
        "type": "knowledge",
        "title": "Agent autopilot controls — Sources",
        "summary": "Full source list with access dates and the claims each supports. Primary vendor docs first."
      },
      {
        "id": "kb-agent-focus-and-scope-control",
        "type": "knowledge",
        "title": "Agent Focus & Scope Control — keeping extended-reasoning models on task",
        "summary": "Sourced evidence base on why extended-reasoning models (GPT-5.x family and peers) keep adding unrequested tasks and ceremony even when reasoning level is..."
      },
      {
        "id": "kb-agent-focus-and-scope-control-glossary",
        "type": "glossary",
        "title": "Agent Focus & Scope Control — Glossary",
        "summary": "The ubiquitous language of agent focus and scope control - overthinking, goal drift, Latent Goal Crystallization, instruction-following degradation, stopping..."
      },
      {
        "id": "kb-agent-focus-and-scope-control-open-questions",
        "type": "knowledge",
        "title": "Agent Focus & Scope Control — Open Questions",
        "summary": "What the research could not settle: no fully satisfactory long-horizon solution yet; the enforcement-vs-autonomy tension; whether a session self-assessment..."
      },
      {
        "id": "kb-agent-focus-and-scope-control-references",
        "type": "knowledge",
        "title": "Agent Focus & Scope Control — References & Patterns",
        "summary": "Copy-usable techniques mapped to the pack's existing controls: reasoning-depth controls, the GPT-5 structured scope-lock block, enforced done predicates,..."
      },
      {
        "id": "kb-agent-focus-and-scope-control-sota",
        "type": "knowledge",
        "title": "Agent Focus & Scope Control — State of the Art",
        "summary": "The two failure modes (overthinking vs goal drift) and the four evidence-backed levers for scope and task adherence: enforced done predicates, adaptive..."
      },
      {
        "id": "kb-agent-focus-and-scope-control-sources",
        "type": "knowledge",
        "title": "Agent Focus & Scope Control — Sources",
        "summary": "The full source list with access dates and confidence labels: primary arXiv research (overthinking, goal drift, agent drift, self-reflection, reasoning path..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — harvesting learnings across repos (domain knowledge)",
        "summary": "Sourced evidence base for continuously harvesting learnings, mistakes, patterns and anti-patterns across a fleet of local repositories and sharing them so..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming-comparables",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — Comparables",
        "summary": "How Claude Dreams, OpenClaw, Reflexion, Generative Agents, A-MEM, the LLM-wiki, self-improving AGENTS.md, and SRE/NASA lessons-learned frame and solve the..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming-data",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — Data, Constants & Invariants",
        "summary": "The concrete parameters (Claude Dreams 1-100 sessions; OpenClaw's six weighted deep-ranking signals and threshold gates; nightly cron), the AI-Forward corpus a..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming-glossary",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — Glossary",
        "summary": "The ubiquitous language for the dreaming/consolidation capability — dream pass, light/REM/deep phases, candidate, promotion, provenance taint gate, Dream..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming-open-questions",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — Open Questions & Failure Modes",
        "summary": "The unresolved forks to carry into /specify (fleet store location, the promotion oracle, safe instance-to-class abstraction, cadence, runner), the known..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming-references",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — References",
        "summary": "Primary product/platform sources, seminal papers (Reflexion, Generative Agents, A-MEM, sleep-time compute), SRE/NASA practice, and the in-repo standards this..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming-sota",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — State of the Art",
        "summary": "Current best practice for continuous self-improvement: the awake/asleep loop; Claude Dreams and OpenClaw's phased local dreaming; Reflexion and Generative..."
      },
      {
        "id": "kb-continuous-improvement-and-dreaming-sources",
        "type": "knowledge",
        "title": "Continuous Improvement & Dreaming — Sources",
        "summary": "Full source list with access dates and confidence labels — primary product/platform docs (Claude Dreams, OpenClaw), seminal papers, SRE/NASA practice, and the..."
      },
      {
        "id": "kb-ddm-comparables",
        "type": "knowledge",
        "title": "Domain & Data Modelling — Comparables",
        "summary": "How other approaches frame and solve \"a durable model that keeps history and an audit trail without a shadow schema\" — CQRS, event sourcing, Data Vault, anchor..."
      },
      {
        "id": "kb-ddm-data",
        "type": "knowledge",
        "title": "Domain & Data Modelling — Data, Shapes & Constants",
        "summary": "The concrete, reusable shapes: the grain statement form, the additivity classes, the Type-2 dimension column set, the append-only fact column set, the..."
      },
      {
        "id": "kb-ddm-glossary",
        "type": "knowledge",
        "title": "Domain & Data Modelling — Glossary",
        "summary": "The ubiquitous language of domain and data modelling, each term defined with what it is NOT — the near-miss disambiguation that stops two people using one word..."
      },
      {
        "id": "kb-ddm-open-questions",
        "type": "knowledge",
        "title": "Domain & Data Modelling — Open Questions & Failure Modes",
        "summary": "What the research could not settle (three Flagged claims), the disconfirming case against this standard's central stance, and the known failure modes of domain..."
      },
      {
        "id": "kb-ddm-references",
        "type": "knowledge",
        "title": "Domain & Data Modelling — References",
        "summary": "The seminal works, standards and vendor documentation this knowledge base rests on — Evans and Vernon for DDD, Kimball for dimensional modelling, Inmon for the..."
      },
      {
        "id": "kb-ddm-sota",
        "type": "knowledge",
        "title": "Domain & Data Modelling — State of the Art",
        "summary": "Current best practice across the four literatures this standard crosses: tactical DDD (aggregate design rules), conceptual/logical/physical modelling, Kimball..."
      },
      {
        "id": "kb-ddm-sources",
        "type": "knowledge",
        "title": "Domain & Data Modelling — Sources",
        "summary": "Full source list with access dates and the confidence each source carries, ordered by the source-of-truth hierarchy: primary works and standards, then vendor..."
      },
      {
        "id": "kb-domain-and-data-modelling",
        "type": "knowledge",
        "title": "Domain & Data Modelling — DDD, conceptual models, ODS, star schemas (domain knowledge)",
        "summary": "Sourced evidence base for the pack's data-model-primacy directive: Domain-Driven Design (bounded contexts, aggregates, entities vs value objects), the..."
      },
      {
        "id": "kb-graph-and-loop-engineering",
        "type": "knowledge",
        "title": "Graph engineering, loop engineering & graph optimization (domain knowledge)",
        "summary": "Sourced evidence base for planning an agent's work as an explicit dependency graph before executing it: the classical work/span and critical-path theory that..."
      },
      {
        "id": "kb-graph-and-loop-engineering-comparables",
        "type": "knowledge",
        "title": "Graph & loop engineering — Comparables",
        "summary": "How existing systems frame and solve execution-graph planning — workflow engines (Airflow, Temporal, Dagster), agent frameworks (LangGraph, LLMCompiler,..."
      },
      {
        "id": "kb-graph-and-loop-engineering-data",
        "type": "knowledge",
        "title": "Graph & loop engineering — Data & constants",
        "summary": "The numbers — published benchmark results (LLMCompiler, orchestrator-worker, MAST failure rates), framework defaults (LangGraph recursion_limit 25), 2026 cost..."
      },
      {
        "id": "kb-graph-and-loop-engineering-glossary",
        "type": "knowledge",
        "title": "Graph & loop engineering — Glossary",
        "summary": "The ubiquitous language for execution-graph planning — work, span, critical path, node, edge, wave, fan-out/join, collapse/promote, variant, well-founded..."
      },
      {
        "id": "kb-graph-and-loop-engineering-open-questions",
        "type": "knowledge",
        "title": "Graph & loop engineering — Open questions & failure modes",
        "summary": "What the research could not settle, the disconfirming evidence against graph optimization, and the domain's known failure modes — including the ones that argue..."
      },
      {
        "id": "kb-graph-and-loop-engineering-references",
        "type": "knowledge",
        "title": "Graph & loop engineering — Reference information",
        "summary": "The formulae, invariants, decision rules and edge cases of the domain — the work/span bounds, Amdahl and Brent, the independence and coupling tests, the..."
      },
      {
        "id": "kb-graph-and-loop-engineering-sota",
        "type": "knowledge",
        "title": "Graph & loop engineering — State of the Art",
        "summary": "Current best practice across the three joined literatures — DAG scheduling and the work/span bound, agentic parallel planning (LLMCompiler,..."
      },
      {
        "id": "kb-graph-and-loop-engineering-sources",
        "type": "knowledge",
        "title": "Graph & loop engineering — Sources",
        "summary": "Full source list with access dates and confidence labels — primary papers (LLMCompiler, MAST), framework documentation (LangGraph), vendor engineering writeups..."
      },
      {
        "id": "kb-native-client-ui-design",
        "type": "knowledge",
        "title": "Native client UI design — WPF, WinUI, Avalonia and desktop apps",
        "summary": "Sourced evidence base for extending the pack's UI reasoning and review from web properties to native client applications. Establishes the native-specific..."
      },
      {
        "id": "kb-native-client-ui-design-comparables",
        "type": "knowledge",
        "title": "Native client UI design — Comparable repositories",
        "summary": "Permissively licensed public repositories and reference apps suitable for native-client UI review and pattern extraction, plus flagged reference-only repos..."
      },
      {
        "id": "kb-native-client-ui-design-data",
        "type": "knowledge",
        "title": "Native client UI design — Data, constants and proof rows",
        "summary": "Checkable native UI invariants and proof rows: accessibility tree, keyboard traversal, theme/high-contrast behavior, DPI/windowing, native resource tokens, OS..."
      },
      {
        "id": "kb-native-client-ui-design-glossary",
        "type": "glossary",
        "title": "Native client UI design — Glossary",
        "summary": "Ubiquitous language for native desktop UI work: platform HIG, Fluent, WinUI, WPF, XAML resources, UI Automation, automation peers, keyboard focus, high DPI,..."
      },
      {
        "id": "kb-native-client-ui-design-open-questions",
        "type": "knowledge",
        "title": "Native client UI design — Open questions and disconfirmation",
        "summary": "Unresolved native UI research questions, disconfirming evidence, and domain failure modes that the next design pass must settle before changing pack skills or..."
      },
      {
        "id": "kb-native-client-ui-design-references",
        "type": "knowledge",
        "title": "Native client UI design — References",
        "summary": "Standards, HIGs, platform documentation and tools that define the native-client UI contract for Windows, macOS, GNOME/KDE and cross-platform XAML applications."
      },
      {
        "id": "kb-native-client-ui-design-sota",
        "type": "knowledge",
        "title": "Native client UI design — State of the Art",
        "summary": "Current best practice for native client UX/UI: use the target OS design system as the primary contract, keep the pack's UX/UI layering and token discipline,..."
      },
      {
        "id": "kb-native-client-ui-design-sources",
        "type": "knowledge",
        "title": "Native client UI design — Sources",
        "summary": "Full source list for native client UI design research: official Windows/Fluent/Avalonia/GNOME/KDE documentation, Apple pages that need direct recheck,..."
      },
      {
        "id": "kb-pack-evolution",
        "type": "knowledge",
        "title": "Pack Evolution — CLI, Doctor, Project Memory, RAI (domain knowledge)",
        "summary": "Sourced evidence base for four capabilities AI-Forward is considering adopting from agent-orchestration products (notably bradygaster/squad): a unified CLI, an..."
      },
      {
        "id": "kb-pack-evolution-comparables",
        "type": "knowledge",
        "title": "Pack Evolution — Comparables",
        "summary": "Squad-vs-AI-Forward capability comparison for the four suggestions, what to borrow (intent) and what to reject (runtime form), plus adjacent..."
      },
      {
        "id": "kb-pack-evolution-glossary",
        "type": "glossary",
        "title": "Pack Evolution — Glossary",
        "summary": "The ubiquitous language for the pack-evolution work: pack-lifecycle skill, source consistency vs install health, doctor, project memory / ledger, Obsidian..."
      },
      {
        "id": "kb-pack-evolution-open-questions",
        "type": "knowledge",
        "title": "Pack Evolution — Open Questions & Failure Modes",
        "summary": "Flagged unknowns (regex-scrub recall, ledger freshness, CLI cross-shell), the domain's failure modes (runtime creep, drift, RAI theater, Obsidian lock-in,..."
      },
      {
        "id": "kb-pack-evolution-references",
        "type": "knowledge",
        "title": "Pack Evolution — References",
        "summary": "Standards (MS RAI Standard, NIST AI RMF, EU AI Act/GDPR), the pack's own contracts the capabilities conform to (knowledge-visualization V1–V18, INSTALL..."
      },
      {
        "id": "kb-pack-evolution-sota",
        "type": "knowledge",
        "title": "Pack Evolution — State of the Art",
        "summary": "Current best practice for the four capabilities: CLI distribution (repo-local stdlib Python wins), the doctor pattern, persistent project/agent memory,..."
      },
      {
        "id": "kb-pack-evolution-sources",
        "type": "knowledge",
        "title": "Pack Evolution — Sources",
        "summary": "The full source list with access dates for the pack-evolution knowledge base — Squad, the pack's own files, the MS RAI and NIST RMF standards, the scrub..."
      },
      {
        "id": "lens-code-doc-join",
        "type": "doc",
        "title": "Lens - code/doc join",
        "summary": "Derived join between the documentation graph (intent) and the Graphify code graph (reality): documentation referencing code that does not exist, and the most..."
      },
      {
        "id": "lens-graph-health",
        "type": "doc",
        "title": "Lens - graph health",
        "summary": "A read-time Dataview lens over the knowledge graph's health - stale artifacts, missing owners, missing freshness SLAs, and review-suggested flags. Derived,..."
      },
      {
        "id": "lens-graph-insight",
        "type": "doc",
        "title": "Lens - graph insight (computed)",
        "summary": "Computed structural analysis of the knowledge graph - hubs, bridges, components, orphans and structural gaps. Regenerate with obsidian-setup.py --analyze..."
      },
      {
        "id": "lens-graph-structure",
        "type": "doc",
        "title": "Lens - graph structure",
        "summary": "A read-time lens over the shape of the knowledge graph - artifacts by type and status, and the traceability chains (spec to design to proof). Derived, never..."
      },
      {
        "id": "mockup-documentation-portal",
        "type": "design",
        "title": "Documentation Portal — mockup",
        "summary": "Self-contained, dependency-free high-fidelity mockup of the Documentation Portal — the DocsPortal (Content Portal / HolyGrail reading layout) front door:..."
      },
      {
        "id": "mockup-dream-review",
        "type": "design",
        "title": "Dream Review — mockup",
        "summary": "Self-contained, dependency-free high-fidelity mockup of the Dream Review view — the Master-Detail approval queue the maintainer uses to review a dream's..."
      },
      {
        "id": "note-20260712-model-orchestration-policy",
        "type": "decision-note",
        "title": "Model-orchestration routing policy for AI-Forward skills",
        "summary": "Historical policy decision for applying LOA tier allocation to skill execution. Superseded after forensic review found the proposed control plane unwired,..."
      },
      {
        "id": "note-20260712-revert-model-orchestration",
        "type": "decision-note",
        "title": "Revert the model-orchestration capability",
        "summary": "Removes the model-orchestration standard, static router, tests, and active wiring after forensic review found the capability unwired and unsafe to claim as..."
      },
      {
        "id": "note-20260818-dream-rerun-unchanged-corpus",
        "type": "decision-note",
        "title": "Re-running /dream over an unchanged corpus re-surfaces already-promoted classes under new proposal ids",
        "summary": "Observed in drm-0004: a dream over a corpus unchanged since the prior dream re-emits the same control-upgrade/marker/mitigation proposals under fresh (dream,..."
      },
      {
        "id": "note-20260820-spike-corpus-assertion",
        "type": "decision-note",
        "title": "A verification script reported COLLISION-FREE over zero identifiers, because it only compared set size to list size",
        "summary": "While spiking the allocator for ADR-0008, the verification harness printed \"COLLISION-FREE WITHOUT COORDINATION\" over an empty result set — the worker..."
      },
      {
        "id": "note-20260822-backlog-triage-and-worktree-discipline",
        "type": "decision-note",
        "title": "Decision note — revision-42 backlog triage, and worktree-per-session",
        "summary": "Four sub-ADR decisions taken while clearing the revision-42 backlog and adding worktree-per-session: withdrawing FR-050 rather than acting on it, closing..."
      },
      {
        "id": "note-20260823-merge-driver-resolves-not-regenerates",
        "type": "decision-note",
        "title": "A merge driver cannot regenerate a derived artifact — git runs drivers before the sources are merged",
        "summary": "The Phase-3 design had the .gitattributes merge driver regenerating a derived artifact during the merge. Git runs merge drivers per file in arbitrary order, so..."
      },
      {
        "id": "note-autopilot-open-questions-decisions",
        "type": "decision-note",
        "title": "Decisions on PACK-O open questions (logging, class granularity, autopilot caps)",
        "summary": "The user's answers to the three open questions from the task-discipline / front-matter proposal (revision 3), which gate the next change: making PACK-O..."
      },
      {
        "id": "note-required-status-checks",
        "type": "decision-note",
        "title": "Decision — do not make pack-consistency a required status check on main",
        "summary": "Decision not to enable required status checks on main, taken while closing FR-062. The control would have prevented the original incident outright, but with..."
      },
      {
        "id": "plan-optimize-graph-live-01",
        "type": "doc",
        "title": "optimize-graph live run 01 — commit the rev-40 change set",
        "summary": "First live /optimize-graph run, on the prompt that asked for it. Records the plan, the planned-vs-actual ledger (GO18), and the run's headline measurement —..."
      },
      {
        "id": "privacy-review",
        "type": "privacy-review",
        "title": "Privacy Review",
        "summary": "Repo-level privacy posture for the pack-evolution tooling: the CLI and doctor touch no personal data; project memory may incidentally record handles/names (no..."
      },
      {
        "id": "project-memory",
        "type": "doc",
        "title": "Project Memory",
        "summary": "The durable, append-only record of what this project has learned and decided — read at every skill's grounding and appended to at every skill's convergence...."
      },
      {
        "id": "proof-coord-collaboration-phase4",
        "type": "proof-pack",
        "title": "Proof Pack - coord collaboration mode, Phase 4",
        "summary": "Proof pack for coord collaboration mode: active-session projection, collaboration health checks, owner-aware claim warnings, seam-request workflow,..."
      },
      {
        "id": "proof-docs-explorer-redesign",
        "type": "proof-pack",
        "title": "Docs Explorer Redesign - Proof Pack",
        "summary": "Accepted implementation evidence for the deterministic, local-first Docs Explorer, native Spatial 3D knowledge portal, and bounded grounding packet..."
      },
      {
        "id": "proof-native-app-ui-skill-extension",
        "type": "proof-pack",
        "title": "Proof Pack — Native app UI skill extension",
        "summary": "Proof pack for implementing the native app UI skill extension: native UI triggers and guardrails, the reusable native UI proof-pack template, XAML token..."
      },
      {
        "id": "proposal-hosting-and-dream-manifest",
        "type": "doc",
        "title": "Proposal / dialog: GitHub Pages hosting + the Dream Manifest",
        "summary": "An RFC/dialog opener on (1) whether to host the Documentation Portal and surfaces on GitHub Pages, (2) how that impacts dream output and privacy, and (3) a..."
      },
      {
        "id": "proposal-turn-goal-state-and-stopping",
        "type": "doc",
        "title": "Proposal: define the goal state before acting — bounding the agent turn",
        "summary": "An incident analysis and proposal. A closed question (\"is /optimize-graph wired into the skills?\") was answered on the first tool call and then became an..."
      },
      {
        "id": "spec-agent-coordination",
        "type": "spec",
        "title": "Agent coordination — shared context and explicit coordination across worktrees and agents",
        "summary": "Specification for a repo-local, model-agnostic coordination layer that lets several agents and worktrees work one repository at once without losing work or..."
      },
      {
        "id": "spec-collaborate-skill",
        "type": "spec",
        "title": "Spec - /collaborate skill proposal",
        "summary": "Proposal for a future /collaborate skill that starts a cross-agent collaboration session by creating or entering a worktree, registering the session,..."
      },
      {
        "id": "spec-design-slice-rename",
        "type": "spec",
        "title": "Rename /design to /design-slice — Specification",
        "summary": "Specification for renaming AI-Forward's detailed component-design workflow from /design to /design-slice. The rename avoids a generic skill-name collision..."
      },
      {
        "id": "spec-documentation-portal",
        "type": "spec",
        "title": "Documentation Portal — a derived, self-maintaining interactive front door",
        "summary": "Specification for a single, polished, interactive HTML documentation portal that is the front door to the AI-Forward repo — a capabilities overview, concrete..."
      },
      {
        "id": "spec-dreaming",
        "type": "spec",
        "title": "Dreaming — continuous-improvement consolidation, review, and cross-repo federation",
        "summary": "Specification for AI-Forward's dreaming capability: a /dream consolidation skill that mines the committed corpus (audit/change logs, defect-class register,..."
      },
      {
        "id": "spec-native-app-ui-skill-extension",
        "type": "spec",
        "title": "Native app UI skill extension — Specification",
        "summary": "Specification for extending the AI-Forward UI skills so WPF, WinUI, Avalonia and other native client applications receive the same rigorous UX/UI reasoning as..."
      },
      {
        "id": "threat-model",
        "type": "threat-model",
        "title": "Threat Model",
        "summary": "Repo-level security posture for the pack-evolution tooling. The scrub handles potentially sensitive file content, while the Docs Explorer crosses..."
      },
      {
        "id": "ui-capability-guide",
        "type": "doc",
        "title": "UI & UX Capability Guide",
        "summary": "The how-to layer over this repository's seven UI standards: the layer stack and what each one decides, a job-to-path picker, the /ui-design loop, the command..."
      },
      {
        "id": "ui-review-pack-explainer",
        "type": "doc",
        "title": "UI review — AI-Forward Pack Explainer",
        "summary": "Review of web/ai-forward-pack-explainer.html, triggered by the question \"can Higgsfield beautify this?\". Measurement says no: the public surface renders blank..."
      }
    ],
    "edges": [
      {
        "from": "adr-0001-grounding-source-corpus-registry",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0001-grounding-source-corpus-registry",
        "to": "design-docs-explorer-grounding-spatial-navigation",
        "rel": "implements"
      },
      {
        "from": "adr-0002-fleet-learnings-store",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0002-fleet-learnings-store",
        "to": "architecture-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0002-fleet-learnings-store",
        "to": "spec-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0003-promotion-oracle",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0003-promotion-oracle",
        "to": "architecture-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0003-promotion-oracle",
        "to": "spec-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0004-instance-to-class-abstraction",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0004-instance-to-class-abstraction",
        "to": "architecture-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0004-instance-to-class-abstraction",
        "to": "spec-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0005-harness-runner-boundary",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0005-harness-runner-boundary",
        "to": "architecture-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0005-harness-runner-boundary",
        "to": "spec-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0006-dream-manifest",
        "to": "adr-0002-fleet-learnings-store",
        "rel": "depends-on"
      },
      {
        "from": "adr-0006-dream-manifest",
        "to": "adr-0005-harness-runner-boundary",
        "rel": "depends-on"
      },
      {
        "from": "adr-0006-dream-manifest",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0006-dream-manifest",
        "to": "architecture-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0006-dream-manifest",
        "to": "spec-dreaming",
        "rel": "implements"
      },
      {
        "from": "adr-0007-coordination-substrate",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0007-coordination-substrate",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0007-coordination-substrate",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0008-non-coordinating-allocation",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0008-non-coordinating-allocation",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "adr-0008-non-coordinating-allocation",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0009-artifact-class-and-derived-merge",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0009-artifact-class-and-derived-merge",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "adr-0009-artifact-class-and-derived-merge",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0010-enforcement-topology",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0010-enforcement-topology",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "adr-0010-enforcement-topology",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0011-projection-trust-boundary",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "adr-0011-projection-trust-boundary",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0011-projection-trust-boundary",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0012-reuse-existing-mechanisms",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "adr-0012-reuse-existing-mechanisms",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "adr-0012-reuse-existing-mechanisms",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "architecture",
        "to": "docs-index",
        "rel": "relates-to"
      },
      {
        "from": "architecture-agent-coordination",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "architecture-agent-coordination",
        "to": "audit-log",
        "rel": "relates-to"
      },
      {
        "from": "architecture-agent-coordination",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "architecture-agent-coordination",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "architecture-dreaming",
        "to": "adr-0002-fleet-learnings-store",
        "rel": "depends-on"
      },
      {
        "from": "architecture-dreaming",
        "to": "adr-0003-promotion-oracle",
        "rel": "depends-on"
      },
      {
        "from": "architecture-dreaming",
        "to": "adr-0004-instance-to-class-abstraction",
        "rel": "depends-on"
      },
      {
        "from": "architecture-dreaming",
        "to": "adr-0005-harness-runner-boundary",
        "rel": "depends-on"
      },
      {
        "from": "architecture-dreaming",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "architecture-dreaming",
        "to": "spec-dreaming",
        "rel": "implements"
      },
      {
        "from": "audit-log",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "audit-log",
        "to": "docs-index",
        "rel": "relates-to"
      },
      {
        "from": "backtest-optimize-graph",
        "to": "audit-log",
        "rel": "relates-to"
      },
      {
        "from": "backtest-optimize-graph",
        "to": "kb-graph-and-loop-engineering",
        "rel": "depends-on"
      },
      {
        "from": "defect-classes",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "defect-classes",
        "to": "kb-domain-and-data-modelling",
        "rel": "relates-to"
      },
      {
        "from": "design-aiforward-cli",
        "to": "kb-pack-evolution",
        "rel": "implements"
      },
      {
        "from": "design-coord-collaboration-phase4",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "design-coord-collaboration-phase4",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "design-coord-collaboration-phase4",
        "to": "design-coord-core-phase1",
        "rel": "refines"
      },
      {
        "from": "design-coord-collaboration-phase4",
        "to": "design-coord-enforcement-phase2",
        "rel": "refines"
      },
      {
        "from": "design-coord-collaboration-phase4",
        "to": "design-coord-federation-phase3",
        "rel": "refines"
      },
      {
        "from": "design-coord-collaboration-phase4",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "design-coord-core-phase1",
        "to": "adr-0007-coordination-substrate",
        "rel": "implements"
      },
      {
        "from": "design-coord-core-phase1",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "design-coord-core-phase1",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "design-coord-core-phase1",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "design-coord-enforcement-phase2",
        "to": "adr-0010-enforcement-topology",
        "rel": "implements"
      },
      {
        "from": "design-coord-enforcement-phase2",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "design-coord-enforcement-phase2",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "design-coord-enforcement-phase2",
        "to": "design-coord-core-phase1",
        "rel": "refines"
      },
      {
        "from": "design-coord-federation-phase3",
        "to": "adr-0008-non-coordinating-allocation",
        "rel": "implements"
      },
      {
        "from": "design-coord-federation-phase3",
        "to": "adr-0009-artifact-class-and-derived-merge",
        "rel": "implements"
      },
      {
        "from": "design-coord-federation-phase3",
        "to": "architecture-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "design-coord-federation-phase3",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "design-coord-federation-phase3",
        "to": "design-coord-enforcement-phase2",
        "rel": "refines"
      },
      {
        "from": "design-docs-explorer-grounding-spatial-navigation",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "design-docs-explorer-grounding-spatial-navigation",
        "to": "design-language-docs-explorer",
        "rel": "depends-on"
      },
      {
        "from": "design-docs-explorer-grounding-spatial-navigation",
        "to": "docs-index",
        "rel": "documents"
      },
      {
        "from": "design-docs-explorer-grounding-spatial-navigation",
        "to": "project-memory",
        "rel": "refines"
      },
      {
        "from": "design-docs-explorer-grounding-spatial-navigation",
        "to": "proof-docs-explorer-redesign",
        "rel": "tested-by"
      },
      {
        "from": "design-language-docs-explorer",
        "to": "design-docs-explorer-grounding-spatial-navigation",
        "rel": "refines"
      },
      {
        "from": "design-language-docs-explorer",
        "to": "docs-index",
        "rel": "documents"
      },
      {
        "from": "design-native-app-ui-skill-extension",
        "to": "kb-native-client-ui-design",
        "rel": "depends-on"
      },
      {
        "from": "design-native-app-ui-skill-extension",
        "to": "kb-native-client-ui-design-comparables",
        "rel": "depends-on"
      },
      {
        "from": "design-native-app-ui-skill-extension",
        "to": "kb-native-client-ui-design-data",
        "rel": "depends-on"
      },
      {
        "from": "design-native-app-ui-skill-extension",
        "to": "spec-native-app-ui-skill-extension",
        "rel": "implements"
      },
      {
        "from": "design-pack-doctor",
        "to": "kb-pack-evolution",
        "rel": "implements"
      },
      {
        "from": "design-project-memory",
        "to": "kb-pack-evolution",
        "rel": "implements"
      },
      {
        "from": "design-rai-and-scrub",
        "to": "kb-pack-evolution",
        "rel": "implements"
      },
      {
        "from": "docs-index",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "dream-diary",
        "to": "spec-dreaming",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "forensic-review",
        "to": "forensic-review-20260802",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review",
        "to": "forensic-review-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-20260712",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "forensic-review-20260712",
        "to": "forensic-review-backlog-20260712",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-20260802",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "forensic-review-20260802",
        "to": "forensic-review-20260712",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-20260802",
        "to": "forensic-review-20260802-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-20260802-backlog",
        "to": "architecture",
        "rel": "depends-on"
      },
      {
        "from": "forensic-review-20260802-backlog",
        "to": "forensic-review-20260802",
        "rel": "refines"
      },
      {
        "from": "forensic-review-20260802-backlog",
        "to": "forensic-review-backlog-20260712",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-backlog",
        "to": "forensic-review",
        "rel": "refines"
      },
      {
        "from": "forensic-review-backlog",
        "to": "forensic-review-20260802-backlog",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-backlog-20260712",
        "to": "architecture",
        "rel": "depends-on"
      },
      {
        "from": "forensic-review-backlog-20260712",
        "to": "forensic-review-20260712",
        "rel": "refines"
      },
      {
        "from": "forensic-review-rev42",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "forensic-review-rev42",
        "to": "forensic-review",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev42",
        "to": "forensic-review-rev42-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev42-backlog",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev42-backlog",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev42-backlog",
        "to": "forensic-review-rev42",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev48",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "forensic-review-rev48",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev48",
        "to": "forensic-review-rev42",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev48",
        "to": "forensic-review-rev48-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev48",
        "to": "forensic-review-rev48-proof",
        "rel": "tested-by"
      },
      {
        "from": "forensic-review-rev48-backlog",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev48-backlog",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev48-backlog",
        "to": "forensic-review-rev42-backlog",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev48-backlog",
        "to": "forensic-review-rev48",
        "rel": "refines"
      },
      {
        "from": "forensic-review-rev48-backlog",
        "to": "forensic-review-rev48-proof",
        "rel": "tested-by"
      },
      {
        "from": "forensic-review-rev48-proof",
        "to": "forensic-review-rev48",
        "rel": "tested-by"
      },
      {
        "from": "forensic-review-rev48-proof",
        "to": "forensic-review-rev48-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev49",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "forensic-review-rev49",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev49",
        "to": "forensic-review-rev48",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev49",
        "to": "forensic-review-rev49-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev49",
        "to": "forensic-review-rev49-proof",
        "rel": "tested-by"
      },
      {
        "from": "forensic-review-rev49-backlog",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev49-backlog",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev49-backlog",
        "to": "forensic-review-rev48-backlog",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev49-backlog",
        "to": "forensic-review-rev49",
        "rel": "refines"
      },
      {
        "from": "forensic-review-rev49-backlog",
        "to": "forensic-review-rev49-proof",
        "rel": "tested-by"
      },
      {
        "from": "forensic-review-rev49-proof",
        "to": "forensic-review-rev48-proof",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev49-proof",
        "to": "forensic-review-rev49",
        "rel": "tested-by"
      },
      {
        "from": "forensic-review-rev49-proof",
        "to": "forensic-review-rev49-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev53",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "forensic-review-rev53",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev53",
        "to": "forensic-review-rev49",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev53",
        "to": "forensic-review-rev53-backlog",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev53-backlog",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev53-backlog",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "forensic-review-rev53-backlog",
        "to": "forensic-review-rev49-backlog",
        "rel": "supersedes"
      },
      {
        "from": "forensic-review-rev53-backlog",
        "to": "forensic-review-rev53",
        "rel": "relates-to"
      },
      {
        "from": "hygiene-backlog",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "hygiene-backlog",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "hygiene-remediation-plan",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "hygiene-remediation-plan",
        "to": "hygiene-backlog",
        "rel": "relates-to"
      },
      {
        "from": "investigation-blank-explainer-live",
        "to": "adr-0006-dream-manifest",
        "rel": "relates-to"
      },
      {
        "from": "investigation-blank-explainer-live",
        "to": "proposal-hosting-and-dream-manifest",
        "rel": "relates-to"
      },
      {
        "from": "investigation-fr-071",
        "to": "audit-log",
        "rel": "documents"
      },
      {
        "from": "investigation-fr-071",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "investigation-fr-071",
        "to": "forensic-review-rev53-backlog",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls",
        "to": "kb-graph-and-loop-engineering",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-comparables",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-data",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-glossary",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-open-questions",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-open-questions",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-references",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-sota",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-autopilot-controls-sources",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-focus-and-scope-control",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-focus-and-scope-control",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "kb-agent-focus-and-scope-control-glossary",
        "to": "kb-agent-focus-and-scope-control",
        "rel": "refines"
      },
      {
        "from": "kb-agent-focus-and-scope-control-open-questions",
        "to": "kb-agent-focus-and-scope-control",
        "rel": "refines"
      },
      {
        "from": "kb-agent-focus-and-scope-control-references",
        "to": "kb-agent-focus-and-scope-control",
        "rel": "refines"
      },
      {
        "from": "kb-agent-focus-and-scope-control-sota",
        "to": "kb-agent-focus-and-scope-control",
        "rel": "refines"
      },
      {
        "from": "kb-agent-focus-and-scope-control-sources",
        "to": "kb-agent-focus-and-scope-control",
        "rel": "refines"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming",
        "to": "audit-log",
        "rel": "relates-to"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming-comparables",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "refines"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming-data",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "refines"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming-glossary",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "refines"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming-open-questions",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "refines"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming-references",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "refines"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming-sota",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "refines"
      },
      {
        "from": "kb-continuous-improvement-and-dreaming-sources",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "refines"
      },
      {
        "from": "kb-ddm-comparables",
        "to": "kb-domain-and-data-modelling",
        "rel": "refines"
      },
      {
        "from": "kb-ddm-data",
        "to": "kb-domain-and-data-modelling",
        "rel": "refines"
      },
      {
        "from": "kb-ddm-glossary",
        "to": "kb-domain-and-data-modelling",
        "rel": "refines"
      },
      {
        "from": "kb-ddm-open-questions",
        "to": "kb-domain-and-data-modelling",
        "rel": "refines"
      },
      {
        "from": "kb-ddm-references",
        "to": "kb-domain-and-data-modelling",
        "rel": "refines"
      },
      {
        "from": "kb-ddm-sota",
        "to": "kb-domain-and-data-modelling",
        "rel": "refines"
      },
      {
        "from": "kb-ddm-sources",
        "to": "kb-domain-and-data-modelling",
        "rel": "refines"
      },
      {
        "from": "kb-domain-and-data-modelling",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "kb-domain-and-data-modelling",
        "to": "kb-pack-evolution",
        "rel": "relates-to"
      },
      {
        "from": "kb-graph-and-loop-engineering",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "kb-graph-and-loop-engineering",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "kb-graph-and-loop-engineering",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "relates-to"
      },
      {
        "from": "kb-graph-and-loop-engineering-comparables",
        "to": "kb-graph-and-loop-engineering",
        "rel": "refines"
      },
      {
        "from": "kb-graph-and-loop-engineering-data",
        "to": "kb-graph-and-loop-engineering",
        "rel": "refines"
      },
      {
        "from": "kb-graph-and-loop-engineering-glossary",
        "to": "kb-graph-and-loop-engineering",
        "rel": "refines"
      },
      {
        "from": "kb-graph-and-loop-engineering-open-questions",
        "to": "kb-graph-and-loop-engineering",
        "rel": "refines"
      },
      {
        "from": "kb-graph-and-loop-engineering-references",
        "to": "kb-graph-and-loop-engineering",
        "rel": "refines"
      },
      {
        "from": "kb-graph-and-loop-engineering-sota",
        "to": "kb-graph-and-loop-engineering",
        "rel": "refines"
      },
      {
        "from": "kb-graph-and-loop-engineering-sources",
        "to": "kb-graph-and-loop-engineering",
        "rel": "refines"
      },
      {
        "from": "kb-native-client-ui-design",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "kb-native-client-ui-design",
        "to": "kb-domain-and-data-modelling",
        "rel": "relates-to"
      },
      {
        "from": "kb-native-client-ui-design-comparables",
        "to": "kb-native-client-ui-design",
        "rel": "refines"
      },
      {
        "from": "kb-native-client-ui-design-data",
        "to": "kb-native-client-ui-design",
        "rel": "refines"
      },
      {
        "from": "kb-native-client-ui-design-glossary",
        "to": "kb-native-client-ui-design",
        "rel": "refines"
      },
      {
        "from": "kb-native-client-ui-design-open-questions",
        "to": "kb-native-client-ui-design",
        "rel": "refines"
      },
      {
        "from": "kb-native-client-ui-design-references",
        "to": "kb-native-client-ui-design",
        "rel": "refines"
      },
      {
        "from": "kb-native-client-ui-design-sota",
        "to": "kb-native-client-ui-design",
        "rel": "refines"
      },
      {
        "from": "kb-native-client-ui-design-sources",
        "to": "kb-native-client-ui-design",
        "rel": "refines"
      },
      {
        "from": "kb-pack-evolution",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "kb-pack-evolution-comparables",
        "to": "kb-pack-evolution",
        "rel": "refines"
      },
      {
        "from": "kb-pack-evolution-glossary",
        "to": "kb-pack-evolution",
        "rel": "refines"
      },
      {
        "from": "kb-pack-evolution-open-questions",
        "to": "kb-pack-evolution",
        "rel": "refines"
      },
      {
        "from": "kb-pack-evolution-references",
        "to": "kb-pack-evolution",
        "rel": "refines"
      },
      {
        "from": "kb-pack-evolution-sota",
        "to": "kb-pack-evolution",
        "rel": "refines"
      },
      {
        "from": "kb-pack-evolution-sources",
        "to": "kb-pack-evolution",
        "rel": "refines"
      },
      {
        "from": "lens-code-doc-join",
        "to": "lens-graph-structure",
        "rel": "relates-to"
      },
      {
        "from": "lens-graph-health",
        "to": "lens-graph-structure",
        "rel": "relates-to"
      },
      {
        "from": "lens-graph-insight",
        "to": "lens-graph-structure",
        "rel": "relates-to"
      },
      {
        "from": "lens-graph-structure",
        "to": "lens-graph-health",
        "rel": "relates-to"
      },
      {
        "from": "mockup-documentation-portal",
        "to": "design-language-docs-explorer",
        "rel": "refines"
      },
      {
        "from": "mockup-documentation-portal",
        "to": "spec-documentation-portal",
        "rel": "implements"
      },
      {
        "from": "mockup-dream-review",
        "to": "design-language-docs-explorer",
        "rel": "refines"
      },
      {
        "from": "mockup-dream-review",
        "to": "spec-dreaming",
        "rel": "implements"
      },
      {
        "from": "note-20260712-model-orchestration-policy",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "note-20260712-revert-model-orchestration",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "note-20260712-revert-model-orchestration",
        "to": "forensic-review",
        "rel": "depends-on"
      },
      {
        "from": "note-20260712-revert-model-orchestration",
        "to": "note-20260712-model-orchestration-policy",
        "rel": "supersedes"
      },
      {
        "from": "note-20260818-dream-rerun-unchanged-corpus",
        "to": "architecture-dreaming",
        "rel": "relates-to"
      },
      {
        "from": "note-20260818-dream-rerun-unchanged-corpus",
        "to": "spec-dreaming",
        "rel": "relates-to"
      },
      {
        "from": "note-20260820-spike-corpus-assertion",
        "to": "architecture-agent-coordination",
        "rel": "relates-to"
      },
      {
        "from": "note-20260820-spike-corpus-assertion",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "note-20260822-backlog-triage-and-worktree-discipline",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "note-20260822-backlog-triage-and-worktree-discipline",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "note-20260822-backlog-triage-and-worktree-discipline",
        "to": "forensic-review-rev42-backlog",
        "rel": "relates-to"
      },
      {
        "from": "note-20260823-merge-driver-resolves-not-regenerates",
        "to": "adr-0009-artifact-class-and-derived-merge",
        "rel": "relates-to"
      },
      {
        "from": "note-20260823-merge-driver-resolves-not-regenerates",
        "to": "design-coord-federation-phase3",
        "rel": "relates-to"
      },
      {
        "from": "note-autopilot-open-questions-decisions",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "note-autopilot-open-questions-decisions",
        "to": "kb-agent-autopilot-controls",
        "rel": "relates-to"
      },
      {
        "from": "note-required-status-checks",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "note-required-status-checks",
        "to": "forensic-review-rev48-backlog",
        "rel": "relates-to"
      },
      {
        "from": "plan-optimize-graph-live-01",
        "to": "audit-log",
        "rel": "relates-to"
      },
      {
        "from": "plan-optimize-graph-live-01",
        "to": "backtest-optimize-graph",
        "rel": "relates-to"
      },
      {
        "from": "plan-optimize-graph-live-01",
        "to": "kb-graph-and-loop-engineering",
        "rel": "depends-on"
      },
      {
        "from": "privacy-review",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-aiforward-cli",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-coord-core-phase1",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-coord-enforcement-phase2",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-coord-federation-phase3",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-docs-explorer-grounding-spatial-navigation",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-pack-doctor",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-project-memory",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "design-rai-and-scrub",
        "rel": "documents"
      },
      {
        "from": "privacy-review",
        "to": "forensic-review",
        "rel": "documents"
      },
      {
        "from": "project-memory",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "project-memory",
        "to": "design-project-memory",
        "rel": "implements"
      },
      {
        "from": "proof-coord-collaboration-phase4",
        "to": "design-coord-collaboration-phase4",
        "rel": "implements"
      },
      {
        "from": "proof-coord-collaboration-phase4",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "proof-docs-explorer-redesign",
        "to": "adr-0001-grounding-source-corpus-registry",
        "rel": "depends-on"
      },
      {
        "from": "proof-docs-explorer-redesign",
        "to": "design-docs-explorer-grounding-spatial-navigation",
        "rel": "relates-to"
      },
      {
        "from": "proof-docs-explorer-redesign",
        "to": "design-language-docs-explorer",
        "rel": "depends-on"
      },
      {
        "from": "proof-docs-explorer-redesign",
        "to": "privacy-review",
        "rel": "relates-to"
      },
      {
        "from": "proof-docs-explorer-redesign",
        "to": "threat-model",
        "rel": "relates-to"
      },
      {
        "from": "proof-native-app-ui-skill-extension",
        "to": "design-native-app-ui-skill-extension",
        "rel": "tested-by"
      },
      {
        "from": "proof-native-app-ui-skill-extension",
        "to": "spec-native-app-ui-skill-extension",
        "rel": "tested-by"
      },
      {
        "from": "proposal-hosting-and-dream-manifest",
        "to": "adr-0002-fleet-learnings-store",
        "rel": "relates-to"
      },
      {
        "from": "proposal-hosting-and-dream-manifest",
        "to": "adr-0006-dream-manifest",
        "rel": "relates-to"
      },
      {
        "from": "proposal-hosting-and-dream-manifest",
        "to": "architecture-dreaming",
        "rel": "relates-to"
      },
      {
        "from": "proposal-hosting-and-dream-manifest",
        "to": "spec-documentation-portal",
        "rel": "relates-to"
      },
      {
        "from": "proposal-turn-goal-state-and-stopping",
        "to": "audit-log",
        "rel": "relates-to"
      },
      {
        "from": "proposal-turn-goal-state-and-stopping",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "proposal-turn-goal-state-and-stopping",
        "to": "kb-graph-and-loop-engineering",
        "rel": "depends-on"
      },
      {
        "from": "proposal-turn-goal-state-and-stopping",
        "to": "plan-optimize-graph-live-01",
        "rel": "relates-to"
      },
      {
        "from": "proposal-turn-goal-state-and-stopping",
        "to": "project-memory",
        "rel": "relates-to"
      },
      {
        "from": "spec-agent-coordination",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "spec-agent-coordination",
        "to": "audit-log",
        "rel": "relates-to"
      },
      {
        "from": "spec-agent-coordination",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "spec-agent-coordination",
        "to": "spec-dreaming",
        "rel": "relates-to"
      },
      {
        "from": "spec-collaborate-skill",
        "to": "design-coord-collaboration-phase4",
        "rel": "refines"
      },
      {
        "from": "spec-collaborate-skill",
        "to": "spec-agent-coordination",
        "rel": "implements"
      },
      {
        "from": "spec-design-slice-rename",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "spec-design-slice-rename",
        "to": "design-native-app-ui-skill-extension",
        "rel": "relates-to"
      },
      {
        "from": "spec-documentation-portal",
        "to": "architecture",
        "rel": "refines"
      },
      {
        "from": "spec-documentation-portal",
        "to": "design-language-docs-explorer",
        "rel": "depends-on"
      },
      {
        "from": "spec-documentation-portal",
        "to": "docs-index",
        "rel": "relates-to"
      },
      {
        "from": "spec-dreaming",
        "to": "audit-log",
        "rel": "relates-to"
      },
      {
        "from": "spec-dreaming",
        "to": "defect-classes",
        "rel": "relates-to"
      },
      {
        "from": "spec-dreaming",
        "to": "kb-continuous-improvement-and-dreaming",
        "rel": "implements"
      },
      {
        "from": "spec-native-app-ui-skill-extension",
        "to": "architecture",
        "rel": "relates-to"
      },
      {
        "from": "spec-native-app-ui-skill-extension",
        "to": "kb-native-client-ui-design",
        "rel": "depends-on"
      },
      {
        "from": "threat-model",
        "to": "architecture",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-aiforward-cli",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-coord-core-phase1",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-coord-enforcement-phase2",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-coord-federation-phase3",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-docs-explorer-grounding-spatial-navigation",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-pack-doctor",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-project-memory",
        "rel": "documents"
      },
      {
        "from": "threat-model",
        "to": "design-rai-and-scrub",
        "rel": "documents"
      },
      {
        "from": "ui-capability-guide",
        "to": "design-language-docs-explorer",
        "rel": "relates-to"
      },
      {
        "from": "ui-capability-guide",
        "to": "docs-index",
        "rel": "relates-to"
      },
      {
        "from": "ui-review-pack-explainer",
        "to": "docs-index",
        "rel": "relates-to"
      },
      {
        "from": "ui-review-pack-explainer",
        "to": "ui-capability-guide",
        "rel": "relates-to"
      }
    ],
    "types": [
      "adr",
      "architecture",
      "decision-note",
      "design",
      "design-language",
      "doc",
      "glossary",
      "investigation",
      "knowledge",
      "privacy-review",
      "proof-pack",
      "spec",
      "threat-model"
    ]
  },
  "surfaces": [
    {
      "name": "Docs Explorer",
      "path": "../index.html",
      "what": "Browse/graph/mind-map the knowledge graph of artifacts."
    },
    {
      "name": "UI Guide",
      "path": "../ui-guide.html",
      "what": "The how-to layer over the seven UI standards."
    },
    {
      "name": "Fleet learnings",
      "path": "../../learnings/fleet-classes.md",
      "what": "Promoted, abstracted, general classes + controls the fleet has learned (public)."
    },
    {
      "name": "Whole-pack index",
      "path": "../../web/index.html",
      "what": "Searchable index of every artifact + the narrative explainer."
    },
    {
      "name": "Audit viewer",
      "path": "../audit/index.html",
      "what": "Timeline + search over the durable audit & change log.",
      "localOnly": true
    },
    {
      "name": "Dream review",
      "path": "../dreams/",
      "what": "Approve proposed learnings from a dream pass.",
      "localOnly": true
    }
  ]
};
