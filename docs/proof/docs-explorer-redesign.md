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
  Accepted implementation evidence for the deterministic, local-first Docs Explorer,
  native Spatial 3D knowledge portal, and bounded grounding packet implementation.
  The P0/P1 contract is covered by Python, Node, and three-engine browser suites;
  phase-attributed benchmark evidence separates graph work from process/host overhead.
  Revision 17 remains intentionally unreleased pending pinned-reference performance
  proof or a human-approved deviation.
---

# Docs Explorer Redesign - Proof Pack

**Status:** Implementation accepted; release blocked. The implementation evidence,
dependency disposition, and independent persona reviews are current. Revision 17 remains
unreleased until the pinned-reference latency budget is proved or explicitly accepted
through the Deviation Protocol.

## Scope proved

This Proof Pack covers the accepted P0/P1 implementation in
`docs/design/docs-explorer-grounding-and-spatial-navigation.md`:

- deterministic Browse, Graph, context-rooted two-hop Mind-map, and native Spatial 3D projections;
- independent selection and exploration context with URL/history restoration;
- selected-node Spatial 3D camera targeting with interruptible motion, orbit/zoom/reset controls,
  reduced-motion behavior, deterministic fallback to Graph, and no effect on graph semantics;
- a local knowledge-surface portal linking audit, documentation, design-preview, and other
  safely discovered HTML artifacts without adding them to the canonical graph hash;
- keyboard, responsive-route, reduced-motion, contrast, target-size, and relationship-list behavior;
- local-first source inspection with inert rendering, byte ceilings, retries, and stale-response rejection;
- deterministic, bounded grounding packets with stable root-relative identity;
- bounded subprocess use in Pack Doctor and the eval harness.

It does **not** claim completion of the remaining P2/P3 backlog: reference-environment
CLI/browser performance proof, retrieval recall evaluation, deeper browser timing
telemetry, a full A6 golden contract corpus, or privacy-preserving usage analytics.

## Verification summary

| Surface | Current evidence |
|---|---|
| Python unit/integration | `python -m unittest discover -s tests/docs_explorer -p "test_*.py"` -> 108 tests passed, including Windows process-tree, append-lock, UTF-8 rollup, timing-invariance, HTML-surface, Audit Explorer regeneration, and contradiction-resistant release-proof contracts |
| JavaScript core | `npm run test:docs-explorer:core` -> 32 tests passed, including deterministic Spatial 3D coordinates, camera precedence, perspective projection, graph-semantic isolation, Audit Explorer static safety contracts, and the accepted browser-benchmark environment contract |
| Browser behavior | `npm run test:docs-explorer:browser` -> 231 passed, 12 intentional engine-specific skips across Chromium, Firefox, and WebKit, including Spatial 3D camera motion, filter-driven target geometry, excluded-selection controls, routine-rerender completion, manual-interruption recovery, reduced motion, orbit/zoom/reset, focus, edge parity, 120/120 rapid replacement-search stress cases, dark-mode computed contrast/target floors, executed Audit Explorer interactions/failure state, IME ordering, empty-index readiness, authored high contrast, portal links, and fallback |
| Design language | Strict design lint passed with zero warnings |
| Bundle consistency | `tools/verify-bundle.ps1` -> `BUNDLE CONSISTENT` after final synchronization |
| Install health | Pack Doctor normal and `--strict` -> 6 PASS, 0 WARN, 0 FAIL |
| Knowledge graph | `docs-graph.py validate` and `freshness --gate fail` -> 21 artifacts, no problems, stale nodes, flags, or orphans |
| Eval/process deadlines | Process tests prove timeout, output-limit, launch-gate, and child-tree cleanup behavior; the benchmark watchdog self-test terminated its child tree at a two-second deadline with no surviving PIDs |
| Grounding benchmark | Deterministic 2,000-artifact / 20,000-edge / 64 MiB corpus: cold start 3,473.809 ms; warm p50 1,321.665 ms, p75 2,049.978 ms, max 2,102.514 ms; peak RSS 48,287,744 bytes. Internal phase p75 is 801.140 ms, dominated by scan at 636.701 ms; the remaining wall time is process/host overhead. The memory threshold passes, the local wall-time threshold still fails, and `referenceBudgetProved` remains false because the pinned environment was not used. |
| Browser benchmark | The committed five-cold/five-warm harness now records Chromium build/flags, headless SwiftShader mode, 1366x768 DPR 1, cache mode, a one-second frame-floor window, p50/p75/max distributions, heap delta, and independently recomputable raw samples. On the current non-reference host: usable-shell p75 1,127.300 ms, search p75 941.600 ms, Graph p75 1,105.350 ms, Spatial p75 1,268.675 ms, orbit floor 59 fps. The shell and frame floor pass; interaction/layout thresholds fail; `localThresholdsPassed` and `referenceBudgetProved` are false. |
| Test dependency provenance | `@playwright/test` 1.61.1 is dev-only and pinned; lock entries resolve to `registry.npmjs.org` with SHA-512 integrity; package metadata records Apache-2.0; `npm audit --audit-level=high` reported 0 vulnerabilities on 2026-07-11 |

