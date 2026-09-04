---
id: forensic-review-rev59
title: "Forensic review — ai-forward at revision 59"
type: doc
status: accepted
owner: "@timianmalloo"
phase: "assessment"
tags: [forensic-review, assessment, governance, rev59]
links:
  - { to: architecture, rel: documents }
  - { to: forensic-review-rev59-backlog, rel: relates-to }
  - { to: forensic-review-rev53, rel: supersedes }
  - { to: defect-classes, rel: relates-to }
review-by: "2027-03-04"
summary: >-
  Forensic assessment of ai-forward at 566d9c5 (pack revision 59). All ten gates green,
  440 tests passing, supply chain clean, publish boundary enforced, workflows least-privilege.
  No P0 or P1. Ten findings (FR-076..FR-085), all governance, consistency or documentation
  debt rather than correctness or security defects — the sharpest being a defect-class register
  whose own stated counts are wrong by an order of magnitude, and a marker linter whose entire
  output is noise from its own test fixtures.
---

# Forensic review — ai-forward at revision 59

## Scope and baseline

| | |
|---|---|
| Commit | `566d9c5c9aea3a99c743e51a8343e58bc8e30b5e` |
| Branch | `main`, **clean worktree** (0 modified files) |
| Pack revision | 59 (`bundle 2026.08.31.1`) |
| Supersedes | `forensic-review-rev53` |
| Findings | **FR-076 … FR-085** (ids continue; the highest prior local id was FR-075) |

**A note on id continuity.** `FR-371` appears in this repo's changelog but belongs to
*TheTerrace's* numbering, quoted in a cross-repo lesson. Continuing from it would have
silently forked this repo's sequence. The highest id actually issued here is FR-075.

### Baseline commands — run before judging, recorded as evidence

| Command | Result |
|---|---|
| `pwsh tools/verify-bundle.ps1` | **10 of 10 gates pass** |
| `python -m pytest tests -q` | **440 passed, 1 skipped**, 166 subtests |
| `node --test tests/docs_explorer/*.test.js` | pass (gate 4) |
| `docs-graph.py validate` | pass — 162 artifacts, 0 problems / stale / flagged / orphans / index drift |
| `docs-graph.py inventory` | clean |
| `python tools/build-pages-bundle.py` | boundary holds — see below |

No baseline failures. Nothing in this report is attributable to a pre-existing red build.

## Recovered system map

This repository is unusual: it is both the **source of the AI-Forward Pack** and a **live
install of it**. `pack/` is canonical; `.claude/`, `.github/{instructions,knowledge,prompts,agents}/`
and `docs/` are generated from it by `tools/sync-pack.ps1`, which also invokes the derivation
tools. The architecture of record is `docs/architecture.md`, verified current in this review.

| Surface | Shape |
|---|---|
| Source | 39 knowledge docs · 24 skills · 23 personas · 28 templates · 20 scripts |
| Public code surface | `pack/scripts/*.py` — 19 modules, **267 public functions**, deployed to consuming repos |
| Repo-local tooling | `tools/` — 8 Python, 4 PowerShell, 3 JS. Deliberately **not** deployed |
| Tests | 28 Python files, 3 Node files |
| CI | 4 workflows, **every action pinned to a 40-char SHA** |
| Dependencies | **zero runtime dependencies.** One devDependency (`@playwright/test`). Stdlib-only policy holds under inspection |

### What was checked and found sound

These were interrogated and produced **no finding**. Recording them matters as much as the
findings: a review that lists only problems misrepresents the system.

- **Publish boundary.** `build-pages-bundle.py` was executed and its output inspected:
  `docs/dreams`, `docs/audit`, `learnings/manifests` and `learnings/plans` are all absent from
  the 483-file bundle, while `learnings/fleet-classes.md` is present as intended. The boundary
  is enforced by execution, not by convention.
- **Workflow permissions.** All four workflows declare least-privilege `contents: read`;
  `pages.yml` adds `pages: write` + `id-token: write` (required), the benchmark adds
  `attestations: write`. No workflow holds more than its job needs.
- **Supply chain.** No unpinned action. No runtime dependency. No non-stdlib import in the
  deployed bundle.
- **Durable-store write ordering.** `dream.py` writes the fleet class *before* the idempotency
  ledger. That is the correct order: a crash between them costs a duplicate (absorbed by the
  de-dup on read) rather than a permanent loss, which ledger-first would have caused.
- **Marker hygiene.** Zero genuine `assume:` / `simplify:` violations in the pack (see FR-077
  for why the linter nonetheless reports ten).
- **Budget estimator sensitivity.** Deliberately stress-tested — see FR-083. The backstop holds
  across the full plausible ratio range.

## Assessment by layer

### Architecture — sound

Dependency direction is single and enforced: source → build → install → consumer, with the
source↔install boundary crossed only by `sync-pack.ps1` and gated by `git diff --exit-code`
(gate 2). No cycles. The one architectural claim that had drifted — that sync does not touch
`docs-index.js` — was corrected in this revision's documentation pass and is now true to code.

