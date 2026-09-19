---
id: design-owner-review
title: "Design — owner review (coord-decide.py · docs/notes/rulings.md · verify-ruling-citations.py · owner-review-gate.py)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, owner-review, decision-request, ruling, register, gate, hook, p5, d6, id-a]
links:
  - { to: spec-owner-review, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: design-typed-seam-requests, rel: depends-on }
  - { to: design-message-layer, rel: depends-on }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Detailed design for spec-owner-review. One stdlib CLI (coord-decide.py) that writes a decision
  request only by running coord-core.py's own `request add` and `request resolve`, sends its two
  mails only through coord-mail.py's append_mail imported by path, and owns exactly one file: the
  ruling register docs/notes/rulings.md whose headings are the allocator. One gate
  (verify-ruling-citations.py) re-homed from ai-de with a self-test. One fail-safe Stop hook
  (owner-review-gate.py) that reads the P1 store through the P1 reader and blocks only on an open
  decision request the stopping session itself sent. No new store, no new dependency, no config.
---

# Design: owner review

- **Status:** Draft
- **Spec / architecture:** `docs/specs/owner-review.md` (US-1…US-10, NFRs, boundary set) · proposal §3.1, §4, §7 P5, D6 · the fixed contracts in `docs/coordination/coordination-p3-p5-p8.md`.
- **Delivery phase / vertical slice:** coordination **P5**, built in parallel with P3 (heartbeats/kick) and XP. Real around it now: `coord-core.py request …` (P1, `cmd_request` at `:2418`), `coord-mail.py append_mail` (P4, `:288`, kinds `decision-request`/`ruling` already in `KINDS`), `coord-board.py` (the by-path import idiom), the hooks README idiom. **Absent until the join:** the `coord decide` front door in `coord-core.py` (the script is invoked by path until then — same as `coord-board.py` was), the hook JSON entries (seam P5 → P3), the `.agents/artifacts.yml` register line (coordinator).

## Responsibility
Give the Owner seat a deterministic review mechanism: a typed decision request out of a Sub-Agent, a numbered ruling back, the register that makes the number readable, the gate that keeps the register honest, and the stop hook that keeps a Sub-Agent from ending with its own question open. Nothing else: no store, no allocator, no UI.

## Spec clarification (recorded, not drift)
- `--contract` is a **JSON object** (`{"options","evidence","recommendation","reversibility","blast_radius"}`) serialised with `sort_keys`. Chosen over a structured text block because P1's fold already surfaces `contract` verbatim in `request list --json`, and a reader (board, metrics, a future explorer view) parses a JSON object without a grammar. Recorded in the note.
- The ruling heading level is `###` (the contract's primary form); the gate accepts `##` too (the contract's parenthetical) and nothing else.
- The hook resolves the session to `$AGENT_SESSION` only. The harness `session_id` on stdin is *not* the identity requests are written under (they carry `AGENT_SESSION`), so it cannot be used to find them; with no `AGENT_SESSION` the path is unevaluable → exit 0.

## Data model (settled first — DM1–DM6)
- **Aggregates:** none new. **Seam request** (P1): the decision request is a `request-add` row with `reason: "decision-request"`, `contract: <JSON object string>`, `text: <the question>`, `to: <owner session>`, `deadline_at`, `fallback`, optional `ref` (a kick mail id). Invariant unchanged (terminal by deadline or resolution). **Mail** (P4): `decision-request` and `ruling` rows, `ref` = request id. **Register** (new file, not a new aggregate class — `register` merge class in `artifacts.yml`, union-merged like `audit-log.jsonl`): root = `docs/notes/rulings.md`; invariant = *one heading per number, numbers monotonic*; enforced at write by `rule` (refuses defined / not-next) and at read by the gate (fails twice-defined).
- **Grain:** one request row = one transition (P1); one mail row = one message (P4); one `### Ruling n — title` block = one ruling.
- **Additivity:** counts additive (`open decision requests`, `rulings`); the number is an identity, non-additive.
- **History rule:** the register is append-only (Type-2 by construction: a ruling is never edited; a later ruling supersedes it in prose). The request's resolution text `Ruling n` is the one stored link from request to ruling; the ruling block carries the request id in its provenance line — accepted duplication of an *identifier* (not a quantity), so the register reads whole offline.
- **Derive, don't store:** `next number` = max(defined) + 1, computed from headings at every `rule`. `open` = folded status ∈ `REQUEST_OPEN`, never written. Citations are recomputed by the gate.
- **Writers and compute readers:** `reason`/`contract` — written by `coord-core.py request add` (invoked by `coord-decide.py`), read by `coord-decide.py list`, `owner-review-gate.py`, P1's `request list --json`. Heading — written by `coord-decide.py rule`, read by `rule` (allocator), `list`, `verify-ruling-citations.py`.

