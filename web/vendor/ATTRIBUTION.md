# Vendored third-party runtime — attribution

FR-051. These files were previously loaded from `unpkg.com` at runtime by
`web/ai-forward-pack-explainer.html`. That made the project's public front door fail closed on a
CDN outage and trusting on a CDN compromise — on the one surface that has already rendered blank
once (defect classes **PACK-G**, **PACK-H**), in a pack whose own standard is dependency-free
self-contained HTML (**V9**, **DX8**). They are now committed and loaded by relative path, so the
page renders with the network blocked.

They are **unmodified vendor builds**. Do not edit them; to upgrade, re-download from the URL
below, re-run `node tools/verify-explainer-render.js`, and record the new version here.

| File | Package | Version | Licence | Source URL |
|---|---|---|---|---|
| `react.production.min.js` | react | 18 (UMD production build) | MIT | `https://unpkg.com/react@18/umd/react.production.min.js` |
| `react-dom.production.min.js` | react-dom | 18 (UMD production build) | MIT | `https://unpkg.com/react-dom@18/umd/react-dom.production.min.js` |
| `htm.umd.js` | htm | 3.1.1 (UMD build) | Apache-2.0 | `https://unpkg.com/htm@3.1.1/dist/htm.umd.js` |

**React** and **React DOM** are © Meta Platforms, Inc. and affiliates, released under the MIT
licence. The licence header is preserved verbatim at the top of each file.

**htm** is © Jason Miller, released under the Apache License 2.0.

Retrieved 2026-08-22. Verified by `tools/verify-explainer-render.js`, which asserts the bundles
load, define their globals, and that no third-party origin remains in the page.
