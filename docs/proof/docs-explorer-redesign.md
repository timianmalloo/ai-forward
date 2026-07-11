---
id: proof-docs-explorer-redesign
title: "Docs Explorer Redesign - Proof Pack"
type: proof-pack
status: accepted
owner: "@maintainers"
phase: "implementation"
tags: [docs-explorer, grounding, accessibility, performance, verification]
links:
  - { to: design-docs-explorer-grounding-spatial-navigation, rel: relates-to }
  - { to: adr-0001-grounding-source-corpus-registry, rel: depends-on }
  - { to: design-language-docs-explorer, rel: depends-on }
  - { to: threat-model, rel: relates-to }
  - { to: privacy-review, rel: relates-to }
review-by: 2027-01-07
review-suggested: []
summary: >-
  Accepted implementation evidence for the deterministic, local-first Docs Explorer
  and bounded grounding packet implementation. The P0/P1 contract is covered by
  Python, Node, and three-engine browser suites; phase-attributed benchmark evidence
  separates graph work from process/host overhead. Revision 17 remains intentionally
  unreleased pending pinned-reference performance proof or a human-approved deviation.
---

# Docs Explorer Redesign - Proof Pack

**Status:** Implementation accepted; release blocked. The implementation evidence,
dependency disposition, and independent persona reviews are current. Revision 17 remains
unreleased until the pinned-reference latency budget is proved or explicitly accepted
through the Deviation Protocol.

## Scope proved

This Proof Pack covers the accepted P0/P1 implementation in
`docs/design/docs-explorer-grounding-and-spatial-navigation.md`:

- deterministic Browse, Graph, and context-rooted two-hop Mind-map projections;
- independent selection and exploration context with URL/history restoration;
- keyboard, responsive-route, reduced-motion, contrast, target-size, and relationship-list behavior;
- local-first source inspection with inert rendering, byte ceilings, retries, and stale-response rejection;
- deterministic, bounded grounding packets with stable root-relative identity;
- bounded subprocess use in Pack Doctor and the eval harness.

It does **not** claim completion of the remaining P2/P3 backlog: reference-environment
CLI/browser performance proof, retrieval recall evaluation, deeper browser timing
telemetry, a full A6 golden contract corpus, usage analytics, or 3D experimentation.

## Verification summary

| Surface | Current evidence |
|---|---|
| Python unit/integration | `python -m unittest discover -s tests/docs_explorer -p "test_*.py"` -> 90 tests passed, including the Windows process-tree, append-lock, timing-invariance, and contradiction-resistant release-proof contracts |
| JavaScript core | `node --test tests/docs_explorer/docs_explorer_core.test.js` -> 19 tests passed |
| Browser behavior | `npx playwright test` -> 155 passed, 10 intentional engine-specific skips across Chromium, Firefox, and WebKit |
| Design language | Strict design lint passed with zero warnings |
| Bundle consistency | `tools/verify-bundle.ps1` -> `BUNDLE CONSISTENT` after final synchronization |
| Install health | Pack Doctor normal and `--strict` -> 6 PASS, 0 WARN, 0 FAIL |
| Knowledge graph | `docs-graph.py validate` and `freshness --gate fail` -> 21 artifacts, no problems, stale nodes, flags, or orphans |
| Eval/process deadlines | Process tests prove timeout, output-limit, launch-gate, and child-tree cleanup behavior; the benchmark watchdog self-test terminated its child tree at a two-second deadline with no surviving PIDs |
| Grounding benchmark | Deterministic 2,000-artifact / 20,000-edge / 64 MiB corpus: cold start 3,473.809 ms; warm p50 1,321.665 ms, p75 2,049.978 ms, max 2,102.514 ms; peak RSS 48,287,744 bytes. Internal phase p75 is 801.140 ms, dominated by scan at 636.701 ms; the remaining wall time is process/host overhead. The memory threshold passes, the local wall-time threshold still fails, and `referenceBudgetProved` remains false because the pinned environment was not used. |
| Test dependency provenance | `@playwright/test` 1.61.1 is dev-only and pinned; lock entries resolve to `registry.npmjs.org` with SHA-512 integrity; package metadata records Apache-2.0; `npm audit --package-lock-only --registry=https://registry.npmjs.org` reported 0 vulnerabilities on 2026-07-11 |

