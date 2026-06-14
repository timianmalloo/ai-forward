<#
.SYNOPSIS
    Refresh the embedded pack snapshot inside web/ai-forward-pack-overview.jsx.

.DESCRIPTION
    The overview .jsx is a self-contained page that lets a viewer download the whole
    pack: it carries the pack zipped and base64-encoded in a single line,
    `const PACK_B64 = "..."`. That snapshot does NOT track edits to pack/ on its own.

    This script re-zips pack/ (staged under a top-level ai-forward-pack/ folder, the same
    shape tools/package-pack.ps1 produces), base64-encodes it, and rewrites the PACK_B64
    line in place. Everything else in the .jsx (the prose, counts, layout) is left as-is —
    update that by hand if the pack's headline numbers change.

    Run this before sharing the .jsx so its download matches the current pack/.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$pack = Join-Path $repo "pack"
$jsx  = Join-Path $repo "web\ai-forward-pack-overview.jsx"

if (-not (Test-Path $pack)) { throw "pack/ not found at $pack." }
if (-not (Test-Path $jsx))  { throw "overview not found at $jsx." }

# --- Build the pack zip into a temp file (top-level folder: ai-forward-pack/) ---
$tmp   = Join-Path ([IO.Path]::GetTempPath()) ("aip-overview-" + [Guid]::NewGuid().ToString("N"))
$stage = Join-Path $tmp "ai-forward-pack"
$zip   = Join-Path $tmp "ai-forward-pack.zip"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Copy-Item (Join-Path $pack "*") $stage -Recurse -Force
Compress-Archive -Path $stage -DestinationPath $zip -Force

# --- Encode and patch the single PACK_B64 line ---------------------------------
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($zip))
$content = [IO.File]::ReadAllText($jsx)

$pattern  = 'const PACK_B64 = "[^"]*";'
if (-not [regex]::IsMatch($content, $pattern)) {
    Remove-Item $tmp -Recurse -Force
    throw ('Could not find the PACK_B64 assignment line in ' + $jsx + '.')
}
$replacement = [System.Text.RegularExpressions.MatchEvaluator]{ param($m) "const PACK_B64 = `"$b64`";" }
$content = [regex]::Replace($content, $pattern, $replacement)

# Write back with LF endings (.gitattributes normalizes anyway; keep the working tree clean).
[IO.File]::WriteAllText($jsx, ($content -replace "`r`n", "`n"), (New-Object System.Text.UTF8Encoding($false)))

Remove-Item $tmp -Recurse -Force
$sizeKB = [math]::Round($b64.Length * 3 / 4 / 1024, 1)
Write-Host "Refreshed $jsx (embedded pack ~$sizeKB KB)." -ForegroundColor Green
