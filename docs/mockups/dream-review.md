---
id: mockup-dream-review
title: "Dream Review — mockup"
type: design
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [dreaming, mockup, review-view, master-detail, ui]
links:
  - { to: spec-dreaming, rel: implements }
  - { to: design-language-docs-explorer, rel: refines }
review-by: "2027-02-11"
summary: >-
  Self-contained, dependency-free high-fidelity mockup of the Dream Review view — the Master-Detail
  approval queue the maintainer uses to review a dream's proposals (evidence, provenance, confidence,
  proposed control, federation scope) and Approve/Edit/Reject/Defer each, then export decisions. Renders
  the hard states (empty/loading/error/overflow) via a review harness (theme · viewport · state · motion)
  and reuses docs/DESIGN.md's AA-audited knowledge-surface tokens.
---

# Dream Review — mockup

The reviewable artifact is [`dream-review.html`](./dream-review.html) — open it over `file://`; it needs no server, no build, no network.

## Direction brief (DX5)
- **Who / emotional state:** the reviewing maintainer, arriving (often in the morning, across several repos) to triage a queue of proposed improvements — wants speed *and* the confidence that nothing corrupts their rules.
- **Job-to-be-done:** *serial review-and-decide over a queue of proposals with rich per-item evidence.* Reading is parallel; **deciding is serial** — so this is a review queue, not a dashboard.
- **Archetype (from the JTBD):** `DreamReview` — Master-Detail review queue (Governor/approval surface), catalog B-series. Not a bento dashboard.
- **Three adjectives (and their opposites):** **calm** (not sterile) · **legible-at-density** (not cramped) · **trustworthy** (not bureaucratic).
- **Named reference (adapt, not clone):** the pack's own audit viewer + Docs Explorer knowledge surfaces — take the derived-HTML, file://-safe, token-driven pattern and the `docs/DESIGN.md` palette; do **not** invent a new visual language.
- **Anti-goals:** a metrics dashboard; a one-click "Approve all" that invites rubber-stamping; any silent write to disk from a `file://` page.
- **Personality (type/color/space):** *type* — the DESIGN.md Segoe/Consolas system (utilitarian, high-legibility, because this is a governance surface); *color* — the audited warm-dark palette with the pink primary reserved for selection + the single primary action (Export), semantic success/warning/danger only on decision state; *space* — Comfortable density (a reviewer reads evidence carefully; this is not a throughput terminal).

## Triggered standards (mapped at Stage 1)
- **UI-T3 fires** — proposals are model-*assisted* (the REM abstraction step). Applied: provenance/footprints on every proposal, `◆ model-proposed — verify before approving` disclosure vs `■ deterministic`, verification-before-the-consequential-action (approve requires evidence visible), the human as the gate. HAX G1/G2/G11/G16/G17.
- **UI-T1 does not fire** — a review queue, not an expert-quantitative surface (no colormaps, no uncertainty distributions). *Excluded with reason.*
- **UI-T2 does not fire** — no generated imagery/persona/motion. *Excluded.*
- **UI-T4 does not fire** — web, opened over `file://`, not a native app. *Excluded.*

## What the mockup renders
- **Normal** — populated Master-Detail: filterable, kind-grouped, **highest-leverage-first** queue (left) + a focal detail pane (right) with signature, evidence+provenance, proposed control (with ladder rung + location), boundary statement, federation-scope toggle, and Approve/Reject/Defer.
- **Loading** — skeletons (matching content shape, not a spinner).
- **Empty** — "No proposals in this dream" (a valid, healthy result), teaching the next action.
- **Error** — "Dream data missing or malformed — nothing was changed", with the regenerate command.
- **Overflow** — an extreme proposal (40 evidence items, a paragraph-long title, a 120-token control body, a very long path) proving the layout wraps/scrolls rather than clips.
- **Export drawer** — the decisions JSON + the exact `apply-decisions` command, with the explicit "writes nothing yet" contract.

## Craft notes / rubric self-check (DX22, structure→surface)
- **Archetype fit:** ✓ serial per-item decision → Master-Detail, not dashboard.
- **State completeness (U9):** ✓ empty/loading/error/overflow/success all present and switchable in the harness.
- **Accessibility (U16):** decision state = icon + colour + text chip (never colour alone); keyboard-operable rows/decisions; visible focus ring; targets ≥44px; contrast from the DESIGN.md audit (panel shown in-artifact). Light + high-contrast modes inherit the audited tokens.
- **Token discipline (U3/U20):** the `:root` values are transcribed verbatim from `docs/DESIGN.md`'s audited palette — a self-contained mockup must inline its tokens; they are the tokens, not arbitrary values.
- **Focal point (DX18):** the selected proposal's detail pane.
- **No layout shift on decision (U17):** decision toggles change chip/colour, not layout.

## Highest-leverage next step
Wire the real `dream.py render` to emit `dream-data.js` in exactly this shape, so the mockup becomes the production view with one data swap.
