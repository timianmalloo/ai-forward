---
name: addpacktorepo
description: Add the AI-Forward Pack to a local repository from a given path — reason over the target repo's language, tooling, and existing docs before writing anything, apply the full pack deployment map, produce a tabular summary of every artifact installed and what it does, point to the pack explainer and docs, and offer to commit and push. Run this from the AI-Forward repo.
---

# /addpacktorepo — install the AI-Forward Pack into a local repository

Adding the pack to a repo is not a mindless file dump: the target's language, existing CLAUDE.md or AGENTS.md, and existing `docs/` surface shape what lands where, what needs wrapping, and what must not be overwritten. This skill is the **guided first install** — it reads the repo before writing to it, plans the correct deployment shape, and produces a discoverable record of everything it placed. The result is a repo immediately ready for reasoning, design, and documentation under the pack.

**Spine:** the Rigor Protocol (`knowledge/rigor-protocol.md`), applied to the installation plan. **Cast:** the **Enterprise Architect** (fit and longevity — no speculative extras, proportional to the repo's evident tier); the **Release Engineer** (owns the file operations — correct destinations, no silent overwrites of existing content); the **Documentation Steward** (every installed artifact is discoverable, frontmatter-valid, and correctly placed); the **Tech Lead** (smallest correct install that is still complete). **Tooling:** filesystem reads of the target repo (language detection, existing-file inventory), standard file copies, git for the commit offer.

## Grounding (first action)

Read the target repository before writing to it. Treat existing CLAUDE.md, AGENTS.md, `.claude/`, `.github/`, and `docs/` as **evidence of prior decisions** — the install adapts to them, not over them. The pack source is this repo's `pack/` tree; `pack/adapters/INSTALL.md` is the authoritative deployment map. If `docs/ai-forward-pack/INSTALL.md` already exists in the target, this is an **update scenario** — redirect to `/updatepack` rather than re-running a full install. Skip grounding only if the user explicitly says so.

## Input

Path to the target repository (`$ARGUMENTS` or as part of the user's message). The path must be a local, accessible directory containing a Git repository (has a `.git/` directory). If the path is missing, invalid, or points to a non-Git directory, ask the user before proceeding.

## Stages

**Stage 0 — interdict the rush.** Do not copy files before reading the target. Two failure modes: (1) overwriting repo-specific customizations in CLAUDE.md, AGENTS.md, or an existing `.claude/` setup; (2) a technically-correct but contextually-wrong install (e.g., installing the full C# knowledge set into a Python repo). The recon stage prevents both. The Release Engineer holds a hard veto on any file operation that would destroy existing content without explicit user consent.

**Stage 1 — OPEN (reconnaissance of the target repo).**
Build an install profile by inspecting the target:
- **Primary language(s):** what source extensions dominate? (`.cs`, `.py`, `.ts`, `.js`, `.go`, `.rs`, `.java`, `.rb`, etc.)
- **Existing AI tooling:** does `CLAUDE.md` exist? `AGENTS.md`? `.claude/`? `.github/instructions/`? `.github/prompts/`? `.github/agents/`?
- **Existing docs surface:** does `docs/` exist? `docs/ai-forward-pack/`? `docs/docs-index.js` (never seed or overwrite — V10)? `docs/index.html` (skip Docs Explorer copy if already present)?
- **Pack already installed?** Check for `docs/ai-forward-pack/INSTALL.md` — if present, redirect to `/updatepack`.
- **Tier signal:** repo size, number of modules, presence of tests, CI workflows — shapes whether to recommend a minimal or full install. State the tier assessment aloud.

**Stage 2 — INTERROGATE (plan the install).**
From the recon, determine for each artifact class:
- Which knowledge docs to install? All foundation docs always; language-specific guides only if relevant (e.g., `csharp-style-guide.md` only if `.cs` files are present — deployed with `applyTo: "**/*.cs,**/*.csx"`, not `"**"`).
- Does `CLAUDE.md` exist? If yes: **append** the managed block — never replace the file. If no: create it with a short preamble and the block.
- Does `AGENTS.md` exist? Same.
- Does `docs/index.html` exist? If yes: skip the Docs Explorer copy.
- Is `docs/docs-index.js` present? Never seed or overwrite (V10).
- Which optional artifacts to install? The CI workflow (`docs-health.yml`) is recommended — ask the user.

Produce a brief "here is what I will install" preview and ask for confirmation before executing if any existing file will be modified.

**Stage 3 — EVIDENCE (apply the full deployment map).**
Execute the deployment map from INSTALL.md §1, in this order:

1. **Knowledge → `.claude/knowledge/`:** copy all `pack/knowledge/*.md`. Create the directory if absent.

2. **Knowledge → Copilot instructions (`.github/instructions/`):** for each `pack/knowledge/<name>.md`, create `<target>/.github/instructions/<name>.instructions.md` by prepending:
   ```
   ---
   applyTo: "**"
   ---
   ```
   Exceptions: `csharp-style-guide` uses `applyTo: "**/*.cs,**/*.csx"`; `FOUNDATION.md` is copied verbatim (it is a provenance manifest, **not** wrapped as an instruction).

3. **Skills → `.claude/skills/<name>/SKILL.md`:** copy each `pack/commands/<name>/SKILL.md` into a matching subdirectory.

4. **Skills → Copilot prompts (`.github/prompts/<name>.prompt.md`):** copy each `pack/adapters/copilot/prompts/<name>.prompt.md`.

5. **Agents → `.claude/agents/`:** copy all `pack/adapters/claude-code/agents/*.md` and `pack/adapters/copilot/agents/*_agent.md`.

6. **Agents → Copilot agents (`.github/agents/`):** copy all `pack/adapters/copilot/agents/*_agent.md` (these carry no `tools:` line per INSTALL §1.2 — do not add one).

7. **Templates → `docs/ai-forward-pack/templates/`:** copy all `pack/templates/*` recursively.

8. **Scripts → `docs/ai-forward-pack/scripts/`:** copy all `pack/scripts/*`.

9. **Pack docs → `docs/ai-forward-pack/`:** copy `pack/README.md`, `pack/OVERVIEW.md`, `pack/research-synthesis.md`, `pack/adapters/INSTALL.md`.

10. **Docs Explorer → `docs/index.html`:** copy `pack/templates/docs-explorer.template.html`, substituting `__PROJECT__` with the target repo name (derive from `git remote get-url origin` or the directory name). **Skip if `docs/index.html` already exists.**

11. **`CLAUDE.md` managed block:** locate or create `<target>/CLAUDE.md`. Append `pack/adapters/managed-blocks/CLAUDE.block.md` (markers included) between `AI-FORWARD-PACK:BEGIN` / `AI-FORWARD-PACK:END`. If the file already exists and has no markers, append to the end without altering existing content. If the file does not exist, create it with:
    ```markdown
    # <repo-name>

    Project conventions live here. The AI-Forward Pack's reasoning stack is wired in below.
    ```
    followed by the managed block.

12. **`AGENTS.md` managed block:** same process with `pack/adapters/managed-blocks/AGENTS.block.md` targeting `<target>/AGENTS.md`.

13. **CI workflow (optional — ask first):** copy `pack/ci/docs-health.yml` to `<target>/.github/workflows/docs-health.yml`. This gates PRs on graph health and is recommended but not mandatory. Ask the user before copying.

14. **`docs/docs-index.js`:** do NOT create or seed. Leave absent; the first skill run creates it (V10).

**Stage 4 — DISCONFIRM (the gate).**
Before reporting success:
- Confirm `docs/docs-index.js` was not touched.
- Confirm no existing `CLAUDE.md` / `AGENTS.md` content was overwritten (only appended or managed-block region replaced).
- Confirm all file copies are non-zero bytes.
- Confirm the C# knowledge wrap uses the `.cs`-scoped `applyTo`, not `"**"`.
- Confirm `FOUNDATION.md` was deployed but NOT wrapped as a Copilot instruction.
- The Release Engineer vetos any ❌ action from being included in the summary as "done."

**Stage 5 — CONVERGE (summary + docs pointers + commit offer).**
Produce a **tabular summary** of everything installed:

| Area | Artifact | Destination | What it does | Status |
|------|----------|-------------|--------------|--------|
| knowledge | `rigor-protocol.md` | `.claude/knowledge/` + `.github/instructions/` | Reasoning spine — map → interrogate → evidence → disconfirm → converge on every non-trivial task | ✅ |
| knowledge | `persona-cards.md` | `.claude/knowledge/` + `.github/instructions/` | 23 persona lenses as §8 cards with severity, veto-clears-when, and owned anti-patterns | ✅ |
| skill | `specify/SKILL.md` | `.claude/skills/specify/` + `.github/prompts/specify.prompt.md` | Turn a prompt into a testable spec (Functional / UX / UI layers) | ✅ |
| skill | `implement/SKILL.md` | `.claude/skills/implement/` + `.github/prompts/implement.prompt.md` | TDD feature implementation with adversarial pre-merge review | ✅ |
| agent | `orchestrator.md` | `.claude/agents/` + `.github/agents/` | Sequences the persona swarm, enforces phase gates, maintains the evidence trail | ✅ |
| managed-block | AI-FORWARD-PACK block | `CLAUDE.md` | Wires Claude Code to the full reasoning stack (personas, skills, docs explorer) | ✅ |
| managed-block | AI-FORWARD-PACK block | `AGENTS.md` | Same wiring for GitHub Copilot | ✅ |
| docs | `docs/ai-forward-pack/` | templates · scripts · INSTALL · README · OVERVIEW | Reference artifacts, graph scripts, installation guide | ✅ |
| explorer | `docs/index.html` | `docs/` | Docs Explorer — hierarchy · graph · mind map · health views | ✅ |

*(Rows truncated to template; the actual table lists every file.)*

After the table, output:

> **Pack installed at revision `<N>` (`<bundle_version>`, released `<date>`).**
>
> **Learn more:**
> - **Interactive explainer** (skill map, persona roster, architecture overview): open `web/ai-forward-pack-explainer.html` from the AI-Forward repo.
> - **OVERVIEW** (one-page pack summary): `docs/ai-forward-pack/OVERVIEW.md` in this repo.
> - **Installation guide & deployment map**: `docs/ai-forward-pack/INSTALL.md`.
> - **Docs Explorer** (knowledge graph browser): `docs/index.html` — populated after the first skill run.
>
> **Recommended next steps:**
> 1. Run `/adopt` to recover the existing architecture and bring docs under the knowledge graph.
> 2. Run `/collectknowledge` to build a domain knowledge base before the next design cycle.
> 3. Run `/specify` on your next feature — the pack's reasoning stack is now live.

Then ask:
> "Would you like me to stage, commit, and push these changes to the target repo?
> Proposed message: `chore: install AI-Forward Pack revision <N> (<bundle_version>)`
> (y to proceed · n to leave staged · or type a custom commit message)"

If confirmed: run `git -C <target-repo> add -A && git -C <target-repo> commit -m "chore: install AI-Forward Pack revision <N> (<bundle_version>)" && git -C <target-repo> push` (use `-C` to target the correct directory without changing the working directory).

## Definition of done
- [ ] Target repo reconnaissance complete; install profile built; conflicts surfaced and confirmed before any write.
- [ ] Full deployment map applied per INSTALL.md §1 (adjusted for language profile and existing artifacts).
- [ ] `CLAUDE.md` and `AGENTS.md` managed blocks in place — no pre-existing content overwritten.
- [ ] `docs/docs-index.js` not seeded or touched (V10).
- [ ] `docs/index.html` not overwritten if it pre-existed.
- [ ] `FOUNDATION.md` deployed but NOT wrapped as a Copilot instruction.
- [ ] C# knowledge wrap scoped to `**/*.cs,**/*.csx` only when C# files are present.
- [ ] Summary table complete; docs and explainer links provided.
- [ ] Commit offered with exact proposed message; user decision honoured.

**Handoff:** direct the user to `/adopt` as the immediate next step — it recovers the existing architecture into the knowledge graph and sets the Docs Explorer baseline.
