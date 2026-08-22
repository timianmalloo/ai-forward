<#
.SYNOPSIS
    Verify the AI-Forward bundle the same way CI does — the one-command proof.
.DESCRIPTION
    Runs the gates from .github/workflows/pack-consistency.yml, in CI's order, and reports
    every failure rather than stopping at the first, so one run tells you everything that is
    wrong instead of only the first thing.

        1.  Count & skill-list consistency     tools/check-consistency.py
        2.  Source<->install drift             sync-pack.ps1 THEN git diff --exit-code
        3.  Python test suite                  pytest tests
        4.  Docs Explorer core contracts       node --test (see the gate-4 note)
        4b. Explainer render + a11y proof      tools/verify-explainer-render.js
        5.  Knowledge-graph validation         docs-graph.py validate
        6.  Vendored-foundation drift          foundation-check.py
        7.  Eval cases well-formed             JSON + compilable regex

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
        python (Join-Path $repo "tools\check-consistency.py")
    }

    # FR-057: sync AND compare. The comparison is the gate; the sync alone is only a repair.
    Gate "2. source<->install drift (pack/ is the only source of truth)" {
        pwsh (Join-Path $repo "tools\sync-pack.ps1") | Out-Null
        $paths = @(".claude", ".github/instructions", ".github/prompts", ".github/agents",
                   "docs", "web", "CLAUDE.md", "AGENTS.md")
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
        Gate "3. python test suite" { python -m pytest tests -q }
        $node = Get-Command node -ErrorAction SilentlyContinue
        if ($node) {
            Gate "4. docs explorer core contracts" {
                # Invoked directly, not through `npm run` - see the gate-4 note above.
                node --test `
                    "tests/docs_explorer/docs_explorer_core.test.js" `
                    "tests/docs_explorer/browser_benchmark.test.js" `
                    "tests/docs_explorer/knowledge_surfaces.test.js"
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
        python (Join-Path $repo "docs\ai-forward-pack\scripts\docs-graph.py") validate | Out-Null
    }

    Gate "6. vendored-foundation drift" {
        python (Join-Path $repo "pack\scripts\foundation-check.py") | Select-Object -Last 1
    }

    Gate "7. eval cases well-formed" {
        python -c @"
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
