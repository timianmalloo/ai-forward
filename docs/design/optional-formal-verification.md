---
id: design-optional-formal-verification
title: "Optional formal verification and claim-scoped evidence"
type: design
status: draft
owner: "@lucioctinoco"
phase: "formal-verification-pilot"
tags: [formal-verification, verus, evidence, proof-pack]
links:
  - { to: spec-optional-formal-verification, rel: implements }
  - { to: plan-optional-formal-verification-implementation, rel: relates-to }
  - { to: architecture, rel: depends-on }
  - { to: api-bounded_process, rel: depends-on }
review-by: "2026-11-16"
summary: >-
  Proposed design for optional Verus checking of one small Rust example, with
  results recorded in the existing Proof Pack. Covers the example's contract,
  how each check is recorded, when a result can be trusted, failure handling
  and tests. Verus has not been run yet.
---

# Design: Optional Formal Verification

- **Status:** Draft for discussion. Not ready for implementation.
- **Specification:** [FV-01 to FV-18 and UX-01 to UX-04](../specs/optional-formal-verification.md).
- **Plan:** [implementation plan](../plans/optional-formal-verification-implementation.md).
- **Architecture:** [source, build, install and consumer pipeline](../architecture.md).
- **Author / date:** GitHub Copilot for @lucioctinoco, 2026-10-16.
- **Baseline:** `269f962e6dcd47d7464a73c24d7fdeec1ae3390b`.
- **Not done yet:** no code written, Verus not installed or run.

## Summary

A developer chooses to have one specific claim about their Rust code checked
by Verus. Here is how it works:

1. A reviewer confirms that the claim, written in English and as a formal
   contract, says the right thing.
2. A small local helper runs one tested version of Verus on the selected code.
3. The helper saves a record of exactly what was checked and what happened.
4. The result appears in the existing Proof Pack.
5. Before anyone relies on the result, the helper checks that the code, contract,
   tools and settings still match what was checked.

The first demonstration is a tiny function that checks whether a requested
range fits inside a buffer. It is not OpenVMM. We must see correct code pass
and deliberately broken code fail. A passing check never replaces existing
tests and never approves a whole feature.

**Scope status.** Tim merged the specification unchanged, but its own text says
implementation waits for his scope decision. This draft is for that review.
It keeps the specification's synthetic example rather than reopening the choice.
Installing tools and production work still need separate permission.

### Terms

- **Verus:** a tool that mathematically checks Rust code against a written contract.
- **Contract:** a precise statement of what a function must do.
- **Obligation:** one claim the verifier is asked to check.
- **Attempt:** one run of the verifier (or one decision not to run it), with its record.
- **Manifest:** the saved record of one attempt.
- **Trust declaration:** the list of things the check assumes but does not
  prove, such as the correctness of the Rust compiler.
- **Applicability:** whether an old result still applies to the current code:
  `current`, `stale` (something it checked has changed) or `unknown` (we cannot tell).
- **Qualification:** testing one exact Verus version in one approved
  environment before relying on it.
- **Digest:** a SHA-256 fingerprint of a file's exact contents.

## Responsibility

This component does one thing: it turns one chosen, reviewed claim into
evidence that the existing Proof Pack can use.

It does **not** add an orchestrator, model provider, proof service, database,
new reviewer panel or upload path.

**First slice:** one example function, one contract, one approved local
environment, saved attempt records, and a real acceptance check in the Proof
Pack. Tests may simulate the verifier's output, but a live Verus run must show
that the simulations match real behavior.

**Off by default.** When nobody opts in, the existing design and implementation
workflows do not look for, install or run Verus. They create no extra files and
add no reviewers. Verification guidance loads only after someone chooses it.
Declining leaves the normal workflow unchanged.

## Data shapes

**The attempt is the central record.** Each attempt gets its own ID, separate
from its outcome. Everything in one attempt (code, contract, obligations,
trust declaration, command and output) refers to the same snapshot of the
code. An attempt cannot declare itself accepted.

**Supporting values:** the obligation ID, the list of files checked, the tested
toolchain ID, file digests and the trust declaration. Requirements and
reviewers are referenced by ID, not copied.

