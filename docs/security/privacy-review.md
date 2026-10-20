---
id: privacy-review
title: "Privacy Review"
type: privacy-review
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [privacy, linddun, data-governance]
links:
  - { to: design-session-profiler, rel: documents }
  - { to: design-reader-first-handbook, rel: documents }
  - { to: architecture, rel: documents }
  - { to: forensic-review, rel: documents }
  - { to: design-aiforward-cli, rel: documents }
  - { to: design-coord-core-phase1, rel: documents }
  - { to: design-agent-coordination-doctrine, rel: documents }
  - { to: design-typed-seam-requests, rel: documents }
  - { to: design-leader-designation, rel: documents }
  - { to: design-message-layer, rel: documents }
  - { to: design-multi-harness-runner, rel: documents }
  - { to: design-native-ownership-enforcement, rel: documents }
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
  Repo-level privacy posture for the pack-evolution tooling: the CLI and doctor touch no personal
  data; project memory may incidentally record handles/names (no special-category data, mitigated
  by the scrub); the scrub is itself a privacy control; Docs Explorer navigation state remains
  local. The reviewed model-orchestration experiment was reverted before an executable
  provider-routing boundary was added.
---

# Privacy Review

*The repo-level rollup of every component's privacy analysis (design SKILL Stage 3, LINDDUN-lite). The register below is **generated** — refresh it with the script bundle, never by hand:*

```bash
python3 docs/ai-forward-pack/scripts/docs-graph.py rollup --heading "Privacy analysis (LINDDUN-lite)" --type design
```

## 1. Personal-data posture

- **Reader handbook** — curated public explanatory content and fictional examples.
  Search stays in browser memory; there are no cookies, analytics, model calls or
  remote image loads. The existing publish boundary excludes raw operational records.

- **aiforward-cli** — no personal data (forwards argv to child processes).
- **pack-doctor** — no personal data (reads frontmatter metadata, file presence, marker counts; never document bodies).
- **project-memory** — *may* incidentally record handles/names that already appear in commits. Rule: **no special-category data** in memory; emails redacted by the scrub; retention = life of the repo (the value is permanence); rights path = git history rewrite if required.
- **rai-and-scrub** — the scrub is a **privacy control** (redaction); it holds nothing and transmits nothing (purely local).
- **Docs Explorer** — processes committed project documentation and local/session navigation
  state only; no remote analytics, model egress, or new personal-data category.
- **multi-harness-runner** — user-authorized delegation sends compiled work to explicitly
  selected installed harnesses under their existing provider policies. Private prompts stay
  in common-git run metadata; tracked coordination events contain bounded operational fields,
  not conversations or credential values. No automatic provider selection is introduced.
- **model-orchestration (reverted)** — the standard and lookup were removed after review; no
  active pack instruction now routes repository/workspace payloads between providers.

## 2. Reverted model-orchestration forensic disposition

| Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|
| Skill context / authored artifact → selected author model | **L/I/N** — proposed routing lacked a data-sensitivity axis | retired by removal | No automatic model-routing instruction remains. A future proposal must introduce data class/provider policy before dispatch. | No pack-owned retention was added |
| Full authored artifact → distinct hard-veto reviewer model | **L/I/N/D** — the proposal could force a cross-provider hop | retired by removal | Existing persona review returns to the pre-experiment host/user-selected model behavior. | Provider/host terms remain outside pack control |
| Routing decision → audit log | **N/U** — proposed evidence fields were unsupported | retired by removal | No routing evidence is required because no routing capability remains. | Audit retains the review/revert decision history |

No personal data was found in the reviewed orchestration artifacts themselves. The proposed
downstream dispatch risk was retired by removing the capability, not by accepting it.

## 3. Generated register (LINDDUN-lite, rolled up from the designs)

