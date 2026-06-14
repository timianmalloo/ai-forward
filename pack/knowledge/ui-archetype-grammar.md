# UI Archetype Grammar & Determinism Control

*A formal grammar for **identifying** a UI/UX template and using it as a **determinism control** for code generation. It gives `/specify` and `/design` a compact, unambiguous way to pin the *kind* of interface being built — its routing model, temporal behavior, data posture, and surface flavor — so an agentic coding tool (in Claude Code or GitHub Copilot) reaches for the right archetype every time instead of defaulting to a generic dashboard. It composes with, and never replaces, the **UI & Interaction Design Standard** (`ui-interaction-design.md`, U1–U20, the token/state/flow authority) and the **Specification Standards** (`specification-standards.md`, S1–S18, the three spec layers). Catalog of archetypes with exemplars and codegen descriptors: `ui-archetype-catalog.md`.*

Normative keywords (**MUST**, **SHOULD**, **MAY**, **MUST NOT**) follow RFC 2119.

The governing idea: **determinism in generated UI comes from constraining the search space before generation, not from correcting after.** A coding model asked for "a dashboard" picks from a vast space and regresses to the mean; the same model given `Type:DSS; Arch:SPA; Layout:ModularDashboard; Pacing:Freeform; …` plus the archetype's named exemplars and codegen rules produces a tightly-bounded, predictable result. The grammar is that constraint — a **selector over a coordinate space of archetypes** — and it is deliberately *two-layer*: a coarse **Archetype Signature** (this document) that picks the template, composed with the **concrete spec** (U1–U20 tokens, states, flows; S1–S18 layers) that fills it in. One without the other is incomplete: the signature alone is a classifier (it can't carry a hex value or an empty state), and U1–U20 alone doesn't pin the routing/temporal model. Together they make a template both *identifiable* and *buildable*.

This work began from an external taxonomy (the "Web Design Theme Taxonomy / UX Grammar v5.0") whose key insight is retained and credited: **modern high-value apps are temporal state machines, not just spatial destinations**, so the grammar must encode *time, pacing, and data persistence*, not only DOM layout. This standard hardens that taxonomy into a valid, multi-valued, composable grammar and wires it to the pack's existing token/state/flow discipline.

---

## 0. Why this exists (the determinism problem)

A code-generation model is a sampler over a distribution of plausible UIs. Three forces make raw output non-deterministic in *kind*: the prompt underspecifies the archetype ("build a checkout" — tunnel or multi-page?), the model regresses toward the most common training example (everything becomes a sidebar dashboard), and stylistic vocabulary is ambiguous ("clean", "modern" mean nothing operationally). The fix is an **architectural fingerprint** the model reads before it generates — a fixed-arity signature naming the routing model, the temporal/pacing behavior, the data/sync posture, and the surface flavor — paired with **named exemplars** (so the model anchors to concrete, known-good references) and **explicit codegen rules** (so the abstract facet becomes a concrete instruction: `Pacing:LockedUntilValid` → "disable the Next button until validation passes"). The signature shrinks the search space; the spec layers (U1–U20) make the remaining choices concrete; the result is reproducible.

This is also why the grammar is **descriptive before generative**: the same signature must *identify* an existing UI (so we can catalog exemplars and audit what an agent built) and *drive* a new one. A signature that round-trips — identify Linear as `KeyboardVelocity`, then generate something Linear-like from it — is the test that it carries real information.

---

## 1. The two layers

**G1 — Archetype Signature + concrete spec, always both.** A UI template is specified as an **Archetype Signature** (this grammar, §2) **composed with** a concrete spec (the U1–U20 UI layer and, in `/specify`, the S1–S18 layers). The signature selects the archetype and its determinism profile; the spec carries the tokens, the complete component states (U9), the real copy (U11), the user flows (S6), and accessibility/performance floors (U16–U17). **A signature alone is never a sufficient UI spec** — it is the constraint, not the content.

**G2 — The signature is a selector, not the design.** The signature names *which* archetype and *how it behaves in time and data*; it does **not** encode values (no hex, no spacing scale, no breakpoint widths) — those live in tokens (U3–U5). The one bridge to specifics is `StyleHints` (§2.9), a bounded natural-language decorator layer applied *on top of* the structural signature, never a substitute for tokens.

