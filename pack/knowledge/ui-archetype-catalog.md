# UI Archetype Catalog

*The filled-out companion to the **UI Archetype Grammar** (`ui-archetype-grammar.md`, G1–G16). Each row is a UI/UX archetype: its **exemplars** (real, known-good references an agent can anchor to), its **canonical Archetype Signature** (the determinism selector), a plain description, and the **codegen descriptor** — the concrete, model-agnostic instructions a coding tool follows to build it. Use a row as the starting point: copy its signature, adjust facets with rationale (grammar G9), then compose with the concrete spec (tokens U3–U5, complete component states U9, real copy U11, flows S6, a11y/perf floors U16–U17). The signatures here are **hardened**: multi-valued facets are sets, `A11y` always carries `WCAG_2.2_AA`, and conflicts (grammar §4) are resolved.*

**How to read a row for generation.** Resolve the archetype from `Type`+`Arch`+`Layout` → apply the codegen descriptor → apply each facet's cross-cutting rule (grammar §3/G7) → realize the concrete spec → meet the floors → apply `StyleHints` last as decoration. The descriptors name *techniques and structures*, not specific libraries or model features, so they hold across stacks and across coding tools (Claude Code, GitHub Copilot) and model versions.

---

## A. Temporal / guided archetypes (state machines — the highest-determinism wins)