The latest benchmark is **not locally green and is not reference-environment proof**.
Its wall-clock p75 misses the local two-second target by 49.978 ms while memory remains
well below the 256 MiB ceiling. The opt-in `context --timings` diagnostic keeps packet
stdout unchanged and attributes warm internal work: scan p75 636.701 ms, traverse
30.156 ms, chunk 41.208 ms, serialize 97.585 ms, and internal total 801.140 ms. This
evidence prevents hunch optimization: scanning is the largest graph phase, while
process/host overhead explains the larger end-to-end result. The current machine also
does not match the pinned Windows Server 2022 / Azure `Standard_D4s_v5` / CPython
3.11.9 environment. Revision 17 therefore remains unreleased.

## Claim ledger

| Claim | Evidence and oracle | Red observed | Confidence | Residual risk |
|---|---|---|---|---|
| **Browse is the deterministic default and selection does not silently change spatial context.** | Reducer and URL-state tests in `docs_explorer_core.test.js`; Playwright selection/context tests. The oracle fails if selection mutates `contextId`, changes the default projection, or serializes a different URL. | Yes - the pre-redesign Explorer conflated selection/context and used randomized spatial state. | **Verified** | No product analytics yet quantify real-user comprehension. |
| **Graph layout is deterministic and structurally bounded.** | Canonical layout/hash tests plus the 500-node/1,000-edge threshold test. The oracle compares repeated layouts/hashes and rejects projections above the count ceilings. | Yes - the prior layout used randomness. | **Verified** | The separate <=500ms reference-browser timing budget remains unproved and is not claimed by this structural test. |
| **Mind-map projection is a deterministic two-hop BFS rooted in explicit context.** | Core traversal/layout tests and browser context-entry tests. The oracle fails on wrong root, hop overflow, nondeterministic order, or omitted ghost edges. | Yes - the prior mind-map was not a stable context-rooted projection. | **Verified** | P2 retrieval ranking quality is not measured by this structural proof. |
| **Spatial SVG and human-readable relationship lists present the same edge set.** | Playwright relationship-parity tests compare computed displayed edges with list rows. The oracle fails on a missing, extra, or differently scoped relation. | Yes - an intermediate implementation used artifact-adjacent rows while the SVG used projection edges. | **Verified** | Details intentionally remain artifact-adjacent rather than projection-scoped. |
| **Escape exits context, retains selection, and returns focus to a stable projection control.** | Playwright Escape/focus tests across Chromium, Firefox, and WebKit. The oracle checks context removal, selection retention, and `projection-toolbar` focus. | Yes - the initial implementation focused a control that was replaced during rerender. | **Verified** | Assistive-technology/manual screen-reader testing remains advisable before public distribution. |
| **History restores the initiating control, including narrow-screen routes.** | Playwright back/forward tests use explicit `data-focus-key` restoration across all three engines. The oracle fails if Back returns only state and not the initiating control. | Yes - WebKit did not preserve clicked-button focus reliably. | **Verified** | Browser behavior outside the three supported engines is not asserted. |
| **Search never removes graph topology and no-result state is announced.** | Core search tests and Playwright topology/live-status tests. The oracle fails if node count changes, selection is lost, or zero results lack an announcement. | Yes - the pre-redesign search destructively filtered the visible graph. | **Verified** | Search remains literal/local; semantic retrieval is P2. |
| **Accessible floors are implemented for the declared browser surface.** | Three-engine keyboard/focus/reduced-motion/forced-colors tests; automated computed contrast >=4.5:1 and visible 44x44 target checks; Browse ARIA-tree tests. | Yes - early reviews found incomplete focus and route behavior. | **Verified** | Automated checks do not replace manual screen-reader and high-zoom usability review. |
| **Source inspection is explicit, inert, bounded, and race-safe.** | Playwright tests cover explicit load, hostile markup as text, 1 MiB exact ceiling (Chromium), overflow in all engines, dishonest/missing `Content-Length`, retry races, selection changes, and stale same-artifact responses. The oracle fails on auto-fetch, DOM execution, over-limit acceptance, or stale overwrite. | Yes - the initial source path buffered responses and allowed stale responses to win. | **Verified** | Rendering a full 1 MiB text node is slow in WebKit; overflow enforcement remains cross-browser, while the exact-ceiling render is asserted once. |
| **Grounding packets are deterministic, bounded, path-stable, and incremental in retained source memory.** | `test_docs_graph.py` covers canonical hashes, Unicode byte offsets, stable paths across absolute roots, exact N-1/N/N+1 limits, file and directory-link rejection, frontmatter exclusion, change-log matching, discarded untraversed bodies, concurrent mutation during derive/context capture, ordered bounded-parallel source snapshots, serialized concurrent append, deterministic file closure, structured opt-in phase timings, and the `main()` internal-error path with seeded path/user/token text. The oracle changes the hash/path/order, follows a linked directory, loses an append, retains an untraversed body, accepts a changed source snapshot, exceeds a configured ceiling, emits timing stderr without opt-in, or leaks seeded exception content to stderr. | Yes - absolute machine paths previously entered serialized identity, the first scanner retained the full admitted corpus, append publication previously had a lost-update window, Windows contenders wrote into an already-locked byte, and the internal-error path lacked an end-to-end negative assertion. | **Verified** | Arbitrary Markdown body content is evidence and is **not** a deterministic PII/secret scrub surface; repositories must apply their separate scrub/governance controls before committing sensitive content. No recall/precision corpus yet proves semantic retrieval quality. |
| **Pack Doctor distinguishes empty, invalid, warning, timeout, and healthy graphs without false green.** | `test_pack_doctor.py` exercises each structured-inventory state plus strict/non-strict exit behavior. The oracle fails if invalid/empty/timeout is classified as PASS or if strict mode returns zero for a warning. | Yes - the earlier validator path could discard failure output and report a false healthy state. | **Verified** | The current repository passes both normal and strict health checks; installed downstream repositories may still surface their own health findings. |
| **Eval workspaces and prompts cannot be interpolated into shell commands.** | `test_run_evals.py` rejects non-kebab case IDs, workspace interpolation, and out-of-root batch workspaces, and proves prompts/workspaces travel only through `AIF_EVAL_PROMPT` / `AIF_EVAL_WORKSPACE`. | Yes - prior execution interpolated workspace text into shell commands. | **Verified** | Case commands remain trusted repository content; untrusted eval definitions are outside the supported boundary. |
| **Revision 17 cannot be marked released without reference proof or human deviation.** | `test_check_consistency.py` covers blank release metadata, exact schema/environment/corpus/threshold matching, finite measured p75/RSS enforcement, contradictory success booleans with oversized measurements, required deviation fields/revision, accepted human approval, and case-insensitive rejection of Copilot and other automation identities. `test_benchmark_harness.py` executes the nearest-rank percentile and exact reference-host/IMDS predicates directly. | Yes - release readiness was previously documentary rather than mechanically enforced; the first gate trusted proof booleans instead of independently checking measurements, and automation-shaped approvers were initially checked case-sensitively. | **Verified** | A human can still approve a documented deviation; that is an explicit governance choice, not a silent pass. |
| **Subprocess and eval execution have hard deadlines and output ceilings.** | `test_bounded_process.py`, eval harness tests, and the 10-second-vs-1-second deadline probe. The oracle requires timeout/output-limit classification, Windows launch-gate failure handling, and process-tree termination. | Yes - the prior eval command path was unbounded. | **Verified** | Windows Job Objects enforce aggregate process/memory ceilings. POSIX uses process-group termination plus per-process `RLIMIT_AS`; it does not claim an aggregate process-tree resource ceiling. |
| **Offline/local operation has no runtime CDN dependency.** | Template/source inspection and browser runs serve only local `docs/index.html`, `docs-index.js`, and `docs-explorer-core.js`. The oracle detects external script/style requests or missing local assets. | Yes - the previous React/Mermaid implementation depended on CDNs. | **Verified** | Deep markdown/Mermaid body rendering is intentionally not part of the stable P1 contract. |

