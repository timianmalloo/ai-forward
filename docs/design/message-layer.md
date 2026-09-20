---
id: design-message-layer
title: "Design — the local message layer and dispatch (coord-mail.py · mail-doorbell.py · pack-apply ignore rules · pack-doctor checks)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination P4"
tags: [coordination, mail, doorbell, dispatch, harness, pack-apply, pack-doctor, p4]
links:
  - { to: spec-message-layer, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: design-coord-core-phase1, rel: relates-to }
  - { to: design-coord-federation-phase3, rel: relates-to }
  - { to: kb-multi-agent-coordination, rel: relates-to }
  - { to: note-20260919-mail-store-deviations, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  One stdlib script owns the inbox writer (append_mail), the reader, the ack and the bounded
  dispatch; one hook script rings every host's doorbell with a count and a pointer built from a
  function that has no body parameter; pack-apply re-includes the ledgers and ignores the mail
  dir; pack-doctor fails on a tracked mail dir, an ignored ledger, or a state-changing mail with
  no twin. Delivery is at-least-once with idempotent, colocated acks; ordering is by id.
---

# Design: the local message layer and dispatch

- **Status:** Draft
- **Spec:** `docs/specs/message-layer.md` (US-1…US-9, NFRs, deviations A.8) · binding contract `docs/coordination/coordination-p2-p8.md` "Fixed contracts" · proposal §4b, §5 dispatch table, D8/D9/D10/D12
- **Delivery phase / vertical slice:** coordination **P4**. Real around it: `coord-core.py` (ledger writer, root resolution, exit codes), `coord_ids.py`, `bounded_process.py`, `audit-log.py`, the four hook adapters. **Mock-substitutable seams:** the harness executable (a fake on `PATH` in tests), the hook payload (stdin fixtures), the store root (a temp `.agents/`). **Absent at this phase:** the board (P6 imports `append_mail` at the join), the `coord mail …` delegation line in `coord-core.py` (coordinator at the join).

## 1. Responsibility and boundaries

`coord-mail.py` — *the one writer and reader of `.agents/mail/`, and the bounded runner of another harness.* `mail-doorbell.py` — *a hook-seam adapter that turns "unacked mail newer than five minutes" into the host's response shape.* `pack-apply.py` — *the ignore rules (D10).* `pack-doctor.py` — *the invariants as FAIL lines.* Nothing here renders a board, elects, reassigns, or stores anything twice.

## 2. Data model (settled first — DM1–DM18)

| Aggregate | Root | Grain (one row is exactly one …) | Invariant | Durable form | History rule |
|---|---|---|---|---|---|
| Inbox | the file `.agents/mail/<session>.jsonl` (or `_broadcast.jsonl` for `to: "*"`) | message (an ack is a message) | every line is a complete JSON object; no line is ever rewritten; an ack refers to an earlier id | append-only fact table, machine-local, git-ignored | none — facts only |
| Ledger twin | `.agents/log/<from>.jsonl` (ADR-0007's aggregate) | mail event | one twin per state-changing message, same `mail_id`, **no body** | append-only, **tracked** (D10) | none |
| Harness status | `.agents/harness-status.json` | harness | `verified` only from a child that ran here in this run | small JSON map, machine-local, git-ignored | last-write per harness, dated |

**Row shape (contract, verbatim):** `{"id","ts","from","to","kind","body","ref","ack"}` — `ack` is always `null` on every line (a contract field; acked-ness is derived). **Twin shape:** `{"type":"mail","mail_id","kind","from","to","ref"}` plus `at` (epoch seconds) and `session` (= `from`) so `coord-core.read_events` sorts it and `active_sessions` does not see a `None` session. `assume:` the two extra keys are tolerated by P6's reader, which keys on `type == "mail"` and `mail_id`; confirmed by P6's fixture at the join; if false, the coordinator strips them at the join (they are additive).

**Measures:** `count new` (additive over messages), `age` (non-additive, derived at read). **Derive-don't-store:** acked?, count, pointer, age — all folds. **Migration:** none (new files).

**Ids:** `coord_ids.new_id("mail")` — `mail-` + 26-char ULID body (48-bit ms timestamp + 80 random bits, Crockford base32). Lexicographic order = time order within one issuer's millisecond resolution; `--since <id>` compares strings.

## 3. Change-surface list (E7)

store (`.agents/mail/*.jsonl`, twin in `.agents/log/`) → model (`coord-mail.py` entry validation, constants) → service (`send/read/ack/dispatch`, `append_mail`) → projection/wire (stdout text under the untrusted heading; `--json`; the doorbell payload per host; `harness-status.json`; the audit `--agent-run` span) → client (the hook adapters' four JSONs; P6's import at the join) → UI (none; P6's board) → compute reader (`pack-doctor` twins/ignore/doorbell checks; P6's fold). Every field has a writer (`append_mail`) and a reader (`read`, doctor, P6).

## 4. Contracts

### 4.1 Exposed

| Surface | Contract |
|---|---|
| `append_mail(root: Path, session: str, entry: dict) -> str` | `root` = the `.agents/` directory; `session` = the **sender**; `entry` needs `to`, `kind`, `body` (`ref` optional); `id`, `ts`, `from`, `ack` are filled. Validates kind ∈ KINDS, body ≤ 4096 bytes UTF-8, `to` a session id or `*`, session ids `[A-Za-z0-9][A-Za-z0-9._-]*` (no leading `_`). Refuses when the recipient has ≥ 50 unacked (`MailError("MAIL-FULL")`). Writes one line by one `os.write` (the ledger writer's idiom, incl. the leading-newline repair), then the twin for state-changing kinds. Returns the id. Raises `MailError(code, message)`; never a partial write of the inbox line. |
| `read_inbox(root, session) -> (entries, errors)` · `unread(entries, me, since=None) -> list` · `queued(root, to) -> int` · `doorbell_state(root, session, now) -> (count, pointer)` | pure folds; `errors` non-empty ⇒ callers exit 4 |
| CLI `send / read / ack / dispatch` | exit 0 · 2 refused-by-contract · 3 inbox full · 4 NOT CHECKED (coord-core's `EXIT` meanings) |
| `mail-doorbell.py --host claude\|grok\|agy\|copilot [--event <name>] [--session <id>]` | stdin = host payload; stdout = host shape or nothing; exit 0 always |
| `payload_for(host, event, session, count, pointer) -> dict \| None` | **no body parameter** — the "refused by construction" control (tested by `inspect.signature`) |
| `HARNESS_STATUS` file | `{"<harness>": {"version": str\|null, "date": ISO, "status": "verified\|observed-only\|unsupported", "evidence": str}}` |

### 4.2 Consumed (sourced)

| Contract | Source | Status |
|---|---|---|
| `coord-core.resolve_root(cwd, COORD_ROOT)`, `append_record(path, record)`, `EXIT` | `pack/scripts/coord-core.py` (read this run) | Verified |
| `coord_ids.new_id(scheme)` | `pack/scripts/coord_ids.py` | Verified |
| `bounded_process.run_bounded(command, cwd, env, timeout_seconds, stdout_limit, …) -> ProcessResult(returncode, stdout, stderr, timed_out, …)` | `pack/scripts/bounded_process.py` | Verified (signature read); `assume:` `stdout` is text — confirmed at implement by reading `drain()`; if bytes, decode utf-8/replace |
| `audit-log.py append --agent-run 'AGENT\|START\|END[\|CALLS/BUDGET]'` | `--help` this run | Verified |
| `claude -p <prompt> --output-format json` (2.1.278) · `codex exec --json [-C dir] [--sandbox …] <prompt>` (0.155.1) · `agy -p … --output-format json --print-timeout` · `grok -p … --output-format json` · `copilot -p …` | KB `data-and-constants.md` "Harness CLI contracts" (`--help` read 2026-09-19) | claude/codex/agy/grok Verified (`--help`); copilot docs-only |
| Hook response shapes: Claude/Grok `hookSpecificOutput.additionalContext`; Copilot `additionalContext` / `{"decision":"block","reason"}` with `stop_hook_active`; Antigravity `PreInvocation → injectSteps` | KB "Hook surfaces" table [P2P-26][AC-40][AC-41][AC-42]; `reread-guard.py` (shapes already shipped) | Claude Verified (deployed hooks); others docs-only → `observed-only` |
| Claude Code native cross-session message | KB: socket + registry, no CLI verb documented | Flagged — probed at implement (`claude --help`); recorded `observed-only` unless a verb exists |

## 5. Patterns (named, justified, past both lenses)

| Pattern | Where | Patterns Expert | Simplifier |
|---|---|---|---|
| **Append-only event store + fold** (event sourcing, local) | inbox, twins, acks | the ledger already uses it; replay is idempotent | no second store, no index file |
| **Single writer** (module import by path) | `append_mail` | one place validates and twins; P6 cannot bypass | the CLI is a thin shell over it |
| **Outbox-style dual write, body-less** | twin | git carries state-changing events (D9); no body in git | not a queue: the twin is a fact, never re-delivered |
| **Doorbell = notification, not payload** (claim-check) | doorbell | the host fetches via `read`; injection surface is count+id | one function, one string template |
| **Bounded subprocess** | dispatch | reuse `bounded_process.py`; deadline = budget | no retry loop, no polling |
| **Fail-open at the tool seam** | doorbell | as `reread-guard.py`: a hook that fails must not deny the tool | exit 0 everywhere |

**Ladder:** YAGNI (no `progress` kind, no expiry sweeper, no `nack` verb — `send --kind nack`) → reuse (`append_record`, `run_bounded`, `new_id`, `resolve_root`) → stdlib only → no new dependency. `simplify:` HELD_CAP=100 is reported by `read` and doctor as an advisory, not enforced as a refusal (ceiling: an inbox over 100 lines; upgrade trigger: a real inbox is seen over the cap, then add an archive verb). `simplify:` `--budget-calls` is recorded in the span, passed to no harness flag until one is verified per harness.

## 6. Error and concurrency model (distributed-systems lens)

- **Delivery:** at-least-once. A retried `send` writes a second message with a new id; the board shows both; a reader acks each. No dedupe window is implemented (`simplify:` identical-repeat drop deferred; trigger: a measured duplicate rate > 0 on the board).
- **Idempotent acks:** an ack is `(ref, from)`-unique — `ack` re-run finds the existing ack line and writes nothing, exit 0.
- **Ordering:** by `(ts, id)` — the writer's live clock is made strictly increasing per process (two back-to-back sends never share a millisecond stamp, and the id is minted from the same stamp so id order agrees with ts order); across issuers no total order is promised (the board sorts by `ts`, a hint). `--since <id>` means "after that message's `(ts, id)` position" when the id is present, else a string comparison. Found at implement: ids minted in one millisecond order by their random bits, which made a pointer and a `--since` flaky — the fix is the monotonic stamp, not a sort tweak.
- **Concurrency:** one `os.write` per line under `O_APPEND` (atomic for lines < PIPE_BUF on POSIX; the ledger's spike S3 basis); the leading-newline repair prevents a fused record. Two senders to one inbox interleave whole lines. The queue cap is a read-then-write race by design: two concurrent sends at 49 may both land (cap 51) — accepted, it bounds, it does not meter.
- **Doorbell is a hint, the inbox is truth:** a doorbell that never fires loses nothing; `read` is the delivery.
- **Expiry:** the doorbell counts unacked messages with `now - ts ≤ 300 s` (a stale unacked note stops ringing at every tool boundary); `read` still shows them; the pointer is the newest counted id.
- **Errors:** `MailError(code)` with stable codes `MAIL-KIND`, `MAIL-BODY-SIZE`, `MAIL-IDENTITY`, `MAIL-TO`, `MAIL-FULL`, `MAIL-NOT-FOUND`, `MAIL-NOT-CHECKED`, `MAIL-DISPATCH-REFUSED`; every CLI refusal prints `<code>  <reason>` on stderr, one line.

## 7. Dispatch

```
dispatch --harness H --brief FILE --deadline S --fallback TEXT [--worktree DIR] [--budget-calls N]
  1. refuse (exit 2) without --deadline or --fallback; brief must resolve inside the repo
  2. exe = shutil.which(H's executable) → None ⇒ status unsupported, evidence "not installed", print fallback, exit 0
  3. version = run_bounded([exe, "--version"], timeout 20)
  4. result = run_bounded(argv(H, brief_text), cwd=worktree, timeout_seconds=S, env=utf-8)
  5. status = verified iff returncode==0 and not timed_out and structured output parses (json for claude/agy/grok; JSONL last line for codex; non-empty stdout for copilot); else observed-only
  6. write harness-status.json[H] = {version, date, status, evidence: head of stdout/stderr ≤ 400 chars}
  7. audit-log.py append --shortname dispatch-<H> --kind script --agent-run "<H>|<start>|<end>|<calls or ->/<budget or ->"
  8. print JSON {harness, status, returncode, timed_out, duration_s, fallback: TEXT if not verified}; exit 0
argv: claude-code → [claude, -p, brief, --output-format, json]
      codex       → [codex, exec, --json, --sandbox, read-only, brief]   (+ -C worktree)
      agy         → [agy, -p, brief, --output-format, json, --print-timeout, S]
      grok        → [grok, -p, brief, --output-format, json]
      copilot     → [copilot, -p, brief]
```
`unsupported` is also the status for a harness present on the machine but not executed in this run (a status file is per run: dispatch rewrites only its own harness entry, and the file's `run` field carries the newest run date; doctor reports what it reads).

## 8. Doorbell adapters

| Host | Event(s) | Response when count > 0 | Otherwise |
|---|---|---|---|
| claude | `PreToolUse` (no matcher), `UserPromptSubmit` | `{"hookSpecificOutput":{"hookEventName":<event>,"additionalContext":<text>}}` | nothing |
| grok | same | same | nothing |
| agy | `PreInvocation` | `{"injectSteps":[{"ephemeralMessage":<text>}]}` (objects — protojson rejected a string list, observed 2026-09-20) | nothing |
| copilot | `preToolUse` | `{"additionalContext":<text>}` | nothing |
| copilot | `agentStop` | `{"decision":"block","reason":<text>}` only if `stop_hook_active` is not true | nothing |

`<text>` = `"coord mail: {count} new for {session}; newest {pointer}; run coord mail read"`. Session = `--session` else `$AGENT_SESSION`; unset ⇒ nothing. The adapter JSONs gain entries in the existing resolver-command shape (interpreter resolved at run time); `pack-apply` places `mail-doorbell.py` beside `reread-guard.py`. Claude Code's native message: probed by `claude --help` at implement; no documented CLI verb ⇒ `observed-only` in `harness-status.json` under key `claude-code-doorbell`.

## 9. Ignore rules and doctor

- `pack-apply`: `GITIGNORE_LINES` gains `!.agents/log/` (right after `!.agents/artifacts.yml`; dependent of the `.agents/*` blanket) and `.agents/mail/` (explicit, so mail stays ignored even when the blanket is withheld). **Report:** today's default ignores `.agents/log/` through `.agents/*`; the conditional withholding of the blanket when a repo already tracks files under `.agents/` beyond the registry is unchanged (`test_pack_apply.py` pins it and is not P4's file) — under it, tracked ledgers still keep the blanket withheld with a KEEP row, and the explicit `.agents/mail/` line is what keeps mail out in that repo.
- `pack-doctor` (`check_mail(root) -> list[result]`): **mail dir** FAIL when `git ls-files .agents/mail` is non-empty; **ledger tracking** FAIL when `git check-ignore -q .agents/log/probe.jsonl` exits 0 (names D10); **mail twins** FAIL naming each state-changing inbox id with no `type: mail` twin in any `.agents/log/*.jsonl` (PASS "no inboxes present (nothing to check)" when the dir is absent); **doorbells** one PASS line per harness from `harness-status.json`; file absent ⇒ PASS with detail `not recorded (run coord-mail.py dispatch)` so a fresh install is not red for lack of a probe.

## 10. Failure-mode analysis

| Mode | Category | Disposition | Test |
|---|---|---|---|
| Unterminated last line in an inbox | state | prevent (leading-newline repair) | US-1 torn-line test |
| Corrupt JSON line | input | detect → exit 4, never a partial fold | read on a bad line |
| Body over 4 KiB / unknown kind / no identity | input | prevent → exit 2, nothing written | US-1 |
| Recipient not reading | time | mitigate → cap 50 → exit 3 | US-2 |
| Twin write fails after inbox write | dependency | detect: doctor "mail twins" FAIL names the id (the inbox line stands; the twin is re-issuable by hand) | doctor test |
| Doorbell run with no session / unreadable store | dependency | fail-open, exit 0, nothing | US-6 |
| Copilot block loop | time | prevent: never block when `stop_hook_active`; never block on count 0 | US-6 |
| Harness hangs / needs auth | time | mitigate: deadline → `observed-only`, fallback printed | US-7 fake harness sleeping past deadline |
| Two concurrent sends at the cap | concurrency | accept (bounds, not meters) | documented |
| Store root outside the repo (`COORD_ROOT`) | input | prevent: `resolve_root` refuses → exit 4 | inherited from coord-core tests |

## 11. Adversarial analysis (STRIDE-lite)

| Boundary | Threat | Disposition | Negative test |
|---|---|---|---|
| Hook stdout → model context | **T**ampering/injection: a message body shaped as an instruction reaches the model | mitigate: payload built from count/session/id only; body never read by the doorbell's string builder | every host output greps clean of the body |
| `read` output → model | same | mitigate: untrusted heading; `--json` for machines | heading present |
| `--body-file`, `--brief` | **I**nformation disclosure / traversal (read an arbitrary file) | mitigate: path must resolve inside the repository root | outside path → exit 2 |
| `COORD_ROOT` | **E**levation: a store outside the repo becomes trusted state | mitigate: coord-core's refusal reused | inherited |
| Twin in git | **I**nfo disclosure of bodies via git | mitigate: twins carry no body | twin has no `body` key |
| `dispatch` | **E**levation via the child's permissions | mitigate: no `--allow-all-tools`/`--permission-mode` flags added by default; brief passed as an argument, not a shell string | argv assert |
| Doorbell `--session` | **S**poofing another session's inbox read | accept: machine-local, same user; the store is not a trust boundary between local sessions (ADR-0007 stance) | — |

**`documents` links needed (reported, not written — coordinator at the join):** `docs/security/threat-model.md` → `design-message-layer` ("doorbell string injection; body-file and brief path traversal; twin body exclusion"); `docs/security/privacy-review.md` → `design-message-layer` ("mail bodies machine-local and git-ignored; ledger twins body-less; no personal data category beyond session ids").

## 12. Privacy analysis (LINDDUN-lite)

Data: session ids (pseudonymous work identifiers), message bodies (work data, may quote files). **L**inkability: twins link session ids across machines — accepted, that is the ledger's purpose. **D**etectability/**D**isclosure: bodies stay in an ignored dir; twins carry none. **U**nawareness: `read` shows who sent what. **N**on-compliance: no personal data category is introduced; retention = the file's lifetime on the machine; deletion = deleting the dir (nothing else references bodies).

## 13. Telemetry (O1–O13)

- `dispatch`: audit entry with `--agent-run` span (harness, start, end, calls/budget) and `--tool coord-mail.py`; stable codes in the JSON result (`status`, `returncode`, `timed_out`, `duration_s`).
- `send/read/ack`: no separate log — the store is the measurement (counts per session, kinds, ack latency = `ack.ts - msg.ts` are folds over the files; the board renders them). Doorbell latency (send → first `read`) is derivable from the same two timestamps. Degrades to "not recorded" (a missing ack is visible as unacked, never as a plausible number).

## 14. Test plan (Testing Strategy union; red-first)

`tests/docs_explorer/test_coord_mail.py`: schema round-trip (US-1); note has no twin, delegate/ruling do; body size / kind / identity refusals; full inbox exit 3 (US-2); read own + broadcast, `--since`, `--ack`, `--json` (US-3); ack is a new line, idempotent, not-found exit 4 (US-4); `append_mail` imported by path equals CLI bytes (US-5); torn-line repair; corrupt line → exit 4; dispatch refused without deadline/fallback (exit 2); absent CLI → `unsupported`; fake harness on PATH → `verified`; fake sleeping harness → `observed-only` with fallback (US-7); pack-apply lines present and `git check-ignore` proves `.agents/log/x.jsonl` tracked, `.agents/mail/x.jsonl` ignored (US-9); pack-doctor FAIL/PASS cases (US-8). `tests/docs_explorer/test_mail_doorbells.py`: every host × event shape; no body in any output (US-6); `payload_for` has no body parameter; copilot agentStop guard; unset session → nothing; the four adapter JSONs carry the doorbell entries in the resolver shape; a 100-line inbox rings in ≤ 250 ms (generous margin, timing assert). Temp repos only; no network.

## 15. Conformance and conventions

Stdlib only; stdio reconfigure guard; `newline="\n"` on writes; `encoding="utf-8"` on subprocesses; no machine paths in tracked files; hyphenated script imported by path via `importlib.util` (the pack's idiom for `coord-core.py`); Python 3.8+ syntax (`from __future__ import annotations`).

## 16. Gate record (adversaries enacted inline, fan-out 0)

| Lens | Finding | Disposition |
|---|---|---|
| Distributed Systems (hard) | "A cap that races is not a cap." | Accepted as a bound; documented; a strict cap would need a lock file, which is a second store (§6). Cleared by the lens, not the author. |
| Distributed Systems | "Expiry hides unacked mail from the doorbell." | Intended: the inbox is truth; `read` shows it; the board shows it aged. |
| Test Architect (hard) | "`verified` from a fake harness proves the wiring, not the harness." | Correct: the real `claude -p` / `codex exec` runs are exit evidence recorded in `harness-status.json`, distinct from the unit test. |
| Security (hard) | "`--brief` reads a file and hands it to a child — traversal." | Mitigated: inside-repo check (§11). |
| Patterns ⇄ Simplifier | "Six patterns for a JSONL file?" | Each maps to one existing idiom in the pack; none introduces a new abstraction or file type. |
| SRE | "Where is the dispatch duration?" | In the `--agent-run` span and the JSON result. |

**Verdict:** PASS-WITH-CONDITIONS — the two `documents` links are owed by the coordinator; the twin's two extra keys are an `assume:` confirmed at the P6 join.

## 17. Confidence ledger, residual risk, status

- Verified: coord-core/coord_ids/bounded_process contracts; harness `--help` shapes for claude/codex/agy/grok; Claude hook shape. Inferred: Copilot/Antigravity/Grok doorbell behaviour (docs-only → `observed-only`). Flagged: nested `claude -p` from within a Claude Code session; codex non-interactive auth.
- Residual risk: a host we cannot execute here never rings — inbox + ledger + deadline/fallback is the floor (D8).
- **Status:** completed — data model, contracts, patterns, failure/STRIDE/LINDDUN, telemetry, test plan · remaining — implementation (`/implement`), the two rollup links (coordinator), P6 join confirmation of the twin's extra keys · best next action — `/implement` red-first.
