---
id: design-coord-core-phase1
title: "Design — coord core, Phase 1 walking skeleton (record · fold · claim/check/release/tail)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, walking-skeleton, append-only, fold, leases, log-a, stdlib]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: spec-agent-coordination, rel: implements }
  - { to: adr-0007-coordination-substrate, rel: implements }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-02-20"
summary: >-
  The Phase-1 walking skeleton: an append-only per-session record, a pure fold over it, and four
  verbs (claim, check, release, tail) that let two sessions in two worktrees see each other's leases.
  Stdlib only, no daemon, no dependency. The LOG-A seam — an append onto a file that does not end in
  a newline fuses two records and loses both — is the record writer's first test, not a hardening.
---

# Design: coord core — Phase 1 walking skeleton

- **Status:** Accepted
- **Spec / architecture:** `docs/specs/agent-coordination.md` · `docs/architecture-agent-coordination.md` · `docs/adr/0007-coordination-substrate.md`
- **Delivery phase / vertical slice:** **Phase 1**, the walking skeleton. The thinnest complete path touching every architectural layer: **append → fold → check → refuse → release**.
- **Author(s) / date:** Patterns Expert + The Simplifier + Python Developer + Domain Researcher (peers), 2026-08-20

> **Grounding trace (V15):** `design-coord-core-phase1` → `implements` → `architecture-agent-coordination` (§6 Phase 1, §4.1 grain, §9-R4) → `implements` → `adr-0007-coordination-substrate` (record + fold, no daemon) → `implements` → `spec-agent-coordination` (US-1, US-9, `NFR-P1`, `NFR-R1`, `NFR-R2`).

## Responsibility

**One:** hold the record of intent and answer *"may this session touch this artifact?"* from it.

It does **not** enforce (Phase 2), allocate ids (Phase 3), resolve merges (Phase 3), or render anything into another agent's context (Phase 4). Those are named here only as the seams that must stay substitutable.

## Placement in the phasing — what is real, what is mocked

| Seam | Phase 1 | Designed as a contract so later phases substitute rather than redesign |
|---|---|---|
| Artifact class | **Mocked** — everything is `authored` | `classify(path) -> str` is a single function. Phase 3 replaces its body with the registry; no caller changes. |
| Enforcement | **Mocked** — `check` is a CLI verb with an exit code | The hook and pre-commit are *callers* of `check`, not new logic. Exit codes are the contract: `0` free/mine, `3` refused, `4` not-checked. |
| Identity | **Real but asserted** — `AGENT_NAME` / `AGENT_SESSION` from env | Unauthenticated by decision (ADR-0011). Nothing later needs to change shape. |
| Allocation | **Mocked** — event ids are `session:counter`, unique within a file | Phase 3 swaps the id function. The fold never parses an id, so nothing downstream couples to its shape. |
| Projection | **Absent** | Deliberately. It is the Phase-4 trust boundary. |

**Human demo (the exit criterion):** two terminals in two worktrees. A claims `src/**`; B claims `src/Foo.cs` and is **refused** with holder, reason, remedy in four lines; A releases; B's claim is granted.

## Data model — settled before the contracts

*Bounded context: Agent Coordination. Aggregates and ubiquitous language are in the spec; only what Phase 1 touches is restated.*

**Aggregate: Session record.** Root `SessionId`. **The one invariant: a session's record has exactly one writer, for its whole life.** This is what keeps the substrate from becoming the hotspot it exists to remove.

**Grain, declared before any field:** *one row of the record is exactly one event emitted by one session at one instant* — identified by `(session, seq)`, recorded when the session decides, never when the fold reads.

**Durable representation** (ADR-0007): append-only JSONL facts, one file per session under `.agents/log/`. **Every** piece of state is a fold. Phase 1's fold produces exactly one thing: the live lease set.

| Field | Additivity | History rule | Writer | Compute reader |
|---|---|---|---|---|
| `kind` | non-additive (categorical) | append-only; never rewritten | the emitting session | `fold()` dispatch |
| `at` (epoch seconds, float) | non-additive (point in time) | append-only | the emitting session | expiry arithmetic in `fold()` |
| `ttl` (seconds) | non-additive (duration) | append-only | the emitting session | `expires = at + ttl` |
| `path` (glob) | non-additive | append-only | the emitting session | `overlaps()` |
| `wi`, `agent`, `session` | non-additive | append-only | the emitting session | the refusal message |

