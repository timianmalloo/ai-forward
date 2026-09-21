---
id: proof-coordination-end-to-end
title: End-to-end coordination qualification
type: proof-pack
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, qualification, acp, proof]
links:
  - { to: coordination-end-to-end, rel: implements }
  - { to: design-multi-harness-runner, rel: implements }
  - { to: spec-multi-harness-launch-and-monitor, rel: implements }
  - { to: proof-native-profile-controls, rel: relates-to }
  - { to: proof-native-ownership-enforcement, rel: relates-to }
review-by: "2026-12-21"
summary: Actual local worker controls, negative handback fences, four reviewed Codex-owned joins and one directly inspected native Claude-owned join; bounded POSIX profile evidence, not blanket unattended authorization.
---

# End-to-end coordination qualification

Verified: the installed local profiles for Claude, Codex, Grok and Agy complete the bounded
coordination workflow. Both an actual Codex Owner and an actual native Claude Owner
operated the workflow and joined independently reviewed receipts. No remote push occurred.
This is finite evidence for the recorded profiles. General unattended coordination remains
disabled; a different checkout, environment, executable, policy or hook binding needs fresh
qualification.

## Actual worker matrix

Each row includes instruction discovery before a native read, an exact permitted native
write, refusal of a leased edit with unchanged held bytes, and cancellation after observed
active work. Cancellation times measure the trigger to transport return; no completion
marker or surviving observed worker process was present.

| Worker | Permitted write / leased refusal | Open decision refused by native Stop and runner | Active cancellation | Accepted receipt / local join |
|---|---|---|---|---|
| Claude | Verified | Verified | 0.406 s | Verified; joined `155682a68541` |
| Codex | Verified | Verified | 0.205 s | Verified; joined `e252f6eb6400` |
| Grok | Verified | Verified | 0.327 s | Verified; joined `1d4f242d937b` |
| Agy | Verified | Verified | 0.211 s | Verified; joined `733079f94d42` |

All four positive runs received and acknowledged the exact instruction blob, created the
admitted receipt, raised one typed Owner decision, and sent done mail. Rulings 13–16 followed
request-specific native Stop refusals and independent receipt checks. The runner then
reported `ready_for_review`, checked zero open decisions, and stopped the review monitor.
Only each declared receipt was committed. Each local join passed its nine configured gates;
the join contract does not run the explainer-render gate and configures no build or push.

The four separate negative attempts retained completed transport and valid receipts while
the runner returned `RUN-DECISION-OPEN`. Their later cleanup rulings did not change the
blocked attempts into successful runs. Negative attempts and diagnostic canaries were not
joined or replayed.

## Actual Owner choice

Codex operated the four-worker matrix from its designated seat, reviewed actual receipts,
issued the bounded rulings, and completed the four configured joins. Leadership came from
the repository designation, not from the worker harness.

Actual Claude session `df14fa70-9062-4728-af57-c2744807fc9e` operated as `coord-e2e-claude-owner-2` at epoch 12. Its native transcript contains the driver invocation,
direct receipt/evidence inspection, acceptance, selective worker commit and conductor join.
The private driver supplied deterministic mechanics and never committed or joined. Claude
performed those final actions itself after its own review. The raw transcript, control
observations and report are hash-bound in the finite evidence corpus.

Claude's accepted worker commit is `38a2d0b64f9cca6206c849d965be119c40e8b829`; its Owner join is `bb059d980d1295f7929329e434b0d34bcd9fb5a7`. The worker commit contains exactly its declared Markdown
receipt, its parent matches the admitted source, and the receipt bytes match in the worker
and joined tree. The native session and its observed descendants terminated cleanly.

## Repairs established by the complete workflow

The surface list was compiler/delegation → isolated worktree → ACP or Agy transport → native
instructions and hooks → shared request/mail ledgers and leader ref → exact receipt → Owner
ruling → strict runner decision state → reviewed join → durable audit and documentation.
Local workspace canaries alone did not establish the shared-ledger side effects.

- Grok's measured early session traffic and exact versioned reload response now have bounded
  protocol handling. Its native `search_replace` edit name is covered by the ownership guard.
- Native Agy/Grok tool payloads and Codex Stop responses use the observed host contracts.
  Agy's selected `accept-edits` argument and reported `request-review` init value are retained
  separately; behavior establishes the qualified file-edit profile.
