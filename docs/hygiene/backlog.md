---
id: hygiene-backlog
title: "Code-hygiene backlog"
type: doc
status: accepted
owner: "@timianmalloo"
tags: [hygiene, code-quality, dead-code, anti-patterns, HYG-A]
links:
  - { to: defect-classes, rel: relates-to }
  - { to: architecture, rel: relates-to }
review-by: "2026-11-30"
summary: >-
  Measured code-hygiene review of this repository's hand-authored source (Python, JS, PowerShell).
  Detects dead/commented-out code (HYG-A) and anti-pattern classes against the pack's coding
  guidelines, with LOC and % of source per class. The source is clean: no real commented-out code,
  no swallowed-exception anti-pattern; the largest actionable class is resource-lifecycle (26
  open() calls without a context manager). Read-only analysis; `fix` mode not yet run.
---

# Code-hygiene backlog

*Produced by `/code-hygiene review` on 2026-08-30. Read-only analysis — no code was changed.*
*Authority: `csharp-style-guide.md` §1.6, `agent-body-of-knowledge.md` Part VII/VIII,
`solution-selection-ladder.md` (L4 floors, L9 delete-list), `communication-and-task-discipline.md`
CT18a, and `docs/lessons/defect-classes.md` (HYG-A).*

## Scope & denominator

**Subject:** hand-authored **source code** — Python, JavaScript, PowerShell. Markdown (the pack's
product), JSON/HTML content, and generated data are out of scope for code hygiene (they have their
own docs-graph / freshness controls).

**Source roots analysed** (deduplicated): `pack/scripts/`, `pack/evals/`, `tools/`,
`tests/docs_explorer/`, `web/pack-index.js`, `playwright.config.js`.

**Excluded from the denominator and analysis** — with reasons:
- `docs/ai-forward-pack/scripts/**` — **generated copies** of `pack/scripts/` (`sync-pack.ps1`).
  Fixes land in `pack/`, never here; counting them would triple-count.
- `web/vendor/*.js` (react, react-dom, htm) — **third-party**, not our code.
- `docs/docs-index.js`, `docs/audit/audit-data.js`, `docs/portal/portal-data.js`,
  `docs/dreams/**`, `docs/backtest/**` — **derived/accumulated data**, never hand-edited.

**Denominator (measured, `git ls-files` + line count):**

| Language | Files | LOC |
|---|---:|---:|
| Python | 46 | 16,900 |
| JavaScript | 11 | 6,251 |
| PowerShell | 5 | 1,032 |
| **Total source** | **62** | **24,183** |

**Detectors used** (installed for this run): `ruff` 0.16.5, `vulture` 2.16, `pyflakes` 3.4.0 (Python).
JavaScript and PowerShell have **no analyzer wired** in this repo — see *Measurement gaps*.

---

## Aggregate — violations by class

Every count is **measured** by the named detector. `%` = violating LOC ÷ 24,183 source LOC.
Confidence: **Verified** = deterministic detector observed it; **Inferred** = heuristic / low-confidence
detector or no hard guideline threshold.

| # | Class | Guideline violated | Instances | Violating LOC | % of source | Severity | Detector · confidence |
|---|---|---|---:|---:|---:|---|---|
| 1 | **HYG-A** — unused import | BoK VII.3; HYG-A | 3 | 3 | 0.01% | Low | ruff `F401` · Verified |
| 2 | **HYG-A** — unused local / loop var | BoK VII; HYG-A | 3 | 3 | 0.01% | Low | ruff `B007` + vulture 100% · Verified |
| 3 | **HYG-A** — unreferenced function (candidate) | HYG-A | 2 | ~15 | 0.06% | Low | vulture 60% · **Inferred** (reserved-API risk) |
| 4 | **Resource lifecycle** — `open()` w/o context manager | BoK VII.3 (context managers for resources) | 26 | ~26 | 0.11% | **Medium** | ruff `SIM115` · Verified |
| 5 | **Robustness** — `subprocess.run` w/o `check=` | BoK VII (correctness) | 38 (~23 in source) | ~38 | 0.16% | Low–Med | ruff `PLW1510` · Verified |
| 6 | **Idiom** — suppressible `try/except/pass` | style (VII.3) | 18 | ~54 | 0.22% | Low (idiom) | ruff `SIM105` · Verified |
| 7 | **Exception chaining** — `raise` w/o `from` | BoK VII.3 | 2 | 2 | 0.01% | Low | ruff `B904` · Verified |
| 8 | **Trivial** — f-string without placeholder | — | 11 | 11 | 0.05% | Nit | ruff `F541` · Verified |
| 9 | **Complexity** — God-method / long-param-list | BoK VIII (no hard PY threshold) | 62 | not recorded¹ | — | Info | ruff `PLR0911/12/13/15/17` · Inferred |
| 10 | **Magic-value comparison** | primitive-obsession-adjacent | 42 | not recorded¹ | — | Info | ruff `PLR2004` · Inferred (noisy) |

