---
id: note-20260920-s1-grok-hooks-surface-freshness
title: "Replace the Grok surface Hooks section: five scripts, eight entries, one sentence today"
type: decision-note
status: proposed
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, grok, hooks, freshness, s1]
links:
  - { to: design-message-layer, rel: relates-to }
  - { to: scenario-s1-three-harness-delegation, rel: relates-to }
review-by: "2027-03-20"
review-suggested: []
summary: >-
  Track G of S1: pack/adapters/grok/grok-surface.md §Hooks names two scripts (re-read
  guard, session-start). The installed .grok/hooks/ai-forward.json (byte-identical to
  pack/adapters/hooks/grok.ai-forward-hooks.json) carries eight entries across five
  scripts. Recommend replacing the section with the text below. No claim in the file
  is false; three scripts and several events are unnamed.
---

# Decision note: Grok surface Hooks section is stale by omission

**Context.** Session `s1-grok` (Sub-Agent of `coord-p3-p5-p8`), brief `docs/coordination/briefs/s1-grok.md`, seam request `req-01M2YGBVQ3EKP5235M2DJ4SBWA` acked `--blob f6e08e511a168e92da038be56dba1c09ee23393e`. Confidence: **Verified** — files opened this turn; `diff -q pack/adapters/hooks/grok.ai-forward-hooks.json .grok/hooks/ai-forward.json` exited 0 (identical).

**Recommendation.** `replace` the Hooks section of `pack/adapters/grok/grok-surface.md` with the proposed text. Reversibility: one commit. Blast radius: one adapter file plus sync.

## Findings

| claim in the file | what the config shows | file:line | verdict |
|---|---|---|---|
| `.grok/hooks/ai-forward.json` wires the re-read guard (CTX-D) | `PreToolUse` matcher `Read` runs `reread-guard.py --host grok` (timeout 10). A second, unnamed copy runs on `UserPromptSubmit` with no matcher. | `pack/adapters/grok/grok-surface.md:25`; `.grok/hooks/ai-forward.json:3-13` (Read) and `:33-42` (`UserPromptSubmit`); `pack/adapters/hooks/README.md:9` | **holds, incomplete** — the script is wired; `UserPromptSubmit` is not named |
| and the session-start audit marker (AL4a) | `SessionStart` and `SubagentStart` each run `session-start.py --host grok` (timeout 15). | `grok-surface.md:25`; `.grok/hooks/ai-forward.json:53-63` and `:64-74`; `README.md:13` | **holds, incomplete** — `SubagentStart` is not named |
| Project hooks run only after folder trust (`/hooks-trust` or `--trust`) | README Grok row: "Project hooks require folder trust (`/hooks-trust` or `--trust`)." | `grok-surface.md:25`; `README.md:11` | **holds** |
| (unnamed) mail doorbell | unmatched `PreToolUse` and `UserPromptSubmit` run `mail-doorbell.py --host grok --event <event>` (timeout 10). Purpose: inbox hint — count and pointer as `additionalContext`, never a body. | `.grok/hooks/ai-forward.json:14-22` and `:43-51`; `README.md:14` | **missing from the file** |
| (unnamed) heartbeat | unmatched `PreToolUse` runs `heartbeat.py --host grok --event PreToolUse` (timeout 10). Purpose: progress beat into `$AGENT_SESSION`'s ledger. README: Claude-format `PreToolUse` on Grok; host status `observed-only`. This config has no `PostToolUse` and no `Stop` heartbeat. | `.grok/hooks/ai-forward.json:23-31`; `README.md:16`, `:30` | **missing from the file** |
| (unnamed) owner review gate | `Stop` runs `owner-review-gate.py --host grok --event Stop` (timeout 10). Purpose: refuse the stop (exit 2, reason on stderr) when this session holds an unresolved decision request it sent. README Grok row: `observed-only`. | `.grok/hooks/ai-forward.json:75-85`; `README.md:15`, `:26` | **missing from the file** |

No claim in the file is unsupported by the config. The defect is omission: one sentence names two of five scripts and two of five events.

## Proposed replacement text (verbatim)

```
## Hooks

`.grok/hooks/ai-forward.json` wires five scripts. Project hooks run only after folder trust (`/hooks-trust` or `--trust`).

- **re-read guard** (`reread-guard.py --host grok`, CTX-D) on `PreToolUse` matcher `Read` and on `UserPromptSubmit`
- **mail doorbell** (`mail-doorbell.py --host grok`) on `PreToolUse` and `UserPromptSubmit` — count and pointer as `additionalContext`, never a body
- **heartbeat** (`heartbeat.py --host grok`) on `PreToolUse` (Claude-format; this config has no `PostToolUse`)
- **session-start audit marker** (`session-start.py --host grok`, AL4a) on `SessionStart` and `SubagentStart`
- **owner review gate** (`owner-review-gate.py --host grok`) on `Stop` — exit 2 with a reason on stderr when this session still holds an unresolved decision request it sent

On Grok the doorbell, heartbeat and stop gate are `observed-only` until a live session shows the event fire (CO12; `pack/adapters/hooks/README.md`).
```

## Channel evidence

**`coord mail:` line the host injected into this context.** not seen

**`coord track` row for `s1-grok` (verbatim).**

```
live     s1-grok                  WI-0       heartbeat       21:27:55       0     0  -                not recorded
```

**Refused stop (reason).** not seen
