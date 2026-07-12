---
id: design-language-docs-explorer
title: "Docs Explorer — Design Language"
type: design-language
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [design-language, docs-explorer, ui, tokens, accessibility]
links:
  - { to: design-docs-explorer-grounding-spatial-navigation, rel: refines }
  - { to: docs-index, rel: documents }
review-by: 2027-01-07
review-suggested: []
summary: >-
  Token and interaction language for the Docs Explorer knowledge portal: browse, graph,
  mind-map, deterministic Spatial 3D, and derived HTML knowledge surfaces. It defines a
  high-legibility dark/light system, selected-node focus behavior, complete visualization
  states, and the performance/accessibility floors that implementation must satisfy.
designmd_version: alpha
archetype: "DocsKnowledgeExplorer { Type:Portal; Arch:HubAndSpoke; Layout:MasterDetail; Density:Comfortable; Nav:TopBar+Sidebar+Breadcrumb; Viewport:FluidResponsive; Input:KeyboardFirst+PrecisionPointer+TouchPrimary; Color:DarkAdaptive; x-TypeStyle:Utilitarian; Depth:SoftShadow; Sync:Stateless; Persistence:Session; Feedback:Instant; Motion:Micro+Fluid; Pacing:Freeform; Transition:Morph; A11y:WCAG_2.2_AA+ReducedMotion+HighLegibility+ScreenReaderFirst; x-ProjectionSet:\"BrowseGraphMindMapSpatial3D\"; x-KnowledgeSurfaces:\"DerivedHtmlDirectory\"; }"
modes: [light, dark, high-contrast]
colors: { primary-dark: "#fd8ea1", primary-light: "#b11f4b", primary-high-contrast: "#ffff00", on-primary-dark: "#1a1a1a", on-primary-light: "#ffffff", on-primary-high-contrast: "#000000", canvas-dark: "#3d3b3a", canvas-light: "#f7f4ef", canvas-high-contrast: "#000000", surface-dark: "#343231", surface-light: "#fcfbf8", surface-high-contrast: "#000000", ink-dark: "#dedede", ink-light: "#242424", ink-high-contrast: "#ffffff", ink-mute-dark: "#a8a8a8", ink-mute-light: "#5c5c5c", ink-mute-high-contrast: "#ffffff", reduced-text-dark: "#b0b0b0", reduced-text-light: "#6f6f6f", reduced-text-high-contrast: "#ffffff", hairline-dark: "#888684", hairline-light: "#8a8886", hairline-high-contrast: "#ffffff", ghost-edge-dark: "#888684", ghost-edge-light: "#8a8886", ghost-edge-high-contrast: "#ffffff", focus-ring-dark: "#62b0ff", focus-ring-light: "#006cbe", focus-ring-high-contrast: "#ffff00", success-dark: "#4ade80", success-light: "#146c2e", success-high-contrast: "#00ff00", warning-dark: "#fbbf24", warning-light: "#8a4b08", warning-high-contrast: "#ffff00", danger-dark: "#ff9191", danger-light: "#b3261e", danger-high-contrast: "#ff8080" }
typography: { display: { fontFamily: "Segoe UI, Aptos, Calibri, sans-serif", fontSize: 22px, fontWeight: 700, lineHeight: 1.2, letterSpacing: -0.2px }, heading: { fontFamily: "Segoe UI, Aptos, Calibri, sans-serif", fontSize: 14px, fontWeight: 650, lineHeight: 1.3, letterSpacing: 0 }, body: { fontFamily: "Segoe UI, Aptos, Calibri, sans-serif", fontSize: 14px, fontWeight: 400, lineHeight: 1.5, letterSpacing: 0 }, label: { fontFamily: "Segoe UI, Aptos, Calibri, sans-serif", fontSize: 12px, fontWeight: 600, lineHeight: 1.3, letterSpacing: 0.2px }, mono: { fontFamily: "Consolas, Courier New, Courier, monospace", fontSize: 12px, fontWeight: 400, lineHeight: 1.45, letterSpacing: 0 } }
rounded: { none: 0px, sm: 5px, md: 8px, lg: 12px, pill: 9999px }
spacing: { scale: [2, 4, 8, 12, 16, 24, 32, 48] }
elevation: { flat: "none", subtle: "0 6px 24px rgba(0,0,0,0.08)", panel: "0 8px 28px rgba(0,0,0,0.06)", floating: "0 18px 48px rgba(0,0,0,0.12)" }
motion: { instant: 0ms, fast: 120ms, context: 220ms, easing: "cubic-bezier(0.2,0,0,1)" }
focus: { ring-width: 3px, ring-offset: 2px }
targets: { minimum: 44px }
breakpoints: { narrow: 720px }
limits: { index-bytes: 5242880, index-nodes: 1000, index-edges: 5000, spatial-nodes: 500, spatial-edges: 1000, visible-labels: 150, html-surfaces: 100 }
---