**Storage.** Each attempt writes one final manifest plus a limited amount of
diagnostic output. These are plain files, not a database or a second ledger.
This includes attempts that stopped before running Verus. An interrupted
attempt leaves only private temporary files, which can never be accepted.
Saved records are never edited later, for example to change "passed" to "failed".

**Applicability is calculated when the result is used, never stored.** A saved
`accepted: true` flag could outlive the inputs it described, so there isn't one.

**Review approval is a separate input.** It is tied to the exact content of:
the English obligation, the requirement it comes from, the formal contract and
the trust declaration. Matching IDs are not enough, because the wording behind
an ID can change. Product acceptance remains the job of the existing checks.

**Other rules:**

- Durations can be added up only for runs that did not overlap.
- Outcomes and applicability are categories; they cannot be added up.
- A correction or retry creates a new attempt; it never overwrites an old one.
- There is no existing evidence format to migrate. A decision record (ADR) and
  compatibility tests are required before this format is accepted.

## The Example Function

**Proposed interface (not yet compiled or tested):**
`validate_range(buffer_len, offset, length) -> optional (start, end)`. It uses
the target platform's unsigned machine-sized integer. It checks a range against
a buffer length. It does not allocate or read memory, authorize access, or prove
anything about later I/O.

A range is **valid** when all three of these are true:

```text
aligned(offset) := offset mod 4 = 0
valid := aligned(offset) AND offset <= buffer_len
         AND length <= buffer_len - offset
```

These definitions are mathematical, so they cannot overflow. In the code, the
subtraction happens only after confirming `offset <= buffer_len`, so it cannot
underflow either.

- The offset must be a multiple of four. This is a rule of the example, not of Verus.
- The length can be any value.
- Empty ranges are allowed at any aligned offset up to the end of the buffer,
  including offset zero of an empty buffer.

**What the contract requires:**

1. The function returns a range **if and only if** the input is valid. The
   "if" half stops a function that rejects everything from passing.
2. A returned range is exactly `(offset, offset + length)`.
3. The range's end is at most `buffer_len`.
4. No arithmetic in the code overflows.

The contract covers every possible input; it does not exclude bad ones.

| Input `(buffer_len, offset, length)` | Required result | Why |
|---|---|---|
| `(16, 4, 12)` | Accept `(4, 16)` | Ends exactly at the buffer's end |
| `(16, 4, 13)` | Reject | One byte past the end |
| `(16, 3, 1)` | Reject | Offset not a multiple of four |
| `(16, 20, 0)` | Reject | Offset outside the buffer |
| `(0, 0, 0)` | Accept `(0, 0)` | Empty range in an empty buffer |
| `(16, 16, 0)` | Accept `(16, 16)` | Empty range at the end |
| `(MAX, 0, MAX)` | Accept `(0, MAX)` | Largest values, no overflow |
| `(MAX, MAX - 3, 4)` | Reject | End would overflow (on 32- and 64-bit targets) |

**Deliberate bugs for the demonstration:**

- Change only the code's comparison from `length <= buffer_len - offset` to
  `<`. The exact-end input `(16, 4, 12)` is then wrongly rejected, so the
  unchanged contract must fail.
- Separately, make the code accept an out-of-bounds range. The safety part of
  the contract must fail.

Never change the contract, trust declaration or selected obligations to make
the demonstration pass or fail.

Verus syntax, proof helpers and build commands are deliberately left out. The
qualification experiment must establish them for the exact version used.

## Contracts

### Operations (not yet a command-line interface)

The helper does three things:

1. **Run** a reviewed attempt.
2. **Assess** whether its evidence still applies.
3. **Report** the result.

These can live in one Python module in the pack. No service or plugin
interface is needed. Command names wait until after the experiment.

**Inputs to a run:** explicit opt-in, repository root, one reviewed obligation
and trust declaration, a single source file, the tested toolchain ID, an
approved fixed command, and finite resource limits.

**Rejected before running:** paths outside the repository, symbolic links and
other non-regular files, duplicate IDs, incomplete reviews and untested commands.

### The attempt manifest (proposed version 1)

