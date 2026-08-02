---
name: ui-design
description: Create, review and elevate user interfaces to a professional standard — direction brief, design language, reviewable mockups, and rubric-based critique. Use to design a new surface, audit an existing one, or take a working UI to best-in-class.
---

# Skill: /ui-design

Take a user-facing surface — new or existing — to a **professional, best-in-class** standard. This is the craft skill for the interface itself: it establishes creative direction in words before pixels, builds the design language, produces a **self-contained, reviewable mockup** that renders the hard states, and critiques against a rubric rather than a reaction. It is deliberately distinct from `/design` (which produces the *component* design — contracts, patterns, failure modes, telemetry, test plan). `/design` decides how the thing works; `/ui-design` decides how it looks and feels, and whether that is actually good.

**Spine:** the Rigor Protocol (`knowledge/rigor-protocol.md`) run on the *interface*, weighted toward **Stage 1 OPEN** (direction, before any visual artifact exists) and **Stage 4 DISCONFIRM** (rubric critique, structure before surface). **Authority:** **`ui-design-craft.md`** (DX1–DX25 — direction, the generic-tells table, the fidelity ladder, the review harness, visual craft, the critique rubric) is this skill's governing standard; the **UI & Interaction Design Standard** (`ui-interaction-design.md`, U1–U20) is the floor; the **UI Archetype Grammar + Catalog** (`ui-archetype-grammar.md`, `ui-archetype-catalog.md`) fixes the *kind*; **`technical-ui-design.md`** (TQ1–TQ12) governs expert/quantitative surfaces; the **Specification Standards** (`specification-standards.md`, S1–S18) supply the UX layer this builds on. **Mode:** Peer Mode to create, Adversary Mode to critique — and the author never clears their own accessibility veto.

## Grounding (first action)
Load what already exists and treat it as the **authoritative source of truth** (Rigor Protocol Stage 0; BoK §III.1): the spec's **Part B (UX)** and **Part C (UI)** (`docs/specs/`), the project's **design language** (`DESIGN.md` — the token system, U3a), any existing mockups (`docs/mockups/`), the component designs that render this surface (`docs/design/`), and the real implementation if one exists (**open the components — do not describe them from memory**, `end-to-end-integrity.md` E15). Prefer **graph traversal** (`knowledge-visualization.md` V15): start from the surface's artifact(s) and follow typed edges 1–2 hops (upstream `implements`/`refines`, downstream `documents`/`tested-by`, `uses-term` into the glossary), citing the traversal path; a missing edge, stale node or orphan is a finding. Also read the **defect-class register** (`docs/lessons/defect-classes.md`, `continuous-improvement.md` CI5) for the UX-* classes, so a known failure is designed out rather than rediscovered. **A settled UI over an unsettled UX layer is a block** (S2, Surface-before-Structure) — if Part B does not exist or its flows do not cover the alternate/error/recovery paths, stop and run `/specify` for the UX layer first.

## Input
A surface to create, review, or elevate. Examples: *"design the onboarding flow"*; *"review our settings screens"*; *"the data-entry page feels cluttered and cumbersome — fix it"*; *"take the dashboard to best-in-class"*. One sentence is enough; the skill expands it into a direction brief.

## Modes
State which mode you are in; they share the flow but weight it differently.

| Mode | When | Emphasis |
|---|---|---|
| **create** | No surface exists yet | Stage 1 (direction brief, archetype) and Stage 5 (design language + mockup) |
| **review** | A surface exists; the question is "how good is it?" | Stage 3 (**measure** before diagnosing) and Stage 4 (rubric critique, ranked plan) |
| **elevate** | A surface works but is not good enough | Full loop: review first, then re-direct and rebuild the weakest layer — often the archetype |

**Default when unclear:** if the surface exists, run **review** first and *then* decide with the user whether to elevate. Rebuilding something you have not measured is how a working screen gets replaced by a differently-flawed one.

