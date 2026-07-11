<#
.SYNOPSIS
    Install the canonical pack in pack/ into this repo so both Claude Code and
    GitHub Copilot can use it (the "dogfood" install). Regenerates .claude/,
    .github/{instructions,prompts,agents}/, and docs/ from pack/.

.DESCRIPTION
    pack/ is the single source of truth. This script mirrors it into the locations
    each tool reads from, following the deployment map in pack/adapters/INSTALL.md:

        Claude Code targets:
          pack/knowledge/*.md                      -> .claude/knowledge/
          pack/commands/<name>/SKILL.md            -> .claude/skills/<name>/SKILL.md
          pack/adapters/claude-code/agents/*.md    -> .claude/agents/
          pack/adapters/copilot/agents/*_agent.md  -> .claude/agents/   (drop-in, per INSTALL Sec 1.1)

        GitHub Copilot targets (dogfood):
          pack/knowledge/<name>.md (wrapped)       -> .github/instructions/<name>.instructions.md
          pack/adapters/copilot/prompts/*.prompt.md -> .github/prompts/
          pack/adapters/copilot/agents/*_agent.md  -> .github/agents/

        Shared docs:
          pack/templates/*                         -> docs/ai-forward-pack/templates/
          pack/scripts/*                           -> docs/ai-forward-pack/scripts/
          pack/{README,OVERVIEW,research-synthesis}.md, pack/adapters/INSTALL.md
                                                   -> docs/ai-forward-pack/
          pack/templates/docs-explorer.template.html (__PROJECT__ -> AI-Forward)
                                                   -> docs/index.html

    It also re-pastes the AI-FORWARD-PACK managed block into the repo's root CLAUDE.md
    and AGENTS.md (the region between the BEGIN/END markers) so the root entry files stay
    in lockstep with pack/adapters/managed-blocks/. It never touches
    .claude/settings.local.json or docs/docs-index.js (the accumulated, skill-maintained
    knowledge-graph index -- V10), and it does not touch .github/copilot-instructions.md
    (manually maintained, repo-specific) or create CLAUDE.md/AGENTS.md from scratch.

    Run this after editing anything under pack/, then commit pack/, .claude/,
    .github/{instructions,prompts,agents}/, docs/, and CLAUDE.md/AGENTS.md together.

.NOTES
    The full pack (incl. evals, ci) stays in pack/ for distribution; this install
    mirrors both the Claude Code and Copilot surfaces for use inside THIS repo.
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

Write-Host "Syncing pack/ -> .claude/ + .github/{instructions,prompts,agents}/ + docs/ (project: $ProjectName)" -ForegroundColor Cyan

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

# --- .github/instructions (Copilot knowledge wraps — dogfood) -----------------
# Each knowledge doc is wrapped with applyTo frontmatter.
# FOUNDATION.md is a provenance manifest — copy verbatim, not as an instruction.
# csharp-style-guide is scoped to C# files only.
$ghInst = Join-Path $repo ".github\instructions"
Reset-Dir $ghInst
foreach ($kFile in Get-ChildItem (Join-Path $pack "knowledge") -Filter "*.md") {
    if ($kFile.Name -eq "FOUNDATION.md") {
        Copy-Item $kFile.FullName $ghInst -Force
        continue
    }
    $applyTo = if ($kFile.BaseName -eq "csharp-style-guide") { '**/*.cs,**/*.csx' } else { '**' }
    $header  = "---`napplyTo: `"$applyTo`"`n---`n"
    $content = Get-Content $kFile.FullName -Raw
    $dest    = Join-Path $ghInst ($kFile.BaseName + ".instructions.md")
    Set-Content $dest -Value ($header + $content) -Encoding UTF8 -NoNewline
}
$ghInstCount = (Get-ChildItem $ghInst -File).Count
Write-Host "  .github/instructions: $ghInstCount files"

# --- .github/prompts (Copilot skill prompts — dogfood) ------------------------
$ghPrompts = Join-Path $repo ".github\prompts"
Reset-Dir $ghPrompts
Copy-Item (Join-Path $pack "adapters\copilot\prompts\*.prompt.md") $ghPrompts -Force
$ghPromptsCount = (Get-ChildItem $ghPrompts -File).Count
Write-Host "  .github/prompts: $ghPromptsCount prompts"

# --- .github/agents (Copilot agents — dogfood) --------------------------------
# These carry no tools: line (per INSTALL §1.2) — Copilot drops them in as-is.
$ghAgents = Join-Path $repo ".github\agents"
Reset-Dir $ghAgents
Copy-Item (Join-Path $pack "adapters\copilot\agents\*_agent.md") $ghAgents -Force
$ghAgentsCount = (Get-ChildItem $ghAgents -File).Count
Write-Host "  .github/agents: $ghAgentsCount agents"

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

# --- root managed blocks (CLAUDE.md + AGENTS.md) -------------------------------
# Keep the AI-FORWARD-PACK block in the repo's root entry files in lockstep with the
# pack source. We replace the marked region wholesale (per INSTALL Sec 1.1) but never
# create these files automatically -- their preamble is hand-authored.
function Update-ManagedBlock([string]$file, [string]$blockFile) {
    $label = Split-Path $file -Leaf
    if (-not (Test-Path $file)) { Write-Host "  ${label}: not present (skipped)"; return }
    $block = (Get-Content $blockFile -Raw).TrimEnd("`r", "`n")
    $content = Get-Content $file -Raw
    $rx = '(?s)<!-- AI-FORWARD-PACK:BEGIN.*?AI-FORWARD-PACK:END -->'
    if ($content -match $rx) {
        $new = [regex]::Replace($content, $rx, { param($m) $block })
        Set-Content $file -Value $new -Encoding UTF8 -NoNewline
        Write-Host "  ${label}: managed block re-pasted"
    } else {
        Add-Content $file -Value ("`n" + $block) -Encoding UTF8
        Write-Host "  ${label}: managed block appended"
    }
}
Update-ManagedBlock (Join-Path $repo "CLAUDE.md")  (Join-Path $pack "adapters\managed-blocks\CLAUDE.block.md")
Update-ManagedBlock (Join-Path $repo "AGENTS.md")  (Join-Path $pack "adapters\managed-blocks\AGENTS.block.md")

# Regenerate the whole-pack navigable/searchable index that web/index.html renders (freshness contract).
$buildWebIndex = Join-Path $repo "tools\build-web-index.py"
if (Test-Path $buildWebIndex) {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pyCmd) { $pyCmd = Get-Command python3 -ErrorAction SilentlyContinue }
    if ($pyCmd) { & $pyCmd.Source $buildWebIndex | ForEach-Object { Write-Host "  $_" } }
    else { Write-Host "  web/pack-index.js skipped (python not found)" -ForegroundColor Yellow }
}

Write-Host "Done. Review changes, then commit pack/ + .claude/ + .github/{instructions,prompts,agents}/ + docs/ + CLAUDE.md/AGENTS.md together." -ForegroundColor Green
