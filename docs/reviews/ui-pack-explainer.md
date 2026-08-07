---
id: ui-review-pack-explainer
title: "UI review — AI-Forward Pack Explainer"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [ui-review, ux, accessibility, supply-chain, explainer]
links:
  - { to: ui-capability-guide, rel: relates-to }
  - { to: docs-index, rel: relates-to }
review-by: 2026-11-05
summary: >-
  Review of web/ai-forward-pack-explainer.html, triggered by the question "can Higgsfield
  beautify this?". Measurement says no: the public surface renders blank without three
  un-hashed CDN scripts, has no focus styling, ARIA or reduced-motion, and carries 166 hex
  colours against 20 tokens. Imagery is not the lever. Inlining the runtime is.
---

# UI review — AI-Forward Pack Explainer

*Produced by `/ui-design` (mode: **review**). Governed by `ui-design-craft.md` DX22–DX25 over the floors in `ui-interaction-design.md` (U1–U20). Every finding carries location · dimension · severity · evidence · fix · confidence.*

**Surface reviewed:** `web/ai-forward-pack-explainer.html` (79 KB) — the public interactive explainer. Sibling `web/index.html` (10 KB) noted but not reviewed.
**Reviewed against:** no spec Part B/C exists for this surface · **no `DESIGN.md` governs `web/`** (finding F5) · archetype inferred, not recorded (finding F4)
**Reviewers:** UX & Accessibility (lead, a11y hard veto) · UX Researcher/IA · The Simplifier · Security & Identity (supply chain) · SRE (availability)
**Date:** 2026-08-07 · **Mode:** review

**Why this review happened.** The question asked was *"does this let me use Higgsfield to beautify the website?"* Rather than answer from taste, the skill's own rule applies: **measure before you diagnose** (DX23). The measurement changed the answer.

---

## 1. Verdict

> **BLOCK** — the public-facing surface renders **blank** without three third-party CDN scripts that carry no integrity hashes, and it meets none of the keyboard, ARIA or reduced-motion floors.
> **Highest-leverage change:** **inline the runtime** — drop React/ReactDOM/htm for the local DOM approach the audit viewer already migrated to in revision 17. One change fixes availability, closes the supply-chain hole, and makes the surface statically scannable so the remaining findings become visible at all (DX25).

| | Count |
|---|---|
| Blockers (sev 4, or any a11y ≥3) | **4** |
| Majors (sev 3) | 2 |
| Minors (sev 2) | 3 |
| Nits (sev 1) | 0 |

**Accessibility veto: BLOCK.** Clears when the surface has a visible focus indicator on every interactive element, correct semantics/labelling, a `prefers-reduced-motion` path for its transitions, and a verified contrast audit. **Not cleared by the author** — this review is the adversarial pass; the fixes need their own reviewer.

---

## 2. Measurements (DX23 — measure before you diagnose)

| Metric | Value | Note |
|---|---|---|
| Body bytes | 68,522 | — |
| **Body bytes with `<script>` removed** | **216** | The surface is entirely runtime-generated |
| **Visible text without JS** | **144 chars** | Blank page without the CDN |
| External `<script src>` | 3 | React 18, ReactDOM 18, htm 3.1.1 — all `unpkg.com` |
| **SRI `integrity=` attributes** | **0** | No pinning of what those scripts contain |
| External hosts referenced | 12 | 3 runtime, the rest are legitimate exemplar links |
| Sections / h1 / h2 / h3 | 9 / 1 / 8 / 17 | Heading hierarchy is sound |
| Interactive controls | 16 (2 button, 14 link) | Modest and appropriate |
| `fetch`/XHR on load | 0 | Good — no data round-trips |
| **Distinct hex colours** | **166** | Against 20 CSS custom properties |
| `var(--…)` references | 118 | A token system exists and is heavily bypassed |
| **Distinct `font-size` literals** | **15** | Incl. `10.5px`, `11.5px`, `12.5px`, `13.5px` |
| Distinct font stacks | 2 | Fine |
| `transition`/`animation` declarations | 2 | — |
| **`prefers-reduced-motion`** | **0** | Motion with no reduced path |
| **`:focus-visible` rules** | **0** | No visible keyboard focus |
| **`aria-*` attributes** | **0** | — |
| `prefers-color-scheme` | 1 | Theme support present |
| `<img>` elements | 0 | **The imagery question: there are none** |