¹ *Not recorded*: complexity/magic-value flags attach to whole methods/expressions, not a clean LOC
span; reporting a per-line figure would be a plausible wrong number, so it is left unrecorded (IO8).

**Totals (clear, actionable violations — classes 1–8):** **103 instances**, **~152 violating LOC** ≈
**0.63% of source**. Medium-or-higher severity (class 4 only): **26 instances ≈ 0.11%**.

**Headline:** the hand-authored source is **clean**. There is **no real commented-out code** and **no
swallowed-exception anti-pattern** (bare `except:` = 0). The single largest actionable clean-up is the
**resource-lifecycle** class — 26 `open()` calls that should use a `with` block.

---

## Itemised backlog

### Class 1 — HYG-A: unused import (`remove`)
| id | file:line | symbol | detector |
|---|---|---|---|
| HB-01 | `pack/scripts/dream.py:23` | `hashlib` | ruff F401 (autofixable) |
| HB-02 | `tools/build-pages-bundle.py:27` | `re` | ruff F401 (autofixable) |
| HB-03 | `tools/build-web-index.py:15` | `html` | ruff F401 (autofixable) |

### Class 2 — HYG-A: unused local / loop variable (`refactor` → prefix `_` or remove)
| id | file:line | symbol | detector |
|---|---|---|---|
| HB-04 | `pack/scripts/coord-core.py:678` | loop var `source_is_ours` | ruff B007 |
| HB-05 | `pack/scripts/coord-core.py:697` | loop var `lineno` | ruff B007 |
| HB-06 | `pack/scripts/coord-core.py:1015` | local `harness` | vulture 100% |

### Class 3 — HYG-A: unreferenced function, candidate (`accept-with-rationale` OR `remove` after human disposition)
| id | file:line | symbol | note |
|---|---|---|---|
| HB-07 | `pack/scripts/coord-core.py:993` | `detect_harness` | in the harness-adapter surface; may be reserved API. **Inferred** — needs human disposition, not auto-removal. |
| HB-08 | `pack/scripts/coord-core.py:1237` | `_role_token` | private helper, currently unreferenced. **Inferred** — verify against intended API before removal. |

### Class 4 — Resource lifecycle: `open()` without a context manager (`refactor` → `with open(...)`)
26 instances (BoK VII.3). Distribution:

| file | count | lines |
|---|---:|---|
| `pack/scripts/graphify-setup.py` | 7 | 165, 228, 275, 341, 491, 566, 594 |
| `pack/scripts/dream.py` | 4 | 107, 448, 460, 534 |
| `pack/scripts/apply-learnings.py` | 3 | 46, 83, 263 |
| `pack/scripts/obsidian-setup.py` | 3 | 153, 173, 602 |
| `tools/new-capability.py` | 3 | 44, 51, 63 |
| `pack/scripts/foundation-check.py` | 2 | (2 sites) |
| `tools/check-consistency.py` | 2 | 819, 827 |
| `pack/scripts/design-lint.py` | 1 | 82 |
| `pack/scripts/scrub.py` | 1 | 114 |

### Classes 5–8 (lower severity — aggregate; itemise in `fix` if approved)
- **HB-SUBPROCESS** — `PLW1510` ×38 (~23 in `pack/scripts/` + `tools/`; ~15 in tests are *deliberate*,
  they inspect `returncode` manually → likely `accept-with-rationale`).
