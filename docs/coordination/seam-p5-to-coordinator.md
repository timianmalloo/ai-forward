---
id: seam-p5-to-coordinator
title: "Seam P5 → coordinator: the `decide` front door, the two skills' contract sentences, the register line, the INSTALL delta, the doctrine sentence"
type: doc
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, seam, owner-review, p5, decide, rulings]
links:
  - { to: design-owner-review, rel: relates-to }
  - { to: spec-owner-review, rel: relates-to }
review-by: "2026-12-19"
review-suggested: []
summary: >-
  What track P5 needs in files it does not own, delivered as text for the coordinator to apply at
  the landing: one parser block and one delegation branch in coord-core.py; verbatim contract
  sentences with insertion points for execute-with-coordination and prepare-for-coordination
  (land with P8 unless P8 is struck); the .agents/artifacts.yml register line for
  docs/notes/rulings.md; the INSTALL.md delta paragraph; one doctrine sentence for CO16.
---

# Seam P5 → coordinator

Applied by the coordinator at P5's join (plan `coordination-p3-p5-p8`, "Seams"). Everything below is verbatim text plus its insertion point; nothing here was written into the target files by P5.

## (a) `pack/scripts/coord-core.py` — the `decide` front door

**Parser** — insert directly after the `board` parser (today `coord-core.py:1220-1221`, the two lines `bd = sub.add_parser("board", …)` / `bd.add_argument("board_args", …)`):

```python
    dc = sub.add_parser("decide", help="request | rule <n|next> | list (delegates to coord-decide.py)")
    dc.add_argument("decide_args", nargs=argparse.REMAINDER)
```

**Delegation** — replace the `mail`/`board` branch in `main()` (today `coord-core.py:3698-3704`, the block starting `if args.cmd in ("mail", "board"):`) with:

```python
    if args.cmd in ("mail", "board", "decide"):
        script = {"mail": "coord-mail.py", "board": "coord-board.py", "decide": "coord-decide.py"}[args.cmd]
        target = os.path.join(_HERE, script)
        passthrough = getattr(args, args.cmd + "_args")
        if not os.path.isfile(target):
            print("COORD-NOT-CHECKED  {} is not beside coord-core.py; the message layer is not installed here".format(os.path.basename(target)))
            return 4
        completed = subprocess.run([sys.executable, target, *passthrough], encoding="utf-8", errors="replace")
        return completed.returncode
```

The comment above that block ("BEFORE the identity gate … the delegate scripts own their identity rules") holds for `decide` too: `list` is a read; `request`/`rule` read `AGENT_SESSION` themselves (`COORD-DECIDE-IDENTITY`, exit 4). Also update the `help` string at `coord-core.py:1218` if it enumerates the delegates, and `HARNESS_STATUS` (`coord-core.py:1846`) if the coordinator wants the stop-hook status mirrored from the README table: claude/grok/copilot `observed-only`, agy `unsupported`.

**Test to add when the door is in** (owned by the coordinator, in `tests/docs_explorer/test_coord_core.py` or a new file): `coord-core.py decide list` in a temp repo exits 0 and prints `NOT CHECKED` twice; `coord-core.py decide` with no delegate script present exits 4.

## (b) Contract sentences for the two coordination skills (land with P8 unless P8 is struck)

**`pack/commands/execute-with-coordination/SKILL.md`** — two insertions.

