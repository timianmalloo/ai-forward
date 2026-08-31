---
id: kb-agent-focus-and-scope-control-sources
title: "Agent Focus & Scope Control — Sources"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [sources, citations, arxiv, openai-prompting-guides]
links:
  - { to: kb-agent-focus-and-scope-control, rel: refines }
review-by: "2027-02-28"
summary: >-
  The full source list with access dates and confidence labels: primary arXiv research (overthinking,
  goal drift, agent drift, self-reflection, reasoning path control), the OpenAI GPT-5/5.1 prompting
  guides, industry framing, and this repo's own drm-0008 corpus finding.
---

# Sources

*Accessed 2026-08-31 via web search. Source-of-truth hierarchy (BoK §III.1): primary papers and
official vendor guides preferred; secondary/industry for framing. Recency matters — this field moves
fast.*

## Primary research
- Su et al., **"Between Underthinking and Overthinking: An Empirical Study of Reasoning Length and
  Correctness in LLMs"**, arXiv **2505.00127** (2025) — overthinking degrades simple-task accuracy;
  models misjudge difficulty. *[Verified, primary]*
- Eisenstadt et al., **"Overclocking LLM Reasoning: Monitoring and Controlling Thinking Path Lengths"**,
  arXiv **2506.07240** (2025) — internal progress encoding to cap reasoning steps. *[Verified, primary]*
- **"Technical Report: Evaluating Goal Drift in Language Model Agents"**, arXiv **2505.02709** (2025)
  — goal drift under context change; stopping-condition gap. *[Verified, primary]*
- **"Agent Drift: Quantifying Behavioral Degradation in Multi-Agent Systems"**, arXiv **2601.04170**
  (2026) — measured degradation over long missions; adaptive anchoring among mitigations. *[Verified, primary]*
- **"Self-Reflection in LLM Agents: Effects on Problem-Solving Performance"**, arXiv **2405.06682**
  (2024) — self-reflection helps but adds cost; needs stopping criteria. *[Verified, primary]*
- Shinn et al., **Reflexion** (verbal self-critique) — foundational self-critique pattern; DoD
  enforcement via a critic. *[Verified, primary/secondary]*
- **"Generative AI and Agentic Systems: Modeling Goal Drift, Self-…"**, IJETA V13I3P63 — Latent Goal
  Crystallization framing. *[Flagged — journal, single source for the LGC term]*

## Official vendor guidance
- **OpenAI GPT-5 prompting guide** — developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide
  — reasoning_effort, verbosity, agentic scope, tool budgets. *[Verified, official]*
- **OpenAI GPT-5.1 prompting guide** — developers.openai.com/cookbook/examples/gpt-5/gpt-5-1_prompting_guide
  — structured scope/plan-and-solve patterns. *[Verified, official]*

## Industry / secondary (framing, not load-bearing)
- IBM, **"Agentic drift: the hidden risk that degrades AI agent performance"** — ibm.com/think/insights.
- usewire.io, **"Agent drift: why long-running AI agents lose the plot"**.
- lyntxglobal.com — long-horizon agentic benchmark convergence survey.
- GPT-5.2 prompting cheatsheet (esso.dev); efficient-LLM-reasoning survey (danilchenko.dev) — derived
  from the primary sources above.

## In-repo corpus (this project's own evidence)
- **`docs/dreams/drm-0008/dream.json`** proposal p12 (Verified): 61/78 substantive turns (78%)
  recorded no goal-state (`done_when`) — the pack's own instruction-following-degradation measurement.
- **`docs/lessons/defect-classes.md`** class **PACK-O**; **`communication-and-task-discipline.md`**
  CT14–CT24; **`execution-graph-optimization.md`** GO1/GO9/GO16.
