#Requires -Version 7.0
<#
.SYNOPSIS
  Stand up BOTH AI-Forward knowledge-graph lenses - Obsidian (docs) and Graphify (code) - in one or more of your repositories.

.DESCRIPTION
  Run this from an ai-forward clone. For each target repo it:

    1. verifies the repo actually has the pack installed (docs/ai-forward-pack/)
    2. copies/refreshes docs/ai-forward-pack/scripts/obsidian-setup.py from this clone
    3. derives the knowledge graph, so the lens has something to read
    4. installs the Obsidian desktop app once, if missing (-InstallApp)
    5. writes the committed vault config + the non-canonical lens notes + the
       .gitignore commit/ignore split
    6. optionally downloads the plugin code (-FetchPlugins), which is third-party
       JavaScript and therefore an explicit opt-in
    7. runs the dependency-free structural analysis and saves it as a lens
    8. re-derives + validates so the new lens notes enter the index

  Everything is idempotent: re-running reports "unchanged" and changes nothing.
  Nothing here edits artifact frontmatter or docs-index.js by hand - docs-graph.py
  remains the only writer of the graph (V18), and Obsidian remains a reader (OB1).

.PARAMETER Repo
  One or more target repository paths. Defaults to this ai-forward clone.

.PARAMETER InstallApp
  Install the Obsidian desktop app if it is not already present (winget / brew / flatpak).

.PARAMETER FetchPlugins
  Download plugin releases directly instead of letting Obsidian's plugin browser
  install them with your consent. Explicit opt-in - this fetches third-party code.

.PARAMETER AllPlugins
  Include the optional-tier plugins (Juggl, ExcaliBrain, Smart Connections) as well
  as the core three (Dataview, Knowledge Graph Analysis, Breadcrumbs).

.PARAMETER DryRun
  Print the plan and write nothing.

.EXAMPLE
  pwsh tools/setup-knowledge-graphs.ps1 -Repo C:\projects\meridian-finance-planner -InstallApp

.EXAMPLE
  pwsh tools/setup-knowledge-graphs.ps1 `
      -Repo C:\projects\meridian-finance-planner, C:\projects\TheTerrace `
      -FetchPlugins -AllPlugins

.NOTES
  A target repo must already have the pack installed and be on a revision that ships
  obsidian-setup.py (>= 19). If it is older, run /updatepack there first - this script
  copies the one script it needs but does not perform a full pack update.
#>
[CmdletBinding()]
param(
    [string[]] $Repo,
    [switch]   $InstallApp,
    [switch]   $FetchPlugins,
    [switch]   $AllPlugins,
    [switch]   $Graphify,
    [switch]   $SkipObsidian,
    [switch]   $DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$packRoot   = Split-Path -Parent $PSScriptRoot
$sourceTools = @('obsidian-setup.py', 'graphify-setup.py') | ForEach-Object {
    $p = Join-Path $packRoot "pack\scripts\$_"
    if (-not (Test-Path $p)) { throw "Run this from an ai-forward clone - pack/scripts/$_ not found at $p" }
    $p
}
$sourceTool = $sourceTools[0]
if (-not $Repo) { $Repo = @($packRoot) }

# `pwsh script.ps1 -Repo A,B` passes "A,B" as ONE literal string, because pwsh is invoked as a
# native executable and does not re-parse the argument as a PowerShell array. That is the most
# natural way to call this, so accept it rather than failing with an unhelpful "path not found".
$Repo = $Repo | ForEach-Object { $_ -split ',' } | Where-Object { $_ -and $_.Trim() } | ForEach-Object { $_.Trim() }

# Resolve a python interpreter once rather than assuming `python3` exists on Windows.
$python = $null
foreach ($candidate in 'python', 'python3', 'py') {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $python = $candidate; break }
}
if (-not $python) { throw 'No Python interpreter found on PATH (tried python, python3, py).' }

function Invoke-Step {
    param([string] $Label, [string[]] $Arguments, [string] $WorkingDirectory, [switch] $AllowFailure)
    Write-Host "    $Label" -ForegroundColor DarkGray
    if ($DryRun) { Write-Host "      (dry run) $python $($Arguments -join ' ')" -ForegroundColor DarkGray; return $true }
    Push-Location $WorkingDirectory
    try {
        & $python @Arguments 2>&1 | ForEach-Object { Write-Host "      $_" }
        $ok = ($LASTEXITCODE -eq 0)
        if (-not $ok -and -not $AllowFailure) { Write-Host "      exit $LASTEXITCODE" -ForegroundColor Yellow }
        return $ok
    } finally { Pop-Location }
}

$summary = [System.Collections.Generic.List[object]]::new()

