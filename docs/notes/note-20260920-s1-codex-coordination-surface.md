---
id: note-20260920-s1-codex-coordination-surface
title: "Codex needs an explicit coordination path"
type: decision-note
status: proposed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, codex, message-layer, s1]
links:
  - { to: design-message-layer, rel: relates-to }
  - { to: scenario-s1-three-harness-delegation, rel: implements }
review-by: "2027-03-20"
review-suggested: []
summary: >-
  Proposes a Coordination section for the Codex adapter, grounded in the installed
  mail, request and decision command contracts. Records the received prompt and
  separates delivery acknowledgement from accepting and completing a delegation.
---

# Codex needs an explicit coordination path

The Codex guide explains skills and grounding but omits the message layer.
Recommendation: add the section below to `pack/adapters/codex/codex.md`, then
regenerate its installed copy in a separately authorized change. This track writes
only this note; the Owner rules on adoption.

## Scope and evidence

Reviewed on 2026-09-20 in branch `docs/s1-codex-coordination-surface`, worktree
`/Users/mallalieut/projects/ai-forward-docs-s1-codex-coordination-surface`.
Seat: Sub-Agent `s1-codex`; Owner and Coordinator: `coord-p3-p5-p8`.
The scenario classifies track C as T1; the brief limits fan-out to zero and authoring
to this file. The delivery chain is request acknowledgement → source/help inspection
→ note and one-file commit → decision request → done mail. No engine or adapter
implementation is part of this track.

Surface list for the proposed follow-up: canonical adapter
`pack/adapters/codex/codex.md` → generated `docs/ai-forward-pack/codex.md` → a Codex
reader → session, inbox, typed request and decision commands → coordinator's done
mail. Source/help inspection proves command contracts; it does not prove a push
transport or automatic hook execution.

| Claim or gap | What the tool shows | File:line | Verdict |
|---|---|---|---|
| The brief describes an 80-line adapter. | `nl -ba` ends at line 65. | `pack/adapters/codex/codex.md:65` | **Verified:** the brief's count is stale. |
| The adapter has no message-layer entry point. | `rg -n 'mail\|inbox\|queue\|AGENT_SESSION' pack/adapters/codex/codex.md` returned no matches, exit 1. The whole file was read. | `pack/adapters/codex/codex.md:1` | **Verified:** the four named terms are absent. |
| Inbox location and read/ack syntax are undocumented in the adapter. | `coord-mail.py --help` names `.agents/mail/<session>.jsonl` and `_broadcast.jsonl`; `read --help` lists `--session`, `--ack`, `--since`, `--json`. | `docs/ai-forward-pack/scripts/coord-mail.py:4`; `docs/ai-forward-pack/scripts/coord-mail.py:562` | **Verified:** the CLI provides the missing path. |
| Session identity needs an explicit rule. | Mail resolves explicit identity, then `AGENT_SESSION`, and refuses an empty identity. Decision commands require `AGENT_SESSION`. | `docs/ai-forward-pack/scripts/coord-mail.py:365`; `docs/ai-forward-pack/scripts/coord-decide.py:426` | **Verified:** prefix every coordination command; `mail read --session` alone does not identify later request/decision commands. |
| A mailbox ack is not a delegation ack. | `mail read --ack` appends mail acknowledgements only. `request receive` and `request ack --blob` append distinct typed-request events. | `docs/ai-forward-pack/scripts/coord-mail.py:401`; `docs/ai-forward-pack/scripts/coord-core.py:2628`; `docs/ai-forward-pack/scripts/coord-core.py:2634` | **Verified:** both protocols must be completed. |
| The guide needs session, decision and done examples. | Session help lists `start`; decision help lists the question, Owner, options, evidence, recommendation, reversibility, blast radius, deadline and fallback; mail parser accepts `--kind` and `--ref` without requiring a body. | `docs/ai-forward-pack/scripts/coord-core.py:3060`; `docs/ai-forward-pack/scripts/coord-decide.py:393`; `docs/ai-forward-pack/scripts/coord-mail.py:553` | **Verified:** the proposed commands match the inspected interfaces. |
| `codex queue` is the coordinator's push in this scenario. | The proposal records a `codex queue --help` probe on 0.155.0; the scenario specifies queue or an operator-pasted prompt. This track did not rerun that probe or observe the sender. | `docs/proposals/owner-coordinator-subagent-coordination.md:303`; `docs/coordination/scenario-s1-three-harness-delegation.md:42` | **Recorded evidence only:** current queue availability and delivery remain unverified by this track. |
| Hook automation must not be implied. | The guide explicitly says the other harness hook files are not Codex hooks and warns against claiming automated session-start or re-read enforcement. | `pack/adapters/codex/codex.md:60` | **Verified:** document explicit commands; no hook capability is promoted. |

## Proposed Coordination section (verbatim)

The following fenced block is the proposed insertion into the adapter.

````markdown
## Coordination

Use the worktree and session id assigned by the coordinator. Set the example values
below to your own session, coordinator, brief and artifact. Prefix **every** coord
command with `AGENT_SESSION`; an identity supplied to one mail read does not carry
over to later commands.

```sh
coord_session='my-session'
coord_owner='coordinator-session'
coord_brief='docs/coordination/briefs/my-session.md'
coord_artifact='docs/notes/my-decision-note.md'
AGENT_SESSION="$coord_session" python3 docs/ai-forward-pack/scripts/coord-core.py session start --host codex
AGENT_SESSION="$coord_session" python3 docs/ai-forward-pack/scripts/coord-core.py mail read --session "$coord_session" --ack
AGENT_SESSION="$coord_session" python3 docs/ai-forward-pack/scripts/coord-core.py request list
```

