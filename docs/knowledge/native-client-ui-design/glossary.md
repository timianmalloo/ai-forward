---
id: kb-native-client-ui-design-glossary
title: "Native client UI design — Glossary"
type: glossary
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, glossary, wpf, winui, avalonia, accessibility]
links:
  - { to: kb-native-client-ui-design, rel: refines }
review-by: "2026-11-24"
summary: >-
  Ubiquitous language for native desktop UI work: platform HIG, Fluent, WinUI, WPF, XAML resources, UI Automation, automation peers, keyboard focus, high DPI, AppWindow, MSIX, SmartScreen and notarization.
---

# Glossary — ubiquitous language

- **Accessibility tree** — the semantic tree exposed to assistive technologies, separate from pixels and usually separate from the visual tree. *(Verified: Windows UI Automation [S4], Avalonia accessibility [S16].)*
- **AppWindow** — Windows App SDK high-level abstraction over a top-level HWND, used to manage window size, position, title bar and presenter behavior. *(Verified: [S7].)*
- **AutomationPeer** — WPF/WinUI/Avalonia object that exposes a control's role, content, state and patterns to the platform accessibility API. *(Verified: [S5], [S16].)*
- **AutomationProperties** — XAML attached properties such as `Name`, `HelpText`, `LabeledBy`, `AutomationId`, heading/landmark/live settings that supply accessibility metadata. *(Verified: [S5], [S16].)*
- **DynamicResource** — WPF resource lookup that can update after initial load; use where theme/system changes must propagate. *(Inferred from WPF/XAML resource model; verify exact WPF behavior before code.)*
- **Fluent Design** — Microsoft’s design language for Windows app color, typography, iconography, motion, materials, layout and accessibility. *(Verified: [S1], [S2].)*
- **HighContrast** — Windows XAML theme dictionary for high-contrast mode; native apps must respect it rather than simulate only light/dark. *(Verified: [S12].)*
- **High DPI / per-monitor DPI** — ability for a desktop app to render at the correct physical size and crispness on displays with different scaling. WPF requires explicit per-monitor awareness and relayout/rerender for some scenarios. *(Verified: [S10], [S22].)*
- **Human Interface Guidelines (HIG)** — platform design guidance such as Apple HIG, GNOME HIG or KDE HIG; the authoritative platform-level UX contract. *(Verified for GNOME/KDE; Apple detailed content flagged.)*
- **MSIX** — Windows app package format; deployment packages must be signed and trusted on the target device. *(Verified: [S13].)*
- **Notarization** — Apple process for scanning and approving macOS software for distribution outside or alongside App Store paths. *(Flagged: official page fetched only title [S20].)*
- **ResourceDictionary** — XAML container for reusable resources such as colors, brushes, styles, templates and dimensions. Native token systems should compile here, not into scattered literals. *(Verified for XAML theme resources [S12]; Inferred pack mapping.)*
- **SmartScreen reputation** — Microsoft Defender SmartScreen trust signal based on publisher and file hash reputation; unsigned or unknown binaries can show warnings or be blocked. *(Verified: [S14].)*
- **ThemeResource** — Windows XAML markup extension that updates when the active theme changes, unlike `StaticResource`. *(Verified: [S12].)*
- **UI Automation (UIA)** — Microsoft accessibility framework through which assistive technologies and automation clients interact with desktop UI. *(Verified: [S4], [S5].)*
- **WinUI 3** — recommended native UI framework for new Windows desktop apps, delivered with the Windows App SDK. *(Verified: [S6].)*
- **WPF** — Windows Presentation Foundation, mature .NET desktop UI framework; still relevant for existing/line-of-business apps and WPF-specific controls/templates. *(Verified from WPF docs/samples [S5], [S22].)*
- **XAML** — markup language used by WPF, WinUI and Avalonia-like frameworks for UI trees, resources, styles and bindings. *(Verified by platform docs; general term.)*
