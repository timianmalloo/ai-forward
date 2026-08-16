---
id: adr-0002-fleet-learnings-store
title: "ADR-0002: Fleet learnings store in ai-forward; append-only facts + slug-keyed learnings; two federation paths"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [dreaming, federation, data-model, fleet-store]
links:
  - { to: architecture-dreaming, rel: implements }
  - { to: spec-dreaming, rel: implements }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  The fleet learnings store lives in the ai-forward repo; corpus/oracle records are append-only facts
  and a Learning is a slug-keyed dimension whose instances are append-only; general classes federate
  two ways — a push skill (/apply-learnings) and a pull path (/updatepack).
---

# ADR-0002: Fleet learnings store & durable representation

**Status:** Accepted · **Date:** 2026-08-15 · **Deciders:** Data & Persistence Architect, Enterprise Architect, the maintainer

## Context
Approved, generalised learnings need a durable home that (a) every repo can read at grounding, (b) ships controls (tests/lints) to repos, and (c) does not become a runtime service or a second source of truth. The maintainer's instruction: *"the location should be in the ai-forward repo first, then I can apply to an existing repo (with the push skill) OR the repo syncs when it runs the update-pack skill."*

## Decision
1. **Location:** the fleet learnings store lives **in the `ai-forward` repo** at `learnings/fleet-classes.md` (a graph-linked register of *general* classes) plus `learnings/fleet-classes.jsonl` (the machine-readable append-only record). General, control-bearing classes that belong in the pack's own always-loaded discipline are additionally promoted into the pack (the seed register in `continuous-improvement.md` / `defect-classes.md`) via `/extendaibundle`.
2. **Durable representation (per `domain-and-data-modelling.md`):** the audit/change logs and the new `mitigations.jsonl` are **append-only facts**. A **Learning** is a **slug-keyed dimension** (`class slug` = identity) whose `instances[]` are append-only facts. *Grain:* one row in `fleet-classes.jsonl` is exactly one promotion event for one class. **Derive-don't-store:** a class's status/recurrence is computed from its instances, never stored twice.
3. **Two federation paths:** (a) **push** — `/apply-learnings --repos …` reconciles the fleet classes into chosen repos as reviewable diffs; (b) **pull** — a repo running `/updatepack` inherits general classes that were promoted into the pack, through the existing deployment map.

## Alternatives considered
- **A dedicated `learnings/` git repo (submodule) —** rejected as the *primary* home: heavier to set up, and it ships prose without the pack's control-shipping mechanism. Kept available as an option for orgs that want a standalone store.
- **A vector DB / runtime memory service —** rejected (non-goal): imports a runtime + substrate the pack avoids; duplicates the note graph the pack already has.
- **In-place rewrite of the register —** rejected: loses history (the whole value) and makes a bad promotion irreversible.

## Consequences
- **+** Zero new runtime; reads at grounding "for free"; general classes ship as real controls via the pack.
- **+** Append-only + slug-keyed means a re-run appends an instance, never duplicates (idempotent promotion).
- **−** Current-state ("is this class controlled?") is a computed reduction over instances — must be materialised as a labelled, rebuildable cache if it becomes a hot read.
- Reversible: a bad promotion is undone by reverting the append / not applying the diff; the source logs are never mutated.