**G3 — Composition direction.** Read top-down for generation: the **Category/Architecture** facets fix the routing and temporal model (the skeleton of behavior), then **Layout/Context/Visuals** shape structure and surface, then **Data/Interaction** fix sync posture and feel, then **A11y** sets the floor, then **StyleHints** decorate, then the **U1–U20 spec** makes every remaining choice concrete. Lower-altitude facets must not contradict higher ones (a `StrictFunnel` architecture with `Freeform` pacing is a conflict — §4).

---

## 2. The Archetype Signature grammar (EBNF)

The grammar is **valid, multi-valued, and order-tolerant**. Improvements over the source taxonomy: every nonterminal resolves (no dangling symbols); facets that are independent in reality (input modes, motion, accessibility, feedback) are **sets**, not single-choice; whitespace and facet order are lexer-handled, not baked into terminals; and an explicit **extension hook** (`x-` custom facet values) keeps closed enums from blocking real cases.

```ebnf
(* ── Top level ──────────────────────────────────────────────── *)
Signature      ::= Name "{" FacetList "}" StyleHints?
Name           ::= Ident
FacetList      ::= Facet (";" Facet)* ";"?          (* order-independent; each facet at most once *)
Facet          ::= Category | Architecture | Layout | Density | Nav
                 | Viewport | Input | Color | Typography | Depth
                 | Sync | Persistence | Feedback | Motion | Pacing
                 | Transition | A11y | Custom

(* ── Identity & routing ─────────────────────────────────────── *)
Category       ::= "Type"  ":" CategoryV
CategoryV      ::= "Consumer" | "OLTP" | "DSS" | "Hybrid" | "Conversational"
                 | "Authoring" | "MediaFeed" | "RTC" | "GuidedJourney"
                 | "Commerce" | "EdTech" | "Configurator" | "Diagnostic"
                 | "Kiosk" | "Portal" | "Marketing" | Ext
Architecture   ::= "Arch"  ":" ArchitectureV
ArchitectureV  ::= "SPA" | "MPA" | "InfiniteScroll" | "Streaming"
                 | "SpatialUnbounded" | "HubAndSpoke" | "StateMachine"
                 | "StrictFunnel" | "Branching" | "Islands" | Ext

(* ── Layout & structure ─────────────────────────────────────── *)
Layout         ::= "Layout" ":" LayoutV
LayoutV        ::= "BentoBox" | "MasterDetail" | "ModularDashboard"
                 | "SpatialCanvas" | "CinematicHero" | "FormWizard"
                 | "BlockDocument" | "StreamingThread" | "CarouselGrid"
                 | "RuggedGrid" | "ProgressiveOrchestrator" | "TunnelCheckout"
                 | "GamifiedCanvas" | "SplitConfigurator" | "HolyGrail" | Ext
Density        ::= "Density" ":" DensityV
DensityV       ::= "Spacious" | "Comfortable" | "Compact" | "UltraDense"
Nav            ::= "Nav" ":" NavV ("+" NavV)*        (* set: e.g. Sidebar+CommandPalette *)
NavV           ::= "TopBar" | "Sidebar" | "CommandPalette" | "FloatingContext"
                 | "Stepper" | "BottomTab" | "LockedFunnel" | "ProgressPills"
                 | "Breadcrumb" | "Hidden" | Ext

(* ── Context (hardware/viewport/input) ──────────────────────── *)
Viewport       ::= "Viewport" ":" ViewportV
ViewportV      ::= "MobileNative" | "FluidResponsive" | "DesktopBound" | "FixedLocked"
Input          ::= "Input" ":" InputV ("+" InputV)*  (* set: Touch+Keyboard is normal *)
InputV         ::= "TouchPrimary" | "KeyboardFirst" | "PrecisionPointer"
                 | "Multimodal" | "SpatialGestures" | "Voice" | Ext

(* ── Visuals (flavor only; values live in tokens, U3–U5) ────── *)
Color          ::= "Color" ":" ColorV
ColorV         ::= "Vibrant" | "Monochrome" | "HighContrast" | "DarkAdaptive"
                 | "BrandCentric" | "MediaDark" | "Pastel" | Ext
Typography     ::= "Type" ":" TypographyV
TypographyV    ::= "Expressive" | "Utilitarian" | "MonospaceTechnical" | "EditorialSerif" | Ext
Depth          ::= "Depth" ":" DepthV
DepthV         ::= "Flat" | "SoftShadow" | "Glassmorphism" | "NeoBrutalist" | "Diegetic3D" | Ext

(* ── Data (the "brain": sync + persistence) ─────────────────── *)
Sync           ::= "Sync" ":" SyncV
SyncV          ::= "Multiplayer" | "LocalFirst" | "Optimistic" | "Stateless"
                 | "ServerStrict" | "AsyncPipeline" | "Polling" | Ext
Persistence    ::= "Persistence" ":" PersistenceV
PersistenceV   ::= "Ephemeral" | "Session" | "Cloud" | "EncryptedVault" | "LocalDevice" | Ext

(* ── Interaction (the "feel": time + response) ──────────────── *)
Feedback       ::= "Feedback" ":" FeedbackV ("+" FeedbackV)*   (* set *)
FeedbackV      ::= "Instant" | "Optimistic" | "Confirmed" | "Haptic" | "Generative"
                 | "Choreographed" | "StrictValidation" | "Gamified" | Ext
Motion         ::= "Motion" ":" MotionV ("+" MotionV)*         (* set: Micro+ScrollDriven *)
MotionV        ::= "None" | "Micro" | "Fluid" | "ScrollDriven" | "PhysicsBased"
Pacing         ::= "Pacing" ":" PacingV
PacingV        ::= "Freeform" | "UserDriven" | "SystemDriven" | "LockedUntilValid"
Transition     ::= "Transition" ":" TransitionV
TransitionV    ::= "None" | "Morph" | "Slide" | "Crossfade" | "HardCut"

(* ── Accessibility (floor; a SET — these co-apply) ──────────── *)
A11y           ::= "A11y" ":" A11yV ("+" A11yV)*
A11yV          ::= "WCAG_2.2_AA" | "WCAG_2.2_AAA" | "ReducedMotion" | "HighLegibility" | "ScreenReaderFirst"

(* ── Extension hook & decorators ────────────────────────────── *)
Custom         ::= "x-" Ident ":" (Ident | String)   (* escape hatch for novel facets *)
Ext            ::= "x-" Ident                          (* novel value within a known facet *)
StyleHints     ::= "[StyleHints:" HintList "]"
HintList       ::= String ("," String)*
String         ::= '"' /[^"]*/ '"'
Ident          ::= /[A-Za-z_][A-Za-z0-9_]*/
```

