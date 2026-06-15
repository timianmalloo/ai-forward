---
id: kb-pack-evolution
title: "Pack Evolution — CLI, Doctor, Project Memory, RAI (domain knowledge)"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [cli, doctor, memory, obsidian, responsible-ai, pii, squad]
links:
  - { to: architecture, rel: relates-to }
review-by: "2026-09-12"
summary: >-
  Sourced evidence base for four capabilities AI-Forward is considering adopting from
  agent-orchestration products (notably bradygaster/squad): a unified CLI, an installed-repo
  doctor, persistent project memory (and whether to introduce Obsidian), and a committed
  Responsible-AI policy plus a PII/secret scrub. Every load-bearing claim is confidence-labeled.
---

# Pack Evolution — domain knowledge

**Domain & problem:** AI-Forward is a Markdown methodology pack (reasoning spine + 23 persona lenses + 13 skills) that installs into a repo for Claude Code and GitHub Copilot. We are evaluating four capabilities borrowed from runtime agent-orchestration products — **(1) a unified CLI**, **(2) an installed-repo `doctor`**, **(3) persistent project memory** (with an explicit Obsidian decision), and **(4) a committed Responsible-AI policy + a PII/secret scrub** — and must decide *whether* and *how* to adopt each **without compromising the pack's identity** (tool-neutral, dependency-averse, zero-drift, human-in-the-loop).

**Canonical framing:** the industry frames these as features of an *agent runtime/product* (Squad ships them as TypeScript/npm). Our framing differs and that difference is load-bearing: AI-Forward is a **methodology pack, not a runtime**, so each capability must be re-expressed as **committed Markdown + stdlib-only scripts**, not as a service or a new runtime dependency. Adopting the *intent* while rejecting the *form* is the through-line.

**Compiled:** 2026-06-14 · **Lead:** Domain Researcher · **Status:** fresh

## Headline findings

