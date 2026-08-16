---
id: architecture-dreaming
title: "Dreaming subsystem — architecture"
type: architecture
status: accepted
owner: "@timianmalloo"
phase: "dreaming"
tags: [dreaming, architecture, consolidation, federation, oracle, loa-continuous-sentinel]
links:
  - { to: spec-dreaming, rel: implements }
  - { to: architecture, rel: refines }
  - { to: adr-0002-fleet-learnings-store, rel: depends-on }
  - { to: adr-0003-promotion-oracle, rel: depends-on }
  - { to: adr-0004-instance-to-class-abstraction, rel: depends-on }
  - { to: adr-0005-harness-runner-boundary, rel: depends-on }
review-by: "2027-02-11"
summary: >-
  Subsystem architecture for AI-Forward's dreaming capability — the offline consolidation pipeline
  (light/REM/deep) over the committed corpus, the HTML review/approval surface, the promotion oracle,
  the safe instance→class abstraction, the fleet learnings store, and the /apply-learnings federation
  path — as an LOA Continuous Sentinel with determinism at the floor and a human gate before any
  durable write. Refines the pack's top-level architecture; it is a subsystem, not a new system.
---

# Dreaming subsystem — architecture

*Refines `docs/architecture.md` (the pack's overall architecture). This is a **subsystem** delivered as committed Markdown/JSONL + a stdlib script bundle + two skills — no new runtime, no new heavy dependency. Governs `spec-dreaming`.*

## 1. Archetype & tier allocation (LOA)
- **Archetype:** **G · Continuous Sentinel** (ongoing oversight of the corpus against the improvement policy), composing **B · Adversarial Ensemble** at the reflect/abstract step (propose class → Simplifier strike → human verify). The review + push surface is a **Governor** (human-in-the-loop before a consequential action).
- **Rejected archetypes:** *E · Generate-Verify-Select loop* (no cheap authoritative auto-verifier for "is this a good learning" — the verifier is a human, which makes it a Sentinel, not a search loop); *H · Long-Horizon Agent* (no persisted autonomous agent — the pass is stateless over a corpus snapshot); *D · Grounded Synthesizer* (we are not answering queries, we are consolidating history).
- **Tier allocation:** **T0** (deterministic stdlib) for staging, dedup, scoring, the taint gate, reconciliation, and rendering — the bulk. **T3** (one throttled model call per phase, bounded window) only for the REM reflection / instance→class abstraction. **Human gate** is the verification tier (P5/P6). *Determinism at the floor (P2):* the model never scores, never gates, never writes durable memory; it only proposes abstractions a human accepts.

## 2. System sketch (stocks · flows · feedback · boundary)
- **Stocks (what accumulates):** the append-only `audit-log.jsonl` / `change-log.jsonl`; the `defect-classes.md` register; the new `mitigations.jsonl` (oracle facts); the fleet learnings store; the per-dream artifacts.
- **Flows:** corpus signals → candidates → proposals → (human) approvals → promotions → distribution plans → per-repo diffs.
- **Feedback loops:** promoted classes are read at grounding (CI5) → fewer recurrences → the *recurrence-as-metric* signal (CI4). The Dream Diary is **excluded** from the corpus (breaks the self-poisoning loop). A rejected proposal kind with a low approve-rate signals a bad abstraction prompt (a slow tuning loop).
- **Delays:** consolidation is offline/nightly (sleep-time compute); federation is human-paced (review then push).
- **Boundary drawn:** *in* — reading the committed corpus, producing proposals, rendering the view, capturing oracle facts, abstracting, storing, and generating reconciled diffs. *Out* — merging anything, executing anything in a target repo, any runtime memory service, any model fine-tune.

## 3. Components & boundaries
```mermaid
flowchart LR
  subgraph Consolidation [Consolidation context - T0 + one T3 step]
    C1[corpus reader\naudit/change/register/mitigations/markers] --> C2[light: stage + dedup + taint gate + scrub]
    C2 --> C3[REM: reflect -> candidate classes\n(model boundary - injected)]
    C3 --> C4[deep: score + threshold gate -> proposals]
    C4 --> C5[render: dream.json + dream-data.js + review HTML + Dream Diary]
  end
  subgraph Governance [Governance context - human gate]
    C5 --> G1[[Dream Review HTML\napprove/edit/reject/defer]]
    G1 --> G2[decisions.json]
    G2 --> G3[apply-decisions: validate + taint re-check]
  end
  subgraph Federation [Federation context]
    G3 -->|approved general| F1[abstract instance->class\n+ scrub + boundary]
    F1 --> F2[(fleet learnings store\nin ai-forward)]
    G3 -->|approved repo-local| F3[(repo defect-classes.md)]
    F2 -->|/apply-learnings push| F4[reconcile vs target repo\n-> reviewable diff/branch]
    F2 -->|/updatepack pull| F5[deployment map -> repo]
  end
  ORACLE[(mitigations.jsonl)]:::o --> C1
  IMPL[/implement, /investigate,\nhuman validation/] --> ORACLE
  classDef o fill:#2c2a29,stroke:#888684;
```
- **Corpus reader** — composes `audit-log.py` (list/search) + a JSONL reader + a marker grep + `defect-classes.md` parse. No new store.
- **Model boundary (REM)** — an *injected* interface: the harness emits a **prompt + candidate bundle**; the runner supplies the completion; the harness validates the returned abstraction against a schema. A missing/failed model call → deterministic-only proposals (dedup + mitigation-promotions still flow). *This is the pack-identity boundary (ADR-0005).*
- **Renderer** — deterministic; emits `dream.json` (canonical), `dream-data.js` (`window.DREAM_DATA`, file://-loadable), the review HTML (from a template, self-bootstrapping like the audit viewer), and appends a **Dream Diary** entry.
- **apply-decisions** — the *only* path that writes a durable store; validates the (possibly hand-edited) decisions file, re-runs the taint/scrub pass, then promotes.
- **Fleet learnings store** — in `ai-forward` (ADR-0002).
- **/apply-learnings** — reconciles + emits diffs; never merges (ADR-0002/spec US-5).

## 4. Cross-cutting concerns (designed in, not deferred)
- **Auth / least privilege:** the push produces diffs; nothing runs in a target repo; the fleet store is a local git-committed directory. No credentials handled.
- **Observability:** every dream appends an audit-log entry (AL5) + a Dream Diary entry (what it added/merged/superseded, with counts). The Diary is human-read and **excluded from re-ingestion**.
- **Idempotency (P8):** a dream is keyed to its corpus snapshot + window; `apply-decisions` records which `drm-`/proposal ids it promoted, so a re-run does not double-promote (a promoted proposal id is skipped). Promotion into a slug-keyed Learning appends an instance rather than duplicating (aggregate invariant).
- **Security / privacy:** `scrub.py` + the provenance taint gate run in `light` (before consolidation) and again in `apply-decisions` (before any store write) and again in `/apply-learnings` (before crossing a repo boundary) — defence in depth. Untrusted/tool-authored/`system` origins are structurally removed, not down-scored.
- **Failure modes:** empty/malformed corpus → valid empty dream; failed model call → deterministic-only dream; malformed decisions file → rejected, nothing written; a target repo without the pack → skipped with a note.

## 5. Durable representation (data)
Consistent with `domain-and-data-modelling.md`: the logs and `mitigations.jsonl` are **append-only facts**; the **Learning** store is a **slug-keyed dimension** whose `instances[]` are append-only facts (a recurrence appends an instance, never a new Learning — the aggregate invariant). The HTML `dream-data.js` and the review view are **derived projections** of `dream.json` (never a second source of truth). Grain: *one row in `mitigations.jsonl` is exactly one verified successful mitigation of one defect at one point in time.* No quantity is stored twice (derive-don't-store): a Learning's status/recurrence is computed from its instances. See ADR-0002.

## 6. Delivery phasing (define whole, phase vertically)
The subsystem is defined whole (above); delivery is four vertical slices, each end-to-end deployable, test-validatable, and human-validatable. Mocked seams are contracts.

| Phase | User-visible capability it proves | Real vs mocked | Human validates (demo) | Tests validate (E2E) | Unblocks |
|---|---|---|---|---|---|
| **P1 — Walking skeleton** | `dream.py run` reads the real corpus, produces `dream.json` + `dream-data.js` + the review HTML with **deterministic** proposals (dedup + mitigation-promotions), and appends a Dream Diary + audit entry | **Real:** corpus read, taint/scrub, deterministic dedup, scoring, render, diary. **Mocked:** the REM model step (returns empty → deterministic-only) | run `dream.py run` in ai-forward; open the HTML; see real proposals from the real corpus | given a fixture corpus, `run` emits a schema-valid `dream.json`; empty corpus → valid empty dream; a tainted signal is excluded | everything |
| **P2 — Oracle** | successful mitigations are captured (`mitigations.jsonl`) from red→green tests and human validations, and appear as "Confirmed mitigation → learning" proposals | **Real:** `dream.py capture-mitigation`; ingestion into the corpus. **Mocked:** auto-emit hooks in /implement (manual capture first) | fix a bug with a red→green test, run `capture-mitigation`, see it in the next dream | a captured mitigation with red→green evidence produces a proposal; an `unverified` fix does not | P3 (better proposals) |
| **P3 — Approve & promote** | `apply-decisions` validates a decisions file, runs the abstraction (instance→class) on approved-general items, and promotes to the fleet store / repo register | **Real:** validation, abstraction, scrub, promotion, idempotent skip. **Mocked:** the model-assisted abstraction may fall back to a deterministic template | approve items in the HTML, export, run `apply-decisions`, see the fleet store update | approving nothing writes nothing; a re-run does not double-promote; a promoted Learning has ≥1 control | P4 |
| **P4 — Federation** | `/apply-learnings --repos …` reconciles approved fleet learnings into target repos as reviewable diffs; `/updatepack` inherits general classes | **Real:** slug-exact reconcile, diff generation, conflict surfacing. **Mocked:** none (targets are real local repos or a scratch repo) | push to a scratch repo; review the diff; confirm merge-not-duplicate on a repo that already has the class | add / merge-into-existing / surfaced-conflict each produce the specified diff; no silent override | — |

**P1 is the walking skeleton:** the thinnest path touching every layer (corpus → pipeline → render → diary → audit) and proving the composition, with the model seam mocked as a defined contract.

## 7. Residual architectural risk
- The **model boundary schema** must be strict enough that a bad completion is rejected, not promoted (mitigated: deterministic fallback + human gate + `apply-decisions` re-validation). [Flagged]
- **Reconciliation** is slug-exact + human-flagged (no fuzzy index — Simplifier's call); a genuinely-equivalent class with a different slug will duplicate until the next dream's dedup catches it. Accepted trade (keeps identity simple). [Flagged]
- **Runner portability:** the model step is injected, so the subsystem builds and runs deterministically without any runner SDK; each runner integration is a thin adapter spiked at integration time, not a build dependency. [Verified — no external SDK in the P1–P3 dependency set]

## 8. Conformance (LOA C1–C11, checked)
C1 tier annotated (§1); C2 model call is budgeted/bounded (one per phase, capped window); C3 cognition/execution split (model proposes, deterministic code + human act); C5 model output validated against a schema before any use; C7 fallback declared (deterministic-only); C10 audit completeness (audit entry + Dream Diary per pass); C11 no ambient-credential action (diffs only). Security & Distributed-Systems hard vetoes: no delivery/ordering surface (offline, single-writer per pass); no secret handling (diffs, local files) — cleared.

---
**Status table**

| | |
|---|---|
| **Completed** | Dreaming subsystem architecture + ADRs 0002–0005; LOA archetype/tiers; vertical phasing (P1–P4); cross-cutting concerns; conformance |
| **Remaining** | Build P1 (walking skeleton) → P2 (oracle) → P3 (approve & promote) → P4 (federation) |
| **Best next action** | Implement **P1**: `dream.py run` (corpus → deterministic proposals → `dream.json`/`dream-data.js`/review HTML → Dream Diary + audit) |
