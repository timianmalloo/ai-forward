---
id: proof-native-ownership-enforcement
title: Native ownership guard implementation and actual-profile proof
type: proof-pack
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, hooks, qualification, claude, codex]
links:
  - { to: design-native-ownership-enforcement, rel: implements }
  - { to: proof-native-coordination-repair, rel: refines }
  - { to: spec-multi-harness-launch-and-monitor, rel: implements }
review-by: "2026-12-20"
summary: Reviewed native file-edit guards are integrated locally. Corrected-base Claude Write and Codex apply_patch allow ordinary work and refuse active leased edits. The user approved exact-definition Codex trust through native review. No unattended profile is attested.
review-suggested: []
---

# Native ownership enforcement

**The guard is implemented; Claude's native Write and Codex's native apply_patch now enforce
the tested lease after explicit approval of Codex's exact hook definition.**
No unattended operation is enabled. Corrected source commit
`7d3f10b93f1e55f3b35f9aea490576acffca37bd` contains the guard, explicit project entries and
regressions, and is integrated into local main. The first observation used `cceb3f4`;
final disconfirmation then reproduced a reverse lease-case alias and future-file collision.
The correction normalizes lease patterns/exceptions too and measures directory case behavior.
A fresh corrected-base Claude control passed independent review
`al-01M30KTQCPZAFSDXXWN6E0BDY0`; Codex passes independent review
`al-01M30MAQS9W0NBE5J85VWXYMF3`. No remote push occurs.

## Change and scope

`coord-core.py hook --host codex` recognizes the native `apply_patch.command` envelope,
checks all source/move targets and returns a supported denial for indeterminate inputs or
state. Existing lease facts and environment identity remain authoritative. Native paths use
actual cwd, reject outside-checkout resolution and check physical aliases. Unknown patch
grammar cannot become a partial allow. The bounded recognizer accepts at most 1 MiB and
256 targets. Default legacy callers retain their response contract.

`hook --config --host claude|codex` emits JSON without installing or trusting it. The explicit
repo entries preserve other hooks. A generated command test runs from a checkout containing
spaces, quotes, dollar and backtick syntax; no embedded command executes. Native decision
facts add actual host/cwd context beside environment session identity, never patch content.
Pack source and all deployed copies are synchronized; API and HTML references are rebuilt.

This is ADR-0010's cooperative native-edit guard, not a shell sandbox. Disabled hooks, host
timeouts/errors, arbitrary shell writes and check/use races remain limits. There is no new
daemon, library, approval broker, permission-mode change or hook-trust bypass. The only
trust change is the user's explicit approval of the one reviewed Codex hook.

## Implementation proof

| Check | Observed result |
|---|---|
| Red first | Original native command patch allows a held target. New host/config cases fail argument admission until implemented. |
| Independent review | Reviewer reproduces case-only physical alias, Unicode filename splitting and malformed/unreadable ledger fail-open. Initial clearance is reopened by reverse lease-case/future-file probes; symmetric comparison and preserved exclusions clear `al-01M30KJ6KMWBF9FA52TVT0T64N`. |
| Focused suite | Initial 46 tests and 21 subtests pass. The final full suite also includes reverse leases, future names, lease-side symlinks, explicit exclusions and empty-directory ambiguity: 18 native test methods in total. |
| Three mutations | Ignoring patch targets, ignoring move destinations, and emitting Codex's unsupported `ask` are each killed without test errors. |
| Final full test run | 1,164 Python tests passed, 12 skipped, 359 subtests passed in 128.29 seconds; 34 Node tests and browser rendering/accessibility proof passed. |
| Release gates | All 17 gates passed together on corrected source before `7d3f10b`. The first source run exposed stale API docs and then downstream HTML drift; both were regenerated. A new full run was required by the alias code correction. Later evidence-only metadata checks retain those test results, not silently count them as rerun by `-SkipTests`. |

The temporary deployed-command fixture initially omitted sibling modules; adding both
actual imports made it execute the guard. Its later path-alias failure was a product defect,
not a quoting pass. The defect register records the generalized failure and control. The
API→HTML generation dependency is retained in the verification record rather than hidden
behind the initial green tests.

## Actual profiles

Both final fresh worker worktrees start at exactly `7d3f10b`. The Claude observer records incoming
wire without changing the installed transport, prompts' admission, or permission policy.
It is bounded to 180 seconds / 4 MiB. A coordinator claim protects the leased canary for
240 seconds; the attempt completes and the claim is released before expiry.

