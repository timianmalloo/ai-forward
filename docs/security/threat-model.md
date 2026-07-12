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
  - { to: design-docs-explorer-grounding-spatial-navigation, rel: documents }
review-by: 2027-01-07
review-suggested: []
summary: >-
  Repo-level security posture for the pack-evolution tooling. The scrub handles potentially
  sensitive file content, while the Docs Explorer crosses committed-Markdown, filesystem,
  browser-rendering, and optional dependency boundaries; the remaining tools are local and
  read-mostly.
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
- **Docs Explorer ← committed Markdown/frontmatter**: malformed or hostile content must
  remain inert in the browser; grounding reads are confined to scanned roots, bounded,
  and source-cited. The Docs Explorer and Audit Explorer execute only local, dependency-free
  browser code; optional 3D presentation never changes graph or grounding semantics.
- **Eval runner ← trusted repository case files**: `cmd-exit` assertions intentionally
  execute case-provided argv under bounded process controls. CI must not execute
  `--exec` or `cmd-exit` from unreviewed fork/PR-supplied cases.
- **Browser test harness ← npm development dependencies**: Playwright is test-only and
  does not ship in the local Explorer runtime. `@playwright/test`, `playwright`, and
  `playwright-core` are pinned to 1.61.1; the lock resolves to `registry.npmjs.org`
  with SHA-512 integrity, records Apache-2.0, and had zero reported audit
  vulnerabilities on 2026-07-11.
- **Reference benchmark workflow -> self-hosted runner**: the manual workflow can execute
  repository code on dedicated infrastructure, so it accepts only the canonical repository's
  protected `main` ref, checks out the exact workflow SHA without persisted credentials,
  requires the protected `docs-context-reference` environment, pins every action by immutable
  SHA, and refuses runners without the dedicated labels and `AIF_EPHEMERAL_RUNNER=1` marker.
  These controls become executable only after this workflow is merged through the protected
  branch.

## 2. Generated register (STRIDE-lite, rolled up from the designs)

