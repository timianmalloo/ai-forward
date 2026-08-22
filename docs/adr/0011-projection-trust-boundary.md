---
id: adr-0011-projection-trust-boundary
title: "ADR-0011: Cross-agent content is untrusted data — the projection ships only after its rendering rules exist"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, security, prompt-injection, trust-boundary, stride, projection]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  The projection renders text authored by one agent's model into another agent's context, which the
  hook schema confirms is a live injection channel. Cross-agent content is therefore treated as data
  with no instruction authority, and the delivery order is inverted so no projection ships before its
  rendering rules and adversarial corpus exist.
---

# ADR-0011: The projection is a trust boundary

- **Status:** Accepted · **Date:** 2026-08-20 · **Deciders:** Security & Identity Architect (lead), Enterprise Architect, Tech Lead, AI Systems Engineer
- **Context spec/architecture:** `docs/specs/agent-coordination.md` (`NFR-S1`, condition 1), `docs/architecture-agent-coordination.md` §7

## Context

Everything else in this layer moves *facts* between machines: a path, an expiry, a session name. The projection moves **prose written by one agent's model into another agent's context** — intents, decision rationales, refusal reasons, block descriptions.

This is not theoretical. Reading the authoritative hook schema for ADR-0010 surfaced the exact channel: `hookSpecificOutput.additionalContext`, described as *"text injected into model context"*. The mechanism that makes a refusal actionable is the same mechanism that makes an injected instruction actionable.

It is also the only boundary in the system that **did not exist before this layer**. Leases, ids and merge drivers all harden things already happening; the projection creates a new path.

## Decision

**Content authored by one agent and rendered into another agent's context is untrusted data with no instruction authority.** It is length-bounded, structurally delimited, rendered under an explicit untrusted heading, and never placed where the reading model would take it as direction. No field in the projection is passed through unescaped.

**And the delivery order is inverted to enforce it:** the projection is **Phase 4**, and its phase gate requires the concrete rendering rules and an adversarial test corpus to exist *first*. The layer is useful without a projection — leases, allocation and the merge driver all work — so nothing forces it early.

## Alternatives considered

- **Treat it as an ordinary formatting concern in `/design`.** Rejected: that is how it stays a formatting concern until something is injected. The spec recorded this as a hard veto resolved-as-requirement with an open threat model, and an ADR is where the ordering obligation becomes binding rather than remembered.
- **Ship the projection early because it is the most visible feature.** Rejected on the same reasoning. It is the most visible and the most dangerous, and it is the only in-scope capability that creates a new attack path.
- **Sanitise by stripping instruction-shaped phrases.** Rejected: a denylist of phrasings is unbounded and fails silently on the phrasing nobody listed. Structural containment — delimit, bound, label, never interpolate — does not depend on predicting the attack.
- **Drop the projection entirely.** Considered seriously, and rejected: US-4 (decisions returned *with the grant*) is the only mechanism aimed at `M3`/`ONE-A`, the most expensive failure mode and the one git never reports. The value is real; the ordering is the mitigation.

## Consequences

- **+** The one new attack path in the design is named, owned, and cannot be shipped by accident.
- **+** The phasing is honest: the capability that needs the most design comes last, rather than first because it demos well.
- **−** Agents work without cross-agent context until Phase 4, so `M3` is unaddressed for three phases. Accepted: `M1`, `M2` and `M4` are all measured and all addressed earlier.
- **−** This ADR **opens** the threat model rather than closing it. The concrete rendering rules and the adversarial corpus are `/design` work on the Phase-4 slice, and this record is what makes that a gate rather than an intention.
- **Related, accepted rather than mitigated:** identity in this layer is **asserted, not authenticated** — an agent can set `AGENT_NAME` to anything. Cryptographic identity is out of proportion for a local tool, so the answer is detection over prevention: the record shows which session acted, and one-session-per-worktree makes impersonation visible rather than silent. Recorded here so it is a decision, not an oversight.
