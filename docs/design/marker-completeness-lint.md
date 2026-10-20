---
id: design-marker-completeness-lint
title: "Marker completeness lint (Tier-1 prose→structure) — Design"
type: design
status: accepted
owner: "@timianmalloo"
phase: "1"
tags: [prose-to-structure, markers, no-guessing, solution-selection-ladder, lint]
links:
  - { to: design-agent-focus-controls, rel: relates-to }
review-by: 2026-11-30
summary: >-
  Tier-1 of the prose→structure review: give the assume: (NG4) and simplify: (L5)
  inline markers an enforced field-completeness check via a new marker-lint.py, using
  backward-compatible semantic-cue detection (trigger / confirm / consequence) that
  warns on legacy free-form rather than mandating a new label syntax.
---

# Marker completeness lint — Design

## Input (spec)
The approved **Tier-1** recommendation of `docs/proposals/prose-to-structure-review.html`:
promote the `assume:` (NG4) and `simplify:` (L5) markers from *prose-only field specs* to
an **enforced** field-completeness contract, warning on legacy free-form (V16a: a suggestion
warns, a defect fails). That proposal is the specify-layer artifact for this work.

## The design decision that grounding changed (a finding)
The proposal *sketched* a rigid multi-line label syntax (`confirms-when:` / `breaks-if:` /
`ceiling:` / `upgrade-when:`). Reading the actual code (E15) showed that would be wrong:

- The existing harvest regex (`dream.py:grep_markers`) captures **only the marker's first
  line**, and the canonical `assume:` marker in NG4 **spans three lines** (belief / breaks-if
  / Confirm). A multi-line label syntax breaks the regex.
- Every existing marker in the tree (`coord-core.py`, etc.) is single-line **free prose** with
  the fields woven in via an em-dash clause and `if`/`when`/`Confirm:` cues. A new syntax
  invalidates all of them for no correctness gain.
- The directives already name the *rot* precisely — L5/L6: "a marker that names **no
  trigger**"; NG4: no "confirmation route and a consequence." The failure to catch is
  **semantic absence**, not label absence.

So the design checks for the **semantic components** the directives already require, which
keeps every existing marker valid and the harvest regex intact. This is the Solution-Selection
Ladder applied to itself: the smallest change that enforces the existing contract.

## Contract
`scripts/marker-lint.py [--root DIR] [--gate] [--json] [--include-md] [paths...]`

- Walks code files (`.py .ps1 .ts .js .cs .go .rs`; `.md` only with `--include-md`), skipping
  generated/vendored trees (`.git node_modules dist _site .claude .github` + any path under
  `ai-forward-pack` or `dreams`) — the same skip set as the harvest.
- For each `simplify:` / `assume:` / `ponytail:` marker it assembles the **marker block** (the
  marker line + immediately-following continuation comment lines, stopping at the first
  non-comment line or the next marker) and classifies it:

| Marker | Required semantic components | Finding when missing |
|---|---|---|
| `simplify:` / `ponytail:` | a **trigger** (revisit condition) | `simplify-no-trigger` |
| `assume:` | a **confirm route** AND a **breaks-if consequence** | `assume-no-confirm` / `assume-no-consequence` |

- Detection is word-boundary keyword cues (trigger: `when if once upgrade revisit beyond above
  exceeds grows becomes reaches past until unless`; confirm: `confirm verify check inspect test
  measure read query run`; consequence: `if breaks false otherwise wrong shifts fails corrupts
  silently would`). These match the existing NG4/L5 example markers exactly.
- **Exit posture (V16a / docs-graph `--gate` pattern):** default = report + **exit 0** (warn,
  grandfathers legacy). `--gate` = exit 1 on any finding. `--json` for machine use. A clean
  scan of a non-empty corpus prints an "all N markers complete" line so an empty run is
  distinguishable from a clean one (E14).

## Why not wire it into verify-bundle as a hard gate
Warn-on-legacy (V16a) is the explicit posture, and a hard gate would (a) fail on any pre-
existing triggerless marker and (b) risk flagging the directive examples themselves. It ships
as a first-class harvest command (the L6 "natural follow-up") the `/investigate` and `/dream`
flows call; a repo may opt into `--gate` in its own CI.

