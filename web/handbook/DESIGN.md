---
colors:
  canvas: "#f7f4ef"
  surface: "#fcfbf8"
  subtle: "#efece6"
  ink: "#242424"
  muted: "#5c5c5c"
  border: "#8a8886"
  accent: "#b11f4b"
  focus: "#006cbe"
typography:
  body: "Segoe UI, Aptos, system-ui, sans-serif"
  heading: "Iowan Old Style, Palatino, Georgia, serif"
  code: "Consolas, Courier New, monospace"
spacing:
  small: "0.5rem"
  medium: "1rem"
  large: "1.5rem"
  section: "3rem"
rounded:
  control: "0.4rem"
motion:
  duration: "0ms"
---

# AI-Forward reader handbook

The handbook is an editorial reading surface with task-oriented reference lookup,
not a dashboard. It adopts the existing portal's warm light palette, restrained
rose accent and system serif/sans pairing. Long-form prose has a bounded measure;
the sidebar explains the learning order and search supports direct task lookup.

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
