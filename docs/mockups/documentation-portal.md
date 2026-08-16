---
id: mockup-documentation-portal
title: "Documentation Portal — mockup"
type: design
status: accepted
owner: "@timianmalloo"
phase: "documentation-portal"
tags: [documentation, portal, mockup, content-portal, ui]
links:
  - { to: spec-documentation-portal, rel: implements }
  - { to: design-language-docs-explorer, rel: refines }
review-by: "2027-02-11"
summary: >-
  Self-contained, dependency-free high-fidelity mockup of the Documentation Portal — the DocsPortal
  (Content Portal / HolyGrail reading layout) front door: persistent sidebar nav over six sections
  (Getting Started · Capabilities · The 21 Skills · UI Capabilities · Systems · Reference), search,
  and reading-optimised content. Renders the hard states (loading/empty/error) via a review harness
  (theme · viewport · state · motion) and reuses docs/DESIGN.md's AA-audited knowledge-surface tokens.
---

# Documentation Portal — mockup

The reviewable artifact is [`documentation-portal.html`](./documentation-portal.html) — open it over `file://`; no server, no build, no network.

## Direction brief (DX5)
- **Who / emotional state:** the evaluator/newcomer arriving cold; wants orientation and confidence, not a wall of 33 docs.
- **JTBD:** *orient-and-read over structured, sectioned content, with lookup.* Reading is the job → a documentation Content Portal, not a dashboard or a graph explorer.
- **Archetype (from the JTBD):** `DocsPortal` — Content Portal / HolyGrail reading layout (persistent sidebar nav + reading pane + search). Catalog F1, adapted.
- **Three adjectives (and their opposites):** **inviting** (not marketing-hype) · **authoritative** (not dense) · **guided** (not hand-holding).
- **Named reference (adapt, not clone):** Stripe / Vercel developer docs (sidebar + reading pane + `/` search) for the *structure*; the pack's own Docs Explorer + `docs/DESIGN.md` for the *visual language*. Neither cloned.
- **Anti-goals:** a marketing splash page; a wall of undifferentiated docs; a graph-first explorer (that surface already exists); a broken-link graveyard.
- **Personality (type/color/space):** *type* — DESIGN.md Segoe body + a serif display for section leads (editorial-technical, high legibility); *color* — the audited warm-dark palette, pink primary reserved for the **active nav item** and primary links only, semantic colours off except status; *space* — Comfortable, reading-optimised (a ~74ch measure), generous section rhythm.

## Triggered standards (mapped at Stage 1)
- **UI-T1 does not fire** — a reading surface, not expert-quantitative. *Excluded.*
- **UI-T2 does not fire** — no generated imagery. *Excluded.*
- **UI-T3 does not fire** — no model-generated content; the portal is a deterministic derived projection. *Excluded.*
- **UI-T4 does not fire** — web, `file://`, not a native app. *Excluded.*
- Only the **unconditional floor** applies (U1–U20, DX1–DX25, CD1–CD20, S2/S7).

## What the mockup renders
- **Six sections** via a persistent left-nav (a select on narrow): **Getting Started** (a 5-step guided descent with commands), **Capabilities** (a live-counts strip + a capability grid), **The 21 Skills** (grouped by the loop — Collect/frame · Architect/design · Build/verify · Continuous improvement · Lifecycle/pack · Utilities — each a card with description · when-to-use · produces · handoff · source link), **UI Capabilities** (the seven-standard stack + the /ui-design stages + link to the UI guide), **Systems** (knowledge graph, dreaming, audit, personas — each linking its specialised surface), **Reference** (a counts table + the "which surface for which job" map).
- **Hard states** (harness): loading skeleton, **empty section** ("generated from `pack/…` — add content there", not blank), **error** ("portal data missing — regenerate"), and overflow is exercised by the long skill descriptions.
- **Search** (`/` focuses it) filters skills live and clears cleanly.

## Craft notes / rubric self-check (DX22, structure→surface)
- **Archetype fit:** ✓ reading-first → HolyGrail Content Portal, not a dashboard/graph.
- **IA / guided descent:** ✓ Getting Started first; depth available but not mandatory (progressive disclosure).
- **State completeness (U9):** ✓ loading/empty/error switchable; overflow via long content.
- **Accessibility (U16):** skip-to-content link; keyboard-operable nav + search (`/` shortcut, visible focus ring); active section by **weight + inset bar**, not colour alone; headings form a correct outline; targets ≥44px; contrast from the DESIGN.md audit. Light + high-contrast inherit the audited tokens.
- **Token discipline (U3/U20):** `:root` values transcribed verbatim from `docs/DESIGN.md`; a self-contained mockup inlines its tokens.
- **Focal point (DX18):** the active content section (the thing being read).
- **No layout shift (U17):** section change swaps content, not layout; reduced-motion path removes animation.
- **Craft gate (CD8):** `ui-craft-gate.py` run over the built source. The `undersized-ui-text` **Major** (accessibility — `.mono` computed to ~10.2px inside the 12px harness) was **fixed** (floored with `max(0.85em,11px)`). One **Minor** `flat-type-hierarchy` is **accepted with reason (CD16 recorded deviation):** the *primary* heading hierarchy is strong (body 15 → h3 21 → display 36 = 1.4×/1.7×); the mid-band (15→18→21) is deliberately tight for reading comfort on a docs surface, and forcing every adjacent step to ≥1.25 would harm legibility. A clean detector run is a floor, not a verdict (CD13/CD14). Note (CD20): the portal is **client-rendered** (static markup ~8% of the file), so the gate validated the CSS/token layer + shell; the runtime UI reuses the same audited tokens by construction.

## The keep-current design (the point of the whole thing)
The mockup embeds `PORTAL_DATA` for review; the **production template loads `./portal-data.js`** emitted by `build-docs-portal.py`, which derives skills/counts/UI-standards from `pack/` sources + committed editorial markdown. So the portal is a **pure function of committed sources** — regenerated on `sync-pack.ps1`, **drift-gated** by `check-consistency.py` (byte-identical regeneration), and therefore complete-by-construction and unable to rot.

## Highest-leverage next step
Implement `build-docs-portal.py` to emit `portal-data.js` in exactly this shape, and the template that loads it — then wire into sync + the drift gate.