1. In **Stage 5 — Coordinate: the loop, with its termination variant** (`SKILL.md:67`), append as the last bullet of that stage's list:

   > - **Owner review is a ruling, never an acceptance (D6, CO1).** When a track raises a decision request (`coord decide request` — the five fields, a deadline and a fallback, P1's request plus a `decision-request` mail), the Owner seat answers it with `coord decide rule next --title "…" --text "…" --request <req-id>`: the next numbered heading is appended to `docs/notes/rulings.md`, the request is resolved with `Ruling NN`, and the requester is mailed. The requester never rules on its own request (`COORD-RULING-SELF`). A track's `Stop` is refused by `owner-review-gate.py` while a decision request it sent is open — that refusal is the loop's signal, not an error to work around; `coord decide list` shows what is open and what was ruled (`NOT CHECKED` over an empty corpus).

2. In **Stage 6 — Converge** (`SKILL.md:75`), directly after the sentence that ends "**The join is the script and nothing else:**" and its list, add:

   > Before the join, `python3 docs/ai-forward-pack/scripts/verify-ruling-citations.py` is green: a `Ruling NN` cited anywhere under `docs/`, `pack/`, `.agents/log/`, `.github/`, `.claude/` with no heading in `docs/notes/rulings.md`, or a number defined twice, blocks the join (class ID-A).

**`pack/commands/prepare-for-coordination/SKILL.md`** — one insertion, in **Stage 7 — Assign** (`SKILL.md:58`), directly after the sentence "Before dispatch, refuse a compiled prompt whose `dispatchable` is false or whose text still carries an unanswered `DR-n` line — stop with `decision request unanswered: DR-n` (CO-S0).":

> Every track row names **who rules**: the Owner session a track's `coord decide request --to <owner-session>` addresses, and the register it rules into (`docs/notes/rulings.md`, class `register`). A plan whose tracks can raise a decision request but name no Owner session has no termination variant for that request (D5, D6).

Both skills' frontmatter already carries `runs_as`; `verify-skill-contracts.py` needs no new rule for these sentences (they add no fan-out, no dispatch, no hard stop). Copilot prompt mirrors are synced by the coordinator as with P8's other text.

## (c) `.agents/artifacts.yml` — the register line

Below the managed block's end marker (`# <<< coord classify init - end managed block. Add your own entries BELOW.`), with this repo's own entries:

```yaml
docs/notes/rulings.md: register
```

Rationale: the file is append-only and merges by union like `docs/audit/audit-log.jsonl`; a lease on it would block every join that must append a ruling (DC-163). `verify-ruling-citations.py` is the belt that catches a union that produced two headings for one number.

## (d) `pack/adapters/INSTALL.md` — delta paragraph (frontmatter entry + body)

Frontmatter `changes` entry (the coordinator sets the revision):

```yaml
  - { type: added, area: coordination, paths: ['scripts/coord-decide.py', 'scripts/verify-ruling-citations.py', 'adapters/hooks/owner-review-gate.py', 'adapters/hooks/README.md', 'adapters/hooks/claude-code.settings.hooks.json', 'adapters/hooks/grok.ai-forward-hooks.json', 'adapters/hooks/copilot.ai-forward-hooks.json', 'tests/docs_explorer/test_coord_decide.py', 'tests/docs_explorer/test_verify_ruling_citations.py'], deploy: 'copy the two new scripts to docs/ai-forward-pack/scripts/ and the new hook to docs/ai-forward-pack/hooks/ ; merge the Stop/SubagentStop (Claude Code), Stop (Grok) and agentStop (Copilot) entries from the hook adapters into each host config ; add `docs/notes/rulings.md: register` to .agents/artifacts.yml (the register is created by the first `coord decide rule`, or commit an empty one with the V2 frontmatter the script writes) ; run verify-ruling-citations.py once — a repository whose prose already cites ruling numbers must define them or rewrite the mentions.', summary: 'COORDINATION P5 (owner review, D6). coord decide request writes P1''s typed request with reason decision-request and the five decision fields as a JSON contract, plus a decision-request mail; coord decide rule <n|next> appends `### Ruling NN — <title>` to docs/notes/rulings.md (the only definition site; numbering read from the headings, class ID-A), resolves the request with Ruling NN and mails the requester; the requester cannot rule on its own request. verify-ruling-citations.py (absorbed from ai-de) fails a cited number with no heading and a number defined twice, with a self-test. owner-review-gate.py refuses a session''s Stop (exit 2, reason on stderr; Copilot decision:block) while a decision request it sent is open and exits 0 on every path it cannot evaluate. Red first: 43 failures on the un-implemented tree, then 35 tests green.' }
```

Body paragraph (beside the session-start and doorbell paragraphs):

> **Owner review (P5, D6).** `coord decide request|rule|list` gives the Owner seat its mechanism over the stores that already exist: a decision request is P1's typed seam request (`reason: decision-request`, the five decision fields as a JSON `contract`, deadline and fallback mandatory) dual-written as a `decision-request` mail; a ruling is the next `### Ruling NN — <title>` heading appended to `docs/notes/rulings.md` — the only definition site and the only allocator — which resolves the request and mails the requester. `verify-ruling-citations.py` fails a number cited in prose with no heading, or defined twice. `adapters/hooks/owner-review-gate.py` runs at the stop seam (Claude Code `Stop`/`SubagentStop`, Grok `Stop`, Copilot `agentStop`; Antigravity unsupported) and refuses a stop only while the stopping session holds an unresolved decision request it sent, exiting 0 on every path it cannot evaluate. Per-host status is in `adapters/hooks/README.md` — `observed-only` until a live stop is seen refused.

## (e) `pack/knowledge/agent-coordination.md` — one doctrine sentence

In **CO16 — Protocol objects**, replace the fragment `**decision request / ruling** (`decide request` / `rule <n>` → a numbered ruling)` with:

> **decision request / ruling** (`decide request` — P1's typed request carrying options, evidence, recommendation, reversibility and blast radius plus deadline and fallback, dual-written as a `decision-request` mail; `decide rule <n|next>` → the next `### Ruling NN — <title>` heading in `docs/notes/rulings.md`, the only definition site, which resolves the request and mails the requester; `verify-ruling-citations.py` fails a cited number with no heading or a number defined twice; `owner-review-gate.py` refuses a session's stop while a decision request it sent is open)

## Findings outside P5's row (not acted on)
- `coord-core.py` `HARNESS_STATUS` has no row for stop-class hooks; the README table carries it until the coordinator or P3 mirrors it.
- The plan's second gate clause (exit evidence named by the plan row that the audit entry does not carry) is unbuilt: it needs a machine-readable exit-evidence list in the plan schema and a matching audit-entry field. The gate exits 0 on it (fail-safe).
- The gate does not refuse an *Owner's* stop while requests addressed to it are open — out of the fixed contract; a one-line extension (`to == session`) once the doctrine says an Owner may not stop with rulings pending.
- `tests/docs_explorer/test_coord_derived.py`: three failures (`Q6_driver_runs_under_rebase`, `register_class_gets_the_conservation_driver_end_to_end`, `Q10_unregistered_driver_degrades`) are pre-existing on the base commit — XP's row (default branch `main` vs `master`).
- pytest's unittest bridge in this environment reported a test whose only assertions sit inside `subTest` as PASSED against a missing script (red-first run, `test_coord_decide.py`). The new tests use no `subTest`; other suites that do (`34 subtests passed` in the coordination set) deserve a sweep — class candidate for `defect-classes.md` (TEST-*), owned by the coordinator.
