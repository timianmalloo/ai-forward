---
id: hygiene-remediation-plan
title: "Code-hygiene remediation plan — SIM115 (resource lifecycle)"
type: doc
status: accepted
owner: "@timianmalloo"
tags: [hygiene, remediation, resource-lifecycle, SIM115]
links:
  - { to: hygiene-backlog, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
review-by: "2026-11-30"
summary: >-
  TDD-guarded, git-labelled remediation of the 26 SIM115 (open()-without-context-manager)
  findings from the hygiene backlog. 25 are behaviour-preserving `with open(...)` refactors;
  1 (check-consistency.py:827, a NamedTemporaryFile(delete=False) consumed by a subprocess by
  path) is accept-with-rationale. Proven green-to-green against the 360-test suite + verify-bundle
  gate; fixes land in pack/ source and are regenerated + gated.
---

# Remediation plan — SIM115 (resource lifecycle: `open()` without a context manager)

*Class from `docs/hygiene/backlog.md` (class 4). Guideline: `agent-body-of-knowledge.md` VII.3
(context managers for resources). Scope requested: `SIM115`.*

## Approval note
The user explicitly invoked `/code-hygiene fix SIM115` — a single, narrow, low-risk class. Per
autopilot ("decide; don't ask") I treat that explicit scoped invocation as approval of this phase,
and execute it. The safety the Stage-7 stop protects is delivered by the execution discipline
below: every change is behaviour-preserving, proven green-to-green, and independently revertible.

## Source-of-truth (from grounding)
Fixes land in **`pack/scripts/*.py`** and **`tools/*.py`** (hand-authored source). The
`docs/ai-forward-pack/scripts/*.py` copies are **generated** by `tools/sync-pack.ps1` and are
committed *with* the source (Stage 6.8). Test command: `python -m unittest discover
tests/docs_explorer` (360 tests, baseline OK). Gate: `tools/verify-bundle.ps1` (9 gates).

## Dispositions

| # | file:line | pattern | disposition | transform |
|---|---|---|---|---|
| 1 | apply-learnings.py:46 | `for line in open(p):` | refactor | wrap loop in `with open(p) as f:` |
| 2 | apply-learnings.py:83 | `txt = open(p).read()` | refactor | `with open(p) as f: txt = f.read()` |
| 3 | apply-learnings.py:263 | `json.loads(open(p).read())` | refactor | `with open(p) as f: manifest = json.load(f)` |
| 4 | design-lint.py:82 | `text = open(p).read()` | refactor | `with … as f: text = f.read()` |
| 5 | dream.py:107 | `txt = open(p).read()` | refactor | `with … as f: txt = f.read()` |
| 6 | dream.py:448 | `json.load(open(p))` | refactor | `with … as f: decisions = json.load(f)` |
| 7 | dream.py:460 | `json.load(open(p))` | refactor | `with … as f: dream = json.load(f)` |
| 8 | dream.py:534 | `json.load(open(p))` | refactor | `with … as f: dj = json.load(f)` |
| 9–15 | graphify-setup.py:165,228,275,341,491,566,594 | reads / conditional reads / `== text` | refactor | `with` wrap; conditional-expr sites restructured to explicit `if os.path.exists` |
| 16–18 | obsidian-setup.py:153,173,602 | `== text` / read / conditional read | refactor | `with` wrap / restructure |
| 19–21 | new-capability.py:44,51,63 | 2× `open(p,"w").write(t)`, 1× read | refactor | `with … as f: f.write(t)` / `f.read()` |
| 22–23 | foundation-check.py:34,40 | `open("rb").read().decode`, `for ln in open(p):` | refactor | `with` wrap (binary read + loop) |
| 24 | check-consistency.py:819 | `html = open(p).read()` | refactor | `with … as f: html = f.read()` |
| **25** | **check-consistency.py:827** | `NamedTemporaryFile(delete=False)` → subprocess by path | **accept-with-rationale** | `# noqa: SIM115` + rationale: the handle is deliberately closed-not-deleted so a separate `node --check` process can open it by path (required on Windows), then `os.unlink`'d in `finally`. `with` would break the cross-process read. |
| 26 | scrub.py:114 | `text = open(p).read()` | refactor | `with … as f: text = f.read()` |

## Test strategy (the non-breaking proof)
- **Nature:** pure behaviour-preserving refactor — `open→with open` reads/writes identical bytes;
  the only change is the handle closes at block end rather than at GC. No observable output changes.
- **Coverage:** 8 of 9 files are exercised by the 360-test suite (`test_deployed_scripts.py`,
  `test_federation_scripts.py`, `test_check_consistency.py`, `test_dream_pack_o.py`, …) →
  **characterize-first**: baseline suite green (360 OK), suite green again after = green-to-green.
- **`new-capability.py`** has no test → smoke proof: `py_compile` + `--help` output identical
  before/after + textbook mechanical equivalence.
- **Completeness:** `ruff --select SIM115 pack/scripts tools` drops 26 → 1 (the accepted noqa).
- **Gate:** `tools/verify-bundle.ps1` green (9 gates), after `sync-pack.ps1` regenerates the copies.

## Commit contract (git-remediation)
One atomic **single-class** commit (Stage 6.4): subject
`chore(hygiene): use context managers for file I/O [HYG]`, trailers `Hygiene-Class: HYG-resource-lifecycle`
· `Hygiene-Item: backlog-class-4-SIM115` · `Hygiene-Scope: pack/scripts,tools`. Source + regenerated
copies committed together. Rollback: `git revert <sha>` undoes the whole class; `git log --grep
'Hygiene-Item: backlog-class-4-SIM115'` finds it. (Class-granularity revert is acceptable — the 26
edits are mechanically identical and low-risk.) A red suite reverts, never forces.

## Floors (L4) — untouched
No validation, error handling, security control, or fail-closed default is removed. The scrub.py
secret/PII regexes are not in scope. The accepted noqa (item 25) preserves a deliberate, correct
resource pattern rather than degrading it.

---

## Execution results (2026-08-30) — DONE

- **Applied:** 25 `with open(...)` refactors across 9 source files + 1 `# noqa: SIM115` with rationale
  (check-consistency.py:827). Every edit landed in **source** (`pack/scripts/*`, `tools/*`); the 7
  `docs/ai-forward-pack/scripts/*` generated copies were regenerated by `tools/sync-pack.ps1`.
- **Completeness:** `ruff --select SIM115 pack/scripts tools` → **All checks passed** (26 → 0); RUF100
  confirms the one `noqa` is used, not stale.
- **Compile:** `py_compile` OK on all 9 files.
- **Green-to-green:** baseline suite **360 tests OK** → post-change gate 3 (python test suite) **PASS**;
  full `verify-bundle.ps1` = **9/9 gates PASS** on the committed tree.
- **Smoke (untested file):** `new-capability.py --help` byte-identical before/after.
- **Commit:** single atomic single-class commit, `Hygiene-Class: HYG-resource-lifecycle` ·
  `Hygiene-Item: backlog-class-4-SIM115`. Rollback: `git revert <sha>`.
- **Re-measured aggregate:** clear violations 103 → 77 (~0.63% → ~0.52%); Medium-or-higher severity 26 → **0**.
