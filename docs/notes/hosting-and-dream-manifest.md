---
id: proposal-hosting-and-dream-manifest
title: "Proposal / dialog: GitHub Pages hosting + the Dream Manifest"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [hosting, github-pages, dreaming, federation, manifest, dialog, rfc]
links:
  - { to: spec-documentation-portal, rel: relates-to }
  - { to: architecture-dreaming, rel: relates-to }
  - { to: adr-0002-fleet-learnings-store, rel: relates-to }
  - { to: adr-0006-dream-manifest, rel: relates-to }
review-by: "2026-11-13"
summary: >-
  An RFC/dialog opener on (1) whether to host the Documentation Portal and surfaces on GitHub Pages,
  (2) how that impacts dream output and privacy, and (3) a proposed Dream Manifest - a first-class,
  reviewable, hostable artifact recording which approved learnings from a dream session target which
  repos (the missing 'targeting' layer between apply-decisions and /apply-learnings). Ends with the
  open decisions for the maintainer.
---

# Hosting on GitHub Pages + the Dream Manifest — a dialog

> **Status: ACCEPTED & IMPLEMENTED (revision 37).** Both proposals below shipped. Hosting = Option A
> (portal as the shareable front door) via `tools/build-pages-bundle.py` + `.github/workflows/pages.yml`,
> with the publish boundary enforced (raw dreams, the audit log, and `learnings/{manifests,plans,working
> ledgers}` kept local; only the abstracted `learnings/fleet-classes.*` published). The Dream Manifest is
> `apply-learnings.py manifest-init` + `push --manifest` (per-assignment targeting, status write-back,
> self-contained compose/rollout HTML from `templates/dream-manifest.template.html`), governed by
> **ADR-0006**. Manifests name repos → local-only (git-ignored + excluded from the bundle). This note is
> retained as the design record; the authoritative decision is ADR-0006.

*Status: **draft / dialog**. This is not a decision; it lays out the options, the grounded facts, a recommendation, and the open forks for you to steer. Nothing here is built yet.*

## 1. Where we are (grounded facts)

- **The repo is PUBLIC** (`github.com/timianmalloo/ai-forward`).
- **Pages already exists** — `.github/workflows/pages.yml` deploys **only the `web/` folder** to Pages (`upload-pages-artifact path: "web"`), so today the site root *is* `web/` and it serves the explainer + `pack-index.js`. Consequence: `web/index.html`'s `../docs/…` links point *above* the Pages root and **do not resolve when hosted** (they work locally over `file://`). The Docs Explorer, the portal, the graph, the audit viewer, and the dream views are **not** currently reachable on Pages.
- **Every surface is already `file://`-safe** and uses **relative** links (`../`, `../../`). The portal links out to `../index.html` (Docs Explorer), `../../pack/knowledge/…` (foundations), `../mockups/…`, `../audit/…`, `../dreams/…`. These resolve **only if Pages serves the repo root**, not a subfolder.

## 2. Should we host the portal (and surfaces) on Pages?

**The case for (strong):** your stated pain is *"when I share with folks it's a lot to discover."* A shareable URL — `timianmalloo.github.io/ai-forward/` opening the **portal** — is the single highest-leverage fix. Everything is already static, self-contained, and `file://`-safe; hosting is *additive*, not a rewrite. The graph view, the foundations, the architecture, all become linkable.

**The cost / considerations:**
- **Public exposure.** The repo is already public, so hosting publishes nothing that isn't already on GitHub. But hosting makes it *browsable and indexable* — a different reach than "a file in a repo." Fine for the portal, the explainer, the knowledge docs, the architecture. **Not** automatically fine for everything under `docs/` (see §3).
- **Serving root vs. subfolder.** For the portal's relative links to resolve, Pages must serve from a base where both `docs/` and `pack/` exist under it — i.e. the **repo root**. That means publishing the *whole* repo tree statically.
- **Private-Pages is paid.** If ai-forward (or a consuming repo) were ever private, Pages for a private repo needs GitHub Team/Enterprise. Not a concern while public; **is** a concern before we ever host a *consuming* repo's portal/dreams.

**The options:**
| Option | What | Links resolve? | Publishes | Verdict |
|---|---|---|---|---|
| **A — deploy repo root** | change `pages.yml` to `path: "."` (root), portal at `/docs/portal/` | ✅ all `../`/`../../` work | the whole (already-public) repo | **Recommended** — lowest effort, everything works |
| **B — curated bundle** | a build step assembles a `web/`-rooted bundle with rewritten links | ✅ after rewriting | only what you choose | more machinery; defers the link problem to a rewriter |
| **C — status quo** | host only `web/`; portal stays `file://`-local | ❌ for cross-links | explainer only | keeps the discovery pain |

**Recommendation:** **Option A**, with a clear **publish boundary** (§3). Set the Pages homepage to the portal (or an explainer→portal link). Add a `.nojekyll` so paths with underscores/dots serve correctly. Verify the portal's relative links against the served base before switching.