1. **The CLI should be a single-file, stdlib-only Python dispatcher over the existing scripts — not npm/pipx/a binary.** Every pack script today is stdlib-only Python (`docs-graph.py`, `check-consistency.py`, `new-capability.py`) plus PowerShell; a Node/npm CLI (Squad's choice) would import an ecosystem the pack deliberately avoids. A repo-local `python tools/aiforward.py <command>` is genuinely zero-install for anyone who can already run the pack's scripts. — *(Verified — repo convention: all of `tools/*.py` and `pack/scripts/*.py` are stdlib-only; CLI-distribution research §"repo-hosted scripts" confirms repo-local Python is the zero-install path)*
2. **`doctor` is a well-established, low-risk pattern, but the installed-repo doctor is a *different check* from the source consistency gate.** `check-consistency.py` validates the **source** (`pack/` filesystem == docs counts); a `doctor` validates an **installed** repo (pack present? which revision? both tool surfaces present? managed blocks intact? graph derivable/fresh?). It composes the existing `docs-graph.py validate|freshness` rather than reinventing it. — *(Verified — `tools/check-consistency.py` is source-only; `docs/ai-forward-pack/scripts/docs-graph.py` already exposes `validate`/`freshness`; doctor precedent: npm/brew/squad `doctor`, `git fsck`)*
3. **The pack already has a project-memory substrate; what it lacks is a rolling, append-only ledger that skills read on grounding.** The knowledge graph (V2 frontmatter), decision notes (V17), the glossary (V14), and the Docs Explorer are durable, git-committed, tool-neutral memory. Squad's per-agent `history.md`/`decisions.md` is the missing *shape*: a continuously-accreting project ledger. The fill is a **convention + a graph-linked `project-memory` doc**, not a new store. — *(Verified — `knowledge-visualization.md` V13/V14/V17; Squad README "What Gets Created" + per-agent `history.md`)*
4. **Obsidian should be adopted as an *optional lens*, never a dependency — because the pack already designed `docs/` to be a valid Obsidian vault.** `knowledge-visualization.md` states verbatim that the per-file frontmatter makes `docs/` "a valid Obsidian vault (Properties, Bases tables, and Obsidian's graph view all read this frontmatter natively)." So Obsidian is **already compatible at zero cost**; making it *required* would impose the per-contributor setup + plugin-fragility the research warns about and violate the pack's tool-neutrality. Recommendation: document the existing compatibility + ship an optional, git-ignored-by-default `.obsidian/` convenience, keep canonical memory in the committed graph. — *(Verified — `knowledge-visualization.md` §0 + V2; Obsidian/git research on downsides: onboarding curve, plugin reliability, per-contributor setup)*
5. **A committed RAI policy is on-brand and mostly *assembly*, not new invention.** Microsoft's Responsible AI Standard (principles) + NIST AI RMF (Govern/Map/Measure/Manage) are the two anchors; the pack already operationalizes most of both through the Privacy & Data Governance persona, the Security persona, the threat-model and privacy-review templates, and the human-in-the-loop Rules of the Road. The gap is a **single committed artifact** that states the stance and *maps* it to those existing lenses. — *(Verified — MS RAI Standard v2 + NIST AI RMF; pack already ships `persona-cards.md`, `engineering-governance.md` §3–4, `templates/{threat-model,privacy-review}.template.md`)*
6. **The PII/secret scrub should be a stdlib-only regex first-pass, explicitly labeled as not a substitute for gitleaks/Presidio in CI.** Presidio (NLP PII) and gitleaks/detect-secrets (secrets) are the heavy, accurate tools — but both are external dependencies. A stdlib regex scrubber (emails, common token/secret shapes) matches the pack's existing scripts and Squad's own lightweight `scrub-emails`; honesty requires labeling its recall limits and pointing at the real CI tools. — *(Verified — PII/secret-scrub research recommends Presidio+gitleaks but confirms regex as the lightweight supplement; Squad ships `squad scrub-emails`; pack convention = stdlib-only)*

## Confidence summary
- **Verified: 6 · Inferred: 0 · Flagged: 2** (recorded in `open-questions.md`).
- Load-bearing Flagged claims: (a) the *long-term maintenance cost* of a regex scrubber's false-negative rate; (b) whether a rolling project-memory ledger will be *kept current by agents* without a freshness gate. Both are design risks, not blockers.

## Design implications (what the next phase should do with this)
- **CLI (#1):** build `tools/aiforward.py` (stdlib-only) as a thin dispatcher — `init`/`update`/`extend` map to the meta-skills' mechanics, `verify` → `verify-bundle.ps1`, `doctor` → the new doctor, `graph` → `docs-graph.py`. It is a *convenience entry point*, not new logic. Keep PowerShell as the canonical sync engine; the CLI shells out.
- **Doctor (#2):** ship a **deployable** `doctor` (lands in installed repos via the deployment map) that reports revision, both-tool-surface presence, managed-block integrity, and graph health (composing `docs-graph.py`). Distinct from the source-only `check-consistency.py`.
- **Memory (#3):** add a **project-memory convention** — a graph-linked, append-only `docs/project-memory.md` (+ the existing decision-notes flow) that skills read at grounding and append to at convergence; document the **already-true Obsidian compatibility** and ship an optional `.obsidian/` workspace; do **not** make Obsidian required.
- **RAI (#4):** add a committed **RAI policy knowledge doc** (principles ← MS RAI; lifecycle controls ← NIST RMF) that *maps to the existing personas/templates*, plus a stdlib **`scrub.py`** redaction script labeled as a first-pass. Wire both into the governance checklist.
- **Cross-cutting:** every one of these is a **pack capability**, so it ships through `/extendaibundle` and must pass `verify-bundle.ps1` (BUNDLE CONSISTENT) — both tool surfaces, reconciled counts, bumped revision.

## How to use this base
Personas and the `/design` and `/extendaibundle` skills cite these files as evidence (BoK §III.1). Refresh when Squad moves or when the RAI standards revise; re-run `/collectknowledge` and bump the date above.
