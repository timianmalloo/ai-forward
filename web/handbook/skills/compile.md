# Compile a rough request into a dispatchable prompt

Use this utility when a prose request is too ambiguous to hand directly to a workflow or worker. It turns the request into a goal state, traced clauses, assumptions and decision requests without adding scope.

## When to use it

Use `compile` before coordination, long-running work or a delegated track. It is not a design workflow; it prepares the starting prompt so the real workflow begins from a clear contract.

## What you need

You need the raw request text or an audit-log prompt id. If the compiled prompt contains unanswered decision requests, a human must answer or edit before dispatch.

## Try it

Slash-command harnesses:

```text
/compile "Add CSV export for HarborTasks. It should export all matches, not just
the visible page, and must not include unauthorized fields."
```

Codex equivalent:

```text
$compile "Add CSV export for HarborTasks..."
```

## What happens

The skill builds a structured prompt with goal, done-when, not-in-scope, tier, budget and traced clauses. A gate refuses clauses that cannot be traced to the raw request or a marked assumption.

## What you get

Illustrative output shape:

```text
Goal: deliver a reviewed CSV export design
Done when: export scope, fields and empty result behavior are explicit
Not in scope: implementation
Decision requests: none
Dispatchable: yes
```

It also logs the raw and compiled prompt together when the repository audit log is available.

## Review before continuing

Check that the compiled version did not enlarge the request. If it added “also build the UI” when the raw request only asked for a plan, reject or edit it.

## Tips and recovery

If the compiler refuses a clause, fix the trace or remove the invented scope. If a decision request remains unanswered, do not let a worker choose a default silently.

## Where to go next

Hand the compiled prompt to [optimize-graph](#skill-optimize-graph), [prepare-for-coordination](#skill-prepare-for-coordination), or the workflow it targets.
