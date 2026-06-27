# GitHub Copilot Instructions — AI-Forward

## Repository purpose

This repo is **two things at once**:
1. The **canonical source** of the AI-Forward Pack — everything you edit to expand the pack lives in `pack/`.
2. A **live install** of that pack — `.claude/` and `docs/` are generated from `pack/` and are what Claude Code reads when working here (dogfooding: the pack is built using the pack).

Never edit `.claude/` or `docs/` directly — they are overwritten by the sync tool.

---

## Build / maintenance commands

All tooling is PowerShell scripts in `tools/`:

```powershell
# After editing anything under pack/ — regenerates .claude/ and docs/
pwsh tools/sync-pack.ps1

# Build the distributable zip for sharing
pwsh tools/package-pack.ps1   # writes dist/ai-forward-pack.zip
```

**Commit discipline:** when changing `pack/`, always commit `pack/`, `.claude/`, and `docs/` together in the same commit so source and install never drift.

### Evals (regression tests for the pack itself)

```bash
# Seed workspace and print the golden prompt
python3 pack/evals/run-evals.py --case pack/evals/cases/design-01-gateway.json --workspace /tmp/eval-ws --setup

# Assert after running the skill
python3 pack/evals/run-evals.py --case pack/evals/cases/design-01-gateway.json --workspace /tmp/eval-ws --check

# Assert all cases (CI-able, exits nonzero on failure)
python3 pack/evals/run-evals.py --cases pack/evals/cases --workspace /tmp/eval-ws --check
```

Run affected skill cases on every pack edit; run all cases on model-version changes.

---

## Architecture overview

```
pack/           ← SINGLE SOURCE OF TRUTH — edit here only
  knowledge/    ← 23 knowledge docs (reasoning spine + vendored foundation)
  commands/     ← 16 skills (one SKILL.md each)
  templates/    ← 17 artifact templates
  adapters/     ← INSTALL.md + Claude Code agents + Copilot agents/prompts + managed blocks
  evals/        ← pack regression suite (NOT deployed to target repos)
  scripts/  ci/  examples/

.claude/        ← GENERATED (Claude Code reads this) — do not edit by hand
  knowledge/  skills/  agents/

docs/           ← GENERATED
  index.html                ← Docs Explorer (hierarchy · graph · mind map · health)
  docs-index.js             ← accumulated knowledge-graph index (skills maintain this — NEVER overwrite)
  audit/                    ← durable audit & change log (audit-log.jsonl, change-log.jsonl, index.html) — skills append, NEVER overwrite the .jsonl
  ai-forward-pack/          ← templates, scripts, pack docs

tools/          ← sync-pack.ps1  package-pack.ps1
web/            ← ai-forward-pack-explainer.html (self-contained interactive explainer)
```

The **deployment map** (every source path → destination per tool) is the contract: `pack/adapters/INSTALL.md`.

---

## Key conventions

### Pack update protocol
When the pack changes, bump `revision` in `pack/adapters/INSTALL.md` frontmatter and update the `changes` list — this is the refresh guide for downstream consumers. The `changes` frontmatter (not a body diff) is what recipients read to know exactly what to re-copy and re-paste.

### Managed blocks
`pack/adapters/managed-blocks/CLAUDE.block.md` and `AGENTS.block.md` are appended to `CLAUDE.md` / `AGENTS.md` between `AI-FORWARD-PACK:BEGIN` / `AI-FORWARD-PACK:END` markers. On updates, replace the marked region **wholesale** — never merge line-by-line.

### Knowledge doc → Copilot instructions wrapping
Each `pack/knowledge/<name>.md` installs as `.github/instructions/<name>.instructions.md` by prepending `---` / `applyTo: "**"` / `---` frontmatter. Exception: `csharp-style-guide` uses `applyTo: "**/*.cs,**/*.csx"`. `FOUNDATION.md` is a provenance manifest — copy it but do **not** wrap it as an instruction.