## Cast
- **Peers (author together):** **UX & Accessibility** (lead — owns the Surface layer and its excellence), **UX Researcher / IA** (owns the structure beneath it: IA, flows, findability), **Product Strategist** (does this serve the job-to-be-done?), the relevant platform developer (**Mobile App** / **Native Desktop** / the web-facing language Developer) for platform idiom and feasibility, **The Simplifier** (every element earns its place), and **Domain Researcher** when comparables or platform guidelines must be established rather than recalled.
- **Adversaries (attack at the gate):** **UX & Accessibility** (state completeness, token discipline, WCAG 2.2 AA — **hard veto**, and the author does not clear it), **UX Researcher / IA** (archetype fit, flow integrity, findability, unhappy-path coverage — **UX-specification veto**), **The Simplifier** (soft veto on anything that does not earn its place — emits the tagged delete-list, `solution-selection-ladder.md` L9), **Product Strategist** (does this still serve the core scenario?), **Test Architect** (are the UI acceptance criteria falsifiable and covered?), **SRE** (performance budget, layout stability), **AI Systems Engineer** when the surface fronts a model (HAX + Shape-of-AI, wrong-answer states).

## Flow (Rigor Protocol, specialized to the interface)

**Stage 0 — Interdict the rush.** **Do not generate a screen.** The single most common failure in agent-produced UI is one pass that decides direction, system and composition together and therefore averages all three into the generic default (`ui-design-craft.md` DX1). No markup, no component, no color until Stage 1 has produced a direction brief. In **review** mode, the equivalent interdiction is: **do not diagnose before you measure** (DX23).

**Stage 1 — OPEN (direction, in words).** Write the **direction brief** (DX5): who this is for and the emotional state they arrive in; the **job-to-be-done**; the **Archetype Signature** chosen from that JTBD (`ui-archetype-grammar.md`, nearest row of `ui-archetype-catalog.md`, deviations noted per G9); **three defining adjectives and their opposites**; **named references** with what specifically is taken from each (DX4 — adapt, never clone); the **anti-goals**; and the constraints (medium(s) + platform HIG, density profile, existing brand assets, accessibility obligation level). Then decide the personality in three moves — **type, color, space** — each with a one-line justification tied to the brief (DX6).

> **Verify the archetype against the shape of the task, including on an existing screen.** *Reading is parallel; entering is serial.* A dashboard/bento archetype applied to a data-entry task is a rewrite, and finding it at the end of a review wastes the review (`continuous-improvement.md` UX-A).

**Stage 2 — INTERROGATE.** Drill the brief with precise questions: *Clarification* — what exactly is this surface for, and what is it explicitly **not** for; *Assumption* — what are we assuming about the user's device, expertise, data volume, and state on arrival; *Cause/Effect* — if we choose this archetype, what does it force (navigation, pacing, density, feedback) and what does it forbid; *Evidence* — is this pattern established for this job (Jakob's Law, U12) or are we inventing; *Significance* — which single decision here most determines whether this succeeds. Enumerate the **surface inventory**: every screen/component in scope, and for each, its full state set (default / hover / focus / active / disabled / **loading** / **empty** / **error** / success / **overflow**) — the list you will be held to at the gate.

**Stage 3 — EVIDENCE (measure, establish, systematise).**
- **In review/elevate mode, measure before diagnosing (DX23).** Count and record: interactive controls per screen, simultaneous sections/cards, network calls on load, competing focal points, distinct type sizes, distinct colors, modes that do the same job, and the token-vs-arbitrary-value ratio. Run `python3 docs/ai-forward-pack/scripts/design-lint.py <DESIGN.md> --strict` and compute the **contrast ratio for every text/surface pairing**. "Cluttered" is a symptom; the count is the diagnosis, and the count is what makes the argument unarguable.
- **Establish, don't recall.** Platform guidelines, the accessibility obligation, comparable products, and any claim about the existing implementation are established from the source (**open the component file** — E15) and labeled Verified / Inferred / Flagged.
- **Build the system before the screens (DX2).** Produce or update the project's **design language** — `DESIGN.md` from `templates/design-language.template.md` (the Stitch format extended with this pack's floors), with the token frontmatter, the **contrast audit at the token layer**, the complete component-state matrix, theme/density modes, the paired **Archetype Signature**, motion + reduced-motion, real UI copy strings, the performance budget, and — for AI surfaces — the HAX/Shape-of-AI rules. Keep it `design-lint.py`-clean and render `templates/design-language-preview.template.html` as the visual catalog.
- **Write the motion inventory** (DX19): every animated moment, its purpose, duration and easing — and cut the purposeless ones.
- **Draft the real UI copy** (DX21): buttons that say what they do, empty states that teach the first action, errors that say what happened and what to do next, confirmations that name the irreversible consequence, numbers with units and precision. Copy is drafted here, never deferred to implementation.
- Maintain the confidence ledger.

