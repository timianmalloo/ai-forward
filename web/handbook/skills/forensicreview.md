# Review an existing repository for evidence-backed risk

Use this skill for a deep review of an existing codebase. It rebuilds the picture from code and docs, checks architecture, design, implementation and documentation, and produces a prioritized remediation backlog.

## When to use it

Use `forensicreview` when you inherit a repository, prepare for a release, suspect systemic issues, or need an external-quality review. It is broader than [investigate](#skill-investigate), which starts from one defect.

## What you need

You need repository access and time for a broad read. Existing specs, architecture, ADRs and tests improve the review, but the skill can also report their absence as risk.

## Try it

Slash-command harnesses:

```text
/forensicreview Review HarborTasks for risks around export, authorization,
documentation drift and test coverage. Produce a prioritized backlog, not fixes.
```

Codex equivalent:

```text
$forensicreview Review HarborTasks for export and authorization risk.
```

## What happens

The skill inventories the repository, reconstructs architecture from evidence, checks docs against code, identifies risks and ranks remediation. It should not expand into unapproved fixes.

## What you get

Illustrative artifact shape:

```text
docs/reviews/forensic-review-2026-09.md
  findings with severity and evidence
  risk register
  prioritized remediation backlog
  residual unknowns
```

## Review before continuing

Check evidence for each finding. A useful finding points to code, tests, docs or runtime evidence and names the smallest next repair. Do not treat every advisory note as current-task scope.

## Tips and recovery

If the review becomes a catalogue of opinions, ask for evidence and impact. If it uncovers a live defect, route that specific issue to [investigate](#skill-investigate).

## Where to go next

Use [code-hygiene](#skill-code-hygiene) for hygiene backlog work, [migrate](#skill-migrate) for large refactors, or [document](#skill-document) to repair documentation drift.
