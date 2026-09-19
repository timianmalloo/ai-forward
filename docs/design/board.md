---
id: design-board
title: "Design — the board (coord-board.py · audit-log.py render messages · the audit explorer's Messages view)"
type: design
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, board, mail, ledger, read-model, audit-explorer, messages-view, p6, d12]
links:
  - { to: spec-board, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: audit-log, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-18"
review-suggested: []
summary: >-
  Detailed design for spec-board. One stdlib reader (coord-board.py) that folds every inbox and
  every ledger twin into rows keyed by mail id, prints them or polls them under a cap, and posts
  a human note or ruling only through the message layer's append_mail() imported by path; one
  added field in audit-log.py render (messages, ledger twins without bodies); one added view in
  the audit explorer template, built on the page's existing tokens and states. No store, no
  write on read, no new dependency, no new colour.
---

# Design: the board

- **Status:** Draft
- **Spec / architecture:** `docs/specs/board.md` (US-1…US-9, NFRs, boundary set) · proposal §4b Board row, §7 P6, D12 · the fixed store contract in `docs/coordination/coordination-p2-p8.md`.
- **Delivery phase / vertical slice:** coordination **P6**, built in parallel with P4 (the store's writer). Real around it at this phase: the coord ledger (`.agents/log/<session>.jsonl`, `coord-core.py append_event`), `audit-log.py render`, the audit explorer template. **Absent until the join:** `pack/scripts/coord-mail.py` (`append_mail`). **Mock-substitutable seam:** the **writer** — `board post --writer <path>` imports a module by path; the default is the sibling `coord-mail.py`; tests ship a fixture writer with the same signature and schema. The coordinator swaps nothing in the board at the join: the default path simply starts resolving.

## Responsibility
Project the message store into a human-readable timeline, in the terminal and in the committed audit explorer, and let a human speak into the same store through its one writer. Nothing else: no persistence, no notification, no transport.

## Spec clarification (recorded, not drift)
- The spec's US-8 `--since <id>` orders by `(ts, id)`; a ledger twin with no `ts` sorts first (empty string) and shows `age: not recorded` — chosen over "sort last" because an undated row hidden at the bottom of a long `--follow` stream is the R4 failure (quiet-looking).
- The page's ack column reads *not recorded here* for every row (acks are not twinned by contract). The terminal's reads `✓ acked` / `- unacked` from inbox ack lines.

## Data model (settled first — DM1–DM6)
- **Aggregate:** none new. A **Mail** (P4's aggregate, root = the line, invariant = append-only, identified by `id`). The board's **Row** is a value object projected from `{inbox line?, ledger twin?}` for one id.
- **Grain:** one Row = one mail id. **Additivity:** row counts additive; `age` non-additive; `acked` boolean.
- **History:** none stored. **Derive-don't-store:** every render is a full fold; rendering twice over unchanged files yields equal rows (the rebuild equality test is `test_board_is_a_pure_fold`).
- **Row shape (the `--json` and `messages` wire):**
  ```json
  {"id": "01J…", "ts": "2026-09-19T18:00:00Z", "from": "p4-mail", "to": "coordinator",
   "kind": "blocked", "ref": "DR-3", "body": "…" , "acked": false,
   "source": "both|inbox|ledger", "age_seconds": 240, "sessions": ["p4-mail"]}
  ```
  `body` is `"(not on this machine)"` when `source == "ledger"`. The render's `messages[]` carries `id, ts, from, to, kind, ref, session` and **never** `body` (dropped even if a twin carries one by mistake — US-7).
- **Every persisted field has a writer and a compute reader:** the inbox/ledger fields are written by P4 and `append_event`; read by `coord-board.py fold()` and `audit-log.py read_ledger_mail()`; rendered by the template's `messageRow()`.

## Contracts

### Exposed
| surface | contract |
|---|---|
| `coord-board.py board [--root <dir>] [--follow] [--interval <s>] [--max-polls <n>] [--since <id>] [--session <s>] [--json]` | prints rows (or NOT CHECKED); exit 0 always for a read, 2 for a bad argument. `--root` is the `.agents` directory; default `<repo root>/.agents` found by walking up from cwd to a `.git` file or directory (the same layout `coord-core.repo_root` reads). `--follow` polls every `--interval` (default 5.0 s) until `--max-polls` (default 720) reads have happened, printing only rows not yet printed, then `stopped: --max-polls N reached`; Ctrl-C prints `stopped: interrupted`. |
| `coord-board.py board post --to <session|*> <text> [--kind note|ruling] [--ref <ref>] [--from <session>] [--writer <path>] [--root <dir>]` | validates (`kind ∈ {note, ruling}`, `ruling ⇒ --ref`, `0 < len(body) ≤ 4096` bytes utf-8, `--to` non-empty), builds the entry `{id, ts, from, to, kind, body, ref, ack: null}`, imports the writer module from `--writer` (default: `coord-mail.py` beside the script) and calls `append_mail(root, to, entry)`; prints `posted <id> → <to>`; exit 2 with a named reason on any refusal; the writer's exception is reported, exit 2. **The board never opens a mail path for writing** — test `test_post_never_opens_a_mail_file` greps the source. |
| `audit-log.py render` | `window.AUDIT_DATA` gains `"messages": [ … ]` read from `<root>/../.agents/log/*.jsonl` records with `type == "mail"`; unreadable lines are reported to stderr in the existing `read_log` idiom and skipped; the field is `[]` when the ledger directory is absent. |
| the template | a third toggle **Messages**; `DATA.messages` treated as `[]` when absent (an older `audit-data.js` still loads); kind select; table rows; the three empty/loading/error states. |

### Consumed (each with source and confidence)
| contract | source | confidence |
|---|---|---|
| inbox line schema, kinds, ack-as-a-new-line | `coordination-p2-p8.md` Fixed contracts | Verified (read) |
| ledger twin `{"type":"mail","mail_id",kind,from,to,ref}` — no `ts` promised | same | Verified; **`ts` absent ⇒ the board reads `ts`, else `at` (epoch seconds from `append_event`), else *not recorded*** |
| `append_mail(root, session, entry)` signature | same (P6 imports P4's by path) | Verified as a contract, **not yet executed** — the fixture writer stands in until the join |
| `append_event` writes `at`/`session`/`seq` | `coord-core.py` lines 177–204 | Verified (read) |
| `render()` writes `audit-data.js` with `newline="\n"` and escapes `</` | `audit-log.py` 650–673 | Verified (read) |
| the template's tokens, `.empty`, `.loading`, `__auditExplorerFail`, toggle group | `audit-explorer.template.html` | Verified (read) |

## Patterns (named, justified, ladder-climbed)
- **Read model / projection (CQRS read side)** — the whole script is a pure `fold(lines) → rows`; the ladder stops at *stdlib + a few owned lines* (no watchdog, no sqlite, no cache).
- **Single writer** — `post` delegates to `append_mail`; the board holds no append code. Pattern: *Facade over the one writer*, with a **path-imported module** (`importlib.util.spec_from_file_location`) so the dependency is a file the coordinator lands, not an import that breaks the tree before the join.
- **Bounded polling loop with a termination variant** (GO-loop rule) — `--max-polls` is the variant; the stop reason is always printed (a cap firing is a signal, so it is said aloud).
- **Degrade to *not recorded*** (IO) — `age`, `ts`, the page's ack column.
- `simplify:` `--follow` re-reads every file each poll (ceiling: a few thousand lines per poll at 5 s; upgrade trigger: a measured poll over 200 ms, then switch to size/mtime-gated reads).

## Data shapes
- Inbox path: `<root>/mail/<session>.jsonl`; ledger: `<root>/log/<session>.jsonl`. Reader accepts both `id` (inbox) and `mail_id` (twin) as the key.
- Sort key: `(ts or "", id)`. Age: `now − parse(ts)` in whole seconds, `None` when unparsable.

## Error & concurrency model
- Readers never lock: an appender's single `write()` under `O_APPEND` (coord-core spike S3) means a reader sees whole lines or not yet; a torn final line without `\n` is parsed like any other (the P4 writer owns LF termination).
- A JSON decode error → `errors[]` + a stderr `NOT CHECKED — <file>:<line> unreadable` line; rows still print; exit 0.
- `post`: argument refusals exit 2 before any import; writer import failure exits 2 with the path and the hint `the message layer (P4) is not installed here; pass --writer <path>`; a writer exception exits 2 with its message. Nothing is retried (a post is not idempotent by id unless the writer says so).

## Change-surface list (E7)
store (P4's inboxes + ledger; **unchanged**) → model (`fold()` rows) → service (`coord-board.py board/post`) → projection/wire (`--json`; `audit-data.js messages[]`) → client type (the template's `DATA.messages`) → UI (Messages view) → compute reader (the template's filters; later `coord metrics` reads counts — P2's file, not touched here).

## Failure-mode analysis
| mode | category | disposition |
|---|---|---|
| empty corpus read as "all quiet" | state | **prevent**: NOT CHECKED line, tested |
| a twin without inbox hides a message | input | **prevent**: ledger-only rows with `(not on this machine)`, tested |
| unbounded `--follow` | time | **prevent**: cap + printed reason, tested |
| a corrupt line silently dropped | input | **detect**: stderr NOT CHECKED per line, tested |
| a post bypassing the writer | concurrency (single-writer) | **prevent**: no append code in the board; source grep test |
| writer absent before the join | dependency | **detect**: exit 2 with the hint; fixture writer in tests |
| a body in the ledger leaking to the page | input | **prevent**: field allowlist in `read_ledger_mail`, tested |
| older `audit-data.js` without `messages` | state | **mitigate**: `DATA.messages || []` — the view shows NOT CHECKED |
| Windows console cannot encode `✓`/`→` | resource | **prevent**: the stdio reconfigure guard (same idiom as `audit-log.py`) |

## Adversarial analysis (STRIDE-lite)
Trust boundary: the operator's shell → the board → local files under the repo. **T (tampering):** the board writes nothing on read; `post` writes only through the writer; `--root` outside the repo is refused (`COORD-NOT-CHECKED-ROOT`, same rule as coord-core). **S (spoofing):** `--from` defaults to `$AGENT_SESSION` or `human`; a forged `from` is possible for anyone who can run the script — accepted, same trust level as writing the file directly (recorded). **I (information disclosure):** the page shows no bodies; the terminal shows the local inbox's bodies to whoever can read the files — no new exposure. **E (elevation):** `--writer <path>` executes a module the operator names — the same class as `COORD_ROOT`; documented, never taken from the environment. **D (denial):** the poll cap bounds the loop. Negative tests: outside-root refused; ruling without ref refused; 4097-byte body refused.

## Privacy analysis (LINDDUN-lite)
No personal-data category introduced; message bodies are agent/operator work text already in the local store; the committed page carries none of them. Retention is the store's (P4). No egress.

## UI & interaction design
Medium: the existing dependency-free audit explorer page. **Tokens:** only `--cp-*`; **no new colours**. Components: the toggle group gains a third `<button aria-pressed>`; a `<select id="audit-kind">` with a `.lbl` label, hidden outside the Messages view; a `<table class="msgs">` with `<caption class="sr-only">`, `<th scope="col">` × 5 (when · from → to · kind · ref · ack); rows are `<tr>` (no expansion — nothing to expand). **States:** loading and error inherited; empty = `NOT CHECKED — nothing recorded.` + guidance (`Run coord board in the repository to read the inboxes on this machine; the ledger's message twins appear here after audit-log.py render.`); filtered-empty = `No messages match the filters.` + *Clear filters*. **Copy:** ack cell = `not recorded here — see coord board`. **Motion:** none. **Reduced motion:** nothing to reduce. **WCAG 2.2 AA:** table semantics, text-only meaning, existing focus ring and 44 px controls; contrast pairs are the page's existing `--cp-text`/`--cp-text-muted` on `--cp-surface`/`--cp-bg`. **Archetype:** B2 with the deviations recorded in the spec. `DESIGN.md`: the page has no design-language doc of its own (pre-existing state, not introduced here) — recorded as a deviation; the craft gate is run on the template directly.

## Telemetry
- **What the operator asks:** *how many messages, of which kinds, per session; how old is the oldest unacked `blocked`?* — answered by the board itself (the rows are the measurement).
- **Board read-rate (the reopen trigger, D5/§6):** **not emitted by the board — reading must not write.** Named gap: the read-rate is measured from the shell history / `/session-profiler` (a `coord board` invocation count per session), and later `coord metrics` (P2's file) may count it. Until then the profiler is the only source; it degrades to *not recorded*.
- `post`: the writer (P4) owns the ledger twin for `ruling`; the board prints `posted <id>` so the shell history carries the event.
- No spans, no logs: a stdlib CLI with no runtime dependency; failures are stable stderr codes (`NOT CHECKED`, `COORD-NOT-CHECKED-ROOT`, `board post refused: <reason>`).

## Test plan (Testing Strategy triggers → directives)
D0 hygiene on every test; temp repos only; `sys.executable` subprocesses with `encoding="utf-8"`. Red first — each test was seen failing on the un-built tree (no `coord-board.py`, render without `messages`, template without the view).
| test | proves |
|---|---|
| `test_union_and_dedup_by_id` (US-1) | one row per id; `source` both/inbox; every emitted id ∈ fixture ids |
| `test_ledger_only_twin_shows_not_on_this_machine` (US-2) | |
| `test_ack_line_marks_row_acked_with_a_word` (US-3) | `✓ acked` / `- unacked` present as text |
| `test_empty_corpus_is_not_checked_exit_0` (US-4) | |
| `test_follow_stops_at_max_polls_and_says_so` (US-5) | |
| `test_post_goes_through_the_writer_fixture` (US-6) | schema of the entry the writer received |
| `test_post_never_opens_a_mail_file` (US-6) | source grep: no `open(…, "a…")` |
| `test_post_ruling_requires_ref` / `test_post_without_writer_is_refused` (US-6) | exit 2 + named reason |
| `test_unreadable_line_is_reported_not_hidden` (US-9) | |
| `test_board_is_a_pure_fold` | two renders equal (DM rebuild test) |
| `test_render_emits_messages_without_bodies` (US-7) | `messages[]` present; no `body` |
| `test_template_has_messages_view` (US-7) | the toggle, the NOT CHECKED state, the table header |
| `test_template_script_parses` | `node --check` on the page script when node is present (skipped, loudly, otherwise) |
Gates: `verify-no-machine-paths.py`, `verify-subprocess-utf8.py`, `verify-portable-text-io.py`; `ui-craft-gate.py` on the template; `tools/verify-explainer-render.js` covers `web/ai-forward-pack-explainer.html` only (**Verified**: `PAGE` at line 28) — so the audit page's render proof is the static-markup test plus `node --check`, recorded as a residual.

## Tracks for `/prepare-for-coordination`
Single track (this one, P6). Authored paths: `pack/scripts/coord-board.py`, `pack/templates/audit-explorer.template.html`, `pack/scripts/audit-log.py` (render only), `tests/docs_explorer/test_coord_board.py`, `docs/specs/board.md`, `docs/design/board.md`, `docs/notes/note-20260919-board-read-model.md`.

## Conformance notes
Local conventions followed: the `NOT CHECKED` idiom and `resolve_root` refusal from `coord-core.py`; the stdio guard, `newline="\n"` and the `</` escape from `audit-log.py`; the token set, `node()` helper, `.toggle`/`.controls`/`.empty` classes from the template. Deviation: `spec-message-layer` is a dangling link in this tree until P4's spec joins (expected; the coordinator's derive resolves it).

## Flagged risks & residual unknowns
- `append_mail` executed against the board only at the join (the fixture proves the seam's shape, not P4's behaviour).
- The page's a11y proof is static + syntax only (no DOM-shim render); a DOM-shim render test in the style of `mockup_harness_audit.test.js` is the next step if the coordinator wants gate-4b-grade proof for this page.
- `--to "*"` semantics belong to the writer (spec assumption 2).

## Status & next action
| | |
|---|---|
| **Completed** | data model, contracts, patterns, failure/adversarial/privacy analyses, UI, telemetry, test plan |
| **Remaining** | implement (red first) |
| **Best next action** | `audit-log.py start --session p6-board --skill implement`, then the tests |

## Gate record
`GATE design-slice · 2026-09-19 · peers: Python Developer (lead) · adversaries, enacted inline under fan-out 0: Patterns Expert (read model / single writer named), Simplifier (soft — accepted the re-read-per-poll with its simplify: marker; rejected a "last read" marker), Test Architect (hard — every promised behaviour has a test above), Security (writer path trust recorded; outside-root refused), UX & Accessibility (states and table semantics specified; no new colours) · verdict: **PASS-WITH-CONDITIONS** — the conditions are the tests, discharged at /implement.`