**G4 — Required vs optional facets.** A well-formed signature **MUST** carry `Type`, `Arch`, `Layout`, and `Pacing` (the four that most determine generated structure and behavior). All other facets **SHOULD** be present for a production spec and **default** per §3 when omitted. `StyleHints` is **MAY**.

**G5 — Multi-valued facets.** `Nav`, `Input`, `Feedback`, `Motion`, and `A11y` are **sets** (joined with `+`) because real interfaces combine them (a SaaS app is `Input:KeyboardFirst+PrecisionPointer`; an AI app is `Feedback:Generative+Optimistic`; accessibility is always at least `A11y:WCAG_2.2_AA` and often `+ReducedMotion`). Single-choice facets (`Type`, `Arch`, `Layout`, `Density`, `Viewport`, `Color`, `Type`, `Depth`, `Sync`, `Persistence`, `Pacing`, `Transition`) take exactly one value.

**G6 — A11y is a floor, not a flavor.** Unlike the source taxonomy (which made accessibility one mutually-exclusive choice), `A11y` is a set and **MUST** include at least `WCAG_2.2_AA` (per U16). `ReducedMotion`, `HighLegibility`, `ScreenReaderFirst` are independent obligations that co-apply. The UX & Accessibility lens holds the veto here exactly as under U16.

---

## 3. Facet semantics & defaults

Each facet, what it controls, and its omitted-default. Defaults bias toward the safest, most common production choice so a partial signature still generates sanely.

