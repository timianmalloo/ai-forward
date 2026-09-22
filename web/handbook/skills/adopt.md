# Bring an existing repository into the knowledge graph

Use this skill after the pack is installed in a project that already has code and docs. It inventories what exists, recovers the architecture, adds graph frontmatter to worthwhile documents, and creates an adoption plan for gaps.

## When to use it

Use `adopt` once per brownfield repository. It is the bridge between “the pack is installed” and “the repository's own knowledge is discoverable.”

## What you need

You need an installed pack and permission to edit docs. You do not need perfect existing documentation. The skill is meant to deal honestly with partial, stale or missing docs.

## Try it

Slash-command harnesses:

```text
/adopt Recover HarborTasks' existing architecture and docs into the knowledge graph.
```

Codex equivalent:

```text
$adopt Recover HarborTasks' existing architecture and docs into the knowledge graph.
```

## What happens

The skill inventories code, existing docs, specs, ADRs and glossary terms. It adds valid metadata to kept documents, creates an initial graph index, records gaps, and proposes phased follow-up work. It does not pretend undocumented architecture is known.

## What you get

Illustrative artifact shape:

```text
docs/index.md                 map of content
docs/docs-index.js            derived graph index
docs/glossary.md              mined starter vocabulary
docs/adoption-plan.md         phases and gaps
```

Claims recovered from code or docs should carry confidence. Unknowns remain visible.

## Review before continuing

Check whether the recovered architecture matches the code, whether terms have one meaning, and whether any document was kept but marked with overconfident metadata. Smaller honest coverage is better than a large guessed graph.

## Tips and recovery

If the inventory finds old plans that do not match code, record them as stale rather than making the graph endorse them. If graph generation fails, fix source frontmatter or links; do not patch only the generated index.

## Where to go next

Run [document](#skill-document) for the full documentation bundle, or [collectknowledge](#skill-collectknowledge) before designing in an unfamiliar domain.
