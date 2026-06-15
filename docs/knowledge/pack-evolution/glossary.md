---
id: kb-pack-evolution-glossary
title: "Pack Evolution — Glossary"
type: glossary
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [glossary, cli, doctor, memory, responsible-ai]
links:
  - { to: kb-pack-evolution, rel: refines }
review-by: "2026-09-12"
summary: >-
  The ubiquitous language for the pack-evolution work: pack-lifecycle skill, source consistency vs install
  health, doctor, project memory / ledger, Obsidian vault, RAI policy, scrub, stdlib-only, zero-drift.
---

# Glossary — ubiquitous language for pack evolution

- **Pack-lifecycle skill** — a skill that operates on the pack *installation* rather than a project's product (e.g. `/addpacktorepo`, `/updatepack`, `/extendaibundle`). The CLI, doctor, memory, and RAI capabilities are delivered as or alongside these. <!-- use this exact term --> *(Verified — pack convention)*
- **Source consistency** — agreement between the `pack/` filesystem and the documentation that counts it (checked by `tools/check-consistency.py`, source-only). *Distinct from* install health. *(Verified)*
- **Install health** — the state of a *target* repo that has the pack installed: correct revision, both tool surfaces present, managed blocks intact, graph derivable/fresh. The **doctor** reports this. A target repo has no `pack/`, so install health ≠ source consistency. *(Verified)*
- **Doctor** — a deployable diagnostic command that reports install health as PASS/WARN/FAIL with suggested fixes and a nonzero exit on failure (after `npm/brew/squad doctor`). *(Verified)*
- **Project memory** — the durable, git-committed, tool-neutral record of what a project has learned and decided. In AI-Forward it is the **knowledge graph + decision notes + glossary + a rolling `project-memory` ledger** — *not* a runtime store and *not* per-agent. *(Verified — knowledge-visualization.md)*
- **Project-memory ledger** — the proposed append-only `docs/project-memory.md`: a graph-linked, chronologically-accreting summary of decisions/learnings that the grounding step of every skill reads, and convergence appends to. Complements (does not replace) per-artifact frontmatter and decision notes. *(Inferred — new convention proposed by this base)*
- **Obsidian vault (here)** — the existing `docs/` tree viewed in Obsidian, which reads the V2 frontmatter natively (Properties, graph, Dataview). An **optional lens** over project memory, never the system of record. *(Verified — knowledge-visualization.md §0/V2)*
- **RAI policy** — a single committed Markdown artifact stating AI-Forward's Responsible-AI stance, with principles mapped to Microsoft RAI and lifecycle controls mapped to NIST AI RMF, and each mapped to the **existing** persona/template that enforces it. *(Verified — MS RAI + NIST RMF)*
- **Scrub (first-pass)** — stdlib regex redaction of obvious PII (emails) and common secret shapes from committed Markdown, explicitly **not** a substitute for gitleaks/Presidio in CI. The analogue of Squad's `scrub-emails`. *(Verified — Squad; PII research)*
- **Stdlib-only** — Python 3.8+ with no third-party imports: the binding constraint on every script the pack ships, the reason the CLI is Python-not-npm and the scrub is regex-not-Presidio. *(Verified — repo convention)*
- **Zero-drift** — the invariant that source and both tool installs never diverge, proven by `verify-bundle.ps1` printing `BUNDLE CONSISTENT`. Every capability added here must end zero-drift. *(Verified — verify-bundle.ps1; prior memory)*
