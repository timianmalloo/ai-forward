---
id: proof-multi-harness-runner
title: "Proof: bounded multi-harness launch and monitoring"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, verification]
links:
  - { to: proof-coordination-runtime-v2, rel: relates-to }
  - { to: design-multi-harness-runner, rel: implements }
  - { to: spec-multi-harness-launch-and-monitor, rel: implements }
review-by: "2026-12-20"
review-suggested: []
summary: >-
  Real git repositories and offline subprocess peers prove the deterministic runner's
  admission, worktree, authority, bounded transport and evidence paths. Independent
  review closed eight runner findings; live provider/profile qualification remains
  separate from this implementation proof.
---

# Proof: bounded multi-harness launch and monitoring

> Reviewed 2026-09-21: this document retains its original observation/plan scope. Current controls and qualification limits are in the [runtime proof](../proof/coordination-runtime-v2.md). Final handback now independently requires a checked worker Owner-decision state with zero open requests and a live leader, after receipt verification. Native Stop or transport completion alone cannot establish readiness. The historical negative profile observations below remain historical; they are not a current deployment verdict.

Live-profile follow-up: [local qualification](local-coordination-profiles.md) found
ACP startup-notification and Agy denial-envelope blockers after integration. The
fixture proof below remains scoped to its tested contracts; unattended rollout is blocked.
The [native repair and requalification](native-coordination-repair.md) fixes those two
transport defects and records the remaining actual-profile blockers.

Branch: `feat/multi-harness-runner`. Tier T2. Date: 2026-09-20.
This proof concerns the **opt-in POSIX pilot**. It does not qualify installed pack hooks
or an arbitrary user's provider policy. The independent live ACP specification/spike is
committed as `abe0cc0` on `feat/acp-compatibility-spec`.

## Claims and evidence

| Claim / spec | Observed evidence and oracle | Red evidence | Confidence / limit |
|---|---|---|---|
| Contract and compiler admission, AC1 | Installed-entrypoint tests reject missing bounds, duplicate/parent identities, open decision requests, aggregate overflow and rewritten manifests; real `prompt-compile finish` output is normalized without its native CLI wrapper | Initial runner suite failed before the script existed; review reproduced unbound rendition and oversize admission | Verified for tested contract shapes; Owner still supplies the complete track contract |
| Separate actual checkouts and identities, AC2–3 | Real linked checkout with a different HEAD produces workers at that HEAD; two worker processes record distinct env/cwd; reused session and substituted clone rejected | Independent disposable reproductions exposed both reuse and clone substitution before fixes | Verified; native tools remain subject to separately qualified permissions |
| Claude/Codex Owner parity and leadership, AC4 | Both Owner host labels run the same CLI; competing leader blocks; successor ref remains byte-identical after cancellation/old-epoch renewal attempt | Missing-entrypoint red; real ref mutation and stalled Git fault injection | Verified for cooperative local protocol; no new election mechanism |
| Bounded session control, AC5–6 | 23 transport subprocess tests cover ACP/Agy repeated turns, schema/error/EOF, byte floods, unterminated lines, stalled stdin, denial, cancellation, process descendants and setup failure | Red-first transport suite; denial, non-success completion and per-token progress mutations killed | Verified against local peers; live spike supplies separately scoped provider contract observations |
| No false ready, AC7 | Missing artifact and symlink fail after successful transport; new descendant commit returns actual HEAD; unchanged commit fails; permission/truncation/unknown result cannot be complete | Initial suite red; independent worker-log false-ready reproduced and fixed; duplicate buffered Agy SUCCESS reproduced red | Verified structural evidence only; semantics require Owner review |
| Recovery and no implicit replay, AC8 | Duplicate/concurrent run does not send another prompt; partial preparation lists retained tree/brief and unprepared worker; status requires Owner admission | Parent observed partial status fail and worker-log false ready, then both pass | Verified; SIGKILL/crash may leave state `interrupted_or_running`; no guessed recovery |
| Normal telemetry, AC9 | Run/worker events and status retain duration, byte volume, turn/progress counts, permission disposition, epoch and explicit unknown spend | Secret sentinel absent from status and every ledger; bounded progress fault/mutation | Verified emitted/read back in real-process fixtures; no model-token/spend measurement claimed |
| Installed reach, AC10 | Tests copy shipped scripts into a real consuming checkout; source skills, Copilot prompt, shared references and deployed modules are regenerated together | Missing installed entrypoint was the initial red; bundle drift is checked separately | Generated-surface and bundle results below |

Parent observation: **29 integration tests passed in 22.809 seconds**, with ResourceWarning
treated as an error. Transport: **23 tests passed in 5.531 seconds** in the parent worktree.
These are test-suite durations, not a provider speed benchmark or transport overhead estimate.
Independent reviewer separately ran 26 integration tests before the final three receipt/
manifest cases were added: all passed in 20.382 seconds. Seven independent disposable
review reproductions also passed after correction.

## Failure, threat and privacy controls

