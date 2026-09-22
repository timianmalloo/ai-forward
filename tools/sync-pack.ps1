<#
.SYNOPSIS
    Install the canonical pack in pack/ into this repo so Claude Code, GitHub
    Copilot, and Grok Build can use it (the "dogfood" install). Regenerates
    .claude/, .github/{instructions,prompts,agents}/, .grok/{skills,agents,hooks,rules}/,
    and docs/ from pack/.

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

# One interpreter, resolved ONCE (class PLAT-A): python3 -> python -> py -3, accepting only
# real Python 3 output (the Windows Store `python3` alias exits 9009). The three derived
# indexes below used to probe `python` then `python3` each on their own and skip SILENTLY
# when neither matched - which gate 2 then reported as drift.
$pyExe = $null; $pyArgs = @()
foreach ($c in @(@{ exe = 'python3'; args = @() }, @{ exe = 'python'; args = @() }, @{ exe = 'py'; args = @('-3') })) {
    if (-not (Get-Command $c.exe -ErrorAction SilentlyContinue)) { continue }
    try { $probe = (& $c.exe @($c.args) --version 2>&1 | Out-String).Trim() } catch { continue }
    if ($LASTEXITCODE -eq 0 -and $probe -like 'Python 3*') { $pyExe = $c.exe; $pyArgs = $c.args; break }
}
if (-not $pyExe) { throw 'No working Python 3 found as python3, python, or py -3 - the derived indexes cannot be regenerated.' }

