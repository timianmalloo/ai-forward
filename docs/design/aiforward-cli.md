---
id: design-aiforward-cli
title: "Design — aiforward CLI (suggestion 1)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [cli, tooling, dx]
links:
  - { to: kb-pack-evolution, rel: implements }
review-by: "2026-12-11"
summary: >-
  A single stdlib-only Python developer CLI (tools/aiforward.py) that is a thin Façade dispatcher
  over the pack's existing scripts (sync, verify, check, new, doctor, graph, scrub) — one
  memorable entry point with --help, no new runtime dependency.
---

# Design: aiforward CLI (suggestion 1)

- **Status:** Accepted
- **Spec / architecture:** `docs/knowledge/pack-evolution/` · `docs/architecture.md`
- **Delivery phase / vertical slice:** Pack-evolution slice 1 (the entry point the other three slices hang off — doctor/scrub subcommands are mock-substitutable until those scripts exist).
- **Author(s) / date:** Domain Researcher + Patterns Expert + Simplifier, 2026-06-14

## Responsibility
A single, memorable developer entry point — `python tools/aiforward.py <command>` — that **dispatches** to the pack's existing scripts and surfaces them under one `--help`. It is a **Façade**, not new logic: every subcommand shells out to a script that already owns the behavior. It is explicitly **not** a reimplementation of sync/verify/graph, **not** a daemon or service, **not** deployed into target repos (it is a *source-repo developer* convenience; the deployable health/scrub scripts are separate — designs 2 & 4). Per the knowledge base headline #1, it is **stdlib-only Python**, not npm/pipx/binary, to preserve the dependency-free install.

## Contracts
- **Exposed:** `aiforward <command> [args...]`. Commands and their delegation:
  | Command | Delegates to | Audience |
  |---|---|---|
  | `verify` | `pwsh tools/verify-bundle.ps1` | dev |
  | `sync` | `pwsh tools/sync-pack.ps1` | dev |
  | `check` | `python tools/check-consistency.py` | dev |
  | `new` | `python tools/new-capability.py …` | dev |
  | `doctor` | `python <scripts>/pack-doctor.py …` (design 2) | dev + consumer |
  | `graph` | `python <scripts>/docs-graph.py <derive|validate|freshness|…>` | dev + consumer |
  | `scrub` | `python <scripts>/scrub.py …` (design 4) | dev + consumer |
  - **Guarantees:** the subcommand's **exit code is propagated** unchanged (so `aiforward verify` is CI-usable exactly like `verify-bundle.ps1`); unknown command → usage + nonzero; `--help` / no args → the command table.
- **Consumed:** the sibling scripts above (all pack-internal, Verified to exist — `tools/*.ps1`, `tools/*.py`, and the `pack/scripts/` + `docs/ai-forward-pack/scripts/` bundle). `pwsh` for the two PowerShell commands; `python3` for the rest. *(Verified — repo files)*

## Patterns
- **Façade (GoF)** — one simple interface over the set of scripts. *Justified:* the scripts are the subsystem; the CLI is a unifying front, adding no behavior. The Simplifier passes it precisely *because* it holds no logic.
- **Command dispatch table** — a `dict[str, spec]` mapping name → the target invocation. Named so it appears in code as `# Pattern: Command dispatch`. Rejected alternative: `argparse` subparsers per command — unnecessary since each command just forwards `argv` to a child process; a flat table is simpler (Simplifier).
- **Graph-script resolution** — `graph`/`doctor`/`scrub` resolve their target from the first existing of `pack/scripts/` (source repo) or `docs/ai-forward-pack/scripts/` (installed repo), so the CLI works in both contexts.

## Data shapes
None persisted. In-memory: the command table; `argv` passthrough; the resolved interpreter (`pwsh` vs `python`).

## Error & concurrency model
Synchronous, single child process per invocation; no concurrency, no state, idempotent (re-running repeats the child). Cancellation = the child's own (Ctrl-C propagates). The CLI never swallows a child's exit code.

## Failure-mode analysis

