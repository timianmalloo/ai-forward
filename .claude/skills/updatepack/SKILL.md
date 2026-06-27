---
name: updatepack
description: Update an installed AI-Forward Pack to the latest revision — reads the pack source INSTALL.md from a local ai-forward clone, diffs the installed vs source revision, applies exactly the changed artifacts listed in the changelog (never guesses by diffing the tree), and produces a tabular action summary before offering to commit and push. Run this from the repo that already has the pack installed.
---

# /updatepack — pull the latest AI-Forward Pack into an installed repo

The AI-Forward Pack evolves: knowledge docs deepen, skills sharpen, new personas join the roster. This skill is the **single safe path for refreshing the pack** in a repo that has already had it installed — it reads the authoritative changelog from the pack source, applies exactly what changed, and never guesses. A wrong update is worse than a stale one; precision beats speed.

**Spine:** the Rigor Protocol (`knowledge/rigor-protocol.md`) applied to the update delta — every change must be named, justified, and verified applied before it is called done. **Cast:** the **Release Engineer** leads (owns the installation path and the "no silent overwrites" rule); the **Documentation Steward** reviews every artifact landing (correct destination, managed-block integrity, V10 protection); the **Tech Lead** guards against over-application (only what `changes` lists, nothing extra). **Tooling:** standard filesystem reads/writes + `git diff --stat` to surface what actually changed.

## Grounding (first action)

The source of truth for *what to apply* is `INSTALL.md`'s **`changes` frontmatter in the pack source**, and the *baseline* is the target repo's **last-applied revision** (recorded in `docs/ai-forward-pack/INSTALL.md`). Read both before touching a single file. If the target repo lacks `docs/ai-forward-pack/INSTALL.md`, surface this gap — the repo either predates revision tracking or has never had the pack installed; redirect to `/addpacktorepo` rather than applying a partial update. Skip grounding only if the user explicitly says to skip.

## Input