# Docs Explorer - Design Language

> This is the Surface token contract for the Docs Explorer. Implementation references
> mode-specific semantic tokens such as `{colors.primary-dark}`,
> `{colors.focus-ring-light}`, `{spacing.scale}`, and `{motion.context}` rather than
> introducing component-local values. The interaction/grounding behavior is defined in
> `docs/design/docs-explorer-grounding-and-spatial-navigation.md`.

## 1. Atmosphere and archetype

The Explorer is a technical content-discovery portal: quiet, high-legibility, and
content-first. Browse and details carry the hierarchy; graph, mind map, and Spatial 3D
add progressively richer spatial understanding without turning the application into a
generic dashboard or an unbounded-canvas editor. A derived Knowledge surfaces rail makes
the audit timeline and other standalone HTML knowledge tools first-class destinations.

## 2. Color roles and contrast audit

| Token | Role | On surface | Contrast | AA |
|---|---|---|---|---|
| `{colors.ink-dark}` | Dark body text | `{colors.canvas-dark}` | 8.28:1 | pass |
| `{colors.ink-mute-dark}` | Dark secondary text | `{colors.canvas-dark}` | 4.68:1 | pass |
| `{colors.reduced-text-dark}` | Dark reduced-emphasis node text | `{colors.canvas-dark}` | 5.14:1 | pass |
| `{colors.ghost-edge-dark}` | Dark dim/ghost edge | `{colors.surface-dark}` | 3.52:1 | pass |
| `{colors.primary-dark}` | Dark link/selection | `{colors.canvas-dark}` | 5.07:1 | pass |
| `{colors.focus-ring-dark}` | Dark focus indicator | `{colors.surface-dark}` | 5.57:1 | pass |
| `{colors.focus-ring-dark}` | Dark focus indicator | `{colors.canvas-dark}` | 4.87:1 | pass |
| `{colors.ink-light}` | Light body text | `{colors.canvas-light}` | 14.15:1 | pass |
| `{colors.ink-mute-light}` | Light secondary text | `{colors.canvas-light}` | 6.10:1 | pass |
| `{colors.reduced-text-light}` | Light reduced-emphasis node text | `{colors.canvas-light}` | 4.58:1 | pass |
| `{colors.ghost-edge-light}` | Light dim/ghost edge | `{colors.surface-light}` | 3.41:1 | pass |
| `{colors.primary-light}` | Light link/selection | `{colors.surface-light}` | 6.41:1 | pass |
| `{colors.focus-ring-light}` | Light focus indicator | `{colors.surface-light}` | 5.22:1 | pass |
| `{colors.focus-ring-light}` | Light focus indicator | `{colors.canvas-light}` | 4.92:1 | pass |
| `{colors.ink-high-contrast}` | High-contrast body text | `{colors.canvas-high-contrast}` | 21.00:1 | pass |
| `{colors.primary-high-contrast}` | High-contrast action/focus | `{colors.canvas-high-contrast}` | 19.56:1 | pass |
| `{colors.hairline-high-contrast}` | High-contrast essential boundary | `{colors.canvas-high-contrast}` | 21.00:1 | pass |
| `{colors.reduced-text-high-contrast}` | High-contrast reduced-emphasis text | `{colors.canvas-high-contrast}` | 21.00:1 | pass |
| `{colors.ghost-edge-high-contrast}` | High-contrast ghost edge | `{colors.canvas-high-contrast}` | 21.00:1 | pass |
| `{colors.focus-ring-high-contrast}` | High-contrast focus indicator | `{colors.canvas-high-contrast}` | 19.56:1 | pass |
| `{colors.on-primary-high-contrast}` | High-contrast action label | `{colors.primary-high-contrast}` | 19.56:1 | pass |
| `{colors.on-primary-dark}` | Dark action label | `{colors.primary-dark}` | 7.92:1 | pass |
| `{colors.on-primary-light}` | Light action label | `{colors.primary-light}` | 6.63:1 | pass |
| `{colors.hairline-dark}` | Dark essential boundary | `{colors.surface-dark}` | 3.52:1 | pass |
| `{colors.hairline-light}` | Light essential boundary | `{colors.surface-light}` | 3.41:1 | pass |
| `{colors.success-dark}` | Dark success text/icon | `{colors.canvas-dark}` | 6.39:1 | pass |
| `{colors.warning-dark}` | Dark warning text/icon | `{colors.canvas-dark}` | 6.67:1 | pass |
| `{colors.danger-dark}` | Dark danger text/icon | `{colors.canvas-dark}` | 5.15:1 | pass |
| `{colors.success-light}` | Light success text/icon | `{colors.canvas-light}` | 5.96:1 | pass |
| `{colors.warning-light}` | Light warning text/icon | `{colors.canvas-light}` | 6.19:1 | pass |
| `{colors.danger-light}` | Light danger text/icon | `{colors.canvas-light}` | 5.96:1 | pass |
| `{colors.success-high-contrast}` | High-contrast success | `{colors.canvas-high-contrast}` | 15.30:1 | pass |
| `{colors.warning-high-contrast}` | High-contrast warning | `{colors.canvas-high-contrast}` | 19.56:1 | pass |
| `{colors.danger-high-contrast}` | High-contrast danger | `{colors.canvas-high-contrast}` | 8.65:1 | pass |

