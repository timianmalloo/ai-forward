---
id: adr-0003-promotion-oracle
title: "ADR-0003: The promotion oracle is captured successful mitigations (red→green test or human validation)"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [dreaming, promotion-oracle, mitigations, reflexion, testing]
links:
  - { to: architecture-dreaming, rel: implements }
  - { to: spec-dreaming, rel: implements }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  The oracle for 'the fix worked' is a captured MitigationRecord whose verification is either a
  red-observed→green test pair or an explicit human validation; a fix with neither is 'unverified'
  and is never mined as a successful mitigation.
---

# ADR-0003: The promotion oracle

**Status:** Accepted · **Date:** 2026-08-15 · **Deciders:** Test Architect, AI Systems Engineer, the maintainer

## Context
A dream pass over the audit log can see *what was attempted* but not reliably *what worked* — the audit `outcome` field is self-reported by the skill that ran, which is optimistic (the Reflexion insight: a memory is only mine-able with a trustworthy Evaluator). The maintainer's instruction: *"the oracle should be from the errors and mitigations you already see (error → new test → test passes after mitigation) or when you ask me to validate … either way successful mitigations should be captured."*

## Decision
Introduce a **MitigationRecord** (`mitigations.jsonl`, `mit-NNNN`) — the oracle's durable evidence — captured at the moment a fix is verified, by `dream.py capture-mitigation`. A record is a **successful mitigation** only if its `verification` is one of:
1. **`oracle: red-green`** — a test was **observed failing before** the fix and **passing after** (the CI6 red-first discipline *is* the oracle; the test ids + the git before/after are the evidence). This is the strongest, automatable signal and the primary source.
2. **`oracle: human-validated`** — the agent asked the maintainer to validate a change and they approved; the record carries the prompt + the approval.

A fix with **neither** is recorded `outcome: unverified` and is **explicitly excluded** from being treated as a successful mitigation by the dream pass (an optimistic self-report is not an oracle). `/implement` and `/investigate` emit a `capture-mitigation` call whenever they observe a red→green transition or receive an explicit human validation.

## Alternatives considered
- **Trust the audit `outcome` field —** rejected: self-reported, optimistic, over-weights apparent successes, under-learns from quiet failures (the worst kind).
- **A separate CI-results integration —** deferred: red→green capture already draws on the test result; a deeper CI hook is a P2+ enhancement, not a build dependency.

## Consequences
- **+** The corpus learns from *what worked*, not only what broke — the positive signal that turns a defect fix into a reusable, control-bearing learning.
- **+** The oracle reuses the pack's existing red-first discipline (CI6) — no new concept for the team.
- **−** Coverage is bounded by where tests exist / where the agent asks — measured by the fraction of fixes producing a record (a tracked, improvable metric, not a silent gap).
- Reversible/auditable: `mitigations.jsonl` is append-only; a mis-captured record is superseded, never edited in place.
