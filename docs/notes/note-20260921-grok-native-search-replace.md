---
id: note-20260921-grok-native-search-replace
title: "Grok search_replace reaches the ownership policy"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, grok, hooks, qualification]
links:
  - { to: design-native-profile-controls, rel: refines }
  - { to: design-native-ownership-enforcement, rel: depends-on }
  - { to: coordination-end-to-end, rel: relates-to }
review-by: "2026-12-21"
summary: An actual Grok search_replace call exposed a missing supported tool name in both native and inherited ownership guards. One instrumented diagnostic captures the exact input; replay tests require real lease decisions rather than an indeterminate denial.
---

# Observed failure and bounded repair

Goal: make the observed Grok native edit reach the existing ownership policy in both
installed guards. Done when exact-envelope regressions prove held/free/own decisions,
unknown and malformed native calls still fail closed, independent review clears the
minimal repair, and all release gates pass before the branch commit. T2; fan-out zero.
No runner changes, global policy/trust changes, new approval path, background service,
or automatic profile attestation. Final native qualification belongs to the coordinator.

The governing contract is native-profile-controls invariant 1: “Every supported native
edit is checked against the complete existing lease policy.” Grounding follows launch
specification AC3/5/7/10 → runner design → native ownership design → ADR-0010. The existing
`cmd_hook` projection owns the lease decision and its append-only per-path fact. No new
record type, identity source, history rule or stored measure is introduced. `AGENT_SESSION`
and actual process cwd remain authoritative; hook payload identity/cwd confer no authority.

Execution graph: capture actual input → recorded red tests → smallest name/matcher repair
→ independent review → source sync and 17 release gates → audit and commit. Each node has
a concrete exit: saved input/outputs, observed wrong lease decisions, passing behavioral
oracles, independent clearance, actual gate results, then retained commit and handoff.
Reasoning owns diagnosis/review; deterministic scripts perform capture/replay/sync/gates.
One native diagnostic was authorized; no native retry is part of this branch repair.
Remaining uncertainty decreases from unknown hook input to a measured parser contract;
a failed final profile run requires diagnosis rather than a silent retry. Parent parallel
work owns other profiles and integration, so no second writer shares this branch.

## Native evidence

The integrated preflight at base `ac35d759e24eea89892ac2ede27391f2e307dab4` completed
three ACP turns in 68.502009 seconds. Instruction recall, native nonce read and the ordinary
file write succeeded. The leased file stayed `OWNER_OWNED`, but `search_replace` failed with
`NOT CHECKED` / `unreadable hook payload (ValueError)`. The only `COORD-REFUSED` ledger row
was the observer's earlier preflight check. An unchanged canary and a completed ACP turn
were therefore insufficient to establish native ownership enforcement. Private observation:
`/tmp/coord-e2e-neg-grok-ownership.json`, SHA-256
`95f27b52d425b2febb41ba917a1d237af0c2606919c283d1ccaf425b9119b8be`.

One fresh registered diagnostic tree, `ai-forward-test-grok-native-search-replace-envelope`,
session `e2e-grok-envelope`, ran a single held `search_replace` under Owner `coord-e2e`, epoch
8. Passive wrappers forwarded identical stdin to both original ownership commands and
returned their exact stdout, stderr and exit status. Each capture was created mode 0600;
input was capped at 64 KiB, the original five-second hook timeout remained configured, and
the wrapper bounded its child to 4.5 seconds. Wrapper failure would deny, never approve.
Transport stayed bounded at 180 seconds / 4 MiB. The original command strings and config
bytes are retained privately. Instrumented config fingerprints make this a diagnostic,
**not final profile qualification**. No permissions or trust settings were changed.

Both handlers received the same actual envelope: camelCase `toolName` / `toolInput` and
snake_case `tool_name` / `tool_input`, all naming `search_replace`. Both input objects
contained the same absolute `file_path`, `old_string` and `new_string`. The original payload
reported `permissionMode` / `permission_mode` as `bypassPermissions`; this is the observed
existing local policy, not a setting established or changed by the repair. The sanitized
fixture preserves every observed key and replaces paths, identities, time and edit contents.

| Handler, actual command selector | Observed result before repair | Consequence |
|---|---|---|
| Inherited `.claude/settings.json`, `hook --host claude` | `allow`, “coordination: no write to a coordinated path” | The unknown write name was filtered out before lease policy. |
| `.grok/hooks/coord-ownership.json`, `hook --host grok` | `deny`, `NOT CHECKED`, `ValueError` | The native parser rejected the unsupported tool name before checking its path. |

Private capture directory: `/tmp/grok-native-search-replace-envelope/`.

| File | SHA-256 |
|---|---|
| `inherited-claude-14617.json` | `9d1876edeb1f81b52656b82639355b9ca781a572b98923ba25376042392c8879` |
| `native-grok-14634.json` | `8ee8e19e1013a700f16f9c967bd41ccd49ed708e492c20ce4f5dd0573170a75d` |
| `raw.json` | `4e70147018cdb0e89706e9ac07246a75d2b3e258528f5f8c31c45b990cf00730` |

