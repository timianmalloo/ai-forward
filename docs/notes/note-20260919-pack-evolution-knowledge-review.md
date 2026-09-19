---
id: note-20260919-pack-evolution-knowledge-review
title: "Pack-evolution knowledge review: the four evaluated capabilities have all shipped; seven docs re-verified against revision 78"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, knowledge, freshness, v13, pack-evolution, kb-track]
links:
  - { to: kb-pack-evolution, rel: relates-to }
  - { to: kb-pack-evolution-open-questions, rel: relates-to }
  - { to: coordination-p3-xp, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  The V13 review of the seven pack-evolution knowledge docs (review-by 2026-09-12, red on the
  docs workflow since): every "proposed / we have none" claim about the unified CLI, the
  installed-repo doctor, project memory and the Responsible-AI policy + scrub is now false
  because all four shipped; those lines were corrected in place with the verifying file cited,
  external claims were confirmed as written, and review-by moved to 2026-12-18 (knowledge SLA
  90 days). One open question stays Flagged: the memory ledger mechanism shipped but its newest
  entry (2026-08-28) predates this review by three weeks.
---

# Pack-evolution knowledge review (2026-09-19)

**Trigger.** The `docs` workflow on `main` failed its freshness gate (`docs-graph.py freshness
--gate fail`, 7 findings, all `STALE (V13)`) from run 35464651721 onward: the seven docs under
`docs/knowledge/pack-evolution/` carried `review-by: "2026-09-12"`. This is the **KB** track of
`coordination-p3-xp`, executed by a `general-purpose` sub-agent in its own worktree; the
coordinator re-ran the three gates in that tree before accepting the result.

**Rule applied.** V13: reviewing is re-reading against reality, fixing or confirming, then bumping
the date. A claim about *this repo's own state* was checked by opening the file or running
`--help`; external claims (other tools, papers, vendors) were confirmed as written without a web
fetch. No section was added; no scope was added.

## Per document

| doc | result | where verified |
|---|---|---|
| `index.md` (`kb-pack-evolution`) | **fixed** — skills 13 → 28; CLI shipped as `tools/aiforward.py` (`verify · sync · check · new · doctor · graph · audit · scrub`, source-repo only, not `init/update/extend`); doctor shipped as `pack-doctor.py` checking four surfaces; memory shipped (`docs/project-memory.md`, `project-memory-and-obsidian.md`, `obsidian-setup.py`; vault config committed, per-user state ignored); RAI shipped (`responsible-ai-policy.md`, `scrub.py`); `/design` → `/design-slice`; a "Reviewed 2026-09-19 vs rev 78" line added | `.claude/skills/` (28 entries), `docs/ai-forward-pack/INSTALL.md` `counts:`, `tools/aiforward.py`, `pack-doctor.py:710-713`, `.gitignore:42-48` |
| `state-of-the-art.md` | **fixed** — the doctor claim moves Inferred → Verified; ledger, `obsidian-setup.py` and `scrub.py` noted as shipped | `pack-doctor.py`, `pack/scripts/` |
| `comparables.md` | **fixed** — the "today" cells for CLI, doctor, memory, RAI and scrub; "no installed-repo health check" and "no policy doc" marked closed | as above |
| `open-questions.md` | **fixed** — CLI-ergonomics question closed (`aiforward.py:100` prints the pwsh message); Obsidian "git-ignored by default" corrected; doctor mitigation Inferred → Verified; **the memory-ledger question stays Flagged**: the mechanism shipped, the newest ledger entry was 2026-08-28 | `tools/aiforward.py`, `docs/project-memory.md`, `git log` |
| `glossary.md` | **fixed** — ledger "proposed"/Inferred → shipped/Verified; doctor, RAI and scrub entries name the shipped file | `pack/scripts/` |
| `references.md` | **fixed** — `docs-graph.py` subcommand list gains `context`; the CLI is not deployed through the INSTALL map; CLI `update` → `sync` | `docs-graph.py --help`, `INSTALL.md` |
| `sources.md` | **confirmed** — date bump only | — |

## Findings not acted on here

- **RAI wiring gap.** `responsible-ai-policy.md` and `scrub.py` are not referenced from the
  governance checklist in `engineering-governance.md`, which `index.md`'s design implication asked
  for. Recorded as a finding for the coordinator's residue list, not fixed in the KB track.
- **The memory ledger is a memoir by cadence.** `docs/project-memory.md` reached its own
  `review-by` (2026-09-20) with no entry since 2026-08-28 while the audit log grew by hundreds of
  entries. The coordinator appended a ledger entry for the coordination landings in the same
  commit and re-dated it; the standing question (should a skill's closing audit entry also write
  the ledger?) stays open in `kb-pack-evolution-open-questions`.

## Gates (run in the worktree, then re-run by the coordinator)

| gate | result |
|---|---|
| `docs-graph.py derive` | exit 0 — `derived 233 entries -> docs/docs-index.js` |
| `docs-graph.py freshness --gate fail` | exit 0 — `freshness: 0 finding(s)` |
| `docs-graph.py validate` | exit 0 — `defects: 0`, `suggestions: 0` |
