---
id: kb-native-client-ui-design-open-questions
title: "Native client UI design — Open questions and disconfirmation"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, open-questions, risks, disconfirmation]
links:
  - { to: kb-native-client-ui-design, rel: refines }
review-by: "2026-11-24"
summary: >-
  Unresolved native UI research questions, disconfirming evidence, and domain failure modes that the next design pass must settle before changing pack skills or shipping native app guidance.
---

# Open questions and domain failure modes

## Unresolved by research

- **Apple notarization details are under-sourced in this run.** The Apple HIG JSON endpoints verified design guidance, but the notarization page still yielded only official page metadata. Before writing macOS-specific release gates, re-open Apple Developer docs directly and cite the exact current notarization requirements. *(Flagged.)*
- **Native UI automation test stack choice.** Accessibility Insights is strong for Windows inspection/FastPass and Avalonia documents Appium for real-window platform/accessibility tests, but the pack still needs a chosen CI-friendly automation path for WPF/WinUI (for example UIA COM/client tests, Appium Windows driver where applicable, FlaUI, Playwright only for WebView surfaces). This is a design decision, not a knowledge fact. *(Flagged.)*
- **Token linting for XAML.** The pack has web-oriented `design-lint.py` and UI craft detection. Native XAML needs a rule set that detects raw colors, static resources in theme-sensitive locations, missing AutomationProperties, and raw sizing tokens. No existing pack script covers this. *(Flagged.)*
- **WPF vs WinUI default recommendation.** Microsoft recommends WinUI 3 for new modern Windows desktop apps, but many products rightly stay WPF for mature controls, designer support, ecosystem, or existing code. The pack should frame this as "justify the framework against the product/runtime constraints," not "always migrate." *(Verified/Inferred.)*

## Disconfirming views deliberately sought

- **Against "web UI knowledge is enough":** official Windows docs require UI Automation, keyboard traversal, high contrast, per-monitor DPI and signed deployment; none are visible in a web-style static mockup. The claim fails. *(Verified.)*
- **Against "a screenshot proves performance":** WPF docs identify layout passes and item container generation as native performance costs; a static mockup cannot prove virtualization, layout invalidation, or UI-thread responsiveness. *(Verified.)*
- **Against "native means copy the OS chrome":** KDE explicitly frames its HIG as guidelines, not an ironclad law, and says good design can innovate when the project understands why. The right rule is "use platform conventions unless a stated user need justifies deviation," not "never custom." *(Verified: [S22].)*
- **Against "cross-platform XAML removes platform design work":** Avalonia abstracts styling/accessibility but still maps to different platform accessibility APIs (UIA/NSAccessibility/AT-SPI); therefore each target platform still needs verification. *(Verified: [S16].)*
- **Against "permissive repo means copy UI":** MIT permits code reuse under terms, but product visual identity, names, assets and screenshots may still be protected by trademark/copyright or brand. The pack should borrow patterns and cite license, not clone distinctive surfaces. *(Inferred from legal boundaries; not legal advice.)*

## Known failure modes

- **Native shell not reviewed:** content screen is polished, but title bar, window resize, restore state, close/minimize behavior, multi-window behavior or tray/dock state feels alien.
- **Keyboard/focus drift:** refactor changes visual order but not XAML declaration/TabIndex; keyboard traversal no longer matches the mental model.
- **Accessibility lost in a custom template:** replacing a standard control template drops names, patterns, states or events.
- **High-contrast token gap:** design tokens define light/dark but not HighContrast; app becomes unreadable for users who depend on OS high contrast.
- **DPI lab gap:** only tested at 100% scale on one monitor; mixed-DPI or remote desktop users see blurred/clipped controls.
- **Installer trust failure:** first-run journey starts with SmartScreen/Gatekeeper warning; product trust is damaged before UI loads.
- **Web detector false assurance:** HTML mockup is clean, but native app lacks UIA names/focus/theming because those cannot be detected in HTML.

## Simplifier gate

The knowledge base is load-bearing because it narrows the future pack change to five native-specific additions:

1. native platform contract checklist,
2. native proof rows,
3. permissive exemplar list,
4. native token/resource mapping,
5. native failure modes.

Excluded as non-load-bearing: broad histories of WPF/WinUI/macOS, screenshots of every exemplar, and deep implementation tutorials for each framework.
