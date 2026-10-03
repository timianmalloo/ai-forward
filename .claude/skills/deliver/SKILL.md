---
name: deliver
description: Deliver one task through only the applicable existing skills, from grounded intent to real-path proof. Use /deliver <request> or /deliver resume <task-id> to continue a paused task without repeating valid completed work.
runs_as: Coordinator
---

# /deliver

## Input
With no task (empty `/deliver` or `$deliver`), ask only **"What outcome would you like me to deliver?"** and stop. Do not compile, create state, run setup or present the command catalog. A question/review-only request authorizes analysis, not product edits; answer it without entering the implementation route. `resume <task-id>` follows the existing checkpoint, not a new task.

## Ground once
**CO-S0 first** (`knowledge/agent-coordination.md`): consume an accepted compiled prompt unchanged; otherwise run `/compile`, preserve the original request, show the contract, and resolve consequential decisions before work. Compare meaning, not just compiler success: no added, narrowed, dropped or substituted criteria. A conflict requires human reconciliation, not a silent edit.

Read relevant existing requirements, code, tests and decisions; follow existing graph links when available. Reuse valid prior spec/design/plan/proof rather than creating substitutes. Establish task type, unresolved questions, risk, authorization and the evidence needed for the original outcome. Read [routing](reference/routing.md); load only selected skills and their required references. **Done:** one grounded contract and a short conditional route, not a tour of all skills.

## Execute the applicable route
Read [checkpoint mechanics](reference/checkpoints.md), create one local task checkpoint, and keep its resume id. Plan once, only where work needs a plan; a selected skill's existing plan is that plan. Execute the current stage to its own exit criteria, record actual evidence, then continue automatically to the next approved stage. Do not ask the human to type another skill command between ungated stages. Never mark a stage complete because a model, tool or transport stopped.

Features use `/implement` with strict vertical red→green→refactor. Defects use `/investigate`, then human approval of repair phases unless an **actual explicit prior human instruction** authorized that repair; the diagnosis is not the fix. Migrations use `/migrate`'s characterization-before-change discipline and are T2; security/identity/data/contracts/money/concurrency, new load-bearing architecture and coordinated execution also impose T2 (§0.2), regardless of diff size. Select missing applicable detailed design at T1/T2; existing valid design may be reused. Genuinely T0 code (e.g. tested local refactor) and T0 docs may self-check without an unconditional review panel; routine features/fixes remain T1+, and every actual applicable veto still requires independent clearance. Omit unnecessary T0 design/architecture ceremony, never outcome proof or a selected skill's applicable preimplementation review. Resolve interface behavior and `/ui-design` before UI implementation. Explicitly requested independent tracks use `/prepare-for-coordination` then `/execute-with-coordination` **instead of** single-session implementation, with approved contracts, termination, deadline and fallback. For coordinated migrations, `migration-characterization` means only `/migrate`'s grounding and old-stack characterization first; carry its coverage veto, increments, equivalence proof and rollback obligations into every track and the join. Do not run a full migration and then dispatch a second implementation. No default spawning or setup/adoption detour. **Done:** stage exit evidence recorded and the next stage selected, or a named gate.

## Pause / resume
At a human decision, permission, hard veto or release gate, checkpoint the exact question, authority, current evidence, actual stage authors and next action; **STOP and send the message** (CO-S2). For partial-work checkpoints or any real hard veto, repeat `pause --actor` for every actual stage author; retain those identities across resume/completion, never rename or omit an author to clear a veto. An unanswered gate never becomes consent. Release and host permissions remain their own gates; this command grants neither.

`/deliver resume <task-id>` works in a fresh session: inspect the checkpoint with `delivery.py status`, re-read contract, identity, inputs and recorded evidence, then obtain/check the **original** authorized decision before recording a bound receipt. Reject drift, missing proof, author self-clearance, stale receipts and model-generated consent. Preserve valid completed work; do not rerun the whole lifecycle. If invalid, explain exactly what must be revalidated; never reset progress silently. **Done:** the same task continues at the first uncompleted approved stage, or remains honestly blocked.

## Hand back the outcome
Verification observes the reviewed product; it does not author a new version. Keep the checkpoint workspace unchanged through verification completion and pauses; write fresh proof locally or externally. Product corrections return through the affected authored stage and applicable independent review, not a permission-pause snapshot replacement.

Use existing reviewer/Proof Pack standards proportionately; authors do not clear their own hard vetoes. Demonstrate every original criterion through its real path, including applicable failures and boundaries. Record the exact criteria→observations→evidence map before closing; report actual changes, tests run, skips, remaining gates and limits. Emit Completed | Remaining | Best next action; stop only at demonstrated completion or an explicit blocker (CT25a).

No automatic repository-wide adoption, new framework, unsolicited documentation, graph/index bootstrap, commit, push, deployment or trust/configuration change. Follow AL0.2/V10 opt-in generated-write rules even when a selected skill's older closing boilerplate says otherwise. Reuse existing artifact homes; otherwise keep routing/checkpoints/evidence local. Audit via the existing script, with honest signals only; no unconditional `docs/audit/` creation or invented Git identity. **Done:** original outcome evidenced, or unmet criteria/gates stated without a success claim.
