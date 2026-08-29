---
id: spec-collaborate-skill
title: "Spec - /collaborate skill proposal"
type: spec
status: draft
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, collaborate, skill, worktrees]
links:
  - { to: design-coord-collaboration-phase4, rel: refines }
  - { to: spec-agent-coordination, rel: implements }
review-by: "2027-02-28"
summary: >-
  Proposal for a future /collaborate skill that starts a cross-agent collaboration session by
  creating or entering a worktree, registering the session, scaffolding or updating the session
  contract, claiming the first files, and printing the collaboration checks before coding begins.
---

# Spec: /collaborate skill proposal

## Problem

AI-DE proved that cross-agent collaboration works when sessions register, write a session contract,
claim files, and agree how seam changes and append-only/derived merges work. It also proved the
current process is too easy to skip: the user had to prompt registration and contract agreement
explicitly.

## Core scenario

The user starts a new session with:

```text
/collaborate --role Design --work "style the graph surfaces" --branch feature/graph-surface-design
```

The skill creates or enters a work-named worktree, exports `AGENT_SESSION`/`AGENT_NAME` guidance,
runs `coord session start`, scaffolds `docs/collaboration/session-contracts.md` from the template if
missing, records this session's role response, optionally claims initial paths, runs
`coord collaborate check`, and stops with the next commands. It does not implement feature work.

## Acceptance criteria

- Given no worktree exists, the skill creates a sibling worktree named for the work and registers
  the session.
- Given a session contract is missing, the skill creates it from `session-contract.template.md`.
- Given a contract exists, the skill appends or updates the current session response without
  overwriting another session's section.
- Given initial paths are supplied, the skill runs `coord claim` for each and reports refusals.
- Given multiple sessions exist, the skill runs `coord collaborate check --json` and surfaces any
  blocker before implementation starts.
- The skill has a Copilot prompt, Claude skill, and an eval asserting the contract artifact and
  command guidance are produced.

## Non-goals

- No autonomous merge, no work assignment planner, no daemon, no ownership enforcement beyond what
  `coord` already exposes.
- No target-repo pack update; installed repos receive it through `/updatepack`.

## Proposed implementation

Add a new pack skill `/collaborate` via `/extendaibundle` after the current coord script slice lands.
It should be a workflow wrapper around existing commands, not a new coordination substrate:

1. `coord worktree new --branch <work> --session <session>` or verify current worktree.
2. `coord session start`.
3. Scaffold or update `docs/collaboration/session-contracts.md` from the template.
4. `coord claim --wi <work-item> --path <path>` for supplied paths.
5. `coord collaborate check --json`.
6. Emit a status table and stop; the next skill does the actual work.

## Best next action

Run `/extendaibundle` for `/collaborate` once the owner-aware claim/request/summary coord slice is
merged and pushed, so the skill can depend on the finalized command contract.
