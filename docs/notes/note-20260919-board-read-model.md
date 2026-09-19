---
id: note-20260919-board-read-model
title: "Board decisions: acks are not on the page, reading never writes, the writer is imported by path"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, board, mail, ledger, p6, d12]
links:
  - { to: spec-board, rel: relates-to }
  - { to: design-board, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: note-20260919-coordination-decisions-ratified, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  Three sub-ADR decisions taken while building P6 (the board): the audit explorer's Messages
  view shows "ack: not recorded here" because acks are not twinned to the ledger by contract;
  the board emits nothing on read, so its read-rate (the reopen trigger) is measured from the
  shell history and the session profiler; and board post reaches the inbox only through P4's
  append_mail() imported by path, with a --writer override that the tests fill with a fixture.
---

# Board decisions (P6, 2026-09-19)

**Context.** Track P6 of `coordination-p2-p8` built the board (D12) against the fixed store contract while P4 built the writer in a sibling tree. Three questions were resolved below ADR weight.

## 1. The page's ack column reads *not recorded here*
- **Decision.** `docs/audit/index.html` (Messages view) shows `not recorded here — see coord board` in the ack column for every row.
- **Why.** The contract twins every kind *except* `note`, `ack` and `nack` to the ledger, and `audit-log.py render` reads only the ledger (the inboxes are per-machine and git-ignored). The page cannot know ack state without inventing it; IO's rule is to degrade to *not recorded*, never to a plausible wrong value.
- **Reopen trigger.** The maintainer wants acks on the committed page → a `coord request add` to P4 to twin acks; the board then reads them with no change to the fold.

## 2. Reading never writes; read-rate is measured elsewhere
- **Decision.** `coord board` records nothing on read — no "last read" marker, no counter.
- **Why.** The board is a read model, *never a store* (D12); a marker would be a second store and a write on every read. The reopen trigger (read-rate zero after two sprints, D5/§6) is measured from the shell history and `/session-profiler` (invocation count per session), and later by `coord metrics` (P2's file).
- **Gap named.** Until the profiler counts `coord board` invocations, the read-rate is *not recorded*.

## 3. The writer is imported by path, with a `--writer` override
- **Decision.** `board post` imports `append_mail(root, session, entry)` from the sibling `coord-mail.py` by path; `--writer <path>` names a substitute. The board holds no append code (a source test proves it).
- **Why.** Single-writer rule (one writer for the inbox); the file does not exist in the P6 tree until the join, and a hard import would break the tree before then. The fixture writer in `tests/docs_explorer/test_coord_board.py` implements the same signature and schema.
- **assume:** `append_mail` owns the ledger twin for a `ruling`, and a `--to "*"` broadcast is resolved by the writer. *Confirmed by* reading `coord-mail.py` at the join; *if false* the coordinator's step 4 (`board` over real mail) shows a ruling with no twin, and the board is not the file to fix.

## Residuals
- The page's render proof is static markup + `node --check`; `tools/verify-explainer-render.js` covers only the explainer page. A DOM-shim render test for the audit page is the next control if gate-4b-grade proof is wanted here.
- `cmd_render`'s summary line still says `rendered N audit + M change entries` (it was outside the `render` seam this track owned); adding `+ K messages` is a one-line coordinator edit.
