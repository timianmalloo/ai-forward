# Design one implementable feature slice

Use this skill to turn a specification or architecture decision into a technical blueprint for one feature or component. It names contracts, data shapes, patterns, errors, concurrency, telemetry and tests before implementation begins.

## When to use it

Use `design-slice` after the product requirement is clear and before code for a non-trivial feature. It is the right place to settle how HarborTasks exports all 63 matching tasks while keeping authorization and empty-result behavior testable.

## What you need

Bring the approved spec, relevant architecture decisions, existing code paths and known constraints. If a dependency is unfamiliar, the design should include a small contract spike.

## Try it

Slash-command harnesses:

```text
/design-slice Design HarborTasks CSV export from the approved spec. Include query
scope, authorization, CSV serialization, error handling, telemetry and tests.
```

Codex equivalent:

```text
$design-slice Design HarborTasks CSV export from the approved spec.
```

## What happens

The skill reads the upstream spec and code, chooses the smallest correct design, names patterns, and tests the contracts the implementation will depend on. It also states what a human must decide, instead of letting the agent invent product policy.

## What you get

Illustrative artifact shape:

```text
docs/design/csv-export.md
  Contracts exposed and consumed
  Data shape and field authorization rule
  Failure modes and telemetry
  Test plan and proof obligations
```

## Review before continuing

Check that the design satisfies the spec, has one source of truth for each rule, handles boundary cases, and does not add speculative layers. Security, data or migration concerns must be resolved before implementation.

## Tips and recovery

If the design says “use existing helper” without opening it, require the source citation or mark the claim unverified. If the test plan cannot fail for the intended defect, redesign the oracle.

## Where to go next

Use [implement](#skill-implement) when the design is approved. Use [ui-design](#skill-ui-design) if the visual interaction is still unsettled.
