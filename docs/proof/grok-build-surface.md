---
id: proof-grok-build-surface
title: "Proof Pack — Grok Build surface (revision 71)"
type: proof-pack
status: accepted
owner: "@timianmalloo"
phase: "pack-evolution"
tags: [grok, adapters, pack-apply, proof]
links:
  - { to: plan-optimize-graph-grok-surface, rel: implements }
  - { to: note-20260914-grok-build-surface, rel: relates-to }
review-by: "2027-03-13"
summary: >-
  Proof that pack-apply and sync-pack deploy a native Grok Build surface
  (.grok/skills, agents, hooks, rules), that knowledge is not dumped into
  .grok/rules/, and that grok hook payloads (camelCase / target_file) are
  accepted. Red-first unit tests plus pack-doctor and deployed-agent parity.
---

# Proof Pack: Grok Build surface

- **Change:** revision 71 — native Grok Build adapter
- **Spec / design:** `pack/adapters/INSTALL.md` §1.7 · `docs/plans/optimize-graph-grok-surface.md` · `docs/notes/note-20260914-grok-build-surface.md`
- **Tier:** T2
- **Author / date:** Grok Build, 2026-09-14

## Claims & evidence

### Claim 1: a fresh install deploys `.grok/{skills,agents,hooks,rules}`
- **Evidence:** `python -m unittest tests.docs_explorer.test_grok_surface -v` → OK. Live `pwsh tools/sync-pack.ps1` reported `.grok/skills: 27`, `.grok/agents: 23`.
- **Oracle:** `test_fresh_install_deploys_the_grok_surface` fails if specify/implement SKILL.md, orchestrator.md, csharp-developer.md (not `*_agent.md`), hooks json, or grok-surface.md are missing; fails if `.grok/rules/` contains extra markdown.
- **Red observed before green:** yes. First run `AttributeError: grok_agent_filename` before the helper existed; dest paths were absent before `pack-apply.skills/agents/bundle` gained Grok copies.
- **Confidence:** Verified.
- **Residual risk:** Encoding drift between PowerShell `Set-Content` and pack-apply text writes could make `test_source_repo_is_already_current` fail on a future host; it is green on this machine after sync-pack.

### Claim 2: Copilot `_agent` suffix is stripped and `tools:` does not leak
- **Evidence:** same unittest; `grok_agent_filename("csharp-developer_agent.md") == "csharp-developer.md"`; orchestrator.md in the fixture has no `^tools:` line. `check-consistency.py` now counts `.grok/agents/` and flags leaked `tools:`.
- **Oracle:** filename tests fail on suffix retention; INSTALL 1.7 parity loop fails if `.grok/agents` count ≠ 23 or a `tools:` line remains.
- **Red observed before green:** yes. Helper did not exist; consistency check had only two directories.
- **Confidence:** Verified.
- **Residual risk:** A new persona source name that is neither `*.md` nor `*_agent.md` would not rename. None exist today.

### Claim 3: Grok hook payloads (camelCase, `read_file`, `target_file`) warn on the third read and record the session-start marker
- **Evidence:** `test_reread_guard` grok cases OK; `test_session_start_hook.test_grok_camelcase_payload_records_the_marker` OK. Warning JSON uses `hookSpecificOutput.additionalContext` (Grok user-guide 10-hooks.md).
- **Oracle:** evaluate() ignores `read_file`/`target_file` unless host is grok; session-start ignores `sessionId` unless both key spellings are read.
- **Red observed before green:** yes. `--host` choices rejected `grok`; evaluate treated grok as Copilot (`toolArgs.path`).
- **Confidence:** Verified (contract read from `~/.grok/docs/user-guide/10-hooks.md` 2026-09-14, then executed).
- **Residual risk:** A future Grok envelope that drops the Claude aliases and uses only a new path key would silently not count reads (fail-open, by design).

### Claim 4: pack-doctor reports the Grok surface; knowledge is not in `.grok/rules/`
- **Evidence:** `pack-doctor.py` → `PASS Grok Build surface .grok/{skills,agents,hooks,rules} present`; re-read guard lists Grok Build. Fixture `test_grok_hooks_alone_pass`. Fresh-install test asserts no extra `*.md` in `.grok/rules/`.
- **Oracle:** `check_surface(..., ".grok", ...)` FAIL if any of the four dirs is missing. Extra-rules assertion FAIL if a knowledge doc is copied there.
- **Red observed before green:** yes. Doctor had only Claude and Copilot surfaces.
- **Confidence:** Verified.
- **Residual risk:** Claude compatibility still also loads `.claude/skills/`. Duplicate discovery is filtered by name (`.grok/skills/` wins). Not a correctness defect; documented.

### Claim 5: consuming-repo install path is pack-apply, not a second map
- **Evidence:** `pack-apply.py` docstring and `skills()`/`agents()`/`bundle()` place Grok dests. `/addpacktorepo` and `/updatepack` name `.grok/`. INSTALL revision 71, §1.7.
- **Oracle:** `test_fresh_install_deploys_the_grok_surface` is an `--install` apply, the same program `/addpacktorepo` runs.
- **Red observed before green:** yes. Fresh install before the place() calls had no `.grok/`.
- **Confidence:** Verified.
- **Residual risk:** A human following INSTALL by hand and skipping §1.7 still gets Claude/Copilot. pack-apply is the supported path.

## Commands

```
python -m unittest tests.docs_explorer.test_grok_surface tests.docs_explorer.test_reread_guard tests.docs_explorer.test_session_start_hook -v
python docs/ai-forward-pack/scripts/pack-doctor.py
python tools/check-consistency.py
pwsh tools/verify-bundle.ps1
```

## Residual risks (roll-up)

Project hooks need folder trust (`/hooks-trust`). Grok bundled `/implement` is overridden in pack-installed repos. No Rhai workflows ship in this revision.
