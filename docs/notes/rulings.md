---
id: rulings
title: "Rulings — the Owner seat's numbered decisions (the only definition site)"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, owner-review, rulings, register, d6, id-a]
links:
  - { to: spec-owner-review, rel: relates-to }
  - { to: design-owner-review, rel: relates-to }
  - { to: spec-agent-coordination-doctrine, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  The ruling register. Each `### Ruling NN — <title>` heading defines exactly one numbered
  decision of the Owner seat; prose anywhere cites it as `Ruling NN`. Written only by
  `coord decide rule`; numbering is read from these headings (no allocator elsewhere, class ID-A);
  `verify-ruling-citations.py` fails a cited number with no heading here and a number defined
  twice. Merge class `register` (union).
---

# Rulings

One heading, one decision. A ruling is never edited in place: a later ruling supersedes it in
prose and cites it. Each block carries the decision request it answered and who ruled. The Owner
seat rules; the requester never rules on its own request (D6, reviewer ≠ author).

### Ruling 1 — Create the ruling register and rule through it

The Owner seat's decisions are numbered headings in this file and nowhere else. A decision
request is P1's typed seam request carrying options, evidence, recommendation, reversibility
and blast radius, a deadline and a fallback; a ruling answers it by `coord decide rule`, which
appends the next heading here, resolves the request with `Ruling NN`, and mails the requester.
A number cited in prose with no heading here, or defined here twice, fails the gate.

- request: none (the register's founding decision, made by the coordination plan `coordination-p3-p5-p8`, fixed contracts) · ruled by: coord-p3-p5-p8 · at: 2026-09-19T20:50:00Z
