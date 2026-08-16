---
id: kb-continuous-improvement-and-dreaming-sota
title: "Continuous Improvement & Dreaming — State of the Art"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [dreaming, agent-memory, self-improvement, reflexion, sleep-time-compute]
links:
  - { to: kb-continuous-improvement-and-dreaming, rel: refines }
review-by: "2026-11-13"
summary: >-
  Current best practice for continuous self-improvement: the awake/asleep loop; Claude Dreams and
  OpenClaw's phased local dreaming; Reflexion and Generative Agents as the academic root; A-MEM and
  Karpathy's LLM-wiki as the durable-store shape; sleep-time compute as the scheduling warrant.
---

# State of the art — continuous improvement & "dreaming"

*Every claim carries a source and a confidence label. Primary sources (Claude Dreams platform docs, OpenClaw concept docs, arXiv papers) are ground truth; 2026 blog/press commentary is used only for framing.*

## The organising idea (the "awake / asleep" loop)

The field has converged on a two-phase loop for agent self-improvement:

- **Awake (online):** the agent *acts* and *captures* — it logs what it did, what happened, and what it noticed, into a memory store or a history file. Cheap, continuous, high-noise.
- **Asleep (offline, "dreaming"):** a scheduled/triggered pass *consolidates* that raw history — deduplicating, resolving contradictions, compressing many instances into a few durable rules, and surfacing cross-cutting insight. Expensive, periodic, high-signal.

