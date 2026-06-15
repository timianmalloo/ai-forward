---
id: threat-model
title: "Threat Model"
type: threat-model
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [security, threat-model]
links:
  - { to: architecture, rel: documents }
  - { to: design-aiforward-cli, rel: documents }
  - { to: design-pack-doctor, rel: documents }
  - { to: design-project-memory, rel: documents }
  - { to: design-rai-and-scrub, rel: documents }
review-by: "2026-12-11"
review-suggested: []
summary: >-
  Repo-level security posture for the pack-evolution tooling: the only real trust boundary is the
  scrub reading files that may contain secrets/PII; the CLI, doctor, and memory ledger are local,
  read-mostly, no-network components with no privilege boundary.
---

# Threat Model

*The repo-level rollup of every component's adversarial analysis (design SKILL Stage 3, STRIDE-lite). The per-boundary register below is **generated** — refresh it with the script bundle, never by hand:*

```bash
python3 docs/ai-forward-pack/scripts/docs-graph.py rollup --heading "Adversarial analysis (STRIDE-lite)" --type design
```

## 1. System trust-boundary map

The pack-evolution capabilities are **local developer/CI tooling** — no network, no service, no privilege escalation. The trust boundaries that matter:

- **scrub ← file content** (the one real boundary): `scrub.py` reads Markdown that may contain secrets/PII. Threats: leaking the found secret in its own output (I), damaging content on `--write` (T), path-traversal writes (E). All mitigated (see register).
- **CLI / doctor ← argv + pack-internal scripts**: no untrusted input (developer's own shell); child processes invoked argv-list, no `shell=True`; read-mostly. No boundary in the security sense.
- **project-memory ← free-text entries**: information-disclosure risk (PII into git history) — mitigated by authoring guidance + the scrub, transferred to CI secret-scanning.

## 2. Generated register (STRIDE-lite, rolled up from the designs)

<!-- BEGIN GENERATED: docs-graph.py rollup -->
<!-- run: python3 docs/ai-forward-pack/scripts/docs-graph.py rollup --heading "Adversarial analysis (STRIDE-lite)" --type design -->
| source | Boundary | STRIDE | Disposition | Control | Negative test |
|---|---|---|---|---|---|
| [design-rai-and-scrub](design/rai-and-scrub.md) | file content → scrub | **I** (the scrub's own output leaks the secret it found) | mitigate | output prints only the **redacted** form; never the raw match | `scrub_check_output_has_no_raw_secret` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | file content → scrub | **T** (`--write` damages content beyond the match) | mitigate | atomic temp+replace; sub only the matched span | `scrub_write_preserves_nonmatching` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | invocation args | **E** (path traversal to write outside repo) | mitigate | resolve + confine to provided paths; argv-list, no `shell=True`; default scope is `docs/`+`pack/` Markdown | `scrub_confined_to_given_paths` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | RAI doc | **R** (repudiation: no record of the stance) | mitigate | the committed RAI doc *is* the attributable record; linked from governance | n/a (artifact existence) |

<!-- rolled up from 1 artifact(s) by docs-graph.py rollup on 2026-06-14 -->
<!-- END GENERATED -->

## 3. Accepted-risk register (maintained by hand)

| Accepted risk | Component | Rationale | Residual |
|---|---|---|---|
| Regex scrub misses some PII/secrets (false negatives) | rai-and-scrub | stdlib-only constraint; NLP/entropy tools are dependencies the pack forbids | Real enforcement transferred to gitleaks/Presidio in CI (named in the RAI policy) |
| CLI degrades if `pwsh` absent | aiforward-cli | PowerShell is the canonical sync engine; not all machines have it | Detect-and-print-manual-command; no silent failure |
