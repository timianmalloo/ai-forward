---
id: lens-code-doc-join
title: "Lens - code/doc join"
type: doc
status: accepted
owner: "@maintainers"
tags: [lens, graphify, code-graph, traceability]
links:
  - { to: lens-graph-structure, rel: relates-to }
review-by: ""
summary: >-
  Derived join between the documentation graph (intent) and the Graphify code
  graph (reality): documentation referencing code that does not exist, and the
  most connected code symbols no artifact governs. A prompt, never a gate.
---

# Lens - code/doc join

> **This is a lens, not a record.** It is *derived* at read time from the docs graph
> (`docs/docs-index.js`, itself derived from artifact frontmatter) and the code graph
> (`graphify-out/graph.json`, derived from source). Both regenerate; neither is edited.
> Findings below are **prompts, not failures** (GK11/OB13) - close the gap, or record
> why it does not apply.

*Code graph: **2050 nodes**, **2509 edges**, 198 source files. Docs graph: **40 artifacts**, 91 distinct paths referenced.*

## Edge provenance (GK6)

*A citation is not a promotion: an `INFERRED` edge quoted as established is the Confident Guess with extra steps.*

| graphify tag | pack label | edges |
|---|---|---|
| `EXTRACTED` | **Verified** | 2478 |
| `INFERRED` | **Inferred** | 31 |
| `AMBIGUOUS` | **Flagged** | 0 |

## Gap 1 - documentation with no implementation

*An artifact references a code path that exists neither on disk nor in the code graph. Either it was never written, or it moved and the document now lies.*

| artifact | referenced path |
|---|---|
| `architecture` | `dist/ai-forward-pack.zip` |
| `defect-classes` | `templates/mockup-harness.template.html` |
| `forensic-review-20260712` | `pack/scripts/model-router.py` |
| `forensic-review-20260712` | `scripts/model-router.py` |
| `forensic-review-20260712` | `tests/docs_explorer/test_model_router.py` |
| `kb-pack-evolution-sota` | `./tool.py` |
| `note-20260712-revert-model-orchestration` | `pack/scripts/model-router.py` |

## Gap 2 - risk with no governance

*The most connected code symbols that **no** documentation artifact references. Change here carries the most blast radius and has the least written intent behind it (GK10). Run `graphify affected "<symbol>"` before touching one.*

| symbol | degree | file:line | community |
|---|---|---|---|
| `DocsGraphTests` | 51 | `tests/docs_explorer/test_docs_graph.py:L33` | DocsGraphTests |
| `load_module()` | 33 | `tests/docs_explorer/test_docs_graph.py:L25` | DocsGraphTests |
| `docs-explorer-core.js` | 29 | `pack/scripts/docs-explorer-core.js:L1` | docs-explorer-core.js |
| `benchmark_docs_explorer.js` | 27 | `tests/docs_explorer/benchmark_docs_explorer.js:L1` | benchmark_docs_explorer.js |
| `BoundedProcessTests` | 23 | `tests/docs_explorer/test_bounded_process.py:L24` | BoundedProcessTests |
| `ReleaseGateTests` | 23 | `tests/docs_explorer/test_check_consistency.py:L21` | ReleaseGateTests |
| `._write_artifact()` | 22 | `tests/docs_explorer/test_docs_graph.py:L1427` | DocsGraphTests |
| `obsidian-setup.py` | 18 | `pack/scripts/obsidian-setup.py:L1` | obsidian-setup.py |
| `browser_benchmark.test.js` | 15 | `tests/docs_explorer/browser_benchmark.test.js:L1` | benchmark_docs_explorer.js |
| `PackDoctorGraphTests` | 15 | `tests/docs_explorer/test_pack_doctor.py:L28` | PackDoctorGraphTests |
| `run_bounded()` | 14 | `pack/scripts/bounded_process.py:L204` | run_bounded |
| `.run_python()` | 14 | `tests/docs_explorer/test_bounded_process.py:L28` | BoundedProcessTests |
| `RunEvalsCommandTests` | 14 | `tests/docs_explorer/test_run_evals.py:L21` | RunEvalsCommandTests |
| `run-evals.py` | 12 | `pack/evals/run-evals.py:L1` | run_bounded |
| `main()` | 12 | `pack/scripts/obsidian-setup.py:L702` | obsidian-setup.py |

## How to act on this

1. **Gap 1** - fix the reference, or delete the claim. A path that does not resolve is a documentation defect, and the pack's own rule is that a stale record is a defect rather than debt (`end-to-end-integrity.md` E17).
2. **Gap 2** - either write the governing design, or record why the symbol needs none. A god node with no design is where the next expensive surprise comes from.
3. **Recurring shapes** - register them as defect *classes* with a control, not as one-off fixes (`continuous-improvement.md` CI1-CI6).

*Code graph built at commit `9a5491f26757929caf8f05ffe568070576cdc04a`. Rebuild with `graphify-setup.py --build` after material code change.*
