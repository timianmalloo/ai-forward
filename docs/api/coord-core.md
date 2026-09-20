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
| `ack` | acknowledge, pinned to the blob you read |
| `add` | send a seam request; refused without a deadline and a fallback (its termination variant) |
| `allocate` | one collision-proof identifier |
| `board` | board [--follow] | board post (delegates to coord-board.py) |
| `check` | may this session touch this path? |
| `claim` | declare intent over an artifact set |
| `class` | what class is this artifact? |
| `classify` | write the artifact registry from what this repo has |
| `collaborate` | cross-session collaboration checks |
| `decide` | request | rule <n|next> | list (delegates to coord-decide.py) |
| `doctor` | is the driver effective? is the registry sane? |
| `expire` | past the deadline: record the fallback as the outcome - every open one, or <id> |
| `guard` | refuse to move HEAD over work held in one place |
| `hook` | PreToolUse adapter: stdin JSON in, decision JSON out |
| `install` | write the pre-commit hook; print the settings entry |
| `kick` | _(no help text — coverage gap)_ |
| `leader` | _(no help text — coverage gap)_ |
| `list` | list seam requests |
| `log` | ledger maintenance: `portable <file>...` rewrites the worktree field of existing rows to its label (F-3) |
| `mail` | send | read | ack | dispatch (delegates to coord-mail.py) |
| `merge-derived` | the .gitattributes merge driver (always 0) |
| `merge-register` | union two append-only registers (always 0) |
| `metrics` | the four measures this layer exists to move |
| `plugin` | emit the bundle both harnesses read; never installs |
| `precommit` | the universal floor: refuse unclaimed staged paths |
| `receive` | the addressee has seen it |
| `regen` | run the regenerations the driver deferred |
| `release` | drop a lease |
| `renew` | extend the holder's designation (holder only) |
| `request` | a typed seam request: add | receive | ack | resolve | expire | list (sent -> received -> acked -> resolved | expired) |
| `resolve` | resolve a seam request |
| `session` | one session per working tree; `heartbeat` samples progress |
| `tail` | the merged chronological stream |
| `track` | the running track: one state per (session, work item) from heartbeats and worktree mtimes - live | stalled | blocked | done; empty corpus is NOT CHECKED |
| `who` | who leads, as of which epoch, until when |
| `worktree` | session worktree lifecycle: new | list | cleanup |

## CLI — options

