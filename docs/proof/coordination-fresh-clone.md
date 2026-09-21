---
id: proof-coordination-fresh-clone
title: Portable historical coordination Git proof
type: proof-pack
status: reviewed
owner: "@timianmalloo"
phase: coordination
tags: [coordination, proof, git, reproducibility]
links:
  - { to: proof-coordination-runtime-v2, rel: relates-to }
  - { to: proof-coordination-end-to-end, rel: refines }
  - { to: design-multi-harness-runner, rel: relates-to }
  - { to: spec-multi-harness-launch-and-monitor, rel: relates-to }
review-by: "2026-12-21"
summary: Original coordination receipt histories retained as a compact pinned Git object fixture let a fresh single-branch clone verify parent, path, ancestry and content invariants without archive refs or private logs.
review-suggested: []
---

# Portable historical coordination Git proof

> Reviewed 2026-09-21: this document retains its original observation/plan scope. Current controls and qualification limits are in the [runtime proof](../proof/coordination-runtime-v2.md). The historical Git proof now uses the pinned original-object fixture, without local archive refs. A fresh single-branch clone passed the public runtime proof command (202 tests). The historical qualification snapshot is unchanged; bounded unattended controls require separate current-profile qualification.

Run from a fresh single-branch clone:

~~~sh
python3 docs/knowledge/acp-compatibility/verify-coordination-end-to-end.py
~~~

This verifies the same recorded history. It does not rerun native models, prove current
permissions or enable unattended coordination. The historical JSON remains unchanged,
including its explicit unattended-disabled flag and private-evidence limitations.

## Invariant and representation

For each of five accepted receipts, the verifier still requires:

1. The source, worker and join IDs identify real Git commit objects.
2. The worker has exactly one parent, the recorded source commit.
3. The source-to-worker diff contains exactly the declared receipt path.
4. The original worker commit is an ancestor of the recorded join.
5. The receipt byte count and SHA-256 match in both original commits and the current checkout.

The durable grain is **one original content-addressed Git object**, retained without
rewriting its bytes or identity. The fixture is
[coordination-receipts.pack](../knowledge/acp-compatibility/coordination-receipts.pack):
230,630 bytes; SHA-256
<code>eca0df6c4df2532921c6ee6a91e829ab8fed16682ff26cee869000876bb5d654</code>.
It contains 323 objects: 285 commits, 33 trees and five receipt blobs. These numbers
describe this fixed snapshot, not aggregate runtime measures.

Commit objects retain original author/committer metadata and messages. Tree objects
retain names, modes and object IDs. The only file bodies are the five already-committed
Markdown receipts. No private native transcript or environment-value file is exported.

This is a purpose-limited object projection, **not a complete repository backup or
fetchable branch bundle**. It retains the complete commit graph of the five joins
and only the trees and blobs needed by the stated checks. Missing unrelated tree
objects are intentional; whole-repository Git fsck is not its verification contract.
Unchanged subtree IDs let native Git verify the one-file diff without exporting
unrelated file bodies.

The verifier requires the exact size and digest, imports the pack with native
Git index-pack into a temporary bare repository, and runs the original Git queries
there. It strips inherited Git environment overrides, disables global/system Git
configuration, and removes the temporary repository on exit. It never imports
evidence into the caller's object database or falls back to local archive refs.
Missing, corrupt or rejected fixtures fail closed.

## Provenance and generation recipe

Objects came directly from the development repository's original Git database.
The five source/worker/join tuples and receipt paths are the existing values in
[end-to-end-qualification.json](../knowledge/acp-compatibility/end-to-end-qualification.json):
the four codex_owner_joins and the claude_owner join. They were not rebuilt from
sanitized text.

To regenerate from a repository retaining those original objects:

1. Form the five tuples from the historical JSON, using owner_join_commit and
   worker_proof.receipt for the Claude Owner tuple.
