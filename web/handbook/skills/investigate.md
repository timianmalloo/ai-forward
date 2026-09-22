# Find the verified cause before fixing a defect

Use this skill when something is broken, slow, inconsistent or surprising. It reproduces or characterizes the symptom, proves the root cause, sweeps for siblings, proposes repair phases and then stops for human review.

**Default outcome: a verified cause and repair plan, not code changes.** The workflow
stops for your review before implementation. It continues into repair only if you
explicitly authorized that investigation to do so.

## When to use it

Use `investigate` for defects and incidents. If HarborTasks export downloads only 20 rows when 63 match, investigate before implementing a fix. The cause might be paging, authorization, a UI call, or a stale test fixture.

## What you need

Bring the symptom, environment, observed output, logs or failing tests. The skill also needs the spec or intended behavior; a defect is a gap between expected and actual behavior.

## Try it

Slash-command harnesses:

```text
/investigate HarborTasks CSV export returns only 20 rows when the current filter
matches 63 tasks. Find the verified root cause and propose repair phases. Stop
before implementation.
```

Codex equivalent:

```text
$investigate HarborTasks CSV export returns only 20 rows when 63 match.
```

## What happens

The skill reproduces or characterizes the failure, builds a timeline, tests competing causes, proves the cause with data, and generalizes the failure class. It does not start coding unless you explicitly asked this investigation to continue into repair.

## What you get

Illustrative artifact shape:

```text
docs/investigations/export-paging.md
  symptom and reproduction
  hypotheses considered
  verified root cause
  sibling sweep
  phased repair plan
  regression test that should fail before the fix
```

## Review before continuing

Confirm the cause explains all evidence, not just the most convenient example. Review the sibling sweep and repair phases before approving implementation.

## Tips and recovery

If the agent names a cause before reproducing the symptom, send it back to evidence. If two causes remain possible, ask what data would distinguish them.

## Where to go next

After approving phases, use [implement](#skill-implement). If the investigation reveals a design gap, use [design-slice](#skill-design-slice) first.
