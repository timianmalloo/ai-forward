---
id: design-native-ownership-enforcement
title: Native ownership guards for Claude and Codex workers
type: design
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, hooks, ownership, codex, claude]
links:
  - { to: spec-multi-harness-launch-and-monitor, rel: implements }
  - { to: design-coord-enforcement-phase2, rel: refines }
  - { to: adr-0010-enforcement-topology, rel: depends-on }
  - { to: proof-native-coordination-repair, rel: depends-on }
review-by: "2026-12-20"
summary: Reuse the existing lease hook at native edit seams, add Codex patch-envelope support, and install explicit project-local guard entries without weakening native hook trust or claiming shell containment.
---

# Native ownership guards for Claude and Codex workers

Goal: continue the recommended native ownership-enforcement slice. Done when the actual
Claude/Codex file-edit boundary respects leases, or a measured native prerequisite is
reported blocked after the reviewable implementation is complete. T2; fan-out one.
No global trust/permission changes, unattended enablement or remote push. Grok early
updates and Agy allowed-write policy remain separately recorded follow-ups.

Grounding path: `proof-native-coordination-repair` → `design-multi-harness-runner` →
`spec-multi-harness-launch-and-monitor` AC1 (unknown is not enforced), AC3 (environment
identity), AC5 (effective hooks/permissions measured), AC7 (transport is not completion),
AC10 (deployed composition); `design-coord-enforcement-phase2` → ADR-0010 (edit-boundary
integrity guard and universal commit floor). The prior live leased writes are the red
runtime evidence. No full security sandbox is promised: ADR-0010 explicitly excludes
shell bypass and disabled native hooks.

## Model and boundary

Reuse the coordination bounded context, Session identity, Lease interval and Decision
value. The invariant is unchanged: a native file mutation must not cross another
session's active lease. Identity comes from `AGENT_SESSION`, never model payload identity.
No new aggregate or durable store. Existing claim/release facts retain one event per
session/time; decision facts retain one checked path per invocation. Counts are additive,
lease state is derived at check time, history stays append-only, and no migration occurs.
The existing `check`, `append_decision`, `tail` and `metrics` remain the writers/readers.
Opted-in native decisions add optional `hook_host` and actual resolved `hook_cwd` context
beside the existing environment-derived session. These are per-event observations, not a
second state store; older facts remain valid and existing readers ignore additive context.
The local decision fact itself supplies the private runtime receipt without a diagnostic
wrapper that would change the qualified hook definition.

Surface list: native input envelope → path normalization → existing lease check → native
denial response and existing decision facts → project hook entry → skill/Codex guide →
real worker edit/file-state evidence. Pack source and deployed script are synchronized.
The settings entries are explicit repo-owned opt-ins, not new defaults for every pack
consumer. No personal config or Codex trust database is written.

## Smallest correct implementation

Reuse-before-write wins the selection ladder: extend `coord-core.py hook` and its existing
parser/response adapter. No hook daemon, second ownership store, new library, ACP approval
proxy or shell-command parser. Pattern: Adapter into the existing deterministic policy.
The surrounding agent remains LOA Tool-Mediated Constructor; this seam is T0 validation.

1. `coord hook --host codex` selects Codex's supported response contract. Existing callers
   retain their behavior. Codex indeterminate input/state maps to `deny` with NOT CHECKED:
   the native host does not implement `ask`. This is an explicit adapter refinement of
   ADR-0010's fail-to-ask rule; emitting an unsupported ask would continue the tool.
2. Normalize native `apply_patch` from `tool_input.command`. Check every Add, Delete,
   Update and Move destination. Require a bounded, recognizable patch envelope and at
   least one file operation; malformed known writes never become pathless reads. Resolve
   relative paths against actual hook process cwd and then the linked checkout root;
   do not trust payload cwd to redirect the check. Existing Claude/Copilot paths remain
   supported. Reject traversal/absolute paths outside the assigned checkout.
   Normalize both edit paths and lease patterns/exceptions in the physical namespace.
   A future filename's case collision uses an actual directory-entry/samefile observation;
   distinct case-sensitive names are preserved. If an empty directory cannot answer,
   conservatively refuse only the ambiguous lease collision, not all new files.
