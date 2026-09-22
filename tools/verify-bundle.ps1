<#
.SYNOPSIS
    Verify the AI-Forward bundle the same way CI does — the one-command proof.
.DESCRIPTION
    Runs the gates from .github/workflows/pack-consistency.yml, in CI's order, and reports
    every failure rather than stopping at the first, so one run tells you everything that is
    wrong instead of only the first thing.

        1.  Count & skill-list consistency     tools/check-consistency.py
        1b. No machine-specific paths          pack/scripts/verify-no-machine-paths.py (PLAT-B)
        1c. Subprocess decodes state utf-8     pack/scripts/verify-subprocess-utf8.py (PLAT-A)
        1d. Text writes/consoles portable      pack/scripts/verify-portable-text-io.py (PLAT-A)
        1e. Skill contracts (seat, CO-S0, CO-S2)  pack/scripts/verify-skill-contracts.py (P8)
        1f. Documented commands, any shell     pack/scripts/verify-documented-commands.py (PLAT-A)
        1g. Ruling citations resolve           pack/scripts/verify-ruling-citations.py (ID-A)
        1h. Inline markers complete            pack/scripts/marker-lint.py --gate (LINT-A)
        2.  Source<->install drift             sync-pack.ps1 THEN git diff --exit-code
        3.  Python test suite                  pytest tests
        4.  Docs Explorer core contracts       node --test (see the gate-4 note)
        4b. Explainer render + a11y proof      tools/verify-explainer-render.js
        5.  Knowledge-graph validation         docs-graph.py validate
        6.  Vendored-foundation drift          foundation-check.py
        7.  Eval cases well-formed             JSON + compilable regex
        8.  Always-on context budget           context-budget.py gate --ceiling 45000

    FR-057 — why gate 2 changed. This script used to run sync-pack.ps1 and then print
    `git status` as friendly advice. Regeneration WITHOUT COMPARISON cannot detect drift: it
    silently creates the corrected file, never inspects it, and reports CONSISTENT. During
    the revision-42 review that is exactly what happened — a stale web/pack-index.js passed
    here and failed in CI. `git diff --exit-code` is the whole oracle, and it has to run in
    the same command that performed the sync (end-to-end-integrity E13/E14: an exit code is
    not a result — read the state back).

    Gate 4 note (FR-055 / class PACK-C): `npm run` executes scripts through a child shell
    whose PATH can differ from yours, so on some Windows hosts it reports "'node' is not
    recognized" while node itself works. This script therefore invokes node DIRECTLY, and
    reports SKIP only when node is genuinely absent — a skip is printed loudly and named in
    the summary, never silently counted as a pass.

.NOTES
    Requires pwsh + Python 3.8+. Node is optional (gate 4 skips, loudly). Run from anywhere.
#>
[CmdletBinding()]
param(
    [switch]$SkipTests   # inner-loop convenience: gates 1,2,5,6,7 only. Prints what it skipped.
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$results = [System.Collections.Generic.List[object]]::new()

# One interpreter, resolved ONCE (class PLAT-A). python.org Windows ships no `python3`;
# stock macOS ships no `python`; a bare word here was correct on exactly one of them. The
# probe requires real Python 3 output, so the Windows Store `python3` alias (exit 9009,
# "Python was not found") is rejected rather than trusted. Copied from
# setup-knowledge-graphs.ps1, which had this right and was the only tool that did.
$pyExe = $null; $pyArgs = @()
foreach ($c in @(@{ exe = 'python3'; args = @() }, @{ exe = 'python'; args = @() }, @{ exe = 'py'; args = @('-3') })) {
    if (-not (Get-Command $c.exe -ErrorAction SilentlyContinue)) { continue }
    try { $probe = (& $c.exe @($c.args) --version 2>&1 | Out-String).Trim() } catch { continue }
    if ($LASTEXITCODE -eq 0 -and $probe -like 'Python 3*') { $pyExe = $c.exe; $pyArgs = $c.args; break }
}
if (-not $pyExe) { throw 'No working Python 3 found as python3, python, or py -3 (pack-doctor names the working form).' }
Write-Host ("python: {0} {1}" -f $pyExe, ($pyArgs -join ' ')) -ForegroundColor DarkGray

function Gate([string]$name, [scriptblock]$action) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    $status = "PASS"
    try {
        & $action
        if ($LASTEXITCODE -ne 0) { $status = "FAIL" }
    } catch {
        Write-Host $_.Exception.Message -ForegroundColor Red
        $status = "FAIL"
    }
    if ($status -eq "FAIL") { Write-Host "FAILED: $name" -ForegroundColor Red }
    $results.Add([pscustomobject]@{ Gate = $name; Status = $status })
}

function Skip([string]$name, [string]$why) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    Write-Host "SKIPPED: $why" -ForegroundColor Yellow
    $results.Add([pscustomobject]@{ Gate = $name; Status = "SKIP" })
}

