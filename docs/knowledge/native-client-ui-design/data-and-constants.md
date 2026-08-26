---
id: kb-native-client-ui-design-data
title: "Native client UI design — Data, constants and proof rows"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, checklist, proof-pack, accessibility, dpi, signing, keyboard]
links:
  - { to: kb-native-client-ui-design, rel: refines }
review-by: "2026-11-24"
summary: >-
  Checkable native UI invariants and proof rows: accessibility tree, keyboard traversal, theme/high-contrast behavior, DPI/windowing, native resource tokens, OS integration and installer/signing trust.
---

# Domain data, constants and invariants

## Native UI proof rows

Use these as the starting Proof Pack for WPF/WinUI/Avalonia/native desktop work.

| Claim to prove | Evidence / oracle | Source |
|---|---|---|
| Every interactive control is keyboard reachable in logical visual order | Keyboard-only traversal recording; no traps; dialog close returns focus to the invoker; grid/table order intentionally matches or documents divergence | Windows keyboard accessibility [S8]; Avalonia focus [S17] |
| Every non-text/icon/custom control has an accessible name, role and state | UI Automation / Accessibility Insights / platform inspector output shows name, control type, patterns and states; custom controls have AutomationPeer/AutomationProperties | Windows accessibility [S4], WPF UIA best practices [S5], Avalonia accessibility [S16] |
| Theme changes update the UI without restart | Switch Light/Dark/HighContrast at runtime; resource-bound colors/fonts update; no `StaticResource` where runtime theme update is required | XAML theme resources [S12] |
| High contrast remains usable and passes contrast floor | OS high-contrast mode screenshot/inspector; foreground/background pairs meet required ratios; non-color affordance remains | Fluent accessibility [S3], Windows accessibility [S4] |
| Per-monitor DPI works on mixed-DPI displays | Move window between monitors at different scale; text/images remain crisp; hosted HWND/WinForms/text-rendered surfaces handle `DpiChanged` | WPF DPI docs [S10], WPF-Samples [S22] |
| Window model follows platform conventions | AppWindow/Window APIs used for title bar, sizing, presenter/full-screen/compact overlay; custom title bars preserve system drag, snap and accessibility | Windows App SDK windowing [S7] |
| Installer does not create a trust interruption | MSIX/installer is signed with trusted certificate; SmartScreen risk documented; Store vs non-Store channel chosen intentionally | MSIX signing [S13], SmartScreen [S14] |
| Native token system is enforced | XAML/resources/styles consume named tokens; raw hex/magic margin/font size in XAML is a lint finding | XAML theme resources [S12], Avalonia styles [S15], pack UI U3/U20 |
| OS integration is least-privilege and discoverable | File/protocol associations, notifications, tray/dock/menu actions, startup/login items are scoped, reversible and documented | Windows App SDK samples [S34]; platform HIGs [S18], [S21], [S22] |
| Large native lists remain responsive | UI virtualization remains enabled; only visible item containers are generated; scrolling does not block the UI thread | WPF control performance [S44] |
| Native layouts avoid unnecessary layout churn | Measured layout passes/reflows stay within budget; template changes do not trigger repeated full-tree measure/arrange | WPF layout performance [S43] |

## Native review checklist

### Windows / WPF / WinUI

- Framework decision stated: WinUI 3 for new modern native desktop by default; WPF justified for existing/WPF-heavy products. *(Verified from Microsoft WinUI docs [S6]; project constraints may override.)*
- Design language: Fluent color/typography/icon/material guidance or an explicitly justified alternative.
- XAML resource plan: primitive/semantic/component token mapping to ResourceDictionary/ThemeResource/DynamicResource.
- Accessibility: AutomationProperties, AutomationPeer for custom controls, UI Automation patterns/events, Accessibility Insights FastPass.
- Keyboard: tab order, focus visuals, accelerators/access keys, command discoverability.
- DPI/windowing: per-monitor DPI, mixed monitor testing, custom title bar correctness, multi-window/document model.
- Performance: layout invalidation, UI virtualization, UI-thread responsiveness and animation smoothness.
- Distribution: Store/MSIX/exe choice, certificate/signing, SmartScreen reputation, update channel.

### Avalonia / cross-platform XAML

- Platform target list stated (Windows/macOS/Linux) and per-platform HIG deltas named.
- Styles/control themes scoped through Avalonia resource/style system; no raw values.
- AutomationProperties/AutomationId used for screen readers and test automation.
- Focus pseudo-classes and `KeyboardNavigation` behavior covered in design/test.
- Per-platform accessibility tested with Narrator, VoiceOver and/or Orca where those platforms ship.
- Test layers chosen deliberately: unit/view-model tests, headless control tests, visual regression tests, and Appium for real-window platform integration/accessibility.

### macOS

- Apple HIG consulted for menus, toolbar/sidebar/window model, keyboard shortcuts and accessibility.
- Standard windows/menu bar/keyboard shortcuts preserved unless a documented product need justifies a deviation.
- Notifications request consent, stay concise/high-value, and do not carry sensitive data.
- Code signing/notarization path stated before release.
- Platform-specific shortcuts and menu bar conventions are not inherited from Windows/web defaults.

### GNOME/KDE

- Target platform declared; GNOME HIG applies to GTK/Libadwaita apps; KDE HIG applies to Plasma/Kirigami/Qt apps.
- Standard widgets/patterns preferred; cross-platform custom chrome must be justified.

## Native failure modes

- **Web-shaped desktop app:** hamburger/mobile/web dashboard patterns replace platform menu/window/keyboard idioms.
- **Accessible pixels, inaccessible tree:** visual labels exist but UI Automation/NSAccessibility/AT-SPI name/role/state is missing.
- **Pointer-only feature:** mouse works, keyboard traversal cannot reach or operate the function.
- **Theme-resources bypassed:** raw colors or static resources ignore dark/high-contrast mode.
- **DPI-blurry shell:** looks fine on one monitor, blurs/clips when dragged to another DPI.
- **Trust-interrupted launch:** app is visually polished but unsigned/notarized/SmartScreen-blocked.
- **Custom control debt hidden by screenshots:** bespoke control lacks standard patterns, focus and automation events.
