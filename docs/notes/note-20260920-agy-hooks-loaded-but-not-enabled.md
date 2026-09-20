---
id: note-20260920-agy-hooks-loaded-but-not-enabled
title: "Antigravity loaded our four hook sections and fired none: the working section is the only one with enabled: true; the s1-agy track hung on its ack command"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [decision-note, coordination, antigravity, agy, hooks, s1, debugging, enabled]
links:
  - { to: note-20260920-s1-agy-hooks-surface-freshness, rel: refines }
  - { to: scenario-s1-three-harness-delegation, rel: relates-to }
  - { to: design-message-layer, rel: relates-to }
review-by: "2027-03-20"
review-suggested: []
summary: >-
  Debugged from this machine without the operator. Antigravity's own CLI log for the s1-agy session
  shows the project hooks file WAS loaded (5 named hooks from 2 files) and the process carried
  AGENT_SESSION=s1-agy, so identity and loading are not the cause; over seven tool calls only the
  operator's user-level section (agy-auto-approve, the sole section with "enabled": true) produced
  any effect, and the agy binary parses an enabled field. Our four sections now carry the flag
  (Inferred cause, pinned by a test, confirmed only by a live row). Separately, the track did not stall
  from idleness: its last step at 04:27:03Z was the request ack with a $(git hash-object …)
  substitution, approved at 04:27:07Z, and no tool result ever followed - the session hung inside
  that command until the deadline.
---

# Antigravity: hooks loaded, none enabled; the ack command hung

**Question left open by the fallback note.** Why did the s1-agy session write no heartbeat row and no
run-start marker across a 13-minute live session? The fallback note named two unverified causes: identity
absent from the environment, or hooks not loading. Both are now ruled out by the host's own records.

## Evidence (all read on this machine, 2026-09-20 06:10–06:25Z)

| # | fact | where |
|---|---|---|
| 1 | The `agy` process (pid 9648) carried `AGENT_SESSION=s1-agy` and `AGENT_HOST=agy` | `ps -E -o command= -p 9648` |
| 2 | The session's CLI log: `hooks_manager.go:53] loaded 1 named hooks from 1 hooks.json file(s)` at start, then `loaded 5 named hooks from 2 hooks.json file(s)` four seconds later, workspace `…/ai-forward-docs-s1-agy-hooks-freshness` | `~/.gemini/antigravity-cli/log/cli-20260919_212445.log:` lines at 21:24:45 and 21:24:49 local |
| 3 | The agy binary knows the project path `.agents/hooks.json` and the user path `~/.gemini/config/hooks.json` | `grep -a` over `~/.local/bin/agy` |
| 4 | Seven tool calls ran (21:26:13 → 21:27:11 local); each logged `command_hook_executor.go:75] JSON hook command stderr: [agy-auto-approve: ALLOW] …` — the user-level `PreToolUse` section fired every time | same log |
| 5 | The user-level section is `{"agy-auto-approve": {"PreToolUse": […], "enabled": true}}`; ours had no `enabled` key on any of the four sections | `~/.gemini/config/hooks.json`; `pack/adapters/hooks/agy.ai-forward-hooks.json` before this note |
| 6 | The binary carries `json:"enabled"` / `json:"enabled,omitempty"` struct tags | `grep -a -o 'json:"…"'` over the binary |
| 7 | No heartbeat accumulator (`.git/coord/heartbeat/s1-agy.json`), no `kind: heartbeat` row in `.agents/log/s1-agy.jsonl`, no run-start marker for `s1-agy` in `docs/audit/.run-starts.json`, no stray ledger under Antigravity's state directory | filesystem |
| 8 | Our heartbeat command, run by hand from the worktree with the process's environment and a `PostToolUse` payload, wrote the accumulator (removed again afterwards) | simulation, 06:16Z |
| 9 | Transcript `brain/1c25332c-…/transcript.jsonl`: 14 steps; #13 at 04:27:03Z is `run_command "python3 … request ack req-01M2YGBW6BFG82E7CG4E86W1KT --blob $(git hash-object …)"`, approved at 04:27:07Z by the evaluator conversation; **no tool result row follows**; the request store shows `receive` and no `ack` | transcripts `1c25332c` and `8c387f21`; `.agents/requests.jsonl` |

## Verdicts

- **Loading:** the project hooks file loads from a linked worktree. Verified (fact 2).
- **Identity:** present in the process. Verified (fact 1).
- **Why none of ours fired:** the one section that fired is the one with `"enabled": true`, and the host
  parses that field. **Inferred** cause: a named section without the flag is loaded but inactive. Our
  four sections now carry it; `test_agy_hooks_enabled.py` pins the shape. Confirmation is a live
  heartbeat row from an Antigravity session — the readiness note's Antigravity column stays
  `observed-only` until then.
- **Why the track produced no artifact:** not idleness. The model executed the brief's steps in order
  and its ack command never returned (fact 9). Whether Antigravity's `run_command` rejects, stalls on, or
  needs a second approval for `$(…)` substitution is not established; Grok and Codex ran the identical
  command. **Control:** the brief's ack line offers a substitution-free form —
  `git hash-object <path>` first, then `request ack <id> --blob <sha>` — and the Antigravity surface doc
  says so.
- **The fallback note's Stop verdict** ("neither PostToolUse nor Stop was observed to fire") stands, with
  its cause now narrowed to the flag.

## Class

Registered as **HOST-A** in `docs/lessons/defect-classes.md`: a host loads our configuration file and
silently ignores the entries that lack the host's activation field; the file is byte-identical to source,
the loader logs success, and nothing fires. Control: every host adapter config is compared against a
*working* host example for its activation fields, not only for its event names; the S1 promotion table
records *loaded* and *fired* as two facts.

## Correction (2026-09-20, later the same day)

The `enabled` verdict above was **wrong**: Antigravity's hooks documentation states the flag defaults to
true. The flag stays (explicit, harmless) but was not the cause. Three headless probes (`agy --add-dir
<tree> -p …`, session `smoke-agy-2`) against the host's documented schema found the real causes and
promoted every Antigravity channel:

| channel | before | cause | after (observed) |
|---|---|---|---|
| heartbeat `PostToolUse` | never counted | handler written in the direct form; tool events need `[{matcher, hooks:[…]}]` | Stop row `calls 2` after a two-call turn — **enforced** |
| heartbeat `Stop` | fired | — | rows on every stop — **enforced** |
| doorbell `PreInvocation` | ran, reply rejected (`failed to unmarshal … via protojson`) | `injectSteps` items must be objects (`{"ephemeralMessage": text}`) | the model quoted the injected line verbatim — **enforced** |
| owner-review gate | `unsupported` (README: "no stop event") | `Stop` exists and a hook may answer `{"decision": "continue"}` | the session reported "Termination was blocked … unresolved decision request" twice, then stopped (cap 2) — **enforced**, Ruling 5 |
| project hooks loading | interactive: loaded at +4 s; plain `agy -p` in an unregistered folder: not loaded | the folder must be a registered project (`--new-project`) or passed with `--add-dir` | loaded (`6 named hooks from 2 files`) |

The S1 fallback note's Stop verdict is superseded by this table. What remains open for Antigravity: the
`$(…)` substitution in a `run_command` that hung the s1-agy ack (the two-command form is documented).

