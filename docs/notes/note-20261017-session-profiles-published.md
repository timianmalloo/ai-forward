---
id: note-20261017-session-profiles-published
title: "Decision — session profiles stay published on Pages and in the repo"
type: decision-note
status: accepted
owner: "@timianmalloo"
phase: "assessment"
tags: [decision, privacy, pages, publish-boundary, owner-ruling]
links:
  - { to: forensic-review-rev108, rel: relates-to }
review-by: "2027-04-17"
review-suggested: []
summary: >-
  During the rev108 forensic review the Privacy persona issued a hard-veto BLOCK because
  docs/profiles (session-profiler output with verbatim prompts, home paths and cwd values that
  name other repositories) is served on GitHub Pages and tracked in the public repo. The owner
  ruled that judgement wrong: publishing the profiles is intended and acceptable. No
  containment is taken; this note is the recorded basis, so later reviews do not re-raise it.
---

# Decision — session profiles stay published

**Date:** 2026-10-17 · **Context:** forensic review rev108, Stage 5 (DISCONFIRM) · **Decided by:** the owner, overruling the Privacy persona's hard veto

## What was raised

The Privacy persona blocked on `docs/profiles/` being outside the Pages bundle's `LOCAL_ONLY`
list (`tools/build-pages-bundle.py`) and tracked in the public repository. Verified facts at the
time of the ruling:

- `https://timianmalloo.github.io/ai-forward/docs/profiles/sp-0009/profile.json` returned HTTP 200.
- The served `sp-0002/profile.json` carried 1,194 `"prompt":` fields.
- `ai-forward` is public; `TheTerrace`, one repository named in the profiles' `cwd` values, is private.

## Ruling

The owner ruled the persona's **judgement** wrong, not its facts: publishing the profiles is
intended and acceptable. The facts above stand; the "no basis for publication" conclusion does not.

## Consequences

- `docs/profiles` stays out of `LOCAL_ONLY` and stays tracked. No redeploy, no history rewrite.
- The rev108 backlog carries no item for it. The machine-path gate's scope (`docs/` is not in
  `verify-no-machine-paths.py` `SURFACES`) is unaffected by this ruling and is not reopened here.

## Addendum 2026-10-19 — scope and scrub (FR-103, FR-104; revision 115)

- **Scope (owner ruling):** *"repos that install the pack should not get session profiles
  committed without notice — just this pack."* This ruling covers the pack's own source
  repository only. Elsewhere `session-profile.py` writes to the untracked
  `<git-dir>/ai-forward/profiles/` and says so. `--publish` writes `docs/profiles/`, with a
  notice that the folder is tracked.
- **Scrub:** re-open trigger 1 was close to firing. A token planted in a piped-gate shell
  command reached a profile verbatim (FR-103); the 8 committed profiles scanned clean. Every
  string is now scrubbed with `dream.py`'s patterns before anything is written, and that also
  covers emails. The publication ruling above is unchanged.

## Re-open triggers

- A profile is found to contain a secret, a credential, or a third party's personal data.
- The owner changes their view of what other repositories' prompts may be public.
- The session profiler starts emitting a new data class (for example file contents or emails).
