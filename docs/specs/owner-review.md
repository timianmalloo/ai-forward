---
id: spec-owner-review
title: "Owner review mechanics — decision request → numbered ruling, a heading-defined register, a citation gate and a stop-hook gate"
type: spec
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, owner-review, decision-request, ruling, register, gate, hook, p5, d6, id-a]
links:
  - { to: proposal-owner-coordinator-subagent-coordination, rel: refines }
  - { to: spec-typed-seam-requests, rel: depends-on }
  - { to: spec-message-layer, rel: depends-on }
  - { to: spec-agent-coordination-doctrine, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  Specifies P5 of the coordination proposal (D6): the Owner seat gets a mechanism. A decision
  request is P1's typed seam request carrying five decision fields (options, evidence,
  recommendation, reversibility, blast radius) plus a deadline and a fallback, dual-written as a
  decision-request mail; a ruling is a numbered heading appended to docs/notes/rulings.md (the
  only definition site) that resolves the request and mails the requester; a citation gate fails
  a number cited with no heading or defined twice; a Stop hook exits 2 when the stopping session
  still holds an unresolved decision request it sent, and 0 on every path it cannot evaluate.
---

# Spec: Owner review mechanics (P5)

- **Status:** Draft
- **Tier (cost-of-error):** **T2** — this is the mechanism behind D6 (*reviewer ≠ author*). A ruling that cannot be read back, or a number that two decisions share, is the measured ai-de failure (`~/projects/ai-de/tools/verify-ruling-citations.py` header, 2026-09-11: eight ruling numbers cited as binding defined nothing; one number was allocated twice *because* nothing recorded the first). A stop gate that blocks on a path it cannot evaluate would end sessions for the wrong reason at the trust seam.
- **Author(s) / date:** Python Developer (Peer Mode, track P5, Sub-Agent seat under `coordination-p3-p5-p8`), 2026-09-19. Adversaries at the gate, **enacted inline (fan-out cap 0 by the track contract)**: Test Architect (hard veto), Security & Identity (hard veto at the hook seam), Simplifier (soft veto). Inline enactment is recorded, not hidden: every veto condition is a falsifiable criterion below and is proven by a named test at `/implement`; the author does not clear the vetoes — the coordinator's Adversary-Mode join does.
- **Supersedes / related:** refines `docs/proposals/owner-coordinator-subagent-coordination.md` §2.1 finding **A7** ("the Owner seat has no mechanism"), §3.1 (Owner seat: *answer decision requests with numbered rulings; never clear its own veto*), §3.2 (registered relationship: **deadline + fallback mandatory on every request**), §4 row *Decision request / Ruling*, §7 row **P5**, decision **D6**. Binding fixed contracts: `docs/coordination/coordination-p3-p5-p8.md` "Fixed contracts" (*the decision request is P1's typed request, not a new store*; *the ruling register is `docs/notes/rulings.md`*; *owner review gate*). Depends on `spec-typed-seam-requests` (P1, landed: `coord request add|resolve`, the `.agents/requests.jsonl` store and its fold) and `spec-message-layer` (P4, landed: `append_mail`, kinds `decision-request` and `ruling`).

> **Grounding trace (V15):** `spec-owner-review` → `refines` → `proposal-owner-coordinator-subagent-coordination` (§4: *"options, evidence, recommendation, reversibility, blast radius / the ruling text under a heading — verify-ruling-citations absorbed into the pack"*; §3.1 Owner *may* "answer decision requests with numbered rulings", *must not* "clear its own veto when it authored the thing"; D6) → `depends-on` → `spec-typed-seam-requests` (`cmd_request` at `pack/scripts/coord-core.py:2418`: `add` refuses without `--deadline`/`--fallback` with `COORD-REQUEST-INCOMPLETE` exit 2; the record carries `contract`, `reason`, `ref` when given; `resolve <id> --resolution` writes `request-resolve`; `fold_requests` at `:471`) → `depends-on` → `spec-message-layer` (`KINDS` at `pack/scripts/coord-mail.py:66` already contain `decision-request` and `ruling`; `append_mail(root, session, entry)` at `:288` validates, appends, twins state-changing kinds; `BODY_MAX_BYTES = 4096`) → `relates-to` → `agent-coordination` (CO1: the Owner rules on decision requests; CO16: *decision request / ruling* (`decide request` / `rule <n>`); CO17 rung 2: escalate with a decision request). Measured origin read whole: `~/projects/ai-de/tools/verify-ruling-citations.py` (definition = heading, citation = prose; the frozen list "may only shrink"); `~/projects/ai-de/docs/collaboration/session-contracts.md` cites rulings by number in prose 22 times and defines none — the definition site there was `docs/notes/`. KB row: `docs/knowledge/multi-agent-coordination/data-and-constants.md:79` ("Rulings defined by headings; numbers that defined nothing — 1–139; 8 (6 frozen)").

---

## Part A — Functional specification

### Problem
The doctrine says the Owner seat reviews by *decision request → numbered ruling* (CO1, D6) and the kick ladder's rung 2 escalates with a decision request (CO17). Nothing implements it. A Sub-Agent that hits a consequential unresolved question today writes prose into a mail or a note; the Owner answers in prose; the number, if any, is typed by hand and enforced by reputation. ai-de measured where that ends: numbers cited as binding with no definition, and a collision in the allocator that did not exist. The pack also has no control that stops a session from ending while its own decision request is still open — the harness auto-approves the stop.

### Target users & personas
- **The Sub-Agent (any track):** must raise a decision it may not make itself, with enough structure that the Owner can rule without a round trip, and must be prevented from *stopping* while that request is unanswered.
- **The Owner seat (a model in Adversary Mode, or the human):** rules with a number that is guaranteed unique and readable back, in one command that also resolves the request and tells the requester.
- **A later session / a reviewer:** cites `Ruling NN` in prose and can open the one file that defines it; CI fails when a cited number defines nothing.

### Core scenario
Track P5 cannot decide whether the citation gate scans JSON records. It runs `coord decide request --to coord-p3-p5-p8 --options "prose only | prose + JSON" --evidence "audit-log.jsonl:164 quotes ai-de's ruling number 38 verbatim" --recommendation "prose only" --reversibility "one constant" --blast-radius "the gate's scan set" --deadline 900 --fallback "prose only, recorded as a note" "Does verify-ruling-citations scan JSON records?"`. One request record lands in `.agents/requests.jsonl` (P1's writer), one `decision-request` mail lands in the coordinator's inbox with `ref` = the request id. The coordinator's doorbell rings. The coordinator runs `coord decide rule next --title "Citation gate scans prose only" --text "…" --request req-…`: `### Ruling n — Citation gate scans prose only` is appended to `docs/notes/rulings.md`, the request is resolved with `Ruling n`, and a `ruling` mail reaches P5. If P5 had tried to stop before that, its `Stop` hook would have exited 2 with `owner-review: 1 unresolved decision request sent by p5-owner-review (req-…); rule or expire it before stopping`.

### In scope / Out of scope (explicit non-goals)
**In scope:**
- `pack/scripts/coord-decide.py request|rule|list` (front door `coord decide …` added by the coordinator at the join — seam).
- `docs/notes/rulings.md` — the register, created with V2 frontmatter; the only definition site.
- `pack/scripts/verify-ruling-citations.py` — the citation gate, absorbed from ai-de and re-homed.
- `pack/adapters/hooks/owner-review-gate.py` — the `Stop` (Claude Code) / `agentStop` (Copilot) gate; its hook JSON entries per host as a seam to P3.
- Tests, README rows, the seam files, the contract sentences for the two coordination skills (delivered as text).

**Out of scope (non-goals):**
- A second store for decision requests (the request store is P1's; the mail is P4's; the register is a Markdown file). No `.agents/decisions/`.
- An allocator for ruling numbers anywhere but the register's own headings (class ID-A).
- Editing `coord-core.py`, the hook JSONs, the skills, `agent-coordination.md`, `INSTALL.md` frontmatter, `.agents/artifacts.yml` — these travel as seams.
- A rulings view in the audit explorer; a separate Owner sub-agent; the cross-harness smoke test; P3's heartbeat/kick verbs.
- The plan's second gate clause (*exit evidence named by the plan row that the audit entry does not carry*): it needs a plan-row parser and an audit-entry shape that do not exist; under the fail-safe rule it is a path the gate cannot evaluate and therefore exits 0. Recorded as a finding for the coordinator, not built.

### Conceptual domain model (DM1/DM4)
- **Decision request** — *not a new aggregate*: a **Seam request** (P1's aggregate, root = the `request-add` row, identity = `req-…` id, invariant = terminal by deadline or resolution) whose `reason` is `decision-request` and whose `contract` is the five decision fields. Grain: one row is exactly one request transition (unchanged).
- **Ruling** — a value in the **Register** aggregate (`docs/notes/rulings.md`; root = the file; invariant = *each number is defined exactly once and numbers are monotonic*). Grain: one `### Ruling NN — <title>` block is exactly one ruling. Identity = the number, allocated by reading the register (max + 1) — never stored elsewhere. History: append-only; a ruling is never edited in place (a later ruling supersedes it in prose).
- **Citation** — a derived relation (prose mention → number). Never stored; recomputed by the gate on every run.
- **Ruling mail / decision-request mail** — P4's Mail aggregate; `ref` carries the request id; the ruling body carries `Ruling NN — <title>`.

### User stories & acceptance criteria (testable)
Each criterion names the test that proves it (Test Architect: every promise has a verification path).

- **US-1 — A decision request is refused without its shape.** `coord-decide.py request` exits **2** with `COORD-DECIDE-INCOMPLETE` naming every missing item when any of `--options`, `--evidence`, `--recommendation`, `--reversibility`, `--blast-radius`, `--deadline`, `--fallback`, `--to` or the question text is absent. Nothing is written (no request row, no mail). *Test:* `test_coord_decide.py::Request::test_refused_without_five_fields_deadline_fallback` (red-first: the script does not exist).
- **US-2 — A decision request is P1's request plus a mail.** A complete `request` appends exactly one `request-add` row to `.agents/requests.jsonl` **through `coord-core.py request add`** (verified by the row shape P1 writes: `kind`, `id`, `at`, `session`, `from`, `to`, `text`, `deadline_at`, `fallback`, plus `reason: decision-request` and `contract` = a JSON object with the five keys `options, evidence, recommendation, reversibility, blast_radius`), and appends one `decision-request` mail to the addressee's inbox with `ref` = the request id and a body carrying the question and the five fields. Stdout is one JSON line `{"id", "status": "sent", "deadline_at", "mail"}`. *Test:* `::Request::test_writes_p1_record_and_decision_request_mail`. **No second writer:** `coord-decide.py` contains no `open(` on `requests.jsonl` (source assertion). *Test:* `::Request::test_no_second_writer_for_the_request_store`.
- **US-3 — A ruling is a heading, a resolution and a mail.** `rule <n> --title T --text X --request <id>` appends `### Ruling n — T`, a blank line, X, and a provenance line to `docs/notes/rulings.md`; resolves the request via `coord-core.py request resolve <id> --resolution "Ruling n"`; sends a `ruling` mail to the request's `from` with `ref` = the request id. *Test:* `::Rule::test_appends_heading_resolves_and_mails`.
- **US-4 — The register is the allocator.** `n` must equal the next number (max defined + 1; 1 on an empty register); the literal `next` is accepted and means that. A number already defined is refused (exit 2, `COORD-RULING-DEFINED`); a gap or a lower number is refused (exit 2, `COORD-RULING-NOT-NEXT`, the remedy names the expected number). *Tests:* `::Rule::test_defined_number_refused`, `::Rule::test_non_next_number_refused`, `::Rule::test_next_literal_allocates_from_the_register`.
- **US-5 — Reviewer ≠ author, and the request must be rulable.** Ruling on a request whose `from` equals the ruling session is refused (exit 2, `COORD-RULING-SELF`, D6). An unknown request id exits 4 (`COORD-REQUEST-NOT-FOUND`); a terminal one exits 3 — both **before** the heading is appended (the register is unchanged). *Tests:* `::Rule::test_self_rule_refused`, `::Rule::test_unknown_or_terminal_request_leaves_register_unchanged`.
- **US-6 — The register is created once, with frontmatter.** When `docs/notes/rulings.md` is missing, `rule` creates it with V2 frontmatter (`id: rulings`, `type: doc`) and one intro paragraph, then appends. Written utf-8, LF. *Test:* `::Rule::test_register_created_with_frontmatter_lf`.
- **US-7 — `list` renders the open decision requests and the rulings; empty says NOT CHECKED.** Open = `reason: decision-request` rows whose folded status is in `REQUEST_OPEN`. Rulings = the register's headings (number, title). When the requests store does not exist, that half renders `NOT CHECKED — no requests store at <path>`; when the register does not exist, `NOT CHECKED — no register at <path>`; an existing store with zero decision requests renders `0 open decision request(s)`. `--json` emits the same. *Tests:* `::List::test_empty_corpus_renders_not_checked`, `::List::test_renders_open_requests_and_rulings`.
- **US-8 — The citation gate fails what ai-de measured.** `verify-ruling-citations.py`: a `Ruling NN` cited in prose (`.md`, `.html`, `.txt`) under `docs/`, `pack/`, `.agents/log/`, `.github/`, `.claude/` with no `## Ruling NN —`/`### Ruling NN —` heading in `docs/notes/rulings.md` → exit **1**, one line per defect; a number defined by two headings → exit 1; `--self-test` proves an undefined citation, a twice-defined number, a prose-only "definition" and a clean tree (exit 0 when all fire correctly); `--root` not a directory → exit 2. *Tests:* `test_verify_ruling_citations.py::Gate::test_undefined_citation_fails`, `::test_twice_defined_fails`, `::test_self_test_passes`, `::test_clean_tree_exit_0`, `::test_scans_only_prose_records_are_quotes`.
- **US-9 — The stop gate blocks only what it can prove.** `owner-review-gate.py --host claude` with `AGENT_SESSION` set and an open decision request whose `from` is that session → exit **2**, one reason line on stderr naming the count and the ids. Exit **0** and no output on: no `AGENT_SESSION`; stdin not JSON; `stop_hook_active` true; no `.agents/`; no requests store; a store with a malformed line; `COORD_ROOT` outside the repository; requests sent by other sessions; requests addressed *to* this session (out of contract — noted); host `agy` (no stop event). `--host copilot --event agentStop` emits `{"decision":"block","reason":…}` on stdout with exit 0 (Copilot's own block form), nothing otherwise. *Tests:* `test_coord_decide.py::Gate::test_exit_2_with_reason_on_own_open_decision_request`, `::Gate::test_fail_safe_paths_exit_0`, `::Gate::test_copilot_block_shape_and_stop_guard`.
- **US-10 — Portable and gated.** Every text write `newline="\n"`, every open `encoding="utf-8"`, every text-mode subprocess `encoding="utf-8"`, the console guard on every printing CLI (`verify-portable-text-io.py`, `verify-subprocess-utf8.py` exit 0); `ruff check` clean on the new files. *Test:* the two gates, run at the exit; `test_coord_decide.py::Hygiene::test_readme_documents_the_gate`.

### Non-functional requirements (ISO/IEC 25010 checklist)
- **Reliability:** the request row is written before the mail; a mail failure is reported in the JSON (`"mail": "not sent: <code>"`) and never changes the exit (the store is truth, the mail is push — the doorbell rule). The heading is appended only after the request is proven rulable.
- **Security (STRIDE-lite, walked in the design):** the hook reads only through `resolve_root` (never outside the repository), never executes anything from the store, and prints only ids and counts (no bodies) in its reason. The register write is inside the repository (`repo_root(cwd)/docs/notes/rulings.md`); `--register` is refused outside it.
- **Performance:** `list` and the gate fold one JSONL file (P1 measured `fold_requests` over 901 events in well under a second); the gate's budget is the hook timeout (10 s) — it does one read and no subprocess.
- **Portability:** stdlib only, Python 3.8+, utf-8/LF everywhere, console guard; the hook command uses the README's interpreter-resolution idiom.
- **Maintainability:** one writer per store (P1's for requests, P4's for mail, this script for the register only); numbering read from the register; no configuration.

### Boundary set
Empty register · register with frontmatter but no rulings · one ruling · non-contiguous numbers written by hand (refused as *not next*; the gate still accepts them as definitions) · a heading at `##` and `###` (both define) · a `####` heading (does not define — the contract names two levels) · `Ruling NN` vs `Rulings NN` (both cite) · a zero-padded `Ruling 0N` (defines N) · a request store with a malformed line · `stop_hook_active` · body over 4 KiB (refused before any write) · `COORD_ROOT` outside the repo · `AGENT_SESSION` unset · `--to *` (refused: a decision request needs one Owner).

### Comparables & user evidence (sourced)
- **ai-de's ruling register** (`~/projects/ai-de/tools/verify-ruling-citations.py`, Verified read whole): definition = heading, citation = prose; the first pattern was wrong and its first run caught it (DC-104) — hence `--self-test` here; the frozen list is *not* carried (this register starts empty — nothing predates the control).
- **ai-de's session contracts** (`~/projects/ai-de/docs/collaboration/session-contracts.md`, Verified): rulings are cited by number inside ownership tables ("ruling number 114 added `ProseView.cs`") — the citation form this gate scans.
- **P1 typed requests** (`docs/notes/note-20260919-seam-request-terminal-by-deadline.md`, Verified): *refuse, do not default* a missing deadline or fallback — the same rule applies to the five decision fields.
- **P4/P6** (`coord-board.py`, Verified): importing the mail writer by path is the landed pattern for a sibling script.
- **Claude Code `Stop` hook contract** (Inferred from `pack/adapters/hooks/README.md` and the doorbell: exit 2 blocks with stderr as the reason; `stop_hook_active` guards the loop). Marked `observed-only` in the README until a live stop shows it fire (CO12).

### Applicable governance lenses
Quality attributes (reliability, portability) — answered above. Threat model — design STRIDE-lite. Privacy — no personal data: session ids and decision text authored by agents; the mail body is the requester's own text (LINDDUN: no new flow). Accessibility — CLI text; `NOT CHECKED` is a word, never a colour. Release/rollback — additive files; the hook entry is applied by P3/the coordinator and removable by deleting one array element. Observability — every refusal has a stable code; `coord metrics` already counts requests by state (decision requests are requests).

### AI-integrated allocation
No model call. The Owner *seat* is a model or a human; this spec gives it a deterministic mechanism.

---

## Part B — UX specification
*Medium: terminal (CLI) and a hook seam. No visual UI (Part C N/A).*

### Personas & jobs-to-be-done
Sub-Agent: *raise a decision I may not make, in one command, and be stopped from ending before it is answered.* Owner: *rule with a number I did not have to look up, and have the requester told.* Reviewer: *open the one file that defines a cited number.*

### Information architecture
`coord decide` — three verbs: `request` (write), `rule` (write), `list` (read). Refusals in the pack's grammar (`CODE  what\n  because  …\n  remedy  …`) on stderr, exit 2. Reads print to stdout. The register is one file under `docs/notes/`, headings in number order.

### User flows (happy + alternate + error + recovery)
1. **Happy:** `request` → row + mail → doorbell → `rule next` → heading + resolve + ruling mail → requester reads → stop hook now exits 0.
2. **Alternate — deadline passes:** `coord request expire` (P1) records the fallback; the gate no longer counts it (terminal); `list` no longer shows it. No ruling is written.
3. **Error — wrong number:** `rule 5` on a register at 2 → `COORD-RULING-NOT-NEXT … remedy: rule 3 (or `next`)`. Register unchanged.
4. **Error — self-rule:** the requester tries to rule its own request → `COORD-RULING-SELF`. Register unchanged.
5. **Recovery — mail not sent:** the request exists; the JSON says `"mail": "not sent: MAIL-FULL"`; the requester tells the Owner by another channel or retries with `coord mail send --kind decision-request --ref <id>` — no second request.
6. **Recovery — heading appended, resolve failed (race):** the gate `verify-ruling-citations` is quiet (a definition without a citation is allowed); `list` still shows the request open; the Owner runs `coord request resolve <id> --resolution "Ruling n"` by hand.

### UX acceptance criteria (falsifiable)
Every refusal names the remedy on the next line (tested in the refusal tests by asserting `remedy`). `list` never renders an empty table as quiet (US-7).

## Part C — UI specification
**N/A — no visual UI.** The audit explorer rulings view is an explicit non-goal.

---

## Flagged risks & residual unknowns
- **(Flagged)** The Claude Code `Stop` hook's exit-2 semantics are taken from the hooks reference as read for the doorbell and not yet observed live in this repo; README marks the host `observed-only`.
- **(Inferred)** Copilot's `agentStop` block shape (`decision: block` + `reason`) is the doorbell's; the gate reuses it unchanged.
- **(Flagged)** The proposal's `HARNESS_STATUS` record lives in `coord-core.py` (P3's file); this track records host status in the README table and asks the coordinator to mirror it (seam).
- **(Verified)** Baseline citations already in the corpus before the register exists: `Rulings 1` (proposal §1.2 "Rulings 1–139", md + html), ai-de's ruling number 38 (`docs/audit/audit-log.jsonl:164`, a verbatim prompt quoting ai-de), ai-de's numbers 126/128 (`docs/dreams/drm-0010/dream.json`). Only the prose ones are citations under this spec (records are quotes); Ruling 1 is defined by the committed register (the decision to create it), which makes the proposal's range mention resolve as a side effect — stated, not hidden.

## Gate record
| Adversary | Veto | Condition | Disposition |
|---|---|---|---|
| Test Architect | hard | every US names a red-first test; the gate has a self-test; the hook's fail-safe paths are each a test case | met — see US-1…US-10; proven at `/implement` |
| Security & Identity | hard | the hook never blocks on a path it cannot evaluate; never reads outside the repo; prints no bodies | met — US-9, NFR Security; STRIDE-lite in the design |
| Simplifier | soft | no second store, no allocator, no new dependency, no config | met — US-2 source assertion, US-4, stdlib only; `next` literal is the one convenience, justified (the caller need not read the register first) |
| Author self-clear | — | none: the coordinator's Adversary-Mode join clears | open by design |
