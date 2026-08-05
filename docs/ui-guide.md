---
id: ui-capability-guide
title: "UI & UX Capability Guide"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [ui, ux, guide, design, accessibility, docs-explorer]
links:
  - { to: design-language-docs-explorer, rel: relates-to }
  - { to: docs-index, rel: relates-to }
review-by: 2026-11-03
review-suggested: []
summary: >-
  The how-to layer over this repository's seven UI standards: the layer stack and what each
  one decides, a job-to-path picker, the /ui-design loop, the command cheat sheet, an
  archetype picker, the veto table, the anti-pattern tells, and where artifacts land. The
  browsable surface is ui-guide.html; this node is its place in the graph.
---

# UI & UX Capability Guide

**Read it here: [`ui-guide.html`](ui-guide.html)** (self-contained, opens over `file://`, and
listed under **Knowledge surfaces** in the [Docs Explorer](index.html)).

## What this is

The repository accumulated a lot of interface capability: seven standards, one craft workflow,
two linters, four templates, an archetype catalog of roughly thirty entries, and a persona
council with real veto power. Each standard is strong on its own, and none of them answers the
question a person actually arrives with, which is *"I have a UI job. What do I run, in what
order, and what does each thing decide?"*

This guide is that answer. It is **derived** from the standards and never authoritative over
them: where the two disagree, the standards win and the guide is the thing that is wrong.

## What it covers

| Section | Answers |
|---|---|
| The stack | Seven standards, the question each one owns, its directive prefix |
| Start here | Six common jobs, and the path each takes |
| The loop | The five `/ui-design` stages and what each leaves behind |
| Commands | Copy-paste for the workflow, the controls, and the graph |
| Archetypes | A condensed picker across the temporal, operational, spatial, streaming, authoring and technical families |
| Gates | Who can block, on what, and what clears it |
| Anti-patterns | The generic-look tells, which detector rule catches each, and the registered defect classes |
| Artifacts | Templates, scripts, examples, and where outputs land |

## Provenance and freshness

The guide is a **template instantiation**: the source is
`pack/templates/ui-capability-guide.template.html`, deployed to
`docs/ai-forward-pack/templates/` for every repo that installs the pack, and instantiated here as
`docs/ui-guide.html`. When a UI standard changes materially, this node is an inbound neighbour
and should be flagged `review-suggested` so the guide does not drift from the standards it
summarises.

It is held to the floors it documents: self-contained with no build step and no CDN, tokens from
`DESIGN.md` rather than literals, WCAG 2.2 AA across light, dark and forced-colors modes,
keyboard operable with a skip link, and **clean under
`ui-craft-gate.py --gate --a11y-obligation`**. That last one was not free. The first run reported
69 findings, including a `kicker-above-heading` that the craft floor bans outright. Every one was
resolved by fixing the artifact, none by suppressing a rule.
