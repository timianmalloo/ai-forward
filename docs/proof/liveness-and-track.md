---
id: proof-liveness-and-track
title: "Proof Pack — progress liveness, the running track and the kick ladder (P3)"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: "coordination P3"
tags: [coordination, liveness, heartbeat, track, kick-ladder, proof-pack, p3]
links:
  - { to: design-liveness-and-track, rel: tested-by }
  - { to: spec-liveness-and-track, rel: tested-by }
review-by: "2027-03-18"
summary: >-
  Forty-one red-first tests (plus the five of the XP seam) prove the heartbeat sampling, the
  fold's four states with the 299/301 s boundary, the NOT CHECKED empty corpus, the kick ladder's
  cap and rung-2 request, the F-1 leader renew, and the F-3 label rule with its migration; the
  hook was executed against the documented Claude Code payload and against this session's own
  ledger. The hook costs 29 ms median per call (40 ms max) against a 100 ms NFR; a first 413 ms
  reading was the shell timing method measuring its own interpreter starts, recorded as a lesson.
---

# Proof Pack: progress liveness, the running track and the kick ladder

- **Change:** `feat/p3-liveness` (track P3 of `coordination-p3-p5-p8`)
- **Spec / design:** `docs/specs/liveness-and-track.md` · `docs/design/liveness-and-track.md`
- **Tier:** T2
- **Author / date:** Track P3 (Python Developer; Test Architect, SRE, Simplifier enacted inline, fan-out 0) · 2026-09-19
- **Red observed:** `python3 -m pytest -q tests/docs_explorer/test_coord_liveness.py` → **41 failed** before any implementation (AttributeError on the module functions, argparse exit 2 on the new verbs, FileNotFoundError on `heartbeat.py`); **41 passed** after; **46 passed** with the XP seam's `test_coord_session_id.py` applied.

## Claims & evidence

