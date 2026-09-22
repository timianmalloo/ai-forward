# Plan the work shape before spending effort

Use this skill to turn a multi-step request into an execution graph: real dependencies, serial work, possible parallelism, budgets, loop exits and checkpoints. It optimizes for completeness and rigor before speed.

## When to use it

Use `optimize-graph` for work with more than two steps, loops, fan-out, hard review gates or coordination. Skip it for a direct one-step lookup or trivial edit.

## What you need

Bring the goal, constraints and known tasks. If you already have a compiled prompt, use that. Be honest where costs are estimated rather than measured.

## Try it

Slash-command harnesses:

```text
/optimize-graph Plan the HarborTasks CSV export work from specification through
design and implementation. Do not run every skill unless the graph requires it.
```

Codex equivalent:

```text
$optimize-graph Plan HarborTasks CSV export work from spec through implementation.
```

## What happens

The skill builds a naive graph, adds mandatory proof and review nodes, removes fake ordering, bounds loops and decides whether parallelism is worth its overhead. If the task is smaller than its plan, it says so.

## What you get

Illustrative output shape:

```text
Node A: specify export contract
Node B: design backend export path, depends on A
Node C: design UI affordance, depends on A
Serial spine: shared CSV schema before implementation
Skipped: no parallel workers until schema is fixed
```

## Review before continuing

Check that no proof or human decision was removed to make the plan faster. Every fan-out needs a width cap, exit condition, join rule and failure handling.

## Tips and recovery

If the plan is slower and proves no more, reject the extra structure. If a loop says “refine until good,” ask for a concrete exit condition.

## Where to go next

Use [prepare-for-coordination](#skill-prepare-for-coordination) if the graph justifies multiple sessions. Otherwise proceed to the next named workflow.