### Persona agent format
- Claude Code agents (`adapters/claude-code/agents/`) carry `tools: [...]` in frontmatter.
- When copying to Copilot (`.github/agents/<name>.agent.md`), **strip the `tools:` line** — Copilot ignores unknown tool names and silently falls back to all-tools, making the line misleading.
- The `adapters/copilot/agents/*_agent.md` files already have no `tools:` line and drop into `.claude/agents/` unchanged — one source per persona, one frontmatter edit at the Copilot boundary.

### Docs Explorer / knowledge graph
- Every knowledge/content artifact carries YAML frontmatter: `id`, `type`, `owner`, typed links, `review-by`.
- `docs/docs-index.js` is **derived and accumulated** — skills maintain it; never seed or overwrite it by hand (V10).
- All graph mechanics go through `docs/ai-forward-pack/scripts/docs-graph.py` — never ad-hoc scripts (V18).
- Material changes flag inbound neighbors `review-suggested`; sub-ADR decisions become linked decision notes in `docs/notes/`.

### Audit & change log
- Every skill, as its last action, appends an **audit-log** entry (`docs/audit/audit-log.jsonl`) recording the run — shortname, datetime, session, prompt, summary (+ kind/skill/tool/artifacts). `/collectknowledge`, `/define-architecture`, `/design`, `/migrate` additionally append a **change-log** entry (`docs/audit/change-log.jsonl`) capturing the decision + git before/after.
- All writes go through `docs/ai-forward-pack/scripts/audit-log.py` (never hand-append JSONL); it regenerates `audit-data.js` + the viewer. The standard is `pack/knowledge/audit-and-change-log.md`.
- The history is the committed counterpart to a session's ephemeral store — read it at grounding (`audit-log.py list`/`search`) so work compounds across sessions. Browse via `/auditlog` or `docs/audit/index.html`. Prompt **reuse** (`/prompts` + `/searchprompts`, engine `prompt-log.py`) is a second lens over the *same* audit log — `prompt-log.py add` writes a `kind:prompt` entry via `audit-log.py`; there is no separate prompt store.

### The 16 skills and their natural order
```
/collectknowledge → /adddomainexperts → /specify → /define-architecture → /design → /implement → /document
                                                                                ↑
                                                            /investigate  (whenever a defect appears)
```
`/adopt` onboards a brownfield repo; `/migrate` runs characterization-first refactors.
`/updatepack` refreshes an installed pack from a local ai-forward clone; `/addpacktorepo` installs the pack into a new local repo by path; `/extendaibundle` extends the pack itself with a new capability from a prose prompt (collect→specify→design→implement, scaffolded by `tools/new-capability.py`, proven by `tools/verify-bundle.ps1`, zero drift). `/auditlog` is the CLI lens over the audit & change log (last-N, search, recall-and-redo a prompt, open the viewer). Two **prompt-log utilities** sit outside the loop: `/prompts` browses the audit log's prompts as an arrow-navigable stack (→ expand / ← collapse) and `/searchprompts` searches them, both to reuse a prior prompt (engine: `docs/ai-forward-pack/scripts/prompt-log.py`, a reuse lens over the same `docs/audit/audit-log.jsonl`).

Skills in `.claude/skills/` apply automatically by description in Claude Code; in Copilot they are available as prompts in `.github/prompts/<name>.prompt.md`.

### Spec structure
`/specify` produces **one spec with three layers**: Functional (what & why), UX (how it works), UI (how it looks) — written bottom-up (UX before UI). Each absent layer is marked N/A with a reason, never silently dropped. The Archetype Signature (from the UI Archetype Grammar) is recorded in Part C of the spec.

### Reasoning discipline
All non-trivial work runs the Rigor Protocol (`.claude/knowledge/rigor-protocol.md`): map → interrogate → ground in evidence → disconfirm → converge, with a confidence label on every claim. The author never clears their own hard veto.
