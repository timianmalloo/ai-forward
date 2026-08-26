---
id: forensic-review-rev48-proof
title: "Proof Pack — Forensic Review, revision 48"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [proof-pack, forensic-review, evidence, ci]
links:
  - { to: forensic-review-rev48, rel: tested-by }
  - { to: forensic-review-rev48-backlog, rel: relates-to }
review-by: "2026-11-24"
review-suggested: []
summary: >-
  Evidence record for the revision-48 forensic review. One row per correctness claim, each
  with the exact command, its observed exit code, the oracle that distinguishes pass from
  fail, and whether a red state was observed. Added after an external Test Architect pass
  blocked the review for recording a self-cleared PASS with no Proof Pack behind it.
---

# Proof Pack — Forensic Review, revision 48

**Why this exists.** The first submission of `forensic-review-rev48` recorded a Test Architect **PASS** written by the review's own author, with no Proof Pack. An external adversarial pass called that what it is — self-certification (BoK D3) — and blocked. This is the replacement.

## Capture context

| Field | Value |
|---|---|
| Repository | `ai-forward` |
| Target commit | `c27f83d5f4db8a296ced04345e46a543ef1490d4` |
| Branch under review | `main` |
| Review worktree | `C:\Projects\ai-forward-forensicreview-pack-audit`, branch `forensicreview/pack-audit` (WT1) |
| Host | Windows; `python` (not `python3` — the Store-alias trap), `pwsh`, `node v24.18.0` |
| `git status` at capture | `M docs/docs-index.js` + the two new review artifacts only; `portal-data.js` and `web/pack-index.js` restored to HEAD and re-verified |
| Tree caveat | `sync-pack.ps1` rewrites 12 `.github/agents/*.agent.md` with CRLF on every Windows run, so they show dirty in `git status` while `git diff` normalizes them clean. Any "clean tree" claim on this repo must be read with that in mind |

## Claims

