---
id: kb-native-client-ui-design-comparables
title: "Native client UI design — Comparable repositories"
type: knowledge
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, exemplars, repositories, mit, wpf, winui, avalonia]
links:
  - { to: kb-native-client-ui-design, rel: refines }
review-by: "2026-11-24"
summary: >-
  Permissively licensed public repositories and reference apps suitable for native-client UI review and pattern extraction, plus flagged reference-only repos whose licenses are non-standard or copyleft.
---

# Comparable solutions and public repositories

**License rule used here:** a repository is "amenable" for pack research when its GitHub REST license metadata or license file reports MIT/Apache/BSD-like terms. Even then, use it for **pattern review and inspiration**, not visual cloning. Product identity, trademarks, screenshots and assets are separate rights.

## Suitable permissive references

| Repository | Stack / framing | What it can teach | License posture | Confidence |
|---|---|---|---|---|
| `microsoft/WinUI-Gallery` | WinUI 3 / Windows App SDK control gallery | Interactive control samples, adaptive UI, Fluent/WinUI code snippets, design and accessibility companion pages | MIT via GitHub REST and license file | **Verified** [S23], [S27] |
| `microsoft/microsoft-ui-xaml` | WinUI framework source | Native control implementation patterns, visual states, resource dictionaries, API/issues for WinUI behavior | MIT via GitHub REST | **Verified** [S29] |
| `microsoft/WindowsAppSDK-Samples` | Windows App SDK samples | App lifecycle, activation, instancing, background tasks, Mica, text rendering, islands, installer/unpackaged scenarios | MIT via GitHub REST | **Verified** [S30], [S34] |
| `microsoft/WPF-Samples` | WPF samples | Per-monitor DPI, controls, data binding, accessibility-adjacent WPF implementation examples | MIT via GitHub REST/license file | **Verified** [S22], [S31] |
| `microsoft/PowerToys` | Large Windows utility suite, WinUI modernization | Multi-utility settings shell, Command Palette, tray/background utilities, installer/update/telemetry tradeoffs, power-user density | MIT via GitHub REST/license file | **Verified** [S24], [S26] |
| `files-community/Files` | Modern Windows file manager | NavigationView-like file manager shell, tabs, multitasking, tags, deep Windows integration, Store/classic installer posture | MIT via GitHub REST/license file | **Verified** [S25], [S28] |
| `lepoco/wpfui` | WPF Fluent control/theme library | Fluent-like WPF theming, navigation, dialogs/snackbars, theme resources, Store gallery pattern | MIT via GitHub REST/license file | **Verified** [S32] |
| `MaterialDesignInXAML/MaterialDesignInXamlToolkit` | WPF Material Design theme/control library | ResourceDictionary-based design systems, runtime palette configuration, WPF dialog/card/transitions, theme package structure | MIT via GitHub REST/license file | **Verified** [S33] |
| `AvaloniaUI/Avalonia` | Cross-platform XAML framework | Cross-platform styling, automation peers, focus, themes, native-platform differences under a common XAML model | MIT via GitHub REST/license file | **Verified** [S15]-[S17], [S35] |
| `microsoft/CsWin32` | Win32 P/Invoke source generator | Safe Windows API integration for file associations, windowing, shell and OS integration when WinUI/WPF abstractions do not cover a scenario | MIT via GitHub REST | **Verified** [S36] |

## Reference-only or flagged

| Repository | Why it is interesting | Why it is not an amenable reuse source | Confidence |
|---|---|---|---|
| `File-New-Project/EarTrumpet` | High-quality Windows tray/audio UX; small focused native utility | GitHub reports `NOASSERTION`; license text contains MIT plus named excluded entities. That is non-standard and needs legal review before reuse. | **Verified / Flagged** |
| `rocksdanister/lively` | WinUI 3 app with Store-style native UX around animated wallpapers | GPL-3.0 license; safe for visual/product study, not for copying into this pack or permissive downstream templates. | **Verified** |

## Pattern implications

1. **Control galleries are exemplars and fixtures.** WinUI Gallery, WPF UI Gallery and MaterialDesignInXaml demos should seed native UI review prompts because they show controls in working native runtime state, not static screenshots.
2. **Settings shells and utilities are the native analog of web dashboards.** PowerToys and Files show the native pattern the pack should study for Windows: left navigation + content pane, command palette/search, high-density settings, file-system/task-specific OS integrations.
3. **Style libraries teach token translation.** WPF UI, MaterialDesignInXaml and Avalonia show how design languages become resource dictionaries, merged dictionaries, styles and control themes.
4. **Sample repos teach proof seams.** WPF-Samples/WindowsAppSDK-Samples are better for DPI/windowing/lifecycle evidence than aesthetic review.
