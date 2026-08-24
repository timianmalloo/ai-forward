---
id: design-coord-federation-phase3
title: "Design — coord Phase 3 (collision-proof allocator · artifact-class registry & derived merge driver · harness adapters)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, allocator, kg-b, merge-driver, gitattributes, copilot, harness-adapter, spikes]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: adr-0008-non-coordinating-allocation, rel: implements }
  - { to: adr-0009-artifact-class-and-derived-merge, rel: implements }
  - { to: design-coord-enforcement-phase2, rel: refines }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-02-23"
summary: >-
  Phase 3 closes the two structural failure modes — allocation collision and derived-artifact
  conflict — and turns the harness adapter from an assumption into a contract. Six spikes ran;
  one closed the F1 condition open since the architecture (Copilot CLI does invoke PreToolUse,
  in the Claude plugin format, and fails OPEN on a 30 s timeout), and one corrected ADR-0009's
  own framing of what an unregistered merge driver costs.
---

# Design: coord Phase 3 — allocator, derived merge, harness adapters

- **Status:** Accepted
- **Spec / architecture:** `docs/specs/agent-coordination.md` (US-3, US-5, US-8, `NFR-C1`, `NFR-C2`) · `docs/architecture-agent-coordination.md` §6 Phase 3 · ADR-0008, ADR-0009
- **Delivery phase / vertical slice:** **Phase 3** — the two structural fixes (M2, M1) plus the remaining harness spikes.
- **Author(s) / date:** Patterns Expert + The Simplifier + Python Developer + Domain Researcher + Data & Persistence Architect (peers), 2026-08-23
- **Refines:** `design-coord-enforcement-phase2`

> **Grounding trace (V15):** `design-coord-federation-phase3` → `implements` → `adr-0008-non-coordinating-allocation` + `adr-0009-artifact-class-and-derived-merge` → `refines` → `design-coord-enforcement-phase2` (the two-store split, the advisory default, the exec-form hook) → `implements` → `architecture-agent-coordination` §6 Phase 3 and its condition 2 (F1 stays open until each harness surface is *executed*).

## Drift surfaced before anything else

`docs/design/coord-enforcement-phase2.md` line 251 records, verbatim: *"**`worktree-status` deferred to Phase 4** with the rest of the operator surface — that one was creep and is dropped."* Commit `fbcd019` ("worktree-per-session discipline, rev 43") nevertheless landed a **~390-line worktree subsystem** in `coord-core.py` — `worktree_inventory`, `worktree_is_clean`, `worktree_safety`, `cmd_worktree`.

It is **tested and green** (254 pass) and it is not harmful. But it has **no design doc, no ADR, and no entry in the architecture's phasing plan**, and it contradicts a recorded gate decision. Per the standing rule this is surfaced rather than absorbed:

- **Not blocking Phase 3** — it does not touch the allocator, the registry, or the adapters.
- **Two honest options**, for the owner to pick: retro-document it as a Phase-4 slice pulled forward (an ADR plus a design section), or record a deviation against the Phase-2 gate. Doing neither leaves a load-bearing subsystem whose only specification is its tests.
- **This design does not depend on it** and does not extend it.

## Responsibility

**One:** make the two structural failure modes **impossible to express**, and turn "which harnesses can enforce" from a belief into a tested contract.

