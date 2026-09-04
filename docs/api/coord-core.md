---
id: api-coord-core
title: "API — coord-core.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  coord-core.py - agent coordination, Phase 1 walking skeleton.
---

# `coord-core.py`

*Generated from `pack/scripts/coord-core.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
coord-core.py - agent coordination, Phase 1 walking skeleton.

Holds the record of intent and answers "may this session touch this artifact?" from it.
Append-only JSONL, one file per session; every piece of state is a fold over it. No daemon,
no database, no dependency beyond the standard library (ADR-0007).

Four controls here were observed failing on the un-fixed shape before they were trusted:
  LOG-A     an append onto a file not ending in a newline fuses two records and loses BOTH
  R4        a check that scanned nothing must not report "free"
  CTRL-PORT os.open without O_BINARY translates newlines on Windows -- which also MASKED
            the LOG-A control, because a stray CR still terminates a line
  F8        a claim over the coordination record itself would lock the substrate

Design: docs/design/coord-core-phase1.md
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `add` | append an open seam request |
| `allocate` | one collision-proof identifier |
| `check` | may this session touch this path? |
| `claim` | declare intent over an artifact set |
| `class` | what class is this artifact? |
| `collaborate` | cross-session collaboration checks |
| `doctor` | is the driver effective? is the registry sane? |
| `guard` | refuse to move HEAD over work held in one place |
| `hook` | PreToolUse adapter: stdin JSON in, decision JSON out |
| `install` | write the pre-commit hook; print the settings entry |
| `list` | list seam requests |
| `merge-derived` | the .gitattributes merge driver (always 0) |
| `merge-register` | union two append-only registers (always 0) |
| `metrics` | the four measures this layer exists to move |
| `plugin` | emit the bundle both harnesses read; never installs |
| `precommit` | the universal floor: refuse unclaimed staged paths |
| `regen` | run the regenerations the driver deferred |
| `release` | drop a lease |
| `request` | record or resolve a seam request |
| `resolve` | resolve a seam request |
| `session` | one session per working tree |
| `tail` | the merged chronological stream |
| `worktree` | session worktree lifecycle: new | list | cleanup |

## CLI — options

| Option | Help |
|---|---|
| `--base` | commit/branch to branch from (default: current HEAD) |
| `--branch` | branch to create; name it for the WORK, not the session |
| `--contract` | _(no help text — coverage gap)_ |
| `--emit` | _(no help text — coverage gap)_ |
| `--fix` | push, the cheapest second copy |
| `--from-role` | _(no help text — coverage gap)_ |
| `--json` | _(no help text — coverage gap)_ |
| `--path` | _(no help text — coverage gap)_ |
| `--reason` | _(no help text — coverage gap)_ |
| `--register` | _(no help text — coverage gap)_ |
| `--remove` | cleanup: actually delete. Off by default - deletion is irreversible |
| `--resolution` | _(no help text — coverage gap)_ |
| `--scheme` | _(no help text — coverage gap)_ |
| `--session` | session id to register (default: $AGENT_SESSION) |
| `--status` | _(no help text — coverage gap)_ |
| `--timeout` | _(no help text — coverage gap)_ |
| `--to` | _(no help text — coverage gap)_ |
| `--ttl` | _(no help text — coverage gap)_ |
| `--wi` | _(no help text — coverage gap)_ |
| `-n` | _(no help text — coverage gap)_ |

## Types

### `CoordError`

_(no docstring — coverage gap)_

## Functions

### `repo_root(cwd)`

The PRIMARY checkout of this repository, from any worktree.

The record is per REPOSITORY, not per checkout. `--git-common-dir` is the primitive
that says so: from a linked worktree it returns the primary .git (absolute), and from
the primary checkout it returns a relative ".git". Its parent is the primary checkout
in both cases.

Found by running the Phase-1 demo: with the root defaulting to cwd/.agents, every
worktree got its own private record and two sessions could never see each other -
which is the exact criterion this phase exists to satisfy.

Read from the filesystem, NOT by shelling out to `git rev-parse --git-common-dir`.
The first implementation did shell out and cost ~35 ms of the check's budget - measured
at 82 ms p95, which met NFR-P1 but blew straight through ADR-0007's own 60 ms
compaction trigger. On the hot path of every edit, a subprocess is not free.

The layout this reads is git's own:
  primary checkout -> .git is a DIRECTORY; the repo root is its parent
  linked worktree  -> .git is a FILE holding "gitdir: <primary>/.git/worktrees/<name>"

### `resolve_root(cwd, raw)`

Resolve COORD_ROOT, refusing anything outside the repository.

COORD_ROOT is attacker-controllable input that selects which file becomes trusted
state (STRIDE B1, elevation of privilege). Found at the design gate, not in the draft.

### `overlaps(a, b)`

Do two path patterns intersect? Prefer a false positive: a false refusal costs a
message, a false grant costs a merge.

Compared by SEGMENT, not by string prefix, so src/Foo/** and src/FooBar/** are
correctly disjoint.

simplify: fnmatch both ways plus a segment-prefix test.
  ceiling: a wildcard in the middle of a pattern, and character classes.
  upgrade trigger: the first refusal a human calls wrong, or Phase 3's artifact-class
  registry introducing nested patterns.

### `make_event(kind, session, agent, wi, path, at, ttl=…, seq=…)`

**Coverage gap** — no docstring in the source.

### `append_event(root, event)`

Append one event as exactly one write() - atomic under O_APPEND (spike S3).

### `read_events(root)`

Return (events, errors, files_scanned).

Errors are collected, never raised - but a single error makes the whole check
not_checked. Fail safe, never open (NFR-R2).

### `fold(events, now)`

Pure fold: events -> live leases. Replaying is idempotent (NFR-R1).

derive-don't-store (DM7): `expires` is computed here (at + ttl) and never persisted.
Two stored definitions of one quantity is the defect signature.

### `check(root, path, me, now)`

**Coverage gap** — no docstring in the source.

### `render(decision)`

Four labelled lines, fixed order: what happened - who - why - what to do.

No colour is load-bearing: every state is distinguishable from the text and the exit
code alone. Accessibility and machine-readability are the same requirement here.
"refused" is never softened to "denied" or "unavailable" - the reader is a model that
must not read the outcome as a transient failure worth retrying.

### `append_decision(root, session, agent, path, decision)`

Record one enforcement decision. Never folded; read by `tail` and `metrics`.

G14: the verdict is computed BEFORE this is attempted and cannot be changed by it.
A refusal that cannot be recorded is still a refusal.

### `read_decisions(root)`

**Coverage gap** — no docstring in the source.

### `append_record(path, record)`

Append one JSONL row to a small operator ledger.

### `request_log_path(root)`

**Coverage gap** — no docstring in the source.

### `read_request_events(root)`

**Coverage gap** — no docstring in the source.

### `fold_requests(events)`

**Coverage gap** — no docstring in the source.

### `unique_commits(repo)`

Commits reachable from HEAD and from NO other ref. Returns (count, reason_code).

`--all` is FORBIDDEN in this expression. Spike S9 reproduced the recorded bug:
`git rev-list HEAD --not --all` returns 0 for a branch holding exactly one commit
that exists nowhere else, because --all implicitly includes HEAD -- so the expression
reduces to `HEAD --not HEAD` and reports SAFE for the one case the guard exists to
catch. `--exclude=<branch> --all` fails identically, because it does not exclude HEAD.

### `staged_paths(repo)`

Staged paths, NUL-separated. Returns (paths, error).

S8: `--cached` works before the first commit; appending HEAD is FATAL there, so HEAD
is never passed. The -z form is required - a path containing a space is otherwise
split, and one containing a quote is otherwise escaped.

### `entry_fingerprint(row)`

A stable identity for a register entry, EXCLUDING its id.

The id is deliberately excluded. In the recorded KG-B instance the two entries had the
SAME id and different content, and the register's own write-up names them by
`shortname` rather than by id because rebases had renumbered them three times. A
fingerprint keyed on the id would both miss the real loss and cry wolf on every
legitimate renumber.

`renumbered_from` is excluded for the same reason, and the conservation check found
that itself: it is provenance ABOUT a merge, not part of the entry's identity, and
including it made a renumbered entry look destroyed.

### `conservation_lost(ours, theirs, merged)`

Entries present on either side and absent from the merge. Empty means conserved.

Unique ids stop the COLLISION; only this stops the RESOLUTION from destroying an entry,
which is what actually happened. The recorded resolution reported "203 ours + 203 theirs
-> 203 unique" and was caught only because that arithmetic is impossible.

### `merge_register(ours, theirs, base=…)`

Union two append-only registers by fingerprint. Returns (merged, lost).

Append-only means the correct resolution is a union, never a pick. Order is preserved:
ours first, then whatever theirs adds.

When `base` is supplied, KG-B's own prescribed resolution also applies: *the id is a
sequence, not an identity.* The side that already published an id keeps it, and an
entry this merge INTRODUCES on a colliding id is renumbered from the allocator rather
than deduped away. NFR-C2 still holds -- nothing already in the base is ever rewritten,
and with no base the driver cannot tell who published first, so it conserves and does
not guess.

### `cmd_merge_register(result_path, base_path, theirs_path, real_path)`

The merge driver for `register`-class artifacts. ALWAYS exits 0 (the S12b rule).

### `load_registry(root)`

Parse `.agents/artifacts.yml` into [(pattern, class, command)].

simplify: a line-oriented parser for `pattern: class [command...]` plus `#` comments,
  NOT general YAML.
  ceiling: anchors, nesting, multi-line values.
  upgrade trigger: the first registry a human writes that this rejects.
