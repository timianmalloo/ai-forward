---
id: proof-github-pages-handbook-ui
title: "GitHub Pages handbook UI proof"
type: proof-pack
status: verified
owner: "@timianmalloo"
phase: documentation
tags: [proof, handbook, ui, accessibility, browser]
links:
  - { to: mockup-github-pages-handbook, rel: relates-to }
  - { to: design-reader-first-handbook, rel: relates-to }
review-by: "2026-12-22"
summary: >-
  Browser, generator, security, accessibility, and mutation evidence for the elevated
  AI-Forward Pages handbook. It records the red-before-green observations for semantic
  diagram rendering and diagram contrast, then ties them to the integrated gate results.
---

# GitHub Pages handbook UI proof

## Proof boundary

This proof covers the canonical `web/handbook/` sources, the generated
`docs/portal/index.html` surface, and the byte-identical
`docs/mockups/github-pages-handbook.html` review build. It does not claim a broad user
comprehension study or native screen-reader study.

## Red before green

| Contract | Red observation | Green observation | Oracle |
|---|---|---|---|
| Semantic diagrams render and stay responsive | Before renderer/content implementation, `npx playwright test tests/docs_explorer/handbook.spec.js --grep "relationship diagrams"` failed in Chromium, Firefox, and WebKit because the named figure did not exist. | The same focused proof passed in all three engines after implementation. | Overview path and knowledge loop are labelled figures; coordination is full-width → two-column branch → full-width join on desktop and one column on mobile; no page overflow. |
| Malformed diagram degrades safely | New malformed-input proof had no prior implementation path. | The focused browser proof passes in all three engines: no figure is produced and escaped source remains in `pre code.language-diagram`. | A malformed or incomplete fence never becomes plausible diagram output. |
| Diagram palette remains readable | Mutation changed light `--accent-soft` from `#f5dce5` to `#625c55`. Chromium failed `light diagramLabel` at **1.63:1**. | Restoring the accepted token made the expanded light/dark contrast matrix pass in Chromium, Firefox, and WebKit. | Every sampled foreground/surface pair is at least 4.5:1: body, eyebrow, article link, brand mark, diagram label/body, active navigation, and raised-surface muted label. |
| Diagram source is inert data | Hostile diagram title/detail includes image and script-shaped text. | All three engines keep `window.handbookInjected` undefined, create no unsafe link/image, and make no external request. | Renderer escapes every diagram field before inserting generated HTML. |
| Mobile discovery stays compact and operable | Independent review of the first elevated build found the mobile search block always visible and primary route targets at 40 px. | Search now collapses with the navigation disclosure and every primary route is at least 44 px tall at 390 px width. | The browser test measures both conditions on the rendered surface; the final independent review rechecks the same viewport. |

The contrast mutation was temporary and was reverted before the green run. It is not
present in the committed source.

## Integrated evidence

| Check | Result |
|---|---|
| `python -m unittest tests.docs_explorer.test_handbook` | 4 passed |
| `npx playwright test tests/docs_explorer/handbook.spec.js` | 33 passed across Chromium, Firefox, WebKit after the diagram proof additions |
| `python docs/ai-forward-pack/scripts/design-lint.py --strict web/handbook/DESIGN.md` | clean; zero warnings |
| `python docs/ai-forward-pack/scripts/ui-craft-gate.py --gate --a11y-obligation --markdown docs/portal/index.html` | non-empty corpus; one Minor `flat-type-hierarchy`, no Major/Blocker |
| `python tools/build-handbook.py` | 43 pages, 28 skills, 39 knowledge docs; deterministic public/review HTML; 241,944 bytes |

The craft detector's remaining hierarchy finding does not recognize the CSS-variable
heading scale. Rendered headings use a 42.4–76 px H1, 30.4 px H2, 20 px H3, 19.2 px
lead, and 16 px body. This is retained as a reported detector limitation rather than
laundered with an unrelated token or suppression.

## Residual risk

The independent UX review covers representative desktop/mobile and light/dark states.
A screen-reader-user study and comprehension study across a broad reader population
remain unperformed; passing mechanical accessibility checks does not make either claim.
