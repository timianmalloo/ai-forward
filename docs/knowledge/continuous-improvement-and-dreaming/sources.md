---
id: kb-continuous-improvement-and-dreaming-sources
title: "Continuous Improvement & Dreaming — Sources"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [dreaming, sources, citations]
links:
  - { to: kb-continuous-improvement-and-dreaming, rel: refines }
review-by: "2026-11-13"
summary: >-
  Full source list with access dates and confidence labels — primary product/platform docs (Claude
  Dreams, OpenClaw), seminal papers, SRE/NASA practice, and the in-repo standards — with a currency
  note on which sources are research-preview or secondary framing.
---

# Sources

*Full source list with access dates. Primary/standard sources are ground truth; secondary (blog/press) sources are used only for framing and are labelled as such. Accessed 2026-08-15 unless noted.*

| # | Title / source | Type | URL | Accessed | Used for |
|---|---|---|---|---|---|
| 1 | Anthropic — Claude Managed Agents: **Dreams** (research preview) | primary / platform docs | https://platform.claude.com/docs/en/managed-agents/dreams | 2026-08-15 | the managed dreaming API: input store + 1–100 sessions → new store; input immutable; `instructions` steering; `dreaming-2026-04-21` header (findings #1, #2; data/constants) |
| 2 | OpenClaw — Concepts: **Dreaming** (`memory-core`) | primary / product docs | https://docs.openclaw.ai/concepts/dreaming | 2026-08-15 | light/REM/deep phases; weighted deep-ranking signals; taint gate; redaction; preimage; source-refs; Dream Diary; cron `0 3 * * *`; backfill (findings #1, #7, #8; data/constants; state-of-the-art) |
| 3 | MindStudio — Claude Dreaming Feature: self-improving agent memory | secondary / blog | https://www.mindstudio.ai/blog/claude-dreaming-feature-self-improving-agent-memory | 2026-08-15 | framing: three memory types; the memory problem; consolidation-as-compression (finding #2) |
| 4 | inventivehq — Claude's "Dreaming" Explained | secondary / blog | https://inventivehq.com/blog/claude-agents-dreaming-explained | 2026-08-15 | framing of the dreaming workflow + human-in-the-loop (finding #2) |
| 5 | Shinn et al. — **Reflexion: Language Agents with Verbal Reinforcement Learning** (NeurIPS 2023) | primary / paper | https://arxiv.org/abs/2303.11366 | 2026-08-15 | Actor–Evaluator–Reflector; verbal self-reflection as episodic memory; the outcome-signal requirement (finding #3, #7) |
| 6 | Park et al. — **Generative Agents: Interactive Simulacra of Human Behavior** (UIST 2023) | primary / paper | https://arxiv.org/abs/2304.03442 | 2026-08-15 | memory stream + periodic reflection; importance×recency×relevance retrieval (finding #3; data/constants) |
| 7 | Xu et al. — **A-MEM: Agentic Memory for LLM Agents** (2025) | primary / paper | https://arxiv.org/abs/2502.12110 | 2026-08-15 | Zettelkasten linked-note memory; validates the note-graph durable store (finding #4) |
| 8 | **Sleep-time Compute** (2025) | primary / paper (referenced) | https://arxiv.org/abs/2504.13171 | 2026-08-15 | offline/between-query consolidation — the warrant for scheduling (finding #5); *to read in full on refresh (Flagged on details)* |
| 9 | Karpathy — "LLM wiki" / self-improving second brain (multiple 2026 writeups) | secondary / blog aggregation | https://www.explainx.ai/blog/karpathy-llm-wiki-pattern-agent-memory-guide-2026 ; https://www.techupkeep.dev/blog/karpathy-self-improving-second-brain-llm ; https://thegenios.com/blog/karpathy-on-memory-and-context/ | 2026-08-15 | the LLM-wiki pattern; context=RAM/LLM=CPU; dreaming-as-anti-overfitting analogy (finding #4, #5; Flagged on specifics) |
| 10 | Anthropic — New in Claude Managed Agents: dreaming, outcomes, multiagent | primary / product blog | https://claude.com/blog/new-in-claude-managed-agents | 2026-08-15 | product framing of dreaming + outcomes (findings #1, #7) |
| 11 | Google SRE Book — **Postmortem Culture: Learning from Failure** | standard / practice | https://sre.google/sre-book/postmortem-culture/ | 2026-08-15 | blameless postmortems; central KB; recurrence as metric (comparables; guardrails) |
| 12 | NASA APPEL — **Lessons Learned** (LLIS) | standard / practice | https://www.nasa.gov/learning-resources/for-professionals/appel-lessons-learned/ | 2026-08-15 | Collect→Record→Disseminate→Apply lifecycle — the federation model (design implications; comparables) |
| 13 | Self-Improving Coding Agents Through Accumulated Behavioural Rules | secondary / blog | https://codex.danielvaughan.com/2026/07/16/self-improving-coding-agents-accumulated-behavioral-rules-closed-loop-codex-cli-agents-md-review-driven-learning/ | 2026-08-15 | agents appending learnings + PR review; the never-auto-merge guardrail (finding #8; comparables) |
| 14 | AGENTS.md best practices (guide) | secondary / blog | https://www.betterclaw.io/blog/agents-md-best-practices ; https://codersera.com/blog/agents-md-vs-claude-md-vs-cursor-rules-comparison-2026/ | 2026-08-15 | AGENTS.md as steering substrate; cross-project `<org>/.agent-memory/`; Linux-Foundation donation *(Flagged provenance)* (comparables) |
| 15 | AI Agent Memory Systems: A 2026 Engineering Guide | secondary / blog | https://jobsbyculture.com/blog/ai-agent-memory-systems-guide-2026 | 2026-08-15 | working/episodic/semantic/procedural taxonomy; MemGPT/Letta tiered memory; explicit forgetting (glossary; state-of-the-art) |

## In-repo sources (authoritative for AI-Forward)

| Source | Used for |
|---|---|
| `.github/instructions/continuous-improvement.instructions.md` (`continuous-improvement.md`, CI1–CI12) | the defect-class discipline the dream pass batches (findings #6; design implications) |
| `.github/instructions/audit-and-change-log.instructions.md` (`audit-and-change-log.md`, AL/CL) | the corpus the dream pass reads; the evolution targets (finding #7; data/constants) |
| `docs/lessons/defect-classes.md` | the register the dream pass proposes into (data/constants) |
| `.github/instructions/knowledge-visualization.instructions.md` (V1–V18) | the note graph = the "wiki" (finding #4) |
| `.github/instructions/project-memory-and-obsidian.md` (M1–M9) | the committed project-memory ledger; Diary home |
| `.github/instructions/responsible-ai-policy.md` + `scrub.py` + `no-guessing-protocol.md` | the federation + promotion guardrails (finding #8; invariants) |
| `.github/instructions/solution-selection-ladder.md` (L5–L6) | the `simplify:`/`assume:` markers the pass harvests (data/constants) |
| `docs/knowledge/pack-evolution/index.md` | precedent for "adopt the intent, reject the runtime form" (framing) |

*Note on currency:* sources 1, 2, 8, 10 are research-preview / actively-moving surfaces; sources 3, 4, 9, 13, 14, 15 are 2026 secondary commentary of variable authority. The load-bearing claims rest on 1, 2, 5, 6, 7 and the in-repo standards; secondary sources are framing only. Re-verify 1 and 2 on any refresh.