Type/status colors never carry meaning alone; labels, icons, and relationship text are
always present. Reduced emphasis uses the audited `reduced-text-*` and `ghost-edge-*`
tokens, never opacity compositing. At Neighborhood zoom, unrelated-node labels are
hidden rather than rendered below text contrast; their shapes and relationships remain
available through the audited graphical tokens and the equivalent relationship list.

## 3. Typography

| Token | Use |
|---|---|
| `{typography.display}` | Project/title and primary selected/context-node title. |
| `{typography.heading}` | Panel headings and grouped relationship labels. |
| `{typography.body}` | Summaries, descriptions, and guidance. |
| `{typography.label}` | Node labels, chips, status, and relation types. |
| `{typography.mono}` | Paths, IDs, hashes, and diagnostic values. |

Full selected-node titles remain visible at every zoom. Unselected labels are subject
to semantic-zoom priority and truncation with an accessible full name.

## 4. Components and complete states

| Component | default | hover | focus | active | disabled | loading | empty | error | success | first-run / overflow |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Projection tab | surface label | mode primary tint | mode focus ring | primary underline | unavailable explanation | keep current view | Browse remains | route to Browse | active projection | horizontally scroll tabs |
| Interactive toolbar/path/menu control | semantic label | mode primary tint | mode focus ring | pressed marker | reason exposed | preserve current view | omit unavailable action | inline alert + recovery | status announcement | menu scrolls; label never clips |
| Browse tree item | title/type | emphasized surface | mode focus ring | selected marker | unavailable group | skeleton row | "No artifacts in this group" | show-all recovery | expanded/selected | wrap label; index limit prevents unbounded DOM |
| Breadcrumb/context trail | link text | underline | mode focus ring | current item | unavailable ancestor | retain prior trail | project root | return to Browse | URL state represented | collapse middle items to menu |
| Filter control | semantic value | mode tint | mode focus ring | applied marker | unavailable value | preserve results | "No filters available" | clear invalid stored filter | active count | long value list scrolls |
| Search | hairline input + Previous/Next | brighter hairline | mode focus ring | query text | n/a | incremental local match | `No search results for "<query>". The graph remains unchanged.` | clear query | match count | no suggestion/listbox state; results remain in Browse |
| Node | type shape plus title | emphasized outline | full-strength mode focus ring independent of node emphasis | selected outline | audited reduced-emphasis tokens outside context | stable placeholder | n/a | warning badge | context halo | label ceiling and LOD |
| Relationship path/list row | directed line/text | emphasized path | mode focus ring | traced relation | outside path dimmed | n/a | "No path found" | canonical list fallback | traced path | browser limits keep the complete list bounded |
| Detail panel | metadata and actions | n/a | internal focus order | selected section | unavailable actions explained | skeleton metadata | "Select an artifact" | metadata-only fallback | source ready | vertical scroll; no clipping |
| Explore action | mode primary button | stronger tint | mode focus ring | pressed | no selection | N/A - neighborhood projection is synchronous | n/a | "Could not explore" | context announcement | browser history preserves state |
| Route Back action | text button | underline | mode focus ring | pressed | root route | preserve title | n/a | return to Browse | focus restored | always first action on narrow route |
| Knowledge surface card | title, kind, destination | stronger boundary | mode focus ring | destination opens | unsafe/missing path omitted | stable directory remains | "No standalone knowledge surfaces" | omit invalid entry + keep graph | destination available | wraps path; directory remains searchable |
| Spatial 3D viewport | deterministic perspective constellation | highlighted node | full-strength node/control focus ring | selected node becomes camera target | reason shown | current frame remains | use graph empty state | Graph fallback with state preserved | orbit/zoom/focus controls available | native renderer only; list parity always follows |

