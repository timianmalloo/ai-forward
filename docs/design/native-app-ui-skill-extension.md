---
id: design-native-app-ui-skill-extension
title: "Native app UI skill extension — Design"
type: design
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [ui-design, visualize, native-ui, wpf, winui, avalonia, blazor-hybrid, xaml-token-lint, templates]
links:
  - { to: spec-native-app-ui-skill-extension, rel: implements }
  - { to: kb-native-client-ui-design, rel: depends-on }
  - { to: kb-native-client-ui-design-data, rel: depends-on }
  - { to: kb-native-client-ui-design-comparables, rel: depends-on }
review-by: "2027-02-21"
summary: >-
  Detailed design for making native client applications first-class in the AI-Forward UI skills. The design updates /ui-design and /visualize, adds a reusable native UI proof-pack template, adds native desktop archetype rows, and introduces a deterministic XAML token linter while keeping web UI and generated-asset guardrails intact.
---

# Design: Native app UI skill extension

- **Status:** Accepted
- **Spec / architecture:** `docs/specs/native-app-ui-skill-extension.md` · `docs/architecture.md`
- **Delivery phase / vertical slice:** Pack UI workflow extension. This slice designs the pack edits; implementation will modify `pack/` sources, run `tools/sync-pack.ps1`, and commit generated `.claude/`, `.github/`, and `docs/` surfaces together.
- **Author(s) / date:** Copilot CLI / 2026-08-26

## Responsibility

This design makes native client UI review a first-class branch of the existing UI workflows. It does **not** create a separate "native UI skill"; it extends `/ui-design` and `/visualize` with native medium declarations, native proof rows, XAML/resource token checks, native desktop archetypes, and license-labeled exemplars.

It is not responsible for implementing a WPF/WinUI/Avalonia application, choosing every downstream UI automation framework, or generating native UI screens. Those remain per-project design/implementation decisions.

## Contracts

### Exposed contracts

| Contract | Shape | Guarantees |
|---|---|---|
| `/ui-design` native trigger | New row `UI-T4 native client` plus expanded behavior in Stage 1/3/4/5. | A native run declares medium/platform/framework/distribution/accessibility API; applies Native Desktop lens; produces a native proof pack; never treats an HTML mockup or static craft detector as native PASS. First slice is Windows/XAML (`WPF`, `WinUI`, `Avalonia`) plus `Blazor Hybrid` shell handling. |
| `/visualize` native clarification | Wording in input/modes/gates. | Generated assets may serve native apps as content fixtures, persona fixtures, onboarding/marketing imagery, or direction boards; generated assets are never native screens/windows/controls/charts/icon sets. |
| Native proof-pack template | New `pack/templates/native-ui-proof-pack.template.md`. | Reusable checklist with `claim`, `failing input or condition`, `oracle`, `evidence`, `red observed`, `confidence`, and `residual risk`; includes Windows/WPF/WinUI/Avalonia/Blazor Hybrid rows. |
| XAML token linter | New `pack/scripts/xaml-token-lint.py`. | Deterministic stdlib check for raw colors, raw brushes, raw dimensions and static theme-sensitive references in `.xaml` / `.axaml`; emits machine-readable findings and non-zero exit on findings. |
| Native archetype catalog rows | Three full rows in `pack/knowledge/ui-archetype-catalog.md`, each with parseable signature and codegen descriptor. | Gives `/specify` and `/ui-design` a native determinism selector instead of reusing web dashboard rows for WPF/WinUI/Avalonia surfaces. |
| Exemplar table | Small table added to UI docs. | Names permissive reference repos and flags GPL/non-standard repos as reference-only, preventing unsafe reuse. |

### Consumed contracts

| Contract | Source | Confidence |
|---|---|---|
| Native proof rows and failure modes | `docs/knowledge/native-client-ui-design/data-and-constants.md` | **Verified/Inferred as labeled** |
| Native evidence and licensing | `docs/knowledge/native-client-ui-design/index.md`, `comparables.md`, `sources.md` | **Verified/Inferred/Flagged as labeled** |
| Existing UI workflow contract | `pack/commands/ui-design/SKILL.md`, `pack/commands/visualize/SKILL.md` | **Verified — opened in this design run** |
| Pack deployment contract | `tools/sync-pack.ps1`, `pack/adapters/INSTALL.md` | **Verified in prior grounding; implementation must update source and generated surfaces together** |
| User decisions for this design | Prompt: WPF/WinUI/Blazor supported; XAML token linting allowed; native archetype rows required; proof pack in skill text and reusable template; exemplar table added to UI docs | **Verified — user input** |