function Reset-Dir([string]$path) {
    if (Test-Path $path) { Remove-Item $path -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

Write-Host "Syncing pack/ -> .claude/ + .github/{instructions,prompts,agents}/ + .grok/ + .agents/ + docs/ (project: $ProjectName)" -ForegroundColor Cyan

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
        # The whole skill directory: SKILL.md is the contract and reference/*.md is the stage
        # detail it reads on demand (progressive disclosure, CTX-E). Copying only SKILL.md
        # would ship a contract whose stages point at files that are not there.
        Copy-Item (Join-Path $cmd.FullName "*") $target -Recurse -Force
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

# --- .github/{instructions,knowledge} (Copilot knowledge surfaces — dogfood) ---
# FR-072 / P1. Every knowledge doc DECLARES its own load scope in frontmatter
# (`load: always | glob | skill | reference`); this step routes on that declaration
# instead of hardcoding `applyTo: "**"` for all of them.
#
# Why it matters: `applyTo: "**"` means "attach on every request". Shipping it on 37 of
# 39 docs made the whole 184K-token knowledge set the STATIC PREFIX of every call —
# 63% of all input tokens in a profiled session, and a context ceiling that failed 27 of
# 39 delegated runs outright on a flash-class model. Scope is the fix; nothing is deleted.
#
#   load: always     -> .github/instructions/, applyTo "**"
#   load: glob       -> .github/instructions/, applyTo the doc's declared pattern
#   load: skill      -> .github/knowledge/, read on demand by the naming skill
#   load: reference  -> .github/knowledge/, fetched only when consulted
#
# The source frontmatter is STRIPPED at this boundary and replaced by the applyTo wrap —
# a doc that already carried frontmatter previously ended up with two stacked blocks
# (session-worktree-discipline did), of which a reader parses only the first.
# FOUNDATION.md is the vendored provenance manifest: always-loaded, copied verbatim,
# and deliberately carries no frontmatter of its own.
function Get-LoadScope([string]$path) {
    $raw = Get-Content $path -Raw
    $fm  = [regex]::Match($raw, '(?s)^---\r?\n(.*?)\r?\n---\r?\n')
    if (-not $fm.Success) { return @{ load = ""; applyTo = ""; body = $raw } }
    $meta = $fm.Groups[1].Value
    return @{
        load    = ([regex]::Match($meta, '(?m)^load:\s*(\S+)')).Groups[1].Value
        applyTo = ([regex]::Match($meta, '(?m)^applyTo:\s*"([^"]*)"')).Groups[1].Value
        body    = $raw.Substring($fm.Length)
    }
}

$ghInst = Join-Path $repo ".github\instructions"
$ghKnow = Join-Path $repo ".github\knowledge"
Reset-Dir $ghInst
Reset-Dir $ghKnow
foreach ($kFile in Get-ChildItem (Join-Path $pack "knowledge") -Filter "*.md") {
    if ($kFile.Name -eq "FOUNDATION.md") {
        Copy-Item $kFile.FullName $ghInst -Force
        continue
    }
    $scope = Get-LoadScope $kFile.FullName
    switch ($scope.load) {
        "always" {
            $header = "---`napplyTo: `"**`"`n---`n"
            Set-Content (Join-Path $ghInst ($kFile.BaseName + ".instructions.md")) `
                -Value ($header + $scope.body) -Encoding UTF8 -NoNewline
        }
        "glob" {
            if (-not $scope.applyTo) { throw "$($kFile.Name): load: glob with no applyTo pattern." }
            $header = "---`napplyTo: `"$($scope.applyTo)`"`n---`n"
            Set-Content (Join-Path $ghInst ($kFile.BaseName + ".instructions.md")) `
                -Value ($header + $scope.body) -Encoding UTF8 -NoNewline
        }
        { $_ -in @("skill", "reference") } {
            Copy-Item $kFile.FullName (Join-Path $ghKnow $kFile.Name) -Force
        }
        default { throw "$($kFile.Name): missing or unknown `load:` scope '$($scope.load)'. Expected always|glob|skill|reference." }
    }
}
$ghInstCount = (Get-ChildItem $ghInst -File).Count
$ghKnowCount = (Get-ChildItem $ghKnow -File).Count
Write-Host "  .github/instructions: $ghInstCount always/glob-scoped"
Write-Host "  .github/knowledge:    $ghKnowCount on-demand (skill/reference)"

# --- .github/prompts (Copilot skill prompts — dogfood) ------------------------
$ghPrompts = Join-Path $repo ".github\prompts"
Reset-Dir $ghPrompts
Copy-Item (Join-Path $pack "adapters\copilot\prompts\*.prompt.md") $ghPrompts -Force
$ghPromptsCount = (Get-ChildItem $ghPrompts -File).Count
Write-Host "  .github/prompts: $ghPromptsCount prompts"

# --- .github/agents (Copilot agents — dogfood) --------------------------------
# The deployment map promises BOTH peers and adversaries on this surface. The
# copilot/agents/*_agent.md files already carry no tools: line and drop in as-is.
# The claude-code/agents/*.md files are the other 12 personas; they carry a tools:
# line that Copilot ignores (and which is therefore misleading), so it is stripped
# at this boundary per INSTALL §1.2 — one source per persona, one frontmatter edit.
# Shipping only the first group left Copilot with 11 of 23 personas (FR-032).
$ghAgents = Join-Path $repo ".github\agents"
Reset-Dir $ghAgents
# Copilot's documented convention is `<name>.agent.md` (docs.github.com, "Create custom
# agents for CLI"). `*_agent.md` is the pack's SOURCE naming (INSTALL 1.2), so the deploy
# step RENAMES rather than copying verbatim - shipping the source name deployed a
# non-standard filename that happened to load, which is not the same as being correct.
foreach ($cop in Get-ChildItem (Join-Path $pack "adapters\copilot\agents") -Filter *_agent.md -File) {
    $name = $cop.BaseName -replace '_agent$', ''
    Copy-Item $cop.FullName (Join-Path $ghAgents ("{0}.agent.md" -f $name)) -Force
}
foreach ($cc in Get-ChildItem (Join-Path $pack "adapters\claude-code\agents") -Filter *.md -File) {
    $dest = Join-Path $ghAgents ("{0}.agent.md" -f $cc.BaseName)
    $lines = Get-Content $cc.FullName
    # Drop the frontmatter `tools:` line (and any indented continuation of it).
    $out = New-Object System.Collections.Generic.List[string]
    $inTools = $false
    foreach ($line in $lines) {
        if ($line -match '^tools:') { $inTools = $true; continue }
        if ($inTools -and $line -match '^\s+\S') { continue }
        $inTools = $false
        $out.Add($line)
    }
    Set-Content -Path $dest -Value $out -Encoding UTF8
}
$ghAgentsCount = (Get-ChildItem $ghAgents -File).Count
Write-Host "  .github/agents: $ghAgentsCount agents"

# --- .grok/{skills,agents,hooks,rules} (Grok Build — dogfood, INSTALL 1.7) -----
# Native destinations so the pack still works when [compat.claude] skills = false.
# Knowledge is NOT copied into .grok/rules/ (CTX-B: Grok loads every *.md there
# on every turn). The path map is the only rules file.
$grokSkills = Join-Path $repo ".grok\skills"
Reset-Dir $grokSkills
$grokSkillCount = 0
foreach ($cmd in Get-ChildItem (Join-Path $pack "commands") -Directory) {
    $skill = Join-Path $cmd.FullName "SKILL.md"
    if (Test-Path $skill) {
        $target = Join-Path $grokSkills $cmd.Name
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Copy-Item (Join-Path $cmd.FullName "*") $target -Recurse -Force
        $grokSkillCount++
    }
}
Write-Host "  .grok/skills: $grokSkillCount"

function Write-StrippedAgent([string]$src, [string]$dest) {
    $lines = Get-Content $src
    $out = New-Object System.Collections.Generic.List[string]
    $inTools = $false
    foreach ($line in $lines) {
        if ($line -match '^tools:') { $inTools = $true; continue }
        if ($inTools -and $line -match '^\s+\S') { continue }
        $inTools = $false
        $out.Add($line)
    }
    Set-Content -Path $dest -Value $out -Encoding UTF8
}
$grokAgents = Join-Path $repo ".grok\agents"
Reset-Dir $grokAgents
foreach ($cc in Get-ChildItem (Join-Path $pack "adapters\claude-code\agents") -Filter *.md -File) {
    Write-StrippedAgent $cc.FullName (Join-Path $grokAgents $cc.Name)
}
foreach ($cop in Get-ChildItem (Join-Path $pack "adapters\copilot\agents") -Filter *_agent.md -File) {
    $name = $cop.BaseName -replace '_agent$', ''
    Write-StrippedAgent $cop.FullName (Join-Path $grokAgents ("{0}.md" -f $name))
}
$grokAgentsCount = (Get-ChildItem $grokAgents -File).Count
Write-Host "  .grok/agents: $grokAgentsCount"

$grokRules = Join-Path $repo ".grok\rules"
Reset-Dir $grokRules
Copy-Item (Join-Path $pack "adapters\grok\grok-surface.md") (Join-Path $grokRules "grok-surface.md") -Force
Write-Host "  .grok/rules: grok-surface.md (path map only)"

# --- .agents/skills shared by Codex and Antigravity (INSTALL 1.8 / 1.9) ---------
$agySkills = Join-Path $repo ".agents\skills"
Reset-Dir $agySkills
$agySkillCount = 0
foreach ($cmd in Get-ChildItem (Join-Path $pack "commands") -Directory) {
    $skill = Join-Path $cmd.FullName "SKILL.md"
    if (Test-Path $skill) {
        $target = Join-Path $agySkills $cmd.Name
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Copy-Item (Join-Path $cmd.FullName "*") $target -Recurse -Force
        $agySkillCount++
    }
}
Write-Host "  .agents/skills: $agySkillCount"

# Pack-owned inventory lets a consuming repo detect missing skills without pack/.
$codexInventory = [ordered]@{}
foreach ($cmd in Get-ChildItem (Join-Path $pack "commands") -Directory | Sort-Object Name) {
    if (Test-Path (Join-Path $cmd.FullName "SKILL.md")) {
        [string[]]$codexFiles = @(Get-ChildItem $cmd.FullName -File -Recurse |
            ForEach-Object { [IO.Path]::GetRelativePath($cmd.FullName, $_.FullName).Replace('\', '/') })
        [Array]::Sort($codexFiles, [StringComparer]::Ordinal)
        $codexInventory[$cmd.Name] = $codexFiles
    }
}
$codexDocs = Join-Path $repo "docs/ai-forward-pack"
New-Item -ItemType Directory -Force -Path $codexDocs | Out-Null
$codexInventory | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $codexDocs "codex-skills.json") -Encoding UTF8
Copy-Item (Join-Path $pack "adapters/codex/codex.md") (Join-Path $codexDocs "codex.md") -Force

$agyRules = Join-Path $repo ".agents\rules"
Reset-Dir $agyRules
Copy-Item (Join-Path $pack "adapters\antigravity\agy-surface.md") (Join-Path $agyRules "agy-surface.md") -Force
Write-Host "  .agents/rules: agy-surface.md (path map only)"

$agyHooksDst = Join-Path $repo ".agents\hooks.json"
& $pyExe @pyArgs (Join-Path $pack "scripts\named_hook_bundles.py") (Join-Path $pack "adapters\hooks\agy.ai-forward-hooks.json") $agyHooksDst
if ($LASTEXITCODE -ne 0) { throw "Antigravity named hook merge failed; current hooks were retained." }

$agySkillsJson = "{`n  `"entries`": [`n    { `"path`": `".agents/skills`" },`n    { `"path`": `".claude/skills`" }`n  ]`n}"
Set-Content (Join-Path $repo ".agents\skills.json") -Value $agySkillsJson -Encoding UTF8
Write-Host "  .agents/hooks.json + .agents/skills.json"

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
# The always-on budget baseline travels with the scripts: context-budget.py resolves it from
# pack/ here and from docs/ai-forward-pack/ in an installed repo. Without it a consuming repo
# finds no baseline and the ratchet silently degrades to backstop-only.
Copy-Item (Join-Path $pack "context-budget.json")    $docPack -Force
# --- hooks: the re-read guard (CTX-D) runs at the tool seam on both hosts -------------
# adapters/hooks/reread-guard.py -> docs/ai-forward-pack/hooks/ (the script both configs call);
# the Copilot config -> .github/hooks/ai-forward.json (loaded from the repo automatically);
# the Claude Code hooks object is NOT merged into .claude/settings.json by this script (a
# JSON merge is a judgement call in a file that carries permissions) - INSTALL 1.5 says how.
$hooksDst = Join-Path $docPack "hooks"
New-Item -ItemType Directory -Force -Path $hooksDst | Out-Null
# every hook adapter ships (an explicit list drifted twice: mail-doorbell.py at rev 77, heartbeat.py + owner-review-gate.py at rev 79 - class PACK-D)
Copy-Item (Join-Path $pack "adapters\hooks\*.py") $hooksDst -Force
Copy-Item (Join-Path $pack "adapters\hooks\copilot.ai-forward-hooks.json") $hooksDst -Force
Copy-Item (Join-Path $pack "adapters\hooks\README.md")       $hooksDst -Force
$ghHooks = Join-Path $repo ".github\hooks"
New-Item -ItemType Directory -Force -Path $ghHooks | Out-Null
Copy-Item (Join-Path $pack "adapters\hooks\copilot.ai-forward-hooks.json") (Join-Path $ghHooks "ai-forward.json") -Force
$grokHooks = Join-Path $repo ".grok\hooks"
New-Item -ItemType Directory -Force -Path $grokHooks | Out-Null
Copy-Item (Join-Path $pack "adapters\hooks\grok.ai-forward-hooks.json") (Join-Path $grokHooks "ai-forward.json") -Force
Write-Host "  hooks: adapters/hooks/*.py -> docs/ai-forward-pack/hooks/, .github/hooks/ai-forward.json, .grok/hooks/ai-forward.json, .agents/hooks.json"
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

# FR-060 (class, closed at source by FR-068). Both generators below read docs/docs-index.js,
# which docs-graph.py derive produces - and every skill runs derive as its LAST action (V10),
# so sync-then-derive left this pair one node behind on any run that added an artifact, with
# nothing local saying so.
#
# Deriving FIRST removes the trap at its source. This was attempted in Phase 2 and had to be
# reverted: docs-index.js carried a wall-clock "generated" field, so pulling it into this
# script pulled it into gate 2's diff scope where it could never be byte-stable, making CI
# permanently red. FR-068 removed that field (the same call the sibling generator had already
# made for web/pack-index.js), so the ordering fix is now safe and gate 2 stays green.
# Detection remains too: check-consistency.py drift-gates BOTH dependents, so a hand-run that
# skips sync still cannot ship a stale pair.
$buildHandbook = Join-Path $repo "tools/build-handbook.py"
if (Test-Path $buildHandbook) {
    & $pyExe @pyArgs $buildHandbook
    if ($LASTEXITCODE -ne 0) { throw "build-handbook failed (exit $LASTEXITCODE)" }
}
$deriveGraph = Join-Path $repo "docs/ai-forward-pack/scripts/docs-graph.py"
if (Test-Path $deriveGraph) {
    & $pyExe @pyArgs $deriveGraph derive | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) { throw "docs-graph derive failed (exit $LASTEXITCODE)" }
}

# Regenerate the whole-pack navigable/searchable index that web/index.html renders (freshness contract).
$buildWebIndex = Join-Path $repo "tools/build-web-index.py"
if (Test-Path $buildWebIndex) {
    & $pyExe @pyArgs $buildWebIndex | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) { throw "build-web-index failed (exit $LASTEXITCODE)" }
}

# Regenerate the Documentation Portal data (docs/portal/portal-data.js) - the derived, drift-gated
# front door (spec-documentation-portal). Derived from pack sources so it cannot rot as the repo evolves.
$buildPortal = Join-Path $repo "tools/build-docs-portal.py"
if (Test-Path $buildPortal) {
    & $pyExe @pyArgs $buildPortal | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) { throw "build-docs-portal failed (exit $LASTEXITCODE)" }
}

Write-Host "Done. Review changes, then commit pack/ + .claude/ + .github/{instructions,prompts,agents}/ + .grok/ + docs/ + CLAUDE.md/AGENTS.md together." -ForegroundColor Green