## 5. Layout and spacing

Desktop uses a Master-Detail composition beneath a compact Knowledge surfaces rail:
browse/navigation, visualization stage, and detail panel. Spacing uses `{spacing.scale}`
only. The visualization is the focal point only after the user explicitly enters Graph,
Mind map, or Spatial 3D; Browse is the default orientation surface.

Narrow screens use one content column. Visualization opens as a full-screen route and
Details opens as the next URL-addressable route. Browser Back restores the prior route
and keyboard focus to its initiating control.

## 6. Elevation, shape, and motion

Panels use `{rounded.md}` with `{elevation.subtle}`, `{elevation.panel}`, or
`{elevation.floating}` according to depth; graph nodes use `{rounded.sm}`.
Focus indicators use `{focus.ring-width}` and `{focus.ring-offset}`. Interactive targets
use `{targets.minimum}`. Selection feedback uses `{motion.fast}`. Graph and Mind map fit
their selected context instantly. Spatial 3D uses one restrained `{motion.context}`
camera transition when a selected node becomes the target; manual orbit and zoom remain
user-driven. Reduced-motion and high-contrast modes use `{motion.instant}` with no
camera flight, spring, parallax, pulsing, or fog animation.
Node emphasis never changes focus-ring opacity, color, width, or offset. The
`{targets.minimum}` floor applies to operable HTML controls and relationship-list rows;
non-interactive overview glyphs may be smaller and never become the sole operable path.

## 7. UI copy