2. Start an object-ID set with the output of Git rev-list for all five join commits.
   Include every commit ancestor, without rewritten or shallow parent substitutes.
3. For each tuple's source, worker and join, add the IDs returned by the three
   tree queries below.
4. For each worker and join, also add the receipt blob ID.
5. Write unique IDs in sorted order, one per line, to objects.txt. Pack the explicit
   object set using the final command below; do not add revision traversal or thin-pack.
6. Import into a new bare repository and run all five original git_receipt checks.
   Review exported object types/counts, byte size and digest before updating the
   fixture and verifier constants together.

~~~sh
git rev-parse 'COMMIT^{tree}'
git rev-parse 'COMMIT:docs'
git rev-parse 'COMMIT:docs/notes'
git rev-parse 'COMMIT:RECEIPT_PATH'
git pack-objects --stdout < objects.txt > coordination-receipts.pack
~~~

Git compression versions can produce different pack bytes for identical objects.
That is a new reviewed fixture version, not a reason to skip the digest. Normal
verification needs no generation step or archive refs.

## Evidence and disconfirmation

An actual transport clone of the proof branch, with --no-local and --single-branch,
failed the original verifier with “Git evidence unavailable or inconsistent”.
The development checkout had hidden the distribution defect by retaining archive objects.

[The focused tests](../../tests/docs_explorer/test_coord_proof_fresh_clone.py)
create a committed proof-only source repository and clone it through Git transport.
They invoke the real CLI, Git, files and original-object fixture.

| Claim | Control and oracle | Evidence |
|---|---|---|
| No local archive history is needed | Original worker object absent before and after successful verification; no alternates | Observed red, then green |
| Fixture remains mandatory on a rich checkout | Import historical objects locally, remove fixture, require GIT-FIXTURE failure | Original verifier incorrectly passed; corrected verifier rejects |
| Corruption cannot become unchecked evidence | Flip one fixture byte or truncate input; require named hash/size failure | Corruption observed red, then green; size fault injected |
| Current checkout bytes remain load-bearing | Alter receipt, require failure | Negative control passes |
| Original Git ancestry remains load-bearing | Substitute existing but wrong worker/join commits, require failure | Negative controls pass |
| Environment cannot redirect fixture writes | Foreign GIT_DIR and GIT_OBJECT_DIRECTORY; verification passes, foreign store stays empty | Observed red, then green |

Seven focused tests pass; the verifier retains its 20 false-claim mutations.
Independent coordinator review accepted the unchanged Git predicates, isolated import,
exact payload pin and proof scope, and independently reran both sets of checks.

The full implementation branch at commit
<code>770e892681339c95d5b94d28840f7b93468bddbd</code> was then cloned with
--no-local and --single-branch. Its standalone verifier passed all five receipt
checks and 20 false-claim controls. Readback confirmed no archive refs or alternates,
the original worker object remained absent after verification, and the fixture digest
was unchanged. This full-repository check complements the focused proof-only clones.

**Class → sweep → derive → prevent:** evidence depending on local object reachability
is not portable merely because its JSON is committed. The E2E verifier consumed these
join histories; its predicates were sound, but linear integration dropped their
reachable refs. Retain the necessary exact objects and exercise the reader from an
object-isolated clone. The tests are the control; this note alone is not the fix.

## Scope and limits

Surfaces: committed fixture → isolated import → existing Git predicates → CLI result,
with focused tests and this linked note. No pack/runtime, hook, permission policy or
historical readiness claim changes. Git/Python are existing dependencies; no service,
download or credential is needed. The fixed digest bounds accepted input; each Git
subprocess has a ten-second deadline. No new data collection or secret-bearing logs
are introduced. Original commit metadata is intentionally preserved to retain identity.

This establishes reproducibility of the **Git and sanitized-corpus checks**.
Private native trace review remains a historical observation. New native runs and
broader unattended authorization require separate current-profile evidence.