| Facet | Controls | Default when omitted |
|---|---|---|
| `Type` | The product archetype family (selects the catalog row) | *required* |
| `Arch` | Routing & temporal model (SPA vs StateMachine vs InfiniteScroll …) | *required* |
| `Layout` | Dominant structural pattern (the skeleton) | *required* |
| `Density` | Information density (maps to spacing-scale choice, U5) | `Comfortable` |
| `Nav` | Navigation mechanism(s) | `TopBar` |
| `Viewport` | Target viewport/hardware constraint | `FluidResponsive` |
| `Input` | Primary input modality(ies) | `PrecisionPointer+KeyboardFirst` |
| `Color` | Color strategy flavor (palette lives in tokens) | `BrandCentric` |
| `Type` (Typography) | Type personality (families live in tokens) | `Utilitarian` |
| `Depth` | Elevation/material treatment | `SoftShadow` |
| `Sync` | Client↔server data strategy | `ServerStrict` |
| `Persistence` | What survives refresh | `Cloud` |
| `Feedback` | System-response mechanism(s) | `Confirmed` |
| `Motion` | Animation posture(s) | `Micro` |
| `Pacing` | Who controls progression speed | *required* |
| `Transition` | How states change visually | `Crossfade` |
| `A11y` | Accessibility obligations (a floor) | `WCAG_2.2_AA` |

**G7 — Facets map to concrete codegen decisions.** The point of each facet is that it resolves to an implementation instruction. The catalog (`ui-archetype-catalog.md`) carries per-archetype rules; the cross-cutting facet→instruction map is:
- `Arch:StateMachine` / `StrictFunnel` / `Branching` → a guarded step machine (often a DAG for `Branching`); forward progress gated; no deep-linking past an incomplete gate.
- `Pacing:LockedUntilValid` → progression controls disabled until validation passes; `UserDriven` → user advances; `SystemDriven` → the system advances (streaming).
- `Sync:Optimistic` → mutate local state immediately, reconcile on server response, roll back on failure; `LocalFirst` → local store is source of truth, background sync; `AsyncPipeline` → long-running job with a progress/"labor-illusion" surface, not a spinner; `ServerStrict` → await authoritative response before progressing.
- `Feedback:Choreographed` → replace generic spinners with a narrated progress surface (streaming status text) during waits; `Generative` → token-streamed output with stop/regenerate (composes with U13–U15 AI patterns); `StrictValidation` → aggressive inline validation with blocking errors.
- `Motion:ScrollDriven` → scroll-linked animation (progress → transforms), pinned sections; `PhysicsBased` → spring/inertia; all motion honors `prefers-reduced-motion` (U10) and the `A11y:ReducedMotion` obligation.
- `Persistence:EncryptedVault` → sensitive data encrypted at rest, never in plain logs/URLs (composes with the privacy review); `Ephemeral` → nothing survives refresh by design.
- `Density:UltraDense` → tightest spacing tokens, tabular/monospace numerics; `Spacious` → generous spacing tokens.

---

## 4. Validity & conflict rules (semantic, beyond syntax)

A syntactically valid signature can still be **semantically incoherent**. These rules are checkable and are part of the gate.

**G8 — No facet contradicts a higher-altitude facet.** Known conflicts to reject (or flag for explicit override with rationale):
- `Arch:StrictFunnel`/`StateMachine` with `Pacing:Freeform` — a locked flow cannot be freely paced.
- `Arch:InfiniteScroll`/`Streaming` with `Pacing:LockedUntilValid` — a continuous feed has no validation gate.
- `Sync:Stateless` with `Persistence:Cloud`/`EncryptedVault` — stateless implies nothing to persist server-side beyond the request.
- `Viewport:FixedLocked` (kiosk) with `Input:KeyboardFirst` as the *only* input — kiosks are touch-first; keyboard may be secondary.
- `Motion:None` with `Transition:Morph`/`Slide` — no motion contradicts animated transitions (use `Transition:None`/`HardCut`).
- `Layout:TunnelCheckout` with `Nav:Sidebar`/`TopBar` — a tunnel removes global nav (`Nav:LockedFunnel`/`ProgressPills`/`Hidden`).

