---
id: forensic-review-rev53-backlog
title: "Forensic Review Backlog - AI-Forward revision 53"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [forensic-review, backlog, verification, documentation, testing, security]
links:
  - { to: forensic-review-rev53, rel: relates-to }
  - { to: forensic-review-rev49-backlog, rel: supersedes }
  - { to: architecture, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-11-30"
review-suggested: []
summary: >-
  Proposed, prioritized backlog from the revision-53 forensic review. One carry-forward P2 (FR-069,
  re-verified open), one carry-forward P3 (FR-071), and four new P3 items (FR-072..FR-075). FR-070 is
  resolved. No P0/P1. FR-### ids continue from the prior maximum (71). All items are `proposed` and await
  human triage; nothing here has been implemented.
---

# Forensic Review Backlog - revision 53

*Proposed items. `risk` = plausible future adverse outcome not yet observed · `issue` = verified present
defect/governance gap · `todo` = improvement that is not itself a defect. Priorities: **P0** blocker · **P1**
high-likelihood correctness/security/reliability/migration · **P2** material debt · **P3** localized/low-impact.
FR ids continue across reviews (prior max FR-071).*

## Phase summary

| Phase | Theme | Items |
|---|---|---|
| 1 — Proof portability | Make the local front-door proof match CI in a clean worktree | FR-069 |
| 2 — Documentation currency | Keep the recovered architecture and portal true to the code | FR-072, FR-073 |
| 3 — Coverage & hardening | Close test gaps on build utilities; harden the regen path; tidy the ledger tool | FR-074, FR-075, FR-071 |

## Carry-forward status (from rev49)

| id | rev49 disposition | rev53 status | evidence |
|---|---|---|---|
| **FR-069** | issue P1 | **still open** (re-verified) | Hid `node_modules`; gate-4 `node --test` → `browser_benchmark.test.js` fail 1 (requires `./benchmark_docs_explorer` → `playwright`). Re-scoped P2 (bounded to local dev proof; CI runs `npm ci`). |
| **FR-070** | issue P2 | **RESOLVED** | Ran `sync-pack.ps1`; worktree clean — no CRLF-dirty `.github/agents` files at rev53. |
| **FR-071** | todo P3 | **still open** | `cmd_suggest` (`audit-log.py:594`) has no self-report guard. |

---

## FR-069 — issue — P2 — `verify-bundle.ps1` is not self-contained in a clean worktree (gate 4 needs `node_modules`)
- **Status:** proposed (carry-forward from rev49)
- **Location:** `tools/verify-bundle.ps1` (gate 4) · `tests/docs_explorer/browser_benchmark.test.js:19` → `tests/docs_explorer/benchmark_docs_explorer.js` (`require("playwright")`)
- **Evidence (Verified):** with `node_modules` removed and node present, gate 4's `node --test` set fails 1 test (`browser_benchmark.test.js`) with a module-not-found on `playwright`. `verify-bundle.ps1` does not run `npm ci`; its skip guard only checks for node's presence, not `node_modules`. CI is unaffected (`pack-consistency.yml` runs `npm ci` first).
- **Violated standard:** `ci-and-test-efficiency.md` (the local proof should mirror the gate it claims to mirror); `end-to-end-integrity.md` E11 (prove the real surface).
- **Consequence:** a contributor running the documented local proof on a fresh clone gets a spurious gate-4 failure and may distrust the gate or their change; the front-door proof silently diverges from CI.
- **Disconfirming check attempted:** confirmed the failing require chain resolves to `playwright` (a `node_modules` package), not a local file.
- **Recommended remediation:** either (a) run `npm ci` inside `verify-bundle.ps1` before gate 4 (skipping loudly if `npm`/network absent), or (b) split gate 4 into a node-builtin-only subset (self-contained) and a `node_modules`-dependent subset that skips loudly when `node_modules` is absent.
- **Acceptance criteria (falsifiable):** on a clean checkout with node present and `node_modules` absent, `verify-bundle.ps1` gate 4 either restores deps and passes, or reports SKIP (not FAIL) for the `node_modules`-dependent test, and never a spurious FAIL.
- **Validation:** reproduce the clean-worktree run (remove `node_modules`, run the gate); expect PASS or loud SKIP.
- **Dependencies:** none. **Owner:** @timianmalloo. **Next skill:** `/investigate` then `/implement`.

## FR-072 — issue — P3 — `docs/architecture.md` currency was stale
- **Status:** **resolved in this review** (recorded for traceability)
- **Location:** `docs/architecture.md` L16, L47, L61
- **Evidence (Verified):** claimed "pack revision 49", "the 22 skills", "118 valid artifacts" while the repo is at revision 53, 24 skills, 128 graph nodes.
- **Violated standard:** `knowledge-visualization.md` V13 (freshness); Documentation Steward truth-to-code.
- **Consequence:** an adopter or agent reading the architecture of record acts on stale counts (agents act confidently on stale docs).
- **Remediation applied:** refreshed the three currency markers to rev53 / 24 skills / 128 nodes, confidence-labelled.
- **Acceptance criteria:** `architecture.md` contains no `revision 49` / `22 skills` / `118 valid` references (verified clean).
- **Follow-up todo:** wire a currency assertion into `check-consistency.py` (assert architecture.md's stated revision equals `INSTALL.md` revision) so this cannot re-stale silently — same class as the forensic-review currency check. **Next skill:** `/implement`.

## FR-073 — todo — P3 — the two newest skills (`also`, `code-hygiene`) lack portal editorial metadata
- **Status:** proposed
- **Location:** portal build (`tools/build-docs-portal.py` → `docs/portal/portal-data.js`); skill sources `pack/commands/{also,code-hygiene}/SKILL.md`
- **Evidence (Verified):** `sync-pack.ps1` warns twice: `note: skills without editorial metadata: also, code-hygiene`.
- **Violated standard:** V10 Discoverability Mandate (a capability fully integrated into its surfaces).
- **Consequence:** the Docs Explorer / portal presents the two skills without the editorial description the others carry — a discoverability gap, not a functional one.
- **Disconfirming check:** confirmed both skills are otherwise present (SKILL.md, generated `.claude`/`.github` surfaces, eval cases).
- **Recommended remediation:** add the editorial metadata entries these two skills need for the portal generator.
- **Acceptance criteria:** `sync-pack.ps1` emits no "skills without editorial metadata" note.
- **Validation:** re-run `sync-pack.ps1`; expect no warning. **Owner:** @timianmalloo. **Next skill:** `/document`.

## FR-074 — todo — P3 — five `tools/` build/scaffold scripts have no automated tests
- **Status:** proposed
- **Location:** `tools/new-capability.py`, `tools/aiforward.py`, `tools/build-docs-portal.py`, `tools/build-web-index.py`, `tools/build-pages-bundle.py`
- **Evidence (Verified):** `git grep` of `tests/` for each module token returns 0. (Contrast: `pack-doctor`, `prompt-log`, `dream`, `apply-learnings`, `foundation-check`, `check-consistency` **are** covered.)
- **Violated standard:** Testing Strategy (proof for load-bearing behavior).
- **Consequence:** the build-* outputs are indirectly gated by parity checks (gate 1), which mitigates them; but `new-capability.py` — the `/extendaibundle` scaffolder — is neither unit-tested nor output-gated, so a regression in it surfaces only when a contributor scaffolds a capability.
- **Disconfirming check:** confirmed the build-* outputs (`web/pack-index.js`, `portal-data.js`) are validated by gate 1 parity — so those are partially covered; `new-capability.py` is the genuine gap.
- **Recommended remediation:** add a smoke/characterization test for `new-capability.py` (`--dry-run` produces the expected plan; a scaffold round-trips schema-valid frontmatter). Optionally add golden-output tests for the build-* scripts.
- **Acceptance criteria:** `new-capability.py` has at least one test observed failing on a deliberately broken template, then green. **Owner:** @timianmalloo. **Next skill:** `/implement`.

## FR-075 — risk — P3 — `coord-core.py` runs a config-derived regen command with `shell=True`
- **Status:** proposed
- **Location:** `pack/scripts/coord-core.py:1902` (`subprocess.run(command, cwd=str(repo), shell=True, ...)`, `command = regen_command(root, path)`)
- **Evidence (Verified):** `shell=True` with a command string derived from repo-local regeneration config.
- **Violated standard:** BoK Part VIII (unsafe boundary handling); `agent-body-of-knowledge.md` VII.4 (establish subprocess contract, prefer arg-lists).
- **Consequence:** shell interpretation of a config-derived string is a shell-injection surface if that config is ever populated from untrusted input. Current trust boundary is the repo's own regen config (trusted), so exposure is low — a hardening item, not an exploitable path.
- **Disconfirming check:** traced `command` to `regen_command(root, path)` (repo-local config), not to user/network input — hence `risk`, not `issue`, and P3.
- **Recommended remediation:** pass an argument list with `shell=False` where the regen command can be tokenized; where a shell is genuinely required, document why and validate the command source.
- **Acceptance criteria:** the regen path no longer uses `shell=True`, or carries a recorded deviation naming the trusted source. **Owner:** @timianmalloo. **Next skill:** `/design-slice` then `/implement`.

## FR-071 — todo — P3 — `audit-log.py suggest` self-reports the commit that records its own closeout
- **Status:** proposed (carry-forward from rev49)
- **Location:** `pack/scripts/audit-log.py:594` (`cmd_suggest`)
- **Evidence (Inferred):** `cmd_suggest` discerns unlogged meaningful changes from recent commits/ADRs; no guard was found excluding the closeout commit that logs the suggestion run itself, so it can recommend logging a change it is in the act of recording.
- **Consequence:** a recurring false-positive in the decision-ledger triage; cosmetic, self-correcting.
- **Recommended remediation:** exclude the current HEAD/closeout commit from `suggest`'s candidate set, or de-duplicate against the just-written entry.
- **Acceptance criteria:** `suggest` does not list the change that records its own run. **Owner:** @timianmalloo. **Next skill:** `/investigate`.

---

## Standing debt (referenced, not itemized)

`docs/lessons/defect-classes.md` records **8 controlled · 8 partially-controlled · 21 uncontrolled** classes.
The 21 uncontrolled are the dominant verification/maintainability debt. This review does **not** duplicate them
as FR items (they are already tracked with a control ladder); it recommends, as the next strategic investment,
converting the highest-frequency uncontrolled families — the **DM-*** (data-model) and **E2E-*** (end-to-end
integrity) classes — into automated controls per `continuous-improvement.md` CI6. Route via `/extendaibundle`.
