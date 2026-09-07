---
id: api-session-profile
title: "API — session-profile.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  session-profile.py — measure how agent sessions actually ran, across harnesses and models.
---

# `session-profile.py`

*Generated from `pack/scripts/session-profile.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
session-profile.py — measure how agent sessions actually ran, across harnesses and models.

Instrumentation over inference (IO1) pointed at the agent's own work: instead of reasoning
about why a session felt slow, expensive or drifty, READ the telemetry every harness already
writes to disk and turn it into a findings table (what happened, with evidence) and a fixes
table (which pack surface owns the control). This is the "asleep half" of continuous
improvement (`/dream`) specialised to performance, efficiency, task adherence, fan-out and
cross-harness coordination — the /session-profiler skill drives it.

Sources (all local, all read-only):

  GitHub Copilot CLI   ~/.copilot/session-store.db        sessions, turns, assistant_usage_events
                       ~/.copilot/session-state/<id>/events.jsonl   the full event stream
                       ~/.copilot/settings.json           model / contextTier / effortLevel
  Claude Code          ~/.claude/projects/<slug>/<session>.jsonl    the transcript

A repo is selected by path (`--repo <path>`, repeatable). Copilot sessions match on cwd or the
`owner/name` remote; Claude Code sessions match on the project slug of the repo path and of each
of its git worktrees. Every number is either read from the store or labelled as an estimate;
a measurement path that does not exist reports "not recorded", never a plausible number (IO8).

Subcommands
  discover   list the sessions found for the repo(s) in the window
  profile    per-turn metrics + findings + fixes for the selected sessions; writes
             docs/profiles/<sp-id>/{profile.json,profile.md} in the FIRST --repo (or --out-root)
  compare    aggregate the same metrics by model family x harness (the tuning view)
  fixes      print the fix catalog (finding id -> pack surface -> control)

Python 3.8+, stdlib only. Windows-safe (utf-8 stdout, read-only SQLite URI).
```

## CLI — subcommands

| Subcommand | Help |
|---|---|
| `compare` | aggregate by model family x harness |
| `discover` | list matching sessions |
| `fixes` | print the fix and finding catalogs |
| `profile` | profile sessions and write docs/profiles/<sp-id>/ |

## CLI — options

| Option | Help |
|---|---|
| `--chars-per-token` | _(no help text — coverage gap)_ |
| `--claude-home` | override ~/.claude |
| `--copilot-home` | override ~/.copilot |
| `--days` | window in days (0 = all) |
| `--harness` | _(no help text — coverage gap)_ |
| `--json-only` | print JSON, write nothing |
| `--limit` | newest N sessions |
| `--out-root` | repo root that receives docs/profiles/ (default: first --repo) |
| `--print-markdown` | _(no help text — coverage gap)_ |
| `--repo` | repo path (repeatable); the first one receives docs/profiles/ |
| `--session-id` | audit session id to record |
| `--session` | restrict to session id(s) or prefixes |

## Functions

### `late_addition_findings(turns)`

`/also` turns that acquired no bound (F-15, class CTX-N).

`/also` guards DIRECTION - "an extension is absorbed; a reversal is raised" - and had no
guard on SIZE. Measured in sp-0004: both `/also` turns were the only substantive turns on
that model carrying neither a goal state nor a tier, and one became 81 main requests, 6
sub-agents, 83 minutes and 13,411 AIU - the most expensive turn in the session.

Deliberately narrower than SP-09, which already owns the generic missing-goal-state case.
This one is about the *late addition* specifically, because the mechanism is different: an
addition to an unbounded turn INHERITS unboundedness rather than acquiring a bound, and
the skill's own flow assumed a goal state was there to re-read.

### `mechanical_cost_findings(turns, min_aiu=…)`

Closing work billed as though it needed novelty (F-17).

Measured: `/updatepack` ran twice in one session - 1,179 AIU on claude-opus-4.8 and
8,890 on gpt-6-astra. Same skill, same repo, 7.5x. "yes commit and push/merge all" cost
5,173 AIU across 21 requests. None of that is novel work; all of it is a script with a
reviewer, and GO19's per-phase tier does not reach it because the phase boundary is
inside the turn.

The finding is the PRICE, not the mechanics - closing work is legitimate and has to
happen. A cheap mechanical turn is exactly right and is not reported. A turn with no
recorded cost is not guessed at (IO8).

### `effective_model(models)`

The model a session actually WAS, by cost. `models` is {model: {requests, cost}}.

By cost rather than request count on purpose: in the measured session `gpt-6-astra` and
the delegate models had comparable request counts and wildly different prices, and it is
the expensive one that determines what the session cost and how it behaved.

