# Technical reference when you need the machinery

The handbook teaches how to use AI-Forward. Sometimes you need the underlying
contracts, source, detailed architecture or history instead. Those records remain
available; they should not be prerequisites for a first useful task.

## Choose the right depth

- Open the [engineering reference portal](maintainer.html) for standards, architecture
  inventories, operational concepts and historical material.
- Open the [Docs Explorer](../index.html) to follow typed relationships among project
  artifacts and inspect knowledge-graph health.
- Open the [rendered architecture and API reference](../_site/bundle.html) for the
  implementation-oriented documentation bundle.
- Read the [pack overview (Markdown)](../../pack/OVERVIEW.md) for the underlying
  workflow overview and source conventions.
- Read [installation and refresh guidance (Markdown)](../../pack/adapters/INSTALL.md)
  when changing the deployment map or updating managed surfaces.

These links lead to technical material with a different job from this handbook.
Some pages intentionally retain development history or detailed verification records.
Use them to answer a precise question, not as an obstacle course before adoption.

## How this handbook stays current

Public handbook sources live under `web/handbook`. A deterministic builder produces
the reader surface and graph-indexed Markdown copies. Its coverage check compares
the current canonical skill inventory with the reference pages, so a newly added
skill cannot silently disappear from the handbook.

The coverage record also maps the major knowledge areas to their guide homes.
Read the [handbook coverage matrix (Markdown)](../handbook/coverage.md) when maintaining
the content. It is a maintenance aid, not the homepage.

Content still needs editorial review. A page with every required heading can be
unhelpful. Review changes as a reader who has not followed the development work,
and exercise the actual rendered site, including search, links and narrow screens.

## Contribute without creating another source of truth

Change the canonical source, regenerate its outputs and run the relevant checks.
Do not repair a generated page by hand. Keep examples aligned with the actual
contracts; label illustrative output and keep unsupported behavior out of tutorials.

When a source and guide disagree, record and resolve the discrepancy. Do not change
runtime behavior simply to make the prose easier to write, and do not erase a useful
historical record to make the current design seem inevitable.

**Next:** [maintain or extend the pack](#maintain), or return to [the handbook](#overview).
