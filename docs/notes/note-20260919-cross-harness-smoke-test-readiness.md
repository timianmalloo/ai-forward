---
id: note-20260919-cross-harness-smoke-test-readiness
title: "Cross-harness smoke-test readiness: what is landed, what each harness channel's status is, and the probe order"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, smoke-test, readiness, harness-status, p3, p5, p8]
links:
  - { to: coordination-p3-p5-p8, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
  - { to: spec-liveness-and-track, rel: relates-to }
  - { to: spec-owner-review, rel: relates-to }
  - { to: spec-message-layer, rel: relates-to }
  - { to: note-20260919-coordination-decisions-ratified, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  The coordination solution's nine build-plan items are landed (P0–P8) and the layer is
  ready for a cross-harness smoke test on this machine, subject to the operator's harness
  logins. Every channel that was not executed live on this machine is recorded
  `observed-only` (CO12) — that list, not the code, is what the smoke test exists to shrink.
  This note names the channels, the probe order that promotes each one, the prerequisites,
  and the residue that is not on the path.
---

# Cross-harness smoke-test readiness (2026-09-19)

**Readiness is the deliverable of `coordination-p3-p5-p8`; running the smoke test is not** (the
compiled prompt's *Not in scope*). A channel is `enforced` only when its refusal was observed on
this machine, `observed-only` when it exists and was executed against the documented payload or
the host's documented contract but not seen fired by the host, `unsupported` when the host has
no such event (CO12). Nothing below was promoted by reasoning.

## 1. What is landed (INSTALL revision 79)

| item | mechanism | landed by | evidence |
|---|---|---|---|
| P0 doctrine | `agent-coordination.md`, `load: always`, 3,000-token ceiling | rev 78 | 19 doctrine tests |
| P1 typed seam requests | `coord request add/receive/ack/resolve/expire`, deadline + fallback mandatory | rev 78 | `test_coord_requests_typed.py` |
| P2 leader designation | `coord leader pin/who/renew/release/reclaim` over `refs/coord/leader`, CAS + epoch, join fence | rev 77 | `test_coord_leader.py`, `test_join_epoch.py` |
| P3 liveness | `coord session heartbeat`, `coord track`, `coord kick`, `heartbeat.py`, leader renew by beat | rev 79 | `test_coord_liveness.py` (41 red → 46 green) |
| P4 message layer | `coord mail send/read/ack`, `coord dispatch`, `mail-doorbell.py` | rev 77 | `test_coord_mail*.py`; claude-code and codex dispatched for real on 2026-09-19 |
| P5 owner review | `coord decide request/rule/list`, `docs/notes/rulings.md`, `verify-ruling-citations.py`, `owner-review-gate.py` | rev 79 | `test_coord_decide*.py` (43 red → 38 green), gate 1g |
| P6 board | `coord board [--follow]`, `board post`, the *Messages* view | rev 77 | `test_coord_board.py` |
| P7 compile stage | `prompt-compile.py`, `verify-compiled-prompt.py`, `/compile` | rev 76 | this run's coordinator prompt `al-01M2XN5XYFCHE5PWRQ3SSJGMM9` compiled and gated |
| P8 skill evolution | `runs_as` on 28 skills, CO-S0/CO-S2 citations, `verify-skill-contracts.py` (gate 1e) | rev 77 + 79 | gate 1e clean on 28 skills |

## 2. Harness channel status on this machine (the smoke test's target list)

| channel | Claude Code | Codex | Copilot CLI | Grok Build | Antigravity |
|---|---|---|---|---|---|
| edit boundary (PreToolUse deny) | **enforcing** (spike S5) | n/a (headless) | **enforcing** (CLI 1.0.80; fails open on a 30 s hook timeout) | observed-only | observed-only |
| session start marker | executed | — | observed-only | observed-only | observed-only |
| mail doorbell | executed (native message) | **`codex queue` verified** 2026-09-20 (S1: two queued pointers arrived as turns, quoted in the track's note) | observed-only | observed-only (S1 Grok session: `additionalContext` line not seen) | observed-only (S1 Antigravity session: no injected step seen) |
| dispatch (`coord dispatch --harness`) | **verified** 2026-09-19 (real `claude -p` child) | **verified** 2026-09-19 | unsupported (no headless CLI found) | not probed | not probed |
| heartbeat (P3) | **enforced** 2026-09-19 (2.1.278: host-fired PostToolUse/Stop rows, `calls: 3` on the first Stop; interactive and headless) | — | observed-only | **enforced** 2026-09-20 (Grok Build 1.0.34: host-fired `PreToolUse` row in `s1-grok.jsonl`) | observed-only (S1 session wrote no row) |
| owner-review stop gate (P5) | **enforced** 2026-09-19 (2.1.278: headless stop refused with the reason while `req-01M2Y374DXAC09F83Q0VXGYSCH` was open; Ruling 2) | — | observed-only (block form) | observed-only | **unsupported** (no stop-class event) |

`harness-status.json` was created on 2026-09-20 by the first `coord mail dispatch --harness claude-code` (finding F-2 closed for Claude Code; the other harnesses are still absent from it): `coord dispatch` writes it on
its first run per harness, so the table above is assembled from the tracks' reports and the
hooks README, not from the file the board reads. The first probe below creates it.

## 3. Probe order (each step promotes one row; stop at the first refusal and record it)

1. **Claude Code, this repo, merged settings.** Open a session with `AGENT_SESSION` set;
   confirm `.claude/settings.json` carries the merged `PostToolUse`, `Stop` and `SubagentStop`
   entries (the pack syncs them from `pack/adapters/hooks/claude-code.settings.hooks.json`).
   Make three tool calls and stop: `coord track` must show one `heartbeat` row with `calls 3` for
   the session → heartbeat **enforced**. Then `coord decide request --to <self> …` and stop: the
   stop must be refused with the reason on stderr → owner-review gate **enforced**; `coord decide
   rule next …`, stop again → allowed.
2. **`coord dispatch --harness claude-code`** with a one-line brief and a 120 s deadline: writes
   `harness-status.json` and a `delegate` mail; the child's exit code is the result.
3. **Codex** (`codex` CLI present): `coord dispatch --harness codex`, then `codex queue` as the
   doorbell → promotes the Codex row; the AGENTS.md instruction set is the same file.
4. **Copilot CLI:** open a session in the repo (the hooks load from `.github/hooks/ai-forward.json`),
   repeat step 1's two checks; `agentStop` block form is what the gate emits → promotes two rows.
   Prerequisite: `gh auth` + Copilot CLI ≥ 1.0.80 (the version the edit boundary was qualified on).
5. **Grok Build** (`/hooks-trust` first) and **Antigravity** (`.agents/hooks.json`; no stop event,
   so only heartbeat and doorbell can promote): repeat step 1's first check.
6. After each promotion, update the status table in `pack/adapters/hooks/README.md` with the
   date and version, and re-run `pack-doctor` — its `harness capability` block must agree.

## 4. Prerequisites the operator holds

- Logins: Claude Code (present), Codex CLI (present at the P4 landing), Copilot CLI with Copilot
  entitlement, Grok Build and Antigravity installs. None of these are in the repo and none can be
  exercised by an unattended coordinator — that is why the smoke test is out of scope for this run.
- The landing commit on `main` (this run's linear landing) so the primary checkout carries revision 79.
- A fresh `coord worktree new` per smoke-test session (WT1); `coord doctor` clean in it.

## 5. Residue not on the path (recorded, deferred with the reason)

- `board post` should let the writer mint the `mail-` id; eight pre-existing ruff findings in
  `coord-core.py` / `conductor-join.py`; the DOM-shim render proof for the audit page — from
  `coordination-p2-p8`, unchanged: none affects a channel's status.
- `coord track`'s `deadline` column is `not recorded` until `coord delegate` lands a work-item deadline
  (`coord kick --deadline-at` carries it meanwhile).
- The owner-review gate's second clause (exit evidence named by the plan row vs the audit entry)
  needs a machine-readable exit-evidence list in the plan schema; it exits 0 today (fail-safe).
- `coord-core.py:64-65` `simplify:` marker names `REQUEST_RETRY` for P3; P3 did not consume it —
  the marker stays for `delegate`.
- Classes GATE-A, MEAS-A, TEST-B, WT-A carry named controls not yet landed (sweeps owed); D13's
  TTL is unchanged because F-1's renew-by-beat removes the lapse once the heartbeat hook is enforced.
- The LINDDUN rollup aggregates one design's table: most designs write their privacy analysis as
  prose under the heading, which the rollup does not read (privacy-review §5 lists the gap).
