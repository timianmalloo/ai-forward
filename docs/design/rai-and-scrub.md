---
id: design-rai-and-scrub
title: "Design — RAI policy + PII/secret scrub (suggestion 4)"
type: design
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [responsible-ai, privacy, pii, secrets, governance]
links:
  - { to: kb-pack-evolution, rel: implements }
review-by: "2026-12-11"
summary: >-
  A committed Responsible-AI policy knowledge doc mapping Microsoft RAI principles + NIST AI RMF
  functions to the pack's EXISTING personas/templates, plus a stdlib regex scrub.py first-pass that
  redacts obvious PII/secrets from Markdown — explicitly labeled not-a-substitute for gitleaks/Presidio.
---

# Design: RAI policy + PII/secret scrub (suggestion 4)

- **Status:** Accepted
- **Spec / architecture:** `docs/knowledge/pack-evolution/` · `docs/architecture.md`
- **Delivery phase / vertical slice:** Pack-evolution slice 4. Two artifacts: a knowledge doc (policy) + a deployable script (scrub).
- **Author(s) / date:** Privacy & Data Governance + Security & Identity + Domain Researcher, 2026-06-14

## Responsibility
Two complementary deliverables (knowledge base headline #5 + #6):
1. **RAI policy** — a single committed Markdown knowledge doc (`responsible-ai-policy.md`) that states AI-Forward's Responsible-AI **stance**, mapping **Microsoft RAI principles** (fairness, reliability & safety, privacy & security, inclusiveness, transparency, accountability) and **NIST AI RMF functions** (Govern/Map/Measure/Manage) **onto the pack's existing enforcement** — the Privacy & Security personas, the threat-model/privacy-review templates, `engineering-governance.md` §3–5, and the human-in-the-loop gates. It **invents no new control**; it names the stance and points at what already enforces it (avoiding "RAI theater" — knowledge base failure mode).
2. **PII/secret scrub** — a stdlib regex `scrub.py` that redacts obvious PII (emails) and common secret shapes (token prefixes, high-entropy-looking keys) from Markdown, with `--check` (report, nonzero on hit) and `--write` (redact in place). It is the on-brand analogue of Squad's `scrub-emails`, **explicitly labeled a first-pass, not CI-grade**, and points at gitleaks/Presidio for real enforcement.

Explicitly **not**: a vendored Presidio/gitleaks dependency; a guarantee of completeness; a history-rewriter (it redacts going forward — points at `git-filter-repo`/BFG for purging).

## Contracts
- **RAI doc exposed:** a knowledge doc, deployed both ways (Claude `.claude/knowledge/` + Copilot `.github/instructions/`), referenced from `engineering-governance.md` so the governance checklist surfaces it. Structure: Stance → Principles table (MS principle → our enforcing persona/template/gate) → Lifecycle table (NIST function → our practice) → Human-oversight statement → Incident/redress pointer → Scope & limits.
- **scrub exposed:** `python scrub.py [paths...] [--check|--write] [--json]`. Default `--check`: prints `path:line: <category> redacted-preview`, exit 1 if any finding, 0 if clean. `--write`: replaces matches with `[REDACTED:<category>]` in place, prints a summary, exit 0. `--json` for CI.
- **scrub consumed:** stdlib `re`, `pathlib`, `argparse` only. *(Verified — stdlib-only convention.)* Patterns: RFC-5322-lite email; common secret prefixes (`ghp_`, `github_pat_`, `xox[baprs]-`, `sk-`, `AKIA[0-9A-Z]{16}`, `AIza[0-9A-Za-z_\-]{35}`, `-----BEGIN … PRIVATE KEY-----`); generic `[A-Za-z0-9_\-]{32,}` gated behind an entropy/`--aggressive` flag to control false positives.

## Patterns
- **Policy-as-map** (RAI doc) — the doc is a *crosswalk*, not a re-statement: each principle row links to the existing artifact that enforces it. Named `# Pattern: Crosswalk/traceability map`.
- **Linter/redactor** (scrub) — the detect-or-fix CLI shape (`--check`/`--write`) shared by formatters and secret scanners. Named `# Pattern: Lint-or-fix CLI`.
- **Pattern registry** (scrub) — a list of `(category, compiled_regex)`; rejected: an NLP recognizer (Presidio) — correct but a dependency the pack forbids; the regex registry is the deliberate, labeled trade-off.

## Data shapes
scrub finding: `{path, line, category, preview}` (preview is the **redacted** match, never the raw secret). `--json`: `{"findings":[...], "summary":{"emails":n,"secrets":n}, "scanned":n}`.

## Error & concurrency model
Read-only in `--check`; `--write` rewrites files in place (atomic per file: write to temp + replace). Idempotent — re-running `--write` on already-redacted text is a no-op (the `[REDACTED:…]` placeholder doesn't match the patterns). No concurrency.

## Failure-mode analysis

| Failure mode | From which choice | Disposition | How addressed | Detection | Test |
|---|---|---|---|---|---|
| false negative (misses PII/secret) | regex (not NLP) | accept + transfer | **accepted** with rationale (stdlib-only); label loudly; **transfer** real enforcement to gitleaks/Presidio in CI (named in the doc) | n/a (inherent) | n/a — documented limit |
| false positive (redacts a non-secret) | broad generic pattern | mitigate | generic 32+ pattern is behind `--aggressive`; default targets known prefixes + emails | `--check` preview | `scrub_no_falsepos_on_hash_default` |
| `--write` corrupts a file | in-place rewrite | prevent | temp-file + atomic replace; redaction is a pure string sub | file intact | `scrub_write_preserves_nonmatching` |
| leaks the secret in its own output | preview line | prevent | preview shows the **redacted** form only | output scan | `scrub_check_output_has_no_raw_secret` |
| re-redaction churn | idempotency | prevent | placeholder doesn't re-match | second run no-op | `scrub_write_idempotent` |
| binary/huge file | path glob | mitigate | skip non-text/`.md`-only by default; size guard | skipped count | `scrub_skips_binary` |

## Adversarial analysis (STRIDE-lite)
**Trust boundary: the scrub reads files that may contain secrets/PII** (its whole purpose). Walk:
| Boundary | STRIDE | Disposition | Control | Negative test |
|---|---|---|---|---|
| file content → scrub | **I** (the scrub's own output leaks the secret it found) | mitigate | output prints only the **redacted** form; never the raw match | `scrub_check_output_has_no_raw_secret` |
| file content → scrub | **T** (`--write` damages content beyond the match) | mitigate | atomic temp+replace; sub only the matched span | `scrub_write_preserves_nonmatching` |
| invocation args | **E** (path traversal to write outside repo) | mitigate | resolve + confine to provided paths; argv-list, no `shell=True`; default scope is `docs/`+`pack/` Markdown | `scrub_confined_to_given_paths` |
| RAI doc | **R** (repudiation: no record of the stance) | mitigate | the committed RAI doc *is* the attributable record; linked from governance | n/a (artifact existence) |
Security & Identity hard veto cleared: no raw secret is ever emitted; `--write` is atomic and span-scoped; no shell interpolation.

## Privacy analysis (LINDDUN-lite)
**The scrub is itself a privacy control.** Findings on the *act of scanning*: **D**etectability/**I**dentifiability — the scrub *reads* content that may identify a person; disposition **mitigate** (read-only in `--check`; redacts in `--write`; never transmits — purely local). **N**on-compliance — the scrub *supports* compliance (data minimization, breach prevention). Data categories handled: emails (direct identifier), secrets (not personal but sensitive). Retention: none — the scrub holds nothing; **rights path**: redaction is the erasure mechanism for the obvious cases, with `git-filter-repo` (named) for history. The **RAI doc's** privacy section maps to the existing Privacy persona + privacy-review template (no new processing). Residual risk: regex recall (accepted, labeled).

## UI & interaction design
**Medium:** CLI (scrub) + Markdown doc (policy). **scrub key screen:**
```
scrub — PII/secret first-pass (NOT a substitute for gitleaks/Presidio in CI)

  docs/project-memory.md:42  email     a••••@example.com → [REDACTED:email]
  pack/notes/x.md:7          secret    ghp_•••• → [REDACTED:secret]

  2 findings in 1 file · run with --write to redact · CI: use gitleaks + Presidio
```
**States:** clean (exit 0, "no findings") · findings (`--check` exit 1, list) · written (`--write` exit 0, summary) · skipped (binary/large). **Copy (real):** the banner's NOT-a-substitute line is load-bearing (honesty) and appears on every run. **Accessibility:** category in the **word**, redacted preview never colour-only; `--json` for machines. **Perf:** linear scan, sub-second on the docs tree.

## Telemetry
The exit code + finding lines + `--json` are the signal (a linter). No service telemetry.

## Test plan
Triggers: **T2** (parser/validator over wide input — the regex registry) → **D2** property-ish (round-trip: redact then re-scan finds nothing; idempotency) + example tests per category; **T8** (the scrub is a security control) → negative security tests (no-raw-secret-in-output, path-confinement); **D0** throughout. Eval case `rai-and-scrub`: (a) the RAI doc exists, is wrapped for Copilot, and `engineering-governance` references it; (b) `scrub.py --check` on a fixture with an email + a `ghp_` token exits 1 and its output contains `[REDACTED` and **not** the raw token; (c) `--write` redacts and a second `--check` exits 0 (idempotent + clean).

## Conformance notes
Stdlib-only. **Counts impact (final tally for the whole pack-evolution batch):** `scrub.py` + `pack-doctor.py` take `pack/scripts` 2→4; the RAI doc + the memory doc (design 3) take knowledge_docs 18→20; the memory template takes templates 15→16. INSTALL `counts` and every prose count must reflect the final numbers — `check-consistency.py` enforces it; `verify-bundle.ps1` proves it. The RAI doc is **not** a FOUNDATION-manifest doc, so it *is* Copilot-wrapped (applyTo "**").

## Flagged risks & residual unknowns
- Regex recall (knowledge base load-bearing Flagged) — **accepted** and labeled on every run; real enforcement transferred to gitleaks/Presidio in CI (named in the RAI doc). This is the honest limit, not a hidden gap.

## Status & next action
| | |
|---|---|
| **Completed** | RAI policy + scrub design — **all four designs done and implemented in revision 8** (`knowledge/responsible-ai-policy.md` + `pack/scripts/scrub.py`; commit 2fa8bce) |
| **Remaining** | none — shipped via revision 8; `BUNDLE CONSISTENT` (16 eval cases, counts reconcile, foundation clean, graph valid+fresh) |
| **Best next action** | none outstanding |

## Gate record
`GATE design · 2026-06-14 · Privacy & Data Governance + Security & Identity + Test Architect · criteria met: RAI doc maps to existing enforcement (no theater), scrub is a labeled first-pass, no raw secret emitted, path-confined, idempotent, counts impact tallied · verdict: PASS · vetoes→resolution: Security confirmed no-raw-secret + atomic write + no shell; Privacy confirmed the scrub is a control + the accept-with-rationale on recall; Test Architect confirmed the security negative tests · author did not self-clear`

---
**Handoff:** → `/implement` (via `/extendaibundle`).
