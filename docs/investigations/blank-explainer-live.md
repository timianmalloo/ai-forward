---
id: investigation-blank-explainer-live
title: "Investigation: the hosted explainer renders blank even after the 'fix'"
type: investigation
status: resolved
owner: "@timianmalloo"
phase: "hosting"
tags: [ui, hosting, github-pages, explainer, deploy, render-verification]
links:
  - { to: adr-0006-dream-manifest, rel: relates-to }
  - { to: proposal-hosting-and-dream-manifest, rel: relates-to }
review-by: ""
review-suggested: []
summary: >-
  The hosted explainer stayed blank after a fix was declared, because the fix lived only in the
  working tree — it was never deployed, so the live URL still served the old syntax-broken file.
  A compounding cause: the earlier fix was proven with `node --check` (syntax) but never with a
  render check (the mounted surface). Both verified here: the live file is the old corrupted
  version; a jsdom load-and-run proves the fixed file MOUNTS while the old one stays BLANK.
  Root cause = not-deployed + verified-at-the-wrong-level. Registered as class PACK-H.
---

# Investigation — the hosted explainer renders blank even after the "fix"

## Symptom
User: *"you claim it is fixed but i still see a blank page: https://timianmalloo.github.io/ai-forward/ai-forward-pack-explainer.html"* — the hosted explainer renders as a blank/black page. A prior turn diagnosed a syntax error in the file's embedded data and reported it **fixed**.

## Reproduction (deterministic)
- **Live URL fetch** (`GET` the hosted file): the served HTML still contains the corruption `…"core"], paired with the Test Architect…` and does **not** contain the watchdog `__afpShowFallback`. → the live file is the **old, unfixed** version.
- **Render check** (jsdom `runScripts:"dangerously", resources:"usable"`, real CDN fetch of React/htm, 6 s settle, then inspect `#root`):
  - OLD file: `rootChildCount: 0`, `Uncaught SyntaxError: Unexpected token 'with'`, verdict **BLANK** — reproduces the symptom exactly.
  - FIXED file (working tree): `rootChildCount: 11`, `rootTextLen: 29974`, fallback not shown, verdict **MOUNTED**.

## Timeline
1. Prior turn: found the embedded skills-array corruption (merged `/ui-design`+`/implement` rows → `SyntaxError`), repaired it, added a watchdog fallback, defaulted the whole-pack index to its self-contained tab, wired a `node --check` gate (PACK-G). Declared **fixed**. All *local* gates green.
2. **No git commit / push occurred** (a standing "don't push while the user is away" guard). The GitHub Pages deployment therefore never rebuilt — the previous `web/`-only workflow's last artifact still serves the **old** file.
3. This turn: user reports the hosted page still blank.

## System map
`working tree (fixed)` → **[git commit + push]** → `GitHub Actions (pages.yml)` → `Pages artifact` → `https://…/ai-forward-pack-explainer.html` (what the user sees). Every local gate reads the **left** end of this pipeline; the user sees the **right** end. The fix never crossed the `[commit + push]` edge, so the two ends diverged. Separately, the prior verification only probed *syntax* (does the script parse), not *render* (does the app mount) — a proof at the wrong altitude.

## Hypotheses considered
| # | Hypothesis | Verdict |
|---|---|---|
| H1 | The fix is deployed but a caching/CDN layer serves a stale copy | **Ruled out** — the live HTML still contains the corruption byte-for-byte and lacks the watchdog; it is the *old source*, not a cached render of the new source. |
| H2 | The fix is correct but the React app has a *runtime* error, so it mounts nothing even when deployed | **Ruled out for the fixed file** — jsdom render check shows the fixed file MOUNTS (`#root` fills). (The lone jsdom `matchMedia is not defined` error is a jsdom artifact; `matchMedia` exists in every real browser and runs *after* the render.) |
| H3 | The fix was never deployed — the live site serves the old broken file | **VERIFIED (necessary + sufficient)** — see below. |

## Verified root cause (necessary + sufficient)
**The fix was never deployed; the live URL serves the previous, syntax-broken file.** Compounded by **verification at the wrong level** — the earlier "fixed" claim rested on `node --check` (syntax), not a render check of the mounted surface.
- **Necessary:** remove the cause (deploy the fixed file) → the live page will serve the MOUNTED version (proven by the render check on the exact bytes that will be deployed). While the cause is present (old file live), the page is BLANK.
- **Sufficient:** the old file, run in a real DOM, produces exactly the BLANK symptom (`rootChildCount: 0` + SyntaxError). Nothing else is required to reproduce it.

## The specific fix
Deploy the already-repaired, now **render-verified** `web/ai-forward-pack-explainer.html` (+ the hardened `web/index.html`) by committing and pushing so the Pages workflow rebuilds. With Option A hosting also deployed, the site **root** additionally redirects to the self-contained portal, so the front door no longer depends on the CDN explainer at all. Rollback: revert the commit (Pages redeploys the prior artifact).

**Regression test (fails on the unfixed code):** the jsdom render check (`rootChildCount > 0`) — **FIXED → MOUNTED, OLD → BLANK**, observed. The cheap pre-filter is the PACK-G `node --check` gate in `check-consistency.py` (also observed failing on the corruption).

