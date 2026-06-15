---
id: kb-pack-evolution-references
title: "Pack Evolution — References"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [responsible-ai, nist, standards, tooling]
links:
  - { to: kb-pack-evolution, rel: refines }
review-by: "2026-09-12"
summary: >-
  Standards (MS RAI Standard, NIST AI RMF, EU AI Act/GDPR), the pack's own contracts the capabilities
  conform to (knowledge-visualization V1–V18, INSTALL deployment map, engineering-governance), and tooling references.
---

# Reference information

## Standards & frameworks (suggestion #4 — RAI)

- **Microsoft Responsible AI Standard (v2)** — the principle set the RAI policy doc adopts: Fairness, Reliability & Safety, Privacy & Security, Inclusiveness, Transparency, Accountability. Requires goals, controls, and documented evidence per principle. *(Verified — https://www.microsoft.com/en-us/ai/responsible-ai)*
- **NIST AI Risk Management Framework (AI RMF 1.0)** — the lifecycle control model the policy doc maps to: the four functions **Govern, Map, Measure, Manage**, each with categories/subcategories. The pairing "MS principles + NIST functions" is the 2025 norm for a credible, auditable policy. *(Verified — https://www.nist.gov/itl/ai-risk-management-framework)*
- **EU AI Act / GDPR** — named as the regulatory backdrop the policy's "compliance & auditability" and "privacy" sections must acknowledge; the pack's Privacy persona already carries residency/lawful-basis/rights-path concerns. *(Verified — RAI research; engineering-governance.md §4)*

## Specifications & primary sources (the pack's own contracts)

- **`knowledge-visualization.md` (V1–V18)** — the authoritative model for memory-as-graph: V2 (frontmatter is the record), V13 (freshness SLAs + ownership), V14 (glossary + relation registry), V16 (change-impact propagation), V17 (decision notes = session exhaust), V18 (all graph mechanics via `docs-graph.py`). **§0 + V2 state `docs/` is a valid Obsidian vault.** The memory design MUST conform to this. *(Verified — pack file)*
- **`adapters/INSTALL.md`** — the deployment map (every source path → destination per tool) + the `revision`/`changes` changelog convention. The CLI, doctor, and scrub must deploy through this map; the RAI doc + memory convention become `changes` entries. *(Verified — pack file)*
- **`engineering-governance.md`** — §3 Threat model (STRIDE), §4 Privacy & data governance, §5 Accessibility, §9 Supply chain. The RAI policy doc *maps onto* this checklist rather than duplicating it. *(Verified — pack file)*
- **Rules of the Road** + **Persona Operating Standard (`persona-audit.md` §8)** — the human-in-the-loop gates and the Privacy/Security hard vetoes that the RAI policy formalizes as a stance. *(Verified — pack files)*

## Tooling references (suggestions #1, #2, #4)

- **Existing stdlib-only pack scripts** — `docs/ai-forward-pack/scripts/docs-graph.py` (`inventory|validate|derive|freshness|flag|clear-flag|stub|snapshot|rollup`), `pack/scripts/foundation-check.py`, `tools/check-consistency.py`, `tools/new-capability.py`. The CLI dispatches to these; the doctor composes `docs-graph.py`. All Python 3.8+, no third-party imports — the binding convention for any new script. *(Verified — files; `docs-graph.py --help`)*
- **`tools/sync-pack.ps1` / `tools/verify-bundle.ps1`** — the canonical sync engine and the consistency proof (`BUNDLE CONSISTENT`). The CLI's `update`/`verify` shell out to these; PowerShell stays the engine. *(Verified — files)*
- **Microsoft Presidio** — NLP PII detection/anonymization, CI-integrable (the CI-grade PII tool the scrub points at, not vendored). *(Verified — https://github.com/microsoft/presidio)*
- **gitleaks** / **detect-secrets** (Yelp) / **TruffleHog** — secret scanners for CI/pre-commit (the CI-grade secret tools the scrub points at). *(Verified — https://github.com/gitleaks/gitleaks)*
- **git-filter-repo / BFG Repo-Cleaner** — history rewriting to *purge* a leaked secret (the scrub redacts going forward; these remove what already leaked). *(Verified — PII/secret-scrub research)*

## Seminal / foundational (memory + PKM, suggestion #3)

- **Zettelkasten / PKM practice** (Luhmann tradition; Obsidian community) — atomic notes, links over folders, Maps of Content. Already the basis of `knowledge-visualization.md`; cited here to confirm the memory ledger should be *linked into the graph*, not a siloed log. *(Verified — knowledge-visualization.md §0 References)*