## Contracts

### Exposed
```
coord-decide.py request --to <owner-session> --options T --evidence T --recommendation T
                        --reversibility T --blast-radius T --deadline <seconds|default>
                        --fallback T [--ref <mail-id>] "<question>"
        stdout: {"id","status":"sent","deadline_at","mail":"<mail-id>"|"not sent: <code>"}
        exit 0 · 2 COORD-DECIDE-INCOMPLETE / COORD-DECIDE-BODY-SIZE / COORD-DECIDE-TO (refused, nothing written)
             · the child's code when `coord-core.py request add` refuses (its stderr passes through)
coord-decide.py rule <n|next> --title T --text T --request <req-id>
        stdout: {"ruling": n, "title", "request", "resolution":"Ruling n", "mail": …}
        exit 0 · 2 COORD-RULING-DEFINED / COORD-RULING-NOT-NEXT / COORD-RULING-SELF / COORD-RULING-REGISTER (outside repo)
             · 3 request terminal · 4 request not found / store unreadable (NOT CHECKED)
coord-decide.py list [--json]
        stdout: open decision requests (id, from → to, deadline text, question) and rulings (n, title, request);
                a missing store or register renders NOT CHECKED — <path>; exit 0 (a read)
verify-ruling-citations.py [--root <repo>] [--self-test]     exit 0 ok · 1 refused · 2 usage
owner-review-gate.py --host claude|grok|copilot|agy [--event E] [--session S]
        claude/grok: exit 2 + one stderr line on an open decision request the session sent; else exit 0, silent
        copilot agentStop: exit 0 + {"decision":"block","reason":…} on stdout; else exit 0, silent
        agy: exit 0 always (no stop event — unsupported)
```
Common options: `--root <.agents dir>` (tests), `--register <path>` (must resolve inside the repository), `--scripts <dir>` (where `coord-core.py`/`coord-mail.py` live; default: the sibling directory).

### Consumed (each with source and confidence)
| Contract | Source | Confidence |
|---|---|---|
| `coord-core.py request add <text> --to --deadline --fallback --contract --reason --ref` → stdout `{"id","status":"sent","deadline_at"}`, exit 2 `COORD-REQUEST-INCOMPLETE` | `pack/scripts/coord-core.py:1119-1136, 2418-2455` read | Verified |
| `coord-core.py request resolve <id> --resolution` → exit 0 / 3 terminal / 4 not found; identity gate needs `AGENT_SESSION` | `coord-core.py:2506-2540, 3742-3746` | Verified |
| `read_request_events(root)`, `fold_requests(events)`, `REQUEST_OPEN`, `resolve_root(cwd, raw)`, `repo_root(cwd)`, `append_record` | `coord-core.py:454-533, 62-67, 121-135, 78, 433` | Verified |
| `append_mail(root, session, entry) -> id`; `MailError(code, reason, exit)`; `BODY_MAX_BYTES = 4096`; kinds `decision-request`, `ruling` | `coord-mail.py:66-70, 288-323` | Verified |
| by-path import of a sibling script (`importlib.util.spec_from_file_location`) | `coord-board.py:282-329`, `coord-mail.py:51-58` | Verified |
| Claude Code `Stop` hook: stdin JSON with `session_id`, `stop_hook_active`; exit 2 blocks and stderr is fed back as the reason | hooks README (RIG-D contracts) + doorbell's `stop_hook_active` handling | Inferred — `observed-only` until a live stop fires |
| Copilot `agentStop`: `{"decision":"block","reason"}`, guard on `stop_hook_active` | `mail-doorbell.py payload_for` | Verified (same shape reused) |
| interpreter-resolution command form for the hook JSON | `pack/adapters/hooks/README.md` "Interpreter" + the four JSONs | Verified |

