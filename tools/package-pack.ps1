<#
.SYNOPSIS
    Build a distributable ai-forward-pack.zip from pack/ for sharing.

.DESCRIPTION
    Stages pack/ under a top-level ai-forward-pack/ folder (so the archive matches the
    pack's own INSTALL.md expectations) and writes dist/ai-forward-pack.zip.
    dist/ is gitignored -- the artifact is a build output, not source.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$pack = Join-Path $repo "pack"
$dist = Join-Path $repo "dist"
$stage = Join-Path $dist "ai-forward-pack"
$zip = Join-Path $dist "ai-forward-pack.zip"

if (-not (Test-Path $pack)) { throw "pack/ not found at $pack." }

New-Item -ItemType Directory -Force -Path $dist | Out-Null
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
if (Test-Path $zip)   { Remove-Item $zip -Force }

New-Item -ItemType Directory -Force -Path $stage | Out-Null
Copy-Item (Join-Path $pack "*") $stage -Recurse -Force
Compress-Archive -Path $stage -DestinationPath $zip -Force
Remove-Item $stage -Recurse -Force

$size = [math]::Round((Get-Item $zip).Length / 1KB, 1)
Write-Host "Wrote $zip ($size KB)" -ForegroundColor Green
