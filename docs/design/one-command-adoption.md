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

## Adversarial analysis (STRIDE-lite)
Trust boundaries: (1) the network → `bootstrap.py`, which fetches a Git source and **executes its code**; (2) the target project → the installer (the target's files are the operator's data, but its code must not run); (3) the installed hook launcher → `uv`; (4) the operator's shell → `delivery.py` checkpoints. **T (tampering):** the source comes from `DEFAULT_REPO` (`bootstrap.py:75`). `--ref` defaults to `main` (`bootstrap.py:527`), and the README one-liner fetches `bootstrap.py` itself from `…/main/` (`README.md:46`). No signature, tag or SHA pin is checked; integrity comes from the Git/HTTPS transport and from the operator pinning `--ref`. This is **transferred** to GitHub transport and account security and **accepted** under "Limits are explicit". The mutable default is FR-093 and is still open. The printed commit and the receipt (`bootstrap.py:571-579`) give provenance after the fact; they do not prevent anything. On the target side, `validate_paths` (`bootstrap.py:270-290`) refuses symlinks, hardlinks, reparse points and non-regular files on every managed path. `promote` (`:185`) refuses if the target changed after preflight, but the check is cooperative and a TOCTOU window remains, as the design says. `deployment_plan` refuses: changed named hook bundles (`checked_named_merge`, `:346-357`), removals (`observe_remove`, `:412-419`), writes to an existing `.gitattributes` (`:405-410`), and unreported archive overwrites (`:439-446`). A control REWRITE becomes REVIEW (`:447-454`). In `delivery.py` the task slug is `[a-z0-9][a-z0-9-]{0,63}` (`state_path`, `:377-380`), so `../other` is refused. Tests: `test_managed_symlink_parent_is_refused_before_external_or_partial_writes`, `test_managed_hardlink_is_refused_before_altering_external_user_file`, `test_managed_windows_junction_is_refused_before_external_writes`, `test_target_change_during_preflight_is_refused_instead_of_overwritten`, `test_source_named_custom_hook_bundle_is_refused_without_losing_disable_or_metadata`, `test_source_selected_stale_removal_requires_review_without_a_duplicate_path_map`, `test_product_crlf_git_policy_requires_review_without_semantic_or_byte_changes`, `test_powershell_product_safety_check_requires_review_and_stays_active`, `test_differing_regular_archives_refuse_without_any_target_writes` (preservation), and the `../other` assertion in `test_delivery.py`. **S (spoofing):** the source's identity is a URL string. Nothing authenticates the publisher beyond the Git transport — transferred, not mitigated in code. A `delivery.py` gate receipt carries self-declared `actor` and `source` strings (`resume`, `delivery.py:754-776`). The author-cannot-clear check compares actor strings (`:771`), so the same agent under a new name passes. Accepted: the design states that labels are cooperative bookkeeping, not authentication. `test_original_author_cannot_clear_repair_by_a_different_author` and `test_invalid_actor_and_consent_authority_are_fail_closed` pin the string checks, not authentication. **R (repudiation):** `docs/ai-forward-pack/bootstrap-receipt.json` records the repository, requested ref, commit and pack revision (`:571-575`). A checkpoint's `integrity` field is an unkeyed sha256 of its own content (`save`, `delivery.py:410`; `load`, `:624-627`). It detects accidental corruption, not a deliberate rewrite, because anyone who can write the file can recompute the hash. Accepted ("Hashes detect drift"). Test: `test_drift_and_integrity_refusals_do_not_rewrite_checkpoint`. **I (information disclosure):** URLs with credentials, a query or a fragment are refused before Git runs (`bootstrap.py:510-518`), so a token cannot reach error output or the committed receipt (`test_credential_repository_url_is_rejected_without_leak_or_target_writes`). The check applies only to URLs containing `://`. An scp-form `user@host:path` is not inspected: it carries a username, not a password, and the username then lands in the committed receipt. No test. Checkpoints, which hold the raw and compiled intent, live under `.git/ai-forward/delivery` or `$XDG_STATE_HOME`, never in the tracked tree (`local_area`, `delivery.py:363-375`). A `--state-root` inside or above the project is refused (`test_unsafe_state_root_cannot_hide_project_or_follow_symlink`). **D (denial):** every child process runs under a timeout and its process tree is killed on expiry (`run`, `bootstrap.py:83-119`; `test_process_timeout_terminates_child_before_late_side_effect`). A lock left behind by a hard kill blocks the task until a human removes it (`locked_execute`, `delivery.py:1030-1043`, "checkpoint busy", asserted in `test_delivery.py`). This is intended: the design asks for inspection, not automatic clearing. **E (elevation):** **not mitigated, accepted.** The remote source's code runs with the operator's full privileges. `pack-apply.py` is executed in-process for the plan (`deployment_plan`, `:319-322`) and as a child for apply (`pack`, `:122-145`), and the source's `repo_identity` is executed too (`:543-547`). The design records this: the installer "executes the selected trusted source". Target code is kept out of that process. POSIX re-execs with `-I -B` (`:36-49`). Windows filters `sys.path` to `base_prefix` and clears the `PYTHON*` variables (`:17-35`). Every child runs `-I -B` with `PYTHONPATH`, `PYTHONHOME` and `PYTHONSTARTUP` removed (`:84-93`). The source checkout runs with hooks disabled (`:540-542`). Tests: `test_dry_run_cannot_execute_target_stdlib_shadows`, `test_apply_cannot_execute_target_sitecustomize_from_pythonpath`, `test_saved_wrapper_entry_cannot_execute_adjacent_stdlib_shadows`, `test_uv_remote_entry_ignores_target_pythonpath_stdlib_shadows`, `test_source_checkout_does_not_execute_user_global_git_hooks`, `test_ambient_git_path_overrides_cannot_redirect_installation`. Residual: the target's own `.git/config` (for example `core.fsmonitor`) still applies to the `git rev-parse`, `clone --shared` and `ls-files` calls made in the target (`:242`, `:252`, `:374`). That is the same trust as the operator running Git there; accepted, no test. `pack/adapters/hooks/run-hook.sh` falls back to `uv run --no-config --no-project --python '>=3.10'` without `--no-python-downloads`, and the README command does the same. uv's default may therefore download an interpreter at install time or hook time (Inferred from uv's documented default, not observed; FR-093). Not mitigated; no test. **Design vs code:** they agree that a remote install trusts its source. The default is still mutable `main`, and no code path warns when an unpinned ref is used. Negative tests are named per threat above. Untested: the scp-form URL, the uv interpreter-download policy, stale-lock recovery, and actor renaming (accepted).

## Privacy analysis (LINDDUN-lite)
| Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|
| Bootstrap → source repository (network) | D: `git clone`/`git fetch` of the source (`bootstrap.py:main`; default `https://github.com/timianmalloo/ai-forward.git`). The target project is never uploaded; the host sees ordinary Git transport metadata | mitigate | `GIT_TERMINAL_PROMPT=0` (`run`). URLs carrying credentials, a query or a fragment are refused before Git runs, but only for `://` URLs; scp-style `user@host:path` is not checked (it cannot carry a password). | The clone lives in a `TemporaryDirectory`, removed on exit. |
| Bootstrap → `docs/ai-forward-pack/bootstrap-receipt.json` | I: source URL (or the literal `local` for `--source`), requested ref, commit, pack revision | accept | No local path, user name or machine identity is written. | Tracked if the project commits it; Git retention. |
| `/deliver` checkpoint → local state | D: raw prompt verbatim (`delivery.py:execute`), compiled contract with its raw audit entry, pause question text, absolute project root / git dir / common dir (`identity`), absolute audit root | mitigate | Every prompt field copies an entry already committed in `docs/audit/audit-log.jsonl` (`compilation`): no new collection. Evidence and inputs are stored as path + SHA-256 only (`file_record`, `capture_file`); the workspace snapshot stores a digest of file hashes, not contents (`snapshot`). | Git projects: `<git-dir>/ai-forward/delivery/<task>.json` (`local_area`), untracked, per clone. Plain projects: `$XDG_STATE_HOME` or `~/.local/state/ai-forward/delivery/<sha256(identity)>/`. **No delete verb exists** (the only `unlink` is the writer lock), so deletion is by hand, and plain-project state survives deleting the project. |

No new personal-data category. The checkpoint is linkable to a project by its absolute path and to a prompt by its audit id, both already linkable in the committed audit log. Neither the bootstrap nor `delivery.py` calls a model or a third-party service; the only network flow is the Git fetch of the selected source. The design's interpreter supply through `uv` may also download a Python build when none is installed; that fetch is uv's, not ours, and was not observed (Inferred). Unawareness and non-compliance: nothing beyond the existing audit log. Rights path: delete `<git-dir>/ai-forward/delivery/` or the `~/.local/state/ai-forward/delivery/<digest>/` directory, then `git rm` the receipt.