| Fields | Written by | Used by / for |
|---|---|---|
| Format version, attempt ID, obligation and requirement IDs | The step that publishes the attempt | The loader checks format and identity; the Proof Pack keeps traceability |
| Digests of the English obligation and requirement, formal contract and reviewed trust declaration | The snapshot step | Acceptance confirms the exact reviewed wording, not just matching IDs or a model-written label |
| Repository-relative source paths and their digests | The snapshot step | Acceptance compares the checked files with the current ones |
| Toolchain ID: tool, library and solver versions, target, relevant settings | The tested recipe and snapshot step | Rejects incompatible results; detects a changed environment |
| Outcome, stable reason code, whether Verus actually ran | The outcome classifier | Decides eligibility; drives the recovery message |
| Actual command, exit result, which obligations were checked, evidence references | The run itself, as interpreted for the tested version | Confirms the intended work was done; allows reproduction |
| Start and end times, plus elapsed duration measured with a monotonic clock | The run step | Reports how long it took; never invented when Verus did not run |
| Diagnostic file paths, digests and sizes | The publish step | Confirms evidence is complete and unaltered before reporting |

If Verus never ran, run-only fields are empty and give a reason.
The manifest never contains home-directory paths, environment dumps,
credentials or raw prompts.

**Rejected when loading:** unknown format versions, missing required fields,
duplicate keys and unsafe paths. Unknown optional fields may be ignored only if
they cannot affect scope, trust or acceptance.

### What this design depends on