**Derive, don't store (DM7).** `expires` is **computed** (`at + ttl`), never persisted — two stored definitions of one quantity is the defect signature. The live lease set is computed per call; **there is no cache in Phase 1** (the snapshot is a Phase-3 optimisation and would be a labelled rebuildable cache with an equality test).

**Append-only invariant, enforced and tested.** The writer opens `O_APPEND` and writes exactly one `write()` per record. **A test attempts a forbidden rewrite** — truncating and re-writing a record — and asserts the reader rejects the result.

**No migration.** Greenfield; nothing to expand-migrate-contract.

## Change surfaces this must reach (E7)

store (`.agents/log/*.jsonl`) → model (`Event`, `Lease`) → service (`fold`, `overlaps`, `check`) → **projection/wire** (the JSON `check` record and the four-line refusal) → client (the CLI verbs) → UI (terminal output, §UI) → **compute reader** (`expires` computed in `fold`, never stored). Implementation ticks each off; the missing-projection defect is found now rather than in Phase 2.

## Contracts

**Exposed — the CLI, and its exit codes *are* the contract:**

```
coord claim   --wi <id> --path <glob> [--ttl 300]     0 granted · 3 refused
coord check   <path>                                  0 free-or-mine · 3 refused · 4 NOT CHECKED
coord release --path <glob>                           0
coord tail    [-n N]                                  0
```

`--json` on `check` emits `{"decision":"allow|deny|not_checked","path":…,"holder":…,"wi":…,"expires_in":…,"reason":…}`.
Identity from `AGENT_NAME` / `AGENT_SESSION`; record root from `COORD_ROOT` (default `.agents/`).

**Consumed:** Python **stdlib only** — `json`, `os`, `time`, `fnmatch`, `argparse`, `sys`. No dependency, at any rung.

## Solution-Selection Ladder (L1)

| Rung | Question | Answer |
|---|---|---|
| 1 YAGNI | Does this need to exist? | Yes — it is the exit criterion for the whole capability. |
| 2 Reuse in codebase | Does the pack already do this? | **`audit-log.py` is the closest sibling** and was read. It is an append-only JSONL writer — and it is the **recorded instance of `LOG-A`**: it writes `json.dumps(entry) + "\n"` with no precondition on the file's final byte. So it is reused as the *shape* and explicitly **not** as the implementation; the fix is the thing Phase 1 must not repeat. |
| 3 stdlib | Is stdlib enough? | Yes — `fnmatch` for globs, `os.open(O_APPEND)` for the write. |
| 4 native | A platform feature? | `O_APPEND` atomicity, **verified by spike S3** (6 processes × 200 × 4 kB → 0 interleaved). |
| 5 installed dep | — | Not reached. |
| 6–7 minimum | Smallest correct? | ~200 lines, four verbs, one fold. |

