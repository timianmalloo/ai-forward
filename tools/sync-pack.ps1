<#
.SYNOPSIS
    Install the canonical pack in pack/ into this repo so Claude Code can use it
    (the "dogfood" install). Regenerates .claude/ and docs/ from pack/.

.DESCRIPTION
    pack/ is the single source of truth. This script is the one command that mirrors
    it into the locations Claude Code (and the Docs Explorer) read from, following the
    deployment map in pack/adapters/INSTALL.md (Claude Code targets only):

        pack/knowledge/*.md                      -> .claude/knowledge/
        pack/commands/<name>/SKILL.md            -> .claude/skills/<name>/SKILL.md
        pack/adapters/claude-code/agents/*.md    -> .claude/agents/
        pack/adapters/copilot/agents/*_agent.md  -> .claude/agents/   (drop-in, per INSTALL Sec 1.1)
        pack/templates/*                         -> docs/ai-forward-pack/templates/
        pack/scripts/*                           -> docs/ai-forward-pack/scripts/
        pack/{README,OVERVIEW,research-synthesis}.md, pack/adapters/INSTALL.md
                                                 -> docs/ai-forward-pack/
        pack/templates/docs-explorer.template.html (__PROJECT__ -> AI-Forward)
                                                 -> docs/index.html

    It never touches .claude/settings.local.json or docs/docs-index.js (the accumulated,
    skill-maintained knowledge-graph index -- V10).

    Run this after editing anything under pack/, then commit both pack/ and the
    regenerated .claude/ + docs/.

.NOTES
    The full pack (incl. all Copilot adapters, evals, ci) stays in pack/ for distribution;
    this install only mirrors the Claude Code surface for use inside THIS repo.
#>
[CmdletBinding()]
param(
    [string]$ProjectName = "AI-Forward"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$pack = Join-Path $repo "pack"

if (-not (Test-Path $pack)) { throw "pack/ not found at $pack -- run from the repo root." }

function Reset-Dir([string]$path) {
    if (Test-Path $path) { Remove-Item $path -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

Write-Host "Syncing pack/ -> .claude/ + docs/ (project: $ProjectName)" -ForegroundColor Cyan

# --- .claude/knowledge ---------------------------------------------------------
$kDst = Join-Path $repo ".claude\knowledge"
Reset-Dir $kDst
Copy-Item (Join-Path $pack "knowledge\*.md") $kDst -Force
$kCount = (Get-ChildItem $kDst -File).Count
Write-Host "  knowledge: $kCount docs"

# --- .claude/skills ------------------------------------------------------------
$sDst = Join-Path $repo ".claude\skills"
Reset-Dir $sDst
$skillCount = 0
foreach ($cmd in Get-ChildItem (Join-Path $pack "commands") -Directory) {
    $skill = Join-Path $cmd.FullName "SKILL.md"
    if (Test-Path $skill) {
        $target = Join-Path $sDst $cmd.Name
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Copy-Item $skill $target -Force
        $skillCount++
    }
}
Write-Host "  skills: $skillCount"

# --- .claude/agents (12 claude-code lenses + 11 drop-in copilot adversaries) ----
$aDst = Join-Path $repo ".claude\agents"
Reset-Dir $aDst
Copy-Item (Join-Path $pack "adapters\claude-code\agents\*.md") $aDst -Force
Copy-Item (Join-Path $pack "adapters\copilot\agents\*_agent.md") $aDst -Force
$aCount = (Get-ChildItem $aDst -File).Count
Write-Host "  agents: $aCount"

# --- docs/ai-forward-pack (templates, scripts, pack docs) ----------------------
$docPack = Join-Path $repo "docs\ai-forward-pack"
Reset-Dir (Join-Path $docPack "templates")
Reset-Dir (Join-Path $docPack "scripts")
Copy-Item (Join-Path $pack "templates\*") (Join-Path $docPack "templates") -Recurse -Force
Copy-Item (Join-Path $pack "scripts\*")   (Join-Path $docPack "scripts")   -Recurse -Force
Copy-Item (Join-Path $pack "README.md")              $docPack -Force
Copy-Item (Join-Path $pack "OVERVIEW.md")            $docPack -Force
Copy-Item (Join-Path $pack "research-synthesis.md")  $docPack -Force
Copy-Item (Join-Path $pack "adapters\INSTALL.md")    $docPack -Force
Write-Host "  docs/ai-forward-pack: templates + scripts + pack docs"

# --- docs/index.html (Docs Explorer; regenerated from template) ----------------
# docs/docs-index.js is intentionally NOT created/overwritten -- skills accumulate it (V10).
$explorerSrc = Join-Path $pack "templates\docs-explorer.template.html"
$explorerDst = Join-Path $repo "docs\index.html"
(Get-Content $explorerSrc -Raw).Replace("__PROJECT__", $ProjectName) |
    Set-Content $explorerDst -Encoding UTF8 -NoNewline
Write-Host "  docs/index.html (Docs Explorer)"

Write-Host "Done. Review changes, then commit pack/ + .claude/ + docs/ together." -ForegroundColor Green