The latest CLI grounding benchmark is **not locally green and is not reference-environment
proof**. Its wall-clock p75 misses the local two-second target by 49.978 ms while memory remains
well below the 256 MiB ceiling. The opt-in `context --timings` diagnostic keeps packet
stdout unchanged and attributes warm internal work: scan p75 636.701 ms, traverse
30.156 ms, chunk 41.208 ms, serialize 97.585 ms, and internal total 801.140 ms. This
evidence prevents hunch optimization: scanning is the largest graph phase, while
process/host overhead explains the larger end-to-end result. The current machine also
does not match the pinned Windows Server 2022 / Azure `Standard_D4s_v5` / CPython
3.11.9 environment. The browser harness is likewise non-reference and fails the
100 ms search plus 500 ms Graph/Spatial p75 thresholds under 4x CPU throttling despite
meeting the usable-shell and 30 fps floors. Revision 17 therefore remains unreleased.

## Claim ledger

| Claim | Evidence and oracle | Red observed | Confidence | Residual risk |
|---|---|---|---|---|
| **Browse is the deterministic default and selection does not silently change spatial context.** | Reducer and URL-state tests in `docs_explorer_core.test.js`; Playwright selection/context tests. The oracle fails if selection mutates `contextId`, changes the default projection, or serializes a different URL. | Yes - the pre-redesign Explorer conflated selection/context and used randomized spatial state. | **Verified** | No product analytics yet quantify real-user comprehension. |
| **Graph layout is deterministic and structurally bounded.** | Canonical layout/hash tests plus the 500-node/1,000-edge threshold test. The oracle compares repeated layouts/hashes and rejects projections above the count ceilings. | Yes - the prior layout used randomness. | **Verified** | The separate <=500ms reference-browser timing budget remains unproved and is not claimed by this structural test. |
| **Browser performance remains an honest release gate.** | The benchmark records five cold and five warm samples on the deterministic Spatial render ceiling (500 artifacts / 1,000 relationships / 100 surfaces), independently recomputes p50/p75/max and the frame floor, records heap deltas and exact browser environment, and force-kills its Playwright BrowserServer on any post-launch deadline. Current local evidence passes usable-shell and orbit floors but fails search and initial Graph/Spatial p75s. | Yes - local misses are preserved rather than rewritten; the timeout test requires cleanup to finish before the stable timeout error is returned. | **Unverified** | Profile the 2.2-9.4x local interaction/layout misses before spending the scarce reference run. The usable-shell claim covers the Spatial ceiling, not the broader 1,000-artifact / 5,000-relationship index hard limit. |
| **Spatial 3D is a deterministic progressive projection whose camera never mutates graph meaning.** | Core tests prove input-order-invariant world coordinates, camera precedence, perspective projection, and unchanged graph/traversal/packet hashes; Playwright proves selected-node focus, geometry-sensitive retargeting after filters move the same selected ID, disabled Focus Selected for excluded artifacts, Reset Camera announcement of the visible canonical target, completion of an active destination before routine rerenders, recovery after manual orbit interruption, reduced-motion snapping, blank-canvas orbit, zoom/reset, edge parity, and Graph fallback. The oracle fails if reordered input changes geometry, camera state enters canonical state, a node action starts orbit, an interrupted transition remains falsely settled, routine rendering strands the camera between targets, motion ignores accessibility modes, or fallback loses selection/context/filter state. | Yes - 3D was previously deferred; the first pointer-capture implementation intercepted node clicks; later camera versions keyed only by ID, stranded partial transitions on rerender, and retained a stale settled target after manual interruption. | **Verified** | Manual vestibular-comfort and spatial-comprehension review remains advisable before broad public distribution. |
| **Mind-map projection is a deterministic two-hop BFS rooted in explicit context.** | Core traversal/layout tests and browser context-entry tests. The oracle fails on wrong root, hop overflow, nondeterministic order, or omitted ghost edges. | Yes - the prior mind-map was not a stable context-rooted projection. | **Verified** | P2 retrieval ranking quality is not measured by this structural proof. |
| **Spatial SVG and human-readable relationship lists present the same edge set.** | Playwright relationship-parity tests compare computed displayed edges with list rows. The oracle fails on a missing, extra, or differently scoped relation. | Yes - an intermediate implementation used artifact-adjacent rows while the SVG used projection edges. | **Verified** | Details intentionally remain artifact-adjacent rather than projection-scoped. |
| **Escape exits context, retains selection, and returns focus to a stable projection control.** | Playwright Escape/focus tests across Chromium, Firefox, and WebKit. The oracle checks context removal, selection retention, and `projection-toolbar` focus. | Yes - the initial implementation focused a control that was replaced during rerender. | **Verified** | Assistive-technology/manual screen-reader testing remains advisable before public distribution. |
| **History restores the initiating control, including narrow-screen routes.** | Playwright back/forward tests use explicit `data-focus-key` restoration across all three engines. The oracle fails if Back returns only state and not the initiating control. | Yes - WebKit did not preserve clicked-button focus reliably. | **Verified** | Browser behavior outside the three supported engines is not asserted. |
| **Search never removes graph topology, reports all result classes honestly, and stale focus restoration cannot interrupt replacement input.** | Core search tests and Playwright topology/live-status tests plus a 120-case three-engine replacement-search stress contract. The implementation preserves the same connected search input across rerenders and synchronizes its value and caret after history restoration rather than replacing the focused control. The oracle fails if node count changes, selection is lost, a surface-only query reports zero, the no-results announcement survives a positive transition, the input disconnects during replacement, or popstate restoration leaves the DOM value/caret inconsistent with canonical state. | Yes - the pre-redesign search destructively filtered the visible graph, an intermediate portal implementation counted artifacts only, and replacing the focused input interrupted rapid replacement text in WebKit. | **Verified** | Search remains literal/local; previous/next navigation intentionally remains artifact-specific; semantic retrieval is P2. |
| **Accessible floors are implemented across the Explorer and linked local knowledge surfaces.** | Three-engine Explorer keyboard/focus/reduced-motion/forced-colors tests; computed light/dark contrast >=4.5:1, non-text contrast >=3:1, and visible 44x44 target checks including Spatial controls; Browse ARIA-tree ownership tests; Firefox IME tests; executed Audit Explorer disclosure/keyboard/copy/filter/toggle/failure tests; and Node contracts rejecting CDN, React, `innerHTML`, unlabeled controls, and missing fallback states. | Yes - final UX review found ineffective Spatial target coverage, redundant assistive instructions, no computed dark-mode audit, and static-only Audit Explorer evidence. | **Verified** | Automated checks do not replace manual NVDA/VoiceOver and high-zoom review. |
| **A valid empty index is an empty knowledge base, not a load failure.** | Three-engine empty-index browser tests require the stable shell, `data-load-state="empty"`, zero-count views, and no recovery error. The oracle fails if an empty but schema-valid index is treated as unavailable. | Yes - the first loader used truthiness and sent valid empty indexes to the recovery shell. | **Verified** | An empty project is intentionally sparse; onboarding content beyond the empty-state guidance is out of scope. |
| **Source inspection is explicit, inert, bounded, and race-safe.** | Playwright tests cover explicit load, hostile markup as text, 1 MiB exact ceiling (Chromium), overflow in all engines, dishonest/missing `Content-Length`, retry races, selection changes, and stale same-artifact responses. The oracle fails on auto-fetch, DOM execution, over-limit acceptance, or stale overwrite. | Yes - the initial source path buffered responses and allowed stale responses to win. | **Verified** | Rendering a full 1 MiB text node is slow in WebKit; overflow enforcement remains cross-browser, while the exact-ceiling render is asserted once. |
| **Grounding packets are deterministic, bounded, path-stable, and incremental in retained source memory.** | `test_docs_graph.py` covers canonical hashes, Unicode byte offsets, stable paths across absolute roots, exact N-1/N/N+1 limits, file and directory-link rejection, frontmatter exclusion, change-log matching, discarded untraversed bodies, concurrent mutation during derive/context capture, ordered bounded-parallel source snapshots, serialized concurrent append, deterministic file closure, structured opt-in phase timings, and the `main()` internal-error path with seeded path/user/token text. The oracle changes the hash/path/order, follows a linked directory, loses an append, retains an untraversed body, accepts a changed source snapshot, exceeds a configured ceiling, emits timing stderr without opt-in, or leaks seeded exception content to stderr. | Yes - absolute machine paths previously entered serialized identity, the first scanner retained the full admitted corpus, append publication previously had a lost-update window, Windows contenders wrote into an already-locked byte, and the internal-error path lacked an end-to-end negative assertion. | **Verified** | Arbitrary Markdown body content is evidence and is **not** a deterministic PII/secret scrub surface; repositories must apply their separate scrub/governance controls before committing sensitive content. No recall/precision corpus yet proves semantic retrieval quality. |
| **Pack Doctor distinguishes empty, invalid, warning, timeout, and healthy graphs without false green.** | `test_pack_doctor.py` exercises each structured-inventory state plus strict/non-strict exit behavior. The oracle fails if invalid/empty/timeout is classified as PASS or if strict mode returns zero for a warning. | Yes - the earlier validator path could discard failure output and report a false healthy state. | **Verified** | The current repository passes both normal and strict health checks; installed downstream repositories may still surface their own health findings. |
| **Eval workspaces and prompts cannot be interpolated into shell commands.** | `test_run_evals.py` rejects non-kebab case IDs, workspace interpolation, and out-of-root batch workspaces, and proves prompts/workspaces travel only through `AIF_EVAL_PROMPT` / `AIF_EVAL_WORKSPACE`. | Yes - prior execution interpolated workspace text into shell commands. | **Verified** | Case commands remain trusted repository content; untrusted eval definitions are outside the supported boundary. |
| **Revision 17 cannot be marked released without reference proof or human deviation.** | `test_check_consistency.py` covers blank release metadata, exact CLI/browser schema/environment/corpus/threshold matching, five-cold/five-warm sample cardinality, cache-mode labels, finite raw metrics and heap deltas, recomputed p50/p75/max distributions, Chromium viewport/flags/SwiftShader/frame-window evidence, contradictory success booleans, required deviation fields/revision, accepted human approval, and case-insensitive rejection of Copilot and other automation identities. `test_benchmark_harness.py` executes the nearest-rank percentile and exact reference-host/IMDS predicates directly. | Yes - release readiness was previously documentary rather than mechanically enforced; the first gate trusted proof booleans instead of independently checking measurements, and the browser proof originally omitted accepted environment/distribution fields. | **Verified** | A human can still approve a documented deviation; that is an explicit governance choice, not a silent pass. |
| **Subprocess and eval execution have hard deadlines and output ceilings.** | `test_bounded_process.py`, eval harness tests, and the 10-second-vs-1-second deadline probe. The oracle requires timeout/output-limit classification, Windows launch-gate failure handling, and process-tree termination. | Yes - the prior eval command path was unbounded. | **Verified** | Windows Job Objects enforce aggregate process/memory ceilings. POSIX uses process-group termination plus per-process `RLIMIT_AS`; it does not claim an aggregate process-tree resource ceiling. |
| **Offline/local operation has no runtime CDN dependency.** | Template/source inspection and browser runs serve only local Explorer assets and `audit-data.js`; static contracts reject remote URLs, React/htm, and unsafe `innerHTML`; browser tests execute both viewers without a remote runtime. The oracle detects external script/style requests, missing local assets, or success-shaped behavior when audit data fails. | Yes - the previous Docs and Audit Explorer implementations depended on CDNs. | **Verified** | Deep markdown/Mermaid body rendering is intentionally not part of the stable P1 contract. |
| **The Explorer is a safe one-stop portal for local HTML knowledge surfaces.** | Python tests cover stable discovery/order/title/kind metadata, graph-hash isolation, traversal rejection, symlink/reparse rejection, and exclusions for the Explorer/template tree; Playwright verifies audit, real documentation-hub, and design-preview links. The committed `docs/_site/index.html` links only to source-backed architecture, design, proof, security, memory, audit, and skill artifacts and explicitly discloses that no generated JavaDoc-style API reference currently exists. The oracle fails if an unsafe/external path is emitted, a crafted title becomes markup, a surface changes canonical graph identity, a required destination is absent, or placeholder documentation is presented as generated API truth. | Yes - the prior Explorer did not expose the audit log or other HTML knowledge surfaces, and the first portal had no real documentation destination. | **Verified** | Surface discovery intentionally indexes only safe local HTML files under `docs/`; external sites and arbitrary filesystem paths are out of scope. |
| **Governance rollups emit valid Unicode on Windows consoles.** | `test_rollup_writes_utf8_when_console_encoding_cannot_encode_source` forces CP1252 and verifies UTF-8 output containing a Unicode arrow. The oracle fails if `docs-graph.py rollup` routes valid Markdown through the console code page. | Yes - the final STRIDE refresh crashed with `UnicodeEncodeError` on Windows. | **Verified** | Consumers should decode rollup stdout as UTF-8. |