The path to the local AI-Forward repository (from `$ARGUMENTS` or the user's message). Locate it in this order:
1. Explicit path provided in the user's message.
2. `AI_FORWARD_PACK` environment variable.
3. A sibling directory named `ai-forward` or `AI-Forward` relative to the current repo root.

If none of the above yields a valid path that contains `pack/adapters/INSTALL.md`, ask the user for the path before proceeding.

## Modes — dry-run & idempotency
- **Dry-run (preview).** If the request contains `dry run`, `--dry-run`, `preview`, or `what would change`, run Stages 0–2 and produce the full **action summary table** (Stage 5) **without writing, staging, committing, or pushing anything**. End by stating it was a preview and how to apply for real. The commit/push step is *always* confirmed regardless of mode — dry-run additionally suppresses every file write.
- **Idempotent by construction.** Re-running is safe: if the target is already at the source `revision` the skill writes nothing and reports "already current" (Stage 1, `delta = 0`). When a delta is applied, every action is a **wholesale** copy or a wholesale managed-block re-paste between markers — never an append — so a duplicate block can never accumulate and re-applying the same delta yields an identical tree. An interrupted update can simply be re-run to completion; the installed `revision` only ever advances to the source revision, never past it.

## Stages

**Stage 0 — interdict the rush.** A pack update is not "just a file copy." Two failure modes to prevent: (1) overwriting accumulated artifacts — especially `docs/docs-index.js`, which must **never** be touched (V10); (2) missing a managed-block re-paste, the step most commonly skipped. Every action here is driven by the changelog; diffing the directory tree is not a substitute.

**Stage 1 — OPEN (read both revisions).**
- Read `<pack-source>/pack/adapters/INSTALL.md` frontmatter: extract `revision`, `bundle_version`, `released`, `counts`, and `changes`.
- Read `<target-repo>/docs/ai-forward-pack/INSTALL.md` frontmatter: extract the installed `revision`.
- Compute: `delta = source.revision − target.revision`.
  - `delta = 0` → pack is current. Report this and stop.
  - `delta < 0` → target is ahead of the claimed source (anomaly). Surface to the user and ask for confirmation before proceeding.
  - `delta > 0` → list every `changes` entry that applies (the entire `changes` list covers the delta from the previous revision to the current one).

**Stage 2 — INTERROGATE (classify each change entry).**
For each entry in `changes`, determine:
- **Type:** `added` (new artifact) | `changed` (replace existing) | `managed-block` (RE-PASTE between markers).
- **Deploy action:** direct copy, Copilot-wrap (prepend `applyTo` frontmatter), or managed-block wholesale replace.
- **Risk:** does the path already exist? Is it a protected path (`docs/docs-index.js` — never overwrite)? Does it overlap with repo-specific customizations that could be silently lost?

Surface any conflict or customization risk to the user before applying. The Release Engineer holds a hard veto on any action that would silently destroy existing content.

**Stage 3 — EVIDENCE (apply, verify each action).**
Apply each change in changelog order:

1. **Copy actions.** Copy the file from `<pack-source>/pack/...` to its mapped destination (per the deployment map in INSTALL.md §1). For knowledge docs destined for Copilot (`.github/instructions/`), prepend the `applyTo` frontmatter wrap (`---\napplyTo: "**"\n---\n`). Exception: `csharp-style-guide` uses `applyTo: "**/*.cs,**/*.csx"`; `FOUNDATION.md` is copied verbatim, **not** wrapped. Never touch `docs/docs-index.js`.

2. **Managed-block re-paste.** For each `deploy: RE-PASTE` entry:
   - Locate `CLAUDE.md` (for the Claude block) and/or `AGENTS.md` (for the Agents block) in the target repo root.
   - Find the `AI-FORWARD-PACK:BEGIN` / `AI-FORWARD-PACK:END` markers.
   - Replace the entire region **wholesale** with the new block from `<pack-source>/pack/adapters/managed-blocks/CLAUDE.block.md` (or `AGENTS.block.md`). Include the markers in the replacement.
   - If markers are absent, append the block (with markers) at the end of the file.

3. **Post-copy verify.** For each action, confirm the file exists at the destination and is not zero bytes. Log: ✅ applied | ⚠️ skipped (with reason) | ❌ failed.

4. **Advance the installed revision.** Copy `<pack-source>/pack/adapters/INSTALL.md` to `<target-repo>/docs/ai-forward-pack/INSTALL.md` — this advances the installed revision to the current one.

**Stage 4 — DISCONFIRM (the gate).**
Before reporting success:
- Confirm `docs/docs-index.js` was **not** touched.
- Confirm each managed-block re-paste replaced *between* markers — not appended as a second copy.
- Confirm no file landed at a wrong destination.
- The Release Engineer vetos reporting "done" if any ❌ rows remain unresolved.

**Stage 5 — CONVERGE (summary + commit offer).**
Produce a **tabular summary** of every action taken:

| Area | Artifact / File | Action | Status |
|------|----------------|--------|--------|
| knowledge | `.claude/knowledge/ui-archetype-grammar.md` | Copied | ✅ |
| knowledge | `.github/instructions/ui-archetype-grammar.instructions.md` | Copied + Copilot-wrapped | ✅ |
| managed-block | `CLAUDE.md` AI-FORWARD-PACK block | RE-PASTED wholesale | ✅ |
| meta | `docs/ai-forward-pack/INSTALL.md` | Revision advanced to `N` | ✅ |

Below the table, state: **Pack updated: revision `<from>` → `<to>` (`<bundle_version>`, released `<date>`).**

Then ask the user:
> "Would you like me to stage, commit, and push these changes?
> Proposed message: `chore: update AI-Forward Pack to revision <N> (<bundle_version>)`
> (y to proceed · n to leave staged · or type a custom commit message)"

If confirmed: run `git add -A && git commit -m "chore: update AI-Forward Pack to revision <N> (<bundle_version>)" && git push` from the target repo root.

## Documentation & discoverability (note)
Unlike the workflow skills, this is a **pack-lifecycle skill**: it operates on the pack *installation*, not on the repo's product, so it produces no `docs/` knowledge-graph artifact and does **not** write frontmatter or sync `docs/docs-index.js` (V10 does not apply). Its durable record is the advanced `revision` in `docs/ai-forward-pack/INSTALL.md` plus the commit. If a *skill run it triggered* later changes product docs, that run owns its own discoverability.

## Definition of done
- [ ] Both revisions read; delta computed; anomalies surfaced before any file operation.
- [ ] Every `changes` entry applied (or explicitly deferred with user confirmation and a ⚠️ entry in the summary).
- [ ] Managed blocks re-pasted wholesale between markers — no partial merges, no duplicate blocks.
- [ ] `docs/docs-index.js` untouched (V10).
- [ ] Target `docs/ai-forward-pack/INSTALL.md` advanced to the new revision.
- [ ] Summary table complete; no ❌ rows without explicit user deferral.
- [ ] Commit offered with exact proposed message; user decision honoured.
- [ ] Dry-run requests produced the action table with zero writes; a normal run is idempotent (re-runnable without duplicate blocks or advancing past the source revision).

**Audit (last action).** Append an audit-log entry to the updated repo's log recording the refresh — `python3 docs/ai-forward-pack/scripts/audit-log.py append --shortname "updatepack-r<to>" --session "<id>" --skill updatepack --kind command --prompt "<the prompt, verbatim>" --summary "<from-revision → to-revision; delta applied>"` — per the Audit Mandate (`knowledge/audit-and-change-log.md`, AL5), so the repo records the revision history of its installed pack.

**Handoff:** if the update added new skills or knowledge docs, mention them by name so the user can orient to the new capabilities.