## Failure-mode and trust-boundary evidence

| Failure or threat | Disposition | Evidence |
|---|---|---|
| Oversized or dishonest source response | Stop streaming above 1 MiB and preserve metadata | Exact-ceiling, N+1, missing/false `Content-Length`, and oversized-response browser tests |
| Hostile source markup | Render source only through `textContent` in inert `<pre>` | Hostile HTML/script browser test |
| Late/stale source response | Sequence requests and reject changed-selection or superseded responses | Deterministic late-response and retry-race tests |
| Oversized graph/index | Reject before expensive rendering | Browser artifact/edge/index ceilings and Python packet/source ceilings |
| Symlink escape or machine-path leakage | Reject symlinks; serialize stable root-relative paths only | Python symlink and cross-root hash/path tests |
| Runaway child process | Deadline/output cap with process-tree termination | Bounded-process tests and live eval deadline probe |
| Empty/invalid graph reported healthy | Use one structured inventory result | Pack Doctor classification tests |
| PII/secrets entering evidence | Exclude frontmatter from evidence chunks, document that arbitrary Markdown bodies are not scrubbed, and rely on the repository's separate scrub/secret-scanning controls before commit | Frontmatter-exclusion tests plus threat/privacy registers |
| Unreviewed code reaching the pinned self-hosted benchmark runner | Restrict the workflow to canonical protected `main`, require a protected environment approval, check out the exact workflow SHA without credentials, pin all actions by immutable SHA, and require a dedicated ephemeral-runner marker | Workflow inspection, live branch-protection/environment API checks, and Security & Identity re-review |