## Failure-mode and trust-boundary evidence

| Failure or threat | Disposition | Evidence |
|---|---|---|
| Oversized or dishonest source response | Stop streaming above 1 MiB and preserve metadata | Exact-ceiling, N+1, missing/false `Content-Length`, and oversized-response browser tests |
| Hostile source markup | Render source only through `textContent` in inert `<pre>` | Hostile HTML/script browser test |
| Late/stale source response | Sequence requests and reject changed-selection or superseded responses | Deterministic late-response and retry-race tests |
| Oversized graph/index | Reject before expensive rendering | Browser artifact/edge/index ceilings and Python packet/source ceilings |
| Spatial 3D render or pointer overload | Bound native geometry, start orbit only on blank canvas, dispose pointer state, and replace with Graph on unsupported/oversized/failed initialization | Core layout/camera tests plus three-engine orbit, focus, limit, transform-failure, and fallback tests |
| Crafted or escaping HTML knowledge surface | Discover safe regular files only; reject links/reparse points; escape metadata; keep surfaces outside graph identity | Python surface fixtures and browser portal-link tests |
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
6. **Done:** final security, test, UX/accessibility, SRE, and simplification findings were dispositioned; the resulting repair set passed the complete executable evidence matrix.
7. **Release block:** prove the <=2-second p75 grounding budget on the pinned reference environment, or obtain human approval for a documented deviation before releasing revision 17.

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
- **P3:** optional richer spatial techniques only after measured usability, accessibility,
  and performance evidence; the shipped native Spatial 3D projection remains bounded,
  local, progressively enhanced, and replaceable by Graph.

## Gate record

`GATE implementation-proof | 2026-07-11 | Test Architect, Security & Identity, Python Developer, UX & Accessibility, SRE & Diagnostician, Simplifier | exit criteria met: P0/P1 implementation, contradiction-resistant release proof, dependency provenance, self-hosted workflow authorization, phase attribution, and durable evidence current | verdict: PASS-WITH-RELEASE-BLOCK | vetoes: implementation vetoes cleared; revision 17 release remains blocked pending pinned-reference proof or human deviation`
