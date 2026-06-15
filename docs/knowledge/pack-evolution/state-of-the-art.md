---
id: kb-pack-evolution-sota
title: "Pack Evolution — State of the Art"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [cli, doctor, memory, obsidian, responsible-ai]
links:
  - { to: kb-pack-evolution, rel: refines }
review-by: "2026-09-12"
summary: >-
  Current best practice for the four capabilities: CLI distribution (repo-local stdlib Python wins),
  the doctor pattern, persistent project/agent memory, Obsidian as an optional lens, and RAI policy + PII scrubbing.
---

# State of the art — pack evolution (CLI · doctor · memory · RAI)

## 1. Developer CLI distribution (for suggestion #1)

- **Repo-local single-file script** — the genuine zero-install path when users can already run the project's scripts. `python ./tool.py <args>`; no packaging, no runtime added. Best for *intra-repo* tooling. *(Verified — CLI-distribution research, "Zero-Install Approaches"; matches AI-Forward where contributors already run `tools/*.py`)*
- **pipx / npx** — one-command global installs, but each *assumes a runtime* (Python+pipx, or Node) the user may not have. npx is the strongest "try-now" story but is Node-native; wrapping a Python tool in npm needs a JS launcher or `pkg` bundling. *(Verified — same source)*
- **Standalone binary** (PyInstaller/Nuitka/shiv) — best for non-Python end users, worst for maintenance (per-OS builds, large artifacts, manual update). Overkill for a tool whose audience already has the repo. *(Verified — same source)*
- **Frontier/trend:** "the script is already in the repo, so it is already zero-install" is the dominant guidance for dev-only tooling; ship binaries only for a broad non-developer audience. *(Verified)*

**Read for us:** AI-Forward's audience is developers who have cloned a repo and run Claude Code / Copilot; a stdlib-only Python dispatcher is the on-brand zero-install choice. A binary or npm package would *add* the very dependency surface the pack avoids.

## 2. The `doctor` pattern (for suggestion #2)

- **Established precedent:** `npm doctor`, `brew doctor`, `flutter doctor`, `gh` status, `git fsck`, and **`squad doctor`** all follow one shape — inspect the environment/install, report PASS/WARN/FAIL per check, suggest the fix, exit nonzero on failure. *(Verified — Squad README "All Commands"; common knowledge of npm/brew/flutter)*
- **What a *methodology-pack* doctor checks (synthesized):** is the pack installed at all; the installed **revision** (from `docs/ai-forward-pack/INSTALL.md`); presence of **both tool surfaces** (`.claude/` and `.github/{instructions,prompts,agents}`); **managed-block integrity** in `CLAUDE.md`/`AGENTS.md`; and **graph health** (schema-valid frontmatter, no dangling links, freshness) — the last by composing the already-shipped `docs-graph.py validate|freshness`. *(Inferred from the deployment map + existing scripts — but each individual check is Verified against an existing artifact)*
- **Frontier:** "self-diagnosing installs" are standard; the novel-for-us part is that our doctor must run in a **target** repo (which has no `pack/` source), so it checks *install* health, not *source* consistency.

## 3. Persistent project / agent memory (for suggestion #3)

- **Squad's model:** every agent owns a `charter.md` (identity) and a **`history.md`** (what it learned about *your* project); team-wide decisions accrete in **`decisions.md`**; `squad nap` compresses/prunes/archives. Memory is committed to git so "anyone who clones gets the team — with accumulated knowledge." *(Verified — Squad README "Knowledge compounds across sessions" + "What Gets Created")*
- **AGENTS.md / Copilot memory practice:** durable instructions + a committed decisions log are the common lightweight pattern; the frontier is *tiered memory* (working/episodic/semantic) and *memory-governance* (Squad has open proposals for both). *(Verified — Squad `docs/proposals/tiered-memory.md`, `memory-governance-provider.md`)*
- **AI-Forward's existing substrate:** the **knowledge graph** (V2 frontmatter per artifact), **decision notes** (V17 — "session exhaust" captured before close), the **glossary** (V14), **freshness SLAs** (V13), and the **Docs Explorer**. This is already durable, git-committed, tool-neutral memory — but it is organized as *artifacts and per-decision notes*, not as a single rolling *project ledger* an agent reads top-to-bottom on grounding. *(Verified — `knowledge-visualization.md` V2/V13/V14/V17)*
- **Frontier read for us:** the gap is **shape, not substrate** — a continuously-appended, graph-linked "what this project has learned/decided" ledger that the grounding step of every skill consults, complementing (not replacing) the graph.

## 4. Obsidian as the memory lens (the explicit decision in #3)

- **Already compatible at zero cost.** `knowledge-visualization.md` designed the per-file YAML frontmatter so `docs/` is *"a valid Obsidian vault (Properties, Bases tables, and Obsidian's graph view all read this frontmatter natively)."* Opening `docs/` in Obsidian today gives Properties, Dataview-style queries, and a graph view over the existing memory — with no schema change. *(Verified — `knowledge-visualization.md` §0 + V2, verbatim)*
- **Obsidian+git strengths:** plain-Markdown, local-first, rich linking, graph view, Dataview querying of frontmatter (`status: draft`, `review-by` past, etc.), strong dev-workflow fit. *(Verified — Obsidian/git research)*
- **Obsidian+git downsides that argue against *requiring* it:** per-contributor setup, plugin reliability across Obsidian updates, no live co-edit, not WYSIWYG, weak with binaries. These are onboarding and maintenance costs. *(Verified — same research)*
- **Frontier read for us:** Obsidian is an **optional, additive lens** over memory the pack already owns — adopt by *documenting* the existing compatibility and shipping an optional workspace, **not** by making it the system of record. This preserves tool-neutrality (the pack must work for someone who never installs Obsidian) and the no-gratuitous-dependency rule.

## 5. Responsible AI policy + PII/secret scrubbing (for suggestion #4)

- **The two anchor frameworks.** **Microsoft Responsible AI Standard (v2)** supplies the *principles* (fairness, reliability & safety, privacy & security, inclusiveness, transparency, accountability). **NIST AI RMF** supplies the *lifecycle controls* via four functions — **Govern, Map, Measure, Manage**. The 2025 consensus is "principles (MS) + practical controls (NIST), embedded across the lifecycle, auditable." *(Verified — RAI research; MS RAI Standard; NIST AI RMF)*
- **AI-Forward already operationalizes most of both** — Privacy & Data Governance persona (purpose/basis/minimization/residency), Security & Identity persona (STRIDE, least privilege, delegated identity), `engineering-governance.md` (§3 threat model, §4 privacy & data governance, §5 accessibility), the threat-model and privacy-review **templates**, and the Rules of the Road's **human-in-the-loop gates**. The missing piece is a *single committed policy artifact* that names the stance and maps it to these. *(Verified — pack contents)*
- **PII/secret scrubbing tools.** **Microsoft Presidio** (NLP, high-accuracy PII redaction, extensible, CI-integrable) for PII; **gitleaks** / **detect-secrets** / **TruffleHog** for secrets; **regex** as the lightweight, customizable supplement with a higher false-positive/negative rate; **git-filter-repo / BFG** to purge history. Squad ships a lightweight `squad scrub-emails`. *(Verified — PII/secret-scrub research; Squad README)*
- **Frontier read for us:** ship a **stdlib regex first-pass `scrub.py`** (the on-brand, dependency-free analogue of `scrub-emails`) for redacting obvious PII/secrets from committed *pack/memory* Markdown, and **explicitly point at gitleaks/Presidio for real CI enforcement** — never claim the regex pass is sufficient.
