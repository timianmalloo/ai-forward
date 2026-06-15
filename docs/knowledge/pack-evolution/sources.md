---
id: kb-pack-evolution-sources
title: "Pack Evolution — Sources"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [sources, citations]
links:
  - { to: kb-pack-evolution, rel: refines }
review-by: "2026-09-12"
summary: >-
  The full source list with access dates for the pack-evolution knowledge base — Squad, the pack's own
  files, the MS RAI and NIST RMF standards, the scrub tooling, and the web research rows.
---

# Sources

| # | Title / source | Type | URL | Accessed | Used for |
|---|---|---|---|---|---|
| 1 | bradygaster/squad — repository + README | primary | https://github.com/bradygaster/squad | 2026-06-14 | All four suggestions' comparable; CLI/doctor/memory/scrub framing |
| 2 | AI-Forward `knowledge-visualization.md` (V1–V18) | primary (pack) | pack/knowledge/knowledge-visualization.md | 2026-06-14 | Memory-as-graph model; **verbatim "valid Obsidian vault"** fact; freshness/decision-notes |
| 3 | AI-Forward `adapters/INSTALL.md` (deployment map + changelog) | primary (pack) | pack/adapters/INSTALL.md | 2026-06-14 | Where CLI/doctor/scrub/RAI deploy; revision/changes convention |
| 4 | AI-Forward `engineering-governance.md` (§3–5, §9) | primary (pack) | pack/knowledge/engineering-governance.md | 2026-06-14 | RAI policy maps onto this checklist |
| 5 | AI-Forward scripts (`docs-graph.py`, `check-consistency.py`, `new-capability.py`, `verify-bundle.ps1`, `sync-pack.ps1`) | primary (pack) | tools/, docs/ai-forward-pack/scripts/ | 2026-06-14 | Stdlib-only convention; what the CLI dispatches to / doctor composes |
| 6 | Microsoft Responsible AI Standard (v2) | standard | https://www.microsoft.com/en-us/ai/responsible-ai | 2026-06-14 | RAI policy principles |
| 7 | NIST AI Risk Management Framework (AI RMF 1.0) | standard | https://www.nist.gov/itl/ai-risk-management-framework | 2026-06-14 | RAI policy lifecycle controls (Govern/Map/Measure/Manage) |
| 8 | Microsoft Presidio | secondary (tool) | https://github.com/microsoft/presidio | 2026-06-14 | CI-grade PII tool the scrub points at (not vendored) |
| 9 | gitleaks | secondary (tool) | https://github.com/gitleaks/gitleaks | 2026-06-14 | CI-grade secret tool the scrub points at (not vendored) |
| 10 | Web research — RAI policy contents (MS + NIST) for an AI dev tool, 2025 | secondary | web_search 2026-06-14 | RAI doc structure |
| 11 | Web research — PII/secret scrubbing tools 2025 (Presidio, gitleaks, regex, detect-secrets, TruffleHog, BFG) | secondary | web_search 2026-06-14 | Scrub design + honest limits |
| 12 | Web research — Obsidian as git-backed doc vault (frontmatter, graph, downsides) 2025 | secondary | web_search 2026-06-14 | Obsidian-as-optional-lens decision |
| 13 | Web research — cross-platform dev CLI distribution 2025 (single-file Python, pipx, npx, binary, zero-install) | secondary | web_search 2026-06-14 | CLI = stdlib-only Python dispatcher decision |

*Note on confidence: pack-internal sources (#2–5) are Verified primary for repo facts; the standards (#6–7) are Verified for principles; the web-research rows (#10–13) corroborate fast-moving tooling guidance and are Verified where they agree with a primary tool source, otherwise contributed to Flagged claims in `open-questions.md`.*
