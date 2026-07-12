---
id: note-20260712-revert-model-orchestration
title: "Revert the model-orchestration capability"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [decision-note, model-orchestration, revert]
links:
  - { to: note-20260712-model-orchestration-policy, rel: supersedes }
  - { to: forensic-review, rel: depends-on }
  - { to: architecture, rel: relates-to }
review-by: 2027-01-08
review-suggested: []
summary: >-
  Removes the model-orchestration standard, static router, tests, and active wiring after forensic review found the capability unwired and unsafe to claim as automatic enforcement; retains the review and decision history.
---

# Revert the model-orchestration capability

- **Kind:** decision
- **Confidence:** Verified
- **Made during:** human triage after `/forensicreview` of commit `5d7b952`

## The call

Remove the model-orchestration capability from the active AI-Forward Pack. Specifically:

- delete `pack/knowledge/model-orchestration.md`;
- delete `pack/scripts/model-router.py` and its test;
- remove the managed-block, INSTALL, OVERVIEW, and generated-install wiring;
- keep the forensic report and original policy note as immutable history;
- mark the proposed remediation backlog closed by removal.

The capability's direction was reasonable, but the implementation overclaimed automatic
dispatch while remaining advisory, contradicted its hard adversary-independence rule, could
downgrade T2 work, lacked behavioral proof and structured audit evidence, and introduced an
unresolved provider/data-governance boundary. Removing it is safer and simpler than carrying
a normative control that the pack does not enforce.

**User decision:** "revert the orchestrator idea given your findings".

## Alternatives dismissed

- **Keep the standard but delete only the router.** Rejected: the global MUST-level instruction
  would still claim auto-dispatch and hard enforcement.
- **Keep it disabled behind an experimental flag.** Rejected: no experimental binding or eval
  exists; retaining the surface adds maintenance and ambiguity.
- **Implement the forensic backlog immediately.** Rejected: the user selected removal, and the
  backlog requires a fresh approved architecture before implementation.

## Consequence

The pack returns to its prior peer/adversary orchestration model. The Orchestrator continues
to coordinate phases and personas, but the pack makes no model-per-task auto-routing promise.
Any future attempt must begin as a new specification/ADR and clear the forensic constraints
before landing.
