---
id: note-20260922-semantic-diagrams-in-reader-first-handbook
title: "The public handbook uses semantic HTML diagrams for selected relationships"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: documentation
tags: [decision-note, handbook, diagrams, accessibility]
links:
  - { to: design-reader-first-handbook, rel: relates-to }
  - { to: mockup-github-pages-handbook, rel: relates-to }
review-by: "2027-03-22"
review-suggested: []
summary: >-
  The public handbook renders selected multi-step, loop, and branch relationships as
  labelled HTML figures backed by ordered lists. The decision affects handbook source
  syntax, rendering, responsive behavior, and accessibility proof.
---

# The public handbook uses semantic HTML diagrams for selected relationships

- **Kind:** decision
- **Confidence:** Verified
- **Made during:** `/ui-design` elevation of the GitHub Pages handbook

## The call

Use a small `diagram` fence in canonical handbook Markdown for relationships with at
least three dependent steps, a loop, or a branch. The local renderer converts it into
a labelled `figure` containing an ordered list. The text and order remain the meaning;
connectors and layout are presentation. Malformed fences remain escaped code blocks.

This keeps diagrams deterministic, dependency-free, searchable, safe over `file://`,
and understandable without color or a canvas. The built HTML and its review copy are
generated from the same canonical source.

## Alternatives dismissed

- Mermaid at runtime — adds a larger client renderer and failure path to a surface that
  currently makes no network requests and needs only three simple relationship shapes.
- Image diagrams — weaken text scaling, search, forced-colors behavior, and maintenance.
- Styling arbitrary prose lists as diagrams — makes presentation depend on heading order
  and gives authors no explicit signal that the relationship must be reviewed as a unit.

## Promotion rule

Promote this to an ADR if the syntax is adopted by surfaces outside the handbook or if
backward compatibility for diagram kinds becomes a cross-project contract.