| Dependency | What we know and how | Limits |
|---|---|---|
| Proof Pack | `pack/templates/proof-pack.template.md`, read [Verified] | Already records claim, oracle, confidence and residual risk. Gets optional verification fields, not a second ledger. |
| Design and implement workflows | Existing skill and stage files, read [Verified] | Review happens before running. Normal tests and reviews still apply. |
| `run_bounded` | `pack/scripts/bounded_process.py`, read [Verified] | Enforces time and output limits, cancellation and cleanup. **It is not a sandbox.** |
| Process containment | Same helper's per-platform code, read [Verified] | On Linux/macOS, memory limits apply per process, not in total. On Windows, job limits can fail to apply. |
| Verus contracts and trust | [Contracts guide](https://verus-lang.github.io/verus/guide/requires_ensures.html) and [overview](https://verus-lang.github.io/verus/guide/), read [Verified] | Assumptions, unsafe code, Verus's supported Rust subset and the unchecked compiler and verifier remain trusted. |
| Verus output, checked scope, link to compiled code | Not yet tested [Flagged] | No output format, version or supported OS is promised yet. |

Use `run_bounded` with limits chosen for this workload, not its ten-second
default. Clean shutdown does not mean the proof passed. If the environment
cannot enforce a required limit, report `unsupported` or `unavailable`
instead of quietly running with weaker limits.

## How Evidence Is Accepted

### Pinning down exactly what was checked

Version 1 supports a single self-contained source file and a fixed, reviewed
library baseline. Cargo workspaces, build scripts, external macros and unknown
dependencies are unsupported until we can record everything they pull in.
Code in other languages is never silently rewritten in Rust.

Steps:

1. Create a private temporary directory unique to the attempt.
2. Read the source file once, take its digest, and run Verus on that copy.
3. Confirm, using the tested version's output, that this exact copy and these
   obligations were checked, and that no option turned checking off.
4. Record the full set of library, toolchain, solver, setting and target
   versions under the toolchain ID. If any is unknown, there is no current evidence.

The copy and environment must not change during the run. Comparing digests
before and after is not enough, because a file could change and change back
mid-run. If the approved environment cannot guarantee this, stop qualification
and say so. Unpinned dependencies from the surrounding system are rejected.

### The acceptance check

Evidence counts only when **all** of these are true:

```text
historical outcome is passed
AND the manifest and required diagnostics are complete and their digests match
AND the intended obligations were checked, as confirmed by the tested version's output
AND the reviewed obligation, requirement, contract and trust declaration match the recorded digests
AND the current inputs and environment match the checked ones
AND the existing required tests, reviews and permissions are satisfied
```

This check is what decides acceptance. Reading or displaying a manifest does not.

- An assessment applies only to the exact code tree it checked. If anything
  relevant changes afterwards, it must be re-run.
- A timestamp or branch name does not identify inputs.
- A hand-edited "passed" record is not verifier evidence. Anyone with write
  access to the repository is trusted, so reviewers rely on reproducible runs.
  Version 1 does not claim cryptographic attestation.

**Applicability rules:**

- A known change to a checked input makes the result `stale`.
- Missing information, missing or corrupt evidence, or any other inability
  to compare makes it `unknown`.
- Only a complete, exact match is `current`.
- Any outcome other than `passed` is never eligible, whatever its applicability.
- The original outcome always stays visible.

## Patterns

- **One adapter for Verus:** a single version-specific boundary separates raw
  process output from acceptance decisions. No registry for multiple verifiers.
- **Write-once records:** one final record per attempt. No event-sourcing framework.
- **Calculated applicability:** worked out from current inputs, never stored as a flag.

**Smallest solution that works:** the feature only runs after opt-in. It
reuses the Proof Pack, existing roles and `run_bounded`, and uses Python's
standard library for hashing, JSON and files. No new dependency or database is
justified. Existing private atomic-write helpers show precedent but are not
assumed to be reusable public APIs. The experiment picks the simplest
write-without-overwrite method it can actually demonstrate.

## Error & concurrency model

| Outcome | Meaning |
|---|---|
| `passed` | The tested Verus version's output confirms the intended obligations and safety checks succeeded. A zero exit code alone is not enough. |
| `failed` | Verus output shows a declared obligation or safety condition was not met. |
| `inconclusive` | No conclusion was possible: timeout, crash, output too large, malformed or unknown output, or failed containment or cleanup. |
| `unavailable` | The approved tool or permission to run it is missing. |
| `unsupported` | The target, dependencies, version or required limits cannot be supported. |
| `cancelled` | Someone cancelled the run. Later success output cannot override this. |
| `not-run` | The attempt was planned or withdrawn and Verus never ran. |

- Cancellation, timeout, resource-limit and cleanup failures take priority
  over output that looks like a pass.
- No automatic retries and no automatic proof repair. A retry is a new, explicit attempt.
- If the meaning or the trust declaration changes, the claim goes back for
  review. Withdrawing a claim is recorded, but it is not a proof.
- Attempts that never ran Verus have no invented output or duration.

**Concurrency:**

- Only one attempt at a time may write to an evidence folder; others are refused.
- Separate worktrees that share an evidence folder must agree on its identity.
- If a previous owner seems to have died, report it for manual recovery.
  Never take over silently.
- A finished record is published once from private temporary files and never
  overwrites an existing attempt, even in a race.
- An interrupted or unverifiable publish leaves no acceptable evidence.

## Failure-mode analysis

| What goes wrong | Caused by which choice | Response | How it is handled | Reason code | Test |
|---|---|---|---|---|---|
| Empty or malformed obligation, or bad path | Explicit file inputs | Prevent | Validate before running; Verus does not start | `FV_INPUT_INVALID` | Empty, duplicate, path-escape, symbolic link and non-regular file cases |
| Tool missing or permission denied | Local approved execution | Detect | Do not run; report `unavailable` with setup steps | `FV_UNAVAILABLE` | Missing program and denied-launch cases |
| Unsupported version, feature or dependency | Version-specific adapter | Prevent | Report `unsupported`; never substitute a hand-written model | `FV_UNSUPPORTED` | Untested version, dependency and settings |
| Zero or wrong obligations checked, or unrecognized output | Version-specific output reading | Detect | Report `inconclusive`, never `passed` | `FV_SCOPE_UNCONFIRMED` | Empty success, filtered run and wrong-function results |
| Counterexample or unmet guarantee | Formal checking | Detect | Report `failed`; keep the diagnostic and the unchanged contract | `FV_OBLIGATION_FAILED` | Live bug run plus a recorded copy of its output |
| Timeout, crash, output flood or cancellation | Running a subprocess | Mitigate | Clean up within limits; never a pass; keep limited output | `FV_EXECUTION_INCOMPLETE` | Real timeout, flood and cancel runs plus classification |
| Inputs changed or not fully known | Snapshot and acceptance | Prevent | Run on a fixed copy; mark `stale` or `unknown` before acceptance | `FV_INPUTS_CHANGED` / `FV_IDENTITY_UNKNOWN` | Change source, settings and toolchain, including mid-run change-and-revert |
| Partial write or missing diagnostic | File-based evidence | Prevent | No acceptable record; history preserved | `FV_EVIDENCE_INCOMPLETE` | Interrupt at each publish step; delete output |
| Two writers or duplicate attempt | Unique attempt publishing | Prevent | Refuse overlap; never replace or mix records | `FV_ATTEMPT_BUSY` | Two real writers, ID collision and abandoned-ownership cases |
| English meaning changed, contract weakened or new assumption added | Human review of meaning | Prevent | Require a new review tied to the new content, even if IDs did not change | `FV_REVIEW_REQUIRED` | English-only change, stronger precondition, weaker guarantee, added assumption |
| Evidence changed after assessment | Separate acceptance step | Prevent | Tie assessment to the exact code tree; recheck when used | `FV_INPUTS_CHANGED` | Change the candidate between assessment and acceptance |

## Adversarial analysis (STRIDE-lite)

These controls are requirements for future code. None exist yet.

| Trust boundary | STRIDE threat | Disposition | Control / rationale | Negative test |
|---|---|---|---|---|
| Source/config -> process argv | E/T: text in the source or settings injects commands or turns checking off | mitigate | Fixed, tested command list with no shell; reject options that change scope; source is treated as data | Shell-like text and disable/filter options never change the command |
| Filesystem -> snapshot/evidence | T/I: path tricks or swapped links read or overwrite unrelated files | mitigate | Stay inside the repository; accept regular files only; private directories; fixed snapshot identity; write without overwrite | Path-escape, link, non-regular file, swap and collision attempts |
| Process -> acceptance | S/T: fake success, wrong tool or unreviewed assumptions | mitigate | Tie results to tested tool versions and checked scope; require a matching contract and trust review | Forged or malformed output, changed binary, added-assumption cases |
| Attempt record -> reviewer | R: a result cannot be traced | mitigate | Permanent attempt ID, input digests, the actual command and limited diagnostics | Missing ID or output cannot satisfy acceptance |
| Tool execution -> environment | D/E: resource abuse or malicious build code | mitigate | Separately approved isolation (the bounded helper is not a sandbox); no build scripts or macros in version 1 | Output flood, process cleanup and denied-containment cases |
| Local writer -> manifest | T: someone with legitimate file access forges evidence | accept | Version 1 has no cryptographic attestation. Relies on a reviewed source and tool baseline plus reproducible live runs. Digests catch inconsistency, not deliberate forgery by the same user. **Proposed for acceptance, not yet accepted.** | Tamper-detection tests, with no claim that they stop a malicious local owner |

## Privacy analysis (LINDDUN-lite)

The example uses no personal data. In real repositories, verifier output can
still contain paths, source code or names, so the general feature is not
claimed to be free of personal data.

| Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|
| Verifier diagnostics -> local evidence | I/D: paths or source text may identify people or reveal secrets | mitigate | Keep raw diagnostics private and size-limited by default; publish only after explicit opt-in to publication and existing scrubbing or manual review; keep a digest link to approved evidence | Follows the adopting repository's local retention. Deleting private diagnostics makes the evidence `unknown`, never silently complete. |
| Manifest -> committed Proof Pack | L/I: attempt and reviewer IDs link work to people | mitigate | Use requirement and obligation IDs and repository-relative paths only; no environment dumps, home paths or new reviewer contact fields | Follows the repository's existing Git retention and access policy |

## UI & interaction design

**Where it appears:** the existing conversation and Markdown output. No new
visual interface, design tokens, `DESIGN.md` or images. Status never depends on
color. Command names wait for the experiment.

Example report (illustrative; not a real result):

```text
Outcome: passed | Obligation: descriptor-range-v1 | Applicability: stale
Not eligible for current acceptance: source identity changed.
Historical scope: synthetic descriptor validator, <recorded target/toolchain>.
Contract and trust: <review references and identities>.
Evidence: <repository-relative reviewed evidence reference>.
Not established: memory authorization, downstream I/O, whole-feature correctness.
Next action: re-run the unchanged reviewed obligation for the current inputs.
```

**States:**

- **Off or declined:** the normal workflow continues.
- **First use:** explains what setup is missing.
- **Running:** shows that a time-limited attempt is in progress.
- **Nothing selected:** a clear input error.
- **Finished:** every outcome gives a reason and a next action.
- **Stale or unknown:** shown next to the original outcome.

Long diagnostics are cut off with a visible notice. If cutting them off makes
the result unreadable, the outcome is `inconclusive`. No animations,
hover-only information, custom keyboard controls or new dashboard. Review of
the contract and trust declaration happens before running and before
acceptance, and any change in meaning sends it back.

## Telemetry

- One local `formal_verification.attempt` span per request. Its ID follows the
  attempt through snapshot, run, publish and acceptance.
- Events: requested, rejected before running, launched, completed, publish
  incomplete, acceptance assessed. Reason codes are listed in the failure table.
- Counters come from final outcomes. Duration is recorded only when Verus actually ran.
- Output size and number of checked obligations show volume. This helper does
  not use a language model, so no token or cost data is recorded.
- Uses the repository's existing logging conventions and Python's standard
  library. No tracing backend or new SDK is needed.
- There is no HTTP interface, so the RFC 9457 error format does not apply.
- Tests confirm the attempt ID, reason and duration are present or absent as
  expected, output is limited, and no planted secret or home path appears in the
  public report.

## Test plan

The repository's Testing Strategy assigns test types by trigger. These apply:

| Directive | Why it applies here |
|---|---|
| D0 | Always required |
| T1/D1 | Range-checking and eligibility logic |
| T2/D2 | Input validation, parsing and identity |
| T4/D4 | Real process and filesystem behavior |
| T7/D6 | Versioned manifest and recorded output samples |
| T8/D7 | Simulated verifier processes |
| T12/A4 | The opted-in workflow from start to finish |
| T13/A5 | Quality of suggested contracts |
| T14/A6 | Changed skill guidance |

If a new public tool contract or cross-layer interface is added, T6/D5-provider
or T3/D3 must be added before implementation. T5 and T9–T11 do not apply: there
is no remote API, new model adapter, MCP server or acceptance of model-written JSON.

| Test group | What must be tried, and what must happen | Requirements |
|---|---|---|
| Example logic and mutations | Exact end, empty, misaligned, maximum and overflow inputs; reject-everything and accept-too-much versions; the `<` mutation and a deleted check must fail | FV-04/05/16 |
| Live Verus run | Real correct code passes; buggy code fails against the identical contract and trust declaration; checked scope confirmed from output, not a total count | FV-07/08/16 |
| Output reading and recorded samples | Zero or wrong obligations, unknown version, malformed or truncated output; every recorded sample matched by live output from the same version | FV-07/09/17; D6/D7 |
| Real files and processes | Interrupted publish, overlapping attempts, ID collisions, history unchanged, cancellation, containment errors, output floods and cleanup | FV-09/10/14/17 |
| Acceptance check | Each changed input becomes `stale`; missing or corrupt becomes `unknown`; changed English, precondition or assumption needs re-review even with the same IDs; old outcomes stay; a late change cannot reuse an assessment | FV-04/05/06/10/11/12 |
| Workflow and content checks | Off paths make zero Verus checks, for Rust and other languages; declining changes nothing; Claude and Copilot behave the same; empty or meaningless contracts are rejected in review | FV-01/02/03/13/15/18; UX-01/04 |
| The real report | Every outcome and applicability shows scope, reason and next action; no broad correctness claims, leaked secrets or invented measurements | FV-10/12; UX-02/03 |

- All deterministic tests run without Verus. The live test is reported as
  blocked when Verus is missing; it never counts as a silent pass.
- Each new check is seen failing before the code makes it pass.
- Small exhaustive and property tests supplement the full proof; they do not
  replace it.
- Use the test tools already installed. Any new property-testing library goes
  through the existing dependency process.

## Files Likely to Change

| Area | Proposed files |
|---|---|
| Example and reviewed obligation | `pack/examples/formal-verification/README.md` and `descriptor.rs`, plus a reproducible code-only mutation under the same contract |
| Run, record and acceptance logic | `pack/scripts/formal-verification.py`, only if the experiment shows it is needed; uses the existing `bounded_process` |
| Tests and recorded samples | Following existing Python test and eval conventions, placed next to the closest existing example |
| Workflow guidance | Existing `pack/commands/design-slice/` and `pack/commands/implement/` stage files, loading verification guidance only on demand; no new required stage when off |
| Proof Pack and report | Optional fields in `pack/templates/proof-pack.template.md`, the report renderer and the acceptance check |
| Packaging | `pack/adapters/INSTALL.md`, the on-demand reference and the sync map; every generated host copy, keeping Claude and Copilot equivalent |

No application database or client schema is added. The manifest loader,
acceptance check and Markdown report are the only new data, logic and display
layers. The manifest table above traces who writes and who reads each field.
Later pack changes use `/extendaibundle` for wiring, revision notes and sync
and bundle checks. Never hand-edit generated pack copies.

## Before the Live Experiment

Fill in and review these before any live run:

- operating system and CPU architecture;
- Verus release and download digest;
- Rust, library and solver versions;
- target and settings;
- the approved isolation method;
- time, memory, process and output limits;
- the selected obligation, and who reviews the contract and trust declaration;
- how the snapshot is kept unchanged.

None of these has been decided yet.

**What the experiment must show:** the real code is checked directly; exactly
which obligations were checked; which assumptions are trusted; the correct
version passes and the buggy one fails; the output format; that limits are
actually enforced; that no outside dependency changes the result; and that
the run can be reproduced. Publish only reviewed, size-limited evidence.

If the chosen Verus version cannot show what was checked and what was
trusted, report the gap and revise the design. Do not build a general-purpose
parser to paper over it.

## Conformance notes

The pack stays a source, build and install pipeline. It does not become a Rust
application or a model-routing runtime, and no new runtime archetype is added.
The record format, helper location, alignment rule and resource policy are
proposals [Inferred], not approved decisions or observed behavior.

## Flagged risks & residual unknowns

- **Known from reading [Verified]:** the repository code and the Verus
  documentation cited above. These are observations of source and
  documentation, not of behavior.
- **Not yet known [Flagged]:** whether Verus checks the right code correctly,
  how to read its output, whether checked code matches compiled code, the
  full set of toolchain inputs, isolation, file-publishing behavior and
  Windows support.
- Digests show that files did not change. They do not show that a contract
  says the right thing.
- Human review of the claim and trust declaration, and the existing tests,
  remain essential.

## Gate record

An independent Astra (`gpt-6-astra`) review returned REVISE with one major
finding: matching obligation IDs did not prove the reviewed English meaning was
unchanged. The fix ties review approval to the content of the English
obligation and its requirement, in the manifest, the acceptance check and the
tests. A separate Astra recheck confirmed the finding resolved. Other design
gates remain open. No veto was cleared by the author, and no live proof is claimed.

**Design checklist.**

- **Drafted:** responsibility, data model, field readers, phasing, failure,
  threat and privacy analyses, text states, telemetry and test plan.
- **Still needed:**
  - the live experiment;
  - a final decision record (ADR) for the record format;
  - observed behavior of publishing and acceptance;
  - independent clearance of any applicable veto reviews.
- **Not applicable:** visual design artifacts, because the existing Markdown
  output is reused.

This draft must not be handed to `/implement` as an accepted design.

## Status & next action

| Item | State |
|---|---|
| Completed | Proposed design and example contract; experiment worksheet; acceptance and test plan; independent review, with its one finding fixed and rechecked |
| Remaining | Tim's scope decision; live experiment; final design, ADR and applicable gates |
| Best next action | Open a draft PR so Tim can review the scope and this design |