| # | Claim | Command | Observed | Oracle (what makes it fail) | Red observed | Confidence |
|---|---|---|---|---|---|---|
| 1 | Gate 1 fails at `c27f83d` with 5 findings | `python tools\check-consistency.py` | exit **1**; 5 findings, verbatim | exits 0 and prints `clean …` when documented counts match the filesystem | **Yes** — this is the red state | Verified |
| 2 | Gate 1 was clean at `e1ec9d0` | same, in a detached probe worktree at `e1ec9d0` | exit **0**, `clean - all documented counts and skill/prompt parity match` | would print findings if the drift predated the commit | Yes (green observed on the older tree) | Verified |
| 3 | Remote CI agrees | `gh run view 32987223699 --log-failed` | same 5 findings, same order; `##[error]Process completed with exit code 1` | a green run, or a different failure set, falsifies it | **Yes** | Verified |
| 4 | The previous commit was green remotely | `gh run list --branch main` | run `32732534879` (`pack-consistency`, `e1ec9d0`) = **success** | a failure there would break the attribution | Yes | Verified |
| 5 | Portal artifact is stale | `python tools\build-docs-portal.py --check` | exit **1**, `DRIFT: docs/portal/portal-data.js is stale` | exits 0 when the committed bytes equal a fresh build | **Yes** | Verified |
| 6 | The portal generator is deterministic (rules out PACK-I) | two consecutive `python tools\build-docs-portal.py`, hashed | `4D9C01E5…` both runs | differing hashes would make this non-determinism, not staleness | n/a — disconfirming check | Verified |
| 7 | Staleness is exactly the post-`derive` node | `git diff -- docs/portal/portal-data.js` | +16 lines = `spec-design-slice-rename` + 2 `relates-to` edges | any other diff content would refute the ordering hypothesis | n/a | Verified |
| 8 | Gate 2 (source↔install drift) fails | `pwsh tools\sync-pack.ps1`; `git diff --quiet -- .claude .github/instructions .github/prompts .github/agents docs web CLAUDE.md AGENTS.md` | exit **1**; names `docs/portal/portal-data.js`, `web/pack-index.js` | exit 0 when a re-sync produces no diff | **Yes** | Verified |
| 8a | *Measurement correction* | first attempt piped through `Select-Object -First 5` | reported `DRIFT_EXIT=0` — **wrong** | `Select-Object -First N` terminates the pipeline and corrupts `$LASTEXITCODE` | — | Recorded as an E14 near-miss: an exit code is not a result. Re-measured with `git diff --quiet` and no pipeline |
| 9 | The aggregate verifier catches both | `pwsh tools\verify-bundle.ps1` | `BUNDLE INCONSISTENT - 2 of 9 gate(s) failed`, exit **1**; gates 1 and 2 FAIL, 3–7 PASS | prints `BUNDLE CONSISTENT` when all gates pass | **Yes** | Verified |
| 10 | The front door never names the verifier | `Select-String -Path CLAUDE.md,AGENTS.md,pack\adapters\managed-blocks\CLAUDE.block.md -Pattern 'verify-bundle\|check-consistency'` | **zero** hits; `sync-pack` 2× in each | any hit falsifies it | n/a | Verified |
| 11 | `README.md` does **not** mention `verify-bundle` | `Select-String -Path README.md -Pattern 'verify-bundle'` | **0** matches | — | — | Verified — **corrects a false claim** in the first draft, which cited `README.md:109` |
| 12 | CTRL-D is unregistered locally | enumerated `^### <ID>` in `docs/lessons/defect-classes.md` | 17 ids: `SHELL-A`, `PACK-A`…`PACK-Q`; no `CTRL-D` | a `CTRL-D` entry falsifies it | n/a | Verified |
| 13 | Pages published from the red commit | `gh run list --branch main` | `32987223694` (`pages`) **success** vs `32987223699` (`pack-consistency`) **failure**, same commit + timestamp | a failed/absent pages run falsifies it | n/a | Verified |
| 14 | `pages.yml` is the only unpinned workflow | `Select-String -Path .github\workflows\*.yml -Pattern 'uses:'` | `pages.yml` 5 bare tags (lines 37, 38, 46, 47, 51); other two fully SHA-pinned | a SHA-pinned `pages.yml`, or a bare tag elsewhere, falsifies it | n/a | Verified |
| 15 | `copilot-instructions.md:48` says 24 vs 38 actual | read line 48; counted `pack/knowledge/*.md` minus `FOUNDATION.md` | `24 knowledge docs` vs **38** | matching numbers falsify it | n/a | Verified — **found by the adversary, missed by the author** |
| 16 | Gate 1 is blind to that prose form | read `tools/check-consistency.py:474-477` | rules cover `skills\|workflows`, `lenses\|personas`, `templates`, `N docs (+FOUNDATION` — **no** `N knowledge docs`, no `N scripts` | a matching rule falsifies it | n/a | Verified |
| 17 | Script/template parity is intact | hashed `pack/scripts` vs `docs/ai-forward-pack/scripts`, and templates | 18/18 and 27/27, **zero** hash mismatches | any mismatch falsifies it | n/a | Verified |
| 18 | Graph is clean with the new artifacts | `python docs\ai-forward-pack\scripts\docs-graph.py validate` | 116 artifacts, 0 defects, 0 suggestions, 0 orphans, no index drift | any defect falsifies it | n/a | Verified |
| 19 | Tests and contracts pass | `unittest discover` (author) and `python -m pytest tests -q` (adversary, CI's form) | 341/1-skipped and 340-passed/1-skipped; node `--test` 31 pass, 1 skipped; explainer proof all-pass | any failure falsifies it | n/a | Verified |
| 20 | `verify-bundle.ps1` still mirrors CI | — | **no command exists** | nothing asserts it; two divergences visible (`pip install pytest`, `python3` vs `python`) | — | **Inferred** — the basis of FR-067 |
| 21 | Gates 3–7 pass *in CI* at `c27f83d` | — | no CI run at this commit reached step 3 | only a green CI run on the fix commit closes it | — | **Inferred** |
| 22 | `main` forbids merge commits | push rejected: `GH006 … Found 1 violation: f935964…` | first-hand, but **not re-runnable** — the push no longer exists | `gh api …/branches/main/protection` would make it Verified | — | **Flagged** — the basis of FR-066 |

## Residual risk

Claims 20, 21 and 22 are **not Verified** and are labelled as such rather than promoted. Claim 8a is recorded as a near-miss because the author's first measurement of gate 2 produced a false green through pipeline truncation — the same E14 error the review reports elsewhere, made by the review itself, caught by re-measuring rather than by luck.

The evidence above establishes the **findings**. It does not establish the **remedies**: no acceptance criterion in the backlog has been executed, and FR-061's and FR-062's criteria were rewritten *because* the adversary showed they could not fail. Their red-first observation is triage work, not review work.
