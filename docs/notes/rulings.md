---
id: rulings
title: "Rulings — the Owner seat's numbered decisions (the only definition site)"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, owner-review, rulings, register, d6, id-a]
links:
  - { to: spec-owner-review, rel: relates-to }
  - { to: design-owner-review, rel: relates-to }
  - { to: spec-agent-coordination-doctrine, rel: relates-to }
review-by: "2027-03-19"
review-suggested: []
summary: >-
  The ruling register. Each `### Ruling NN — <title>` heading defines exactly one numbered
  decision of the Owner seat; prose anywhere cites it as `Ruling NN`. Written only by
  `coord decide rule`; numbering is read from these headings (no allocator elsewhere, class ID-A);
  `verify-ruling-citations.py` fails a cited number with no heading here and a number defined
  twice. Merge class `register` (union).
---

# Rulings

One heading, one decision. A ruling is never edited in place: a later ruling supersedes it in
prose and cites it. Each block carries the decision request it answered and who ruled. The Owner
seat rules; the requester never rules on its own request (D6, reviewer ≠ author).

### Ruling 1 — Create the ruling register and rule through it

The Owner seat's decisions are numbered headings in this file and nowhere else. A decision
request is P1's typed seam request carrying options, evidence, recommendation, reversibility
and blast radius, a deadline and a fallback; a ruling answers it by `coord decide rule`, which
appends the next heading here, resolves the request with `Ruling NN`, and mails the requester.
A number cited in prose with no heading here, or defined here twice, fails the gate.

