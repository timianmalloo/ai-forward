# Reader-first handbook authoring

This directory is the canonical source for the public learning handbook. It is website
content, not another agent instruction layer. The handbook replaces the portal's
development-retrospective framing; technical records remain secondary reference.

## Reader and editorial contract

The reader is a capable engineer who has never used AI-Forward. Start with a problem,
explain the approach, then show how to use it. Do not require development-history
context or make internal rule identifiers, commit hashes or verdict tables do the
explaining. Ground claims in the pack privately and explain practical limitations.

The running example is **HarborTasks**, an illustrative task-tracking service. The
team wants CSV export for the current project and filter. Its existing screen shows
20 items at a time, while more may match the filter. This creates a useful question:
does export mean the visible page or every matching item? No application is built or
model/provider called merely to illustrate the handbook.

Guides live in `guides/<slug>.md`; skill references in `skills/<canonical-name>.md`.
Each begins with one human-readable H1 and an introductory paragraph explaining the
problem. Skill routes are `#skill-<canonical-name>`. Guide routes are `#<slug>`.
Use descriptive internal links such as `[Plan the work](#workflow)`, never opaque
evidence IDs. A linked page must stand alone when reached directly.

Every skill reference has these sections:

- `## When to use it`
- `## What you need`
- `## Try it`
- `## What happens`
- `## What you get`
- `## Review before continuing`
- `## Tips and recovery`
- `## Where to go next`

Explain prerequisites, scope, expected artifacts/behavior, a realistic invocation,
human review, and recovery. Label sample output illustrative. Use slash notation for
the documented slash-command harnesses and show the Codex `$skill` equivalent.
Do not invent switches or claim a utility produces files when it returns a view.
Give complex workflows additional depth through the appropriate guide; a short
utility should remain useful, not padded.

## Information architecture

| Reader question | Pages |
|---|---|
| Is this for me, and how do I start? | overview, get-started, workflow |
| How do I make the work trustworthy? | rigor, design, interfaces |
| How do I share work safely? | coordination, harnesses |
| How does useful knowledge accumulate? | knowledge, improvement, maintain |
| How do I find a tool or resolve a problem? | skills, troubleshooting, glossary, maintainer |

The skill catalogue is a reference destination, not the landing page. History,
internal evidence and API details belong behind the maintainer reference.

## UI direction and scope

Mode: elevate. Medium: static web documentation, readable on desktop and mobile.
Archetype: learning guide plus searchable reference, not a dashboard.
Qualities: calm, precise, practical; not ceremonial, crowded or promotional.
Use the established documentation pattern of a chapter sidebar and readable prose,
as seen in MDN's learning area and Django's tutorial/reference separation. Adapt the
pattern, not their content or visual identity.

Use system fonts, a restrained existing-brand accent, generous paragraph spacing,
a bounded reading measure, visible keyboard focus, semantic headings and links.
Support light/dark preference, reduced motion, narrow screens, search with no results,
unknown routes, missing/corrupt content, and JavaScript-unavailable fallback.
No generated imagery, native app, quantitative workbench or live AI interface is in
scope. Accessibility and responsive reading remain mandatory.

Canonical Markdown is compiled into a self-contained public HTML surface. Reuse a
pinned, locally vendored Markdown parser rather than implementing another parser.
Reject executable URL schemes and render raw source HTML as text. Public runtime
needs no provider, server, cookies, analytics, or external script origin.

## Execution shape

Inventory and this editorial pattern precede two independent tracks: skill-reference
authoring and handbook generation/guides. They join for coverage, content accuracy,
fresh-reader and accessibility reviews, then publication. Only the owner integrates
and regenerates shared outputs; authoring tracks use separate worktrees.

The coverage oracle compares canonical skill names with reference pages and requires
the reader-facing sections above. It does not mistake word count for useful writing.
Browser proof covers first-task discovery, a problem-driven skill search, the
plan/compile/execute handoff, keyboard/mobile use, and actual live destinations.

Planning cost is not measured; no speedup is claimed. The parallelism removes an
incidental dependency between independent prose and renderer work, not a review gate.
The completion variant is the finite set of missing pages, failed checks and unresolved
reader findings. A budget overrun is reported rather than silently dropping a floor.