**Stage 4 — DISCONFIRM (the gate — critique against the rubric).** Switch to Adversary Mode and run the **critique rubric** (DX22), **structure before surface** (DX24): archetype fit and flow/IA first, then state completeness, then accessibility, then craft. Every finding carries **location · dimension · severity (0–4) · evidence · recommended fix · confidence**, mapped to the pack's severities (4→Blocker, 3→Major, 2→Minor, 1→Nit); an accessibility finding at ≥3 is a **Blocker** under U16 regardless of usability impact. Self-check against the **generic-tells table** (DX3) — each tell is either absent or a deliberate, justified choice. The Simplifier emits its tagged delete-list with a `net: -N` line. The UX & Accessibility lens states **PASS/BLOCK** with its veto-clears-when predicate; **the author does not clear it**. Attack the mockup through the harness: switch every persona, viewport, state, theme and the reduced-motion path, and confirm each is real rather than claimed.

**Stage 5 — CONVERGE (produce the artifacts).**
- **Mockup** — a **self-contained, dependency-free HTML file** at `docs/mockups/<surface>.html` (DX8): one file, no build step, no CDN, opens over `file://`. It renders the **hard states** — empty/first-run, loading (skeleton matching the content shape), error with its real recovery affordance, partial/degraded, and overflow with realistic extreme content (the longest name, the 7-digit number, the negative value, the missing avatar) (DX9, DX16). It ships with the **review harness** (DX10): a control bar switching **persona · viewport · component state · theme/density · capability flags · reduced motion**, plus in-artifact mechanical checks (computed contrast per pairing, undersized targets flagged) (DX11). The harness is review chrome and never ships to production. Start from `templates/mockup-harness.template.html`.
- **Hub node** — `docs/mockups/<surface>.md` carrying the V2 frontmatter and typed links, so the mockup is in the graph (the `.html` is data; the `.md` is the node).
- **Design language** — `DESIGN.md` created/updated, lint-clean, preview rendered.
- **Review artifact (review/elevate mode)** — `docs/reviews/ui-<surface>.md` from `templates/ui-review.template.md`: the measurements, the rubric findings, the scorecard by dimension, and a **ranked plan** — must-fix / should-fix-next / worth-doing — with **the single highest improvement-to-effort change named explicitly** (DX25). A review that returns 40 undifferentiated findings gets ignored, and the reviewer owns that.
- State the residual risk and the flagged unknowns. Where the work changed the UI acceptance criteria, update the spec's Part C rather than letting the artifacts diverge.

**Close with the status table (mandatory).** End the response with:

| | |
|---|---|
| **Completed** | the surface(s) designed or reviewed in this run |
| **Remaining** | the surfaces/states still undesigned or unreviewed |
| **Best next action** | the single concrete next step (typically the highest-leverage fix from the ranked plan, `/design` for the component beneath it, or `/implement`) |

## Output artifact
- `docs/mockups/<surface>.html` — self-contained, dependency-free high-fidelity mockup with the review harness and the hard states (+ `docs/mockups/<surface>.md` hub node with frontmatter).
- `DESIGN.md` — the project design language, created or updated, `design-lint.py`-clean, with its rendered preview.
- `docs/reviews/ui-<surface>.md` (review/elevate mode) — measurements, rubric findings with severities, scorecard, and the ranked plan with the highest-leverage change named.

