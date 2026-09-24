---
id: api-verify-ruling-citations
title: "API — verify-ruling-citations.py"
type: api
status: accepted
owner: "@timianmalloo"
tags: [api, scripts, generated]
links:
  - { to: api-index, rel: refines }
review-by: "2027-03-03"
summary: >-
  verify-ruling-citations.py - every ruling cited as authority resolves to exactly one heading that says what it decided.
---

# `verify-ruling-citations.py`

*Generated from `pack/scripts/verify-ruling-citations.py` by `tools/build-api-docs.py`. Do not edit by hand — edit the source docstrings and regenerate.*

## Summary

```text
verify-ruling-citations.py - every ruling cited as authority resolves to exactly one heading that says what it decided.

THE CLASS (absorbed from ai-de's tools/verify-ruling-citations.py, measured 2026-09-11; class ID-A).
Programme decisions were cited by number across that repository and enforced as binding. Eight of
them defined nothing: numbers cited with no note anywhere recording what they said, one of them
cited six times as governing a dependency decision. Two ends of that met on the same day: a number
was cited by a mockup, a review and a mid-task correction BEFORE any ruling of that number had been
made, and the Owner, unable to see it because nothing recorded it, allocated the same number again
for a different decision. THE ABSENCE OF THE REGISTER IS WHAT CAUSED THE COLLISION IN THE REGISTER.
A decision that cannot be read is not a decision; it is a number with a reputation.

WHAT COUNTS. A DEFINITION is a heading `### Ruling NN — …` (or `## Ruling NN — …`) in
docs/notes/rulings.md - the only definition site; `coord decide rule` writes it. A CITATION is
`Ruling NN` (or `Rulings NN`) in PROSE - `.md`, `.html`, `.txt` - anywhere under docs/, pack/,
.agents/log/, .github/, .claude/. A mention inside prose is a citation, never a definition: that
distinction is the whole point, and collapsing it would make the gate agree with any file that talks
about a ruling often enough. Records (`.json`, `.jsonl`) are not scanned: the audit log and the
dreams quote other repositories' prose verbatim, and a quote is not a citation (decision note
note-20260919-owner-review-register-and-scan-scope). docs/ai-forward-pack/ is skipped as the
generated copy of pack/.

THE SHORT FORM. A register may number its rulings `## R-n · date · seat · title` (measured in
x-harness-x-model-bench, 2026-09-24): there the gate read no heading and no citation, and passed
while checking nothing. So `## R-n` / `### R-n` also define number n, and `R-n` in prose (e.g.
"R-7", "ruling R-4") also cites it: `R-n` and `Ruling n` name one number. The short form is
strict because short ids are common: `R-` must not follow a letter, digit or hyphen (DR-1, PR-12,
AR-R-7) and the number must not continue as `.d`, `-d` or a letter (spike R-2.3, R-3-4, R-12a).

THE TWO DEFECTS. (1) A number cited with no heading. (2) A number defined by two headings. There is
no frozen list: nothing predates this control, so the list that "may only shrink" starts empty and
therefore does not exist. And one refusal to report clean (class PACK-P): a register with level-2/3
headings of which none parses as a ruling is NOT CHECKED - the R-n register passed as "0 defined"
because an unread register and an empty one printed the same.

USAGE
  python3 verify-ruling-citations.py                 scan the repository at the cwd
  python3 verify-ruling-citations.py --root <repo>   scan that repository
  python3 verify-ruling-citations.py --self-test     prove both defects fire and a clean tree is quiet (DC-104)

EXIT  0 ok  ·  1 refused (defects listed, one per line)  ·  2 usage (--root is not a directory)
```

## CLI — options

| Option | Help |
|---|---|
| `--root` | the repository to scan (default: cwd) |
| `--self-test` | prove this gate can fail, against a synthetic tree |

## Functions

### `definitions(root, spellings=…)`

number -> the register line numbers that define it (two lines = the collision).

### `citations(root, spellings=…)`

number -> the prose files (repo-relative, posix) that cite it. The register is scanned
too: prose in it that names a number is a citation (a heading is the only definition).

### `unread_headings(root)`

How many level-2/3 register headings exist when NONE of them parsed as a definition (PACK-P):
a register of headings in an unknown numbering is not an empty register, and must not read as one.

### `check(root)`

**Coverage gap** — no docstring in the source.

### `self_test()`

Break a synthetic tree in each direction and require the gate to notice (DC-104): a
control's first green is evidence about the control, and the control is the part nobody
re-examines because it is what they just reasoned about.

## Coverage

- Public functions: **5** · documented: **4** (**80%**)
- Undocumented (recorded, not invented): `check`

