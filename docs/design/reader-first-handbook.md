---
id: design-reader-first-handbook
title: "Reader-first handbook: content and publishing contract"
type: design
status: accepted
owner: "@timianmalloo"
phase: documentation
tags: [handbook, documentation, accessibility, publishing]
links:
  - { to: handbook-overview, rel: documents }
  - { to: spec-documentation-portal, rel: refines }
  - { to: architecture, rel: relates-to }
review-by: "2027-03-22"
summary: "A problem-led public handbook replaces the retrospective portal as the default reading path. Canonical website Markdown produces a self-contained reader and graph-indexed mirrors, with exact skill/capability coverage and independent newcomer review."
---

# Reader-first handbook contract

The human request is an editorial rebuild, not an extension of the development
timeline. A newcomer must understand the purpose, adopt the pack, choose a workflow,
and use coordination without being given unpublished history. The former portal
remains a secondary engineering reference, not the first learning path.

## Model and source ownership

One source page is one reader topic or one canonical skill reference. Its identity
is a stable route, independent of its heading. Source Markdown lives in
`web/handbook/guides` and `web/handbook/skills`; navigation and capability coverage
live in `navigation.json`. These are website sources, not agent instructions.

`build-handbook.py` derives the embedded reader, Markdown mirrors and coverage map.
`docs-graph.py` alone derives the accumulated documentation index. The mirrors are
not independently edited. The existing API and diagram bundle remains available.
No runtime agent contract is changed to simplify the explanation.

## UX and presentation

The reading journey is purpose -> first task -> appropriate workflow -> deeper
engineering/coordination concepts -> reference. Direct problem search is a second
entry path. The fictional HarborTasks example consistently distinguishes 63 matches
from 20 visible rows; sample outputs are illustrative.

Archetype: learning guide plus searchable reference. Medium: static web, WCAG 2.2 AA.
The website adopts the existing warm/rose palette and system serif/sans typography,
not the old catalogue layout. `web/handbook/DESIGN.md` records tokens and states.
The actual self-contained build is the reviewable prototype; browser fixtures drive
viewport, theme, reduced-motion and error states rather than maintaining a second UI.

## Surface list and dependencies

Source Markdown/navigation -> validated page records -> escaped embedded JSON ->
vendored Markdown renderer -> reader navigation/search/prose -> generated Markdown
mirrors -> documentation graph -> published Pages bundle. Source changes are checked
against generated outputs. Historical anchors map to the corresponding reader topic.

The UI does not call a model, provider, telemetry service or external asset host.
Build output records page/skill/knowledge counts, HTML bytes, duration and error codes.
The page is bounded to 1 MiB; the current content is approximately 231 KiB.

## Adversarial analysis (STRIDE-lite)

| Boundary / threat | Disposition | Control and verification |
|---|---|---|
| Markdown raw HTML or dangerous links execute in the reader | Prevent | Escape raw HTML; permit only safe URL forms; hostile-source browser fixture proves no script, event handler, unsafe href or remote image request. |
| A JSON string closes its script element | Prevent | Encode less-than signs in embedded JSON; producer test and real-browser fixture cover script breakout, quotes, backslashes and Unicode separators. |
| A source alias admits another local content tree | Prevent | Exact guides/skills roots, nonrecursive scans and canonical path checks; generated outputs are owned and checks are read-only. |
| A stale or empty catalogue appears complete | Detect | Reconcile every canonical skill and knowledge source with authored pages and guide homes; reject missing sections, routes and coverage. |
| A dependency changes silently | Prevent/detect | Pinned local marked 18.0.14, retained MIT license/provenance, SHA-256 guard; no runtime CDN. |
| Unknown page or damaged data strands the reader | Recover | Visible recovery, overview/source link and working navigation; browser checks cover both states. |

## Privacy analysis (LINDDUN-lite)

| Data / risk | Disposition | Control and verification |
|---|---|---|
| Raw operational history reaches public prose | Prevent | Curated website source corpus only; publish boundary still excludes raw audit/dream/manifests/working ledgers. |
| Search terms become tracking data | Prevent | Search stays in page memory; no analytics, cookies, provider calls or outbound requests. |
| Illustrations are mistaken for real customer records | Prevent | Fictional HarborTasks and explicitly illustrative outputs; no customer material or live model runs needed. |
| Third-party scripts or images observe reading activity | Prevent | Locally embedded parser; system fonts; image embeddings disabled with visible text fallback; browser request inventory is empty. |

## Verification and confidence

- Verified: canonical inventory coverage, deterministic generation, injection protection,
  reader task paths, all skill sections, mobile/keyboard behavior, route recovery,
  and sampled text/link contrast in light and dark.
- Verified: the built preview's craft detector has no Major findings. Its remaining
  flat-type warning does not interpret the responsive H1 clamp; visual and computed
  browser inspection remain authoritative for hierarchy.
- Reader review found that the investigation stop point, first-adoption sequence and
  manual-brief meaning needed more prominence. These were clarified in public copy,
  rather than supplying the reviewer with internal context.
- Residual: no screen-reader-user study or comprehension study across a broad population
  was performed. A fresh independent reader and browser accessibility checks are the
  evidence for this release, not a claim about every reader.
