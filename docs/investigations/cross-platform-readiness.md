---
id: investigation-cross-platform-readiness
title: "Investigation: does the AI-Forward Pack — scripts, hooks, tools, skills — work on both Windows and macOS?"
type: investigation
status: draft
owner: "@timianmalloo"
phase: "pack-hygiene"
tags: [cross-platform, windows, macos, interpreter, encoding, newlines, hooks, ci, investigation]
links:
  - { to: defect-classes, rel: relates-to }
  - { to: architecture-agent-coordination, rel: relates-to }
  - { to: kb-multi-agent-coordination, rel: relates-to }
review-by: ""
review-suggested: []
summary: >-
  Read-only cross-platform audit of pack/scripts, pack/adapters/hooks, tools/*.ps1, the hook
  wiring for five harnesses, CI, and every command the skills and knowledge docs tell an agent
  to run, with ai-de's Windows defect register as the empirical baseline. Verdict: the pack is
  much better than average on encoding and platform branching, but six systemic classes remain
  — an interpreter word never resolved at one seam, machine state persisted into tracked files,
  no Windows or macOS CI so the `nt` branches never execute, subprocess output decoded without an
  encoding, POSIX shell syntax in agent-typed commands, and tests that assume the Linux CI box.
  Nothing is fixed here; the plan is a sibling document awaiting approval.
---

# Investigation: cross-platform readiness of the pack (Windows and macOS)

- **Status:** Root causes verified (six classes); fix plan in `docs/plans/cross-platform-readiness.md` — **P0 and P1 landed at revision 74, P2 and P3 at revision 75**; P4 and the `master`-branch half of P5 open
- **Severity / tier:** T1. Nothing blocks today's Mac/pyenv or Windows/python.org developer, but several defects corrupt silently when a repo is shared across the two.
- **Reported by / date:** operator request, 2026-09-19 ("analyze the repo in terms of pack, scripts and skills; ensure they all work cross-platform")
- **Worktree:** `analysis/cross-platform-readiness` @ `11e0197` (origin/main)

## Symptom

The pack is developed on macOS (this machine: pyenv 3.13, zsh, pwsh 7.5) and consumed on Windows
(ai-de: `c:\projects\ai-de`, python.org Python, Git for Windows, pwsh). Observed this week:
`coord regen` fails on this Mac because the tracked registry `.agents/artifacts.yml` carries
`C:\Users\malla\AppData\Local\Programs\Python\Python312\python.exe` on seven `derived` lines
(written by `coord classify init` on a Windows machine). Expected: every pack script, hook,
tool and documented command runs unchanged on both operating systems, and the shared repo
carries no machine state.

## Method (measured, not recalled)

| Instrument | What it established |
|---|---|
| AST scan of 82 Python files (`pack/scripts`, `pack/adapters/hooks`, `tools`, `tests`) | text `open()` without `encoding=`: **1**; text writers without `newline=`: **44** (26 in pack); `subprocess` text-mode calls without `encoding=`: **21** (5 with); `python3` literal inside a process call: **0**; `os.path.relpath`: **0** |
| Regex scan of the same files | POSIX-only modules/calls: `fcntl` ×2, `os.killpg` ×2, `sh -c` ×1, `chmod` ×3 — **all inside `os.name` branches**; 32 existing platform branches; `shell=True` ×2 (coord-core) |
| Regex scan of `pack/commands/**`, `pack/knowledge`, `pack/templates`, INSTALL, AGENTS, README | agent-typed `python3` commands: **84** (60 in skills, 22 in knowledge, 2 in INSTALL); bare `python`: **16** (10 unintended); `&&` chains in commands: **4**; backslash line continuations: **8**; heredocs, `export`, `/tmp`, `pbcopy`, `chmod +x`: 0 each |
| Repo facts | `.gitattributes`: `* text=auto eol=lf` plus per-type rules; **zero CRLF files**; no `.editorconfig`; CI gates run only on `ubuntu-latest`; the sole Windows job is a self-hosted, dispatch-only benchmark |
| Test suite on this Mac | 700 passed, **5 failed**: 3 hard-code `master` as the default branch (this machine's `init.defaultBranch=main`), 1 breaks on macOS's `/private/var` symlink for temp dirs, 1 (`audit-log selfcheck --since`) fails for a cause not established |
| Four read-only reviews (scripts · tools/hooks/CI · skills/docs · ai-de's Windows register) | 37 + 23 + 25 findings and 19 ai-de defect classes, consolidated below |
| Executed on this Mac | `which python` → pyenv shim (so bare `python` works *here* and hides XP-02) |

## System map — what runs where

```
agent / human types a command  ──►  skill or knowledge doc says `python3 …`  (84×)  ──►  shell (zsh · pwsh · cmd · Git Bash)
harness fires a hook           ──►  .claude/settings.json / .grok / .agents / .github hooks JSON  ──►  `python …` or `python3 …`
git commits                    ──►  .git/hooks/pre-commit (#!/bin/sh, exec "<abs python>" …)  ──►  coord precommit
git merges                     ──►  .gitattributes merge=coord-*  ──►  .git/config driver "<abs python>" … (per clone)
coord regen / conductor-join   ──►  .agents/artifacts.yml (TRACKED) derived "<abs python>" …  ──►  shell=True
CI                             ──►  ubuntu-latest only  ──►  every `os.name == "nt"` branch is dead code in CI
```

Two kinds of seam carry the interpreter word: **run-time** (a shell resolves `python`/`python3`
from PATH) and **persisted** (a generator writes `sys.executable` into a file). The first fails
loudly on the wrong OS; the second fails on *every other machine*.

## Findings register (consolidated; ids from the four reviews kept)

Severity: **S1** blocks a documented flow · **S2** silent corruption · **S3** degraded / fail-open · **S4** cosmetic. Confidence: Verified = the line was read or the behaviour executed; Inferred = reasoned from a read line.

### Class 1 — the interpreter word is resolved at the wrong seam

| id | file:line | finding | breaks on | sev | conf |
|---|---|---|---|---|---|
| XP-01 | `pack/scripts/coord-core.py:958` → `.agents/artifacts.yml:15-17,26-29` | `coord classify init` writes `sys.executable` into a **tracked** file; the Windows path is now in this repo and `coord regen` fails on macOS (observed 2026-09-19). ai-de hand-normalised its copy to `python` with a 9-line comment saying `--force` re-bakes the path | every other machine | S2 | Verified |
| XP-02 / XT-01 | `pack/adapters/hooks/claude-code.settings.hooks.json:9,20,31,42` → `.claude/settings.json` | four Claude Code hooks run bare `python` with a repo-relative path; stock macOS and Debian have no `python`. Works here only because pyenv ships a shim | macOS without a shim | S3 (fail-open, CTX-D control silently off) | Verified |
| XP-03 / XT-03 | `grok.ai-forward-hooks.json:9,20,31,42` | same shape for Grok Build | macOS | S3 | Verified |
| XT-02 | `agy.ai-forward-hooks.json:9,20` → `.agents/hooks.json` | `python ../docs/ai-forward-pack/hooks/…` — **parent-relative**; escapes the repo unless the hook cwd is one level down | both | S3 | Verified (string) / Inferred (cwd) |
| XP-04 / H7 | `coord-core.py:2773` | `coord plugin` emits `python "${CLAUDE_PLUGIN_ROOT}/hooks/hook.py"` — the Windows lesson (bare interpreter) encoded as the Windows-only name | macOS | S3 | Verified |
| XP-05 / XT-18 | `coord-core.py:2811` | `coord install` prints `"command": sys.executable` for a human to paste into tracked `.claude/settings.json` | every other machine | S2 | Verified |
| XT-04 / D1-D2 | `coord-core.py:2371-2398`; live `.git/config` | merge drivers registered as `"<abs python>" "<abs coord-core.py>" merge-<class>`; per-clone so acceptable, but a pyenv version bump silently unregisters them and a fresh clone falls back to a text merge of `docs/audit/*.jsonl` (pack-doctor WARNs by design) | any clone that did not run `coord install` | S3 | Verified |
| XT-11 | `tools/verify-bundle.ps1:68,88,120,124,128,137,149,183-192` | bare `python` for all ten gates, contradicting `INSTALL.md:199` ("Linux/macOS → `python3`"); `setup-knowledge-graphs.ps1:82-87` has the correct resolver and `sync-pack.ps1:353` a partial one | macOS without a shim | S1 | Verified |
| XS-01..06 | `pack/commands/{dream,apply-learnings,extendaibundle}/SKILL.md`, `ui-design/reference/flow.md` | 10 bare-`python` commands that contradict the pack's own `python3` convention | stock macOS/Linux | S1 | Verified |
| XS-11, 20-24 | `prepare-for-coordination/SKILL.md:36-38`, `updatepack/SKILL.md:31,37`, `prompts/SKILL.md:17,22`, `searchprompts/SKILL.md:17` and 78 more | `python3 …` with the Windows substitution stated only in `AGENTS.md:243`; no skill restates it; only `pack-doctor` names the working form and no skill calls it as a preflight | Windows (python.org) | S1 when `AGENTS.md` is not in context | Verified |
| XP-36 | usage strings in `run-verify-gates.py`, `verify-no-conflict-markers.py`, `conductor-join.py`, `obsidian-setup.py`, `session-start.py:24`, `pack-doctor.py:333` | no printed invocation is correct on both OSes; `conductor-join._interp` (`:88-92`) rewrites `python3`/`python` → `sys.executable` at run time — the right pattern, applied to what runs, not to what is printed | one OS each | S3 | Verified |

### Class 2 — text encoding and newlines

| id | file:line | finding | breaks on | sev | conf |
|---|---|---|---|---|---|
| XP-13 / DC-211 | 21 sites: `coord-core.py:450,1023,2508` (incl. the universal `_git()` wrapper), `audit-log.py:409,519`, `conductor-join.py:81,246`, `pack-apply.py:554,722`, `run-verify-gates.py:60`, `session-profile.py:547`, `ui-craft-gate.py:127`, `verify-no-conflict-markers.py:53,61`, `verify-no-new-console-launches.py:54`, `graphify-setup.py:200,307`, `obsidian-setup.py:710`, `tools/check-consistency.py:850,980`, `tools/build-doc-site.py:80` | `subprocess.run(..., text=True)` with no `encoding=` decodes with cp1252 on Windows; a non-ASCII path or branch name becomes mojibake and `_dirty_paths` mis-compares. ai-de fixed its own tools and gated them (`verify-subprocess-utf8.py`), and logged the pack copy as "the pack's to fix" (DC-211). `prompt-log.py:243-248` fixed one site with a comment and it was never swept | Windows | S2 | Verified |
| XP-08 | `dream.py:57,440,459,589,594` | JSONL and diary appends without `newline="\n"` → CRLF on Windows; a CRLF line and its LF twin are distinct strings, so a union merge conserves both. `audit-log.py:465` does it right | Windows | S2 | Verified |
| XP-09..12 | `session-profile.py:1726,1729`; `apply-learnings.py:182,244,288,304,338`; `visual-assets-setup.py:307,314,440,484,507` (incl. an append to `.gitignore`); `foundation-check.py:55-59` (`--update` rewrites the whole manifest CRLF) | 26 pack writers without `newline=`; 9 scripts use it, 17 do not | Windows | S2/S3 | Verified |
| XP-07 | `docs-graph.py:339-346,1118-1125` | `tempfile.mkstemp(text=True)` opens with `_O_TEXT`; the inferred effect was CRLF in `docs/docs-index.js` on Windows. **Disconfirmed by the P0 Windows job (run 35450221833): `docs-graph derive` on `windows-latest` regenerated `docs-index.js` byte-identically** — `newline="\n"` on the `fdopen` wrapper does hold. Kept as a code-clarity item for P3, not a defect | — | Inferred → **disconfirmed by execution** |
| XP-14 | `apply-learnings.py:348,376,379` | `—` and `×` in `print`/`help` with no `sys.stdout.reconfigure` guard (15 sibling scripts have it) → `UnicodeEncodeError` on a cp1252 console; `--help` crashes | Windows | S1 | Verified |
| XP-15 / XP-16 | `coord-core.py` (whole file), `reread-guard.py:146`, `session-start.py:57` | no stdio guard on the hook/merge-driver entry point; hook stdin decoded with the console code page → wrong dedup key / cwd for non-ASCII paths, fail-open | Windows | S3 | Verified / Inferred |
| XP-18 | `scrub.py:115-125` | reads with `errors="replace"` and writes back — permanently replaces non-UTF-8 bytes with U+FFFD | both | S2 | Verified |
| XP-22 / XT-19 | `prompt-log.py:190-195` | UTF-8 bytes piped to `clip.exe`, which reads the console code page → mojibake for the em-dashes and arrows the prompts contain | Windows | S3 | Inferred |
| XT-09 / XP-29 | pack ships **no `.gitattributes` template**; `coord install` appends only `merge=coord-*` lines and its comment at `coord-core.py:188-190` assumes LF "as .gitattributes requires" | every LF-writer rests on an invariant the pack never installs in a consuming repo | Windows consumer with `autocrlf=true` | S2 | Verified |
| XT-10 | no `.editorconfig` | editors re-introduce CRLF; only the git filter catches it | Windows | S4 | Verified |
| — | `tools/build-pages-bundle.py:139` | the single text `open()` without `encoding=` | Windows | S3 | Verified |

### Class 3 — processes, shells, paths

| id | file:line | finding | breaks on | sev | conf |
|---|---|---|---|---|---|
| XP-19 / XT-17 | `coord-core.py:1023,2508` | `shell=True` for registry commands "so they run identically on POSIX and Windows" — they cannot: `cmd.exe /c` vs `/bin/sh -c` differ on quotes, `$VAR`, `2>/dev/null`, globbing; a quoted first token with an interpreter path containing a space trips cmd.exe's outer-quote rule | Windows | S3 | Verified / Inferred |
| DC-086/088 | `coord-core.py:559` → `:172,:353` | `AGENT_SESSION` used raw as the ledger file name (`{session}.jsonl`); a `:` becomes an NTFS alternate data stream — the write "succeeds" and the file is invisible to `glob`. ai-de hit this twice | Windows | S2 | Verified (shape) |
| XT-12 | `tools/verify-bundle.ps1:68,103,120…`, `sync-pack.ps1`, `setup-knowledge-graphs.ps1` | `Join-Path $repo "tools\check-consistency.py"` — literal backslash handed to a **native** `python` process, which does not normalise on Unix (provider cmdlets do, which is why sync-pack survives CI) | macOS/Linux | S3 | Inferred |
| XP-20/21 | `ui-craft-gate.py:106,113-114` | `explicit.split()` breaks a quoted path with spaces; `shutil.which("npx")` → `npx.cmd`, whose argv is re-quoted by cmd.exe ("BatBadBut") | Windows | S3 | Verified / Inferred |
| XP-26/27 | `docs-graph.py:257,274-291,355,373-377` | `(st_dev, st_ino)` identity across `os.stat`/`os.fstat` on NTFS; `os.replace` onto a file an editor holds open raises `PermissionError` with no retry | Windows | S3 | Inferred |
| XP-28 | `coord-core.py:674,1196` | `MAX_PATH = 4096` — a POSIX value under a Windows name; the real Windows limit is 260 unless long paths are enabled | Windows | S4 | Verified |
| XP-23/24/25 | `bounded_process.py:389-394 vs 19-27,100-134; 219-220 vs 346; 128` | the **Windows** arm is the complete one (Job Object, stdin gate, `taskkill /T`); POSIX has per-process `RLIMIT_AS` only, no process-count limit; docstring/timeout divergence; private `process._handle` | macOS (weaker containment) | S3 | Verified |
| XP-31 | `verify-no-conflict-markers.py:61` | `git ls-files -z` with no return-code check → zero files → gate exits 0 having scanned nothing | both | S2 (fail-open gate) | Verified |
| XP-32 | `graphify-setup.py:476` | `pip install --user` raises inside a venv; on Windows installs to a Scripts dir not on PATH | Windows | S3 | Inferred |
| XP-35 | `pack-apply.py:825-892` | the retirement shim is PowerShell-only; `pwsh` is optional on macOS. Line 864 hedges `python`/`python3` — the one place hedging the right way | macOS without pwsh | S3 | Verified |
| XS-07/08 | `addpacktorepo/SKILL.md:154`, `extendaibundle/SKILL.md:70` | `git add -A && git commit … && git push` — `&&` is not a statement separator in Windows PowerShell 5.1 | Windows PS 5.1 | S1 (a skill's close-out step) | Verified |
| XS-12..19 | `execute-with-coordination/SKILL.md:76-77`, `audit-and-change-log.md:93-96,108-111,144-147`, `session-worktree-discipline.md:139-141,152-153`, `code-knowledge-graph.md:129-130`, `obsidian-lens.md:128-129` | trailing-backslash line continuation in 8 multi-line commands — bash/zsh only; cmd runs the next line as a separate command, PowerShell uses `` ` `` | Windows | S1 (AL5 audit step, WT1 worktree step, the only join line) | Verified |
| XS-25 | `communication-and-task-discipline.md:113` | CT27's remedy is `set -o pipefail` with no `$LASTEXITCODE` equivalent for PowerShell hosts | Windows | S4 | Verified |
| DC-207 | ai-de: 70 failed heredoc runs across 28 nodes | `python - <<'EOF'` under Git Bash mangles quotes; the pack's rule "a multi-line program is a file" exists in prose (CT27) and is `uncontrolled` | Windows Git Bash | S3 | Verified (ai-de) |

### Class 4 — CI, tests and diagnosis

| id | file:line | finding | sev | conf |
|---|---|---|---|---|
| XT-CI | `.github/workflows/pack-consistency.yml:33` and every other workflow | every gate runs on `ubuntu-latest`; the only Windows execution is a dispatch-only, owner-gated, self-hosted benchmark. Every `os.name == "nt"` branch above is **never executed in CI**; neither is any macOS path | S2 (the enabling gap) | Verified |
| T-1 | `tests/docs_explorer/test_coord_derived.py:188,190,193,246,371` | three tests hard-code `master`; this machine's `init.defaultBranch=main` makes them red on any Mac or Windows dev box configured that way (they fail identically on a clean clone of `main`) | S3 | Verified by execution |
| T-2 | `tests/docs_explorer/test_run_evals.py:187` | compares `Path.resolve()` against the script's realpath; macOS temp dirs live under `/private/var` symlinked from `/var` | S3 | Verified by execution |
| T-3 | `pack/scripts/audit-log.py` `ids_at_ref` (was `:411`) | **Root cause verified 2026-09-19:** `git rev-parse --show-toplevel` returns the real path (`/private/var/…` on macOS; long names on Windows) while the caller's root is the symlinked `/var/…` temp path, so `os.path.relpath` produced `../../../var/…` and `git show <ref>:<that>` found nothing — `--since` silently grandfathered nothing on macOS and Windows and passed only on ubuntu, where `/tmp` is real. Fixed by resolving both sides with `os.path.realpath`; the same shape as T-2. Not a test defect: the script fails the same way in any repo reached through a symlink | S2 (a gate that could not see its base) | Verified by execution |
| CI-1 | `tests/docs_explorer/test_codex_surface.py` (two tests), Codex support landed at revision 73 | `UnicodeDecodeError: 'charmap' codec can't decode byte 0x90` on `windows-latest` — a UTF-8 file read through cp1252 (class 2, the P2 sweep); found by the P0 Windows job on its first run | S1 on Windows | Verified (CI log) |
| XP-30 | `pack-doctor.py:300-338` | the `coordination` check validates that the registry parses and drivers are registered — never that a `derived` command's argv[0] **resolves on this machine**; the registry with the Windows path passes `pack-doctor` clean on macOS | S2 | Verified |
| DC-119 (ai-de) | ai-de `build.yml:632-642` | a two-OS split where the Windows job runs only `Platform=Windows` — 1,889 portable tests never run on Windows; the same hole would appear in any pack matrix that filters by platform | S3 | Verified (ai-de) |

### Already right (credit where the code earned it)

- Encoding on `open()`: 1 miss in 16.5k lines. `pack-apply.py:162` compares after newline/BOM normalisation; its `git()` wrapper sets `encoding="utf-8"`.
- Platform branches are complete two-way splits: `docs-graph.py` `msvcrt`/`fcntl` lock; `bounded_process.py` Job Objects; `run-verify-gates.py` `taskkill`/`killpg`; `pack-doctor.py` `cmd /c`/`sh -c`; `obsidian-setup.py` three-way; `getattr(os, "O_BINARY", 0)` guards; `os.path.normcase` in the hooks.
- `pack-doctor.check_interpreter()` (`:397-446`) rejects the Store alias (exit 9009) and names the working form. `conductor-join._interp` rewrites the interpreter at run time. `session-start.py:77` spawns with `sys.executable`, list argv, no shell. `coord install` refuses to run from a linked worktree (`:2312-2318`) and writes the hook with `newline="\n"`.
- `.github/hooks/ai-forward.json` carries `bash:`/`powershell:` arms — the one hook config that gets the split right.
- `.gitattributes` in this repo forces LF; no CRLF anywhere; `verify-no-new-console-launches.py` (DC-170) already absorbed from ai-de.

## Hypotheses considered (Change Analysis + class sweep)

| Hypothesis | Predicts | Evidence for | Evidence against | Verdict |
|---|---|---|---|---|
| "The pack is POSIX-only by accident" | pervasive `fcntl`/`/tmp`/missing encoding | — | 1 encoding miss; all POSIX calls branched; Windows arm of bounded_process is the stronger | **Rejected** |
| "Windows breakage is confined to the `python3` word" | fixing docs fixes it | 84 doc commands | 21 subprocess decodes, 26 newline writers, tracked registry path, hook JSON, CI | **Rejected** as sufficient |
| "Lessons were learned once and never swept" | the same class fixed in one file, present in others | `prompt-log.py:243-248` (encoding), `audit-log.py:465` (newline), `conductor-join._interp` (interpreter), `setup-knowledge-graphs.ps1:82-87` (pwsh resolver), Copilot hook arms — each correct in one place and absent in siblings | — | **Verified** (systemic) |
| "Machine state leaks into tracked files" | absolute paths in git | `.agents/artifacts.yml`; `_print_settings_entry`; ai-de's hand-normalisation comment | `.git/config`, `.git/hooks` correctly per-clone | **Verified** |
| "No CI on the other OS is the enabling cause" | `nt` branches untested; Mac-only test failures unnoticed | zero `windows-latest`/`macos-latest` jobs; 5 red tests on a Mac that CI never sees | — | **Verified** |

## Verified root causes (systemic, each necessary for its class)

1. **The interpreter word is resolved at the wrong seam.** It is either fixed in prose (`python3`, 84 places, one substitution note in `AGENTS.md`), fixed in a shipped file (`python` in three hook adapters, `verify-bundle.ps1`), or frozen as `sys.executable` into a tracked artifact. The one correct pattern — resolve at run time (`conductor-join._interp`, `setup-knowledge-graphs.ps1`) — exists and is not the default. *Proximate fix:* one resolver, used everywhere. *Systemic fix:* a lint that fails on any other spelling.
2. **A platform lesson is applied where it was learned and never swept** (encoding in `prompt-log.py`, newline in `audit-log.py`, hook arms in the Copilot adapter). The pack's own CI1 says "class, not instance"; four instances show the sweep step was skipped. *Systemic fix:* lints for each class so the next instance fails at commit.
3. **Machine state persisted into tracked files** with no gate that checks a persisted command is runnable here (`pack-doctor` XP-30).
4. **No Windows or macOS CI**, so every `nt` branch is dead code in CI and every Mac-only test failure is invisible until a developer hits it.
5. **Agent-typed commands assume bash/zsh** (`&&`, `\`-continuation, `set -o pipefail`) while the pack targets PowerShell hosts; the DC-207 heredoc rule is prose only.
6. **The test suite assumes the CI box** (`master`, `/var`), so a green CI and a red dev machine coexist.

## Causes ruled out

- Line endings in this repo (`.gitattributes` forces LF; no CRLF files) — but not in consuming repos (XT-09).
- Missing `encoding=` on `open()` — one file only.
- Unguarded POSIX calls — none found.

## Not verified from a Mac (needs one Windows run; each is a P4 matrix case)

XP-07 (`_O_TEXT` CRLF through `fdopen`), XP-26 (`st_ino` on NTFS), XP-21 (`npx.cmd` quoting),
XP-22 (`clip.exe` decoding), XP-01 reverse direction (a macOS-written registry on Windows),
XP-23 (Job Object contains a fork bomb), XP-02 (whether Claude Code surfaces a failing hook on
macOS), XP-28/33 (MAX_PATH; `/c/…` from `--git-common-dir`), XP-14 under `chcp 1252`, T-3's cause.

## Defect classes proposed (registered as `uncontrolled` with the control named in the plan)

- **PLAT-A — A platform lesson applied where it was learned and never swept.** Signature: the same
  hazard fixed in one file with a comment naming the defect, present unfixed in its siblings.
- **PLAT-B — Machine state persisted into a tracked artifact.** Signature: a generator writes
  `sys.executable`, a home directory or a drive letter into a file git carries, and no check
  asks whether the persisted command resolves on the machine reading it.

## Related

- `docs/plans/cross-platform-readiness.md` — the fix plan and approval checklist.
- ai-de `docs/lessons/defect-classes.md` DC-086, DC-088, DC-108, DC-113, DC-119, DC-150, DC-177, DC-207, DC-211, DC-225 — the Windows register this investigation cross-checked.
- Prior pack controls in the same family: FR-031 (`pack-doctor` interpreter check), FR-046/047 (stdio guard), PACK-C, CTX-H, CTX-K.
