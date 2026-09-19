---
id: design-liveness-and-track
title: "Design — progress liveness, the running track and the kick ladder (heartbeat_tick · track_fold · kick ladder · log portable)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination P3"
tags: [coordination, liveness, heartbeat, track, kick-ladder, hooks, p3, design]
links:
  - { to: spec-liveness-and-track, rel: implements }
  - { to: design-message-layer, rel: depends-on }
  - { to: design-typed-seam-requests, rel: depends-on }
  - { to: design-leader-designation, rel: depends-on }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
  - { to: note-20260919-liveness-heartbeat-renews-the-leader, rel: relates-to }
  - { to: note-20260919-liveness-worktree-field-is-a-label, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  One new fact kind (`heartbeat`) and one new event kind (`kick-ladder`) in the existing session
  ledger; a machine-local accumulator between samples in the git common dir; a pure fold
  (`track_fold`) from ledger rows and worktree mtimes to one state per work item; the kick ladder
  as one verb that refuses, counts and records; the `worktree` field made a label and a one-field
  in-place migration. No new store, no daemon, no dependency.
---

# Design: progress liveness, the running track and the kick ladder

- **Spec:** `docs/specs/liveness-and-track.md` (US-1..US-9). **Architecture:** ADR-0007 (the `.agents/` record; `coord-core.py` is the one writer of ledger rows via `append_event`/`append_record`).
- **Author / date:** Track P3 (Python Developer, Peer Mode; Patterns Expert, Simplifier, Test Architect, SRE, Security enacted inline; fan-out 0) · 2026-09-19
- **Grounding traversal:** `spec-liveness-and-track` → (depends-on) `spec-message-layer` (`append_mail` is the only mail writer; `_twin` shape `{type: mail, mail_id, kind, from, to, ref, at, session}`), `spec-typed-seam-requests` (`cmd_request(... "add" ...)` refuses without deadline + fallback), `spec-leader-designation` (`leader_read`/`leader_decide`/`leader_write`). Quoted constraints: "sampled into the ledger at most once per TTL/3" (proposal §4); "zero-delta pings render stalled, never live; empty corpus NOT CHECKED" (plan Fixed contracts); "cap two kicks per work item; count them; nothing automatic" (CO17).

## 1. Responsibility and boundaries

Read liveness from the world and render it; climb the ladder only when asked. In: `heartbeat_tick`, `track_fold`, `cmd_track`, `cmd_kick`, `cmd_log_portable`, `liveness_metrics`, `heartbeat_doctor_line`, `pack/adapters/hooks/heartbeat.py`, hook JSON entries. Out: rulings (P5), the board render (P6 reads the same rows later), any automatic action.

## 2. Data model (settled first — DM1–DM18)

**Grain.** One `heartbeat` row = one *sampled* beat of one session (`at` is the sample instant). One `kick-ladder` row = one climb attempt (ok or refused) by one kicker against one (target session, wi).

**Durable representation** — rows in the existing append-only session ledger `.agents/log/<session>.jsonl` (register class, union merge, tracked by D10). Heartbeats go to the *beating* session's file; kick-ladder rows to the *kicker's* file (the kick mail's twin already lands there via `_twin`).

```
heartbeat    {kind:"heartbeat", session, agent, wi, path:"-", at, seq,
              worktree:<label>, host, event, calls:int, files:int,
              tokens:int|"not recorded", since:float|null, leader_renewed:true|"expired"|null}
kick-ladder  {kind:"kick-ladder", session:<kicker>, agent, wi:<target wi>, path:"-", at, seq,
              to:<target>, rung:0|1|2, outcome:"ok"|"refused", code:<refusal code>|"",
              kicks_before:int, mail_id:str|"", request_id:str|"", stall_age_s:float|null,
              missed_beats:int|null, state:<track state>, deadline_at:float|null}
```

**Additivity.** `calls`, `files`, `tokens` are additive over beats of one session (a session total is a sum). `kicks_before` is a snapshot (non-additive). States are derived (non-additive).

**History rule.** Append-only facts; nothing is updated (Type-2 by construction). The migration `log portable` is the one sanctioned rewrite and touches exactly one field's *representation*, not its meaning (a path → its label), recorded in the note.

**Derive, don't store.** `state`, `missed_beats`, `last_progress`, `source`, `kicks` are computed by `track_fold(events, now, mtimes)`; the `state` copied onto a kick-ladder row is the *state at the kick* (an observation, the SRE's measurement), not a second home for the current state.

**Machine-local accumulator** (not data of record): `<git common dir>/coord/heartbeat/<session>.json` = `{calls, files:[rel paths, capped 64], tokens, last_beat_at}`; when the tree is not a git repository, `<root>/heartbeat/<session>.json`. Never tracked (git never tracks its own dir); rebuilt from nothing when missing. Written atomically (temp + `os.replace`).

**Identity.** Sessions by `AGENT_SESSION` (validated by the existing `SESSION_RE` of coord-mail for mail; the XP seam adds a file-name sanitiser to coord-core — applied if present). Work item by `wi` string.

## 3. Change-surface list (E7)

| surface | writer | compute reader |
|---|---|---|
| store: ledger rows `heartbeat`, `kick-ladder` | `heartbeat_tick`, `cmd_kick` (via `append_event`) | `track_fold`, `liveness_metrics`, `heartbeat_doctor_line` |
| store: `worktree` label on `session-start/end`, `worktree new`, heartbeat | `cmd_session`, `cmd_worktree`, `heartbeat_tick` | occupancy in `cmd_session`; `live_keys` in `cmd_worktree`; `track_fold` mtime lookup |
| store: `.agents/requests.jsonl` `request-add reason=kick-ladder` | `cmd_kick` rung 2 → `cmd_request` | `request_metrics`, P5's `decide list` |
| store: inbox rows `note`/`kick`/`decision-request` | `cmd_kick` → `coord_mail.append_mail` | `coord mail read`, doorbell |
| wire: `coord session heartbeat`, `coord track [--json]`, `coord kick`, `coord log portable` | `_build_parser`/`main` | tests through the CLI (real composition root) |
| host seam: `heartbeat.py` + 4 hook JSONs | this track | the hosts (Claude executed against the contract; others observed-only) |
| doctor/metrics: `pack-doctor` heartbeat line; `coord metrics` liveness block | `check_heartbeat`, `cmd_metrics` | operator |

## 4. Contracts

### 4.1 Exposed
- `heartbeat_tick(root, repo, session, agent, now, *, files=(), calls=1, tokens=None, host="", event="", wi="WI-0", worktree_label="", flush=False) -> dict|None` — accumulates; returns the written row or `None` when the window is open and `flush` is false. Renews the leader when the holder (note F-1).
- `track_fold(events, now, mtimes=None) -> list[dict]` — pure. `mtimes: {label: newest_mtime}`. Row: `session, agent, wi, state, source, last_progress_at, last_beat_at, missed_beats, calls_last, files_last, kicks, blocked_on, deadline_at ("not recorded" rendering), worktree`.
- `cmd_track(root, repo, now, as_json) -> int` — 0 / 4 (NOT CHECKED).
- `cmd_kick(root, repo, target, args, session, agent, now) -> int` — 0 ok · 2 incomplete · 3 refused (cap, not due, no owner) · 4 not checked.
- `cmd_log_portable(paths) -> int` — prints `<file>: <n> row(s) rewritten`; 0.
- `liveness_metrics(events, now) -> dict` — keys with `_reason` when the corpus is empty (R4).
- `heartbeat_doctor_line(root, now) -> (line, is_problem)`.

### 4.2 Consumed (sourced)
- `append_event` (`coord-core.py:212`) — atomic one-write append, LOG-A guard. `read_events` (`:244`).
- `leader_read/leader_decide/leader_write` (`:693/:728/:795`) — renew path.
- `cmd_request(root, "add", now, session, agent, ns, repo)` (`:2418`) with a `Namespace(text, to, deadline, fallback, blob="", ref, contract="", reason="kick-ladder", from_role="", path="")`.
- `coord_mail.append_mail(root, session, {"to","kind","body","ref"})` (`coord-mail.py:288`), loaded by path like `mail-doorbell.py._load_mail` does — the delegate scripts sit beside `coord-core.py`.
- `worktree_inventory(repo)` (`:2553`) — label → path for the mtime fallback.
- Host payloads (KB hook table; README): Claude/Grok `{hook_event_name, session_id, cwd, tool_name, tool_input{file_path|path|notebook_path}, stop_hook_active}`; Copilot `{sessionId, toolName, toolArgs}`; Antigravity `{conversationId, workspacePaths, ...}` — every key optional; the hook never fails on absence.

## 5. Patterns (named, justified, past both lenses)

- **Event sourcing / pure fold** (existing idiom: `fold`, `fold_requests`, `active_sessions`) — the track is a read model; replay is idempotent. Simplifier: no new store, so nothing to keep consistent.
- **Sampling with a local accumulator** (Temporal heartbeat throttling) — bounds ledger growth to ≤ 1 row / 100 s / session; Simplifier: one JSON file, `os.replace`.
- **Refuse-count-record** (existing idiom: `cmd_request`, `cmd_leader.refused`) for the ladder cap.
- **Interpreter-resolution command form** for the hook JSONs (README) — copied verbatim; PLAT-A/B.
- Ladder: stdlib only (`json`, `os`, `time`, `argparse`); reuse of every writer and reader already in the file; no dependency.

## 6. Error and concurrency model

- Two hooks racing on one session (sub-agents share `AGENT_SESSION` only when misconfigured): the accumulator write is `os.replace` (last writer wins, at most one beat's counts lost — accepted; the ledger append is atomic).
- The leader renew inside a beat is a CAS; a stale CAS is recorded as `leader_renewed: null` and never retried inside the hook (D13's retry is the coordinator's).
- Every refusal is a stable code: `COORD-TRACK-NOT-CHECKED`, `COORD-KICK-NOT-DUE`, `COORD-KICK-CAP`, `COORD-KICK-INCOMPLETE`, `COORD-KICK-NO-OWNER`, `COORD-KICK-NOT-CHECKED`.
- The hook: `try/except Exception` at the top level, exit 0, print nothing (the doorbell's contract).

## 7. Failure-mode analysis (mode → disposition)

| mode | disposition | test |
|---|---|---|
| Hook payload malformed / not JSON / not a dict | detect → treat as empty, still count the call | `test_hook_malformed_stdin_exits_0_and_counts` |
| `AGENT_SESSION` unset | prevent → exit 0, write nothing | `test_hook_without_session_writes_nothing` |
| Sample window open on Stop | Stop flushes (zero delta allowed) | US-1 |
| Accumulator unreadable (corrupt JSON) | recover → start from zero, record `since: null` | `test_accumulator_corrupt_resets` |
| Leader ref unreadable | detect → `leader_renewed: null`, beat still written | `test_leader_unreadable_still_beats` |
| Zero-delta beat fresh | render `stalled` (D7) | US-2 |
| Empty corpus | `NOT CHECKED`, exit 4 | US-3 |
| Worktree label unresolved | source `none`, state `stalled` | US-5 |
| Third kick | refuse `COORD-KICK-CAP`, record the refusal | US-6 |
| Rung 2 without fallback | refuse `COORD-KICK-INCOMPLETE` (nothing written) | US-6 |
| Rung 2 with no owner and no live leader | refuse `COORD-KICK-NO-OWNER` | US-6 |
| Mail send fails (inbox full / bad session) | report the `MailError` code; no kick-ladder `ok` row | `test_kick_mail_refused_records_refusal` |
| Legacy absolute `worktree` rows | read as label (basename); migrate with `log portable` | US-9 |
| `log portable` on a non-JSON line | copy byte-for-byte, count as skipped, never fail | `test_portable_keeps_unparseable_lines` |

## 8. Adversarial analysis (STRIDE-lite)

| boundary | threat | disposition |
|---|---|---|
| Hook stdin (host → script) | Tampering: a payload naming `../../etc/passwd` as file_path | mitigate — paths are relativised and *counted*; never opened, never stored (only the count reaches the ledger) |
| `AGENT_SESSION` (env → file name) | Tampering: `../x` as a session id | mitigate — XP's sanitiser (seam) in `append_event`'s caller; until applied, `Path(root)/"log"/f"{session}.jsonl"` is bounded by the existing `resolve_root` check; test with `..` in the id |
| Accumulator in the git dir | Information disclosure: relative paths of touched files, machine-local | accept — same class as `.git/index`; never tracked |
| Ledger rows (tracked) | Information disclosure: absolute paths → PLAT-B | mitigate — label only; gate 1b test |
| Kick ladder (coordinator → target) | Denial of service: a flood of kicks | mitigate — cap 2 per work item, counted; rung 2 is one request |
| Rung 2 request | Repudiation | mitigate — request row + ledger twin + mail twin, all appended |

## 9. Privacy analysis (LINDDUN-lite)

No personal data beyond session ids (opaque labels chosen by the operator) and repo-relative file paths in a machine-local accumulator. Nothing new reaches telemetry or git that was not already a ledger field. No retention job needed: the accumulator is one small file per session, overwritten.

## 10. Telemetry (O1–O13) — instrumentation over inference

Operator questions and their emitting source, on the normal path, no flag:
- *how often does a session beat / with how much progress* → the heartbeat rows themselves (`calls`, `files`, `tokens`, `since`).
- *how long was a track stalled before someone kicked* → `stall_age_s` and `missed_beats` on every `kick-ladder` row; `coord metrics` renders the median (stall-detection latency; baseline 8,143 s).
- *how often was a kick wrong* → `false_kicks` = rung-1 kicks followed by a progress beat from the target within `STALL_AFTER`.
- *how often did the cap fire / did rung 2 happen* → `kicks_refused_cap`, `escalations`.
- *is the heartbeat wired here* → `pack-doctor` heartbeat line; `coord metrics` `heartbeat_reason` when empty.
Every counter over an empty corpus renders a reason, never 0 (R4/IO).

## 11. Test plan (Testing Strategy union; red-first) — `tests/docs_explorer/test_coord_liveness.py`

T-pure fold (boundary set: 0 beats, zero-delta fresh, 299/301 s, blocked over unblocked, done, mtime, unresolved label) · T-CLI through the real entry point (`coord track`, `coord kick` ×4 refusals + rung 0/1/1/cap/2, `coord log portable`, `coord session start` in a linked worktree → no absolute path) · T-hook (`heartbeat.py` with Claude PostToolUse/Stop payloads: sampling, flush, malformed, no session, exit 0 + empty stdout on every path) · T-leader (renew on beat; expired not reclaimed; non-holder untouched) · T-metrics (counters; empty-corpus reasons) · T-doctor (`pack-doctor` line present/absent) · T-portability (gate 1b script over the fixture file). D0: each test names its failing input in its docstring; deterministic clocks (`now` injected; CLI tests seed rows with fixed `at`).

## 12. Conformance and deviations

Local conventions kept: refusal render, `_safe`, `append_event`, `R4` renders, `simplify:` markers, no heredocs in docs, `python3` command form. Deviations: the plan's `tree` → `worktree` (note); Claude Code channel status `observed-only` for the live event (spec A.8).

## Gate record (adversaries enacted inline, fan-out 0)

| adversary | finding | disposition |
|---|---|---|
| Patterns Expert ⇄ Simplifier | the accumulator is a second file — justified? | kept: without it the ledger takes one row per tool call (the spike counted 100+ calls per track); one JSON file is the smallest form |
| Simplifier | `--rung` auto-selection | kept minimal; three branches, each tested; `--rung` overrides |
| Test Architect (hard) | every failure mode in §7 has a named test; the 299/301 boundary is explicit | cleared by red-first runs in `/implement` (not by the author) |
| SRE | latency and false-kick rate computable from rows alone | §10; metrics test asserts the median and the false-kick count on a fixture |
| Security | path from stdin | §8 row 1; negative test with a traversal path asserts nothing is opened (the record carries a count only) |
| Distributed systems | two writers on one accumulator | accepted (one beat's counts), ledger append atomic; documented in §6 |

Verdict: **PASS-WITH-CONDITIONS** (the red-first tests). Rollups (`docs/security/**`) are the coordinator's surface this run — the STRIDE/LINDDUN tables above are the rollup input; reported in the hand-off.

## Status

| | |
|---|---|
| **Completed** | data model, E7 list, contracts sourced, patterns past both lenses, FMEA/STRIDE/LINDDUN, telemetry, test plan |
| **Remaining** | `/implement` red-first; seams (XP sanitiser, P5 hook entries) applied if present |
| **Best next action** | write `test_coord_liveness.py`, run it red, record the count |
