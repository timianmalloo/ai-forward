# Build the approved change with tests

Use this skill after the requirement and design are clear enough to code. It implements through test-first increments, verifies the real behavior and produces evidence for review.

## When to use it

Use `implement` for a feature or approved repair phase. Do not use it to investigate a vague symptom or invent the product requirement. For a bug, start with [investigate](#skill-investigate) unless the repair phase is already approved.

## What you need

Bring the approved spec or design, the intended scope, and the proof expected. For HarborTasks export, that means all matching rows, authorized fields only, and empty headers are already accepted requirements.

## Try it

Slash-command harnesses:

```text
/implement Build the HarborTasks CSV export from docs/design/csv-export.md.
Prove all matching rows export, unauthorized fields are omitted, and empty results
produce headers.
```

Codex equivalent:

```text
$implement Build HarborTasks CSV export from docs/design/csv-export.md.
```

## What happens

The skill maps tests to the design, observes failing tests where needed, makes the smallest code changes, refactors, and runs the targeted checks. It keeps human decisions separate from tool execution.

## What you get

Illustrative output shape:

```text
Changed: export service, CSV serializer, UI action
Tests: ExportAllMatches, OmitsUnauthorizedFields, EmptyExportHasHeaders
Proof: targeted test run output and residual risk
```

If the change touches public surfaces or docs, related documentation may need a follow-up.

## Review before continuing

Review the diff, the tests and what they actually prove. A green suite is not enough if it never crosses the paging boundary or authorization path you care about.

## Tips and recovery

If tests fail for changed code, the task is not done. If the agent discovers the design is wrong, stop and update the design rather than patching around it.

## Where to go next

Use [document](#skill-document) after public surfaces change. Use [code-hygiene](#skill-code-hygiene) only for cleanup that is in scope or approved separately.
