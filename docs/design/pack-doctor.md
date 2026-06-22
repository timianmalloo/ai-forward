---
id: design-pack-doctor
title: "Design — installed-repo doctor (suggestion 2)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [doctor, health, install, tooling]
links:
  - { to: kb-pack-evolution, rel: implements }
review-by: "2026-12-11"
summary: >-
  A deployable, stdlib-only pack-doctor.py that reports the INSTALL health of a target repo
  (revision, both tool surfaces, managed-block integrity, graph health) as PASS/WARN/FAIL with
  fixes and a nonzero exit — distinct from the source-only consistency gate.
---

# Design: installed-repo doctor (suggestion 2)

- **Status:** Accepted
- **Spec / architecture:** `docs/knowledge/pack-evolution/` · `docs/architecture.md`
- **Delivery phase / vertical slice:** Pack-evolution slice 2. Deployable — lands in installed repos via the deployment map. The CLI's `doctor` subcommand (design 1) is its source-repo front.
- **Author(s) / date:** SRE + Domain Researcher + Simplifier, 2026-06-14

## Responsibility
Report the **install health** of the repo it runs in: is the pack installed, at what **revision**, are **both tool surfaces** present (`.claude/` and `.github/{instructions,prompts,agents}`), are the **managed blocks** intact in `CLAUDE.md`/`AGENTS.md`, and is the **knowledge graph** healthy (schema-valid frontmatter, no dangling links, not stale). Output one PASS/WARN/FAIL line per check with a suggested fix; exit nonzero if any FAIL. It is explicitly **not** the source-consistency gate (`check-consistency.py` validates `pack/` == docs in the *source* repo; the doctor validates an *installed* repo that has **no `pack/`**). Per knowledge base headline #2, it **composes** `docs-graph.py validate|freshness` for the graph half rather than reinventing it.

## Contracts
- **Exposed:** `python pack-doctor.py [--json] [--root <repo>]`. Human output by default (aligned/coloured-optional PASS/WARN/FAIL lines + a summary); `--json` emits a machine record `{checks:[{name,status,detail,fix}], summary, exit}`. **Exit:** 0 = all PASS/WARN; 1 = any FAIL.
- **Consumed:**
  - `docs/ai-forward-pack/INSTALL.md` frontmatter → installed `revision`. *(Verified — exists in every install)*
  - Filesystem presence of `.claude/knowledge|skills|agents`, `.github/instructions|prompts|agents`. *(Verified — deployment map)*
  - `CLAUDE.md`/`AGENTS.md` `AI-FORWARD-PACK:BEGIN/END` markers. *(Verified — managed-blocks convention)*
  - The graph bundle: `python docs/ai-forward-pack/scripts/docs-graph.py validate` and `… freshness` (best-effort; skipped-with-WARN if the bundle or `docs/` is absent). *(Verified — docs-graph.py ships in every install)*

## Patterns
- **Doctor / diagnostic** (npm/brew/flutter/`squad doctor`) — the established "inspect install, PASS/WARN/FAIL, suggest fix, nonzero on fail" shape. Named in code `# Pattern: Doctor diagnostic`.
- **Composition over reinvention** — the graph checks *shell out to* `docs-graph.py` (V18: graph mechanics go through the bundle), never re-parse the graph. Rejected: re-implementing frontmatter validation in the doctor (would duplicate `docs-graph.py` and drift).
- **Check registry** — a list of `(name, fn) → Result(status, detail, fix)`; the runner aggregates. Simple, extensible, testable per-check.

## Data shapes
`Result = {name: str, status: "PASS"|"WARN"|"FAIL", detail: str, fix: str}`. The `--json` document is `{"checks": [Result...], "summary": {"pass":n,"warn":n,"fail":n}, "revision": "<n|unknown>"}`.

## Error & concurrency model
Read-only, synchronous, no state, idempotent. A missing optional input (e.g. no `docs/`) is a **WARN with a fix**, not a crash. A subprocess failure invoking `docs-graph.py` is caught and reported as a WARN ("graph tool unavailable"), never propagated as a doctor crash.

## Failure-mode analysis

| Failure mode | From which choice | Disposition | How addressed | Detection | Test |
|---|---|---|---|---|---|
| not an installed repo (no `docs/ai-forward-pack/INSTALL.md`) | revision check | detect + guide | single clear FAIL: "pack not installed — run /addpacktorepo"; exit 1 | the FAIL line | `doctor_no_install_fails_clearly` |
| only one tool surface present | surface check | detect | FAIL naming the missing surface + "re-run sync/updatepack" | per-surface line | `doctor_missing_github_surface_fails` |
| managed block missing/duplicated in CLAUDE/AGENTS | marker scan | detect | FAIL "managed block absent in AGENTS.md — run /updatepack" | marker count != 1 | `doctor_missing_block_fails` |
| `docs/` absent or graph empty | graph check | degrade (WARN) | WARN "no knowledge graph yet — first skill run creates it" | graph subprocess result | `doctor_no_graph_warns_not_fails` |
| `docs-graph.py` errors/absent | composition | degrade (WARN) | catch; WARN "graph tool unavailable"; do not crash | caught exception | `doctor_graph_tool_missing_warns` |
| stale graph (review-by past) | freshness | detect (WARN) | surface `freshness` findings as WARN with the stale ids | freshness exit/JSON | `doctor_stale_graph_warns` |
| INSTALL.md present but no `revision:` | parse | detect | WARN "revision unreadable" + show raw | regex miss | `doctor_unparseable_revision_warns` |