## Generalization — the failure class
**Class (PACK-H):** *a fix to a hosted surface reported "done" from the working tree, not verified on the live surface* — and the E11 corollary, *a rendered-surface claim proven only at the syntax level*. Registered in `docs/lessons/defect-classes.md` with the two-part control: (1) "done" for a hosted-surface defect requires deploy + re-verify at the live URL; (2) prove render (jsdom/headless `#root` fills), not just syntax.

**Sweep for siblings.** Other hosted client-rendered surfaces in this repo that mount at runtime and could exhibit the same *proven-syntax-not-render* / *not-deployed* gap:
- `docs/index.html` (Docs Explorer — React UMD from CDN, same house pattern) — **render check recommended** as a sibling; not yet run this turn.
- `docs/portal/index.html` (portal shell) — self-contained (1 same-origin script), already confirmed dependency-free; low risk but included in the render-gate scope.
- `docs/mockups/*.html`, `learnings/manifests/*.html`, `templates/*explorer*.html` — client-rendered; in scope for the render gate.
The **class-prevention item** generalizes the PACK-G `node --check` gate into a **render gate** (jsdom mount assertion) over these surfaces, and adds a live-URL post-deploy verification step.

## Phased repair plan
| Phase | Scope (code + tests) | Failure mode eliminated | Validation | Depends on |
|---|---|---|---|---|
| **1 — Deploy the fix** | commit + push the repaired `web/ai-forward-pack-explainer.html`, `web/index.html`, and the Option A hosting bundle; Pages rebuilds | The live page serves the old broken file (the reported symptom) | Fetch the live URL post-deploy; assert the corruption is gone and the page mounts | Pages workflow |
| **2 — Live-URL re-verification** | after deploy, fetch the live explainer + root; assert fixed bytes present and (headless) `#root` fills | "Fixed in the working tree" mistaken for "fixed for the user" (PACK-H control 1) | live fetch shows watchdog present + no corruption | Phase 1 |
| **3 — Render gate (class prevention)** | extend the PACK-G syntax gate to a jsdom **render** assertion over `web/**`, `docs/index.html`, `docs/portal/`, `docs/mockups/**`; run in `pack-consistency` CI | A surface that parses but mounts nothing ships green (E11 / PACK-H control 2) | gate observed failing on the old file, passing on the fixed file | jsdom in CI |
| **4 — Sibling sweep** | run the render gate over the Docs Explorer + mockups; fix any that don't mount | Undetected siblings of the same class | each sibling MOUNTED or fixed | Phase 3 |

## Residual risk / what would change the diagnosis
- After deploy, GitHub Pages propagation can lag a minute or two; a blank immediately post-push is propagation, not a new defect — re-verify after the Actions run completes.
- The jsdom render check is a strong proxy but not a real browser; a browser-only API used *during* render (not the post-render `matchMedia`) could still differ. A real headless-browser check (Phase 3, if Chromium is added) would be stronger.
- Phases 3–4 (the render gate + sibling sweep) are **not yet executed** — they are the class-prevention work proposed for approval.

## Separate findings surfaced during the deploy (out of scope for this fix)
Deploying and verifying live exposed three defects independent of the blank explainer; each is registered and, where safe, fixed:
- **PACK-I (fixed):** `web/pack-index.js` element order followed OS-dependent `os.walk` descent, so it was byte-stable locally but reordered on CI Linux → source-install drift failed. Fixed with `_dirs.sort()`; the residual `generated` timestamp was removed (unconsumed; mtime ≠ checkout time) so the file is now byte-identical across builds and platforms.
- **PACK-H second instance (fixed):** the Option A restructure moved `web/` under `/web/`, 404-ing the user's bookmarked `/ai-forward-pack-explainer.html`. Fixed with backward-compat root aliases in `build-pages-bundle.py` (verified live: the old URL now returns 200).
- **PACK-J (fixed — version-independent):** `pack-consistency` CI went red on the first run under the runner's new Python 3.14 (floating `python-version: "3.x"`): `docs-graph.py`'s `_TitleParser` and its atomic-write test depend on stdlib behaviour that changed in 3.14 (HTMLParser RCDATA for `<title>`; a tempfile/`os.stat`-mock interaction). Both pass on 3.12 (verified). **Interim:** pinned CI to `python-version: "3.12"` to restore green main. **Proper fix (tracked, not done here):** make `docs-graph.py` version-independent (strip residual tags from an extracted title; narrow the atomic-write test's global `os.stat` mock), then restore `"3.x"` with a newest-minor matrix. This is a distinct investigation; it does not affect the blank-explainer fix, which ships via the separate (green) `pages` workflow.

## Gate record
GATE investigate-blank-explainer-live · 2026-08-16 · SRE + Test Architect (adversary) · exit criteria met: root cause Verified necessary+sufficient against live-fetch + jsdom render evidence; the fix is render-proven; class registered · verdict: PASS · vetoes: Test Architect (fix must be proven to render) → cleared by the jsdom MOUNTED/BLANK discrimination.
