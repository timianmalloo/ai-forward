---
id: forensic-review-rev108-backlog
title: "Forensic review backlog — ai-forward revision 108 (FR-086 … FR-102)"
type: doc
status: proposed
owner: "@timianmalloo"
phase: "assessment"
tags: [forensic-review, backlog, rev108, governance, security]
links:
  - { to: forensic-review-rev108, rel: relates-to }
  - { to: forensic-review-rev59-backlog, rel: relates-to }
  - { to: defect-classes, rel: relates-to }
  - { to: plan-ci-speed-and-required-checks, rel: relates-to }
review-by: "2027-04-17"
summary: >-
  Seventeen items from the revision-108 forensic review, FR-086 to FR-102, each with evidence,
  falsifiable acceptance criteria and a next skill. No P0 or P1. Four P2: shared-temp byte-code
  cache, manual-only CI, git-identity guard bypasses, and an ownership hook that grants writes.
  Eleven P3. Two were resolved during the review: FR-101 (the hook's needless prompts, PR #12)
  and FR-102 (bundle changes shipped without a revision bump, revision 109). FR-087 was resolved
  on 2026-10-18. FR-086 and FR-088 were resolved in revision 114, and FR-089 by owner ruling. The
  rest await triage.
---

# Forensic review backlog — revision 108

**Status: `proposed`.** FR-086, FR-087, FR-088, FR-101 and FR-102 are **resolved**, FR-089 by owner ruling; FR-099 is partly resolved (2026-10-17/18). The rest are not
implemented and await triage. Open items carried from revision 59 (FR-078 … FR-085) stay in
`forensic-review-rev59-backlog`; their current state is tabled in the review.

Priorities: **P0** exploitable / data-loss / irreversible · **P1** high-likelihood correctness,
security or migration risk · **P2** material maintainability, operability or governance debt ·
**P3** localized hygiene.

---

## Phase 1 — Make CI automatic again (P2)

### FR-087 · risk · P2 — Every workflow runs only on manual dispatch
- **Location:** `.github/workflows/*.yml` (`on:` blocks); commit `156943d`.
- **Evidence:** all five workflows declare only `workflow_dispatch`. `156943d` removed the
  `push` / `pull_request` triggers from `docs.yml`, `pack-consistency.yml` and `pages.yml`.
- **Consequence:** with FR-082 (no required check), no push or PR runs CI unless someone
  dispatches it. A red `main` is caught only by a local gate run.
- **Remediation:** execute `plan-ci-speed-and-required-checks` (P0–P9): restore PR triggers on a
  fast ring, then make that ring a required check.
- **Acceptance:** (a) opening a PR starts `pack-consistency` with no manual step; (b) branch
  protection lists it under `required_status_checks`; (c) a deliberately red PR cannot merge.
- **Dependencies:** FR-082, FR-094. **Owner:** SRE. **Next skill:** `/implement` on the plan.
- **Resolved 2026-10-18** (CI-speed P5–P7). (a) Opening PR #17 started `pack-consistency` and
  `docs` with no dispatch. (b) Protection requires `consistency`, `consistency-windows` and
  `consistency-macos`, bound to the GitHub Actions app, `strict`. (c) Deliberately red PR #18 was
  `BLOCKED` and `gh pr merge` refused. This also closes rev59's FR-082.

## Phase 2 — Trust boundaries (P2)

### FR-088 · issue · P2 — The git-identity guard misses six identity-setting forms and over-matches text
- **Location:** `pack/adapters/hooks/git-identity-guard.py:55-60` (`GIT_IDENTITY_SET_RX`).
- **Evidence (executed):** `evaluate()` allows `git -C . config user.name X`,
  `git config --file … user.email X`, `git config --worktree user.name X`,
  `git config set user.name X`, `GIT_AUTHOR_NAME=… git commit`, and `git commit --author=…`.
  It blocks `echo 'docs: git config user.name X is forbidden' > notes.md`. Table in the review.
- **Violated contract:** AL0.2 / PK-07 — never invent a git identity.
- **Consequence:** the control passes the commands it exists to stop, and a false block on
  documentation text teaches the user to switch it off.
- **Remediation:** tokenize with `shlex`, skip leading `VAR=` assignments and git global
  options (`-C`, `-c`, `--git-dir`, `--work-tree`); block a `config` write of `user.*` under any
  scope or `set` form, `--author` on `commit`, and `GIT_AUTHOR_*` / `GIT_COMMITTER_*` assignment.
  Match only command words, never quoted arguments.
- **Acceptance:** each row of the probe table becomes a test with the correct verdict, observed
  failing first.
- **Owner:** Security & Identity. **Next skill:** `/implement`.
- **Resolved 2026-10-19** (revision 114). The guard splits simple commands with `shlex` and judges
  command words. `ProbeTableTests` holds the six probe rows and 19 more setting forms (refused),
  and the `echo` row with 11 more mentions (allowed); it was **observed red** on 21 before the fix.
  An unsplittable command falls back to the old pattern. Class PK-07 (instance added).

### FR-089 · risk · P2 — The ownership hook's `allow` skips the user's permission prompt
- **Location:** `pack/scripts/coord-core.py` `cmd_hook` — the `"coordination: {} path(s) free
  or mine"` and `"no write to a coordinated path"` returns.
- **Evidence:** for a free in-repo path the Claude host prints `permissionDecision: "allow"`.
  `hook_response` already treats agy differently ("ownership is not permission to autoapprove a
  tool") and Copilot gets `{}`. Claude gets an explicit grant.
- **Consequence (Inferred):** a Claude Code PreToolUse `allow` bypasses the permission prompt,
  so a user in default mode is not asked before in-repo edits. The hook needed only not to
  refuse; it grants instead.
- **Confirming check:** in a default-mode Claude Code session in a coordinated repo, edit a free
  path. A prompt means the inference is wrong and this item drops to P3 hygiene.
- **Remediation:** return no decision (`{}`) wherever ownership is satisfied, as WT-E now does
  for outside paths; keep `deny` for held leases and PRIM-A.
- **Acceptance:** tests assert `{}` for free and own-lease paths on the Claude host; held and
  primary paths still `deny`.
- **Owner:** Security & Identity. **Next skill:** `/investigate` then `/implement`.
- **Resolved 2026-10-19 by owner ruling, not by the remediation above.** The owner ruled that an
  edit never asks for permission: the `allow` on a checked free or own path is the intent. The
  same ruling removed the hook's remaining `ask` (revision 114, class EDIT-ASK). Every "not
  checked" condition answered `ask` on Claude, and Claude Code prompts on `ask` even in bypass
  mode. Now an unverifiable edit gets `{}` (the session's mode decides), and a suspect path gets
  `deny`. `EditsNeverPromptTests` pins the `allow` this item questioned.

### FR-086 · risk · P2 — Hook byte-code cache in a fixed directory under shared temp
- **Location:** `pack/adapters/hooks/dispatch.py:142`.
- **Evidence:** `sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "ai-forward-pycache")`.
- **Consequence (Inferred):** on a multi-user POSIX host `/tmp` is shared. Another user can
  create `ai-forward-pycache` first and plant `.pyc` files that the hooks then import. A
  Windows temp directory is per-user, so the exposure is POSIX only.
- **Remediation:** a per-user, owner-only directory (for example under
  `$XDG_CACHE_HOME` or `~/.cache`, created mode `0700` and verified owned by the current uid), or
  `sys.dont_write_bytecode = True` in hook processes.
- **Acceptance:** a test pre-creates the directory as foreign or world-writable and asserts the
  hook refuses to use it.
- **Owner:** Security & Identity. **Next skill:** `/implement`.
- **Resolved 2026-10-19** (revision 114). The cache is `$XDG_CACHE_HOME/ai-forward/pycache` (else
  `~/.cache/…`), created `0700`. On POSIX it is refused unless it and its parent are directories
  owned by the current uid with no group or other write; with no usable cache no byte code is
  written. `BytecodeCacheIsPrivate` plants a world-writable directory at each level (POSIX
  runners; Windows profiles are per user) and was **observed red** (`AttributeError`) first.

## Phase 3 — Operability and portability (P3)

### FR-094 · risk · P3 — The Windows CI job grew to ~47 minutes
- **Evidence:** `pack-consistency.yml:165` (`windows-latest`). 46.7 min on run 38983040683 and
  49.6 min on run 38953998178 (both PR #6 branches), against 8.6–12.0 min before. Not yet
  measured on `main`.
- **Remediation:** covered by the CI plan; profile first (CE1).
- **Acceptance:** a measured Windows-job duration on `main`, and a target recorded in the plan.
- **Next skill:** `/session-profiler` or the plan's profiling step.

### FR-099 · issue · P3 — Ten tests fail for environmental reasons instead of skipping
- **Evidence:** the same 10 failures on `c267bd4` and `332c297`: 5 symlink tests raise
  `WinError 1314` (no Developer Mode), 2 `test_delivery_session_start` tests read
  `AGENT_SESSION` leaked from `.claude/settings.local.json`, 3 `test_uv_hook_launcher` tests
  cannot spawn `sh`.
- **Consequence:** a permanently red gate 3 on Windows hides a real new failure among known ones.
- **Remediation:** skip on a failed symlink-capability probe; clear `AGENT_SESSION` in those
  tests' environment; skip the launcher tests when `sh` is not on `PATH`.
- **Acceptance:** gate 3 is green on this machine with Developer Mode off.
- **Owner:** Test Architect. **Next skill:** `/implement`.
- **Partly resolved 2026-10-18.** The `AGENT_SESSION` leak is fixed for every test: the
  `docs_explorer` conftest drops the harness's `AGENT_SESSION` / `AGENT_HOST` / `AGENT_NAME`.
  Since revision 110 the symlink and `uv` tests pass or skip on the owner's machine, and the
  local suite is fully green. **Still open:** no general skip guard for a host without symlink
  privilege or a POSIX `sh`, so acceptance holds on this machine, not in general.

### FR-100 · issue · P3 — Native hosts refuse every write outside the repository
- **Evidence:** `_not_checked` returns `deny` for codex, grok, agy and copilot;
  `test_native_hosts_still_fail_closed_on_an_outside_path` pins it.
- **Consequence:** on those hosts an agent cannot write user memory or a scratch directory at
  all. WT-E fixed this for Claude only, because the native fail-closed rule is a recorded
  design, not an accident.
- **Remediation:** decide per host whether "no decision" is expressible (Copilot `{}` and agy
  `""` already are); where it is, apply WT-E. Record the decision.
- **Acceptance:** a decision note per host, and tests matching it.
- **Next skill:** `/design-slice`.

### FR-097 · todo · P3 — The delivery checkpoint lock has manual-only recovery
- **Evidence:** `pack/scripts/delivery.py:1007-1018` (`O_CREAT|O_EXCL`, no pid or age check);
  `checkpoints.md:81` tells the operator to remove a stale lock by hand.
- **Consequence:** a crash blocks the task until a human notices. Deliberate, but undiagnosed:
  the error does not say how old the lock is or which pid wrote it.
- **Remediation:** write pid and time into the lock; report both in the "busy" error; keep
  breaking it manual.
- **Acceptance:** the busy message names pid and age; a test covers it.

### FR-098 · risk · P3 — `session-checks.json` is committed config that runs commands
- **Evidence:** `pack/adapters/hooks/session-start.py:83-89,134-143` runs up to five declared
  argv entries with `subprocess.run`; `pack-apply.py:268` un-ignores the file;
  `hooks/README.md:101-105` says it runs with same-user project trust, not in a sandbox.
- **Consequence:** cloning a repo and opening a session runs whatever a contributor committed
  there, before any review in that session.
- **Remediation:** pin a hash of the file at first approval and refuse to run a changed file
  until re-approved, or require a per-user opt-in outside the repo.
- **Acceptance:** a changed `session-checks.json` does not execute until approved; tested.
- **Owner:** Security & Identity. **Next skill:** `/design-slice`.

### FR-092 · risk · P3 — Hook state and installer writes follow links
- **Evidence:** `reread-guard.py:53-72` writes a predictable
  `<tempdir>/ai-forward-reread-guard-<session>.json` via `open(tmp, "w")` then `os.replace`,
  with no link check; `pack-apply.py:542-547` (`_write`) opens the destination with no link or
  containment check (only hook-settings files are checked, lines 71 and 771).
- **Consequence:** a planted link at the `.tmp` name, or a junction in a target parent
  directory, redirects the write.
- **Remediation:** `O_EXCL` / `O_NOFOLLOW` for the temp file in a per-user directory; resolve and
  contain every `pack-apply` destination under the target root.
- **Acceptance:** tests plant each link and assert the write is refused.

### FR-093 · risk · P3 — One-command setup runs from mutable `main`
- **Evidence:** `README.md:46` runs
  `uv run … https://raw.githubusercontent.com/timianmalloo/ai-forward/main/bootstrap.py`;
  `bootstrap.py:527` defaults the ref to `main`; no `--no-python-downloads`.
- **Consequence:** what a user installs changes with every push. uv may also fetch an
  interpreter (Inferred from uv's default; not observed).
- **Remediation:** document a tagged or SHA-pinned command as the default, keep `main` as an
  explicit opt-in, and state the interpreter policy.
- **Acceptance:** README's primary command names a tag or SHA.

### FR-090 · issue · P3 — Documented counts are stale
- **Evidence:** `architecture.md` says revision 53 (lines 16, 47), "24 skills" (61), "10 gates"
  (158). Actual: revision 108, 30 skills, 18 gates. `AGENTS.md:11` says "ten gates";
  `.github/copilot-instructions.md:21` and `docs/project-memory.md:59` say "nine".
- **Remediation:** regenerate `architecture.md` under `/document`; replace prose gate counts with
  a reference to `verify-bundle.ps1`, or have `check-consistency.py` check them.
- **Acceptance:** `check-consistency.py` fails on a wrong gate count, observed failing first.
- **Next skill:** `/document`.

### FR-091 · issue · P3 — CI's gate steps are hand-copied from `verify-bundle.ps1` and drift
- **Evidence:** the ubuntu job splits gate 8 into two steps and runs 7 → 8 → 8b; the script runs
  8b → 7 → 8. The OS subsets on Windows and macOS are documented as deliberate.
- **Remediation:** have CI call `verify-bundle.ps1` (or a gate list it exports), with
  per-OS exclusions declared in one place.
- **Acceptance:** adding a gate to the script changes CI with no workflow edit.

### FR-095 · todo · P3 — No ADR records the six-harness support decision
- **Evidence:** `docs/adr/0001–0013` cover no harness-support decision; Muse appears in no ADR
  or note.
- **Remediation:** one ADR: which harnesses, why, the per-harness cost (surfaces, gates,
  `AGENTS.md` bytes), and the criteria to add or drop one.
- **Next skill:** `/define-architecture` (ADR only).
- **Resolved 2026-10-19** by `adr-0014-meet-the-developer-in-their-harness`. The owner's framing: harness
  support is not a cost to justify but the pack's fundamental purpose, to meet the developer where they
  are. The ADR records the six supported harnesses, the obligations (a native surface, the host's own
  shapes, verified on the host, parity as the floor), and that a harness is never dropped for cost.

### FR-096 · todo · P3 — `.codex/hooks.json` has no pack source file
- **Evidence:** no file under `pack/` is copied to it; `sync-pack.ps1:391-395` refreshes it only
  if it exists; its PreToolUse entry is produced by `coord-core.py hook --config --host codex`.
- **Consequence:** a fresh clone without the file never gets it from sync; its content is
  defined in code, not in the source tree the rest of the install comes from.
- **Remediation:** generate it unconditionally in sync, or add a source file and gate it under
  gate 2.
- **Acceptance:** deleting `.codex/hooks.json` and running sync recreates it.

## Found 2026-10-19 — the four designs' security and privacy sections

Writing the missing STRIDE and LINDDUN sections for `decision-interrogation`, `one-command-adoption`,
`session-profiler` and `skill-evolution` (Security & Identity and Privacy lenses, from the code)
surfaced these. None is fixed.

### FR-103 · risk · P1 — The session profiler commits secrets from shell commands unscrubbed
- **Location:** `pack/scripts/session-profile.py` `shell_shape_counts` (piped-gate and failed-heredoc
  evidence, 90 chars), `profile_copilot` / `profile_claude` (prompt previews, 160 chars).
- **Evidence (executed):** `shell_shape_counts([("t1", "export GH_TOKEN=ghp_PLANTED… && python -m
  pytest tests -q | tail -5")], {})` returned `gate piped: export GH_TOKEN=ghp_PLANTED… …` with the
  token intact. `session-profile.py` has no scrub; `dream.py`'s `scrub` runs only on what `/dream`
  mines. The design's failure-mode row claimed a review-before-commit step the skill does not have
  (corrected in the design).
- **Consequence:** a secret typed into a gated shell line, or into a prompt, lands in
  `docs/profiles/<sp-id>/profile.{json,md}`. Here those are committed and published on Pages.
  A pattern scan of the 8 committed profiles on 2026-10-19 found no token, key or password, so
  nothing is exposed now.
- **Remediation:** apply one scrub (reuse `dream.py`'s) to every prompt, title and evidence string
  before writing.
- **Acceptance:** a test plants `ghp_…`, `KEY=…` and a private-key header in a prompt, a piped gate
  and a failed heredoc, and asserts that none appears in either output. Observed failing first.
- **Owner:** Security & Identity. **Next skill:** `/implement`.
- **Resolved 2026-10-19** (revision 115). `cmd_profile` scrubs every string with `dream.py`'s `scrub`, which gained `github_pat_` and private-key patterns, before `--json-only`, both files and the index. It refuses to write if the scrubber is missing. `NoSecretReachesAProfileTests` plants a token, a fine-grained PAT, a password, a key header and an email across the prompt, title, piped gate and failed heredoc, and was **observed red** on all five first. On 8 real sessions the scrub fired only on two email addresses. Residual: pattern-based. New class SCRUB-A.

### FR-104 · risk · P2 — A consuming repo's profiles are committed with no notice or opt-in
- **Evidence:** `cmd_profile` writes prompt prefixes, absolute paths, session titles and command
  fragments into the target repo's tracked `docs/profiles/`. `note-20261017-session-profiles-published`
  covers this repository only. The skill tells the operator neither what the output carries nor
  that it may be published.
- **Remediation (owner decision):** a notice plus opt-in, or a git-ignored default output path
  for consuming repos. The owner also confirms whether command and tool-output fragments fall under
  the 2026-10-17 ruling (its re-open trigger 3).
- **Owner:** Privacy & Data Governance. **Next skill:** owner ruling, then `/implement`.
- **Resolved 2026-10-19 by owner ruling** (*"just this pack"*; revision 115). Only the pack source repository commits profiles by default. Elsewhere they go to the untracked `<git-dir>/ai-forward/profiles/` and the run says so; `--publish` writes `docs/profiles/` with a tracked notice. `ProfilesStayLocalOutsideThePackTests`, observed red first. The ruling is recorded in `note-20261017-session-profiles-published` (addendum).

### FR-105 · risk · P3 — The profiler runs code found in the repository it writes into
- **Evidence:** `_audit` runs the target repo's own `audit-log.py` with `sys.executable` and no
  `-I`, and `repo_identity` runs `git` in every `--repo`, so that repo's `.git/config` applies.
- **Remediation:** run the profiler's sibling `audit-log.py` with `-I`, or record the trust assumption.
- **Next skill:** `/implement`.

### FR-106 · risk · P3 — Decision interrogation does not record who answered
- **Evidence:** the four authoring skills declare `runs_as: either`. As a Sub-Agent, the skill's
  "human" is its parent, and none of the four cites CO-S2. A parent agent's answer enters the
  artifact looking like a human decision.
- **Remediation:** DI4 sends any answer not given by the human back as a decision request, and the
  artifact records each answer's source.
- **Next skill:** `/implement` (skill text plus a contract test).

### FR-107 · todo · P3 — `/deliver` checkpoints have no deletion path
- **Evidence:** `delivery.py` has no forget verb; the only `unlink` is the writer lock. Plain-project
  state under `~/.local/state/ai-forward/delivery/` outlives the project.
- **Remediation:** a `delivery.py forget <task>` verb, or document the path.
- **Next skill:** `/implement`.

### FR-108 · todo · P2 — Local LLMs have no support
- **Evidence:** no file under `pack/`, `docs/adr/` or `docs/notes/` mentions Ollama, LM Studio, llama.cpp,
  vLLM or a local model. The owner codes with local LLMs (ADR-0014).
- **Consequence:** in a repo with the pack applied, a local-model session gets whatever its host happens
  to load, with no path map, no tuning for smaller context windows, and no verification.
- **Remediation:** first establish which harness or tool runs the local models and how it discovers
  instructions and skills (Spike Protocol), then give it a native surface under ADR-0014's obligations.
- **Deferred 2026-10-19 by the owner** ("I will work through that later"). Do not start until the owner
  names the local-model setup.
- **Owner:** the owner (which setup), then Domain Researcher. **Next skill:** `/investigate` (spike), then
  `/implement`.

## Resolved during the review

### FR-101 · issue · P3 — The edit-ownership hook prompted for writes it does not govern — **resolved**
- **What happened:** WT-D — writes from the primary into a linked worktree of the same
  repository got `ask`. WT-E — writes outside every checkout (user memory, a scratchpad) got
  `ask`, which forces a prompt even in bypass mode.
- **Resolution (PR #12, `4c5cf91`, `b808e73`):** sibling worktrees are checked in place; outside
  paths get no decision on the Claude host; an in-tree alias that escapes still fails closed.
  Both classes are `controlled` in `defect-classes.md`, with red-first tests.
- **Correction (revision 111):** the WT-E alias check compared spellings, so on macOS and Windows
  runners an escaping in-tree alias got no decision instead of failing closed. The first CI
  baseline on `main` found it; fixed as WT-E2.

### FR-102 · issue · P2 — Bundle changes shipped without a revision bump — **resolved**
- **What happened:** PR #12 (`coord-core.py`) and the Muse re-measure (`context-budget.json`,
  `muse-surface.md`) changed deployed files at revision 108. pack-apply resolves a merge base
  from the commits whose INSTALL text matches the installed copy (`pack-apply.py:521-538`), so
  revision 108 named two versions of each file. `test_bootstrap` failed with CONFLICT on
  `context-budget.json`, and a same-revision refresh keeps the old bytes as a "local deviation"
  (`pack-apply.py:576-579`), so the hook fix could not reach any consumer.
- **Resolution:** revision 109 records all three changes and archives 108.
  `tests/docs_explorer/test_install_revision_bump.py` (gate 3) fails when the newest commit
  touching `pack/` does not touch `pack/adapters/INSTALL.md`, observed failing first on
  `332c297`. Class PACK-W, `controlled`. Limit: a depth-1 clone passes vacuously.

## Summary

| Id | Priority | Kind | Title | Next skill |
|---|---|---|---|---|
| FR-087 | P2 | risk | CI runs only on manual dispatch | resolved |
| FR-088 | P2 | issue | Git-identity guard bypasses | resolved |
| FR-089 | P2 | risk | Ownership hook `allow` skips the prompt | resolved (ruling) |
| FR-086 | P2 | risk | Byte-code cache in shared temp | resolved |
| FR-094 | P3 | risk | Windows CI job ~47 min | profile |
| FR-099 | P3 | issue | Ten environmental test failures | partly resolved |
| FR-100 | P3 | issue | Native hosts refuse outside writes | `/design-slice` |
| FR-097 | P3 | todo | Lock with manual-only recovery | `/implement` |
| FR-098 | P3 | risk | Executable session-check config | `/design-slice` |
| FR-092 | P3 | risk | Link-following writes | `/implement` |
| FR-093 | P3 | risk | Setup from mutable `main` | `/implement` |
| FR-090 | P3 | issue | Stale documented counts | `/document` |
| FR-091 | P3 | issue | Hand-copied CI gate list | `/implement` |
| FR-095 | P3 | todo | No six-harness ADR | resolved (ADR-0014) |
| FR-096 | P3 | todo | `.codex/hooks.json` unsourced | `/implement` |
| FR-101 | P3 | issue | Hook prompted outside its domain | resolved |
| FR-102 | P2 | issue | Bundle change without a revision bump | resolved |
| FR-103 | P1 | risk | Profiler commits secrets unscrubbed | resolved |
| FR-104 | P2 | risk | Consumer profiles with no notice or opt-in | resolved (ruling) |
| FR-105 | P3 | risk | Profiler runs the target repo's code | `/implement` |
| FR-106 | P3 | risk | Decision answers carry no source | `/implement` |
| FR-107 | P3 | todo | No checkpoint deletion path | `/implement` |
| FR-108 | P2 | todo | Local LLMs have no support | deferred (owner) |
