---
id: kb-continuous-improvement-and-dreaming-glossary
title: "Continuous Improvement & Dreaming — Glossary"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [dreaming, glossary, ubiquitous-language]
links:
  - { to: kb-continuous-improvement-and-dreaming, rel: refines }
review-by: "2026-11-13"
summary: >-
  The ubiquitous language for the dreaming/consolidation capability — dream pass, light/REM/deep
  phases, candidate, promotion, provenance taint gate, Dream Diary, outcome signal, defect class,
  control ladder, federation, fleet learnings store — for use in the spec, design, and code.
---

# Glossary — ubiquitous language

*Use these exact terms in the spec, the design, and any code for this capability. Definitions are for this project's usage; where a term is a vendor's, that is noted.*

- **Dreaming** — an offline, asynchronous, *reviewable* pass that consolidates accumulated agent history (logs + session transcripts + prior durable memory) into fewer, higher-signal, durable learnings — deduplicating, resolving contradictions, and surfacing cross-cutting insight. Named by analogy to sleep-driven memory consolidation. *Not* model retraining. *(Verified — Claude Dreams; OpenClaw)* <!-- use "dream pass" for one run, "dreaming" for the capability -->
- **Dream pass / sweep** — one execution of dreaming: reads the corpus, runs the phases, emits proposals + a Diary entry.
- **Consolidation** — the act of merging duplicates, replacing stale/contradicted entries, and compressing many instances into a few rules. The core verb of a dream pass.
- **Awake half / asleep half** — our framing: *awake* = online capture (the audit log, markers, session exhaust); *asleep* = offline consolidation (the dream pass). The pack has the awake half; the asleep half is the gap.
- **Memory store** *(Claude Dreams term)* — the durable note store a managed agent reads/writes. In AI-Forward the equivalent is the **committed corpus**: the audit/change logs + the defect register + the knowledge graph. We do **not** adopt a vendor runtime store as the substrate.
- **Light / REM / Deep phases** *(OpenClaw terms)* — the three cooperative sub-steps of a sweep: **Light** stages and dedupes recent material (no durable write); **REM** reflects on recurring themes (no durable write); **Deep** scores candidates and writes durable memory behind threshold gates. Only Deep promotes.
- **Candidate** — a staged, not-yet-promoted learning extracted from the corpus, carrying its provenance, outcome, and scoring signals; must pass the gates before promotion.
- **Promotion** — moving a candidate from staged to durable (into the defect register / a knowledge doc / the shared learnings store). Always human-reviewed; never auto-committed.
- **Provenance taint gate** — a *structural* filter (removal, not a score penalty) that excludes candidates whose origin is untrusted, tool-authored, cron/subagent, or secret/PII-bearing, *before* they can be consolidated. *(Verified — OpenClaw)*
- **Dream Diary** — a human-readable narrative log of what each pass added/merged/superseded (with diff highlights), kept **separate** from the durable store and **excluded** from being a promotion source. In AI-Forward it composes with the audit log / project-memory ledger. *(Verified — OpenClaw `DREAMS.md`)*
- **Outcome signal** *(Reflexion "Evaluator")* — the success/partial/failed/blocked marker on an action that makes it mine-able for a lesson. Already present as the audit `outcome` field; under-used today.
- **Reflection** *(Generative Agents / Reflexion term)* — synthesising higher-level inferences from a batch of lower-level observations; the "REM" of a dream pass; the step that turns instances into a class.
- **Defect class** *(AI-Forward term)* — a recurring *shape* of failure (not a single bug), with a signature, "why it survives," instances, a named control, and a status. The primary promotion target of a dream pass. *(Verified — `continuous-improvement.md`)*
- **Control** — the test / gate / lint rule / always-loaded instruction that fires when a class recurs. A learning is not "learned" until it is a control ("a lesson recorded as prose is a memoir"). *(Verified — CI6)*
- **class → sweep → derive → prevent** — the pack's four-step discipline for turning one defect into a control across the codebase; the dream pass runs this *in bulk* over the accumulated corpus. *(Verified — CI2)*
- **Control ladder** — the ranked homes for a lesson: *make it impossible* > *automated control* > *always-loaded instruction* > *knowledge doc* > *register entry only*. Promotion should climb as high as holds. *(Verified — CI6)*
- **`simplify:` / `assume:` marker** — inline greppable debt/assumption markers (ceiling + upgrade trigger / belief + confirmation route + consequence). A *triggered* marker is a lesson already written and unread — a dream pass harvests them. *(Verified — L5–L6; NG4)*
- **Federation** — sharing *generalised* learnings across a fleet of repos: each repo's dream pass contributes abstracted classes to a central **learnings store** and pulls from it at grounding. Instance-to-class abstraction + PII/secret scrub happen *before* anything crosses a repo boundary. *(Our term; maps to NASA Disseminate/Apply + `<org>/.agent-memory/`)*
- **Learnings store (fleet store)** — the central, git-committed home of federated, generalised classes + controls that every repo reads and writes. Candidate hosts: a dedicated `learnings/` repo, or the AI-Forward pack itself (via `/extendaibundle`).
- **Sleep-time compute** — spending compute offline/between queries to pre-consolidate context (arXiv:2504.13171); the warrant for scheduling dreaming rather than doing it inline. *(Verified — as referenced)*
- **LLM wiki** *(Karpathy)* — an agent-maintained Markdown knowledge base that compounds over time; the mental model for AI-Forward's `docs/` graph. *(Verified pattern)*
- **Explicit forgetting** — deliberately archiving/discarding stale memory as a first-class, measured operation; the automated cousin of the pack's freshness SLAs (V13). *(Verified — MemGPT/Letta lineage)*
