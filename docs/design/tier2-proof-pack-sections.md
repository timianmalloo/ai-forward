---
id: design-tier2-proof-pack-sections
title: "Tier-2 prose→structure: opt-in Proof-Pack sections (E7/E8, IO2) — Design"
type: design
status: accepted
owner: "@timianmalloo"
phase: "1"
tags: [prose-to-structure, proof-pack, end-to-end-integrity, instrumentation, opt-in]
links:
  - { to: design-marker-completeness-lint, rel: relates-to }
review-by: 2026-11-30
summary: >-
  Tier-2 of the prose→structure review: give E7/E8 (change-surface list + reader trace)
  and IO2 (operator questions) a structured home as opt-in tables in the Proof-Pack
  template, referenced from the directives — piloted, deliberately not a mandatory block
  or a failing gate, because the surface list differs per architecture.
---

# Tier-2 — opt-in Proof-Pack sections

## Input (spec)
The **Tier-2** recommendation of `docs/proposals/prose-to-structure-review.html`: adopt
E7/E8 (the change-surface list and writer/compute-reader trace) and IO2 (the operator
questions) as an **opt-in Proof-Pack section for the work that triggers them, not a new
mandatory per-turn block** — and pilot it before considering it standard.

## The decision, and why it is not a gate
Tier-1 shipped with teeth (a lint) because a marker's required fields are the *same*
everywhere, so a mechanical check cannot false-positive. Tier-2 is different **by E7's own
words**: *"the list differs per architecture."* A fixed, mechanically-enforced surface
checklist would false-positive on every project whose layers are not store→…→compute-reader.
So the correct structure here is a **checkable home in a committed artifact** (the T1/T2
Proof Pack, which a reviewer reads) — not a lint, and not a mandatory block. This honours
the proposal's own guard against over-promotion (structure with no *appropriate* checking
surface is ceremony, CT15 / the Simplifier).

## What shipped
- `templates/proof-pack.template.md` gains one **opt-in** H2, *Change reach & instrumentation*,
  with two subsections (the proposal's "fold IO2 into the same section" note):
  - **Change-surface completeness (E7/E8)** — a per-surface reached/where table (the
    canonical path as an adaptable default) + a per-field writer / compute-reader trace.
  - **Operator questions instrumented (IO2/IO10)** — a question → emitting-source → observed
    table.
  Both follow the template's existing *"delete if not applicable"* pattern (as the UI section
  does), so they cost nothing on a change that does not trigger them.
- `end-to-end-integrity.md` E7 and `instrumentation-over-inference.md` IO2 each gain a
  one-line pointer to the section, so a reader of the directive knows where the structure lives.

## Not in scope (deliberate)
- No mandatory per-turn block; no failing lint/gate (would false-positive per-architecture).
- No test that merely re-asserts the template contains the section — it would prevent no real
  failure (CT15, Coverage Theater). The pilot's evidence is whether a real `/implement` run
  catches a miss it would otherwise have shipped; that is measured in use, not in a unit test.

## Pilot & promotion
Run the section on one or two real `/implement` runs (the natural next candidates are any
data-carrying field change). If it catches a miss that the unit suite would have passed
(the E2E-A / DM-C shapes), promote it from opt-in to standard for field-changing T1/T2 work;
otherwise leave it opt-in. That is the same "measure the skip, then promote" loop that
justified CT19 and Tier-1, applied to Tier-2 itself.