| Option | Help |
|---|---|
| `--base` | commit/branch to branch from (default: the INVOKING tree's HEAD) |
| `--blob` | the blob sha the request was written against |
| `--branch` | branch to create; name it for the WORK, not the session |
| `--calls` | heartbeat: tool calls this tick adds |
| `--contract` | _(no help text — coverage gap)_ |
| `--deadline-at` | the work item's deadline from the plan row; when passed, a kick is due even on a live track |
| `--deadline` | _(no help text — coverage gap)_ |
| `--emit` | _(no help text — coverage gap)_ |
| `--event` | heartbeat: the host event that fired |
| `--except` | carve this path out of the lease (repeatable): a directory lease that excludes a peer's owned files (class CTX-R) |
| `--fallback` | rung 2: what the kicker does at the deadline; required |
| `--file` | heartbeat: a file touched (counted, never stored) |
| `--fix` | push, the cheapest second copy |
| `--flush` | _(no help text — coverage gap)_ |
| `--force` | install from a linked worktree anyway. It overwrites the repository's shared registration with a path that dies with this tree - the recorded exception, never the default |
| `--from-role` | _(no help text — coverage gap)_ |
| `--host` | heartbeat: harness name (default $AGENT_HOST) |
| `--include-unmerged` | cleanup: also remove a clean tree whose branch has commits NOT on the default branch (a pushed but unmerged branch is HELD by default - DC-142). The count is printed either way. |
| `--json` | _(no help text — coverage gap)_ |
| `--long-edit` | the recorded reason for a --ttl above the cap; it is written into the claim event so a queued peer can read why it waits |
| `--owner` | rung 2: the Owner session (default: the live leader) |
| `--path` | _(no help text — coverage gap)_ |
| `--reason` | appended to the mail body |
| `--reclaim` | the same path as `reclaim`: over an EXPIRED designation, after the quiet period |
| `--ref` | a mail id (coord mail) this request answers |
| `--register` | _(no help text — coverage gap)_ |
| `--remove` | cleanup: actually delete. Off by default - deletion is irreversible |
| `--resolution` | _(no help text — coverage gap)_ |
| `--rung` | default: 0 for a blocked track not yet notified, else 1 |
| `--scheme` | _(no help text — coverage gap)_ |
| `--session` | session id to register (default: $AGENT_SESSION) |
| `--status` | open = every non-terminal state (default) |
| `--timeout` | _(no help text — coverage gap)_ |
| `--to` | _(no help text — coverage gap)_ |
| `--tokens` | heartbeat: tokens, when the host knows |
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

### `checkout_top(cwd)`

The top of the CURRENT checkout - primary or linked worktree - i.e. the first ancestor
holding a `.git` entry (a directory or a worktree's pointer file).

`repo_root` answers "which repository" and is right for the `.agents` stores and shared
refs. Three questions in main() are "which tree": the base a hook's absolute path is made
relative to, the index the pre-commit floor reads, and the file whose blob a request's ack
is compared with. Asked of the primary from a worktree they answered about the wrong
tree - the hook could not match a worktree path to its lease (a false grant), `coord
precommit` run by hand read the primary's index, and a stale-ack check read the primary's
file (class WT-A). Filesystem only, like repo_root.

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

### `excepted(lease, path)`

Is `path` carved out of this lease by its `except` list (claim --except, class CTX-R)?

### `lease_covers(lease, path)`

Does a live lease cover this path? A directory lease minus the peer's named files.

### `make_event(kind, session, agent, wi, path, at, ttl=…, seq=…, excepts=…)`

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

Pure fold: request-* rows -> one state per request id (spec-typed-seam-requests).

sent -> received -> acked -> resolved | expired. Terminal wins: a row of a later kind after
a terminal state is ignored (the CLI refuses to write one; the fold does not rely on that).
An add with no deadline_at predates the typed shape and folds to `untyped` - listed, never
expired, never failed (US-10).

### `blob_sha(data)`

git's blob id: sha1("blob <len> " + bytes). Spiked against `git hash-object`.

### `current_blob(repo, path)`

The blob id of repo/path now, in-process; None (rendered `not recorded`) when there is
no path, the path escapes the repository (STRIDE: a crafted --path reads nothing outside
it), or the file cannot be read.

### `annotate_requests(requests, repo, now)`

Derived fields, never stored (DM7): overdue, deadline_in, stale.

stale is True/False only when an ack pinned a blob AND the cited path can be hashed now;
otherwise the string "not recorded" - an absent comparison never renders as "fresh".

### `request_doctor_lines(root, repo, now)`

(lines, problems) for `coord doctor` and pack-doctor's `requests` check.

FAIL  a typed request past its deadline with no recorded outcome (silence - the 28%)
WARN  an ack pinned to a blob that has since changed; untyped rows (counted, never failed)
An absent store is `not recorded`, never "0 problems" (R4).

### `request_metrics(root, repo, now)`

Three counts, or `not recorded` over nothing - a rate over an empty corpus is not a
measurement (R4/PACK-P).

### `lease_overlap_lines(root, now)`

(lines, warns): two live leases from two sessions that cover each other's path and
neither excepts the other (class CTX-R's detector). A WARN never changes doctor's exit.

### `leader_validate(record)`

The blob's contract; anything else is NOT CHECKED, never a leader and never absent.

### `leader_read(repo)`

(record, oid, err). (None, None, None) is ABSENT - a read that succeeded and found no
ref. Every failure is err - rendered NOT CHECKED, never "absent" (R4).

### `leader_state(record, now)`

absent | live | expired | released - derived on every read, never stored (DM7).

### `leader_decide(action, record, now, me, target, ttl, host=…, tree=…)`

Pure: (new_record, None) or (None, refusal). Touches neither git nor the clock.

The invariant it holds (with the CAS in leader_write): at most one live designation, and
the epoch advances by exactly one on every change of holder - never on a renew.

### `leader_write(repo, record, old_oid)`

hash-object then `update-ref <ref> <new> <old>`: the ONLY writer, and the CAS.

No `-d`, no `--force`, no `--force-with-lease` anywhere in this file (SPK-2: `--force`
silently overrides the lease); a test walks every git argv here to keep it so.

### `leader_metrics(events)`

The three measures P2 exists to move (proposal §7, P2). R4: an empty corpus is a
reason, never a zero.

### `leader_doctor_line(repo, now)`

(line, is_problem) for `coord doctor`: the holder, the epoch, the time left - or
NOT CHECKED, which counts as a problem because a fence cannot run over it.

### `cmd_leader(root, repo, action, args, session, agent, cwd, now)`

**Coverage gap** — no docstring in the source.

### `unique_commits(repo)`

Commits reachable from HEAD and from NO other ref. Returns (count, reason_code).

`--all` is FORBIDDEN in this expression. Spike S9 reproduced the recorded bug:
`git rev-list HEAD --not --all` returns 0 for a branch holding exactly one commit
that exists nowhere else, because --all implicitly includes HEAD -- so the expression
reduces to `HEAD --not HEAD` and reports SAFE for the one case the guard exists to
catch. `--exclude=<branch> --all` fails identically, because it does not exclude HEAD.

### `default_branch(repo)`

The repository's DEFAULT branch, resolved rather than assumed. Returns (name, None)
or (None, reason_code).

The ladder: `refs/remotes/origin/HEAD` (what a clone records) -> a local branch of that
name -> the remote-tracking ref of that name -> `main` -> `master`. Nothing is guessed:
a repository that resolves none of these reports COORD-NO-DEFAULT-BRANCH and the caller
HOLDS, because "merged" cannot be established against a branch nobody named (WT7).

### `commits_ahead_of_default(repo, branch)`

`git rev-list --count <default>..<branch>` -- the ONLY meaning of "merged" this tool
uses. Returns (count, default_name, None) or (None, default_name, reason_code).

DC-142 (recurrence 2, measured 2026-09-13): the old label was derived from
unique_commits(), whose question is "does every commit exist SOMEWHERE else?" A pushed
branch answers yes -- every commit is on its remote-tracking ref -- so a frozen tree 21
commits ahead of main was printed as `clean, merged, unheld` and would have been deleted
by --remove. "Merged" here means merged into the DEFAULT branch, and the count is printed
so a reader never has to take the word on trust (IO2).

### `staged_paths(repo)`

Staged paths, NUL-separated. Returns (paths, error).

S8: `--cached` works before the first commit; appending HEAD is FATAL there, so HEAD
is never passed. The -z form is required - a path containing a space is otherwise
split, and one containing a quote is otherwise escaped.

### `session_id_error(session)`

Why `session` may not become a file name, or None when it may (seam XP -> P3, PLAT-A).

The id is interpolated into `.agents/log/<session>.jsonl` by append_event and
append_decision, so `:` is a name NTFS refuses, `/` and `\` change the directory, `..`
escapes it, and a character outside `[A-Za-z0-9._-]` is a portability bet. The rule
REFUSES; it never rewrites, because two ids that differ only in a stripped character
would silently share one log file.

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

### `resolve_interpreter(command)`

Map a registry command's leading interpreter TOKEN to this machine's interpreter.

`python3` (the documented POSIX name) and `python` (the python.org Windows name) are
resolved to `sys.executable`, quoted, so the same tracked registry line runs on both
operating systems. Anything else -- another tool, or an explicit interpreter path -- is
returned unchanged ON PURPOSE: a stale absolute path must fail loudly where it runs,
not be silently repaired here while `pack-doctor` reports it (class PLAT-B). Mirrors
`conductor-join._interp`, which does the same for argv lists; this one takes the shell
string the registry stores.

### `pack_defaults(repo)`

The pack's own artifacts, as classify-init candidates.

`requires` keeps the registry honest about THIS repo: a pattern naming a path that does
not exist is a claim nothing checks, and it would start matching the day someone creates
the file. Everything not listed stays `authored` -- the safe default. Do not enumerate it.

### `verify_regen_command(repo, patterns, command, timeout=…)`

Run it. Return (ok, reason). The near-miss control.

`patterns` is the set the generator OWNS, not one path: `audit-log.py render` rebuilds
the data projection and ensures the viewer exists, and both are derived. Declaring half
a generator's output leaves the other half conflicting by hand forever.

Two ways to fail, and the second is the subtle one: a command that exits 0 while
rewriting something outside that set is not a regenerate command, it is a side effect,
and classifying its target `derived` would licence the driver to resolve a file that
command will then clobber.

### `cmd_classify_init(root, repo, candidates=…, force=…, timeout=…)`

Write `.agents/artifacts.yml` from what this repo actually has. Verified, not guessed.

### `record_regen_owed(root, path)`

**Coverage gap** — no docstring in the source.

### `regen_owed(root)`

**Coverage gap** — no docstring in the source.

### `clear_regen_owed(root, paths)`

**Coverage gap** — no docstring in the source.

### `render_harness_capability()`

The harness capability block, as lines. ONE renderer, both surfaces.

The two surfaces disagreed for two revisions because each carried its own literal:
`plugin emit` called Copilot's edit boundary advisory-pending-proof, beside the constant
recording that the proof had arrived, and the comment above the doctor loop said the same
superseded thing a third time. Prose restating a verdict is REC-A; a single renderer makes
the disagreement structurally impossible. The superseded sentences are deliberately not
reproduced here -- a file that still contains them cannot be grepped clean, and the next
reader could copy one back out.

The commit-floor sentence is UNCONDITIONAL. It used to sit behind `if edit_boundary !=
"enforcing"`, which became unreachable the moment both entries said enforcing -- so the
one sentence that is true in every state printed in none of them. It is not a consolation
for a weak harness; it is the floor that holds regardless of what the hook does.

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

### `cmd_request(root, action, now, session, agent, args, repo=…)`

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

### `base_commit(cwd, repo, base)`

Resolve `--base` against the INVOKING worktree, never the primary (class PACK-P).

`repo` is deliberately the PRIMARY checkout: the coordination record is per repository,
which is exactly what `repo_root` exists to answer. But HEAD, @ and every relative ref
are per WORKTREE, so `git -C <primary> worktree add ... HEAD` run from a linked worktree
silently bases the new tree on the PRIMARY's commit. That is PACK-P one level along --
the right primitive for "which repository", used for a question that is "which tree".
Branch and tag names resolve identically from either tree, so for those this is only ever
a confirmation, never a change.

MEASURED HARM, and why this is worse than a wrong directory name: a node that had just
committed a fix created a tree with `--base HEAD`, silently got the primary's OLDER
commit, ran the pre-fix script, saw the pre-fix result, and nearly reported a correct fix
as broken. A tool that silently bases work on the wrong commit will be believed.

Returns (sha, None) or (None, message).

### `classify_removals(attempts, after, exists=…)`

What ACTUALLY happened to each attempted removal -- read back, never inferred (E14).

The old summary printed `len(removable) - failed`: a count derived from INTENT, where a
git call that returned quietly counted as a success. An operator then reads "removed 4 of
4" while a tree is still there, and an over-reporting cleanup is worse than an
under-reporting one -- the recovery nobody takes is the one nobody knows is needed.

REGISTRATION is the discriminator, not the error text, because git de-registers BEFORE it
deletes. A delete that fails can therefore leave the tree unregistered AND on disk, and
calling that "not removed" tells the operator to retry something git can no longer see.
Observed on Windows with a file held open: exit 255, "failed to delete", entry already
gone. That state is ORPHANED and must be named, because no worktree command will ever
mention it again.

`attempts` is [(record, err_text_or_None)]; `after` is the post-prune inventory.
Returns (removed_paths, refused_pairs, orphaned_pairs).

### `worktree_safety(record, primary, cwd, live_keys, index, include_unmerged=…)`

WT7, in order, fail-safe. Returns (safe, reason).

Every condition is a HARD STOP that reports rather than removes. A cleanup that deletes
on a heuristic will eventually delete the tree that mattered, and that single event ends
the adoption of the whole practice.

### `cmd_worktree(root, repo, action, cwd, now, session=…, agent=…, branch=…, base=…, remove=…, only=…, include_unmerged=…)`

**Coverage gap** — no docstring in the source.

### `session_tree_kind(repo, cwd)`

"primary" | "worktree", or None when it cannot be established.

None is a real answer and must not collapse to either value: a session whose tree could
not be resolved is not evidence of discipline (IO8).

### `wt4_exception_rate(root)`

How often did a session start in the primary checkout?

Sessions recorded before this field existed carry no `tree` and are counted as
`not_recorded` -- never as `worktree`, which would invent a number in the direction
that flatters us.

### `cmd_session(root, action, session, agent, cwd, now, repo=…)`

**Coverage gap** — no docstring in the source.

### `cmd_metrics(root, repo, as_json)`

**Coverage gap** — no docstring in the source.

### `heartbeat_scratch_path(root, repo, session)`

The machine-local accumulator between samples. It lives in the git COMMON dir (never
tracked, shared by every worktree of the clone, no .gitignore line to forget); when there
is no .git at all it falls back beside the ledgers, under the `.agents/*` ignore.

### `heartbeat_tick(root, repo, session, agent, now, files=…, calls=…, tokens=…, host=…, event=…, wi=…, cwd=…, flush=…)`

Accumulate one host event; write ONE `heartbeat` row when the sample window (100 s) has
passed or on `flush` (a stop-class event). Returns the row written, else None.

The row carries COUNTS: calls and distinct files since the previous row, tokens when a host
exposed them (`not recorded` otherwise - never a plausible number, IO8), `since` = the
previous row's instant, and `leader_renewed` (F-1). A zero-delta row is legal and renders
`stalled` (D7). Paths from the host are relativised, counted, never stored or opened.

### `track_fold(events, now, mtimes=…)`

Pure fold: ledger rows (+ worktree mtimes by label) -> one row per (session, wi).

live     the newest beat carries a progress delta and is younger than STALL_AFTER
         (or, with no beat at all, the worktree changed within STALL_AFTER)
stalled  everything else that is neither blocked nor done - a zero-delta ping is stalled
         however fresh (D7), and unproven liveness (no beat, no worktree) is never live
blocked  a `blocked` mail twin newer than any `unblocked`; blocked_on = its addressee
done     a session-end or a `done` twin
`missed_beats` counts sample windows since the last progress (or the last beat, or the
start); `kicks` counts rung-1 kicks recorded against (session, wi). Nothing is stored.

### `worktree_mtimes(repo)`

label -> newest change instant per registered worktree: the last commit's time or the
newest mtime of a modified/untracked file, whichever is later. Read from the world, bounded
by the changed set (never a walk of the whole tree). A tree git cannot read is absent.

### `cmd_track(root, repo, now, as_json=…)`

**Coverage gap** — no docstring in the source.

### `cmd_kick(root, repo, target, args, session, agent, now)`

The kick ladder (CO17): 0 notify (mail `note`) -> 1 kick (mail `kick`, cap KICK_CAP,
counted) -> 2 decision request (P1 typed request + mail `decision-request`). Every climb -
ok or refused - is a `kick-ladder` row in the kicker's ledger carrying the target's state,
stall age and missed beats at that instant (the SRE's measurement).

### `liveness_metrics(events, now, mtimes=…)`

The P3 measures (proposal §7 row P3): stall-detection latency and the false-kick rate,
plus the counts they rest on. R4: an empty corpus is a reason, never a zero.

### `heartbeat_doctor_line(root, now)`

(line, is_problem) for `coord doctor` and pack-doctor: who beats, how fresh, how many
stalled - or `not recorded`, which is not a problem and not a pass (CTX-H).

### `cmd_log_portable(paths)`

F-3 migration: rewrite ONLY the `worktree` field of existing ledger rows to its label.
Idempotent (a label maps to itself); every other line is copied byte-for-byte, including
lines that are not JSON; the writer's own dump (sort_keys) is used for the rewritten rows.

### `cmd_install(repo, root, force=…)`

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
CLONE is exactly where the gap appears. A worktree is not: it shares the parent's
config and inherits the registration.

This answers "is a driver registered", which is not the same question as "will its
path still be there next month" -- see driver_path_status.

### `driver_path_status(repo)`

Will the registered driver path OUTLIVE the tree that wrote it? (measured defect)

`driver_status` asks whether a driver is declared and registered. Both were true in the
consuming repo that found this, throughout -- and the registration pointed inside a
temporary worktree, because the pack told every agent to run `coord install` in one.
A worktree SHARES .git/config, so that install did not add a registration, it replaced
the repository's. WT8 cleanup then deletes the tree, and every declared path merges by
invoking a script that is not there.

There is no signature while the tree exists: the path resolves and names a byte-identical
script. So the question `doctor` has to ask is not "is a driver registered" but "where
does it point, and does that place outlive this merge". The primary checkout is the
answer, because it is the only tree the repository cannot lose.

The hazard is narrow and worth stating precisely: a path inside a LINKED WORKTREE,
which WT8 cleanup deletes. A path merely outside the repository is a different and
legitimate shape -- a global or out-of-tree install of the scripts -- and reporting it
would be a false positive, so this does not.

Returns one row per registered `merge.coord-*.driver`:
  ok | missing | foreign | unreadable | unchecked
`unchecked` is a real answer and never collapses to `ok` (R4).

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

- Public functions: **95** · documented: **71** (**75%**)
- Undocumented (recorded, not invented): `make_event`, `check`, `read_decisions`, `request_log_path`, `read_request_events`, `cmd_leader`, `regen_command`, `record_regen_owed`, `regen_owed`, `clear_regen_owed`, `detect_harness`, `cmd_precommit`, `cmd_guard`, `session_contract_path`, `owner_rows_for_path`, `cmd_session_list`, `cmd_collaborate`, `cmd_request`, `cmd_worktree`, `cmd_session`, `cmd_metrics`, `cmd_track`, `cmd_install`, `cmd_doctor`