<!-- BEGIN GENERATED: docs-graph.py rollup -->
| source | Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|---|
| [design-agent-focus-controls](design/agent-focus-controls.md) | Audit log → `selfcheck` (read) | D: the log holds each substantive turn's verbatim prompt and its session id; `selfcheck` reads every entry | mitigate | Output carries only `shortname`, `id`, `done_when`, `summary`, budget counts and fan-out numbers (`cmd_selfcheck`, `audit-log.py:1263-1324`). The `prompt` field is never printed (Verified by reading). | No new store; `selfcheck` writes nothing. The log keeps its own Git retention. |
| [design-agent-focus-controls](design/agent-focus-controls.md) | `done_when` / `summary` → stdout or CI log | I: free text written by an agent may quote a path, a name or a pasted value | accept | Truncated to 60 / 80 characters in text mode; full in `--json`. No scrub. The same text is already committed in the log. | Terminal only, or the CI host's log retention where a repo wires `--gate` into CI. |
| [design-agent-focus-controls](design/agent-focus-controls.md) | `--session <id>` filter | L: links one session's turns together | accept | By design. Session ids are pseudonymous work identifiers already in the log. | As the log. |
| [design-agent-focus-controls](design/agent-focus-controls.md) | FC-2 goal-state block → audit `goal` / `done_when` fields | U/I: every substantive turn now records its goal text in a committed store | accept | Work description, not a personal-data category. The verbatim prompt is already recorded (AL5b), so FC-2 adds structure, not a new data class. | Git retention of `docs/audit/audit-log.jsonl`; the only rights path is a history rewrite. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | `coord request add` → `.agents/requests.jsonl` | D/I: free text (`text`, `reason`, `fallback`, `contract`), `from` / `to` role names, session id and agent name (`cmd_request`, `:3067`) | mitigate | The store is git-ignored by `.agents/*` (`.gitignore:28`; `git check-ignore` Verified 2026-10-19). The tracked ledger twin carries id, action, `to` and `deadline_at`, but no text (`_request_twin`, `:3046`). | Lives as long as the local file. No delete verb exists; every action appends. Deletion is removing the file by hand. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Session record → `session list` / `collaborate check` / `summary` | L/I: session id, agent name, worktree, claim paths and timestamps link one session to its work | accept | Already in the tracked ledger `.agents/log/*.jsonl` (re-included by `.gitignore:34`). New writers store the worktree basename (`_worktree_label`, `:2785`). `active_sessions` projects the stored value as is (`:2823`), so legacy rows show an absolute path: 6 tracked ledgers hold `C:/Projects/...` values (Verified by `git grep` 2026-10-19; no home directory was found). | Git retention of the ledger; the only rights path is a history rewrite. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Session-contract template → `docs/collaboration/session-contracts.md` | I: an `owner: "@<owner>"` handle and per-session agent and tool names in a committed doc (`pack/templates/session-contract.template.md:6`, `:21`) | accept | A handle is the same identifier the repo's frontmatter already carries. | Git retention. |
| [design-coord-collaboration-phase4](design/coord-collaboration-phase4.md) | Request text → terminal / model reader | D: request text is shown to whoever runs `request list` or `collaborate summary` | mitigate | Text mode strips control characters and caps length with `_safe` (`:406`, `:3118`); `--json` escapes it. The reader is the same local user. | Terminal only. |
| [design-coordination-runtime-v2](design/coordination-runtime-v2.md) | Linkability and identifiability | Run/worker IDs intentionally link execution; raw prompts and native action details remain private local files. | Sentinel-secret output tests; sanitized native observation records. |
| [design-coordination-runtime-v2](design/coordination-runtime-v2.md) | Disclosure | Permission details and compiled bodies are owner-only mode0600 records in mode0700 directories. | Permissions, symlink, tamper and size negatives. |
| [design-coordination-runtime-v2](design/coordination-runtime-v2.md) | Detectability and unawareness | Pending approval is explicit; no background approval or hidden mailbox input. | Pending/decision events and exact-option CLI tests. |
| [design-coordination-runtime-v2](design/coordination-runtime-v2.md) | Retention | Operator retains completed private run directories until explicitly removed. No new analytics recipient. | Public launch guide documents the local deletion boundary. |
| [design-docs-explorer-grounding-spatial-navigation](design/docs-explorer-grounding-and-spatial-navigation.md) | Committed project docs + local search/selection/context state | **L/D** stable artifact IDs and selected context are visible in the same-device URL/history; no new personal-data category is introduced | mitigate | Same-origin local operation only; no analytics, model egress, cross-user store, or remote state. Existing no-secrets/no-PII rules for committed docs still apply. | Navigation state lasts only in browser history/session and is cleared by leaving the page or removing the hash; document retention follows Git governance. |
| [design-marker-completeness-lint](design/marker-completeness-lint.md) | Code comments → stdout / `--json` | none: no personal data, because the lint reads only code files (`CODE_EXT`, `marker-lint.py:56`; `.md` only with `--include-md`) and prints only the marker comments it finds (up to 200 characters, `:125`) | n/a | A name or secret in a marker comment is already committed repository content. No scrub. | No store; the lint writes nothing. Output lives in the terminal or the CI log. |
| [design-marker-completeness-lint](design/marker-completeness-lint.md) | Lint → third party | none: no egress | n/a | No network module is imported (`:22-26`); no model is called. | — |
| [design-multi-harness-runner](design/multi-harness-runner.md) | Contract and repository work → selected harness | Disclosure follows the selected harness/provider's existing policy | Explicit Owner-selected installed transport; no automatic provider routing or credential copying; bind effective policy |
| [design-multi-harness-runner](design/multi-harness-runner.md) | Prompt bytes → run metadata | Local retention may contain repository work data | Private common-git directory; no raw prompt/conversation in tracked operational facts |
| [design-multi-harness-runner](design/multi-harness-runner.md) | Worker metadata → ledger | Session linkability | Accepted for durable audit; only bounded operational fields, hashes and explicit unknown cost |
| [design-native-ownership-enforcement](design/native-ownership-enforcement.md) | Hook input/environment → local decision facts | L/I: session/path/cwd can identify the local workspace or account directory | mitigate | Existing decision grain with host/cwd metadata; no raw patches or credentials. Export only allowlisted shapes/hashes and cwd-match booleans. | Existing local ledger lifecycle; raw diagnostics remain private and can be removed locally. Committed sanitized proof follows Git retention. |
| [design-native-profile-controls](design/native-profile-controls.md) | Stop and decision projection → local facts/status | Linkability of session/cwd/request IDs | Existing local ledger retention; validated IDs capped32 plus count; no question/body/prompt/config contents. Tests assert sentinel absence. |
| [design-one-command-adoption](design/one-command-adoption.md) | Bootstrap → source repository (network) | D: `git clone`/`git fetch` of the source (`bootstrap.py:main`; default `https://github.com/timianmalloo/ai-forward.git`). The target project is never uploaded; the host sees ordinary Git transport metadata | mitigate | `GIT_TERMINAL_PROMPT=0` (`run`). URLs carrying credentials, a query or a fragment are refused before Git runs, but only for `://` URLs; scp-style `user@host:path` is not checked (it cannot carry a password). | The clone lives in a `TemporaryDirectory`, removed on exit. |
| [design-one-command-adoption](design/one-command-adoption.md) | Bootstrap → `docs/ai-forward-pack/bootstrap-receipt.json` | I: source URL (or the literal `local` for `--source`), requested ref, commit, pack revision | accept | No local path, user name or machine identity is written. | Tracked if the project commits it; Git retention. |
| [design-one-command-adoption](design/one-command-adoption.md) | `/deliver` checkpoint → local state | D: raw prompt verbatim (`delivery.py:execute`), compiled contract with its raw audit entry, pause question text, absolute project root / git dir / common dir (`identity`), absolute audit root | mitigate | Every prompt field copies an entry already committed in `docs/audit/audit-log.jsonl` (`compilation`): no new collection. Evidence and inputs are stored as path + SHA-256 only (`file_record`, `capture_file`); the workspace snapshot stores a digest of file hashes, not contents (`snapshot`). | Git projects: `<git-dir>/ai-forward/delivery/<task>.json` (`local_area`), untracked, per clone. Plain projects: `$XDG_STATE_HOME` or `~/.local/state/ai-forward/delivery/<sha256(identity)>/`. **No delete verb exists** (the only `unlink` is the writer lock), so deletion is by hand, and plain-project state survives deleting the project. |
| [design-reader-first-handbook](design/reader-first-handbook.md) | Raw operational history reaches public prose | Prevent | Curated website source corpus only; publish boundary still excludes raw audit/dream/manifests/working ledgers. |
| [design-reader-first-handbook](design/reader-first-handbook.md) | Search terms become tracking data | Prevent | Search stays in page memory; no analytics, cookies, provider calls or outbound requests. |
| [design-reader-first-handbook](design/reader-first-handbook.md) | Illustrations are mistaken for real customer records | Prevent | Fictional HarborTasks and explicitly illustrative outputs; no customer material or live model runs needed. |
| [design-reader-first-handbook](design/reader-first-handbook.md) | Third-party scripts or images observe reading activity | Prevent | Locally embedded parser; system fonts; image embeddings disabled with visible text fallback; browser request inventory is empty. |
| [design-session-profiler](design/session-profiler.md) | Harness stores → profiler (read) | D: reads the human's prompts, assistant text, tool calls and file paths from `~/.copilot/session-store.db` + `session-state/<id>/events.jsonl`, `~/.copilot/settings.json`, `~/.claude/projects/<slug>/*.jsonl` and their `subagents/agent-*.jsonl` + `.meta.json` | mitigate (partial) | Read-only: SQLite opened `mode=ro` (`session-profile.py:_ro`); JSONL opened read-only (`_load_events`, `read_subagents`). Assistant text and reasoning are measured as character counts only (`profile_copilot`, `profile_claude`) and never copied out. | Source stores are the harness's; the profiler never writes or deletes them. |
| [design-session-profiler](design/session-profiler.md) | Turn prompt → `profile.json` / `profile.md` | I/D: the human's verbatim prompt, truncated to 160 chars (`profile_copilot`, `profile_claude`); 60 chars of it are re-quoted in finding evidence (`detect`) and 48 in the markdown table (`render_markdown`) | accept (owner ruling) | Truncation is the only minimization. **There is no redaction or secret scrub in `session-profile.py`.** | Committed under `docs/profiles/<sp-id>/` and served on Pages (`docs/profiles` is not in `tools/build-pages-bundle.py` `LOCAL_ONLY`). Git retention; the only rights path is a history rewrite (`git-filter-repo`) plus a Pages redeploy. |
| [design-session-profiler](design/session-profiler.md) | Session metadata → profile | L/I: session id, harness title/summary (`sessions.summary`, Claude `ai-title`), absolute `cwd`, absolute `--repo` paths (`cmd_profile`): home directory and other repository names | accept (owner ruling) | None; paths are emitted unshortened. | as above |
| [design-session-profiler](design/session-profiler.md) | Tool calls → profile | D: full paths of files read 3+ times and of instruction files (`rereads`, `instruction_views`); basenames of sub-agent orientation reads; Claude sub-agent task descriptions (`read_subagents`); **shell command text (≤90 chars) for gate-behind-pipe lines and tool-result text (≤90 chars) for failed heredocs** (`shell_shape_counts`) | accept (owner ruling); command and tool-output fragments are a data class the ruling does not name | Truncation only. | as above |
| [design-session-profiler](design/session-profiler.md) | `docs/audit/audit-log.jsonl` → compile section | L: per-session compile measurements (`compile_measurements`) | accept | Numeric aggregates and ids, from a store that is already committed. | The audit log's own retention. |
| [design-session-profiler](design/session-profiler.md) | `--repo A --repo B` → `A/docs/profiles` | D: session data from repository B is written into repository A (`cmd_profile`) | accept (owner ruling, re-open trigger 2) | None; the operator chooses the repos. | A's Git retention. |
| [design-tier2-proof-pack-sections](design/tier2-proof-pack-sections.md) | Operator-questions table → committed Proof Pack | I/D: "Observed once?" asks for evidence of a real observation, so an author may paste a log line or metric sample that carries a user value or a secret | accept | The table asks for the emitting source (`proof-pack.template.md:87-97`), but nothing in the template says to cite a field name rather than a value. The pack's no-secrets / no-PII rule for committed docs is the only control. No test. | Git retention of the Proof Pack; the only rights path is a history rewrite. |
| [design-tier2-proof-pack-sections](design/tier2-proof-pack-sections.md) | Change-surface tables → committed Proof Pack | none: rows name files, members and fields, which is code structure, not personal data (`:67-85`) | n/a | — | Git retention. |