- Primary action: **Explore neighborhood**
- Exit action: **Leave neighborhood**
- Search empty: **No search results for "<query>". The graph remains unchanged.**
- Filter empty: **No artifacts match these filters. Clear filters**
- No selection: **Select an artifact to inspect its context**
- Grounding warning: **Some context is stale or incomplete. Review warnings before using it**
- 3D fallback: **DOC.SPATIAL3D.UNAVAILABLE Spatial 3D is unavailable. The same semantic state is shown in Graph**
- Knowledge surfaces empty: **No standalone knowledge surfaces were discovered**
- Offline diagrams: **Enhanced diagrams are offline. Source text is still available**

## 8. Modes

- `dark`: native `prefers-color-scheme: dark` workspace using `{colors.canvas-dark}`
  and `{colors.surface-dark}`.
- `light`: native browser-default/light workspace using `{colors.canvas-light}` and
  `{colors.surface-light}` with `{colors.focus-ring-light}`.
- Theme selection follows the browser/OS preference only; query-string overrides and
  render-blocking theme bootstrap scripts are not part of the contract.
- `high-contrast`: black/white surfaces, `{colors.primary-high-contrast}` actions,
  `{colors.hairline-high-contrast}` boundaries, no shadows, and
  `{colors.focus-ring-high-contrast}` focus. Under `forced-colors: active`, use system
  colors (`Canvas`, `CanvasText`, `LinkText`, `Highlight`, `HighlightText`) and
  `forced-color-adjust:auto`; do not preserve authored status colors.

## 9. Performance budget

- Usable 2D shell: <=2.0s p75 under the paired design's benchmark environment.
- Selection/search feedback: <=100ms.
- Initial supported-size layout: <=500ms.
- Navigation: 60fps target and 30fps floor.
- Visible labels: <={limits.visible-labels} through semantic zoom.
- HTML knowledge surfaces: <={limits.html-surfaces}; derivation and the browser both
  fail closed above the ceiling.
- Spatial pointer/wheel projection updates are coalesced through one animation frame
  and reuse cached node/edge references; rerender and lost capture clear drag state.
- Spatial 3D uses no additional runtime dependency and must meet the same interaction
  budget within its explicit node/edge ceiling.
- Mermaid is lazy-loaded; its failure cannot block local navigation.

## 10. AI surface

The Explorer does not generate content with AI. It is a grounding and provenance
surface for agents. Trust-builder behavior therefore centers on exact source paths,
line ranges, hashes, health warnings, and clear separation of evidence from summaries.

## 11. Do and do not

- Do keep Browse and the relationship list usable without spatial navigation.
- Do preserve selection, neighborhood context, filters, and browser history across
  projections.
- Do derive standalone HTML destinations from the docs tree instead of hardcoding a menu.
- Do make selected-node focus explicit in Spatial 3D and keep equivalent keyboard/list paths.
- Do use directed edges, relation labels, and inverse readings.
- Do not use 3D, motion, color, or proximity as the only carrier of information.
- Do not let camera position, depth, or visual distance influence grounding traversal.
- Do not remove nodes while searching; filtering is a separate explicit action.
- Do not show all labels and edge text at every zoom.

## 12. Responsive behavior

Interactive targets remain at least `{targets.minimum}` square. At
`{breakpoints.narrow}` and below, move from
three simultaneous regions to Browse -> Visualization -> Details flow. Graph controls
stay in document order; an explicit Back action is first; browser Back restores the
initiating control. The selected-node title remains visible.

## 13. Agent implementation guide

- Read the paired design before changing graph behavior.
- Reference these tokens and complete states directly.
- Preserve the accessible non-spatial list before adding visual enhancement.
- Run `design-lint.py` after token changes.

## 14. Provenance

This design language specializes the repository's existing dark technical surface. It
does not clone an external brand. The contrast audit, complete states, mode behavior,
derived knowledge-surface directory, selected-node context, and native deterministic
Spatial 3D rules are project-specific.
