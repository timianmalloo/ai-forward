---
id: adr-0004-instance-to-class-abstraction
title: "ADR-0004: Safe instance→class abstraction — deterministic strip, model name, generalisation guards, human gate"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [dreaming, abstraction, federation, privacy, over-generalisation]
links:
  - { to: architecture-dreaming, rel: implements }
  - { to: spec-dreaming, rel: implements }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  Defines the safe instance→class abstraction: deterministically strip specifics + PII, model-name the
  shape, enforce five generalisation guards (evidence threshold, falsifiable control, boundary
  statement, retained provenance, no PII across the boundary), and never promote without the human gate.
---

# ADR-0004: Safe instance→class abstraction

**Status:** Accepted · **Date:** 2026-08-15 · **Deciders:** the maintainer (delegated the design), AI Systems Engineer, the Simplifier, Privacy & Data Governance

## Context
Turning "repo X's `OrderConsumer.cs:88` double-charged on redelivery" into "at-least-once consumer treated as exactly-once" is the entire value of federation — and the single riskiest step. It can **over-generalise** (a false universal law that fires wrongly forever), **under-generalise** (leak the instance / not reusable), or **leak** (carry a path, a name, a token across a repo boundary). The maintainer asked us to define the procedure.

## Decision
The abstraction is a **deterministic-first, model-assisted, human-verified** procedure with five hard guards. It runs in `apply-decisions` (for approved-general items) and again in `/apply-learnings` (before crossing a repo boundary).

**Procedure**
1. **Strip (deterministic):** remove repo name, file paths, line numbers, identifiers, concrete values, and run `scrub.py` for secrets/PII → leaving the *shape*. Structural taint gate excludes untrusted/tool-authored/`system` origins.
2. **Name (model, REM step):** state the class as a **signature** ("a persisted field with no compute reader"), a **"why it survives"** (which existing controls it passes), and a proposed **control**. The model's output is validated against a schema; a failed/absent call falls back to a deterministic template from the register's own entry shape.
3. **Guard (deterministic gate — all five MUST hold or it is not federated):**
   - **G1 Evidence threshold** — ≥2 distinct instances, *or* 1 instance with an explicitly stated general mechanism; otherwise it stays **repo-local** until it recurs or a human blesses it general.
   - **G2 Falsifiable control** — the class names a control that can be *observed failing* on the un-fixed shape (CI6). An un-testable "always do X" is **rejected**, not promoted.
   - **G3 Boundary statement** — the class states where it applies **and where it does not** (the anti-false-universal guard).
   - **G4 Retained provenance** — the class links back to its *scrubbed* instances so a reviewer can check the abstraction is faithful (and so it is auditable).
   - **G5 No specifics cross the boundary** — after strip+scrub, the class carries no path/name/value/secret/PII; the shared item is a *shape + a control*, never a raw instance.
4. **Gate (human):** the abstraction is a **proposal** shown in the review view; the Simplifier strikes spurious "classes"; the maintainer approves. Nothing is federated without approval.

## Alternatives considered
- **Fully-automatic model abstraction —** rejected: over-generalisation risk with no gate corrupts every repo. The model *proposes*; it never *promotes*.
- **Never abstract (share raw, scrubbed instances) —** rejected: not reusable across repos and leaks specifics; defeats the point.
- **A similarity/embedding index to cluster instances into classes —** rejected by the Simplifier: out-of-identity dependency weight; the register's stable slugs + human review do the clustering.

## Consequences
- **+** The riskiest step is bounded: a false universal can be *proposed* but never *promoted* — residual risk is reviewer fatigue, not silent corruption.
- **+** Privacy is enforced by construction (strip+scrub before the boundary; Privacy veto).
- **−** Requires a human decision per general class (by design — the whole capability is human-gated).
- **Metric:** track approve/reject ratio per proposal kind; a low approve-rate for "New class" signals a bad abstraction prompt to tune.