**Detector (`ui-craft-gate.py`, `--a11y-obligation`):** 3 Minor — `dark-glow`, `gradient-text`, `overused-font`.

> **Read that number correctly (CD14, CD9).** The detector reported almost nothing **because there was almost nothing to scan** — it saw 216 bytes of static shell, not the 68 KB of runtime-generated surface. This is the live case for *"a clean run is a floor, never a verdict."* Taking "3 Minor findings" as "the surface is fine" would be exactly the laundering NG7 forbids.
>
> **The detector has a mode that would see the real surface, and it is not installed.** `detect <url>` drives a headless browser against the rendered page (CD19). Attempting it here returned `puppeteer is required for URL scanning`, and the puppeteer install fails in this environment. So: *URL scanning is a supported mode gated on an extra dependency* — **Verified**; *it would surface substantially more on this page* — **Inferred**, not established. Recorded rather than asserted (NG6).

---

## 3. Findings (structure before surface, DX24)

### Architecture and availability

**F1 · Blocker · Performance & stability · Verified**
**Location:** `<head>`, three `<script src="https://unpkg.com/…">` tags.
**Evidence:** stripping `<script>` blocks leaves **216 bytes** of body and **144 characters** of visible text. The page is blank without the CDN.
**Why it matters:** this is the project's *public* explainer. If unpkg is unreachable — offline, corporate proxy, regional block, outage — a visitor sees nothing. Every other HTML surface in this repo is dependency-free by deliberate design (V9, DX8), and the audit viewer was *already migrated off* CDN runtimes in revision 17. This is the last surface still on one, and it is the most exposed.
**Fix:** inline the runtime. The explainer's interactivity (tabs, disclosure, filtering) is well within native DOM APIs, which is precisely what `audit-explorer.template.html` and `docs-explorer.template.html` already use.

**F2 · Blocker · Security (supply chain) · Verified**
**Location:** the same three tags.
**Evidence:** `integrity=` count is **0**.
**Why it matters:** three unpinned third-party scripts execute with full page authority on the project's marketing surface. A compromised or hijacked CDN path serves arbitrary JavaScript to every visitor. The pack's own Security lens treats a new dependency as a trust boundary; here there are three, unverified, on the public edge.
**Fix:** removed entirely by F1. If any external script is ever genuinely required, it carries an SRI hash and a pinned version.

### Accessibility

**F3 · Blocker · Accessibility · Verified**
**Location:** whole surface.
**Evidence:** `:focus-visible` rules = **0**; `aria-*` attributes = **0**; `prefers-reduced-motion` = **0** while 2 transition/animation declarations exist.
**Why it matters:** 16 interactive controls with no authored focus indicator means keyboard users cannot see where they are (WCAG 2.4.7 / 2.4.11). Motion with no reduced path fails 2.3.3 preference handling. U16 is a hard veto and does not negotiate.
**Fix:** author a visible focus ring on every control, add the reduced-motion media query, and label the two buttons and any icon-only affordance. Note the surface *does* have a skip link — the bones are there.

**F3b · Blocker · Accessibility · Flagged**
**Evidence:** contrast could **not** be verified statically, because colours are applied at runtime by the React tree.
**Why it matters:** with 166 hex values in play and no token-layer contrast audit, the probability that every text/surface pairing meets 4.5:1 is low, and it is currently unprovable. Flagged rather than asserted (NG6).
**Fix:** after F1, the palette becomes statically analysable and the detector's `low-contrast` rule plus a token-layer audit will settle it.

### Design system

**F4 · Major · Token discipline · Verified**
**Evidence:** **166 distinct hex colours** against **20** custom properties, with 118 `var()` references.
**Why it matters:** a token system exists and is bypassed roughly eight times for every colour it defines. This is the U3/U20 contract failing in the direction the detector was adopted to catch — and it cannot catch it here, because the values live in runtime JS (see the CD14 note above).
**Fix:** consolidate to the token layer as part of F1.

**F5 · Major · Token discipline · Verified**
**Evidence:** no `DESIGN.md` exists at the repo root or governing `web/`; the only design language is `docs/DESIGN.md`, which is the **Docs Explorer's**, a different product surface.
**Why it matters:** the public marketing surface is governed by no design language at all, which is the root cause of F4. It also means the detector, run from the repo root, evaluates `web/` against the *wrong* token system.
**Fix:** either bring `web/` under a stated design language or record explicitly that it is a separate brand surface with its own.