Returns None for a corpus it cannot read - an unknown model is not a guess (IO8).

### `model_attribution(settings, models)`

Reconcile the RECORDED model against the EFFECTIVE one (class CTX-O).

The setting is a true statement about what was configured and is simply not a statement
about what executed: measured, one session recorded `claude-opus-4.8` while `gpt-6-astra`
ran 1,022 requests for 95% of the spend, across eleven model/effort combinations. Both
values are plausible, which is why the error is invisible.

Note what counts as a mismatch: the recorded model having RUN is not enough. In that
session it ran - on 5% of the requests. Presence is not attribution.

An absent setting is not a mismatch. Claude Code records no model setting, and absent
must not read as wrong.

### `main_line_share(buckets)`

Split a session's requests and cost between the main line and its delegates.

`buckets` is {initiator: {"requests": n, "cost": aiu}}. The main line is `agent`, `user`
and `compaction` - a compaction request and the request that opens a user turn are both
paid on the main conversation, and both were substantial: in sp-0003 the 24 bare
user-initiated requests alone cost 12,853 AIU, MORE THAN THE ENTIRE DELEGATE FLEET.

This is the measured half of CT19's `Main-line budget:`, which is only a declaration - an
agent cannot count its own model requests, and this can. Reconciled, never conflated.

Returns None for a share or a ratio it cannot establish: a percentage over an empty
corpus is not a measurement (R4), and no delegates means there is no ratio to report
rather than a ratio of infinity.

### `parse_ts(s)`

**Coverage gap** — no docstring in the source.

### `iso(d)`

**Coverage gap** — no docstring in the source.

### `pct(values, q)`

**Coverage gap** — no docstring in the source.

### `est_tokens(chars)`

**Coverage gap** — no docstring in the source.

### `model_family(model)`

**Coverage gap** — no docstring in the source.

### `norm_path(p)`

**Coverage gap** — no docstring in the source.

### `git(args, cwd)`

**Coverage gap** — no docstring in the source.

### `repo_identity(path)`

Everything a session could have recorded to say 'I ran in this repo'.

### `repo_label(path)`

A canonical, worktree-independent name for a repo (class PACK-P: a generated artifact
must never stamp the worktree folder name): the origin owner/name when there is one, else
the basename of the PRIMARY checkout from `git worktree list`, else the basename.

### `claude_slug(path)`

Claude Code names a project directory by replacing every non-alphanumeric character in
the absolute path with '-'. Observed: C:\projects\ai-forward -> C--projects-ai-forward.

### `in_repo(identity, cwd, repository=…)`

**Coverage gap** — no docstring in the source.

### `copilot_home()`

**Coverage gap** — no docstring in the source.

### `copilot_settings(home)`

**Coverage gap** — no docstring in the source.

### `copilot_sessions(identity, since, home)`

**Coverage gap** — no docstring in the source.

### `profile_copilot(sess, settings)`

One Copilot session -> normalized turns + session-level facts.

### `claude_home()`

**Coverage gap** — no docstring in the source.

### `claude_sessions(identity, since, home)`

**Coverage gap** — no docstring in the source.

### `profile_claude(sess)`

**Coverage gap** — no docstring in the source.

### `detect(session)`

Rule-based detectors over one profiled session. Returns finding dicts with evidence.
Every rule is deterministic; the 'confidence' is Verified for measured facts and Inferred
where a heuristic (regex over text) stands in for a field the harness does not record.

### `cross_session_findings(sessions)`

SP-15 concurrent sessions in one checkout (same cwd, overlapping windows).

### `family_comparison(sessions)`

Aggregate per (family, harness): the tuning view. Drift indicators are counts per turn.

### `render_markdown(profile)`

**Coverage gap** — no docstring in the source.

### `cmd_discover(args)`

**Coverage gap** — no docstring in the source.

### `profile_id(root)`

**Coverage gap** — no docstring in the source.

### `cmd_profile(args)`

**Coverage gap** — no docstring in the source.

### `cmd_compare(args)`

**Coverage gap** — no docstring in the source.

### `cmd_fixes(args)`

**Coverage gap** — no docstring in the source.

## Coverage

- Public functions: **32** · documented: **12** (**38%**)
- Undocumented (recorded, not invented): `parse_ts`, `iso`, `pct`, `est_tokens`, `model_family`, `norm_path`, `git`, `in_repo`, `copilot_home`, `copilot_settings`, `copilot_sessions`, `claude_home`, `claude_sessions`, `profile_claude`, `render_markdown`, `cmd_discover`, `profile_id`, `cmd_profile`, `cmd_compare`, `cmd_fixes`

