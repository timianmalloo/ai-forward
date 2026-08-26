---
id: spec-design-slice-rename
title: "Rename /design to /design-slice — Specification"
type: spec
status: accepted
owner: "@timianmalloo"
phase: "pack-namespace"
tags: [skills, naming, design-slice, claude-code, copilot]
links:
  - { to: architecture, rel: relates-to }
  - { to: design-native-app-ui-skill-extension, rel: relates-to }
review-by: "2027-02-22"
summary: >-
  Specification for renaming AI-Forward's detailed component-design workflow from /design to /design-slice. The rename avoids a generic skill-name collision while preserving the workflow's meaning and updating generated Claude/Copilot pack surfaces.
---

# Spec: Rename `/design` to `/design-slice`

- **Status:** Accepted
- **Tier (cost-of-error):** T1 — cross-pack workflow naming contract.
- **Author(s) / date:** Copilot CLI / 2026-08-26
- **Related:** `docs/design/native-app-ui-skill-extension.md`

## Part A — Functional specification

### Problem

[Verified] AI-Forward currently defines a local skill named `design` in `pack/commands/design/SKILL.md`, `.claude/skills/design/SKILL.md`, and `.github/prompts/design.prompt.md`. [Verified] Anthropic's official skills docs and `anthropics/skills` repository do not currently list an official bundled skill named `design`, but they do list design-adjacent skills such as `frontend-design`, `brand-guidelines`, `theme-factory`, and `canvas-design`. [Inferred] Because `design` is a generic skill name and Claude Code skills share slash-command namespace, the AI-Forward name has a high future/plugin collision risk.

### Target users & personas

- **Primary:** AI-Forward users invoking the detailed component/feature design workflow.
- **Secondary:** maintainers updating downstream packs and generated Claude/Copilot surfaces.

### Core scenario

A user types `/design-slice` after `/define-architecture` or `/specify`. The same detailed design workflow runs as before, producing `docs/design/<component>.md`, but no command named `/design` is advertised by AI-Forward.

### In scope / Out of scope

- **In:** rename the skill directory/name/prompt from `design` to `design-slice`; update workflow references, audit/change examples, docs, generated surfaces, tests and pack install metadata.
- **Out:** renaming the `docs/design/` artifact directory or the generic English word "design"; changing the workflow behavior.

### Conceptual model scope

No persisted product domain is introduced. The bounded context is **AI-Forward skill namespace**.

**Ubiquitous language:**
- **Design slice:** the detailed implementable blueprint for one component/feature/vertical slice, after architecture/specification and before implementation.
- **Design artifact:** the file under `docs/design/`; this directory name remains unchanged.

**Invariants:**

| Concept | Invariant |
|---|---|
| Skill command | The AI-Forward detailed design workflow is invoked as `/design-slice`, not `/design`. |
| Artifact path | Detailed designs still write to `docs/design/<component>.md`; only the skill name changes. |
| Generated surfaces | `.claude/skills/design-slice/` and `.github/prompts/design-slice.prompt.md` exist after sync; old generated `design` skill/prompt does not. |

### User stories & acceptance criteria

**US-1 — As a user, I want the detailed design workflow to have a non-generic name so it does not collide with tool/vendor design skills.**
- **Given** the pack is synced **When** I inspect skills/prompts **Then** AI-Forward exposes `design-slice` and does not expose `design`.
- **Given** I search pack workflow references **When** the reference is a slash command **Then** it uses `/design-slice` except where historical audit log entries are immutable records.

**US-2 — As a maintainer, I want the rename to preserve behavior.**
- **Given** `/design-slice` runs **When** it converges **Then** it still writes `docs/design/<component>.md`.
- **Given** audit/change examples refer to this workflow **When** they show `--skill` or shortname **Then** they use `design-slice`.

### Non-functional requirements

| Attribute | Requirement |
|---|---|
| Compatibility | Generated Claude and Copilot surfaces must sync from `pack/` with no stale `design` command. |
| Maintainability | Rename must be mechanically testable with a regression scan. |
| Usability | The new name must communicate scope: detailed design of a slice, not UI design or general product design. |

### Boundary set

- **False positive:** generic prose using "design" remains valid.
- **False negative:** `/design`, `commands/design`, `.claude/skills/design`, `.github/prompts/design.prompt.md`, and `--skill design` must not remain in pack/generated current instructions.
- **Substring:** `/ui-design` and `define-architecture` must not be changed incorrectly.

### Comparables & evidence

| Claim | Source | Confidence |
|---|---|---|
| Claude Code skills are invoked as slash commands and bundled skills occupy the same style of namespace. | Official Claude Code skills docs fetched 2026-08-26 | **Verified** |
| Official `anthropics/skills` repository does not list a `design` skill. | `gh api repos/anthropics/skills/contents/skills` list | **Verified** |
| AI-Forward currently defines local `design`. | `rg` and file paths in this repo | **Verified** |

## Part B — UX specification

This is a command-name UX change.

### Information architecture

Workflow order becomes:

`/collectknowledge` → `/adddomainexperts` → `/specify` → `/define-architecture` → `/design-slice` → `/implement` → `/document`

### User flow

```mermaid
flowchart LR
  architecture[/define-architecture or existing architecture] --> designSlice[/design-slice]
  specify[/specify] --> designSlice
  designSlice --> artifact[docs/design/<component>.md]
  artifact --> implement[/implement]
```

### UX acceptance criteria

- Users can infer that `/design-slice` is scoped below architecture and above implementation.
- The docs distinguish `/design-slice` from `/ui-design`.

## Part C — UI specification

N/A — no visual UI is introduced.

## Flagged risks & residual unknowns

- [Flagged] Some historical docs/audit entries may still mention `/design`; do not rewrite immutable history unless it is part of current pack instructions.

## Gate record

`GATE specify · 2026-08-26 · reviewers: self-check against source evidence · criteria met: three layers present/N/A; acceptance criteria falsifiable; scope limited to skill namespace rename · verdict: PASS.`

## Handoff

→ `/implement` the rename.