3. `coord hook --config --host claude|codex` emits the small JSON snippet to merge into
   `.claude/settings.json` or `.codex/hooks.json`. It writes no file or trust state. The
   script command locates the deployed core from the current git root, resolves Python
   at runtime and quotes both paths. Guard matchers cover the supported native file tools.
   This repo installs those entries explicitly and preserves existing settings/hooks.
4. The launch reference tells the coordinator to review/install the entry before creating
   worker bases and bind the exact config/core bytes in qualification. Codex hook trust
   is a native prerequisite; new untrusted definitions remain blocked, not auto-approved.

Native command-string refinement of ADR-0010: these hosts consume `command`, not the old
exec-form `args` assumption. Use only a fixed wrapper with quoted runtime path expansions;
never interpolate hook payloads, concatenate model text, or call eval. A real generated
command test in a checkout whose name contains spaces, quotes, dollar and backtick syntax
must prove that no injected command executes. Unknown patch syntax rejects the whole
invocation before any partial path list can become an allow decision.

Qualification reads Codex `hooks/list` at the actual worker cwd and records the expected
synchronous PreToolUse source, matcher, currentHash, enabled and trustStatus, plus inventory
errors/warnings and effective hooks policy. Missing, modified, untrusted, disabled or
errored inventory blocks qualification. The adapter sets session-root project trust to
trusted internally; unchanged files do not imply unchanged effective project trust.
Exact hook-definition trust is separate. Any claimed native refusal must also show the
hook's actual process cwd and propagated `AGENT_SESSION` in a private diagnostic receipt.

