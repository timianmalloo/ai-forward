---
id: design-coord-enforcement-phase2
title: "Design — coord enforcement, Phase 2 (PreToolUse hook · pre-commit floor · work-preservation guard)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "coordination"
tags: [coordination, enforcement, pretooluse, pre-commit, reachability, work-loss, ctrl-g, stdlib]
links:
  - { to: architecture-agent-coordination, rel: implements }
  - { to: adr-0010-enforcement-topology, rel: implements }
  - { to: design-coord-core-phase1, rel: refines }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-02-22"
summary: >-
  Phase 2 makes the Phase-1 lease actually hold: a PreToolUse hook that refuses an unleased edit,
  a pre-commit floor no settings key can switch off, and a guard that refuses to move HEAD over work
  reachable from exactly one ref. Splits the store in two — intent stays folded, enforcement decisions
  never are — because Phase 1's measurement put the fold at its compaction trigger at 10k events.
---

# Design: coord enforcement — Phase 2

- **Status:** Accepted
- **Spec / architecture:** `docs/specs/agent-coordination.md` (US-2, US-6, `NFR-M1`, `NFR-R2`, `NFR-S2`) · `docs/architecture-agent-coordination.md` §6 Phase 2 · `docs/adr/0010-enforcement-topology.md`
- **Delivery phase / vertical slice:** **Phase 2.** Real: the hook, the commit floor, the reachability guard, one-session-per-worktree. Mocked: other harnesses stay advisory **and say so**.
- **Author(s) / date:** Patterns Expert + The Simplifier + Python Developer + Security & Identity Architect (peers), 2026-08-22
- **Refines:** `design-coord-core-phase1` — and changes one thing it decided; see *Deviation from Phase 1*.

