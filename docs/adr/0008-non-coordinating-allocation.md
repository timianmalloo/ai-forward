---
id: adr-0008-non-coordinating-allocation
title: "ADR-0008: Identifiers come from a non-coordinating stdlib scheme — not uuid7, and not branch scanning"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, allocation, ulid, kg-b, spike, stdlib]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
  - { to: defect-classes, rel: relates-to }
review-by: ""
review-suggested: []
summary: >-
  Shared-register identifiers are issued from a stdlib-only, time-ordered, non-coordinating scheme —
  48 bits of millisecond timestamp plus 80 bits from os.urandom, Crockford base32. uuid.uuid7 is
  rejected because it is absent on the installed 3.12 interpreter and present on the "3.x" CI runner;
  branch scanning is rejected because a working 22-branch scanner still collided within the hour.
---

# ADR-0008: Non-coordinating identifier allocation

- **Status:** Accepted · **Date:** 2026-08-20 · **Deciders:** Data & Persistence Architect, Domain Researcher, Distributed Systems Architect, Tech Lead
- **Context spec/architecture:** `docs/specs/agent-coordination.md` (US-3, `NFR-C2`), `docs/architecture-agent-coordination.md` §4.3

## Context

`KG-B` in TheTerrace records **nine** occurrences of client-minted sequential ids colliding across branches — twice reaching `main`, and once **silently destroying an entry** when the collision was resolved by deduping on the id. The prevention built for it scans every remote branch before allocating: it works, it takes about a second over 22 branches, **and it collided again within the hour**, because two sessions that mint before either has pushed are invisible to each other by construction. Its own addendum records that limit as *measured rather than predicted*.

The control ladder therefore points at rung 1 — **make it impossible**. Nothing below it has held.

## Decision

We will issue identifiers from a **non-coordinating, time-ordered scheme implemented in the standard library**: 48 bits of millisecond timestamp, 80 bits from `os.urandom`, rendered Crockford base32 as 26 characters. About ten lines, no dependency, no version sensitivity, lexicographically sortable by time.

The allocator **serves the repository's existing registers**, not only this layer's own record. Adoption is expand-migrate-contract: new ids come from the allocator, **every existing identifier keeps its value**, nothing is renumbered, no history is rewritten (`NFR-C2`).

## Alternatives considered

- **`uuid.uuid7()` from the standard library.** The obvious answer, and **rejected on execution**. **Spike S1:** the installed interpreter is **3.12.10**, where `uuid.uuid7` raises `AttributeError` — it landed in 3.14. This repository's CI workflow pins `python-version: "3.x"`, meaning *whatever is newest*. A stdlib call that exists on the runner and not on the developer's machine is the **`PACK-J`** class by construction: a deployed script whose behaviour depends on a version-specific stdlib surface, broken by a runner auto-upgrade. Adopting it would have been a defect authored inside the architecture that names the class.
- **Branch scanning (the existing allocator).** Rejected as a **design**, not as an implementation. The failure is structural and already measured: scanning shrinks the collision window from "any two sessions the same day" to "any two sessions minting within the same few minutes", and not to zero.
- **A third-party ULID or UUIDv7 package.** Rejected: `NFR-P2` forbids a runtime the pack does not already require, and the pack's identity is dependency-free stdlib scripts.
- **Renumbering the existing schemes to a collision-proof format.** Rejected for the reason it was rejected once before: it would touch every `FR-` and `al-` reference in specs, backlogs, trackers, **commit subjects and merged PR bodies** — places no edit can reach.

## Consequences

- **+** **Verified against the exact condition that defeated its predecessor.** *Spike S1b:* 8 separate processes issuing 500 ids each, **all pinned to the same millisecond**, no shared state and no network — **4,000 issued, 4,000 unique, 0 collisions**.
- **+** Works offline, on a detached HEAD, in a fresh worktree, with no remote configured.
- **+** Time-ordered, so a register still sorts chronologically without a sequence.
- **−** Ids are 26 characters and not human-countable. `FR-142` is easier to say than `01M0GANEPS6EWS2ZYP3Z8S9NG2`. Accepted deliberately: countability is precisely the property that produced nine collisions.
- **−** Two schemes coexist during expand-migrate-contract, and every reader must tolerate both.
- **−** Uniqueness rests on 80 bits of `os.urandom` — probabilistic, not proven. At this issue rate the collision probability is negligible, and **it is the same guarantee as the UUIDv7 the standard library will eventually ship**. Stated rather than implied.
- **Required alongside it (the merge half).** Unique ids stop the *collision*; only a conservation assertion stops the *resolution* from destroying an entry, which is what actually happened. Any merge of a register must fail closed when the resulting entry count falls below the sum of the distinct entries on either side.
