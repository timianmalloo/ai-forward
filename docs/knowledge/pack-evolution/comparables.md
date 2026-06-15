---
id: kb-pack-evolution-comparables
title: "Pack Evolution — Comparables"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [squad, comparables, cli, doctor, memory, responsible-ai]
links:
  - { to: kb-pack-evolution, rel: refines }
review-by: "2026-09-12"
summary: >-
  Squad-vs-AI-Forward capability comparison for the four suggestions, what to borrow (intent) and
  what to reject (runtime form), plus adjacent doctor/changesets/Dataview patterns worth borrowing.
---

# Comparable solutions & problem framings

The primary comparable is **bradygaster/squad** (analyzed directly from its repo + README, 2026-06). Each row maps a Squad capability to what AI-Forward already has and what adopting the *intent* (not the *form*) implies.

| Capability | How Squad frames & solves it | What AI-Forward has today | Does well (Squad) | Does badly / cost (for us) | Confidence |
|---|---|---|---|---|---|
| **Unified CLI** | `@bradygaster/squad-cli` — a published npm/TypeScript CLI, ~17 commands (`init`, `upgrade`, `doctor`, `status`, `watch`, `export`…) | Loose scripts: `sync-pack.ps1`, `verify-bundle.ps1`, `check-consistency.py`, `new-capability.py`, `docs-graph.py`; meta-skills `/addpacktorepo` `/updatepack` `/extendaibundle` | One memorable entry point; discoverable `--help`; upgrade path | npm = a runtime dependency the pack avoids; TS build chain we don't want | Verified [Squad README] |
| **Doctor / status** | `squad doctor` (alias `heartbeat`), `squad status`, `watch --health` — environment + install diagnostics | `check-consistency.py` (source-only); `docs-graph.py validate/freshness` (graph) | One command to answer "is my setup OK?" | We have no *installed-repo* health check; check-consistency is source-only | Verified [Squad README; repo] |
| **Persistent memory** | Per-agent `charter.md`+`history.md`, team `decisions.md`, `squad nap` compaction, tiered-memory proposals; committed to git | Knowledge graph (V2 frontmatter), decision notes (V17), glossary (V14), freshness SLAs (V13), Docs Explorer | Knowledge compounds per agent across sessions; clone = inherit the memory | Per-*agent* memory implies a runtime with agents; we have lenses, not processes | Verified [Squad README; knowledge-visualization.md] |
| **Obsidian / vault view** | Not Squad — but the PKM/Zettelkasten tradition Squad's docs echo | `docs/` is *already* a valid Obsidian vault (frontmatter Properties + graph view) per knowledge-visualization.md §0 | Free graph/Properties/Dataview over existing memory | Requiring it adds per-contributor setup + plugin fragility | Verified [knowledge-visualization.md] |
| **Responsible AI** | Committed `rai-charter.md` + `rai-policy.md`; PII scrub; reviewer lockout; file-write guards; PII scrubbing in the SDK | Privacy & Security personas; threat-model + privacy-review templates; engineering-governance §3–4; human-in-loop gates | A single visible RAI artifact anyone can read | We have the controls but no one *policy doc* that names the stance | Verified [Squad README/templates; pack] |
| **PII / secret scrub** | `squad scrub-emails [dir]` — lightweight redaction of state files | None (privacy persona reviews, but no mechanical scrub) | A one-command redaction before sharing state | Regex recall is limited; must not be sold as CI-grade | Verified [Squad README] |

## Adjacent problems worth borrowing from

- **`npm doctor` / `brew doctor` / `flutter doctor`** — the canonical "diagnose my install, PASS/WARN/FAIL, suggest the fix, nonzero on failure" UX. Borrow the *output shape* directly for our doctor. *(Verified — common knowledge)*
- **`git fsck`** — integrity-check-of-the-repo framing; our graph-health (`docs-graph.py validate`) is the analogue, and the doctor should surface it. *(Verified)*
- **Changesets** (Squad's release tool) — per-change fragments instead of one global version. Noted as a *future* option for our INSTALL `revision`, but not adopted now (single-maintainer; the global revision works). *(Verified — Squad README; deferred per Simplifier)*
- **Dataview (Obsidian plugin)** — querying frontmatter (`status`, `review-by`) is exactly our freshness/health view; it validates that our frontmatter schema is the right substrate for a memory lens. *(Verified — Obsidian research)*

## What we deliberately are NOT borrowing (the Simplifier's cut)

- **A runtime / parallel agent processes, Ralph/Watch autonomy, casting/themes, distributed mesh, KEDA** — these serve Squad's nature as a *runtime product*; they are anti-fits for a reasoning/governance pack and were rejected in the prior comparison. *(Verified — prior analysis; Simplifier veto on scope sprawl)*
- **npm/TypeScript distribution** — rejected in favor of stdlib Python to preserve the dependency-free install. *(Verified — repo convention)*
- **Presidio/gitleaks as a *shipped dependency*** — referenced as the CI-grade tools, but not vendored; the pack ships a regex first-pass and points at them. *(Verified)*
