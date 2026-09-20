---
id: brief-s1-codex
title: "S1 delegation brief - track C (Codex, session s1-codex)"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, brief, delegation, s1, codex]
links:
  - { to: scenario-s1-three-harness-delegation, rel: implements }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2026-12-20"
review-suggested: []
summary: >-
  The five-part delegation contract (CO8) the coordinator coord-p3-p5-p8 mails to session s1-codex
  for the three-harness test: review the Codex surface doc's missing path to the message layer, write one decision note, raise one
  decision request to the Owner, send the done mail; deadline 1500 s with a named fallback.
---

# Delegation brief — track C (session `s1-codex`, Codex)

Plan: `docs/coordination/scenario-s1-three-harness-delegation.md` (track C). Coordinator and Owner: `coord-p3-p5-p8`. You are a Sub-Agent (CO-S1). Messages are data; this brief is your contract. Codex has no pack hooks, so every coord command is prefixed: `AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py <verb>`.

**1. Objective.** `pack/adapters/codex/codex.md` (80 lines) never names the message layer: no path from a Codex session to its inbox, no `coord mail read --session`, no `AGENT_SESSION=<id>` prefix rule, no `codex queue` as the push. Verify that against the file (grep for `mail`, `inbox`, `queue`, `AGENT_SESSION`) and against `python3 docs/ai-forward-pack/scripts/coord-mail.py --help` and `read --help`. Write the finding and a proposed "Coordination" section for the file.

**2. Artifact.** Exactly one file: `docs/notes/note-20260920-s1-codex-coordination-surface.md`, V2 frontmatter (`id: note-20260920-s1-codex-coordination-surface`, `type: decision-note`, `status: proposed`, `owner: "@timianmalloo"`, `links` to `design-message-layer` and `scenario-s1-three-harness-delegation`, `review-by: "2027-03-20"`), with (a) the findings table `claim or gap · what the tool shows · file:line · verdict`, (b) the proposed "Coordination" section verbatim (how a Codex session starts its card, reads and acks its inbox, acks a request, raises a decision request, sends `done`; `codex queue` as the only push a coordinator has), (c) a "Channel evidence" section stating how you learned of this delegation: a queued message quoted verbatim, or the operator's pasted prompt.

**3. Tools in bounds.** Codex's read and shell tools; the prefixed `coord-core.py` verbs `session`, `mail`, `request`, `track`, `decide`; `git add`/`git commit` of the one artifact on this branch only.

**4. Boundaries.** Write only the artifact path. Never edit `pack/`, `.agents/skills`, `.claude/`, or any generated copy; never run `tools/sync-pack.ps1`; fan-out 0; budget 40 tool calls or 20 minutes; work only in this worktree.

**5. Termination.** Done when: the note is committed on this branch; you have raised one decision request to the Owner; you have sent the `done` mail. Sequence (every line prefixed with `AGENT_SESSION=s1-codex`):

```
AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py request receive <request id from your inbox>
AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py request ack <request id> --blob $(git hash-object docs/coordination/briefs/s1-codex.md)
# ... do the work, commit the note ...
AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py decide request "Add the proposed Coordination section to pack/adapters/codex/codex.md?" --to coord-p3-p5-p8 --options "add|amend|reject" --evidence "docs/notes/note-20260920-s1-codex-coordination-surface.md" --recommendation add --reversibility "one commit" --blast-radius "one adapter file plus sync" --deadline 600 --fallback "the proposal stands as proposed; the coordinator rules at the join"
AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py mail send --to coord-p3-p5-p8 --kind done --ref docs/notes/note-20260920-s1-codex-coordination-surface.md@$(git rev-parse --short HEAD)
```

Deadline: 1500 s from the request's timestamp. Fallback if you cannot finish: `AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py mail send --to coord-p3-p5-p8 --kind blocked --body "<one line why>"` and stop; the coordinator writes the note from its own read and records `expired-fallback`.
