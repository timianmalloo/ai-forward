# Decide the system shape before building

Use this skill when a project or major capability needs a top-level architecture: components, boundaries, data representation, integration contracts, AI tiering and durable decisions.

## When to use it

Use `define-architecture` for new systems, new services, load-bearing platform choices, unfamiliar SDKs or protocols, data-model decisions, and AI-integrated system shape. Do not use it for a small local implementation detail.

## What you need

Bring a specification or clear problem statement, known constraints, target environments and any existing architecture docs. Be ready to run small spikes for unfamiliar APIs before depending on them.

## Try it

Slash-command harnesses:

```text
/define-architecture From the HarborTasks export spec, define the architecture
for CSV export across service, authorization, storage and UI download boundaries.
```

Codex equivalent:

```text
$define-architecture Define HarborTasks CSV export architecture from the approved spec.
```

## What happens

The skill maps the system, settles key boundaries, tests unfamiliar contracts, and records decisions as architecture and ADRs. For data work, it starts with domain concepts and durable representation before table or endpoint details.

## What you get

Illustrative artifact shape:

```text
docs/architecture.md
docs/adr/0007-csv-export-boundary.md
diagrams showing components, layers and external systems
spike notes for unfamiliar contracts
```

## Review before continuing

Review boundaries, data ownership, security and privacy implications, operational risks, rejected alternatives and any assumptions left open. Architecture decisions are expensive to reverse; do not approve them by skimming.

## Tips and recovery

If the skill guesses a vendor API, stop and require a spike or source read. If it proposes many services for a small feature, ask which boundary each service protects.

## Where to go next

Use [design-slice](#skill-design-slice) to make one component implementable, then [implement](#skill-implement) after the design is reviewed.
