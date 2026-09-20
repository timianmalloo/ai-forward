---
id: note-20260920-acp-qualification-is-profile-specific
title: "ACP qualification belongs to an effective profile, not a harness name"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: coordination
tags: [coordination, acp, permissions, evidence]
links:
  - { to: spec-acp-coordination, rel: documents }
  - { to: kb-acp-compatibility, rel: depends-on }
review-by: "2026-12-20"
review-suggested: []
summary: >-
  The live ACP spike showed that a mode named read-only can allow workspace writes,
  and that missing local instructions can be a project-trust issue shared with the native
  CLI. Qualification therefore binds actual policy, cwd, trust and required hooks.
---

# Qualification follows the effective profile

**Decision:** capability observations must bind the executable/adapter version, actual
workspace/trust state, effective permissions and required instruction/hook configuration.
A changed binding invalidates cached qualification. A capability's evidence also names
its scope: same-process load is not restart recovery; hook invocation is not enforcement;
transport end-turn is not completed repository work.

**Evidence:** Codex ACP adapter 1.12.0 advertises mode ID `read-only` as “Ask for approval”
and maps it to workspace-write with on-request approval. The first local edit succeeded
without a callback; a subsequent external-path edit received one ACP denial and left no
file. Grok missed the instruction canary on both ACP and native paths while inspection
reported the fixture untrusted. These disconfirm name-based policy inference and an
ACP-only diagnosis, respectively. See the [measured records](../knowledge/acp-compatibility/observations.json).

**Additional correction:** a driver and its child probe have separate outcomes. The
follow-up Grok driver hit its three-turn cap after producing completed target records;
its final stdout was empty. The evidence exporter initially assumed every wrapper had
JSON stdout and raised a decoding error. It now records the failed wrapper and retains
independently inspected child observations; it never substitutes an empty successful
result. The finite cap is an estimation finding, not evidence of completion.

**Control:** [verify-evidence.py](../knowledge/acp-compatibility/verify-evidence.py)
requires a positive permission-request count before a denial verdict, a real final result
before successful wrapper completion, and preserves the actual failed follow-up wrapper.
Its negative controls cover zero callbacks, an allowed write, empty result at exit zero,
and a nonzero wrapper exit despite valid-looking response text. The class-level rule is
the existing PACK-P corpus-presence obligation; the new specimen is a permission or
completion corpus, not a file scan. Product-level stale-profile tests are required by
ACP-2 and remain implementation work, not falsely claimed as built by this specification.
