# UI Visual Assets — the generative pipeline and its guardrails

*Normative guidance for **generating the imagery, personas and motion a UI contains** — the visual-world direction board that makes a brief concrete, the photographic assets a mockup renders, the consistent characters the review harness switches between, and the cinematic motion a marketing surface uses. The reference implementation is the **Higgsfield** MCP server (`platform.higgsfield.ai`); the directives are written so a different generation backend substitutes without rewriting the standard. `ui-design-craft.md` (DX1–DX25) governs the craft this serves; `ui-craft-detection.md` (CD1–CD19) governs the control that verifies the result; **this document governs what may be generated, how, and at what cost.***

Normative keywords (**MUST**, **SHOULD**, **MAY**, **MUST NOT**) follow RFC 2119.

The governing idea: **a direction brief is words, and words are where UI design goes generic.** `ui-design-craft.md` DX4 already says *anchor to named references, not adjectives* — "modern and clean" constrains nothing. Generation closes the last gap in that instruction: instead of an adjective, the build codes toward **a concrete image**. That is a genuine step change, and it is also the exact point at which three failure modes enter the pack at once — non-determinism leaking into a deterministic artifact, real money leaving the account per call, and personal data leaving the machine. So the capability is adopted *with* the guardrails, never before them.

And the single most important rule is a prohibition, stated first because it is the one people break: **never generate the interface itself.** Image models render fake, illegible text and hallucinated controls. A "dashboard screenshot" pasted into a mockup makes a design look finished while encoding nothing a developer can build, no state a reviewer can interrogate, and no token any linter can check. Generate what the UI **shows**, never the UI.

---

## 0. When this applies

Any UI work that needs **imagery, avatars, illustrative photography, product video, or a visual direction reference** — a landing or marketing surface, a mockup that must render realistic content (DX16), a review harness that switches persona (DX10), an onboarding or empty-state illustration, an OG/social card, a product turntable. It is triggered from `/ui-design` (Stage 1 direction, Stage 5 artifacts) and `/implement` (asset production). It is **not** triggered for a UI that ships no imagery, and it is never a prerequisite for good design — a superb interface with zero generated assets is a normal outcome.

**Owner:** the **UX & Accessibility** lens (visual direction, alt text, the WCAG floor) with the **AI Systems Engineer** (non-determinism containment, eval, inference cost — hard veto), the **Privacy & Data Governance** lens (egress, likeness, personal data — hard veto), and **The Simplifier** (does this asset earn its weight at all — soft veto).

---

## 1. What the backend is — established by execution

**VA1 — Establish the generation contract before depending on it.** The following were verified against the live MCP surface, not inferred (`no-guessing-protocol.md` NG1; `spike-protocol.md`):

| Capability | Surface | Notes | Confidence |
|---|---|---|---|
| Text → image | `generate_image` (Soul, `style_id`, `character_id`, 720p/1080p), `generate_image_reve`, `generate_image_seedream` (Seedream v4) | Soul returns `job_set_id`; the rest return `request_id` | **Verified** |
| Image → image | `edit_image_seedream` | transform/edit an existing image | **Verified** |
| Image → video | `generate_video` (DoP, `motion_id`, ~5s), `generate_video_dop_standard` (2–10s), `generate_video_kling`, `generate_video_seedance` | source image must be a **public HTTPS URL** | **Verified** |
| Image + audio → video | `generate_talking_head` (Speak v2) | audio **must be WAV**; 5/10/15s; 2–3 min processing | **Verified** |
| Consistent character | `create_character` (1–5 face images), `list/get/delete_character` | **40 credits ≈ $2.50** per character | **Verified** |
| Hosting | `upload_image` (base64 → public URL) | **egresses the image** — see VA9 | **Verified** |
| Polling | `get_generation_status` (job_set_id) · `get_request_status` (request_id) | statuses: `queued`, `in_progress`, `completed`, `failed`, **`nsfw`**, `cancelled` | **Verified** |
| Presets | `list_styles` (**106**), `list_motions` (**121**) | enumerated at adoption | **Verified** |
| **Retention** | **results retained 7 days** | the single most load-bearing operational fact — see VA4 | **Verified** |

