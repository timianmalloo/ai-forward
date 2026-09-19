---
id: plan-cross-platform-readiness
title: "Plan: make the pack's scripts, hooks, tools and skills work unchanged on Windows and macOS"
type: doc
status: draft
owner: "@timianmalloo"
phase: "pack-hygiene"
tags: [cross-platform, windows, macos, plan, controls, ci]
links:
  - { to: investigation-cross-platform-readiness, rel: implements }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-12-18"
review-suggested: []
summary: >-
  Six phases, ranked by benefit ÷ cost, each landing with a control that was observed failing
  first: one interpreter resolver used everywhere; three lints (encoding on subprocess, newline on
  writers, no machine paths in tracked files) that mechanise the sweeps the pack skipped; a
  .gitattributes template and a registry-execution check in pack-doctor; skill commands rewritten
  without bash-only syntax; a Windows and a macOS CI job so the nt branches and the Mac-only test
  failures are seen; and the five red tests made configuration-independent. Awaiting approval
  before any file is changed.
---

# Plan: cross-platform readiness (Windows and macOS)

*Implements `docs/investigations/cross-platform-readiness.md`. Every phase lands with its
control red first (CI6), re-runs `tools/sync-pack.ps1` then `pwsh tools/verify-bundle.ps1`,
and commits `pack/`, `.claude/`, `.github/`, `.grok/`, `.agents/` and `docs/` together.
Nothing below is implemented; this is the checklist for approval.*

## Ordering principle

Phase 0 is the enabling gap: without a Windows and a macOS runner every other fix is asserted,
not observed. Phases 1–3 are one-commit sweeps with lints, cheap because the codebase already
passes the same bar for `encoding=` on `open()`. Phase 4 is the documented-command rewrite.
Phase 5 is the test hygiene that makes a developer machine agree with CI.

