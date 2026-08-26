---
id: kb-native-client-ui-design-sota
title: "Native client UI design — State of the Art"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, fluent, wpf, winui, avalonia, accessibility, keyboard, high-dpi, windowing]
links:
  - { to: kb-native-client-ui-design, rel: refines }
review-by: "2026-11-24"
summary: >-
  Current best practice for native client UX/UI: use the target OS design system as the primary contract, keep the pack's UX/UI layering and token discipline, translate tokens into native resource systems, and verify native runtime behavior through accessibility, keyboard, DPI, windowing and distribution gates.
---

# State of the art

## 1. Native app design is platform-first

**Windows.** Microsoft frames Windows app design as Fluent-based experiences that are intuitive, accessible, and work across devices, input types and form factors. The guidelines include layout, navigation, input, typography, motion, materials, color, icons and commanding; WinUI Gallery is the interactive companion showing controls, code snippets, adaptive UI and accessibility/design guidance. *(Verified: [S1], [S2], [S23].)*

**macOS.** Apple's HIG says Mac design starts from large/high-resolution displays, multi-app work, high-precision input, keyboard shortcuts, menu bar commands, flexible windows and platform system features. Apple JSON sources also say system windows should adapt to size changes, excessive new windows create clutter, custom window frames/controls are risky, menu bar ordering and disabled-visible items matter, and notifications require consent and should not carry sensitive information. *(Verified from Apple HIG JSON endpoints: [S18], [S19], [S20], [S48]-[S53]. Detailed notarization mechanics remain Flagged.)*

**Linux desktop.** GNOME and KDE both publish HIGs that emphasize app-specific platform conventions rather than generic cross-platform sameness. GNOME states its HIG is the primary design documentation for GTK 4/Libadwaita apps and covers design principles, resources, guidelines, patterns and reference. KDE states its HIG covers design philosophy, workflows/patterns, UI conventions and platform integration, and explicitly encourages knowing target users/use cases rather than spreading thin. *(Verified: [S21], [S22].)*

## 2. Use native controls/resources before custom visuals

Native controls carry behavior that web-style mockups do not: theme participation, focus affordances, automation peers, text rendering, DPI scaling, keyboard patterns and platform-consistent density. The default should be to **style native controls through resources/themes** rather than rebuild controls from scratch. Custom controls carry an accessibility and behavior debt: they must expose the same automation role, name, state, patterns and events as the standard control they replace. *(Verified for WPF/Windows/Avalonia accessibility: [S4], [S5], [S16].)*

## 3. Token discipline becomes resource discipline

The pack's token system survives, but its implementation changes:

- **WinUI/UWP/Windows XAML:** use theme resources. `{ThemeResource}` re-evaluates when the app/theme changes; `{StaticResource}` does not. XAML supports Light, Dark and HighContrast dictionaries. *(Verified: [S12].)*
- **WPF:** use ResourceDictionary, DynamicResource and system colors where the value must react to theme/high contrast. WPF’s built-in controls already provide much accessibility behavior; custom controls require automation peer work. *(Verified: [S5]; Inferred mapping to pack tokens.)*
- **Avalonia:** styles/control themes and cascading selectors provide a resource system analogous to CSS/XAML styling; scoped styles should receive token values instead of one-off literals. *(Verified: [S15].)*

## 4. Accessibility proof is an accessibility tree, not only pixels

Windows accessible apps should support keyboard interactions, screen readers, customization such as font/zoom/color/high contrast, and alternative/supplemental UI. XAML controls integrate with Microsoft UI Automation through automation peers and patterns. Accessibility Insights for Windows can inspect UIA properties, run FastPass automated checks, test tab stops, inspect patterns, record events and check contrast. *(Verified: [S4], [S5], [S11].)*

Avalonia similarly exposes controls to platform accessibility APIs through automation peers and `AutomationProperties`; `AutomationId` is a stable UI automation testing identifier and should not localize. Avalonia's Appium guidance is explicit that Appium launches the real app and drives it through the platform accessibility tree, while headless tests do not prove platform accessibility. *(Verified: [S16], [S47].)*

## 5. Keyboard-first is a desktop quality bar

Microsoft explicitly says keyboard accessibility should be treated as a primary interaction model. Controls must be focusable/reachable, tab behavior must be validated, and grid/table layouts commonly produce mismatches between visual and focus order. Avalonia documents `Focusable`, explicit focus, focus pseudo-classes and tab navigation as core concepts. *(Verified: [S8], [S17].)*

## 6. High DPI, multi-monitor and windowing are functional behavior

WPF is system-DPI aware by default; per-monitor DPI awareness requires manifest/config and relayout/rerender behavior. The official WPF-Samples guide calls out images, hosted HWND/WinForms controls, `RenderTargetBitmap` and text formatting as extra coding scenarios. Windows App SDK `AppWindow` APIs manage top-level windows and title bar/presenter behavior across WinUI, WPF, WinForms and Win32. *(Verified: [S10], [S22], [S7].)*

## 7. Distribution trust is part of UX

MSIX package signing is required for deployment, and the certificate must chain to a trusted root on the device. SmartScreen evaluates publisher reputation and file hash reputation; Store-distributed apps avoid SmartScreen download warnings, while unsigned/self-signed downloads produce warnings and may be blocked by policy. *(Verified: [S13], [S14].)*

For macOS, notarization must be treated as a release gate, but detailed requirements should be rechecked from Apple Developer documentation at the time of release. *(Flagged: [S20].)*

## 8. Performance is layout and virtualization, not only bundle size

WPF performance guidance identifies layout passes as mathematically intensive and recommends reducing unnecessary layout invalidation. WPF control guidance states large item lists should use UI virtualization so only visible item containers are generated and arranged. Native UI performance review therefore needs tests/measurements for layout churn, virtualization, UI-thread responsiveness and rendered frame behavior, not only web-style payload size. *(Verified: [S43], [S44].)*

## 9. Verification frontier

Native UI quality is moving toward automated proof, but no one tool covers it:

- Accessibility Insights/Inspect/UIA tests prove UI Automation and tab stops on Windows.
- Snapshot/image diff can catch visual regressions but cannot prove accessibility semantics.
- XAML resource linting can catch raw token values, but must be built or extended.
- DPI/windowing tests often need a real Windows environment with mixed DPI or targeted simulator/probes.
- Avalonia Appium tests can prove full-app, platform integration and accessibility behavior through a real window; Avalonia headless tests are faster but explicitly do not prove platform accessibility.
- macOS/Linux equivalents require their platform accessibility tools and packaging checks.

**Design implication:** `/implement` should produce multiple proof rows: accessibility tree, keyboard traversal, theme/high-contrast, DPI/windowing, and distribution gate. A screenshot is insufficient.
