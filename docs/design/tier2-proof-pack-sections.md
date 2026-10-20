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

## Adversarial analysis (STRIDE-lite)
Trust boundary: the committed Proof-Pack template → the model that fills it during `/implement` → a committed Proof Pack a reviewer reads. The change is Markdown only: one opt-in section in `pack/templates/proof-pack.template.md:61-97` and one pointer sentence each in `pack/knowledge/end-to-end-integrity.md:40` and `pack/knowledge/instrumentation-over-inference.md:28` (Verified by reading). No script, store, network call or permission is added.

| Boundary | Threat | Disposition | Control, evidence and test |
|---|---|---|---|
| Template → model prefix | **T** (injection): a repo write turns template comment text into an instruction to the model | transfer | Repo write access and branch protection on `main` are the control, as for all pack text. The template inlines no external content (`proof-pack.template.md:61-97`). |
| Filled Proof Pack → reviewer | **S/R**: an agent ticks "Reached?" or "Observed once?" with no evidence behind it | accept | Opt-in by design, with no lint ("Not in scope" above). The reviewer and the test suite are the control. No test; the design records why one would be Coverage Theater. |
| Template → runtime | **E/D**: none | n/a | No executable surface exists to elevate through or exhaust. |

## Privacy analysis (LINDDUN-lite)
| Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|
| Operator-questions table → committed Proof Pack | I/D: "Observed once?" asks for evidence of a real observation, so an author may paste a log line or metric sample that carries a user value or a secret | accept | The table asks for the emitting source (`proof-pack.template.md:87-97`), but nothing in the template says to cite a field name rather than a value. The pack's no-secrets / no-PII rule for committed docs is the only control. No test. | Git retention of the Proof Pack; the only rights path is a history rewrite. |
| Change-surface tables → committed Proof Pack | none: rows name files, members and fields, which is code structure, not personal data (`:67-85`) | n/a | — | Git retention. |

No new personal-data category, store or egress. The template is filled in the existing harness conversation, so no new third party sees it.

**Security and privacy review (2026-10-19):** both sections were written from the shipped template and directives, not from the plan, to close the gap rows in `docs/security/threat-model.md` §4 and `docs/security/privacy-review.md` §5.