## Adversarial analysis (STRIDE-lite)
No trust boundary in the security sense: a **read-only** local diagnostic over files in the repo it is run on, no network, no privilege change, no untrusted external input (the "input" is the repo's own committed files). It executes only the pack's own `docs-graph.py` (by absolute resolved path, argv-list, no `shell=True`). Explicit negative: *no secret handling, no remote call, no write, no privilege boundary.* (Information disclosure: the doctor prints file *presence and counts*, never file *contents*, so it cannot leak secrets — verified by the no-content-echo test.)

## Privacy analysis (LINDDUN-lite)
This component touches no personal data (verified — it reads frontmatter metadata, file presence, and marker counts; it never reads or emits document *bodies* or user content).

## UI & interaction design
**Medium:** CLI. **Platform guidelines:** CLI conventions — status visibility, exit codes, the `doctor` genre's aligned check list. **Key screen:** the check list, one line per check —
```
AI-Forward doctor — install health

  PASS  pack installed            revision 7 (2026.06.14.5)
  PASS  Claude Code surface       .claude/{knowledge,skills,agents} present
  FAIL  Copilot surface           .github/prompts missing
        → fix: run /updatepack (or pwsh tools/sync-pack.ps1 in the source repo)
  PASS  CLAUDE.md managed block    intact (1 block)
  WARN  knowledge graph            2 stale nodes (review-by past)
        → fix: review and bump review-by, then docs-graph.py derive

  1 FAIL · 1 WARN · 3 PASS
```
**States:** all-pass (exit 0, green summary) · warn-only (exit 0, yellow) · any-fail (exit 1, red) · not-installed (single FAIL + guidance). **Copy (real):** the strings above. **Accessibility:** status is in the **word** (PASS/WARN/FAIL), never colour alone (colour is optional decoration — U16 "no info by colour alone"); plain ASCII; `--json` for machine/AT consumption. **Perf:** sub-second (filesystem stats + one subprocess).

## Telemetry
Proportionate: the exit code and the per-check lines *are* the telemetry (it is a diagnostic, the output is the signal). `--json` is the structured form for CI. No spans/metrics (no service). *(Recorded as proportionate per Observability Standard §0.)*

## Test plan
Triggers: **T1** (check logic) → **D1**; the graph composition is a boundary → **D7** paired with a **real** `docs-graph.py` run (not a mock) on a seeded fixture; **D0** throughout. Eval case `pack-doctor`: seed a minimal fake install (INSTALL.md with `revision: N`, the two surface dirs, a CLAUDE.md with markers) → `cmd-exit 0`; then a broken fixture (missing `.github/prompts`) → `cmd-exit 1`. Every failure-mode row above is a negative/error-path test. No-content-echo test (security): a file containing a fake secret is never echoed by the doctor.

## Conformance notes
Stdlib-only (no third-party import). **Counts impact:** adds `pack/scripts/pack-doctor.py` → the pack `scripts` count goes 2→3 (then design 4 adds `scrub.py` → the consistency gate and INSTALL `counts.scripts` must reflect the final number). Deploys via the existing `pack/scripts/* → docs/ai-forward-pack/scripts/*` map (no map change needed). V18 honored (graph mechanics via the bundle).

## Flagged risks & residual unknowns
- Doctor false confidence (knowledge base failure mode) — mitigated by composing `docs-graph.py validate|freshness` rather than mere `Test-Path`; residual: checks are only as good as the deployment map they encode (kept in sync because the same map drives `sync-pack.ps1`).

## Status & next action
| | |
|---|---|
| **Completed** | installed-repo doctor design — **implemented in revision 8** (`pack/scripts/pack-doctor.py`; commit 2fa8bce) |
| **Remaining** | none — all four pack-evolution designs delivered in revision 8; `BUNDLE CONSISTENT` |
| **Best next action** | none outstanding — doctor shipped & deployed via the `pack/scripts/* → docs/ai-forward-pack/scripts/*` map |

## Gate record
`GATE design · 2026-06-14 · SRE + Simplifier + Security + Test Architect · criteria met: composes docs-graph.py (no reinvention), read-only (no trust boundary), every check has a test, counts impact recorded · verdict: PASS · vetoes→resolution: SRE confirmed every failure mode is detectable + degrades not crashes; Security confirmed no-content-echo; Test Architect confirmed the real-graph D7 pairing · author did not self-clear`

---
**Handoff:** → `/implement` (via `/extendaibundle`).