## 3. Impact on dream output (the privacy boundary)

This is where hosting needs a deliberate line, because **dream artifacts are not all the same sensitivity**:

- **Raw dream review** (`docs/dreams/<id>/index.html` + `dream-data.js`) contains **repo-specific evidence** — audit-entry ids, file paths, defect signatures, marker text. Even with the taint gate + `scrub.py`, this is *working material*, pre-approval. → **Keep local. Do not publish.** It is a review surface, not a publication.
- **The audit viewer** (`docs/audit/`) is the repo's activity/decision history — same reasoning. → **Local.**
- **Promoted, abstracted, scrubbed fleet learnings** (`learnings/fleet-classes.md`) are, by construction (ADR-0004), *general classes + controls with no path/name/value/secret*. → **Safe to publish** — and genuinely useful as a public "what this fleet has learned" page.

**So the publish boundary is:** portal · explainer · Docs Explorer (graph of *public* artifacts) · knowledge docs · architecture · **promoted fleet learnings** → public. **Raw dreams · audit · repo-specific evidence** → local (or gated). This is also the natural boundary the federation design already draws (the abstraction guard *is* the "is this shareable?" gate).

*Practical control:* if we go Option A, exclude `docs/dreams/` and `docs/audit/` from the deployed artifact (or keep them but accept they're public working-notes — your call). The portal's Systems section would then link the *hosted fleet learnings* publicly and the *local dream review* only for a maintainer running locally.

## 4. The Dream Manifest (the "nifty" part) — a proposal

You asked for *"a more functional way to compose a manifest of what from a dream session should then be applied to a corpus of repos."* This names a real gap in the current flow.

**Current flow:** `/dream` → review (approve/reject in the HTML) → `apply-decisions` (promote to fleet store) → `/apply-learnings --repos a,b,…` (per-repo reconciled plans). The **targeting** — *which* approved learnings go to *which* repos — is a loose CLI argument, not a durable, reviewable artifact.

**Proposal — the Dream Manifest:** a first-class, committed artifact (`learnings/manifests/<dream-id>.json` + a rendered view) that is the **learnings × repos matrix** for a dream session:

```jsonc
{
  "dream": "drm-0002",
  "composed": "…",
  "repos": ["../repo-a", "../repo-b", "../repo-c"],
  "assignments": [
    { "learning": "OPS-B ignore-rule matches nothing", "scope": "general",
      "targets": ["../repo-a", "../repo-b", "../repo-c"], "status": {"repo-a":"applied","repo-b":"planned","repo-c":"skip"} },
    { "learning": "PACK-E install destination without template", "scope": "general",
      "targets": ["../repo-a"], "status": {"repo-a":"planned"} }
  ]
}
```

- **Composed in a UI** (a sibling of the dream review view): approved learnings down one axis, the repo corpus across the top, a checkbox matrix → emits the manifest. This is the "more functional way to compose" — you *see* the fleet, you *assign* deliberately, instead of guessing a `--repos` list.
- **Consumed by `/apply-learnings`** with `--manifest <file>` (extending, not replacing, ADR-0002's push): it reconciles each assignment into its target repo as today, and **writes the per-repo status back into the manifest** (planned → applied), so the manifest becomes the *durable record of what rolled out where*.
- **Hostable, read-only:** on Pages the manifest + the fleet learnings become a browsable **"fleet rollout" page** — *what has this dream taught, and where has it landed?* Composing and applying stay **local/agent** (Pages is static; it displays, it does not write).

**Why it fits:** it is the missing targeting/record layer between "approve" (apply-decisions) and "push" (apply-learnings), it reuses the existing artifacts (approved learnings, the per-repo reconciliation), and it is the same committed-Markdown/JSON + review-HTML + stdlib-script shape as everything else. It also makes the federation *auditable* — a manifest is the evidence of a rollout.

## 5. Open decisions (your steer)

1. **Host it?** Option A (deploy repo root, portal becomes the shareable front door) — yes / no / prefer B or C?
2. **Publish boundary** — agree that portal + explainer + graph + knowledge/architecture + **promoted fleet learnings** are public, while **raw dreams + audit stay local** (excluded from the deployed artifact)?
3. **Set the Pages home to the portal?** (Today it's the explainer.) Portal-first, explainer linked — or keep explainer-first?
4. **Build the Dream Manifest now?** (a) the manifest artifact + a compose UI + `/apply-learnings --manifest`, (b) just the manifest artifact + CLI for now (defer the UI), or (c) keep as dialog, decide later.
5. **Manifest as a required step?** Make the flow `apply-decisions → compose manifest → apply-learnings`, or keep the manifest **optional** (the direct `--repos` path still works)?

*Recommendation in one line:* **do Option A with the local/public boundary of §3, set the portal as home, and build the Dream Manifest as an optional artifact + CLI first (4b/5-optional), adding the compose UI once the artifact proves itself.* But this is your call — the questions above are the fork.