**`simplify:` markers to carry in code:**
- `simplify:` glob overlap is `fnmatch` both ways plus a literal-prefix test. **Ceiling:** patterns with `**` in the middle, and character classes. **Upgrade trigger:** the first refusal a human calls wrong, or Phase 3's registry introducing nested patterns.
- `simplify:` the fold reads every file every call. **Ceiling:** measured p95 60 ms (ADR-0007's compaction trigger). **Upgrade trigger:** the check p95 crossing 60 ms.

## Patterns (named, and surviving both lenses)

- **Event Sourcing** — the record is the source; state is a fold. *Simplifier:* justified because the alternative (mutable state) is the very thing that cannot be reviewed in a PR.
- **CQRS read model, degenerate** — the fold is the read side, computed per call with **no materialisation in Phase 1**. *Patterns Expert conceded:* a cache here would be pattern-for-its-own-sake at 47 ms.
- **Lease with TTL** (Chubby/etcd family) — expiry without a liveness protocol.
- **Ports & Adapters** — `coord_core` is a pure module; the CLI is a thin host. Follows [ADR-0005](../adr/0005-harness-runner-boundary.md).
- **Rejected:** Repository (no store to abstract); Observer/pub-sub for lease changes (nothing subscribes in Phase 1); a State Machine for lease lifecycle (three states derived from a fold do not need one).

## Error & concurrency model

- **Every error path names itself.** A malformed line reports its file, line number, and the parse error; it never causes a silent skip.
- **Fail to `not_checked`, never to `allow`** (`NFR-R2`). Missing identity, unreadable record, absent root → exit `4` with a reason beginning `NOT CHECKED`.
- **Concurrency:** one writer per file makes writes race-free by construction; `O_APPEND` + one `write()` per record makes even a shared file safe (S3). Two simultaneous intersecting claims are both recorded; the fold resolves by total order and the loser is refused on its **next** check — stated as advisory-until-checked, not sold as mutual exclusion.

## Failure-mode analysis

| # | Mode | Disposition |
|---|---|---|
| F1 | **Append onto a file whose last byte is not `\n` fuses two records; both are lost, exit 0** (`LOG-A`, recorded instance in `audit-log.py`) | **PREVENT.** The writer seeks to the end, reads the final byte, and emits a leading `\n` when it is not already one — making fusion *impossible to express* rather than detectable. Rung 1. Test: `test_append_after_missing_trailing_newline_does_not_fuse`. |
| F2 | A malformed line makes the whole fold unreadable | **DETECT + DEGRADE.** Parse errors are collected, not raised; `fold` returns `(leases, errors)`. Any error ⇒ `check` returns `not_checked`, never `allow`. Test: a corrupt line yields exit 4 with the file and line number. |
| F3 | **A check over an empty record reports "free" indistinguishably from "checked and free"** (§9-R4, and the note that produced it) | **PREVENT.** `check --json` always reports `events_scanned` and `files_scanned`; a zero-file scan is `not_checked`, not `allow`. Test: `test_empty_record_is_not_checked_not_clean`. |
| F4 | Identity unset ⇒ every lease looks like someone else's | **PREVENT.** Missing `AGENT_SESSION` ⇒ exit 4 before any fold. Test asserts the reason names the variable. |
| F5 | A session dies holding leases | **RECOVER.** TTL expiry, computed at read time. Test: a lease past its TTL does not refuse. |
| F6 | Clock moves backwards / skew between worktrees | **ACCEPT, bounded.** A backwards clock *shortens* a lease — the safe direction. **Residual risk:** skew beyond one TTL could grant an overlapping lease early. Accepted: bounded by TTL, and the alternative (a clock protocol) is disproportionate for a local tool. |
| F7 | Disk full / permission denied mid-write | **DETECT.** `os.write` errors propagate with the path named; the CLI exits non-zero. Never reported as success (`CTRL-E`: an exit code is not a result). |
| F8 | A claim glob matching the record itself (`.agents/**`) | **PREVENT.** Claims over `COORD_ROOT` are refused at parse time. Test included. |
| F9 | The same claim emitted twice (a retried tool call) | **PREVENT.** Idempotent by `(session, seq)`; re-emitting is a no-op, not a second lease. |
| F10 | Fold cost grows unbounded | **DETECT.** `check --json` reports `events_scanned`; ADR-0007's 60 ms trigger is the upgrade signal. `simplify:` marker carries it. |
| F11 | Two writers to one session file (two processes, same `AGENT_SESSION`) | **DETECT.** Cannot be prevented without a lock, and S3 shows it does not corrupt. The fold reports `duplicate seq` for that session; Phase 2's one-session-per-worktree rule prevents it properly. **Residual risk:** in Phase 1 the second writer's events are folded normally. |

## Adversarial analysis (STRIDE-lite)

**Trust boundaries in Phase 1:** (B1) the environment → the process (`AGENT_*`, `COORD_ROOT`); (B2) the record file → the fold (content another session wrote); (B3) the CLI argv → the writer. *The projection boundary does not exist in this phase — that is the point of phasing it last.*

| B | Threat | Disposition |
|---|---|---|
| B1 | **S** — a session sets `AGENT_SESSION` to another's and releases its leases | **ACCEPT, documented** (ADR-0011). Identity is asserted. Residual risk: local impersonation. Detection over prevention — the record shows which session released. |
| B1 | **E** — `COORD_ROOT` pointed outside the repo to make the layer read an attacker-controlled record | **MITIGATE.** `COORD_ROOT` is resolved and must be inside the repo root; otherwise `not_checked`. Negative test included. |
| B2 | **T** — a session edits another's record file | **DETECT.** Not preventable on a shared filesystem; the record is git-tracked, so tampering shows in a diff, and **no line is ever rewritten** by the tool. |
| B2 | **I** — the refusal message echoes a `wi` or `path` containing a secret | **MITIGATE.** Phase 1 emits only `path`, `wi`, `agent`, `session`, `expires_in` — all short, structured fields; **there is no free-text `intent` field in Phase 1**. Free text arrives in Phase 4 behind the scrub boundary. |
| B2 | **E** — a record field containing instruction-shaped text reaching a model | **TRANSFERRED to Phase 4 by construction, and named rather than assumed:** the refusal is a fixed four-line template with **no field interpolated into prose**; `path`/`wi` are rendered as delimited values. |
| B3 | **D** — a claim glob matching 100,000 files | **MITIGATE.** Patterns are matched lazily against the queried path only; the fold never enumerates the filesystem. Cost is O(leases), not O(files). |
| B3 | **T** — a path containing `..` or a shell metacharacter | **MITIGATE.** Paths are normalised and compared as strings; nothing is ever passed to a shell. Phase 2's hook uses exec-form `args` (ADR-0010), which closes `SHELL-A` structurally. |

## Privacy analysis (LINDDUN-lite)

**Phase 1 touches no personal data.** The record holds an agent name (a logical role such as `opus`, not a person), a session id, a work-item id, a glob, and timestamps. There is **no free-text field in this phase** — the one that will carry model-authored prose (`intent`) arrives in Phase 4, behind the scrub boundary and the LINDDUN pass that belongs with it. Stated as an explicit negative, not an omission.

## Telemetry

Phase 1 is a CLI with no service, so the Observability Standard's span/RFC-9457 surfaces do not apply; what does apply is **stable error codes** and **evidence for the four metrics**.

| Code | Meaning | Where |
|---|---|---|
| `COORD-REFUSED` | An unexpired lease held by another session overlaps | exit 3 |
| `COORD-NOT-CHECKED-IDENTITY` | `AGENT_SESSION` unset | exit 4 |
| `COORD-NOT-CHECKED-RECORD` | Record unreadable, absent, or containing a parse error | exit 4 |
| `COORD-NOT-CHECKED-ROOT` | `COORD_ROOT` resolves outside the repo | exit 4 |
| `COORD-CLAIM-SELF` | A claim over the coordination root itself | exit 2 |

**Metric evidence.** A refusal is an **appended event**, not just a returned string — otherwise the most interesting thing the system does would be invisible. `tail` replays them. This is what makes *"wait on a refused claim"* derivable in Phase 2 with no new instrumentation.

## Test plan (Testing Strategy directives)

**Triggered:** D0 hygiene (always) · D1 pure-function units (fold, overlaps, expiry) · D2 file-I/O contract (the writer) · D4 concurrency (two writers) · D6 error paths (every mode dispositioned *detect* or *prevent*) · A1 negative security tests (the mitigated STRIDE rows).

| # | Test | Proves |
|---|---|---|
| T1 | `test_append_after_missing_trailing_newline_does_not_fuse` | **F1 / `LOG-A`. Red-first against the naive writer.** |
| T2 | `test_fold_is_idempotent_under_replay` | `NFR-R1` — replay twice, identical state |
| T3 | `test_empty_record_is_not_checked_not_clean` | **F3 / §9-R4** — the rule this architecture's own spike violated |
| T4 | `test_missing_identity_is_not_checked` | F4 / `NFR-R2` |
| T5 | `test_expired_lease_does_not_refuse` | F5 |
| T6 | `test_malformed_line_is_not_checked_and_names_the_line` | F2 |
| T7 | `test_overlapping_claim_by_other_session_is_refused` | US-1 |
| T8 | `test_own_lease_and_free_path_are_allowed` | US-1 |
| T9 | `test_release_frees_the_path` | US-1 |
| T10 | `test_concurrent_appends_do_not_interleave` | S3, as a regression |
| T11 | `test_claim_over_coordination_root_is_refused` | F8 / B3 |
| T12 | `test_coord_root_outside_repo_is_not_checked` | **A1 negative security** — B1 elevation |
| T13 | `test_forbidden_rewrite_is_detected` | DM11 — attempts the forbidden update |
| T14 | `test_refusal_names_holder_reason_and_remedy` | UX-1 |
| T15 | `test_duplicate_seq_is_idempotent` | F9 |

**T1 and T3 must be observed failing on the un-fixed shape before they are trusted** (architecture gate condition 3).

## UI design — the CLI surface

**Medium:** terminal. **Platform guidance:** POSIX CLI conventions — exit codes carry the verdict, stdout carries the answer, stderr carries diagnostics, `--json` for machines.

**The refusal — the most-read output in the system.** Four labelled lines, fixed order, no prose: *what happened · who · why · what to do.*

```
REFUSED  src/Ingest/Reader.cs
  held by   opus · WI-142 · expires in 3m12s
  because   an unexpired lease overlaps your pattern
  remedy    wait, or claim a disjoint subset, or record a block on WI-142
```

**Complete state set for `check`:** allowed (silent, exit 0 — Unix convention: success says nothing) · refused (the block above, exit 3) · **not-checked** (same shape, `NOT CHECKED` in the verdict slot and the reason naming what was missing, exit 4) · empty record (a *not-checked* variant that says `0 files scanned`) · malformed (not-checked naming file and line).

**Copy, in voice, load-bearing.** `refused` — never "denied", "blocked" or "unavailable": the reader is a model that must not read the outcome as a transient failure worth retrying. `NOT CHECKED` in capitals because it is the one state that must not be mistaken for a pass.

**Accessibility:** no colour is load-bearing — every state is distinguishable from the text and the exit code alone (a11y and machine-readability are the same requirement here). No motion, no spinner. **Performance budget:** `NFR-P1` — the check under 100 ms p95, already measured at 47 ms.

**`DESIGN.md` / `ui-craft-gate.py`:** **not applicable** — those govern rendered visual surfaces, and this phase has none. Stated as an explicit negative. They become applicable if the Phase-4 operator view ever becomes an HTML lens, which the architecture defers.

## Gate record

`GATE design · 2026-08-20 · Patterns Expert, Simplifier, Python Developer, Domain Researcher → + Test Architect, Security, SRE · verdict: PASS`

| Adversary | Finding | Resolution |
|---|---|---|
| **Test Architect** *(hard veto)* | "Fold idempotence" is unfalsifiable unless the comparison is exact | **Resolved** — T2 compares the full lease dict after two replays, not a count |
| **Test Architect** *(hard veto)* | F1 and F3 must be proven red on the un-fixed shape, not just present | **Resolved** — made a gate condition; both are written against the naive implementation first |
| **Simplifier** | `--json` on `check` in Phase 1 is speculative | **Overruled with a reason:** Phase 2's hook consumes it, and `events_scanned` is how F3 is prevented rather than hoped for. It is not speculative generality; it is the next caller's contract |
| **Patterns Expert** | The fold should materialise a read model | **Withdrawn** on ADR-0007's measurement — 47 ms p95 makes a cache pattern-for-its-own-sake at this phase |
| **Security** *(hard veto)* | `COORD_ROOT` is attacker-controllable input that selects which file becomes trusted state | **Resolved** — resolved-path containment check, negative test T12. *This was found at the gate, not in the first draft.* |
| **Security** | Does Phase 1 leak anything into a model's context? | **Resolved** — no free-text field exists in this phase, and the refusal interpolates nothing into prose |
| **SRE** | Is a refusal detectable from telemetry alone? | **Resolved** — a refusal is an appended event, not only a returned string |
| **SRE** | Missing mode: what if two processes share one `AGENT_SESSION`? | **Resolved** — added as F11, dispositioned *detect* with residual risk, properly prevented in Phase 2 |

**The authors did not clear their own hard veto.**

## Residual risk

- **F6** clock skew beyond one TTL — accepted, bounded.
- **F11** two writers to one session file — detected, not prevented until Phase 2.
- **Glob overlap** is `fnmatch` both ways plus a literal-prefix test; mid-pattern `**` is the known ceiling, carried as a `simplify:` marker with its upgrade trigger. **This is the item the architecture explicitly declined to claim as spiked**, and it is still not spiked — it is bounded instead.
