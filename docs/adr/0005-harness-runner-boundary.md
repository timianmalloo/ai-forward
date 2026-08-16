---
id: adr-0005-harness-runner-boundary
title: "ADR-0005: Ship a stdlib deterministic harness; the model call is an injected boundary owned by the runner; human-gate, no auto-merge"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [dreaming, pack-identity, model-boundary, human-gate, runner]
links:
  - { to: architecture-dreaming, rel: implements }
  - { to: spec-dreaming, rel: implements }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  The pack ships a stdlib-only deterministic harness (dream.py) + prompts; the one model call per phase
  is an injected boundary the runner (claude-cowork / OpenClaw / Claude Dreams / a skill session) owns;
  every durable write and every cross-repo change passes a human gate — never an auto-merge.
---

# ADR-0005: Harness/runner boundary & the human gate

**Status:** Accepted · **Date:** 2026-08-15 · **Deciders:** Enterprise Architect, Security & Identity, the Simplifier, the Tech Lead

## Context
Dreaming needs a model call (the REM abstraction). But the pack's identity is **tool-neutral, dependency-averse, stdlib-only committed Markdown/scripts** — it is *not* a runtime that holds model credentials. And the runner surfaces (Claude Dreams is research-preview; claude-cowork and OpenClaw schedule and expose sessions differently) are moving targets. We must not make an unfamiliar, moving SDK a *build* dependency (Spike Protocol: don't depend on a contract you haven't exercised — and here we deliberately choose not to depend on any single one).

## Decision
1. **Ship the deterministic harness + the prompts.** `dream.py` (stdlib only) does all of light/deep — corpus read, taint/scrub, dedup, scoring, thresholds, rendering, diary, idempotent promotion, reconciliation. It composes existing pack scripts (`audit-log.py`, `docs-graph.py`, `scrub.py`).
2. **The model call is an injected boundary.** For the REM step, the harness **emits a prompt + a candidate bundle** and consumes a **schema-validated completion**. *Who supplies the completion is the runner's job:* a Claude Code / Copilot skill session (the interactive `/dream`), or a scheduled runner (claude-cowork / OpenClaw / a GitHub Action calling a model), or the Claude Dreams API — each a thin adapter, none a build dependency. A missing/failed completion → **deterministic-only** proposals (dedup + mitigation-promotions still flow). This mirrors the `kb-pack-evolution` decision (ship the mechanics; the model call is the runner's).
3. **Human gate, always; no auto-merge (BoK D3).** No durable store is written and no target repo is changed without a human approval. `/dream` and the job *propose*; `apply-decisions` writes only what the human approved; `/apply-learnings` emits *diffs/branches*, never merges; nothing is executed in a target repo.

## Alternatives considered
- **Depend on the Claude Dreams API directly —** rejected as the primary path: research-preview, credential-holding, single-vendor; makes the pack a runtime. Kept as one available adapter.
- **Embed a model client in the harness —** rejected: imports an SDK + credentials the pack deliberately avoids; breaks stdlib-only + tool-neutrality.
- **Auto-apply high-confidence proposals —** rejected (hard): every source warns against it; a single hallucinated rule auto-merged corrupts every future session.

## Consequences
- **+** The subsystem **builds and runs deterministically with no runner SDK** (P1–P3 have zero external deps) — proven at build time.
- **+** Portable across every runner; each integration is a thin, independently-spiked adapter.
- **+** The human gate + diffs-not-merges keeps the whole capability inside the pack's safety posture.
- **−** The interactive `/dream` needs a session that can make one model call for the best abstractions; without it, proposals are deterministic-only (still useful — dedup + mitigations).
- **C1–C11:** cognition/execution split (C3), model output schema-validated before use (C5), fallback declared (C7), no ambient-credential action (C11).