Thirty lines against a dependency the pack does not have (NFR-P2) -- the
Gratuitous-Dependency gate holds at rung 5.

Raises CoordError; never returns a partly-parsed registry, because a half-read registry
would silently reclassify whatever it failed to read.

### `classify(root, path)`

(class, reason_code). Longest matching pattern wins; the default is `authored`.

Pattern: Null Object -- an unclassified path yields the SAFE class, so no call site
needs a branch for "unknown".

### `regen_command(root, path)`

**Coverage gap** — no docstring in the source.

### `record_regen_owed(root, path)`

**Coverage gap** — no docstring in the source.

### `regen_owed(root)`

**Coverage gap** — no docstring in the source.

### `clear_regen_owed(root, paths)`

**Coverage gap** — no docstring in the source.

### `parse_hook_request(event, repo)`

Normalise any harness's PreToolUse envelope to [(tool_name, repo_relative_path)].

A path of None means "this tool call carries no path" -- a shell command, a search, a
read. That is not the same as "no path found", and the difference decides whether the
layer has an opinion at all.

### `detect_harness(event)`

**Coverage gap** — no docstring in the source.

### `hook_decision_of(response)`

Read a decision back out of any harness's response envelope.

Used by the conformance suite so the assertion does not have to know which shape it is
looking at -- adding a harness means adding a fixture and a branch here, not rewriting
the tests.

