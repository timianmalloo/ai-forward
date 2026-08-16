---
id: kb-continuous-improvement-and-dreaming-open-questions
title: "Continuous Improvement & Dreaming — Open Questions & Failure Modes"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "continuous-improvement"
tags: [dreaming, open-questions, failure-modes, disconfirming, federation]
links:
  - { to: kb-continuous-improvement-and-dreaming, rel: refines }
review-by: "2026-11-13"
summary: >-
  The unresolved forks to carry into /specify (fleet store location, the promotion oracle, safe
  instance-to-class abstraction, cadence, runner), the known failure modes to design against
  (prose memoir, auto-merge, in-place mutation, memory poisoning, over-generalisation, PII leakage),
  and the disconfirming views deliberately sought.
---

# Open questions & domain failure modes

## Unresolved by research (carry into `/specify` as flagged risks)

1. **Where does the fleet learnings store live, and how do repos sync it?** A dedicated `learnings/` git repo (pulled as a submodule / synced by the job) vs. the AI-Forward pack itself (learnings become pack changes via `/extendaibundle`) vs. an `<org>/.agent-memory/` convention. Trade-off: the pack route gets *controls* (tests/lints) shipped everywhere for free but is heavier to change; a plain store is lighter but only ships *prose*. **Best current guess (Flagged):** general, control-bearing classes → the pack via `/extendaibundle` (CI8 already says this); repo-specific or still-prose learnings → a local `learnings/` store. Needs a decision.
2. **What is the promotion oracle without a runtime Evaluator?** Reflexion has an environment that returns success/failure; our audit `outcome` field is set by the skill that ran, which may be optimistic. How do we get a *trustworthy* success signal — from CI results, from git (did the fix stick or get reverted?), from a later defect referencing the same area? **Flagged** — the quality of federation depends entirely on the quality of this signal.
3. **How do we abstract an instance to a class *safely and well*?** Turning "repo X's `OrderConsumer.cs:88` double-charged" into "at-least-once consumer treated as exactly-once" is the whole value — and is a model judgement that can over-generalise (a false universal law) or under-generalise (leak the instance). Needs a rubric + human review; the Simplifier must strike spurious "classes."
4. **What is the right cadence and trigger per repo?** Nightly (OpenClaw default) is fine for active repos but wasteful for dormant ones. Threshold-triggered (N new audit entries) vs. scheduled vs. manual. **Flagged** — likely a small policy, not a constant.
5. **How do we prevent the corpus from poisoning itself?** If the dream pass writes to the audit log / project-memory, and the next pass reads them, a bad promotion could compound. OpenClaw's answer (Diary excluded from promotion source; recalled context stripped so it isn't re-learned) is the pattern; we must replicate the *exclusion* discipline exactly.
6. **Which runner, and what does each actually expose?** claude-cowork, OpenClaw, a GitHub Action, and plain cron differ in scheduling, session-history access, and model-call surface. The vendor APIs are moving (Claude Dreams is research-preview). **Flagged** — must be re-verified by a spike at `/specify`/`/design` time, not assumed.
7. **Does a scheduled model-in-the-loop job fit the pack's "stdlib-only, dependency-averse" identity?** The deterministic staging/scoring/taint steps are pure stdlib; the reflect/consolidate step needs a model. Is the model call in-scope for a *pack* capability, or does the pack ship only the deterministic harness + prompts and leave the model call to the runner? **Flagged** — an identity question, resolved the same way the CLI/doctor question was in `kb-pack-evolution` (ship the mechanics; the model call is the runner's).

## Known failure modes of this domain (design *against* these)

- **Prose memoir instead of a control.** The dominant failure the pack already names (CI6): a "learning" that is a paragraph nobody re-reads at the moment it matters. A dream pass that emits prose has done nothing; it must emit *controls* (or a register entry with a named control-to-build).
- **Auto-merge / self-certification.** Every source that shipped this warns against it. An agent promoting its own learnings into the always-loaded instruction path with no human gate is how a single hallucinated "rule" corrupts every future session. Hard line: PR/diff review before promotion.
- **In-place mutation of the source of truth.** Rewriting `MEMORY.md`/the audit log/the register *in place* loses the history that is the whole value and makes a bad pass irreversible. Emit a new artifact (branch/store/Diary); keep the input append-only; store a preimage.
- **Memory poisoning / contradiction accretion.** Without dedup + contradiction resolution + a taint gate, the store fills with duplicates, stale rules, and untrusted content — the exact rot Claude Dreams exists to fix. A pass without these gates makes the corpus *worse*.
- **Over-generalisation into false universals.** A model that promotes "always do X" from one instance creates a rule that fires wrongly forever. The Simplifier's soft veto and a human review are the countermeasure; abstraction needs a rubric, not vibes.
- **PII / secret leakage across repos.** Federation is the highest-risk surface: a raw instance shared to the fleet store can carry a path, a name, a token. Abstraction-to-class + `scrub.py` + the taint gate must run *before* the boundary, and the Privacy lens holds a veto.
- **Optimistic outcome signals.** If "did it work?" is self-reported by the skill that ran, the corpus over-weights apparent successes and under-learns from quiet failures (the worst kind — the ones that pass tests). The oracle must draw on independent signal (CI, revert history, recurrence).
- **Cost/noise runaway.** An unbounded input window or too-frequent cadence turns a cheap nightly pass into a budget and noise problem. Cap the window, throttle the model call, gate hard on the thresholds.

## Disconfirming views we deliberately sought

- **"Isn't this just a vector-DB memory system with a cron?"** — Sought the strongest form: managed vendor stores (Claude Dreams, MemGPT/Letta) *are* the mainstream answer, and they work. It fares badly *for us* specifically: it imports a runtime + substrate the pack deliberately avoids, and it duplicates a note graph we already committed. The disconfirmation strengthens the framing (adopt the *shape*, reject the *substrate*) rather than overturning it.
- **"Won't a self-improving loop drift or degrade (the classic auto-improvement failure)?"** — This is the real risk, and the sources agree: it degrades *without* the guardrails (review gate, append-only inputs, taint gate, provenance, Diary-excluded-from-promotion, recurrence-as-metric). With them, it is bounded. So the finding is conditional: the capability is safe *iff* the guardrails are load-bearing, not optional — which is why they are stated as invariants (`data-and-constants.md`), not suggestions.
- **"Does the pack even need this — isn't per-defect `class→sweep→derive→prevent` (CI2) enough?"** — The Simplifier's challenge. Per-defect CI2 catches what a human notices *at the moment of a defect*; it misses (a) cross-cutting classes only visible in aggregate, (b) triggered `assume:`/`simplify:` markers nobody re-read, and (c) sharing across repos. The dream pass earns its place precisely on those three, and *only* those three — it does not replace CI2, it batches and federates it. If it grew beyond that, the Simplifier's veto applies.