| Profile | Measured result | Qualification and next action |
|---|---|---|
| Claude ACP0.79.0 / SDK0.3.274 | Three turns complete in 27.798208 seconds. Native Write creates `PROFILE_WORKSPACE_WRITE`. Native Write to the leased file ends `failed` with the exact REFUSED reason before lease expiry; bytes remain `OWNER_OWNED`. Two native decision rows prove the correct worker session, host and cwd. Captured config/executable bindings are unchanged. | Tested native Write ownership boundary passes. Owner Stop veto, active-tool cancellation and reviewed handback/join remain unqualified; other edit tools have regression coverage but no new native runtime trial. |
| Codex ACP1.12.0 / CLI0.155.1 | Primary integration reveals the expected native hook. The user approves only its exact definition; native individual-hook review changes it to trusted with the same hash. Three turns complete in 37.981709 seconds. Ordinary native patch succeeds; the leased patch is refused with correct host/cwd/session receipts and unchanged bytes. Captured bindings remain unchanged during the post-approval attempt. | Tested native apply_patch ownership boundary passes. Owner Stop veto, active-tool cancellation, reviewed handback/join and other native edit-tool counterparts remain unqualified. |

One captured Claude decision is the preflight rule check; it occurs before launch and has
no native host/cwd. It is excluded from the two native receipts. The transport's `complete`
and `native_denials=0` do not contradict the refusal: that counter measures Agy native denial
envelopes, not Claude tool failure. Completion is never promoted to full profile readiness.

Codex emits one ACP edit item for the allowed patch, but no failed-tool item for the blocked
PreToolUse operation. Its refusal evidence is the native hook decision fact, unchanged canary,
active lease, no later edit call and the agent's explicit denial report. The report alone is
not the oracle. Both native receipts exclude the separate preflight rule check.

Codex's installed adapter sets project trust to trusted inside session configuration.
That differs from exact hook-definition trust, as documented by
[Codex native hooks](https://learn.chatgpt.com/docs/hooks). A read-only inventory control
requested the same project override via process flags, but `config/read` did not confirm the
worker override and inventory stayed empty. This does **not** establish effective equivalence
with an ACP session or prove a runtime enforcement failure. A subsequent controlled observation
resolved discovery: primary checkout integration changed zero hooks to the expected hook, whose
reported sourcePath explicitly names the primary checkout. The launch reference now requires
binding that actual source as well as worker guard bytes. An earlier empty project-config
control made no difference and was removed. The user then explicitly authorized
"Trust this project guard and qualify Codex" (audit `al-01M30M6KDETB877S4TG8SY7X3J`). Native
`/hooks` reviewed the individual PreToolUse entry and marked it trusted; neither Trust All
nor a bypass flag was used. Read-back confirms the same synchronous enabled hook and exact
definition hash `sha256:2a61e11f3c15ee291fb8820452f81f09d4924a2aa35654ee5059cb8f33f9be33`.
No project trust level or permission mode changed. The native UI persisted only the approved
hook trust; no trust database was edited directly.

## Evidence and remaining work

[Sanitized evidence](../knowledge/acp-compatibility/native-ownership-qualification.json)
retains exact hashes, observed native outcomes, finite bounds, receipts and the negative
Codex observation. Raw transcripts stay private. The final Claude attempt emitted 151,318
combined bytes; two Claude attempts and one Codex attempt total 97.142783 seconds and
450,460 bytes. Tokens and spend are not recorded. Run
`python3 docs/knowledge/acp-compatibility/verify-native-ownership.py` to check the finite
corpus and reject six mutations: false readiness, missing Claude refusal, false cwd,
missing Codex native proof, unapproved trust and wrong-checkout session closure.

The seven-node plan executed at model-work width one. Independent review overlapped
mechanical parent work; three native model attempts ran separately. The corrected-base control
was justified by changed guard bytes, not an automatic retry. Review corrections were closed
before the final full release tests. Codex qualification waited for explicit user approval;
the prerequisite was satisfied rather than bypassed. Parent token/call totals were not recorded; skill
duration comes from the audit start marker. All four worker registrations are ended at closure;
dirty canary evidence is retained rather than removed.
Closure first ran from the coordinator cwd: the global session list cleared identities,
but the per-tree fold required matching labels. The final events were corrected from each
registered worker checkout, and the evidence verifier pins that exact closure map.

Best next actions: prove Owner Stop/cancel/handback on Claude and Codex; then repair Grok early-update correlation and
qualify Agy's allowed-write counterpart. Grok and Agy retain the prior proof's blocked
results. Claude or Codex may still lead the runner, but **zero profiles have a complete
unattended qualification**. No positive runner attestation is issued.