| Failure mode | From which choice | Disposition | How addressed | Detection | Test |
|---|---|---|---|---|---|
| `pwsh` absent (for `verify`/`sync`) | shelling to PowerShell | detect + degrade | catch `FileNotFoundError`; print the exact manual command + "install PowerShell 7"; exit 2 | stderr message, exit 2 | `cli_pwsh_missing_prints_manual_cmd` |
| target script missing | dispatch table | detect | check path before run; "script not found at <path>" + exit 2 | stderr, exit 2 | `cli_unknown_target_errors` |
| unknown subcommand | user input | prevent | not in table → usage + exit 2 | stderr usage | `cli_unknown_command_usage` |
| child returns nonzero | delegated script failed | propagate | return the child's exit code verbatim | child's own output | `cli_propagates_child_exit` |
| run from wrong directory | path resolution | mitigate | resolve paths relative to the repo root (the CLI's own location), not CWD | works from any subdir | `cli_runs_from_subdir` |

## Adversarial analysis (STRIDE-lite)
No trust boundary: a local, developer-invoked CLI with **no network, no untrusted input** (args come from the developer's own shell), reading/executing only pack-internal scripts it ships with. The one consideration — command injection via args — is mitigated by passing argv as a **list to `subprocess.run` without `shell=True`** (no shell interpolation). One line, explicit negative: *no remote, no privilege change, no secret handling in this component.*

## Privacy analysis (LINDDUN-lite)
This component touches no personal data (verified — it forwards argv to child processes and prints their output; it stores nothing and inspects no file contents itself).

## UI & interaction design
**Medium:** CLI. **Platform guidelines:** standard CLI conventions (visibility of status, clear `--help`, meaningful exit codes — Body of Knowledge §VII.4). **Key "screens":** (1) no-args/`--help` → the command table with one-line descriptions; (2) a dispatched command → the child's own output, unmodified; (3) an error → a one-line diagnosis + the manual fallback command. **States:** success (child exit 0, silent passthrough) · error (nonzero, diagnostic to stderr) · unknown-command (usage). **Copy (real):** `aiforward — AI-Forward pack CLI (a thin front over tools/ + scripts/).` ; `Unknown command '{x}'. Run 'aiforward --help'.` ; `PowerShell (pwsh) not found — run manually: pwsh tools/verify-bundle.ps1`. **Accessibility/perf:** plain ASCII, no color required, instant (just spawns a child). No reduced-motion/contrast concerns (text stream).

## Telemetry
Proportionate to a dev CLI: none beyond the child's stdout/stderr and exit code (the observable contract). No spans/metrics — there is no service. *(Deviation from O-series recorded: this is a local CLI dispatcher, not a runtime path; telemetry would be noise. Rationale per Observability Standard §0 "repo target wins / proportionate.")*

## Test plan
Testing Strategy triggers: **T1** (pure dispatch logic) → **D1** unit; **D0** hygiene throughout. Eval case (`cmd-exit` running `aiforward --help` returns 0; `aiforward bogus` returns nonzero). Concretely: the dispatch table maps correctly; unknown command exits nonzero; child exit code is propagated; `pwsh`-missing path prints the manual command. No mocks needed beyond a real `python -c` child for the exit-propagation test (D7 satisfied with a real child, not a substitute).

## Conformance notes
LOA tiers N/A (no inference). Honors the stdlib-only repo convention (no third-party import). Deployment: `tools/aiforward.py` is **not** in the deployment map (source-repo only) — recorded so the doctor/consistency don't expect it in installed repos.

## Flagged risks & residual unknowns
- Cross-shell `pwsh` availability (Flagged, knowledge base open-questions) — mitigated by the detect-and-print-manual-command path, not eliminated.

## Status & next action
| | |
|---|---|
| **Completed** | aiforward CLI design |
| **Remaining** | designs 2 (doctor), 3 (memory), 4 (RAI+scrub) |
| **Best next action** | design the doctor (its subcommand is the CLI's first real dependency) |

## Gate record
`GATE design · 2026-06-14 · Patterns Expert + Simplifier + Test Architect · criteria met: single responsibility (Façade), all delegated scripts Verified, no trust boundary, test plan present · verdict: PASS · vetoes→resolution: Simplifier confirmed zero added logic; Test Architect confirmed exit-propagation + unknown-command tests · author did not self-clear`

---
**Handoff:** → `/implement` (via `/extendaibundle`).