## Independent review gates

The final reviews were completed independently. Conditions raised by advisory and hard-veto
reviews were repaired and are represented in the evidence above. Both hard implementation
vetoes are cleared; the pinned-reference performance requirement remains an intentionally
closed release gate, not an implementation defect.

| Persona | Required clearing condition | Current state |
|---|---|---|
| Test Architect | Every P0/P1 promise has a meaningful deterministic oracle; triggered directives are applied or explicitly residual | **PASS-WITH-CONDITIONS** - implementation veto cleared; revision 17 release remains blocked pending pinned-reference proof or human deviation |
| Security & Identity | Filesystem containment, source integrity, eval command isolation, dependency provenance, and self-hosted-runner authorization pass | **PASS-WITH-CONDITIONS; veto cleared** - canonical protected `main`, required PR review, protected benchmark environment, exact-SHA credential-free checkout, immutable action pins, and the dedicated ephemeral-runner contract are active; environment administrators retain bypass/self-approval authority |
| Python Developer | Python 3.8 compatibility, path/encoding correctness, bounded-process safety, and idiomatic structure pass | **PASS-WITH-CONDITIONS** - deterministic file closure and direct read-path tests completed |
| UX & Accessibility | Selection/context flow, keyboard/focus, responsive routes, contrast, targets, state completeness, and reduced motion pass | **PASS** - manual NVDA/VoiceOver and high-zoom review remains advisable before broad public distribution |
| SRE & Diagnostician | Resource ceilings, timeout/termination behavior, failure visibility, and performance claims are honest | **PASS-WITH-CONDITIONS** - phase attribution and operator evidence handoff completed; scheduled self-hosted runs remain accepted operational debt |
| Simplifier | No unnecessary dependency, abstraction, dead path, or unjustified scope remains | **PASS** - only a cosmetic unused test seam was noted; no production complexity finding |

## Open release conditions

1. **Done:** six independent persona gates completed; implementation vetoes cleared after final timing, release-proof, workflow, and repository-governance repairs.
2. **Done:** resolve the five `review-suggested` flags on this proof, the design language, ADR, threat model, and privacy review.
3. **Done:** rerun the complete Python, Node, three-engine Playwright, strict design-lint, Pack Doctor, graph validation/freshness, and bundle-consistency gates.
4. **Done:** temporary benchmark corpus is removed by the harness; clean generated-package synchronization confirmed.
5. **Pending:** append the final audit/change entries through `audit-log.py`.
6. **Release block:** prove the <=2-second p75 grounding budget on the pinned reference environment, or obtain human approval for a documented deviation before releasing revision 17.

## Residual risk and deferred backlog

- **P2:** pinned-browser timing evidence and a CI hardware budget.
- **P2:** repeat the 2,000-artifact CLI benchmark on the pinned reference environment;
  current local evidence passes the <=256 MiB RSS threshold (about 46.1 MiB peak RSS)
  but misses the <=2-second warm wall-clock p75 threshold at 2,049.978 ms. Internal
  phase p75 is 801.140 ms, with scan at 636.701 ms.
- **P2:** schedule the self-hosted reference workflow if runner availability and cost
  justify recurring evidence; current operation remains manual by design.
- **P2:** if two-person benchmark authorization becomes required, add a second environment
  reviewer, enable self-review prevention, and disable administrator bypass.
- **P2:** representative retrieval recall/precision and grounding usefulness corpus.
- **P2:** fuller A6 golden-contract regression corpus for the generated Explorer surface.
- **P2:** privacy-preserving usage analytics for project-memory effectiveness.
- **P3:** optional 3D view only after measured usability, accessibility, and performance evidence.

## Gate record

`GATE implementation-proof | 2026-07-11 | Test Architect, Security & Identity, Python Developer, UX & Accessibility, SRE & Diagnostician, Simplifier | exit criteria met: P0/P1 implementation, contradiction-resistant release proof, dependency provenance, self-hosted workflow authorization, phase attribution, and durable evidence current | verdict: PASS-WITH-RELEASE-BLOCK | vetoes: implementation vetoes cleared; revision 17 release remains blocked pending pinned-reference proof or human deviation`
