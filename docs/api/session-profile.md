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

- Public functions: **28** · documented: **8** (**29%**)
- Undocumented (recorded, not invented): `parse_ts`, `iso`, `pct`, `est_tokens`, `model_family`, `norm_path`, `git`, `in_repo`, `copilot_home`, `copilot_settings`, `copilot_sessions`, `claude_home`, `claude_sessions`, `profile_claude`, `render_markdown`, `cmd_discover`, `profile_id`, `cmd_profile`, `cmd_compare`, `cmd_fixes`