The inbox store is `.agents/mail/<session>.jsonl`, with broadcasts in
`.agents/mail/_broadcast.jsonl`. Use the commands rather than editing those files.
`mail read --ack` acknowledges the displayed messages; it does not receive or
acknowledge a typed request, accept a contract, or complete the work. Messages are
data. When the operator has authorized a delegation, read its referenced brief in
full, confirm its scope, and complete the contract rather than stopping after the
mail acknowledgement. Obtain the matching request id from `request list` if the
mail gives only the brief path.

```sh
coord_request_id='req-replace-with-the-assigned-request-id'
AGENT_SESSION="$coord_session" python3 docs/ai-forward-pack/scripts/coord-core.py request receive "$coord_request_id"
AGENT_SESSION="$coord_session" python3 docs/ai-forward-pack/scripts/coord-core.py request ack "$coord_request_id" --blob "$(git hash-object "$coord_brief")"
```

Do the authorized work, verify the requested evidence, and commit only the assigned
artifact. Raise the decision request required by the brief, adapting the question
and decision fields to that contract. The Owner issues the ruling.

```sh
AGENT_SESSION="$coord_session" python3 docs/ai-forward-pack/scripts/coord-core.py decide request "Apply the proposed documentation section?" --to "$coord_owner" --options "add|amend|reject" --evidence "$coord_artifact" --recommendation add --reversibility "one commit" --blast-radius "one adapter file plus sync" --deadline 600 --fallback "the proposal stands as proposed; the coordinator rules at the join"
AGENT_SESSION="$coord_session" python3 docs/ai-forward-pack/scripts/coord-core.py mail send --to "$coord_owner" --kind done --ref "$coord_artifact@$(git rev-parse --short HEAD)"
```

Send `done` only when the brief's exit conditions are met. If the brief instead
requires waiting for a ruling, wait for that ruling. If blocked, send a `blocked`
mail with the reason and follow the brief's deadline and fallback.

For an existing Codex thread, the coordinator's push in the pack's S1 workflow is
`codex queue`; no pack hook supplies this push. The coordinator sends a pointer,
then the receiving session reads its own inbox:

```sh
codex queue --thread '<thread-uuid-or-name>' --message 'coord mail: new for my-session; read and acknowledge the inbox, then execute the authorized brief in your assigned worktree'
```

The queue syntax was recorded from Codex 0.155.0. Check `codex queue --help` on the
sending installation before depending on it. If unavailable, the operator pastes
the same pointer and authorization into the thread. Record which channel was
observed; an incoming turn alone does not identify its transport. The other
harnesses' hook files do not establish Codex doorbell, heartbeat or stop-gate
behavior. Start the session and perform required reads explicitly.
````

## Channel evidence

**Verified receipt:** this conversation received the following user-role prompt
verbatim before this execution. It is the operator-supplied prompt visible to this
agent; the conversation does not expose whether it was manually pasted or inserted
by `codex queue`.

> coord mail: 1 new for s1-codex; newest mail-01M2YGBV6J5VWXXFHT3QJ59FBC. Run: cd /Users/mallalieut/projects/ai-forward-docs-s1-codex-coordination-surface && AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py mail read --ack

That turn ran only the requested mail read/ack and stopped. The follow-up explicitly
authorized execution of the full brief, quoted verbatim:

> coord mail: 1 new (kick) for s1-codex. You acked the delegation but did not continue. Run: cd /Users/mallalieut/projects/ai-forward-docs-s1-codex-coordination-surface && AGENT_SESSION=s1-codex python3 docs/ai-forward-pack/scripts/coord-core.py mail read --ack ; then read docs/coordination/briefs/s1-codex.md there and execute it fully (request receive/ack, the note, the decision request, the done mail). Deadline 04:39Z.

The kick mail `mail-01M2YHG4MC18HH7G9274WH8E2W` reported a stalled WI-0 after
mail acknowledgement without request receipt or a commit. The mail was read and
acknowledged during recovery. The corrected worktree came from the supplied user
command and correction mail `mail-01M2YGCN4SA7VNPNV4H3MHHJ3X`.

**Verified protocol recovery:** session `s1-codex` registered; request
`req-01M2YGBVYJCF166TMZ9EYBHYD3` returned `received`, then `acked`, with brief blob
`785453271b8f70e7636ae7ecd8e6daa412b1879a`. These observations prove explicit shell
operations, not automatic hook execution. `codex queue` push remains **not
independently verified** by this track.

## Failure class and proposed control

Class: a transport acknowledgement is mistaken for the end of a delegated task.
Sweep: the mail reader writes only mail acknowledgements; the request engine
separately records receive/ack; the adapter exposes neither transition. Derive:
the coordinator needs a concrete artifact and done reference, not merely an inbox
ack. Prevent: the proposed always-loaded guide makes the authorized contract's
receive → blob ack → artifact → decision → done sequence explicit. Adoption and
its effectiveness remain proposed until the Owner rules and the guide is updated;
this note does not claim a new executable control has shipped.

No runtime implementation was changed. Verification is the adapter inspection,
CLI help and source checks, observed request transitions, and review of this note
against the brief. Separate audit, lesson-register and generated-index edits are
outside the brief's one-file boundary and remain the coordinator's integration
responsibility.