**G9 — Coherent archetype, or explicit deviation.** A signature SHOULD match a catalog archetype's profile; deviations from the catalog's canonical signature are allowed but **recorded as deviations with rationale** (mirroring U12's "familiar unless justified"). An agent generating from a signature that conflicts with its declared `Type` must surface the conflict, not silently resolve it.

**G10 — Round-trip test.** A signature is well-formed enough to use when it can both *identify* a named exemplar and *drive* generation of something recognizably in that family. The catalog's exemplars are the fixtures for this check.

---

## 5. Using the grammar for deterministic code generation

**G11 — The codegen contract.** When a signature drives generation, the agent (in Claude Code or GitHub Copilot) MUST: (a) resolve the archetype from `Type`+`Arch`+`Layout` and load its catalog row; (b) apply every facet's codegen rule (§3, G7) and the archetype's specific rules; (c) realize the concrete spec — tokens (U3–U5), **complete component states incl. empty/loading/error** (U9), real copy (U11), the user flows incl. unhappy paths (S6); (d) meet the `A11y` floor and the performance budget (U16–U17); (e) treat `StyleHints` as decoration applied last, over the structure, never as a structural instruction. A facet with no corresponding implementation is an incomplete build (the UX & Accessibility veto for states/floors; the Test Architect for coverage).

**G12 — Determinism, not rigidity.** The signature constrains *kind*, not *every pixel*. Within the archetype, the agent still designs (the spec layers carry that). The goal is that two generations from the same signature + spec are the **same archetype with the same behavioral and state contract** — not byte-identical. Where the source under-determines, the spec layers (not the model's defaults) decide.

**G13 — Surfacing in the artifacts.** In `/specify`, the chosen signature is recorded in the spec's **Part C (UI)** as the archetype selector, with deviations noted (S8). In `/design`, the signature heads the UI design section and each facet's resolution is made concrete against the tokens and states. In `/implement`, the build satisfies the facet rules and the spec proves them (the U9 state tests, the U16 a11y tests, the U17 budget — red-first, like security tests).

---

## 6. Authoring & evolving signatures

**G14 — Identify before you generate.** To catalog or audit an existing UI, write its signature by observation (its routing, pacing, data posture, surface) and match it to the nearest archetype; discrepancies are either a new archetype candidate or a deviation. To build, start from the nearest catalog archetype's canonical signature and adjust facets with rationale.

**G15 — Extension over violation.** Novel cases use the `x-` hook (`x-` value within a facet, or an `x-name:` custom facet) rather than forcing a wrong enum. Recurring `x-` usage is the signal to propose a new enum value or a new archetype (a catalog change, versioned like any pack change).

**G16 — Versioned vocabulary.** The enum sets and the archetype catalog are versioned with the bundle (the INSTALL changelog). Adding a value or archetype is a normal change: update this grammar, the catalog, and the changelog together.

---

## 7. Self-verification checklist (signatures)

- [ ] Signature carries the four required facets (`Type`, `Arch`, `Layout`, `Pacing`); others present or intentionally defaulted (G4).
- [ ] Multi-valued facets use sets correctly; single-choice facets carry one value (G5).
- [ ] `A11y` includes at least `WCAG_2.2_AA`; co-obligations listed (G6).
- [ ] No semantic conflicts (§4 G8), or each deviation recorded with rationale (G9).
- [ ] Composed with a concrete spec — tokens, **complete component states**, real copy, flows, a11y + performance floors (G1, G11); the signature is not standing in for the spec.
- [ ] Maps to an archetype in `ui-archetype-catalog.md`, or a new archetype/`x-` extension is proposed (G14–G15).
- [ ] Recorded in the right artifact layer: spec Part C / design UI section / implementation proofs (G13).

---

## 8. References & provenance

- **Source taxonomy** — the externally-provided *"Web Design Theme Taxonomy & Formal Grammar (v5.0)" / "UX/UI Formal Grammar"* (Gemini-authored). Retained insight: **apps are temporal state machines, not just spatial destinations**, so the grammar encodes *time, pacing, and data persistence*. This standard hardens it (valid EBNF, multi-valued facets, defaults, conflict rules, extension hook) and composes it with the pack's token/state/flow discipline. The original archetype roster and exemplars are carried, corrected, and extended in `ui-archetype-catalog.md`.
- **`ui-interaction-design.md`** (U1–U20) — the authority the signature composes with for tokens, component states, AI-UX patterns (HAX/Shape-of-AI), accessibility, and performance. The signature selects; U1–U20 makes concrete.
- **`specification-standards.md`** (S1–S18) — the three spec layers; the signature lands in Part C (UI), gated behind the Part B (UX) flows.
- **Garrett's Five Planes** (via `specification-standards.md`) — the signature spans Scope (Category), Structure/Skeleton (Architecture/Layout/Nav), and Surface (Visuals); the spec layers carry the rest.
- **`ui-archetype-catalog.md`** — the filled-out table: archetypes, exemplars, canonical signatures, and codegen descriptors.