## Patterns

| Pattern / idiom | Applied where | Why this is the smallest correct choice |
|---|---|---|
| **Extension over new skill** | `/ui-design`, `/visualize` | Reuses existing UI doctrine and avoids a parallel native workflow. A new skill would duplicate cast, stages and audit/discoverability mechanics. |
| **Trigger table union** | `/ui-design` triggered standards | Existing pattern already governs expert UI, generated assets and AI surfaces; native becomes another orthogonal trigger. |
| **Proof Pack** | Native proof template and review output | Matches existing Test Architect evidence shape and keeps "native proof" testable instead of prose. |
| **Deterministic Verifier / Adapter** | `xaml-token-lint.py` | Mirrors `design-lint.py` / `ui-craft-gate.py`: mechanize the XAML subset that can be checked without a model, with the same JSON-finding idiom. |
| **Proof Pack Template / Single Source of Truth** | Native proof-pack template | Keeps repeated native proof rows in one reusable artifact instead of copying a table into every skill run. |
| **Catalog row extension** | UI archetype catalog | Adds native archetypes under the existing grammar/catalog rather than inventing a new grammar. |

**Rejected patterns:**

- **Separate `/native-ui-design` skill** — rejected as duplicated ceremony. Existing `/ui-design` already owns interface craft; the native gap is proof surface, not workflow identity.
- **Use only `ui-craft-gate.py` for native** — rejected because static HTML/source rules cannot prove accessibility tree, DPI, OS integration or signing.
- **Build a universal native automation runner now** — rejected as over-scoped. The design adds a proof-pack contract and a XAML linter; exact UIA/Appium/FlaUI choices remain flagged per project/tooling design.

## Data shapes

No persistent product data is introduced.

### Native medium declaration

```yaml
native:
  medium: native-desktop              # native-desktop | blazor-hybrid | other
  platform: windows                   # windows | cross-platform | other
  framework: wpf                      # wpf | winui | avalonia | blazor-hybrid | other
  distribution: msix                  # msix | exe | store | other
  accessibility_api: ui-automation    # ui-automation | browser-dom+native-shell | other
  hig_source: "<official URL or native knowledge source id>"
```

`other` is allowed only with `hig_source` and a Flagged residual-risk note until `/design` adds a concrete proof row for that platform.

### Native proof row

```yaml
- claim: "Keyboard traversal works"
  failing_condition: "User cannot complete the core flow without pointer input, including dialogs and recovery states"
  oracle: "Recorded traversal or automated test shows order, focus trap/restore, default/cancel actions, shortcut map"
  evidence: "<tool output / test name / recording path>"
  red_observed: "planned | observed-failing | observed-passing-after-fix"
  confidence: "Verified | Inferred | Flagged"
  residual_risk: "<uncovered platform/path>"
```

### XAML linter finding

```json
{
  "file": "src/App/MainWindow.xaml",
  "line": 42,
  "rule": "xaml-raw-color",
  "severity": "major",
  "message": "Raw color '#FF0067B8' should reference a design token resource.",
  "attribute": "Background"
}
```

## Designed source changes

| Source file | Change |
|---|---|
| `pack/commands/ui-design/SKILL.md` | Expand UI-T4 from a one-line native trigger into a native-client trigger with medium declaration, first-slice WPF/WinUI/Avalonia, Blazor Hybrid handling, platform HIG, native proof pack, native token/resource mapping, and `/visualize` handoff rules. |
| `pack/commands/visualize/SKILL.md` | Add native-app asset mode language: native direction boards/personas/content imagery/motion are allowed; generated screens/windows/control panels/charts/icon sets are rejected as generated interface. |
| `pack/knowledge/ui-design-craft.md` | Add a native proof-pack subsection that explains why HTML mockups are direction evidence only for native apps and why runtime proof is required. |
| `pack/knowledge/ui-visual-assets.md` | Add native client note: generated assets can populate native review harnesses and onboarding/marketing surfaces, but may not replace native XAML/WinUI/WPF controls or app icons. |
| `pack/knowledge/ui-archetype-catalog.md` | Add native archetype rows. See "Native archetype rows" below. |
| `pack/templates/native-ui-proof-pack.template.md` | New reusable proof-pack/checklist artifact. |
| `pack/scripts/xaml-token-lint.py` | New deterministic linter for `.xaml` and `.axaml` token discipline. |
| `pack/adapters/INSTALL.md` | Bump revision; update counts (`templates +1`, `scripts +1`); list changed paths and deployment instructions. |