| # | Phase | Closes | Cost | Control that fails on recurrence |
|---|---|---|---|---|
| **P0** | **See it: a `windows-latest` and a `macos-latest` job in `pack-consistency.yml`** running gates 1, 2, 3, 5, 6, 8, 8b (skip node/playwright to hold runner cost), plus a Windows-only step: `chcp 1252` then `--help` on every script under `pack/scripts`, `coord classify init --force` followed by `git diff --exit-code .agents/artifacts.yml`, `docs-graph derive` followed by `git diff --exit-code`, and the generated `pre-commit` executed under Git Bash `sh` | XT-CI; makes XP-07/14/21/22/23/26 Verified or closed; enforces every phase below | ~½ day, +2 runners per push (CE rings: keep the matrix in the every-push ring for `pack/**` changes only) | the jobs themselves, marked required |
| **P1** | **One interpreter resolver, used everywhere.** (a) `coord classify init` writes the token `python3` on POSIX and `python` on Windows **never** `sys.executable` (`coord-core.py:958`); `verify_regen_command` and `coord regen` resolve the first token through `conductor-join._interp`'s rule (`python3`/`python` → `sys.executable`) before running. (b) `_print_settings_entry` (`:2811`) and `coord plugin` (`:2773`) emit a launcher shape, not an absolute path. (c) The Claude, Grok and Antigravity hook adapters gain the Copilot adapter's two-arm shape or a `#!/bin/sh` shim resolved from `$CLAUDE_PROJECT_DIR`; the Antigravity `../` prefix is removed. (d) `tools/verify-bundle.ps1` and `sync-pack.ps1` adopt `setup-knowledge-graphs.ps1:82-87`'s resolver (`python` → `python3` → `py -3`, throw if none) and `/` separators. (e) Re-normalise this repo's `.agents/artifacts.yml` | XP-01/02/03/04/05/06/36, XT-01/02/03/11/12/14/18, XS-01..06 | ~1 day | **lint `verify-no-machine-paths.py`**: fails on `[A-Za-z]:\\`, `/opt/homebrew/`, `/Users/`, `/home/`, `\.pyenv` in any tracked text file outside `docs/audit/**` and `docs/profiles/**`; **conformance test** (`test_harness_conformance.py:225` extended) asserting every hook command in `pack/adapters/hooks/*.json` names a resolvable interpreter and no path starts with `..`; **pack-doctor** check that argv[0] of every `derived` command resolves on this machine (XP-30) — red today |
| **P2** | **Encoding sweep (DC-211 shape).** Add `encoding="utf-8", errors="replace"` to the 21 `subprocess` text-mode calls; add the `sys.stdout.reconfigure` guard to `coord-core.py`, `dream.py`, `apply-learnings.py`, `graphify-setup.py`, `obsidian-setup.py`, `ui-craft-gate.py`, `visual-assets-setup.py` and both hooks (and `sys.stdin.reconfigure` in the hooks); fix `tools/build-pages-bundle.py:139`; fix `prompt-log.py` to hand `clip.exe` UTF-16LE (or use `Set-Clipboard` via pwsh) and to fall through the clipboard ladder | XP-13/14/15/16/22, the last `open()` | ~½ day | **lint `verify-subprocess-utf8.py`** (absorb ai-de's, which already exists there): fails on `text=True`/`universal_newlines=True` without `encoding=`; **lint** asserting every `__main__` script carries the stdio guard — both red today (21 and 9 sites) |
| **P3** | **Newline sweep.** `newline="\n"` on the 26 pack writers (`dream.py` JSONL appends first); drop `text=True` from both `mkstemp` calls in `docs-graph.py`; `context-budget.py` inserts with the file's own EOL; `scrub.py` refuses to rewrite when replacement characters were introduced. Ship `.gitattributes` (`* text=auto eol=lf` + per-type + the `merge=coord-*` lines) and an `.editorconfig` through `pack-apply.py`'s deployment map; `coord install` verifies the `eol` rule instead of assuming it | XP-07/08/09/10/11/12/17/18, XT-09/10 | ~½ day | **lint**: `open(..., "w"|"a")` / `write_text` without `newline=` fails; **test**: regenerate `docs-index.js` and assert no `\r` (runs on the P0 Windows job); **pack-doctor** FAILs when `.gitattributes` declares `merge=coord-register` without an `eol` rule |
| **P4** | **Documented commands that run in any shell.** Rewrite the 8 backslash-continued and 4 `&&`-chained commands as single lines or separate lines; change the 10 bare `python` skill commands to `python3`; add one sentence to the skill template's "Audit (last action)" block pointing at `pack-doctor`'s interpreter line; give CT27 a `$LASTEXITCODE` remedy beside `set -o pipefail`; promote DC-207 ("a multi-line program is a file, then a run") from prose to the dispatch rule in `execute-with-coordination`; sanitise `AGENT_SESSION` before it becomes a file name (`coord-core.py:559`; reject `:`/`/`/`\`) | XS-01..25, DC-207, DC-086/088 | ~½ day | **lint over `pack/`**: fails on a fenced-command line ending in `\`, on ` && ` inside a fenced command, and on bare `python ` outside `INSTALL.md`'s labelled Windows table; **test**: a session id containing `:` is refused by `coord session start` |
| **P5** | **Tests that agree with the developer's machine.** `test_coord_derived.py` reads the default branch from `git symbolic-ref` (or passes `-b main` to `git init`) instead of `master`; `test_run_evals.py` compares `os.path.realpath` on both sides; establish and fix T-3 (`audit-log selfcheck --since`) | T-1/T-2/T-3 | ~½ day | the P0 `macos-latest` job (these fail there today); the whole suite green on Mac, Windows and Linux |

**Struck (the Simplifier's pass):** a `{py}` placeholder substituted at sync time into two flavours
of every doc (doubles the generated surface and violates CTX-B); a Python launcher binary shipped
per OS (the resolver rule is one function); rewriting the `.ps1` tools in Python (they run under
pwsh on all three OSes in CI already); "fixing" the POSIX arm of `bounded_process.py` to Windows
parity (cgroups would be the honest tool; record XP-23 as a known asymmetry and report it in the
result object, which it already does).

## Approval checklist (files that will change)

- [ ] P0 — `.github/workflows/pack-consistency.yml` (two jobs); `tools/verify-bundle.ps1` gains a `-Matrix` note
- [ ] P1 — `pack/scripts/coord-core.py` (`:958`, `:1023`, `:2508`, `:2773`, `:2811`), `pack/scripts/pack-doctor.py` (registry-execution check), `pack/adapters/hooks/{claude-code.settings,grok.ai-forward,agy.ai-forward}-hooks.json`, `tools/verify-bundle.ps1`, `tools/sync-pack.ps1`, new `pack/scripts/verify-no-machine-paths.py`, `tests/docs_explorer/test_harness_conformance.py`, `.agents/artifacts.yml` (re-normalised), the installed copies via `sync-pack`
- [ ] P2 — 21 call sites across 13 scripts + `tools/check-consistency.py`, `tools/build-doc-site.py`, `tools/build-pages-bundle.py`; new `pack/scripts/verify-subprocess-utf8.py` (from ai-de); stdio guard in 9 scripts; `prompt-log.py` clipboard
- [ ] P3 — 26 writer sites in 7 scripts; `docs-graph.py` `mkstemp`; new `pack/adapters/gitattributes.template`, `pack/adapters/editorconfig.template`; `pack-apply.py` deployment map; `pack-doctor.py`; INSTALL.md deployment-map row
- [ ] P4 — 12 command lines across 5 knowledge docs and 3 skills; 10 `python` → `python3` edits in 4 skill files; `pack/templates/*.md` audit block; `communication-and-task-discipline.md` CT27; `execute-with-coordination/SKILL.md`; `coord-core.py:559` sanitiser + test
- [ ] P5 — `tests/docs_explorer/test_coord_derived.py`, `test_run_evals.py`, `test_audit_selfcheck.py` (after diagnosis)
- [ ] Register PLAT-A and PLAT-B in `docs/lessons/defect-classes.md` as `controlled` once P1–P3's lints are red-then-green
- [ ] Each phase: `pwsh tools/sync-pack.ps1`, `pwsh tools/verify-bundle.ps1`, one conventional commit, rebase onto `origin/main`, push

## Measurement (IO rules)

| Question | Emitting source |
|---|---|
| Does the pack run on Windows? | the P0 `windows-latest` job, required check |
| Does it run on macOS? | the P0 `macos-latest` job |
| How many machine paths are in tracked files? | `verify-no-machine-paths.py` count, 0 after P1 |
| How many undecoded subprocess calls / un-newlined writers remain? | the two lints' counts (21 → 0, 26 → 0) |
| How many documented commands are shell-portable? | the P4 lint (12 → 0 chained/continued; 10 → 0 bare `python`) |
| Is the test suite green off the CI box? | the P0 macOS job; developer `pytest` on a `main`-default machine |

## Status

| | |
|---|---|
| **Completed** | Investigation (60+ findings, six systemic causes). **P0 and P1 landed at revision 74** (approved 2026-09-19): `windows-latest` and `macos-latest` jobs in `pack-consistency.yml` with the Windows-only proofs (cp1252 `--help` sweep, byte-identical registry and `docs-index.js`, pre-commit under Git Bash `sh`); `coord-core.resolve_interpreter` and the `python3` registry token; the three Claude-format hook adapters resolve the interpreter in the shell and the Antigravity path is anchored at the git top level; `coord install` prints a machine-neutral settings entry; `coord plugin` names `python3` off Windows; `pack-doctor` FAILs an unresolvable derived command; `verify-no-machine-paths.py` (gate 1b + CI); `verify-bundle.ps1` and `sync-pack.ps1` resolve `python3 → python → py -3` once. One P5 item pulled forward because P0 depends on it: the macOS `/private/var` test comparison (T-2). Red first: 17 assertions, 7 lint hits, the doctor on the Windows path. |
| **Remaining** | P2 (encoding sweep), P3 (newline sweep + `.gitattributes` template), P4 (documented commands), P5 (T-1 `master`, T-3 cause). **New item, found while landing P1:** `coord classify init` / `coord regen` run from a linked worktree write the **primary** checkout's tracked registry and derived files (`.agents/` resolves to the primary by design); the tracked registry should follow the invoking tree. First observation of the Windows job is the next measurement — a red step there is a finding for P2/P3, not a reason to mute it. |
| **First measurement (run 35449895490, 2026-09-19)** | ubuntu green. **Windows:** counts, machine-path lint and source↔install drift all pass under pwsh; pytest 735 passed / 3 failed — `test_audit_selfcheck …--since` (T-3) and two `test_codex_surface` tests raising `UnicodeDecodeError: 'charmap' codec can't decode byte 0x90` (UTF-8 read through cp1252 in the Codex support that landed at revision 73 — the P2 class, caught on day one). **macOS:** 725 passed / 1 failed — T-3 only; T-1 (`master`) passes on the runner and T-2's fix holds. T-3 therefore fails on Windows, macOS and a developer Mac and passes only on ubuntu: an environment-dependent test, not a platform arm. The Windows-only proofs did not execute because pytest ran first; the step order is now proofs-then-pytest so the next run reports them. |
| **Second measurement (run 35450221833, proofs before pytest)** | **Windows: every proof passes** — every script answers `--help` under cp1252 (XP-14 does not reproduce for `--help` with `PYTHONIOENCODING` cleared; the risk stays for non-ASCII *output* paths), the registry regenerates byte-identically (PLAT-B closed on Windows), `docs-index.js` regenerates byte-identically (**XP-07 disconfirmed**), and the pre-commit hook runs under Git Bash `sh` in both the advisory and the enforcing path. **macOS: every proof passes.** The two Codex cp1252 test reads are fixed. **T-3's cause is verified and fixed** in `audit-log.py ids_at_ref`: git returns the real path while the caller's root is a symlinked temp path, so the relative log path was wrong and `--since` grandfathered nothing on macOS and Windows. |
| **Third measurement (run 35450598384)** | **All three jobs green** — ubuntu, macOS (every proof + 726 tests) and Windows (every proof + 738 tests) — with the `--since` fix and the Codex test encoding sweep landed. `main` @ `c8557b0`, revision 74. |
| **P2 + P3 (revision 75, approved 2026-09-19)** | Two gates that stay, both red first: `verify-subprocess-utf8.py` (21 sites) and `verify-portable-text-io.py` (30 sites: text writes without `newline`, unguarded printing CLIs, `mkstemp(text=True)`); wired as `verify-bundle` 1c/1d and CI steps on all three runners. Sweeps applied across `pack/scripts`, both hooks and `tools/`. `prompt-log` hands `clip.exe` UTF-16LE and falls through its clipboard ladder; `verify-no-conflict-markers` no longer passes when `git ls-files` fails; `scrub` refuses to rewrite bytes it could not decode; `context-budget` inserts with the file's own EOL; `ui-craft-gate` splits its override with `shlex`. `pack-apply` ships the line-ending policy (`* text=auto eol=lf` appended to `.gitattributes`, `.editorconfig` created once); `pack-doctor` FAILs a repo that declares the coord merge drivers without an `eol=lf` rule. PLAT-A is `controlled`. |
| **Residuals from the P3 sweep (second-reviewed, accepted)** | `visual-assets-setup.py`'s `.gitignore` append and the `dream.py` / `apply-learnings.py` Markdown appends write LF without reading the file's EOL, so a CRLF target would become mixed — moot under the `eol=lf` policy `pack-apply` now installs, and the `_eol` treatment in `context-budget.py` is the fix if a repo declines the policy. The `clip.exe` UTF-16LE path and the Windows `shlex` split are proven by simulation on macOS; the Windows job is where they become Verified. `scrub.py`'s `splitlines()` line numbers were pre-existing and untouched. |
| **Best next action** | P4 (documented commands: 8 backslash continuations, 4 `&&` chains, 10 bare `python`, the `AGENT_SESSION` file-name sanitiser) and P5's remaining item (the three `master`-branch tests). Then the worktree-registry follow-up. |