**VA2 — Everything is asynchronous and some of it fails.** Generation returns an identifier, not an image. A pipeline **MUST** poll to a terminal state and **MUST** handle `failed` and `nsfw` as ordinary outcomes, not exceptions — `nsfw` is a real return value from a benign prompt and a build that treats it as a crash is a defect. `cancel_request` works on **queued** jobs only; an `in_progress` job cannot be cancelled and **will** be billed. Budget accordingly (VA10).

**VA3 — Know what the presets actually are, and don't reach past them.** The **style** catalogue skews heavily to fashion, lifestyle and social-selfie registers (`0.5 Selfie`, `Coquette core`, `Y2K`, `Nail Check`, `Tokyo Streetstyle`). The subset that is appropriate for a product or brand surface is small and worth naming: **`Realistic`, `General`, `Geominimal`, `Japandi`, `Quiet luxury`, `Gallery`, `Library`, `Movie`, `Artwork`, `Mixed Media`, `90's Editorial`, `Spotlight`, `Overexposed`**. The **motion** catalogue is genuinely professional cinematography — `Dolly In/Out`, `Crane Up/Down`, `Arc Left/Right`, `Jib Up/Down`, `Tilt`, `Whip Pan`, `Focus Change`, `Handheld`, `Static`, `Hyperlapse`, `Overhead`, `Push To Glass`, `Dutch Angle`, `Zoom`, and notably **`360 Orbit`/`Lazy Susan`, which are product-turntable shots** — mixed with VFX gimmicks (`Head Explosion`, `Tentacles`, `Set on Fire`) that have no place on a product surface. Pick from the professional subset and **name the preset in the asset manifest**; a preset chosen for novelty is the motion equivalent of a purposeless animation (DX19).

---

## 2. The hard prohibitions

**VA4 — Generate once, commit the artifact, reference the file. Never generate at render time.** Every generated asset **MUST** be downloaded, optimized, committed to the repository, and referenced by **relative path**. Three independent reasons, any one of which is sufficient:
- **Non-determinism must not leak into a deterministic path.** A mockup or build whose imagery re-rolls per run is not reproducible and cannot be reviewed — the AI Systems Engineer's hard veto applies (`persona-audit.md` §8.4).
- **Retention is 7 days (Verified).** A mockup pointing at a provider CDN URL is a wall of broken images in eight days — and `broken-image` is one of the detector's own rules (CD6). This is not a doctrinal preference; it is an expiry date.
- **Cost.** Re-generating on every render bills every render.

**VA5 — Never generate the interface.** No generated screenshot, mockup image, UI panel, chart, table, icon set, or any asset whose content is **text a user must read** or **a control a user must operate**. Image models produce malformed glyphs and invented affordances; embedding one in a design artifact creates the appearance of a finished decision where no decision exists. The pack's mockups are **hand-authored, dependency-free HTML** (DX8) precisely so every element is real, inspectable and token-checkable. Generate the photograph *inside* the card; never generate the card.

**VA6 — Generated imagery informs mood, never structure.** Direction boards (§3) may set atmosphere, palette temperature, material, era and emotional register. They **MUST NOT** determine the archetype, the information architecture, the navigation model or the layout — those come from the **Archetype Signature** (`ui-archetype-grammar.md`) and the UX layer (`specification-standards.md` S6), which are settled *before* any visual artifact exists (DX1, S2). A moodboard that starts dictating structure has inverted the fidelity ladder (DX7).

**VA7 — A generated reference does not replace a real named reference.** DX4 requires anchoring to concrete, known-good products and saying what specifically is taken from each. A generated image is **evidence of nothing** — no product shipped it, no user used it, and it is drawn from the same statistical mean that produces the generic AI look the whole craft doctrine exists to defeat (DX3). Generated boards **supplement** named references; they never substitute for them, and a direction brief whose only anchors are generated images fails DX4.

**VA8 — The generic tells apply to imagery too.** Generated visuals have their own recognizable mean: over-lit teal-and-orange grading, impossible bokeh, glossy plastic skin, symmetrical hero compositions, "diverse team laughing at a laptop" stock-mimicry, and objects with subtly wrong geometry. Self-check the output against the brief's **anti-goals** (DX5) and reject the average. If the generated asset looks like every other AI image, it is doing the same damage to the surface that a violet gradient does — for the same reason.

---

## 3. Privacy, likeness, disclosure and licence

**VA9 — Never send real people's images or customer data to the generator. Hard line.** `upload_image` and the character tools **egress image data to a third party**. Uploading a real user's, employee's or customer's photograph — to build a "realistic" persona, to test an avatar, or for any convenience — is a **Privacy & Data Governance hard veto** and, in most jurisdictions, a likeness and biometric-data problem as well (`responsible-ai-policy.md`; `engineering-governance.md` §4). Personas are **fictional by construction**. Screenshots or exports containing real records are equally out of scope: they are personal data, and pasting one into a generation prompt is an egress decision nobody reviewed.

**VA10 — Cost is metered and therefore budgeted.** Generation spends credits — real money, per call, with a character reference alone at **40 credits ≈ $2.50** (Verified) and an un-cancellable in-progress job billed regardless. Treat it exactly as the pack treats inference cost (`ai-commercial-models.md` AC3, the Token Budget Throttle; AC2, the Receipt Ledger): state an **asset budget per surface** before generating, record what each asset cost in the manifest (VA12), and prefer regenerating **one** asset with a better prompt over sampling ten and picking. Batch exploration is where budgets die.

**VA11 — Disclose, attribute, and check the terms.** Generated assets are disclosed as AI-generated wherever a reasonable user would otherwise assume a photograph of a real person, place or product (`ui-interaction-design.md` U13–U14, the Shape-of-AI *Trust builders*; `responsible-ai-policy.md`). The commercial-use terms of the generation provider and each underlying model **MUST** be established before an asset ships to a customer-facing surface — provider terms change, so this is a **check, not a recollection** (NG3). A generated asset depicting a recognizable real person, trademark or brand does not ship.

---

## 4. The artifacts

**VA12 — Every generated asset carries a manifest entry.** Assets live under `docs/assets/<surface>/` and are recorded in the project's design language (`DESIGN.md`, U3a) under an `assets:` section, one entry each:

```yaml
assets:
  - id: hero-workspace
    file: docs/assets/onboarding/hero-workspace.webp
    purpose: "Landing hero — the calm-focused-workspace register from the direction brief"
    generator: "higgsfield/seedream-v4"          # backend + model
    preset: "Quiet luxury"                        # style_id name, or motion name for video
    prompt: "<the exact prompt, verbatim>"
    generated: 2026-08-05
    cost_credits: 8
    alt: "A quiet desk at dawn, one notebook open, low warm light"   # VA13 — mandatory
    disclosure: ai-generated
    licence-checked: true