foreach ($target in $Repo) {
    $requested = $target          # keep the original: the resolve below nulls $target on failure,
                                  # and an error message that has lost its subject is useless
    $target = (Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue)?.Path
    if (-not $target) {
        Write-Host "SKIP  $requested - path not found" -ForegroundColor Yellow
        $summary.Add([pscustomobject]@{ Repo = $requested; Status = 'not found' }); continue
    }

    Write-Host ""
    Write-Host "=== $target ===" -ForegroundColor Cyan

    $scriptsDir = Join-Path $target 'docs\ai-forward-pack\scripts'
    if (-not (Test-Path (Join-Path $target 'docs\ai-forward-pack'))) {
        Write-Host "  SKIP - no docs/ai-forward-pack/ (pack not installed). Run /addpacktorepo first." -ForegroundColor Yellow
        $summary.Add([pscustomobject]@{ Repo = $target; Status = 'pack not installed' }); continue
    }

    # 1. refresh the scripts we need (idempotent; content-compared, not blindly copied)
    foreach ($src in $sourceTools) {
        $name = Split-Path -Leaf $src
        $dest = Join-Path $scriptsDir $name
        $needsCopy = -not (Test-Path $dest) -or ((Get-FileHash $src).Hash -ne (Get-FileHash $dest).Hash)
        if ($needsCopy) {
            Write-Host "    $name -> docs/ai-forward-pack/scripts/" -ForegroundColor DarkGray
            if (-not $DryRun) {
                New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null
                Copy-Item $src $dest -Force
            }
        } else {
            Write-Host "    $name already current" -ForegroundColor DarkGray
        }
    }

    $tool  = 'docs/ai-forward-pack/scripts/obsidian-setup.py'
    $gtool = 'docs/ai-forward-pack/scripts/graphify-setup.py'
    $graph = 'docs/ai-forward-pack/scripts/docs-graph.py'
    $dry   = if ($DryRun) { @('--dry-run') } else { @() }

    # 2. the lens reads the graph, so the graph must exist first
    if (Test-Path (Join-Path $target 'docs\ai-forward-pack\scripts\docs-graph.py')) {
        Invoke-Step 'derive the knowledge graph' @($graph, 'derive') $target -AllowFailure | Out-Null
    }

    # 3. Obsidian lens: app, config, plugins, analysis  (skip with -SkipObsidian)
    if (-not $SkipObsidian) {
        if ($InstallApp)   { Invoke-Step 'install Obsidian'        @($tool, '--install-app', '--yes')            $target -AllowFailure | Out-Null }
        $initArgs = @($tool, '--init') + $(if ($AllPlugins) { @('--all-plugins') } else { @() }) + $dry
        Invoke-Step 'write vault config + lenses' $initArgs $target | Out-Null
        if ($FetchPlugins) {
            $fetchArgs = @($tool, '--fetch-plugins') + $(if ($AllPlugins) { @('--all-plugins') } else { @() }) + $dry
            Invoke-Step 'fetch plugin releases (third-party code)' $fetchArgs $target -AllowFailure | Out-Null
        }
        Invoke-Step 'structural analysis -> docs/lenses/graph-insight.md' (@($tool, '--analyze', '--write') + $dry) $target -AllowFailure | Out-Null
    }

    # 3b. Graphify code graph (opt-in with -Graphify). The ignore rules are repo-kind aware:
    #     in a CONSUMING repo .claude/ and docs/ai-forward-pack/ are the only copy and are kept.
    if ($Graphify) {
        Invoke-Step 'install graphifyy + register the /graphify skill' (@($gtool, '--install') + $dry) $target -AllowFailure | Out-Null
        Invoke-Step 'write .graphifyignore (repo-kind aware de-dup)'   (@($gtool, '--init')    + $dry) $target -AllowFailure | Out-Null
        Invoke-Step 'build the code graph (full re-extraction)'        (@($gtool, '--build')   + $dry) $target -AllowFailure | Out-Null
        Invoke-Step 'join code <-> docs -> docs/lenses/code-doc-join.md' (@($gtool, '--join')  + $dry) $target -AllowFailure | Out-Null
    }

    # 4. the new lens notes are artifacts - index and validate them (V10/V11)
    $valid = $true
    if (-not $DryRun -and (Test-Path (Join-Path $target 'docs\ai-forward-pack\scripts\docs-graph.py'))) {
        Invoke-Step 're-derive the index' @($graph, 'derive') $target -AllowFailure | Out-Null
        $valid = Invoke-Step 'validate the graph' @($graph, 'validate') $target -AllowFailure
    }

    $summary.Add([pscustomobject]@{
        Repo   = $target
        Status = if ($DryRun) { 'dry run' } elseif ($valid) { 'ok' } else { 'graph validate failed' }
    })
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
$summary | Format-Table -AutoSize

Write-Host @"
Next, per repo:
  1. Obsidian -> 'Open folder as vault' -> select <repo>\docs
  2. Settings -> Community plugins -> Browse -> install the enabled list
     (skip if you used -FetchPlugins)
  3. Open the graph view: it is coloured by artifact type, with draft/superseded
     overlaid last.
  4. Read docs/lenses/graph-insight.md for hubs, bridges, orphans and structural gaps.

Reminders (obsidian-lens.md):
  * Obsidian is a READER. Frontmatter is the record; docs-graph.py is the only writer.
  * No Dataview query may be load-bearing in a canonical artifact - queries live in docs/lenses/.
  * Commit the vault config; the .gitignore rules keep workspace state and plugin code local.
  * AI plugin features send note content to a third party - a Privacy-lens decision (OB11).
"@ -ForegroundColor DarkGray
