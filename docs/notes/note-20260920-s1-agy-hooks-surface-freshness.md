---
id: note-20260920-s1-agy-hooks-surface-freshness
title: "S1 track A (Antigravity): the surface doc names two of four hook sections; the Stop event was not observed - written by the coordinator under the track's fallback"
type: decision-note
status: proposed
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, s1, antigravity, agy, hooks, freshness, fallback]
links:
  - { to: design-message-layer, rel: relates-to }
  - { to: scenario-s1-three-harness-delegation, rel: implements }
  - { to: brief-s1-agy, rel: relates-to }
review-by: "2027-03-20"
review-suggested: []
summary: >-
  Track A's request (req-01M2YGBW6BFG82E7CG4E86W1KT) reached its 1500 s deadline at 04:39:38Z with
  the session live (session-start and request receive recorded) but no artifact; the contract's
  fallback ran: expired-fallback recorded and this note written by the coordinator from its own read.
  Finding: pack/adapters/antigravity/agy-surface.md names two of the four hook sections the installed
  .agents/hooks.json carries (mail-doorbell on PreInvocation and heartbeat on PostToolUse/Stop are
  unnamed). Stop verdict: the s1-agy ledger holds no heartbeat row at all, so neither PostToolUse nor
  Stop was observed to fire on Antigravity in this run; every Antigravity channel stays observed-only
  and the README's "none documented" for the stop gate stands as unobserved, not confirmed.
---

# S1 track A — Antigravity hooks surface freshness (coordinator's fallback note)

**Who wrote this and why.** The brief `docs/coordination/briefs/s1-agy.md` assigned this note to session
`s1-agy`. Its typed request was received at 04:26:22Z, never acked, and reached its 1500 s deadline at
04:39:38Z with no artifact in the track's tree; the coordinator ran the contract's fallback
(`coord request expire` → `expired-fallback`) and wrote this note from its own read of the two files.
If the session delivers a `done` mail later, its note is recorded as late evidence beside this one.

## Findings

| claim in the file | what the config shows | file:line | verdict |
|---|---|---|---|
| `.agents/hooks.json` wires the re-read guard (`reread-guard.py` on `PreToolUse` for `view_file`, CTX-D) | section `reread-guard`: `PreToolUse`, matcher `view_file`, `reread-guard.py --host agy` | `pack/adapters/antigravity/agy-surface.md:26`; `.agents/hooks.json` section 1 | **holds** |
| and the session-start audit marker (`session-start.py` on `PreInvocation`, AL4a) | section `session-start`: `PreInvocation` → `session-start.py --host agy` | `agy-surface.md:26`; `.agents/hooks.json` section 2 | **holds** |
| (unnamed) mail doorbell | section `mail-doorbell`: `PreInvocation` → `mail-doorbell.py --host agy` — a count and a pointer injected as steps, never a body | `.agents/hooks.json` section 3; `pack/adapters/hooks/README.md:12,14` | **omission** |
| (unnamed) heartbeat | section `heartbeat`: `PostToolUse` and `Stop` → `heartbeat.py --host agy` | `.agents/hooks.json` section 4; `README.md:16` | **omission** |
| README: Antigravity stop-class event "none documented", owner gate `unsupported` | the hook config wires `heartbeat` on `Stop`; the KB row lists `Stop` for Antigravity 1.2.7 | `README.md:28`; `docs/knowledge/multi-agent-coordination/data-and-constants.md:54` | **contradiction in the docs; not settled by observation** (below) |

No claim in the file is false; the defect is omission (two of four sections named).

## Stop verdict (evidence, not inference)

`.agents/log/s1-agy.jsonl` at 04:40Z carries `session-start` (seq 2) and `request receive` (seq 3) and **no
`kind: heartbeat` row** — neither `PostToolUse` nor `Stop` produced one during a ~13-minute live session
that ran at least the tool calls behind `mail read --ack` and `request receive`. So: `Stop` on Antigravity
is **not seen**, and `PostToolUse` is **not seen** either. The README's "none documented" cannot be promoted
to confirmed, and the heartbeat entries cannot be called dead config; what is established is that, as
launched today, the Antigravity hooks did not write a heartbeat. The likely causes are unverified and named
as such: `AGENT_SESSION` absent from the session's environment (the hooks exit silently without it), or the
hooks not loading in this launch mode. **Next probe:** in the Antigravity session run
`printenv AGENT_SESSION` and one `view_file`, then read the ledger.

## Proposed replacement text (verbatim) for `pack/adapters/antigravity/agy-surface.md` § Hooks

```
## Hooks

`.agents/hooks.json` wires four sections:

- **re-read guard** (`reread-guard.py --host agy`, CTX-D) on `PreToolUse`, matcher `view_file`
- **session-start audit marker** (`session-start.py --host agy`, AL4a) on `PreInvocation`
- **mail doorbell** (`mail-doorbell.py --host agy`) on `PreInvocation` — the inbox count and a pointer, injected as steps, never a body
- **heartbeat** (`heartbeat.py --host agy`) on `PostToolUse` and `Stop` — a progress row in `$AGENT_SESSION`'s ledger

Every hook reads the session identity from `AGENT_SESSION` in the process environment and exits silently
without it: launch `agy` with `AGENT_SESSION=<id>` exported. On Antigravity the doorbell and heartbeat are
`observed-only` and the owner review gate is `unsupported` (no stop-class event documented) until a live
session shows the event fire (CO12; `pack/adapters/hooks/README.md`).
```

## Channel evidence

- Doorbell `coord mail:` step injected: **not seen** (no session transcript available to the coordinator; the
  session acked its two mails at 04:26:22Z after the operator's first prompt, which is consistent with the
  prompt, not the doorbell).
- `coord track` row for `s1-agy`: `stalled … worktree-mtime` throughout (no heartbeat source).
- Refused stop: **not seen**.
- Kick ladder: rung 1 fired at 04:29:51Z (`mail-01M2YH7QH2183XDQETXKS5N68S`); the session acked it; the
  deadline then expired the request. The ladder behaved as designed: a kick, then the fallback, nothing
  automatic beyond the record.
