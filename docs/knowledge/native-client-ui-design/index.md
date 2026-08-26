---
id: kb-native-client-ui-design
title: "Native client UI design — WPF, WinUI, Avalonia and desktop apps"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, desktop, wpf, winui, avalonia, fluent, macos, accessibility, high-dpi, ui-automation]
links:
  - { to: architecture, rel: relates-to }
  - { to: kb-domain-and-data-modelling, rel: relates-to }
review-by: "2026-11-24"
summary: >-
  Sourced evidence base for extending the pack's UI reasoning and review from web properties to native client applications. Establishes the native-specific design contract: platform HIG conformance, OS window/input integration, design tokens through XAML/resource systems, UI Automation accessibility, high-DPI/multi-monitor behavior, and packaging/signing trust gates.
---

# Native client UI design — domain knowledge

**Domain & problem:** the pack already has strong UI standards and a Native Desktop Developer lens, but the supporting knowledge is mostly web/component oriented. We need a durable evidence base for reviewing, refining and elevating native client UX/UI, especially WPF, WinUI/Windows App SDK, Avalonia and other desktop applications.

**Canonical framing:** native desktop UI excellence is **platform-conformant product design** plus **native runtime proof**. The web framing ("responsive component surface rendered in the browser") is too narrow: a desktop app also has windowing, command routing, keyboard focus, OS theme/high-contrast settings, accessibility trees, high-DPI/mixed-monitor rendering, file/protocol associations, installers, signing/notarization and auto-update. *(Verified: Microsoft Windows design overview; Windows accessibility overview; WinUI 3; Windows App SDK windowing; Apple HIG; GNOME/KDE HIGs.)*

**Compiled:** 2026-08-26 · **Lead:** Domain Researcher · **Status:** fresh

## Research map

The load-bearing questions were:

1. Which parts of the pack's existing UI doctrine transfer unchanged to native clients?
2. Which native contracts must be added before WPF/WinUI/Avalonia/macOS review can be trusted?
3. Which public, permissively licensed repositories are safe exemplars for review, refinement and pattern extraction?
4. Which official standards and tools should become the citation base for the native desktop lens?
5. What disconfirms a naive "web UI rules are enough" approach?

## Headline findings

1. **Native app review must start with the platform's design contract, not the framework.** Windows design guidance says Windows app experiences should leverage Fluent Design and work across devices, input types and form factors; WinUI 3 is Microsoft’s recommended native UI framework for new Windows desktop applications and brings Fluent controls/styles, high-DPI visuals, and Windows App SDK access. *(Verified: Microsoft Learn Windows design overview [S1], WinUI 3 [S6].)*

2. **The pack's UX layers still apply, but native changes the evidence required at the gate.** Functional -> UX -> UI layering, direction briefs, state completeness, token discipline, copy, and critique dimensions transfer. The proof must be native: UI Automation/NSAccessibility/AT-SPI metadata, keyboard-only traversal, per-monitor DPI, window behavior, installer/signing checks, and real OS theme/high-contrast state. *(Verified for Windows and Avalonia accessibility APIs [S4], [S5], [S16], [S17]; Inferred as a pack synthesis across standards.)*

3. **Accessibility is programmatic in native clients.** WPF and Windows XAML expose accessibility through UI Automation and automation peers; custom controls require explicit peers/properties. Avalonia uses automation peers that map to UI Automation on Windows, NSAccessibility on macOS and AT-SPI on Linux; `AutomationProperties.Name`, `HelpText`, `LabeledBy`, `AutomationId`, `HeadingLevel` and live settings are part of the native UI contract. *(Verified: Microsoft UI Automation accessibility best practices [S5], Windows accessibility overview [S4], Avalonia accessibility [S16].)*

4. **Keyboard is a primary desktop interaction model, not an accessibility afterthought.** Microsoft’s keyboard accessibility guidance states keyboard access should be treated as primary, with focusable/reachable controls, tested tab behavior, logical visual/focus order, and explicit validation for grid/table layouts. Avalonia's focus documentation likewise treats focus visuals, `Focusable`, `TabIndex`, `KeyboardNavigation`, and focus pseudo-classes as design inputs. *(Verified: Windows keyboard accessibility [S8], Avalonia focus [S17].)*

5. **Design tokens translate to native resource systems, not CSS variables.** Windows XAML theme resources respond to runtime theme changes and explicitly support Light, Dark and HighContrast; Avalonia styles/control themes use scoped cascading XAML selectors. So the pack's `DESIGN.md` token contract should compile into ResourceDictionaries, ThemeResources/DynamicResources and style classes, not into raw XAML literals. *(Verified: XAML theme resources [S12], Avalonia styles [S15]; Inferred design implication.)*

