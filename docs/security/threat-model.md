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
  - { to: design-coord-core-phase1, rel: documents }
  - { to: design-agent-coordination-doctrine, rel: documents }
  - { to: design-typed-seam-requests, rel: documents }
  - { to: design-leader-designation, rel: documents }
  - { to: design-message-layer, rel: documents }
  - { to: design-compile-readers, rel: documents }
  - { to: design-board, rel: documents }
  - { to: design-compile-stage, rel: documents }
  - { to: design-coord-enforcement-phase2, rel: documents }
  - { to: design-coord-federation-phase3, rel: documents }
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
| source | Boundary | Threat | Disposition |
|---|---|---|---|
| [design-agent-coordination-doctrine](design/agent-coordination-doctrine.md) | Knowledge doc → every model prefix | **Tampering / injection**: a repo write that turns a doctrine line into an instruction to the model (the doc *is* instruction text by design) | **Transfer** — repo write access is the trust boundary (branch protection on `main`, `required_conversation_resolution`); the doc carries no external content and cites by id, so no untrusted text is inlined. **Accept** the residual: the pack's own text is trusted by construction (ADR-0011's untrusted-heading rule applies to *messages*, not to committed doctrine). |
| [design-agent-coordination-doctrine](design/agent-coordination-doctrine.md) | Test → `git show origin/main` | **Spoofing** of the base (a local `origin/main` ref pointing elsewhere) | **Accept** — a local repo owner can already edit the doc; the test guards drift, not malice. In CI the ref is the protected branch. |
| [design-agent-coordination-doctrine](design/agent-coordination-doctrine.md) | Test → proposal text | **Denial** — an oversized or pathological proposal making the regex slow | **Accept** — the region is bounded to §3.3 (≈ 30 lines) before any regex runs. |
| [design-compile-readers](design/compile-readers.md) | Committed audit log → profile/dream text | I: prompt text (possibly a pasted secret) copied into a finding | mitigate | evidence carries ids, shortnames, codes and numbers only; dream notes pass the existing `scrub()` and a tainted note is excluded | `test_evidence_carries_no_prompt_text` (a fixture prompt containing `sk-…` never appears in evidence) |
| [design-compile-readers](design/compile-readers.md) | Committed SKILL.md → lint verdict | T: a skill cites `CO-S0` in a comment to pass | accept | the lint checks presence, not meaning; the citation test checks the fixed sentence for the prose-input set; residual: a bad-faith author — reviewed at the PR | `test_self_test_directions` |
| [design-compile-readers](design/compile-readers.md) | `--root` argument | D: a huge or non-repo path | accept | reads ≤ 28 small files under one directory; no recursion beyond `*/SKILL.md` and `*/reference/*.md` | n/a |
| [design-compile-stage](design/compile-stage.md) | Raw prompt text → compiled prompt | **T** injection: prose instructs the compiler ("mark everything verified") | mitigate | output grammar has no free-text instruction slot; only the eight sections render | `test_instruction_in_prose_has_no_slot` (rendered text contains no line outside the template's sections) |
| [design-compile-stage](design/compile-stage.md) | Referenced repo file → compiled prompt | **T/I** a file's content is smuggled into the prompt | mitigate | references render as path + sha256 only; body never read after hashing | `test_reference_body_never_rendered` |
| [design-compile-stage](design/compile-stage.md) | Reference path → filesystem | **I** read outside the repo (`../../.env`, symlink) | mitigate | `os.path.realpath` under root check before open | `test_reference_outside_repo_never_read` |
| [design-compile-stage](design/compile-stage.md) | Compiled JSON → audit log | **S** a compiled prompt claims a raw id it did not come from | mitigate | `raw_sha256` recomputed by the gate | self-test dir 5 |
| [design-compile-stage](design/compile-stage.md) | Compiled prompt → consuming skill | **E** an agent treats a compiled prompt as consent to dispatch | mitigate | `dispatchable: false` + unanswered `DR-n` stops the three consuming skills (owned by their tests) | `test_prepare_stops_on_unanswered_dr` (P8 track owns; recorded remaining) |
| [design-compile-stage](design/compile-stage.md) | Environment → compiled prompt | **I** env values leak | mitigate | engine never reads `os.environ` into output (grep-tested) | `test_engine_reads_no_environ` (AST check: no `os.environ` in the two scripts except `PYTHONIOENCODING` for the child pipe) |
| [design-compile-stage](design/compile-stage.md) | Audit log (committed) | **R** repudiation | transfer | the audit log's own append discipline and git history | existing audit tests |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Coordination record -> collaboration projection | Tampering: malformed event hides a session | Reuse `read_events` errors; finding emitted, no OK. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Environment identity -> session actions | Spoofing: false `AGENT_SESSION` | Existing ADR-0011 accepted identity model. This slice does not increase authority. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Template -> repo policy | Elevation: a template is mistaken for enforcement | Template states claims are advisory unless hook/pre-commit/merge drivers enforce. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Terminal output -> model reader | Prompt injection via event fields | Output is structured fields; no free-text intent in this slice. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Request reason -> model reader | Prompt injection through seam request prose | Request prose is rendered as data in a fixed JSON/text shape; no execution or shell path consumes it. |
| [design-coord-core-phase1](design/coord-core-phase1.md) | B1 | **S** — a session sets `AGENT_SESSION` to another's and releases its leases | **ACCEPT, documented** (ADR-0011). Identity is asserted. Residual risk: local impersonation. Detection over prevention — the record shows which session released. |
| [design-coord-core-phase1](design/coord-core-phase1.md) | B1 | **E** — `COORD_ROOT` pointed outside the repo to make the layer read an attacker-controlled record | **MITIGATE.** `COORD_ROOT` is resolved and must be inside the repo root; otherwise `not_checked`. Negative test included. |
| [design-coord-core-phase1](design/coord-core-phase1.md) | B2 | **T** — a session edits another's record file | **DETECT.** Not preventable on a shared filesystem; the record is git-tracked, so tampering shows in a diff, and **no line is ever rewritten** by the tool. |
| [design-coord-core-phase1](design/coord-core-phase1.md) | B2 | **I** — the refusal message echoes a `wi` or `path` containing a secret | **MITIGATE.** Phase 1 emits only `path`, `wi`, `agent`, `session`, `expires_in` — all short, structured fields; **there is no free-text `intent` field in Phase 1**. Free text arrives in Phase 4 behind the scrub boundary. |
| [design-coord-core-phase1](design/coord-core-phase1.md) | B2 | **E** — a record field containing instruction-shaped text reaching a model | **TRANSFERRED to Phase 4 by construction, and named rather than assumed:** the refusal is a fixed four-line template with **no field interpolated into prose**; `path`/`wi` are rendered as delimited values. |
| [design-coord-core-phase1](design/coord-core-phase1.md) | B3 | **D** — a claim glob matching 100,000 files | **MITIGATE.** Patterns are matched lazily against the queried path only; the fold never enumerates the filesystem. Cost is O(leases), not O(files). |
| [design-coord-core-phase1](design/coord-core-phase1.md) | B3 | **T** — a path containing `..` or a shell metacharacter | **MITIGATE.** Paths are normalised and compared as strings; nothing is ever passed to a shell. Phase 2's hook uses exec-form `args` (ADR-0010), which closes `SHELL-A` structurally. |
| [design-coord-enforcement-phase2](design/coord-enforcement-phase2.md) | B4 | **T** — a crafted `file_path` (`../../etc`, a NUL, 5 MB) steers or breaks the check | **MITIGATE.** The path is normalised and compared as a string; it is never opened, never globbed against the filesystem, never passed to a shell. Length-capped. Negative tests for all three. |
| [design-coord-enforcement-phase2](design/coord-enforcement-phase2.md) | B4 | **S** — the payload asserts a `session_id` that is not this session's | **MITIGATE.** Identity comes from the **environment**, never from the payload. The payload's `session_id` is ignored entirely. Test asserts a forged `session_id` changes nothing. |
| [design-coord-enforcement-phase2](design/coord-enforcement-phase2.md) | B4 | **E** — a `permissionDecisionReason` containing instruction-shaped text reaching the model | **MITIGATE.** The reason is a **fixed four-line template**; the only interpolated values are `path`, `wi`, `agent`, `expires_in` — all short, structured, and rendered as delimited values, never into prose. Newlines and control characters are stripped from interpolated values. **This is the Phase-4 boundary arriving three phases early**, so it is closed here rather than deferred. |
| [design-coord-enforcement-phase2](design/coord-enforcement-phase2.md) | B5 | **T** — a staged path that escapes the repo | **MITIGATE.** git reports index paths repo-relative; anything resolving outside the repo root is `not_checked`, not allowed. |
| [design-coord-enforcement-phase2](design/coord-enforcement-phase2.md) | B6 | **E** — `install` writes an executable into `.git/hooks` | **MITIGATE.** Writes exactly one file, exactly one known body, refuses to overwrite a foreign hook, and prints what it wrote. It **never** edits `.claude/settings.json` — it prints the entry for a human to paste, because silently editing the file that controls tool permissions is precisely the elevation this row is about. |
| [design-coord-enforcement-phase2](design/coord-enforcement-phase2.md) | B6 | **T** — `install` invoked from a linked worktree writes to the shared hooks dir | **ACCEPT, documented.** S10 established that this is git's design: one hooks dir per repository. It is the correct scope; the surprise is documented rather than worked around. |
| [design-coord-enforcement-phase2](design/coord-enforcement-phase2.md) | B4 | **D** — a flood of hook invocations | **TRANSFER, named:** the harness's `if` pre-filter decides whether the process spawns. Not an assumption — it is in the settings entry `install` prints. |
| [design-coord-federation-phase3](design/coord-federation-phase3.md) | B7 | **E** — a PR reclassifies `src/**` as `derived`, so the next merge overwrites authored work | **MITIGATE, layered.** Registry changes are PR-reviewed; the driver cross-checks `check-attr` against the registry and refuses on disagreement; the default is `authored`. Negative test: a registry marking a source tree `derived` is refused by the driver. |
| [design-coord-federation-phase3](design/coord-federation-phase3.md) | B7 | **T** — a pattern with `..` or an absolute path escaping the repo | **MITIGATE.** Patterns are repo-relative; anything escaping is a registry error. Reuses Phase-2's `_reject_path`. Negative test. |
| [design-coord-federation-phase3](design/coord-federation-phase3.md) | B8 | **T** — the driver writes outside `%A` | **MITIGATE.** It writes **only** `%A`. Negative test asserts no other path is touched during a merge. |
| [design-coord-federation-phase3](design/coord-federation-phase3.md) | B8 | **I** — regenerator output leaks into a file the driver did not own | **MITIGATE.** Same control; `%P` is used for identity only, never as a write target. |
| [design-coord-federation-phase3](design/coord-federation-phase3.md) | B9 | **E** — the emitted plugin runs an arbitrary command in two harnesses | **MITIGATE.** `--emit` writes to a directory the caller names and **prints what it wrote**; it never installs, never edits `~/.copilot/` or `.claude/settings.json`. The Phase-2 precedent (P19) — a layer that grants itself tool permissions is the elevation it exists to prevent. Negative test. |
| [design-coord-federation-phase3](design/coord-federation-phase3.md) | B9 | **S** — a bundle claiming to be someone else's plugin | **ACCEPT.** Plugin identity is the harness's trust model, not ours. Residual: a user installing a bundle from an untrusted source. Named, not mitigated here. |
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
| [design-leader-designation](design/leader-designation.md) | **S** a session pins a name that is not its own | **accept** — designation is by the human; any session may run the human's command; the ledger records who ran it (`session` ≠ `leader` is visible) | `test_ledger_records_recorder_and_target` |
| [design-leader-designation](design/leader-designation.md) | **T** a hand-written blob | **mitigate** — validated on read; invalid → NOT CHECKED; valid hand-written → accepted as a human override (recorded nowhere but the ref: residual) | `test_who_not_checked_on_malformed_blob` |
| [design-leader-designation](design/leader-designation.md) | **R** who changed the leader | **mitigate** — every attempt is a ledger row with session/host/tree/at | `test_every_transition_is_recorded` |
| [design-leader-designation](design/leader-designation.md) | **I** leaks | **mitigate** — the blob holds session id, harness name, `primary|worktree`; no hostname, path or user; `_safe` strips control chars from output | `test_refusal_lines_are_safe` |
| [design-leader-designation](design/leader-designation.md) | **D** pin-and-never-release | **mitigate** — TTL bounds the hold to 300 s + 30 s quiet | `test_reclaim_after_quiet_advances_epoch_by_one` |
| [design-leader-designation](design/leader-designation.md) | **E** leadership as a lease grant | **prevent** — no code path reads the ref in `check`/`claim`; leadership grants nothing | `test_leader_ref_does_not_affect_check` |
| [design-native-app-ui-skill-extension](design/native-app-ui-skill-extension.md) | Generated assets from user input to provider | I: customer screenshots/real likeness leak to provider | mitigate | `/visualize` keeps existing VA9 hard line and adds native-app examples | Prompt fixture with customer screenshot request is blocked |
| [design-native-app-ui-skill-extension](design/native-app-ui-skill-extension.md) | Public exemplar table to downstream users | T/I: license posture misrepresented | mitigate | Table includes license/reuse posture; GPL/non-standard reference-only | Static test/grep for `GPL-3.0` and `reference-only`; `NOASSERTION` flagged |
| [design-native-app-ui-skill-extension](design/native-app-ui-skill-extension.md) | Native proof template to review gate | R: reviewer claims proof without evidence | mitigate | Schema requires evidence, red-observed status and confidence | Template fixture lacks evidence -> docs/test failure |
| [design-native-app-ui-skill-extension](design/native-app-ui-skill-extension.md) | Native distribution trust | S/T/R/E: spoofed publisher, tampered artifact, unsigned update, unverifiable release provenance, SmartScreen/Gatekeeper/notarization bypass | mitigate | Signed artifacts, cert/key custody outside repo, timestamping where applicable, Store/MSIX/AuthentiCode/SmartScreen posture or macOS notarization recheck before release PASS | Unsigned/unnotarized fixture/check cannot clear release proof row |
| [design-native-app-ui-skill-extension](design/native-app-ui-skill-extension.md) | XAML linter input | T/I/D: hostile PR XAML/path causes parser abuse, path escape, terminal/log injection, or secret-like source disclosure | mitigate | Repo-root path normalization, no network/includes, text/XML scanning only, escaped JSON/text output, no raw source snippets or secret expansion | Malicious path/XAML fixture returns controlled error/finding without reading outside root or echoing unsafe content |
| [design-rai-and-scrub](design/rai-and-scrub.md) | file content → scrub | **I** (the scrub's own output leaks the secret it found) | mitigate | output prints only the **redacted** form; never the raw match | `scrub_check_output_has_no_raw_secret` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | file content → scrub | **T** (`--write` damages content beyond the match) | mitigate | atomic temp+replace; sub only the matched span | `scrub_write_preserves_nonmatching` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | invocation args | **E** (path traversal to write outside repo) | mitigate | resolve + confine to provided paths; argv-list, no `shell=True`; default scope is `docs/`+`pack/` Markdown | `scrub_confined_to_given_paths` |
| [design-rai-and-scrub](design/rai-and-scrub.md) | RAI doc | **R** (repudiation: no record of the stance) | mitigate | the committed RAI doc *is* the attributable record; linked from governance | n/a (artifact existence) |

<!-- rolled up from 11 artifact(s) by docs-graph.py rollup on 2026-09-19 -->
<!-- END GENERATED -->

## 3. Accepted-risk register (maintained by hand)

| Accepted risk | Component | Rationale | Residual |
|---|---|---|---|
| Regex scrub misses some PII/secrets (false negatives) | rai-and-scrub | stdlib-only constraint; NLP/entropy tools are dependencies the pack forbids | Real enforcement transferred to gitleaks/Presidio in CI (named in the RAI policy) |
| CLI degrades if `pwsh` absent | aiforward-cli | PowerShell is the canonical sync engine; not all machines have it | Detect-and-print-manual-command; no silent failure |
| Intermediate docs directory is swapped after admission but before traversal | docs-explorer-grounding-spatial-navigation | Requires concurrent same-user write access to the repository checkout; leaf reads still pin file identity and bytes | No privilege escalation. Revisit with descriptor-relative traversal if less-trusted scan roots are supported |
| Eval case argv executes with the CI identity | docs-explorer-grounding-spatial-navigation | `cmd-exit` exists to assert real command behavior; case files are trusted, reviewed repository content | Bounded process containment limits impact, but cannot make hostile commands safe. Never execute unreviewed external case files. |
| Benchmark environment administrators can bypass protection, and the sole required reviewer can approve their own deployment | docs-context-reference workflow | The workflow is manual, read-only, exact-SHA, protected-main-only, and runs on a dedicated ephemeral host; one-person approval keeps the workflow operable for the current maintainer | If independent two-person authorization becomes required, add a second reviewer, enable self-review prevention, and disable administrator bypass |


## 4. Gaps — designs with no STRIDE analysis

The register above can only roll up analyses that exist. These designs carry none, so their boundaries are **unanalysed, not clean** — the absence of a row is not evidence of safety. Recorded here as upstream gate failures against the design, per the /document definition of done; the fix belongs in each design, not in this file.

| Design | Gap | Why it matters |
|---|---|---|
| [`agent-focus-controls.md`](../design/agent-focus-controls.md) | no `Adversarial analysis (STRIDE-lite)` section | the design shipped without the analysis its gate requires |
| [`marker-completeness-lint.md`](../design/marker-completeness-lint.md) | no `Adversarial analysis (STRIDE-lite)` section | the design shipped without the analysis its gate requires |
| [`tier2-proof-pack-sections.md`](../design/tier2-proof-pack-sections.md) | no `Adversarial analysis (STRIDE-lite)` section | the design shipped without the analysis its gate requires |