- request: none (the register's founding decision, made by the coordination plan `coordination-p3-p5-p8`, fixed contracts) · ruled by: coord-p3-p5-p8 · at: 2026-09-19T20:50:00Z

### Ruling 2 — Smoke test: the Claude Code stop gate refuses a stop while a decision request is open

Observed 2026-09-19 on Claude Code 2.1.278, headless (claude -p) in a linked worktree with AGENT_SESSION=smoke-claude-1: the Stop hook exited 2 with the owner-review reason; the host fed it back and the model reported 'The Stop hook refused the stop because of one open decision request' without ruling or expiring it. Heartbeat rows from the same session: PostToolUse and Stop, calls counted. Both Claude Code channels move from observed-only to enforced.

- request: req-01M2Y374DXAC09F83Q0VXGYSCH · ruled by: smoke-owner-1 · at: 2026-09-20T00:37:30Z

### Ruling 3 — S1 track G: replace the Hooks section of pack/adapters/grok/grok-surface.md with the note's proposed text

Ruled replace. The note (docs/notes/note-20260920-s1-grok-hooks-surface-freshness.md, commit a19c6bd on docs/s1-grok-hooks-freshness) shows the installed .grok/hooks/ai-forward.json wires five scripts on five events while the surface doc names two; no claim in the doc is false, the defect is omission. The coordinator applies the proposed text verbatim at the join and syncs. Channel evidence from this track: the session ledger .agents/log/s1-grok.jsonl carries a host-fired heartbeat row {event PreToolUse, host grok} - the Grok heartbeat channel moves to enforced; the doorbell additionalContext line and a refused Stop were 'not seen' by the session, so those two rows stay observed-only.

- request: req-01M2YH6PR3E924YF4RBW2DD275 · ruled by: coord-p3-p5-p8 · at: 2026-09-20T04:30:44Z

### Ruling 4 — S1 track C: add the proposed Coordination section to pack/adapters/codex/codex.md

Ruled add. The note (docs/notes/note-20260920-s1-codex-coordination-surface.md, commit 90cc0e9 on docs/s1-codex-coordination-surface) verifies that codex.md documents no path from a Codex session to its inbox and proposes a Coordination section (session start, mail read --ack, the AGENT_SESSION prefix, request ack, decide request, done mail, codex queue as the only push). The coordinator applies it at the join. Channel evidence: both coordinator pointers arrived in the Codex thread as user-role prompts and are quoted verbatim in the note; the coordinator sent them with codex queue (queued ids 01a0bd06 and 01a0bd18), nobody pasted them - the Codex push channel is verified. Lesson for the pointer text: the first pointer said only 'run mail read --ack' and the session did exactly that and stopped; the second said 'then execute the brief' and the track completed. The doorbell pointer must name the action after the read.

- request: req-01M2YHQ24BQ52GN4VTZ4DER247 · ruled by: coord-p3-p5-p8 · at: 2026-09-20T04:39:21Z

### Ruling 5 — Stop-gate probe on Antigravity: the gate's continue decision holds a stopping session while its decision request is open

Ruled yes, observed 2026-09-20 13:50Z on Antigravity 1.2.7, headless (agy --add-dir <tree> -p) with AGENT_SESSION=smoke-agy-2 and this request open: the session's final output read 'Termination was blocked by the stop hook because there is unread coordination mail for session smoke-agy-2.' and then 'Termination was blocked because session smoke-agy-2 has an unresolved decision request that must be ruled or expired before stopping.' - two refusals (AGY_MAX_REFUSALS), then the stop was allowed with the reason on stderr. In the same probe series the PreInvocation doorbell injected its ephemeralMessage (quoted verbatim by the model) and PostToolUse counted calls (Stop row calls=2). All three Antigravity channels move from observed-only to enforced; the S1 fallback note's Stop verdict is superseded.

- request: req-01M2ZH9713A9BT4PWZ894R5BEA · ruled by: coord-p3-p5-p8 · at: 2026-09-20T13:52:51Z

### Ruling 6 — Bound early Grok updates to the confirmed session

Approved bounded single-candidate identity plus count during session/new, matching response required before creation/prompt authority. Keep existing deadline/output/cancellation bounds. Native permission requests must require an already established nonempty session identity; a null or missing ID must not match the pre-creation None state. Prove early permission refusal, foreign/malformed/EOF/flood/cancellation cases and killed correlation/phase mutations. No raw update retention, policy changes, new schema or prompt replay.

- request: req-01M30NFSZ8ARJA2WHSRNQCPVVN · ruled by: coord-e2e · at: 2026-09-21T00:23:32Z

### Ruling 7 — Separate native Stop behavior from final decision handback

Approve the native-profile-controls design with strict bounded decision-ledger validation, known-empty initialization check, bounded IDs plus total/truncation, and final exact leader/cancellation fence before readiness. Preserve receipts and distinguish RUN-DECISION-OPEN from RUN-DECISION-NOT-CHECKED. Keep Agy ownership success neutral rather than granting permission; observe ordinary write under documented normal mode before selecting policy. Preserve Codex approved apply_patch hash; separate Stop definition awaits native user trust review. Grok1.0.34 advertises blocking Stop contrary to current web documentation: preserve requested refusal and label only observed runtime enforcement, never infer it from either source. No new broker, replay, dynamic prompt loop or permission bypass.

- request: req-01M30NZ4Z1VQHG9SBMNZRKK2DK · ruled by: coord-e2e · at: 2026-09-21T00:31:49Z

### Ruling 8 — Contain the measured Grok skills-reload response defect

Approve only the documented workaround selected by initialize metadata grokShell true and exact agentVersion 1.0.34, after confirmed session creation and during a pending session/prompt. Consume only the exact JSON-RPC skills-reload nested result with integer reloaded equal to one; count separately without granting authority, acknowledging permissions, or completing the pending RPC. Wrong versions, IDs, fields, types and phases still fail. Preserve existing time, bytes, cancellation and cleanup bounds. Record reported version provenance. Kill selector/envelope/response-authority mutants and run a fresh two-turn diagnostic. This workaround expires at a changed runtime binding and does not weaken generic ACP response correlation.

- request: req-01M30P12KWPRP2J9CGCY2PGFVA · ruled by: coord-e2e · at: 2026-09-21T00:32:51Z
