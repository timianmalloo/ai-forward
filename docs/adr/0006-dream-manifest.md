---
id: adr-0006-dream-manifest
title: "ADR-0006: The Dream Manifest — a learnings×repos targeting/record layer for federation, composed in a UI, consumed by apply-learnings --manifest, local-only by default"
type: adr
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [dreaming, federation, manifest, targeting, publish-boundary]
links:
  - { to: architecture-dreaming, rel: implements }
  - { to: spec-dreaming, rel: implements }
  - { to: adr-0002-fleet-learnings-store, rel: depends-on }
  - { to: adr-0005-harness-runner-boundary, rel: depends-on }
  - { to: architecture, rel: refines }
review-by: ""
review-suggested: []
summary: >-
  Federation had a distribution mechanism (apply-learnings push -> per-repo plans) but no
  targeting/record layer: which learnings go to which repos, and what happened when they did. The
  Dream Manifest is that layer — a learnings×repos assignment matrix (learnings/manifests/<id>.json)
  composed in a self-contained HTML, consumed by `apply-learnings.py push --manifest`, which
  reconciles per assignment and writes status back. Manifests carry repo identifiers so they are
  LOCAL-ONLY by default (excluded from the published Pages bundle), consistent with the publish
  boundary.
---

# ADR-0006 — The Dream Manifest

## Status
Accepted.

## Context

The dreaming capability (ADR-0002..0005) gives us a **capture → consolidate → approve → distribute**
loop. Distribution is `apply-learnings.py push`, which reconciles the fleet's promoted classes
(`learnings/fleet-classes.jsonl`) into each target repo's defect-class register and emits a
**reviewable plan** (never a merge — ADR-0005). That works, but it is *all-or-nothing per invocation*:
it pushes **every** fleet class into **every** named repo, and it keeps **no record** of which
learning was targeted at which repo or what became of it.

Real fleet operation is a **matrix**, not a broadcast: a C#-specific class belongs in the .NET repos,
not the Python one; a class already merged into repo A last week should not re-surface as noise; and
after a rollout you want to *see* — per (learning, repo) — whether it was added, merged, conflicted,
or skipped. That is a **targeting layer** (who gets what) and a **record layer** (what happened),
and federation had neither.

The user framed it exactly: *"a proposed Dream Manifest (a learnings×repos matrix composed in a UI,
consumed by `/apply-learnings --manifest`, hostable read-only) — the missing targeting/record layer
in federation."*

## Decision

Introduce the **Dream Manifest**: a persisted learnings×repos assignment matrix that federation reads
and writes.

1. **Shape (`learnings/manifests/<id>.json`).** A manifest is
   `{ id, created, dream?, repos:[path…], assignments:[ {learning:slug, sig, scope:"all"|"targeted",
   targets:[path…], status:{ repo: state } } ] }`. One assignment per fleet class; `targets` is the
   subset of `repos` that class is aimed at; `status[repo]` records the outcome of the last push
   (`pending` → `planned`/`merge`/`conflict`/`skipped`).

2. **Compose in a UI (`manifest-init`).** `apply-learnings.py manifest-init --repos a,b,c [--dream id]`
   scaffolds the JSON from `learnings/fleet-classes.jsonl` (every class assigned to every repo by
   default, `scope:"all"`, `status:pending`) **and** renders a **self-contained HTML** matrix
   (`learnings/manifests/<id>.html`, data inlined) where the human toggles each (learning, repo) cell,
   exports the edited manifest JSON, and copies the exact apply command. This is the *compose* mode.

3. **Consume + record (`push --manifest`).** `apply-learnings.py push --manifest <file>` reconciles
   **per assignment** — a learning is planned only into its `targets` — reusing the existing
   `reconcile`/`scrub`/`slug`/`render_patch` internals, writes the per-repo plan under
   `learnings/plans/`, and **writes the outcome back** into the manifest's `status` map. It then
   re-renders the same HTML in *rollout* mode (read-only status matrix). Still **never a merge**
   (ADR-0005) — the plan is the artifact; the human applies it.

4. **The safe instance→class abstraction is unchanged.** The manifest targets *already-promoted*
   fleet classes (which passed the five instance→class guards of ADR-0004 at promotion time). The
   manifest adds **routing and record**, not new promotion — it cannot smuggle an un-generalised
   instance across repos.

5. **Local-only by default (publish boundary).** A manifest **names repositories** — operational
   fleet topology. It is therefore **excluded from the published Pages bundle**
   (`tools/build-pages-bundle.py` LOCAL_ONLY: `learnings/manifests`, `learnings/plans`), consistent
   with keeping raw dreams and the audit log local while publishing only the *abstracted*
   `learnings/fleet-classes.*`. The *rollout* HTML can be shared read-only **by hand** if desired,
   but it is not auto-published, because it embeds repo paths.

## Consequences

**Positive.**
- Federation gains the missing *who-gets-what* and *what-happened* layers with one small, persisted,
  human-editable artifact — no new store, no daemon.
- Targeting removes cross-language noise (a class lands only where it is assigned) and repeat-push
  noise (status shows what already merged).
- The record is durable and greppable; a future dream pass / audit read can see prior rollouts.
- Reuses every existing federation internal — no second reconciliation engine (Simplifier).

**Negative / watch.**
- A manifest can drift from the fleet store if classes are added after it is scaffolded; `manifest-init`
  is cheap to re-run, and the compose UI shows the manifest's own snapshot with its `created` date.
- Status is *last-push* state, not a live guarantee the target register still matches; the per-repo
  plan remains the source of truth for what to apply.

**Alternatives rejected.**
- *Extend the fleet store with per-repo status columns.* Rejected: the fleet store is the abstracted,
  publishable class register; stapling repo topology onto it would violate the publish boundary and
  conflate "what we learned" with "where we sent it."
- *A live federation daemon.* Rejected: over-engineered; the pack's stance is stdlib harness + human
  gate (ADR-0005). A composed manifest + an on-demand push is the smallest correct thing.