### `hook_response_is_valid(response, harness)`

Does this response match the envelope that harness actually reads?

Copilot consumes the Claude plugin format, and the recorded corpus does not show the
response shape -- so both adapters emit the Claude envelope and this returns True for
both. That is a DELIBERATE, RECORDED assumption, not a verified fact: it is exactly
what a live Copilot deny would confirm or refute (H13).

### `hook_response(decision, reason)`

The PreToolUse envelope. ALWAYS printed, and the caller ALWAYS exits 0 - the
harness reads the decision in the JSON, not the exit code. Conflating them would make
a crashed hook indistinguishable from a refusal.

### `cmd_hook(root, session, agent, now, stdin_text, repo=…)`

G1: this must never raise. A hook that crashes on a bad payload blocks every edit.

Envelope-agnostic: `parse_hook_request` normalises whichever harness is calling. Copilot
BATCHES tool calls, so one invocation can carry several paths -- and if any of them is
refused the whole batch is refused. A false refusal costs a message; a false grant costs
a merge.

### `cmd_precommit(root, repo, session, agent, now)`

**Coverage gap** — no docstring in the source.

### `cmd_guard(repo, fix)`

**Coverage gap** — no docstring in the source.

### `active_sessions(root, now, stale_seconds=…)`

Fold the append-only record into active collaboration sessions.

The session ledger is evidence that someone announced themselves, not proof that nobody
else exists (DC-024). This fold therefore reports only positive liveness; callers that
need absence-of-use proof must also inspect the filesystem/worktree state.

### `session_contract_path(repo)`

**Coverage gap** — no docstring in the source.

### `contract_ownership(repo)`

Parse the simple ownership tables from the session contract template.

This is intentionally Markdown-shaped rather than a general Markdown parser: the pack
owns the template and the rows are `| Path | Why |` under `### <Role> owns`.
Unknown shapes simply yield no ownership facts; the contract remains human-readable.

### `infer_session_roles(session, agent, ownership)`

Infer contract role membership from session/agent labels.

This stays advisory. A false warning costs a message; a false grant is what creates
cross-owned edits. A later slice can replace this with explicit `COORD_ROLE`.