## Patterns (named, justified, ladder-climbed)
- **Front door + delegate by subprocess** (as `coord-core.py` → `coord-mail.py`): `coord-decide.py` runs `coord-core.py request add|resolve` as a child with the caller's environment, parses its one JSON line. Ladder: reuse-in-codebase over importing `cmd_request` with a hand-built `Namespace` (which would couple to nine attribute names and would need stdout capture). Cost: one interpreter start per write (~25 ms) — accepted.
- **Import-by-path for the mail writer** (as `coord-board.py`): `append_mail` is the single writer; the same idiom loads `coord-core.py` for the *readers* (`fold_requests`) and `resolve_root`.
- **Register as allocator** (ID-A): the heading regex over the file is the only source of the next number.
- **Fail-open hook at the tool seam** (as `mail-doorbell.py`, `session-start.py`): one `try` around everything, `return 0` on any exception.
- **Self-testing gate** (DC-104, as `verify-skill-contracts.py`): `--self-test` breaks a synthetic tree in each direction.
- Simplifier pass: no `--text-file`, no `--kind` on the ruling mail, no rulings view, no frozen list (nothing predates the control), no `HARNESS_STATUS` write (P3's file; README row instead). `simplify:` markers inline where a ceiling exists.

## Data shapes
```
request-add row (P1, unchanged keys + two P1 optionals used):
  {"kind":"request-add","id":"req-…","at":<float>,"session":"p5","agent":"p5","from":"p5","to":"coord",
   "text":"<question>","path":"","deadline_at":<float>,"fallback":"…","reason":"decision-request",
   "contract":"{\"blast_radius\":…,\"evidence\":…,\"options\":…,\"recommendation\":…,\"reversibility\":…}"}
decision-request mail body (≤ 4096 bytes, refused before any write otherwise):
  "<question>\noptions: …\nevidence: …\nrecommendation: …\nreversibility: …\nblast radius: …\nrequest: req-…"
register block:
  "### Ruling n — <title>\n\n<text>\n\n- request: req-… · ruled by: <session> · at: 2026-09-19T20:50:00Z\n"
ruling mail body: "Ruling n — <title>\n<text>"   (ref = req-…)
```

## Error & concurrency model
- Refusals exit 2 before any write; store/identity errors from the child pass through with the child's code. A mail failure after a successful write is reported in the JSON and does not change the exit (doorbell rule; a non-zero here would invite a retry that duplicates the request).
- `rule` order: read register → compute next/refuse → fold requests → refuse (not found 4 / terminal 3 / self 2) → **append heading** → `request resolve` (child) → `ruling` mail. Failure after the heading is appended leaves a definition with no citation (allowed by the gate) and the request open (visible in `list`); the remedy is printed. The reverse order would leave `resolution: "Ruling n"` pointing at no heading — the exact defect the gate exists for — so the heading goes first.
- Concurrency: two Owners ruling at once could both compute `next = 3`; the second append is caught by the gate (twice-defined) and by the register's union merge showing both. Accepted: one Owner seat per run is the doctrine (CO1); the gate is the belt.

## Change-surface list (E7)
store (`.agents/requests.jsonl` via P1; `.agents/mail/<to>.jsonl` via P4; `docs/notes/rulings.md`) → model (P1 row + `reason`/`contract`; register heading) → service (`coord-decide.py`) → projection/wire (`list` text + `--json`; the ruling/decision-request mail; the gate's stderr line / Copilot JSON) → client (`coord decide` front door — seam; the hook JSON — seam) → UI (terminal only) → compute readers (`list`, `owner-review-gate.py`, `verify-ruling-citations.py`; P1's `request list`; P6's board shows the mails).

## Failure-mode analysis
| Mode | Category | Disposition | Test |
|---|---|---|---|
| five fields / deadline / fallback / to / question missing | input | prevent — refuse exit 2, nothing written | Request::test_refused… |
| body over 4 KiB | input | prevent — refuse before the request row is written (the size is computed first) | Request::test_body_over_4k_refused_before_write |
| `coord-core.py` not beside the script | dependency | detect — `COORD-DECIDE-NOT-INSTALLED` exit 4 | Request::test_missing_core_is_not_checked |
| store unreadable (malformed line) | state | detect — P1 returns `COORD-REQUEST-NOT-CHECKED` 4; the gate exits 0 | Gate::test_fail_safe_paths_exit_0 |
| register number collision / gap | state | prevent at write (refuse) + detect at read (gate) | Rule::test_defined_number_refused, Gate self-test |
| register outside the repo (`--register ../x`) | security | prevent — refuse `COORD-RULING-REGISTER` | Rule::test_register_outside_repo_refused |
| mail inbox full / identity invalid after the row is written | dependency | mitigate — report `not sent: <code>` in the JSON, exit 0 | Request::test_mail_failure_reported_not_fatal |
| hook: no session / no JSON / no store / stop_hook_active / outside root | time/state | accept-by-design — exit 0 silent (fail-safe) | Gate::test_fail_safe_paths_exit_0 |
| hook: harness has no stop event (agy) | dependency | accept — `unsupported`, exit 0, README row | Gate::test_agy_unsupported_exit_0 |

## Adversarial analysis (STRIDE-lite)
Trust boundary: the hook seam (host → script via stdin) and the store files (written by other sessions).
- **Spoofing:** a request row can claim any `from`; the gate only counts rows whose `from`/`session` equals `$AGENT_SESSION` — a peer cannot make *my* stop fail except by writing a row as me, which the ledger records. Accept (integrity control, not a security one — NFR-S2 of P1).
- **Tampering:** the register is a tracked file; the gate fails a twice-defined number; hand edits are visible in git. Accept.
- **Repudiation:** every ruling carries `ruled by: <session>` and the request id; P1's ledger twin records the resolve. Mitigated.
- **Information disclosure:** the hook's reason names ids and a count only — never a body (the doorbell rule). The `decision-request` mail body is the requester's own text. Mitigated; test asserts no body in the reason.
- **Denial of service:** a hostile row could keep a session from stopping? Only if `from` = that session (see spoofing) — and `coord request expire`/`resolve` ends it; the host's `stop_hook_active` guard prevents a loop. Mitigated.
- **Elevation:** `COORD_ROOT`/`--root` outside the repository is refused by `resolve_root` (P1's control, reused); `--register` outside the repository is refused; stdin JSON is data, never executed. Mitigated; tests for both.

## Privacy analysis (LINDDUN-lite)
No personal data: session identifiers, decision text written by agents, timestamps. No new flow leaves the machine (mail is local files). Retention follows the repository. **Explicit no-personal-data line.**

## UI & interaction design
Terminal only. Refusal grammar `CODE  what / because / remedy`. `NOT CHECKED — <path>` is words, not colour. No visual UI (Part C N/A).

## Telemetry
`coord metrics` already counts requests by state; decision requests are requests (no new counter needed — derive, don't store). Each refusal has a stable code (above). The gate prints one reason line, structured as `owner-review: <count> unresolved decision request(s) sent by <session> (<ids>); …`. Instrumentation gap (named): no per-host record of the stop hook *firing* until `HARNESS_STATUS` (P3's file) gains a row — carried to the coordinator.

## Test plan (Testing Strategy triggers → directives)
Triggers: new CLI (D-CLI: subprocess through the real entry point, exit codes read); store-touching (D-STORE: fixture in a temp git repo, never the real `.agents/`); a gate (D-GATE: self-test + red-first fixture); a hook at a trust seam (D-SEC: negative tests for the fail-safe paths and the root refusal); portability (the two verify gates). Files: `tests/docs_explorer/test_coord_decide.py` (classes Request, Rule, List, Gate, Hygiene), `tests/docs_explorer/test_verify_ruling_citations.py` (class Gate). Red-first counts recorded in the Proof Pack section of this design's status table at `/implement`.

## Tracks for `/prepare-for-coordination`
Single track (P5). Seams out: `docs/coordination/seam-p5-to-p3.json`, `docs/coordination/seam-p5-to-coordinator.md`.

## Conformance notes
Stdlib only; utf-8 explicit on every open; `newline="\n"` on every text write; console guard on the three CLIs; `encoding="utf-8"` on every text-mode subprocess; ruff-clean. Exit codes follow `coord-mail.py`'s (0 ok · 2 refused · 3 full/terminal · 4 not checked) and the gate contract (0 · 1 · 2).

## Flagged risks & residual unknowns
As the spec's list, plus: the plan's second gate clause (exit evidence vs audit entry) is not built — fail-safe exit 0; recorded for the coordinator.

## Proof Pack (`/implement`, 2026-09-19 — observed in the P5 tree, T2)
| Claim | Oracle | Red observed | Green observed | Confidence |
|---|---|---|---|---|
| US-1…US-10 as tests | `tests/docs_explorer/test_coord_decide.py` (Request 7 · Rule 8 · List 2 · Gate 5 · Hygiene 2), `test_verify_ruling_citations.py` (Gate 11) | **43 failed, 3 passed** on the tree with no scripts (the 3 "passes" had every assertion inside `subTest`, which pytest's unittest bridge reported as PASSED against a missing script — the tests were rewritten without `subTest` before green) | **35 passed** | Verified |
| `request` refuses without the shape, writes P1's row + the mail | run in a throwaway repo (scratchpad `p5-evidence.sh`) | exit 2 `COORD-DECIDE-INCOMPLETE … --recommendation and --fallback`, `.agents/` holds only `log/` | exit 0; `requests.jsonl` row `kind: request-add, reason: decision-request, contract: {five keys}`; inbox row `kind: decision-request, ref: req-01M2XQE766…` | Verified |
| `rule` appends, resolves, mails; refuses self / not-next / defined | same run | `COORD-RULING-SELF` (exit 2), `COORD-RULING-NOT-NEXT … remedy rule 1` (exit 2), `COORD-RULING-DEFINED … remedy rule 2` (exit 2) | `### Ruling 1 — Citation gate scans prose only` + provenance line; `request-resolve … "Ruling 1"`; `ruling` mail to the requester | Verified |
| `list` empty → NOT CHECKED; populated → counts | same run | `NOT CHECKED — no requests store …` / `NOT CHECKED — no register …` | `1 open decision request(s)` (the unruled one only) · `1 ruling(s)` | Verified |
| gate exit 2 with reason; exit 0 on unevaluable paths | same run, captured stdin JSON | — | exit 2 `owner-review: 1 unresolved decision request(s) sent by p5-owner-review (req-…)`; exit 0 silent on no `AGENT_SESSION`, non-JSON stdin, `stop_hook_active`; Copilot `{"decision":"block","reason":…}` exit 0; after the ruling the ruled request no longer blocks | Verified |
| citation gate | `--self-test`; fixture; this tree | fixture: a number defined twice (`… is defined twice in docs/notes/rulings.md (lines 3, 7)`) + a cited number with no heading → exit 1; the gate then caught this very row's first draft, which quoted the fixture numbers as `Ruling <n>` prose — rewritten, and the catch is the evidence | `self-test: 6 cases …` exit 0; this tree `OK — 1 ruling(s) cited, 1 defined` exit 0 | Verified |
| portability + lint | `verify-subprocess-utf8.py`, `verify-portable-text-io.py`, `ruff check` (5 files) | — | all exit 0 | Verified |
| no regression in the coordination set | `pytest tests/docs_explorer -k "coord or requests or mail or board or leader"` | — | 358 passed, 1 skipped, **3 failed in `test_coord_derived.py`** — the same 3 fail on the primary checkout at the base commit (`main` vs `master` default branch; XP's row) | Verified (pre-existing) |

Instrumentation: every refusal has a stable code; `coord metrics` counts decision requests as requests. Named gap: no per-host record that the stop hook *fired* (`HARNESS_STATUS` is P3's file) — README table `observed-only` until seen.

## Status & next action
Completed: data model, contracts, patterns, failure/STRIDE/LINDDUN, test plan, implementation red → green, seams, README rows, Proof Pack. Remaining (coordinator): the `decide` front door, the hook JSON entries (P3), the `artifacts.yml` register line, the INSTALL delta, the skills' sentences (P8). Next: the coordinator's Adversary-Mode join clears the vetoes.

## Gate record
| Adversary | Veto | Condition | Disposition |
|---|---|---|---|
| Test Architect | hard | every failure mode has a test; the gate self-tests; red-first counts recorded | met in plan — proven at `/implement` |
| Security & Identity | hard | root/register confined to the repo; hook fail-safe; no body in the reason; stdin never executed | met — STRIDE rows + tests |
| Patterns Expert ⇄ Simplifier | soft | named idioms reused from siblings; no new abstraction or dependency; `next` literal justified | met |
| Distributed Systems | hard (if async) | n/a — no async; the concurrent-rule race dispositioned (gate is the belt) | n/a |
| SRE | advisory | stable codes; `not recorded`/`NOT CHECKED` over absence; one named instrumentation gap | met |
| Author self-clear | — | none — the coordinator clears at the join | open by design |