Implementation must then run `tools/sync-pack.ps1`, which deploys templates/scripts to `docs/ai-forward-pack/` and wraps knowledge/skills into `.claude/` and `.github/`.

## Native archetype rows

Add a new section to `ui-archetype-catalog.md` after the technical/scientific section or as a sibling section. Each row follows the catalog contract: exemplar anchors, canonical parseable signature, description, and codegen descriptor.

### N1 · Windows Fluent Utility Shell

- **Exemplars:** Microsoft PowerToys · WPF UI · WinUI Gallery
- **Category:** NativeDesktop / Windows utility and settings surfaces
- **Signature:** `WindowsFluentUtility { Type:OLTP; Arch:SPA; Layout:MasterDetail; Density:Compact; Nav:Sidebar+CommandPalette; Viewport:DesktopBound; Input:KeyboardFirst+PrecisionPointer; Color:DarkAdaptive; Type:Utilitarian; Depth:Flat; Sync:LocalFirst; Persistence:Session; Feedback:Confirmed; Motion:Micro; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA+HighLegibility; x-platform:windows; x-framework:"winui-or-wpf"; }`
- **Description:** A compact Windows utility/settings shell that feels native to Fluent/Windows, optimized for keyboard-first configuration and operational throughput.
- **Codegen descriptor:** Use native Windows/Fluent controls and resources; left navigation/settings shell; keyboard accelerators and command search; UI Automation names/roles; Light/Dark/HighContrast resources; Windows signing/SmartScreen proof; no HTML mockup can clear native PASS.

### N2 · Native File/Object Workbench

- **Exemplars:** Files · Windows Explorer conventions · WPF-Samples
- **Category:** NativeDesktop / file-object management
- **Signature:** `NativeFileWorkbench { Type:OLTP; Arch:SPA; Layout:MasterDetail; Density:Compact; Nav:Breadcrumb+Sidebar+CommandPalette; Viewport:DesktopBound; Input:KeyboardFirst+PrecisionPointer; Color:DarkAdaptive; Type:Utilitarian; Depth:Flat; Sync:LocalFirst; Persistence:Cloud; Feedback:Confirmed+Instant; Motion:Micro; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA+HighLegibility; x-platform:windows; x-framework:"winui-or-wpf"; }`
- **Description:** A native file/object management workbench with panes, breadcrumbs, selection, context commands, drag/drop and high-volume list behavior.
- **Codegen descriptor:** Multi-pane navigation, path/breadcrumb, tabs optional, drag/drop, file associations, context menus, virtualization for large item sets, keyboard selection/open/rename/delete flows, UIA tree proof, DPI/windowing proof, distribution proof.

### N3 · Cross-Platform XAML / Blazor Hybrid Workbench

- **Exemplars:** Avalonia · WindowsAppSDK-Samples · Blazor Hybrid shell pattern
- **Category:** NativeDesktop / cross-platform shell
- **Signature:** `CrossPlatformXamlWorkbench { Type:Hybrid; Arch:SPA; Layout:MasterDetail; Density:Comfortable; Nav:Sidebar+CommandPalette; Viewport:DesktopBound; Input:KeyboardFirst+PrecisionPointer; Color:BrandCentric; Type:Utilitarian; Depth:Flat; Sync:LocalFirst; Persistence:Cloud; Feedback:Confirmed; Motion:Micro; Pacing:Freeform; Transition:HardCut; A11y:WCAG_2.2_AA; x-platform:"cross-platform"; x-framework:"avalonia-or-blazor-hybrid"; }`
- **Description:** A cross-platform XAML or Blazor Hybrid native shell that shares product structure while requiring per-platform proof for accessibility, windowing, resources and distribution.
- **Codegen descriptor:** Declare platform deltas; map tokens through Avalonia theme variants or native shell resources; prove accessibility per platform through UIA/NSAccessibility/AT-SPI or browser DOM + native shell; for Blazor Hybrid prove native shell windowing/packaging plus WebView focus/zoom/high-contrast handoff.

