# Keep documentation true to the code

Use this skill to generate or refresh the documentation bundle: API reference, diagrams, architecture overview, Docs Explorer index and browsable documentation view.

## When to use it

Use `document` after public APIs, contracts, architecture or important user-visible behavior change. Also use it to bootstrap docs for an existing codebase after [adopt](#skill-adopt).

## What you need

You need the code, relevant specs and designs, and permission to update docs. Documentation must reflect what exists, not what the plan hoped would exist.

## Try it

Slash-command harnesses:

```text
/document --changed Refresh docs for HarborTasks CSV export public API,
sequence flow and Docs Explorer entries.
```

Codex equivalent:

```text
$document --changed Refresh docs for HarborTasks CSV export public API and diagrams.
```

## What happens

The skill inventories public surface and graph artifacts, extracts doc comments where available, checks diagrams against code, derives the docs index and records stale or missing docs as findings. It does not invent examples.

## What you get

Illustrative artifact shape:

```text
docs/api/export.md
docs/diagrams/export-sequence.md
docs/architecture.md updates
docs/docs-index.js
docs/_site/index.html
```

## Review before continuing

Check examples, diagrams and API claims against code. An undocumented public member is a gap; a diagram contradicting code is worse than no diagram.

## Tips and recovery

If code and spec disagree, docs should describe code and flag the discrepancy. If generated graph output is wrong, fix source frontmatter or links, not only the generated index.

## Where to go next

Use [maintain the knowledge graph](#maintain) for ongoing docs health, or [auditlog](#skill-auditlog) to find the decision that caused a documentation change.
