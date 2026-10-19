---
id: design-decision-interrogation
title: "Decision Interrogation Skill Design"
type: design
status: accepted
owner: "@timmalloo"
phase: "decision-interrogation"
tags: [skills, dialogue]
links:
  - { to: architecture-decision-interrogation, rel: refines }
  - { to: spec-decision-interrogation-protocol, rel: implements }
review-by: 2027-03-27
summary: >-
  Defines the reusable question table, serial question loop, insertion points, and fast path used
  by the four authoring skills.
---

# Decision Interrogation Skill Design

## Shared contract

Each skill builds a short list of unresolved consequential questions. A question is consequential
only when its answer changes the artifact, acceptance criteria, architecture, or design direction.
The skill resolves facts itself and does not ask the human to do research it can perform.

Before asking, render:

| Question | Needed for | Recommendation |
|---|---|---|
| concise decision question | artifact choice it controls | preferred answer and one-line reason |

Then ask one question at a time. After each answer:

1. record the decision in the working artifact;
2. remove questions made irrelevant;
3. add a newly exposed question only when it is consequential;
4. stop when the list is empty or the human defers the remaining decision.

## Insertion points

| Skill | During authoring | Before handoff |
|---|---|---|
| `/specify` | Before settling scope, user need, UX flow, or UI archetype when evidence does not decide | Yes |
| `/ui-design` | Before settling direction, archetype, density, interaction, or visual trade-offs | Yes |
| `/define-architecture` | Facts are researched; human product/constraint forks are recorded for closure | Yes |
| `/design-slice` | Facts are researched; unresolved component trade-offs are recorded for closure | Yes |

## Question shape

Each question contains:

- the question;
- what it is needed for;
- the recommendation and reason;
- suggested choices where useful;
- a free-form answer path;
- defer only when the dependent artifact section can remain explicitly unresolved.

## Proof

Static regression tests assert that the shared contract and all four insertion points remain wired.
The existing skill evals provide behavioral regression coverage.

## Adversarial analysis (STRIDE-lite)
Trust boundary: the human ↔ the authoring skill's conversation, and — because all four skills declare `runs_as: either` — the parent agent ↔ a sub-agent running the skill. The implementation is text only: `pack/knowledge/decision-interrogation.md` (DI1–DI6) and the insertion sentences in `pack/commands/{specify,ui-design,define-architecture,design-slice}/SKILL.md`. No script, store, network call or permission is added, and the knowledge doc says so: "ordinary conversation, not a separate security, privacy, identity, or persistence system". **T (tampering):** an answer is written into the working artifact (DI6 step 3), a committed file that goes through the skill's own review — no new tampering surface. **S (spoofing):** **not mitigated.** The author of a decision is neither recorded nor checked. DI4 says to ask "the human" and wait, but nothing says that an answer from a parent agent, a tool result, or text inside a fetched document is not the human's decision. Run as a Sub-Agent, the skill's "human" is its parent, and none of the four skills cites CO-S2 (a stop is a message), so an agent's answer can enter the artifact as a product decision that reads the same as a human one. No test. **R (repudiation):** resolved decisions are written into the artifact and deferrals are listed with their impact (DI5, DI6); a decision carries no actor or time — accepted, the commit and the audit log are the record. **I (information disclosure):** questions and recommendations are built from repository evidence and shown in the same conversation — no new exposure. **D (denial):** the DI2 fast path and the DI4 "remove questions made irrelevant" rule bound the loop; DI4 step 3 can still grow the list with no cap — accepted, because the human can defer (DI5). **E (elevation):** the pattern grants no authority. The one guard against an unasked-for decision is DI5 ("Never silently turn deferral into the recommendation"), and it is prose, not a control. Negative tests: `tests/docs_explorer/test_decision_interrogation_skills.py` pins only the wiring strings (the table header, "one question at a time", the fast path, "ordinary conversation"). Untested: who answered, and the DI5 deferral rule. The "existing skill evals" in Proof are not named, so they cannot be cited as coverage here.

## Privacy analysis (LINDDUN-lite)
No new personal-data category, store or egress. The pattern is instruction text only (`pack/knowledge/decision-interrogation.md`, wired into the authoring skills); no script reads or writes data. The human's answers are work decisions recorded in the artifact being authored (DI6 step 3) and inherit that artifact's Git retention. Questions and answers travel in the existing harness conversation to the existing provider: no new model call, tier or third party.