Not in scope: the decision register and the projection (Phase 4, gated behind ADR-0011's STRIDE work), the operator surface, record rotation.

## What the spikes established

| # | Question | Executed | Result |
|---|---|---|---|
| **S11** | Does a `.gitattributes` merge driver run under **rebase**, not just merge? | driver + two branches, both operations | **Yes, both.** Two invocations logged. This matters more than the merge case — protected `main` forces rebase, and rebase is where the measured conflicts actually happen. |
| **S11b** | What do the driver placeholders actually carry? | logged `%A %O %B %L %P` | `%A` is a **temp file**, not the real path; `%P` is the real pathname. A regenerator must write to `%A` while knowing its identity from `%P`. |
| **S12a** | What happens in a **fresh clone**, where `.gitattributes` declares the driver but `.git/config` does not define it? | unregistered driver, real merge | **It degrades to an ordinary 3-way merge with conflict markers.** *This corrects ADR-0009's framing:* the ADR called it "silently gets default behaviour" and treated it as a hazard. It is default behaviour, and default behaviour is a **visible conflict** — the cost is a lost benefit, not lost work. |
| **S12b** | What if the driver **fails** (exit ≠ 0)? | driver exiting 1 | **The dangerous one.** The file is left **unmerged but with OURS content and no conflict markers**. It looks clean. A `git add .` commits ours and silently discards theirs. The driver must therefore never exit non-zero. |
| **S13** | How is registration read back? | `git check-attr` vs `git config` | `git check-attr merge -- <path>` → `merge: regen`; `git config merge.regen.driver` → empty, exit 1. **Only reading both finds the gap** — `check-attr` reports the declaration whether or not a driver exists. |
| **S14** | **F1: does Copilot CLI have a pre-edit hook surface?** | binary, config, plugin, logs | **Yes — closed, with a qualification.** See below. |

### S14 — the F1 condition, closed for Copilot

Open since the architecture: *"F1 stays open for Copilot and any third harness until each hook surface is executed, not read."* Copilot CLI **1.0.80** is installed on this machine, so it was executed.

**Verified:**
- Copilot **invokes `PreToolUse`**. `~/.copilot/session-state/*/events.jsonl` holds **11,419 `hook.start`/`hook.end` pairs**; an installed plugin registers `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `SessionStart`, `SessionEnd`, `Stop`, `StopFailure`, `Notification`.
- It consumes the **Claude plugin format**: `.claude-plugin/plugin.json` + `hooks/hooks.json`, the identical `{"matcher": …, "hooks": [{"type": "command", "command": …}]}` shape, and the `${CLAUDE_PLUGIN_ROOT}` placeholder. **One plugin can therefore serve both harnesses** — `NFR-C1` gets much cheaper than the architecture assumed.
- The default hook timeout is **30 seconds**, and **on timeout Copilot ALLOWS**. Logged verbatim: `preToolUse hook from "wt-agent-hooks@wt-local" timed out; allowing the tool call to proceed: HookTimeoutError: Hook command timed out after 30 seconds`.

**NOT verified, and not claimed:** whether Copilot honours a `hookSpecificOutput.permissionDecision: deny` response. The only plugin installed here is observational — it forwards events to a terminal and has never denied anything — so no deny has ever been exercised on this machine. **This is the residual, and §Conformance harness is how it gets closed rather than assumed.**

**The consequence that changes the design:** Copilot's failure mode is the **opposite of ours**. `NFR-R2` says fail safe, never open; Copilot's harness says *if the hook does not answer in 30 s, allow*. Our measured check is **63 ms p95** — 475× headroom, so a timeout means the hook is hung, not slow. That is detectable (a `hook.start` with no `hook.end`) and it is a **named residual**, not a solved problem.

## Data model — settled first

Two new aggregates, one new dimension. Nothing existing is rewritten.

**Aggregate: Allocation scheme.** Root `SchemeId` (`al`, `cl`, `FR`, …). **The one invariant: an issued identifier is never issued twice, and issuance requires no communication between issuers.** The second half is the whole point — a scheme that is only safe when issuers can see each other is the defect, not the fix.

**Aggregate: Artifact-class registry.** Root the registry file. **The one invariant: every path pattern resolves to exactly one class.** Overlapping patterns are a registry error, not a precedence puzzle — first-match-wins would make the class of a path depend on file ordering.

| Store | Grain | Additivity | History rule | Writer | Compute reader |
|---|---|---|---|---|---|
| `.agents/artifacts.yml` *(new dimension)* | *one row is exactly one path pattern* | n/a (categorical) | **Type-1 by decision** — the current classification is what governs a merge happening now; the *history* of how a path was classified is in git, which is the right store for it. Recorded as a deliberate choice to not model it twice. | a human, in a PR | `classify()`, the merge driver |
| existing registers (`audit-log.jsonl`, …) | unchanged | unchanged | unchanged | unchanged | unchanged |

**No new fact store.** The allocator is a **pure function**, not a ledger: it issues from a clock plus randomness and records nothing. A ledger of issued ids would reintroduce exactly the coordination the scheme exists to avoid — and would be a second definition of "which ids exist", when the registers themselves already are that.

**Derive, don't store.** Class is derived from the registry at read time, never stamped onto an artifact. Whether a driver is *effective* is derived from `check-attr` ∧ `config`, never cached.

**Migration — expand-migrate-contract, and a backfill that never guesses.** `audit-log.py:next_id()` currently does `max(existing) + 1` over the **local file only** — literally the `KG-B` shape, zero-padded to four digits.

1. **Expand.** `next_id` gains an optional injected id; readers accept both formats. Nothing else changes. Reversible by deletion.
2. **Migrate.** New entries take a collision-proof id. **Every existing `al-NNNN` keeps its value** (`NFR-C2`). There is **no backfill at all** — nothing is guessed, because nothing is rewritten.
3. **Contract.** Removing `next_id` is a later decision, explicitly **not** in Phase 3.

**The consumer ADR-0008 did not name.** `/auditlog get --id al-0064` and human recall ("show me al-0064") depend on the sequence being sayable. A 26-character identifier breaks that, and the ADR accepted the cost without naming this consumer. Phase 3 restores usability **without a second identity**: recall accepts a **unique prefix**, the git short-hash idiom. `al-01M0GA` resolves if exactly one id starts with it, and reports the ambiguity if more than one do. One identity, short handle — not two ids.

## Change surfaces (E7)

store (`artifacts.yml`, `.gitattributes`) → model (`ArtifactClass`, `Allocation`) → service (`classify`, `allocate`, `resolve_prefix`, `driver_status`) → **projection/wire** (`coord class --json`, the driver's stdout, the allocator's returned string) → client (`audit-log.py`'s injected id; the git driver invocation; the harness plugin manifest) → UI (`coord doctor` output, the refusal's class line) → **compute reader** (`overlaps()` consults class; `check()` skips leases on `derived`).

## Contracts

**Exposed:**

```
coord allocate --scheme al                 # one collision-proof id on stdout
coord resolve  --scheme al <prefix>        # 0 unique · 3 ambiguous (lists) · 4 no match
coord class    <path> [--json]             # authored | derived | register | hotspot
coord merge-derived %A %O %B %P            # the driver. ALWAYS exits 0. Resolves; never regenerates.
coord regen                                # run the regenerations the driver deferred
coord doctor                               # is the driver effective? is the registry sane? what is owed?
coord plugin --emit <dir>                  # write the .claude-plugin bundle both harnesses read
```

**Consumed — each established by execution above:** the merge-driver placeholder set (S11b), `git check-attr` (S13), `git config merge.<name>.driver` (S13), `audit-log.py:next_id` (read), the Claude/Copilot plugin manifest shape (S14).

**`coord merge-derived` always exits 0.** S12b is the reason: a non-zero exit leaves the file **unmerged, with ours content, and no conflict markers** — a state that looks clean and silently discards the other side on `git add .`. Whenever the driver cannot resolve safely it **writes conventional conflict markers itself** and exits 0, so the failure is visible in the file rather than hidden in the index.

> **AMENDED DURING IMPLEMENTATION (2026-08-23) — the driver resolves, it does not regenerate.**
> This section originally had the driver *regenerating* the artifact during the merge. That
> cannot be correct: git runs merge drivers **per file, in arbitrary order**, so a derived
> artifact's own sources may still be unmerged when its driver runs — regenerating then
> produces output from a half-merged tree. It would also force the generator to write the
> working tree mid-merge, the exact hazard `Q8`/`B8` guards against.
>
> The corrected contract matches the proven prior art (`sync-generated.ps1`: rebase, *then*
> regenerate): **the driver resolves the derived artifact to ours and records that a
> regeneration is owed; `coord regen` regenerates afterwards, when the tree is whole.** A
> failed regeneration **stays owed and reports non-zero**, because a stale derived artifact
> looks finished, which is worse than a conflict. See `docs/notes/note-20260823-merge-driver-resolves-not-regenerates.md`.
>
> Two consequences: the registry needs a **regenerate command per `derived` pattern** (the
> design had nowhere to put one), and the exposed surface gains `coord regen`.

## Solution-Selection Ladder (L1)

| Rung | Answer |
|---|---|
| 1 YAGNI | All three earn their place: M2 has nine recorded occurrences, M1 is the dominant conflict source, and F1 is an architecture condition. |
| 2 Reuse | **`check()` and the two-store split are reused unchanged.** The allocator reuses the S1b implementation already proven. The registry reuses `overlaps()`. `audit-log.py` is **extended, not replaced**. |
| 3 stdlib | `json`, `os`, `time`, `fnmatch`, plus a **~30-line line-oriented parser** for `artifacts.yml`. |
| 4 native | `.gitattributes` + merge driver — git doing the work rather than a script racing it. |
| 5 dep | **PyYAML deliberately not taken.** The registry is `pattern: class` lines; a parser for that is thirty lines and the pack ships zero dependencies (`NFR-P2`). The Gratuitous-Dependency gate holds. |
| 6–7 | ~260 added lines. |

**`simplify:` markers:**
- `simplify:` the registry parser accepts `pattern: class` and `#` comments only — not general YAML. **Ceiling:** anchors, nesting, multi-line values. **Upgrade trigger:** the first registry a human writes that the parser rejects.
- `simplify:` `resolve --prefix` scans the register linearly. **Ceiling:** ~100k entries. **Upgrade trigger:** resolution above 500 ms.
- `simplify:` the class of a path is the **longest matching pattern**, and overlapping patterns of *different* classes are a registry error rather than a precedence rule. **Ceiling:** a registry that genuinely needs precedence. **Upgrade trigger:** the first legitimate overlap someone cannot express.

## Patterns

- **Strategy, keyed by artifact class** — the Phase-2 design deferred this as speculative generality; the registry is what makes it real. Now justified, not anticipated.
- **Adapter** — one plugin bundle, two harnesses (S14).
- **Null Object** — an unclassified path yields `authored`, the safe direction, with no branch at the call site.
- **Pure function (allocator)** — no state, therefore no coordination, therefore no collision.
- **Rejected:** a Registry *service* (the file is the registry); a Factory for allocators (one scheme shape); caching `classify()` (the registry is tens of lines — a cache would be a second source for a cheap derivation).

## Failure-mode analysis

| # | Mode | Disposition |
|---|---|---|
| H1 | Two sessions allocate in the same millisecond with no network | **PREVENT.** Non-coordinating scheme, proven at 4,000 ids / 8 processes / one millisecond / 0 collisions (S1b). |
| H2 | A merge of a register loses an entry to a "dedupe by id" resolution | **PREVENT.** Unique ids stop the collision; a **conservation assertion** stops the resolution — a merge whose entry count falls below the sum of the distinct entries fails closed. Unique ids alone would not have caught the recorded instance. |
| H3 | `.gitattributes` declares the driver, `.git/config` does not define it (fresh clone / new worktree) | **DETECT.** `coord doctor` reads **both** (S13) and reports. Degradation is a visible conflict (S12a), so this costs benefit, not work — corrected from ADR-0009. |
| H4 | **The driver fails and leaves a clean-looking unmerged file** | **PREVENT.** The driver never exits non-zero; on internal failure it writes conflict markers itself. Test asserts markers are present and the exit is 0 (S12b). |
| H5 | A regenerator is slow or hangs inside a merge | **MITIGATE.** Bounded wall-clock; on expiry, conflict markers and exit 0. Never an indefinite hang inside `git rebase`. |
| H6 | An **authored** file misclassified as `derived` — a merge overwrites real work | **PREVENT + DETECT.** Default is `authored`; the driver refuses any path whose `check-attr` and registry class disagree; the registry is PR-reviewed. **This is the highest-severity mode in the phase** and gets three controls. |
| H7 | Overlapping registry patterns of different classes | **PREVENT.** A registry error at load, not a precedence rule. `coord doctor` fails. |
| H8 | The registry is missing or unparseable | **DEGRADE, advisory.** Everything is `authored`, and the layer **says** it is unclassified — the Phase-2 advisory precedent (US-8). |
| H9 | A prefix resolves to more than one id | **PREVENT.** Exit 3, listing the candidates. Never "the first match". |
| H10 | A prefix resolves to nothing | **DETECT.** Exit 4 with the corpus size — R4 again: a scan of zero entries is not "not found". |
| H11 | `audit-log.py` is re-synced by the pack and loses the injected-id seam | **DETECT.** A parity test asserts the seam exists in both `pack/scripts/` and the synced copy. `PACK-D` is the recorded class for exactly this. |
| H12 | **A Copilot hook times out and the edit is allowed** | **ACCEPT, named, measured.** Copilot fails open by design (S14); we cannot change that. 63 ms p95 against a 30 s budget is 475× headroom, so a timeout means hung, not slow. **Residual: real.** Detected by `hook.start` without `hook.end`, and by `edits_under_lease_pct`. |
| H13 | Copilot silently ignores a `deny` response | **DETECT — the conformance harness.** Unverified today and **not assumed**; until the harness passes on a real Copilot session, Copilot is **advisory at the edit boundary and enforced at commit**, exactly as the architecture requires. |
| H14 | The plugin bundle drifts from the two harnesses' formats | **DETECT.** The emitted manifest is validated against the recorded fixture from S14. |

## Adversarial analysis (STRIDE-lite)

**New trust boundaries:** (B7) `artifacts.yml` → the driver (a committed file that decides whether a merge may overwrite); (B8) the merge driver → the working tree (it writes files during a merge); (B9) the emitted plugin bundle → two harnesses (it becomes executable configuration).

| B | Threat | Disposition |
|---|---|---|
| B7 | **E** — a PR reclassifies `src/**` as `derived`, so the next merge overwrites authored work | **MITIGATE, layered.** Registry changes are PR-reviewed; the driver cross-checks `check-attr` against the registry and refuses on disagreement; the default is `authored`. Negative test: a registry marking a source tree `derived` is refused by the driver. |
| B7 | **T** — a pattern with `..` or an absolute path escaping the repo | **MITIGATE.** Patterns are repo-relative; anything escaping is a registry error. Reuses Phase-2's `_reject_path`. Negative test. |
| B8 | **T** — the driver writes outside `%A` | **MITIGATE.** It writes **only** `%A`. Negative test asserts no other path is touched during a merge. |
| B8 | **I** — regenerator output leaks into a file the driver did not own | **MITIGATE.** Same control; `%P` is used for identity only, never as a write target. |
| B9 | **E** — the emitted plugin runs an arbitrary command in two harnesses | **MITIGATE.** `--emit` writes to a directory the caller names and **prints what it wrote**; it never installs, never edits `~/.copilot/` or `.claude/settings.json`. The Phase-2 precedent (P19) — a layer that grants itself tool permissions is the elevation it exists to prevent. Negative test. |
| B9 | **S** — a bundle claiming to be someone else's plugin | **ACCEPT.** Plugin identity is the harness's trust model, not ours. Residual: a user installing a bundle from an untrusted source. Named, not mitigated here. |

## Privacy analysis (LINDDUN-lite)

**Phase 3 touches no personal data.** The registry holds path patterns and class names; the allocator holds a timestamp and randomness; the plugin bundle holds a command line. The only carry-forward is Phase 2's named residual — **a path can be personal by inference** — and it is unchanged: paths are already in git history and every commit message, and the decisions store remains git-ignored. No new category, no new retention, no new egress. Rights path: unchanged, deleting the derived stores is lossless.

## Telemetry

| Code | Meaning |
|---|---|
`COORD-ALLOC-SCHEME-UNKNOWN` | an unregistered scheme prefix
`COORD-PREFIX-AMBIGUOUS` | a prefix matching more than one id (exit 3, candidates listed)
`COORD-PREFIX-NOMATCH` | no match, **with the corpus size** (exit 4)
`COORD-CLASS-CONFLICT` | overlapping registry patterns of different classes
`COORD-CLASS-UNREGISTERED` | no registry — advisory, everything `authored`
`COORD-DRIVER-NOT-EFFECTIVE` | declared in `.gitattributes`, absent from `.git/config`
`COORD-DRIVER-DISAGREES` | `check-attr` and the registry disagree for a path
`COORD-REGEN-FAILED` | regeneration failed; conflict markers written; **exit 0**

**Metrics, all derived:** allocations per scheme · derived-merge resolutions vs. authored conflicts (the M1 measure) · driver-effectiveness as a boolean per clone · `edits_under_lease_pct` **segmented by harness**, which is how H12/H13 become visible rather than assumed.

## Test plan

**Triggered directives:** D0 hygiene · D1 pure units (allocator, `classify`, prefix resolution) · D2 file-I/O (registry parser, driver) · D3 subprocess/CLI contract (every git call) · D4 concurrency (the allocation burst) · D6 error paths (every mode above) · A1 negative security tests (every mitigated STRIDE row).

| # | Test | Proves |
|---|---|---|
| Q1 | `test_burst_asserts_ids_were_actually_issued_then_uniqueness` | H1 — **and asserts the corpus size first** (R4; the architecture named this test) |
| Q2 | `test_existing_ids_are_never_rewritten` | `NFR-C2`, expand-migrate-contract |
| Q3 | `test_merge_losing_an_entry_fails_closed` | H2 — **red-first on a dedupe-by-id resolution** |
| Q4 | `test_prefix_resolution_is_unique_or_refuses` | H9 |
| Q5 | `test_prefix_nomatch_reports_corpus_size` | H10 / R4 |
| Q6 | `test_driver_runs_under_rebase_not_only_merge` | S11 — the case that actually matters |
| Q7 | `test_driver_writes_conflict_markers_and_exits_zero_on_failure` | **H4, red-first against a driver that exits 1** |
| Q8 | `test_driver_touches_only_the_temp_result_file` | **A1 — B8** |
| Q9 | `test_unregistered_driver_is_detected_by_doctor` | H3 (S13) |
| Q10 | `test_unregistered_driver_degrades_to_a_visible_conflict` | S12a — pins the corrected ADR-0009 claim |
| Q11 | `test_source_tree_marked_derived_is_refused` | **A1 — B7, the highest-severity mode** |
| Q12 | `test_overlapping_classes_are_a_registry_error` | H7 |
| Q13 | `test_missing_registry_is_advisory_and_says_so` | H8 (US-8) |
| Q14 | `test_registry_pattern_escaping_the_repo_is_refused` | **A1 — B7** |
| Q15 | `test_emitted_plugin_matches_the_recorded_harness_fixture` | H14 (S14) |
| Q16 | `test_emit_does_not_install_or_edit_harness_config` | **A1 — B9** |
| Q17 | `test_audit_log_injected_id_seam_survives_pack_sync` | H11 (`PACK-D`) |
| Q18 | **Conformance harness** — `test_harness_adapter_conformance[claude,copilot]` | see below |

**Q1, Q3 and Q7 are proven red on the un-fixed shape before being trusted.**

> **AMENDED DURING IMPLEMENTATION (2026-08-24) — the two envelopes are not similar, and the
> adapter was a silent no-op on Copilot.**
> This design treated the Copilot adapter as "one function" whose response shape differs.
> Extracting the **real** payload from `~/.copilot/session-state/*/events.jsonl` (55,541
> recorded `preToolUse` invocations) showed the *request* differs at least as much:
>
> ```
> Claude   {"tool_name": "Edit", "tool_input": {"file_path": "src/a.cs"}}
> Copilot  {"hookType": "preToolUse",
>           "input": {"cwd": "C:\\repo",
>                     "toolCalls": [{"name": "edit", "args": "{\"path\": \"C:\\repo\\src\\a.cs\"}"}]}}
> ```
>
> Copilot **batches** N tool calls per invocation, `args` is a **JSON string** not an object,
> the path key is **`path`** not `file_path`, and the path is **absolute**. The Phase-2 hook
> reads `tool_input.file_path`, finds nothing, and returns **`allow` for every Copilot edit** —
> a silent no-op wearing the shape of enforcement. **The conformance suite caught this before
> any of it shipped, which is the entire argument for writing it.**
>
> Consequences now designed and implemented: an envelope-normalising `parse_hook_request`;
> **batch semantics** (any refused call refuses the batch — a false refusal costs a message,
> a false grant costs a merge); absolute→repo-relative path resolution; and a **parser/policy
> split** — the parser extracts every path, the hook decides which tools matter, so a *read*
> of a leased artifact is allowed (reads are parallel, writes serialize).
>
> One further measured fact: **`powershell` is the single commonest recorded tool call
> (26,210 of 55,541)** — the shell-bypass path named as `G4` in the Phase-2 design, observed
> rather than supposed.

### The conformance harness (how H13 gets closed, not assumed)

A **fixture-driven suite any harness adapter must pass**: feed the adapter each harness's recorded `PreToolUse` payload, assert the response matches that harness's documented decision envelope, and assert the fail-safe path. It runs today against the **Claude** payload (executed, S5) and against the **recorded Copilot invocation shape** (S14).

It **cannot** assert that Copilot *honours* a deny — that needs a live Copilot session denying a real edit, which is not run here. The harness is written so that closing H13 is **running one test**, not writing one. Until it passes: **Copilot is advisory at the edit boundary and enforced at commit**, and `coord doctor` says so.

## UI design

**Medium:** terminal. Two new surfaces.

`coord doctor` — the state set is `effective` / `declared-but-not-registered` / `no registry (advisory)` / `registry error`. Real copy:

```
merge driver     NOT EFFECTIVE
  declared    .gitattributes covers 6 path(s)
  registered  no - `git config merge.coord-regen.driver` is unset in this clone
  effect      those files will conflict normally instead of regenerating
  remedy      run `coord install` in this clone; .git/config is per-clone and never committed
```

The `effect` line is load-bearing: it says the consequence is a **normal conflict**, not lost work — the S12a correction, surfaced where someone will actually read it.

`coord resolve` ambiguity lists every candidate and refuses; it never picks. **No colour is load-bearing.** `DESIGN.md` / `ui-craft-gate.py`: **not applicable** — no rendered visual surface. Explicit negative.

## Gate record

`GATE design · 2026-08-23 · Patterns Expert, Simplifier, Python Developer, Domain Researcher, Data & Persistence → + Test Architect, Security, SRE, Distributed Systems · verdict: PASS WITH ONE CONDITION`

| Adversary | Finding | Resolution |
|---|---|---|
| **The Simplifier** | Three components in one phase; split it | **Overruled with the architecture's own phasing** — these three are Phase 3 by definition, and the registry is what makes the driver meaningful. `plugin --emit` was challenged separately and **kept**: without it `NFR-C1` is a claim with no artifact. |
| **The Simplifier** | PyYAML for the registry | **Rejected** — thirty lines against the pack's zero-dependency floor. |
| **Patterns Expert** | The class Strategy was called speculative in Phase 2 and is adopted now | **Consistent, and deliberately noted:** in Phase 2 there was one class and no registry, so it was anticipation. The registry makes it real. |
| **Test Architect** *(hard veto)* | Q1 must assert the burst **actually issued** ids before judging uniqueness | **Resolved** — the R4 rule, and the exact defect this architecture's own spike committed. |
| **Test Architect** *(hard veto)* | "The driver is safe" is unfalsifiable without the failing-driver case | **Resolved** — Q7 red-first against a driver exiting 1, asserting markers present and exit 0. |
| **Data & Persistence** *(veto)* | Where is the backfill? | **Resolved: there is none, and that is the point.** Nothing is rewritten, so nothing is guessed. Expand-migrate-contract with `next_id` retained. |
| **Data & Persistence** | Registry history rule | **Resolved** — Type-1 by decision; git holds the history, and modelling it twice would be the defect. |
| **Security** *(hard veto)* | A registry change can authorise overwriting authored work — the highest-severity path in the phase | **Resolved, layered** — PR review + driver cross-check + `authored` default + Q11. |
| **Security** *(hard veto)* | `--emit` must not install | **Resolved** — writes where told, prints what it wrote, touches no harness config. Q16. |
| **SRE** | Is a non-effective driver visible without someone thinking to look? | **Resolved** — `coord doctor`, and driver-effectiveness is a metric per clone. |
| **SRE** | Missing mode: a regenerator hanging inside a rebase | **Resolved** — added as H5, bounded wall-clock, markers on expiry. |
| **Distributed Systems** *(hard veto)* | Copilot fails **open** on timeout — the design cannot claim enforcement there | **Resolved as a named residual (H12) and a condition.** Stated in `coord doctor`, measured per harness, and H13 keeps Copilot advisory-at-edit until the conformance harness passes live. |

**Condition of pass:** the conformance harness must be **run against a live Copilot session** before any claim that Copilot enforces at the edit boundary. Until then the layer reports Copilot as advisory, and the commit floor is its real enforcement.

**The authors did not clear their own hard veto.**

## Residual risk

- **H13** — Copilot's deny contract is unverified. The spike closed *invocation*, not *obedience*.
- **H12** — Copilot fails open on a 30 s timeout, by its design, not ours. 475× headroom, but not zero.
- **H6** — a misclassification is the one way this phase could *cause* the loss it prevents. Three controls, still the mode to watch.
- **The 26-character id** remains unwieldy; prefix recall mitigates the consumer cost the ADR did not name, and does not eliminate it.
- **`cmd_worktree`** is undesigned and contradicts a recorded gate decision — surfaced above, owned by nobody yet.
