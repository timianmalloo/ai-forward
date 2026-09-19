---
id: note-20260919-owner-review-register-and-scan-scope
title: "Owner review: the register opens with Ruling 1, the contract is a JSON object, the gate scans prose not records, a mail failure never changes a write's verdict, and the stop gate counts only what the session sent"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, owner-review, ruling, register, gate, hook, id-a, d6]
links:
  - { to: spec-owner-review, rel: relates-to }
  - { to: design-owner-review, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Six calls made while building P5: (1) docs/notes/rulings.md is committed carrying Ruling 1 —
  the decision to create the register — so the file is never an empty allocator and the
  proposal's pre-existing "Rulings 1–139" mention resolves; (2) the five decision fields travel
  in P1's `contract` as a sorted JSON object; (3) verify-ruling-citations scans prose suffixes
  only (.md .html .txt) — JSON/JSONL records quote other repos' prose verbatim and a quote is not
  a citation; (4) after the request row is written, a mail failure is reported in the JSON and
  never changes the exit; (5) `rule` refuses a non-next number and a self-rule, and accepts the
  literal `next`; (6) the stop gate blocks only on an open decision request the stopping session
  itself sent — requests addressed to it, and the plan's exit-evidence clause, are unevaluable
  here and exit 0.
---

# Decision note: owner review — the register, the contract, the scan scope, the gate

**Context.** Track P5 of `coordination-p3-p5-p8` built the Owner seat's mechanism to the fixed contracts. Six calls were below ADR weight but change what a later reader sees.

## The call
1. **The register is committed with Ruling 1.** `docs/notes/rulings.md` carries `### Ruling 1 — Create the ruling register and rule through it`. An empty register makes the first `rule next` compute 1 correctly anyway; committing Ruling 1 records *why the file exists* in the file, and it resolves the one prose citation already in the corpus (`docs/proposals/owner-coordinator-subagent-coordination.md:125` "Rulings 1–139" — ai-de's range, matched as `Rulings 1` by the citation regex). That resolution is a side effect and is stated here, not hidden. Test rulings created by the suite live in temporary repositories only.
2. **`--contract` is a JSON object** `{"blast_radius","evidence","options","recommendation","reversibility"}` (sorted keys). P1's `request list --json` already surfaces `contract` verbatim; a JSON object needs no grammar to read back.
3. **The citation gate scans prose suffixes only** (`.md`, `.html`, `.txt`) under `docs/`, `pack/`, `.agents/log/`, `.github/`, `.claude/`, skipping `docs/ai-forward-pack/` (a generated copy of `pack/`). Measured before deciding: `docs/audit/audit-log.jsonl:164` quotes an ai-de prompt naming ai-de's ruling number 38; `docs/dreams/drm-0010/dream.json` quotes ai-de's ruling numbers 126/128. Records quote; prose cites. Reopen trigger: a ruling cited only inside a record and nowhere in prose — then add `.jsonl` and define the frozen list ai-de needed.
4. **Mail after the row is best-effort.** `request` writes the P1 row first, then the `decision-request` mail; `rule` appends the heading, resolves, then mails. A mail failure is reported as `"mail": "not sent: <code>"` with exit 0 — a non-zero exit after a successful store write invites a retry that duplicates the request (the doorbell rule: the store is truth, the mail is push).
5. **`rule <n>` refuses what the register does not allow.** `n` must be max(defined)+1 (`COORD-RULING-NOT-NEXT` names the expected number); a defined number is `COORD-RULING-DEFINED`; ruling on a request the same session sent is `COORD-RULING-SELF` (D6, reviewer ≠ author). The literal `next` is accepted so the Owner need not read the register first — the one convenience, justified because it removes the only reason to read the number by hand.
6. **The stop gate counts only requests the stopping session sent.** Requests addressed *to* the session (an Owner stopping without ruling) are out of the fixed contract and are a finding for the coordinator; the plan's second clause (exit evidence named by the plan row that the audit entry does not carry) needs a plan-row parser and an audit-entry shape that do not exist, so it is a path the gate cannot evaluate and exits 0 by the fail-safe rule.

## Alternatives dismissed
- Importing `cmd_request` and calling it with a hand-built `Namespace` — couples to nine attribute names and needs stdout capture; the subprocess is the landed front-door idiom.
- A frozen-undefined list as in ai-de — nothing predates this control; a list that may only shrink starts empty, so it does not exist.
- Writing `HARNESS_STATUS` for the stop hook — the dict lives in `coord-core.py` (P3's file this run); the README table carries the per-host status and the seam asks the coordinator to mirror it.

## Validation condition
Re-check (3) when a ruling is cited only in a record; re-check (6) when the plan-row schema gains a machine-readable exit-evidence list.

## Promotion rule
Promote (1)–(3) to an ADR if the register moves out of `docs/notes/` or gains a second definition site.