## Definition of done (exit gate)
- [ ] **Direction brief written before any visual artifact** — user + emotional state, JTBD, **Archetype Signature** (justified from the JTBD), three adjectives *and their opposites*, named references with what's taken, anti-goals, constraints (DX5).
- [ ] **Archetype verified against the shape of the task** — including on an existing screen; reading-vs-entering checked (DX5, UX-A).
- [ ] **UX layer settled first**: Part B exists and its flows cover alternate/error/recovery paths; no settled Surface over an unsettled Structure (S2, S7).
- [ ] Personality decided in **type / color / space** with a one-line justification each (DX6).
- [ ] **System before screens**: `DESIGN.md` produced/updated with token frontmatter, **token-layer contrast audit**, complete state matrix, modes, paired Archetype Signature, motion, copy, performance budget, AI-UX rules; `design-lint.py` clean; preview rendered (DX2, U3a).
- [ ] **Mockup** is self-contained and dependency-free, committed under `docs/mockups/`, and renders **empty / loading / error / partial / overflow** with realistic extreme content (DX8–DX9, DX16).
- [ ] **Review harness** present and exercised — persona · viewport · state · theme/density · capability flags · **reduced motion** — with in-artifact contrast/target checks (DX10–DX11).
- [ ] **Craft** holds: real scale contrast, spacing-as-grouping (tighter within than between), restrained color with an earned accent, optical alignment, **one defended focal point**, density calibrated with matching hierarchy (DX12–DX18).
- [ ] **Motion inventory** written; durations/easings consistent; reduced-motion path proven in the harness; **no layout shift** (DX19–DX20, U17).
- [ ] **Real in-voice copy** drafted here, not deferred: actionable errors, teaching empty states, consequence-naming confirmations, units + precision (DX21, TQ2).
- [ ] **Generic-tells self-check** passed — each tell absent or a justified deliberate choice (DX3).
- [ ] **Measured before diagnosed** (review/elevate): counts recorded for controls, sections, load calls, focal points, type sizes, colors, redundant modes (DX23).
- [ ] **Rubric critique run structure-before-surface**; every finding carries location · dimension · severity · evidence · fix · confidence (DX22, DX24).
- [ ] **WCAG 2.2 AA** met and evidenced; the **UX & Accessibility hard veto** is cleared **by someone other than the author** (U16).
- [ ] **Ranked plan** delivered with must-fix / should-fix-next / worth-doing and **the highest-leverage change named** (DX25).
- [ ] For expert/quantitative surfaces, **`technical-ui-design.md`** applies: numeric legibility, perceptually-uniform colormaps (never jet), uncertainty-first, direct-manipulation-plus-precision (TQ1–TQ12).
- [ ] For AI surfaces, the applicable **HAX** guidelines and **Shape-of-AI** patterns are named, and the **wrong answer and uncertainty are designed as first-class states** (U13–U15).

## Documentation & discoverability (last action)
Per the **Knowledge Visualization & Docs Explorer Standard** (`knowledge/knowledge-visualization.md`, the Discoverability Mandate V10): after producing the artifacts, **write each one's frontmatter** (V2: id, title, type, status, **owner**, phase, tags, **typed links** per the relation registry, **review-by** per the type's SLA, and a real 1–3-sentence summary — the mockup's hub `.md` is the graph node; the `.html` is data) and **sync the derived `docs/docs-index.js`** by running the script bundle — `python3 docs/ai-forward-pack/scripts/docs-graph.py derive` (and `flag --changed <id> --reason …` for V16 propagation) — never ad-hoc scripts (V18); frontmatter wins wherever the two disagree. Ensure `docs/index.html` (the Docs Explorer) exists — instantiate it from `templates/docs-explorer.template.html` if missing — and verify each new entry has at least one typed link into the graph (an orphan is a finding). Index and diagrams land **in the same change** as the content (V11). **Propagate impact (V16):** a changed UI contract, archetype, or token system is material — flag the inbound neighbours (the spec's Part C, the component designs that render this surface) `review-suggested`. **Capture session exhaust (V17):** any direction decision, rejected alternative, or discovered constraint below ADR weight becomes a linked **decision note** (`docs/notes/`) before close. **Register what was learned (CI1):** any UI defect found or created in this run is captured as a **class** in `docs/lessons/defect-classes.md` with its control (`continuous-improvement.md`).

**Audit (last action).** Append an audit-log entry for this run — `python3 docs/ai-forward-pack/scripts/audit-log.py append --shortname "ui-design-<surface>" --session "<id>" --skill ui-design --kind skill --prompt "<the prompt, verbatim>" --summary "<what it produced or found>" --artifact docs/mockups/<surface>.html` — per the Audit Mandate (`knowledge/audit-and-change-log.md`, AL5). When the run settles a load-bearing direction or archetype decision, also add a change-log entry (`audit-log.py change`, CL1).

**Handoff:** → `/specify` if the UX layer beneath is unsettled · → `/design` for the component contracts behind the approved surface · → `/implement` to build it against `DESIGN.md` (referencing tokens, never raw values) · → `/investigate` if the review uncovered a defect in running software.
