---
id: proof-native-ownership-enforcement
title: Native ownership guard implementation and actual-profile proof
type: proof-pack
status: draft
owner: "@timianmalloo"
phase: coordination
tags: [coordination, hooks, qualification, claude, codex]
links:
  - { to: design-native-ownership-enforcement, rel: implements }
  - { to: proof-native-coordination-repair, rel: refines }
  - { to: spec-multi-harness-launch-and-monitor, rel: implements }
review-by: "2026-12-20"
summary: Reviewed native file-edit guards are implemented. A fresh Claude profile permits its ordinary Write and refuses an active leased Write; Codex hook discovery remains blocked. No unattended profile is attested.
---

# Native ownership enforcement

**The guard is implemented; Claude's actual native Write boundary now enforces the tested
lease. Codex remains unqualified because its expected hook is absent from native inventory.**
No unattended operation is enabled. Source commit `cceb3f4474d200c9ab597b6f6e01895281d64abb`
contains the reviewed guard, explicit project entries, guidance and regressions. This proof
records that first observation. Final disconfirmation reproduced a reverse lease-case alias
and a future-file collision; the follow-up normalizes lease patterns/exceptions too and
measures directory case behavior. A corrected-base native control and final release record
are pending. Local integration is authorized; no remote push occurs.

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
daemon, library, approval broker, global policy change or hook-trust bypass.

## Implementation proof

| Check | Observed result |
|---|---|
| Red first | Original native command patch allows a held target. New host/config cases fail argument admission until implemented. |
| Independent review | Reviewer reproduces case-only physical alias, Unicode filename splitting and malformed/unreadable ledger fail-open. Each is fixed and pinned before clearance `al-01M30JP6RNV51Q1RVB9DN1BQ9T`. |
| Focused suite | 46 tests and 21 subtests pass, including 14 native cases, legacy hooks and linked-worktree behavior. |
| Three mutations | Ignoring patch targets, ignoring move destinations, and emitting Codex's unsupported `ask` are each killed without test errors. |
| Full test run | 1,160 Python tests passed, 12 skipped, 357 subtests passed in 127.62 seconds; 34 Node tests and browser rendering/accessibility proof passed. |
| Release gates | Full run passed every gate except stale generated API docs. API regeneration then exposed its downstream HTML bundle drift. Both were regenerated; all affected metadata/drift gates passed before the source commit. Test results are retained, not silently counted as rerun by `-SkipTests`. |

The temporary deployed-command fixture initially omitted sibling modules; adding both
actual imports made it execute the guard. Its later path-alias failure was a product defect,
not a quoting pass. The defect register records the generalized failure and control. The
API→HTML generation dependency is retained in the verification record rather than hidden
behind the initial green tests.

## Actual profiles

Both fresh worker worktrees start at exactly `cceb3f4`. The Claude observer records incoming
wire without changing the installed transport, prompts' admission, or permission policy.
It is bounded to 180 seconds / 4 MiB. A coordinator claim protects the leased canary for
240 seconds; the attempt completes and the claim is released before expiry.

| Profile | Measured result | Qualification and next action |
|---|---|---|
| Claude ACP0.79.0 / SDK0.3.274 | Three turns complete in 31.362866 seconds. Native Write creates `PROFILE_WORKSPACE_WRITE`. Native Write to the leased file ends `failed` with the exact REFUSED reason and 211 seconds left on the lease; bytes remain `OWNER_OWNED`. Two native decision rows prove the correct worker session, host and cwd. Captured config/executable bindings are unchanged. | Tested native Write ownership boundary passes. Owner Stop veto, active-tool cancellation and reviewed handback/join remain unqualified; other edit tools have regression coverage but no new native runtime trial. |
| Codex ACP1.12.0 / CLI0.155.1 | Project JSON is present, but `hooks/list` at the fresh worker cwd returns zero hooks and no warnings/errors. Native `/hooks` in the author tree also shows zero installed/active hooks. An empty project-config control makes no difference and is removed. | Blocked at discovery. No Codex model turn starts and no hook is trusted or bypassed. Diagnose the missing native source before attempting positive qualification. |

One captured Claude decision is the preflight rule check; it occurs before launch and has
no native host/cwd. It is excluded from the two native receipts. The transport's `complete`
and `native_denials=0` do not contradict the refusal: that counter measures Agy native denial
envelopes, not Claude tool failure. Completion is never promoted to full profile readiness.

Codex's installed adapter sets project trust to trusted inside session configuration.
That differs from exact hook-definition trust, as documented by
[Codex native hooks](https://learn.chatgpt.com/docs/hooks). A read-only inventory control
requested the same project override via process flags, but `config/read` did not confirm the
worker override and inventory stayed empty. This does **not** establish effective equivalence
with an ACP session or prove a runtime enforcement failure. The discovery cause is unresolved.
No user/system configuration or native hook-trust database was modified.

## Evidence and remaining work

[Sanitized evidence](../knowledge/acp-compatibility/native-ownership-qualification.json)
retains exact hashes, observed native outcomes, finite bounds, receipts and the negative
Codex observation. Raw transcripts stay private. Claude emitted 151,522 combined bytes;
tokens and spend are not recorded. Run
`python3 docs/knowledge/acp-compatibility/verify-native-ownership.py` to check the finite
corpus and reject false readiness, missing refusal, false cwd and Codex promotion mutations.

The seven-node plan executed at model-work width one. Independent review overlapped
mechanical parent work; the one native model attempt ran separately. Review corrections
were closed before full release tests. Failed Codex discovery stops downstream qualification;
it does not weaken the admission floor. Parent token/call totals were not recorded; skill
duration comes from the audit start marker. Both worker registrations are ended at closure;
dirty canary evidence is retained rather than removed.

Best next actions: prove Claude Owner Stop/cancel/handback; diagnose Codex's native hook
discovery in the actual ACP launch context; then repair Grok early-update correlation and
qualify Agy's allowed-write counterpart. Grok and Agy retain the prior proof's blocked
results. Claude or Codex may still lead the runner, but **zero profiles have a complete
unattended qualification**. No positive runner attestation is issued.