Do not add macOS/GNOME/KDE-specific rows until a concrete surface requires them; `other`/declared-platform deviations must carry a HIG source and proof source.

## XAML token linter design

### Scope

First implementation is a deterministic text/XML scanner for:

- `.xaml`, `.axaml`, `.xaml.cs` only for obvious inline XAML strings if cheap; default target is markup files.
- WPF, WinUI/UWP XAML, Avalonia XAML.
- Blazor Hybrid: native shell `.xaml` is checked here; `.razor`, `.css` and rendered DOM stay with existing web UI craft tooling.

### Rules

| Rule | Detects | Severity |
|---|---|---|
| `xaml-raw-color` | `#RGB`, `#RRGGBB`, `#AARRGGBB`, named colors in visual properties outside allowed system/theme resources | Major |
| `xaml-raw-brush` | Inline `SolidColorBrush Color="..."` not bound to a token/system resource | Major |
| `xaml-raw-dimension` | `Margin`, `Padding`, `CornerRadius`, `Width`, `Height`, `FontSize` literal values not in allowlist/token map | Minor/Major depending property |

Allowed first-slice token/resource forms:

| Framework | Allowed forms |
|---|---|
| WPF | `{StaticResource ...}` or `{DynamicResource ...}` for token/resource references; system color/brush resources where appropriate. |
| WinUI/UWP | `{ThemeResource ...}` for theme-sensitive brushes/colors; `{StaticResource ...}` only for values that do not need runtime theme changes. |
| Avalonia | `{DynamicResource ...}`, theme-variant resources, or style/control-theme resources; literal values allowed only in token definition files, not in component markup. |
| Blazor Hybrid | Native shell `.xaml` follows WPF/WinUI/Avalonia rules; `.razor`/CSS follows existing web token/craft tooling. |

### Inputs and config

- Optional `--format json|text`.
- Optional `--path` repeated or directory argument.

### Exit codes

- `0`: no findings.
- `1`: findings.
- `2`: invalid arguments/unreadable file.

Deferred until fixtures prove need: semantic inference that decides whether a specific WPF `StaticResource` should have been `DynamicResource`, automation-name rules, suppressions, `.xaml.cs` scanning, and `--design` token-value comparison. Those are not first-slice requirements.

### Non-goals

- Full XAML semantic compiler.
- WCAG contrast computation from every XAML state.
- Runtime UI Automation proof.

## Native proof-pack template

Add `pack/templates/native-ui-proof-pack.template.md` with frontmatter `type: proof-pack` or `type: doc` depending whether it is used as proof artifact. Recommended: `type: proof-pack`, because this is evidence, not mere notes.

Sections:

1. Medium declaration.
2. Platform/HIG checklist.
3. Required proof rows table using the schema above.
4. Framework-specific rows:
   - WPF/WinUI: UIA, keyboard accelerators/access keys, theme/high contrast, DPI/windowing, virtualization, signing/SmartScreen.
   - Avalonia: AutomationProperties/AutomationId, focus/KeyboardNavigation, theme variants, Appium/headless split, per-platform accessibility, distribution signing/notarization/SmartScreen where the target platform requires it.
   - Blazor Hybrid: browser DOM accessibility + native shell proof (windowing, packaging/signing, permissions, WebView sizing, DPI), native↔WebView focus handoff, accelerator conflicts, zoom/text scaling and high contrast across both layers.
5. Exemplar/license references used.
6. Gate verdict and residual risk.

The template is referenced from `/ui-design` and `/design` test plans.

## Exemplar table in UI docs

Add a small, license-labeled table to `pack/knowledge/ui-design-craft.md` or `pack/knowledge/ui-interaction-design.md`. Best placement: `ui-design-craft.md` near DX4 "Anchor to named references" because exemplars are reference anchors, not normative platform standards.

Table rows:

