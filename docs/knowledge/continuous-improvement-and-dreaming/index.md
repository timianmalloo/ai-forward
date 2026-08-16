---
id: kb-continuous-improvement-and-dreaming
title: "Continuous Improvement & Dreaming — harvesting learnings across repos (domain knowledge)"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [continuous-improvement, dreaming, agent-memory, self-improvement, audit-log, defect-classes, cross-repo, federation]
links:
  - { to: defect-classes, rel: relates-to }
  - { to: audit-log, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2026-11-13"
summary: >-
  Sourced evidence base for continuously harvesting learnings, mistakes, patterns and
  anti-patterns across a fleet of local repositories and sharing them so every repo benefits.
  Synthesises the "dreaming" wave (Claude Dreams, OpenClaw, Karpathy's LLM-wiki), its academic
  roots (Reflexion, Generative Agents reflection, A-MEM, sleep-time compute), the self-improving
  AGENTS.md trend, and SRE/NASA lessons-learned practice — then maps them onto what AI-Forward
  already ships (audit/change logs, the defect-class register, the knowledge graph) and states
  the gap: the pack has built the *awake* half (capture) and lacks the *asleep* half (scheduled
  offline consolidation + cross-repo federation).
---

# Continuous Improvement & Dreaming — domain knowledge

**Domain & problem:** we want a system that **continuously harvests the knowledge, learnings, mistakes, patterns and anti-patterns** produced across *all* our local repositories, distils them, and **shares them back so every repo benefits** — the "get better every day, and get better *together*" loop. The trigger is the 2026 "dreaming" wave (Karpathy; Anthropic's Claude Dreams; OpenClaw's `memory-core`) plus the older academic lineage of agent self-improvement, set against what AI-Forward already does with audit logs and defect classes.

**Canonical framing:** the field frames this as **agent memory + offline consolidation ("dreaming") + a self-improving knowledge base ("the wiki")**, and separately as **organisational lessons-learned / blameless-postmortem practice**. Our framing is deliberately narrower and more concrete: this is a **methodology-pack problem, not a model problem** — we do not fine-tune weights; we curate *committed Markdown and structured logs* that both humans and agents read. That framing is load-bearing: it rules out the vendor "managed-agent memory store" as the primary mechanism and rules in a consolidation *job* over the artifacts the pack already commits.

**Compiled:** 2026-08-15 · **Lead:** Domain Researcher · **Status:** fresh

## Headline findings

1. **"Dreaming" is a real, shipping pattern with a stable shape: an *offline, asynchronous, reviewable* consolidation pass over accumulated session history + a memory store, producing a *new* store (the input is never mutated), gated by human review.** Claude Dreams (research preview, `dreaming-2026-04-21`) takes a memory store + 1–100 session transcripts and emits a **separate** reorganised store — duplicates merged, stale/contradicted entries replaced, new insights surfaced — steerable by a natural-language `instructions` field. OpenClaw's `memory-core` implements the same idea locally with `light → REM → deep` phases where **only the deep phase writes durable memory**, behind deterministic score/recall/diversity gates and a provenance **taint gate**. — *(Verified — [Claude Dreams docs]; [OpenClaw dreaming docs])*

2. **The mechanism is memory *curation*, explicitly not model retraining.** Every primary source stresses that dreaming operates at the level of "learned heuristics / durable notes" (compression of noisy logs into high-signal rules), leaves the raw inputs intact for audit, and keeps a human in the loop — you review the output store and discard it if you dislike it. This is exactly the pack's stance (human-in-the-loop, never self-certify) applied to memory. — *(Verified — [Claude Dreams docs]; [MindStudio]; [inventivehq])*

3. **The academic root is Reflexion (verbal self-reflection as memory), and the retrieval maths is Generative Agents (importance × recency × relevance).** Reflexion's Actor–Evaluator–Reflector loop turns a *failure signal* into a *textual lesson* stored in episodic memory and re-injected on the next attempt — no weight update, model-agnostic, 91% pass@1 on HumanEval vs 80% baseline. Generative Agents contributes the **memory stream + periodic reflection** and the three-factor retrieval score that OpenClaw's six weighted deep-ranking signals descend from. Both are the theory under "dreaming." — *(Verified — [Reflexion, NeurIPS 2023]; [Generative Agents, Park 2023])*

4. **The durable-store design the field is converging on is a *linked note graph*, i.e. the pack already built it.** A-MEM (Zettelkasten-inspired agentic memory: typed notes, auto bi-directional links, memory evolution) and Karpathy's "LLM wiki" (agents collaboratively maintain a Markdown knowledge base, cross-referencing and refactoring it over time) are the same shape as AI-Forward's **knowledge graph** — V2 frontmatter, typed links (V14 relation registry), the glossary, decision notes (V17). The pack's `docs/` *is* the wiki these papers describe. — *(Verified — [A-MEM, arXiv:2502.12110]; [Karpathy LLM-wiki writeups] — Inferred on the "same shape" mapping)*

5. **The theoretical justification for a *scheduled offline* pass is sleep-time compute and the "dreams prevent overfitting" hypothesis.** Sleep-time compute (arXiv:2504.13171) formalises spending compute *between* queries to pre-consolidate context; OpenClaw cites it directly. Karpathy borrows Erik Hoel's *overfitted-brain* hypothesis — dreams inject noise/diversity to fight overfitting — to argue a dreaming pass should *generalise* (mine the class), not just *memorise* (log the instance). This is precisely the pack's `class → sweep → derive → prevent` (CI2). — *(Verified — sleep-time compute paper referenced by OpenClaw; Flagged — the Hoel/overfitting link is Karpathy's analogy, not a proven property of LLM consolidation)*

6. **AI-Forward has already built the *awake* half of the loop; the gap is the *asleep* half and *cross-repo federation*.** The pack captures continuously — the **audit log** (every skill's last action), the **change log**, the **defect-class register** (`class → sweep → derive → prevent`, the control ladder, "a lesson recorded as prose is a memoir"), and the **knowledge graph** — and it already reads that history *at grounding* (CI5, AL10). What it lacks is (a) a **scheduled consolidation job** that mines the accumulated audit/change/defect corpus *plus session exhaust* to promote, dedupe, and surface cross-cutting classes, and (b) a **federation layer** that lifts repo-specific instances to general classes and shares them across every local repo (CI8's "raise it upstream" done systematically, both ways). — *(Verified — `continuous-improvement.md` CI1–CI12; `audit-and-change-log.md`; `defect-classes.md`; `knowledge-visualization.md`)*

7. **The audit log must evolve from a *write-only history* into a *mined corpus* — and the four missing ingredients are named by the sources.** To feed a dreaming pass, entries need: **(i) an outcome/success signal** per action (Reflexion's Evaluator — `outcome: success/partial/failed` already exists in the schema but is under-used); **(ii) session-transcript ingestion** with redaction + a provenance taint gate (OpenClaw ingests only interactive, redacted sessions; excludes cron/subagent/tool-output/untrusted origins); **(iii) a promotion pipeline** with deterministic score/recall/diversity thresholds so noise never reaches durable memory; and **(iv) a Dream Diary** — a human-readable narrative of what each pass changed, kept *separate* from the promotion source. — *(Verified — [OpenClaw dreaming docs]; `audit-and-change-log.md` AL1–AL2)*

8. **The non-negotiable guardrails are the same ones the pack already holds — and the sources independently arrive at them.** *Never auto-merge a learning* (review via PR — self-improving-AGENTS.md practice and Claude Dreams' discard-able output agree); *never mutate the source of truth in place* (dreaming emits a new store; the pack's logs are append-only JSONL); *never promote untrusted content* (taint gate; the pack's `scrub.py` + no-secrets/PII rule AL4); *provenance on every promoted item* (OpenClaw requires `Source: path#Lx-Ly`; the pack requires citations and confidence labels). Federation adds one more: *abstract to the class, never share the raw instance* (minimisation + no cross-repo PII leakage). — *(Verified — [OpenClaw]; [Claude Dreams]; [self-improving AGENTS.md]; `continuous-improvement.md`; `responsible-ai-policy.md`)*

## Confidence summary
- **Verified: 6 · Inferred: 1 · Flagged: 1.**
- Load-bearing **Flagged** claim: the "dreams-prevent-overfitting → LLM dreaming should generalise" link (finding #5) is an *analogy* Karpathy draws from neuroscience, not an empirically established property of LLM consolidation; treat the *design instinct* (promote the class, not the instance) as sound because the pack already independently holds it (CI2), but do not cite the neuroscience as proof.
- Load-bearing **Inferred** claim: the "A-MEM / LLM-wiki == the pack's knowledge graph" mapping (finding #4) is our synthesis; it is strong (both are typed, linked, evolving Markdown note graphs) but is not asserted by the sources themselves.
- **Currency caveat:** much of the "dreaming" secondary commentary is 2026-dated blog/press material of variable authority; the two load-bearing primary sources (Claude Dreams platform docs, OpenClaw concept docs) are the ground truth and the secondary sources are used only for framing. Both are research-preview / actively-moving surfaces — re-verify on refresh.

## Design implications (what the next phase — `/specify` — should do with this)

The synthesis points at **one new capability with two faces**, both of which the pack's conventions already accommodate:

- **A `/dream` skill (the interactive face).** An on-demand consolidation pass a human runs (or reviews): read this repo's `audit-log.jsonl` + `change-log.jsonl` + `defect-classes.md` + recent session exhaust → run `light → REM → deep` (stage → reflect on recurring themes → score-and-promote) → emit **proposals** (new/updated defect classes with controls, dedupe of the register, knowledge-doc updates, `simplify:`/`assume:` marker harvest) as a **reviewable diff + a Dream Diary entry**, *never* an auto-commit. It is `class → sweep → derive → prevent` (CI2) run *in bulk over the accumulated corpus* instead of one defect at a time. Lead persona: a consolidation role composing the **Domain Researcher** (evidence) + **the Simplifier** (strike non-load-bearing noise) + the **Test Architect** (a promoted lesson is not done until it is a control).

- **A `dream` job (the scheduled face).** The same pass wired to run **offline, on a schedule, across every local repo** in a runner (claude-cowork / OpenClaw / cron / a GitHub Action), producing a branch/PR of proposals per repo. This is where the audit log *evolves* (finding #7): add the outcome signal, session ingestion with redaction, the promotion thresholds, and the Dream Diary.

- **A federation layer (the "share across repos" face — the user's actual ask).** A central, git-committed **fleet learnings store** (e.g. a `learnings/` repo, or the AI-Forward pack itself) that each repo's dream job (a) *contributes* generalised classes to (abstracted away from repo-specifics, PII-scrubbed) and (b) *pulls* from at grounding — so a mistake made once in repo A becomes a control everywhere. This operationalises CI8 ("if the lesson would help any project, raise it upstream via `/extendaibundle`") in **both directions and automatically**, and mirrors NASA's *Collect → Record → Disseminate → Apply* lifecycle and the cross-project `<org>/.agent-memory/` pattern.

- **Guardrails to carry into the spec (non-negotiable, finding #8):** append-only inputs; new-store/new-branch output (never in-place mutation); human review before any promotion lands (PR gate); provenance + confidence label on every promoted item; a taint gate excluding untrusted/tool-authored/secret-bearing content; abstraction-to-class + PII-scrub before anything crosses a repo boundary. These are all restatements of rules the pack already enforces, which is the strongest possible signal the capability *fits*.

- **What NOT to build (the Simplifier's standing veto):** not a vector database, not a runtime memory service, not a model fine-tune, not a new dependency-heavy framework. The pack already has the note graph (knowledge-viz), the append-only history (audit/change logs), the class register (defect-classes), and the read-at-grounding habit. The dream capability is **a consolidation pass over artifacts that already exist**, expressed as stdlib scripts + a skill + a schedulable job — nothing more.

## How to use this base
`/specify` and `/design` cite these files as evidence (BoK §III.1) when scoping the dreaming/consolidation capability. The **overview** at `overview.html` (in this folder) is the human-facing map of techniques for that specification conversation. Refresh when Claude Dreams leaves research preview or OpenClaw's `memory-core` design moves; re-run `/collectknowledge` and bump the date above.