**F6 · Minor · Craft (hierarchy) · Verified**
**Evidence:** 15 distinct `font-size` literals including `10.5px`, `11.5px`, `12.5px`, `13.5px`, and a `10.5px` value below the 11px functional-text floor.
**Fix:** collapse to a modular scale with real ratio contrast (DX12); nothing functional below 11px.

### Surface craft

**F7 · Minor · Craft (the tells) · Verified**
**Evidence:** detector — `gradient-text`, `dark-glow`, `overused-font`.
**Why it matters:** `gradient-text` is on the craft floor's **refuse** list, not its discouraged list: emphasis comes from weight or size. These are small, but they are the recognisable-AI-look tells on the surface that represents the project.
**Fix:** weight/size for emphasis; drop the glow; check the font choice against the brand rather than the default.

**F8 · Minor · Archetype · Inferred**
**Evidence:** no Archetype Signature is recorded for this surface anywhere.
**Why it matters:** it reads as **E2 Cinematic Scrollytelling / F1 Content Portal**, and that inference has never been written down or tested against the job. G13 requires the signature be recorded in the spec's Part C; there is no Part C.
**Fix:** record the signature, or run `/specify` for the UX layer if this surface is going to keep growing.

---

## 4. Scorecard

| Dimension | Verdict |
|---|---|
| Archetype fit | Inferred, unrecorded (F8) |
| Flow / IA | **Sound** — 9 sections, clean h1→h2→h3, 16 controls, no `fetch` on load |
| State completeness | **n/a** — static content surface; no data states to design |
| Token discipline | **Fails** (F4, F5) |
| Accessibility | **Fails — Blocker** (F3, F3b) |
| Performance & stability | **Fails — Blocker** (F1) |
| Security / supply chain | **Fails — Blocker** (F2) |
| Content & copy | **Strong** — real, in-voice, no lorem |
| Craft | Minor tells (F6, F7) |
| **Imagery** | **Zero present. Not a finding.** No dimension of this review is limited by the absence of imagery |

---

## 5. Ranked plan

### Must fix before this is a surface we point people at
1. **F1 — inline the runtime.** Removes the blank-page failure mode, closes F2 entirely, and makes F3b/F4 statically checkable. In-repo precedent: revision 17 did exactly this migration for the audit viewer. **This is the highest improvement-to-effort change in the review.**
2. **F3 — the accessibility floor.** Focus indicator, reduced-motion path, labelling. Cheap; currently zero.

### Should fix next
3. **F5 → F4** — give `web/` a design language, then collapse 166 colours onto it. Do it in this order: the design language is the fix, the colour count is the symptom.
4. **F6** — one modular type scale, nothing functional under 11px.

### Worth doing
5. **F7** — drop `gradient-text` and the glow.
6. **F8** — record the Archetype Signature.

---

## 6. So: should Higgsfield beautify this?

**Not yet, and not as the next move.** The evidence is unambiguous: the surface's problems are **availability, supply chain, accessibility and token discipline**, none of which imagery touches. Adding a generated hero to a page that renders blank without a CDN, has no focus indicator, and carries 166 loose hex values would be decorating a structural problem — and the Simplifier's question ("does this earn its place?") answers itself while F1 is open.

**After F1–F4 land, the answer changes to a genuine yes.** This is a marketing/explanatory surface, which is exactly where `ui-visual-assets.md` says generated imagery earns its place (UI-T2). At that point the useful moves are a hero image in a brand-appropriate register (`Geominimal`, `Quiet luxury`, `Japandi`, `Gallery` or `90's Editorial` — not the fashion/selfie majority of the catalog), possibly one scroll-linked cinematic moment (`Dolly In`, `Crane Up`, `Push To Glass`), and OG cards built by compositing real text in HTML over a generated background. All under VA4 (committed, not linked), VA12–VA13 (manifest + alt text), and the U17 performance budget — which, note, is *easier* to hold once the CDN runtime is gone.

**Residual risk / flagged.** Contrast is unverified (F3b) and stays unverifiable until F1. `web/index.html` was not reviewed. No spec Part B/C exists for either web surface, so this review has no acceptance criteria to trace against — it measures the artifact, not conformance to an agreed intent.
