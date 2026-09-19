---
id: note-20260919-doctrine-stages-close-the-document
title: "The doctrine doc ends with its frozen sections: CO-S0 → CO-S1 → CO-S2 → CO-L close the file, and the ceiling was met by cutting prose, never a rule"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, doctrine, context-budget, p0]
links:
  - { to: design-agent-coordination-doctrine, rel: relates-to }
  - { to: spec-agent-coordination-doctrine, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Three calls made while implementing P0: the seeded CO-S0 and CO-L sections sit at the end of
  the doctrine doc (a byte-for-byte contract on a section that runs to end-of-file would break on
  any text appended after it), the ceiling was met at 2,982 est. tokens by removing a References
  section and clause-level prose while keeping every CO line's phrase and citation, and the
  CTX-Q rule landed as its own directive (CO15) rather than as a clause on CO14. Blast radius:
  the doc's section order and any future edit that wants to append after CO-L.
---

# The doctrine doc ends with its frozen sections

*A decision note (`knowledge-visualization.md` V17): below ADR weight, above chat-scrollback weight.*

- **Kind:** decision
- **Confidence:** Verified — `test_agent_coordination_doctrine.py` (19 tests) is green on the landed order; `context-budget.py` reports 2,982 est. tokens (14,405 bytes at 4.83 chars/token).
- **Made during:** `/implement` of `design-agent-coordination-doctrine` (Track P0 of `coordination-p0-p1`).

## The call
1. **Section order.** The spec's reading-surface IA put the three stages between the kick ladder and the scenarios. The landed order is: preamble → vocabulary → CO1–CO2 → CO3–CO15 → CO16 → CO17 → scenarios → struck list → **CO-S0 → CO-S1 → CO-S2 → CO-L**. Reason: the fixed contract freezes CO-S0 and CO-L *byte-for-byte* and the test compares each section from its heading to the next H2 (or end-of-file). In the seed, CO-L is the last section, so its text ends at EOF; any section placed after it would either change CO-L's bytes (a blank line) or force a heading with no blank line before it (valid Markdown, but a trap for the next editor). Ending the file with CO-L keeps the frozen text identical without either trap. The stages stay adjacent (S0 → S1 → S2), which is the order D15 names.
2. **Ceiling.** The first assembly measured 3,389 est. tokens; the design's trim order (struck list → seats column → preamble) yielded ≈ 300 tokens; the rest came from dropping a References section (every id it carried already appears in the preamble or in a CO line) and from clause-level prose in CO1, CO2, CO3, CO8, CO14 and CO16. **Never cut:** the §3.3 bold phrases, their citations, the seeded sections, the protocol-object names, the kick ladder, the struck rows and their triggers. The spec's recovery path (moving the struck list to the KB) was **not** needed and was not taken.
3. **CO15.** "The tree comes before the first spawn" is a directive of its own with the CTX-Q and SP-23 citations, not a clause appended to CO14 (fan-out): a skill or a register row cites `CO15`, and the register's CTX-Q control names it.
4. **`runs_as` enum.** CO-S1 quotes `Coordinator|Sub-Agent|either` exactly as `verify-skill-contracts.py` (P8) accepts it — read from the lint, not recalled.

## Alternatives dismissed
- Stages before the scenarios (the spec's IA) — rejected for the byte-for-byte reason above; the reading order loses little because every stage is found by its `CO-S*` id.
- A blank-line-free `## Scenarios` heading directly after CO-L — valid, but the next editor "fixes" it and the golden-master test fails for a reason they cannot see.
- Moving the struck list to `kb-multi-agent-coordination-open-questions` — the fixed contract wants each struck item *in the doc* with its trigger; only if the ceiling could not be met by prose cuts, which it was.

## Validation condition
Holds until CO-L is no longer the last section by another track's landed decision — at which point the seeded-section test still passes if that track changes the base (`origin/main`) in the same commit, and this note is superseded.

## Promotion rule
No promotion expected: the call shapes one file's layout. If a second always-on doc adopts the frozen-trailing-section convention, write it into `knowledge-visualization.md` and supersede this note.
