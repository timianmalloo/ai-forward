---
id: proof-native-app-ui-skill-extension
title: "Proof Pack — Native app UI skill extension"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: "native-client-ui"
tags: [native-ui, proof-pack, ui-design, visualize, xaml-token-lint]
links:
  - { to: design-native-app-ui-skill-extension, rel: tested-by }
  - { to: spec-native-app-ui-skill-extension, rel: tested-by }
review-by: "2027-02-21"
summary: >-
  Proof pack for implementing the native app UI skill extension: native UI triggers and guardrails, the reusable native UI proof-pack template, XAML token linter, native archetype rows, generated-interface rejection, and license-aware exemplars.
---

# Proof Pack: Native app UI skill extension

- **Change:** `implement/native-app-ui-skills`
- **Spec / design:** `docs/specs/native-app-ui-skill-extension.md` · `docs/design/native-app-ui-skill-extension.md`
- **Tier:** T2
- **Author / date:** Copilot CLI / 2026-08-26

## Claims & evidence

| Claim | Evidence | Oracle / why it can fail | Red observed | Confidence | Residual risk |
|---|---|---|---|---|---|
| `/ui-design` treats WPF/WinUI/Avalonia/Blazor Hybrid as native-client surfaces requiring native proof, not web-only evidence. | `pack/commands/ui-design/SKILL.md`; `tests.docs_explorer.test_native_ui_extension.NativeUiContractTextTests.test_ui_design_native_trigger_contract_is_behavioral_not_visual_only`; focused and full unittest runs. | Test fails if the skill omits native proof pack, WPF/WinUI/Avalonia/Blazor Hybrid, HTML mockup limitation, or Accessibility Insights evidence. | Yes — initial focused run failed before implementation because the text was absent. | **Verified** | Future wording could weaken semantics without removing substrings; A6 eval cases cover behavior at skill-run level. |
| `/visualize` supports native content assets/personas/motion and rejects generated native interfaces. | `pack/commands/visualize/SKILL.md`; native contract text test; `pack/evals/cases/visualize-native-01.json`. | Test/eval fails if native asset wording or generated-interface rejection disappears. | Yes — initial focused run failed before implementation because native wording was absent. | **Verified** | Eval case still requires a future skill run to prove generated artifact behavior end-to-end. |
| `native-ui-proof-pack.template.md` provides reusable native proof rows with falsifying conditions and evidence fields. | `pack/templates/native-ui-proof-pack.template.md`; `test_native_proof_pack_template_has_required_columns_and_frameworks`. | Test fails if required columns or WPF/WinUI/Avalonia/Blazor Hybrid/signing rows disappear. | Yes — first green attempt failed because title-case headers did not satisfy the schema check. | **Verified** | Template cannot prove actual native app behavior; it defines the evidence contract. |
| `xaml-token-lint.py` deterministically flags raw XAML colors, brushes and dimensions while staying inside the declared root. | `pack/scripts/xaml-token-lint.py`; `XamlTokenLintTests`; focused and full unittest runs. | Tests fail for raw double/single-quoted colors, named colors, 4-digit ARGB, raw dimensions, malformed markup crash, or scanning outside root. | Yes — initial test run failed before script existed; implementation review found single-quote/named-color/root traversal misses; regressions were added and fixed. | **Verified** | First slice intentionally defers semantic `StaticResource` vs `DynamicResource` inference and automation-name rules. |
| Native archetype rows are valid catalog rows. | `pack/knowledge/ui-archetype-catalog.md`; `test_native_archetype_rows_are_catalog_shaped`; Patterns Expert re-review. | Test/review fails if rows lack signatures/descriptions/descriptors or invalid quoted `x-` facets. | Yes — Patterns Expert blocked narrative-only/invalid custom facets; rows were revised. | **Verified** | No parser-level grammar test exists yet beyond text and reviewer checks. |
| Native exemplar policy is license-aware. | `pack/knowledge/ui-design-craft.md`; `test_exemplar_policy_labels_reference_only_repos`. | Test fails if permissive references, GPL-3.0, `NOASSERTION`, Flagged/non-standard, or reference-only labels disappear. | Yes — initial focused run failed because table did not exist. | **Verified** | Legal interpretation remains not legal advice; flagged rows require legal review before reuse. |

## Boundary set coverage