```

The manifest is what makes a generated asset **reproducible, auditable, and reviewable**: without the verbatim prompt and preset, nobody can regenerate a consistent sibling, and without cost and date nobody can see the spend or the staleness. It is the Receipt Ledger (`layered-optimized-architecture.md` 4.3) at asset granularity.

**VA13 — Alt text is written when the asset is generated, not later.** Every image gets alt text authored at manifest time — descriptive for informative imagery, `alt=""` for genuinely decorative imagery, and never the prompt reused as alt text (a prompt describes what you asked for; alt text describes what a non-sighted user needs). This is **U16**, and a generated image without alt text is an accessibility Blocker, not a to-do.

**VA14 — Assets meet the performance budget.** Generated output is 720p/1080p raster and is heavy. Before commit: convert to a modern format (WebP/AVIF), size to the largest rendered dimension, provide responsive sources, set explicit `width`/`height` to prevent layout shift, and lazy-load below the fold. **U17** is a floor, and "it's a nice hero image" does not buy an exemption — an unoptimized hero is the most common single cause of a blown budget.

---

## 5. Where it plugs into the loop

**VA15 — The visual world comes *after* the words, and *before* the system.** In `/ui-design`, the order is fixed (DX1, DX7): the **direction brief in words** (DX5 — user, JTBD, archetype, three adjectives *and their opposites*, named references, anti-goals) → **then, optionally, a visual-world board** of 2–4 generated candidates that make the brief's register concrete → the chosen board is recorded in `DESIGN.md` with its prompt and preset → **then** the design language → **then** the screens. Generating before the brief exists is DX1's exact failure: deciding direction, system and composition in one averaged pass.

**VA16 — Consistent personas are the highest-value use, and they are test data.** A **character reference** gives the same face across every state, viewport and theme in the review harness (DX10) — which turns the harness's persona switcher from a label into a visibly different user, and supplies the *realistic extreme content* DX16 demands (the long name, the missing avatar, the user with no photo). Personas are fictional (VA9), named in the manifest, and treated as **fixtures**: they belong to the mockup and the design system, never to production data.

**VA17 — Motion is for marketing surfaces and product demonstration, and it obeys the motion inventory.** Image→video is appropriate for a scrollytelling or cinematic-hero archetype (`ui-archetype-catalog.md` E2), a product turntable (`360 Orbit`/`Lazy Susan`), or an onboarding walkthrough. It is **not** appropriate as decoration inside an application surface. Every generated clip is an entry in the **motion inventory** (DX19) with its purpose, duration and easing; it **MUST** honour `prefers-reduced-motion` with a static poster fallback (U10), carry captions or a text alternative where it conveys information (U16), and count against the performance budget (U17, VA14).

**VA18 — What is generated is then verified.** Generated assets enter the same control as everything else: the detector's `broken-image`, `image-hover-transform`, `text-occlusion`, `low-contrast` and `shape-assembled-illustration` rules run over the surface that renders them (`ui-craft-detection.md` CD8). Text placed **over** a generated image is the classic contrast failure — the background is photographic and variable, so the contrast floor is checked against the actual composite, not against the intended overlay colour.

---

## 6. Self-verification checklist

- [ ] The generation contract was **established by execution** (models, statuses, presets, retention), not recalled (VA1–VA2).
- [ ] The chosen **style/motion presets** come from the product-appropriate subset and are named in the manifest (VA3).
- [ ] Every asset is **generated once, downloaded, optimized, committed, referenced by relative path** — no provider CDN URL in a committed artifact (VA4).
- [ ] **No generated interface** — no screenshot, panel, chart, icon set, or asset containing readable UI text or operable controls (VA5).
- [ ] Generated imagery informed **mood only**; archetype, IA and layout came from the grammar and the UX layer (VA6).
- [ ] **Real named references** are present in the direction brief; generated boards supplement rather than substitute (VA7).
- [ ] Output was self-checked against the **imagery tells** and the brief's anti-goals (VA8).
- [ ] **No real person's image or customer data** was uploaded; personas are fictional (VA9).
- [ ] An **asset budget** was set, and per-asset cost recorded (VA10).
- [ ] **Disclosure** applied and **commercial-use terms checked** at time of use (VA11).
- [ ] Every asset has a **manifest entry** with verbatim prompt, generator, preset, date, cost (VA12).
- [ ] Every image has **alt text written at generation time**; decorative images use `alt=""` (VA13).
- [ ] Assets meet the **performance budget** — modern format, sized, dimensioned, lazy-loaded (VA14).
- [ ] The **order held**: words → visual world → design language → screens (VA15).
- [ ] Personas are **fixtures**, used in the harness, never production data (VA16).
- [ ] Motion is in the **motion inventory**, has a reduced-motion fallback and a text alternative (VA17).
- [ ] The rendering surface passed the **detector**, including contrast of text over imagery (VA18).

---

## 7. References

- **Higgsfield** — `platform.higgsfield.ai`, exposed as an MCP server. Models: Soul, Reve, Seedream v4 (+edit), DoP / DoP Standard, Kling v2.1 Pro, Seedance v1 Pro, Speak v2. Surface, presets (106 styles / 121 motions), statuses and the **7-day retention** verified by execution at adoption; re-establish on upgrade.
- **`ui-design-craft.md`** — **DX1** direction before pixels, **DX4** named references, **DX5** the direction brief, **DX7** the fidelity ladder, **DX8–DX10** the mockup and harness, **DX16** realistic extreme content, **DX19** the motion inventory, **DX3** the tells (whose imagery analogue is VA8).
- **`ui-craft-detection.md`** — the verification half of the same loop (CD8, CD14); `broken-image` is why VA4 exists in two directions.
- **`ui-interaction-design.md`** — **U11** no generic stock, **U13–U14** disclosure and Trust builders, **U16** alt text and the accessibility floor, **U17** the performance budget; **U3a** the `DESIGN.md` the manifest lives in.
- **`ai-commercial-models.md`** — AC2 the Receipt Ledger and AC3 the Token Budget Throttle, applied to asset spend (VA10, VA12).
- **`responsible-ai-policy.md`** + **`engineering-governance.md`** §4 — disclosure, likeness, and the personal-data egress line (VA9, VA11).
- **`no-guessing-protocol.md`** / **`spike-protocol.md`** — why VA1 is executed rather than assumed, and why provider terms are re-checked rather than recalled.
