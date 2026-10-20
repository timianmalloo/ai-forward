<#
.SYNOPSIS
    Verify the AI-Forward bundle the same way CI does - the one-command proof.
.DESCRIPTION
    Runs every gate in tools/gates.py, the one list CI runs too (FR-091), and reports every
    failure rather than stopping at the first. `python tools/gates.py list` prints the gates;
    CI runs `gates.py run --ci` per OS, where a skipped gate counts as a failure.

    FR-057 - gate 2 syncs AND compares: regeneration without a comparison silently repairs the
    tree and reports a pass, which is how a stale web/pack-index.js once passed here and failed
    in CI. Gate 4 runs node directly, not through `npm run`, whose child-shell PATH can differ
    from yours (FR-055 / PACK-C); without node it is SKIPPED loudly, never counted as a pass.

    This used to hold its own copy of the gates, and CI held another; the copies drifted (CI ran
    two of the four context-budget ratchets). Both now call the same list.
.NOTES
    Requires pwsh + Python 3.8+. Node is optional (gate 4 skips, loudly). Run from anywhere.
#>
[CmdletBinding()]
param(
    [switch]$SkipTests   # inner-loop convenience: skip the test suites. Prints what it skipped.
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

# One interpreter, resolved ONCE (class PLAT-A). python.org Windows ships no `python3`;
# stock macOS ships no `python`. The probe requires real Python 3 output, so the Windows Store
# `python3` alias (exit 9009, "Python was not found") is rejected rather than trusted.
$pyExe = $null; $pyArgs = @()
foreach ($c in @(@{ exe = 'python3'; args = @() }, @{ exe = 'python'; args = @() }, @{ exe = 'py'; args = @('-3') })) {
    if (-not (Get-Command $c.exe -ErrorAction SilentlyContinue)) { continue }
    try { $probe = (& $c.exe @($c.args) --version 2>&1 | Out-String).Trim() } catch { continue }
    if ($LASTEXITCODE -eq 0 -and $probe -like 'Python 3*') { $pyExe = $c.exe; $pyArgs = $c.args; break }
}
if (-not $pyExe) { throw 'No working Python 3 found as python3, python, or py -3 (pack-doctor names the working form).' }

$gateArgs = @((Join-Path $repo "tools/gates.py"), "run")
if ($SkipTests) { $gateArgs += "--skip-tests" }
& $pyExe @pyArgs @gateArgs
exit $LASTEXITCODE
