---
id: api-audit-log
title: "API — audit-log.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  audit-log.py — the AI-Forward Pack audit & change log bundle (audit-and-change-log.md).
---

# `audit-log.py`

*Generated from `pack/scripts/audit-log.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
audit-log.py — the AI-Forward Pack audit & change log bundle (audit-and-change-log.md).

Durable, committed, history-as-knowledge for a repo: an append-only record of every
meaningful prompt / skill / script / decision, so any future Copilot or Claude Code
session reads the project's own history instead of starting blind. The canonical logs
are append-only JSONL (clean git diffs, like docs/health-history.jsonl); the viewer
reads a derived window.AUDIT_DATA JS (loadable over file://, like docs/docs-index.js).
Python 3.8+, stdlib only — no dependencies.

Two logs, one bundle:
  docs/audit/audit-log.jsonl    every action (shortname, datetime, session, prompt, summary, …)
  docs/audit/change-log.jsonl   the meaningful design changes / decisions (+ git before/after)
  docs/audit/audit-data.js      derived window.AUDIT_DATA = {audit:[…], changes:[…]} (the viewer's data)
  docs/audit/index.html         the interactive viewer (self-bootstrapped from the template)

Subcommands
  append      Add an audit entry.            (Audit Mandate — every skill's last action)
  change      Add a change-log entry.        (Change Mandate — collectknowledge/define-architecture/design-slice/migrate)
  list        Show the last N entries (audit|change). For the CLI skill.
  search      Filter by --session / --since / --until / --keyword. For the CLI skill.
  get         Print one entry by --id (use --field prompt to extract the prompt to re-run).
  render      Regenerate audit-data.js from the JSONL and ensure the viewer exists (repair).
  git-context Print the current git {sha, short, branch, pushed} as JSON (a helper).
  verify      Fail when any log line is unreadable — the system of record must never lose
              an entry silently (FR-052). CI-able.
  suggest     Discern unlogged meaningful changes (recent commits + new ADRs/notes not in the change log).
  import      Ingest a session-export JSON array of turns into the audit log (build on session history).

Conventions
  --root defaults to docs/. The audit dir is <root>/audit. The viewer template is resolved
  relative to this script (pack/templates or docs/ai-forward-pack/templates). git is optional —
  every git call degrades gracefully when git or a repo is absent. This tool never invents a
  prompt or a summary; required fields must be supplied (flags, --*-file, or --from-json -).
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `append` | add an audit entry |
| `change` | add a change-log entry |
| `get` | print one entry by id |
| `git-context` | print current git context as JSON |
| `import` | ingest a session-export JSON array into the audit log |
| `list` | show the last N entries |
| `render` | regenerate audit-data.js and ensure the viewer exists |
| `search` | filter by session/datetime/keyword |
| `selfcheck` | bounded inline session self-assessment (FC-1): goal-state presence gaps + scope review for a session |
| `start` | record this run's start stamp (call at grounding) so the closing `append` records duration automatically (IO1) |
| `suggest` | surface meaningful changes not yet in the change log |
| `verify` | fail if any log line is unreadable (FR-052; CI-able) |
| `yield` | persona yield: findings raised vs accepted (P6) |

## CLI — options

| Option | Help |
|---|---|
| `--actor` | _(no help text — coverage gap)_ |
| `--agent-run` | one sub-agent run as '<agent>|<start-iso>|<end-iso>'; repeatable. Records agent_runs + a parallelism block (agent_seconds, span_seconds, speedup, peak_concurrency) so fan-out is MEASURED, not asserted (P8). Summed duration cannot tell serial from parallel; the union of the intervals can. |
| `--artifact` | _(no help text — coverage gap)_ |
| `--audit-ref` | _(no help text — coverage gap)_ |
| `--change` | link to a change-log id (cl-NNNN) |
| `--datetime` | _(no help text — coverage gap)_ |
| `--done-when` | the terminal condition (front matter CT19); the PACK-O presence signal /dream mines (AL5b) |
| `--field` | print just this field (e.g. prompt) |
| `--file` | JSON file (or - for stdin) |
| `--from-json` | read fields from a JSON object (path or - for stdin) |
| `--git-before` | HEAD sha captured before the work began |
| `--git` | capture current git context |
| `--goal` | the turn's goal (front matter CT19) |
| `--id` | _(no help text — coverage gap)_ |
| `--json` | _(no help text — coverage gap)_ |
| `--keyword` | _(no help text — coverage gap)_ |
| `--kind` | _(no help text — coverage gap)_ |
| `--n` | _(no help text — coverage gap)_ |
| `--outcome` | _(no help text — coverage gap)_ |
| `--persona-yield` | one persona's findings raised vs accepted; repeatable. Makes the roster tunable on measured yield rather than belief (P6) — an advisory lens re-convenes only on an accepted finding. |
| `--project` | project name for the viewer (default: repo dir name) |
| `--prompt-file` | _(no help text — coverage gap)_ |
| `--prompt` | _(no help text — coverage gap)_ |
| `--rationale` | _(no help text — coverage gap)_ |
| `--root` | docs root (default: docs); audit dir is <root>/audit |
| `--session` | _(no help text — coverage gap)_ |
| `--shortname` | _(no help text — coverage gap)_ |
| `--signal-acceptance-met` | signal: the done_when acceptance criterion was met |
| `--signal-regression` | signal: a known regression was introduced (a claim, so emit only when checked) |
| `--signal-verification-executed` | signal: the verification (red-observed) was actually executed |
| `--signal-verification-path` | signal: a committed Proof Pack / verification path exists (watcher AL2a) |
| `--since` | _(no help text — coverage gap)_ |
| `--skill` | _(no help text — coverage gap)_ |
| `--started` | ISO-8601 UTC start stamp captured at grounding; records started_at + duration_seconds so elapsed time is MEASURED, not modeled (instrumentation over inference, IO1) |
| `--summary-file` | _(no help text — coverage gap)_ |
| `--summary` | _(no help text — coverage gap)_ |
| `--supersedes` | _(no help text — coverage gap)_ |
| `--tag` | _(no help text — coverage gap)_ |
| `--title` | _(no help text — coverage gap)_ |
| `--tool` | _(no help text — coverage gap)_ |
| `--until` | _(no help text — coverage gap)_ |

## Functions

### `now_iso()`

**Coverage gap** — no docstring in the source.

### `parse_iso(s)`

Parse an ISO-8601 UTC stamp. Returns None on anything unparseable -- an unusable
--started value must degrade to 'no duration recorded', never to a wrong duration.

### `duration_fields(started, ended_iso)`

Instrumentation over inference: when a start stamp is supplied, RECORD the elapsed
seconds rather than leaving a future reader to model it. Returns {} when the start is
absent or unparseable, and refuses a negative duration (clock skew) rather than
emitting a number that is precise and wrong.

### `parse_agent_run(spec)`

'<agent>|<start-iso>|<end-iso>' -> a span dict, or None when unusable.

Degrades to None on anything unparseable or time-reversed, never to a plausible wrong
span (IO8) -- a fabricated interval would corrupt the very measurement it exists for.

### `parallelism_fields(runs)`

Union-of-intervals wall clock vs summed run time, from a list of parse_agent_run spans.

Returns {} when no usable span is present -- "not recorded" rather than a speedup of 1.0
that a reader would mistake for a measurement of serial execution.

### `parse_persona_yield(spec)`

'<persona>|<raised>|<accepted>' -> a yield record, or None when unusable.

Refuses accepted > raised and negative counts: a row that cannot be true would corrupt
every ratio derived from it, and a corrupt ratio is worse than a missing one (IO8).

### `aggregate_persona_yield(entries)`

Roll persona_yield records up across audit entries.

`acceptance` is None when nothing was raised: 0/0 is an absence of evidence, not a
measured 0% -- reporting 0.0 would read as a verdict on a persona never actually asked.

### `should_reconvene(stats, advisory=…)`

Should this persona be convened AGAIN on the same work? (P6)

Advisory lenses re-convene on evidence: a repeat run has to be earned by a finding that
was actually accepted. Hard-veto lenses are never yield-gated -- a veto exists to be
able to say no, and gating it on past productivity would silence precisely the review
that has been quiet because the work was clean.

A persona with no history always gets its first run; the rule gates repeats, not entry.

### `record_start(root, session, stamp=…)`

**Coverage gap** — no docstring in the source.

### `consume_start(root, session)`

Return the recorded start for this session and clear it, so one marker measures one
run. Returns None when there is none -- which degrades to no duration (IO8).

### `audit_dir(root)`

**Coverage gap** — no docstring in the source.

### `log_path(root, which)`

**Coverage gap** — no docstring in the source.

### `read_log(root, which, warn=…)`

**Coverage gap** — no docstring in the source.

### `append_log(root, which, entry)`

**Coverage gap** — no docstring in the source.

### `next_id(entries, prefix, allocator=…)`

Mint the next identifier. EXPAND step of expand-migrate-contract (ADR-0008).

This function was literally the KG-B shape: max(existing) + 1 over the LOCAL file only.
Two branches minting before either has pushed cannot see each other, so the collision is
structural -- nine recorded occurrences, twice reaching main, once destroying an entry
when the conflict was resolved by deduping on the id.

The sequential path is RETAINED, not deleted: every existing al-NNNN keeps its value,
there is no backfill (so nothing is guessed), and COORD_LEGACY_IDS=1 restores the old
scheme entirely. Removing it is the CONTRACT step and is a later decision.

### `git(args, root)`

**Coverage gap** — no docstring in the source.

### `git_context(root)`

**Coverage gap** — no docstring in the source.

### `commits_between(before, after, root)`

**Coverage gap** — no docstring in the source.

### `ensure_hub(adir)`

AL7 requires the bundle be registered in the knowledge graph through a hub artifact.
Nothing created it: a fresh install produced audit-data.js, audit-log.jsonl and
index.html but no .md, so the bundle was invisible to the graph. Bootstrapped here
alongside the viewer (AL11) because the same trigger applies - if it is missing, make it.

Links are deliberately EMPTY: a fresh install has no other artifact to point at, and a
dangling link fails `docs-graph.py validate` outright. An INBOUND link (from the UI guide
hub, or the first skill-authored artifact) clears the orphan check - verified by execution.

### `find_template()`

**Coverage gap** — no docstring in the source.

### `project_name(root)`

**Coverage gap** — no docstring in the source.

### `render(root, project=…)`

Regenerate audit-data.js and the managed viewer from canonical sources.

### `cmd_start(args)`

Instrumentation over inference (IO1): called as a skill's FIRST action (grounding). It
persists the run's start stamp keyed by session, so the closing `append` records
duration_seconds automatically -- no flag to remember, no variable to thread through.
That is what makes the measurement default-on rather than opt-in.

### `cmd_append(args)`

**Coverage gap** — no docstring in the source.

### `cmd_change(args)`

**Coverage gap** — no docstring in the source.

### `cmd_list(args)`

**Coverage gap** — no docstring in the source.

### `cmd_search(args)`

**Coverage gap** — no docstring in the source.

### `cmd_get(args)`

**Coverage gap** — no docstring in the source.

### `cmd_render(args)`

**Coverage gap** — no docstring in the source.

### `cmd_git_context(args)`

**Coverage gap** — no docstring in the source.

### `cmd_yield(args)`

Persona yield across the log: what each lens raised, and what actually landed (P6).

This is the report the roster is tuned from. It never issues a verdict on a persona --
it reports the ratio and marks the ones with no evidence either way, because "never
raised anything" and "raised things nobody took" are different facts with different
responses.

### `cmd_verify(args)`

FR-052. Assert the system of record is fully readable.

`read_log` deliberately survives a malformed line so the tooling keeps working — but a
line that is silently dropped is a line /dream will never see, and the consolidation
would report success over an incomplete corpus. This makes the skip COUNTABLE and
therefore gateable: exit 1 while any line is unreadable, naming file and line number.

### `cmd_suggest(args)`

Advisory: surface meaningful changes that may not be in the change log yet.

### `cmd_selfcheck(args)`

Bounded inline session self-assessment (FC-1, spec-agent-focus-controls). One deterministic
pass over a session's substantive turns -> goal-state presence gaps + done_when->summary review
pairs. Advisory and never a scope verdict (the agent/human judges drift); no network, no model,
no second pass. This is the rung-2 mechanical aid to the CT25 closing self-assessment.

### `cmd_import(args)`

Ingest a session-export JSON array of turns into the audit log (build on session history).

## Coverage

- Public functions: **35** · documented: **17** (**49%**)
- Undocumented (recorded, not invented): `now_iso`, `record_start`, `audit_dir`, `log_path`, `read_log`, `append_log`, `git`, `git_context`, `commits_between`, `find_template`, `project_name`, `cmd_append`, `cmd_change`, `cmd_list`, `cmd_search`, `cmd_get`, `cmd_render`, `cmd_git_context`

