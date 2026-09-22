# Measure how agent sessions actually behaved

Use this skill to profile local harness telemetry and turn it into findings and fixes for cost, context growth, re-reads, task drift, fan-out and cross-harness coordination.

## When to use it

Use `session-profiler` after a session felt slow, expensive or drifty; weekly on active pack-consuming repos; and before or after changing model or harness settings.

## What you need

You need one or more local repositories with session telemetry available. Missing measurements must remain `not recorded`, not estimated as facts.

## Try it

Slash-command harnesses:

```text
/session-profiler --days 7 --repo C:\Projects\harbortasks
```

Codex equivalent:

```text
$session-profiler --days 7 --repo C:\Projects\harbortasks
```

## What happens

The skill discovers sessions in the window, reads telemetry stores, profiles costs and behavior, compares model families where enough comparable turns exist, and maps findings to proposed controls.

## What you get

Illustrative artifact shape:

```text
docs/profiles/session-profile-20260922/profile.json
docs/profiles/session-profile-20260922/profile.md
Findings: repeated reads, missing goal state, over-wide fan-out
Fixes: pack surface, control, recurrence signal
```

The numbers are useful only when their source is clear. Token counts, request counts
and timing come from harness stores where available. Transcript-based classifications
remain review findings until a human accepts the interpretation.

## Review before continuing

Check which findings are measured and which are inferred from transcript text. A tuning recommendation based on fewer than comparable sessions should stay tentative.

## Tips and recovery

If a store is unavailable, report the gap. If the profile finds a real software defect, route it to [investigate](#skill-investigate) rather than treating it as a session-tuning issue.

## Where to go next

Use [dream](#skill-dream) to consolidate repeated findings, or [apply-learnings](#skill-apply-learnings) after approved general controls exist.
