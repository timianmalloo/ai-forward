---
id: kb-continuous-improvement-and-dreaming-references
title: "Continuous Improvement & Dreaming — References"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [dreaming, references, standards, papers, in-repo-standards]
links:
  - { to: kb-continuous-improvement-and-dreaming, rel: refines }
review-by: "2026-11-13"
summary: >-
  Primary product/platform sources, seminal papers (Reflexion, Generative Agents, A-MEM, sleep-time
  compute), SRE/NASA practice, and the in-repo standards this capability composes with
  (continuous-improvement, audit-and-change-log, defect-classes, knowledge-visualization) plus runners.
---

# Reference information

*Standards, specifications, seminal works, and the in-repo standards this capability composes with. Links and access dates are in `sources.md`.*

## Primary product / platform sources (ground truth)

- **Anthropic — Claude Managed Agents: Dreams** (research preview) — the authoritative definition of the managed "dreaming" API: async job, `inputs` = one memory store + 1–100 sessions, output = a *new* memory store, `instructions` steering, model selection, `dreaming-2026-04-21` beta header, input-never-mutated / review-and-discard semantics. — *(Verified — official platform docs)*
- **OpenClaw — Concepts: Dreaming** (`memory-core`) — the authoritative description of a local, file-based dreaming implementation: light/REM/deep phases, weighted deep-ranking signals + threshold gates, provenance taint gate, redaction, preimage storage, source-reference requirement, bootstrap budget, Dream Diary (`DREAMS.md`), nightly cron (`0 3 * * *`), reversible backfill lanes. — *(Verified — official concept docs)*

## Seminal / foundational works

- **Shinn, Cassano, et al. — "Reflexion: Language Agents with Verbal Reinforcement Learning"** (NeurIPS 2023, arXiv:2303.11366). The Actor–Evaluator–Reflector loop; textual self-reflection as episodic memory replacing weight updates. The root of "learn from failure as text." — *(Verified)*
- **Park, O'Brien, et al. — "Generative Agents: Interactive Simulacra of Human Behavior"** (arXiv:2304.03442, UIST 2023). The memory stream + periodic reflection + importance×recency×relevance retrieval score. The maths under candidate promotion. — *(Verified)*
- **Xu, et al. — "A-MEM: Agentic Memory for LLM Agents"** (arXiv:2502.12110, 2025). Zettelkasten-inspired self-evolving linked note memory. Validates the *linked note graph* as the durable store. — *(Verified — paper; internal benchmark numbers are the authors' own)*
- **"Sleep-time Compute"** (arXiv:2504.13171, 2025). Spending compute offline/between queries to pre-consolidate context; the theoretical warrant for a *scheduled* dream pass. Cited directly by OpenClaw. — *(Verified — as referenced; original paper to be read in full on refresh → Flagged on details)*
- **Hoel — the "overfitted brain" hypothesis** (dreams as anti-overfitting via injected noise/diversity). Karpathy's borrowed analogy for why dreaming should *generalise*. — *(Flagged — a neuroscience hypothesis and an analogy, not evidence about LLMs)*

## Practitioner standards & culture

- **Google SRE Book — "Postmortem Culture: Learning from Failure."** Blameless postmortems; standardised templates; central searchable KB; tracked action items; recurrence as the effectiveness metric. — *(Verified)*
- **NASA APPEL — Lessons Learned (LLIS).** The **Collect → Record → Disseminate → Apply** institutional-knowledge lifecycle — the canonical federation model. — *(Verified)*
- **AGENTS.md** (open standard, donated to the Linux Foundation, Dec 2025) — vendor-neutral Markdown steering file read by all major agents; the substrate for the "self-improving learnings" trend and cross-project `<org>/.agent-memory/`. — *(Verified — trend well-attested; "Linux Foundation donation" date is from secondary reporting → Flagged on the exact provenance)*

## The in-repo standards this capability composes with (authoritative *for us*)

These are the pack's own governing documents; the dreaming capability **extends** them, it does not replace them. Cite them by their directive IDs.

- **`continuous-improvement.md` (CI1–CI12)** — the defect-class discipline: `class → sweep → derive → prevent`; the control ladder (make-impossible > automated control > always-loaded instruction > knowledge doc > register); "a lesson recorded as prose is a memoir" (CI6); read the register at grounding (CI5); recurrence is the metric (CI4); raise general lessons upstream via `/extendaibundle` (CI8). **The dream pass is CI2 run in bulk over the accumulated corpus.**
- **`audit-and-change-log.md` (AL1–AL13, CL1–CL3)** — the durable, committed, append-only audit log (every skill's last action) + change log; the five required fields + enrichment (`outcome`, `tags`, `artifacts`); JSONL is source-of-truth, the JS/HTML are derived; no secrets/PII (AL4); read the history at grounding (AL10); the prompt-reuse lens. **The dream pass is the missing *consumer* of this corpus.**
- **`defect-classes.md`** — this repo's register: one entry per class, a signature, "why it survives," instances, a named control, a status. **The dream pass proposes new/updated entries and dedupes the register.**
- **`knowledge-visualization.md` (V1–V18)** — the knowledge graph: V2 frontmatter as the record, V13 freshness SLAs, V14 the glossary + relation registry, V16 change-impact propagation, V17 decision notes, V18 the `docs-graph.py` script bundle. **This is the "wiki"/A-MEM note graph the field is reinventing; the dream pass keeps it consolidated.**
- **`project-memory-and-obsidian.md` (M1–M9)** — the rolling committed project-memory ledger read at grounding; the tool-neutral, Markdown-first stance. **The dream pass writes its Diary here-style, not into a runtime store.**
- **`responsible-ai-policy.md`** + **`scrub.py`** + **`no-guessing-protocol.md`** — the human-in-the-loop, no-secrets/PII, provenance-and-confidence-label guardrails the dreaming pass and (especially) the federation layer must honour.
- **`solution-selection-ladder.md` (L5–L6)** — the `simplify:`/`assume:` inline markers and the debt ledger the dream pass should *harvest* (a triggered marker is a lesson already written down and unread).

## Runners / execution surfaces for the scheduled job

- **cron / launchd / Task Scheduler** — the lowest-common-denominator scheduler for a nightly local sweep (OpenClaw uses `0 3 * * *`).
- **GitHub Actions (scheduled workflow)** — for a per-repo dream job that opens a PR of proposals; native to where the review happens.
- **claude-cowork / OpenClaw / agent runners** — where a model-in-the-loop consolidation subagent runs; each provides its own scheduling + session-history access. *(To be verified against each product's current API on `/specify`.)*
