---
id: kb-continuous-improvement-and-dreaming-data
title: "Continuous Improvement & Dreaming — Data, Constants & Invariants"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [dreaming, constants, invariants, guardrails, scoring, corpus]
links:
  - { to: kb-continuous-improvement-and-dreaming, rel: refines }
review-by: "2026-11-13"
summary: >-
  The concrete parameters (Claude Dreams 1-100 sessions; OpenClaw's six weighted deep-ranking signals
  and threshold gates; nightly cron), the AI-Forward corpus a dream pass reads, the eight testable
  invariants (guardrails), and an order-of-magnitude cost/cadence model.
---

# Domain data, constants & invariants

*The concrete numbers, thresholds, schemas, and invariants a dreaming/consolidation capability must honour. Sourced; treat vendor previews as moving targets.*

## Consolidation-pass parameters (observed in the wild)

- **Claude Dreams input bound:** **1–100 sessions** per dream, plus exactly one input memory store. Output is a **separate** store; input is immutable. Beta header **`dreaming-2026-04-21`** (distinct from `managed-agents-2026-04-01`). — *(Verified — [Claude Dreams docs])*
- **OpenClaw deep-ranking signals (weighted, sum = 1.00):** — *(Verified — [OpenClaw docs])*

  | Signal | Weight | Meaning |
  |---|---:|---|
  | Relevance | 0.30 | average retrieval quality for the entry |
  | Frequency | 0.24 | how many short-term signals accumulated |
  | Query diversity | 0.15 | distinct query/day contexts that surfaced it |
  | Recency | 0.15 | time-decayed freshness |
  | Consolidation | 0.10 | multi-day recurrence strength |
  | Conceptual richness | 0.06 | concept-tag density |

  These echo Generative Agents' **importance × recency × relevance** and are a reasonable *starting* weighting to adapt — **not** constants to copy blindly (they were tuned for a different corpus). A candidate promotes only if `minScore`, `minRecallCount`, and `minUniqueQueries` **all** pass (an AND gate, not a weighted average). — *(Verified — weights; Inferred — that we should re-tune)*
- **OpenClaw schedule default:** `0 3 * * *` (nightly at 03:00, local dreaming timezone). — *(Verified)*
- **Promotion budget:** an accepted rewrite must preserve prior entries within a `maxPriorEntryLossFraction`, include every promoted candidate's `Source: path#Lx-Ly` reference, and fit a bootstrap-safe file budget — else it falls back to append-only. — *(Verified — [OpenClaw docs])*

## The AI-Forward corpus the dream pass reads (what already exists)

- **`docs/audit/audit-log.jsonl`** — append-only; per entry the five required fields (`shortname`, `datetime`, `session`, `prompt`, `summary`) + enrichment (`id` `al-NNNN`, `kind`, `skill`, `tool`, `artifacts[]`, `tags[]`, **`outcome`** = `success|partial|failed|blocked`, `change`, `git`). — *(Verified — `audit-and-change-log.md` §1)*
- **`docs/audit/change-log.jsonl`** — append-only; `id` `cl-NNNN`, `kind`, `title`, `prompt`, `summary`, `rationale`, `artifacts[]`, `supersedes`, `audit_ref`, `git{before,after,commits,pushed}`. — *(Verified)*
- **`docs/lessons/defect-classes.md`** — the register; per class: `Signature`, `Why it survives`, `Instances`, `Control` (+ location, or `NONE YET`), `Status` = `controlled|partially-controlled|uncontrolled`. Status counts + "recurrence since last review" are tracked in the header. — *(Verified — `defect-classes.md`)*
- **`docs/docs-index.js`** — derived `window.DOCS_INDEX` (nodes + typed edges) from V2 frontmatter; the graph the pass traverses. — *(Verified — `knowledge-visualization.md` V2)*
- **`simplify:` / `assume:` inline markers** — greppable debt/assumption markers carrying a ceiling + upgrade trigger (or belief + confirmation route + consequence); a *triggered* marker is a lesson already written and unread. Grep: `(#|//) ?(simplify|ponytail|assume):`. — *(Verified — `solution-selection-ladder.md` L5–L6; `no-guessing-protocol.md` NG4)*
- **Session exhaust** — the ephemeral per-session turn/event store; importable via `audit-log.py import --file <export.json>` (maps `prompt`/`summary`/`session`/`datetime`). This is the transcript half a dream pass mines. — *(Verified — `audit-and-change-log.md` AL9)*

## Invariants the capability MUST hold (the guardrails, as testable statements)

1. **Inputs are append-only and never mutated by a pass.** The audit/change JSONL are the source of truth; a dream reads them and writes *elsewhere* (a proposal branch, a Diary). *(Mirrors Claude Dreams "input never modified" + the pack's append-only logs.)*
2. **No promotion lands without human review.** Every promoted class/control/doc-change is a **PR/diff a human accepts**, never an auto-commit. *(Self-improving-AGENTS.md + Claude Dreams discard-model + BoK D3.)*
3. **Every promoted item carries provenance + a confidence label.** `Source: <file>#Lx-Ly` (or the `al-`/`cl-` id it derived from) and Verified/Inferred/Flagged. A promotion with no traceable source is rejected. *(OpenClaw source-ref requirement + BoK §III.1.)*
4. **The taint gate excludes untrusted/tool-authored/secret-bearing content** from the consolidation input — structurally (removed), not by score penalty. Run `scrub.py`; drop `outcome`-less or origin-`untrusted` candidates. *(OpenClaw taint gate + AL4.)*
5. **A control is not a control until observed failing on the un-fixed code.** A promoted class must name a control on the ladder and demonstrate red-first. *(CI6 — carried verbatim.)*
6. **Federation abstracts to the class and strips specifics.** Nothing crosses a repo boundary until it is generalised (instance → class) and PII/secret-scrubbed; the shared item is a *shape + control*, never a raw transcript or path. *(Minimisation; `responsible-ai-policy.md`; the federation-specific rule.)*
7. **Recurrence is the metric of success.** The pass is working when a known class does **not** recur; a second occurrence means the control was wrong, not that someone was careless. *(CI4.)*
8. **The Diary is a narrative, not a source.** The human-readable "what changed" log is excluded from being re-ingested as promotable memory. *(OpenClaw Dream Diary rule.)*

## Cost / cadence model (order-of-magnitude, to refine in `/design`)

- **Cadence:** nightly is the observed default; for a low-write repo, weekly is likely sufficient. Trigger options: schedule (cron/Action), threshold (N new audit entries since last dream), or manual (`/dream`). *(Inferred from OpenClaw default + write-volume reasoning.)*
- **Model cost:** a dream is one (or few) model calls over a bounded window (≤100 sessions; a capped audit slice), so per-repo nightly cost is small and bounded — apply the Token-Budget-Throttle discipline (LOA 2.4) and cap the input window. *(Inferred.)*
- **Determinism split:** the *staging/scoring/taint* steps are deterministic (stdlib scripts over JSONL); only the *reflect/consolidate* step needs a model. Keep the deterministic floor large so the pass is cheap, auditable, and mostly reproducible. *(Design principle — LOA P2, determinism at the floor.)*
