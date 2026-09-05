---
id: design-session-profiler
title: "Design — session profiler (the measured half of tuning)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [profiling, instrumentation, efficiency, adherence, coordination, tooling]
links:
  - { to: kb-pack-evolution, rel: implements }
  - { to: design-pack-doctor, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-05"
summary: >-
  A deployable, stdlib-only session-profile.py that reads the telemetry Claude Code and
  GitHub Copilot CLI already write to disk for one or more pack-consuming repos and emits a
  findings table (SP-01..SP-16, with per-turn evidence), a fixes table (F-01..F-11, each naming
  the pack surface and its control) and a model-family x harness comparison — the input to
  /dream for performance, efficiency, task adherence, fan-out and cross-harness tuning.
---

# Design: session profiler

- **Status:** Accepted
- **Spec / architecture:** the profiling pass that produced revision 60 (`docs/profiles/sp-0001`), `docs/architecture.md`
- **Delivery phase / vertical slice:** Pack-evolution slice 3. Deployable — `docs/ai-forward-pack/scripts/session-profile.py` lands in installed repos; the `/session-profiler` skill drives it.
- **Author(s) / date:** AI Systems Engineer + SRE + Simplifier, 2026-09-05

## Responsibility
Turn *"the session felt slow / expensive / drifty"* into a measured, cited finding with the pack surface that owns its control. One script, three views: **profile** (per session, per turn), **compare** (model family × harness), **fixes** (the catalog). It never judges intent — heuristics over text are labelled *Inferred* and the skill confirms them against the transcript.

## Contracts
- **Exposed:** `session-profile.py --repo <path>[ --repo …] [--days N] [--harness all|copilot|claude] [--session id…] [--limit N] discover | profile [--out-root] [--json-only] [--session-id] | compare | fixes`. Exit 0 on success, 1 when no session matches, 2 on usage error. Output: `docs/profiles/<sp-id>/profile.json` (canonical), `profile.md` (V2 frontmatter, `relates-to` this design - a graph node), a row in `docs/profiles/PROFILES.md`, an audit entry via `audit-log.py`.
- **Consumed (established from the stores themselves, not documentation — RIG-D):**
  - Copilot CLI 1.0.83: `~/.copilot/session-store.db` — `sessions(id, cwd, repository, summary, created_at, updated_at)`, `assistant_usage_events(turn_index, agent_id NULL=main, model, input/output/cache_read/cache_write/reasoning tokens, total_nano_aiu, duration_ms, time_to_first_token_ms, …)`; `session-state/<id>/events.jsonl` — `user.message` (delivery idle/steering = human; queued = parent→sub-agent), `assistant.message`, `tool.execution_start/complete` (interactionId attributes tools to a conversation), `subagent.started/completed`, `system.message` (the prefix, `<custom_instruction>` blocks), `hook.*`, `abort`, `session.error`. *(Verified on a captured 4,700-event stream.)*
  - Claude Code 2.1.x: `~/.claude/projects/<slug>/<session>.jsonl` — `user`/`assistant` records (`isSidechain` = sub-agent), `message.usage` (input, cache_read, cache_creation, output, thinking), `tool_use` blocks, `ai-title`, `cost-state`. The project slug is the absolute path with every non-alphanumeric character replaced by `-`. *(Verified on this repo's own transcripts.)*
- **Not recorded (and said so):** Claude Code TTFT and the system prompt; Copilot per-turn USD. `context-budget.py prefix` is the offline estimate for the prefix; the profiler reads the real one only where the harness stored it.

## Patterns
- **Instrument, don't infer** (IO1/IO5) — the whole design. Named in code `# instrumentation over inference`.
- **Detector catalog with stable ids** (SP-xx → F-xx) so `/dream` can mine recurrence across profiles and `/apply-learnings` can push a fix by id. Rejected: free-text findings — un-minable.
- **Fail-open readers**: a broken or missing store is reported per session and skipped; nothing is estimated around it (IO8).
- **Attribution by the log's own field** for Copilot: every sub-agent event (its `user.message`, `system.message`, `assistant.*`, `tool.*`) carries a top-level `agentId`; main-conversation events carry none. A human turn is a main `user.message` delivered `idle` or `steering`; a `queued` or delivery-less main message is a parent→sub-agent message. Established on the captured stream after two positional rules (parent-id chains, event ordering) were falsified against it — the chain is linear and parallel sub-agent starts interleave. `simplify:` a message with no `delivery` value is never treated as a human turn — upgrade trigger: a harness release that changes the delivery vocabulary.

## Failure modes
| Mode | Disposition |
|---|---|
| Store schema changes (column renamed) | **detect** — the session is skipped with the exception named on stderr; the profile says how many were skipped |
| Two harnesses record the same session differently | **accept** — metrics are normalised per turn, and per-field `not recorded` marks what a harness lacks |
| A heuristic (goal-state regex) misfires | **mitigate** — labelled Inferred; the skill's Stage 2 confirms against the transcript before it enters the fixes table |
| Prompt fragments carry a secret into a profile | **mitigate** — prompt previews are truncated to 160 chars and `/dream` scrubs every note it mines; profiles are committed only after the skill's review |
| Huge stores (100 MB transcripts) | **accept** — linear single pass per file; `--days`/`--limit` bound the window |

## Test plan
`tests/docs_explorer/test_session_profile.py` — synthetic Copilot store + events (double-loaded prefix, 3× re-read, skill re-invocation, runaway sub-agent + converge nudge, orientation read, harness nudge, TTFT 25 s) → SP-02/04/05/07/08/10/11 with the planted evidence; a clean fixture produces none of them; a Claude transcript parses into turns with `not recorded` where the harness lacks the field; missing stores → exit 1; catalog integrity (every finding maps to a known fix); markdown render carries the three tables.

## Conformance notes
Runs under `python3`/`python`/`py -3` (INSTALL §0); utf-8 stdout reconfigured (FR-047 class); read-only SQLite URI; no third-party imports.

## Flagged risks
- The model-family comparison is only as good as the turn mix — SP-14 carries a caveat and the skill requires ≥3 comparable turns per family before tuning.
- Claude Code sub-agent attribution relies on `isSidechain`; an agent run through a different mechanism (a remote session) would count as main.

## Gate record
Simplifier: struck a proposed HTML review view (the markdown tables are the deliverable; `/dream` already renders HTML for promotion). Test Architect: PASS-WITH-CONDITIONS — detectors pinned by fixture; the family-gap heuristic is Inferred by construction and must stay labelled.
