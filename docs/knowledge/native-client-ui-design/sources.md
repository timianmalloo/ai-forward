---
id: kb-native-client-ui-design-sources
title: "Native client UI design — Sources"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, sources, citations, licenses]
links:
  - { to: kb-native-client-ui-design, rel: refines }
review-by: "2026-11-24"
summary: >-
  Full source list for native client UI design research: official Windows/Fluent/Avalonia/GNOME/KDE documentation, Apple pages that need direct recheck, Accessibility Insights, and GitHub license evidence for public native app exemplars.
---

# Sources

**Accessed:** 2026-08-26. Ordered by source-of-truth hierarchy: official platform docs first, then official tools/docs, then public repository metadata.

| ID | Title / source | Type | URL | Used for | Confidence |
|---|---|---|---|---|---|
| S1 | Design Windows apps overview | official docs | https://learn.microsoft.com/en-us/windows/apps/design/ | Windows design hub, Fluent framing, devices/input/form factors | **Verified** |
| S2 | Design guidelines - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/design/guidelines-overview | Windows foundations: color, typography, layout, materials, motion, navigation, input | **Verified** |
| S3 | Fluent 2 Accessibility | official design system | https://fluent2.microsoft.design/accessibility | WCAG AA, focus, structure, contrast, responsive text/zoom | **Verified** |
| S4 | Accessibility overview - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-overview | keyboard/screen reader/customization, UI Automation, automation peers | **Verified** |
| S5 | Accessibility Best Practices - .NET Framework | official docs | https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/accessibility-best-practices | WPF AutomationPeer, AutomationProperties, custom control accessibility | **Verified** |
| S6 | WinUI 3 - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/winui/winui3/ | WinUI 3 recommended framework, Fluent controls, high-DPI rendering | **Verified** |
| S7 | Manage app windows - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/develop/ui/manage-app-windows | AppWindow/HWND mapping, top-level window management | **Verified** |
| S8 | Keyboard accessibility - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/design/accessibility/keyboard-accessibility | keyboard as primary model, focus traversal, tab order validation | **Verified** |
| S9 | Input and interactions - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/develop/input/ | WinUI desktop input APIs, package identity caveat, UWP-only caveats | **Verified** |
| S10 | Developing a Per-Monitor DPI-Aware WPF Application | official docs | https://learn.microsoft.com/en-us/windows/win32/hidpi/declaring-managed-apps-dpi-aware | WPF DPI manifest, WM_DPICHANGED, relayout/rerender requirements | **Verified** |
| S11 | Accessibility Insights for Windows overview | official tool docs | https://accessibilityinsights.io/docs/windows/overview/ | Live Inspect, FastPass, tab stops, UIA properties/events/contrast | **Verified** |
| S12 | XAML theme resources | official docs | https://learn.microsoft.com/en-us/windows/apps/develop/platform/xaml/xaml-theme-resources | Light/Dark/HighContrast theme dictionaries; ThemeResource vs StaticResource | **Verified** |
| S13 | Sign an MSIX package | official docs | https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview | MSIX signing requirement, certificate trust, signing options | **Verified** |
| S14 | SmartScreen reputation for Windows app developers | official docs | https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation | publisher/hash reputation, unsigned/self-signed warning behavior | **Verified** |
| S15 | Avalonia styles | official docs | https://docs.avaloniaui.net/docs/styling/styles | Avalonia styles/control themes/container queries and cascading style model | **Verified** |
| S16 | Avalonia accessibility | official docs | https://docs.avaloniaui.net/docs/app-development/accessibility | automation peers, AutomationProperties, UIA/NSAccessibility/AT-SPI mapping | **Verified** |
| S17 | Avalonia focus | official docs | https://docs.avaloniaui.net/docs/input-interaction/focus | focus properties, focus pseudo-classes, tab navigation | **Verified** |
| S18 | Apple HIG | official docs | https://developer.apple.com/design/human-interface-guidelines/ | macOS/iOS platform design authority | **Verified** as official source; detailed claims use JSON endpoints below |
| S19 | Designing for macOS | official docs | https://developer.apple.com/design/human-interface-guidelines/designing-for-macos | macOS-specific design authority | **Verified** via JSON endpoint S47 |
| S20 | Notarizing macOS software before distribution | official docs | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | macOS distribution trust gate | **Flagged** - fetch returned title/official page only |
| S21 | GNOME Human Interface Guidelines | official docs | https://developer.gnome.org/hig/ | GTK/Libadwaita design principles, patterns and reference | **Verified** |
| S22 | KDE Human Interface Guidelines | official docs | https://develop.kde.org/hig/ | KDE design philosophy, patterns, platform integration and innovation caveat | **Verified** |
| S23 | `microsoft/WinUI-Gallery` README | public repo | https://github.com/microsoft/WinUI-Gallery | WinUI control/style companion app; adaptive UI; samples; design/accessibility guidance | **Verified** |
| S24 | `microsoft/PowerToys` README | public repo | https://github.com/microsoft/PowerToys | Windows utility suite; installation channels; WinUI modernization; design contributions | **Verified** |
| S25 | `files-community/Files` README | public repo | https://github.com/files-community/Files | modern Windows file manager, multitasking, tags, Store/classic installer | **Verified** |
| S26 | `microsoft/PowerToys` license metadata | GitHub REST | https://github.com/microsoft/PowerToys/blob/main/LICENSE | MIT license | **Verified** |
| S27 | `microsoft/WinUI-Gallery` license metadata | GitHub REST | https://github.com/microsoft/WinUI-Gallery/blob/main/LICENSE | MIT license | **Verified** |
| S28 | `files-community/Files` license metadata | GitHub REST | https://github.com/files-community/Files/blob/main/LICENSE-MIT | MIT license | **Verified** |
| S29 | `microsoft/microsoft-ui-xaml` metadata | GitHub REST | https://github.com/microsoft/microsoft-ui-xaml | MIT license; WinUI framework | **Verified** |
| S30 | `microsoft/WindowsAppSDK-Samples` metadata | GitHub REST | https://github.com/microsoft/WindowsAppSDK-Samples | MIT license; SDK feature samples | **Verified** |
| S31 | `microsoft/WPF-Samples` metadata | GitHub REST | https://github.com/microsoft/WPF-Samples | MIT license; WPF sample corpus | **Verified** |
| S32 | `lepoco/wpfui` README/license | public repo | https://github.com/lepoco/wpfui | MIT WPF Fluent theme/control library, gallery, tray/menu examples | **Verified** |
| S33 | `MaterialDesignInXAML/MaterialDesignInXamlToolkit` README/license | public repo | https://github.com/MaterialDesignInXAML/MaterialDesignInXamlToolkit | MIT WPF Material Design theme/control library | **Verified** |
| S34 | `WindowsAppSDK-Samples` README | public repo | https://github.com/microsoft/WindowsAppSDK-Samples | App lifecycle, AI, background task, resource, Mica, TextRendering, Islands samples | **Verified** |
| S35 | `AvaloniaUI/Avalonia` README/license | public repo | https://github.com/AvaloniaUI/Avalonia | MIT cross-platform .NET UI framework | **Verified** |
| S36 | `microsoft/CsWin32` metadata | GitHub REST | https://github.com/microsoft/CsWin32 | MIT source generator for Win32 interop | **Verified** |
| S37 | Color in Windows | official docs | https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/color | Fluent color, light/dark, accent and hierarchy | **Verified** |
| S38 | Typography in Windows | official docs | https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography | Segoe UI Variable, optical size, typography hierarchy | **Verified** |
| S39 | Icons in Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/icons | icon purpose, clarity and visual shorthand in Windows apps | **Verified** |
| S40 | Contrast themes - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/design/accessibility/high-contrast-themes | contrast themes are distinct from light/dark; constrained palette; HighContrast dictionaries | **Verified** |
| S41 | Keyboard accelerators - Windows apps | official docs | https://learn.microsoft.com/en-us/windows/apps/develop/input/keyboard-accelerators | shortcuts, menus as discovery, app/control accelerators | **Verified** |
| S42 | UI Automation of a Custom Control - WPF | official docs | https://learn.microsoft.com/en-us/dotnet/desktop/wpf/controls/ui-automation-of-a-wpf-custom-control | custom AutomationPeer implementation and UIA provider role | **Verified** |
| S43 | Optimizing Performance: Layout and Design - WPF | official docs | https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/optimizing-performance-layout-and-design | layout passes, measure/arrange cost, reducing layout invalidation | **Verified** |
| S44 | Optimize control performance - WPF | official docs | https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/optimizing-performance-controls | UI virtualization and large data set control performance | **Verified** |
| S45 | Avalonia theme variants | official docs | https://docs.avaloniaui.net/docs/styling/theme-variants | Light/Dark theme variants, RequestedThemeVariant, variant-specific resources | **Verified** |
| S46 | Avalonia testing | official docs | https://docs.avaloniaui.net/docs/testing/ | unit/headless/visual/Appium test strategy distinctions | **Verified** |
| S47 | Avalonia UI testing with Appium | official docs | https://docs.avaloniaui.net/docs/testing/ui-testing-with-appium | real-window platform integration and accessibility tests through accessibility tree | **Verified** |
| S48 | Apple HIG JSON - Designing for macOS | official docs JSON | https://developer.apple.com/tutorials/data/design/human-interface-guidelines/designing-for-macos.json | large displays, multiple apps, menu bar, windows, keyboard/high-precision input | **Verified** |
| S49 | Apple HIG JSON - Windows | official docs JSON | https://developer.apple.com/tutorials/data/design/human-interface-guidelines/windows.json | window types, resizing/multitasking, avoid custom window chrome | **Verified** |
| S50 | Apple HIG JSON - Menu bar | official docs JSON | https://developer.apple.com/tutorials/data/design/human-interface-guidelines/the-menu-bar.json | menu bar reliance, menu order, disabled visible items, standard icons | **Verified** |
| S51 | Apple HIG JSON - Keyboards | official docs JSON | https://developer.apple.com/tutorials/data/design/human-interface-guidelines/keyboards.json | Full Keyboard Access, standard shortcut respect, custom shortcut guidance | **Verified** |
| S52 | Apple HIG JSON - Accessibility | official docs JSON | https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json | intuitive/perceivable/adaptable UI, Accessibility Inspector, Dynamic Type, text size defaults | **Verified** |
| S53 | Apple HIG JSON - Notifications | official docs JSON | https://developer.apple.com/tutorials/data/design/human-interface-guidelines/notifications.json | notification consent, concise/high-value notices, alerts for errors, avoid sensitive content | **Verified** |

## GitHub REST evidence

The following license facts were read through `gh api repos/<owner>/<repo>` and `gh api repos/<owner>/<repo>/license` on 2026-08-26:

- MIT: `microsoft/PowerToys`, `files-community/Files`, `microsoft/WinUI-Gallery`, `lepoco/wpfui`, `MaterialDesignInXAML/MaterialDesignInXamlToolkit`, `AvaloniaUI/Avalonia`, `microsoft/WPF-Samples`, `microsoft/microsoft-ui-xaml`, `microsoft/WindowsAppSDK-Samples`, `microsoft/CsWin32`.
- GPL-3.0: `rocksdanister/lively` - reference-only.
- `NOASSERTION`: `File-New-Project/EarTrumpet`; license text includes MIT terms plus excluded entities - flagged and not treated as reusable.

## Currency

- **Fast-moving:** WinUI/Windows App SDK release guidance, Apple notarization requirements, SmartScreen/signing services, Avalonia accessibility coverage, native UI automation tool recommendations.
- **Stable:** keyboard reachability, accessible name/role/state, platform HIG primacy, DPI testing, package signing as user-trust gate.
