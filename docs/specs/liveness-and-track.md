---
id: spec-liveness-and-track
title: "Spec — progress liveness, the running track and the kick ladder (coord session heartbeat · coord track · coord kick)"
type: spec
status: draft
owner: "@timianmalloo"
phase: "coordination P3"
tags: [coordination, liveness, heartbeat, track, kick-ladder, hooks, p3]
links:
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: coordination-p3-p5-p8, rel: implements }
  - { to: spec-message-layer, rel: depends-on }
  - { to: spec-typed-seam-requests, rel: depends-on }
  - { to: spec-leader-designation, rel: depends-on }
  - { to: kb-multi-agent-coordination, rel: relates-to }
  - { to: note-20260919-liveness-heartbeat-renews-the-leader, rel: relates-to }
  - { to: note-20260919-liveness-worktree-field-is-a-label, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  A session's liveness is read from the world, never volunteered: each host's tool-boundary hook
  samples a heartbeat that carries progress deltas into the coord ledger, `coord track` folds
  heartbeats and worktree mtimes into one state per work item (live · stalled · blocked · done,
  zero-delta beats never live, empty corpus NOT CHECKED), and `coord kick` climbs the ladder
  notify → kick (two, counted) → decision request — nothing automatic beyond the record.
---

# Spec: progress liveness, the running track and the kick ladder

- **Status:** Draft
- **Tier (cost-of-error):** T2 — the measured baseline is an 8,143 s stall nobody saw (DC-206); a liveness view that renders a dead session `live` reproduces it with a nicer screen.
- **Author(s) / date:** Track P3 (Python Developer, Peer Mode; Test Architect, SRE and Simplifier enacted inline, fan-out 0) · 2026-09-19
- **Compiled prompt / binding contract:** `docs/coordination/coordination-p3-p5-p8.md` (row P3, "Fixed contracts", findings F-1 and F-3). Refines `docs/proposals/owner-coordinator-subagent-coordination.md` §3.3 (invariants 5, 10, 11), §4 (progress heartbeat, running track), §4b (kick ladder), §7 row P3, D7 (no phi-accrual), D13 (leader constants); `pack/knowledge/agent-coordination.md` CO12, CO17.

## Grounding (traversal)

`proposal-owner-coordinator-subagent-coordination` → (refines) this spec → (depends-on) `spec-message-layer` (mail kinds `note`, `kick`, `decision-request`; the ledger twin), `spec-typed-seam-requests` (`coord request add --deadline --fallback --reason --ref`, rung 2's store), `spec-leader-designation` (`refs/coord/leader`, D13 constants; F-1). Sibling in the same run: `spec-owner-review` (P5) consumes nothing from here and this spec consumes nothing from it (plan "Fixed contracts"). KB: `docs/knowledge/multi-agent-coordination/data-and-constants.md` "Hook surfaces usable as a doorbell or a heartbeat" (Claude Code executed; Antigravity, Grok, Copilot docs-only). Finding at grounding: the plan's F-3 names the field `tree`; the ledger's absolute path lives in **`worktree`** (26 records in the primary's `.agents/log/*.jsonl`, 0 in `tree`, which holds `primary|worktree` — Verified by grep, 2026-09-19). The fix applies to the field that carries the path.

---

## Part A — Functional

### A.1 Problem (solution-independent)

A coordinator with three sub-agents in three worktrees cannot tell a session that is working from one that has died, hung on a refusal, or is waiting on it. The ledger records claims and mail, not *progress*. Sessions do not volunteer liveness (ai-de: 58% never ended, 19% of claims never released — KB, Verified), so liveness must be read from the world: the host's own hook seam, or the files the session changes. A view that reports "all quiet" over an empty record, or `live` over a ping with nothing behind it, is worse than no view (R4; §3.3-5).

### A.2 Personas / jobs-to-be-done

| Persona | JTBD | Evidence |
|---|---|---|
| Coordinator session (Owner seat) | "Which track is progressing, which stalled, which is waiting on me — without opening three terminals" | 8,143 s stall (DC-206); plan `coordination-p2-p8` planned-vs-actual |
| Sub-agent session (any harness) | "Be seen working without doing anything" | the hook fires per tool call; nothing to remember |
| Operator / `pack-doctor` | "Is the heartbeat wired and beating in this repo?" | CTX-H: an uninstalled control looks like a quiet fleet |
| `coord metrics` reader | "Stall-detection latency and false-kick rate, from records" | proposal §7 P3 measurement column |

### A.3 Conceptual domain model (DM1/DM4 — before any surface)

**Bounded context:** *coordination liveness* — a read model over the coordination record (ADR-0007) plus one new fact kind in it. No second store.

**Ubiquitous language:**
- **Heartbeat** — one sampled statement by a session's host that the session did something: *at, session, work item, worktree label, host, event, calls since the last beat, files touched since the last beat, tokens since the last beat (or `not recorded`)*. A heartbeat is a **fact** (append-only, one row = one sampled beat).
- **Progress delta** — `calls + files > 0` (tokens count when recorded). A beat with no progress delta is a **zero-delta ping**.
- **Work item** — the `wi` a session declares (`$AGENT_WI`, default `WI-0`); a **track row** is one (session, work item).
- **Track state** — `live · stalled · blocked · done`, derived at read time, never stored (DM7).
- **Progress source** — `heartbeat`, `worktree-mtime` (the newest mtime under the session's worktree), or `none`.
- **Kick ladder** — rung 0 *notify* (mail `note`), rung 1 *kick* (mail `kick`, cap two per work item, counted), rung 2 *decision request* (P1 typed request + mail `decision-request`); rung 3 is the human (CO17). Each climb is a **kick-ladder event** in the kicker's ledger.
- **Worktree label** — the basename of the worktree path; the value the ledger carries in `worktree` (F-3).

**Aggregates:** the *session ledger file* (`.agents/log/<session>.jsonl`) is the aggregate root for that session's heartbeats and kick-ladder events; its invariant: *append-only, one JSON record per line, no absolute machine path in any field* (LOG-A; PLAT-B). The track row is a projection, not an aggregate.

### A.4 Core scenario

The coordinator dispatches P3, P5 and XP. Every tool call in each sub-agent's session fires the host's tool-boundary hook; `heartbeat.py` accumulates the call and any file it touched, and at most once per 100 s writes a heartbeat into that session's ledger. Twenty minutes in, the coordinator runs `coord track`: P3 `live` (last progress 40 s ago, 37 calls, 4 files since the last beat), XP `blocked` on a seam request to P3, P5 `stalled` (last beat 9 min ago carried zero deltas; 5 missed beats). The coordinator runs `coord kick p5-owner-review --wi P5`: rung 1, mail `kick` sent, counted 1 of 2. Ten minutes later, still stalled: rung 1 again (2 of 2). A third `coord kick` is refused with the cap and the remedy; the coordinator runs it with `--rung 2 --fallback "the coordinator lands P3 and XP; P5 re-dispatched after the join"`: a typed decision request to the leader session and a `decision-request` mail. `coord metrics` now counts 2 kicks, 1 escalation, stall latency 540 s.

### A.5 Non-goals

- **No phi-accrual, no adaptive thresholds** (D7): the rule is deadline passed **or** three missed beats, constants in one block.
- **No automatic kick, reassignment, kill or cleanup** (CO17, WT11): every rung is a verb a person or coordinator runs; the ladder refuses, counts and records — it never acts on its own.
- **No second store**: heartbeats and kick-ladder events are ledger rows; the track is a fold.
- **No body in a hook output**: the heartbeat hook prints nothing on every path (it is not a doorbell; the doorbell exists).
- **No deadline store**: the delegation contract (`coord delegate`) is not landed; the track renders `deadline: not recorded` and `coord kick` accepts `--deadline-at` from the coordinator's plan row. When `delegate` lands, the column reads it.
- **Not P5's `coord decide`**: rung 2 emits P1's request plus the P4 mail, exactly as the plan fixes it.
- **No transcript parsing for tokens** on Claude Code: the hook payload does not carry usage; `tokens: "not recorded"` (IO: never a plausible number).

### A.6 User stories and acceptance criteria (Gherkin; every criterion names a failing input)

**US-1 — Heartbeat from the host seam.**
```gherkin
Given AGENT_SESSION=s1 in a repository with .agents/log/
When heartbeat.py --host claude receives a PostToolUse payload naming tool Edit on docs/x.md
Then no ledger row is written yet (the sample window is open) and the scratch accumulator holds calls=1 files=1
When 100 s pass and a second PostToolUse payload arrives
Then exactly one row {"kind":"heartbeat","calls":2,"files":1,"tokens":"not recorded"} is appended to .agents/log/s1.jsonl
  And the row's worktree field is a basename, never an absolute path   # fails: a row with "/Users/..." or "C:\Users\..."
When a Stop payload arrives 5 s later with nothing accumulated
Then one row with calls=0 files=0 is appended (a Stop flushes)         # fails: the Stop is swallowed and the stall is invisible
```
Failing inputs: the sample window ignored (two rows in 5 s); a hook that exits non-zero or prints on any path (Copilot denies the call); `AGENT_SESSION` unset → exit 0, nothing written.

**US-2 — Zero-delta pings render `stalled`, never `live`.**
```gherkin
Given a session with a session-start and a heartbeat 10 s old carrying calls=0 files=0
When coord track runs
Then the row's state is "stalled" and its source is "heartbeat"      # fails: "live" because the beat is recent
Given instead the heartbeat carries calls=3 and is 10 s old
Then the state is "live"
Given instead the last beat with progress is 301 s old
Then the state is "stalled" with missed_beats=3                       # fails: 299 s renders stalled; 301 renders live
```

**US-3 — Empty corpus is NOT CHECKED.**
```gherkin
Given .agents/log/ has no session-start at all (0 files, or files with no session)
When coord track runs
Then it prints "COORD-TRACK-NOT-CHECKED" and exits 4                   # fails: "0 tracks, all quiet", exit 0
```

**US-4 — Blocked and done.**
```gherkin
Given a session whose ledger holds a mail twin kind=blocked newer than any kind=unblocked twin
Then coord track renders state "blocked" and blocked_on = the twin's `to`
Given a session-end (or a mail twin kind=done) for the session
Then the state is "done" regardless of heartbeats                     # fails: a done session renders stalled after 300 s
```

**US-5 — Worktree-mtime fallback.**
```gherkin
Given a session with a session-start whose worktree label resolves to a registered worktree, and no heartbeat
When a tracked file in that worktree was modified 30 s ago
Then the state is "live", source "worktree-mtime"                     # fails: stalled although files change
When nothing under the worktree changed for 300 s
Then the state is "stalled", source "worktree-mtime"
Given the label resolves to no worktree
Then the state is "stalled", source "none"  (unproven liveness is never live)
```

**US-6 — The kick ladder.**
```gherkin
Given a stalled track (s2, WI-7) and AGENT_SESSION=coord
When coord kick s2 --wi WI-7 runs twice
Then two mail rows kind=kick reach s2's inbox, each with a ledger twin, and two kick-ladder events (rung 1) are recorded
When coord kick s2 --wi WI-7 runs a third time
Then it is refused with COORD-KICK-CAP, exit 3, nothing is sent, the refusal is recorded    # fails: a third kick lands
When coord kick s2 --wi WI-7 --rung 2 --fallback "<text>" runs with a live leader `coord`
Then a request-add row exists in .agents/requests.jsonl with reason=kick-ladder, to=coord, ref=<last kick mail id>, a deadline and the fallback
  And a mail kind=decision-request reaches coord's inbox
When --rung 2 runs without --fallback
Then COORD-KICK-INCOMPLETE, exit 2, nothing written                  # fails: a request without a termination variant
When the track is live and no --deadline-at is given
Then coord kick is refused with COORD-KICK-NOT-DUE                    # fails: a kick on a live track
Given a blocked track with no prior notify
When coord kick runs with no --rung
Then rung 0: a mail kind=note (inbox only, no twin) and a kick-ladder event rung 0
```

**US-7 — Metrics and doctor.**
```gherkin
Given the fixtures above
When coord metrics runs
Then it reports heartbeats, zero-delta beats, live/stalled/blocked now, kicks, cap refusals, escalations,
     stall-detection latency (median stall_age_s over rung-1 kicks) and false kicks (a rung-1 kick followed by a progress beat from the target within 300 s)
Given no heartbeat in the corpus
Then every liveness counter renders "no heartbeat recorded", never 0            # fails: "0 stalls" over an empty corpus
When pack-doctor runs in a repo with no heartbeat rows
Then a "heartbeat" check prints "not recorded (no heartbeat in .agents/log; wire heartbeat.py)"
When heartbeat rows exist
Then it prints the beating session count, the newest beat's age and the stalled count
```

**US-8 (F-1) — The leader's heartbeat renews the designation.**
```gherkin
Given refs/coord/leader is held by s1 (live) and AGENT_SESSION=s1
When a sampled heartbeat is written for s1
Then the record's expires_at advances by its ttl and the heartbeat row carries leader_renewed=true    # fails: the designation lapses under a working coordinator
Given the designation has expired
Then the heartbeat does NOT reclaim (the epoch is untouched) and carries leader_renewed="expired"     # fails: a silent epoch advance
Given s1 is not the holder
Then leader_renewed is null and the ref is untouched
```

**US-9 (F-3) — No absolute path in the ledger.**
```gherkin
Given a linked worktree at <tmp>/wt-a
When coord session start runs there
Then the session-start row's worktree field equals "wt-a"                       # fails: the row carries <tmp>/wt-a
  And coord session start from a second session in the same tree is refused COORD-WORKTREE-OCCUPIED (occupancy still keys by label)
Given a ledger file whose rows carry absolute worktree paths
When coord log portable <file> runs
Then only the worktree values change (to their basename), other lines are byte-identical, and a second run changes nothing
  And verify-no-machine-paths.py accepts the file                                  # fails: any other field rewritten; a second run rewrites again
```

### A.7 ISO 25010 NFRs

| Attribute | Requirement | Verified by |
|---|---|---|
| Reliability | the hook exits 0 and prints nothing on every path (a hook failure never denies a tool call) | tests: malformed stdin, unset session, missing repo |
| Performance | one hook run ≤ 100 ms on the sampling path (no git subprocess between samples; one `update-ref` per sampled leader beat) | measured in the Proof Pack |
| Portability | no absolute path in any ledger row; Windows-safe writes via the existing `append_event` (O_BINARY, one write) | gate 1b; the portable-text-io gate |
| Maintainability | constants in one block (`HEARTBEAT_SAMPLE`, `STALL_AFTER`, `KICK_CAP`); the fold is a pure function | tests call the fold directly |
| Security | the hook reads stdin as data only; file paths from `tool_input` are relativised and only counted, never executed | STRIDE table in the design |

### A.8 Contract deviations raised (never silent)

1. **F-3 field name.** The plan says `tree`; the path is in `worktree`. Fixed where the path is; `tree` is untouched. Recorded in `note-20260919-liveness-worktree-field-is-a-label`.
2. **Deadline column.** No landed store carries a work-item deadline; rendered `not recorded`; `coord kick --deadline-at` carries the coordinator's plan-row deadline into the record. Reopen when `coord delegate` lands.
3. **Claude Code heartbeat channel status.** A live `PostToolUse` event could not be captured from inside this sub-agent's own session (settings hooks are loaded at session start). The hook is executed here against the documented payload contract (README, RIG-D); the channel is reported **observed-only** until a live session shows it fire (CO12).

---

## Part B — UX specification (CLI terms)

Surfaces: `coord session heartbeat`, `coord track [--json]`, `coord kick <session> [...]`, `coord log portable <file>...`, `coord metrics`, `pack-doctor`. Every refusal is `CODE  subject` + `because` + `remedy` (the existing render). `coord track` prints one row per (session, wi): `state  session  wi  source  last-progress  missed  kicks  blocked-on  deadline`, then the legend line. `--json` returns the fold. Empty → `COORD-TRACK-NOT-CHECKED`, exit 4. Error and recovery paths are the refusals in A.6 and the NOT CHECKED renders. No visual UI.

## Part C — UI specification

N/A — command-line output only; no visual UI.

## Evidence and comparables

| Claim | Confidence | Source |
|---|---|---|
| Heartbeats must carry progress; phi-accrual is over-engineered below ~9 nodes | Verified (KB) | proposal §1.3 items 6–7, D7; Temporal heartbeat classes; Akka cutoff |
| Claude Code `PostToolUse`/`Stop` payloads: `session_id`, `cwd`, `hook_event_name`, `tool_name`, `tool_input`, (`tool_response`), `stop_hook_active` | Verified (docs; `PreToolUse` executed here in spike S5) | hooks README; KB hook-surface table [P2P-26] |
| Antigravity `PostToolUse`/`Stop`, Copilot `preToolUse`/`agentStop`, Grok Claude-format `PreToolUse` | Inferred (docs-only) → **observed-only** | KB [AC-40..42]; CO12 |
| D13 constants 300 / 100 / 20 / 30 s | Verified | `coord-core.py:53-56` |
| The absolute path is in `worktree` (26 records), never `tree` | Verified | grep over the primary's `.agents/log/*.jsonl`, 2026-09-19 |

## Gate record (Stage 4, adversaries enacted inline — fan-out 0)

| Adversary | Attack | Disposition |
|---|---|---|
| Test Architect (hard) | "301 s renders stalled, 299 live — is the boundary in a test?" | US-2 third clause; the fold takes `now` as an argument |
| Test Architect | "US-1 sampling: what input fails it?" | two payloads 5 s apart must yield one row; 100 s apart two rows |
| Simplifier (soft) | "Deadline store, delegate verb, transcript token parsing — YAGNI" | struck (A.5); `--deadline-at` is one optional flag |
| Simplifier | "Rung auto-selection is logic nobody asked for" | kept minimal: rung = 0 if blocked-and-unnotified, 1 while under cap, 2 at cap; `--rung` overrides; every branch has a test |
| SRE | "Stall-detection latency and false-kick rate must be measurable from the records" | `stall_age_s`, `missed_beats` on every kick-ladder event; metrics derive latency median and false kicks; R4 renders absence |
| SRE | "A hook that shells out per tool call is a hot path" | scratch accumulator between samples; git touched only on a sampled leader beat |
| Security | "A hook payload names a path; is it trusted?" | counted after `_relativise`, never opened or executed; the record stores counts, not paths |

Verdict: **PASS-WITH-CONDITIONS** — conditions are the tests named in A.6, all red-first. The author did not clear the Test Architect's veto; it is cleared by the tests running red then green in `/implement`.

## Confidence ledger and residual risk

- Verified: D13 constants, ledger writer contract, mail kinds and twin shape, request store, the F-3 field.
- Inferred: non-Claude hook payload keys (aliases accepted; `observed-only`).
- Residual risk: a session on a host with no hook and no resolvable worktree renders `stalled` with source `none` — honest, but the coordinator must read the source column; basename labels collide across parent directories on one machine (cleanup errs to HELD).
