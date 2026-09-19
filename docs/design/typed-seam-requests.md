---
id: design-typed-seam-requests
title: "Design — typed seam requests (the Request aggregate's rows · stale-by-blob · expire · doctor/metrics · claim --except · coord_ids monotonic stamp)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, seam-request, deadline, fallback, ack, blob, termination, cli, p1]
links:
  - { to: spec-typed-seam-requests, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: adr-0007-coordination-substrate, rel: depends-on }
  - { to: design-message-layer, rel: relates-to }
  - { to: design-coord-enforcement-phase2, rel: relates-to }
  - { to: kb-multi-agent-coordination-data, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Detailed design for spec-typed-seam-requests: five request-* row kinds folded into one Request
  state per id in .agents/requests.jsonl, a twin `type: request` row per transition in the session
  ledger, staleness derived at read time from git's blob formula over the cited path, `expire` as the
  termination variant that records the fallback, doctor FAIL/WARN lines, three metrics that read
  "not recorded" over nothing, `claim --except` carried on the claim event and honoured by
  `overlaps`, and a process-monotonic millisecond stamp inside coord_ids.new_id (ID-A).
---

# Design: typed seam requests

- **Status:** Draft
- **Spec / architecture:** `docs/specs/typed-seam-requests.md` (US-1…US-10, the Request aggregate and its invariant) · ADR-0007 (append-only JSONL, no daemon, stdlib only) · proposal §3.3/7, §4, P1, D5, D13.
- **Author(s) / date:** Python Developer (lead) + Patterns Expert + Simplifier + Data & Persistence Architect (peers), 2026-09-19. Adversaries at the gate: Patterns Expert ⇄ Simplifier, Test Architect (hard veto), Security (hard veto), Distributed Systems (advisory — one writer per row, no cross-process ordering claimed), SRE. **Fan-out 0 — enacted inline; the Coordinator re-reads the gate record at the join.**

> **Grounding trace (V15):** `design-typed-seam-requests` → `implements` → `spec-typed-seam-requests` → `refines` → the proposal → `depends-on` → `adr-0007-coordination-substrate`; → `relates-to` → `design-message-layer` (`coord-mail.py` `_next_ms`, the `--ref` shape, `append_record` reuse) and `design-coord-enforcement-phase2` (`cmd_doctor`, `cmd_metrics` shapes). Quoted from the spec and satisfied here: *"every typed request reaches a terminal state by its deadline — by a resolution, or by its own recorded fallback — never by silence"*; *"store `deadline_at` only"*; *"stale … `not recorded`, never `false`"*; *"`not recorded` over an empty store, never 0"*. **Spike (executed):** git's blob hash is `sha1(b"blob <len>\0" + bytes)` — `git hash-object` and the Python formula both returned `7d056635d5490241ee2e910806cbd0772f978302` for the same file (2026-09-19). Verified.

## 1. Responsibility
Give a seam request a termination variant and make its lifecycle a fold over appended rows: refuse an incomplete request; pin an ack to a blob; expire past the deadline into the recorded fallback; render silence as a doctor FAIL; count outcomes. Plus the CTX-R lease control. Nothing else — no watcher, no store, no mail.

## 2. Data model (settled first — DM1–DM18)

### 2.1 Aggregate
**Request** (root: `id`, `req-<26 Crockford>`). Invariant: terminal by `deadline_at`, by resolution or by its own fallback. Enforced by (a) `add` refusing a request without both, (b) `expire` being the only path to `expired` and always copying the fallback, (c) `doctor` failing a past-deadline non-terminal typed request.

### 2.2 Durable representation — the store `.agents/requests.jsonl` (exists; ADR-0007)
**Grain: one row is exactly one transition of one request.** Append-only; never updated. Row kinds and fields (all rows: `kind`, `id`, `at`, `session`, `agent`):

| kind | added fields | writer | compute reader |
|---|---|---|---|
| `request-add` | `from`, `to`, `text`, `path` (optional), `deadline_at`, `fallback`, `blob` (opt), `ref` (opt); legacy fields `contract`, `reason` kept when passed | `cmd_request add` | `fold_requests` |
| `request-receive` | — | `receive` | fold |
| `request-ack` | `blob` (required) | `ack` | fold; staleness |
| `request-resolve` | `resolution` | `resolve` (unchanged shape) | fold |
| `request-expire` | `outcome: "fallback"`, `fallback` (copied) | `expire` | fold; metrics |

- **Additivity:** counts over rows are additive; `deadline_at` is a point-in-time attribute (non-additive).
- **History rule:** Type-2 by construction — every change is a new row; `fold_requests` is the projection. No row is ever rewritten.
- **Derive, don't store:** `status` (fold), `overdue` (`now ≥ deadline_at` and non-terminal), `stale` (ack blob ≠ current blob of `path`) and `outcome` are computed by the reader. `deadline_at` is the only stored deadline quantity (the seconds are the input). The fallback text appears twice — on `add` (the promise) and on `expire` (the outcome) — deliberately: the expire row is the *record of what was taken* and must stand alone in `tail`/ledger reads (an accepted duplication, not two definitions: the expire copy is the outcome fact).
- **Fold (`fold_requests`)**: `add` → `sent`; `receive` → `received`; `ack` → `acked` (+`ack_blob`, `acked_at`, `acked_by`); `resolve` → `resolved`; `expire` → `expired` (+`outcome`, `fallback`, `expired_at`). Rows for an unknown id are ignored (as today). A row of a later kind after a terminal state is ignored (terminal wins; the CLI refuses to write it anyway). **Untyped:** an `add` with no `deadline_at` → status `untyped` unless resolved.
- **Ledger twin:** each transition also appends to `log/<session>.jsonl` via `append_event`: `{"kind": "request", "type": "request", "action": add|receive|ack|resolve|expire, "id", "to", "deadline_at", "outcome"?, "wi": "WI-0", "path": "-", "at"}`. `fold` (leases) ignores it; `tail` prints it; the store is the state, the ledger is the audit trail — as for leader and mail. Written *after* the store row; a failed twin is printed as `COORD-NOT-CHECKED-RECORD` on stderr and does not change the verdict (G14, as `append_decision`).
- **Migration:** expand only — new optional fields, new kinds; old readers ignore them; no backfill (an untyped row is labelled, not guessed).

### 2.3 Staleness (derived at read time)
`current_blob(repo, path)` = `sha1(b"blob %d\0" % len + bytes)` over the file at `repo_root/path` (spiked). `stale` = `True` when `ack_blob != current_blob`; `False` when equal; `"not recorded"` when the request has no `path`, the file is unreadable, or the reader has no repo root. No subprocess on the list path.

### 2.4 The claim event gains `except`
`make_event("claim", …, excepts=[…])` stores `"except": [norm paths]` on the event; `fold` carries it on the lease; `lease_covers(lease, path)` = `overlaps(lease.path, path) and not any(overlaps(e, path) for e in lease.except)`. `check` uses `lease_covers` instead of bare `overlaps`. Doctor's overlap WARN: for every pair of live leases from different sessions where `lease_covers(a, b.path) or lease_covers(b, a.path)`.

### 2.5 Identity (ID-A)
`coord_ids.new_id(scheme, ts_ms=None)`: when `ts_ms` is None the stamp is `_next_ms(time.time())` — process-monotonic, strictly increasing (the `_next_ms` shape from `coord-mail.py`, moved to the one id module; mail keeps passing its own explicit stamp, which is honoured as given). Sweep result: `req-` (coord-core), `allocate --scheme` (coord-core), register-merge placeholder ids (coord-core `merge_register`), `mail-` (explicit stamp), `al-`/`cl-` (`audit-log.py` via `_load_allocator` → `new_id`; **the sequential `al-NNNN` fallback under `COORD_LEGACY_IDS` or a failed import is outside the guarantee — reported, read-only**). Session and worktree ids are *not minted* by the pack (supplied by `AGENT_SESSION`/`--session`) — nothing to sweep.

## 3. Change-surface list (E7)
store (`requests.jsonl` rows; `log/*.jsonl` twins; claim `except`) → model (`fold_requests`, `fold`, `lease_covers`, `current_blob`, `coord_ids._next_ms`) → service (`cmd_request` verbs; `claim --except`; `check`) → projection (`list` text + `--json`; doctor lines in `cmd_doctor` and `pack-doctor.check_requests`; `cmd_metrics` fields + lines) → client (CLI flags; `--help`) → UI: none → compute readers (`doctor`, `metrics`, tests). Constants: `REQUEST_DEADLINE = 900`, `REQUEST_RETRY = 20` in one block beside the leader's.

## 4. Contracts
**Exposed (CLI):**
- `request add --to S --deadline SECS|default --fallback TEXT [--blob SHA] [--ref ID] [--path P] [--from-role R] [--contract C] [--reason R] [TEXT]` → 0 JSON `{id, status: sent, deadline_at}`; 2 `COORD-REQUEST-INCOMPLETE <missing>`; 4 store unreadable. `TEXT` or `--contract` required (2 `COORD-REQUEST-INCOMPLETE text`).
- `request receive ID` → 0; 4 not found; 3 `COORD-REQUEST-TERMINAL`.
- `request ack ID --blob SHA` → 0 JSON `{id, status: acked, blob}`; 2 `COORD-REQUEST-ACK-NO-BLOB`; 3 terminal; 4 not found.
- `request resolve ID --resolution TEXT` → unchanged (0/4), plus 3 when already terminal.
- `request expire [ID]` → 0 with the list (`N expired` then one line per id: id, fallback); `ID` not due → 3 `COORD-REQUEST-NOT-DUE`; terminal → 3; untyped → 3 `COORD-REQUEST-UNTYPED`.
- `request list [--status sent|received|acked|resolved|expired|untyped|open|all] [--json]` — `open` = sent+received+acked+untyped (default, as today).
- `claim --path P --wi W [--except P …]` — `--except` repeatable.
- `doctor`: line `requests  <verdict>` — FAIL `COORD-REQUEST-SILENT-EXPIRY` naming ids; WARN `COORD-REQUEST-UNTYPED n` and WARN `COORD-REQUEST-STALE-ACK` naming ids; `not recorded` when no store. Line `lease overlap  WARN` per overlapping pair; `ok` otherwise; NOT CHECKED when the ledger is unreadable.
- `metrics`: `requests_unresolved_by_deadline`, `requests_fallback_taken`, `requests_stale_acks` (ints or `"not recorded"`), `requests_reason`.
- `pack-doctor.py`: `check_requests(root)` → `requests` PASS/WARN/FAIL with the same rules.

**Consumed:** `append_record`, `append_event`, `read_request_events`, `overlaps`, `_safe`, `repo_root` (this file); `hashlib.sha1` (stdlib); `coord_ids.new_id`. `--ref` is recorded as given (P1→P4 seam: none; read-only against the mail store means *not dereferenced* here — the board joins them).

## 5. Patterns (named, ladder-climbed)
- **Event-sourced aggregate / fold** (existing idiom: leases, leader) — reuse-in-codebase rung.
- **Content-addressed pin** (git blob sha) for the ack — stdlib `hashlib`, no subprocess.
- **Termination variant as an explicit verb** (`expire`), not a daemon (D9; Simplifier).
- **Null object for the empty corpus** — `"not recorded"` (R4/PACK-P idiom).
- Rejected: a `pending-expiry` scheduler; a second index file; storing `stale` (derive-don't-store).

## 6. Error and concurrency model
Exit codes follow `EXIT`: 0 ok · 2 incomplete input (a named reason, never argparse's) · 3 refused by state · 4 NOT CHECKED (unreadable store / not found). Rows are one `write()` under `O_APPEND` (existing `append_record`); two sessions expiring the same request concurrently produce two `request-expire` rows — the fold takes the first, the second is harmless (idempotent outcome). No cross-process ordering is claimed for ids (R2).

## 7. Failure-mode analysis (mode → disposition)
| Mode | Category | Disposition | Test |
|---|---|---|---|
| request added without deadline/fallback | input | prevent (exit 2) | T1 |
| ack without blob | input | prevent (exit 2) | T3 |
| deadline passes, nobody runs expire | time | detect (doctor FAIL, metrics count) | T5 |
| acked blob changes under the ack | state | detect (stale on list/doctor) | T3 |
| path missing/unreadable for staleness | dependency | degrade to `not recorded` | T3b |
| store unreadable / damaged row | dependency | NOT CHECKED exit 4 (existing) | existing |
| ledger twin write fails | resource | verdict stands; stderr NOT-CHECKED-RECORD | T2 (twin present) |
| untyped legacy rows | state | label `untyped`; WARN; never expire | T5b, T10 |
| empty corpus | state | `not recorded`, never zero | T6 |
| two live overlapping leases | concurrency | detect (doctor WARN) | T8 |
| directory lease blocks a peer's file | concurrency | prevent (`--except`) | T7 |
| burst minting in one tick | time | prevent (monotonic stamp) | T9 |

## 8. Adversarial analysis (STRIDE-lite)
Boundary: the CLI's stdout/stderr rendered into another model's context; the store on disk.
| Threat | Disposition |
|---|---|
| Tampering — a crafted `text`/`fallback` with newlines reads as an instruction | mitigate: every rendered value passes `_safe` (existing control) — negative test T11 |
| Tampering — `--path ../../x` reads outside the repo for staleness | mitigate: the path is normalised and must stay under `repo_root`; else `not recorded` — T3b |
| Spoofing — any session may ack/resolve/expire another's request | accept-with-rationale: the substrate is an integrity control, not a security one (NFR-S2, ADR-0007); the ledger records who |
| Denial — `--blob`/`--ref` unbounded | mitigate: `_safe` caps at 200 chars on render; stored as given |
| Repudiation | mitigate: ledger twin per transition |

## 9. Privacy analysis (LINDDUN-lite)
No personal data: session ids, agent labels and request text authored by agents. Explicit no-personal-data line.

## 10. Telemetry (O1–O13)
Stable codes: `COORD-REQUEST-INCOMPLETE`, `-ACK-NO-BLOB`, `-NOT-DUE`, `-TERMINAL`, `-UNTYPED`, `-NOT-FOUND`, `-SILENT-EXPIRY`, `-STALE-ACK`, `-NOT-CHECKED`, `COORD-LEASE-OVERLAP`. Measures: the three metrics; each ledger twin carries `at`, `id`, `action`, `deadline_at` so time-to-ack and time-to-resolve are derivable from the ledger without a new field. No spans: a stdlib CLI; duration is the harness's.

## 11. Test plan (Testing Strategy; red first)
`tests/docs_explorer/test_coord_requests_typed.py` (CLI via subprocess in a temp repo, `encoding="utf-8"`):
T1 add refused without deadline / without fallback / without text (exit 2, code on stderr, no row) · T2 add records `deadline_at`, `fallback`, status `sent`, ledger twin `type: request` · T3 ack pins blob; changed file → stale true; ack without blob exit 2 · T3b no path → `not recorded` · T4 expire (no id) records outcome fallback and lists; `expire ID` not due → 3 · T5 doctor FAIL on silent expiry (exit 1) · T5b doctor WARN counts untyped; exit 0 · T6 metrics counts; `not recorded` on empty · T7 claim --except: peer check allowed inside the exception, refused outside · T8 doctor WARN on overlapping live leases · T10 untyped rows list `untyped`, never expire · T11 a fallback with a newline is rendered on one line · pack-doctor `check_requests` FAIL/WARN/PASS. `tests/docs_explorer/test_coord_ids_order.py`: T9 1,000 per prefix strictly ordered + unique; explicit `ts_ms` honoured. Existing suites stay green except the one conflict already filed (`req-01M2XGPYW5ZNC39094ZCM0WHRW`).

## 12. Conformance and deviations
Python: stdlib only, `encoding="utf-8"` everywhere, `newline="\n"` on text writes, no machine paths, no bare except (the existing `append_decision` swallow is not extended). `simplify:` markers: `REQUEST_RETRY` named-but-unconsumed (ceiling: P3's kick ladder); staleness compares whole-file blob, not a hunk (ceiling: a rename; trigger: the first false stale a human calls wrong).

## Gate record
| Adversary | Attack | Outcome |
|---|---|---|
| Simplifier ⇄ Patterns Expert | "`receive` adds a verb nobody needs" / "the fold pattern wants the full state set" | kept: one row kind, one fold branch, optional in the flow |
| Test Architect (hard) | "T3 passes if `stale` is always true" | T3 asserts `false` before the change and `true` after; T3b asserts the string `not recorded` |
| Test Architect | "T6 passes with zeros" | asserts `== "not recorded"` on empty and `== 1` after one expire |
| Security (hard) | "`--path` staleness read escapes the repo" | mitigated (§8), negative test T3b variant with `../` |
| Data & Persistence | "the fallback stored twice" | accepted with rationale (§2.2): the expire row is the outcome fact |
| SRE | "how is time-to-ack measured?" | from the ledger twins' `at` per action; no new field |
| Distributed Systems | "concurrent expire" | idempotent by fold-first-wins; §6 |

**Verdict:** PASS — hard vetoes have no open finding; the author-never-clears rule is discharged by the Coordinator at the join (fan-out 0 stated).

## Status
| | |
|---|---|
| **Completed** | data model; change-surface list; contracts; spike (blob hash); failure/STRIDE/LINDDUN; test plan; gate |
| **Remaining** | `/implement` red-first; `docs/security/*` `documents` links (reported to the Coordinator — not edited by this track) |
| **Best next action** | write `test_coord_requests_typed.py` and observe it red |
