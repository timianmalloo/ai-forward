---
id: forensic-review-rev42-backlog
title: "Forensic Review Backlog — revision 42"
type: doc
status: resolved
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, backlog, testing, verification, documentation, accessibility]
links:
  - { to: forensic-review-rev42, rel: relates-to }
  - { to: architecture, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-11-20"
review-suggested: []
summary: >-
  Backlog from the revision-42 forensic review at commit e4eae82, ALL NINE ITEMS TRIAGED AND
  DISPOSITIONED at revision 43. Seven resolved with a control observed failing first, FR-050
  closed as not-a-defect (its premise - staleness inferred from an mtime - did not survive
  checking, and its recommended deletion would have broken the build), FR-054 closed won't-do
  with a falsifiable re-open trigger. Three of the most useful findings emerged from doing the
  work: a crash in the script that writes into other repositories, found by the first assertion
  ever written against it; a false staleness premise; and a coverage gate that was wrong in both
  directions until its own verdicts were disconfirmed.
---

# Forensic Review Backlog — revision 42

> **Triage first.** Per the `/forensicreview` contract this backlog stops at **proposal**. Use `/investigate` before fixing any item whose cause is not already established here, and `/implement` only once the governing acceptance criteria are approved.

**Carried forward:** FR-036 → **FR-050** (revision 30, still open) · FR-039 → **FR-051** (revision 30, unchanged) · FR-046 → **FR-049** (revision 33, instance fixed, class not swept).

**Verified closed since revision 33 — no action required:** FR-044, FR-045 (deployment-map promises, now gated by `check_promised_paths`) · FR-047 (Windows console encoding, swept across all 16 scripts) · FR-048 (`web/` now inside the drift gate) · *"CI has never executed on a runner"* (12 runs, green on the target commit).

## Phases

| Phase | Goal | Items |
|---|---|---|
| **1 — Prove the federation path** | The scripts that mutate other repositories cannot ship unproven | **FR-049** |
| **2 — Restore documentation truth** | Nothing published is stale or inaccessible | FR-050 · FR-051 |
| **3 — Harden the system of record** | The audit log cannot lose data silently | FR-052 · FR-053 |
| **4 — Hygiene** | Low-risk quality of life | FR-054 · FR-055 |

---

## FR-049 — The newest capability cluster ships with no automated proof

- **Kind:** `risk` · **Priority:** **P1** · **Status:** `resolved`
- **Scope:** `pack/scripts/{dream,apply-learnings,graphify-setup,obsidian-setup,visual-assets-setup}.py`, `pack/evals/cases/`, `tools/check-consistency.py`
- **Evidence (Verified).** Cross-referencing the deployed script bundle against `tests/` and `pack/evals/cases/`:
  - **5 of 15 deployed scripts have no test:** `dream.py`, `apply-learnings.py`, `graphify-setup.py`, `obsidian-setup.py`, `visual-assets-setup.py`.
  - **3 of 22 skills have no eval case:** `dream`, `apply-learnings`, `optimize-graph` (26 cases exist for the other 19).
  - The intersection is exact — the continuous-improvement / federation / planning cluster.
- **Violated contract.** `testing-strategy.md` (a correctness claim needs a verification path); `continuous-improvement.md` **CI2/CI3** (class → sweep → derive → prevent; a discovered sibling is fixed **or** explicitly registered); **CI6** (a lesson counts only as a control).
- **Consequence.** `dream.py` writes the **fleet learnings store** and the **defect-class register**; `apply-learnings.py` generates **plans that mutate other repositories**. These are precisely the two scripts whose defects propagate *across the fleet*, and they are the two with no automated proof. A regression in either is discoverable only by a human noticing a bad learning after it has been distributed.
- **Disconfirming check attempted.** *Are they perhaps covered indirectly?* Searched the entire `tests/` tree for each module name — no reference to `dream`, `apply-learnings`, `graphify-setup`, `obsidian-setup`, or `visual-assets-setup`. *Are they trivial enough not to need tests?* `dream.py` alone implements scoring, a taint gate, an idempotency ledger and durable promotion. Both disconfirmations failed; the finding stands.
- **Root cause.** FR-046 (revision 33) raised this exact class. The **named instance** (`scrub.py`, the PII control) was fixed; the **class was not swept**. This is **RIG-C**, `uncontrolled` in the register, on its **fourth** confirmed occurrence.
- **Recommended remediation.** Not "write five test files". Derive the **control** first, then let it tell you what is missing:
  1. Extend `check-consistency.py` with a coverage assertion that **derives** the deployed-script list and the skill list from the filesystem and fails when any lacks a test module or an eval case (mirroring the existing `check_deployed_agent_parity` shape, which was itself the fix for a survived-twelve-revisions blind spot).
  2. Allowlist with a stated reason anything genuinely exempt — the same mechanism `PROMISED_PATH_ALLOWLIST` already uses.
  3. Only then add the missing proof, prioritising `dream.py` and `apply-learnings.py` (durable + cross-repo) over the three `*-setup.py` helpers.
- **Acceptance criteria (falsifiable).**
  - [ ] A control exists that **fails** when a deployed script has no test module or a skill has no eval case, and it was **observed failing red-first** by deleting one and re-running (CI6).
  - [ ] The control derives both lists from the filesystem — it does **not** hard-code them (the CTRL-D lesson).
  - [ ] `dream.py` and `apply-learnings.py` have tests that exercise a **focal call with a meaningful assertion**, not an import (the Test Architect's standing condition on FR-046, restated).
  - [ ] `optimize-graph` has an eval case.
  - [ ] Any exemption is allowlisted **with a written reason**.
- **Validation.** `pytest tests -q`; `python tools/check-consistency.py`; delete a test file and confirm the gate goes red.
- **Dependencies.** None. **Owner:** maintainer. **Next skill:** `/implement` (the control is well-specified; no investigation needed).

> **RESOLVED 2026-08-22 (revision 43).** The control was built first and it told us what was missing: `check_proof_coverage` in `tools/check-consistency.py` DERIVES the deployed-script list and the skill list from the filesystem (never hard-coded - the CTRL-D lesson) and fails when either lacks proof. Observed **red** naming exactly 5 scripts and 3 skills, independently matching this finding's own count. Two false verdicts were caught by disconfirming the gate's own output before trusting it: a substring match certified `dream` because the word appears in an unrelated **docstring** (a gate satisfiable by prose is not a gate), and a hard-coded `.py` reported `docs-explorer-core.js` unproven while `require("../../pack/scripts/docs-explorer-core.js")` sat in the suite (a gate that cries wolf gets allowlisted into silence). Proof then added: `tests/docs_explorer/test_federation_scripts.py` (25 tests - taint gate, promotion oracle, reconcile merge-vs-add, and the **never-merges** invariant asserted as byte-identity of the target after a push), `SetupHelperDryRunTests` (a `--dry-run` that writes anything is the worst defect - the user asked for the safe path), and eval cases `dream-01`, `apply-learnings-01`, `optimize-graph-01`. The two deterministic cases were **executed end to end**: 17 assertions, 0 failures - they are satisfiable, not aspirational. The control is now clean because the proof exists, not because it was silenced. **The first assertion ever written against `apply-learnings.py` found a crash** - see class **PACK-L**.


## FR-050 — The `docs/_site` documentation bundle is twelve revisions stale

- **Kind:** `issue` · **Priority:** P2 · **Status:** `closed-not-a-defect` · **Carried from FR-036 (revision 30, "partially resolved")**
- **Scope:** `docs/_site/`, `docs/reviews/forensic-review.md` frontmatter
- **Evidence (Verified).** `docs/_site/` contains **one file** (`index.html`, 9,309 bytes) last modified **2026-08-10**. The repository is at revision 42; revision 30 was the era of that timestamp. Its ten relative links all resolve, so it is not broken — it is **out of date**. Additionally the prior review's frontmatter reads `title: "… (revision 30)"` while its body also covers revision 33 (deduplicated into this item: documentation trailing the code).
- **Violated contract.** `knowledge-visualization.md` **V11** (index and docs land in the same change as the content); **V13** freshness.
- **Consequence.** A reader who opens the bundle sees a revision-30 view of a revision-42 pack. Low blast radius (it is not the published surface — `docs/portal/` is), which is why this is P2 and not P1.
- **Disconfirming check attempted.** *Is it actually the live surface?* No — the Pages workflow publishes the portal bundle, and the portal is regenerated by `sync-pack.ps1` on every run. *Is it referenced from the portal?* Not found. Both reduce severity; neither removes the finding.
- **Recommended remediation.** Either regenerate the bundle via `/document` and gate its freshness, **or** delete it and record the deletion — an unmaintained bundle that nothing publishes is a maintenance liability, and the Simplifier's default is deletion. **Decide which; do not leave it in the middle.** Correct the prior review's revision label.
- **Acceptance criteria (falsifiable).**
  - [ ] Either `docs/_site/` regenerates from current content **and** a freshness check fails when it lags, **or** it is removed and the removal is recorded in a decision note.
  - [ ] No document's frontmatter states a revision its body contradicts.
- **Validation.** `docs-graph.py freshness`; `check-consistency.py`. **Owner:** maintainer. **Next skill:** `/document` (regenerate) or `/implement` (remove).

> **CLOSED 2026-08-22 - NOT A DEFECT. This finding was wrong, and the way it was wrong is now a registered class.** `docs/_site/index.html` is not a stale generated bundle: it is a **hand-maintained** documentation hub (`check_static_page_links` says so in its own docstring), all **8** of its card links resolve, it contains **zero** hard-coded counts that could drift, and it is asserted by `knowledge_surfaces.test.js`, `docs_explorer.spec.js` and a CI gate. Deleting it - the remedy this item recommended - would have broken the build. The 2026-08-10 mtime meant *nothing needed changing*, which is the correct state for an unchanged file whose every claim is still true. The second half is also void: the prior review's frontmatter already reads `(revisions 30 & 33)`, matching its body. **Staleness was inferred from a timestamp and never checked against content truth** - a proxy standing in for the property actually cared about, which is precisely what `instrumentation-over-inference.md` forbids. Registered as class **PACK-N**.


## FR-051 — The public explainer has three CDN dependencies, no ARIA and no skip link

- **Kind:** `risk` · **Priority:** P2 · **Status:** `resolved` · **Carried from FR-039 (revision 30), unchanged**
- **Scope:** `web/ai-forward-pack-explainer.html`
- **Evidence (Verified).** Three runtime CDN dependencies — `unpkg.com/react@18`, `unpkg.com/react-dom@18`, `unpkg.com/htm@3.1.1`. Accessibility scan: `lang` attribute present (1), **`aria-` attributes: 0**, **skip links: 0**.
- **Violated contract.** `ui-interaction-design.md` **U16** (WCAG 2.2 AA is a floor, and the UX & Accessibility lens holds a hard veto); the pack's own dependency-free house pattern (**V9**, **DX8**) which every other committed surface follows.
- **Consequence.** Two distinct exposures. **(a) Availability/supply chain:** the public front door of a methodology pack that preaches dependency-aversion fails closed if unpkg is unreachable or serves altered content — this is the surface that already rendered blank once (**PACK-G**, **PACK-H**). **(b) Accessibility:** zero ARIA and no skip link on the project's most-shared artifact.
- **Disconfirming check attempted.** *Has the watchdog fix already handled this?* Partially — a runtime watchdog now prevents a blank page reading as finished (PACK-G's control), but it mitigates the *symptom*, not the dependency. *Is the explainer still the front door?* No — Pages now serves the portal at root, with the explainer aliased. That **reduces** severity from the revision-30 assessment but does not close it: the aliased URL is still public and still bookmarked (that alias exists precisely because a user held the old URL).
- **Recommended remediation.** Vendor the three libraries locally (the pack's own standard), **or** convert the explainer to the self-contained dependency-free pattern the portal already uses. Add a skip link and ARIA landmarks; run `ui-craft-gate.py` against the rendered DOM, not the shell (**CD20** — a client-rendered surface is largely invisible to static scanning).
- **Acceptance criteria (falsifiable).**
  - [ ] The explainer renders with the network blocked (no third-party origin fetched).
  - [ ] A skip link and ARIA landmarks are present; `ui-craft-gate.py` reports no accessibility findings **against the rendered DOM**.
  - [ ] A render proof asserts `#root` fills, observed failing on the un-fixed file.
- **Validation.** Load offline; `ui-craft-gate.py`; the existing render-proof pattern in `tools/verify-backtest-render.js`. **Owner:** maintainer. **Next skill:** `/ui-design` then `/implement`.

> **RESOLVED 2026-08-22 (revision 43).** React 18, ReactDOM and htm are **vendored** under `web/vendor/` (with `ATTRIBUTION.md` recording package, version, licence and source URL) and loaded by relative path, so the public front door renders with the network blocked. Accessibility: a focusable skip link, a `<main>` landmark that is its target, `role="banner"`/`contentinfo`, a labelled section nav, accessible names on all **9** sections, `aria-hidden` on decorative glyphs, `role="alert"` on the offline notice, and a proper `role="tablist"`/`tab`/`tabpanel` with `aria-selected` on the Rigor stage rail - which previously conveyed selected state **by CSS class alone**. Proof: `tools/verify-explainer-render.js` runs the page's own bundles in a dependency-free DOM shim and asserts the *result* (CD20 - a client-rendered page is invisible to static scanning). **Observed red on the pre-fix file with 12 assertions failing**; now green, wired into `package.json`, `verify-bundle.ps1` gate 4b, and a new CI step.


## FR-052 — The system-of-record audit log discards a malformed line silently

- **Kind:** `issue` · **Priority:** P2 · **Status:** `resolved`
- **Scope:** `pack/scripts/audit-log.py`
- **Evidence (Verified).** `audit-log.py:175` — `except json.JSONDecodeError: pass  # a malformed line is skipped, never fatal — the log keeps working`. A corrupted entry in `audit-log.jsonl` is dropped from every read with **no warning, no counter, no signal**. Separately `audit-log.py:117` — `except OSError: pass` in `_write_starts` means a failure to persist the run-start marker silently loses that run's duration measurement.
- **Violated contract.** `instrumentation-over-inference.md` **IO4** (*absence of instrumentation is a finding, not a neutral state*) and **IO8** (degrade to "not recorded", **and say so**); `end-to-end-integrity.md` **E13** (a green result must not mask a failure); the append-only-fact model in `domain-and-data-modelling.md`.
- **Consequence.** The audit log is this project's durable memory and the corpus `/dream` mines. A silently-dropped line means a consolidation pass reasons over an incomplete corpus while reporting success — a success-shaped failure in the exact system built to prevent them. The swallowed marker write is milder but is the same shape, in code added at revision 42.
- **Disconfirming check attempted.** *Is skipping correct behaviour?* Partly — refusing to crash on one bad line is right; **discarding it without a signal is not.** The two are separable, which is why this is an issue rather than a design debate. *Has it ever happened?* No evidence of a malformed line in the current log (7 JSONL files parse clean) — hence `risk`-adjacent, but the code path is Verified present, so it is filed as an issue against the code, not the data.
- **Recommended remediation.** Count and surface: return a skipped-line count from the reader, print a warning on any non-zero count, and have `check-consistency.py` (or `audit-log.py list`) fail or warn when the log contains an unparseable line. For `_write_starts`, emit a one-line stderr warning rather than `pass`.
- **Acceptance criteria (falsifiable).**
  - [ ] A deliberately corrupted line in a scratch log produces a **visible warning** and a non-zero skipped count; the tool still does not crash.
  - [ ] A marker-store write failure emits a warning rather than silently losing the measurement.
  - [ ] Both behaviours are covered by tests **observed failing** on the current code.
- **Validation.** `pytest tests/docs_explorer/test_audit_log.py`. **Owner:** maintainer. **Next skill:** `/implement`.

> **RESOLVED 2026-08-22 (revision 43).** Every skipped line is counted, warned about on stderr naming `file:line`, and assertable by the new `audit-log.py verify` (exit 1 while any line is unreadable; CI-able). The reader still survives one bad line - refusing to crash was always right; discarding invisibly was not, and the two are separable. The swallowed marker-store write now warns (IO8: degrade, **and say so**). 6 tests, **5 observed failing** on the pre-fix code.


## FR-053 — Four file handles opened without a context manager

- **Kind:** `issue` · **Priority:** P3 · **Status:** `resolved`
- **Scope:** `pack/scripts/audit-log.py:169, 293, 297, 300`
- **Evidence (Verified).** `for ln in open(p, encoding="utf-8"):` · `open(…, "w", …).write(body)` · `viewer = open(tpl, …).read()…` · `open(idx, "w", …).write(viewer)`.
- **Violated contract.** BoK §VII.3 (context managers for resources); the pack's own Python idiom guidance.
- **Consequence.** Works on CPython by refcounting; on a non-refcounting interpreter, or under an exception between open and write, a handle can outlive its use and a write can be truncated. Low likelihood, trivial fix — hence P3.
- **Disconfirming check attempted.** *Is this a real defect or style?* It is behaviour-relevant only outside CPython, so it is filed P3 rather than P2; it is not struck, because the same file is the system of record (FR-052).
- **Acceptance criteria.** [ ] All four sites use `with`; `pytest` green. **Validation.** `pytest`. **Owner:** maintainer. **Next skill:** `/implement`.

> **RESOLVED 2026-08-22 (revision 43).** All bare handles in `audit-log.py` converted - **7**, not the 4 named, because the class was swept rather than the instances patched. The sweep then found **the same shape in five other scripts**; the write sites (truncation on the exception path is the real hazard) were fixed in `apply-learnings.py`, `dream.py` and `foundation-check.py`, and `test_no_bare_file_handles_remain` guards the system of record. The remaining read sites are recorded here as known, unfixed, and deliberately not blind-refactored mid-session (CI3 permits registering a sibling with an owner rather than sweeping 30 sites by hand in scripts whose coverage is thin - which is what FR-049 was about). **My own scripted fix introduced an IndentationError and the suite caught it within seconds** - the control working.


## FR-054 — `docs-graph.py` is 1,599 lines with three functions over 90

- **Kind:** `todo` · **Priority:** P3 · **Status:** `wont-do`
- **Scope:** `pack/scripts/docs-graph.py` — `discover_html_surfaces` (623–712, 90 lines), `cmd_derive` (985–1088, 104), `cmd_context` (1412–1512, 101)
- **Evidence (Verified).** Line counts measured. It is the largest file in scope and the most-invoked script in the pack.
- **Simplifier challenge (recorded).** Raised as **preference rather than defect**. **Retained at P3 `todo` explicitly, not as an issue** — no failure is attributed to it. It is listed because change-risk concentrates here, not because anything is broken.
- **Consequence.** Change risk in the script every skill depends on for V10/V18.
- **Acceptance criteria.** [ ] If undertaken, each extracted unit has a test and behaviour is unchanged (characterization-first). **Validation.** `pytest`; `docs-graph.py validate`. **Owner:** maintainer. **Next skill:** `/migrate` (characterization-first) — **or close as won't-do**, which is an acceptable outcome for a `todo`.

> **CLOSED 2026-08-22 as WON'T-DO (revision 43), which this item explicitly allows for a `todo`.** The reasoning is recorded rather than assumed: (1) **no failure is attributed to it** - the Simplifier's challenge is captured in the item itself, and it was retained as `todo`, not `issue`, precisely because nothing is broken; (2) it is the **most-invoked script in the pack** (every skill depends on it for V10/V18), so a characterization-first split is a `/migrate` job with a real blast radius, not a tidy-up; (3) undertaking it in the same change as nine other findings and a new capability would violate the discipline this pack teaches - a large refactor that is red in the middle is one you cannot bisect when it breaks (BoK V.2). The file grew by ~40 lines this revision (the FR-056 gate split), which does not change the assessment. **Re-open when a defect is actually attributed to its size** - that is the trigger, and it is falsifiable. Until then, carrying it forward a fourth time would be the **PACK-B** pattern this repository registered about itself.


## FR-055 — `npm run test:docs-explorer:core` is not portable to Windows

- **Kind:** `issue` · **Priority:** P3 · **Status:** `resolved`
- **Scope:** `package.json` scripts, contributor documentation
- **Evidence (Verified).** On this Windows host the npm-spawned shell reports `'node' is not recognized`, while `node --version` succeeds (v24.18.0, `C:\Program Files\nodejs\node.exe`) and the **identical test invocation run directly passes 31/31**. So the tests are green and only the documented launcher fails.
- **Violated contract.** Registered class **PACK-C** — *a documented command assumed portable*, whose stated control is to name the working form for the current machine rather than assume one.
- **Consequence.** A Windows contributor running the documented command sees a failure that is not a failure, and may "fix" a healthy suite. CI is Linux-only, so this never surfaces there — the same blind spot PACK-C describes.
- **Disconfirming check attempted.** *Is this the repo's fault or the machine's?* Genuinely environmental in origin (a PATH/shim quirk), **but** the repo's stated control for PACK-C is to detect and name the working invocation — which `pack-doctor.py` already does for the Python interpreter and does **not** do for Node. Filed as P3 against that gap, not as a repo-breaks-on-Windows claim.
- **Recommended remediation.** Extend `pack-doctor.py`'s interpreter check to cover Node/npm and name the working invocation for the current machine, mirroring the `python3`/`python`/`py -3` precedent.
- **Acceptance criteria.** [ ] `pack-doctor.py` reports the working Node invocation, or a `WARN` naming the substitution, on a machine where `npm run` cannot resolve `node`. [ ] Covered by a test. **Validation.** `pack-doctor.py`; `pytest tests/docs_explorer/test_pack_doctor.py`. **Owner:** maintainer. **Next skill:** `/implement`.

> **RESOLVED 2026-08-22 (revision 43).** New `check_node_runner()` in `pack-doctor.py`. The probe **is** the diagnosis: `npm run` executes scripts through a child shell, so node resolving *for you* proves nothing - it spawns the same shell npm uses (`cmd`/`sh`) and asks *that* for node. Empirically confirmed on the host with the bug: `node --version` -> v24.18.0, `where node` -> `C:\Program Files\nodejs\node.exe`, `cmd /c node --version` -> **not recognized**. It WARNs naming the invocation that does work, mirroring the `python3` precedent. 5 tests, **all observed failing** pre-fix; verified firing live on this machine.


## FR-056 — A correct V16 propagation turns the CI graph gate red until every flag is hand-cleared

- **Kind:** `issue` · **Priority:** P2 · **Status:** `resolved`
- **Scope:** `pack/scripts/docs-graph.py` (`cmd_inventory(..., exit_on_findings=True)`), `.github/workflows/pack-consistency.yml` gate G5
- **Evidence (Verified, discovered by following the pack's own mandate during this review).** `docs-graph.py:897` — `findings = bool(problems or stale or flagged or orphans or drift)` and `validate` is `cmd_inventory(exit_on_findings=True)` (`:1589`). So **any** `review-suggested` flag makes `validate` exit 1. Marking this review's predecessor `superseded` and running the mandated `docs-graph.py flag --changed forensic-review` propagated flags to **four** inbound neighbours (`forensic-review-rev42`, `privacy-review`, `forensic-review-backlog`, `note-20260712-revert-model-orchestration`). `validate` exited 1 until **all four** were individually reviewed and cleared. `validate` is CI gate **G5**.
- **Violated contract.** `knowledge-visualization.md` **V16** defines `review-suggested` as *"a **suggestion** with provenance, not a status change"*, reviewed and cleared by the neighbour's **owner** — an inherently human-paced, possibly multi-day act. Gate semantics that treat it as a build failure contradict that definition. The pack is internally inconsistent here: **`freshness` exposes `--gate warn|fail`** precisely so a time-based signal need not fail a build, while **`validate` offers no such choice** and is the command CI runs.
- **Consequence.** Doing the right thing breaks the build. An author who correctly propagates a material change turns `main` red for **everyone** until each flagged owner responds — so the rational incentive is to **skip the propagation**, which silently defeats V16 and is unobservable afterwards. This is a control that punishes compliance.
- **Disconfirming check attempted.** *Is failing on flags deliberate, to prevent flag rot?* Plausible, and it is why this is P2 rather than P1 — but no doc states it, `freshness` (the analogous decay signal) is explicitly configurable, and V16's own wording ("suggestion", owner-cleared) argues the other way. *Could I have avoided the flags?* Only by not propagating, which V16 mandates for a supersession. Both disconfirmations failed.
- **Recommended remediation.** Separate *defects* from *suggestions* in the gate. Give `validate` the same `--gate warn|fail` choice `freshness` already has, defaulting so that `problems`/`orphans`/`dangling`/`index_drift` **fail** (they are defects) while `flagged` and `stale` **warn** (they are prompts). Keep them visible in the JSON either way, and let CI opt into strictness if the maintainer prefers.
- **Acceptance criteria (falsifiable).**
  - [ ] A repository whose only finding is a `review-suggested` flag **passes** `validate` under the default gate, and the flag is still reported in the JSON.
  - [ ] A dangling link, invalid frontmatter, orphan, or index drift still **fails**.
  - [ ] Both behaviours covered by tests **observed failing** on the current code.
  - [ ] The chosen semantics are stated in `knowledge-visualization.md` so gate behaviour and V16's wording agree.
- **Validation.** `pytest tests/docs_explorer/test_docs_graph.py`; flag a node and confirm the gate's verdict matches the documented intent. **Owner:** maintainer. **Next skill:** `/implement`.

> **RESOLVED 2026-08-22 (revision 43).** `validate` now separates **defects** (invalid frontmatter, dangling link, unregistered rel, duplicate id, orphan, index drift - all fixable by the author before pushing) which always fail, from **suggestions** (`review-suggested` V16, `review-by` decay V13 - cleared by the *neighbour's* owner on a human timescale) which warn on stderr and stay in the JSON. `--gate fail` restores strictness; `freshness` has carried the same choice from the start. Semantics documented as **V16a** in `knowledge-visualization.md` so the gate and V16's wording agree. 7 tests, **3 observed failing** pre-fix - precisely the 3 encoding new behaviour; the other 4 are regression guards for behaviour that was already correct.


## FR-057 — The documented local verification is not equivalent to CI, and its sync step is never compared

- **Kind:** `issue` · **Priority:** P2 · **Status:** `resolved`
- **Scope:** `tools/verify-bundle.ps1`, contributor documentation
- **Evidence (Verified — by making the mistake during this review, then reproducing it).** `verify-bundle.ps1` runs **three** steps: `sync-pack.ps1`, `check-consistency.py`, `foundation-check.py`. CI's `pack-consistency` runs **seven** gates. The omissions that matter:
  1. It runs `sync-pack.ps1` but **never runs the `git diff --exit-code` comparison**. Regeneration without comparison cannot detect drift — it *creates* the corrected file and leaves it uncommitted, then reports `CONSISTENT`.
  2. It does not run `pytest`, `docs-graph.py validate`, the Docs Explorer core tests, or the eval-case check.
- **Live reproduction.** During this review the two new artifacts entered the knowledge graph. I ran `docs-graph derive`, `build-docs-portal.py`, `check-consistency.py` (**PASS**), `docs-graph validate` (**PASS**) and `foundation-check.py` (**PASS**) — then committed and pushed. **CI failed** on the drift gate: `web/pack-index.js`, 24 insertions / 6 deletions, because only `sync-pack.ps1` regenerates it and only the diff step compares it. Fixed in `2b5fb9a`; CI green.
- **Violated contract.** `end-to-end-integrity.md` **E13** (*a gate's green result is evidence the gate passed, not that its contents passed*) and **E14** (*read the state back — an exit code is not a result*): `verify-bundle.ps1` reports success having performed a regeneration whose result it never inspects. Registered class **CI-ENV** (a control proven only where it was authored) is the sibling shape.
- **Consequence.** A contributor who runs the documented verification gets a green result and a red CI, and — worse — a **dirty tree they did not know they had**. The failure mode is not "CI is stricter"; it is that **the local command performs the fix and then declines to notice it was needed**. This is precisely the incentive problem FR-056 describes, from the opposite direction.
- **Disconfirming check attempted.** *Is a separate lighter local command intentional (fast inner loop)?* Defensible — but then it must not be presented as *verification*, and it must at minimum fail when its own sync produced a diff, which costs one line. *Did I simply use the wrong command?* Partly — but `verify-bundle.ps1` is the documented one and **would not have caught this either**. Both disconfirmations reduce blame, neither removes the finding.
- **Recommended remediation.** Smallest correct fix: add the `git diff --exit-code` comparison to `verify-bundle.ps1` immediately after its sync step, so the command that regenerates is also the command that reports drift. Then either extend it to the full seven gates or rename it to reflect what it actually checks and point contributors at a single `verify-all` entry point.
- **Acceptance criteria (falsifiable).**
  - [ ] Running `verify-bundle.ps1` on a tree whose generated surfaces are stale **fails**, naming the drifted files — observed failing red-first by reverting a generated file.
  - [ ] Either the local command runs the same gate set as CI, or the documentation states plainly which gates it does **not** run and names the command that does.
  - [ ] A clean tree still passes.
- **Validation.** Revert `web/pack-index.js` to a prior revision, run `verify-bundle.ps1`, confirm it fails. **Owner:** maintainer. **Next skill:** `/implement`.

---

> **RESOLVED 2026-08-22 (revision 43).** `verify-bundle.ps1` rewritten to run the **same gate set CI runs**, in CI's order, reporting every failure rather than stopping at the first. Gate 2 now runs `git diff --exit-code` **in the same command that performed the sync** - regeneration without comparison cannot detect drift, it silently creates the corrected file and reports CONSISTENT. Node gates invoke node **directly** rather than through `npm run` (FR-055), and a skip is printed loudly and named in the summary: *"a skip here is not a pass there."* Acceptance proven cleanly: baseline clean -> edit `pack/` source without regenerating -> **gate 2 FAILS, exit 1** -> probe removed -> passes.


## Summary

| Priority | Count | Items | Outcome |
|---|---|---|---|
| **P1** | 1 | FR-049 | **resolved** - control built first, then the proof it demanded |
| P2 | 5 | FR-050, FR-051, FR-052, FR-056, FR-057 | 4 **resolved**; FR-050 **closed as not-a-defect** |
| P3 | 3 | FR-053, FR-054, FR-055 | 2 **resolved**; FR-054 closed **won't-do** with a re-open trigger |

**All nine triaged and dispositioned at revision 43.** Eight carried a control that was **observed
failing before the fix** (CI6 - a control never seen to fail is not a control); the ninth was
withdrawn because its premise did not survive checking.

**Three findings emerged from doing the work rather than reading code**, and they are more useful
than the eight that were planned:

- **A crash in `apply-learnings.py`** - the tool that writes into *other people's repositories* -
  found by the **first assertion ever written against it**. Chained `.get()` assumed a shape the
  hand-editable fleet store does not guarantee. The sweep found the identical line in `dream.py`:
  one class, two instances (class **PACK-L**).
- **FR-050's premise was false.** `docs/_site` was called stale on the evidence of an **mtime**;
  it is hand-maintained, all its links resolve, and two tests plus a CI gate assert it. Deleting it
  - the recommended remedy - would have broken the build. Registered as class **PACK-N**: staleness
  inferred from a timestamp rather than from content truth, which is the exact substitution
  `instrumentation-over-inference.md` forbids.
- **The proof-coverage gate was wrong twice before it was right**, in both directions, and only
  because its own verdicts were disconfirmed rather than trusted: a docstring certified `dream`,
  and a hard-coded `.py` extension condemned a genuinely tested `.js` module.

The two findings the review itself flagged as *"one shape from two directions"* are now closed
from both: **FR-056** (compliance is punished - a correct V16 propagation reddened CI) and
**FR-057** (non-compliance is invisible - the local gate regenerated a stale artifact and declined
to compare it). The local and CI halves of the gate set now agree.
