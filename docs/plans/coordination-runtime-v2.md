---
id: plan-coordination-runtime-v2
title: "Coordination runtime expansion and portable proof"
type: plan
status: active
owner: "@timianmalloo"
phase: coordination
tags: [coordination, runtime, proof]
links:
  - { to: spec-coordination-runtime-v2, rel: implements }
  - { to: design-coordination-runtime-v2, rel: depends-on }
review-by: "2026-12-21"
review-suggested: []
summary: "Bounded integration, portable historical evidence, and runtime control work."
---

# Coordination runtime expansion

Goal: reconcile the three pushed feature branches, enable bounded unattended work,
make historical proof reproducible from a fresh single-branch clone, and add live
session attachment, dynamic prompts, safe retries and explicit permission decisions.
Done when each supported path has inspected execution evidence, unavailable native
capabilities are named, and local main equals origin/main. T2. No blanket approvals,
automatic semantic acceptance, automatic push by workers, or terminal keystroke injection.

## Execution graph

Ground and compile → independent capability spike / independent portable-proof slice /
root branch reconciliation and specification → independent design review → runtime
implementation → independent security and correctness review → native qualification +
fresh-clone verification → sync, full bundle gates → linear integration, push, cleanup.

The root owns runner, private control store, skill, spec/design and integration.
`coord-proof-fresh` owns only the historical-proof verifier, its Git fixture/tests and
its reproduction note. `coord-runtime-spike` owns capability research; transport changes
are assigned only after the callback contract is reviewed. Each has a separate worktree.
Fan-out two; no shared index or generated-file integration until join. Initial budget:
150 root tool calls / 90 minutes, with an explicit reassessment if evidence remains open.
Retries have diagnosed preconditions, one automatic retry maximum by default, and never
replay an ambiguously dispatched model prompt. Failure retains evidence and worktrees.

## Integration findings

The pushed ACP and native-control branches contain work already linearly integrated
into main. Their late audit records still need reconciliation. The transport snapshot
predates current main's wire repairs. Resolve overlaps using current fixes, retaining
new audit facts; do not replace current source with the old snapshot. Main requires
linear history. Reviewed feature contents land by squash, not a merge commit.

The original proof references Git objects outside a fresh single-branch clone. The
proof track has reproduced that failure and measured a compact original-object fixture
that executes the same ancestry/tree/blob assertions in an isolated bare object store.

## Measurement and join

Record actual test counts, failure codes, native versions, permission decisions, prompt
dispatch counts and retry counts. Cost/tokens remain `not recorded` unless supplied by
the runtime. Source inspection establishes a contract, not a live capability verdict.
Finish with planned-versus-actual observations, remaining limitations and task-tree cleanup.

## Actual join and release corrections

The two independent tracks completed and their reviewed changes were joined. Native
two-turn canaries passed on all four runtimes. Claude and explicitly mode-selected Codex
produced inspected once-only approvals; Grok's current profile produced no callback and
remains ask-unqualified. Codex app-server and Grok live leader attachment were measured;
Terminal.app is the Owner's selected terminal host. Claude/Agy generic live attachment
and Windows containment remain outside the proven capability set.

The initial aggregate run passed 1,258 Python tests and 505 subtests with 12 skips, but
three tests and six release gates failed on stale generation and portability defects.
Source edits during that run also made its install comparison stale. The final run
therefore starts only after source freeze, synchronization and staging. The inherited
ledger portability defect is repaired at the centralized writer and explicit migration,
with two new red-first tests; no gate is muted. Root tool-call count was not recorded;
the earlier planning audit's asserted count overrun was not measured and is withdrawn.
Actual elapsed time and final gate results are recorded by the closing audit.

Reconciled remote tips: ACP `bb1e6c610f976a6ebf180a985c64bf75e82cf41a`, native controls
`e05786c1fb13442ba04b142485c731531099f48a`, bounded transport
`193fb9baee2e8b72e3536d2d2be023aa45f37ca3`. Their functional snapshots were already
integrated before newer main repairs. Retain those newer repairs and union all late
append-only audit facts; squash reconciliation preserves protected-main linear history.