> **Grounding trace (V15):** `design-coord-enforcement-phase2` → `implements` → `adr-0010-enforcement-topology` (two boundaries, fail to `ask`, exec-form `args`) → `refines` → `design-coord-core-phase1` (the record, the fold, the four verbs, and F11's promise that one-session-per-worktree is "properly prevented in Phase 2") → `implements` → `architecture-agent-coordination` §6.

## Responsibility

**One:** make the Phase-1 verdict *bind* — refuse the edit, refuse the commit, refuse the HEAD move.

It does **not** decide the verdict (that is Phase 1's `check`), classify artifacts (Phase 3), allocate ids (Phase 3), or render anything into another agent's context (Phase 4).

## Deviation from Phase 1 — the store splits in two

Phase 1 appended a `refused` event into the intent log so a refusal would be observable. **That is now wrong, and the reason is Phase 1's own measurement.** The end-to-end check was **63 ms p95 at 10,000 events** — already at ADR-0007's 60 ms compaction trigger. Phase 2 records a decision **per edit**, which is one to three orders of magnitude more traffic than one per claim. Folding those would push the hot path past its budget within a day of real use.

| Store | Grain | Written by | Read by | Folded? |
|---|---|---|---|---|
| `.agents/log/<session>.jsonl` | *one row is exactly one **intent** event from one session at one instant* — `claim`, `release`, `session-start`, `session-end` | the claiming session | `fold()` → leases | **Yes** |
| `.agents/decisions/<session>.jsonl` | *one row is exactly one **enforcement decision** at one instant* — `allowed`, `refused`, `guard-refused` | the enforcing boundary | `tail`, `metrics` | **Never** |

Two grains, two stores, one reader each. The fold stays proportional to *claims*, not to *edits*, and the metric that decides whether this phase worked costs nothing on the hot path. `tail` reads both (it is the human stream); `check` reads only `log/` (it is the machine verdict). **This is a refinement of `design-coord-core-phase1`, recorded rather than silent** — it changes one Phase-1 behaviour and one Phase-1 test.

**Additivity:** `allowed` and `refused` counts are **additive** over time and over sessions (they are counts of events, not levels) — so `% of edits under a held lease` is a legitimate ratio of two sums. A lease *count* would be semi-additive and is deliberately not a measure here.
**History rule:** append-only, Type-2 by construction; no attribute is ever rewritten.
**Derive, don't store:** the percentage is **computed** from the two counts and never persisted. `unique_commits` is computed from git and never persisted.

## Placement — what is real, what is mocked

| Seam | Phase 2 | Contract that lets Phase 3/4 substitute |
|---|---|---|
| Artifact class | still **mocked** — all `authored` | `check` is called unchanged; Phase 3 changes only what `classify()` returns |
| Other harnesses | **advisory, and they say so** | the same `hook` verb serves any harness that can pipe JSON; only the *response shape* is Claude-Code-specific, and it is one function |
| Identity | asserted (ADR-0011) | unchanged |
| Allocator | mocked | unchanged |

**Human demo (the exit criterion):** an unclaimed `Edit` is refused **in the transcript**, with the four-line refusal. Then, with an unpushed commit reachable from one ref, `checkout` is refused and offers push. Then `coord metrics` prints a real percentage.

## Change surfaces (E7)

store (`decisions/*.jsonl` — new) → model (`Decision`) → service (`hook`, `precommit`, `guard`, `session`, `metrics`) → **projection/wire** (the PreToolUse JSON envelope; the pre-commit exit code; the `metrics --json` record) → client (`.claude/settings.json` hook entry; `.git/hooks/pre-commit`) → UI (terminal + the transcript's permission decision) → **compute reader** (`metrics` computes the ratio; `guard` computes `unique_commits`).

## Contracts

**Exposed:**

```
coord hook            # stdin: PreToolUse JSON · stdout: permissionDecision JSON · ALWAYS exit 0
coord precommit       # 0 clean · 3 an unclaimed staged artifact · 4 not-checked
coord guard [--fix]   # 0 safe to move HEAD · 3 unique work · 4 cannot determine
coord session start   # 0 registered · 3 this worktree already has a live session
coord session end     # 0
coord metrics [--json]# 0; the four NFR-M1 measures
coord install         # writes .git/hooks/pre-commit; prints the settings.json hook entry
```

**`hook` always exits 0.** The harness reads the *decision in the JSON*, not the exit code; a non-zero exit is an infrastructure failure, and conflating the two would make a crashed hook indistinguishable from a refusal. **This is the inversion of `precommit`, where the exit code *is* the contract** — recorded because the asymmetry is surprising and would otherwise be "fixed" by someone later.

**Consumed — all established by execution:**

| Contract | Established | Result |
|---|---|---|
| `PreToolUse` envelope + `hookSpecificOutput.permissionDecision` | authoritative settings schema (read) + program run across 5 cases (**S5**) | `allow` / `deny` / `ask` + `permissionDecisionReason`; stdin carries `tool_name`, `tool_input.file_path` |
| exec-form `args` | schema | no shell; placeholders substituted per element as plain strings — closes `SHELL-A` structurally |
| `if` pre-filter | schema | decides whether the process is **spawned at all** — the largest latency lever, and free |
| `git diff --cached --name-only -z` | **S8** | works **before the first commit**; appending `HEAD` **fails** on a repo with no commits, so HEAD is never passed. `-z` needed — a path with a space is otherwise split |
| unique-work expression | **S9**, five cases | see below |
| `.git/hooks` across worktrees | **S10** | linked worktrees **share** the primary `.git/hooks`, so one install covers every worktree — matching the record's own per-repository scope |

**The unique-work expression, and the two ways it was got wrong before:**

```
current = git symbolic-ref -q --short HEAD        # empty => detached => decline, do not accuse
peers   = git for-each-ref refs/heads refs/remotes  minus refs/heads/<current>
unique  = git rev-list HEAD --not <peers...>
```

`--all` is **forbidden here**. S9 reproduced both recorded bugs: `rev-list HEAD --not --all` returned **0** for a branch holding exactly one commit that existed nowhere else — because `--all` implicitly includes `HEAD`, reducing the expression to `HEAD --not HEAD`. And a single at-risk commit must be *counted*, not lost to array semantics.

## Solution-Selection Ladder (L1)

| Rung | Answer |
|---|---|
| 1 YAGNI | The hook and guard are the phase. `metrics` earns its place because it is the number that decides whether the phase worked (spec F2) — without it, enforcement is unfalsifiable. |
| 2 Reuse | **`coord check` is reused unchanged** — the hook and the floor are *callers*, not new logic. `guard-worktree.ps1` and `worktree-status.ps1` from TheTerrace are the **prior art being ported** (ADR-0012), not reinvented. |
| 3 stdlib | `json`, `subprocess`, `os`. |
| 4 native | git plumbing for reachability and staged files; `.git/hooks` for the floor; the harness's own hook surface for the edit boundary. |
| 5 dep | not reached. |
| 6–7 | ~230 added lines, six verbs. |

**`simplify:` markers:**
- `simplify:` `session start` detects an occupied worktree by reading the newest `session-start` without a matching `session-end` and comparing timestamps against a staleness window. **Ceiling:** a session killed without `session-end` holds the worktree until the window elapses. **Upgrade trigger:** the first time a human is blocked by a dead session.
- `simplify:` `metrics` reads every `decisions/*.jsonl` in full. **Ceiling:** ~100k decisions. **Upgrade trigger:** `metrics` taking over 2 s — it is an operator command, never on the hot path.

## Patterns

- **Adapter** — `hook` adapts one harness's envelope to `check`. The vendor-specific part is one function, which is what keeps `NFR-C1` reachable.
- **Interceptor / Sidecar** — the hook intercepts at the tool boundary without the harness knowing what a lease is.
- **Guard clause, inverted** — every boundary computes *reasons to refuse* and defaults to refusing.
- **Ports & Adapters** — `check` is the port; hook, pre-commit and CLI are adapters. Per ADR-0005.
- **Rejected:** Chain of Responsibility across boundaries (two boundaries do not need a chain); a Policy/Strategy object for decisions (the artifact-class Strategy arrives in Phase 3 — adding it now is speculative generality); a daemon holding the fold in memory (ADR-0007 measured it unnecessary).

## Error & concurrency model

- **`hook` never raises.** Any exception becomes `ask` with `NOT CHECKED` and the exception class named. A hook that crashes on a malformed payload would block every edit in the session.
- **Fail to `ask` / exit 4, never to `allow`** (`NFR-R2`). Missing identity, unreadable record, root outside the repo, git absent → not-checked with the reason.
- **Concurrency:** decisions are append-only, one file per session, one `write()` per record — the S3 atomicity result carries over. The guard is read-only against git.
- **Idempotency:** running `install` twice is a no-op; a pre-commit hook already present and not ours is **never overwritten** — it is reported.

## Failure-mode analysis

| # | Mode | Disposition |
|---|---|---|
| G1 | The hook raises on a malformed payload and blocks every edit | **PREVENT.** Total try/except → `ask` + `NOT CHECKED`. Test: malformed, empty, and non-object stdin. |
| G2 | The hook is invoked for a tool with no `file_path` (Bash, Read) | **PREVENT.** No `file_path` ⇒ `allow` with a reason saying why. The `if` pre-filter should stop most of these from ever spawning. |
| G3 | **Enforcement is switched off by `disableAllHooks` / `allowManagedHooksOnly` / `strictPluginOnlyCustomization`** | **DETECT + say so.** `install` reports which settings sources could disable it; the layer never claims enforcement it is not performing (`NFR-S2`). **Residual risk: real and accepted** — the commit floor is the answer. |
| G4 | An agent runs the edit through a shell, bypassing the tool boundary | **DETECT at the floor.** The commit boundary catches it. **Residual risk:** an agent that never commits is not caught by this phase — measured by `% of edits under a held lease`, which is spec F2's own probe. |
| G5 | `git diff --cached` fails (no git, not a repo, corrupt index) | **DETECT.** `precommit` exits 4 with the git stderr, never 0. *An exit code is not a result — the state is read back.* |
| G6 | A staged path contains a space, a quote, or a newline | **PREVENT.** `-z` NUL-separated form (S8). Test includes all three. |
| G7 | Pre-commit runs on a repo with **no commits yet** | **PREVENT.** `HEAD` is never passed to `diff --cached` (S8 proved appending it is fatal there). Test on a repo with zero commits. |
| G8 | **The guard reports SAFE for a branch holding exactly one unique commit** — the recorded bug | **PREVENT.** `--all` forbidden; explicit peer enumeration. **Test proves the buggy form returning 0 first** (architecture gate condition 3). |
| G9 | The guard runs on a **detached HEAD** — the state every PR gate runs in | **PREVENT.** `symbolic-ref` empty ⇒ decline with `not_checked`. It does **not** accuse; the recorded instance had a control accusing its own branch on CI. |
| G10 | A repo with **no peer refs at all** (one branch, no remote) — everything is "unique" | **DETECT, with an honest reason.** Reported as `no peer refs exist`, distinct from `unique work found`, so a fresh repo does not train people to disable the guard. |
| G11 | `install` overwrites somebody's existing pre-commit hook | **PREVENT.** An existing hook that is not ours is never overwritten; `install` reports it and exits non-zero. Test included. |
| G12 | A session dies without `session-end`, holding the worktree | **RECOVER.** Staleness window; `simplify:` marker carries the ceiling. |
| G13 | The decisions store grows without bound | **ACCEPT, bounded.** It is never folded, so it costs nothing on the hot path; `metrics` is an operator command. **Residual risk:** disk. Rotation is Phase 3 work. |
| G14 | Recording a decision fails (disk full) and the hook turns that into an allow | **PREVENT.** The decision is recorded *after* the verdict is computed and *cannot* change it; a failed record is swallowed and the verdict stands. A refusal that cannot be logged is still a refusal. |
| G15 | `metrics` divides by zero on an empty decisions store | **PREVENT + R4.** Zero decisions reports `no decisions recorded`, not `0%` — a rate over an empty corpus is not a measurement. |

## Adversarial analysis (STRIDE-lite)

**Trust boundaries:** (B4) the harness → the hook process (stdin JSON, an untrusted payload the model influences); (B5) the git index → `precommit`; (B6) `.git/hooks` and `.claude/settings.json` → the machine (what `install` writes); (B1–B3) inherited from Phase 1.

| B | Threat | Disposition |
|---|---|---|
| B4 | **T** — a crafted `file_path` (`../../etc`, a NUL, 5 MB) steers or breaks the check | **MITIGATE.** The path is normalised and compared as a string; it is never opened, never globbed against the filesystem, never passed to a shell. Length-capped. Negative tests for all three. |
| B4 | **S** — the payload asserts a `session_id` that is not this session's | **MITIGATE.** Identity comes from the **environment**, never from the payload. The payload's `session_id` is ignored entirely. Test asserts a forged `session_id` changes nothing. |
| B4 | **E** — a `permissionDecisionReason` containing instruction-shaped text reaching the model | **MITIGATE.** The reason is a **fixed four-line template**; the only interpolated values are `path`, `wi`, `agent`, `expires_in` — all short, structured, and rendered as delimited values, never into prose. Newlines and control characters are stripped from interpolated values. **This is the Phase-4 boundary arriving three phases early**, so it is closed here rather than deferred. |
| B5 | **T** — a staged path that escapes the repo | **MITIGATE.** git reports index paths repo-relative; anything resolving outside the repo root is `not_checked`, not allowed. |
| B6 | **E** — `install` writes an executable into `.git/hooks` | **MITIGATE.** Writes exactly one file, exactly one known body, refuses to overwrite a foreign hook, and prints what it wrote. It **never** edits `.claude/settings.json` — it prints the entry for a human to paste, because silently editing the file that controls tool permissions is precisely the elevation this row is about. |
| B6 | **T** — `install` invoked from a linked worktree writes to the shared hooks dir | **ACCEPT, documented.** S10 established that this is git's design: one hooks dir per repository. It is the correct scope; the surprise is documented rather than worked around. |
| B4 | **D** — a flood of hook invocations | **TRANSFER, named:** the harness's `if` pre-filter decides whether the process spawns. Not an assumption — it is in the settings entry `install` prints. |

## Privacy analysis (LINDDUN-lite)

**Phase 2 touches no personal data.** The decisions store holds a session id, an agent name (a logical role, not a person), a repo-relative path, a work-item id, a timestamp and an error code. There is still **no free-text field** in the record. One new consideration: a **file path can be personal data by inference** (`src/customers/jane-doe/...`). Disposition: **accept with a named residual** — paths are already in git history and in every commit message, so the decisions store adds no exposure git does not already have; and the store is **git-ignored** by default (`install` adds `.agents/decisions/` to `.gitignore`), so it never leaves the machine. Retention: local only, until rotation (Phase 3). Rights path: deleting the directory is lossless — it is derived observability, never a source.

## Telemetry

| Code | Meaning | Surface |
|---|---|---|
`COORD-REFUSED` | an unexpired lease held by another session overlaps | hook `deny`; precommit exit 3
`COORD-NOT-CHECKED-IDENTITY` / `-RECORD` / `-ROOT` | inherited from Phase 1 | hook `ask`; exit 4
`COORD-NOT-CHECKED-GIT` | git absent, not a repo, or a failed plumbing call | precommit/guard exit 4
`COORD-UNIQUE-WORK` | HEAD holds commits reachable from no other ref | guard exit 3
`COORD-NO-PEER-REFS` | no peer refs exist, so "second copy" has no meaning here | guard exit 3, distinct reason
`COORD-DETACHED` | detached HEAD — declined, not accused | guard exit 4
`COORD-WORKTREE-OCCUPIED` | a live session already holds this worktree | session start exit 3
`COORD-HOOK-EXISTS` | a foreign pre-commit hook is present | install non-zero

**Metrics (`NFR-M1`), all derived, none instrumented separately:** `edits_under_lease_pct` = `allowed / (allowed + refused)` · `refusals` and `mean_wait_on_refusal` from the decisions store · `unique_commit_count` from git. Each carries the corpus size, and an empty corpus reports *no decisions recorded* rather than a number (G15/R4).

## Test plan

**Triggered directives:** D0 hygiene · D1 pure units (the decision renderer, the metric ratio) · D2 file-I/O contract (the decisions store, the hook installer) · D3 subprocess/CLI contract (every git plumbing call) · D6 error paths (every mode above dispositioned prevent/detect) · A1 negative security tests (every mitigated STRIDE row).

| # | Test | Proves |
|---|---|---|
| P1 | `test_buggy_all_form_reports_safe_for_one_unique_commit` | **G8, red-first — the recorded bug, reproduced before the fix is trusted** |
| P2 | `test_guard_counts_a_single_at_risk_commit` | G8, array semantics |
| P3 | `test_guard_declines_on_detached_head` | G9 |
| P4 | `test_guard_reports_no_peer_refs_distinctly` | G10 |
| P5 | `test_guard_is_safe_once_a_second_ref_holds_the_work` | S9c |
| P6 | `test_hook_denies_unleased_edit_with_four_line_reason` | US-2 |
| P7 | `test_hook_allows_own_lease` / `test_hook_allows_when_no_file_path` | G2 |
| P8 | `test_hook_asks_on_malformed_payload_and_never_raises` | G1 |
| P9 | `test_hook_always_exits_zero` | the contract asymmetry |
| P10 | `test_hook_ignores_session_id_in_payload` | **A1 — B4 spoofing** |
| P11 | `test_hook_reason_has_no_newline_injection` | **A1 — B4 elevation** |
| P12 | `test_hook_rejects_oversized_and_traversal_paths` | **A1 — B4 tampering** |
| P13 | `test_precommit_refuses_unclaimed_staged_file` | US-2 floor |
| P14 | `test_precommit_handles_repo_with_no_commits` | G7 (S8) |
| P15 | `test_precommit_handles_paths_with_spaces_and_quotes` | G6 (S8) |
| P16 | `test_precommit_not_checked_when_git_fails` | G5 |
| P17 | `test_install_refuses_to_overwrite_foreign_hook` | G11 |
| P18 | `test_install_is_idempotent` | idempotency |
| P19 | `test_install_does_not_edit_settings_json` | **A1 — B6 elevation** |
| P20 | `test_session_start_refuses_occupied_worktree` | F11 from Phase 1 |
| P21 | `test_metrics_empty_corpus_reports_no_decisions_not_zero_pct` | **G15 / R4** |
| P22 | `test_metrics_ratio_is_correct` | `NFR-M1` |
| P23 | `test_decisions_store_is_not_folded` | **the Phase-1 deviation** — a decision must not create or clear a lease |

**P1 and P21 are proven red on the un-fixed shape before being trusted.**

## UI design

**Medium:** terminal, plus **the transcript** — the hook's `permissionDecisionReason` is rendered by the harness, not by us, so the four-line block must survive being embedded in someone else's chrome. That is why it is four short labelled lines and not a box.

**Complete state set for the hook decision:** `allow` (no user-visible output) · `deny` (the four-line refusal) · `ask` (same shape, `NOT CHECKED` in the verdict slot) · not-applicable (no `file_path` — allow, with a one-line reason).

**Copy.** `install` prints, verbatim:

```
Wrote .git/hooks/pre-commit  (shared by every worktree of this repo)

Add this to .claude/settings.json yourself - this tool does not edit it:
  "hooks": { "PreToolUse": [ { "matcher": "Write|Edit",
    "hooks": [ { "type": "command", "command": "python",
                 "args": ["<repo>/coord-core.py", "hook"],
                 "if": "Edit(src/**)", "timeout": 5 } ] } ] }

Enforcement can be switched off by disableAllHooks, allowManagedHooksOnly, or
strictPluginOnlyCustomization. The pre-commit floor cannot.
```

The last sentence is load-bearing: the tool states the limit of its own control rather than letting a reader assume exclusion it cannot provide.

**Accessibility:** no colour is load-bearing; every state is distinguishable from text and exit code alone. **`DESIGN.md` / `ui-craft-gate.py`: not applicable** — no rendered visual surface. Explicit negative.

## Gate record

`GATE design · 2026-08-22 · Patterns Expert, Simplifier, Python Developer, Security & Identity → + Test Architect, SRE, Distributed Systems · verdict: PASS`

| Adversary | Finding | Resolution |
|---|---|---|
| **The Simplifier** | Six verbs is Phase-2 scope creep — `metrics` and `install` are not enforcement | **Partially upheld.** `metrics` **kept**: it is the number that decides whether this phase worked, and without it enforcement is unfalsifiable (spec F2). `install` **kept**: without it the commit floor is aspirational. **`worktree-status` deferred to Phase 4** with the rest of the operator surface — that one was creep and is dropped. |
| **The Simplifier** | A Strategy object for decisions now, ready for Phase 3 | **Rejected as speculative generality** — the artifact-class Strategy arrives when the registry does. |
| **Test Architect** *(hard veto)* | "Refuses an unleased edit" is unfalsifiable without asserting the *response shape* the harness reads | **Resolved** — P6/P9 assert `hookSpecificOutput.permissionDecision` and exit 0 explicitly. |
| **Test Architect** *(hard veto)* | The recorded guard bug must be reproduced, not just avoided | **Resolved** — P1 runs the buggy `--all` form and asserts it returns 0 for a branch holding one unique commit, before the fixed form is trusted. |
| **Security** *(hard veto)* | The `permissionDecisionReason` reaches a model — the Phase-4 boundary, three phases early | **Resolved and closed here.** Fixed template, no prose interpolation, newlines and control characters stripped from interpolated values, negative test P11. |
| **Security** *(hard veto)* | `install` writing `.claude/settings.json` would be the layer granting itself tool permissions | **Resolved** — `install` **prints** the entry and never edits the file. Negative test P19. |
| **Security** | The payload's `session_id` as identity | **Resolved** — identity is environment-only; P10 asserts a forged payload changes nothing. |
| **SRE** | Is a bypass detectable from telemetry alone? | **Resolved** — `edits_under_lease_pct`. A low number *is* the bypass signal, and it is spec F2's own probe. |
| **SRE** | Missing mode: the decision record fails and the hook turns that into an allow | **Resolved** — added as G14. The verdict is computed before the record is attempted and cannot be changed by it. |
| **Distributed Systems** | The hook may run twice on a retried tool call, double-counting the metric | **Accepted, and stated.** Counts are additive event counts; a duplicate inflates both numerator and denominator negligibly. Deduping would need an id the payload does not carry. **Residual risk written down.** |
| **Data & Persistence** | Recording a decision per edit into the folded log would blow the hot path | **Upheld — this is the deviation.** Two stores, two grains; the fold stays proportional to claims, not edits. |

**The authors did not clear their own hard veto.**

## Residual risk

- **G3/G4** enforcement is bypassable — by policy settings, or by a shell. Conceded in `NFR-S2`, measured by `edits_under_lease_pct`.
- **An agent that never commits** is caught by neither boundary in this phase.
- **G13** the decisions store is unbounded; rotation is Phase 3.
- **Duplicate hook invocations** inflate both metric counts; accepted.
- **The hook is only spiked for one harness.** Copilot and any third harness remain **advisory at the edit boundary and enforced at commit** until each surface is executed — the architecture's condition 2 is still open, and this design does not close it.
