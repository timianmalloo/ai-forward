---
id: kb-continuous-improvement-and-dreaming-comparables
title: "Continuous Improvement & Dreaming — Comparables"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [dreaming, comparables, claude-dreams, openclaw, postmortem, agents-md]
links:
  - { to: kb-continuous-improvement-and-dreaming, rel: refines }
review-by: "2026-11-13"
summary: >-
  How Claude Dreams, OpenClaw, Reflexion, Generative Agents, A-MEM, the LLM-wiki, self-improving
  AGENTS.md, and SRE/NASA lessons-learned frame and solve the problem — and what AI-Forward should
  borrow or reject; plus the five-part architecture everyone independently builds.
---

# Comparable solutions & problem framings

*How existing products and the literature frame and solve "learn continuously, consolidate offline, share across contexts." Named, with what each does well and badly, and — the load-bearing column — what AI-Forward should borrow or reject.*

| Solution / source | How it frames the problem | Approach | Does well | Does badly (for us) | Confidence |
|---|---|---|---|---|---|
| **Anthropic Claude Dreams** | Managed-agent memory rots; curate it offline | Async job: memory store + ≤100 sessions → **new** reorganised store; `instructions` steer; review & discard | Clean human-in-the-loop (input never mutated); steerable; simple mental model | Vendor runtime store, not committed Markdown; presumes the managed-agents platform; research-preview | Verified [Claude Dreams docs] |
| **OpenClaw `memory-core` (dreaming)** | Promote strong short-term signals to durable memory, explainably | **light→REM→deep** phases; only deep writes; weighted scoring + threshold gates; taint gate; preimage + source refs; Dream Diary; nightly cron | File-based, reversible, provenance-gated, scheduled — closest to what we need; every safety idea is reusable | Its own plugin/runtime + SQLite state; more machinery than a Markdown pack wants to import wholesale | Verified [OpenClaw docs] |
| **Reflexion (Shinn et al., 2023)** | Learn from failure without retraining | Actor→Evaluator→Reflector; verbal lesson → episodic buffer → re-injected next attempt | Names the missing *outcome/Evaluator* signal; proves text-memory beats nothing (91% vs 80% HumanEval) | Per-task, single-agent, in-session; not a cross-repo/offline design | Verified [arXiv:2303.11366] |
| **Generative Agents (Park et al., 2023)** | Believable long-horizon memory | Memory stream + periodic **reflection**; retrieval = importance×recency×relevance | The maths for *which* memory to promote; reflection = synthesise higher-level inferences | A simulation research artifact, not an ops tool | Verified [arXiv:2304.03442] |
| **A-MEM (Xu et al., 2025)** | Rigid memory schemas don't evolve | Zettelkasten notes: tags + auto bi-directional links + memory evolution | Validates a *linked note graph* as the durable store — the pack already has this | Vector-store implementation; token-cost claims are the authors' own | Verified paper / Flagged numbers [arXiv:2502.12110] |
| **Karpathy "LLM wiki" / second brain** | Agents should maintain a compounding knowledge base | Collaborative Markdown wiki: ingest → summarise → cross-ref → refactor; context=RAM, LLM=CPU, memory=disk | The exact mental model for the pack's `docs/` graph; "dreaming" as the refactor step | Attributed via secondary 2026 blogs; no single canonical spec to cite | Verified pattern / Flagged specifics |
| **Self-improving AGENTS.md** | Agents repeat mistakes across sessions | Append "learnings" to AGENTS.md; auto-generate + **PR review**; cross-project via `<org>/.agent-memory/` | Low-tech, ambient, and lands on the same guardrail (review before promote); has the *cross-project* half | Unstructured prose accretes; no scoring/dedup/taint discipline | Verified trend [self-improving AGENTS.md] |
| **Google SRE blameless postmortems** | Incidents must produce learning, not blame | Blameless template; central searchable KB tagged by failure mode; tracked action items | The cultural + template discipline; "are similar incidents recurring?" as the metric | Human-process heavy; no agent/automation layer | Verified [Google SRE book] |
| **NASA Lessons Learned (LLIS)** | Institutional knowledge evaporates | **Collect → Record → Disseminate → Apply** lifecycle; org-wide dissemination | The canonical *federation* lifecycle — capture is worthless without dissemination + application | Heavyweight governance; slow | Verified [NASA APPEL] |
| **AI-Forward (us), today** | Work must compound across sessions | Append-only audit + change logs; defect-class register (`class→sweep→derive→prevent`); knowledge graph; read-at-grounding | Best-in-class *capture* + *classification* + a *linked note graph* + human-in-the-loop, all in committed Markdown | No **scheduled offline consolidation**; no **cross-repo federation**; `outcome` signal + session ingestion under-used | Verified (in-repo standards) |

## The pattern across the column: everyone builds the same five parts

Read down the table and the same architecture recurs, whatever the label:

1. **Capture** — a running record of what happened (memory store / memory stream / audit log / AGENTS.md / postmortem).
2. **An outcome signal** — did it work? (Reflexion Evaluator; incident severity; the pack's `outcome` field).
3. **Consolidation** — an offline pass that dedupes, resolves contradictions, and compresses instances into rules (dreaming; reflection; postmortem review; `class→sweep→derive→prevent`).
4. **A durable, linked store** — where the promoted knowledge lives and is retrieved (MEMORY.md / note graph / KB / defect register + knowledge graph).
5. **Dissemination + application** — getting the learning to where it will fire (memory integration at session start; grounding read; NASA Disseminate/Apply; federation).

**AI-Forward has 1, 2 (under-used), and 4 already, and does 3 one-defect-at-a-time.** The gap is **3 at scale (the dream pass)** and **5 across repos (federation)**.

## Adjacent problems worth borrowing from

- **Log analytics / SIEM** — the "mine a high-volume append-only log for recurring patterns" problem is solved daily in security; the transferable idea is *scheduled aggregation queries over structured events*, which is exactly what a dream pass over `audit-log.jsonl` is.
- **Data-pipeline medallion (bronze→silver→gold)** — raw → cleaned → curated maps cleanly onto raw-log → staged-candidate → promoted-class. The pack's own domain-and-data-modelling standard (append-only facts, derive-don't-store) is the same discipline; the dream pass is a *gold projection* of the audit facts. *(Inferred — our mapping)*
- **Spaced repetition / knowledge decay** — the freshness-SLA (V13) and "recurrence is the metric" (CI4) are a manual spaced-repetition system; the frontier's explicit-forgetting work is the automated version.
- **Monorepo vs. polyrepo knowledge** — the federation question ("share learnings across repos") is the polyrepo version of the monorepo advantage (shared context for free). The learnings store is how polyrepos buy back some of that.