6. **High-DPI and multi-monitor behavior is a native correctness requirement.** WPF apps are system-DPI aware by default; per-monitor DPI awareness requires manifest/config and relayout/rerender behavior, including images, hosted HWND/WinForms controls, `RenderTargetBitmap`, and text formatting paths. Windows App SDK windowing APIs also make top-level windows a first-class integration point. *(Verified: WPF high-DPI page [S10], WPF-Samples PerMonitorDPI [S22], Windows App SDK windowing [S7].)*

7. **Distribution trust is part of native UX.** Windows MSIX packages must be signed with a valid code-signing certificate and trusted on the device; SmartScreen checks publisher and file reputation and unsigned or new binaries can interrupt launch. macOS has its own signing/notarization gate that must be rechecked before release. A beautiful unsigned app is still a broken user journey. *(Verified for Windows signing/SmartScreen [S13], [S14]; Flagged for detailed macOS release mechanics beyond the official notarization page title [S20].)*

8. **Permissively licensed exemplars exist and should be reviewed as patterns, not copied wholesale.** PowerToys, Files, WinUI Gallery, WPF UI, MaterialDesignInXamlToolkit, Avalonia, WPF-Samples, microsoft-ui-xaml and WindowsAppSDK-Samples are public and MIT-licensed by GitHub REST license metadata or repository license files. They are suitable for pattern study and limited reuse under license terms; product-specific visual identity should still be adapted, never cloned. *(Verified: GitHub REST license checks and repo READMEs [S24]-[S33].)*

9. **Some attractive public native apps are not amenable reuse sources.** Lively reports GPL-3.0 and is reference-only for this pack. EarTrumpet’s license file contains an MIT text plus named excluded entities, and GitHub classifies it as `NOASSERTION`; treat it as **Flagged** and do not use it as a reusable source without legal review. *(Verified: GitHub REST license checks and EarTrumpet license text.)*

10. **Native review needs a broader failure-mode list than web craft detection can see.** A static HTML/CSS detector cannot prove UI Automation names, focus restoration after dialogs, per-monitor DPI scaling, installer trust, window lifecycle, tray/menu behavior, OS notification permissions, or WPF/Avalonia layout virtualization behavior. Those become explicit native proof rows, not style nits. *(Inferred from the gap between existing pack tooling and native platform contracts; grounded by [S8], [S10], [S11], [S40]-[S46].)*

## Confidence summary

- **Verified:** 8 headline claims have current official/platform or repository-license evidence.
- **Inferred:** 2 claims are pack-level synthesis: token-to-native-resource mapping and native proof rows. They are grounded in primary docs but no source states the pack-specific mapping directly.
- **Flagged:** Detailed Apple notarization requirements beyond the official page title need direct Apple Developer recheck before a release gate. EarTrumpet licensing is non-standard and must not be treated as permissive reuse.

## Design implications

1. **Extend `/ui-design` for native with a "native proof pack."** Add checks for platform HIG, native window model, keyboard traversal, UI Automation/accessibility tree, theme/high-contrast, DPI/multi-monitor, OS integration and packaging/signing.
2. **Treat `DESIGN.md` as source and generate native resources.** For WPF/WinUI/Avalonia, tokens should bind through resource dictionaries/theme resources/styles; raw colors, font sizes, margins and radii in XAML are findings just like raw CSS values.
3. **Create native mockups/prototypes differently from web mockups.** The existing dependency-free HTML mockup remains useful for direction, but native final proof must run inside the target runtime because focus, automation peers, windowing and DPI are OS behaviors.
4. **Add native exemplar rows to the UI archetype catalog.** Candidate archetypes: Windows Fluent Utility, File Manager Workbench, Command Palette Shell, Tray/Background Utility, Data Grid Line-of-Business Client, Cross-Platform XAML Workbench.
5. **Promote public repos as reference exemplars with license labels.** Use MIT examples for pattern study; keep GPL/non-standard licenses reference-only and record the license status beside each exemplar.

## How to use this base

- **`/adddomainexperts`** may add a Windows Desktop UI Architect or WPF/WinUI Native UX Reviewer lens that cites this base.
- **`/specify`** should declare native medium, platform guidelines, distribution channel and accessibility obligation.
- **`/design`** should consume `state-of-the-art.md` and `comparables.md` before producing native UI architecture.
- **`/implement`** should map the proof rows in `data-and-constants.md` into UI Automation, keyboard, theme and DPI tests.

## Files

| File | Contents |
|---|---|
| `state-of-the-art.md` | Current best practice and native-specific design contracts |
| `comparables.md` | Public repositories and products worth reviewing, with license posture |
| `references.md` | Official standards, HIGs, docs and tools |
| `data-and-constants.md` | Checklists, invariants and proof rows for native UI review |
| `glossary.md` | Native UI ubiquitous language |
| `open-questions.md` | Unsettled claims and failure modes |
| `sources.md` | Full source list with access dates |