### A1 · Phased Narrative Orchestrator
- **Exemplars:** [PrinciplesYou](https://principlesyou.com/) · [Noom](https://www.noom.com/) · [16Personalities](https://www.16personalities.com/)
- **Category:** GuidedJourney · Expert/assessment systems
- **Signature:** `PhasedOrchestrator { Type:GuidedJourney; Arch:StateMachine; Layout:ProgressiveOrchestrator; Density:Spacious; Nav:Stepper+ProgressPills; Viewport:FluidResponsive; Input:Multimodal; Color:BrandCentric; Type:EditorialSerif; Depth:SoftShadow; Sync:AsyncPipeline; Persistence:Cloud; Feedback:Choreographed; Motion:ScrollDriven+Micro; Pacing:UserDriven; Transition:Slide; A11y:WCAG_2.2_AA; }`
- **Description:** A multi-stage app that locks the user into a focused stepper, orchestrates long-running (often AI) work behind a narrated wait, and resolves into an immersive results surface.
- **Codegen descriptor:** Build a **3-phase guarded state machine** (Intake → Orchestration → Reveal); Phase N+1 is unreachable until Phase N's gate passes. *Intake:* minimalist, one decision per screen, global nav hidden to cut cognitive load, progression disabled until validation passes (`Pacing:UserDriven`). *Orchestration:* on submit, **never a generic spinner** — render a narrated progress surface ("labor illusion") streaming status lines while the async job/AI call runs (`Sync:AsyncPipeline`+`Feedback:Choreographed`; if AI, compose U13–U15 — disclose, allow cancel). *Reveal:* unlock and transition (`Slide`) into a scroll-driven results dashboard. State persists to cloud so refresh resumes the correct phase. Every phase ships its empty/loading/error states (U9). `StyleHints` decorate (palette → borders/background; accent palette → charts only).

### A2 · Secure Checkout Pipeline
- **Exemplars:** [Shopify Checkout](https://www.shopify.com/checkout) · [Stripe Checkout](https://stripe.com/payments/checkout) · [Apple Store](https://www.apple.com/store)
- **Category:** Commerce · Conversion funnels
- **Signature:** `CheckoutTunnel { Type:Commerce; Arch:StrictFunnel; Layout:TunnelCheckout; Density:Comfortable; Nav:LockedFunnel+ProgressPills; Viewport:FluidResponsive; Input:KeyboardFirst+TouchPrimary; Color:HighContrast; Type:Utilitarian; Depth:Flat; Sync:ServerStrict; Persistence:EncryptedVault; Feedback:StrictValidation+Confirmed; Motion:Micro; Pacing:LockedUntilValid; Transition:Crossfade; A11y:WCAG_2.2_AA+HighLegibility; }`
- **Description:** A strictly linear flow that removes external navigation to focus entirely on sequential, secure data entry — the conversion gold standard.
- **Codegen descriptor:** **Strip all global navigation and outbound links** — the tunnel is inescapable by design. Each step uses **aggressive inline validation** with auto-formatting (card, postal, email); the advance control is disabled until the step validates (`Pacing:LockedUntilValid`) and a real server **200 handshake** confirms before progression (`Sync:ServerStrict`). Sensitive fields never appear in logs or URLs; payment data follows `EncryptedVault` posture (compose the privacy review). Trust indicators near the pay action; error states are humane and specific (U9/U11). `StyleHints`: muted, trustworthy palette.

### A3 · Branching Diagnostic Wizard
- **Exemplars:** [TurboTax](https://turbotax.intuit.com/) · [BetterHelp](https://www.betterhelp.com/) · [Apple Support](https://getsupport.apple.com/)
- **Category:** Diagnostic · Triage
- **Signature:** `DiagnosticWizard { Type:Diagnostic; Arch:Branching; Layout:FormWizard; Density:Spacious; Nav:Stepper+Breadcrumb; Viewport:FluidResponsive; Input:KeyboardFirst+TouchPrimary; Color:Monochrome; Type:Utilitarian; Depth:Flat; Sync:ServerStrict; Persistence:Cloud; Feedback:Confirmed; Motion:Micro; Pacing:LockedUntilValid; Transition:Morph; A11y:WCAG_2.2_AA; }`
- **Description:** A smart form that hides future questions and computes the next step from the prior answer, building a personalized path to a diagnosis.
- **Codegen descriptor:** Implement a **DAG state manager** where step N+1 is derived from step N's answer — **do not render all fields at once**. Use large card-based selection grids for choices. Persist progress so a refresh resumes mid-path. Show a breadcrumb of decided steps (revisitable) without exposing undecided ones. Morph transitions between questions. Every branch terminates in a clear result state with next actions (U9/U11).

### A4 · Gamified Learning Loop
- **Exemplars:** [Duolingo](https://www.duolingo.com/) · [Brilliant](https://brilliant.org/) · [Codecademy](https://www.codecademy.com/)
- **Category:** EdTech · Consumer
- **Signature:** `GamifiedLoop { Type:EdTech; Arch:SPA; Layout:GamifiedCanvas; Density:Spacious; Nav:ProgressPills; Viewport:MobileNative; Input:TouchPrimary; Color:Vibrant; Type:Expressive; Depth:NeoBrutalist; Sync:Optimistic; Persistence:Cloud; Feedback:Gamified+Instant; Motion:PhysicsBased+Micro; Pacing:UserDriven; Transition:Morph; A11y:WCAG_2.2_AA+ReducedMotion; }`
- **Description:** A fast, sequential interface pairing micro-interactions with immediate, visually explosive validation and progress.
- **Codegen descriptor:** Map correct answers to **instant UI updates with micro-animations** (e.g., bouncing checkmarks, streak counters). Mutate state optimistically so feedback is zero-latency (`Sync:Optimistic`). Use shared-element/`Morph` transitions to animate elements seamlessly between questions. Physics-based motion for celebratory moments — but gate all of it behind `prefers-reduced-motion` (the `A11y:ReducedMotion` obligation is non-negotiable). Progress pills and reward states are first-class (U9). `StyleHints`: bold, thick-bordered, playful.

---

## B. Operational / data-dense archetypes (OLTP, DSS, admin)

### B1 · Keyboard-Velocity GUI
- **Exemplars:** [Linear](https://linear.app/) · [Superhuman](https://superhuman.com/) · [Raycast](https://www.raycast.com/)
- **Category:** OLTP / SaaS — power-user operational throughput
- **Signature:** `KeyboardVelocity { Type:OLTP; Arch:SPA; Layout:MasterDetail; Density:Compact; Nav:CommandPalette+Sidebar; Viewport:DesktopBound; Input:KeyboardFirst+PrecisionPointer; Color:DarkAdaptive; Type:Utilitarian; Depth:Flat; Sync:LocalFirst; Persistence:Session; Feedback:Optimistic; Motion:Micro; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA; }`
- **Description:** A sleek, dark interface stripped of excess padding, built to function like a rapid developer IDE for fast task triage.
- **Codegen descriptor:** Strip UI padding to strict minimum bounds (4–8px scale, `Density:Compact`). Implement a **global keydown listener for a Command Palette** (Cmd/Ctrl+K) as a primary nav path; trap keyboard focus within active panels; ensure **zero layout shift on render**. State mutations are **optimistic** with background sync (`Sync:LocalFirst`) so the UI never blocks. Hard-cut transitions (no animation tax on speed). Full keyboard operability is both the archetype's point and the a11y floor (U16). `StyleHints`: subtle accent on dark.

### B2 · Enterprise Master-Detail
- **Exemplars:** [Stripe Dashboard](https://dashboard.stripe.com/) · [Salesforce](https://www.salesforce.com/) · [Shopify Admin](https://admin.shopify.com/)
- **Category:** OLTP / Admin — relational record management at volume
- **Signature:** `EnterpriseMasterDetail { Type:OLTP; Arch:SPA; Layout:MasterDetail; Density:Comfortable; Nav:Sidebar+Breadcrumb; Viewport:FluidResponsive; Input:PrecisionPointer+KeyboardFirst; Color:BrandCentric; Type:Utilitarian; Depth:SoftShadow; Sync:ServerStrict; Persistence:Cloud; Feedback:Confirmed; Motion:Micro; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA+HighLegibility; }`
- **Description:** A split-view layout using a prominent left sidebar to manage deeply relational business data.
- **Codegen descriptor:** **CSS Grid: fixed left sidebar + fluid `1fr` content pane.** Relational data uses **split-view panes** (master list left, detail context right). Tables require **sticky headers**, virtualized rows for large sets, column sort/filter, and a persistent detail drawer. Mutations confirm against the server before reflecting (`Sync:ServerStrict`). Bulk actions and empty/loading/error/overflow states are designed (U9). `StyleHints`: crisp, high-legibility, neutral backgrounds.

### B3 · Telemetry Bento Box
- **Exemplars:** [Vercel Analytics](https://vercel.com/analytics) · [Datadog](https://www.datadoghq.com/) · [PostHog](https://posthog.com/)
- **Category:** Analytics / DSS — real-time visualization
- **Signature:** `TelemetryBento { Type:DSS; Arch:SPA; Layout:ModularDashboard; Density:Compact; Nav:Sidebar; Viewport:FluidResponsive; Input:PrecisionPointer; Color:Monochrome; Type:MonospaceTechnical; Depth:Flat; Sync:Polling; Persistence:Ephemeral; Feedback:Instant; Motion:None; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA; }`
- **Description:** A strict, modular dashboard confining real-time charts into uniform bordered cells to maximize spatial legibility.
- **Codegen descriptor:** Build a **strictly bounded CSS Grid** (`grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))`); cards have identical `1px` borders and corner radii. Overflowing data inside a widget **scrolls independently** of the main viewport. Use **tabular-lining / monospace numerics** for arrays and metrics. Live data via polling or stream; each widget owns its loading/empty/error state and a stale-data indicator (U9). Motion off by default (data dashboards distract with animation). `StyleHints`: harsh, precise grid lines.

### B4 · Oversized POS Utility
- **Exemplars:** [Square POS](https://squareup.com/) · [Toast POS](https://pos.toasttab.com/) · [Shopify POS](https://www.shopify.com/pos)
- **Category:** Kiosk / Industrial — error reduction under physical stress
- **Signature:** `POSUtility { Type:Kiosk; Arch:HubAndSpoke; Layout:RuggedGrid; Density:Comfortable; Nav:BottomTab; Viewport:FixedLocked; Input:TouchPrimary; Color:HighContrast; Type:Utilitarian; Depth:Flat; Sync:ServerStrict; Persistence:EncryptedVault; Feedback:Haptic+Confirmed; Motion:None; Pacing:LockedUntilValid; Transition:HardCut; A11y:WCAG_2.2_AA+HighLegibility; }`
- **Description:** A rugged, touch-first layout of large, color-coded grid blocks designed to minimize accidental misclicks in a fast retail setting.
- **Codegen descriptor:** **Disable text selection and pinch-zoom** (`user-select:none; touch-action:none`). All interactive targets are **massive** (`min-height/width: 64px`) with generous spacing to prevent fat-finger errors. Color-code action categories. Confirm destructive/financial actions in deliberate forward-moving modals (`Pacing:LockedUntilValid`). Haptic feedback on key actions. Contrast must meet the highest practical bar for variable lighting. `StyleHints`: primary-color action buttons.

---

## C. Spatial / canvas archetypes

### C1 · Unbounded Spatial Canvas
- **Exemplars:** [Figma](https://www.figma.com/) · [Miro](https://miro.com/) · [Excalidraw](https://excalidraw.com/)
- **Category:** Hybrid / Visual DSS — infinite collaborative canvas
- **Signature:** `SpatialCanvas { Type:Hybrid; Arch:SpatialUnbounded; Layout:SpatialCanvas; Density:Compact; Nav:FloatingContext; Viewport:DesktopBound; Input:PrecisionPointer+SpatialGestures; Color:Monochrome; Type:Utilitarian; Depth:Flat; Sync:Multiplayer; Persistence:Cloud; Feedback:Instant; Motion:None; Pacing:Freeform; Transition:None; A11y:WCAG_2.2_AA; }`
- **Description:** A boundless workspace granting absolute spatial control to pan and zoom across a large visual dataset.
- **Codegen descriptor:** Mount a **Canvas/WebGL plane at `100vw`/`100vh`**; **prevent default browser pinch-zoom**; construct a **2D camera system** managing pan and zoom matrices. Render HTML tools as **absolute overlays** above the canvas. Use **CRDTs** for multiplayer convergence (`Sync:Multiplayer`) with live cursors/presence. Floating contextual toolbars, not global chrome. Provide keyboard-navigable alternatives to spatial gestures for the a11y floor.

---

## D. Streaming / feed / conversational archetypes

### D1 · Generative Stream Thread
- **Exemplars:** [ChatGPT](https://chatgpt.com/) · [Claude](https://claude.ai/) · [Perplexity](https://www.perplexity.ai/)
- **Category:** Conversational AI
- **Signature:** `GenerativeThread { Type:Conversational; Arch:Streaming; Layout:StreamingThread; Density:Comfortable; Nav:Hidden; Viewport:FluidResponsive; Input:Multimodal; Color:DarkAdaptive; Type:Utilitarian; Depth:Flat; Sync:Stateless; Persistence:Session; Feedback:Generative+Optimistic; Motion:Fluid; Pacing:SystemDriven; Transition:Slide; A11y:WCAG_2.2_AA+ScreenReaderFirst; }`
- **Description:** A chat interface centered on a multimodal input, where AI content is delivered sequentially via auto-scrolling message blocks.
- **Codegen descriptor:** Implement **token-by-token streaming** (SSE/WebSocket); bind an observer to **auto-scroll the thread to the bottom** smoothly as tokens arrive; **anchor the input to the bottom**. This is an AI surface, so it MUST satisfy U13–U15: **disclose** AI content, allow **stop/regenerate**, show **uncertainty/citations** where relevant, and design the **wrong-answer path** as first-class. Streamed output remains interruptible (`Pacing:SystemDriven` but user can halt). Message blocks render markdown; copy/feedback affordances per message. Screen-reader-first because streaming content needs careful live-region handling.

### D2 · Immersive Infinite Feed
- **Exemplars:** [TikTok](https://www.tiktok.com/) · [Instagram Reels](https://www.instagram.com/reels/) · [YouTube Shorts](https://www.youtube.com/shorts/)
- **Category:** MediaFeed / UGC
- **Signature:** `InfiniteFeed { Type:MediaFeed; Arch:InfiniteScroll; Layout:CinematicHero; Density:UltraDense; Nav:Hidden; Viewport:FixedLocked; Input:TouchPrimary+SpatialGestures; Color:MediaDark; Type:Expressive; Depth:Flat; Sync:ServerStrict; Persistence:Ephemeral; Feedback:Haptic; Motion:PhysicsBased; Pacing:UserDriven; Transition:Slide; A11y:WCAG_2.2_AA+ReducedMotion; }`
- **Description:** A deeply engaging, dark-themed layout relying entirely on full-screen media nodes and tactile swipe gestures for pagination.
- **Codegen descriptor:** **Lock `html/body` overflow.** Implement **CSS Scroll Snap** (`scroll-snap-type: y mandatory`) where each media container is exactly `100vh` with `object-fit: cover`. Use an **IntersectionObserver** to autoplay only the fully-in-view node and to **aggressively prefetch the next 3 nodes**. Swipe/physics-based pagination. Provide captions and reduced-motion alternatives (the a11y floor). Ephemeral by design — feed position is not persisted.

### D3 · Chronological Presence Hub
- **Exemplars:** [Discord](https://discord.com/) · [Slack](https://slack.com/) · [Microsoft Teams](https://www.microsoft.com/en-us/microsoft-teams/group-chat-software)
- **Category:** RTC — real-time multi-user communication
- **Signature:** `PresenceHub { Type:RTC; Arch:SPA; Layout:MasterDetail; Density:Compact; Nav:Sidebar; Viewport:DesktopBound; Input:KeyboardFirst+PrecisionPointer; Color:DarkAdaptive; Type:Utilitarian; Depth:Flat; Sync:Multiplayer; Persistence:Cloud; Feedback:Optimistic; Motion:Micro; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA; }`
- **Description:** A deeply nested hub for managing concurrent streams of synchronous multi-user chat alongside live presence indicators.
- **Codegen descriptor:** Wrap the app in **WebSocket listeners** for live messages and presence. **Virtualize the message list** to handle thousands of DOM nodes without crashing. **Isolate state updates for typing indicators** so they don't trigger broad re-renders. Optimistic send with reconcile. Nested channel/server sidebar navigation. Unread/mention/error states are first-class (U9).

---

## E. Authoring & marketing archetypes

### E1 · Distraction-Free Block Document
- **Exemplars:** [Notion](https://www.notion.so/) · [Craft](https://www.craft.do/) · [Obsidian](https://obsidian.md/)
- **Category:** Authoring / Prose
- **Signature:** `BlockDocument { Type:Authoring; Arch:SPA; Layout:BlockDocument; Density:Spacious; Nav:FloatingContext; Viewport:FluidResponsive; Input:KeyboardFirst; Color:Monochrome; Type:EditorialSerif; Depth:Flat; Sync:LocalFirst; Persistence:Cloud; Feedback:Optimistic; Motion:Micro; Pacing:Freeform; Transition:Crossfade; A11y:WCAG_2.2_AA; }`
- **Description:** An ultra-clean, whitespace-heavy document editor where traditional UI bars are hidden in favor of inline contextual popovers.
- **Codegen descriptor:** Treat the document as a **JSON array of blocks**. **Auto-focus empty block nodes** immediately. **Hide formatting toolbars until text is actively highlighted** (selection-driven inline popover). Implement a **`/` keydown listener** that spawns a command menu for block insertion. Local-first for **zero-latency typing**, background cloud sync. Generous whitespace (`Density:Spacious`). Crossfade between states. `StyleHints`: extreme whitespace, editorial type.

### E2 · Cinematic Scrollytelling
- **Exemplars:** [Apple Mac](https://www.apple.com/mac/) · [Stripe Connect](https://stripe.com/connect) · [Vercel Ship](https://vercel.com/ship)
- **Category:** Consumer / Marketing
- **Signature:** `Scrollytelling { Type:Marketing; Arch:MPA; Layout:CinematicHero; Density:Spacious; Nav:TopBar; Viewport:FluidResponsive; Input:PrecisionPointer+TouchPrimary; Color:DarkAdaptive; Type:Expressive; Depth:SoftShadow; Sync:Stateless; Persistence:Ephemeral; Feedback:Instant; Motion:ScrollDriven; Pacing:UserDriven; Transition:Crossfade; A11y:WCAG_2.2_AA+ReducedMotion; }`
- **Description:** A motion-heavy landing page where scrolling controls fluid animations and object reveals on a timeline.
- **Codegen descriptor:** Implement **scroll-linked animations** (scroll progress → `opacity`/`translateY`/WebGL transforms). **Pin sections** so the scroll wheel scrubs an animation timeline. Lazy-load high-fidelity assets; maintain the performance budget despite motion (U17). **Honor `prefers-reduced-motion`** with a static fallback (the a11y floor is not optional here). Glassmorphic nav over the hero. `StyleHints`: expressive type, dark-adaptive.

---

## F. Common gaps the source roster missed (added)

### F1 · Content Portal / Hub-and-Spoke
- **Exemplars:** [The New York Times](https://www.nytimes.com/) · [BBC](https://www.bbc.com/) · [Bloomberg](https://www.bloomberg.com/)
- **Category:** Portal / Editorial — high-volume content discovery
- **Signature:** `ContentPortal { Type:Portal; Arch:MPA; Layout:HolyGrail; Density:Comfortable; Nav:TopBar+Breadcrumb; Viewport:FluidResponsive; Input:PrecisionPointer+TouchPrimary; Color:BrandCentric; Type:EditorialSerif; Depth:Flat; Sync:Stateless; Persistence:Session; Feedback:Instant; Motion:Micro; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA+HighLegibility; }`
- **Description:** A dense editorial home that ranks and routes a high volume of content through clear hierarchy and section navigation.
- **Codegen descriptor:** Classic content hierarchy (lead story, section blocks, rails). Server-rendered for SEO/first paint (`Arch:MPA`, `Sync:Stateless`). Strong typographic hierarchy and scan patterns (F-pattern). Section nav + breadcrumb; infinite or paginated section feeds. Reading-optimized measure and legibility floor.

### F2 · Settings / Preferences Surface
- **Exemplars:** [GitHub Settings](https://github.com/settings/profile) · [Stripe Settings](https://dashboard.stripe.com/settings) · [Vercel Settings](https://vercel.com/dashboard)
- **Category:** OLTP — configuration with consequential, often irreversible actions
- **Signature:** `SettingsSurface { Type:OLTP; Arch:SPA; Layout:MasterDetail; Density:Comfortable; Nav:Sidebar+Breadcrumb; Viewport:FluidResponsive; Input:KeyboardFirst+PrecisionPointer; Color:BrandCentric; Type:Utilitarian; Depth:Flat; Sync:ServerStrict; Persistence:Cloud; Feedback:Confirmed+StrictValidation; Motion:Micro; Pacing:UserDriven; Transition:Crossfade; A11y:WCAG_2.2_AA; }`
- **Description:** A grouped settings surface where changes are explicit, validated, and consequential actions are gated behind confirmation.
- **Codegen descriptor:** Left nav of setting groups + detail pane. Each control reflects saved vs dirty state; saves confirm against the server (`Sync:ServerStrict`). **Destructive/irreversible actions** (delete, rotate keys, change permissions) require typed confirmation and clear consequence text — and per the pack's agent-safety rules these are exactly the actions an agent must surface, not auto-execute. Inline validation; success/error toasts. Composes with the threat model (these are privileged operations).

---

## G. Using a row (worked example)

To build the **Executive Coaching app** from the source bundle: start at **A1 (Phased Narrative Orchestrator)**, take its canonical signature, and specialize with `StyleHints` and any facet overrides:

```
ExecCoachPipeline {
  Type:GuidedJourney; Arch:StateMachine; Layout:ProgressiveOrchestrator;
  Density:Spacious; Nav:Stepper+ProgressPills; Viewport:FluidResponsive;
  Input:Multimodal; Color:BrandCentric; Type:EditorialSerif; Depth:SoftShadow;
  Sync:AsyncPipeline; Persistence:Cloud; Feedback:Choreographed;
  Motion:ScrollDriven+Micro; Pacing:UserDriven; Transition:Slide;
  A11y:WCAG_2.2_AA;
} [StyleHints: "corporate color palette", "warm background tones", "tropical data-viz accents"]
```

Then compose the concrete spec: define the **tokens** (the actual corporate palette, warm background, tropical chart accents — U3–U5), the **complete states** for each phase's components (U9), the **real copy** for the streamed orchestration lines and the results narrative (U11), the **user flows** including the failure path when the async/AI call errors (S6), and the **a11y + performance** floors (U16–U17). The signature made the archetype deterministic; the spec made it buildable. An agent in Claude Code or GitHub Copilot, given the signature + the codegen descriptor + the spec, builds the same three-phase orchestrator every time — not a generic dashboard.

---

## H. Provenance

Archetypes A1–A4, B1–B4, C1, D1–D3, E1–E2 originate from the externally-provided *Web Design Theme Taxonomy / UX Grammar v5.0* (Gemini-authored) — names and exemplars retained, signatures **hardened** (multi-valued facets, `A11y` floors, conflict resolution, the `LockedUntilValid` typo fixed) per `ui-archetype-grammar.md`. F1–F2 are pack additions covering common gaps (content portals, settings surfaces). Exemplar links are to live products as of authoring; verify on use. All signatures compose with `ui-interaction-design.md` (U1–U20) and `specification-standards.md` (S1–S18).