- **HB-SUPPRESS** — `SIM105` ×18 — narrow, intentional suppressions (`json.JSONDecodeError`, `OSError`,
  `ProcessLookupError`). Idiom nicety (`contextlib.suppress`), **not** a swallowed-exception bug.
- **HB-CHAIN** — `B904` ×2 — add `from err` / `from None`.
- **HB-FSTRING** — `F541` ×11 — drop the `f` prefix (autofixable).

### Classes 9–10 (informational — no `fix` disposition)
God-method / long-param-list (62) and magic-value comparisons (42) are **signals**, not guideline
violations (the pack sets no hard Python thresholds). Concentrated in the large scripts
(`coord-core.py`, `docs-graph.py`, `audit-log.py`). Left as informational; not scheduled for removal.

---

## Explicitly excluded (disconfirmed — NOT violations)

The Rigor Protocol Stage-4 gate ruled these out. A finding is a candidate, not a verdict.

**False positives — not commented-out code (ERA001 ×3):** all three are *documentation*, not rot:
- `pack/scripts/coord-core.py:892` — a section banner + a genuine *why* block explaining the two
  hook envelopes, with **illustrative JSON literals** that trip the eradicate heuristic.
- `pack/scripts/dream.py:60` — a `# ----- scrub & taint` **section divider**.
- `tools/build-docs-portal.py:140` — a `# ----- architecture` **section divider**.

**Framework / API — not dead code (vulture 60–60%):** removing any would break behaviour →
Security/SRE exclusion:
- `pack/scripts/docs-graph.py:550/555/568` — `handle_starttag` / `handle_endtag` / `handle_data`
  are **`html.parser.HTMLParser` overrides**, called by the framework.
- `pack/scripts/bounded_process.py:110/115/116` — `LimitFlags` / `ActiveProcessLimit` /
  `JobMemoryLimit` are **`ctypes.Structure` fields** consumed by the Windows Job Object API by
  memory layout.
- `coord-core.py` `hook_decision_of` / `hook_response_is_valid` — **used by
  `tests/docs_explorer/test_harness_conformance.py`** (verified references), not dead.

**L4 floors — never a hygiene target** (`solution-selection-ladder.md` L4): the secret/PII-scanning
regexes in `scrub.py`, input validation, fail-closed defaults, and error handling that prevents data
loss are excluded by policy even where a metric flags them.

**Intentional markers:** no `simplify:` / `assume:` markers were mis-flagged; they remain tracked
intent (L5, NG4), not rot.

---

## Measurement gaps (honest — not guessed)

- **PowerShell** (1,032 LOC, 5 files): **PSScriptAnalyzer is not installed** and could not be run
  offline in this environment → dead-code / anti-pattern detection for PowerShell is **not recorded**.
  Any figure would be an Inferred guess; none is given.
- **JavaScript** (6,251 LOC, 11 source files): no `eslint` / `knip` / `ts-prune` wired in this repo.
  A commented-out-code heuristic returned **0** hits (Inferred-clean), but unused-export / dead-code
  detection for JS is **not recorded** — a deterministic pass would need one of those tools installed.
- To close these gaps, `fix` (or a future run) should wire `knip`/ESLint for JS and PSScriptAnalyzer
  for PowerShell before claiming those languages Verified-clean.

---

## Next

- **Triage** this backlog (human). The obvious green-light items are the **8 autofixable** ruff hits
  (F401 ×3, F541 ×11 — wait, F401 counts as 3) and the **26 SIM115** resource-lifecycle refactors.
- Run **`/code-hygiene fix <class|scope>`** on approved classes — it will build a TDD-guarded,
  git-labelled (`Hygiene-Class` / `Hygiene-Item`) phased plan (each removal proven behaviour-preserving,
  independently revertible) and **stop for approval before executing**.
- Note the pack rule: all fixes land in **`pack/`** (source of truth), then `tools/sync-pack.ps1`
  regenerates `.claude/` and `docs/`, then `tools/verify-bundle.ps1` before commit.