- `microsoft/WinUI-Gallery` — MIT — control/style samples.
- `microsoft/PowerToys` — MIT — Windows utility/settings shell.
- `files-community/Files` — MIT — file manager workbench.
- `lepoco/wpfui` — MIT — WPF Fluent controls.
- `MaterialDesignInXAML/MaterialDesignInXamlToolkit` — MIT — WPF Material theming.
- `AvaloniaUI/Avalonia` — MIT — cross-platform XAML patterns.
- `microsoft/WPF-Samples` — MIT — WPF DPI/control samples.
- `File-New-Project/EarTrumpet` — Flagged/non-standard — reference-only.
- `rocksdanister/lively` — GPL-3.0 — reference-only.

Instruction: "Borrow patterns and cite license posture; do not clone brand, screenshots, icons, or product identity."

## Error & concurrency model

This design mostly changes deterministic markdown/scripts. Error model:

| Error | Handling |
|---|---|
| Native platform not declared | `/ui-design` blocks preflight; output asks for or records medium/platform/framework/distribution/accessibility API. |
| Native proof tool unavailable | Proof row is Flagged with next probe; no Verified native PASS from web evidence. |
| XAML linter cannot read a file | Exit `2`; surface error in test plan; do not convert to clean findings. |
| XAML linter finds unsupported framework syntax | Emit `xaml-unsupported-syntax` Flagged finding only when it affects proof; do not fail unknown syntax by default. |
| `/visualize` request asks for generated native UI | Reject and route to `/ui-design` or native implementation; do not generate. |

Concurrency:

- No runtime concurrency introduced.
- `xaml-token-lint.py` can scan files sequentially in first implementation; parallel scan is not needed.
- Docs/audit writes remain through existing scripts.

## Failure-mode analysis

| Failure mode | From which choice | Disposition | How addressed | Detection | Test |
|---|---|---|---|---|---|
| Web-shaped native review passes | Extending existing web-centered `/ui-design` | prevent | Native trigger and proof-pack required before native PASS | Native proof row count in review/template | Check docs mention native proof pack and template exists |
| Screenshot accepted as accessibility proof | Existing mockup/craft gate culture | prevent | Template requires accessibility tree evidence for accessibility claims | Proof row schema | Template golden text includes "screenshot alone is insufficient" |
| Generated native screen used as UI | `/visualize` supports images | prevent | Skill rejects screens/windows/control panels/charts/icon sets | `/visualize` text and tests/docs grep | Prompt fixture contains "generate WPF screen" expectation to reject |
| Token docs exist but XAML uses raw values | Token system not native-enforced | detect | XAML token linter flags raw colors/dimensions/resources | Linter findings | Red/green linter fixtures |
| Native proof rows copied inconsistently | Skill text only | prevent | Reusable proof-pack template is source for rows | Template frontmatter and skill link | docs-graph validates template deployed |
| GPL/non-standard repo reused as code | Exemplar list includes attractive projects | prevent/detect | Exemplar table includes license posture and reuse restriction | Table review | Test/grep rows include GPL/reference-only |
| macOS/GNOME/KDE under-specified | First slice mostly Windows/XAML | accept with guard | Treat as declared-platform extensions; require HIG/proof source when declared | Flagged risk in design/spec | Reviewer checks exact wording |
| Linter becomes too broad and noisy | Adding deterministic check | mitigate | Limit first implementation to obvious raw color/brush/dimension token patterns; defer automation and suppression rules until fixtures prove need | Exit codes and fixture tests | Linter clean/finding/error fixtures |

## Adversarial analysis (STRIDE-lite)

| Trust boundary | STRIDE threat | Disposition | Control / rationale | Negative test |
|---|---|---|---|---|
| Generated assets from user input to provider | I: customer screenshots/real likeness leak to provider | mitigate | `/visualize` keeps existing VA9 hard line and adds native-app examples | Prompt fixture with customer screenshot request is blocked |
| Public exemplar table to downstream users | T/I: license posture misrepresented | mitigate | Table includes license/reuse posture; GPL/non-standard reference-only | Static test/grep for `GPL-3.0` and `reference-only`; `NOASSERTION` flagged |
| Native proof template to review gate | R: reviewer claims proof without evidence | mitigate | Schema requires evidence, red-observed status and confidence | Template fixture lacks evidence -> docs/test failure |
| Native distribution trust | S/T/R/E: spoofed publisher, tampered artifact, unsigned update, unverifiable release provenance, SmartScreen/Gatekeeper/notarization bypass | mitigate | Signed artifacts, cert/key custody outside repo, timestamping where applicable, Store/MSIX/AuthentiCode/SmartScreen posture or macOS notarization recheck before release PASS | Unsigned/unnotarized fixture/check cannot clear release proof row |
| XAML linter input | T/I/D: hostile PR XAML/path causes parser abuse, path escape, terminal/log injection, or secret-like source disclosure | mitigate | Repo-root path normalization, no network/includes, text/XML scanning only, escaped JSON/text output, no raw source snippets or secret expansion | Malicious path/XAML fixture returns controlled error/finding without reading outside root or echoing unsafe content |