| Boundary | Covered by |
|---|---|
| Empty native declaration | `/ui-design` text + `ui-design-native-01` eval expectation. |
| Malformed/generated native interface request | `/visualize` text + `visualize-native-01` eval expectation. |
| Hostile privacy/customer screenshot | `/visualize` text + eval expectation + security review. |
| Wide/malformed XAML input | `test_malformed_and_large_markup_do_not_crash`; root-containment test. |
| Raw XAML token values | raw color/brush/dimension tests. |
| Cross-layer Blazor Hybrid proof | native proof-pack template and `/ui-design` text. |

## Failure modes addressed

| Failure mode | Handled in code/docs by | Proven by | Accepted residual risk |
|---|---|---|---|
| Web-shaped native review passes | `/ui-design` UI-T4 and proof-pack template | Text tests + `ui-design-native-01` eval case | Future skill execution still needs run-level eval. |
| Screenshot accepted as accessibility proof | `/ui-design` native proof wording + template | Text tests and Test Architect review | Native proof tooling selection remains per-project. |
| Generated native screen used as UI | `/visualize` native input rule | Text tests + `visualize-native-01` eval case | None for this slice. |
| Token docs exist but XAML uses raw values | `xaml-token-lint.py` | Linter unit tests | Semantic resource inference deferred. |
| Native proof rows copied inconsistently | reusable template | Template tests | None for first slice. |
| GPL/non-standard repo reused as code | exemplar table | Text tests | Legal approval still needed for flagged repos. |

## Threats addressed

| Boundary / threat | Disposition | Enforcing artifact | Negative security test | Result |
|---|---|---|---|---|
| Generated asset input → provider / personal data egress | mitigate | `/visualize` native wording + VA5a | eval/text cases block customer screenshot and real UI generation | red→green |
| Exemplar table → unsafe reuse | mitigate | DX4a exemplar table | test requires GPL/reference-only and NOASSERTION/Flagged labels | red→green |
| Native proof template → proof without evidence | mitigate | proof-pack template schema | test requires evidence/oracle/red observed/confidence/residual risk fields | red→green |
| XAML linter filesystem input → path escape/snippet disclosure | mitigate | root containment in `xaml-token-lint.py` | symlink/junction/outside-root tests | red→green after review finding |

## Privacy findings addressed

| Data flow / finding | Disposition | Enforcing artifact | Privacy test | Result |
|---|---|---|---|---|
| User/customer image or screenshot proposed for native asset generation | mitigate | `/visualize` native wording and `ui-visual-assets.md` VA5a/VA9 | `visualize-native-01` requires customer screenshot rejection | planned eval + text check |

## Testing Strategy directives applied

| Trigger | Directive | Evidence |
|---|---|---|
| T1 deterministic linter logic | D1 | `XamlTokenLintTests` |
| T2 wide/malformed XAML scanner input | D2 | malformed/large/symlink fixture tests |
| T3 new script/template/docs graph surfaces | D3 | `docs-graph.py validate`; deployed script help test |
| T7 JSON output | D6 | linter JSON tests |
| T14 skill/prompt changes | A6 | `ui-design-native-01.json`, `visualize-native-01.json`, native text regression tests |

## Verification commands

```powershell
python -m unittest tests.docs_explorer.test_native_ui_extension tests.docs_explorer.test_deployed_scripts
python -m unittest discover -s tests\docs_explorer -p 'test_*.py'
python docs\ai-forward-pack\scripts\docs-graph.py derive
python docs\ai-forward-pack\scripts\docs-graph.py validate
python docs\ai-forward-pack\scripts\audit-log.py verify
```

## Flagged risks / residual unknowns

- Exact CI-friendly WPF/WinUI UI automation runner remains deferred to future design/project implementation.
- Apple notarization details still require direct recheck before macOS release PASS.
- XAML linter semantic resource inference and automation-name rules are deliberately deferred until fixtures prove need.

## Status & next action

| | |
|---|---|
| **Completed** | Native UI skill extension implemented in pack source, generated surfaces synced, tests and graph/audit validation passed. |
| **Remaining** | Commit this implementation and later consider richer native UI automation tooling. |
| **Best next action** | Pre-merge review, then commit. |

## Gate record

`GATE implement · 2026-08-26 · reviewers: Python Developer, Security & Identity Architect, Test Architect · criteria met: linter hardened for single quotes, named colors, ARGB and root containment; proof pack attached; A6 eval cases added; focused/full tests pass · verdict: PASS-WITH-CONDITIONS · vetoes→resolution: initial Python/Security/Test blockers fixed; residual automation-tool choice deferred by design.`