Verified official Codex contract: [native hooks](https://learn.chatgpt.com/docs/hooks).
The installed CLI is 0.155.1, hooks stable/enabled; the ACP adapter is 1.12.0. Native
apply_patch uses `tool_input.command`; deny responses are supported. Non-managed hook
definitions require exact-hash trust and can be skipped until reviewed. Recorded native
envelopes or an explicitly blocked trust observation must accompany the implementation.
Claude's existing envelope and response are established in the Phase-2 conformance suite;
the actual SDK adapter must still show a refusal after this entry is installed.

## Failure modes and adversarial analysis (STRIDE-lite)

| Boundary / threat | Disposition and proof |
|---|---|
| Payload spoofs session or cwd (S/E) | Environment identity and actual process cwd win; forged fields do not clear a lease in subprocess tests. |
| Patch contains several files or a rename (T/E) | Check every source and move destination; one denied path denies the entire native invocation. Mixed-file/move tests. |
| Malformed/oversize known write or missing record/identity (T/D) | Bounded parse, explicit NOT CHECKED; Codex denies instead of unsupported ask. Negative tests include empty command and wrong types. |
| Relative path from a subdirectory, traversal or symlink alias (T/E) | Normalize to the actual linked root; test subdirectory and path aliases; paths outside root do not silently pass. |
| Hook trust absent, disabled hooks, native error/timeout (E/D) | Detect in actual profile qualification and refuse readiness. Host fail-open behavior remains a stated limitation, not something a payload adapter can repair. |
| Guard install overwrites user settings (T) | Generator only emits JSON. Repo installation preserves existing settings and hooks; no global files or trust records changed. |
| Patch content appears in durable facts (I) | Existing decision records receive path/verdict metadata, not patch bodies. Sentinel content must be absent from generated logs. |
| Check/use race and shell bypass (E) | Existing cooperative integrity boundary accepted by ADR-0010; no malicious-process or arbitrary-shell containment claim. Commit floor retained. |

## Privacy analysis (LINDDUN-lite)

| Data flow | Finding / disposition | Retention / rights |
|---|---|---|
| Hook input → decision facts | Existing session/path linkability; retain only existing bounded decision metadata, never raw patch content or credentials | Existing local ledger lifecycle; diagnostic raw hooks remain private and are exported only as allowlisted shapes/hashes |

No new personal-data category or egress. UI is existing plain JSON and native refusal text;
no new visual surface. Unknown inspection state is never rendered as enforcing. Telemetry
questions: did the guard run, what verdict, which session/path, how often, how long? Existing
decision facts supply the first four; bounded live observer supplies measured duration and
bytes. No invented token/spend values. No HTTP/RFC9457 surface.

## Verification and execution graph

Testing Strategy union: D0 hygiene; D1 logic boundaries; D2 malformed/security inputs;
D3 deployed structure; D4 real filesystem/git/subprocess composition; D5-provider native
hook contract; D6 payload schema; D7 native recorded-envelope fidelity; A1/A3/A4 tool
side-effect workflow checks; A6 config/skill regression.
Oracle: a leased canary changes only for its holder or after release; non-holder native
attempt is refused with a decision fact and unchanged file. Unit success cannot promote
an untrusted/skipped hook or a malformed edit into enforcement proof.

| Node | Inputs / real dependency | Exit | Tier |
|---|---|---|---|
| A Ground and spike contracts | Prior proof, installed versions | Supported native contract and trust prerequisites observed | T2 |
| B Independent design/plan gate | A decision | Security/Test Architect and Simplifier clear this bounded design | T2 |
| C Red conformance and config regressions | B decision | Original code fails the declared native cases | T2 |
| D Minimal parser/config implementation | C data | Targeted tests and mutants pass | T2 |
| E Independent code review + release gates | D data | No hard veto; source/install and complete bundle pass | T2 |
| F Serial actual-profile probes | E data | Allowed/denied native edits, or named trust prerequisite; no false readiness | T2 |
| G Evidence review and local integration | F data | Proof/audits/graph committed, local main advanced linearly | T1 |

Width one for model work. Independent read-only contract research overlaps parent grounding;
live profiles never overlap each other or reviewer execution. No speculative speed gain:
seven logical nodes, model-work span approximately work; mechanical batching saves calls.
Historical comparison: last repaired product passed 17 gates (Python122.53s), five native
attempts128.98s; not a promise for new trust/config behavior. Inferred budget60min/120calls.
Research/review passes ≤12calls/8min; no automatic model retry, one diagnosed control/profile.
Variant: remaining finite native-envelope and profile evidence cells. Failed prerequisites
become explicit blocked cells; a budget cap triggers re-estimation, not omitted proof.
Partial branches join only as named limitations. No unattended attestation until all its
required hooks/permissions/Owner-veto/cancel/handback capabilities are actually established.

## Review and confidence ledger

| Gate / claim | Evidence | Confidence / remaining proof |
|---|---|---|
| Independent design gate | `al-01M30J3RMQPHATZN93FJFM62SD` clears trust inventory and command-string conditions | Verified review; implementation is separate |
| Independent code gate | `al-01M30JP6RNV51Q1RVB9DN1BQ9T` clears three reproduced alias/state/Unicode defects | Verified review and real CLI regressions |
| Hook normalization and quoting | 46 focused tests, 21 subtests; three killed mutants | Verified locally; not native host admission |
| Codex configured entry | JSON emitted and merged, no trust database written | Verified file; native inventory currently empty, cause unresolved |
| Native enforcement | Fresh committed worker probes follow release gates | Not yet qualified |

Design DoD: existing spec/ADR trace, domain grain/history, surface contract, failure modes,
STRIDE/privacy, selection ladder, bounded graph and testing union are above. No new visual
UI or external SDK dependency. Independent author/reviewer separation is recorded. Runtime
evidence and release results will be linked in the implementation proof; they cannot be
inferred from this design.
