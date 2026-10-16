---
id: design-one-command-adoption
title: "One-command adoption boundaries and implementation"
type: design
status: in-review
owner: "@ahutanu"
phase: "pack-adoption"
tags: [adoption, delivery, installation, portability]
links:
 - { to: spec-one-command-adoption, rel: refines }
 - { to: architecture, rel: refines }
review-by: 2027-01-01
review-suggested: []
summary: >-
  A conditional skill entry point and source-driven portable bootstrap reduce manual
  workflow selection without replacing outcome ownership or changing trust boundaries.
---

# One-command adoption design

## Delivery is a skill, not a new execution service

`pack/commands/deliver/SKILL.md` is the authoritative entry point. The existing
host/model executes the selected skills. `delivery.py` only derives a conditional
stage list and validates local checkpoint integrity; it does not call models,
execute arbitrary commands, approve permissions or certify semantic acceptance.

Ground the original request and reuse an accepted/current contract, plan, spec or
design. Select stages for real unresolved questions. T0 stays short; explicit
security, identity, data, contract, money and concurrency risks, and migrations,
retain the Rules-of-the-Road T2 floor. Coordinated migrations characterize old
behavior before track implementation and retain coverage, equivalence and rollback
obligations. Independent tracks prepare their contracts before execution. Review-only
requests and empty invocations do not enter a product-editing pipeline.

Checkpoint records preserve raw/compiled intent, project identity, routing facts,
completed-stage evidence, input/workspace fingerprints, gates and final criteria
observations. Git state is worktree-local; plain projects use a project-keyed local
state area without creating Git history. Atomic replacement and an exclusive writer
lock avoid cooperative simultaneous task updates. A crash lock requires inspection,
not an invented completion or automatic clearance.

A pause carries a question, authority, task/gate binding and partial proof. A reply
receipt is valid only after the host/agent has checked the original authorized reply
or independent review. Source labels and actor names are cooperative bookkeeping,
not cryptographic authentication. Hashes detect drift; they do not prove a report is
true. Hard vetoes, host tool permissions and release consent remain independent
controls. The original criteria must be matched to real observations before closure.

## Setup reuses the committed source deployment map

The stdlib PEP 723 `bootstrap.py` is run through `uv` with `--no-config --no-project
--script`. Git and uv are explicit prerequisites. This supplies an appropriate
interpreter without resolving target dependencies, creating a target environment or
lockfile, or changing global runtime/trust configuration. The shared installed hook
launcher prefers native Python and uses uv only when Python is not on PATH.

The bootstrap resolves the project root, obtains the selected committed source and
prints its exact Git commit and pack revision. `--source` supports a local committed
checkout; `--repo` and `--ref` select a remote source. The source applier is used,
not a possibly stale installed applier. Before upstream merge, the fork preview
explicitly selects the fork branch; it must not silently install upstream main.

1. Strictly decode existing policy-bearing settings and validate the managed blocks.
2. Compute the source applier's dry plan in a bounded subprocess. Its action rows and
   observed write/remove destinations supply the staging footprint, including backups
   and legacy removals. There is no second deployment copy map.
3. Stage only the managed/baseline context in a disposable directory. Preserve relevant
   Git history/index context. Do not walk/hash/copy the entire target or dependency
   binaries; necessary parity discovery honors ignored-untracked paths.
4. Apply the actual source program in staging. Run a fresh source plan there to verify
   no required actions remain. Child exit zero alone is insufficient.
5. Recheck original owned paths for drift and unsafe objects. Promote only verified
   changes, then read actual target bytes back. Ordinary I/O failure attempts rollback;
   unsafe/incomplete recovery retains originals and reports the exact boundary.
6. Report the installed source receipt and the next `/deliver` action.

Unrelated product work, untracked files, owned graph/index data and custom
instructions/settings remain outside this operation. Managed symlinks, hardlinks,
nonregular files and Windows reparse points refuse; conflicts/REVIEW are not forced.
Repeat runs recompute the map and preserve local deviations. There is no Git init,
identity invention, commit, push, deployment or new ownership/trust opt-in.

The source plan's observed reads and writes are run in isolated Python children
(`-I -B`) so ordinary target `json.py`/`subprocess.py` names are not executable import
paths and previews do not write bytecode into the target. Source-named existing hook
bundle changes, unverified removals, writes to an existing `.gitattributes`, and
active product control rewrites require reconciliation before target writes. This
is deliberately conservative, including old stock hook refreshes; it does not guess
ownership from a filename. Credential-bearing/query/fragment source URLs refuse
before Git, preventing transport credentials from appearing in tracked receipts.

## Limits are explicit

- A remote installer executes the selected trusted source. It is not a malicious-source
  sandbox; pin both the bootstrap URL and source ref when requiring immutable inputs.
- Target comparison is cooperative drift detection, not a concurrent-writer lock or
  power-loss/SIGKILL-atomic transaction.
- Plain-project workspace hashing does not reinterpret every possible ignore format;
  load-bearing runtime/ignored/external files require explicit input registration.
- Current inherited compiler limitations remain inherited. The new entry point does not
  make quote provenance a semantic guarantee or silently waive nondispatchable contracts.
- Filesystem projection and deterministic tests do not qualify model behavior on every
  host. Native scenarios and real Windows/macOS/Linux executions are recorded separately.

## Verification homes

Focused regression controls live in `test_delivery.py`, `test_bootstrap.py`,
`test_adoption_entrypoints.py` and `test_uv_hook_launcher.py`. The existing complete
bundle, portability, source/parity, API, portal and browser gates remain in force.
The adoption workflow exercises native Windows/macOS/Linux and Windows cmd invocation
against the exact source SHA. Verification results belong in the linked Proof Pack,
not in an unconditional claim of semantic or host enforcement.
