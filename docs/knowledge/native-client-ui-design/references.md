---
id: kb-native-client-ui-design-references
title: "Native client UI design — References"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, standards, references, fluent, hig, accessibility, packaging]
links:
  - { to: kb-native-client-ui-design, rel: refines }
review-by: "2026-11-24"
summary: >-
  Standards, HIGs, platform documentation and tools that define the native-client UI contract for Windows, macOS, GNOME/KDE and cross-platform XAML applications.
---

# Reference information

## Platform design systems and HIGs

- **Windows app design overview / guidelines** — primary Windows app design hub; covers Fluent, design principles, layout, navigation, input, typography, motion, color, materials and tools. *(Verified, [S1], [S2].)*
- **Fluent 2 accessibility** — Microsoft design-system accessibility guidance; states Fluent components meet or surpass WCAG 2.1 AA and gives structure, keyboard, color, responsive layout and text guidance. *(Verified, [S3].)*
- **Apple Human Interface Guidelines / Designing for macOS** — authoritative macOS design source; JSON endpoints verified specific rules for Mac display/input/window/menu/keyboard/accessibility/notification behavior. Use Apple pages directly before quoting more than the summarized claims here. *(Verified for included claims, [S18], [S48]-[S53].)*
- **GNOME HIG** — primary GNOME design documentation for GTK 4 and Libadwaita; covers principles, resources, guidelines, patterns and reference. *(Verified, [S21].)*
- **KDE HIG** — KDE design philosophy, workflows/patterns, UI conventions and platform integration. *(Verified, [S22].)*

## Windows implementation contracts

- **WinUI 3** — recommended native UI framework for new Windows desktop apps, with Fluent controls/styles, high-DPI rendering, and Windows App SDK access. *(Verified, [S6].)*
- **Windows App SDK windowing / AppWindow** — high-level HWND abstraction; manages top-level window size, position, title/icon/title-bar and presenters across supported frameworks. *(Verified, [S7].)*
- **Windows input and interactions** — WinUI can access most WinRT input APIs in desktop apps, with some APIs requiring package identity and some remaining UWP-only. *(Verified, [S9].)*
- **XAML theme resources** — Light, Dark and HighContrast dictionaries; `{ThemeResource}` updates at runtime on theme changes while `{StaticResource}` does not. *(Verified, [S12].)*
- **Windows color / typography / icons** — Fluent color, Segoe UI Variable, icon guidance and use of common controls/system design resources. *(Verified, [S37]-[S39].)*

## Accessibility and verification tools

- **Windows accessibility overview** — treat accessibility as a core quality requirement; support keyboard, screen readers, customization and UI Automation. *(Verified, [S4].)*
- **WPF UI Automation accessibility best practices** — custom controls require `AutomationPeer`; WPF controls need `AutomationProperties.Name`, `HelpText` and descriptive titles. *(Verified, [S5].)*
- **Keyboard accessibility** — keyboard is primary; focus traversal and tab behavior must be explicitly validated, especially grids/tables. *(Verified, [S8].)*
- **Accessibility Insights for Windows** — Live Inspect, FastPass automated checks, tab stops test, pattern invocation, event recording and contrast checker. *(Verified, [S11].)*
- **Avalonia accessibility/focus** — automation peers map to platform accessibility APIs; `AutomationProperties` and focus navigation are first-class. *(Verified, [S16], [S17].)*

## High-DPI, windowing and distribution

- **WPF per-monitor DPI** — manifest/config and relayout/rerender for physical size, fonts, images, hosted HWND/WinForms controls, `RenderTargetBitmap` and text formatting. *(Verified, [S10], [S22].)*
- **WPF layout/control performance** — layout passes are mathematically intensive; UI virtualization is required for large item sets; native performance proof must include layout churn and virtualization. *(Verified, [S43], [S44].)*
- **MSIX package signing** — packages must be signed with a valid code-signing certificate trusted on the device; production signing options include Microsoft-managed Trusted Signing/Azure Artifact Signing, OV certificate or Store signing. *(Verified, [S13].)*
- **SmartScreen reputation** — evaluates publisher and file hash reputation; unsigned/self-signed files produce warnings and can be blocked by enterprise policy. *(Verified, [S14].)*
- **Apple notarization** — official Apple distribution trust gate; confirm details directly before macOS release. *(Flagged on detailed extraction, [S20].)*

## Open-source reference corpus

The verified permissive corpus is listed in `comparables.md`. Treat it as:

1. **Pattern evidence** — how a shipped/native control or shell works.
2. **Terminology evidence** — how native teams name surfaces (AppWindow, NavigationView, ResourceDictionary, AutomationPeer).
3. **Anti-pattern evidence** — where web abstractions fail or where native integration is required.
