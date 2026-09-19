---
id: design-leader-designation
title: "Design — leader designation (coord leader verbs over refs/coord/leader · the join fence · doctor/metrics · CO-L)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, leader, fencing, epoch, git-ref, compare-and-swap, conductor-join, p2]
links:
  - { to: spec-leader-designation, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: note-20260919-leadership-in-a-ref-not-the-ledger, rel: relates-to }
  - { to: note-20260919-leader-release-keeps-the-epoch, rel: relates-to }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
  - { to: design-coord-enforcement-phase2, rel: relates-to }
  - { to: kb-multi-agent-coordination-data, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  Detailed design for spec-leader-designation: five stdlib verbs in coord-core.py over one blob held
  by `git update-ref <ref> <new> <old>` (the 40-zero old for creation; no -d, no --force), a state
  machine absent/live/expired/released with a strictly monotonic epoch, one constants block (D13), a
  ledger fact per attempted transition, a leader line in doctor, three measures in metrics, and a
  fence step in conductor-join.py that exits 11 before the merge on a lower epoch or an unread ref.
---

# Design: leader designation

- **Status:** Draft
- **Spec / architecture:** `docs/specs/leader-designation.md` (US-1…US-9, NFRs, the Designation aggregate, gate conditions a–d) · ADR-0007 (append-only JSONL per session, `merge=union`, no daemon, fail-open only where the spec says so) · proposal §3.3 invariants 1, 2, 4; §5.3; D2, D3, D13.
- **Delivery phase / vertical slice:** coordination **P2**, built after P0's seeded doctrine doc and P7's compile stage; in parallel with P4 (mail), P6 (board) and P8 (readers) under `coordination-p2-p8`. Real around it: the ledger writer (`append_event`), `read_events`, `_git`, `cmd_doctor`, `cmd_metrics`, `conductor-join.py` steps 1–10 and its `--self-test`. **Absent / mocked:** P3's in-flight table (a reclaim re-establishes nothing here — a skill stage later), P4's dispatch (the epoch is passed by hand via `--epoch`), any push of the ref (out of scope). Mock-substitutable seams: **time** (every pure function takes `now`; the CLI passes `time.time()`) and **git** (a temp repository per test — the contract *is* git, so it is never mocked).
- **Author(s) / date:** Python Developer (lead) + Patterns Expert + The Simplifier + Data & Persistence Architect + Distributed Systems Architect + Security & Identity Architect (peers), 2026-09-19. Adversaries: Test Architect (hard), Security (hard), Distributed Systems (hard), SRE, Patterns Expert ⇄ Simplifier. **Fan-out 0: enacted inline** — see the gate record.

> **Grounding trace (V15):** `design-leader-designation` → `implements` → `spec-leader-designation` (the nine stories; the conditions a–d) → `refines` → `proposal-owner-coordinator-subagent-coordination` (§3.3, §4, §5.3, P2) → `relates-to` → `note-20260919-leadership-in-a-ref-not-the-ledger` (SPK-1..3) and `note-20260919-leader-release-keeps-the-epoch` (release keeps the epoch; quiet period on expiry only) → `depends-on` → `adr-0007-coordination-substrate` → `relates-to` → `design-coord-enforcement-phase2` (the local conventions: a real temp repository per test, `run_cli` with a scrubbed env, exit triple 0/3/4, `render`'s four labelled lines, `_safe` before interpolation) → `relates-to` → `kb-multi-agent-coordination-data` (constants, spikes, invariants 1–4, 7). Code read, not recalled: `coord-core.py` `_git` (drops the return code — a new helper is needed, below), `append_event` (one `write()`, LOG-A guard), `fold` (ignores kinds other than claim/release, so `leader` lines are inert to leases), `resolve_root` (needs only a git repo), `main` (the identity gate is after `worktree`/`session list`/`collaborate`/`request`; `who` must sit before it), `cmd_doctor` (returns 1 on problems), `cmd_metrics` (R4: `None` over an empty corpus); `conductor-join.py` `Join.run` (raises `SystemExit(step)`), `join()` (step 1 inline, not via `run`), `self_test`. No drift between spec and architecture found. **One spec clarification** below.

---

## Responsibility

**One:** hold and answer *who leads, as of which epoch, until when* in a compare-and-swap cell, record every attempted transition in the ledger, and refuse a join whose epoch is stale. Not responsible for: electing, pushing the ref, re-establishing in-flight work after a reclaim, dispatching, or granting path leases.

## Spec clarification (recorded, not drift)

The spec's US-3 says `who` exits 3 when the ref is absent, expired or released. The **fence** treats those three differently: *absent* → not applicable (S2 has no leader; the join proceeds), *expired*/*released* → the epoch still exists and is compared. So `who --json` always carries `state` and, when a record exists, `epoch`; the fence reads the JSON, never the exit code alone. The spec's exit code is kept.

## Data model (settled first — DM1–DM6)

- **Aggregate:** *Designation* (root; identity = the ref). **Invariant:** at most one live designation per repository; the epoch is strictly monotonic and advances by exactly one on every change of holder, never on renewal. Held by the CAS (`update-ref <ref> <new> <old>`), which is the only writer.
- **Durable representation — two stores, one quantity each (DM7):**
  1. **The ref `refs/coord/leader` → a blob** (current state; **Type-1** by CAS — a recorded decision to keep only the present, because the past is in the ledger). JSON, `sort_keys`, one object:
     `{"leader": "<session>"|null, "epoch": <int ≥ 1>, "pinned_at": <float>, "expires_at": <float>, "released_at": <float>|absent, "host": "<harness>"|"unknown", "tree": "primary"|"worktree"|null, "ttl": <float>}`.
     *Writer:* `leader_write` (every verb but `who`). *Compute readers:* `leader_read` for `who`, `doctor`, the fence.
  2. **The ledger fact** in `.agents/log/<session>.jsonl` (`append_event`, union-merged). **Grain:** *one row is exactly one attempted transition of the designation by one session at one instant, identified by (session, seq), recorded when the verb returns.* Fields: the common ones (`kind: "leader"`, `type: "leader"`, `session`, `agent`, `wi: "WI-0"`, `path: "-"`, `at`, `seq`) plus `action` (pin|renew|release|reclaim), `leader` (the target session), `outcome` (ok|refused), `code` (on refusal), `epoch`, `previous_epoch`, `ref_old`, `ref_new`, `expires_at`, `expired_at` (reclaim only), `host`, `tree`. **Measures:** `leader_loss` (count of `reclaim`/`ok` — **additive**), `contested_pins` (count of pin/reclaim refused with `COORD-LEADER-HELD` — **additive**), `reclaim_latency_seconds` = `at − expired_at` per reclaim (**non-additive**; reported as count + median). **History rule:** append-only; a refusal is a row, never an edit. *Writer:* the verb. *Compute reader:* `leader_metrics` in `cmd_metrics`.
- **Derive, don't store:** `state` and `expires_in` are computed from the blob and `now` on every read; never persisted. `epoch` is stored once (the blob) and copied into facts as a recorded value, not a second source.
- **No migration:** the ref is created on first pin; absence is a valid state.

## Contracts

### Exposed

| Surface | Contract | Exit |
|---|---|---|
| `coord leader pin <session> [--ttl N] [--host H] [--reclaim]` | state `absent` → create epoch 1 (`old` = 40 zeros); `released` → epoch + 1; `live` → `COORD-LEADER-HELD`; `expired` → `COORD-LEADER-EXPIRED` (remedy: reclaim after the quiet period); with `--reclaim` → the `reclaim` path. `--ttl` defaults to `LEADER_TTL`, capped at `TTL_CAP` like path leases. | 0 · 3 · 4 |
| `coord leader who [--json]` | prints the record + `state` + `expires_in`; JSON is the blob plus `{"state", "expires_in", "oid"}`; needs no `AGENT_SESSION` | 0 live · 3 absent/expired/released · 4 NOT CHECKED |
| `coord leader renew` | holder (`AGENT_SESSION == leader`) and `live` → `expires_at = now + ttl`, epoch unchanged; else `COORD-LEADER-NOT-HOLDER` / `COORD-LEADER-EXPIRED` / `COORD-LEADER-ABSENT` | 0 · 3 · 4 |
| `coord leader release` | holder and (`live` or `expired`) → `leader: null`, `released_at: now`, epoch kept; else refused | 0 · 3 · 4 |
| `coord leader reclaim <session> [--ttl N] [--host H]` | `expired` and `now ≥ expires_at + LEADER_QUIET` → epoch + 1, records `expired_at`; `expired` inside quiet → `COORD-LEADER-QUIET <n> s left`; `released` → epoch + 1 (no quiet — decision note); `live` → `COORD-LEADER-HELD` (contested); `absent` → `COORD-LEADER-ABSENT` (remedy: pin) | 0 · 3 · 4 |
| any CAS loss | git exits 128 "cannot lock ref … expected" or "reference already exists" → `COORD-LEADER-STALE` (remedy: re-read; retry after `LEADER_RETRY` s) — recorded as refused | 3 |
| `coord doctor` | one line `leader           <holder> epoch <n> expires in <s> s` · `released (epoch <n>)` · `EXPIRED <s> s ago (epoch <n>) - reclaimable after the quiet period` · `none designated` · `NOT CHECKED  [COORD-LEADER-NOT-CHECKED] <reason>` (the last counts as a problem) | unchanged (1 on problems) |
| `coord metrics [--json]` | `leader_loss`, `contested_pins`, `reclaims`, `reclaim_latency_median_seconds` (None when no reclaim), `leader_reason` ("no leader events recorded" when the corpus has none — printed instead of zeros) | unchanged |
| `conductor-join.py … [--epoch N]` | **step 0 — leader fence**, before step 1 and before `--continue`'s step 2: runs `coord-core.py leader who --json` in the join root; NOT CHECKED → refuse; `absent` → "fence not applicable", proceed; else `given = --epoch or the ref's epoch`; `given < epoch` → refuse. A refusal logs `conductor-join: step 0 (leader fence) refused … [COORD-JOIN-EPOCH-STALE|COORD-JOIN-LEADER-NOT-CHECKED]` and exits **11** (`EXIT_FENCE`; steps are 1–10, 0 is success). No merge commit exists after a refusal. | 11 |
| Constants (one block, D13) | `LEADER_REF = "refs/coord/leader"`, `LEADER_TTL = 300`, `LEADER_RENEW = 100`, `LEADER_RETRY = 20`, `LEADER_QUIET = 30`, `ZERO_OID = "0"*40` — cited by name in the doctrine; a test asserts the block exists and the values | — |

### Consumed (source and confidence)

| Contract | Established by | Confidence |
|---|---|---|
| `git update-ref <ref> <new> <old>`: 0 on success; 128 with "cannot lock ref … is at X but expected Y" on a stale `old`; 128 "reference already exists" when `old` is zeros and the ref exists; a blob is an acceptable target | SPK-1 + re-executed 2026-09-19 (git 2.54.0) | Verified |
| `git hash-object -w --stdin` → the blob's oid; the blob is reachable through the ref so `gc --prune=now` keeps it | executed 2026-09-19 | Verified |
| `git rev-parse -q --verify <ref>`: 1 and empty stdout when absent; 0 + oid when present; 128 outside a repository | executed 2026-09-19 (`verify after delete: exit=1`) | Verified |
| `git cat-file -p <oid>` returns the bytes; `cat-file -t` says `blob` | executed 2026-09-19 | Verified |
| refs under `refs/coord/` are shared by every linked worktree (only `HEAD`, `refs/bisect`, `refs/worktree` are per-worktree) | git docs (`gitrepository-layout`, "refs/worktree") — and `coord worktree` already relies on shared refs for `rev-list` | Verified (docs) |
| `append_event(root, event)` accepts any `kind`; `fold` ignores kinds other than claim/release | `coord-core.py` `fold`, read today | Verified |
| `Join.run` raises `SystemExit(step)`; `join()` returns 1 itself on a merge conflict; `main` returns `int(exc.code)` | `conductor-join.py`, read today | Verified |
| zsh: `"$C1:refs/x"` — the `:r` modifier eats the variable; write `"${C1}:refs/x"` | `data-and-constants.md` "Shell hazard" | Verified — no shell strings are built here; git is called as an argv list |

## Patterns (named, justified, ladder-climbed)

- **Compare-and-swap cell / fencing token** (Kleppmann; etcd creation revision) — the ref is the cell, the epoch the token. *Ladder:* rung 3 (git is already installed; stdlib `subprocess`). Rejected: a lock file (no epoch, no CAS across worktrees), the ledger (SPK-3).
- **Pure fold + thin CLI** (the layer's own idiom, `fold`/`check`/`render`) — `leader_state(record, now)`, `leader_decide(action, record, now, me, target)` are pure and take `now`; the CLI wraps them with `time.time()` and git. *Justified:* every state transition is unit-testable without waiting; the concurrency test alone needs processes.
- **Lease with renew-at-TTL/3** (Kubernetes) — constants only; no timer runs inside the tool (the doctrine tells the Coordinator when to renew).
- **Fail-safe read → NOT CHECKED** (R4, the layer's own control) — every read failure is the fourth exit code, never `absent`.
- **Named-step exit** (conductor-join's own idiom) — the fence is a step with a number and an exit code, not an `if` before the loop.
- `simplify:` markers planned: (1) `who` re-reads the ref on every call (four git calls) — ceiling: a Coordinator polling every second; trigger: `metrics` shows > 1 call/s. (2) The median in `metrics` is `statistics.median` over every reclaim ever — ceiling: thousands of reclaims; trigger: `metrics` slower than 1 s.

## Data shapes

```python
LeaderRecord = dict   # the blob's JSON (keys above); validated on read by leader_validate()
# leader_read(repo) -> (record | None, oid | None, err | None)
#   err = {"code": "COORD-LEADER-NOT-CHECKED", "reason": str}   # git failed / not JSON / bad fields
#   (None, None, None) == absent
# leader_state(record, now) -> "absent" | "live" | "expired" | "released"
# leader_decide(action, record, state, now, me, target, ttl) -> (new_record | None, refusal | None)
#   refusal = {"code": ..., "because": ..., "remedy": ...}
# leader_write(repo, record, old_oid) -> (new_oid | None, err | None)   # hash-object -w, update-ref CAS
# _git_status(repo, *args, stdin=None) -> (returncode | None, stdout, stderr)   # keeps the code (rev-parse 1 vs 128)
```

## Error & concurrency model

- **Read-decide-write with CAS.** Read (oid, record) → decide purely → `update-ref <ref> <new> <old=oid>` (or zeros). A loss between read and write is `COORD-LEADER-STALE` (3) and is recorded as a refused attempt; the tool does not loop — the remedy names `LEADER_RETRY`. Two concurrent pins: at most one CAS succeeds by construction (git's ref lock).
- **Exit triple:** 0 / 3 (refused, with `because`/`remedy`) / 4 (NOT CHECKED); 2 on usage. No fifth code in `coord`; the join adds 11.
- **Ledger write after the ref write.** If the ledger append fails after a successful CAS the ref is right and the record is missing; printed as `COORD-NOT-CHECKED-RECORD` on stderr with exit 4 (the state changed; the operator is told the record did not). Recorded as an accepted mode below.
- **Identity.** `pin`/`reclaim` take the target session as a positional; the *recording* identity is `AGENT_SESSION` when set, else the target (a human pinning from a shell without the env). `renew`/`release` require `AGENT_SESSION` and compare it with `leader`.
- **Time.** Wall-clock `time.time()` from the writing process; one machine, one clock (cross-machine is out of scope).
- **`--force` never.** No verb passes `--force`, `-d`, or `--force-with-lease`; the grep test (US-9) walks every `_git`/`_git_status`/`subprocess` invocation in `coord-core.py`.

## Change-surface list (E7)

store (`refs/coord/leader` blob; ledger `kind: leader` rows) → model (`leader_state`, `leader_decide`, constants block) → service (`cmd_leader`; `_git_status`; `leader_read/write`) → projection/wire (`who --json`; `doctor` line; `metrics` fields) → client (`conductor-join.py --epoch` + fence step; the two skills' Stage 6 / Stage 7 lines; `execute-with-coordination` passes `--epoch`) → UI (terminal text: `render`-shaped refusals) → compute reader (`leader_metrics`; the fence's comparison) → doctrine (`agent-coordination.md` §CO-L; `session-worktree-discipline.md` one sentence) → tests (`test_coord_leader.py`, `test_join_epoch.py`; `--self-test` case c).

## Failure-mode analysis

| # | Mode (category) | Disposition | Test |
|---|---|---|---|
| F1 | ref unreadable: git missing, not a repo, permission (dependency) | **detect** → `COORD-LEADER-NOT-CHECKED`, exit 4; doctor problem; fence exit 11 | `test_who_not_checked_when_git_fails`, `test_doctor_not_checked_on_unreadable_ref`, join `test_fence_refuses_not_checked` |
| F2 | blob is not JSON / missing fields / epoch not int (malformed input) | **detect** → NOT CHECKED (never "absent", never a leader) | `test_who_not_checked_on_malformed_blob` |
| F3 | stale `old` (concurrency, lost update) | **prevent** by CAS; **detect** → `COORD-LEADER-STALE` recorded | `test_stale_old_refused_ref_unchanged`, `test_two_concurrent_pins_one_epoch` |
| F4 | two pins race the create (concurrency) | **prevent** — zeros-old create refuses when present (128 "already exists") | `test_two_concurrent_pins_one_epoch` (two processes) |
| F5 | leader dies without release (time/expiry) | **recover** — expiry + quiet + reclaim; **detect** — `metrics.leader_loss` | `test_reclaim_after_quiet_advances_epoch_by_one` |
| F6 | reclaim inside the quiet period (time) | **prevent** → `COORD-LEADER-QUIET` with seconds left | `test_reclaim_inside_quiet_refused` |
| F7 | renew by a non-holder / after expiry (state) | **prevent** → `COORD-LEADER-NOT-HOLDER` / `-EXPIRED` | `test_renew_non_holder_refused`, `test_renew_after_expiry_refused` |
| F8 | release deletes the epoch (state) | **prevent** — release keeps the epoch (decision note) | `test_pin_after_release_advances_epoch` |
| F9 | ledger append fails after a successful CAS (partial write) | **accept** — the ref is the truth; stderr `COORD-NOT-CHECKED-RECORD`, exit 4; residual: one missing fact, reconstructible from the ref's `pinned_at` | `test_ledger_failure_after_cas_exits_4` (read-only log dir) |
| F10 | clock jump backwards on the holder (time) | **accept** — `renew` still writes `now + ttl`; a backward jump shortens nothing already written; out-of-scope step-down rule named in the spec | — (residual) |
| F11 | `--epoch` given but ref absent (input) | **mitigate** — logged "fence not applicable (no leader)"; proceeds (S2) | `test_fence_not_applicable_when_absent` |
| F12 | ref changes between the fence and the merge (time-of-check) | **accept** — the window is the join's own duration; a second Coordinator that reclaims mid-join is the contested case the human is paged on; residual named | — |
| F13 | `who` called outside any repository (dependency) | **detect** — `resolve_root` NOT CHECKED (existing) | existing `resolve_root` tests |
| F14 | oversized / hostile session name (input) | **mitigate** — `_safe` before every interpolation; the blob stores the raw string but the ledger and output are capped | `test_refusal_lines_are_safe` |

## Adversarial analysis (STRIDE-lite)

Trust boundary: **every process with write access to the checkout** (the same boundary as the ledger; NFR-S2 posture — an integrity control, not access control).

| Threat | Disposition | Negative test |
|---|---|---|
| **S** a session pins a name that is not its own | **accept** — designation is by the human; any session may run the human's command; the ledger records who ran it (`session` ≠ `leader` is visible) | `test_ledger_records_recorder_and_target` |
| **T** a hand-written blob | **mitigate** — validated on read; invalid → NOT CHECKED; valid hand-written → accepted as a human override (recorded nowhere but the ref: residual) | `test_who_not_checked_on_malformed_blob` |
| **R** who changed the leader | **mitigate** — every attempt is a ledger row with session/host/tree/at | `test_every_transition_is_recorded` |
| **I** leaks | **mitigate** — the blob holds session id, harness name, `primary|worktree`; no hostname, path or user; `_safe` strips control chars from output | `test_refusal_lines_are_safe` |
| **D** pin-and-never-release | **mitigate** — TTL bounds the hold to 300 s + 30 s quiet | `test_reclaim_after_quiet_advances_epoch_by_one` |
| **E** leadership as a lease grant | **prevent** — no code path reads the ref in `check`/`claim`; leadership grants nothing | `test_leader_ref_does_not_affect_check` |

## Privacy analysis (LINDDUN-lite)

No personal data: the blob and the facts carry a session id (already in every ledger row), a harness name and `primary|worktree`. No hostname, no user name, no path. One line, explicit.

## UI & interaction design

Terminal only. Refusals use `render`'s four-line skeleton (`CODE  target` · `because` · `remedy`, with `held by` when a holder exists); `who` prints six labelled lines; no colour; every state distinguishable from text + exit code. `doctor`'s line aligns with the existing `registry`/`merge driver` columns.

## Telemetry

- **Structured events:** the ledger rows *are* the log (JSONL, stable fields, `at` as the timestamp; `session` is the trace-correlation key the whole layer uses).
- **Stable error codes:** `COORD-LEADER-HELD`, `-QUIET`, `-NOT-HOLDER`, `-EXPIRED`, `-ABSENT`, `-STALE`, `-NOT-CHECKED`; `COORD-JOIN-EPOCH-STALE`, `COORD-JOIN-LEADER-NOT-CHECKED`.
- **Metrics:** `leader_loss`, `contested_pins`, `reclaims`, `reclaim_latency_median_seconds`; empty corpus → `leader_reason`, never zeros (R4).
- **No HTTP surface** → no RFC 9457. No spans (a CLI of four git calls; `bounded_process` is not involved).

## Test plan (Testing Strategy triggers → directives)

- **D0 hygiene:** temp repositories only; no sleeps in unit tests (`now` injected); the two-process test uses a real repo and asserts on the ref; every subprocess `encoding="utf-8"`; every text write `newline="\n"`.
- **D1 unit:** `leader_state` × 4 states; `leader_decide` × every (action, state, holder) cell in the contract table; boundary: `now == expires_at` (expired), `now == expires_at + LEADER_QUIET` (reclaimable), epoch 1 create.
- **D4 real-infra (git):** stale old refused (SPK-1 as a test); create-while-present refused; two subprocess pins ⇒ exactly one epoch-1 record and one refused row; blob survives the write; the fence in a temp repo (`test_join_epoch.py`) with `--epoch 1` vs ref 2 → exit 11 and no merge commit; `--epoch 2` and no `--epoch` → step 1 runs.
- **D6 schema/golden:** the blob's key set and the ledger row's key set asserted (a renamed field breaks P4/P6/P8 readers).
- **Static grep (US-9):** every `"--force"` literal in `coord-core.py` outside `--force-with-lease` fails — and, to make the test mean something, it asserts that `install --force` (argparse) is excluded only by being an `add_argument` line.
- **Constants:** the block exists once; values 300/100/20/30; `LEADER_RENEW == LEADER_TTL // 3`.
- **Regression:** `test_coord_core.py`, `test_coord_enforcement.py`, `conductor-join.py --self-test` (with the new case c) stay green.

## Tracks for `/prepare-for-coordination`

Already divided: this design is Track P2 of `coordination-p2-p8`; every authored path is in that plan's P2 row.

## Conformance notes

- Follows `coord-core.py`'s conventions: pure decide + CLI wrapper; `_safe`; the exit triple; R4 NOT CHECKED; `append_event` as the only ledger writer; `argparse` sub-subcommand like `request`.
- `conductor-join.py`: the fence is a numbered step (0) with `EXIT_FENCE = 11`, logged in the same `== step n:` shape; the docstring's step list gains the line.
- Skills: one sentence per change; `runs_as: Coordinator` in frontmatter; each `SKILL.md` stays within baseline + 2% (`context-budget.py skills --gate`).
- Doctrine: `agent-coordination.md` gains **CO-L — Leadership**; `load: skill` unchanged; the constants are cited as names, not restated as numbers.

## Flagged risks & residual unknowns

- [Inferred] Claude Code's skill loader ignores an unknown frontmatter key (`runs_as`). *Confirm:* the skill still lists after sync (P8's lint is the consumer). *Breaks:* nothing at runtime — the key is data.
- [Flagged] F12 — the fence-to-merge window. Residual until the join holds the ref for its own duration (a later item, if `metrics.contested_pins` ever shows it).
- [Flagged] `context-budget` headroom: +2% is ≈ 60 tokens per skill; the verbatim CO-S0 sentence alone is ≈ 40. Existing wording in the two skills will be tightened where needed, never a floor removed.

## Proof Pack (`/implement`, 2026-09-19, session `p2-leader`)

Red observed first: `python3 -m pytest -q tests/docs_explorer/test_coord_leader.py tests/docs_explorer/test_join_epoch.py` → **36 failed, 2 passed** before any implementation (the two passing were the detector's own positive check and the pre-existing `--self-test`); after: **38 passed**; with `test_coord_core.py`, `test_coord_enforcement.py` and the two worktree files: **143 passed, 1 skipped** (the read-only-directory test skips under root/Windows only).

| # | Claim | Evidence (test · assertion) | Source | Oracle (how it can fail) | Red-observed | Confidence | Residual |
|---|---|---|---|---|---|---|---|
| 1 | a stale `old` is refused and the ref keeps the other writer's value (SPK-1) | `CasTests.test_stale_old_refused_ref_unchanged` — `err.code == COORD-LEADER-STALE`, `ref_oid() == second` | `coord-core.py` `leader_write` | a writer that ignores `update-ref`'s 128 would land `c` | yes (AttributeError) | Verified | — |
| 2 | `--force` never reaches a git argv in `coord-core.py` | `ForceNeverEmittedTests` — AST walk over `_git`/`_git_status`/`subprocess.*` and `["git", …]` literals; the detector proven on a bad snippet first | test file | a `--force` in any git argv; the detector matching nothing (asserted `> 10` literals) | yes — **it found one**: `worktree remove --force` (pre-existing); removed, cleanup tests still green | Verified | the argparse `--force` option names are excluded by construction (not git argv) |
| 3 | two concurrent pins ⇒ exactly one epoch advances | `PinTests.test_two_concurrent_pins_exactly_one_epoch_advances` — two subprocesses, codes `[0, 3]`, `epoch == 1`, one `ok` + one `refused` row | `leader_write` (zeros-old create) | both exit 0, or epoch 2 | yes | Verified | processes started from threads; the loser is `HELD` or `STALE` depending on interleaving (both asserted) |
| 4 | the join refuses a lower epoch before the merge and proceeds on an equal one | `test_join_epoch.py` (7 cases) + `--self-test` case (c) + demo (`HEAD before 1c49b19 / after 1c49b19 -> no merge`, then `--epoch 3` → exit 0) | `conductor-join.py` `leader_fence` | a merge commit after exit 11; `--epoch 2` refused | yes (argparse exit 2 on `--epoch`) | Verified | F12 window (fence → merge) accepted |
| 5 | quiet period honoured; reclaim after it advances by exactly one | `ReclaimTests` ×4, `StateTests.test_reclaim_boundary_is_expiry_plus_quiet` (`expires_at + QUIET − 0.001` refused, `+ QUIET` allowed); demo "4 s left" then epoch 3 | `leader_decide` | reclaim inside quiet succeeds; epoch jumps by 2 | yes | Verified | — |
| 6 | renew by a non-holder / after expiry refused; release keeps the epoch; pin after release advances | `RenewReleaseTests` ×5 | `leader_decide` | epoch reset to 1 after release | yes | Verified | — |
| 7 | unreadable ref ⇒ NOT CHECKED in `who` (4), `doctor` (problem, exit 1), the fence (exit 11), and a pin over it does not decide | `test_who_not_checked_on_malformed_blob`, `test_who_not_checked_when_git_fails` (empty `PATH`), `test_fence_refuses_when_the_ref_cannot_be_read` | `leader_read`, `_git_status` | "absent" rendered for a broken ref | yes | Verified | — |
| 8 | constants are one block with D13's values | `ConstantsTests` — values, `RENEW == TTL // 3`, each name defined exactly once | constants block | a second definition or a drifted value | yes | Verified | — |
| 9 | metrics: empty corpus is a reason, never zeros; loss / reclaims / median latency / contested counted | `test_metrics_leader_fields`; demo `leader loss 1 · reclaims 2 · median 32.2 s · contested 1` | `leader_metrics` | zeros over an empty ledger | yes | Verified | median over one value is that value (noted in spec gate 6) |
| 10 | leadership grants no lease; refusals are `_safe` | `test_leader_ref_does_not_affect_check`, `test_refusal_lines_are_safe` | `check` unchanged; `_safe` | a control character echoed | yes | Verified | — |
| 11 | ledger write failure after a successful CAS ⇒ exit 4 with `COORD-NOT-CHECKED-RECORD`, ref right (F9 accepted) | `test_ledger_failure_after_cas_exits_4` | `cmd_leader` | exit 0 with a missing record | yes | Verified (skipped as root / Windows) | one missing fact, reconstructible from the ref |

Gates run in the tree (all exit 0): `verify-no-machine-paths.py --root <tree>` (675 files clean; the untracked spec was grepped by hand and one machine path removed), `verify-subprocess-utf8.py`, `verify-portable-text-io.py`, `context-budget.py skills --gate` (the two skills unchanged — see Status), `conductor-join.py --self-test`; `ruff check` on the four touched files reports 8 findings, all on pre-existing lines (E702 parser semicolons, E741 `l`) and none in the new code.

**E7 ticked:** store (ref blob; `kind: leader` rows) ✓ → model (`leader_state`, `leader_decide`, constants) ✓ → service (`cmd_leader`, `_git_status`, `leader_read/write`) ✓ → projection/wire (`who --json`; doctor line; metrics fields) ✓ → client (`conductor-join.py --epoch`, fence; `--self-test` c) ✓ → UI (four-line refusals, `who` lines) ✓ → compute reader (`leader_metrics`; the fence comparison) ✓ → doctrine (`agent-coordination.md` CO-L; `session-worktree-discipline.md` one paragraph) ✓ → **skills (Stage 6 / Stage 7 lines, `runs_as`, the CO-S0 sentence): pending** — see Status.

**Simplifier's delete-list over the diff:** `shrink:` `_leader_lines`/`leader_doctor_line` share three formats (kept: one is a machine-aligned doctor column, the other a human block); `yagni:` `--host` flag (kept: the proposal's common field, P3's reader); `delete:` nothing; **net: −0 lines**. One `simplify:`-class shortcut: `who` re-reads the ref on every call (four git calls) — ceiling a 1 Hz poller; trigger `metrics` showing > 1 call/s.

## Status & next action

| | |
|---|---|
| **Completed** | design; `/implement`: verbs, fence, doctor, metrics, doctrine (CO-L, WT paragraph), 38 red-first tests green, demo transcript, lints and gates |
| **Remaining** | the two `documents` links into `docs/security/threat-model.md` and `docs/security/privacy-review.md` (Coordinator, at the join); ADR promotion of the leadership note; register the boundary-collision class (`p8-readers` held a lease on P2's two skill files for most of the run — seam request `req-01M2XEERW07PGWMJVSTPKY2NC0`; the lease lapsed before P2's close and the skill edits landed in this tree) in `docs/lessons/defect-classes.md` (Coordinator) |
| **Best next action** | Coordinator: `conductor-join.py impl/p2-leader --epoch <coord leader who>` |

## Gate record

`GATE design-slice · 2026-09-19 · fan-out 0 — every adversary enacted inline by the authoring agent; the hard vetoes below are recorded as findings folded in, not cleared by a second reader. Verdict: PASS-WITH-CONDITIONS (advisory until the Coordinator's E16 verification).`

| # | Adversary · finding | Disposition |
|---|---|---|
| 1 | **Test Architect (hard):** "`_git` drops the return code, so `rev-parse -q --verify` cannot tell absent (1) from broken (128) — the design would render broken as absent." | Found at the gate: `_git_status` added (keeps the code); `leader_read` maps 1 → absent, anything else → NOT CHECKED. Test F1. |
| 2 | **Distributed Systems (hard):** "read-decide-write without a retry loop — is a lost CAS a failure?" | It is a *refusal* (3) with the retry constant in the remedy; looping inside the tool would hide contention from `metrics.contested_pins`. Recorded. |
| 3 | **Security (hard):** "a valid hand-written blob is accepted silently." | Accepted with residual: the human is the designator; the ledger shows no `pin` row for that epoch, which `metrics` could flag later (not built). |
| 4 | **Simplifier (soft):** "`--host` flag, `tree`, `ttl` in the blob — three fields the fence never reads." | `host`/`tree` are the proposal's common fields (§4) and P3's readers; `ttl` lets `renew` extend by the pinned TTL rather than the default — kept, each with a reader named. |
| 5 | **Patterns Expert:** "the fence should be `Join.run` like every other step." | It cannot: `run` only knows exit codes; the fence must parse JSON. It is a named step with the same log shape and its own constant — recorded conformance deviation. |
| 6 | **SRE:** "F9 (ledger write after CAS) accepted — is it detectable?" | Yes: exit 4 + stderr, and `doctor` shows a leader whose epoch has no `pin` row when `metrics` is extended (later). Residual named. |

**Conditions carried into `/implement`:** `_git_status`; the fence before `--continue` too; `who` before the identity gate; the grep test walks argv lists, not prose.