## Privacy analysis (LINDDUN-lite)

This design touches no personal data directly. It changes pack documentation and planned scripts. Privacy risk arises only when `/visualize` receives user/customer imagery or screenshots; this design preserves VA9 and adds native examples to make that hard line explicit.

## UI & interaction design

This design has no new end-user app interface. It modifies skill documentation, templates and a deterministic command-line linter. For developer-facing artifacts:

- **Medium:** markdown + CLI output.
- **Guideline:** repo communication/task discipline plus table-first summaries.
- **Accessibility:** templates and tables are markdown-readable; no visual UI introduced.
- **Performance:** linter should run fast enough for commit cadence on typical XAML trees; first implementation should avoid full semantic XAML compilation.

## Telemetry

No runtime telemetry is introduced. Script observability:

| Signal | Shape |
|---|---|
| `xaml-token-lint.py` stdout | Human-readable findings unless `--format json`. |
| JSON output | Array of `{file,line,rule,severity,message,attribute}`. Raw source snippets are not emitted by default so CI logs do not disclose secrets from repository content. |
| Exit code | `0` clean, `1` findings, `2` invocation/read error. |
| Audit | `/design` and later `/implement` runs use existing `audit-log.py`; no new logging path. |

## Test plan

Testing Strategy triggers. D0 test hygiene applies to every test unconditionally.

| Trigger | Applies? | Directives |
|---|---|---|
| T1 | Yes, deterministic linting/string contracts | D1 unit tests for raw color/brush/dimension detection. |
| T2 | Yes, scanner/parser over wide XAML input | D2 property/adversarial fixture tests for malformed XML, long files, comments, nested resources, escaped strings and allowed system resources. |
| T3 | Yes, new script/template/docs graph surfaces | D3 architecture/docs validation for deployment map and index. |
| T7 | Yes, JSON linter output schema | D6 schema/golden payload tests for findings and clean/error cases. |
| T14 | Yes, skill/knowledge/template markdown changes | A6 prompt/skill regression gate with golden scenarios and old/new behavior deltas. |

Concrete tests/checks for `/implement`:

1. `xaml-token-lint.py` clean fixture returns `0`.
2. Raw color/brush fixture returns `1` with `xaml-raw-color` / `xaml-raw-brush`.
3. Raw dimension fixture returns expected rule.
4. Malformed XML, very long attribute, comments, escaped strings and nested resource dictionaries do not crash or read outside the repo root.
5. Invalid file/path returns `2`.
6. JSON schema/golden tests cover clean, findings and invocation-error output, and assert raw source snippets/secrets are not echoed.
7. Template/frontmatter validates with `docs-graph.py validate`.
8. Proof-pack template schema test fails if required columns disappear: `claim`, `failing input or condition`, `oracle`, `evidence`, `red observed`, `confidence`, `residual risk`.
9. Native proof-pack golden rows fail if Windows/WPF/WinUI/Avalonia/Blazor Hybrid rows omit signing, windowing, DPI, keyboard or accessibility claims.
10. `/ui-design` A6 golden scenarios:
    - native WPF surface with missing platform declaration -> preflight block;
    - native WPF surface with only screenshot evidence -> no native PASS;
    - WPF/WinUI/Avalonia surface -> proof-pack template referenced;
    - Blazor Hybrid surface -> both DOM/web proof and native shell proof required;
    - ordinary web surface -> unchanged existing web behavior.
11. `/visualize` A6 golden scenarios:
    - "generate WPF settings window screenshot" -> rejected as generated interface;
    - "generate fictional persona portrait for native review harness" -> allowed under VA guardrails;
    - "use customer screenshot as source image" -> blocked by privacy/egress rule;
    - ordinary web hero image request -> unchanged existing behavior.