The diagnostic took 13.003927 seconds, read 269,549 stdout bytes and zero stderr bytes,
completed one ACP turn, and reported no cleanup error. The leased canary remained unchanged
and its claim was released. `compatibility_responses=0`; no watcher exception was exercised.
Raw prompts, paths and native output remain private, not in the durable event stream.

## Minimal contract change and proof

The parser already supports the observed absolute `file_path`; replay confirmed it resolves
to the correct checkout path. `search_replace` was absent from `_WRITE_TOOLS`. Adding that
one observed name reuses the existing complete lease policy in both guards. The generated
Grok matcher now also names `search_replace` explicitly. Grok's installed hook guide already
maps the `Edit`, `Write` and `MultiEdit` aliases to this native name; an explicit match removes
dependence on that alias translation. Unknown native tools and malformed inputs still deny.
No wildcard, fallback permission grant, alternate identity or new parsing convention is added.

Surface list: observed native name/input → shared supported-write vocabulary → native parser
and existing lease check → supported decision envelope and per-path ledger → emitted Grok
config → source/install sync. The inherited Claude config retains its existing matcher; the
native diagnostic measured its selection of this tool. Existing path, alias, exclusion,
unreadable-state and command-quoting controls remain unchanged and run in the enforcement suite.

Testing Strategy union: D0 hygiene, D1/D2 deterministic policy/parser boundaries, D4 real
filesystem/CLI/ledger integration and D6 recorded native input contract. No HTTP, new UI,
new model prompt product, persistence schema or dependency is introduced. The diagnostic
prompt is finite test instrumentation, not a shipped agent workflow.

| Claim / failure disposition | Oracle and evidence | Red observed / confidence |
|---|---|---|
| Both guards check held, own and free paths | `test_grok_recorded_search_replace_reaches_lease_policy_in_both_guards`: real CLI, correct decision, matching path/host/environment session in ledger; a no-op allow fails | Six subcases failed before repair; Verified after repair |
| Raw edit contents do not enter durable facts | Same test requires both private replacement strings absent from ledger | Existing privacy invariant retained; Verified by actual ledger inspection |
| Missing/empty/typed/outside target and unknown native tool remain unchecked denial | `test_grok_recorded_search_replace_malformed_and_unknown_stay_unchecked`: deny plus `NOT CHECKED`, no credited decision fact | Baseline retained; unknown-tool mutant killed |
| Native emitted matcher selects actual tool directly | `test_grok_generated_matcher_selects_recorded_native_tool_without_aliases`: regex against recorded tool name | Failed before repair; matcher-removal mutant killed |
| Removing supported name is caught in both guards | Disposable source mutation, real CLI tests | Name-removal mutant killed |

Red log `/tmp/grok-native-search-replace-red.log`: seven failures (six lease subcases plus
matcher); malformed/unknown cases preserved their existing fail-closed behavior. Green log
`/tmp/grok-native-search-replace-green.log`: 51 tests and 47 subtests passed in 12.95 seconds.
Mutation evidence: `/tmp/grok-native-search-replace-mutations.log`; three targeted mutants
(missing name, missing matcher, unknown tool admitted) were rejected by their behavioral tests.

Defect class → matcher vocabulary and policy vocabulary diverge, so a real native edit is
either silently excluded or rejected as indeterminate. Sweep → both discovered handlers,
actual dual-key stdin, shared name filter, parser, emitted matcher, decision ledger and
existing native tests. Derive → a refusal qualifies ownership only when the actual tool
reaches the lease policy. Prevent → recorded-envelope regressions assert decision facts for
positive and negative counterparts. The coordinator owns the shared defect-register update.

Independent source review passed: the coordinator reviewed the two-line name/matcher repair,
the actual captured dual-key stdin and the regression fixture, then independently observed
51 tests and 47 subtests pass in 13.16 seconds. After this repair the inherited Claude-shaped
guard may refuse a Grok edit before the native Grok handler runs. A `hook_host=claude` refusal
is legitimate evidence for that Grok action when correlated to its actual call and path;
requiring both handlers to run after the first deny would misclassify the native chain.

Source sync and API generation completed. All 17 release gates passed using
`PATH=/tmp/ai-forward-runner-verify-venv/bin:$PATH pwsh tools/verify-bundle.ps1`:
1,194 Python tests and 415 subtests passed in 154.66 seconds, with 12 explicit Python skips;
all 34 Node checks passed without skips; the explainer render/accessibility assertions,
source/install drift, graph, audit and other release controls passed. Gate output is retained
at `/tmp/grok-native-search-replace-verify-bundle.log`. Only this evidence text, metadata and
official audit-derived records were updated after the source gate; source did not change.

Planned versus actual: one diagnostic, one minimal red/green repair, three disposable mutant
checks, one independent review and one full gate run. No native retry, dependency addition,
policy change or new product surface was needed. The audit marker measures total run duration;
model token cost is not recorded. Fresh native post-fix qualification is deliberately separate
and requires the coordinator's authorization; this branch does not claim it has passed.
