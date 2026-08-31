---
id: design-marker-completeness-lint
title: "Marker completeness lint (Tier-1 prose→structure) — Design"
type: design
status: accepted
owner: "@timianmalloo"
phase: "1"
tags: [prose-to-structure, markers, no-guessing, solution-selection-ladder, lint]
links:
  - { to: design-agent-focus-controls, rel: relates-to }
review-by: 2026-11-30
summary: >-
  Tier-1 of the prose→structure review: give the assume: (NG4) and simplify: (L5)
  inline markers an enforced field-completeness check via a new marker-lint.py, using
  backward-compatible semantic-cue detection (trigger / confirm / consequence) that
  warns on legacy free-form rather than mandating a new label syntax.
---

# Marker completeness lint — Design

## Input (spec)
The approved **Tier-1** recommendation of `docs/proposals/prose-to-structure-review.html`:
promote the `assume:` (NG4) and `simplify:` (L5) markers from *prose-only field specs* to
an **enforced** field-completeness contract, warning on legacy free-form (V16a: a suggestion
warns, a defect fails). That proposal is the specify-layer artifact for this work.

## The design decision that grounding changed (a finding)
The proposal *sketched* a rigid multi-line label syntax (`confirms-when:` / `breaks-if:` /
`ceiling:` / `upgrade-when:`). Reading the actual code (E15) showed that would be wrong:

- The existing harvest regex (`dream.py:grep_markers`) captures **only the marker's first
  line**, and the canonical `assume:` marker in NG4 **spans three lines** (belief / breaks-if
  / Confirm). A multi-line label syntax breaks the regex.
- Every existing marker in the tree (`coord-core.py`, etc.) is single-line **free prose** with
  the fields woven in via an em-dash clause and `if`/`when`/`Confirm:` cues. A new syntax
  invalidates all of them for no correctness gain.
- The directives already name the *rot* precisely — L5/L6: "a marker that names **no
  trigger**"; NG4: no "confirmation route and a consequence." The failure to catch is
  **semantic absence**, not label absence.

So the design checks for the **semantic components** the directives already require, which
keeps every existing marker valid and the harvest regex intact. This is the Solution-Selection
Ladder applied to itself: the smallest change that enforces the existing contract.

## Contract
`scripts/marker-lint.py [--root DIR] [--gate] [--json] [--include-md] [paths...]`

- Walks code files (`.py .ps1 .ts .js .cs .go .rs`; `.md` only with `--include-md`), skipping
  generated/vendored trees (`.git node_modules dist _site .claude .github` + any path under
  `ai-forward-pack` or `dreams`) — the same skip set as the harvest.
- For each `simplify:` / `assume:` / `ponytail:` marker it assembles the **marker block** (the
  marker line + immediately-following continuation comment lines, stopping at the first
  non-comment line or the next marker) and classifies it:

| Marker | Required semantic components | Finding when missing |
|---|---|---|
| `simplify:` / `ponytail:` | a **trigger** (revisit condition) | `simplify-no-trigger` |
| `assume:` | a **confirm route** AND a **breaks-if consequence** | `assume-no-confirm` / `assume-no-consequence` |

- Detection is word-boundary keyword cues (trigger: `when if once upgrade revisit beyond above
  exceeds grows becomes reaches past until unless`; confirm: `confirm verify check inspect test
  measure read query run`; consequence: `if breaks false otherwise wrong shifts fails corrupts
  silently would`). These match the existing NG4/L5 example markers exactly.
- **Exit posture (V16a / docs-graph `--gate` pattern):** default = report + **exit 0** (warn,
  grandfathers legacy). `--gate` = exit 1 on any finding. `--json` for machine use. A clean
  scan of a non-empty corpus prints an "all N markers complete" line so an empty run is
  distinguishable from a clean one (E14).

## Why not wire it into verify-bundle as a hard gate
Warn-on-legacy (V16a) is the explicit posture, and a hard gate would (a) fail on any pre-
existing triggerless marker and (b) risk flagging the directive examples themselves. It ships
as a first-class harvest command (the L6 "natural follow-up") the `/investigate` and `/dream`
flows call; a repo may opt into `--gate` in its own CI.

## Directive edits
- **NG4 / NG9** — name the completeness check as the enforcement surface for the three fields.
- **L5 / L6** — the harvest is now a first-class command; the triggerless marker is what it flags.

## Failure modes
- **Continuation over-capture** (swallowing an unrelated following comment) → bounded: stop at
  first non-comment line or the next marker; tested.
- **Keyword false-positive inside a word** (`if` in `verify`) → word boundaries; tested.
- **Self-reference** (the lint's own tests contain marker-like fixtures) → tests run against a
  tmp `--root`, never the repo; `.md` excluded by default so directive examples are not scanned.
- **Empty corpus reads as clean** → explicit "0 markers found" vs "N complete" (E14).
