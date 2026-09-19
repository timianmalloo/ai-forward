---
id: note-20260919-skill-evolution-citation-forms-and-budget
title: "A utility skill cites CO-S0 by naming its own touch-point; the join detail moves to reference/join.md so P5's verbatim sentences fit; every skill now needs the citation, so the lint's older fixtures gained it"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, skills, co-s0, context-budget, lint, owner-review, p8]
links:
  - { to: spec-skill-evolution, rel: relates-to }
  - { to: design-skill-evolution, rel: relates-to }
  - { to: note-20260919-readers-seat-and-citation-placement, rel: refines }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Three decisions below ADR weight taken while landing the P8 skill sweep: (1) the four turn/log
  utilities cite CO-S0 in one sentence that names what they do with a compiled prompt, not the
  consumer sentence, which would be false in them; six plan/prose consumers take the
  reference/co-s0.md pointer; (2) execute-with-coordination's Stage 6 join mechanics move unchanged
  to reference/join.md (CTX-E) so P5's owner-review sentences land verbatim inside the 2% budget;
  (3) rule 5 makes CO-S0 mandatory for every skill, so the readers' older lint fixtures gained the
  token - the directions they assert are unchanged.
---

# Skill evolution: citation forms, the budget and the lint's premise (P8, 2026-09-19)

## Decision 1 — two inline forms, one pointer
The fixed sentence ("Consume the compiled prompt when one is in hand …") describes a **consumer** of a compiled prompt. `also`, `prompts`, `searchprompts` and `auditlog` do not consume one — they re-make it (`/also` recompiles on a cap raise) or show it (`⟲ compiled from <raw id>`, `--raw <id>`, the `kind:compilation` twin). Writing the consumer sentence into them would be a false contract (AI Systems Engineer), and a `reference/co-s0.md` for a 600-token utility is ceremony (Simplifier). So each cites `CO-S0` in the one sentence that names its own touch-point. The six skills that take prose or a plan (`apply-learnings`, `dream`, `session-profiler`, `addpacktorepo`, `updatepack`, `extendaibundle`) take the pointer route from `note-20260919-readers-seat-and-citation-placement` Decision 2, because none had room for the 54-token sentence beside its §7b.3 row. The lint's rule 5 reads the token, not the form; `test_skill_co_s0_citation.py` keeps "exactly once" for the fourteen; `test_verify_skill_contracts.py` pins the six pointers and the four touch-points.

## Decision 2 — the join detail is stage detail
Seam (b) puts ≈1,230 characters of verbatim P5 text into `execute-with-coordination`, whose headroom was 406. The ratchet's own remedy (`--update-baseline`) is a coordinator-owned line; thinning P2's obligations to make room is the defect the Simplifier's gate finding named. The pack's sanctioned third route is progressive disclosure (`pack/context-budget.json` `skills_note`: "stage detail belongs in reference/*.md"): the Stage 6 paragraph that narrates what `conductor-join.py` does moved **unchanged** to `reference/join.md`, and Stage 6 keeps the command, P5's `verify-ruling-citations.py` sentence and a one-line pointer. Measured after: 2,990 tokens against a 3,065 baseline — the skill shrank. The Stage 5 owner-review bullet landed as item 5 of the numbered list (the seam said "last bullet"; the list is numbered). The two-pass "not converging" rule now climbs the kick ladder (CO17) instead of stopping on the paragraph — §7b.3's group A row for this skill, which had not been applied.

## Decision 3 — rule 5 changes the lint's premise, so the older fixtures gained the token
`test_readers_compile_fields.py::LintTests` asserted that a skill with only a seat, or a fan-out cap of zero, or a CO-S2 stop, passes clean. Under rule 5 no skill passes without `CO-S0`, and under rule 7 no dispatcher passes without a deadline and a fallback. The fixtures gained those tokens; every direction those tests assert (seat missing/invalid, fan-out without compile/contract, hard stop without message, dispatch before compile, exit 2) is unchanged and still observed red on its fixture.

## Observed, not estimated
- Red-first: new tests 12 failed / 6 passed on the unedited tree; the lint with rules 5–7 refused **11 across 28** (10 × `compile missing`, 1 × `dispatch without deadline` on `execute-with-coordination`); after the edits `clean - 28 skill(s)`.
- Budget: after the first patch ten skills were over (addpacktorepo +136 tokens, updatepack +89, extendaibundle +77, prepare-for-coordination +67, session-profiler +63, apply-learnings +36, dream +32, auditlog +25, prompts +24, searchprompts +13 past baseline); after the compressions (`patch_skills2.py`, expression only) `clean - no unacknowledged skill growth`.
- `pack-apply.py:527` copies three of the five hook scripts while the Claude hook JSON it merges names all five — an engine seam, reported to the coordinator, not built here.