## Directive edits
- **NG4 / NG9** — name the completeness check as the enforcement surface for the three fields.
- **L5 / L6** — the harvest is now a first-class command; the triggerless marker is what it flags.

## Failure modes
- **Continuation over-capture** (swallowing an unrelated following comment) → bounded: stop at
  first non-comment line or the next marker; tested.
- **Keyword false-positive inside a word** (`if` in `verify`) → word boundaries; tested.
- **Self-reference** (the lint's own tests contain marker-like fixtures) → tests run against a
  tmp `--root`, never the repo; `.md` excluded by default so directive examples are not scanned.
- **Empty corpus reads as clean** → explicit "0 markers found" vs "N complete" (E14).

## Adversarial analysis (STRIDE-lite)
Trust boundary: repository source files, which any contributor can write → `marker-lint.py` → stdout and the gate's exit code. The gate is now a required step: `tools/verify-bundle.ps1:126` and `.github/workflows/pack-consistency.yml:68`, `:223`, `:349` run `marker-lint.py --gate`. The script imports only `argparse json os re sys` (`pack/scripts/marker-lint.py:22-26`). It opens files for reading only, runs no subprocess and makes no network call (Verified by reading).

| Boundary | Threat | Disposition | Control, evidence and test |
|---|---|---|---|
| `--root` path → file walk | **T** (gate fails open): the skip test runs on the whole `dirpath`, root included. A root whose path contains `ai-forward-pack`, or a directory such as `dreams-old`, scans 0 files, and `--gate` exits 0 | **not mitigated** | `_iter_files`, `marker-lint.py:65`. Verified 2026-10-19: one triggerless `simplify:` marker under `<tmp>/clone-plain` gave exit 1; the same file under `<tmp>/clone-ai-forward-pack` printed "0 markers found in 0 file(s)" and gave exit 0. The E14 line prints, but the gate still passes. The `dreams` case is Inferred from the substring test. No test. Fix: match path components relative to the root, and fail `--gate` when 0 files are scanned. |
| Source tree → skip set | **T**: a contributor hides an incomplete marker in a skipped tree (`.claude`, `.github`, `dist`, `_site` at any depth) | accept | `SKIP_DIRS` (`:57`) exists so generated copies are not linted twice; the source of those copies (`pack/`) is linted. Repo review is the control. |
| Marker text → classifier | **S**: a cue word satisfies the check without meaning (`simplify: fine, revisit later`) | accept | Word-boundary keyword cues (`:47-55`). The design checks semantic presence, not truth. Review is the control. |
| File content → memory | **D**: each file is read whole with no size cap | accept | `f.read()` (`:111-112`). Input is repo-controlled; the CI job timeout bounds it. |
| File symlink → read | **I**: `os.walk` does not descend directory symlinks (`followlinks` defaults to False, `:62`), but a file symlink is opened, and up to 200 characters of a matching marker line from its target are printed | accept (Inferred) | `:111`, `:125`. Needs repo write to plant; prints only lines that match `MARKER_RX` (`:43`). No test. |
| Output → terminal, CI log or model | **T** (injection): marker text is echoed verbatim | accept | Up to 200 characters (`:125`, `:147`); `--json` escapes it. No control-character strip. The text is already committed comment content. |

**Design vs code:** the design says the lint is not wired into verify-bundle as a hard gate. It now is (see above). The design's contract also lists `[paths...]`; the parser takes no positional paths (`main`, `:133-138`). The tables above analyse the code.

## Privacy analysis (LINDDUN-lite)
| Data flow / category | LINDDUN finding | Disposition | Control / rationale | Retention & rights path |
|---|---|---|---|---|
| Code comments → stdout / `--json` | none: no personal data, because the lint reads only code files (`CODE_EXT`, `marker-lint.py:56`; `.md` only with `--include-md`) and prints only the marker comments it finds (up to 200 characters, `:125`) | n/a | A name or secret in a marker comment is already committed repository content. No scrub. | No store; the lint writes nothing. Output lives in the terminal or the CI log. |
| Lint → third party | none: no egress | n/a | No network module is imported (`:22-26`); no model is called. | — |

This component touches no personal data: its only input is source code and its only output is lint findings about that code.

**Security and privacy review (2026-10-19):** both sections were written from the code as it is now, not from the plan, to close the gap rows in `docs/security/threat-model.md` §4 and `docs/security/privacy-review.md` §5.