The **load-scope tiering** (rev 58) is the significant architectural change since rev 53: the
always-on instruction prefix fell from the whole 184K-token corpus to 13 documents at ~43.7K,
routed by each document's own frontmatter. It is enforced by gate 8 and by a ratchet against a
recorded baseline.

### Design — sound, with governance gaps

The control ladder is applied consistently: most findings from previous revisions closed with a
named test observed failing first. The gaps found here are **not** design defects; they are
places where a stated fact is not checked (FR-076), a control's output is unusable (FR-077), or
a shipped capability is not exercised on its own repo (FR-078).

### Implementation — sound

440 tests pass. The scripts are stdlib-only, defensive at boundaries (the empty-corpus guard,
the taint/scrub pass, the identity-pinned file reads), and consistently degrade to "not
recorded" rather than to a plausible wrong value. The largest implementation-adjacent debt is
documentation coverage (FR-079), not correctness.

### Traceability — mostly intact, one break

Spec → architecture → design → code → test is traceable through the graph (162 artifacts, no
orphans). The break is at the **fleet boundary**: a class promoted from one repo into another
loses its provenance on application (FR-081), so no target can answer "where did this class come
from?".

## Persona verdicts

| Lens | Verdict | Note |
|---|---|---|
| Enterprise Architect | **PASS** | Boundaries and dependency direction hold; the tiering is a genuine improvement |
| Documentation Steward | **PASS with findings** | Bundle is true to code after this revision's corrections; FR-079 coverage debt recorded, not hidden |
| Test Architect | **PASS** | No finding admitted without an executed check; FR-085 raised for absent coverage measurement |
| Security & Identity | **PASS** | Pinned actions, least-privilege workflows, enforced publish boundary, no secrets in tree |
| Data & Persistence | **PASS** | Append-only stores; write ordering interrogated and found correct |
| SRE | **PASS with risk** | FR-082: no required status check means CI cannot block a red push |
| Simplifier | **PASS** | Two candidate findings struck as preference rather than defect (see below) |
| Privacy & Data Governance | **PASS** | Publish boundary verified by execution; no personal data in published surfaces |

**Struck by the Simplifier**, recorded so they are not re-raised: (1) the committed 132 KB
`docs/_site/bundle.html` — a generated artifact, but the repo consistently commits derived
surfaces and drift-gates them, so this is convention, not debt; (2) `append_log` performing a
plain append without `fsync` — single-writer append-only JSONL with a readability gate is
adequate, and atomicity here would be ceremony.

## Readiness verdict

**Healthy.** No P0, no P1. Ten gates green on a clean tree, a passing suite, a clean supply
chain, and an enforced publish boundary. Every finding below is **governance, consistency or
documentation debt** — the kind that accumulates quietly in a repo whose subject *is* discipline,
which is precisely why they are worth naming.

The two that most deserve attention are not the largest: **FR-076** (a governance metric wrong
by an order of magnitude, in the file that governs continuous improvement) and **FR-077** (a
linter whose entire output is noise, which is how a real finding gets missed). Both are cheap to
fix and both currently teach the reader to distrust the instrument.

## Confidence ledger

| Finding | Confidence | Basis |
|---|---|---|
| FR-076 | **Verified** | Parsed the register: 24 classes, 14/8/2 actual against 12/9/22 stated |
| FR-077 | **Verified** | Ran the linter; all 10 findings are in `test_marker_lint.py` |
| FR-078 | **Verified** | `coord-core.py doctor` on this repo |
| FR-079 | **Verified** | `build-api-docs.py` — 267 public functions, 108 documented |
| FR-080 | **Verified** | Measured overlap 0.17 / 0.14 against the 0.6 threshold |
| FR-081 | **Verified** | Zero `Source:** fleet` markers in any target's committed register |
| FR-082 | **Verified** | `gh api …/branches/main/protection` — `required_status_checks` absent |
| FR-083 | **Verified** | Recomputed the always-on total across 4.0–5.2 chars/token |
| FR-084 | **Verified** | Node 20 deprecation annotation on recent runs |
| FR-085 | **Verified** | No coverage tooling in any workflow, script or manifest |

## Residual risk

- The budget gate rests on a **fitted** constant (4.83 chars/token). The ratchet is immune —
  it compares like with like — but the absolute backstop is not. FR-083 records the sensitivity
  analysis; the backstop holds, with less headroom than the headline number suggests.
- **Fleet distribution remains unverifiable end-to-end.** Five target repos currently hold
  uncommitted register changes from this session. Until FR-081 is closed, "did this learning
  land?" cannot be answered from the target.
- This review was produced by the same agent that authored much of the reviewed revision. The
  mitigation applied was to run every claim through an executed check rather than recall, and to
  record the two occasions in recent history where an assertion made without opening the file
  proved wrong. It is a mitigation, not a substitute for an independent reviewer.