<!-- rolled up from 12 artifact(s) by docs-graph.py rollup on 2026-10-19 -->
<!-- END GENERATED -->

## 4. Accepted-risk register (maintained by hand)

| Accepted risk | Component | Rationale | Residual |
|---|---|---|---|
| Durable retention of handles/names in project memory | project-memory | Permanence is the point of a memory ledger; data is no more than commit metadata already exposes | Low; rights path is `git-filter-repo` if ever required |
| Scrub false negatives leave some PII in history | rai-and-scrub | stdlib-only first-pass | Transferred to Presidio/gitleaks in CI; `git-filter-repo`/BFG for purge |


## 5. Gaps — designs with no LINDDUN analysis

These designs carry no LINDDUN section. Two of them plausibly touch no personal data at all, but *plausibly* is the problem: an unwritten analysis and a written finding of "no personal data" are indistinguishable from here, and only one of them was actually reasoned about. Recorded as upstream gate failures against each design.

**None as of 2026-10-19.** All 31 designs under `docs/design/` carry a `Privacy analysis (LINDDUN-lite)` section (checked with `grep -L`). The last four (`agent-focus-controls`, `coord-collaboration-phase4`, `marker-completeness-lint`, `tier2-proof-pack-sections`) were analysed against the shipped code on 2026-10-19; a design with no personal data says so in a written finding.