| Failure / boundary | Control | Negative proof |
|---|---|---|
| Untrusted or separately edited prompt rendition | Render only verified compiled sections, with assigned-worker envelope | Poisoned rendition absent; actual compiler-finish wrapper absent |
| Qualification versus launched process | Freeze executable resolved using child cwd/PATH; hash effective bindings; recheck queued worker at spawn | Relative executable change, config drift and queued drift |
| Check/renew authority race | Bounded helper checks admitted holder/epoch in existing leader CAS | Same Owner with successor epoch cannot be renewed |
| Hung Git while model is alive | Independent transport deadline/cached expiry plus outer bounded leader call | Inject 30-second Git stall; worker reaped within asserted cleanup window |
| Output/input resource exhaustion | Nonblocking pipes, cumulative byte cap, bounded single frame, one total attempt deadline | stdout/stderr flood, no newline, stopped stdin reader, multi-turn deadline |
| Permission elevation / false success | Denial-only callbacks, sticky denied state, positive terminal whitelist for every turn | Permission mutant and unknown/non-success stops fail even with artifacts |
| Wrong artifact / wrong checkout | Registered common-dir identity, descriptor-relative no-symlink reads, commit ancestry | Clone substitution, traversal, symlink, unchanged commit |
| Worker claim promoted to Owner evidence | Status filters admitted Owner facts and requires matching started epoch | Worker writes finished in its own log; status remains prepared |
| Conversations or secrets in durable records | Bounded operational metadata only; no raw tool/error/output/environment values | Sentinel absent from actual status and ledger files |
| Private prompts and session linkability | Prompts retained under private common-git run metadata; pseudonymous ledger links intentional | Metadata/receipt inspection; same-user forgery is an accepted existing boundary |

Defect classes `RUN-A` and `PROC-A` record the class → sweep → derive → prevent work and
the automated controls. The reader-size bound covers aggregate serialized data before
worktree creation. Partial preparation and exclusive worker reservations are retained after
failure rather than deleted to make a retry appear fresh.

## Change reach and instrumentation

| Surface | Writer | Reader / proof |
|---|---|---|
| Immutable local manifest, worker reservations and start marker | `Runner.prepare`, exclusive private writes, `Runner.run` | hash-bound load, duplicate refusal, status |
| Existing coordination facts | `Runner.event`, existing `core.append_event` | Owner-filtered `Runner.status`; no second event ledger |
| Native session wire | `coord_transport.run_session` | ACP request IDs or Agy single-flight sequencing; local peers |
| Artifact receipts | `Runner.verify` | terminal result and Owner review; file bytes/hash or actual commit |
| Skill / CLI UX | canonical skill, Copilot adapter prompt and launch reference | generated surfaces and installed-entrypoint tests |
| Operator cost axes | normal transport duration/byte/count/status fields | JSON result and status; token/spend `not recorded` |

No graphical product UI is added. CLI empty/invalid, prepared, partial, blocked, running,
failed, cancelled, evidence-incomplete and ready states are structured; color is unnecessary.
The separate ACP HTML artifact has its own final-hash desktop/mobile render evidence.
Graphical craft, asset generation and HTTP problem responses are N/A to this runner.

## Testing Strategy and reproduction

Applied union: D0–D4, D6–D7, A1, A3–A4, A6. Real Git refs/worktrees exercise state and
concurrency; real subprocess peers exercise wire/OS failures; source mutations exercise
the load-bearing safety assertions. No provider credentials or online model call is needed
for deterministic CI. Model-authored task quality remains an Owner semantic review.

```sh
python3 -W error::ResourceWarning -m unittest discover -s tests/docs_explorer -p test_coord_runner.py
python3 -W error::ResourceWarning -m unittest discover -s tests/docs_explorer -p test_coord_transport.py
pwsh tools/sync-pack.ps1
pwsh tools/verify-bundle.ps1
```

Independent runner review: PASS after seven reproduced defects and one queued-worker
check/use finding were corrected. Parent reviewed the independent transport module and
requested the red-first duplicate-result guard before accepting it. The producer did not
clear its own implementation hard veto.

## Residual limits

- Full installed pack ownership hooks and native policy/trust need profile-specific live
  qualification. A matching hash is drift detection, not proof a hook fired.
- POSIX groups contain cooperative descendants. Malicious same-user files/processes and
  deliberately escaped groups are outside this local coordination boundary.
- Agy exposes no observed per-turn correlation id. The client refuses unsolicited buffered
  results and flushes the admitted input; it does not claim malicious-provider protection.
- Windows interactive launch, arbitrary TUI attachment, cross-process resume, dynamic
  mailbox prompting, interactive permission approval and automatic integration are absent.
- Run data is retained for review. There is no implicit retry or automatic cleanup/deletion.

## Gate record and status

Implementation review: PASS. Targeted tests: 52 passed. After regenerating the count/API/
reading surfaces and advancing the refresh metadata to revision 85, the final full
`pwsh tools/verify-bundle.ps1` run passed **all 17 gates**. Its Python gate reports
**1,137 passed, 12 skipped, 321 subtests passed in 117.22 s**. Node contracts, rendered
explainer proof, graph/audit validation, source/install drift, portability, coordination
installation and context budgets all passed. The local Python test dependency was installed
in an isolated temporary venv using CI's pytest install step; no runtime dependency was added.
Only this result record and audit closure changed afterward; their packaging checks are
rerun without repeating the unchanged test suites.

| | |
|---|---|
| Completed | Specification, independent live ACP evidence, design, implementation, full tests, generated surfaces and adversarial review |
| Remaining | Live profile qualification is required before unattended adoption; no implementation gate remains open |
| Best next action | Review the opt-in pilot and qualify actual native instructions/hooks/policy; preserve Owner review and existing join |
