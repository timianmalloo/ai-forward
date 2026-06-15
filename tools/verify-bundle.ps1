<#
.SYNOPSIS
    Verify the AI-Forward bundle is internally consistent — the one-command proof.

.DESCRIPTION
    Runs the full source-of-truth checks after a pack edit, in order, and stops on the
    first failure. This is the "proof that it is consistent" that /extendaibundle (and any
    pack edit) ends on:

        1. tools/sync-pack.ps1            regenerate both tool surfaces + re-paste managed blocks
        2. tools/check-consistency.py     counts, skill<->prompt parity, managed-block lists, prose
        3. pack/scripts/foundation-check.py   vendored-foundation drift
        4. eval cases                     valid JSON + compilable regex
        5. git status                     report whether the tree is clean after sync (drift signal)

    Exit 0 = consistent. Nonzero = a check failed (its output is shown).

.NOTES
    Requires pwsh + Python 3.8+. Run from anywhere in the repo.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$fail = 0

function Step([string]$label, [scriptblock]$action) {
    Write-Host "`n=== $label ===" -ForegroundColor Cyan
    & $action
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $label (exit $LASTEXITCODE)" -ForegroundColor Red
        $script:fail++
    }
}

Step "1. sync pack -> .claude/ + .github/ + docs/" { pwsh (Join-Path $repo "tools\sync-pack.ps1") | Out-Null; $global:LASTEXITCODE = $LASTEXITCODE }
Step "2. consistency (counts, parity, managed-block lists, prose)" { python (Join-Path $repo "tools\check-consistency.py") }
Step "3. vendored-foundation drift" { python (Join-Path $repo "pack\scripts\foundation-check.py") | Select-Object -Last 1 }
Step "4. eval cases well-formed" {
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

Write-Host "`n=== 5. git status (clean after sync = no drift) ===" -ForegroundColor Cyan
Push-Location $repo
$dirty = git status --porcelain
Pop-Location
if ($dirty) {
    Write-Host "working tree has changes after sync (review before commit):" -ForegroundColor Yellow
    $dirty | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "clean"
}

Write-Host ""
if ($fail -gt 0) {
    Write-Host "BUNDLE INCONSISTENT - $fail check(s) failed." -ForegroundColor Red
    exit 1
}
Write-Host "BUNDLE CONSISTENT - all checks passed." -ForegroundColor Green
exit 0
