---
id: kb-pack-evolution-open-questions
title: "Pack Evolution — Open Questions & Failure Modes"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [risks, pii, memory, responsible-ai, disconfirmation]
links:
  - { to: kb-pack-evolution, rel: refines }
review-by: "2026-09-12"
summary: >-
  Flagged unknowns (regex-scrub recall, ledger freshness, CLI cross-shell), the domain's failure modes
  (runtime creep, drift, RAI theater, Obsidian lock-in, doctor false confidence), and disconfirming views sought.
---

# Open questions & domain failure modes

## Unresolved by research (Flagged)

- **Regex-scrub recall (load-bearing Flagged).** A stdlib regex scrubber will miss PII/secrets that NLP (Presidio) or entropy/rule engines (gitleaks/TruffleHog) catch — names, contextual identifiers, novel token shapes. *What we'd need to settle it:* a labeled corpus of real pack/memory leakage. *Current best guess:* ship the regex pass for the *obvious* cases (emails, common key prefixes), label its limits loudly, and point at CI-grade tools — never claim sufficiency. *(Flagged — PII/secret-scrub research is clear regex is a *supplement*)*
- **Will a rolling project-memory ledger stay current? (load-bearing Flagged).** Decision notes (V17) are captured "before close," but a free-form ledger can rot like any log. *What we'd need:* either a freshness gate over it (V13-style `review-by`) or a discipline that skills *append on convergence*. *Current best guess:* make appending part of the skills' "last action" and give the ledger a `review-by`, so the existing freshness machinery surfaces staleness. *(Flagged — generalizing from V13; not yet proven in practice)*
- **CLI ergonomics across shells.** A Python dispatcher runs everywhere Python does, but it shells out to PowerShell (`sync`/`verify`) — on a machine with only `pwsh`-less PowerShell or none, those subcommands degrade. *Best guess:* detect `pwsh`, and have the CLI print the exact manual command when a dependency is absent rather than failing opaquely. *(Flagged — environment-dependent; mitigated by clear messaging)*

## Known failure modes of this domain

- **Adding a runtime to a methodology pack.** The biggest risk is letting "a CLI" or "memory" smuggle in a service, a daemon, or a dependency that breaks the zero-install, tool-neutral promise. Mitigation: every capability is committed Markdown + stdlib script; no process, no third-party import. *(Verified — repo identity; Simplifier veto)*
- **Drift between the new capabilities and the docs.** New scripts/skills that don't update counts, managed-block lists, or the changelog reintroduce exactly the drift the consistency gate exists to stop. Mitigation: ship via `/extendaibundle`; `verify-bundle.ps1` must print `BUNDLE CONSISTENT`. *(Verified — prior session; CI gate)*
- **RAI theater.** A policy doc that *states* principles but maps to nothing enforceable is decoration. Mitigation: every principle row links to the **existing persona/template/gate** that actually enforces it, and the governance checklist references it. *(Verified — engineering-governance.md exists to be that enforcement)*
- **Obsidian lock-in by accident.** If memory tooling starts *depending* on Obsidian plugins (Dataview queries embedded in canonical docs), the "works without Obsidian" promise breaks. Mitigation: canonical docs stay plain Markdown + the pack's own `docs-graph.py`; Obsidian config is optional and git-ignored by default. *(Verified — Obsidian downsides research)*
- **Doctor false confidence.** A doctor that only checks file presence can pass while the install is subtly broken (stale graph, wrong revision). Mitigation: compose `docs-graph.py validate|freshness`, not just `Test-Path`. *(Inferred from the `git fsck` analogue)*

## Disconfirming views we deliberately sought

- **"Just use Squad / a real runtime."** The strongest counter to building these into a Markdown pack is that Squad already does them in a maintained product. It fares poorly *for our goal*: Squad is a runtime with parallel agents and per-agent memory; AI-Forward's value is the **reasoning/governance methodology**, which is tool-neutral and dependency-free by design. Adopting Squad wholesale would discard that identity. The right move is to borrow **intent**, re-expressed in our form. *(Verified — prior comparison; this is the load-bearing framing)*
- **"Make Obsidian the system of record."** Counter-argument: Obsidian gives the richest memory UX out of the box. It fares poorly as a *requirement* because of per-contributor setup, plugin fragility, and the loss of tool-neutrality — so it is adopted as an **optional lens**, which captures the upside without the lock-in. *(Verified — Obsidian research)*
- **"Vendor Presidio/gitleaks for real PII protection."** Counter: they are more accurate. They fare poorly as a *shipped dependency* (the pack is stdlib-only and installs into arbitrary repos). Resolution: regex first-pass in the pack, explicit pointer to those tools for CI. *(Verified — PII research)*
