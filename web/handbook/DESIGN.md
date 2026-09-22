---
colors:
  canvas: "#f5f0e8"
  surface: "#fffaf3"
  surface-raised: "#fffdf9"
  subtle: "#ebe4da"
  ink: "#211f1c"
  muted: "#625c55"
  border: "#8b8177"
  border-soft: "#d8cec2"
  accent: "#a51f4c"
  accent-strong: "#781436"
  accent-soft: "#f5dce5"
  focus: "#005ea8"
typography:
  body: "Segoe UI, Aptos, system-ui, sans-serif"
  heading: "Iowan Old Style, Palatino, Georgia, serif"
  code: "Consolas, Courier New, monospace"
spacing:
  xsmall: "0.3rem"
  small: "0.55rem"
  medium: "1rem"
  large: "1.6rem"
  section: "3.4rem"
rounded:
  compact: "0.25rem"
  control: "0.5rem"
  brand: "0.75rem"
  panel: "1rem"
  pill: "999px"
motion:
  duration: "0ms"
---

# AI-Forward reader handbook

The handbook is an editorial reading surface with task-oriented reference lookup,
not a dashboard. It uses a warm paper canvas, a restrained rose accent and a
system serif/sans pairing. Long-form prose has a bounded measure; the sidebar
explains the learning order and search supports direct task lookup.

## Direction brief

- **Reader and arrival state:** a capable engineer who is curious about agentic work
  and cautious about losing control, quality, or project context.
- **Job to be done:** understand the method, choose the right workflow, and begin one
  bounded task without reading the whole repository.
- **Archetype signature:** `Handbook { Type:Portal; Arch:HubAndSpoke; Layout:ReadingRail;
  Density:Comfortable; Nav:Header+Sidebar+Search+Contents; Viewport:FluidResponsive;
  Input:KeyboardFirst+Pointer+Touch; Color:WarmAdaptive; TypeStyle:EditorialTechnical;
  Sync:Static; Persistence:URL; Feedback:Instant; Motion:None;
  A11y:WCAG_2.2_AA+ReducedMotion+ForcedColors; }`.
- **Qualities:** calm, exact, human. Their opposites are ornamental, vague, and
  corporate.
- **References:** adapt MDN Learn's structured path from orientation to core material,
  and Django's clear separation of tutorial, topic guide, and reference. Preserve the
  handbook's own voice and information architecture.
- **Anti-goals:** a marketing landing page, a card dashboard, an animated network,
  decorative illustration, or a second navigation model.
- **Type, color, space:** editorial serif headings make reading landmarks distinct;
  rose marks action and position; layered warm neutrals create depth with borders and
  spacing before shadow.

## Relationship diagrams

The handbook may use a semantic `diagram` fence for relationships that are harder to
scan in prose. The first line is `<kind> | <title>` and each remaining line is
`<step> | <heading> | <explanation>`. Supported kinds are `path`, `cycle`, and
`branch`. Rendering produces a labelled `figure` containing an ordered list, so the
text, sequence, and reading order remain available without color, motion, or a canvas.

Use a diagram only when it explains at least three dependent steps, a loop, or a
branch. It supplements the prose. It does not carry unique instructions, and it must
remain a readable code block if enhanced rendering is unavailable.

## Interaction contract

- First visit opens the newcomer overview, never a skill-count dashboard.
- Chapter links, skill links and previous/next links are ordinary bookmarkable links.
- Search matches titles, summaries and body text; results identify guide versus skill.
- No-results explains how to broaden the query and leaves navigation usable.
- Unknown page addresses show a recovery path rather than silently rendering a
  different page as success.
- Missing/malformed data has an announced error and plain-source fallback.
- Raw Markdown HTML and unsafe link schemes do not execute.
- JavaScript-unavailable readers get the purpose statement and source links.

The old portal remains an explicitly secondary engineering reference. Old public
entry anchors map to the equivalent handbook topic.

## Accessibility and responsive reading

Use native links, inputs and a mobile navigation disclosure; visible focus and a
skip link; one primary heading per page; semantic lists/tables; labelled navigation,
search and contents. Search status is politely announced. Route changes move focus
to the page heading; typing in search does not steal focus. At narrow widths the
layout becomes one column, prose and code remain readable, and only code/table
regions may scroll horizontally.

Dark mode follows the system preference using the prior portal's dark palette.
Forced-colors mode uses system colors. There is no decorative animation, and reduced
motion is respected. No information depends on color alone.

Diagram connectors are decorative. The ordered-list numbering and headings carry the
meaning. At narrow widths every diagram becomes one vertical list with no horizontal
scroll. Forced-colors mode removes authored fills and keeps explicit boundaries.

## Component states

| Component | Default | Hover / focus | Loading | Empty | Error | Overflow |
|---|---|---|---|---|---|---|
| Header and quick routes | brand, short descriptor, four routes | underline plus focus ring | stable shell | N/A | routes remain ordinary links | routes wrap below the brand |
| Sidebar search | query field and clear action | border emphasis plus focus ring | local index already embedded | no-results guidance | content error is announced above the article | result summaries wrap |
| Article | eyebrow, title, lead, section rhythm | linked text thickens underline | initial fallback content remains | unknown route offers overview recovery | plain-source recovery | code and tables scroll within labelled regions |
| Relationship diagram | labelled semantic figure and ordered steps | no diagram-only interaction | source fence remains until parse | malformed/short fence stays a code block | escaped text, never executable HTML | horizontal kinds collapse to a vertical list |
| Previous / next | directional links with destination title | raised surface plus focus ring | N/A | missing side is omitted | remaining route stays usable | long titles wrap |

## Motion inventory

There is no authored animation. Hover, focus, theme, route, and diagram state changes
are immediate. Reduced motion therefore matches the default behavior.

## Copy added by this section

| Surface | Copy |
|---|---|
| Header descriptor | `A field guide for dependable agentic engineering` |

## Reader and verification budget

The public runtime has zero third-party script or asset requests, no analytics and
no model calls. Its complete embedded HTML should remain below 1 MiB. Search should
respond without a network request. The real built surface serves as the reviewable
prototype; browser tests provide the persona/viewport/state/theme harness rather
than a second hand-maintained visual mockup.

Required checks include text contrast, keyboard use, mobile overflow, missing/empty
search states, malformed routes, source-content injection, coverage of every skill
and knowledge area, and a fresh-reader task review. Mechanical scores alone do not
establish that the explanation is understandable.
