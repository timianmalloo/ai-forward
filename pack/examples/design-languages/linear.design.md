---
# ── Graph record (V2) ──
id: example-design-language-linear
title: "Example — Linear-style Design Language (worked, floor-extended)"
type: design-language
status: accepted
owner: "@ai-forward"
tags: [design-language, example, ui, tokens]
links:
  - { to: ui-interaction-design, rel: refines }
  - { to: ui-archetype-catalog, rel: relates-to }
review-by: 2026-12-31
summary: >-
  A worked, condensed exemplar of the pack's design-language artifact: the Stitch
  DESIGN.md format seeded from Linear's public design language (awesome-design-md, MIT)
  and EXTENDED with the pack's floors — a contrast audit (which surfaces a real
  borderline CTA finding), the complete component-state set, theme modes, the paired
  UI Archetype Signature (B1 KeyboardVelocity), motion, and a performance budget.
# ── Design-language record (Stitch DESIGN.md) ──
designmd_version: alpha
archetype: "KeyboardVelocity { Type:OLTP; Arch:SPA; Layout:MasterDetail; Density:Compact; Nav:CommandPalette+Sidebar; Input:KeyboardFirst+PrecisionPointer; Color:DarkAdaptive; Sync:LocalFirst; Feedback:Optimistic; Pacing:Freeform; A11y:WCAG_2.2_AA; }"
modes: [dark, light]
colors:
  primary: "#5e6ad2"
  primary-hover: "#828fff"
  on-primary: "#ffffff"
  canvas: "#010102"
  surface-1: "#0f1011"
  ink: "#f7f8f8"
  ink-subtle: "#8a8f98"
  ink-tertiary: "#62666d"
  hairline: "#23252a"
  focus-ring: "#5e69d1"
  success: "#27a644"
  danger: "#eb5757"
typography:
  display-xl:
    fontFamily: "Linear Display, SF Pro Display, system-ui, sans-serif"
    fontSize: 80px
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: -3.0px
  body:
    fontFamily: "Linear Text, SF Pro Text, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: -0.05px
  button:
    fontFamily: "Linear Text, SF Pro Text, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: 0
rounded: { sm: 6px, md: 8px, pill: 9999px }
spacing: { scale: [4, 8, 12, 16, 24, 32, 48, 64] }
motion: { fast: 120ms, base: 200ms, easing: "cubic-bezier(0.2,0,0,1)" }
---

# Example — Linear-style Design Language (worked & floor-extended)

> A **demonstration** of the pack artifact: Linear's public surface vocabulary
> (seeded from `awesome-design-md`, MIT — see `ATTRIBUTION.md`) with the pack's
> **floors added**. Lints clean: `python docs/ai-forward-pack/scripts/design-lint.py
> examples/design-languages/linear.design.md`. **Adapt, don't clone** (U12) — this is
> a starting point to specialize, not a brand to copy.

## 1. Overview & paired archetype
Near-black, software-craft canvas: `{colors.canvas}` with `{colors.ink}` light-gray
type and a single chromatic accent, `{colors.primary}` lavender-blue, used only on the
brand mark, focus rings, and a few CTAs. It pairs with the **B1 KeyboardVelocity**
archetype (`archetype:` above) — compact density, command-palette nav, optimistic
local-first data — so the build is that *kind*, not a generic dashboard.

## 2. Color palette & roles — contrast audit (U16/U3)
| Token | Hex | Role | On | Contrast | AA |
|---|---|---|---|---|---|
| `{colors.ink}` | #f7f8f8 | Body / headline | `{colors.canvas}` | ~19.5:1 | **pass** |
| `{colors.ink-subtle}` | #8a8f98 | Tertiary / deselected | `{colors.canvas}` | ~6.6:1 | **pass** |
| `{colors.ink-tertiary}` | #62666d | Disabled / footnote | `{colors.canvas}` | ~3.4:1 | **fail (normal)** — large/UI only |
| `{colors.on-primary}` | #ffffff | CTA label | `{colors.primary}` | ~4.3:1 | **borderline** — passes large (3:1), under 4.5 for small text |
| `{colors.focus-ring}` | #5e69d1 | Focus ring | `{colors.canvas}` | >=3:1 | **pass (UI)** |

> **Finding the raw DESIGN.md misses:** the CTA label is ~4.3:1 — under AA for small
> text. Disposition: render `{typography.button}` at >=14px **500 weight** (large-text
> threshold) or darken `{colors.primary}` one step. And `{colors.ink-tertiary}` is
> sub-AA — never use it for essential body text, only disabled/decorative.

## 3. Typography
`{typography.display-xl}` (80px/600, -3px tracking — the brand's aggressive negative
tracking) down to `{typography.body}` (16px/400) and `{typography.button}` (14px/500).
One continuous voice from display to body. Substitute: SF Pro / system-ui.

## 4. Components & the complete state set (U9)
| Component | default | hover | focus | disabled | **loading** | **empty** | **error** | **success** |
|---|---|---|---|---|---|---|---|---|
| Button (primary) | `{colors.primary}` `{rounded.md}` | `{colors.primary-hover}` | `{colors.focus-ring}` ring | `{colors.ink-tertiary}` 40% | inline spinner, label->"Saving..." | — | shake + `{colors.danger}` border | brief `{colors.success}` check |
| Input | `{colors.hairline}` border | — | `{colors.focus-ring}` ring | dimmed | — | placeholder = real copy (S6) | `{colors.danger}` border + message | — |
| Issue list (master-detail) | rows on `{colors.surface-1}` | row hover lift | row focus ring | — | **skeleton rows** | **"No issues — press C to create"** | **"Couldn't load — Retry"** | virtualize > 50 rows |

## 5. Layout, elevation, motion
Compact density; spacing via `{spacing.scale}` rungs only. Surfaces step
canvas->`{colors.surface-1}` for elevation (dark UI uses lightness, not shadow).
**Motion (U10):** `{motion.fast}` for state changes, `{motion.base}` for panel
transitions, `{motion.easing}`; **`prefers-reduced-motion` -> cross-fade only, no
transform/slide.**

## 6. UI copy (U11)
CTA: "Start building". Empty issue list: "No issues yet — press **C** to create one".
Error: "We couldn't load your issues. **Retry**." (humane, actionable, keyboard-hinted —
fits the KeyboardVelocity archetype).

## 7. Modes (U4)
`dark` is canonical (`{colors.canvas}` near-black). `light` inverts the semantic layer
(canvas->white, ink->near-black) — same components, no forks. High-contrast mode lifts
`{colors.ink-tertiary}` to an AA-passing value.

## 8. Performance budget (U17)
Interaction latency < 50ms (the archetype's whole point — "zero layout shift on
render"); command-palette open < 100ms; route transition < 200ms; optimistic local
mutation reflects instantly, reconciles in the background.

## 9. Provenance & adapt-don't-clone (U12)
Seeded from Linear's public design language via **awesome-design-md** (MIT,
voltagent/awesome-design-md) — see `ATTRIBUTION.md`. The contrast audit, the complete
state set, the modes, the archetype pairing, the motion/perf floors are the pack's
**additions**. Do not ship a Linear clone; adapt this vocabulary to your product.