12. Exemplar policy tests parse the table and fail if `GPL-3.0` or `NOASSERTION` rows are not marked `reference-only` / `Flagged`.
13. Existing pack evals for changed skills, if present, run affected cases.

## Design proof pack

| Claim | Evidence | Oracle / failing condition | Red observed | Confidence | Residual risk |
|---|---|---|---|---|---|
| Native support extends existing UI workflow, not a new skill. | Designed source changes modify `/ui-design`, `/visualize`, UI docs, template/script/catalog only. | A design introduces a new `/native-ui-design` skill or duplicates `/ui-design` flow. | Simplifier review blocked overbroad scope; this revision removes parallel-skill scope. | **Verified** | Implementation must keep wording centralized. |
| XAML token linting is deterministic and bounded. | Linter scope narrowed to raw color/brush/dimension markup checks with JSON/text output and no suppressions first slice; output emits attribute names, not raw source snippets. | Linter attempts full semantic XAML compilation, network/includes, broad suppressions, source-snippet logging, or undocumented dynamic checks. | Security/Simplifier/Patterns/Python reviews blocked broader or leaky drafts; this revision narrows it. | **Verified** | Future rules may be added after fixtures prove need. |
| Native archetype rows meet catalog contract. | Design now specifies three rows with signatures and codegen descriptors. | A catalog row lacks a parseable signature or descriptor. | Patterns review blocked narrative-only rows; this revision adds row contracts. | **Verified** | Exact grammar parser validation happens in implementation. |
| Native proof pack is testable. | Template schema, proof row fields and golden tests are specified. | Proof row can pass with screenshot-only evidence for accessibility/keyboard/DPI/signing. | Test Architect review blocked missing proof pack; this revision adds schema and tests. | **Verified** | Actual template must preserve these fields. |
| Generated native interface remains prohibited. | `/visualize` design includes reject scenarios and native asset-only wording. | Prompt asks for generated WPF/WinUI screen and workflow allows it. | Planned A6 golden scenario. | **Inferred until implemented** | Implementation must add the golden prompt/eval. |

## Conformance notes

- **LOA P2 / deterministic floor:** XAML token linting is deterministic; model critique never proves native runtime behavior.
- **LOA P3/P5:** generated assets never execute side effects or become UI; model output is not accepted as interface proof.
- **P9 typed boundaries:** native proof row schema is structured and reusable.
- **P10 audit:** skill/design/implementation runs continue through existing audit log.

## Flagged risks & residual unknowns

| Risk | Disposition |
|---|---|
| Exact CI-friendly WPF/WinUI automation tool not chosen | Accepted for design; implementation can ship skill/template/linter first and leave UIA/Appium/FlaUI runner selection per repo. |
| Apple notarization details still need direct recheck | Accept with guard: design requires recheck before macOS release PASS. |
| Native archetype row names/signatures may need adjustment | Accept; implement rows from this design and revise when real native surface feedback appears. |
| XAML linter false positives | Mitigate with narrow first rules and clean fixtures from WPF/WinUI/Avalonia examples; suppressions require a separate design before they exist. |

## Status & next action

| | |
|---|---|
| **Completed** | Designed the native app UI skill extension across `/ui-design`, `/visualize`, a native proof-pack template, XAML token linting, native archetype rows, and exemplar policy. |
| **Remaining** | Implementation of pack source changes and generated-surface sync. |
| **Best next action** | `/implement` this design in the pack source, then run `tools/sync-pack.ps1`, graph validation, and affected evals/static tests. |

## Gate record

`GATE design · 2026-08-26 · reviewers: Test Architect, Security & Identity Architect, Native Desktop Developer, Patterns Expert, The Simplifier · criteria met: accepted spec implemented, contracts named, patterns justified, failure modes/STRIDE/privacy/test plan present, proof-pack schema attached, native archetype rows have parseable signatures/descriptions, first-slice XAML linter scope bounded · verdict: PASS-WITH-CONDITIONS · vetoes→resolution: initial Test/Security/Native/Patterns/Simplifier blocks resolved by adding proof-pack schema/tests, distribution and linter boundaries, valid catalog rows, framework-specific token/resource forms, and narrowed scope; residual tooling choices deferred to /implement or later /design.`

---
**Handoff:** → `/implement`.