### `owner_rows_for_path(ownership, path)`

**Coverage gap** — no docstring in the source.

### `collaboration_findings(root, repo, now, snapshot=…)`

Return collaboration health findings.

This is a small operator gate over the live session fold. It is deliberately advisory:
it catches the AI-DE class where two sessions had to publish a contract and claim files
to avoid merge/rebase damage, but it does not pretend a claim is a distributed lock.

### `cmd_session_list(root, now, as_json=…)`

**Coverage gap** — no docstring in the source.

### `cmd_collaborate(root, repo, action, now, as_json=…)`

**Coverage gap** — no docstring in the source.

### `cmd_request(root, action, now, session, agent, args)`

**Coverage gap** — no docstring in the source.

### `worktree_inventory(repo)`

Parse `git worktree list --porcelain`. Returns (records, error).

Porcelain is used rather than the human format because a path containing a space is
otherwise unparseable - the same reasoning as staged_paths()'s -z form.

### `worktree_is_clean(path)`

True when there is nothing modified, staged OR UNTRACKED.

Untracked is the condition that matters most: a new file nobody has committed exists
nowhere else, so deleting its tree destroys the only copy. `git status --porcelain`
includes untracked by default and the -z form survives paths with spaces or quotes.

### `worktree_safety(record, primary, cwd, live_keys, index)`

WT7, in order, fail-safe. Returns (safe, reason).

Every condition is a HARD STOP that reports rather than removes. A cleanup that deletes
on a heuristic will eventually delete the tree that mattered, and that single event ends
the adoption of the whole practice.

### `cmd_worktree(root, repo, action, cwd, now, session=…, agent=…, branch=…, base=…, remove=…)`

**Coverage gap** — no docstring in the source.

### `cmd_session(root, action, session, agent, cwd, now)`

**Coverage gap** — no docstring in the source.

### `cmd_metrics(root, repo, as_json)`

**Coverage gap** — no docstring in the source.

### `cmd_install(repo, root)`

**Coverage gap** — no docstring in the source.

### `cmd_merge_derived(root, repo, result_path, base_path, theirs_path, real_path)`

The .gitattributes merge driver. ALWAYS returns 0 -- see _write_conflict.

Resolves a `derived` artifact to OURS and records that a regeneration is owed; anything
it cannot classify as derived gets conventional conflict markers instead.

### `cmd_regen(root, repo, timeout=…)`

Run the regenerations the driver deferred. Returns (exit_code, results).

A failed regeneration STAYS OWED and reports non-zero: a stale derived artifact looks
finished, which is worse than a conflict.

### `driver_status(repo)`

Is the merge driver EFFECTIVE? Requires reading BOTH sources (spike S13).

`git check-attr` reports the DECLARATION whether or not a driver exists, and
`git config` reports the registration without knowing what it covers. Only comparing
the two finds the gap -- and .git/config is per-clone and never committed, so a fresh
clone or a new worktree is exactly where the gap appears.

### `cmd_doctor(root, repo)`

**Coverage gap** — no docstring in the source.

### `cmd_plugin_emit(out_dir)`

Write the plugin bundle BOTH harnesses read. It never installs anything.

S14 established that Copilot CLI consumes the Claude plugin format verbatim --
`.claude-plugin/plugin.json` plus `hooks/hooks.json` with the same matcher/hooks shape
and the same ${CLAUDE_PLUGIN_ROOT} placeholder. One bundle therefore serves both, which
is what made NFR-C1 cheap.

STRIDE B9: this writes only where it is told and PRINTS what it wrote. It never edits
~/.copilot/settings.json or .claude/settings.json, because a layer that grants itself
tool permissions is the elevation it exists to prevent -- the same rule `install`
follows by printing the settings entry rather than writing it.

## Coverage

- Public functions: **56** · documented: **33** (**59%**)
- Undocumented (recorded, not invented): `make_event`, `check`, `read_decisions`, `request_log_path`, `read_request_events`, `fold_requests`, `regen_command`, `record_regen_owed`, `regen_owed`, `clear_regen_owed`, `detect_harness`, `cmd_precommit`, `cmd_guard`, `session_contract_path`, `owner_rows_for_path`, `cmd_session_list`, `cmd_collaborate`, `cmd_request`, `cmd_worktree`, `cmd_session`, `cmd_metrics`, `cmd_install`, `cmd_doctor`