- Codex's two exact approved hook definitions remain enabled and trusted. The original
  `apply_patch` definition is `sha256:2a61e11f3c15ee291fb8820452f81f09d4924a2aa35654ee5059cb8f33f9be33`;
  Stop is `sha256:06a60eceeece9b9c70f5ecdabdd8372477e1d947757558eac9f3c01789866698`.
- Explicit Codex file roots permit only the required request ledger, worker log and Owner
  inbox. Canonical regular-file and identity checks reject aliases, directories, symlinks and
  replacement. Native sandbox probes also checked adjacent-file refusal. No parent-directory
  grant or global trust/permission change was used.
- The final runner fence reads bounded, strict decision state. Open or unreadable decisions
  cannot become ready, even after a native Stop loop guard permits the model turn to end.

## Failed observations and corrections

The first Grok ownership attempt did not qualify before the native edit-name repair. The
first Codex handback returned `RUN-EVIDENCE` because workspace sandboxing refused the shared
request ledger; it produced no qualifying acknowledgement or receipt. Both remain failures.

The first actual Claude Owner attempt stopped during preparation: a private test helper
used runtime host `claude` where the compiler requires template `claude-code`. Real compiler
fixtures reproduced the error and passed for both Owner hosts after the mapping fix. The
second attempt used a fresh Owner checkout, worker identity and tag. No failed attempt was
replayed. The first native report also misattributed a later lease renewal to the outer
launcher from a process listing; actual PostToolUse/Stop heartbeat records establish the
renewing source. The original report and this correction are both retained.

Independent review reproduced private evidence-checker false passes and an interrupted
driver child leak. Correlated request/native-action checks and exception-path cleanup were
repaired before use. The driver passed 17 focused tests, the outer process observer four,
the join helper three, and the compiler mapping two real-template tests. Private helpers
are qualification fixtures, not new installed orchestration services.

## Verification and reproducibility

The reviewed source proof covers all 17 release gates: 1,201 Python tests passed, 12 were
explicitly skipped, 440 subtests ran, and 34 Node tests passed. Render checks passed. The
first integrated run failed only the drift check because reviewed preparation-audit files
were unstaged; staging and the metadata/browser rerun corrected that with unchanged source
and test bytes. This is combined gate evidence, not one all-green full run.

The sanitized corpus is [end-to-end-qualification.json](../knowledge/acp-compatibility/end-to-end-qualification.json).
Its [finite consistency verifier](../knowledge/acp-compatibility/verify-coordination-end-to-end.py)
checks the recorded matrix, exact trusted definitions, receipt bytes, real commit ancestry,
both Owner roles and retained failures. Export also rechecks private raw hashes and reruns
the independently reviewed raw-evidence checker. The public verifier does not launch models
or issue a reusable qualification attestation.

Git checks require the retained local archive branches: `archive/coord-e2e-native-proof-joins`
and `archive/coord-e2e-final-owner-proof-joins`. A fresh clone containing only linear main
will not contain all original worker/join objects. The archive is local; no branch was pushed.

Run from the repository:

```sh
python3 docs/knowledge/acp-compatibility/verify-coordination-end-to-end.py
```

Raw native records stay private and are identified by filename plus SHA-256 in the corpus.
Aggregate tokens, spend and tool-call totals for the entire qualification were not
computed. The native Claude Owner session does contain provider-reported usage: USD
3.379134, 78 input tokens, 18,055 output tokens, 3,570,200 cached-read tokens and 113,954
cached-write tokens (3,702,287 reported total). This is session telemetry, not the cost of
the entire qualification or a verified bill. Timings reported above are measurements.
No performance speedup is inferred from concurrent tool execution.

## Operational boundary and next use

Use [execute-with-coordination](../../.agents/skills/execute-with-coordination/SKILL.md) and
its [launch reference](../../.agents/skills/execute-with-coordination/reference/launch.md)
from either Claude or Codex. Select the Owner explicitly, prepare fresh worker contracts,
qualify each actual binding, run the bounded dispatcher, review the evidence, then use the
existing conductor join. Grok and Agy can invoke the same installed scripts.

The POSIX pilot does not attach to arbitrary existing terminals, dynamically prompt a
mailbox, approve interactive permission requests, retry started runs, or support Windows.
Native file hooks do not contain arbitrary shell writes. Existing local Grok/Agy permission
settings were observed and bound. This proves the named coordination controls, not complete
compliance with every pack instruction. The recommended next use is a small real task with explicit
ownership and bounded prompts under the selected Owner, retaining independent review.