The insight the sources share: **capture is easy and consolidation is where the value is.** A write-only log rots into "duplicates, contradictions, and stale entries" (Claude Dreams' own words); the dreaming pass is what keeps it useful. — *(Verified — [Claude Dreams docs]; [OpenClaw dreaming docs])*

## Current best-practice approaches

### 1. Managed "dreaming" — Anthropic Claude Dreams *(research preview)*
- **What it is:** an asynchronous job that takes a **memory store + 1–100 session transcripts** and produces a **new, separate** memory store — duplicates merged, stale/contradicted entries replaced with the latest value, new insights surfaced. Steerable with a natural-language `instructions` field ("Focus on coding-style preferences; ignore one-off debugging notes"). Model-selectable (`claude-opus-4-8`). **The input store is never modified**, so the output is reviewable and discardable. Gated by the `dreaming-2026-04-21` beta header. — *(Verified — [Claude Dreams docs])*
- **Where it wins:** zero-infrastructure for teams already on managed agents; the review-and-discard model is a clean human-in-the-loop.
- **Where it fails for us:** it is a *vendor runtime memory store*, not committed Markdown; it presumes the managed-agents platform. AI-Forward's artifacts (audit JSONL, defect register, the graph) are the store we already have. Adopt the *shape*, not the *substrate*.

### 2. Local, phased, reviewable "dreaming" — OpenClaw `memory-core` *(the richest concrete design)*
- **What it is:** background memory consolidation with three cooperative phases per sweep, **light → REM → deep**, of which **only `deep` writes durable memory** (`MEMORY.md`). Everything is explainable and reversible.
  - **Light** — sort/stage recent short-term material, dedupe, record reinforcement signals. *No durable write.*
  - **REM** — reflect on recurring themes and ideas, build reflection summaries. *No durable write.*
  - **Deep** — score candidates against weighted signals + threshold gates (`minScore`, `minRecallCount`, `minUniqueQueries` must *all* pass), rehydrate snippets from live files (skip stale), pass gated candidates to a consolidation subagent, and rewrite durable memory only if the result preserves enough prior entries, includes candidate **source references**, and fits a bootstrap budget. Falls back to append-only if the model is unavailable or validation fails. — *(Verified — [OpenClaw dreaming docs])*
- **Safety machinery worth stealing wholesale:** a **provenance taint gate** (candidates whose origin is `untrusted`/`system` are structurally removed before the consolidation prompt — not merely penalised); **redaction** of personal/sensitive content and removal of already-recalled context (so recalled snippets can't be re-learned as "new"); **preimage storage** (the previous durable file is saved before any rewrite); a **Dream Diary** (`DREAMS.md`) that records added/merged/superseded counts + diff highlights but is *excluded from being a promotion source*; and **reversible backfill lanes** for replaying history. — *(Verified — [OpenClaw dreaming docs])*
- **Scheduling:** one cron sweep, default `0 3 * * *` (nightly), deduped across workspaces. — *(Verified)*
- **Where it wins:** it is the closest existing design to what AI-Forward needs — file-based, reviewable, provenance-gated, scheduled. It even cites the same theory (sleep-time compute; Generative Agents durable memory).

### 3. Verbal self-reflection as memory — Reflexion *(the academic root)*
- **What it is:** an **Actor → Evaluator → Reflector** loop. The Actor attempts the task; the Evaluator produces a success/failure signal; the Reflector writes a *natural-language* lesson ("I ignored constraint X; next time check all constraints first") into an episodic memory buffer; the next attempt is conditioned on that buffer. No weight updates; model-agnostic; API-friendly. 91% pass@1 on HumanEval vs 80% baseline GPT-4. — *(Verified — [Reflexion, arXiv:2303.11366])*
- **Why it matters here:** it names the missing ingredient in a pure audit log — the **Evaluator/outcome signal**. A lesson is only mine-able if the log records whether the action *succeeded*.

### 4. Memory stream + periodic reflection — Generative Agents *(the retrieval maths)*
- **What it is:** a time-stamped **memory stream** of observations, with **periodic reflection** that synthesises higher-level inferences from recent memories, retrieved by a score combining **importance × recency × relevance**. — *(Verified — [Generative Agents, arXiv:2304.03442])*
- **Why it matters here:** OpenClaw's six weighted deep-ranking signals (relevance, frequency, query-diversity, recency, consolidation, conceptual-richness) are a direct descendant; this is the maths for *which* candidates deserve promotion.

### 5. The self-improving durable store — A-MEM / Karpathy's "LLM wiki"
- **A-MEM** (arXiv:2502.12110): a **Zettelkasten-inspired** agentic memory — each memory is a structured note with description, keywords, tags and **auto-generated bi-directional links**; adding a note can **evolve** existing notes; the network self-organises. Reports large multi-hop reasoning gains and 85–93% memory-op token-cost reduction vs baselines. — *(Verified — paper; performance numbers are the authors' own → treat as Flagged)*
- **Karpathy's "LLM wiki"**: agents collaboratively build and maintain a **Markdown knowledge base** — ingest new knowledge, update summaries, cross-reference, refactor structure over time — a "second brain" that compounds. Framed alongside "context window = RAM, LLM = CPU, external memory = disk." — *(Verified on the pattern being widely attributed to Karpathy across multiple 2026 writeups; Flagged on any specific quote/date, as these are secondary blogs)*
- **Why they matter here:** they describe, almost exactly, the pack's existing **knowledge graph** (typed, linked, evolving Markdown notes with a glossary). AI-Forward does not need to *build* the wiki — it needs to *dream over* the one it has.

### 6. Self-improving steering files — the "learnings in AGENTS.md" trend
- **What it is:** after a task/session, the agent appends a **learning** to `AGENTS.md` (or an adjacent memory file) — e.g. "Do not use npm 9.x with this project." Some setups **auto-generate** learnings and open a **PR** for human review; cross-project patterns migrate via a shared `<org>/.agent-memory/` with opt-in privacy controls. The near-universal caveat: **never auto-approve agent edits to the steering file — review via PR.** — *(Verified — [self-improving AGENTS.md writeups]; [AGENTS.md best practices])*
- **Why it matters here:** it is the low-tech, ambient version of dreaming, and it independently lands on the pack's own guardrail (human-in-the-loop, review before promote). It is the *cross-project* half the pack has not yet automated.

## The frontier / open research

- **Sleep-time compute (arXiv:2504.13171):** formalises spending compute *offline, between queries*, to pre-compute/consolidate context so online queries are cheaper and better — the theoretical warrant for a *scheduled* dream pass rather than an inline one. — *(Verified — referenced directly by OpenClaw)*
- **Explicit forgetting / decay:** newer memory OSes (MemGPT/Letta lineage) put *what to keep vs. archive vs. discard* under learnable, agentic control. The pack's freshness SLAs (V13) and "recurrence is the metric" (CI4) are the manual version; the frontier is making forgetting a first-class, measured operation.
- **Cross-agent / fleet memory federation:** still immature and mostly proprietary; the open question is how to share *generalised* learnings across projects/orgs without leaking specifics — exactly the federation guardrail this base flags (finding #8).
- **Dreaming as generalisation, not memorisation:** the (Flagged) neuroscience analogy — dreams fight overfitting by injecting diversity — is the aspiration that a dream pass should output *classes and controls*, not a transcript of instances. The pack's `class → sweep → derive → prevent` is the disciplined form of this instinct.