Push-Location $repo
try {
    Gate "1. counts, skill/prompt parity, proof coverage" {
        & $pyExe @pyArgs (Join-Path $repo "tools/check-consistency.py")
    }

    # PLAT-B: a tracked, machine-readable file never carries one machine's paths. The
    # registry shipped a Windows python.exe path for a week and only `coord regen` on a Mac
    # noticed. Self-test proves the gate can fail (DC-104).
    Gate "1b. no machine-specific paths in tracked files" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/verify-no-machine-paths.py") --root $repo
    }

    # PLAT-A (P2/P3): a platform lesson fixed in one file and left in its siblings. These two
    # are the sweeps that stay: every text-mode subprocess states utf-8 (ai-de's DC-211, 21
    # sites red first), every text write is LF and every printing CLI guards a cp1252 console
    # (30 sites red first).
    Gate "1c. subprocess text decodes state utf-8" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/verify-subprocess-utf8.py") --root $repo
    }
    Gate "1d. text writes and consoles are portable" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/verify-portable-text-io.py") --root $repo
    }
    Gate "1e. skill contracts: seat, CO-S0 before dispatch, CO-S2 on hard stops" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/verify-skill-contracts.py") --root $repo
    }

    # PLAT-A (XP): a documented command that only one shell can run. Single-line, unchained,
    # python3 - the 26 sites were red first (coordination-p3-p5-p8, track XP).
    Gate "1f. documented commands run in any shell" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/verify-documented-commands.py") --root $repo
    }
    # ID-A (P5, D6): a ruling cited as authority must resolve to a heading in docs/notes/rulings.md;
    # ai-de measured eight numbers that defined nothing. Self-test proves the gate can fail.
    Gate "1g. ruling citations resolve to one heading each" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/verify-ruling-citations.py") --root $repo
    }
    # FR-077 (LINT-A): every finding was the linter's own test fixtures; with string literals
    # excluded the scan is empty, which is what makes gating it safe.
    Gate "1h. inline markers carry their required fields" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/marker-lint.py") --root $repo --gate
    }

    # FR-057: sync AND compare. The comparison is the gate; the sync alone is only a repair.
    Gate "2. source<->install drift (pack/ is the only source of truth)" {
        pwsh (Join-Path $repo "tools\sync-pack.ps1") | Out-Null
        $paths = @(".claude", ".github/instructions", ".github/knowledge", ".github/prompts",
                   ".github/agents", ".grok", ".agents", "docs", "web", "CLAUDE.md", "AGENTS.md")
        git --no-pager diff --stat -- $paths
        git diff --exit-code -- $paths
        if ($LASTEXITCODE -ne 0) {
            Write-Host "pack/ and the generated surfaces have drifted." -ForegroundColor Red
            Write-Host "The files listed above were just regenerated for you - review and commit them." -ForegroundColor Red
        }
    }

    if ($SkipTests) {
        Skip "3. python test suite" "-SkipTests was passed (CI still runs it)"
        Skip "4. docs explorer core contracts" "-SkipTests was passed (CI still runs it)"
    } else {
        Gate "3. python test suite" { & $pyExe @pyArgs -m pytest tests -q }
        $node = Get-Command node -ErrorAction SilentlyContinue
        if ($node) {
            Gate "4. docs explorer core contracts" {
                # Invoked directly, not through `npm run` - see the gate-4 note above.
                # browser_benchmark.test.js requires ./benchmark_docs_explorer -> playwright,
                # a node_modules package. To keep this local proof SELF-CONTAINED in a clean
                # worktree (FR-069), include that test only when node_modules/playwright is
                # present; otherwise SKIP it loudly (never a spurious FAIL). The node-builtin
                # tests always run. CI runs `npm ci` first, so CI runs all three.
                $coreTests = @(
                    "tests/docs_explorer/docs_explorer_core.test.js",
                    "tests/docs_explorer/knowledge_surfaces.test.js",
                    "tests/docs_explorer/mockup_harness_audit.test.js"
                )
                if (Test-Path (Join-Path $repo "node_modules\playwright")) {
                    $coreTests += "tests/docs_explorer/browser_benchmark.test.js"
                } else {
                    Write-Host "  (skipping browser_benchmark.test.js: node_modules/playwright absent - run 'npm ci'; CI runs it)" -ForegroundColor Yellow
                }
                node --test $coreTests
            }
            Gate "4b. explainer render + accessibility proof" {
                node "tools/verify-explainer-render.js"
            }
        } else {
            Skip "4. docs explorer core contracts" "node is not installed; CI runs this gate"
            Skip "4b. explainer render + accessibility proof" "node is not installed; CI runs this gate"
        }
    }

    Gate "5. knowledge-graph validation" {
        & $pyExe @pyArgs (Join-Path $repo "docs/ai-forward-pack/scripts/docs-graph.py") validate | Out-Null
    }

    Gate "6. vendored-foundation drift" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/foundation-check.py") | Select-Object -Last 1
    }

    Gate "6b. audit log is fully readable" {
        & $pyExe @pyArgs (Join-Path $repo "pack/scripts/audit-log.py") verify
    }

    # Gate 11 (numbered 8b so the always-on budget keeps its place in CI's order).
    # CTX-H: the pack repo is itself a pack install, so its own coordination layer being ON
    # is the only end-to-end proof the install path works. A gate that only ran in a fixture
    # would have passed throughout the two revisions the layer shipped switched off.
    Gate "8b. coordination layer installed (pack-doctor)" {
        $doctor = Join-Path $repo "docs/ai-forward-pack/scripts/pack-doctor.py"
        $raw = & $pyExe @pyArgs $doctor --root $repo --json
        if ($LASTEXITCODE -ne 0 -and -not $raw) { throw "pack-doctor produced no output" }
        $coord = ($raw | ConvertFrom-Json).checks | Where-Object { $_.name -eq "coordination" }
        if (-not $coord) { throw "pack-doctor has no `coordination` check" }
        Write-Host ("  {0}  {1}" -f $coord.status, $coord.detail)
        if ($coord.status -eq "FAIL") {
            Write-Host ("  fix: {0}" -f $coord.fix) -ForegroundColor Red
            throw "the coordination layer is not installed in this repo"
        }
    }

    Gate "7. eval cases well-formed" {
        & $pyExe @pyArgs -c @"
import glob, json, re, sys, os
root = r'$repo'
bad = 0
files = sorted(glob.glob(os.path.join(root, 'pack', 'evals', 'cases', '*.json')))
for f in files:
    try:
        case = json.load(open(f, encoding='utf-8'))
        for a in case.get('assertions', []):
            if 'pattern' in a:
                re.compile(a['pattern'])
    except Exception as e:
        print('  -', os.path.basename(f), e); bad += 1
print(len(files), 'eval cases checked')
sys.exit(1 if bad else 0)
"@
    }

    # FR-072 / P2, reshaped by FR-073. The always-on knowledge set IS the static prefix of
    # every call: re-read every turn, billed every turn, subtracted from the window before the
    # user speaks. Left ungated it re-grows, because each new doc looks free at the moment it
    # is written and nothing reports what it costs.
    #
    # This is a RATCHET, not a ceiling. The first cut used a fixed 45,000-token ceiling and was
    # the wrong shape: two ordinary paragraphs took the set to 97% of budget, so the next
    # routine edit would have red-lighted the build - training the "just raise the ceiling"
    # reflex that the gate exists to break. Growth is fine; UNACKNOWLEDGED growth fails, and
    # the fix is one recorded line in pack/context-budget.json that a reviewer can see.
    #
    # Both halves always run and EITHER fails the gate: a budget that holds only because a
    # persona quietly inherits the whole set is not a budget. Short-circuiting on the first
    # would hide the second until the first was fixed.
    Gate "8. always-on context budget" {
        $budget = Join-Path $repo "pack/scripts/context-budget.py"
        & $pyExe @pyArgs $budget gate
        $ceilingOk = ($LASTEXITCODE -eq 0)
        & $pyExe @pyArgs $budget agents | Select-Object -Last 4
        $lensOk = ($LASTEXITCODE -eq 0)
        # CTX-B / CTX-E: the WHOLE prefix (blocks + always-on + allowances) and every SKILL.md
        # carry their own ratchets. A knowledge-only budget that stayed green while the real
        # prefix was 2.5x larger is the shape this closes.
        & $pyExe @pyArgs $budget prefix --gate | Select-Object -Last 3
        $prefixOk = ($LASTEXITCODE -eq 0)
        & $pyExe @pyArgs $budget skills --gate | Select-Object -Last 2
        $skillsOk = ($LASTEXITCODE -eq 0)
        if (-not ($ceilingOk -and $lensOk -and $prefixOk -and $skillsOk)) { $global:LASTEXITCODE = 1 } else { $global:LASTEXITCODE = 0 }
    }
} finally {
    Pop-Location
}

Write-Host "`n=== summary ===" -ForegroundColor Cyan
foreach ($r in $results) {
    $colour = switch ($r.Status) { "PASS" { "Green" } "SKIP" { "Yellow" } default { "Red" } }
    Write-Host ("  {0,-5} {1}" -f $r.Status, $r.Gate) -ForegroundColor $colour
}

$failed = @($results | Where-Object Status -eq "FAIL")
$skipped = @($results | Where-Object Status -eq "SKIP")
Write-Host ""
if ($failed.Count -gt 0) {
    Write-Host "BUNDLE INCONSISTENT - $($failed.Count) of $($results.Count) gate(s) failed." -ForegroundColor Red
    exit 1
}
if ($skipped.Count -gt 0) {
    Write-Host "BUNDLE CONSISTENT for the gates that ran - but $($skipped.Count) gate(s) were SKIPPED." -ForegroundColor Yellow
    Write-Host "CI runs all $($results.Count). A skip here is not a pass there." -ForegroundColor Yellow
    exit 0
}
Write-Host "BUNDLE CONSISTENT - all $($results.Count) gates passed (the same set CI runs)." -ForegroundColor Green
exit 0