<!-- BEGIN GENERATED: docs-graph.py rollup -->
<!-- run: python3 docs/ai-forward-pack/scripts/docs-graph.py rollup --heading "Adversarial analysis (STRIDE-lite)" --type design -->
| source | Boundary | STRIDE | Disposition | Control | Negative test |
|---|---|---|---|---|---|
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Markdown -> browser | **T** tampered frontmatter injects HTML/script-shaped data | mitigate | Validate schema and render metadata, source Markdown, and Mermaid code as literal escaped text. The P1 contract has no Markdown/Mermaid execution step. | Script/HTML fixture renders inert. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | CLI -> filesystem | **T/E** path traversal through artifact path or CLI ID | mitigate | Resolve only scanned canonical paths under approved roots. | `../` and absolute-path misuse tests. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Filesystem path -> opened source | **T/E** a scanned source is replaced by a symlink, reparse point, or different same-size file before/during read | mitigate | Reject links/reparse points, pin regular-file identity across `lstat`/open/`fstat`, use no-follow opens where available, and recheck identity/size/timestamps after the read. Windows has no `O_NOFOLLOW`; its effective control is the identity/reparse pin before and after open. | Symlink, reparse, concurrent mutation, and same-size path-swap fixtures fail closed. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Scanner directory -> traversal | **T/E** an intermediate directory is replaced by a symlink or junction after admission but before `os.walk` descends | accept | Exploitation requires concurrent write access to the repository checkout; leaf reads remain identity-pinned and the race does not cross a privilege boundary. Revisit with descriptor-relative traversal if the scanner accepts less-trusted roots. | Accepted local same-user residual risk; no success-shaped fallback. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Graph -> grounding packet | **R** context provenance cannot be reconstructed | mitigate | Include line ranges, source/chunk SHA-256, paths, traversal paths, and schema version. | Recompute source/chunk hashes and compare. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Scanner -> packet | **I** unintended files enter grounding context | mitigate | Explicit roots/exclusions; no arbitrary path input; packet lists coverage. | Secret-shaped file outside roots never appears. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Index -> layout/parser | **D** dense or malformed graph exhausts resources | mitigate | Preflight/index/spatial limits, bounded traversal/layout, and fallback list. | Large/cyclic/over-limit synthetic fixtures. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Eval case file -> subprocess | **T/E** a case-controlled `cmd-exit` argv executes with the CI identity | accept | Eval cases are trusted, reviewed repository content; bounded execution limits time, memory, output, and process descendants. CI must not execute `--exec` or `cmd-exit` from unreviewed fork/PR-supplied cases. | Hostile IDs/workspaces fail containment; bounded-process fixtures terminate the full process tree. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Spatial 3D -> browser | **T/D/E** pointer/camera path exhausts rendering or exposes hidden actions | mitigate | Native bounded geometry, host-owned actions, explicit limits, pointer release/disposal, Graph fallback. | Exceed limits, force transform/init failure, interrupt pointer capture, repeatedly mount/unmount. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | HTML surfaces -> browser | **T/E** crafted title/path becomes executable or escapes docs root | prevent | Safe regular-file discovery, escaped text, repo-relative links, template exclusions. | Script-shaped title, traversal path, symlink/reparse, and external-path fixtures. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Protected workflow -> self-hosted benchmark runner/OIDC attestation | **S/T/E** a dispatcher, approver, or runner administrator executes unreviewed code or attests forged evidence | mitigate | Canonical protected `main` only, required PR review, exact-SHA credential-free checkout, immutable action pins, protected environment, dedicated one-job ephemeral runner, and attested evidence. | Fork/branch dispatch is skipped; a non-ephemeral runner fails with a stable error code; release validation rejects mismatched evidence. Residual: environment/repository administrators retain bypass or self-approval authority. |
| [design-rai-and-scrub](design/rai-and-scrub.md) | file content → scrub | **I** (the scrub's own output leaks the secret it found) | mitigate | output prints only the **redacted** form; never the raw match | `scrub_check_output_has_no_raw_secret` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | file content → scrub | **T** (`--write` damages content beyond the match) | mitigate | atomic temp+replace; sub only the matched span | `scrub_write_preserves_nonmatching` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | invocation args | **E** (path traversal to write outside repo) | mitigate | resolve + confine to provided paths; argv-list, no `shell=True`; default scope is `docs/`+`pack/` Markdown | `scrub_confined_to_given_paths` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | RAI doc | **R** (repudiation: no record of the stance) | mitigate | the committed RAI doc *is* the attributable record; linked from governance | n/a (artifact existence) |

<!-- rolled up from 2 artifact(s) by docs-graph.py rollup on 2026-07-11 -->
<!-- END GENERATED -->

## 3. Accepted-risk register (maintained by hand)

| Accepted risk | Component | Rationale | Residual |
|---|---|---|---|
| Regex scrub misses some PII/secrets (false negatives) | rai-and-scrub | stdlib-only constraint; NLP/entropy tools are dependencies the pack forbids | Real enforcement transferred to gitleaks/Presidio in CI (named in the RAI policy) |
| CLI degrades if `pwsh` absent | aiforward-cli | PowerShell is the canonical sync engine; not all machines have it | Detect-and-print-manual-command; no silent failure |
| Intermediate docs directory is swapped after admission but before traversal | docs-explorer-grounding-spatial-navigation | Requires concurrent same-user write access to the repository checkout; leaf reads still pin file identity and bytes | No privilege escalation. Revisit with descriptor-relative traversal if less-trusted scan roots are supported |
| Eval case argv executes with the CI identity | docs-explorer-grounding-spatial-navigation | `cmd-exit` exists to assert real command behavior; case files are trusted, reviewed repository content | Bounded process containment limits impact, but cannot make hostile commands safe. Never execute unreviewed external case files. |
| Benchmark environment administrators can bypass protection, and the sole required reviewer can approve their own deployment | docs-context-reference workflow | The workflow is manual, read-only, exact-SHA, protected-main-only, and runs on a dedicated ephemeral host; one-person approval keeps the workflow operable for the current maintainer | If independent two-person authorization becomes required, add a second reviewer, enable self-review prevention, and disable administrator bypass |
