---
id: note-20260919-mail-store-deviations
title: "The mail store keeps the fixed contract with three named additions: a broadcast file, prefixed ULIDs, and colocated acks"
type: decision-note
status: draft
owner: "@timianmalloo"
phase: "coordination P4"
tags: [decision-note, coordination, mail, p4, p6]
links:
  - { to: spec-message-layer, rel: relates-to }
  - { to: design-message-layer, rel: relates-to }
  - { to: proposal-owner-coordinator-subagent-coordination, rel: relates-to }
review-by: "2026-12-18"
review-suggested: []
summary: >-
  Three shapes the fixed mail contract left open are settled here and raised to the coordinator
  and Track P6 as seam requests before any line was written; blast radius is P6's fold (file
  glob, id ordering, acked? derivation) and nothing else.
---

# Decision note — mail store: three additions to the fixed contract

**Context.** `docs/coordination/coordination-p2-p8.md` fixes the mail store schema, kinds, twin, doorbell and constants. It does not say where a `to: "*"` message lives, what a "ULID" looks like in this pack, or which file an `ack` line goes into. Each of those shapes reaches Track P6's reader, so the rule is *raise, never silently decide*.

**Decisions (raised 2026-09-19 as `req-01M2XDMSD0N3SJSHJESEWAKFF9` → coordinator and `req-01M2XDMSKGF4Y3B9NC8J40VCPG` → p6-board; the contract default holds until resolved):**

1. **Broadcast file.** A message to `*` is appended to `.agents/mail/_broadcast.jsonl`. Reason: `*` is not a valid file name on Windows; one file keeps "one row per message id" for the board (fan-out into every inbox would write N rows). Session ids therefore may not start with `_`.
2. **Id scheme.** `coord_ids.new_id("mail")` — `mail-` + a 26-character ULID body (48-bit millisecond time + 80 random bits, Crockford base32). Reason: one id scheme across the pack (ONE-A); lexicographic order is still time order.
3. **Colocated acks.** An `ack`/`nack` line is appended to the **same file** as the message it references, carrying `from` = the acknowledging session. Reason: "acked?" stays a single-file fold; a broadcast collects one ack per reader in one place.

**What would change my mind.** P6 resolves either request with a different shape → this note is updated and the code follows; the contract owner (coordinator) rules otherwise → same.

**Blast radius.** P6's glob (`.agents/mail/*.jsonl` already matches `_broadcast.jsonl`), P6's sort (string order on ids works), P6's acked? fold (an ack row in the same file). No other consumer.

**Also settled here (below ADR weight).** The ledger twin carries `at` and `session` beside the contract's six keys so `coord-core.read_events` sorts it and `active_sessions` sees no `None` session — additive; `assume:` tolerated by P6's reader (keys on `type` and `mail_id`); confirmed at the join, stripped by the coordinator if not.