| Claim | Evidence | Oracle / why it can fail | Red observed | Confidence | Residual risk |
|---|---|---|---|---|---|
| A zero-delta beat renders `stalled`, never `live`, however fresh (D7) | `TrackFoldTests.test_zero_delta_ping_is_stalled_never_live`, `test_stale_progress_after_zero_delta_still_stalled`; fixture run: `stalled  p5-owner-review` with a 540 s old `calls=0` Stop beat | fails if recency alone makes a row live | yes | Verified | — |
| Three missed beats (300 s) is the boundary | `test_three_missed_beats_boundary` (299 → live, 301 → stalled, `missed_beats == 3`) | fails on an off-by-one or a changed constant | yes | Verified | constants are one block; a retune must move the test |
| Empty corpus is NOT CHECKED, exit 4 | `TrackCliTests.test_empty_corpus_is_not_checked`; fixture run section 1 | fails on "0 tracks, all quiet" | yes | Verified | — |
| Blocked / done from mail twins and session-end | `test_blocked_from_mail_twin_and_unblocked_clears_it`, `test_done_from_session_end_regardless_of_age`, `test_done_from_done_twin` | fails if a twin is misread or an ended session ages into stalled | yes | Verified | — |
| Worktree-mtime fallback; unresolved label is never live | `test_worktree_mtime_fallback`, `test_unresolved_worktree_is_stalled_with_source_none`; real record: `coord-p3-p5-p8 live worktree-mtime` (a session with no hook) | fails if a session with no beat and changing files renders stalled, or no evidence renders live | yes | Verified | `worktree_mtimes` reads the last commit and the changed set, not every file |
| Sampling: one row per 100 s, Stop flushes | `HeartbeatTickTests.test_first_tick_opens_the_window_and_writes_nothing`, `test_sampled_row_carries_the_deltas`, `test_flush_writes_a_zero_delta_row`; hook run: three `PostToolUse` then `Stop` → one row `calls 3 files 1` in this session's own ledger (`.agents/log/p3-liveness.jsonl` seq 2) | fails if two ticks 5 s apart yield two rows, or a Stop is swallowed | yes | Verified | two hooks racing on one session may lose one tick's counts (`os.replace`, accepted) |
| The hook exits 0 and prints nothing on every path; a stdin path is counted, never stored | `HookTests` ×4 incl. `test_a_traversal_path_is_counted_never_stored_or_opened` (`passwd` absent from the ledger text, `files == 1`) | fails if any path prints, exits non-zero, or leaks the path | yes | Verified | — |
| Hook configs carry the seam per host; no machine path | `test_hook_json_entries_per_host`; `verify-no-machine-paths.py --root .` exit 0 | fails if an entry is missing or a path is absolute | yes | Verified | Grok / agy / Copilot entries **observed-only** (CO12) |
| Two kicks then the cap; refusals recorded | `KickLadderTests.test_two_kicks_then_the_cap` (`[(1,ok),(1,ok),(1,refused COORD-KICK-CAP)]`, twins = 2); fixture run section 3 | fails if a third kick lands or is not recorded | yes | Verified | — |
| Rung 2 = P1 typed request + `decision-request` mail; refused without fallback or owner | `test_rung_2_writes_the_typed_request_and_the_mail` (reason `kick-ladder`, ref = last kick mail id, deadline 600 s, fallback), `test_rung_2_needs_a_fallback`, `test_rung_2_needs_an_owner` | fails if the request lacks a field or the mail its ref | yes | Verified | — |
| A live track is not due; `--deadline-at` past makes it due; blocked gets rung 0 | `test_kick_on_a_live_track_is_not_due`, `test_blocked_track_gets_rung_0_notify`, `test_unknown_target_is_not_checked` | fails if a live track is kickable or a note is twinned | yes | Verified | — |
| Metrics: counts, stall latency median, false kicks; reasons over an empty corpus | `MetricsAndDoctorTests` ×3; fixture run: `kicks 2 … 1 refused … 1 rung-2`, `stall detection latency, median 540.2 s`, `false kicks 0` | fails on a wrong count or a 0 over nothing | yes | Verified | false-kick window = STALL_AFTER (a modelling choice, stated) |
| `pack-doctor` heartbeat line | `test_pack_doctor_heartbeat_line` (`not recorded` → `2 session(s) beating … 1 stalled`) | fails if the check is absent or counts over nothing | yes | Verified | — |
| F-1: the holder's sampled beat renews; expired is not reclaimed; non-holder untouched | `test_holder_beat_renews_the_leader`, `test_expired_designation_is_not_reclaimed_by_a_beat`, `test_non_holder_beat_leaves_the_ref_alone`; fixture run section 6 (`leader_renewed True`, `expires in 299 s` after two beats) | fails if `expires_at` stands still, or the epoch moves | yes | Verified | — |
| F-3: no absolute path in `worktree`; occupancy still keyed; `worktree new` too | `WorktreeLabelTests.test_session_start_from_a_linked_worktree_carries_no_absolute_path` (`"wt-a"`, second start refused `COORD-WORKTREE-OCCUPIED`), `test_worktree_new_records_the_label` | fails if the path returns or occupancy breaks | yes | Verified | two trees with one basename share a label (cleanup errs to HELD) |
| `coord log portable` rewrites only `worktree`, byte-identical elsewhere, idempotent, gate-clean | `test_log_portable_rewrites_only_the_worktree_field_idempotently` (unsorted line and non-JSON line unchanged; second run `0 row(s)`; `verify-no-machine-paths.py` exit 0 on the file) | fails if any other byte moves | yes | Verified | — |
| Existing coord suites unaffected | `pytest tests/docs_explorer -k "coord or leader or requests or mail or board or doctrine or cross_platform or doorbell or session_id"` → 392 passed, 3 failed — all three in `test_coord_derived.py` on `git checkout -q master` (the default-branch failures the plan assigns to XP) | a fourth failure would be mine | one regression **was** introduced and caught: `test_coord_core.py::test_a_live_session_blocks_removal` (label vs path in `worktree_safety`) → fixed to honour both forms | Verified (my files) / Inferred (the three are XP's: attributed by message, not re-run on HEAD) | — |
| Lints | `ruff check` on the touched files: 8 findings, all present at HEAD (7 `coord-core.py`, 1 `pack-doctor.py`, plan R-3); gates 1b/1c/1d exit 0 | a new finding would be mine | 1d went red once on `_write_scratch` (`write_text` without `newline`) → fixed | Verified | the 8 pre-existing findings stay R-3 |

## Test coverage of the boundary set

| Boundary | Covered by |
|---|---|
| empty corpus · no session · malformed stdin | `test_empty_corpus_is_not_checked`, `test_without_a_session_nothing_is_written`, `test_malformed_stdin_exits_0_prints_nothing_and_counts_the_call` |
| 299 / 300 / 301 s | `test_three_missed_beats_boundary` |
| zero delta fresh · progress stale | `test_zero_delta_ping_is_stalled_never_live`, `test_stale_progress_after_zero_delta_still_stalled` |
| cap − 1, cap, cap + 1 | `test_two_kicks_then_the_cap` |
| hostile path · unknown target · no owner · no fallback | `HookTests`, `KickLadderTests` |
| legacy absolute row · non-JSON line · second run | `test_legacy_absolute_worktree_matches_label`, `test_log_portable_…` |
| corrupt accumulator | `test_corrupt_accumulator_resets` |

## Change reach & instrumentation

| Operator question | Emitting source | Observed once? |
|---|---|---|
| is a session progressing, with how much? | `heartbeat` rows (`calls`, `files`, `tokens`, `since`) | yes — `.agents/log/p3-liveness.jsonl` seq 2 (this session, via the hook) |
| how long was a track stalled before a kick? | `kick-ladder.stall_age_s`, `missed_beats`; `coord metrics` median | yes — fixture: 540.2 s |
| how often was a kick wrong? | `coord metrics false_kicks` | yes — fixture 0; `test_false_kick_is_counted` 1 |
| did the cap or rung 2 fire? | `kicks_refused_cap`, `escalations` | yes — fixture 1 / 1 |
| is the heartbeat wired here? | `pack-doctor` heartbeat line; `coord doctor`; `heartbeat_reason` | yes — `not recorded` in an empty repo; `4 session(s) beating` in the fixture |
| how much does the hook cost per call? | measured, not emitted: **29 ms median, 40 ms max** per `PostToolUse` with the window open (n = 5, `subprocess.run` timed in one process; `python3 -c pass` 9 ms, `mail-doorbell.py` 31 ms, `coord-core.py --help` 46 ms on this machine) — the spec's 100 ms NFR holds | yes — see Deviations for the first, wrong, reading |

Change-surface (E7): store (`heartbeat`, `kick-ladder`, `worktree` label, `request-add reason=kick-ladder`, inbox rows) → fold (`track_fold`) → wire (`coord session heartbeat`, `track`, `kick`, `log portable`) → host seam (`heartbeat.py`, 4 JSONs) → readers (`coord metrics`, `coord doctor`, `pack-doctor`). Every field has a writer and a compute reader in the table above.

## Failure modes addressed

| Failure mode | Handled in code by | Proven by (test) | or Accepted |
|---|---|---|---|
| malformed / absent payload | `heartbeat.py` fail-open, counts the call | `test_malformed_stdin…` | — |
| `AGENT_SESSION` unset | early `return 0`, nothing written | `test_without_a_session…` | — |
| corrupt accumulator | `_read_scratch` → None → fresh | `test_corrupt_accumulator_resets` | — |
| leader ref unreadable / not holder / expired | `_renew_leader_if_holder` → `None` / `"expired"` | leader tests ×3 | — |
| unresolved worktree | source `none`, state `stalled` | `test_unresolved_worktree…` | — |
| third kick · no fallback · no owner · unknown target · live track | refusals `COORD-KICK-CAP/INCOMPLETE/NO-OWNER/NOT-CHECKED/NOT-DUE` | `KickLadderTests` | — |
| mail refusal mid-kick | `MailError` → recorded refusal, no `ok` row | — | accepted untested this run (the `MailError` path is the message layer's own tested contract; a negative test is a follow-up) |
| two hooks racing on one accumulator | `os.replace` | — | accepted: one tick's counts lost at most; the ledger append is atomic |

## Threats addressed (adversarial analysis)

| Boundary / threat | Disposition | Enforcing code | Negative test | Result |
|---|---|---|---|---|
| hook stdin: hostile path | mitigate | `heartbeat_tick` relativises and counts; never opens | `test_a_traversal_path_is_counted_never_stored_or_opened` | red→green |
| `AGENT_SESSION` as a file name | mitigate | `session_id_error` (XP seam) | `test_coord_session_id.py` ×5 | green (XP observed it red on `main`) |
| tracked ledger: machine paths | mitigate | `_worktree_label` in every writer | `WorktreeLabelTests`; gate 1b | red→green |
| kick flood | mitigate | `KICK_CAP` | `test_two_kicks_then_the_cap` | red→green |

## Privacy findings addressed (LINDDUN-lite)

No personal data beyond operator-chosen session ids; touched-file paths stay in the machine-local accumulator (git common dir), counts only reach the ledger. No new flow.

## Deviations recorded

1. **A first latency reading was wrong by 10×, and the method was the defect.** Timing the hook from the shell with `s=$(python3 -c 'print(time.time())')` on either side read **413 ms**; each timestamp was itself a `python3` start through the pyenv shim (~200 ms), so the reading measured the ruler. Re-measured inside one process with `time.perf_counter()` around `subprocess.run`: **29 ms median / 40 ms max** — the NFR holds. Class for the coordinator's register (instrumentation): *a timing method whose own cost is the same order as the thing timed*; control: measure with the same tool that runs the process, and always print the baseline (`python3 -c pass`) beside the reading.
2. **Claude Code channel: observed-only for the live event.** The hook was executed here against the documented `PostToolUse`/`Stop` payloads and against this session's real ledger, but not as a hook fired by the host (settings load at session start). A live session with the merged settings is the smoke test's step.
3. **Process:** the authored files were edited without a `coord claim` for the minutes of the edit (the brief asked for one); claims were taken for the commit only. Reported, not hidden.
